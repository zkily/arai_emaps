<template>
  <div class="pdi-page pdm-modern">
    <header class="pdi-hero">
      <div class="page-header-fx" aria-hidden="true"><span class="fx-orb orb-a" /><span class="fx-orb orb-b" /><span class="fx-grid" /><span class="fx-sheen" /></div>
      <div class="pdi-hero__accent" aria-hidden="true" />
      <div class="pdi-hero__inner">
        <div class="pdi-hero__icon">
          <el-icon :size="20"><Warning /></el-icon>
        </div>
        <div class="pdi-hero__text">
          <h1 class="pdi-hero__title">工程別不良項目マスタ</h1>
          <p class="pdi-hero__sub">
            収集工程ごとに MES で選択する不良項目を登録。帰属工程で責任工程（前工程不良等）を指定します。
          </p>
        </div>
        <div class="pdi-hero__stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
          <div class="stat-card stat-total">
            <span class="stat-num">{{ total }}</span>
            <span class="stat-lbl">総件数</span>
          </div>
          <div class="stat-card stat-active">
            <span class="stat-num">{{ activeRowCount }}</span>
            <span class="stat-lbl">有効</span>
          </div>
          <div class="stat-card stat-upstream">
            <span class="stat-num">{{ upstreamRowCount }}</span>
            <span class="stat-lbl">前工程帰属</span>
          </div>
          <div class="stat-card stat-proc">
            <span class="stat-num">{{ detectionProcessCount }}</span>
            <span class="stat-lbl">収集工程</span>
          </div>
        </div>
      </div>
    </header>

    <el-card class="pdi-toolbar-card" shadow="never">
      <div class="pdi-toolbar">
        <el-form :inline="true" class="pdi-filter-form" @submit.prevent>
          <el-form-item label="収集工程">
            <el-select
              v-model="filterDetectionCd"
              filterable
              clearable
              placeholder="全工程"
              class="pdi-filt-select"
              size="small"
              :loading="processLoading"
            >
              <el-option
                v-for="p in processOptions"
                :key="p.process_cd"
                :label="`${p.process_cd} — ${p.process_name || ''}`"
                :value="p.process_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="帰属工程">
            <el-select
              v-model="filterAttributableCd"
              filterable
              clearable
              placeholder="全て"
              class="pdi-filt-select"
              size="small"
              :loading="processLoading"
            >
              <el-option
                v-for="p in processOptions"
                :key="'att-' + p.process_cd"
                :label="`${p.process_cd} — ${p.process_name || ''}`"
                :value="p.process_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="キーワード">
            <el-input
              v-model="filterKeyword"
              placeholder="不良CD/名称"
              clearable
              size="small"
              class="pdi-filt-input"
              @keyup.enter="loadList"
            />
          </el-form-item>
          <el-form-item label="状態">
            <el-select v-model="filterStatus" clearable placeholder="全て" class="pdi-filt-status" size="small">
              <el-option label="有効" value="active" />
              <el-option label="無効" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item class="pdi-toolbar__btns">
            <el-button type="primary" size="small" :icon="Search" class="pdi-btn-search" @click="loadList">検索</el-button>
            <el-button size="small" class="pdi-btn-clear" @click="resetFilter">クリア</el-button>
            <el-button v-if="canCreate" type="primary" size="small" :icon="Plus" plain class="pdi-btn-new" @click="openCreate">新規</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card class="pdi-data-card" shadow="never">
      <template #header>
        <div class="pdi-data-cap">
          <span class="pdi-data-cap__dot" />
          <span class="pdi-data-cap__title">登録一覧</span>
          <span class="pdi-data-cap__meta">{{ total }} 件</span>
        </div>
      </template>
      <el-table
        v-loading="loading"
        class="pdi-table"
        :data="rows"
        stripe
        style="width: 100%"
        max-height="calc(100vh - 300px)"
        size="small"
      >
        <el-table-column prop="detection_process_cd" label="収集工程CD" width="110">
          <template #default="{ row }">
            <span class="pdi-chip pdi-chip--detect">{{ row.detection_process_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="detection_process_name" label="収集工程" min-width="100" show-overflow-tooltip />
        <el-table-column prop="attributable_process_cd" label="帰属工程CD" width="110">
          <template #default="{ row }">
            <span
              v-if="row.attributable_process_cd"
              :class="[
                'pdi-chip',
                row.attributable_process_cd !== row.detection_process_cd ? 'pdi-chip--upstream' : 'pdi-chip--same',
              ]"
            >
              {{ row.attributable_process_cd }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="attributable_process_name" label="帰属工程" min-width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag
              v-if="row.attributable_process_cd !== row.detection_process_cd"
              type="warning"
              size="small"
              effect="plain"
              class="pdi-upstream-tag"
            >
              {{ row.attributable_process_name || row.attributable_process_cd }}
            </el-tag>
            <span v-else>{{ row.attributable_process_name || row.attributable_process_cd || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="defect_cd" label="不良CD" width="130">
          <template #default="{ row }">
            <span class="pdi-chip pdi-chip--defect">{{ row.defect_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="defect_name" label="不良項目名" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pdi-defect-name">{{ row.defect_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="順" width="56" align="center">
          <template #default="{ row }">
            <span v-if="row.sort_order != null" class="pdi-order">{{ row.sort_order }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状態" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small" :class="['pdi-status', `pdi-status--${row.status}`]">
              {{ row.status === 'active' ? '有効' : '無効' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remarks" label="備考" min-width="100" show-overflow-tooltip />
        <el-table-column v-if="canEdit || canDelete" label="操作" width="128" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-if="canEdit" size="small" type="primary" link @click="openEdit(row)">編集</el-button>
            <el-popconfirm v-if="canDelete" title="削除しますか？" width="200" @confirm="handleDelete(row.id!)">
              <template #reference>
                <el-button size="small" type="danger" link>削除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pdi-pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          size="small"
          layout="total, sizes, prev, pager, next"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      width="620px"
      destroy-on-close
      align-center
      class="pdi-form-dialog"
      :close-on-click-modal="false"
      append-to-body
    >
      <template #header>
        <div class="pdi-dlg-header">
          <div class="pdi-dlg-header__accent" aria-hidden="true" />
          <div class="pdi-dlg-header__main">
            <div class="pdi-dlg-header__icon" :class="{ 'pdi-dlg-header__icon--edit': isEdit }">
              <el-icon :size="20">
                <component :is="isEdit ? EditPen : CirclePlus" />
              </el-icon>
            </div>
            <div class="pdi-dlg-header__text">
              <h3 class="pdi-dlg-header__title">{{ isEdit ? '不良項目を編集' : '不良項目を新規登録' }}</h3>
              <p class="pdi-dlg-header__desc">後工程で発見した不良は帰属工程を前工程に設定してください</p>
            </div>
          </div>
        </div>
      </template>

      <div class="pdi-dlg-body">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="pdi-dlg-form">
          <section class="pdi-section">
            <div class="pdi-section__head">
              <span class="pdi-section__badge">01</span>
              <span class="pdi-section__label">工程</span>
            </div>
            <el-form-item label="収集工程（MES画面の工程）" prop="detection_process_cd">
              <el-select
                v-model="form.detection_process_cd"
                filterable
                placeholder="工程を選択"
                class="pdi-input-full"
                :loading="processLoading"
              >
                <el-option
                  v-for="p in processOptions"
                  :key="p.process_cd"
                  :label="`${p.process_cd} — ${p.process_name || ''}`"
                  :value="p.process_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="帰属工程（不良を負う工程）" prop="attributable_process_cd">
              <el-select
                v-model="form.attributable_process_cd"
                filterable
                placeholder="工程を選択"
                class="pdi-input-full"
                :loading="processLoading"
              >
                <el-option
                  v-for="p in processOptions"
                  :key="'f-' + p.process_cd"
                  :label="`${p.process_cd} — ${p.process_name || ''}`"
                  :value="p.process_cd"
                />
              </el-select>
              <div class="pdi-field-hint">検査等で前工程不良を記録する場合は、帰属を切断・面取等に設定</div>
            </el-form-item>
          </section>

          <section class="pdi-section">
            <div class="pdi-section__head">
              <span class="pdi-section__badge pdi-section__badge--accent">02</span>
              <span class="pdi-section__label">不良項目</span>
            </div>
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="不良項目CD" prop="defect_cd">
                  <el-input v-model="form.defect_cd" placeholder="例: scratch" clearable :disabled="isEdit" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="表示順" prop="sort_order">
                  <el-input-number v-model="form.sort_order" :min="0" :max="9999" class="pdi-input-full" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="不良項目名" prop="defect_name">
              <el-input v-model="form.defect_name" placeholder="例: キズ" clearable />
            </el-form-item>
            <el-form-item label="状態" prop="status">
              <el-radio-group v-model="form.status">
                <el-radio value="active">有効</el-radio>
                <el-radio value="inactive">無効</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="備考">
              <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="任意" />
            </el-form-item>
          </section>
        </el-form>
      </div>
      <template #footer>
        <div class="pdi-dlg-footer">
          <el-button @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Warning, Search, Plus, EditPen, CirclePlus } from '@element-plus/icons-vue'
import { getProcessList } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchProcessDefectItems,
  createProcessDefectItem,
  updateProcessDefectItem,
  deleteProcessDefectItem,
  type ProcessDefectItem,
} from '@/api/master/processDefectItemMaster'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

defineOptions({ name: 'ProcessDefectItemManagement' })

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const loading = ref(false)
const submitLoading = ref(false)
const processLoading = ref(false)
const rows = ref<ProcessDefectItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const processOptions = ref<ProcessItem[]>([])

const activeRowCount = computed(() => rows.value.filter((r) => r.status === 'active').length)
const upstreamRowCount = computed(
  () =>
    rows.value.filter(
      (r) => !!r.attributable_process_cd && r.attributable_process_cd !== r.detection_process_cd,
    ).length,
)
const detectionProcessCount = computed(
  () => new Set(rows.value.map((r) => r.detection_process_cd).filter(Boolean)).size,
)

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

const filterDetectionCd = ref('')
const filterAttributableCd = ref('')
const filterKeyword = ref('')
const filterStatus = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const defaultForm = (): ProcessDefectItem => ({
  detection_process_cd: '',
  attributable_process_cd: '',
  defect_cd: '',
  defect_name: '',
  sort_order: 0,
  status: 'active',
  remarks: '',
})

const form = reactive<ProcessDefectItem>(defaultForm())

const rules: FormRules = {
  detection_process_cd: [{ required: true, message: '収集工程を選択してください', trigger: 'change' }],
  attributable_process_cd: [{ required: true, message: '帰属工程を選択してください', trigger: 'change' }],
  defect_cd: [{ required: true, message: '不良項目CDを入力してください', trigger: 'blur' }],
  defect_name: [{ required: true, message: '不良項目名を入力してください', trigger: 'blur' }],
}

watch(
  () => form.detection_process_cd,
  (cd, prev) => {
    if (!cd) return
    if (!form.attributable_process_cd || form.attributable_process_cd === prev) {
      form.attributable_process_cd = cd
    }
  }
)

async function loadProcesses() {
  processLoading.value = true
  try {
    const res = await getProcessList({ pageSize: 5000 })
    const list = res.data?.list ?? res.list ?? []
    processOptions.value = list
  } catch {
    ElMessage.error('工程一覧の取得に失敗しました')
  } finally {
    processLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await fetchProcessDefectItems({
      detectionProcessCd: filterDetectionCd.value || undefined,
      attributableProcessCd: filterAttributableCd.value || undefined,
      keyword: filterKeyword.value || undefined,
      status: filterStatus.value || undefined,
      page: page.value,
      pageSize: pageSize.value,
    })
    rows.value = res.data?.list ?? []
    total.value = res.data?.total ?? 0
  } catch {
    ElMessage.error('一覧の取得に失敗しました')
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  filterDetectionCd.value = ''
  filterAttributableCd.value = ''
  filterKeyword.value = ''
  filterStatus.value = ''
  page.value = 1
  loadList()
}

function resetForm() {
  Object.assign(form, defaultForm())
}

function openCreate() {
  if (!guardMasterOperation(canCreate)) return
  isEdit.value = false
  editId.value = null
  resetForm()
  if (filterDetectionCd.value) {
    form.detection_process_cd = filterDetectionCd.value
    form.attributable_process_cd = filterDetectionCd.value
  }
  dialogVisible.value = true
}

function openEdit(row: ProcessDefectItem) {
  if (!guardMasterOperation(canEdit)) return
  isEdit.value = true
  editId.value = row.id ?? null
  Object.assign(form, {
    detection_process_cd: row.detection_process_cd,
    attributable_process_cd: row.attributable_process_cd,
    defect_cd: row.defect_cd,
    defect_name: row.defect_name,
    sort_order: row.sort_order ?? 0,
    status: row.status || 'active',
    remarks: row.remarks ?? '',
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    const payload = { ...form }
    if (isEdit.value && editId.value != null) {
      await updateProcessDefectItem(editId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createProcessDefectItem(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    loadList()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof msg === 'string' ? msg : '保存に失敗しました')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(id: number) {
  if (!guardMasterOperation(canDelete)) return
  try {
    await deleteProcessDefectItem(id)
    ElMessage.success('削除しました')
    loadList()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

onMounted(async () => {
  await loadProcesses()
  await loadList()
})
</script>

<style scoped>
.pdi-page {
  padding: 12px 16px 20px;
  min-height: 100%;
  background: linear-gradient(160deg, #f8fafc 0%, #eef2f7 100%);
}

.pdi-hero {
  position: relative;
  margin-bottom: 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 1px 3px rgb(15 23 42 / 6%);
}

.pdi-hero__accent {
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #ef4444);
  transform-origin: left;
}

.pdi-hero__inner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}

.pdi-hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #b45309;
}

.pdi-hero__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.pdi-hero__sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.45;
}

.pdi-toolbar-card,
.pdi-data-card {
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  margin-bottom: 10px;
}

.pdi-toolbar-card :deep(.el-card__body) {
  padding: 10px 14px;
}

.pdi-data-card :deep(.el-card__header) {
  padding: 8px 14px;
  border-bottom: 1px solid #f3f4f6;
}

.pdi-data-card :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

.pdi-filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
}

.pdi-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.pdi-filt-select {
  width: 200px;
}

.pdi-filt-input {
  width: 160px;
}

.pdi-filt-status {
  width: 100px;
}

.pdi-toolbar__btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-left: auto;
}

.pdi-data-cap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pdi-data-cap__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
}

.pdi-data-cap__title {
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.pdi-data-cap__meta {
  margin-left: auto;
  font-size: 12px;
  color: #9ca3af;
}

.pdi-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.pdi-field-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #9ca3af;
  line-height: 1.4;
}

.pdi-input-full {
  width: 100%;
}

.pdi-dlg-header__accent {
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #ef4444);
}

.pdi-dlg-header__main {
  display: flex;
  gap: 12px;
  padding: 4px 0 0;
}

.pdi-dlg-header__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fef3c7;
  color: #b45309;
}

.pdi-dlg-header__icon--edit {
  background: #dbeafe;
  color: #1d4ed8;
}

.pdi-dlg-header__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.pdi-dlg-header__desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.pdi-section {
  margin-bottom: 12px;
}

.pdi-section__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.pdi-section__badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: #e5e7eb;
  color: #4b5563;
}

.pdi-section__badge--accent {
  background: #fef3c7;
  color: #b45309;
}

.pdi-section__label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}

.pdi-dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（工程別不良項目 / wine→crimson→amber）
 * ============================================================ */
.pdm-modern {
  --hx-1: #27070b;
  --hx-2: #9f1239;
  --hx-3: #e11d48;
  --hx-4: #f59e0b;
  --hx-deep: #881337;
  --hx-soft: #fff1f2;
  --hx-line: rgba(225, 29, 72, 0.16);
  background:
    radial-gradient(1100px 360px at 10% -10%, rgba(225, 29, 72, 0.08), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(245, 158, 11, 0.08), transparent 60%),
    linear-gradient(160deg, #fdf7f8 0%, #fff5f6 40%, #f8fafc 100%);
}

.pdm-modern .pdi-hero {
  border: none;
  border-radius: 16px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 38%, var(--hx-3) 72%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(159, 18, 57, 0.6),
    0 6px 14px -6px rgba(245, 158, 11, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.pdm-modern .pdi-hero > :not(.page-header-fx) {
  position: relative;
  z-index: 1;
}

.pdm-modern .pdi-hero__accent {
  background: linear-gradient(90deg, #fbbf24, #fb7185, #fbbf24);
  background-size: 200% 100%;
  animation: pdmAccentFlow 4s linear infinite;
}

.pdm-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.pdm-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.55;
  animation: pdmOrbFloat 11s ease-in-out infinite;
}

.pdm-modern .fx-orb.orb-a {
  width: 220px;
  height: 220px;
  top: -100px;
  left: 30%;
  background: radial-gradient(circle, rgba(251, 113, 133, 0.65), transparent 70%);
}

.pdm-modern .fx-orb.orb-b {
  width: 180px;
  height: 180px;
  bottom: -90px;
  right: 12%;
  background: radial-gradient(circle, rgba(252, 211, 77, 0.6), transparent 70%);
  animation-delay: -5s;
}

.pdm-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at 30% 50%, #000 20%, transparent 75%);
}

.pdm-modern .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 30%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.16), transparent);
  transform: skewX(-18deg);
  animation: pdmSheen 7s ease-in-out infinite;
}

.pdm-modern .pdi-hero__inner {
  flex-wrap: wrap;
}

.pdm-modern .pdi-hero__icon {
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 4px 0 rgba(39, 7, 11, 0.5),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  animation: pdmIconAlert 3.2s ease-in-out infinite;
}

.pdm-modern .pdi-hero__text {
  flex: 1;
  min-width: 240px;
}

.pdm-modern .pdi-hero__title {
  font-weight: 800;
  color: #fff;
  text-shadow: 0 2px 10px rgba(39, 7, 11, 0.4);
}

.pdm-modern .pdi-hero__sub {
  color: rgba(255, 255, 255, 0.85);
}

.pdm-modern .pdi-hero__stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  perspective: 650px;
}

.pdm-modern .stat-card {
  --sc: #fecdd3;
  position: relative;
  overflow: hidden;
  min-width: 70px;
  padding: 6px 12px 5px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(8px);
  box-shadow:
    0 3px 0 rgba(39, 7, 11, 0.45),
    0 10px 20px -10px rgba(0, 0, 0, 0.45);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease;
}

.pdm-modern .stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--sc);
}

.pdm-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.35), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.pdm-modern .stat-card:hover {
  box-shadow:
    0 5px 0 rgba(39, 7, 11, 0.5),
    0 16px 26px -12px rgba(0, 0, 0, 0.5);
}

.pdm-modern .stat-card:hover::after {
  opacity: 1;
}

.pdm-modern .stat-total { --sc: #fde68a; }
.pdm-modern .stat-active { --sc: #86efac; }
.pdm-modern .stat-upstream { --sc: #fdba74; }
.pdm-modern .stat-proc { --sc: #c4b5fd; }

.pdm-modern .stat-num {
  font-size: 17px;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(39, 7, 11, 0.4);
}

.pdm-modern .stat-lbl {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
  letter-spacing: 0.04em;
}

.pdm-modern .pdi-toolbar-card,
.pdm-modern .pdi-data-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 10px 24px -16px rgba(136, 19, 55, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.pdm-modern .pdi-toolbar-card::before,
.pdm-modern .pdi-data-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), #fb923c, var(--hx-4));
}

.pdm-modern .pdi-toolbar-card :deep(.el-card__body) {
  padding-top: 13px;
}

.pdm-modern .pdi-filter-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: var(--hx-deep);
}

.pdm-modern .pdi-filter-form :deep(.el-input__wrapper),
.pdm-modern .pdi-filter-form :deep(.el-select__wrapper) {
  border-radius: 9px;
}

.pdm-modern .pdi-filter-form :deep(.el-input__wrapper.is-focus),
.pdm-modern .pdi-filter-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--hx-3) inset, 0 0 0 3px rgba(225, 29, 72, 0.12);
}

.pdm-modern .pdi-btn-search,
.pdm-modern .pdi-btn-new {
  border: none;
  font-weight: 700;
  color: #fff;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.pdm-modern .pdi-btn-search {
  --k-edge: #1e40af;
  --k-glow: rgba(59, 130, 246, 0.5);
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.pdm-modern .pdi-btn-new {
  --k-edge: #881337;
  --k-glow: rgba(225, 29, 72, 0.5);
  background: linear-gradient(135deg, #fb7185, #e11d48);
}

.pdm-modern .pdi-btn-search:hover,
.pdm-modern .pdi-btn-search:focus {
  color: #fff;
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.pdm-modern .pdi-btn-new:hover,
.pdm-modern .pdi-btn-new:focus {
  color: #fff;
  background: linear-gradient(135deg, #fb7185, #e11d48);
}

.pdm-modern .pdi-btn-search:hover,
.pdm-modern .pdi-btn-new:hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.pdm-modern .pdi-btn-search:active,
.pdm-modern .pdi-btn-new:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge);
}

.pdm-modern .pdi-btn-clear {
  color: var(--hx-deep);
  background: var(--hx-soft);
  border-color: rgba(225, 29, 72, 0.22);
  box-shadow: 0 2px 0 rgba(225, 29, 72, 0.2);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.pdm-modern .pdi-btn-clear:hover {
  transform: translateY(-1px);
  color: var(--hx-deep);
  background: #ffe4e6;
  border-color: rgba(225, 29, 72, 0.3);
  box-shadow: 0 3px 0 rgba(225, 29, 72, 0.26);
}

.pdm-modern .pdi-data-card :deep(.el-card__header) {
  padding-top: 11px;
  background: linear-gradient(180deg, #fff, #fff7f8);
}

.pdm-modern .pdi-data-cap__dot {
  background: var(--hx-3);
  box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.18);
  animation: pdmDotPulse 2s ease-in-out infinite;
}

.pdm-modern .pdi-data-cap__title {
  font-weight: 800;
  color: var(--hx-deep);
}

.pdm-modern .pdi-data-cap__meta {
  padding: 1px 9px;
  border-radius: 999px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4));
  box-shadow: 0 2px 0 var(--hx-deep);
}

.pdm-modern .pdi-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #881337, #9f1239) !important;
  color: #fff !important;
  border-bottom: 2px solid var(--hx-4) !important;
}

.pdm-modern .pdi-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #fff1f2 !important;
}

.pdm-modern .pdi-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-3);
}

