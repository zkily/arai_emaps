<template>
  <div class="material-editor">
    <div class="header">
      <h3>📋 材料構成</h3>
      <el-button type="success" size="small" icon="Plus" @click="handleAdd">材料追加</el-button>
    </div>

    <!-- 材料一覧 -->
    <el-table :data="materialList" border size="small" :loading="loading">
      <el-table-column label="材料CD" prop="material_cd" width="120" />
      <el-table-column label="材料名称" prop="material_name" />
      <el-table-column label="数量" prop="quantity" width="120" align="right" />
      <el-table-column label="単価" prop="unit_price" width="120" align="right" />
      <el-table-column label="操作" width="140">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.row)">編集</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">削除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 材料編集ダイアログ -->
    <el-dialog v-model="dialogVisible" title="材料設定" width="400px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="材料">
          <el-select v-model="editForm.material_cd" filterable placeholder="選択">
            <el-option v-for="item in materialOptions" :key="item.cd"
              :label="`${item.cd}｜${item.name}`" :value="item.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="editForm.quantity" :min="0.01" :precision="4" />
        </el-form-item>
        <el-form-item label="単価">
          <el-input-number v-model="editForm.unit_price" :min="0" :precision="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="saveMaterial">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import request from '@/utils/request'
import type { OptionItem } from '@/types/master'
import { getMaterialOptions } from '@/api/options'

const props = defineProps<{ component_cd: string }>()
const materialList = ref<any[]>([])
const materialOptions = ref<OptionItem[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const editForm = reactive<any>({
  id: 0,
  material_cd: '',
  quantity: 1,
  unit_price: 0
})

// ✅ 材料一覧取得
const fetchMaterials = async () => {
  if (!props.component_cd) return
  loading.value = true
  try {
    const res = await request.get(`/api/master/component-materials/${props.component_cd}`)
    materialList.value = res ?? []
  } catch {
    ElMessage.error('材料一覧取得に失敗')
  } finally {
    loading.value = false
  }
}

// ✅ 材料追加
const handleAdd = () => {
  Object.assign(editForm, { id: 0, material_cd: '', quantity: 1, unit_price: 0 })
  dialogVisible.value = true
}

// ✅ 材料編集
const handleEdit = (row: any) => {
  Object.assign(editForm, row)
  dialogVisible.value = true
}

// ✅ 保存
const saveMaterial = async () => {
  if (!editForm.material_cd) {
    ElMessage.warning('材料を選択してください')
    return
  }
  try {
    if (editForm.id) {
      await request.put(`/api/master/component-materials/${editForm.id}`, {
        material_cd: editForm.material_cd,
        quantity: editForm.quantity,
        unit_price: editForm.unit_price
      })
      ElMessage.success('更新しました')
    } else {
      await request.post('/api/master/component-materials', {
        component_cd: props.component_cd,
        material_cd: editForm.material_cd,
        quantity: editForm.quantity,
        unit_price: editForm.unit_price
      })
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    fetchMaterials()
  } catch {
    ElMessage.error('保存に失敗しました')
  }
}

// ✅ 材料削除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('この材料を削除しますか？', '確認', { type: 'warning' })
    .then(async () => {
      await request.delete(`/api/master/component-materials/${row.id}`)
      ElMessage.success('削除しました')
      fetchMaterials()
    })
    .catch(() => { })
}

// ✅ 初回 + component_cd 変化時に fetch
onMounted(async () => {
  fetchMaterials()
  materialOptions.value = await getMaterialOptions()
})

watch(() => props.component_cd, () => fetchMaterials())
</script>

<style scoped>
.material-editor {
  padding: 10px 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
</style>
