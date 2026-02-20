<template>
  <div class="menu-management">
    <div class="page-header">
      <h2>メニュー管理</h2>
      <p class="subtitle">サイドバーメニューと権限・ロールのメニュー権限で使用。新規ルートは router/menuConfig.ts に追加し「ルート定義から取り込み」で反映。</p>
    </div>

    <div class="action-bar">
      <el-button type="primary" size="small" :icon="Upload" @click="handleSyncFromConfig">ルート定義から取り込み</el-button>
      <el-button size="small" :icon="Plus" @click="handleAddRoot">ルート追加</el-button>
      <el-button size="small" :icon="Refresh" @click="fetchMenus">更新</el-button>
      <el-input
        v-model="searchQuery"
        placeholder="検索..."
        :prefix-icon="Search"
        clearable
        class="search-input"
        size="small"
      />
    </div>

    <div class="table-wrap">
      <el-table
        :data="filteredTreeData"
        v-loading="loading"
        row-key="id"
        default-expand-all
        size="small"
        stripe
      >
        <el-table-column prop="code" label="コード" width="160">
          <template #default="{ row }">
            <code class="code-text">{{ row.code }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名前" min-width="120" />
        <el-table-column prop="path" label="パス" min-width="160">
          <template #default="{ row }">
            <span v-if="row.path" class="path-text">{{ row.path }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="icon" label="アイコン" width="88" align="center">
          <template #default="{ row }">
            <span v-if="row.icon" class="icon-tag">{{ row.icon }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="順" width="56" align="center" />
        <el-table-column prop="is_active" label="状態" width="72" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small" effect="plain">
              {{ row.is_active ? '有効' : '無効' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleAddChild(row)">子</el-button>
            <el-button size="small" type="primary" link @click="handleEdit(row)">編集</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="460px" destroy-on-close class="compact-dialog">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="88px" label-position="left" class="compact-form">
        <el-form-item label="コード" prop="code">
          <el-input v-model="form.code" placeholder="例: ERP_SALES" :disabled="!!editingId" size="small" />
          <div class="form-tip" v-if="!editingId">登録後は変更不可</div>
        </el-form-item>
        <el-form-item label="名前" prop="name">
          <el-input v-model="form.name" placeholder="表示名" size="small" />
        </el-form-item>
        <el-form-item label="親" prop="parent_id">
          <el-select v-model="form.parent_id" placeholder="ルートは空" clearable size="small" style="width:100%">
            <el-option v-for="opt in parentOptions" :key="opt.id" :label="opt.label" :value="opt.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="パス" prop="path">
          <el-input v-model="form.path" placeholder="/erp/sales" size="small" />
        </el-form-item>
        <el-form-item label="アイコン" prop="icon">
          <el-input v-model="form.icon" placeholder="例: Sell" size="small" />
        </el-form-item>
        <el-form-item label="表示順" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" size="small" />
        </el-form-item>
        <el-form-item label="有効" prop="is_active" v-if="editingId !== null">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="dialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Upload, Search } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as systemApi from '@/api/system'
import type { MenuItem } from '@/api/system'
import { menuConfig } from '@/router/menuConfig'

const loading = ref(false)
const submitting = ref(false)
const menuList = ref<MenuItem[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('メニュー追加')
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const searchQuery = ref('')

const form = reactive({
  code: '',
  name: '',
  parent_id: null as number | null,
  path: '',
  icon: '',
  sort_order: 0,
  is_active: true,
})

const formRules: FormRules = {
  code: [{ required: true, message: 'コードを入力してください', trigger: 'blur' }],
  name: [{ required: true, message: '名前を入力してください', trigger: 'blur' }],
}

const treeData = computed(() => {
  const list = menuList.value
  const byId = new Map(list.map((m) => [m.id, { ...m, children: [] as MenuItem[] }]))
  const roots: (MenuItem & { children: MenuItem[] })[] = []
  for (const m of list) {
    const node = byId.get(m.id)!
    if (!m.parent_id) roots.push(node)
    else {
      const parent = byId.get(m.parent_id)
      if (parent) (parent as { children: MenuItem[] }).children.push(node)
      else roots.push(node)
    }
  }
  const sort = (arr: (MenuItem & { children?: MenuItem[] })[]) =>
    arr.sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
  sort(roots)
  roots.forEach((r) => r.children?.length && sort(r.children))
  return roots
})

const filteredTreeData = computed(() => {
  if (!searchQuery.value.trim()) return treeData.value
  const q = searchQuery.value.toLowerCase().trim()
  const filter = (nodes: (MenuItem & { children?: MenuItem[] })[]): (MenuItem & { children?: MenuItem[] })[] => {
    return nodes.reduce((acc, node) => {
      const match = node.code.toLowerCase().includes(q) || node.name.toLowerCase().includes(q) ||
        (node.path && node.path.toLowerCase().includes(q))
      const children = node.children ? filter(node.children) : []
      if (match || children.length) acc.push({ ...node, children })
      return acc
    }, [] as (MenuItem & { children?: MenuItem[] })[])
  }
  return filter(treeData.value)
})

const parentOptions = computed(() => {
  const list = menuList.value
  const exclude = new Set<number>()
  if (editingId.value) {
    const collect = (id: number) => {
      exclude.add(id)
      list.filter((m) => m.parent_id === id).forEach((m) => collect(m.id))
    }
    collect(editingId.value)
  }
  return list.filter((m) => !exclude.has(m.id)).map((m) => ({ id: m.id, label: `${m.code} - ${m.name}` }))
})

async function fetchMenus() {
  loading.value = true
  try {
    const res = (await systemApi.getMenus(true)) as unknown
    menuList.value = Array.isArray(res) ? res : []
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err?.response?.data?.detail || 'メニュー一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function handleSyncFromConfig() {
  ElMessageBox.confirm(
    'router/menuConfig.ts の定義を DB に同期します。続行しますか？',
    'ルート定義から取り込み',
    { confirmButtonText: '取り込み', cancelButtonText: 'キャンセル', type: 'info' }
  ).then(async () => {
    submitting.value = true
    try {
      await systemApi.syncMenus(menuConfig.map((c) => ({
        code: c.code,
        name: c.name,
        path: c.path ?? null,
        icon: c.icon ?? null,
        parent_code: c.parentCode ?? null,
        sort_order: Number.isFinite(c.sortOrder) ? Math.round(Number(c.sortOrder)) : 0,
      })))
      ElMessage.success('メニューを同期しました')
      await fetchMenus()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      ElMessage.error(err?.response?.data?.detail || '同期に失敗しました')
    } finally {
      submitting.value = false
    }
  }).catch(() => {})
}

function handleAddRoot() {
  editingId.value = null
  dialogTitle.value = 'ルートメニュー追加'
  form.code = ''
  form.name = ''
  form.parent_id = null
  form.path = ''
  form.icon = ''
  form.sort_order = 0
  form.is_active = true
  dialogVisible.value = true
}

function handleAddChild(row: MenuItem) {
  editingId.value = null
  dialogTitle.value = '子メニュー追加'
  form.code = ''
  form.name = ''
  form.parent_id = row.id
  form.path = ''
  form.icon = ''
  form.sort_order = menuList.value.filter((m) => m.parent_id === row.id).length
  form.is_active = true
  dialogVisible.value = true
}

function handleEdit(row: MenuItem) {
  editingId.value = row.id
  dialogTitle.value = 'メニュー編集'
  form.code = row.code
  form.name = row.name
  form.parent_id = row.parent_id
  form.path = row.path || ''
  form.icon = row.icon || ''
  form.sort_order = row.sort_order
  form.is_active = row.is_active
  dialogVisible.value = true
}

function handleSubmit() {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editingId.value !== null) {
        await systemApi.updateMenu(editingId.value, {
          name: form.name,
          parent_id: form.parent_id,
          path: form.path || null,
          icon: form.icon || null,
          sort_order: form.sort_order,
          is_active: form.is_active,
        })
        ElMessage.success('更新しました')
      } else {
        await systemApi.createMenu({
          code: form.code,
          name: form.name,
          parent_id: form.parent_id,
          path: form.path || null,
          icon: form.icon || null,
          sort_order: form.sort_order,
          is_active: form.is_active,
        })
        ElMessage.success('追加しました')
      }
      dialogVisible.value = false
      await fetchMenus()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      ElMessage.error(err?.response?.data?.detail || '保存に失敗しました')
    } finally {
      submitting.value = false
    }
  })
}

function handleDelete(row: MenuItem) {
  const hasChildren = menuList.value.some((m) => m.parent_id === row.id)
  ElMessageBox.confirm(
    hasChildren ? `「${row.name}」に子メニューがあります。削除しますか？` : `「${row.name}」を削除しますか？`,
    '削除確認',
    { confirmButtonText: '削除', cancelButtonText: 'キャンセル', type: 'warning' }
  ).then(async () => {
    try {
      await systemApi.deleteMenu(row.id)
      ElMessage.success('削除しました')
      await fetchMenus()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      ElMessage.error(err?.response?.data?.detail || '削除に失敗しました')
    }
  }).catch(() => {})
}

onMounted(() => fetchMenus())
</script>

<style scoped>
.menu-management {
  padding: 12px 16px 20px;
  min-height: 100%;
  background: #f8fafc;
}

.page-header {
  margin-bottom: 10px;
}
.page-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 2px 0;
}
.subtitle {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.search-input {
  width: 160px;
  margin-left: auto;
}

.table-wrap {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}
.table-wrap :deep(.el-table) {
  font-size: 12px;
}
.table-wrap :deep(.el-table th.el-table__cell) {
  background: #f1f5f9;
  color: #475569;
  font-weight: 600;
  padding: 6px 0;
}
.table-wrap :deep(.el-table td.el-table__cell) {
  padding: 6px 0;
}
.code-text {
  font-size: 11px;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  color: #475569;
}
.path-text {
  font-size: 11px;
  color: #64748b;
  font-family: ui-monospace, monospace;
}
.muted {
  color: #94a3b8;
  font-size: 12px;
}
.icon-tag {
  font-size: 11px;
  color: #64748b;
}

.compact-dialog :deep(.el-dialog__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
}
.compact-dialog :deep(.el-dialog__body) {
  padding: 12px 16px;
}
.compact-dialog :deep(.el-dialog__footer) {
  padding: 10px 16px 12px;
  border-top: 1px solid #e2e8f0;
}
.compact-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
.compact-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}
.form-tip {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

@media (max-width: 768px) {
  .menu-management { padding: 8px 12px 16px; }
  .search-input { width: 120px; margin-left: 0; }
}
</style>