.pdm-modern .pdi-chip {
  --cc: #475569;
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

.pdm-modern .pdi-chip--detect { --cc: #0369a1; }
.pdm-modern .pdi-chip--same { --cc: #475569; }
.pdm-modern .pdi-chip--upstream { --cc: #c2410c; }
.pdm-modern .pdi-chip--defect { --cc: #be123c; }

.pdm-modern .pdi-table :deep(tr:hover) .pdi-chip {
  transform: translateY(-1px);
}

.pdm-modern .pdi-defect-name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #1f2937;
}

.pdm-modern .pdi-defect-name::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--hx-3);
  box-shadow: 0 0 0 2px rgba(225, 29, 72, 0.18);
}

.pdm-modern .pdi-order {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 5px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fde68a;
}

.pdm-modern .pdi-upstream-tag {
  font-weight: 700;
  border-radius: 999px;
}

.pdm-modern .pdi-status {
  border-radius: 999px;
  font-weight: 700;
}

.pdm-modern .pdi-status--active {
  box-shadow: 0 2px 0 rgba(22, 163, 74, 0.28);
}

.pdm-modern .pdi-pagination :deep(.el-pager li.is-active) {
  border-radius: 6px;
  color: #fff;
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4));
  box-shadow: 0 2px 0 var(--hx-deep);
}

@keyframes pdmOrbFloat {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(26px, 14px) scale(1.12);
  }
}

@keyframes pdmSheen {
  0% {
    left: -40%;
  }
  60%,
  100% {
    left: 130%;
  }
}

@keyframes pdmAccentFlow {
  from {
    background-position: 0% 0;
  }
  to {
    background-position: 200% 0;
  }
}

@keyframes pdmIconAlert {
  0%,
  70%,
  100% {
    transform: perspective(300px) rotateZ(0deg) rotateX(0deg);
  }
  76% {
    transform: perspective(300px) rotateZ(-10deg) rotateX(10deg);
  }
  82% {
    transform: perspective(300px) rotateZ(8deg) rotateX(10deg);
  }
  88% {
    transform: perspective(300px) rotateZ(-5deg) rotateX(6deg);
  }
}

@keyframes pdmDotPulse {
  0%,
  100% {
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.18);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(225, 29, 72, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pdm-modern .fx-orb,
  .pdm-modern .fx-sheen,
  .pdm-modern .pdi-hero__accent,
  .pdm-modern .pdi-hero__icon,
  .pdm-modern .pdi-data-cap__dot {
    animation: none;
  }

  .pdm-modern .stat-card {
    transform: none;
  }
}
</style>
