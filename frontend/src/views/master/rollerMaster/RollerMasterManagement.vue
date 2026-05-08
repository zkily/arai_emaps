<template>
  <div class="rm-page">
    <div class="rm-header">
      <div class="rm-header-left">
        <div class="rm-title-row">
          <el-icon class="rm-title-icon" :size="20"><Histogram /></el-icon>
          <div>
            <h1 class="rm-title">ローラーマスタ管理</h1>
            <p class="rm-subtitle">roller_master の登録・編集・照会を行います</p>
          </div>
        </div>
      </div>

      <div class="rm-header-actions">
        <el-button type="primary" :icon="Plus" size="small" class="rm-add-btn" @click="openDialog()">
          新規登録
        </el-button>
      </div>
    </div>

    <div class="rm-toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="ローラーCD・ローラー名で検索…"
        clearable
        class="rm-search"
        size="small"
        @input="onKeywordInput"
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
        class="rm-filter-select"
        size="small"
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
        v-model="filters.category"
        placeholder="区分で絞込"
        clearable
        class="rm-filter-select"
        size="small"
        @change="onFilterChange"
      >
        <el-option v-for="c in categoryFilterOptions" :key="c.value" :label="c.label" :value="c.value" />
      </el-select>

      <div class="rm-toolbar-right">
        <el-button text size="small" class="rm-clear-btn" @click="clearFilters" :icon="RefreshLeft">
          クリア
        </el-button>
      </div>
    </div>

    <div class="rm-table-wrap">
      <el-table
        ref="tableRef"
        :data="rows"
        v-loading="loading"
        stripe
        border
        size="small"
        class="rm-table"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        height="calc(100vh - 240px)"
      >
        <el-table-column prop="roller_cd" label="ローラーCD" width="120" show-overflow-tooltip />
        <el-table-column prop="roller_name" label="ローラー名" min-width="160" sortable show-overflow-tooltip />
        <el-table-column prop="exchange_freq_qty" label="交換頻度本数" width="150" align="center">
          <template #default="{ row }">
            {{ row.exchange_freq_qty ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="exchange_freq_month" label="交換頻度月" width="130" align="center">
          <template #default="{ row }">
            {{ row.exchange_freq_month ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="cleaning_freq_month" label="清掃頻度月" width="130" align="center">
          <template #default="{ row }">
            {{ row.cleaning_freq_month ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="category" label="区分" width="120" show-overflow-tooltip />
        <el-table-column prop="machine_cd" label="設備CD" width="120" align="center" show-overflow-tooltip />
        <el-table-column label="設備名" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ machineNameMap[row.machine_cd || ''] || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="note" label="備考" min-width="180" show-overflow-tooltip />
        <el-table-column label="更新日時" width="160" align="center" prop="updated_at">
          <template #default="{ row }">
            {{ formatDt(row.updated_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :icon="Edit" @click="openDialog(row)">
              編集
            </el-button>
            <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="rm-result-bar">
        <span>表示 <b>{{ rows.length }}</b> / <b>{{ total }}</b> 件</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
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
      :title="isEdit ? 'ローラーマスタ 編集' : 'ローラーマスタ 新規登録'"
      width="680px"
      :close-on-click-modal="false"
      destroy-on-close
      class="rm-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        label-width="0"
        class="rm-form"
      >
        <div class="rm-dialog-grid">
          <el-form-item label="ローラーCD" prop="roller_cd">
            <el-input
              v-model="form.roller_cd"
              disabled
              :placeholder="isEdit ? '' : '自動採番（A001…）'"
            />
          </el-form-item>
          <el-form-item label="ローラー名" prop="roller_name">
            <el-input v-model="form.roller_name" placeholder="例: 成型ローラーA" />
          </el-form-item>

          <el-form-item label="交換頻度本数" prop="exchange_freq_qty">
            <el-input-number v-model="form.exchange_freq_qty" :min="0" :step="1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="交換頻度月" prop="exchange_freq_month">
            <el-input-number v-model="form.exchange_freq_month" :min="0" :step="1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="清掃頻度月" prop="cleaning_freq_month">
            <el-input-number v-model="form.cleaning_freq_month" :min="0" :step="1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="区分" prop="category">
            <el-select v-model="form.category" clearable filterable style="width: 100%">
              <el-option v-for="c in categoryFilterOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>

          <el-form-item label="設備CD" prop="machine_cd">
            <el-select v-model="form.machine_cd" clearable filterable style="width: 100%">
              <el-option
                v-for="m in formingMachineFormOptions"
                :key="m.value"
                :label="`${m.label} (${m.value})`"
                :value="m.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="備考" prop="note" class="rm-span-full">
            <el-input v-model="form.note" type="textarea" :rows="3" placeholder="備考を入力…" />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="rm-dialog-footer">
          <el-button class="rm-btn-cancel" @click="dialogVisible = false">
            キャンセル
          </el-button>
          <el-button type="primary" class="rm-btn-save" :loading="submitting" @click="submitForm">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Histogram, Search, RefreshLeft, Plus, Edit, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

import {
  fetchRollerMasterList,
  fetchNextRollerCd,
  createRollerMaster,
  updateRollerMaster,
  deleteRollerMaster,
  type RollerMasterRow,
} from '@/api/master/rollerMaster'

import { fetchMachines } from '@/api/master/machineMaster'

defineOptions({ name: 'RollerMasterManagement' })

const loading = ref(false)
const submitting = ref(false)

const rows = ref<RollerMasterRow[]>([])
const total = ref(0)

const currentPage = ref(1)
const pageSize = ref(20)

const filters = ref({ keyword: '', machine_cd: '', category: '' })
let keywordTimer: ReturnType<typeof setTimeout> | null = null

const machineOptions = ref<Array<{ label: string; value: string; machine_type?: string }>>([])
/** ツールバー「成型設備で絞込」は設備名（machine_name）文字列に「成型」を含むものだけ */
const isFormingMachineName = (label: string) => (label ?? '').includes('成型')

/** ツールバー「設備」フィルタは成型設備のみ表示 */
const formingMachineFilterOptions = computed(() =>
  machineOptions.value.filter((m) => isFormingMachineName(m.label))
)

/** 編集フォーム「設備CD」— 設備名に「成型」を含むもののみ。既存データが対象外の場合は当該1件だけ選択肢に追加 */
const formingMachineFormOptions = computed(() => {
  const base = formingMachineFilterOptions.value
  const cd = String(form.value.machine_cd ?? '').trim()
  if (!cd || base.some((m) => m.value === cd)) return base
  const lbl = machineNameMap.value[cd] || cd
  return [...base, { label: `${lbl} (${cd})`, value: cd }]
})

const categoryFilterOptions = [
  { label: 'コットン機', value: 'コットン機' },
  { label: '金型', value: '金型' },
  { label: 'その他', value: 'その他' },
]
const machineNameMap = computed(() => {
  const m: Record<string, string> = {}
  for (const x of machineOptions.value) m[x.value] = x.label
  return m
})

const headerCellStyle = () => ({
  background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
  color: '#fff',
  fontWeight: 600,
  fontSize: '12px',
  padding: '6px 10px',
  lineHeight: '1.3',
})

const cellStyle = () => ({ padding: '5px 8px', fontSize: '12px' })

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
    const res = await fetchMachines()
    const list = extractList(res)
    machineOptions.value = list.map((x: unknown) => {
      const o = x as Record<string, unknown>
      return {
        label: String(o.machine_name ?? ''),
        value: String(o.machine_cd ?? ''),
        machine_type: o.machine_type ? String(o.machine_type) : undefined,
      }
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
}

const loadData = async () => {
  loading.value = true
  try {
    const keyword = filters.value.keyword?.trim()
    const res = await fetchRollerMasterList({
      page: currentPage.value,
      pageSize: pageSize.value,
      ...(keyword ? { keyword } : {}),
      ...(filters.value.machine_cd ? { machine_cd: filters.value.machine_cd } : {}),
      ...(filters.value.category ? { category: filters.value.category } : {}),
    })

    const raw = res as Record<string, unknown>
    const data = (raw.success && raw.data ? raw.data : raw) as {
      list?: RollerMasterRow[]
      total?: number
    }
    rows.value = data.list || (raw.list as RollerMasterRow[]) || []
    total.value = typeof data.total === 'number' ? data.total : Number(raw.total) || 0
  } catch (e) {
    console.error(e)
    ElMessage.error('ローラーマスタ一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const onKeywordInput = () => {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => {
    currentPage.value = 1
    loadData()
  }, 350)
}

const onFilterChange = () => {
  currentPage.value = 1
  loadData()
}

const clearFilters = () => {
  filters.value.keyword = ''
  filters.value.machine_cd = ''
  filters.value.category = ''
  currentPage.value = 1
  loadData()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  loadData()
}

const tableRef = ref()

// dialog
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = ref<Partial<RollerMasterRow>>({})

const rules: FormRules = {
  roller_cd: [{ required: true, message: 'ローラーCDは必須です', trigger: 'blur' }],
  roller_name: [{ required: false }],
}

const resetForm = () => {
  form.value = {
    roller_cd: '',
    roller_name: '',
    exchange_freq_qty: null,
    exchange_freq_month: null,
    cleaning_freq_month: null,
    category: '',
    note: '',
    machine_cd: null,
  }
}

const openDialog = async (row?: RollerMasterRow) => {
  if (row?.id) {
    isEdit.value = true
    editingId.value = row.id
    form.value = {
      roller_cd: row.roller_cd ?? '',
      roller_name: row.roller_name ?? '',
      exchange_freq_qty: row.exchange_freq_qty ?? null,
      exchange_freq_month: row.exchange_freq_month ?? null,
      cleaning_freq_month: row.cleaning_freq_month ?? null,
      category: row.category ?? '',
      note: row.note ?? '',
      machine_cd: row.machine_cd ?? null,
    }
    dialogVisible.value = true
  } else {
    isEdit.value = false
    editingId.value = null
    resetForm()
    try {
      const res = await fetchNextRollerCd()
      const cd = (res?.roller_cd ?? '').trim()
      form.value.roller_cd = cd || 'A001'
    } catch (e) {
      console.error(e)
      form.value.roller_cd = 'A001'
      ElMessage.warning('ローラーCDの自動採番に失敗しました。保存前に再読込してください')
    }
    dialogVisible.value = true
  }
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload: Partial<RollerMasterRow> = {
      roller_cd: String(form.value.roller_cd ?? '').trim(),
      roller_name: (form.value.roller_name ?? '')?.trim?.() ? String(form.value.roller_name) : null,
      exchange_freq_qty: form.value.exchange_freq_qty ?? null,
      exchange_freq_month: form.value.exchange_freq_month ?? null,
      cleaning_freq_month: form.value.cleaning_freq_month ?? null,
      category: (form.value.category ?? '')?.trim?.() ? String(form.value.category) : null,
      note: (form.value.note ?? '') ?? null,
      machine_cd: (form.value.machine_cd ?? null) ? String(form.value.machine_cd) : null,
    }

    if (isEdit.value && editingId.value != null) {
      await updateRollerMaster(editingId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createRollerMaster(payload)
      ElMessage.success('登録しました')
    }

    dialogVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
    const ax = e as { response?: { data?: { detail?: string } } }
    const msg = ax.response?.data?.detail
    ElMessage.error(typeof msg === 'string' ? msg : '保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row: RollerMasterRow) => {
  if (!row.id) return
  try {
    await ElMessageBox.confirm(`ローラーCD ${row.roller_cd} を削除しますか？`, '確認', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteRollerMaster(row.id)
    ElMessage.success('削除しました')
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('削除に失敗しました')
  }
}

onMounted(async () => {
  await loadOptions()
  await loadData()
})
</script>

<style scoped>
.rm-page {
  padding: 12px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(165deg, #f0fdfa 0%, #ecfeff 35%, #f8fafc 100%);
  font-family: 'Inter', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
}

.rm-header {
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 55%, #0284c7 100%);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10px 30px rgba(13, 148, 136, 0.28);
  color: #fff;
  gap: 12px;
}

.rm-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rm-title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  flex-shrink: 0;
}

.rm-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.rm-subtitle {
  margin: 4px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
}

.rm-toolbar {
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(13, 148, 136, 0.12);
  box-shadow: 0 2px 10px rgba(15, 118, 110, 0.06);
  display: flex;
  align-items: center;
  gap: 10px;
}

.rm-search {
  flex: 1;
  min-width: 260px;
}

.rm-toolbar-right {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.rm-clear-btn {
  height: 32px;
  font-size: 12px;
}

.rm-batch-btn {
  height: 32px;
  border-radius: 10px;
}

.rm-table-wrap {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  padding: 0 0 10px;
  box-shadow: 0 2px 12px rgba(15, 118, 110, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.rm-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 12px 0;
  color: #64748b;
  font-size: 12px;
  flex-wrap: wrap;
}

.rm-dialog :deep(.el-dialog__header) {
  padding: 14px 18px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.95) 0%, rgba(8, 145, 178, 0.95) 55%, rgba(2, 132, 199, 0.95) 100%);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.rm-dialog :deep(.el-dialog__body) {
  padding: 10px 14px 8px;
}

.rm-form :deep(.el-form-item__label) {
  color: #0f766e;
  font-weight: 750;
  font-size: 12px;
  padding-bottom: 4px;
  line-height: 1.2;
}

.rm-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.rm-form :deep(.el-input__wrapper),
.rm-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  box-shadow: none;
}

.rm-form :deep(.el-input__wrapper.is-focus),
.rm-form :deep(.el-select__wrapper.is-focus) {
  border-color: #0891b2;
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.14);
}

.rm-form :deep(.el-textarea__inner) {
  border-radius: 10px;
}

.rm-dialog-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 12px;
}

.rm-span-full {
  grid-column: 1 / -1;
}

.rm-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.rm-btn-cancel {
  height: 32px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
}

.rm-btn-save {
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  border: none;
  box-shadow: 0 2px 10px rgba(13, 148, 136, 0.25);
}

.rm-filter-select {
  width: 210px;
}
</style>

