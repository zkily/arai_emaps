<template>
  <div class="pc-page">
    <!-- Header -->
    <div class="pc-header">
      <div class="pc-header-glow" aria-hidden="true" />
      <div class="pc-title-row">
        <div class="pc-title-icon">
          <el-icon :size="22"><Warning /></el-icon>
        </div>
        <div>
          <h1 class="pc-title">生産注意事項</h1>
          <p class="pc-subtitle">工程別に生産時の注意・ヒントを管理（例：検査時新聞紙投入）</p>
        </div>
      </div>
      <div class="pc-header-stats">
        <div class="pc-stat-card pc-stat-card--total">
          <div class="pc-stat-icon"><el-icon><Collection /></el-icon></div>
          <div class="pc-stat-body">
            <span class="pc-stat-value">{{ rows.length }}</span>
            <span class="pc-stat-label">全件</span>
          </div>
        </div>
        <div class="pc-stat-card pc-stat-card--ok">
          <div class="pc-stat-icon"><el-icon><CircleCheck /></el-icon></div>
          <div class="pc-stat-body">
            <span class="pc-stat-value">{{ activeCount }}</span>
            <span class="pc-stat-label">有効</span>
          </div>
        </div>
        <div class="pc-stat-card pc-stat-card--mute">
          <div class="pc-stat-icon"><el-icon><Remove /></el-icon></div>
          <div class="pc-stat-body">
            <span class="pc-stat-value">{{ inactiveCount }}</span>
            <span class="pc-stat-label">無効</span>
          </div>
        </div>
        <div class="pc-stat-card pc-stat-card--view">
          <div class="pc-stat-icon"><el-icon><View /></el-icon></div>
          <div class="pc-stat-body">
            <span class="pc-stat-value">{{ filteredRows.length }}</span>
            <span class="pc-stat-label">表示</span>
          </div>
        </div>
      </div>
      <div class="pc-header-actions">
        <el-button size="small" class="pc-head-btn pc-btn-refresh" :loading="loading" @click="loadList">
          <el-icon><Refresh /></el-icon>
          再読込
        </el-button>
        <el-button
          v-if="canCreate"
          size="small"
          class="pc-head-btn pc-btn-add"
          @click="openDialog()"
        >
          <el-icon><Plus /></el-icon>
          追加
        </el-button>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="pc-toolbar">
      <div class="pc-process-tabs">
        <button
          v-for="p in processTabs"
          :key="p.code"
          type="button"
          class="pc-process-tab"
          :class="{ 'is-active': processFilter === p.code }"
          :style="processTabStyle(p.code)"
          @click="processFilter = p.code"
        >
          <span v-if="p.code !== 'all'" class="pc-tab-dot" :style="{ background: processColor(p.code) }" />
          {{ p.label }}
          <span class="pc-count">{{ processCount(p.code) }}</span>
        </button>
      </div>
      <div class="pc-toolbar-row">
        <div class="pc-scope-switch">
          <button
            v-for="s in scopeOptions"
            :key="s.value"
            type="button"
            class="pc-scope-btn"
            :class="[`pc-scope-btn--${s.value}`, { 'is-active': scopeFilter === s.value }]"
            @click="scopeFilter = s.value"
          >
            {{ s.label }}
          </button>
        </div>
        <el-input
          v-model="keyword"
          placeholder="製品CD・製品名・注意内容で検索…"
          clearable
          size="small"
          class="pc-search"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <label class="pc-check">
          <el-checkbox v-model="includeInactive" />
          <span>無効も表示</span>
        </label>
        <el-button size="small" class="pc-btn-reset" @click="resetFilters">リセット</el-button>
      </div>
    </div>

    <!-- Table panel -->
    <div v-loading="loading" class="pc-panel">
      <div class="pc-panel-bar">
        <div class="pc-panel-title">
          <span class="pc-badge">一覧</span>
          <span>双クリックで編集 · 工程色で対象を識別</span>
        </div>
        <div class="pc-legend">
          <span v-for="p in processes" :key="p.code" class="pc-legend-item">
            <i :style="{ background: p.color }" />{{ p.label.replace('工程', '') }}
          </span>
        </div>
      </div>
      <el-table
        :data="filteredRows"
        size="small"
        border
        stripe
        height="calc(100vh - 318px)"
        class="pc-table"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        :row-class-name="rowClassName"
        empty-text="注意事項がありません。「追加」から登録してください"
        @row-dblclick="(row: ProcessCaution) => openDialog(row)"
      >
        <el-table-column label="工程" width="124" sortable :sort-method="sortByProcess">
          <template #default="{ row }">
            <span class="pc-proc" :style="processPillStyle(row.process_code)">
              <i class="pc-proc-dot" :style="{ background: processColor(row.process_code) }" />
              {{ processLabel(row.process_code) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="対象製品" min-width="200" show-overflow-tooltip sortable :sort-method="sortByProduct">
          <template #default="{ row }">
            <span v-if="!row.product_cd" class="pc-common-pill">
              <el-icon :size="12"><Share /></el-icon>
              工程共通
            </span>
            <div v-else class="pc-product">
              <b class="pc-cd">{{ row.product_cd }}</b>
              <span v-if="row.product_name" class="pc-name">{{ row.product_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="caution_text" label="注意事項" min-width="280" show-overflow-tooltip sortable>
          <template #default="{ row }">
            <span class="pc-caution" :style="cautionStyle(row.process_code)">
              <el-icon :size="13" class="pc-caution-ico"><WarningFilled /></el-icon>
              {{ row.caution_text }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="並び" prop="sort_order" width="72" align="center" sortable>
          <template #default="{ row }">
            <span class="pc-sort">{{ row.sort_order }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状態" width="92" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              size="small"
              inline-prompt
              active-text="有"
              inactive-text="無"
              :disabled="!canEdit || togglingId === row.id"
              @change="(v: string | number | boolean) => toggleActive(row, !!v)"
            />
          </template>
        </el-table-column>
        <el-table-column label="更新" width="148" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="pc-meta">
              <span>{{ formatDate(row.updated_at) }}</span>
              <span v-if="row.updated_by" class="pc-meta-by">{{ row.updated_by }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="128" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="canEdit"
              type="primary"
              link
              size="small"
              class="pc-op-edit"
              @click="openDialog(row)"
            >
              編集
            </el-button>
            <el-button
              v-if="canDelete"
              type="danger"
              link
              size="small"
              @click="removeRow(row)"
            >
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      width="600px"
      destroy-on-close
      :close-on-click-modal="false"
      class="pc-dialog"
      align-center
      @closed="onDialogClosed"
    >
      <template #header>
        <div class="pc-dlg-head">
          <div class="pc-dlg-icon" :style="{ background: processColor(form.process_code) }">
            <el-icon :size="18"><WarningFilled /></el-icon>
          </div>
          <div>
            <div class="pc-dlg-title">{{ editingId ? '生産注意事項の編集' : '生産注意事項の追加' }}</div>
            <div class="pc-dlg-sub">{{ processLabel(form.process_code) }}向けの注意事項を登録</div>
          </div>
        </div>
      </template>

      <div class="pc-dlg-body">
        <div class="pc-process-picker">
          <button
            v-for="p in processes"
            :key="p.code"
            type="button"
            class="pc-pick"
            :class="{ 'is-active': form.process_code === p.code }"
            :style="form.process_code === p.code
              ? { background: p.color, borderColor: p.color, color: '#fff' }
              : { borderColor: `${p.color}55`, color: p.color }"
            @click="form.process_code = p.code"
          >
            <i :style="{ background: form.process_code === p.code ? '#fff' : p.color }" />
            {{ p.label.replace('工程', '') }}
          </button>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          label-position="top"
          size="default"
          class="pc-form"
          @submit.prevent
        >
          <el-form-item label="対象製品" class="pc-form-item">
            <el-select
              v-model="form.product_cd"
              filterable
              clearable
              remote
              :remote-method="filterProducts"
              placeholder="空欄＝工程共通 / 製品CD・製品名で検索"
              style="width: 100%"
              :loading="productOptionsLoading"
              @change="onProductChange"
              @visible-change="(open: boolean) => open && void loadProductOptions()"
            >
              <el-option
                v-for="p in filteredProductOptions"
                :key="p.product_cd"
                :label="`${p.product_cd} ${p.product_name}`"
                :value="p.product_cd"
              />
            </el-select>
            <div class="pc-form-hint">
              <el-icon :size="12"><InfoFilled /></el-icon>
              未選択の場合は当該工程の全製品に表示されます
            </div>
          </el-form-item>

          <el-form-item v-if="form.product_name" label="製品名" class="pc-form-item">
            <el-input :model-value="form.product_name" disabled />
          </el-form-item>

          <el-form-item label="注意事項" prop="caution_text" required class="pc-form-item">
            <el-input
              v-model="form.caution_text"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="例：検査時新聞紙投入"
              class="pc-caution-input"
            />
          </el-form-item>

          <div class="pc-form-row">
            <el-form-item label="並び順" class="pc-form-item">
              <el-input-number
                v-model="form.sort_order"
                :min="0"
                :max="99999"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="状態" class="pc-form-item">
              <div class="pc-active-box" :class="{ 'is-on': form.is_active }">
                <el-switch v-model="form.is_active" inline-prompt active-text="有効" inactive-text="無効" />
                <span>{{ form.is_active ? '現場に表示' : '非表示' }}</span>
              </div>
            </el-form-item>
          </div>
        </el-form>

        <div class="pc-preview" :style="{ borderColor: `${processColor(form.process_code)}44` }">
          <div class="pc-preview-label">プレビュー</div>
          <div class="pc-preview-card" :style="cautionStyle(form.process_code)">
            <el-icon :size="14"><WarningFilled /></el-icon>
            <div>
              <div class="pc-preview-proc">{{ processLabel(form.process_code) }}
                <span class="pc-preview-scope">{{ form.product_cd ? form.product_cd : '工程共通' }}</span>
              </div>
              <div class="pc-preview-text">{{ form.caution_text.trim() || '（注意事項を入力）' }}</div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="pc-dlg-footer">
          <el-button class="pc-btn-cancel" @click="dialogVisible = false">キャンセル</el-button>
          <el-button class="pc-btn-save" :loading="saving" @click="saveRow">
            <el-icon><Select /></el-icon>
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  CircleCheck,
  Collection,
  InfoFilled,
  Plus,
  Refresh,
  Remove,
  Search,
  Select,
  Share,
  View,
  Warning,
  WarningFilled,
} from '@element-plus/icons-vue'
import { getProductList } from '@/api/master/productMaster'
import {
  createProcessCaution,
  deleteProcessCaution,
  fetchProcessCautions,
  setProcessCautionActive,
  updateProcessCaution,
  type CautionScope,
  type ProcessCaution,
  type ProcessCautionCode,
} from '@/api/erp/quality/processCaution'
import { useQualityOperationPermission } from '@/composables/useQualityOperationPermission'
import { guardQualityOperation } from '@/utils/qualityOperationGuard'
import type { Product } from '@/types/master'

defineOptions({ name: 'ProcessCautionManagement' })

const { canCreate, canEdit, canDelete } = useQualityOperationPermission()

const processes: Array<{ code: ProcessCautionCode; label: string; color: string }> = [
  { code: 'cutting', label: '切断工程', color: '#0f766e' },
  { code: 'chamfering', label: '面取工程', color: '#0369a1' },
  { code: 'forming', label: '成型工程', color: '#1d4ed8' },
  { code: 'welding', label: '溶接工程', color: '#b45309' },
  { code: 'plating', label: 'メッキ工程', color: '#6d28d9' },
  { code: 'inspection', label: '検査工程', color: '#f43f5e' },
]

const scopeOptions: Array<{ value: CautionScope; label: string }> = [
  { value: 'all', label: 'すべて' },
  { value: 'product', label: '製品指定' },
  { value: 'common', label: '工程共通' },
]

const processOrder = processes.map((p) => p.code)
const processTabs = [{ code: 'all' as const, label: 'すべて' }, ...processes.map((p) => ({ code: p.code, label: p.label }))]

const loading = ref(false)
const saving = ref(false)
const togglingId = ref<number | null>(null)
const keyword = ref('')
const includeInactive = ref(false)
const scopeFilter = ref<CautionScope>('all')
const processFilter = ref<'all' | ProcessCautionCode>('all')
const rows = ref<ProcessCaution[]>([])
const productOptions = ref<Product[]>([])
const productFilterKw = ref('')
const productOptionsLoading = ref(false)

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  process_code: 'inspection' as ProcessCautionCode,
  product_cd: '' as string,
  product_name: '' as string,
  caution_text: '',
  is_active: true,
  sort_order: 0,
})

const formRules: FormRules = {
  caution_text: [{ required: true, message: '注意事項を入力してください', trigger: 'blur' }],
}

const processLabel = (code: string) => processes.find((p) => p.code === code)?.label ?? code
const processColor = (code: string) => processes.find((p) => p.code === code)?.color ?? '#64748b'

const processTabStyle = (code: string) => {
  if (processFilter.value !== code) return {}
  if (code === 'all') return { background: '#1e3a5f', borderColor: '#1e3a5f', color: '#fff' }
  const c = processColor(code)
  return { background: c, borderColor: c, color: '#fff' }
}

const processPillStyle = (code: string) => {
  const c = processColor(code)
  return { color: c, background: `${c}14`, borderColor: `${c}40` }
}

const cautionStyle = (code: string) => {
  const c = processColor(code)
  return {
    color: c,
    background: `linear-gradient(90deg, ${c}12 0%, ${c}06 100%)`,
    borderColor: `${c}33`,
  }
}

const activeCount = computed(() => rows.value.filter((r) => r.is_active).length)
const inactiveCount = computed(() => rows.value.filter((r) => !r.is_active).length)

const filteredRows = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (processFilter.value !== 'all' && r.process_code !== processFilter.value) return false
    if (scopeFilter.value === 'product' && !r.product_cd) return false
    if (scopeFilter.value === 'common' && r.product_cd) return false
    if (!includeInactive.value && !r.is_active) return false
    if (!kw) return true
    const hay = `${r.product_cd || ''} ${r.product_name || ''} ${r.caution_text}`.toLowerCase()
    return hay.includes(kw)
  })
})

