<template>
  <div class="em-page">
    <div class="em-header">
      <div class="em-title-row">
        <el-icon class="em-title-icon" :size="20"><Tools /></el-icon>
        <div>
          <h1 class="em-title">設備保全管理</h1>
          <p class="em-subtitle">工程別の保全・修理 — 予定登録 → カレンダー反映 → 実施記録</p>
        </div>
      </div>
      <div class="em-header-actions">
        <el-button size="small" class="em-head-btn em-btn-import" :loading="importing" @click="handleImport">
          <el-icon><Refresh /></el-icon>
          設備再同期
        </el-button>
        <el-button size="small" class="em-head-btn em-btn-equip" @click="openEquipmentDialog()">
          <el-icon><Plus /></el-icon>
          設備追加
        </el-button>
        <el-button
          v-if="viewMode === 'plan'"
          size="small"
          class="em-head-btn em-btn-plan"
          @click="openRecordDialog(undefined, 'planned')"
        >
          <el-icon><Calendar /></el-icon>
          予定追加
        </el-button>
        <el-button
          v-if="viewMode === 'done'"
          size="small"
          class="em-head-btn em-btn-done"
          @click="openRecordDialog(undefined, 'done')"
        >
          <el-icon><CircleCheck /></el-icon>
          実施登録
        </el-button>
      </div>
    </div>

    <div class="em-toolbar">
      <div class="em-process-tabs">
        <button
          v-for="p in processTabs"
          :key="p.code"
          type="button"
          class="em-process-tab"
          :class="{ 'is-active': processFilter === p.code }"
          :style="processTabStyle(p.code)"
          @click="processFilter = p.code"
        >
          <span v-if="p.code !== 'all'" class="em-tab-dot" :style="{ background: processColor(p.code) }" />
          {{ p.label }}
          <span class="em-count">{{ processCount(p.code) }}</span>
        </button>
      </div>
      <el-input
        v-model="keyword"
        placeholder="設備名・件名・担当で検索…"
        clearable
        size="small"
        class="em-search"
        @input="onKeywordInput"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <div class="em-view-switch">
        <button
          type="button"
          class="em-view-btn em-view-done"
          :class="{ 'is-active': viewMode === 'done' }"
          @click="viewMode = 'done'"
        >
          <el-icon><CircleCheck /></el-icon>
          実施一覧
        </button>
        <button
          type="button"
          class="em-view-btn em-view-plan"
          :class="{ 'is-active': viewMode === 'plan' }"
          @click="viewMode = 'plan'"
        >
          <el-icon><List /></el-icon>
          予定一覧
        </button>
        <button
          type="button"
          class="em-view-btn em-view-cal"
          :class="{ 'is-active': viewMode === 'calendar' }"
          @click="viewMode = 'calendar'"
        >
          <el-icon><Calendar /></el-icon>
          カレンダー
        </button>
      </div>
    </div>

    <!-- ===== 実施一覧 ===== -->
    <div v-if="viewMode === 'done'" v-loading="recordsLoading" class="em-panel em-panel--done">
      <div class="em-panel-bar">
        <div class="em-panel-title">
          <span class="em-badge em-badge--done">実施済</span>
          <span>実施済みの保全・修理のみ表示</span>
        </div>
        <div class="em-stat-chips">
          <span class="em-stat">表示 <b>{{ filteredDoneRows.length }}</b></span>
        </div>
      </div>
      <el-table
        :data="filteredDoneRows"
        size="small"
        border
        stripe
        height="calc(100vh - 268px)"
        class="em-table"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        empty-text="実施データがありません。「実施登録」または予定から実施済にしてください"
      >
        <el-table-column label="工程" width="110">
          <template #default="{ row }">
            <span class="em-proc" :style="processPillStyle(row.process_code)">
              {{ processLabel(row.process_code) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="equipment_name" label="設備" min-width="130" show-overflow-tooltip />
        <el-table-column label="区分" width="80" align="center">
          <template #default="{ row }">
            <span class="em-work" :class="row.work_type === 'repair' ? 'is-repair' : 'is-maint'">
              {{ workLabel(row.work_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_date" label="実施日" width="110" align="center" sortable />
        <el-table-column label="工数(H)" width="88" align="right">
          <template #default="{ row }">{{ formatHours(row.work_hours) }}</template>
        </el-table-column>
        <el-table-column prop="title" label="件名" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.title || '—' }}</template>
        </el-table-column>
        <el-table-column prop="assignee" label="担当" width="100" show-overflow-tooltip>
          <template #default="{ row }">{{ row.assignee || '—' }}</template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.content || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openRecordDialog(undefined, undefined, row)">編集</el-button>
            <el-button type="danger" link size="small" @click="removeRecord(row.id)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== 予定一覧 ===== -->
    <div v-else-if="viewMode === 'plan'" v-loading="recordsLoading" class="em-panel em-panel--plan">
      <div class="em-panel-bar">
        <div class="em-panel-title">
          <span class="em-badge em-badge--plan">予定</span>
          <span>件名を先に登録 → 日付設定でカレンダーへ反映</span>
        </div>
        <div class="em-stat-chips">
          <span class="em-stat em-stat--warn">未定 <b>{{ undeterminedCount }}</b></span>
          <span class="em-stat em-stat--ok">日付あり <b>{{ datedPlanCount }}</b></span>
          <span class="em-stat">合計 <b>{{ filteredPlanRows.length }}</b></span>
        </div>
      </div>
      <el-table
        :data="filteredPlanRows"
        size="small"
        border
        stripe
        height="calc(100vh - 268px)"
        class="em-table"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        :row-class-name="planRowClass"
        empty-text="予定がありません。「予定追加」から登録してください"
      >
        <el-table-column label="工程" width="110">
          <template #default="{ row }">
            <span class="em-proc" :style="processPillStyle(row.process_code)">
              {{ processLabel(row.process_code) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="equipment_name" label="設備" min-width="130" show-overflow-tooltip />
        <el-table-column label="区分" width="80" align="center">
          <template #default="{ row }">
            <span class="em-work" :class="row.work_type === 'repair' ? 'is-repair' : 'is-maint'">
              {{ workLabel(row.work_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="予定日" width="120" align="center" sortable>
          <template #default="{ row }">
            <span v-if="!row.planned_date" class="em-undetermined">未定</span>
            <span v-else :class="dateTone(row.planned_date)">{{ row.planned_date }}</span>
          </template>
        </el-table-column>
        <el-table-column label="カレンダー" width="96" align="center">
          <template #default="{ row }">
            <span v-if="row.planned_date" class="em-cal-on">反映中</span>
            <span v-else class="em-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="工数(H)" width="88" align="right">
          <template #default="{ row }">{{ formatHours(row.work_hours) }}</template>
        </el-table-column>
        <el-table-column prop="title" label="件名" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.title || '—' }}</template>
        </el-table-column>
        <el-table-column prop="assignee" label="担当" width="100" show-overflow-tooltip>
          <template #default="{ row }">{{ row.assignee || '—' }}</template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.content || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="210" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openRecordDialog(undefined, undefined, row)">編集</el-button>
            <el-button type="success" link size="small" @click="markAsDone(row)">実施済</el-button>
            <el-button type="danger" link size="small" @click="removeRecord(row.id)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ===== カレンダー ===== -->
    <div v-else class="em-calendar-wrap" v-loading="calendarLoading">
      <div class="em-cal-nav">
        <div class="em-cal-nav-left">
          <el-button size="small" class="em-cal-nav-btn" :icon="ArrowLeft" @click="shiftMonth(-1)" />
          <span class="em-cal-title">{{ calendarTitle }}</span>
          <el-button size="small" class="em-cal-nav-btn" :icon="ArrowRight" @click="shiftMonth(1)" />
          <el-button size="small" class="em-cal-today" @click="goToday">今月</el-button>
        </div>
        <div class="em-legend">
          <span class="em-chip em-chip--plan-m">保全予定</span>
          <span class="em-chip em-chip--plan-r">修理予定</span>
        </div>
        <span class="em-cal-note">日付のある予定のみ表示</span>
      </div>
      <div class="em-cal-grid">
        <div
          v-for="(w, wi) in weekLabels"
          :key="w"
          class="em-cal-dow"
          :class="{ 'is-sun': wi === 0, 'is-sat': wi === 6 }"
        >
          {{ w }}
        </div>
        <button
          v-for="cell in calendarCells"
          :key="cell.key"
          type="button"
          class="em-cal-cell"
          :class="{
            'is-out': !cell.inMonth,
            'is-today': cell.isToday,
            'has-events': cell.events.length > 0,
          }"
          @click="openDay(cell)"
        >
          <span class="em-cal-day">{{ cell.day }}</span>
          <span
            v-for="ev in cell.events.slice(0, 3)"
            :key="ev.id"
            class="em-chip"
            :class="chipClass(ev)"
            @click.stop="openRecordDialog(undefined, undefined, ev)"
          >
            {{ eventLabel(ev) }}
          </span>
          <span v-if="cell.events.length > 3" class="em-cal-more">+{{ cell.events.length - 3 }}</span>
        </button>
      </div>
    </div>

    <!-- 設備ダイアログ -->
    <el-dialog
      v-model="equipmentVisible"
      :title="editingEquipmentId ? '設備を編集' : '設備を追加'"
      width="640px"
      :close-on-click-modal="false"
      destroy-on-close
      class="em-dialog"
    >
      <el-form label-position="top" class="em-form">
        <div class="em-form-grid">
          <el-form-item label="工程" required>
            <el-select v-model="equipmentForm.process_code" style="width: 100%" @change="onProcessChange">
              <el-option v-for="p in processes" :key="p.code" :label="p.label" :value="p.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="設備マスタ">
            <el-select
              v-model="equipmentForm.machine_cd"
              filterable
              clearable
              placeholder="任意で紐付け"
              style="width: 100%"
              @change="onMachinePick"
            >
              <el-option
                v-for="m in machinesForProcess"
                :key="m.machine_cd"
                :label="`${m.machine_name} (${m.machine_cd})`"
                :value="m.machine_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="設備名" required class="em-span">
            <el-input v-model="equipmentForm.equipment_name" maxlength="100" />
          </el-form-item>
          <el-form-item label="管理番号">
            <el-input v-model="equipmentForm.asset_no" maxlength="50" />
          </el-form-item>
          <el-form-item label="設置場所">
            <el-input v-model="equipmentForm.location" maxlength="100" />
          </el-form-item>
          <el-form-item label="保全周期（日）">
            <el-input-number v-model="equipmentForm.cycle_days" :min="1" :max="3650" style="width: 100%" />
          </el-form-item>
          <el-form-item label="状態">
            <el-switch v-model="equipmentForm.is_active" active-text="使用中" inactive-text="停止" />
          </el-form-item>
          <el-form-item label="備考" class="em-span">
            <el-input v-model="equipmentForm.note" type="textarea" :rows="2" maxlength="2000" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="em-dialog-footer">
          <el-button class="em-btn-cancel" @click="equipmentVisible = false">キャンセル</el-button>
          <el-button type="primary" class="em-btn-save" :loading="savingEquipment" @click="saveEquipment">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 記録ダイアログ -->
    <el-dialog
      v-model="recordVisible"
      :title="recordDialogTitle"
      width="640px"
      :close-on-click-modal="false"
      destroy-on-close
      class="em-dialog"
    >
      <el-form label-position="top" class="em-form">
        <div class="em-form-grid">
          <el-form-item label="設備" required class="em-span">
            <el-select v-model="recordForm.equipment_id" filterable style="width: 100%">
              <el-option
                v-for="eq in equipmentsForSelect"
                :key="eq.id"
                :label="`${processLabel(eq.process_code)} / ${eq.equipment_name}`"
                :value="eq.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="区分" required>
            <el-select v-model="recordForm.work_type" style="width: 100%">
              <el-option label="保全" value="maintenance" />
              <el-option label="修理" value="repair" />
            </el-select>
          </el-form-item>
          <el-form-item label="状態" required>
            <el-select v-model="recordForm.status" style="width: 100%" @change="onStatusChange">
              <el-option label="予定" value="planned" />
              <el-option label="実施済" value="done" />
              <el-option label="取消" value="cancelled" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="recordForm.status === 'planned'" label="予定日">
            <div class="em-date-row">
              <el-date-picker
                v-model="recordForm.planned_date"
                type="date"
                value-format="YYYY-MM-DD"
                clearable
                :disabled="recordForm.date_undetermined"
                placeholder="日付を選択（未定可）"
                style="width: 100%"
              />
              <el-checkbox v-model="recordForm.date_undetermined" @change="onUndeterminedChange">
                予定日未定
              </el-checkbox>
            </div>
            <p class="em-hint">日付を入れるとカレンダーに反映されます。未定の場合は件名だけ先に登録できます</p>
          </el-form-item>
          <el-form-item v-if="recordForm.status === 'done'" label="実施日" required>
            <el-date-picker
              v-model="recordForm.actual_date"
              type="date"
              value-format="YYYY-MM-DD"
              clearable
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="件名" class="em-span" required>
            <el-input
              v-model="recordForm.title"
              maxlength="200"
              placeholder="例: 定期点検、刃物交換"
            />
          </el-form-item>
          <el-form-item label="担当">
            <el-input v-model="recordForm.assignee" maxlength="100" />
          </el-form-item>
          <el-form-item label="工数(H)">
            <el-input-number
              v-model="recordForm.work_hours"
              :min="0"
              :max="9999.99"
              :step="0.5"
              :precision="2"
              controls-position="right"
              placeholder="例: 1.5"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="内容" class="em-span">
            <el-input v-model="recordForm.content" type="textarea" :rows="3" maxlength="4000" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="em-dialog-footer">
          <el-button v-if="editingRecordId" type="danger" plain @click="removeRecord(editingRecordId)">削除</el-button>
          <el-button class="em-btn-cancel" @click="recordVisible = false">キャンセル</el-button>
          <el-button type="primary" class="em-btn-save" :loading="savingRecord" @click="saveRecord">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="dayVisible" :title="dayTitle" width="560px" destroy-on-close class="em-dialog">
      <el-table :data="dayEvents" size="small" border empty-text="この日の予定はありません">
        <el-table-column label="工程" width="96">
          <template #default="{ row }">{{ processLabel(row.process_code) }}</template>
        </el-table-column>
        <el-table-column prop="equipment_name" label="設備" min-width="120" show-overflow-tooltip />
        <el-table-column label="内容" min-width="140">
          <template #default="{ row }">{{ workLabel(row.work_type) }} {{ row.title || '' }}</template>
        </el-table-column>
        <el-table-column width="70" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openRecordDialog(undefined, undefined, row)">編集</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button type="primary" @click="openRecordForDay">この日に予定追加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Calendar, CircleCheck, List, Plus, Refresh, Search, Tools } from '@element-plus/icons-vue'
import { getMachineList } from '@/api/master/machineMaster'
import {
  createMaintenanceEquipment,
  createMaintenanceRecord,
  deleteMaintenanceRecord,
  fetchMaintenanceEquipments,
  fetchMaintenanceRecords,
  importMaintenanceMachines,
  updateMaintenanceEquipment,
  updateMaintenanceRecord,
  type MaintenanceEquipment,
  type MaintenanceRecord,
  type ProcessCode,
  type RecordStatus,
  type WorkType,
} from '@/api/erp/quality/equipmentMaintenance'
import { useQualityOperationPermission } from '@/composables/useQualityOperationPermission'
import { guardQualityOperation } from '@/utils/qualityOperationGuard'
import type { MachineItem } from '@/types/master'

defineOptions({ name: 'EquipmentMaintenance' })

const { canCreate, canEdit, canDelete } = useQualityOperationPermission()

const processes: Array<{ code: ProcessCode; label: string; color: string; machineType: string }> = [
  { code: 'cutting', label: '切断工程', color: '#0f766e', machineType: '切断' },
  { code: 'chamfering', label: '面取工程', color: '#0369a1', machineType: '面取' },
  { code: 'forming', label: '成型工程', color: '#1d4ed8', machineType: '成型' },
  { code: 'welding', label: '溶接工程', color: '#b45309', machineType: '溶接' },
  { code: 'plating', label: 'メッキ工程', color: '#6d28d9', machineType: 'メッキ' },
]

const processTabs = [{ code: 'all' as const, label: 'すべて' }, ...processes.map((p) => ({ code: p.code, label: p.label }))]
const weekLabels = ['日', '月', '火', '水', '木', '金', '土']

const importing = ref(false)
const recordsLoading = ref(false)
const calendarLoading = ref(false)
const keyword = ref('')
const processFilter = ref<'all' | ProcessCode>('all')
const viewMode = ref<'done' | 'plan' | 'calendar'>('plan')
const equipments = ref<MaintenanceEquipment[]>([])
const machines = ref<MachineItem[]>([])
const doneRecords = ref<MaintenanceRecord[]>([])
const planRecords = ref<MaintenanceRecord[]>([])
const monthCursor = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const monthRecords = ref<Array<MaintenanceRecord & { anchor: string }>>([])

let keywordTimer: ReturnType<typeof setTimeout> | null = null

const processLabel = (code: string) => processes.find((p) => p.code === code)?.label ?? code
const processColor = (code: string) => processes.find((p) => p.code === code)?.color ?? '#64748b'
const workLabel = (v: string) => (v === 'repair' ? '修理' : '保全')
const formatHours = (v?: number | null) => (v == null || Number.isNaN(Number(v)) ? '—' : Number(v).toFixed(2))

const processTabStyle = (code: string) => {
  if (processFilter.value !== code) return {}
  if (code === 'all') return { background: '#1e3a5f', borderColor: '#1e3a5f', color: '#fff' }
  const c = processColor(code)
  return { background: c, borderColor: c, color: '#fff' }
}

const processPillStyle = (code: string) => {
  const c = processColor(code)
  return { color: c, background: `${c}18`, borderColor: `${c}44` }
}

const matchKeyword = (row: MaintenanceRecord) => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return true
  const hay = `${row.equipment_name} ${row.machine_cd || ''} ${row.title || ''} ${row.assignee || ''} ${row.content || ''}`.toLowerCase()
  return hay.includes(kw)
}

const matchProcess = (row: MaintenanceRecord) =>
  processFilter.value === 'all' || row.process_code === processFilter.value

const filteredDoneRows = computed(() =>
  doneRecords.value
    .filter((r) => matchProcess(r) && matchKeyword(r))
    .sort((a, b) => String(b.actual_date || '').localeCompare(String(a.actual_date || ''))),
)

const filteredPlanRows = computed(() => {
  const rows = planRecords.value.filter((r) => matchProcess(r) && matchKeyword(r))
  return rows.sort((a, b) => {
    const aUnd = !a.planned_date
    const bUnd = !b.planned_date
    if (aUnd !== bUnd) return aUnd ? -1 : 1
    return String(a.planned_date || '').localeCompare(String(b.planned_date || ''))
  })
})

const undeterminedCount = computed(() => filteredPlanRows.value.filter((r) => !r.planned_date).length)
const datedPlanCount = computed(() => filteredPlanRows.value.filter((r) => !!r.planned_date).length)

const processCount = (code: string) => {
  const source = viewMode.value === 'done' ? doneRecords.value : planRecords.value
  if (viewMode.value === 'calendar') {
    const dated = planRecords.value.filter((r) => r.planned_date)
    if (code === 'all') return dated.length
    return dated.filter((r) => r.process_code === code).length
  }
  if (code === 'all') return source.length
  return source.filter((r) => r.process_code === code).length
}

const equipmentsForSelect = computed(() => {
  if (processFilter.value === 'all') return equipments.value
  return equipments.value.filter((e) => e.process_code === processFilter.value)
})

const todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const dateTone = (value?: string | null) => {
  if (!value) return ''
  if (value < todayStr()) return 'em-overdue'
  const diff = (new Date(value).getTime() - Date.now()) / 86400000
  if (diff < 14) return 'em-near'
  return ''
}

const headerCellStyle = () => ({
  background: 'linear-gradient(135deg, #1e3a5f 0%, #1565c0 100%)',
  color: '#fff',
  fontWeight: 600,
  fontSize: '11px',
  padding: '7px 8px',
  lineHeight: '1.3',
})
const cellStyle = () => ({ padding: '5px 6px', fontSize: '12px' })

const planRowClass = ({ row }: { row: MaintenanceRecord }) => {
  if (!row.planned_date) return 'em-row-undetermined'
  if (row.planned_date < todayStr()) return 'em-row-overdue'
  return ''
}

const unwrap = <T,>(res: unknown): T[] => {
  const raw = res as { data?: { list?: T[] }; list?: T[] }
  return raw.data?.list ?? raw.list ?? []
}

const loadEquipments = async (opts: { quiet?: boolean } = {}) => {
  try {
    const res = await fetchMaintenanceEquipments({ auto_sync: true, include_inactive: false })
    equipments.value = unwrap<MaintenanceEquipment>(res)
    const synced = Number((res as { data?: { synced?: number } }).data?.synced || 0)
    if (!opts.quiet && synced > 0) {
      ElMessage.success(`設備マスタから${synced}件を自動取込しました`)
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('設備一覧の取得に失敗しました')
  }
}

const loadRecords = async () => {
  recordsLoading.value = true
  try {
    const [doneRes, planRes] = await Promise.all([
      fetchMaintenanceRecords({ status: 'done' }),
      fetchMaintenanceRecords({ status: 'planned' }),
    ])
    doneRecords.value = unwrap<MaintenanceRecord>(doneRes)
    planRecords.value = unwrap<MaintenanceRecord>(planRes)
  } catch (e) {
    console.error(e)
    ElMessage.error('記録の取得に失敗しました')
  } finally {
    recordsLoading.value = false
  }
}

const onKeywordInput = () => {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => {
    /* client filter only */
  }, 200)
}

const loadMachines = async () => {
  try {
    const res = await getMachineList({ page: 1, pageSize: 5000, status: 'active' })
    machines.value = res.data?.list ?? res.list ?? []
  } catch {
    machines.value = []
  }
}

const machinesForProcess = computed(() => {
  const type = processes.find((p) => p.code === equipmentForm.value.process_code)?.machineType
  return machines.value.filter((m) => !type || m.machine_type === type)
})

const pad = (n: number) => String(n).padStart(2, '0')
const ymd = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

const calendarTitle = computed(
  () => `${monthCursor.value.getFullYear()}年${monthCursor.value.getMonth() + 1}月`,
)

const monthRange = () => {
  const start = new Date(monthCursor.value.getFullYear(), monthCursor.value.getMonth(), 1)
  const end = new Date(monthCursor.value.getFullYear(), monthCursor.value.getMonth() + 1, 0)
  return { from_date: ymd(start), to_date: ymd(end) }
}

const loadCalendar = async () => {
  calendarLoading.value = true
  try {
    // 日付のある予定のみカレンダーへ
    const res = await fetchMaintenanceRecords({
      status: 'planned',
      ...(processFilter.value !== 'all' ? { process_code: processFilter.value } : {}),
      ...monthRange(),
    })
    const list = unwrap<MaintenanceRecord>(res).filter((r) => !!r.planned_date)
    monthRecords.value = list.map((row) => ({ ...row, anchor: String(row.planned_date) }))
  } catch (e) {
    console.error(e)
    ElMessage.error('カレンダーの取得に失敗しました')
  } finally {
    calendarLoading.value = false
  }
}

const calendarCells = computed(() => {
  const year = monthCursor.value.getFullYear()
  const month = monthCursor.value.getMonth()
  const first = new Date(year, month, 1)
  const start = new Date(first)
  start.setDate(1 - first.getDay())
  const today = todayStr()
  const cells = []
  for (let i = 0; i < 42; i += 1) {
    const date = new Date(start)
    date.setDate(start.getDate() + i)
    const key = ymd(date)
    cells.push({
      key,
      day: date.getDate(),
      inMonth: date.getMonth() === month,
      isToday: key === today,
      date: key,
      events: monthRecords.value.filter((r) => r.anchor === key),
    })
  }
  return cells
})

const chipClass = (ev: MaintenanceRecord) =>
  ev.work_type === 'repair' ? 'em-chip--plan-r' : 'em-chip--plan-m'

const eventLabel = (ev: MaintenanceRecord) =>
  `${ev.equipment_name}${ev.title ? ` ${ev.title}` : ''}`

const shiftMonth = (delta: number) => {
  const d = new Date(monthCursor.value)
  d.setMonth(d.getMonth() + delta)
  monthCursor.value = d
}

const goToday = () => {
  const now = new Date()
  monthCursor.value = new Date(now.getFullYear(), now.getMonth(), 1)
}

const refreshCurrentView = async () => {
  await loadRecords()
  if (viewMode.value === 'calendar') await loadCalendar()
}

watch(viewMode, (mode) => {
  if (mode === 'calendar') loadCalendar()
  else loadRecords()
})
watch(processFilter, () => {
  if (viewMode.value === 'calendar') loadCalendar()
})
watch(monthCursor, () => {
  if (viewMode.value === 'calendar') loadCalendar()
})

const handleImport = async () => {
  if (!guardQualityOperation(canCreate)) return
  importing.value = true
  try {
    const res = await importMaintenanceMachines(processFilter.value === 'all' ? undefined : processFilter.value)
    ElMessage.success(res.message || '再同期しました')
    await loadEquipments({ quiet: true })
  } catch (e) {
    console.error(e)
    ElMessage.error('再同期に失敗しました')
  } finally {
    importing.value = false
  }
}

const equipmentVisible = ref(false)
const savingEquipment = ref(false)
const editingEquipmentId = ref<number | null>(null)
const equipmentForm = ref({
  process_code: 'cutting' as ProcessCode,
  machine_cd: '' as string | null,
  equipment_name: '',
  asset_no: '',
  location: '',
  cycle_days: null as number | null,
  note: '',
  is_active: true,
})

const openEquipmentDialog = (row?: MaintenanceEquipment) => {
  if (row) {
    if (!guardQualityOperation(canEdit)) return
    editingEquipmentId.value = row.id
    equipmentForm.value = {
      process_code: row.process_code,
      machine_cd: row.machine_cd,
      equipment_name: row.equipment_name,
      asset_no: row.asset_no || '',
      location: row.location || '',
      cycle_days: row.cycle_days,
      note: row.note || '',
      is_active: row.is_active,
    }
  } else {
    if (!guardQualityOperation(canCreate)) return
    editingEquipmentId.value = null
    equipmentForm.value = {
      process_code: processFilter.value === 'all' ? 'cutting' : processFilter.value,
      machine_cd: '',
      equipment_name: '',
      asset_no: '',
      location: '',
      cycle_days: null,
      note: '',
      is_active: true,
    }
  }
  equipmentVisible.value = true
}

const onProcessChange = () => {
  const still = machinesForProcess.value.some((m) => m.machine_cd === equipmentForm.value.machine_cd)
  if (!still) equipmentForm.value.machine_cd = ''
}

const onMachinePick = (cd: string) => {
  const found = machines.value.find((m) => m.machine_cd === cd)
  if (found && !equipmentForm.value.equipment_name.trim()) {
    equipmentForm.value.equipment_name = found.machine_name
  }
}

const saveEquipment = async () => {
  if (!equipmentForm.value.equipment_name.trim()) {
    ElMessage.warning('設備名を入力してください')
    return
  }
  savingEquipment.value = true
  const payload = {
    ...equipmentForm.value,
    machine_cd: equipmentForm.value.machine_cd || null,
    asset_no: equipmentForm.value.asset_no || null,
    location: equipmentForm.value.location || null,
    note: equipmentForm.value.note || null,
  }
  try {
    if (editingEquipmentId.value) {
      await updateMaintenanceEquipment(editingEquipmentId.value, payload)
      ElMessage.success('更新しました')
    } else {
      await createMaintenanceEquipment(payload)
      ElMessage.success('登録しました')
    }
    equipmentVisible.value = false
    await loadEquipments({ quiet: true })
  } catch (e) {
    console.error(e)
    ElMessage.error('保存に失敗しました')
  } finally {
    savingEquipment.value = false
  }
}

const recordVisible = ref(false)
const savingRecord = ref(false)
const editingRecordId = ref<number | null>(null)
const recordForm = ref({
  equipment_id: undefined as number | undefined,
  work_type: 'maintenance' as WorkType,
  status: 'planned' as RecordStatus,
  planned_date: '' as string | null,
  actual_date: '' as string | null,
  title: '',
  content: '',
  assignee: '',
  work_hours: null as number | null,
  date_undetermined: false,
})

const recordDialogTitle = computed(() => {
  if (editingRecordId.value) return '記録を編集'
  return recordForm.value.status === 'done' ? '実施登録' : '予定登録'
})

const onUndeterminedChange = (checked: boolean | string | number) => {
  if (checked) recordForm.value.planned_date = null
}

const onStatusChange = (status: string) => {
  if (status === 'planned') {
    recordForm.value.date_undetermined = !recordForm.value.planned_date
    if (!recordForm.value.actual_date) recordForm.value.actual_date = null
  }
  if (status === 'done') {
    recordForm.value.date_undetermined = false
    if (!recordForm.value.actual_date) recordForm.value.actual_date = todayStr()
  }
}

const openRecordDialog = (
  _equipment?: MaintenanceEquipment,
  preset?: 'planned' | 'done',
  existing?: MaintenanceRecord,
) => {
  if (existing) {
    if (!guardQualityOperation(canEdit)) return
    editingRecordId.value = existing.id
    const undetermined = existing.status === 'planned' && !existing.planned_date
    recordForm.value = {
      equipment_id: existing.equipment_id,
      work_type: existing.work_type,
      status: existing.status,
      planned_date: existing.planned_date,
      actual_date: existing.actual_date,
      title: existing.title || '',
      content: existing.content || '',
      assignee: existing.assignee || '',
      work_hours: existing.work_hours ?? null,
      date_undetermined: undetermined,
    }
  } else {
    if (!guardQualityOperation(canCreate)) return
    editingRecordId.value = null
    const today = todayStr()
    const asDone = preset === 'done'
    const preferred = equipmentsForSelect.value[0]?.id ?? equipments.value[0]?.id
    recordForm.value = {
      equipment_id: preferred,
      work_type: 'maintenance',
      status: asDone ? 'done' : 'planned',
      planned_date: null,
      actual_date: asDone ? today : null,
      title: '',
      content: '',
      assignee: '',
      work_hours: null,
      date_undetermined: !asDone,
    }
  }
  recordVisible.value = true
}

const saveRecord = async () => {
  if (!recordForm.value.equipment_id) {
    ElMessage.warning('設備を選択してください')
    return
  }
  if (!String(recordForm.value.title || '').trim()) {
    ElMessage.warning('件名を入力してください')
    return
  }
  const undetermined =
    recordForm.value.status === 'planned' &&
    (recordForm.value.date_undetermined || !recordForm.value.planned_date)
  if (recordForm.value.status === 'done' && !recordForm.value.actual_date) {
    ElMessage.warning('実施日を入力してください')
    return
  }
  savingRecord.value = true
  const payload = {
    equipment_id: recordForm.value.equipment_id,
    work_type: recordForm.value.work_type,
    status: recordForm.value.status,
    planned_date: undetermined ? null : recordForm.value.planned_date || null,
    actual_date: recordForm.value.actual_date || null,
    title: recordForm.value.title || null,
    content: recordForm.value.content || null,
    assignee: recordForm.value.assignee || null,
    work_hours: recordForm.value.work_hours ?? null,
  }
  try {
    if (editingRecordId.value) await updateMaintenanceRecord(editingRecordId.value, payload)
    else await createMaintenanceRecord(payload)
    ElMessage.success('保存しました')
    recordVisible.value = false
    dayVisible.value = false
    await refreshCurrentView()
  } catch (e) {
    console.error(e)
    ElMessage.error('保存に失敗しました')
  } finally {
    savingRecord.value = false
  }
}

const markAsDone = async (row: MaintenanceRecord) => {
  if (!guardQualityOperation(canEdit)) return
  editingRecordId.value = row.id
  recordForm.value = {
    equipment_id: row.equipment_id,
    work_type: row.work_type,
    status: 'done',
    planned_date: row.planned_date,
    actual_date: todayStr(),
    title: row.title || '',
    content: row.content || '',
    assignee: row.assignee || '',
    work_hours: row.work_hours ?? null,
    date_undetermined: false,
  }
  recordVisible.value = true
}

const removeRecord = async (id: number) => {
  if (!guardQualityOperation(canDelete)) return
  try {
    await ElMessageBox.confirm('この記録を削除しますか？', '確認', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteMaintenanceRecord(id)
    ElMessage.success('削除しました')
    recordVisible.value = false
    await refreshCurrentView()
  } catch (e) {
    console.error(e)
    ElMessage.error('削除に失敗しました')
  }
}

const dayVisible = ref(false)
const dayDate = ref('')
const dayEvents = ref<Array<MaintenanceRecord & { anchor: string }>>([])
const dayTitle = computed(() => (dayDate.value ? `${dayDate.value} の予定` : '日別'))

const openDay = (cell: { date: string; events: Array<MaintenanceRecord & { anchor: string }> }) => {
  dayDate.value = cell.date
  dayEvents.value = cell.events
  dayVisible.value = true
}

const openRecordForDay = () => {
  dayVisible.value = false
  if (!guardQualityOperation(canCreate)) return
  editingRecordId.value = null
  recordForm.value = {
    equipment_id: equipmentsForSelect.value[0]?.id ?? equipments.value[0]?.id,
    work_type: 'maintenance',
    status: 'planned',
    planned_date: dayDate.value,
    actual_date: null,
    title: '',
    content: '',
    assignee: '',
    work_hours: null,
    date_undetermined: false,
  }
  recordVisible.value = true
}

onMounted(async () => {
  await Promise.all([loadEquipments({ quiet: false }), loadMachines(), loadRecords()])
})
</script>

<style scoped>
.em-page {
  min-height: 100%;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(165deg, #eff6ff 0%, #f0f9ff 35%, #f8fafc 100%);
  font-family: 'Inter', 'Noto Sans JP', -apple-system, sans-serif;
}

.em-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #1e3a5f 0%, #1565c0 55%, #0891b2 100%);
  box-shadow: 0 10px 30px rgba(21, 101, 192, 0.28);
}
.em-title-row { display: flex; align-items: center; gap: 10px; }
.em-title-icon {
  width: 34px; height: 34px; border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  flex-shrink: 0;
}
.em-title { margin: 0; font-size: 18px; font-weight: 800; letter-spacing: -0.02em; }
.em-subtitle { margin: 4px 0 0; font-size: 11px; color: rgba(255, 255, 255, 0.9); }
.em-header-actions { display: flex; gap: 8px; flex-wrap: wrap; flex-shrink: 0; }
.em-head-btn {
  height: 32px;
  border-radius: 10px;
  font-size: 12px;
  border: 1px solid transparent;
  color: #fff;
  font-weight: 600;
  transition: all 0.2s ease;
}
.em-head-btn:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.2);
}
.em-btn-import {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border-color: rgba(186, 230, 253, 0.8);
}
.em-btn-equip {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border-color: rgba(221, 214, 254, 0.8);
}
.em-btn-plan {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: rgba(253, 230, 138, 0.8);
  color: #fff;
}
.em-btn-done {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: rgba(167, 243, 208, 0.8);
}

.em-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(21, 101, 192, 0.12);
  box-shadow: 0 2px 10px rgba(21, 101, 192, 0.06);
}
.em-process-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.em-process-tab {
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
.em-process-tab:hover {
  border-color: #94a3b8;
  transform: translateY(-1px);
}
.em-process-tab.is-active {
  box-shadow: 0 4px 12px rgba(30, 58, 95, 0.22);
}
.em-tab-dot {
  width: 7px; height: 7px; border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.35);
}
.em-count {
  margin-left: 2px;
  min-width: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.em-process-tab.is-active .em-count {
  background: rgba(255, 255, 255, 0.22);
}
.em-search { width: 220px; min-width: 160px; margin-left: auto; }

.em-view-switch {
  display: inline-flex;
  padding: 3px;
  gap: 3px;
  background: #f1f5f9;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}
.em-view-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
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
.em-view-btn.is-active.em-view-done {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(16, 185, 129, 0.35);
}
.em-view-btn.is-active.em-view-plan {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(245, 158, 11, 0.35);
}
.em-view-btn.is-active.em-view-cal {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(37, 99, 235, 0.35);
}

.em-panel {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(21, 101, 192, 0.1);
  padding: 0 0 8px;
  box-shadow: 0 2px 12px rgba(21, 101, 192, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.em-panel--done { border-top: 3px solid #10b981; }
.em-panel--plan { border-top: 3px solid #f59e0b; }
.em-panel-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(90deg, #f8fafc 0%, #fff 100%);
  border-bottom: 1px solid #eef2f7;
}
.em-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}
.em-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.em-badge--done { background: linear-gradient(135deg, #10b981, #059669); }
.em-badge--plan { background: linear-gradient(135deg, #f59e0b, #d97706); }
.em-stat-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.em-stat {
  font-size: 12px;
  color: #475569;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 3px 9px;
  border: 1px solid #e2e8f0;
}
.em-stat b { font-variant-numeric: tabular-nums; color: #0f172a; }
.em-stat--warn { background: #fffbeb; border-color: #fde68a; color: #b45309; }
.em-stat--warn b { color: #b45309; }
.em-stat--ok { background: #ecfdf5; border-color: #a7f3d0; color: #047857; }
.em-stat--ok b { color: #047857; }

.em-proc {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}
.em-work {
  display: inline-flex;
  min-width: 42px;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}
.em-work.is-maint { background: #dbeafe; color: #1d4ed8; }
.em-work.is-repair { background: #ffedd5; color: #c2410c; }
.em-undetermined {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 6px;
  background: #fef3c7;
  color: #b45309;
  font-size: 11px;
  font-weight: 700;
}
.em-cal-on {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 6px;
  background: #dcfce7;
  color: #15803d;
  font-size: 11px;
  font-weight: 700;
}
.em-muted { color: #94a3b8; }
.em-overdue { color: #dc2626; font-weight: 700; }
.em-near { color: #d97706; font-weight: 700; }
:deep(.em-row-overdue td) { background: #fff7ed !important; }
:deep(.em-row-undetermined td) { background: #fffbeb !important; }

.em-calendar-wrap {
  background: #fff;
  border: 1px solid rgba(21, 101, 192, 0.1);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 12px rgba(21, 101, 192, 0.06);
  border-top: 3px solid #3b82f6;
}
.em-cal-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.em-cal-nav-left { display: flex; align-items: center; gap: 6px; }
.em-cal-nav-btn {
  border-radius: 8px !important;
  border-color: #dbeafe !important;
  color: #1d4ed8 !important;
}
.em-cal-today {
  border-radius: 8px !important;
  background: #eff6ff !important;
  border-color: #bfdbfe !important;
  color: #1d4ed8 !important;
  font-weight: 600;
}
.em-cal-title {
  font-weight: 800;
  min-width: 118px;
  text-align: center;
  font-size: 15px;
  color: #0f172a;
}
.em-legend { display: flex; gap: 6px; margin-left: auto; flex-wrap: wrap; }
.em-cal-note { font-size: 11px; color: #64748b; }
.em-cal-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 5px; }
.em-cal-dow {
  text-align: center;
  font-size: 12px;
  color: #64748b;
  font-weight: 700;
  padding: 4px 0;
}
.em-cal-dow.is-sun { color: #ef4444; }
.em-cal-dow.is-sat { color: #2563eb; }
.em-cal-cell {
  min-height: 96px;
  text-align: left;
  border: 1px solid #e8eef5;
  border-radius: 10px;
  background: #fff;
  padding: 5px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 3px;
  transition: all 0.15s ease;
}
.em-cal-cell:hover {
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
  transform: translateY(-1px);
}
.em-cal-cell.is-out { background: #f8fafc; color: #94a3b8; }
.em-cal-cell.is-today {
  outline: 2px solid #2563eb;
  background: #f8fbff;
}
.em-cal-cell.has-events { background: linear-gradient(180deg, #fff 0%, #f8fbff 100%); }
.em-cal-day { font-size: 12px; font-weight: 700; color: #334155; }
.em-cal-cell.is-out .em-cal-day { color: #94a3b8; }
.em-cal-more { font-size: 11px; color: #64748b; font-weight: 600; }
.em-chip {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-radius: 5px;
  padding: 2px 5px;
  font-size: 11px;
  line-height: 1.35;
  font-weight: 600;
}
.em-chip--plan-m { background: #dbeafe; color: #1d4ed8; }
.em-chip--plan-r { background: #ffedd5; color: #c2410c; }

.em-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }
.em-span { grid-column: 1 / -1; }
.em-date-row { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.em-hint { margin: 4px 0 0; font-size: 11px; color: #64748b; line-height: 1.4; }
.em-dialog-footer { display: flex; justify-content: flex-end; gap: 10px; width: 100%; }
.em-btn-cancel {
  height: 32px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}
.em-btn-save {
  height: 32px;
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 10px rgba(21, 101, 192, 0.25);
}

.em-dialog :deep(.el-dialog__header) {
  padding: 14px 18px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, rgba(30, 58, 95, 0.95) 0%, rgba(21, 101, 192, 0.95) 55%, rgba(8, 145, 178, 0.95) 100%);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}
.em-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
  font-size: 14px;
}
.em-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.85);
}
.em-dialog :deep(.el-dialog__body) { padding: 12px 16px 8px; }
.em-form :deep(.el-form-item__label) {
  color: #1565c0;
  font-weight: 700;
  font-size: 12px;
  padding-bottom: 4px;
}
.em-form :deep(.el-form-item) { margin-bottom: 10px; }
.em-form :deep(.el-input__wrapper),
.em-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  box-shadow: none;
}
.em-form :deep(.el-input__wrapper.is-focus),
.em-form :deep(.el-select__wrapper.is-focus) {
  border-color: #1565c0;
  box-shadow: 0 0 0 3px rgba(21, 101, 192, 0.14);
}
.em-form :deep(.el-textarea__inner) { border-radius: 10px; }

@media (max-width: 960px) {
  .em-search { margin-left: 0; width: 100%; }
  .em-header { flex-direction: column; align-items: flex-start; }
}
</style>
