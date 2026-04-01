<template>
  <div class="bom-editor">
    <!-- ヘッダー -->
    <div class="page-header">
      <div class="header-left">
        <h2>明細BOM管理</h2>
        <span class="subtitle">製品別部品構成表の登録・編集・ツリー表示</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新規BOM作成</el-button>
      </div>
    </div>

    <!-- 検索バー -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" class="search-form">
        <el-form-item label="製品CD">
          <el-input v-model="searchProductCd" placeholder="製品CDで検索" clearable style="width: 200px" @keyup.enter="loadHeaders" />
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="searchStatus" clearable placeholder="全て" style="width: 130px">
            <el-option label="有効" value="active" />
            <el-option label="履歴" value="historical" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadHeaders">検索</el-button>
          <el-button @click="resetSearch">クリア</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- メインコンテンツ: 左ヘッダ一覧 + 右ツリー -->
    <div class="main-content">
      <!-- 左: BOMヘッダ一覧 -->
      <el-card class="header-list-card" shadow="never">
        <template #header>
          <span>BOMヘッダ一覧（{{ headerTotal }}件）</span>
        </template>
        <el-table
          :data="headers"
          v-loading="loadingHeaders"
          highlight-current-row
          size="small"
          @current-change="onHeaderSelect"
          style="width: 100%"
        >
          <el-table-column prop="parent_product_cd" label="親製品CD" width="140" />
          <el-table-column prop="bom_type" label="種別" width="100">
            <template #default="{ row }">
              <el-tag :type="row.bom_type === 'production' ? 'success' : 'info'" size="small">
                {{ row.bom_type === 'production' ? '製造' : '設計' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="revision" label="版番" width="70" />
          <el-table-column prop="status" label="状態" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '有効' : '履歴' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="effective_from" label="有効開始" width="110" />
          <el-table-column prop="effective_to" label="有効終了" width="110" />
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog(row)">編集</el-button>
              <el-popconfirm title="削除しますか？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button link type="danger" size="small">削除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap">
          <el-pagination
            size="small"
            layout="total, prev, pager, next"
            :total="headerTotal"
            :page-size="pageSize"
            v-model:current-page="currentPage"
            @current-change="loadHeaders"
          />
        </div>
      </el-card>

      <!-- 右: BOMツリー -->
      <el-card class="tree-card" shadow="never">
        <template #header>
          <span>BOM構成ツリー{{ selectedHeader ? ` — ${selectedHeader.parent_product_cd}` : '' }}</span>
        </template>
        <div v-if="!selectedHeader" class="empty-tree">
          <el-empty description="左のリストからBOMヘッダを選択してください" />
        </div>
        <el-table
          v-else
          :data="treeData"
          v-loading="loadingTree"
          row-key="id"
          :tree-props="{ children: 'children' }"
          default-expand-all
          size="small"
          border
          style="width: 100%"
        >
          <el-table-column prop="line_no" label="行番" width="70" />
          <el-table-column prop="component_type" label="子品目種別" width="110">
            <template #default="{ row }">
              <el-tag
                :type="componentTypeTagMap[row.component_type] || 'info'"
                size="small"
              >{{ componentTypeLabel[row.component_type] || row.component_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="子品目CD" width="150">
            <template #default="{ row }">
              {{ row.component_product_cd || row.component_material_cd || '—' }}
            </template>
          </el-table-column>
          <el-table-column prop="qty_per" label="所要量" width="100" align="right" />
          <el-table-column prop="uom" label="単位" width="70" />
          <el-table-column prop="scrap_rate" label="ロス率(%)" width="100" align="right" />
          <el-table-column prop="consume_process_cd" label="投入工程" width="120" />
          <el-table-column prop="remarks" label="備考" min-width="120" />
        </el-table>
      </el-card>
    </div>

    <!-- 新規/編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? 'BOM編集' : '新規BOM作成'"
      width="900px"
      destroy-on-close
    >
      <el-form :model="formData" label-width="120px" size="small">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="親製品CD" required>
              <el-input v-model="formData.parent_product_cd" :disabled="isEditing" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="種別">
              <el-select v-model="formData.bom_type" style="width: 100%">
                <el-option label="製造" value="production" />
                <el-option label="設計" value="engineering" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="版番">
              <el-input v-model="formData.revision" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="有効開始">
              <el-date-picker v-model="formData.effective_from" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="有効終了">
              <el-date-picker v-model="formData.effective_to" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="基準数量">
              <el-input-number v-model="formData.base_quantity" :min="0.0001" :step="1" :precision="4" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="単位">
              <el-input v-model="formData.uom" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="備考">
          <el-input v-model="formData.remarks" type="textarea" :rows="2" />
        </el-form-item>

        <!-- 行エディタ -->
        <el-divider content-position="left">BOM明細行</el-divider>
        <div style="margin-bottom: 8px">
          <el-button type="primary" size="small" :icon="Plus" @click="addLine">行追加</el-button>
        </div>
        <el-table :data="formData.lines" size="small" border max-height="300">
          <el-table-column label="行番" width="80">
            <template #default="{ row }">
              <el-input-number v-model="row.line_no" :min="1" :step="10" size="small" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="種別" width="120">
            <template #default="{ row }">
              <el-select v-model="row.component_type" size="small" style="width: 100%">
                <el-option label="原材料" value="material" />
                <el-option label="外購品" value="purchased" />
                <el-option label="子阶品" value="subassy" />
                <el-option label="Phantom" value="phantom" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="製品CD" width="140">
            <template #default="{ row }">
              <el-input v-model="row.component_product_cd" size="small" placeholder="製品CD" />
            </template>
          </el-table-column>
          <el-table-column label="材料CD" width="140">
            <template #default="{ row }">
              <el-input v-model="row.component_material_cd" size="small" placeholder="材料CD" />
            </template>
          </el-table-column>
          <el-table-column label="所要量" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.qty_per" :min="0" :precision="6" size="small" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="単位" width="70">
            <template #default="{ row }">
              <el-input v-model="row.uom" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="ロス率" width="80">
            <template #default="{ row }">
              <el-input-number v-model="row.scrap_rate" :min="0" :max="100" :precision="2" size="small" controls-position="right" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60">
            <template #default="{ $index }">
              <el-button link type="danger" size="small" @click="removeLine($index)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getBomHeaders,
  getBomTree,
  createBomHeader,
  updateBomHeader,
  deleteBomHeader,
  type BomHeader,
  type BomLine,
  type BomLinePayload,
} from '@/api/master/productBom'

const componentTypeLabel: Record<string, string> = {
  material: '原材料',
  purchased: '外購品',
  subassy: '子阶品',
  phantom: 'Phantom',
}
const componentTypeTagMap: Record<string, string> = {
  material: 'warning',
  purchased: 'success',
  subassy: 'primary',
  phantom: 'info',
}

const searchProductCd = ref('')
const searchStatus = ref('')
const currentPage = ref(1)
const pageSize = 20
const headerTotal = ref(0)
const headers = ref<BomHeader[]>([])
const loadingHeaders = ref(false)

const selectedHeader = ref<BomHeader | null>(null)
const treeData = ref<BomLine[]>([])
const loadingTree = ref(false)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const defaultLine = (): BomLinePayload => ({
  line_no: 10,
  component_type: 'material',
  component_product_cd: null,
  component_material_cd: null,
  qty_per: 1,
  uom: '個',
  scrap_rate: 0,
  consume_process_cd: null,
  consume_step_no: null,
  remarks: null,
})

const formData = reactive({
  parent_product_cd: '',
  bom_type: 'production',
  revision: '1',
  status: 'active',
  effective_from: null as string | null,
  effective_to: null as string | null,
  base_quantity: 1,
  uom: '個',
  remarks: null as string | null,
  lines: [] as BomLinePayload[],
})

async function loadHeaders() {
  loadingHeaders.value = true
  try {
    const params: Record<string, unknown> = { page: currentPage.value, limit: pageSize }
    if (searchProductCd.value) params.keyword = searchProductCd.value
    if (searchStatus.value) params.status = searchStatus.value
    const res = await getBomHeaders(params)
    const d = (res as any)?.data ?? res
    headers.value = d?.list ?? []
    headerTotal.value = d?.total ?? 0
  } catch {
    ElMessage.error('BOMヘッダの取得に失敗しました')
  } finally {
    loadingHeaders.value = false
  }
}

async function onHeaderSelect(row: BomHeader | null) {
  selectedHeader.value = row
  if (!row) { treeData.value = []; return }
  loadingTree.value = true
  try {
    const res = await getBomTree(row.id)
    const d = (res as any)?.data ?? res
    treeData.value = d?.tree ?? []
  } catch {
    ElMessage.error('BOMツリーの取得に失敗しました')
  } finally {
    loadingTree.value = false
  }
}

function resetSearch() {
  searchProductCd.value = ''
  searchStatus.value = ''
  currentPage.value = 1
  loadHeaders()
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  Object.assign(formData, {
    parent_product_cd: '',
    bom_type: 'production',
    revision: '1',
    status: 'active',
    effective_from: null,
    effective_to: null,
    base_quantity: 1,
    uom: '個',
    remarks: null,
    lines: [defaultLine()],
  })
  dialogVisible.value = true
}

function openEditDialog(row: BomHeader) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    parent_product_cd: row.parent_product_cd,
    bom_type: row.bom_type,
    revision: row.revision,
    status: row.status,
    effective_from: row.effective_from,
    effective_to: row.effective_to,
    base_quantity: row.base_quantity,
    uom: row.uom,
    remarks: row.remarks,
    lines: row.lines?.map(l => ({ ...l })) ?? [],
  })
  if (formData.lines.length === 0) {
    getBomTree(row.id).then(res => {
      const d = (res as any)?.data ?? res
      const flat: BomLinePayload[] = []
      function flatten(items: BomLine[]) {
        for (const it of items) {
          flat.push({ ...it })
          if (it.children?.length) flatten(it.children)
        }
      }
      flatten(d?.tree ?? [])
      formData.lines = flat.length ? flat : [defaultLine()]
    })
  }
  dialogVisible.value = true
}