const processCount = (code: string) => {
  const base = rows.value.filter((r) => {
    if (scopeFilter.value === 'product' && !r.product_cd) return false
    if (scopeFilter.value === 'common' && r.product_cd) return false
    if (!includeInactive.value && !r.is_active) return false
    return true
  })
  if (code === 'all') return base.length
  return base.filter((r) => r.process_code === code).length
}

const filteredProductOptions = computed(() => {
  const kw = productFilterKw.value.trim().toLowerCase()
  const list = productOptions.value
  if (!kw) return list.slice(0, 200)
  return list
    .filter((p) => {
      const hay = `${p.product_cd || ''} ${p.product_name || ''}`.toLowerCase()
      return hay.includes(kw)
    })
    .slice(0, 200)
})

const headerCellStyle = () => ({
  background: 'linear-gradient(135deg, #fff5f6 0%, #ffe8ec 50%, #ffd6de 100%)',
  color: '#9f1239',
  fontWeight: 700,
  fontSize: '11px',
  padding: '8px',
  lineHeight: '1.3',
})
const cellStyle = () => ({ padding: '6px 8px', fontSize: '12px' })

const rowClassName = ({ row }: { row: ProcessCaution }) => (row.is_active ? '' : 'pc-row-inactive')

const sortByProcess = (a: ProcessCaution, b: ProcessCaution) =>
  processOrder.indexOf(a.process_code) - processOrder.indexOf(b.process_code)

