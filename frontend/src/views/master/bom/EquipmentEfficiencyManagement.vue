<template>
  <div class="ee-container eef-modern pb-std">
    <!-- 页面头部 -->
    <div class="ee-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="ee-header-left">
        <span class="ee-title-icon"><el-icon :size="20"><Tools /></el-icon></span>
        <div class="ee-title-copy">
          <h1 class="ee-title pb-hero-title">設備能率管理</h1>
          <p class="ee-subtitle pb-hero-desc">設備ごとの加工製品別能率設定・管理</p>
        </div>
      </div>
      <div class="ee-stats">
        <div
          v-for="(s, i) in [
            { n: tabCountsAll, l: '設定数' },
            { n: machineDistinctCount, l: '設備数' },
            { n: productDistinctCount, l: '製品数' },
            { n: efficiencyList.length, l: '表示中' }
          ]"
          :key="s.l"
          class="ee-stat"
          :class="`ee-stat--${i}`"
        >
          <span class="ee-stat-lbl"><i class="ee-stat-dot" />{{ s.l }}</span>
          <span class="ee-stat-num">{{ s.n }}</span>
        </div>
      </div>
    </div>

    <!-- 工具栏：搜索 + 操作 -->
    <div class="ee-toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="製品名・設備名で検索…"
        clearable
        @input="scheduleKeywordSearch"
        class="ee-search"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="filters.machineCd"
        placeholder="設備"
        filterable
        clearable
        class="ee-filter-select"
        @change="handleMachineFilterChange"
      >
        <el-option
          v-for="m in machineFilterOptions"
          :key="m.value"
          :label="m.label"
          :value="m.value"
        />
      </el-select>
      <el-select
        v-model="filters.productCd"
        placeholder="製品名"
        filterable
        clearable
        class="ee-filter-select ee-filter-select--product"
        @change="resetPageAndLoad"
      >
        <el-option
          v-for="p in productFilterOptions"
          :key="p.value"
          :label="p.label"
          :value="p.value"
        >
          <span>{{ p.name }}</span>
          <span class="ee-filter-opt-cd">{{ p.value }}</span>
        </el-option>
      </el-select>
      <div class="ee-toolbar-actions">
        <el-button @click="clearFilters" :icon="Refresh" class="ee-btn ee-btn--clear">クリア</el-button>
        <el-button @click="overviewVisible = true" :icon="Grid" class="ee-btn ee-btn--overview">
          工程別一覧
        </el-button>
        <el-button
          v-if="canExport"
          @click="handlePrint"
          :icon="Printer"
          :loading="printing"
          class="ee-btn ee-btn--print"
        >
          印刷
        </el-button>
        <el-button
          v-if="canExport"
          @click="handleExportExcel"
          :icon="Download"
          :loading="exporting"
          class="ee-btn ee-btn--excel"
        >
          Excel出力
        </el-button>
        <el-button
          v-if="canEdit"
          @click="handleRefreshCurrentRate"
          :icon="DataAnalysis"
          :loading="refreshingCurrent"
          class="ee-btn ee-btn--rate"
        >
          現在能率更新
        </el-button>
        <el-button
          v-if="canCreate"
          @click="openMissingDialog"
          :icon="DocumentAdd"
          :loading="missingLoading && !missingVisible"
          class="ee-btn ee-btn--import"
        >
          生産性から追加
        </el-button>
        <el-button v-if="canCreate" @click="openDialog()" :icon="Plus" class="ee-btn ee-btn--add">
          <span class="btn-label">新規登録</span>
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="ee-table-wrap">
      <el-tabs v-model="activeProcessTab" @tab-change="handleTabChange" class="ee-tabs">
        <el-tab-pane
          v-for="process in processTypes"
          :key="process.value"
          :label="`${process.label} (${getProcessCount(process.value)})`"
          :name="process.value"
        >
          <el-table
            :data="process.value === activeProcessTab ? efficiencyList : []"
            v-loading="loading"
            stripe
            border
            size="small"
            style="width: 100%"
            class="ee-table"
            :empty-text="'データがありません'"
            :default-sort="{ prop: 'machines_name', order: 'ascending' }"
            :row-class-name="getRowClassName"
            height="calc(100vh - 260px)"
          >
            <el-table-column type="index" label="#" width="48" align="center" :index="tableIndexMethod" />
            <el-table-column prop="machine_cd" label="設備CD" width="96" align="center" sortable>
              <template #default="{ row }">
                <span class="ee-code ee-code--machine">{{ row.machine_cd }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="machines_name" label="設備名" min-width="130" sortable show-overflow-tooltip>
              <template #default="{ row }">
                <span class="ee-name">{{ row.machines_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_cd" label="製品CD" width="96" align="center" sortable>
              <template #default="{ row }">
                <span class="ee-code ee-code--product">{{ row.product_cd }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="製品名" min-width="140" sortable show-overflow-tooltip />
            <el-table-column prop="efficiency_rate" label="能率" width="100" align="center">
              <template #default="{ row }">
                <span class="ee-eff-cell">
                  <span class="ee-eff-val">{{ row.efficiency_rate?.toFixed(1) }}</span>
                  <span v-if="row.unit" class="ee-eff-unit">{{ row.unit }}</span>
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="current_efficiency_rate" label="現在能率" width="92" align="center">
              <template #default="{ row }">
                <el-tooltip
                  v-if="row.current_efficiency_rate != null"
                  :content="currentRateTip(row)"
                  placement="top"
                >
                  <span class="ee-current">{{ Number(row.current_efficiency_rate).toFixed(1) }}</span>
                </el-tooltip>
                <span v-else class="ee-current ee-current--empty">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="step_time" label="段取" width="76" align="center">
              <template #default="{ row }">
                <span v-if="row.step_time != null" class="ee-step">{{ row.step_time }}<small class="ee-min">分</small></span>
                <span v-else class="ee-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状態" width="92" align="center">
              <template #default="{ row }">
                <div class="ee-status-cell">
                  <el-switch
                    v-model="row.status"
                    :active-value="1"
                    :inactive-value="0"
                    :disabled="!canEdit"
                    :loading="statusUpdatingId === row.id"
                    @change="(value) => handleStatusChange(row, value)"
                    size="small"
                  />
                  <span class="ee-status-lbl" :class="{ on: row.status === 1 }">
                    {{ row.status === 1 ? '有効' : '無効' }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="備考" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="ee-remarks">{{ row.remarks }}</span>
              </template>
            </el-table-column>
            <el-table-column v-if="canEdit || canDelete" label="操作" fixed="right" width="186" align="center">
              <template #default="{ row }">
                <div class="ee-row-actions">
                  <el-button
                    v-if="canEdit"
                    size="small"
                    link
                    class="ee-act ee-act--edit pb-btn-plain"
                    @click="openDialog(row)"
                    :icon="Edit"
                  >
                    編集
                  </el-button>
                  <el-tooltip content="現在能率を能率へ反映" placement="top" :disabled="row.current_efficiency_rate == null">
                    <el-button
                      v-if="canEdit"
                      size="small"
                      link
                      class="ee-act ee-act--apply pb-btn-plain"
                      :disabled="row.current_efficiency_rate == null || applyingId === row.id"
                      :loading="applyingId === row.id"
                      @click="handleApplyCurrentRate(row)"
                    >
                      反映
                    </el-button>
                  </el-tooltip>
                  <el-button
                    v-if="canDelete"
                    size="small"
                    link
                    class="ee-act ee-act--delete pb-btn-plain"
                    @click="handleDelete(row.id)"
                    :icon="Delete"
                  >
                    削除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <!-- 結果バー + ページング -->
      <div class="ee-result-bar">
        <span>表示: <b>{{ efficiencyList.length }}</b> / <b>{{ total }}</b> 件</span>
        <span v-if="activeProcessTab !== 'all'" class="ee-proc-tag" :class="`ee-proc-tag--${activeProcessTab}`">
          {{ processTypes.find((p) => p.value === activeProcessTab)?.label }}工程
        </span>
        <div class="ee-pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            size="small"
            background
            @size-change="handlePageSizeChange"
          />
        </div>
      </div>
    </div>

    <!-- ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      width="580px"
      :close-on-click-modal="false"
      :show-close="false"
      class="eef-dialog pb-std"
      destroy-on-close
    >
      <template #header>
        <div class="eef-dialog-hero pb-hero" :class="isEdit ? 'is-edit' : 'is-new'">
          <div class="pb-bubbles" aria-hidden="true" />
          <div class="eef-dialog-icon">
            <el-icon><component :is="isEdit ? Edit : Plus" /></el-icon>
          </div>
          <div class="eef-dialog-copy">
            <h3>{{ isEdit ? '能率設定編集' : '能率設定新規登録' }}</h3>
            <p>{{ isEdit ? '設備・製品ごとの能率と段取時間を更新します' : '設備と製品を選び、能率と段取時間を登録します' }}</p>
          </div>
          <el-icon class="eef-close" @click="dialogVisible = false"><Close /></el-icon>
        </div>
      </template>
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="110px"
        label-position="left"
        class="ee-form"
        size="default"
      >
        <div class="ee-form-section">
          <div class="ee-form-section-title"><span class="ee-form-section-dot" />設備・製品</div>
          <el-form-item label="設備" prop="machine_cd">
            <el-select
              v-model="formData.machine_cd"
              placeholder="選択…"
              filterable
              style="width: 100%"
              @change="handleEquipmentChange"
            >
              <el-option
                v-for="equipment in equipmentOptions"
                :key="equipment.value"
                :label="`${equipment.label} (${equipment.value})`"
                :value="equipment.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="設備名">
            <el-input v-model="formData.machines_name" disabled />
          </el-form-item>
          <el-form-item label="製品" prop="product_cd">
            <el-select
              v-model="formData.product_cd"
              placeholder="選択…"
              filterable
              style="width: 100%"
              @change="handleProductChange"
            >
              <el-option
                v-for="product in productOptions"
                :key="product.value"
                :label="`${product.label} (${product.value})`"
                :value="product.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="製品名">
            <el-input v-model="formData.product_name" disabled />
          </el-form-item>
        </div>
        <div class="ee-form-section ee-form-section--amber">
          <div class="ee-form-section-title"><span class="ee-form-section-dot" />能率設定</div>
          <div class="ee-form-row">
            <el-form-item label="能率" prop="efficiency_rate" class="ee-form-half">
              <el-input-number
                v-model="formData.efficiency_rate"
                :min="0"
                :max="10000"
                :precision="1"
                :step="0.1"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="段取時間" prop="step_time" class="ee-form-half">
              <el-input-number
                v-model="formData.step_time"
                :min="0"
                :max="9999"
                :precision="0"
                controls-position="right"
                style="width: 100%"
                placeholder="分"
              />
            </el-form-item>
          </div>
          <el-form-item label="状態" prop="status">
            <el-radio-group v-model="formData.status" class="ee-status-switch">
              <el-radio-button :value="1">有効</el-radio-button>
              <el-radio-button :value="0">無効</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="備考" prop="remarks">
            <el-input v-model="formData.remarks" type="textarea" :rows="2" placeholder="備考を入力…" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="ee-dialog-footer">
          <el-button class="eef-cancel" @click="dialogVisible = false">キャンセル</el-button>
          <el-button class="eef-save" :class="{ 'is-edit': isEdit }" @click="handleSubmit" :loading="submitting">
            <el-icon><Check /></el-icon>
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="missingVisible"
      title="生産性から追加"
      width="1000px"
      top="5vh"
      class="ee-dialog"
      :close-on-click-modal="false"
      append-to-body
    >
      <div v-loading="missingLoading" class="ee-missing">
        <p v-if="missingResult" class="ee-missing-desc">
          期間 <b>{{ missingResult.period_from }} 〜 {{ missingResult.period_to }}</b>
          の生産性（{{ missingResult.sources.join('・') }}）にあって、設備能率に未登録の組み合わせです。
          能率・現在能率には「実績数 ÷ 作業時間 × 95%」が入ります。
          実績件数が {{ LOW_SAMPLE_RECORDS }} 件未満の行は能率がぶれやすいため、必要に応じて外してください。
        </p>
        <el-table
          ref="missingTableRef"
          :data="missingResult?.candidates ?? []"
          size="small"
          border
          height="56vh"
          :row-key="(r: ProductivityMissingCandidate) => `${r.machine_cd}|${r.product_cd}`"
          empty-text="追加できる組み合わせはありません"
          @selection-change="(rows: ProductivityMissingCandidate[]) => (missingSelection = rows)"
        >
          <el-table-column type="selection" width="40" align="center" />
          <el-table-column prop="process" label="工程" width="64" align="center" />
          <el-table-column label="設備 / 検査員" min-width="130">
            <template #default="{ row }">
              {{ row.machines_name }} <span class="ee-filter-opt-cd">{{ row.machine_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品CD" width="90" align="center" />
          <el-table-column prop="product_name" label="製品名" min-width="150" show-overflow-tooltip />
          <el-table-column prop="actual_qty" label="実績数" width="80" align="right" />
          <el-table-column prop="work_hours" label="作業時間(h)" width="96" align="right" />
          <el-table-column label="実績件数" width="84" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.record_count < LOW_SAMPLE_RECORDS" type="warning" size="small">
                {{ row.record_count }}
              </el-tag>
              <span v-else>{{ row.record_count }}</span>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="76" align="center">
            <template #default="{ row }">
              <span class="ee-current">{{ Number(row.efficiency_rate).toFixed(1) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <p v-if="missingResult?.unknown_product_cds?.length" class="ee-missing-note">
          製品マスタに無い製品CDは対象外：{{ missingResult.unknown_product_cds.join('、') }}
        </p>
        <p v-if="missingResult?.unmatched_lines?.length" class="ee-missing-note">
          設備マスタに一致しないライン：
          {{ missingResult.unmatched_lines.map((u) => `${u.process} ${u.line_name}`).join('、') }}
        </p>
      </div>
      <template #footer>
        <div class="ee-dialog-footer">
          <span class="ee-missing-count">選択 {{ missingSelection.length }} / {{ missingResult?.candidates.length ?? 0 }} 件</span>
          <el-button @click="missingVisible = false">キャンセル</el-button>
          <el-button
            type="primary"
            :disabled="missingSelection.length === 0"
            :loading="missingAdding"
            @click="handleAddMissing"
          >
            選択した組み合わせを追加
          </el-button>
        </div>
      </template>
    </el-dialog>

    <EquipmentEfficiencyProcessOverview
      v-model="overviewVisible"
      :initial-process="activeProcessTab"
      :initial-keyword="filters.keyword"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Tools,
  Refresh,
  Plus,
  Search,
  Edit,
  Delete,
  Printer,
  Grid,
  DataAnalysis,
  Close,
  Check,
  DocumentAdd,
  Download,
} from '@element-plus/icons-vue'
import EquipmentEfficiencyProcessOverview from './EquipmentEfficiencyProcessOverview.vue'
import {
  fetchEquipmentEfficiencyList,
  createEquipmentEfficiency,
  updateEquipmentEfficiency,
  deleteEquipmentEfficiency,
  refreshEquipmentCurrentEfficiency,
  applyEquipmentCurrentEfficiency,
  fetchEquipmentEfficiencyFilterOptions,
  fetchProductivityMissing,
  addProductivityMissing,
  type EquipmentEfficiencyFilterPair,
  type ProductivityMissingCandidate,
  type ProductivityMissingResult,
  type EquipmentEfficiency,
  type EquipmentEfficiencyTabCounts,
} from '@/api/master/equipmentEfficiencyMaster'
import { fetchMachines } from '@/api/master/machineMaster'
import { getProductList } from '@/api/master/productMaster'
import type { FormInstance, FormRules, TableInstance } from 'element-plus'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'
import { downloadExcelMultiSheet } from '@/utils/excelExport'

const { canCreate, canEdit, canDelete, canExport } = useMasterOperationPermission()

defineOptions({ name: 'EquipmentEfficiencyManagement' })

const efficiencyList = ref<EquipmentEfficiency[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const tabCounts = ref<Partial<EquipmentEfficiencyTabCounts>>({})
const machineDistinctCount = ref(0)
const productDistinctCount = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const activeProcessTab = ref('all')
const statusUpdatingId = ref<number | null>(null)
const printing = ref(false)
const exporting = ref(false)
const overviewVisible = ref(false)
const refreshingCurrent = ref(false)
const applyingId = ref<number | null>(null)

/** 実績件数がこれ未満の候補は警告表示 */
const LOW_SAMPLE_RECORDS = 3
const missingVisible = ref(false)
const missingLoading = ref(false)
const missingAdding = ref(false)
const missingResult = ref<ProductivityMissingResult | null>(null)
const missingSelection = ref<ProductivityMissingCandidate[]>([])
const missingTableRef = ref<TableInstance>()

const processTypes = [
  { label: '全て', value: 'all' },
  { label: '切断', value: 'cutting' },
  { label: '面取', value: 'chamfering' },
  { label: '成型', value: 'forming' },
  { label: '溶接', value: 'welding' },
  { label: 'メッキ', value: 'plating' },
  { label: '検査', value: 'inspection' },
  { label: 'その他', value: 'other' },
]

const extractList = (response: any): any[] => {
  if (!response) return []
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.list)) return response.list
  if (Array.isArray(response?.data?.list)) return response.data.list
  if (Array.isArray(response?.data?.data)) return response.data.data
  if (Array.isArray(response?.result)) return response.result
  return []
}

const equipmentOptions = ref<Array<{ label: string; value: string }>>([])
const productOptions = ref<Array<{ label: string; value: string }>>([])

const formData = ref<Partial<EquipmentEfficiency>>({
  machine_cd: '',
  machines_name: '',
  product_cd: '',
  product_name: '',
  efficiency_rate: 0,
  step_time: undefined,
  unit: '',
  status: 1,
  remarks: '',
})

const formRules: FormRules = {
  machine_cd: [{ required: true, message: '設備を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  efficiency_rate: [
    { required: true, message: '能率を入力してください', trigger: 'blur' },
    { type: 'number', min: 0, message: '能率は0以上である必要があります', trigger: 'blur' },
  ],
}

const filters = ref({ keyword: '', machineCd: '', productCd: '' })

const filterPairs = ref<EquipmentEfficiencyFilterPair[]>([])

const compareOption = (a: string, b: string): number =>
  a.localeCompare(b, 'ja', { numeric: true, sensitivity: 'base' })

/** 選択中の工程タブに属する組み合わせのみ（「全て」は全件） */
const tabFilterPairs = computed(() => {
  const tab = activeProcessTab.value
  if (tab === 'all') return filterPairs.value
  return filterPairs.value.filter((p) => (p.process_type || 'other') === tab)
})

const machineFilterOptions = computed(() => {
  const map = new Map<string, string>()
  for (const p of tabFilterPairs.value) {
    const cd = p.machine_cd || ''
    if (cd && !map.has(cd)) map.set(cd, p.machines_name || cd)
  }
  return [...map.entries()]
    .map(([value, name]) => ({ value, label: `${name}（${value}）` }))
    .sort((a, b) => compareOption(a.label, b.label))
})

/** 設備選択時はその設備に登録された製品だけを候補にする */
const productFilterOptions = computed(() => {
  const mc = filters.value.machineCd
  const map = new Map<string, string>()
  for (const p of tabFilterPairs.value) {
    if (mc && p.machine_cd !== mc) continue
    const cd = p.product_cd || ''
    if (cd && !map.has(cd)) map.set(cd, p.product_name || cd)
  }
  return [...map.entries()]
    .map(([value, name]) => ({ value, name, label: `${name}（${value}）` }))
    .sort((a, b) => compareOption(a.name, b.name))
})

const loadFilterOptions = async () => {
  try {
    const res = (await fetchEquipmentEfficiencyFilterOptions()) as Record<string, any>
    const pairs = res?.data?.pairs ?? res?.pairs
    filterPairs.value = Array.isArray(pairs) ? pairs : []
  } catch (error) {
    console.error('絞込候補の読み込みに失敗:', error)
  }
}

const filterParams = () => {
  const kw = filters.value.keyword?.trim()
  return {
    ...(kw ? { keyword: kw } : {}),
    ...(filters.value.machineCd ? { machineCd: filters.value.machineCd } : {}),
    ...(filters.value.productCd ? { productCd: filters.value.productCd } : {}),
  }
}

const resetPageAndLoad = () => {
  if (currentPage.value === 1) {
    loadData()
  } else {
    currentPage.value = 1
  }
}

const handleMachineFilterChange = () => {
  const pc = filters.value.productCd
  if (pc && !productFilterOptions.value.some((p) => p.value === pc)) {
    filters.value.productCd = ''
  }
  resetPageAndLoad()
}

/** 検索キーワードに一致する総件数（タブラベル用・全タブ合計） */
const tabCountsAll = computed(() => tabCounts.value.all ?? 0)

const activeProcessLabel = computed(
  () => processTypes.find((p) => p.value === activeProcessTab.value)?.label ?? '全て'
)

const getProcessCount = (processType: string): number => {
  const key = processType as keyof EquipmentEfficiencyTabCounts
  const v = tabCounts.value[key]
  return typeof v === 'number' ? v : 0
}

const handleTabChange = () => {
  const mc = filters.value.machineCd
  if (mc && !machineFilterOptions.value.some((m) => m.value === mc)) {
    filters.value.machineCd = ''
  }
  const pc = filters.value.productCd
  if (pc && !productFilterOptions.value.some((p) => p.value === pc)) {
    filters.value.productCd = ''
  }
  resetPageAndLoad()
}

const tableIndexMethod = (index: number) => (currentPage.value - 1) * pageSize.value + index + 1

let keywordSearchTimer: ReturnType<typeof setTimeout> | null = null
const scheduleKeywordSearch = () => {
  if (keywordSearchTimer) clearTimeout(keywordSearchTimer)
  keywordSearchTimer = setTimeout(() => {
    if (currentPage.value === 1) {
      loadData()
    } else {
      currentPage.value = 1
    }
  }, 350)
}

const handlePageSizeChange = () => {
  currentPage.value = 1
}

const getRowClassName = () => 'ee-row'

const handleStatusChange = async (row: EquipmentEfficiency, value: number | string | boolean) => {
  if (!guardMasterOperation(canEdit)) return
  if (!row.id) return
  const previousStatus = row.status
  const newStatus = typeof value === 'number' ? value : Number(value)
  row.status = newStatus
  statusUpdatingId.value = row.id
  try {
    await updateEquipmentEfficiency(row.id, { status: newStatus })
    ElMessage.success('状態を更新しました')
  } catch (error) {
    row.status = previousStatus
    console.error('状態更新に失敗:', error)
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    statusUpdatingId.value = null
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await fetchEquipmentEfficiencyList({
      page: currentPage.value,
      pageSize: pageSize.value,
      processType: activeProcessTab.value,
      ...filterParams(),
    })
    const raw = result as Record<string, unknown>
    const data = (raw.success && raw.data ? raw.data : raw) as {
      list?: EquipmentEfficiency[]
      total?: number
      tab_counts?: EquipmentEfficiencyTabCounts
      machine_distinct_count?: number
      product_distinct_count?: number
    }
    efficiencyList.value = data.list || (raw.list as EquipmentEfficiency[]) || []
    total.value = typeof data.total === 'number' ? data.total : Number(raw.total) || 0
    if (data.tab_counts) tabCounts.value = data.tab_counts
    else if (raw.tab_counts) tabCounts.value = raw.tab_counts as EquipmentEfficiencyTabCounts
    machineDistinctCount.value = Number(data.machine_distinct_count ?? raw.machine_distinct_count ?? 0)
    productDistinctCount.value = Number(data.product_distinct_count ?? raw.product_distinct_count ?? 0)
  } catch (error) {
    console.error('能率データの読み込みに失敗:', error)
    ElMessage.error('能率データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

const loadEquipmentOptions = async () => {
  try {
    const result = (await fetchMachines()) as any
    const machineList = extractList(result)
    equipmentOptions.value = machineList.map((machine: any) => ({
      label: machine.machine_name || '',
      value: machine.machine_cd || '',
    }))
  } catch (error) {
    console.error('設備データの読み込みに失敗:', error)
    ElMessage.error('設備データの読み込みに失敗しました')
  }
}

const loadProductOptions = async () => {
  try {
    const result = await getProductList({ page: 1, pageSize: 10000 })
    const productList = extractList(result)
    productOptions.value = productList.map((product: any) => ({
      label: product.product_name || '',
      value: product.product_cd || '',
    }))
  } catch (error) {
    console.error('製品データの読み込みに失敗:', error)
    ElMessage.error('製品データの読み込みに失敗しました')
  }
}

const handleEquipmentChange = (value: string) => {
  const equipment = equipmentOptions.value.find((eq) => eq.value === value)
  if (equipment) {
    formData.value.machines_name = equipment.label
    formData.value.machine_cd = value
  }
}

const handleProductChange = (value: string) => {
  const product = productOptions.value.find((prod) => prod.value === value)
  if (product) {
    formData.value.product_name = product.label
    formData.value.product_cd = value
  }
}

const openDialog = (row?: EquipmentEfficiency) => {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  isEdit.value = !!row
  if (row) {
    formData.value = { ...row }
  } else {
    formData.value = {
      machine_cd: '',
      machines_name: '',
      product_cd: '',
      product_name: '',
      efficiency_rate: 0,
      step_time: undefined,
      unit: '',
      status: 1,
      remarks: '',
    }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && formData.value.id) {
        await updateEquipmentEfficiency(formData.value.id, formData.value)
        ElMessage.success('能率設定を更新しました')
      } else {
        await createEquipmentEfficiency(formData.value)
        ElMessage.success('能率設定を登録しました')
      }
      dialogVisible.value = false
      await Promise.all([loadData(), loadFilterOptions()])
    } catch (error) {
      console.error('保存に失敗:', error)
      ElMessage.error('保存に失敗しました')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (id?: number) => {
  if (!guardMasterOperation(canDelete)) return
  if (!id) return
  try {
    await ElMessageBox.confirm('この能率設定を削除しますか？', '確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
    await deleteEquipmentEfficiency(id)
    ElMessage.success('能率設定を削除しました')
    await Promise.all([loadData(), loadFilterOptions()])
    if (efficiencyList.value.length === 0 && currentPage.value > 1) {
      currentPage.value -= 1
      await loadData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('削除に失敗:', error)
      ElMessage.error('削除に失敗しました')
    }
  }
}

const currentRatePeriodLabel = (): string => {
  const today = new Date()
  const start = new Date(today.getFullYear(), today.getMonth() - 2, 1)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return `${fmt(start)} 〜 ${fmt(today)}`
}

const currentRateTip = (row: EquipmentEfficiency): string => {
  const at = row.current_efficiency_updated_at
  const when = at ? at.replace('T', ' ').slice(0, 16) : ''
  return when ? `更新日時 ${when}（直近3ヶ月の生産性 × 95%）` : '直近3ヶ月の生産性 × 95%'
}

const handleRefreshCurrentRate = async () => {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      `期間 ${currentRatePeriodLabel()} の生産性（実績数 ÷ 作業時間）を、製品と設備（検査は検査員）の組み合わせごとに集計し、95% を現在能率に書き込みます。能率そのものは変わりません。メッキ工程は集計対象外で、現在能率も変更しません。`,
      '現在能率を更新',
      { confirmButtonText: '更新', cancelButtonText: 'キャンセル', type: 'warning' }
    )
  } catch {
    return
  }
  refreshingCurrent.value = true
  try {
    const result = await refreshEquipmentCurrentEfficiency()
    ElMessage.success(
      `現在能率を更新しました（${result.period_from} 〜 ${result.period_to}、算出 ${result.updated} 件 / 実績なし ${result.cleared} 件 / 対象外 ${result.skipped} 件）`
    )
    await loadData()
  } catch (error) {
    console.error('現在能率の更新に失敗:', error)
    ElMessage.error('現在能率の更新に失敗しました')
  } finally {
    refreshingCurrent.value = false
  }
}

const openMissingDialog = async () => {
  if (!guardMasterOperation(canCreate)) return
  missingLoading.value = true
  missingSelection.value = []
  try {
    const result = await fetchProductivityMissing()
    if (!result.candidates.length) {
      ElMessage.info(
        `期間 ${result.period_from} 〜 ${result.period_to} の生産性に、未登録の組み合わせはありません`
      )
      return
    }
    missingResult.value = result
    missingVisible.value = true
    await nextTick()
    missingTableRef.value?.toggleAllSelection()
  } catch (error) {
    console.error('未登録組み合わせの取得に失敗:', error)
    ElMessage.error('未登録組み合わせの取得に失敗しました')
  } finally {
    missingLoading.value = false
  }
}

const handleAddMissing = async () => {
  if (!guardMasterOperation(canCreate)) return
  const items = missingSelection.value.map((c) => ({
    machine_cd: c.machine_cd,
    product_cd: c.product_cd,
  }))
  if (!items.length) return
  missingAdding.value = true
  try {
    const result = await addProductivityMissing(items)
    ElMessage.success(`${result.added} 件を追加しました`)
    missingVisible.value = false
    await Promise.all([loadData(), loadFilterOptions()])
  } catch (error) {
    console.error('生産性からの追加に失敗:', error)
    ElMessage.error('生産性からの追加に失敗しました')
  } finally {
    missingAdding.value = false
  }
}

const handleApplyCurrentRate = async (row: EquipmentEfficiency) => {
  if (!guardMasterOperation(canEdit)) return
  if (!row.id || row.current_efficiency_rate == null) return
  const next = Number(row.current_efficiency_rate).toFixed(1)
  try {
    await ElMessageBox.confirm(
      `現在能率 ${next} を能率に反映しますか？`,
      '能率へ反映',
      { confirmButtonText: '反映', cancelButtonText: 'キャンセル', type: 'warning' }
    )
  } catch {
    return
  }
  applyingId.value = row.id
  try {
    const updated = await applyEquipmentCurrentEfficiency(row.id)
    row.efficiency_rate = updated.efficiency_rate
    row.current_efficiency_rate = updated.current_efficiency_rate
    ElMessage.success('能率を更新しました')
  } catch (error) {
    console.error('能率への反映に失敗:', error)
    ElMessage.error('能率への反映に失敗しました')
  } finally {
    applyingId.value = null
  }
}

const clearFilters = () => {
  filters.value = { keyword: '', machineCd: '', productCd: '' }
  resetPageAndLoad()
}

function escHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const fetchFilteredListForPrint = async (): Promise<EquipmentEfficiency[]> => {
  const fetchSize = Math.max(total.value, efficiencyList.value.length, 1)
  const result = await fetchEquipmentEfficiencyList({
    page: 1,
    pageSize: Math.min(fetchSize, 99999),
    processType: activeProcessTab.value,
    ...filterParams(),
  })
  const raw = result as Record<string, unknown>
  const data = (raw.success && raw.data ? raw.data : raw) as { list?: EquipmentEfficiency[] }
  return data.list || (raw.list as EquipmentEfficiency[]) || []
}

const formatEfficiencyRate = (row: EquipmentEfficiency): string => {
  const rate = row.efficiency_rate
  if (rate == null || Number.isNaN(Number(rate))) return '—'
  const text = Number(rate).toFixed(1)
  return row.unit ? `${text} ${row.unit}` : text
}

const formatStepTime = (row: EquipmentEfficiency): string => {
  if (row.step_time == null) return '—'
  return `${row.step_time}分`
}

const formatStatusLabel = (status?: number): string => (status === 1 ? '有効' : '無効')

const compareJa = (a: string, b: string): number =>
  a.localeCompare(b, 'ja', { numeric: true, sensitivity: 'base' })

type PrintEquipmentGroup = {
  machineCd: string
  machinesName: string
  rows: EquipmentEfficiency[]
}

const groupRowsForPrint = (rows: EquipmentEfficiency[]): PrintEquipmentGroup[] => {
  const map = new Map<string, EquipmentEfficiency[]>()
  for (const row of rows) {
    const key = `${row.machine_cd || ''}\t${row.machines_name || ''}`
    const group = map.get(key)
    if (group) group.push(row)
    else map.set(key, [row])
  }

  return [...map.entries()]
    .sort(([, aRows], [, bRows]) =>
      compareJa(aRows[0]?.machines_name || '', bRows[0]?.machines_name || '')
    )
    .map(([key, groupRows]) => {
      const [machineCd = '', machinesName = ''] = key.split('\t')
      return {
        machineCd,
        machinesName,
        rows: [...groupRows].sort((a, b) => compareJa(a.product_name || '', b.product_name || '')),
      }
    })
}

const buildPrintHtml = (rows: EquipmentEfficiency[]): string => {
  const title = '設備能率管理（絞込結果）'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const keyword = filters.value.keyword?.trim()
  const machineLabel = machineFilterOptions.value.find((m) => m.value === filters.value.machineCd)?.label
  const productLabel = productFilterOptions.value.find((p) => p.value === filters.value.productCd)?.label
  const keywordLine =
    (keyword ? `キーワード：<strong>${escHtml(keyword)}</strong>　` : '') +
    (machineLabel ? `設備：<strong>${escHtml(machineLabel)}</strong>　` : '') +
    (productLabel ? `製品：<strong>${escHtml(productLabel)}</strong>　` : '')
  const groups = groupRowsForPrint(rows)
  let rowIndex = 0

  const sectionsHtml = groups
    .map((group) => {
      const groupTitle = group.machinesName
        ? `${group.machinesName}${group.machineCd ? `（${group.machineCd}）` : ''}`
        : group.machineCd || '—'
      const body = group.rows
        .map((row) => {
          rowIndex += 1
          return `<tr>
            <td class="cen">${escHtml(String(rowIndex))}</td>
            <td class="cen">${escHtml(row.product_cd || '—')}</td>
            <td class="left">${escHtml(row.product_name || '—')}</td>
            <td class="num">${escHtml(formatEfficiencyRate(row))}</td>
            <td class="cen">${escHtml(formatStepTime(row))}</td>
            <td class="cen">${escHtml(formatStatusLabel(row.status))}</td>
            <td class="left">${escHtml(row.remarks || '—')}</td>
          </tr>`
        })
        .join('')

      return `<section class="print-sec">
        <div class="grp-title">${escHtml(groupTitle)}</div>
        <table>
          <thead>
            <tr>
              <th class="cen">#</th>
              <th class="cen">製品CD</th>
              <th class="left">製品名</th>
              <th class="num">能率</th>
              <th class="cen">段取</th>
              <th class="cen">状態</th>
              <th class="left">備考</th>
            </tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      </section>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body {
      margin: 0;
      padding: 10px 12px 14px;
      color: #0f172a;
      font: 9.5px/1.35 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif;
      background: #fff;
    }
    .hd {
      margin-bottom: 10px;
      padding: 10px 12px;
      border: 1px solid #dbe5f1;
      border-radius: 8px;
      background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
    }
    .tt { font-size: 14px; font-weight: 800; color: #1e3a8a; }
    .meta { margin-top: 4px; color: #475569; font-size: 8.5px; line-height: 1.55; }
    .meta strong { color: #334155; font-weight: 700; }
    .print-sec { margin-bottom: 12px; break-inside: avoid; page-break-inside: avoid; }
    .grp-title {
      font-size: 10px;
      font-weight: 800;
      color: #1e293b;
      margin: 0 0 4px 2px;
      padding: 3px 0;
      border-bottom: 2px solid #94a3b8;
    }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 3px 4px;
      word-wrap: break-word;
      overflow-wrap: anywhere;
    }
    th {
      background: linear-gradient(180deg, #eaf3ff 0%, #dceafe 100%);
      font-weight: 800;
      color: #334155;
      font-size: 8.5px;
    }
    tbody tr:nth-child(odd) { background: #fcfdff; }
    tbody tr:nth-child(even) { background: #f7fbff; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .cen { text-align: center; }
    @media print {
      @page { size: A4 portrait; margin: 10mm; }
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">
      ${keywordLine}工程：<strong>${escHtml(activeProcessLabel.value)}</strong>
      　件数：<strong>${escHtml(String(rows.length))}</strong> 件
      　印刷日時：${escHtml(printedAt)}
    </div>
  </div>
  ${sectionsHtml}
</body>
</html>`
}

const handlePrint = async () => {
  if (!guardMasterOperation(canExport)) return
  if (total.value === 0 && efficiencyList.value.length === 0) {
    ElMessage.warning('印刷対象の行がありません（絞込みを確認してください）')
    return
  }

  printing.value = true
  try {
    const rows = await fetchFilteredListForPrint()
    if (rows.length === 0) {
      ElMessage.warning('印刷対象の行がありません（絞込みを確認してください）')
      return
    }

    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました')
      return
    }

    printWindow.document.write(buildPrintHtml(rows))
    printWindow.document.close()
    printWindow.onload = () => {
      printWindow.print()
      setTimeout(() => printWindow.close(), 400)
    }
  } catch (error) {
    console.error('印刷に失敗:', error)
    ElMessage.error('印刷データの取得に失敗しました')
  } finally {
    printing.value = false
  }
}

const EXCEL_HEADERS = [
  '工程',
  '設備CD',
  '設備名',
  '製品CD',
  '製品名',
  '能率',
  '単位',
  '現在能率',
  '現在能率更新日時',
  'ステップタイム(分)',
  '状態',
  '備考',
]

const processLabelOf = (value: string): string =>
  processTypes.find((p) => p.value === value)?.label || 'その他'

const buildExcelAoa = (rows: EquipmentEfficiency[]): (string | number | null)[][] => {
  const processByMachine = new Map<string, string>()
  for (const p of filterPairs.value) {
    if (p.machine_cd && !processByMachine.has(p.machine_cd)) {
      processByMachine.set(p.machine_cd, p.process_type || 'other')
    }
  }
  const toNum = (v: unknown): number | null =>
    v == null || v === '' || Number.isNaN(Number(v)) ? null : Number(v)

  return [
    EXCEL_HEADERS,
    ...rows.map((row) => [
      activeProcessTab.value === 'all'
        ? processLabelOf(processByMachine.get(row.machine_cd || '') || 'other')
        : activeProcessLabel.value,
      row.machine_cd || '',
      row.machines_name || '',
      row.product_cd || '',
      row.product_name || '',
      toNum(row.efficiency_rate),
      row.unit || '',
      toNum(row.current_efficiency_rate),
      row.current_efficiency_updated_at
        ? row.current_efficiency_updated_at.replace('T', ' ').slice(0, 16)
        : '',
      toNum(row.step_time),
      formatStatusLabel(row.status),
      row.remarks || '',
    ]),
  ]
}

const handleExportExcel = async () => {
  if (!guardMasterOperation(canExport)) return
  exporting.value = true
  try {
    const rows = await fetchFilteredListForPrint()
    if (rows.length === 0) {
      ElMessage.warning('出力対象の行がありません（絞込みを確認してください）')
      return
    }
    const now = new Date()
    const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(
      now.getDate()
    ).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(
      now.getMinutes()
    ).padStart(2, '0')}`
    const label = activeProcessLabel.value
    await downloadExcelMultiSheet(
      [{ name: `設備能率_${label}`, aoa: buildExcelAoa(rows) }],
      `設備能率管理_${label}_${stamp}.xlsx`
    )
    ElMessage.success(`${rows.length} 件を Excel に出力しました`)
  } catch (error) {
    console.error('Excel出力に失敗:', error)
    ElMessage.error('Excel出力に失敗しました')
  } finally {
    exporting.value = false
  }
}

let listWatchReady = false
watch([currentPage, pageSize], () => {
  if (!listWatchReady) return
  loadData()
})

onMounted(async () => {
  await Promise.all([loadEquipmentOptions(), loadProductOptions(), loadFilterOptions()])
  listWatchReady = true
  await loadData()
})
</script>

<style scoped>
/* ===== Layout ===== */
.ee-container {
  min-height: 100vh;
  padding: 12px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-family: 'Inter', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
  background: linear-gradient(180deg, #f1f8e4 0%, #f8fafc 240px, #f8fafc 100%);
}

/* ===== Header（olive → lime → gold） ===== */
.ee-header {
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(125deg, #365314 0%, #4d7c0f 34%, #65a30d 66%, #ca8a04 100%);
  box-shadow: 0 10px 24px -12px rgba(63, 98, 18, 0.5);
}

.ee-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.ee-title-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.ee-title-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.ee-title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: #fff;
}

.ee-subtitle {
  margin: 0;
  color: rgba(247, 254, 231, 0.92);
}

.ee-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.ee-stat {
  --sc: #4d7c0f;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #fff;
  box-shadow:
    inset 0 -2px 0 color-mix(in srgb, var(--sc) 14%, transparent),
    0 4px 10px -6px rgba(26, 46, 5, 0.45);
}

.ee-stat--0 { --sc: #4d7c0f; }
.ee-stat--1 { --sc: #0284c7; }
.ee-stat--2 { --sc: #7c3aed; }
.ee-stat--3 { --sc: #d97706; }

.ee-stat-lbl {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #64748b;
  white-space: nowrap;
}

.ee-stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--sc);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--sc) 22%, transparent);
}

.ee-stat-num {
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
  color: var(--sc);
  font-variant-numeric: tabular-nums;
}

/* ===== Toolbar ===== */
.ee-toolbar {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 11px 14px 8px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2eccf;
  box-shadow: 0 4px 12px -8px rgba(63, 98, 18, 0.3);
}

.ee-toolbar::before,
.ee-table-wrap::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, #4d7c0f, #65a30d, #a3e635, #ca8a04);
}

.ee-search {
  flex: 1;
  max-width: 360px;
}

.ee-search :deep(.el-input__wrapper) {
  height: 32px;
  border-radius: 9px;
  box-shadow: inset 0 0 0 1px #dfe7d2;
  transition: box-shadow 0.15s ease;
}

.ee-search :deep(.el-input__wrapper:hover) {
  box-shadow: inset 0 0 0 1px #a3e635;
}

.ee-search :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px #65a30d,
    0 0 0 3px rgba(101, 163, 13, 0.15);
}

.ee-filter-select {
  width: 170px;
}

.ee-filter-select--product {
  width: 230px;
}

.ee-filter-select :deep(.el-select__wrapper) {
  min-height: 32px;
  border-radius: 8px;
}

.ee-filter-opt-cd {
  float: right;
  margin-left: 12px;
  font-family: 'Consolas', monospace;
  font-size: 11px;
  color: #94a3b8;
}

.ee-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-left: auto;
}

.ee-toolbar .ee-btn {
  --b-from: #ffffff;
  --b-to: #f1f5f9;
  --b-line: #d6dde8;
  --k-rgb: 100 116 139;
  height: 32px;
  padding: 0 14px;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  border: 1px solid var(--b-line);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, var(--b-from), var(--b-to));
}

.ee-toolbar .ee-btn:hover,
.ee-toolbar .ee-btn:focus-visible {
  color: #fff;
  border-color: var(--b-line);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, var(--b-from), var(--b-to));
}

.ee-toolbar .ee-btn--clear,
.ee-toolbar .ee-btn--clear:hover,
.ee-toolbar .ee-btn--clear:focus-visible {
  color: #475569;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}

.ee-toolbar .ee-btn--overview {
  --b-from: #38bdf8;
  --b-to: #0284c7;
  --b-line: #0369a1;
  --k-rgb: 2 132 199;
}

.ee-toolbar .ee-btn--print {
  --b-from: #34d399;
  --b-to: #059669;
  --b-line: #047857;
  --k-rgb: 5 150 105;
}

.ee-toolbar .ee-btn--excel {
  --b-from: #2dd4bf;
  --b-to: #0f766e;
  --b-line: #115e59;
  --k-rgb: 15 118 110;
}

.ee-toolbar .ee-btn--rate {
  --b-from: #fbbf24;
  --b-to: #d97706;
  --b-line: #b45309;
  --k-rgb: 217 119 6;
}

.ee-toolbar .ee-btn--import {
  --b-from: #a78bfa;
  --b-to: #7c3aed;
  --b-line: #6d28d9;
  --k-rgb: 124 58 237;
}

.ee-toolbar .ee-btn--add {
  --b-from: #84cc16;
  --b-to: #4d7c0f;
  --b-line: #3f6212;
  --k-rgb: 77 124 15;
  padding: 0 16px;
}

/* ===== Table Section ===== */
.ee-table-wrap {
  position: relative;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-top: 3px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2eccf;
  box-shadow: 0 6px 18px -12px rgba(63, 98, 18, 0.35);
}

/* 工程タブ：工程ごとに色分け */
.ee-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.ee-tabs > :deep(.el-tabs__header) {
  margin: 0;
  padding: 8px 12px;
  background: #fafcf6;
  border-bottom: 1px solid #edf2e3;
}

.ee-tabs > :deep(.el-tabs__header .el-tabs__nav-wrap::after),
.ee-tabs > :deep(.el-tabs__header .el-tabs__active-bar) {
  display: none;
}

.ee-tabs > :deep(.el-tabs__header .el-tabs__nav) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border: none;
}

.ee-tabs > :deep(.el-tabs__header .el-tabs__item) {
  --tc: #4d7c0f;
  height: 28px;
  padding: 0 12px !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 28px;
  color: var(--tc);
  background: color-mix(in srgb, var(--tc) 8%, #fff);
  border: 1px solid color-mix(in srgb, var(--tc) 24%, #fff);
  transition:
    background-color 0.15s ease,
    color 0.15s ease,
    border-color 0.15s ease;
}

.ee-tabs > :deep(.el-tabs__header .el-tabs__item::before) {
  content: '';
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--tc);
}

.ee-tabs > :deep(.el-tabs__header #tab-all) { --tc: #4d7c0f; }
.ee-tabs > :deep(.el-tabs__header #tab-cutting) { --tc: #2563eb; }
.ee-tabs > :deep(.el-tabs__header #tab-chamfering) { --tc: #0891b2; }
.ee-tabs > :deep(.el-tabs__header #tab-forming) { --tc: #059669; }
.ee-tabs > :deep(.el-tabs__header #tab-welding) { --tc: #dc2626; }
.ee-tabs > :deep(.el-tabs__header #tab-plating) { --tc: #ca8a04; }
.ee-tabs > :deep(.el-tabs__header #tab-inspection) { --tc: #db2777; }
.ee-tabs > :deep(.el-tabs__header #tab-other) { --tc: #64748b; }

.ee-tabs > :deep(.el-tabs__header .el-tabs__item:hover) {
  background: color-mix(in srgb, var(--tc) 14%, #fff);
  border-color: color-mix(in srgb, var(--tc) 40%, #fff);
}

.ee-tabs > :deep(.el-tabs__header .el-tabs__item.is-active) {
  color: #fff;
  border-color: color-mix(in srgb, var(--tc) 80%, #000);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0) 55%),
    linear-gradient(135deg, color-mix(in srgb, var(--tc) 78%, #fff), var(--tc));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.16),
    0 3px 8px -3px color-mix(in srgb, var(--tc) 60%, transparent);
}

.ee-tabs > :deep(.el-tabs__header .el-tabs__item.is-active::before) {
  background: #fff;
}

.ee-tabs > :deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
}

.ee-tabs > :deep(.el-tabs__content .el-tab-pane) {
  height: 100%;
}

/* 一覧：文字色・背景を統一、1行表示 */
.ee-table {
  --el-table-border-color: #edf1e6;
  --el-table-row-hover-bg-color: #f4faea;
  --el-table-header-bg-color: #f4f8ec;
  --el-table-text-color: #334155;
  font-size: 12px;
  color: #334155;
}

.ee-table :deep(th.el-table__cell) {
  padding: 6px 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #3f6212;
  background: #f4f8ec;
  border-bottom: 1px solid #dbe8c4;
}

.ee-table :deep(td.el-table__cell) {
  padding: 4px 0;
}

.ee-table :deep(.cell) {
  padding: 0 8px;
  line-height: 22px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ee-table :deep(th.el-table__cell .cell) {
  line-height: 18px;
}

.ee-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #fbfdf8;
}

.ee-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f4faea;
}

.ee-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #84cc16;
}

.ee-table :deep(td.el-table__cell:first-child .cell) {
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.ee-code {
  --cc: #4d7c0f;
  display: inline-block;
  max-width: 100%;
  padding: 0 7px;
  border-radius: 6px;
  font-family: Consolas, Monaco, monospace;
  font-size: 11px;
  font-weight: 700;
  line-height: 20px;
  vertical-align: middle;
  color: var(--cc);
  background: color-mix(in srgb, var(--cc) 8%, #fff);
  border: 1px solid color-mix(in srgb, var(--cc) 22%, #fff);
  overflow: hidden;
  text-overflow: ellipsis;
}

.ee-code--machine { --cc: #4d7c0f; }
.ee-code--product { --cc: #0369a1; }

.ee-name {
  font-weight: 600;
  color: #1e293b;
}

.ee-remarks {
  color: #64748b;
}

.ee-muted {
  color: #cbd5e1;
}

.ee-eff-cell {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  max-width: 100%;
  padding: 0 8px;
  border-radius: 999px;
  line-height: 20px;
  background: #f4faea;
  border: 1px solid #d9f0b0;
}

.ee-eff-val {
  font-size: 12px;
  font-weight: 800;
  color: #3f6212;
  font-variant-numeric: tabular-nums;
}

.ee-eff-unit {
  font-size: 9px;
  color: #65a30d;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ee-current {
  display: inline-block;
  min-width: 42px;
  padding: 0 6px;
  border-radius: 999px;
  line-height: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #c2410c;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  cursor: default;
}

.ee-current--empty {
  color: #cbd5e1;
  font-weight: 500;
  background: transparent;
  border-color: transparent;
}

.ee-step {
  font-weight: 700;
  color: #475569;
  font-variant-numeric: tabular-nums;
}

.ee-min {
  margin-left: 1px;
  font-size: 9px;
  color: #94a3b8;
}

.ee-status-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  vertical-align: middle;
}

.ee-status-cell :deep(.el-switch.is-checked .el-switch__core) {
  background: #65a30d;
  border-color: #65a30d;
}

.ee-status-lbl {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
}

.ee-status-lbl.on {
  color: #4d7c0f;
  font-weight: 700;
}

.ee-row-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  vertical-align: middle;
}

.ee-row-actions .ee-act {
  --ac: #2563eb;
  height: 22px;
  margin: 0;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ac);
  background: color-mix(in srgb, var(--ac) 8%, #fff);
  border: 1px solid color-mix(in srgb, var(--ac) 24%, #fff);
}

.ee-row-actions .ee-act:hover,
.ee-row-actions .ee-act:focus-visible {
  color: #fff;
  background: var(--ac);
  border-color: var(--ac);
}

.ee-row-actions .ee-act--edit { --ac: #2563eb; }
.ee-row-actions .ee-act--apply { --ac: #d97706; }
.ee-row-actions .ee-act--delete { --ac: #e11d48; }

.ee-row-actions .ee-act.is-disabled,
.ee-row-actions .ee-act.is-disabled:hover {
  color: #94a3b8;
  background: #e5e7eb;
  border-color: #d1d5db;
}

.ee-row-actions .ee-act + .ee-act {
  margin-left: 0;
}

/* Result bar */
.ee-result-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 16px;
  font-size: 12px;
  color: #64748b;
  background: #fafcf6;
  border-top: 1px solid #edf2e3;
}

.ee-result-bar b {
  color: #4d7c0f;
}

.ee-pagination-wrap {
  flex: 1 1 auto;
  display: flex;
  justify-content: flex-end;
  min-width: 0;
  margin-left: auto;
}

.ee-pagination-wrap :deep(.el-pagination) {
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 4px;
}

.ee-pagination-wrap :deep(.el-pager li.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #84cc16, #4d7c0f) !important;
}

.ee-proc-tag {
  --tc: #4d7c0f;
  display: inline-flex;
  align-items: center;
  padding: 1px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--tc);
  background: color-mix(in srgb, var(--tc) 10%, #fff);
  border: 1px solid color-mix(in srgb, var(--tc) 28%, #fff);
}

.ee-proc-tag--cutting { --tc: #2563eb; }
.ee-proc-tag--chamfering { --tc: #0891b2; }
.ee-proc-tag--forming { --tc: #059669; }
.ee-proc-tag--welding { --tc: #dc2626; }
.ee-proc-tag--plating { --tc: #ca8a04; }
.ee-proc-tag--inspection { --tc: #db2777; }
.ee-proc-tag--other { --tc: #64748b; }

/* ===== Dialog（append 先で scope 属性が付かないため外枠は :global で指定） ===== */
:global(.el-dialog.eef-dialog) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 24px 48px -16px rgba(63, 98, 18, 0.4),
    0 0 0 1px rgba(101, 163, 13, 0.12);
}

:global(.el-dialog.eef-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}

:global(.el-dialog.eef-dialog .el-dialog__body) {
  padding: 14px 16px 4px;
  background: linear-gradient(180deg, #f8fbf3, #f5f7fb);
}

:global(.el-dialog.eef-dialog .el-dialog__footer) {
  padding: 12px 18px 14px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.eef-dialog-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #fff;
  background: linear-gradient(125deg, #3f6212 0%, #4d7c0f 34%, #65a30d 68%, #84cc16 100%);
}

.eef-dialog-hero.is-edit {
  background: linear-gradient(125deg, #b45309 0%, #d97706 40%, #f59e0b 76%, #fbbf24 100%);
}

.eef-dialog-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.18);
}

.eef-dialog-copy {
  flex: 1;
  min-width: 0;
}

.eef-dialog-copy h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
}

.eef-dialog-copy p {
  margin: 3px 0 0;
  overflow: hidden;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.88);
}

.eef-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 9px;
  font-size: 18px;
  color: #fff;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: background 0.2s ease;
}

.eef-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.ee-form {
  display: flex;
  flex-direction: column;
}

.ee-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.ee-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.ee-form-section {
  --accent: #65a30d;
  position: relative;
  overflow: hidden;
  margin-bottom: 10px;
  padding: 12px 14px 2px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #e2e8f0);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.ee-form-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 30%, #fff));
}

.ee-form-section--amber {
  --accent: #d97706;
}

.ee-form-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #334155;
}

.ee-form-section-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
}

.ee-form-row {
  display: flex;
  gap: 12px;
}

.ee-form-half {
  flex: 1;
}

.ee-form :deep(.el-input__wrapper),
.ee-form :deep(.el-select__wrapper),
.ee-form :deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: inset 0 0 0 1px #dfe7d2;
  transition: box-shadow 0.15s ease;
}

.ee-form :deep(.el-input__wrapper:hover),
.ee-form :deep(.el-select__wrapper:hover),
.ee-form :deep(.el-textarea__inner:hover) {
  box-shadow: inset 0 0 0 1px #a3e635;
}

.ee-form :deep(.el-input__wrapper.is-focus),
.ee-form :deep(.el-select__wrapper.is-focused),
.ee-form :deep(.el-textarea__inner:focus) {
  box-shadow:
    inset 0 0 0 1px #65a30d,
    0 0 0 3px rgba(101, 163, 13, 0.14);
}

.ee-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f1f5f9;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

.ee-status-switch :deep(.el-radio-button__inner) {
  font-weight: 700;
  color: #4d7c0f;
}

.ee-status-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  border-color: #4d7c0f;
  background: linear-gradient(135deg, #84cc16, #4d7c0f);
  box-shadow: -1px 0 0 0 #4d7c0f;
}

.ee-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.ee-missing-desc {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
}

.ee-missing-note {
  margin: 8px 0 0;
  font-size: 11px;
  color: #b45309;
}

.ee-missing-count {
  margin-right: auto;
  align-self: center;
  font-size: 12px;
  color: #64748b;
}

.ee-dialog-footer .eef-cancel {
  --k-rgb: 100 116 139;
  height: 34px;
  border-radius: 9px;
  font-weight: 700;
  color: #475569;
  border: 1px solid #d6dde8;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}

.ee-dialog-footer .eef-save {
  --k-rgb: 77 124 15;
  min-width: 104px;
  height: 34px;
  border-radius: 9px;
  font-weight: 800;
  color: #fff;
  border: 1px solid #3f6212;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #84cc16, #4d7c0f);
}

.ee-dialog-footer .eef-save:hover,
.ee-dialog-footer .eef-save:focus-visible {
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #a3e635, #65a30d);
}

.ee-dialog-footer .eef-save.is-edit {
  --k-rgb: 217 119 6;
  border-color: #b45309;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #f59e0b, #d97706);
}

.ee-dialog-footer .eef-save.is-edit:hover,
.ee-dialog-footer .eef-save.is-edit:focus-visible {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fbbf24, #f59e0b);
}

.ee-dialog-footer .eef-save .el-icon {
  margin-right: 4px;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .ee-container {
    padding: 8px 10px 16px;
  }
  .ee-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .ee-stats {
    width: 100%;
  }
  .ee-toolbar {
    flex-wrap: wrap;
  }
  .ee-search {
    max-width: 100%;
    flex-basis: 100%;
  }
  .ee-filter-select,
  .ee-filter-select--product {
    flex: 1 1 140px;
    width: auto;
  }
  .btn-label {
    display: none;
  }
  .ee-form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
