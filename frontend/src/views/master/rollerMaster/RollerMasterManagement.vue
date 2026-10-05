<template>
  <div class="rm-page rlm-modern pb-std">
    <div class="rm-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="rm-header-left">
        <div class="rm-title-row">
          <el-icon class="rm-title-icon" :size="20"><Histogram /></el-icon>
          <div>
            <h1 class="rm-title pb-hero-title">ローラーマスタ管理</h1>
            <p class="rm-subtitle pb-hero-desc">roller_master の登録・編集・照会を行います</p>
          </div>
        </div>
      </div>

      <div class="rm-header-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
        <div class="stat-card stat-total">
          <span class="stat-num">{{ total }}</span>
          <span class="stat-lbl">総件数</span>
        </div>
        <div class="stat-card stat-shown">
          <span class="stat-num">{{ rows.length }}</span>
          <span class="stat-lbl">表示中</span>
        </div>
        <div class="stat-card stat-manual">
          <span class="stat-num">{{ manualCount }}</span>
          <span class="stat-lbl">手動予定</span>
        </div>
        <div class="stat-card stat-linked">
          <span class="stat-num">{{ linkedCount }}</span>
          <span class="stat-lbl">設備紐付</span>
        </div>
      </div>

      <div class="rm-header-actions">
        <el-button v-if="canCreate" type="primary" :icon="Plus" size="small" class="rm-add-btn" @click="openDialog()">
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
        <el-table-column prop="roller_cd" label="ローラーCD" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="code-chip">{{ row.roller_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="roller_name" label="ローラー名" min-width="160" sortable show-overflow-tooltip />
        <el-table-column prop="exchange_freq_qty" label="交換頻度本数" width="150" align="center">
          <template #default="{ row }">
            <span v-if="row.exchange_freq_qty != null" class="freq-pill freq--qty">{{ row.exchange_freq_qty }}</span>
            <span v-else class="freq-empty">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="exchange_freq_month" label="交換頻度月" width="130" align="center">
          <template #default="{ row }">
            <span v-if="row.exchange_freq_month != null" class="freq-pill freq--month">{{ row.exchange_freq_month }}</span>
            <span v-else class="freq-empty">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="cleaning_freq_month" label="清掃頻度月" width="130" align="center">
          <template #default="{ row }">
            <span v-if="row.cleaning_freq_month != null" class="freq-pill freq--clean">{{ row.cleaning_freq_month }}</span>
            <span v-else class="freq-empty">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="区分" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.category" :class="['cat-tag', `cat--${categoryTone(row.category)}`]">{{ row.category }}</span>
            <span v-else class="freq-empty">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="machine_cd" label="設備CD" width="120" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.machine_cd" class="mc-chip">{{ row.machine_cd }}</span>
            <span v-else class="freq-empty">—</span>
          </template>
        </el-table-column>
        <el-table-column label="設備名" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ machineNameMap[row.machine_cd || ''] || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="schedule_mode" label="予定方式" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.schedule_mode === 'manual'" type="warning" size="small" effect="light">手動</el-tag>
            <el-tag v-else type="info" size="small" effect="plain">自動</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="備考" min-width="180" show-overflow-tooltip />
        <el-table-column label="更新日時" width="160" align="center" prop="updated_at">
          <template #default="{ row }">
            {{ formatDt(row.updated_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column v-if="canEdit || canDelete" label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEdit" type="primary" link size="small" :icon="Edit" @click="openDialog(row)">
              編集
            </el-button>
            <el-button v-if="canDelete" type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">
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

          <el-form-item label="予定方式" prop="schedule_mode">
            <el-select v-model="form.schedule_mode" style="width: 100%">
              <el-option label="自動予測" value="auto" />
              <el-option label="手動予定日" value="manual" />
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
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

defineOptions({ name: 'RollerMasterManagement' })

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

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

const manualCount = computed(() => rows.value.filter((r) => r.schedule_mode === 'manual').length)
const linkedCount = computed(() => rows.value.filter((r) => !!r.machine_cd).length)

const categoryTone = (category?: string | null) => {
  if (category === 'コットン機') return 'cotton'
  if (category === '金型') return 'mold'
  return 'other'
}

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
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
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

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
    schedule_mode: 'auto',
  }
}

const openDialog = async (row?: RollerMasterRow) => {
  if (row?.id) {
    if (!guardMasterOperation(canEdit)) return
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
      schedule_mode: row.schedule_mode === 'manual' ? 'manual' : 'auto',
    }
    dialogVisible.value = true
  } else {
    if (!guardMasterOperation(canCreate)) return
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
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
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
      schedule_mode: form.value.schedule_mode === 'manual' ? 'manual' : 'auto',
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
  if (!guardMasterOperation(canDelete)) return
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

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（ローラーマスタ / crimson→flame）
 * ============================================================ */
.rlm-modern {
  --hx-1: #450a0a;
  --hx-2: #991b1b;
  --hx-3: #dc2626;
  --hx-4: #f97316;
  --hx-deep: #7f1d1d;
  --hx-accent: #dc2626;
  --hx-soft: #fef2f2;
  --hx-soft2: #fff7ed;
  --hx-line: rgba(220, 38, 38, 0.16);
  background:
    radial-gradient(1200px 380px at 12% -8%, rgba(249, 115, 22, 0.1), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(220, 38, 38, 0.08), transparent 60%),
    linear-gradient(165deg, #fff7f5 0%, #fef2f2 40%, #f8fafc 100%);
}

.rlm-modern .rm-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 14px 18px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 38%, var(--hx-3) 72%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(153, 27, 27, 0.6),
    0 6px 14px -6px rgba(249, 115, 22, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.rlm-modern .rm-header > :not(.page-header-fx) {
  position: relative;
  z-index: 1;
}

.rlm-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.rlm-modern .rm-title-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 4px 0 rgba(69, 10, 10, 0.45),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  animation: rlmIconSpin 6s ease-in-out infinite;
}

.rlm-modern .rm-title {
  text-shadow: 0 2px 10px rgba(69, 10, 10, 0.35);
}

.rlm-modern .rm-header-stats {
  display: flex;
  gap: 8px;
  perspective: 650px;
  flex-wrap: wrap;
  margin-left: auto;
}

.rlm-modern .stat-card {
  --sc: #fecaca;
  position: relative;
  overflow: hidden;
  min-width: 78px;
  padding: 7px 12px 6px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(8px);
  box-shadow:
    0 3px 0 rgba(69, 10, 10, 0.35),
    0 10px 20px -10px rgba(0, 0, 0, 0.45);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease;
}

.rlm-modern .stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--sc);
}

.rlm-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.35), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.rlm-modern .stat-card:hover::after {
  opacity: 1;
}

.rlm-modern .stat-card:hover {
  box-shadow:
    0 5px 0 rgba(69, 10, 10, 0.4),
    0 16px 26px -12px rgba(0, 0, 0, 0.5);
}

.rlm-modern .stat-total { --sc: #fde68a; }
.rlm-modern .stat-shown { --sc: #fecaca; }
.rlm-modern .stat-manual { --sc: #fdba74; }
.rlm-modern .stat-linked { --sc: #a7f3d0; }

.rlm-modern .stat-num {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(69, 10, 10, 0.35);
}

.rlm-modern .stat-lbl {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
  letter-spacing: 0.04em;
}

.rlm-modern .rm-add-btn {
  --k-edge: #9a3412;
  --k-glow: rgba(249, 115, 22, 0.55);
  height: 32px;
  padding: 0 14px;
  border-radius: 10px;
  border: none;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #fb923c, #ea580c) !important;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.rlm-modern .rm-add-btn:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  background: linear-gradient(135deg, #fb923c, #ea580c) !important;
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.rlm-modern .rm-add-btn:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.rlm-modern .rm-toolbar,
.rlm-modern .rm-table-wrap {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 10px 24px -16px rgba(153, 27, 27, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.rlm-modern .rm-toolbar::before,
.rlm-modern .rm-table-wrap::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), var(--hx-4), #fbbf24);
}

.rlm-modern .rm-toolbar {
  padding-top: 12px;
}

.rlm-modern .rm-toolbar :deep(.el-input__wrapper),
.rlm-modern .rm-toolbar :deep(.el-select__wrapper) {
  border-radius: 10px;
  transition: box-shadow 0.2s ease;
}

.rlm-modern .rm-toolbar :deep(.el-input__wrapper.is-focus),
.rlm-modern .rm-toolbar :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--hx-3) inset, 0 0 0 3px rgba(220, 38, 38, 0.12);
}

.rlm-modern .rm-clear-btn {
  border-radius: 10px;
  padding: 0 12px;
  color: var(--hx-deep);
  background: var(--hx-soft);
  border: 1px solid rgba(220, 38, 38, 0.2);
  box-shadow: 0 2px 0 rgba(220, 38, 38, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rlm-modern .rm-clear-btn:hover {
  transform: translateY(-1px);
  color: var(--hx-deep);
  background: #fee2e2;
  box-shadow: 0 3px 0 rgba(220, 38, 38, 0.24);
}

.rlm-modern .rm-table-wrap {
  padding-top: 3px;
}

.rlm-modern .rm-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #7f1d1d, #991b1b) !important;
  color: #fff !important;
  border-bottom: 2px solid #f97316 !important;
  letter-spacing: 0.02em;
}

.rlm-modern .rm-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #fff1ec !important;
}

.rlm-modern .rm-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-3);
}

.rlm-modern .code-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 7px;
  font-family: 'Consolas', 'SFMono-Regular', monospace;
  font-weight: 700;
  font-size: 11px;
  color: #991b1b;
  background: linear-gradient(135deg, #fff1f2, #ffe4e6);
  box-shadow: inset 0 0 0 1px rgba(220, 38, 38, 0.25), 0 2px 0 rgba(220, 38, 38, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rlm-modern .rm-table :deep(tr:hover) .code-chip {
  transform: translateY(-1px);
  box-shadow: inset 0 0 0 1px rgba(220, 38, 38, 0.35), 0 3px 0 rgba(220, 38, 38, 0.24);
}

.rlm-modern .mc-chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-family: 'Consolas', 'SFMono-Regular', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  background: linear-gradient(180deg, #f8fafc, #e2e8f0);
  box-shadow: inset 0 0 0 1px rgba(100, 116, 139, 0.3), 0 1px 0 rgba(100, 116, 139, 0.25);
}

.rlm-modern .freq-pill {
  --ft: #ea580c;
  display: inline-block;
  min-width: 34px;
  padding: 1px 8px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  color: var(--ft);
  background: color-mix(in srgb, var(--ft) 10%, #fff);
  border: 1px solid color-mix(in srgb, var(--ft) 32%, #fff);
}

.rlm-modern .freq--qty { --ft: #dc2626; }
.rlm-modern .freq--month { --ft: #ea580c; }
.rlm-modern .freq--clean { --ft: #0891b2; }

.rlm-modern .freq-empty {
  color: #cbd5e1;
}

.rlm-modern .cat-tag {
  --ct: #64748b;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ct);
  background: color-mix(in srgb, var(--ct) 9%, #fff);
  border: 1px solid color-mix(in srgb, var(--ct) 35%, #fff);
}

.rlm-modern .cat-tag::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ct);
}

.rlm-modern .cat--cotton { --ct: #0d9488; }
.rlm-modern .cat--mold { --ct: #b45309; }
.rlm-modern .cat--other { --ct: #64748b; }

.rlm-modern .rm-result-bar b {
  color: var(--hx-3);
}

.rlm-modern .rm-result-bar :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4)) !important;
  color: #fff;
  box-shadow: 0 2px 0 var(--hx-deep);
}

.rlm-modern .rm-dialog :deep(.el-dialog__header) {
  background: linear-gradient(125deg, var(--hx-1), var(--hx-2) 45%, var(--hx-3) 80%, var(--hx-4));
}

.rlm-modern .rm-form :deep(.el-form-item__label) {
  color: var(--hx-deep);
}

.rlm-modern .rm-form :deep(.el-input__wrapper.is-focus),
.rlm-modern .rm-form :deep(.el-select__wrapper.is-focus) {
  border-color: var(--hx-3);
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.14);
}

.rlm-modern .rm-btn-save {
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4));
  box-shadow: 0 3px 0 var(--hx-deep), 0 10px 18px -8px rgba(249, 115, 22, 0.5);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rlm-modern .rm-btn-save:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4));
  box-shadow: 0 5px 0 var(--hx-deep), 0 14px 22px -8px rgba(249, 115, 22, 0.55);
}

.rlm-modern .rm-btn-save:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--hx-deep);
}

@keyframes rlmIconSpin {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) rotateZ(0deg);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) rotateZ(-8deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .rlm-modern .rm-title-icon {
    animation: none;
  }

  .rlm-modern .stat-card {
    transform: none;
  }
}
</style>