const sortByProduct = (a: ProcessCaution, b: ProcessCaution) => {
  const aKey = a.product_cd ? `${a.product_name || ''} ${a.product_cd}` : ''
  const bKey = b.product_cd ? `${b.product_name || ''} ${b.product_cd}` : ''
  if (!a.product_cd && b.product_cd) return -1
  if (a.product_cd && !b.product_cd) return 1
  return aKey.localeCompare(bKey, 'ja')
}

function formatDate(value?: string | null) {
  if (!value) return '—'
  return value.length >= 16 ? value.slice(0, 16) : value
}

function resetFilters() {
  processFilter.value = 'all'
  scopeFilter.value = 'all'
  keyword.value = ''
  includeInactive.value = false
}

async function loadList() {
  loading.value = true
  try {
    const res = await fetchProcessCautions({ include_inactive: true })
    rows.value = res.data?.list ?? []
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.response?.data?.detail || '一覧の取得に失敗しました')
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function loadProductOptions() {
  if (productOptions.value.length) return
  productOptionsLoading.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    productOptions.value = res.data?.list ?? res.list ?? []
  } catch (e) {
    console.error(e)
    productOptions.value = []
  } finally {
    productOptionsLoading.value = false
  }
}

function filterProducts(query: string) {
  productFilterKw.value = query || ''
  if (!productOptions.value.length) void loadProductOptions()
}

