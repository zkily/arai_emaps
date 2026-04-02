<template>
  <div class="tolerance-page">
    <div class="page-header">
      <div class="header-left">
        <div class="title-wrap">
          <h2>材料公差管理</h2>
          <p>材料マスタテーブルの公差・範囲項目を編集します</p>
        </div>
        <div class="header-stats">
          <el-tag type="info" effect="light">総件数 {{ totalCount }}</el-tag>
          <el-tag type="success" effect="light">表示 {{ filteredList.length }}</el-tag>
        </div>
      </div>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="fetchList">再読込</el-button>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="材料CD・材料名・規格で検索"
        clearable
        :prefix-icon="Search"
        size="small"
      />
    </div>

    <div class="table-card">
      <el-table
        :data="filteredList"
        v-loading="loading"
        border
        stripe
        size="small"
        height="calc(100vh - 220px)"
      >
        <el-table-column prop="material_cd" label="材料CD" width="70" />
        <el-table-column prop="material_name" label="材料名" width="120" show-overflow-tooltip />
        <el-table-column prop="standard_spec" label="規格" width="90" show-overflow-tooltip />
        <el-table-column prop="tolerance_range" label="公差範囲" width="80" show-overflow-tooltip />
        <el-table-column prop="tolerance_1" label="公差1" width="70" align="right" />
        <el-table-column prop="tolerance_2" label="公差2" width="70" align="right" />
        <el-table-column prop="range_value" label="範囲" width="180" align="center" />
        <el-table-column prop="min_value" label="最小値" width="70" align="right" />
        <el-table-column prop="max_value" label="最大値" width="70" align="right" />
        <el-table-column prop="actual_value_1" label="実力値1" width="75" align="right" />
        <el-table-column prop="actual_value_2" label="実力値2" width="75" align="right" />
        <el-table-column prop="actual_value_3" label="実力値3" width="75" align="right" />
        <el-table-column prop="representative_model" label="代表品種" min-width="100" show-overflow-tooltip />
        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="openEdit(row)">編集</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="公差・範囲編集"
      width="760px"
      :close-on-click-modal="false"
      class="tolerance-dialog"
    >
      <el-form :model="form" label-width="110px" class="edit-form">
        <div class="row">
          <el-form-item label="材料CD"><el-input v-model="form.material_cd" disabled /></el-form-item>
          <el-form-item label="材料名"><el-input v-model="form.material_name" disabled /></el-form-item>
        </div>
        <div class="row">
          <el-form-item label="公差範囲"><el-input v-model="form.tolerance_range" /></el-form-item>
          <el-form-item label="範囲"><el-input v-model="form.range_value" /></el-form-item>
        </div>
        <div class="row">
          <el-form-item label="公差1">
            <el-input-number v-model="form.tolerance_1" :step="0.01" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="公差2">
            <el-input-number v-model="form.tolerance_2" :step="0.01" :precision="2" controls-position="right" />
          </el-form-item>
        </div>
        <div class="row">
          <el-form-item label="最小値">
            <el-input-number v-model="form.min_value" :step="0.01" :precision="2" controls-position="right" />
          </el-form-item>
          <el-form-item label="最大値">
            <el-input-number v-model="form.max_value" :step="0.01" :precision="2" controls-position="right" />
          </el-form-item>
        </div>
        <div class="row">
          <el-form-item label="実力値1">
            <el-input-number v-model="form.actual_value_1" :step="0.001" :precision="3" controls-position="right" />
          </el-form-item>
          <el-form-item label="実力値2">
            <el-input-number v-model="form.actual_value_2" :step="0.001" :precision="3" controls-position="right" />
          </el-form-item>
        </div>
        <div class="row">
          <el-form-item label="実力値3">
            <el-input-number v-model="form.actual_value_3" :step="0.001" :precision="3" controls-position="right" />
          </el-form-item>
          <el-form-item label="代表品種"><el-input v-model="form.representative_model" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="saveTolerance">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { getMaterialList, updateMaterial } from '@/api/master/materialMaster'
import type { Material } from '@/types/master'

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const materialList = ref<Material[]>([])

const dialogVisible = ref(false)
const form = ref<Material>({
  id: 0,
  material_cd: '',
  material_name: '',
})

const filteredList = computed(() => {
  const k = keyword.value.trim().toLowerCase()
  const baseList = !k
    ? materialList.value
    : materialList.value.filter((row) =>
    [row.material_cd, row.material_name, row.standard_spec]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(k)),
  )
  return [...baseList].sort((a, b) =>
    String(a.material_name || '').localeCompare(String(b.material_name || ''), 'ja'),
  )
})
const totalCount = computed(() => materialList.value.length)

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getMaterialList({ page: 1, pageSize: 10000 })
    materialList.value = res?.data?.list ?? res?.list ?? []
  } finally {
    loading.value = false
  }
}

const openEdit = (row: Material) => {
  form.value = { ...row }
  dialogVisible.value = true
}

const saveTolerance = async () => {
  if (!form.value.id) {
    ElMessage.error('IDが不正です')
    return
  }
  saving.value = true
  try {
    await updateMaterial({ ...form.value })
    ElMessage.success('公差情報を更新しました')
    dialogVisible.value = false
    await fetchList()
  } catch {
    ElMessage.error('更新に失敗しました')
  } finally {
    saving.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.tolerance-page {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: linear-gradient(145deg, #f4f7fb 0%, #eef3f9 100%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  padding: 10px 12px;
  color: #fff;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.22);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-wrap h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}

.title-wrap p {
  margin: 3px 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
}

.header-stats {
  display: flex;
  gap: 6px;
}

.filter-bar {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.table-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 6px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
}

.table-card :deep(.el-table th) {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}

.tolerance-dialog :deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.edit-form .row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}

.edit-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

@media (max-width: 900px) {
  .edit-form .row {
    grid-template-columns: 1fr;
  }
}
</style>
