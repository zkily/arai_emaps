<template>
  <div class="pdi-page">
    <header class="pdi-hero">
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
            <el-button type="primary" size="small" :icon="Search" @click="loadList">検索</el-button>
            <el-button size="small" @click="resetFilter">クリア</el-button>
            <el-button v-if="canCreate" type="primary" size="small" :icon="Plus" plain @click="openCreate">新規</el-button>
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
        <el-table-column prop="detection_process_cd" label="収集工程CD" width="110" />
        <el-table-column prop="detection_process_name" label="収集工程" min-width="100" show-overflow-tooltip />
        <el-table-column prop="attributable_process_cd" label="帰属工程CD" width="110" />
        <el-table-column prop="attributable_process_name" label="帰属工程" min-width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag
              v-if="row.attributable_process_cd !== row.detection_process_cd"
              type="warning"
              size="small"
              effect="plain"
            >
              {{ row.attributable_process_name || row.attributable_process_cd }}
            </el-tag>
            <span v-else>{{ row.attributable_process_name || row.attributable_process_cd || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="defect_cd" label="不良CD" width="130" />
        <el-table-column prop="defect_name" label="不良項目名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="順" width="56" align="center" />
        <el-table-column prop="status" label="状態" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
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
import { ref, reactive, onMounted, watch } from 'vue'
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
</style>