function onProductChange(cd: string | null | undefined) {
  const product = productOptions.value.find((p) => p.product_cd === cd)
  form.product_name = product?.product_name ?? ''
}

function openDialog(row?: ProcessCaution) {
  if (row) {
    if (!guardQualityOperation(canEdit)) return
    editingId.value = row.id
    form.process_code = row.process_code
    form.product_cd = row.product_cd || ''
    form.product_name = row.product_name || ''
    form.caution_text = row.caution_text
    form.is_active = row.is_active
    form.sort_order = row.sort_order ?? 0
  } else {
    if (!guardQualityOperation(canCreate)) return
    editingId.value = null
    form.process_code = processFilter.value === 'all' ? 'inspection' : processFilter.value
    form.product_cd = ''
    form.product_name = ''
    form.caution_text = ''
    form.is_active = true
    form.sort_order = 0
  }
  productFilterKw.value = ''
  dialogVisible.value = true
  void loadProductOptions()
}

function onDialogClosed() {
  formRef.value?.clearValidate()
}

async function saveRow() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  const cautionText = form.caution_text.trim()
  if (!cautionText) {
    ElMessage.warning('注意事項を入力してください')
    return
  }
  if (editingId.value) {
    if (!guardQualityOperation(canEdit)) return
  } else if (!guardQualityOperation(canCreate)) {
    return
  }
  saving.value = true
  try {
    const payload = {
      process_code: form.process_code,
      product_cd: form.product_cd?.trim() || null,
      product_name: form.product_name?.trim() || null,
      caution_text: cautionText,
      is_active: form.is_active,
      sort_order: form.sort_order ?? 0,
    }
    if (editingId.value) {
      await updateProcessCaution(editingId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createProcessCaution(payload)
      ElMessage.success('追加しました')
    }
    dialogVisible.value = false
    await loadList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function toggleActive(row: ProcessCaution, next: boolean) {
  if (!guardQualityOperation(canEdit)) return
  if (row.is_active === next) return
  togglingId.value = row.id
  const prev = row.is_active
  row.is_active = next
  try {
    await setProcessCautionActive(row.id, next)
    ElMessage.success(next ? '有効にしました' : '無効にしました')
  } catch (e: any) {
    row.is_active = prev
    ElMessage.error(e?.response?.data?.detail || '更新に失敗しました')
  } finally {
    togglingId.value = null
  }
}

async function removeRow(row: ProcessCaution) {
  if (!guardQualityOperation(canDelete)) return
  const target = row.product_cd
    ? `${row.product_cd} / ${row.caution_text}`
    : `工程共通 / ${row.caution_text}`
  try {
    await ElMessageBox.confirm(`「${target}」を削除しますか？`, '削除確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
  } catch {
    return
  }
  try {
    await deleteProcessCaution(row.id)
    ElMessage.success('削除しました')
    await loadList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '削除に失敗しました')
  }
}

onMounted(() => {
  void loadList()
})
</script>

<style scoped>
.pc-page {
  min-height: 100%;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(165deg, #fffafa 0%, #fff5f6 28%, #f8fafc 62%, #f8fafc 100%);
  font-family: 'Inter', 'Noto Sans JP', -apple-system, sans-serif;
}

/* ===== Header ===== */
.pc-header {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 14px;
  padding: 14px 18px;
  border-radius: 14px;
  color: #881337;
  background: linear-gradient(135deg, #fffafa 0%, #fff5f6 40%, #ffeef1 70%, #ffe4e8 100%);
  border: 1px solid #f8d7dd;
  box-shadow: 0 8px 24px rgba(244, 63, 94, 0.08);
  animation: pc-rise 0.4s ease both;
}
.pc-header-glow {
  position: absolute;
  top: -80px;
  right: -30px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 228, 232, 0.9) 0%, transparent 70%);
  pointer-events: none;
}
.pc-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}
.pc-title-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #e11d48;
  background: #fff;
  border: 1px solid #f8d7dd;
  box-shadow: 0 4px 12px rgba(244, 63, 94, 0.1);
  flex-shrink: 0;
}
.pc-title {
  margin: 0;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #9f1239;
}
.pc-subtitle {
  margin: 3px 0 0;
  font-size: 12px;
  color: #a87988;
}
.pc-header-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
  position: relative;
  z-index: 1;
}
.pc-stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 86px;
  padding: 7px 11px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #f3d4da;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.pc-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(244, 63, 94, 0.1);
}
.pc-stat-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.pc-stat-card--total .pc-stat-icon {
  background: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
}
.pc-stat-card--ok .pc-stat-icon {
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
}
.pc-stat-card--mute .pc-stat-icon {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}
.pc-stat-card--view .pc-stat-icon {
  background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
}
.pc-stat-body {
  display: flex;
  flex-direction: column;
}
.pc-stat-value {
  font-size: 16px;
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: #9f1239;
}
.pc-stat-label {
  margin-top: 2px;
  font-size: 11px;
  color: #a87988;
}
.pc-header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.pc-head-btn {
  height: 32px;
  border-radius: 10px !important;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid transparent !important;
  color: #fff !important;
  transition: all 0.2s ease;
}
.pc-head-btn:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.2);
}
.pc-btn-refresh {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
  border-color: rgba(186, 230, 253, 0.75) !important;
}
.pc-btn-add {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
  border-color: rgba(253, 230, 138, 0.85) !important;
  color: #7c2d12 !important;
}

