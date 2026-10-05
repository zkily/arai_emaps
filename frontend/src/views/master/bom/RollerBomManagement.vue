<template>
  <div class="rb-page rbm-modern pb-std">
    <div class="rb-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="rb-header-left">
        <div class="rb-title-row">
          <span class="rb-title-icon"><el-icon :size="20"><Histogram /></el-icon></span>
          <h1 class="rb-title pb-hero-title">ローラーBOM管理</h1>
        </div>
        <p class="rb-subtitle pb-hero-desc">ローラー・製品・設備の対応関係を登録・検索・一括操作します</p>
      </div>
      <div class="rb-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
        <div v-for="(s, i) in statItems" :key="s.l" :class="['rb-stat', `rb-stat--${i}`]">
          <span class="rb-stat-num">{{ s.n }}</span>
          <span class="rb-stat-lbl">{{ s.l }}</span>
        </div>
      </div>
    </div>

    <div class="rb-toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="ローラーCD・種類・製品CD・設備CDで検索…"
        clearable
        class="rb-search"
        @input="scheduleKeywordSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="filters.machine_cd"
        placeholder="成型設備で絞込"
        clearable
        filterable
        class="rb-filter"
        @change="onFilterChange"
      >
        <el-option
          v-for="m in formingMachineFilterOptions"
          :key="m.value"
          :label="`${m.label} (${m.value})`"
          :value="m.value"
        />
      </el-select>
      <el-select
        v-model="filters.product_cd"
        placeholder="製品で絞込"
        clearable
        filterable
        class="rb-filter"
        @change="onFilterChange"
      >
        <el-option
          v-for="p in productOptions"
          :key="p.value"
          :label="`${p.label} (${p.value})`"
          :value="p.value"
        />
      </el-select>
      <div class="rb-toolbar-actions">
        <el-button :icon="Refresh" class="rb-btn-ghost" @click="loadData">更新</el-button>
        <el-button :icon="RefreshLeft" class="rb-btn-ghost" @click="clearFilters">クリア</el-button>
        <el-button
          v-if="canDelete"
          type="danger"
          plain
          :disabled="!selectedIds.length"
          :icon="Delete"
          class="rb-btn-batch"
          @click="handleBatchDelete"
        >
          一括削除 ({{ selectedIds.length }})
        </el-button>
        <el-button v-if="canCreate" type="primary" :icon="Plus" class="rb-btn-add" @click="openDialog()">
          新規登録
        </el-button>
      </div>
    </div>

    <div class="rb-table-wrap">
      <el-table
        ref="tableRef"
        :data="rows"
        v-loading="loading"
        stripe
        border
        size="small"
        class="rb-table"
        :empty-text="'データがありません'"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        height="calc(100vh - 210px)"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="42" align="center" fixed />
        <!-- <el-table-column type="index" label="#" width="55" align="center" :index="indexMethod" fixed /> -->
        <el-table-column prop="roller_cd" label="ローラーCD" width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="rb-chip rb-chip--roller">{{ row.roller_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="roller_type" label="ローラー種類" width="150" sortable show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.roller_type" class="rb-type">{{ row.roller_type }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_cd" label="製品CD" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.product_cd" class="rb-chip rb-chip--product">{{ row.product_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column label="製品名" width="130" sortable show-overflow-tooltip >
          <template #default="{ row }">
            {{ productNameByCd[row.product_cd || ''] || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="machine_cd" label="設備CD" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.machine_cd" class="rb-chip rb-chip--machine">{{ row.machine_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column label="設備名" width="100" sortable show-overflow-tooltip>
          <template #default="{ row }">
            {{ machineNameMap[row.machine_cd || ''] || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="更新日時" width="150" align="center" sortable prop="updated_at">
          <template #default="{ row }">
            {{ formatDt(row.updated_at || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column v-if="canEdit || canDelete" label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEdit" type="primary" link size="small" :icon="Edit" @click="openDialog(row)">編集</el-button>
            <el-button v-if="canDelete" type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="rb-result-bar">
        <span>表示 <b>{{ rows.length }}</b> / <b>{{ total }}</b> 件</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          size="small"
          background
          @current-change="loadData"
          @size-change="handlePageSizeChange"
        />
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? 'ローラーBOM 編集' : 'ローラーBOM 新規登録'"
      width="520px"
      :close-on-click-modal="false"
      class="rb-dialog"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        label-width="0"
        size="default"
        class="rb-form"
      >
        <div class="rb-dialog-form-grid">
          <el-form-item label="ローラーCD" prop="roller_cd">
            <el-select
              v-model="form.roller_cd"
              placeholder="ローラーマスタから選択…"
              filterable
              clearable
              style="width: 100%"
              @change="onRollerCdFromMasterChange"
            >
              <el-option
                v-for="o in rollerCdFormOptions"
                :key="o.value"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="ローラー種類" prop="roller_type">
            <el-input
              v-model="form.roller_type"
              placeholder="ローラーCD選択で自動表示（ローラー名）"
              maxlength="100"
              readonly
              class="rb-input-readonly"
            />
          </el-form-item>

          <el-form-item label="製品" prop="product_cd">
            <el-select
              v-model="form.product_cd"
              placeholder="製品を選択…"
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="p in productFormOptions"
                :key="p.value"
                :label="`${p.label} (${p.value})`"
                :value="p.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="設備" prop="machine_cd">
            <el-select
              v-model="form.machine_cd"
              placeholder="設備を選択…"
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="m in machineOptions"
                :key="m.value"
                :label="`${m.label} (${m.value})`"
                :value="m.value"
              />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button class="rb-btn-cancel" @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" class="rb-btn-save" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Histogram,
  Search,
  Refresh,
  RefreshLeft,
  Plus,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  fetchRollerBomList,
  createRollerBom,
  updateRollerBom,
  deleteRollerBom,
  batchDeleteRollerBom,
  type RollerBomRow,
} from '@/api/master/rollerBomMaster'
import { fetchRollerMasterList, type RollerMasterRow } from '@/api/master/rollerMaster'
import { fetchMachines } from '@/api/master/machineMaster'
import { getProductList } from '@/api/master/productMaster'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

defineOptions({ name: 'RollerBomManagement' })

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const loading = ref(false)
const submitting = ref(false)
const rows = ref<RollerBomRow[]>([])
const total = ref(0)
const rollerDistinct = ref(0)
const productDistinct = ref(0)
const machineDistinct = ref(0)
const currentPage = ref(1)
const pageSize = ref(30)

const filters = ref({ keyword: '', machine_cd: '', product_cd: '' })

const machineOptions = ref<Array<{ label: string; value: string }>>([])
const productOptions = ref<Array<{ label: string; value: string }>>([])
/** 全製品の CD→名称（一覧表示用。下位桁が 1 以外も含む） */
const productNameByCd = ref<Record<string, string>>({})

/** ローラーマスタ（ローラーBOM フォーム用） */
const rollerMasterList = ref<RollerMasterRow[]>([])

const isFormingMachineLabel = (label: string, value: string) =>
  label.includes('成型') || value.includes('成型')

/** ツールバー「設備で絞込」は成型設備のみ（名称・CD に「成型」を含む） */
const formingMachineFilterOptions = computed(() =>
  machineOptions.value.filter((m) => isFormingMachineLabel(m.label, m.value))
)

const machineNameMap = computed(() => {
  const m: Record<string, string> = {}
  for (const x of machineOptions.value) m[x.value] = x.label
  return m
})

const statItems = computed(() => [
  { n: total.value, l: '総件数' },
  { n: rollerDistinct.value, l: 'ローラー種' },
  { n: machineDistinct.value, l: '設備数' },
  { n: productDistinct.value, l: '製品数' },
])

const headerCellStyle = () => ({
  background: '#eef8f7',
  color: '#0f766e',
  fontWeight: 600,
  fontSize: '11px',
  padding: '4px 8px',
  lineHeight: '1.3',
})
const cellStyle = () => ({ padding: '3px 8px', fontSize: '12px', lineHeight: '1.35' })

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.rb-stat')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.rb-stat').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.rb-stat').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

const tableRef = ref()
const selectedIds = ref<number[]>([])
const onSelectionChange = (sel: RollerBomRow[]) => {
  selectedIds.value = sel.map((r) => r.id!).filter(Boolean)
}

const indexMethod = (i: number) => (currentPage.value - 1) * pageSize.value + i + 1

const formatDt = (s?: string) => {
  if (!s) return '—'
  return s.replace('T', ' ').slice(0, 19)
}

const extractList = (response: unknown): unknown[] => {
  if (!response) return []
  const r = response as Record<string, unknown>
  if (Array.isArray(response)) return response as unknown[]
  if (Array.isArray(r.data)) return r.data as unknown[]
  if (Array.isArray(r.list)) return r.list as unknown[]
  const d = r.data as Record<string, unknown> | undefined
  if (d && Array.isArray(d.list)) return d.list as unknown[]
  return []
}

const loadOptions = async () => {
  try {
    const mr = (await fetchMachines()) as unknown
    const ml = extractList(mr)
    machineOptions.value = ml.map((x: unknown) => {
      const o = x as Record<string, unknown>
      return { label: String(o.machine_name ?? ''), value: String(o.machine_cd ?? '') }
    })
    if (
      filters.value.machine_cd &&
      !formingMachineFilterOptions.value.some((m) => m.value === filters.value.machine_cd)
    ) {
      filters.value.machine_cd = ''
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('設備マスタの取得に失敗しました')
  }
  try {
    const pr = await getProductList({ page: 1, pageSize: 10000 })
    const pl = extractList(pr)
    const _mapped = pl.map((x: unknown) => {
      const o = x as Record<string, unknown>
      return { label: String(o.product_name ?? ''), value: String(o.product_cd ?? '').trim() }
    })
    const names: Record<string, string> = {}
    for (const p of _mapped) {
      if (p.value) names[p.value] = p.label
    }
    productNameByCd.value = names
    productOptions.value = _mapped
      .filter((p) => p.value.length > 0 && p.value.endsWith('1'))
      .sort((a, b) => a.label.localeCompare(b.label, 'ja', { sensitivity: 'base' }))
    if (
      filters.value.product_cd &&
      !productOptions.value.some((p) => p.value === filters.value.product_cd)
    ) {
      filters.value.product_cd = ''
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('製品マスタの取得に失敗しました')
  }
  try {
    const rr = await fetchRollerMasterList()
    const raw = rr as Record<string, unknown>
    const d = raw.data as { list?: RollerMasterRow[] } | undefined
    rollerMasterList.value =
      d?.list || (raw.list as RollerMasterRow[]) || []
  } catch (e) {
    console.error(e)
    ElMessage.error('ローラーマスタの取得に失敗しました')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const kw = filters.value.keyword?.trim()
    const res = await fetchRollerBomList({
      page: currentPage.value,
      pageSize: pageSize.value,
      ...(kw ? { keyword: kw } : {}),
      ...(filters.value.machine_cd ? { machine_cd: filters.value.machine_cd } : {}),
      ...(filters.value.product_cd ? { product_cd: filters.value.product_cd } : {}),
    })
    const raw = res as Record<string, unknown>
    const data = (raw.success && raw.data ? raw.data : raw) as {
      list?: RollerBomRow[]
      total?: number
      roller_distinct_count?: number
      product_distinct_count?: number
      machine_distinct_count?: number
    }
    rows.value = data.list || (raw.list as RollerBomRow[]) || []
    total.value = typeof data.total === 'number' ? data.total : Number(raw.total) || 0
    rollerDistinct.value = Number(data.roller_distinct_count ?? raw.roller_distinct_count ?? 0)
    productDistinct.value = Number(data.product_distinct_count ?? raw.product_distinct_count ?? 0)
    machineDistinct.value = Number(data.machine_distinct_count ?? raw.machine_distinct_count ?? 0)
  } catch (e) {
    console.error(e)
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

let kwTimer: ReturnType<typeof setTimeout> | null = null
const scheduleKeywordSearch = () => {
  if (kwTimer) clearTimeout(kwTimer)
  kwTimer = setTimeout(() => {
    currentPage.value = 1
    loadData()
  }, 320)
}

const onFilterChange = () => {
  currentPage.value = 1
  loadData()
}

const clearFilters = () => {
  filters.value = { keyword: '', machine_cd: '', product_cd: '' }
  currentPage.value = 1
  loadData()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  loadData()
}

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = ref({
  roller_cd: '',
  roller_type: '',
  product_cd: '',
  machine_cd: '',
})

/** 編集時：マスタに無いローラーCDも下に出す */
const rollerCdFormOptions = computed(() => {
  const base = rollerMasterList.value
    .map((r) => {
      const cd = (r.roller_cd ?? '').trim()
      if (!cd) return null
      const name = r.roller_name ?? ''
      return {
        value: cd,
        label: name ? `${name} (${cd})` : cd,
      }
    })
    .filter(Boolean) as Array<{ value: string; label: string }>
  const cd = (form.value.roller_cd || '').trim()
  if (!cd || base.some((o) => o.value === cd)) return base
  const hint = form.value.roller_type || cd
  return [...base, { value: cd, label: `${hint} (${cd}) ※マスタ未登録` }]
})

const onRollerCdFromMasterChange = (val: string | undefined) => {
  if (!val) {
    form.value.roller_type = ''
    return
  }
  const r = rollerMasterList.value.find((x) => x.roller_cd === val)
  if (r) {
    form.value.roller_type = r.roller_name ?? ''
  }
}

/** 編集時：マスタに無い製品CDも選択肢に含める */
const productFormOptions = computed(() => {
  const base = productOptions.value
  const cd = (form.value.product_cd || '').trim()
  if (!cd || base.some((p) => p.value === cd)) return base
  const lbl = productNameByCd.value[cd] || cd
  return [...base, { label: `${lbl} (${cd})`, value: cd }]
})

const rules: FormRules = {
  roller_cd: [{ required: true, message: 'ローラーCDを入力してください', trigger: 'blur' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  machine_cd: [{ required: true, message: '設備を選択してください', trigger: 'change' }],
}

const openDialog = (row?: RollerBomRow) => {
  if (row?.id) {
    if (!guardMasterOperation(canEdit)) return
    isEdit.value = true
    editingId.value = row.id
    form.value = {
      roller_cd: row.roller_cd || '',
      roller_type: (row.roller_type as string) || '',
      product_cd: row.product_cd || '',
      machine_cd: row.machine_cd || '',
    }
  } else {
    if (!guardMasterOperation(canCreate)) return
    isEdit.value = false
    editingId.value = null
    form.value = { roller_cd: '', roller_type: '', product_cd: '', machine_cd: '' }
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload: Partial<RollerBomRow> = {
      roller_cd: form.value.roller_cd.trim(),
      roller_type: form.value.roller_type?.trim() || undefined,
      product_cd: form.value.product_cd,
      machine_cd: form.value.machine_cd,
    }
    if (isEdit.value && editingId.value != null) {
      await updateRollerBom(editingId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createRollerBom(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    console.error(e)
    const ax = e as { response?: { data?: { detail?: string } } }
    const msg = ax.response?.data?.detail
    ElMessage.error(typeof msg === 'string' ? msg : '保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row: RollerBomRow) => {
  if (!guardMasterOperation(canDelete)) return
  if (!row.id) return
  try {
    await ElMessageBox.confirm('この行を削除しますか？', '確認', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteRollerBom(row.id)
    ElMessage.success('削除しました')
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('削除に失敗しました')
  }
}

const handleBatchDelete = async () => {
  if (!guardMasterOperation(canDelete)) return
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`選択した ${selectedIds.value.length} 件を削除しますか？`, '確認', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await batchDeleteRollerBom(selectedIds.value)
    ElMessage.success('削除しました')
    selectedIds.value = []
    tableRef.value?.clearSelection?.()
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('一括削除に失敗しました')
  }
}

onMounted(async () => {
  await loadOptions()
  await loadData()
})
</script>

<style scoped>
.rb-page {
  padding: 10px 12px 12px;
  min-height: 100vh;
  background: linear-gradient(165deg, #f0fdfa 0%, #ecfeff 35%, #f8fafc 100%);
  font-family: 'Inter', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rb-header {
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 55%, #0284c7 100%);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: #fff;
  box-shadow: 0 4px 18px rgba(13, 148, 136, 0.28);
}

.rb-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rb-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 8px;
}

.rb-title {
  font-size: 17px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.02em;
}

.rb-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.88);
  margin: 4px 0 0 38px;
  line-height: 1.35;
}

.rb-stats {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.rb-stat {
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  padding: 6px 12px;
  text-align: center;
  min-width: 56px;
}

.rb-stat-num {
  display: block;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.1;
}

.rb-stat-lbl {
  display: block;
  font-size: 9px;
  color: rgba(255, 255, 255, 0.88);
  margin-top: 2px;
}

.rb-toolbar {
  background: #fff;
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(13, 148, 136, 0.12);
  box-shadow: 0 2px 8px rgba(15, 118, 110, 0.06);
}

.rb-search {
  flex: 1;
  min-width: 200px;
  max-width: 380px;
}

.rb-search :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  height: 32px;
}

.rb-filter {
  width: 200px;
}

.rb-filter :deep(.el-input__wrapper) {
  height: 32px;
  border-radius: 8px;
}

.rb-toolbar-actions {
  display: flex;
  gap: 6px;
  margin-left: auto;
  flex-wrap: wrap;
}

.rb-btn-ghost {
  height: 32px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.rb-btn-batch {
  height: 32px;
  font-size: 12px;
  border-radius: 8px;
}

.rb-btn-add {
  height: 32px;
  font-size: 12px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  border: none;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.35);
}

.rb-table-wrap {
  background: #fff;
  border-radius: 10px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  padding: 0 0 8px;
  box-shadow: 0 2px 12px rgba(15, 118, 110, 0.06);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.rb-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 12px 0;
  font-size: 12px;
  color: #64748b;
}

.rb-dialog :deep(.el-dialog__header) {
  padding: 14px 18px 12px;
  margin: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.95) 0%, rgba(8, 145, 178, 0.95) 55%, rgba(2, 132, 199, 0.95) 100%);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.rb-dialog :deep(.el-dialog__body) {
  padding: 14px 18px 10px;
}

.rb-dialog-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 14px;
}

.rb-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.rb-form :deep(.el-form-item__label) {
  color: #0f766e;
  font-weight: 650;
  padding-bottom: 6px;
}

.rb-form :deep(.el-input__wrapper),
.rb-form :deep(.el-select__wrapper) {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  box-shadow: none;
}

.rb-form :deep(.el-input__wrapper:focus-within),
.rb-form :deep(.el-select__wrapper:focus-within) {
  border-color: #0891b2;
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.14);
}

.rb-dialog :deep(.el-dialog__footer) {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 6px;
}

.rb-btn-cancel {
  height: 34px;
  border-radius: 12px;
  font-size: 12px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.rb-btn-save {
  height: 34px;
  border-radius: 12px;
  font-size: 12px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  border: none;
  box-shadow: 0 2px 10px rgba(13, 148, 136, 0.25);
}

.rb-input-readonly :deep(.el-input__wrapper) {
  background-color: #f8fafc;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（ローラーBOM / graphite→copper）
 * ============================================================ */
.rbm-modern {
  --hx-1: #1c1917;
  --hx-2: #44403c;
  --hx-3: #9a3412;
  --hx-4: #ea580c;
  --hx-deep: #7c2d12;
  --hx-soft: #fff7ed;
  --hx-line: rgba(154, 52, 18, 0.16);
  background:
    radial-gradient(1100px 360px at 10% -10%, rgba(234, 88, 12, 0.08), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(120, 113, 108, 0.1), transparent 60%),
    linear-gradient(165deg, #faf8f6 0%, #f7f3ef 40%, #f8fafc 100%);
}

.rbm-modern .rb-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 14px 18px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 38%, var(--hx-3) 72%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(68, 64, 60, 0.65),
    0 6px 14px -6px rgba(234, 88, 12, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.rbm-modern .rb-header > :not(.page-header-fx) {
  position: relative;
  z-index: 1;
}

.rbm-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.rbm-modern .rb-title-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.32);
  box-shadow:
    0 4px 0 rgba(28, 25, 23, 0.55),
    0 10px 18px -6px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  animation: rbmIconRoll 6s ease-in-out infinite;
}

.rbm-modern .rb-title {
  font-size: 18px;
  font-weight: 800;
  text-shadow: 0 2px 10px rgba(28, 25, 23, 0.4);
}

.rbm-modern .rb-subtitle {
  margin-left: 48px;
}

.rbm-modern .rb-stats {
  gap: 8px;
  perspective: 650px;
  flex-wrap: wrap;
}

.rbm-modern .rb-stat {
  --sc: #fed7aa;
  position: relative;
  overflow: hidden;
  min-width: 66px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.07));
  border: 1px solid rgba(255, 255, 255, 0.26);
  backdrop-filter: blur(8px);
  box-shadow:
    0 3px 0 rgba(28, 25, 23, 0.45),
    0 10px 20px -10px rgba(0, 0, 0, 0.5);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease;
}

.rbm-modern .rb-stat::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--sc);
}

.rbm-modern .rb-stat::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.35), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.rbm-modern .rb-stat:hover {
  box-shadow:
    0 5px 0 rgba(28, 25, 23, 0.5),
    0 16px 26px -12px rgba(0, 0, 0, 0.55);
}

.rbm-modern .rb-stat:hover::after {
  opacity: 1;
}

.rbm-modern .rb-stat--0 { --sc: #fde68a; }
.rbm-modern .rb-stat--1 { --sc: #fdba74; }
.rbm-modern .rb-stat--2 { --sc: #86efac; }
.rbm-modern .rb-stat--3 { --sc: #93c5fd; }

.rbm-modern .rb-stat-num {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(28, 25, 23, 0.4);
}

.rbm-modern .rb-toolbar,
.rbm-modern .rb-table-wrap {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 10px 24px -16px rgba(124, 45, 18, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.rbm-modern .rb-toolbar::before,
.rbm-modern .rb-table-wrap::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), var(--hx-4), #fbbf24);
}

.rbm-modern .rb-toolbar {
  padding-top: 11px;
}

.rbm-modern .rb-table-wrap {
  padding-top: 3px;
}

.rbm-modern .rb-toolbar :deep(.el-input__wrapper.is-focus),
.rbm-modern .rb-toolbar :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--hx-4) inset, 0 0 0 3px rgba(234, 88, 12, 0.12);
}

.rbm-modern .rb-btn-ghost {
  color: var(--hx-deep);
  background: var(--hx-soft);
  border-color: rgba(234, 88, 12, 0.22);
  box-shadow: 0 2px 0 rgba(154, 52, 18, 0.2);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rbm-modern .rb-btn-ghost:hover {
  transform: translateY(-1px);
  color: var(--hx-deep);
  background: #ffedd5;
  border-color: rgba(234, 88, 12, 0.3);
  box-shadow: 0 3px 0 rgba(154, 52, 18, 0.26);
}

.rbm-modern .rb-btn-batch:not(.is-disabled) {
  box-shadow: 0 2px 0 rgba(220, 38, 38, 0.3);
}

.rbm-modern .rb-btn-add {
  --k-edge: #7c2d12;
  --k-glow: rgba(234, 88, 12, 0.5);
  font-weight: 700;
  background: linear-gradient(135deg, #f97316, #c2410c);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.rbm-modern .rb-btn-add:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  background: linear-gradient(135deg, #f97316, #c2410c);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.rbm-modern .rb-btn-add:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge);
}

.rbm-modern .rb-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #292524, #44403c) !important;
  color: #fff !important;
  border-bottom: 2px solid var(--hx-4) !important;
}

.rbm-modern .rb-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #fff7ed !important;
}

.rbm-modern .rb-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-4);
}

.rbm-modern .rb-chip {
  --cc: #9a3412;
  display: inline-block;
  padding: 1px 8px;
  border-radius: 6px;
  font-family: 'Consolas', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--cc);
  background: color-mix(in srgb, var(--cc) 9%, #fff);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--cc) 32%, #fff), 0 2px 0 color-mix(in srgb, var(--cc) 25%, #fff);
  transition: transform 0.15s ease;
}

.rbm-modern .rb-chip--roller { --cc: #c2410c; }
.rbm-modern .rb-chip--product { --cc: #1d4ed8; }
.rbm-modern .rb-chip--machine { --cc: #047857; }

.rbm-modern .rb-table :deep(tr:hover) .rb-chip {
  transform: translateY(-1px);
}

.rbm-modern .rb-type {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-weight: 600;
  color: #44403c;
}

.rbm-modern .rb-type::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fdba74, #9a3412);
  box-shadow: 0 1px 2px rgba(124, 45, 18, 0.4);
}

.rbm-modern .rb-result-bar b {
  color: var(--hx-4);
}

.rbm-modern .rb-result-bar :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4)) !important;
  color: #fff;
  box-shadow: 0 2px 0 var(--hx-deep);
}

.rbm-modern .rb-dialog :deep(.el-dialog__header) {
  background: linear-gradient(125deg, var(--hx-1), var(--hx-2) 40%, var(--hx-3) 75%, var(--hx-4));
}

.rbm-modern .rb-form :deep(.el-form-item__label) {
  color: var(--hx-deep);
}

.rbm-modern .rb-form :deep(.el-input__wrapper:focus-within),
.rbm-modern .rb-form :deep(.el-select__wrapper:focus-within) {
  border-color: var(--hx-4);
  box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.14);
}

.rbm-modern .rb-btn-save {
  background: linear-gradient(135deg, #f97316, #c2410c);
  box-shadow: 0 3px 0 var(--hx-deep), 0 10px 18px -8px rgba(234, 88, 12, 0.5);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rbm-modern .rb-btn-save:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #f97316, #c2410c);
  box-shadow: 0 5px 0 var(--hx-deep), 0 14px 22px -8px rgba(234, 88, 12, 0.55);
}

.rbm-modern .rb-btn-save:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--hx-deep);
}

@keyframes rbmIconRoll {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg);
  }
  50% {
    transform: perspective(300px) rotateX(-14deg) rotateY(18deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .rbm-modern .rb-title-icon {
    animation: none;
  }

  .rbm-modern .rb-stat {
    transform: none;
  }
}
</style>