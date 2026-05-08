<template>
  <div class="ea-page">
    <!-- ===== ヘッダー ===== -->
    <div class="ea-header">
      <div class="ea-header-left">
        <div class="ea-title-row">
          <el-icon class="ea-title-icon" :size="20"><Setting /></el-icon>
          <div>
            <h1 class="ea-title">ローラー使用管理</h1>
            <p class="ea-subtitle">ローラーの使用状況・交換予測・実施登録を管理します</p>
          </div>
        </div>
      </div>
      <div class="ea-header-actions">
        <el-button size="small" class="ea-head-btn ea-btn-log" @click="openLogManageDialog">
          <el-icon><List /></el-icon>
          使用ログ管理
        </el-button>
        <el-button size="small" class="ea-head-btn ea-btn-master" @click="goRollerMaster">
          <el-icon><Histogram /></el-icon>
          ローラーマスタ
        </el-button>
        <el-button size="small" class="ea-head-btn ea-btn-bom" @click="goRollerBom">
          <el-icon><Connection /></el-icon>
          ローラーBOM管理
        </el-button>
        <el-button size="small" class="ea-head-btn ea-btn-sync" :loading="syncing" @click="handleSync">
          <el-icon><Refresh /></el-icon>
          マスタ同期
        </el-button>
        <el-button size="small" class="ea-head-btn ea-btn-calc" :loading="recalculating" @click="handleRecalculate">
          <el-icon><DataAnalysis /></el-icon>
          予測再計算
        </el-button>
        <el-button size="small" class="ea-head-btn ea-btn-print" :loading="printingList" @click="printMainListReport">
          <el-icon><Printer /></el-icon>
          一覧印刷
        </el-button>
      </div>
    </div>

    <!-- ===== ツールバー ===== -->
    <div class="ea-toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="ローラーCD・種類・設備で検索…"
        clearable
        class="ea-search"
        size="small"
        @input="onKeywordInput"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>

      <el-select
        v-model="filters.machine_cd"
        placeholder="設備で絞込"
        clearable
        filterable
        class="ea-filter-select"
        size="small"
        @change="onFilterChange"
      >
        <el-option
          v-for="m in formingMachineOptions"
          :key="m.value"
          :label="`${m.label} (${m.value})`"
          :value="m.value"
        />
      </el-select>

      <el-select
        v-model="filters.exec_type"
        placeholder="実施内容で絞込"
        clearable
        class="ea-filter-select"
        size="small"
        @change="onFilterChange"
      >
        <el-option v-for="t in execTypeOptions" :key="t" :label="t" :value="t" />
      </el-select>

      <div class="ea-toolbar-right">
        <el-button text size="small" :icon="RefreshLeft" @click="clearFilters">クリア</el-button>
      </div>
    </div>

    <!-- ===== メインテーブル ===== -->
    <div class="ea-table-wrap">
      <el-table
        ref="mainTableRef"
        :data="rows"
        v-loading="loading"
        stripe
        border
        size="small"
        class="ea-table"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        :row-class-name="rowClassName"
        height="calc(100vh - 250px)"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="roller_cd" label="CD" width="70" fixed show-overflow-tooltip />
        <el-table-column
          prop="roller_type"
          label="ローラー種類"
          width="150"
          show-overflow-tooltip
          sortable="custom"
        />
        <!-- <el-table-column prop="machine_cd" label="設備CD" width="80" align="center" show-overflow-tooltip /> -->
        <el-table-column prop="machine_name" label="設備名" width="80" show-overflow-tooltip />
        <el-table-column prop="exchange_freq_qty" label="交換本数" width="110" align="center">
          <template #default="{ row }">{{ row.exchange_freq_qty ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="exchange_freq_month" label="交換月" width="110" align="center" sortable="custom">
          <template #default="{ row }">{{ row.exchange_freq_month ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="cleaning_freq_month" label="清掃月" width="100" align="center" sortable="custom">
          <template #default="{ row }">{{ row.cleaning_freq_month ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="exec_type" label="実施内容" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              v-if="row.exec_type"
              :type="row.exec_type === 'ローラー交換' ? 'warning' : 'success'"
              size="small"
              effect="light"
            >{{ row.exec_type }}</el-tag>
            <span v-else class="ea-dash">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_exec_date" label="前回実施日" width="105" align="center">
          <template #default="{ row }">{{ row.last_exec_date ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="prod_cumulative_qty" label="生産数累計" width="100" align="right">
          <template #default="{ row }">{{ fmtNum(row.prod_cumulative_qty) }}</template>
        </el-table-column>
        <el-table-column prop="prod_manual_addon_qty" label="手入力補正" width="95" align="right">
          <template #default="{ row }">{{ fmtSignedQty(row.prod_manual_addon_qty) }}</template>
        </el-table-column>
        <el-table-column label="合計" width="100" align="right">
          <template #default="{ row }">{{ prodQtyTotal(row).toLocaleString('ja-JP') }}</template>
        </el-table-column>
        <el-table-column prop="planned_product_cd" label="予定段取品" width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.planned_product_cd ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="next_exec_date" label="実施日" width="105" align="center" sortable="custom">
          <template #default="{ row }">
            <span :class="nextDateClass(row.next_exec_date)">
              {{ row.next_exec_date ?? '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="exchange_remaining_qty" label="残数" width="90" align="right" sortable="custom">
          <template #default="{ row }">
            <span :class="remainingClass(row.exchange_remaining_qty)">
              {{ fmtNum(row.exchange_remaining_qty) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" min-width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :icon="Edit" @click="openEditDialog(row)">
              修正
            </el-button>
            <el-button type="success" link size="small" :icon="DocumentAdd" @click="openLogDialog(row)">
              実施登録
            </el-button>
            <el-button type="info" link size="small" :icon="List" @click="openHistoryDrawer(row)">
              履歴
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="ea-result-bar">
        <span>表示 <b>{{ rows.length }}</b> / <b>{{ total }}</b> 件</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          size="small"
          background
          @current-change="loadData"
          @size-change="() => { currentPage = 1; loadData() }"
        />
      </div>
    </div>

    <!-- ===== 手動修正ダイアログ ===== -->
    <el-dialog
      v-model="editDialogVisible"
      title="ローラー使用状況 修正"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
      class="ea-dialog"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        label-position="top"
        class="ea-form"
      >
        <div class="ea-dialog-grid">
          <el-form-item label="ローラーCD">
            <el-input v-model="editForm.roller_cd" disabled />
          </el-form-item>
          <el-form-item label="ローラー種類">
            <el-input :model-value="editDialogRollerType || '—'" disabled />
          </el-form-item>
          <el-form-item label="実施内容">
            <el-select v-model="editForm.exec_type" clearable style="width:100%">
              <el-option v-for="t in execTypeOptions" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="前回実施日">
            <el-date-picker v-model="editForm.last_exec_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="生産数累計">
            <el-input-number v-model="editForm.prod_cumulative_qty" :min="0" :step="1" style="width:100%" />
          </el-form-item>
          <el-form-item>
            <template #label>
              <span>手入力補正</span>
              <span style="font-weight:400;color:#64748b;font-size:11px;margin-left:6px">（自動累計に加算・マイナス可）</span>
            </template>
            <el-input-number v-model="editForm.prod_manual_addon_qty" :step="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="予定段取品">
            <el-input v-model="editForm.planned_product_cd" placeholder="製品CD" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="ea-dialog-footer">
          <el-button class="ea-btn-cancel" @click="editDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" class="ea-btn-save" :loading="editSubmitting" @click="submitEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ===== 実施登録ダイアログ ===== -->
    <el-dialog
      v-model="logDialogVisible"
      :title="logDialogTitle"
      width="560px"
      :close-on-click-modal="false"
      destroy-on-close
      class="ea-dialog"
    >
      <el-form
        ref="logFormRef"
        :model="logForm"
        :rules="logRules"
        label-position="top"
        class="ea-form"
      >
        <div class="ea-dialog-grid">
          <el-form-item label="ローラー種類" class="ea-span-full">
            <el-input :model-value="logDialogRollerType || '—'" disabled />
          </el-form-item>
          <el-form-item label="実施内容" prop="exec_type">
            <el-select v-model="logForm.exec_type" style="width:100%">
              <el-option v-for="t in execTypeOptions" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item label="実施日" prop="exec_date">
            <el-date-picker v-model="logForm.exec_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="管理CD">
            <el-input v-model="logForm.management_cd" placeholder="例: MG-001" />
          </el-form-item>
          <el-form-item label="備考" class="ea-span-full">
            <el-input v-model="logForm.note" type="textarea" :rows="2" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="ea-dialog-footer">
          <el-button class="ea-btn-cancel" @click="logDialogVisible = false">キャンセル</el-button>
          <el-button type="success" class="ea-btn-save" :loading="logSubmitting" @click="submitLog">登録</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ===== 使用ログ管理ダイアログ ===== -->
    <el-dialog
      v-model="logManageVisible"
      title="ローラー使用ログ 管理"
      width="980px"
      :close-on-click-modal="false"
      destroy-on-close
      class="ea-dialog"
    >
      <div class="ea-log-manage-toolbar">
        <el-input
          v-model="logManageFilter.roller_cd"
          placeholder="ローラーCDで絞込"
          size="small"
          clearable
          class="ea-log-filter"
          @keyup.enter="loadLogManageData"
        />
        <el-button size="small" @click="loadLogManageData">検索</el-button>
        <el-button size="small" @click="clearLogManageFilter">クリア</el-button>
        <div class="ea-log-toolbar-right">
          <el-button size="small" type="primary" :icon="DocumentAdd" @click="openLogManageCreate">
            新規ログ
          </el-button>
        </div>
      </div>

      <el-dialog
        v-model="logManageCreateVisible"
        title="使用ログ 新規登録"
        width="560px"
        append-to-body
        :close-on-click-modal="false"
        class="ea-dialog"
      >
        <el-form
          ref="logManageFormRef"
          :model="logManageForm"
          :rules="logManageRules"
          label-position="top"
          class="ea-form"
        >
          <div class="ea-dialog-grid">
            <el-form-item label="ローラーCD" prop="roller_cd">
              <el-select
                v-model="logManageForm.roller_cd"
                filterable
                clearable
                placeholder="ローラーCDを選択"
                style="width: 100%"
              >
                <el-option
                  v-for="r in rollerMasterOptions"
                  :key="r.value"
                  :label="r.label"
                  :value="r.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="実施内容" prop="exec_type">
              <el-select v-model="logManageForm.exec_type" style="width:100%">
                <el-option v-for="t in execTypeOptions" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
            <el-form-item label="実施日" prop="exec_date">
              <el-date-picker v-model="logManageForm.exec_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
            <el-form-item label="管理CD">
              <el-input
                v-model="logManageForm.management_cd"
                readonly
                placeholder="ローラーCD+実施日 で自動生成"
              />
            </el-form-item>
            <el-form-item label="備考" class="ea-span-full">
              <el-input v-model="logManageForm.note" type="textarea" :rows="2" />
            </el-form-item>
          </div>
        </el-form>
        <template #footer>
          <div class="ea-dialog-footer">
            <el-button class="ea-btn-cancel" @click="logManageCreateVisible = false">キャンセル</el-button>
            <el-button type="primary" class="ea-btn-save" :loading="logManageSubmitting" @click="submitLogManageCreate">保存</el-button>
          </div>
        </template>
      </el-dialog>

      <el-table
        :data="logManageRows"
        v-loading="logManageLoading"
        stripe
        border
        size="small"
        class="ea-table"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        height="460px"
      >
        <el-table-column prop="roller_cd" label="CD" width="80" />
        <el-table-column prop="exec_type" label="実施内容" width="120" />
        <el-table-column prop="exec_date" label="実施日" width="100" />
        <el-table-column prop="management_cd" label="管理CD" width="130">
          <template #default="{ row }">{{ row.management_cd ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="note" label="備考" width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.note ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="created_by" label="登録者" width="120">
          <template #default="{ row }">{{ row.created_by ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="登録日時" width="170">
          <template #default="{ row }">{{ row.created_at ? row.created_at.replace('T', ' ').slice(0, 19) : '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link size="small" :icon="Delete" @click="deleteLogManage(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="!logManageLoading && logManageRows.length === 0" class="ea-no-history">データなし</p>
    </el-dialog>

    <!-- ===== 履歴ドロワー ===== -->
    <el-drawer
      v-model="historyDrawerVisible"
      size="340px"
      direction="rtl"
      destroy-on-close
    >
      <template #header>
        <div class="ea-history-drawer-header">
          <span class="ea-history-drawer-title">{{ historyDrawerTitle }}</span>
          <el-button type="primary" size="small" :icon="Printer" @click="printHistory">
            印刷
          </el-button>
        </div>
      </template>
      <div v-loading="historyLoading">
        <el-table
          :data="historyLogs"
          size="small"
          stripe
          border
          :header-cell-style="headerCellStyle"
          :cell-style="cellStyle"
        >
          <el-table-column prop="exec_date" label="実施日" min-width="110" />
          <el-table-column prop="exec_type" label="実施内容" min-width="140" show-overflow-tooltip />
        </el-table>
        <p v-if="!historyLoading && historyLogs.length === 0" class="ea-no-history">履歴なし</p>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting, Search, RefreshLeft, Refresh, Edit, Delete, List,
  DocumentAdd, DataAnalysis, Histogram, Connection, Printer,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

import {
  fetchRollerUsageStatusList,
  updateRollerUsageStatus,
  syncFromRollerMaster,
  recalculatePredictions,
  type RollerUsageStatusRow,
} from '@/api/erp/quality/rollerUsageStatus'
import {
  fetchRollerUsageLogList,
  createRollerUsageLog,
  deleteRollerUsageLog,
  type RollerUsageLogRow,
} from '@/api/erp/quality/rollerUsageLog'
import { fetchMachines } from '@/api/master/machineMaster'
import { fetchRollerMasterList, type RollerMasterRow } from '@/api/master/rollerMaster'

defineOptions({ name: 'EquipmentAssociationHome' })
const router = useRouter()

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const loading = ref(false)
const syncing = ref(false)
const recalculating = ref(false)
const printingList = ref(false)

const rows = ref<RollerUsageStatusRow[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)

const filters = ref({ keyword: '', machine_cd: '', exec_type: '' })
let keywordTimer: ReturnType<typeof setTimeout> | null = null

/** サーバー側ソート（ページングと整合） */
const mainTableRef = ref<{ clearSort?: () => void } | null>(null)
const tableSortBy = ref<string | undefined>(undefined)
const tableSortOrder = ref<'asc' | 'desc' | undefined>(undefined)

const execTypeOptions = ['ローラー交換', 'ローラー清掃', 'その他']

const machineOptions = ref<Array<{ label: string; value: string }>>([])
const formingMachineOptions = computed(() =>
  machineOptions.value.filter((m) => (m.label ?? '').includes('成型')),
)
const rollerMasterOptions = ref<Array<{ label: string; value: string }>>([])
const rollerCategoryMap = ref<Record<string, string>>({})

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------
const loadMachineOptions = async () => {
  try {
    const res = await fetchMachines()
    const raw = res as Record<string, unknown>
    const list: unknown[] = Array.isArray(raw.list)
      ? (raw.list as unknown[])
      : ((raw.data as Record<string, unknown>)?.list as unknown[]) ?? []
    machineOptions.value = list.map((x) => {
      const o = x as Record<string, unknown>
      return { label: String(o.machine_name ?? ''), value: String(o.machine_cd ?? '') }
    })
    if (
      filters.value.machine_cd &&
      !formingMachineOptions.value.some((m) => m.value === filters.value.machine_cd)
    ) {
      filters.value.machine_cd = ''
    }
  } catch {
    /* silent */
  }
}

const loadRollerMasterOptions = async () => {
  try {
    const res = await fetchRollerMasterList({ page: 1, pageSize: 5000 })
    const raw = res as Record<string, unknown>
    const data = raw.data as { list?: RollerMasterRow[] } | undefined
    const list = data?.list ?? (raw.list as RollerMasterRow[]) ?? []
    rollerCategoryMap.value = list.reduce<Record<string, string>>((acc, x) => {
      const cd = String(x.roller_cd ?? '').trim()
      if (!cd) return acc
      acc[cd] = String(x.category ?? '').trim()
      return acc
    }, {})
    rollerMasterOptions.value = list
      .map((x) => {
        const cd = String(x.roller_cd ?? '').trim()
        const name = String(x.roller_name ?? '').trim()
        if (!cd) return null
        return { value: cd, name, label: name ? `${name} (${cd})` : cd }
      })
      .filter((x): x is { label: string; value: string; name: string } => !!x)
      .sort((a, b) => {
        const byName = a.name.localeCompare(b.name, 'ja', { sensitivity: 'base' })
        if (byName !== 0) return byName
        return a.value.localeCompare(b.value, 'ja', { sensitivity: 'base' })
      })
      .map(({ label, value }) => ({ label, value }))
  } catch (e) {
    console.error(e)
    ElMessage.error('ローラーマスタの取得に失敗しました')
  }
}

// ---------------------------------------------------------------------------
// Main data
// ---------------------------------------------------------------------------
const extractListAndTotal = (res: unknown): { list: RollerUsageStatusRow[]; total: number } => {
  const r = res as Record<string, unknown>
  const data = r.data as { list?: RollerUsageStatusRow[]; total?: number } | undefined
  const list: RollerUsageStatusRow[] = data?.list ?? (r.list as RollerUsageStatusRow[]) ?? []
  const tot = typeof data?.total === 'number' ? data.total : Number(r.total) || 0
  return { list, total: tot }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchRollerUsageStatusList({
      page: currentPage.value,
      pageSize: pageSize.value,
      ...(filters.value.keyword.trim() ? { keyword: filters.value.keyword.trim() } : {}),
      ...(filters.value.machine_cd ? { machine_cd: filters.value.machine_cd } : {}),
      ...(filters.value.exec_type ? { exec_type: filters.value.exec_type } : {}),
      ...(tableSortBy.value && tableSortOrder.value
        ? { sortBy: tableSortBy.value, sortOrder: tableSortOrder.value }
        : {}),
    })
    const { list, total: tot } = extractListAndTotal(res)
    rows.value = list
    total.value = tot
  } catch (e) {
    console.error(e)
    ElMessage.error('ローラー使用状況の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const onKeywordInput = () => {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => { currentPage.value = 1; loadData() }, 350)
}
const onFilterChange = () => { currentPage.value = 1; loadData() }

const handleSortChange = (data: { prop?: string; order: string | null }) => {
  const prop = data.prop
  const order = data.order
  if (!prop || !order) {
    tableSortBy.value = undefined
    tableSortOrder.value = undefined
  } else {
    tableSortBy.value = prop
    tableSortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  }
  currentPage.value = 1
  loadData()
}

const clearFilters = () => {
  filters.value = { keyword: '', machine_cd: '', exec_type: '' }
  tableSortBy.value = undefined
  tableSortOrder.value = undefined
  mainTableRef.value?.clearSort?.()
  currentPage.value = 1
  loadData()
}

// ---------------------------------------------------------------------------
// Sync / Recalculate
// ---------------------------------------------------------------------------
const handleSync = async () => {
  syncing.value = true
  try {
    const res = await syncFromRollerMaster()
    ElMessage.success(res.message ?? '同期完了')
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('同期に失敗しました')
  } finally {
    syncing.value = false
  }
}

const handleRecalculate = async () => {
  recalculating.value = true
  try {
    const res = await recalculatePredictions()
    ElMessage.success(res.message ?? '再計算完了')
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('再計算に失敗しました')
  } finally {
    recalculating.value = false
  }
}

const goRollerMaster = () => {
  router.push('/master/roller-master')
}

const goRollerBom = () => {
  router.push('/master/bom/roller-bom')
}

// ---------------------------------------------------------------------------
// Edit dialog
// ---------------------------------------------------------------------------
const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const editForm = ref<Partial<RollerUsageStatusRow>>({})
const editDialogRollerType = ref('')

const openEditDialog = (row: RollerUsageStatusRow) => {
  editingId.value = row.id ?? null
  editDialogRollerType.value = String(row.roller_type ?? '').trim()
  editForm.value = {
    roller_cd: row.roller_cd,
    exec_type: row.exec_type ?? '',
    last_exec_date: row.last_exec_date ?? null,
    prod_cumulative_qty: row.prod_cumulative_qty ?? null,
    prod_manual_addon_qty: row.prod_manual_addon_qty ?? 0,
    planned_product_cd: row.planned_product_cd ?? '',
  }
  editDialogVisible.value = true
}

const submitEdit = async () => {
  if (!editingId.value) return
  editSubmitting.value = true
  try {
    await updateRollerUsageStatus(editingId.value, editForm.value)
    ElMessage.success('更新しました')
    editDialogVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('更新に失敗しました')
  } finally {
    editSubmitting.value = false
  }
}

// ---------------------------------------------------------------------------
// Log dialog
// ---------------------------------------------------------------------------
const logDialogVisible = ref(false)
const logSubmitting = ref(false)
const logFormRef = ref<FormInstance>()
const logForm = ref<Partial<RollerUsageLogRow>>({})
const logDialogRollerType = ref('')
const logDialogTitle = computed(() => {
  const cd = logForm.value.roller_cd ?? ''
  const tp = logDialogRollerType.value.trim()
  if (!cd && !tp) return '実施登録'
  return tp ? `実施登録 — ${cd}（${tp}）` : `実施登録 — ${cd}`
})
const logRules: FormRules = {
  exec_type: [{ required: true, message: '実施内容は必須です', trigger: 'change' }],
  exec_date:  [{ required: true, message: '実施日は必須です', trigger: 'change' }],
}

const openLogDialog = (row: RollerUsageStatusRow) => {
  logDialogRollerType.value = String(row.roller_type ?? '').trim()
  logForm.value = {
    roller_cd: row.roller_cd,
    exec_type: 'ローラー交換',
    exec_date: new Date().toISOString().slice(0, 10),
    management_cd: '',
    note: '',
  }
  logDialogVisible.value = true
}

const submitLog = async () => {
  try { await logFormRef.value?.validate() } catch { return }
  logSubmitting.value = true
  try {
    await createRollerUsageLog(logForm.value)
    ElMessage.success('登録しました')
    logDialogVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('登録に失敗しました')
  } finally {
    logSubmitting.value = false
  }
}

// ---------------------------------------------------------------------------
// Log manage dialog
// ---------------------------------------------------------------------------
const logManageVisible = ref(false)
const logManageLoading = ref(false)
const logManageSubmitting = ref(false)
const logManageRows = ref<RollerUsageLogRow[]>([])
const logManageFilter = ref({ roller_cd: '' })
const logManageCreateVisible = ref(false)
const logManageFormRef = ref<FormInstance>()
const logManageForm = ref<Partial<RollerUsageLogRow>>({})
const logManageRules: FormRules = {
  roller_cd: [{ required: true, message: 'ローラーCDは必須です', trigger: 'change' }],
  exec_type: [{ required: true, message: '実施内容は必須です', trigger: 'change' }],
  exec_date: [{ required: true, message: '実施日は必須です', trigger: 'change' }],
}

const buildManagementCd = (rollerCd?: string | null, execDate?: string | null) => {
  const cd = String(rollerCd ?? '').trim()
  const dt = String(execDate ?? '').trim()
  if (!cd || !dt) return ''
  return `${cd}${dt.replace(/\D/g, '')}`
}

const loadLogManageData = async () => {
  logManageLoading.value = true
  try {
    const res = await fetchRollerUsageLogList({
      page: 1,
      pageSize: 500,
      ...(logManageFilter.value.roller_cd.trim()
        ? { roller_cd: logManageFilter.value.roller_cd.trim() }
        : {}),
    })
    const r = res as Record<string, unknown>
    const data = r.data as { list?: RollerUsageLogRow[] } | undefined
    logManageRows.value = data?.list ?? (r.list as RollerUsageLogRow[]) ?? []
  } catch (e) {
    console.error(e)
    ElMessage.error('使用ログの取得に失敗しました')
  } finally {
    logManageLoading.value = false
  }
}

const openLogManageDialog = async () => {
  logManageVisible.value = true
  await loadLogManageData()
}

const clearLogManageFilter = async () => {
  logManageFilter.value.roller_cd = ''
  await loadLogManageData()
}

const openLogManageCreate = () => {
  logManageForm.value = {
    roller_cd: '',
    exec_type: 'ローラー交換',
    exec_date: new Date().toISOString().slice(0, 10),
    management_cd: '',
    note: '',
  }
  logManageForm.value.management_cd = buildManagementCd(
    logManageForm.value.roller_cd,
    logManageForm.value.exec_date,
  )
  logManageCreateVisible.value = true
}

watch(
  () => [logManageForm.value.roller_cd, logManageForm.value.exec_date],
  ([rollerCd, execDate]) => {
    logManageForm.value.management_cd = buildManagementCd(
      String(rollerCd ?? ''),
      String(execDate ?? ''),
    )
  },
)

const submitLogManageCreate = async () => {
  try { await logManageFormRef.value?.validate() } catch { return }
  logManageSubmitting.value = true
  try {
    await createRollerUsageLog(logManageForm.value)
    ElMessage.success('登録しました')
    logManageCreateVisible.value = false
    await Promise.all([loadLogManageData(), loadData()])
  } catch (e) {
    console.error(e)
    ElMessage.error('登録に失敗しました')
  } finally {
    logManageSubmitting.value = false
  }
}

const deleteLogManage = async (row: RollerUsageLogRow) => {
  if (!row.id) return
  try {
    await ElMessageBox.confirm('この実施ログを削除しますか？', '確認', { type: 'warning' })
  } catch { return }
  try {
    await deleteRollerUsageLog(row.id)
    ElMessage.success('削除しました')
    await Promise.all([loadLogManageData(), loadData()])
  } catch (e) {
    console.error(e)
    ElMessage.error('削除に失敗しました')
  }
}

// ---------------------------------------------------------------------------
// History drawer
// ---------------------------------------------------------------------------
const historyDrawerVisible = ref(false)
const historyLoading = ref(false)
const historyLogs = ref<RollerUsageLogRow[]>([])
const historyRollerCd = ref('')
const historyRollerType = ref('')
const historyDrawerTitle = computed(() => {
  const cd = historyRollerCd.value
  const tp = historyRollerType.value.trim()
  if (!cd && !tp) return '履歴'
  return tp ? `履歴 — ${cd}（${tp}）` : `履歴 — ${cd}`
})

const openHistoryDrawer = async (row: RollerUsageStatusRow) => {
  historyRollerCd.value = row.roller_cd ?? ''
  historyRollerType.value = String(row.roller_type ?? '').trim()
  historyDrawerVisible.value = true
  historyLoading.value = true
  try {
    const res = await fetchRollerUsageLogList({ roller_cd: historyRollerCd.value })
    const r = res as Record<string, unknown>
    const data = r.data as { list?: RollerUsageLogRow[] } | undefined
    historyLogs.value = data?.list ?? (r.list as RollerUsageLogRow[]) ?? []
  } catch (e) {
    console.error(e)
    ElMessage.error('履歴の取得に失敗しました')
  } finally {
    historyLoading.value = false
  }
}

const _escHtml = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

const printHistory = () => {
  if (historyLoading.value) {
    ElMessage.warning('読み込み中です')
    return
  }
  const cd = historyRollerCd.value || ''
  const tp = historyRollerType.value.trim()
  const metaLine = tp ? `${_escHtml(cd)}（${_escHtml(tp)}）` : _escHtml(cd)

  const rowsHtml =
    historyLogs.value.length > 0
      ? historyLogs.value
          .map((l) => {
            const d = _escHtml(String(l.exec_date ?? ''))
            const t = _escHtml(String(l.exec_type ?? ''))
            return `<tr><td>${d}</td><td>${t}</td></tr>`
          })
          .join('')
      : '<tr><td colspan="2" style="text-align:center">履歴なし</td></tr>'

  const printedAt = _escHtml(new Date().toLocaleString('ja-JP'))
  const html = `<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>ローラー実施履歴</title>
<style>
  @page { margin: 14mm; }
  body { font-family: 'Noto Sans JP','Hiragino Kaku Gothic ProN','Meiryo',sans-serif; padding: 12px; font-size: 11pt; color: #111; }
  h1 { font-size: 13pt; margin: 0 0 10px; border-bottom: 2px solid #1e3a5f; padding-bottom: 6px; }
  .meta { margin-bottom: 14px; font-size: 11pt; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #333; padding: 7px 10px; text-align: left; }
  th { background: #e8eef5; font-weight: 700; }
  .foot { margin-top: 14px; font-size: 9pt; color: #555; }
</style></head><body>
  <h1>ローラー実施履歴</h1>
  <div class="meta">ローラーCD：${metaLine}</div>
  <table><thead><tr><th style="width:28%">実施日</th><th>実施内容</th></tr></thead><tbody>${rowsHtml}</tbody></table>
  <div class="foot">印刷日時：${printedAt}</div>
</body></html>`

  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
    return
  }
  w.document.open()
  w.document.write(html)
  w.document.close()
  w.onafterprint = () => {
    try {
      w.close()
    } catch {
      /* noop */
    }
  }
  setTimeout(() => {
    w.focus()
    w.print()
    setTimeout(() => {
      try {
        w.close()
      } catch {
        /* noop */
      }
    }, 1200)
  }, 150)
}

/** 現在のフィルタで一覧を取得し、実施日（次回実施日）昇順で A4 縦印刷 */
const printMainListReport = async () => {
  printingList.value = true
  try {
    const res = await fetchRollerUsageStatusList({
      page: 1,
      pageSize: 5000,
      ...(filters.value.keyword.trim() ? { keyword: filters.value.keyword.trim() } : {}),
      ...(filters.value.machine_cd ? { machine_cd: filters.value.machine_cd } : {}),
      ...(filters.value.exec_type ? { exec_type: filters.value.exec_type } : {}),
    })
    const { list, total } = extractListAndTotal(res)
    const sorted = [...list].sort((a, b) => {
      const sa = String(a.next_exec_date ?? '').trim()
      const sb = String(b.next_exec_date ?? '').trim()
      if (!sa && !sb) {
        return String(a.roller_cd ?? '').localeCompare(String(b.roller_cd ?? ''), 'ja')
      }
      if (!sa) return 1
      if (!sb) return -1
      return sa.localeCompare(sb)
    })

    const rowsHtml =
      sorted.length > 0
        ? (() => {
            let currentMonth = ''
            return sorted
              .map((row) => {
                const rawDate = String(row.next_exec_date ?? '').trim()
                const monthKey = rawDate ? rawDate.slice(0, 7) : '未設定'
                const monthLabel = monthKey === '未設定' ? '実施日未設定' : `${monthKey} 月`

                const category = _escHtml(
                  String(rollerCategoryMap.value[String(row.roller_cd ?? '').trim()] || '').trim() || '—',
                )
                const rt = _escHtml(String(row.roller_type ?? '').trim() || '—')
                const mn = _escHtml(String(row.machine_name ?? '').trim() || '—')
                const pqNum = row.prod_cumulative_qty
                const pq =
                  pqNum == null
                    ? '—'
                    : _escHtml(Number(pqNum).toLocaleString('ja-JP'))
                const ld = _escHtml(rawDate || '—')
                const pp = _escHtml(String(row.planned_product_cd ?? '').trim() || '—')

                const monthRow =
                  monthKey !== currentMonth
                    ? `<tr class="month-group"><td colspan="9">${_escHtml(monthLabel)}</td></tr>`
                    : ''
                currentMonth = monthKey

                return `${monthRow}<tr><td>${category}</td><td>${rt}</td><td>${mn}</td><td class="num">${pq}</td><td>${pp}</td><td>${ld}</td><td></td><td></td><td></td></tr>`
              })
              .join('')
          })()
        : '<tr><td colspan="9" style="text-align:center">データなし</td></tr>'

    const printedAt = _escHtml(new Date().toLocaleString('ja-JP'))
    const metaChunks: string[] = []
    if (filters.value.keyword.trim()) {
      metaChunks.push(`キーワード: ${_escHtml(filters.value.keyword.trim())}`)
    }
    if (filters.value.machine_cd) {
      metaChunks.push(`設備: ${_escHtml(filters.value.machine_cd)}`)
    }
    if (filters.value.exec_type) {
      metaChunks.push(`実施内容: ${_escHtml(filters.value.exec_type)}`)
    }
    const countNote =
      total > sorted.length
        ? `${sorted.length}件表示（全${total}件中・上限5000件）`
        : `${sorted.length}件`

    const html = `<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>ローラー使用管理一覧</title>
<style>
  @page { size: A4 portrait; margin: 10mm; }
  body { font-family: 'Noto Sans JP','Hiragino Kaku Gothic ProN','Meiryo',sans-serif; padding: 0; font-size: 9pt; color: #111; }
  .title-row { display: flex; justify-content: space-between; align-items: flex-end; gap: 8px; margin: 0 0 8px; border-bottom: 2px solid #1e3a5f; padding-bottom: 4px; }
  h1 { font-size: 12pt; margin: 0; }
  .title-right { font-size: 9pt; color: #374151; white-space: nowrap; text-align: right; }
  table { width: 100%; border-collapse: collapse; table-layout: fixed; }
  th, td { border: 1px solid #333; padding: 4px 6px; text-align: left; vertical-align: top; word-wrap: break-word; }
  th { background: #e8eef5; font-weight: 700; font-size: 8.5pt; }
  td.num { text-align: right; }
  .foot { margin-top: 10px; font-size: 8pt; color: #555; }
  .month-group td { background: #f5f8fc; font-weight: 700; text-align: left; }
</style></head><body>
  <div class="title-row">
    <h1>ローラー使用管理 一覧</h1>
    <div class="title-right">並び：実施日昇順（次回実施日）　／　${countNote}</div>
  </div>
  <table><thead><tr>
    <th style="width:10%">区分</th>
    <th style="width:22%">ローラー種類</th>
    <th style="width:8%">設備名</th>
    <th style="width:8%">累計</th>
    <th style="width:17%">予定段取品</th>
    <th style="width:11%">実施日</th>
    <th style="width:6%">実施日</th>
    <th style="width:6%">実施者</th>
    <th style="width:6%">確認者</th>
  </tr></thead><tbody>${rowsHtml}</tbody></table>
  <div class="foot">印刷日時：${printedAt}</div>
</body></html>`

    const w = window.open('', '_blank')
    if (!w) {
      ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
      return
    }
    w.document.open()
    w.document.write(html)
    w.document.close()
    w.onafterprint = () => {
      try {
        w.close()
      } catch {
        /* noop */
      }
    }
    setTimeout(() => {
      w.focus()
      w.print()
      setTimeout(() => {
        try {
          w.close()
        } catch {
          /* noop */
        }
      }, 1200)
    }, 150)
  } catch (e) {
    console.error(e)
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    printingList.value = false
  }
}

// ---------------------------------------------------------------------------
// Styles / helpers
// ---------------------------------------------------------------------------
const headerCellStyle = () => ({
  background: 'linear-gradient(135deg, #1e3a5f 0%, #1565c0 100%)',
  color: '#fff',
  fontWeight: 600,
  fontSize: '11px',
  padding: '6px 8px',
  lineHeight: '1.3',
})
const cellStyle = () => ({ padding: '5px 6px', fontSize: '12px' })

const rowClassName = ({ row }: { row: RollerUsageStatusRow }) => {
  if (row.exchange_remaining_qty != null && row.exchange_remaining_qty <= 0) return 'ea-row-danger'
  if (row.next_exec_date && row.next_exec_date <= todayStr()) return 'ea-row-warning'
  return ''
}

const todayStr = () => new Date().toISOString().slice(0, 10)

const nextDateClass = (d?: string | null) => {
  if (!d) return ''
  if (d < todayStr()) return 'ea-overdue'
  const diff = (new Date(d).getTime() - Date.now()) / 86400000
  if (diff < 14) return 'ea-near'
  return ''
}

const remainingClass = (v?: number | null) => {
  if (v == null) return ''
  if (v <= 0) return 'ea-overdue'
  if (v < 5000) return 'ea-near'
  return ''
}

const fmtNum = (v?: number | null) =>
  v == null ? '—' : v.toLocaleString('ja-JP')

const fmtSignedQty = (v?: number | null) =>
  v == null ? '—' : v.toLocaleString('ja-JP')

const prodQtyTotal = (row: RollerUsageStatusRow) =>
  (row.prod_cumulative_qty ?? 0) + (row.prod_manual_addon_qty ?? 0)

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
onMounted(async () => {
  await loadMachineOptions()
  await loadRollerMasterOptions()
  await loadData()
})
</script>

<style scoped>
.ea-page {
  padding: 12px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(165deg, #eff6ff 0%, #f0f9ff 35%, #f8fafc 100%);
  font-family: 'Inter', 'Noto Sans JP', -apple-system, sans-serif;
}

/* ── ヘッダー ── */
.ea-header {
  background: linear-gradient(135deg, #1e3a5f 0%, #1565c0 55%, #0891b2 100%);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10px 30px rgba(21, 101, 192, 0.28);
  color: #fff;
  gap: 12px;
}

.ea-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ea-title-icon {
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ea-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.ea-subtitle {
  margin: 4px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
}

.ea-header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.ea-head-btn {
  height: 32px;
  border-radius: 10px;
  font-size: 12px;
  border: 1px solid transparent;
  color: #fff;
  font-weight: 600;
  transition: all 0.2s ease;
}

.ea-btn-log {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border-color: rgba(186, 230, 253, 0.8);
}
.ea-btn-master {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-color: rgba(221, 214, 254, 0.8);
}
.ea-btn-bom {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: rgba(253, 230, 138, 0.8);
}
.ea-btn-sync {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: rgba(167, 243, 208, 0.8);
}
.ea-btn-calc {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: rgba(254, 202, 202, 0.9);
}
.ea-btn-print {
  background: linear-gradient(135deg, #334155 0%, #1f2937 100%);
  border-color: rgba(203, 213, 225, 0.75);
}

.ea-head-btn:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.2);
}
.ea-head-btn:active {
  transform: translateY(0);
}
.ea-head-btn.is-disabled,
.ea-head-btn.is-loading {
  filter: grayscale(0.2);
}

/* ── ツールバー ── */
.ea-toolbar {
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(21, 101, 192, 0.12);
  box-shadow: 0 2px 10px rgba(21, 101, 192, 0.06);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ea-search {
  flex: 1;
  min-width: 240px;
}

.ea-filter-select {
  width: 180px;
}

.ea-toolbar-right {
  margin-left: auto;
}

.ea-log-manage-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
}

.ea-log-filter {
  width: 240px;
}

.ea-log-toolbar-right {
  margin-left: auto;
}

/* ── テーブル ── */
.ea-table-wrap {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(21, 101, 192, 0.1);
  padding: 0 0 10px;
  box-shadow: 0 2px 12px rgba(21, 101, 192, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex: 1;
}

.ea-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 12px 0;
  color: #64748b;
  font-size: 12px;
  flex-wrap: wrap;
}

.ea-dash {
  color: #cbd5e1;
}

/* 行の色分け */
:deep(.ea-row-danger td) {
  background: #fff1f2 !important;
}
:deep(.ea-row-warning td) {
  background: #fffbeb !important;
}

.ea-overdue {
  color: #dc2626;
  font-weight: 700;
}
.ea-near {
  color: #d97706;
  font-weight: 600;
}

/* ── ダイアログ共通 ── */
.ea-dialog :deep(.el-dialog__header) {
  padding: 14px 18px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, rgba(30, 58, 95, 0.95) 0%, rgba(21, 101, 192, 0.95) 55%, rgba(8, 145, 178, 0.95) 100%);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.ea-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
  font-size: 14px;
}

.ea-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.ea-dialog :deep(.el-dialog__body) {
  padding: 12px 16px 8px;
}

.ea-form :deep(.el-form-item__label) {
  color: #1565c0;
  font-weight: 700;
  font-size: 12px;
  padding-bottom: 4px;
}

.ea-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.ea-form :deep(.el-input__wrapper),
.ea-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  box-shadow: none;
}

.ea-form :deep(.el-input__wrapper.is-focus),
.ea-form :deep(.el-select__wrapper.is-focus) {
  border-color: #1565c0;
  box-shadow: 0 0 0 3px rgba(21, 101, 192, 0.14);
}

.ea-form :deep(.el-textarea__inner) {
  border-radius: 10px;
}

.ea-dialog-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 14px;
}

.ea-span-full {
  grid-column: 1 / -1;
}

.ea-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.ea-btn-cancel {
  height: 32px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}

.ea-btn-save {
  height: 32px;
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 10px rgba(21, 101, 192, 0.25);
}

.ea-no-history {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 20px 0;
}

.ea-history-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding-right: 4px;
}

.ea-history-drawer-title {
  font-weight: 700;
  font-size: 15px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
</style>
