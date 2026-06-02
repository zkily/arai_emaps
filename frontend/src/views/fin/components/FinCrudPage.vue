<!--
  FIN 汎用 CRUD ページ。
  一覧（ページング・キーワード検索）＋ ドロワーフォームでの新規/編集/削除。
  生成ラッパ（views/fin/<domain>/*.vue）から title / apiBase / columns / fields を受け取る。
  業務固有の検証や明細編集が必要な画面は、この上に *.custom.vue を作って差し替える。
-->
<template>
  <div class="fin-crud-page">
    <div class="fin-page-header">
      <div class="fin-page-title">
        <el-icon><Tickets /></el-icon>
        <span>{{ title }}</span>
      </div>
      <div class="fin-page-actions">
        <el-input
          v-model="keyword"
          placeholder="キーワード検索"
          clearable
          style="width: 220px"
          @keyup.enter="reload"
          @clear="reload"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新規
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="fin-table-card">
      <el-table :data="rows" v-loading="loading" stripe border height="calc(100vh - 260px)">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="col.width || 140"
          :align="col.align || 'left'"
          show-overflow-tooltip
        />
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">編集</el-button>
            <el-button link type="danger" size="small" @click="remove(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="fin-pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="reload"
          @size-change="reload"
        />
      </div>
    </el-card>

    <el-drawer v-model="drawerVisible" :title="editingId ? `${title} 編集` : `${title} 新規`" size="480px">
      <el-form :model="form" label-width="140px" class="fin-form">
        <el-form-item
          v-for="f in fields"
          :key="f.prop"
          :label="f.label"
          :required="f.required"
        >
          <el-switch v-if="f.type === 'switch'" v-model="form[f.prop]" />
          <el-input-number
            v-else-if="f.type === 'number'"
            v-model="form[f.prop]"
            :controls="false"
            style="width: 100%"
          />
          <el-date-picker
            v-else-if="f.type === 'date'"
            v-model="form[f.prop]"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
          <el-date-picker
            v-else-if="f.type === 'datetime'"
            v-model="form[f.prop]"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
          <el-input
            v-else
            v-model="form[f.prop]"
            :type="f.type === 'textarea' ? 'textarea' : 'text'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Tickets } from '@element-plus/icons-vue'
import { createFinResource } from '@/api/fin'
import type { FinColumn, FinField } from './types'

const props = defineProps<{
  title: string
  apiBase: string
  columns: FinColumn[]
  fields: FinField[]
}>()

type Row = Record<string, unknown>
const api = createFinResource<Row>(props.apiBase)

const rows = ref<Row[]>([])
const loading = ref(false)
const saving = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const drawerVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Row>({})

async function reload() {
  loading.value = true
  try {
    const data = await api.list({ page: page.value, page_size: pageSize.value, q: keyword.value || undefined })
    rows.value = data.items || []
    total.value = data.total || 0
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.keys(form).forEach((k) => delete form[k])
  props.fields.forEach((f) => {
    form[f.prop] = f.type === 'switch' ? false : null
  })
}

function openCreate() {
  editingId.value = null
  resetForm()
  drawerVisible.value = true
}

function openEdit(row: Row) {
  editingId.value = (row.id as number) ?? null
  resetForm()
  props.fields.forEach((f) => {
    if (row[f.prop] !== undefined) form[f.prop] = row[f.prop]
  })
  drawerVisible.value = true
}

async function save() {
  saving.value = true
  try {
    if (editingId.value) {
      await api.update(editingId.value, { ...form })
      ElMessage.success('更新しました')
    } else {
      await api.create({ ...form })
      ElMessage.success('作成しました')
    }
    drawerVisible.value = false
    await reload()
  } catch {
    /* request インターセプタがエラー表示する */
  } finally {
    saving.value = false
  }
}

async function remove(row: Row) {
  await ElMessageBox.confirm('削除してよろしいですか？', '確認', { type: 'warning' })
  await api.remove(row.id as number)
  ElMessage.success('削除しました')
  await reload()
}

onMounted(reload)
</script>

<style scoped>
.fin-crud-page {
  padding: 16px;
}
.fin-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.fin-page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
}
.fin-page-actions {
  display: flex;
  gap: 10px;
}
.fin-pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.fin-form :deep(.el-input-number .el-input__inner) {
  text-align: left;
}
</style>