/* ===== Toolbar ===== */
.pc-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f3d4da;
  box-shadow: 0 2px 10px rgba(244, 63, 94, 0.04);
  animation: pc-rise 0.45s ease 0.05s both;
}
.pc-process-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pc-process-tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  border-radius: 999px;
  padding: 5px 11px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pc-process-tab:hover {
  border-color: #94a3b8;
  transform: translateY(-1px);
}
.pc-process-tab.is-active {
  box-shadow: 0 4px 12px rgba(30, 58, 95, 0.2);
}
.pc-tab-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.35);
}
.pc-count {
  margin-left: 2px;
  min-width: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.pc-process-tab.is-active .pc-count {
  background: rgba(255, 255, 255, 0.22);
}
.pc-toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.pc-scope-switch {
  display: inline-flex;
  padding: 3px;
  gap: 3px;
  background: #f1f5f9;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}
.pc-scope-btn {
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 8px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pc-scope-btn.is-active.pc-scope-btn--all {
  background: linear-gradient(135deg, #1e3a5f 0%, #334155 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(30, 58, 95, 0.3);
}
.pc-scope-btn.is-active.pc-scope-btn--product {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(37, 99, 235, 0.35);
}
.pc-scope-btn.is-active.pc-scope-btn--common {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(124, 58, 237, 0.35);
}
.pc-search {
  width: 240px;
  min-width: 160px;
  margin-left: auto;
}
.pc-check {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  user-select: none;
}
.pc-btn-reset {
  border-radius: 8px !important;
  border-color: #f3d4da !important;
  color: #c45c72 !important;
  background: #fff8f9 !important;
  font-weight: 600;
}

/* ===== Panel / Table ===== */
.pc-panel {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f3d4da;
  box-shadow: 0 2px 12px rgba(244, 63, 94, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-top: 3px solid #f8b4c0;
  animation: pc-rise 0.5s ease 0.08s both;
}
.pc-panel-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(90deg, #fff8f9 0%, #fff 55%);
  border-bottom: 1px solid #f8e4e8;
}
.pc-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}
.pc-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #9f1239;
  background: linear-gradient(135deg, #ffe8ec, #ffd6de);
  border: 1px solid #f3d4da;
}
.pc-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.pc-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}
.pc-legend-item i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.pc-proc {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid;
  font-size: 11px;
  font-weight: 700;
}
.pc-proc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.pc-common-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f3e8ff;
  color: #7c3aed;
  border: 1px solid #e9d5ff;
  font-size: 11px;
  font-weight: 700;
}
.pc-product {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  gap: 1px;
}
.pc-cd {
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  font-size: 12px;
}
.pc-name {
  color: #64748b;
  font-size: 11px;
}
.pc-caution {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  padding: 3px 8px;
  border-radius: 8px;
  border: 1px solid;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.35;
}
.pc-caution-ico {
  flex-shrink: 0;
}
.pc-sort {
  display: inline-flex;
  min-width: 28px;
  justify-content: center;
  padding: 1px 6px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #475569;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.pc-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  font-size: 11px;
  color: #64748b;
}
.pc-meta-by {
  color: #94a3b8;
}
.pc-op-edit {
  font-weight: 700;
}
:deep(.pc-table .el-table__header th) {
  border-color: #f3d4da;
}
:deep(.pc-row-inactive) {
  opacity: 0.5;
}
:deep(.pc-table .el-table__row) {
  cursor: pointer;
  transition: background 0.15s ease;
}
:deep(.pc-table .el-table__row:hover > td) {
  background: #fff8f9 !important;
}

/* ===== Dialog ===== */
.pc-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(244, 63, 94, 0.12);
  border: 1px solid #f3d4da;
}
.pc-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}
.pc-dialog :deep(.el-dialog__body) {
  padding: 14px 18px 8px;
  background: linear-gradient(180deg, #fffafa 0%, #fff 40%);
}
.pc-dialog :deep(.el-dialog__footer) {
  padding: 10px 18px 16px;
  border-top: 1px solid #f8e4e8;
}
.pc-dialog :deep(.el-dialog__headerbtn) {
  top: 14px;
  right: 14px;
  width: 28px;
  height: 28px;
}
.pc-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #c45c72;
  font-size: 16px;
}
.pc-dlg-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #881337;
  background: linear-gradient(135deg, #fffafa 0%, #fff5f6 45%, #ffe8ec 100%);
  border-bottom: 1px solid #f3d4da;
}
.pc-dlg-icon {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(244, 63, 94, 0.18);
  flex-shrink: 0;
  transition: background 0.2s ease;
}
.pc-dlg-title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: #9f1239;
}
.pc-dlg-sub {
  margin-top: 2px;
  font-size: 11px;
  color: #a87988;
}
.pc-dlg-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.pc-process-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pc-pick {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1.5px solid;
  background: #fff;
  border-radius: 999px;
  padding: 5px 11px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pc-pick:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}