function addLine() {
  const lastNo = formData.lines.length > 0 ? formData.lines[formData.lines.length - 1].line_no : 0
  const line = defaultLine()
  line.line_no = lastNo + 10
  formData.lines.push(line)
}

function removeLine(idx: number) {
  formData.lines.splice(idx, 1)
}

async function handleSave() {
  if (!formData.parent_product_cd) {
    ElMessage.warning('親製品CDを入力してください')
    return
  }
  saving.value = true
  try {
    if (isEditing.value && editingId.value) {
      await updateBomHeader(editingId.value, { ...formData })
      ElMessage.success('更新しました')
    } else {
      await createBomHeader({ ...formData })
      ElMessage.success('作成しました')
    }
    dialogVisible.value = false
    loadHeaders()
    if (selectedHeader.value) onHeaderSelect(selectedHeader.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteBomHeader(id)
    ElMessage.success('削除しました')
    if (selectedHeader.value?.id === id) {
      selectedHeader.value = null
      treeData.value = []
    }
    loadHeaders()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

onMounted(() => {
  loadHeaders()
})
</script>

<style scoped>
.bom-editor {
  padding: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.subtitle {
  color: #909399;
  font-size: 13px;
  margin-left: 12px;
}
.search-card {
  margin-bottom: 12px;
}
.search-card :deep(.el-card__body) {
  padding: 12px 16px;
}
.search-form .el-form-item {
  margin-bottom: 0;
}
.main-content {
  display: flex;
  gap: 12px;
}
.header-list-card {
  flex: 0 0 560px;
}
.tree-card {
  flex: 1;
  min-width: 0;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.empty-tree {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style>