.pc-pick.is-active {
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.16);
}
.pc-pick i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.pc-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #334155;
  font-size: 12px;
  margin-bottom: 4px !important;
}
.pc-form-item {
  margin-bottom: 12px;
}
.pc-form-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 5px;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.3;
}
.pc-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.pc-active-box {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 32px;
  padding: 0 12px;
  border-radius: 10px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  transition: all 0.2s ease;
}
.pc-active-box.is-on {
  background: #ecfdf5;
  border-color: #a7f3d0;
  color: #047857;
}
.pc-caution-input :deep(.el-textarea__inner) {
  border-radius: 10px;
  border-color: #f3d4da;
  background: #fffafa;
}
.pc-caution-input :deep(.el-textarea__inner:focus) {
  border-color: #f8b4c0;
  box-shadow: 0 0 0 3px rgba(248, 180, 192, 0.35);
}
.pc-preview {
  border: 1px dashed;
  border-radius: 12px;
  padding: 10px 12px;
  background: #fff;
}
.pc-preview-label {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 6px;
  letter-spacing: 0.04em;
}
.pc-preview-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid;
  font-weight: 600;
}
.pc-preview-proc {
  font-size: 11px;
  opacity: 0.85;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.pc-preview-scope {
  display: inline-flex;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  font-size: 10px;
  font-weight: 700;
}
.pc-preview-text {
  font-size: 13px;
  line-height: 1.4;
}
.pc-dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}
.pc-btn-cancel {
  height: 34px;
  border-radius: 10px !important;
  border: 1px solid #e5e7eb !important;
  font-weight: 600;
}
.pc-btn-save {
  height: 34px;
  border-radius: 10px !important;
  border: 1px solid #f3d4da !important;
  background: linear-gradient(135deg, #ffe8ec 0%, #ffd6de 100%) !important;
  color: #9f1239 !important;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(244, 63, 94, 0.12);
}
.pc-btn-save:hover {
  filter: brightness(0.98);
  background: linear-gradient(135deg, #ffd6de 0%, #fecdd3 100%) !important;
}

@keyframes pc-rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 860px) {
  .pc-search {
    margin-left: 0;
    width: 100%;
  }
  .pc-form-row {
    grid-template-columns: 1fr;
  }
  .pc-header-stats {
    margin-left: 0;
  }
}
</style>
