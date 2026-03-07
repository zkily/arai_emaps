<template>
  <el-dialog
    :model-value="visible"
    @update:modelValue="(val) => emit('update:visible', val)"
    width="48%"
    top="2vh"
    destroy-on-close
    :before-close="handleClose"
    :close-on-click-modal="false"
    class="daily-manage-dialog dm-glass"
    :show-close="false"
  >
    <template #header>
      <div class="dm-header">
        <div class="dm-header-inner">
          <div class="dm-title-wrap">
            <div class="dm-title-icon">
              <el-icon><Calendar /></el-icon>
            </div>
            <h2 class="dm-title">{{ t('orderDailyManage.title') }}</h2>
            <span class="dm-count-badge">{{ t('orderDailyManage.countBadge', { n: dailyOrdersList.length }) }}</span>
            <span v-if="dailyChangedRows.size > 0" class="dm-changed-badge">
              <el-icon><Edit /></el-icon>
              {{ t('orderDailyManage.changedBadge', { n: dailyChangedRows.size }) }}
            </span>
          </div>
          <div class="dm-header-actions">
            <el-button
              :loading="saving"
              :disabled="dailyChangedRows.size === 0"
              @click="handleBatchSave"
              class="dm-btn dm-btn-save"
            >
              <el-icon><Check /></el-icon>
              {{ t('orderDailyManage.btnBatchSave') }}
            </el-button>
            <el-button class="dm-btn dm-btn-close" @click="handleClose">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </template>

    <!-- 筛选 - 紧凑玻璃条 -->
    <div class="dm-filter">
      <div class="dm-filter-inner">
        <div class="dm-filter-group">
          <span class="dm-filter-label">{{ t('orderDailyManage.filterDate') }}</span>
          <el-date-picker
            v-model="selectedDate"
            type="date"
            value-format="YYYY-MM-DD"
            :placeholder="t('orderDailyManage.placeholderDate')"
            class="dm-date-picker"
          />
          <div class="dm-date-nav">
            <el-button size="small" class="dm-nav-btn" @click="setPrevDay">{{ t('orderDailyManage.prevDay') }}</el-button>
            <el-button size="small" class="dm-nav-today" @click="setToday">{{ t('orderDailyManage.today') }}</el-button>
            <el-button size="small" class="dm-nav-btn" @click="setNextDay">{{ t('orderDailyManage.nextDay') }}</el-button>
          </div>
        </div>
        <div class="dm-filter-sep"></div>
        <div class="dm-filter-group">
          <span class="dm-filter-label">{{ t('orderDailyManage.filterDestination') }}</span>
          <el-select
            v-model="destinationCd"
            :placeholder="t('orderDailyManage.placeholderDestination')"
            clearable
            filterable
            class="dm-dest-select"
            popper-class="destination-select-popper"
          >
            <el-option
              v-for="opt in destinationOptions"
              :key="opt.cd"
              :label="opt.name"
              :value="opt.cd"
            />
          </el-select>
        </div>
        <div class="dm-filter-sep"></div>
        <div class="dm-filter-group dm-shortcuts">
          <span class="dm-filter-label">{{ t('orderDailyManage.shortcut') }}</span>
          <div class="dm-shortcut-btns">
            <el-button
              v-for="label in shortcutLabels"
              :key="label"
              size="small"
              :class="['dm-shortcut-btn', { 'is-active': shortcutDestinationCd(label) === destinationCd }]"
              @click="applyShortcut(label)"
            >
              {{ label }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="dm-table-wrap">
      <el-table
        v-loading="loading"
        :data="dailyOrdersList"
        border
        stripe
        show-summary
        :summary-method="getDailySummaries"
        :sum-text="t('orderDailyManage.sumText')"
        class="daily-manage-table compact-table"
        height="480"
        size="small"
        :row-key="(row) => row.id"
        :row-class-name="tableRowClassName"
      >
        <el-table-column :label="t('orderDailyManage.colDestinationName')" prop="destination_name" width="150" show-overflow-tooltip />
        <el-table-column :label="t('orderDailyManage.colProductName')" prop="product_name" width="150" show-overflow-tooltip />
        <el-table-column :label="t('orderDailyManage.colProductType')" prop="product_type" width="90" align="center" />
        <el-table-column :label="t('orderDailyManage.colUnitPerBox')" prop="unit_per_box" width="55" align="center" />
        <el-table-column :label="t('orderDailyManage.colDate')" prop="date" width="90" align="center">
          <template #default="{ row }">
            <span class="cell-date">{{ formatDateOnly(row.date) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('orderDailyManage.colWeekday')" prop="weekday" width="52" align="center">
          <template #default="{ row }">
            <span :class="weekdayClass(row.weekday)">{{ row.weekday || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('orderDailyManage.colConfirmedBoxes')" prop="confirmed_boxes" width="100" align="center">
          <template #default="{ row, $index }">
            <el-input
              :disabled="saving"
              class="compact-input"
              :model-value="row.confirmed_boxes === 0 ? '' : row.confirmed_boxes"
              @update:model-value="(val) => handleDailyConfirmedBoxesChange(row, val)"
              @keydown.enter="focusDailyNextInput($index)"
              :ref="(el) => setConfirmedBoxesRef(el, $index)"
            />
          </template>
        </el-table-column>
        <el-table-column :label="t('orderDailyManage.colConfirmedUnits')" prop="confirmed_units" width="100" align="center">
          <template #default="{ row, $index }">
            <el-input
              :disabled="saving"
              class="compact-input"
              :model-value="row.confirmed_units === 0 ? '' : row.confirmed_units"
              @update:model-value="(val) => handleDailyConfirmedUnitsChange(row, val)"
              @keydown.enter="focusDailyNextConfirmedUnitsInput($index)"
              :ref="(el) => setConfirmedUnitsRef(el, $index)"
            />
          </template>
        </el-table-column>
        <el-table-column :label="t('orderDailyManage.colDeliveryDate')" prop="delivery_date" width="80" align="center">
          <template #default="{ row }">
            <span class="cell-delivery-date">{{ formatDeliveryDate(row.delivery_date) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div v-if="!loading && dailyOrdersList.length === 0" class="dm-empty">
      {{ t('orderDailyManage.emptyMessage') }}
    </div>

    <template #footer>
      <div class="dm-footer" />
    </template>

    <el-overlay v-if="saving" class="dm-saving-overlay" />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchOrderDailyList } from '@/api/erp/orderDaily'
import { batchUpdateDailyOrders } from '@/api/order/order'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { ElMessage } from 'element-plus'
import { Check, Close, Calendar, Edit } from '@element-plus/icons-vue'
import type { OrderDailyItem } from '@/api/erp/orderDaily'

const { t } = useI18n()

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'saved'): void
}>()

const shortcutLabels = ['愛知', '横浜', '東海', '西浦', '吉良']

function getJapanDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const selectedDate = ref(getJapanDateStr(new Date()))
const destinationCd = ref<string>('')
const dailyOrdersList = ref<OrderDailyItem[]>([])
const dailyChangedRows = ref<Set<number>>(new Set())
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const loading = ref(false)
const saving = ref(false)

const confirmedBoxesInputs = ref<(HTMLInputElement | undefined)[]>([])
const confirmedUnitsInputs = ref<(HTMLInputElement | undefined)[]>([])

function setConfirmedBoxesRef(el: any, index: number) {
  if (el && '$el' in el) {
    const input = (el as { $el: HTMLElement }).$el?.querySelector?.('input') as HTMLInputElement | undefined
    confirmedBoxesInputs.value[index] = input
  }
}
function setConfirmedUnitsRef(el: any, index: number) {
  if (el && '$el' in el) {
    const input = (el as { $el: HTMLElement }).$el?.querySelector?.('input') as HTMLInputElement | undefined
    confirmedUnitsInputs.value[index] = input
  }
}

const formatDateOnly = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    const d = new Date(dateString)
    return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return String(dateString)
  }
}

const formatDeliveryDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    const d = new Date(dateString)
    return `${d.getMonth() + 1}/${d.getDate()}`
  } catch {
    return String(dateString)
  }
}

function weekdayClass(weekday: string | null | undefined): string {
  if (!weekday) return ''
  if (weekday === '土') return 'weekday-saturday'
  if (weekday === '日') return 'weekday-sunday'
  return ''
}

function setPrevDay() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() - 1)
  selectedDate.value = getJapanDateStr(d)
}

function setToday() {
  selectedDate.value = getJapanDateStr(new Date())
}

function setNextDay() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() + 1)
  selectedDate.value = getJapanDateStr(d)
}

function shortcutDestinationCd(label: string): string {
  const opt = destinationOptions.value.find((o) => (o.name || '').includes(label))
  return opt ? opt.cd : ''
}

function applyShortcut(label: string) {
  const cd = shortcutDestinationCd(label)
  destinationCd.value = cd || ''
}

async function fetchDailyOrdersList() {
  const date = selectedDate.value
  if (!date) return
  loading.value = true
  try {
    const list = await fetchOrderDailyList({
      start_date: date,
      end_date: date,
      destination_cd: destinationCd.value || undefined,
    })
    const arr = Array.isArray(list) ? list : []
    dailyOrdersList.value = arr.slice().sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'ja'))
    dailyChangedRows.value = new Set()
  } catch (e) {
    console.error(e)
    dailyOrdersList.value = []
    dailyChangedRows.value = new Set()
  } finally {
    loading.value = false
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      selectedDate.value = getJapanDateStr(new Date())
      destinationCd.value = ''
      dailyOrdersList.value = []
      dailyChangedRows.value = new Set()
    }
  },
  { immediate: true }
)

watch(
  () => [props.visible, selectedDate.value, destinationCd.value] as const,
  ([visible, date]) => {
    if (visible && date) fetchDailyOrdersList()
  },
  { immediate: true }
)

function markDailyRowChanged(row: OrderDailyItem) {
  if (!row.id) return
  const next = new Set(dailyChangedRows.value)
  next.add(Number(row.id))
  dailyChangedRows.value = next
}

function handleDailyConfirmedBoxesChange(row: OrderDailyItem, val: string | number) {
  const boxes = val === '' ? 0 : Number(val)
  row.confirmed_boxes = boxes
  const unitPerBox = row.unit_per_box ?? 0
  row.confirmed_units = unitPerBox > 0 ? boxes * unitPerBox : boxes
  markDailyRowChanged(row)
}

function handleDailyConfirmedUnitsChange(row: OrderDailyItem, val: string | number) {
  row.confirmed_units = val === '' ? 0 : Number(val)
  markDailyRowChanged(row)
}

async function focusDailyNextInput(currentIndex: number) {
  await nextTick()
  const nextInput = confirmedBoxesInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

async function focusDailyNextConfirmedUnitsInput(currentIndex: number) {
  await nextTick()
  const nextInput = confirmedUnitsInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

const tableRowClassName = ({ row }: { row: OrderDailyItem }) =>
  dailyChangedRows.value.has(Number(row.id)) ? 'edited-row' : ''

interface SummaryProps {
  columns: Array<{ property: string; label: string }>
  data: OrderDailyItem[]
}

function getDailySummaries({ columns, data }: SummaryProps): string[] {
  const sums: string[] = []
  columns.forEach((col, index) => {
    if (index === 0) {
      sums[index] = t('orderDailyManage.sumText')
      return
    }
    if (['confirmed_boxes', 'confirmed_units'].includes(col.property)) {
      const sum = data.reduce((acc, item) => acc + (Number((item as any)[col.property]) || 0), 0)
      sums[index] = sum > 0 ? sum.toLocaleString() : ''
    } else {
      sums[index] = ''
    }
  })
  return sums
}

async function handleBatchSave() {
  if (dailyChangedRows.value.size === 0) {
    ElMessage.warning(t('orderDailyManage.msgNoChangedData'))
    return
  }
  saving.value = true
  try {
    const updates = dailyOrdersList.value
      .filter((row) => row.id && dailyChangedRows.value.has(Number(row.id)))
      .map((row) => ({
        id: Number(row.id),
        forecast_units: Number(row.forecast_units ?? 0),
        confirmed_boxes: Number(row.confirmed_boxes ?? 0),
        confirmed_units: Number(row.confirmed_units ?? 0),
        status: row.status ?? '未出荷',
        remarks: row.remarks ?? '',
      }))
    await batchUpdateDailyOrders({ list: updates })
    ElMessage.success(t('orderDailyManage.msgSaveSuccess'))
    dailyChangedRows.value = new Set()
    await fetchDailyOrdersList()
    emit('saved')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : t('orderDailyManage.msgSaveFailed')
    ElMessage.error(String(msg))
  } finally {
    saving.value = false
  }
}

function handleClose() {
  emit('update:visible', false)
}

onMounted(() => {
  getDestinationOptions().then((opts) => {
    destinationOptions.value = Array.isArray(opts) ? opts : []
  }).catch(() => {
    destinationOptions.value = []
  })
})
</script>

<style scoped>
/* 弹窗容器 - 玻璃感 */
.dm-glass {
  --el-dialog-padding-primary: 0;
}
.daily-manage-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 20px 56px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.04);
}
.daily-manage-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}
.daily-manage-dialog :deep(.el-dialog__footer) {
  padding: 0;
  border-top: none;
}

/* ヘッダー - 玻璃质感 */
.dm-header {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.92) 0%, rgba(99, 102, 241, 0.92) 100%);
  backdrop-filter: blur(12px);
  padding: 6px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.2);
  position: relative;
  overflow: hidden;
}
.dm-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 55%);
  pointer-events: none;
}
.dm-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  min-height: 32px;
  position: relative;
  z-index: 1;
}
.dm-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.dm-title-icon {
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.dm-title-icon .el-icon {
  font-size: 15px;
  color: #fff;
}
.dm-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}
.dm-count-badge {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(6px);
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-weight: 600;
}
.dm-changed-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #fff;
  background: rgba(253, 224, 71, 0.35);
  backdrop-filter: blur(6px);
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  font-weight: 600;
}
.dm-changed-badge .el-icon {
  font-size: 12px;
}
.dm-header-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

/* ヘッダーボタン - 颜色区分 */
.dm-btn {
  height: 30px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 12px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  min-width: 0;
}
.dm-btn .el-icon {
  font-size: 14px;
}
.dm-btn-save {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.35);
}
.dm-btn-save:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}
.dm-btn-save:disabled {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.6);
  box-shadow: none;
}
.dm-btn-close {
  width: 32px;
  padding: 0;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(6px);
}
.dm-btn-close:hover {
  background: rgba(239, 68, 68, 0.9);
  color: #fff;
  border-color: rgba(239, 68, 68, 1);
  transform: translateY(-1px);
}

/* 筛选条 - 紧凑玻璃 */
.dm-filter {
  padding: 6px 12px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.dm-filter-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}
.dm-filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.dm-filter-label {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  font-weight: 500;
}
.dm-date-picker {
  width: 92px;
}
.dm-date-picker :deep(.el-input__wrapper) {
  border-radius: 8px;
  font-size: 12px;
  min-height: 28px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.dm-date-nav {
  display: flex;
  gap: 3px;
}
.dm-nav-btn {
  font-size: 11px !important;
  padding: 4px 8px !important;
  min-height: 26px;
  border-radius: 6px;
  color: #64748b;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.dm-nav-btn:hover {
  color: #475569;
  border-color: #94a3b8;
  background: #f8fafc;
}
.dm-nav-today {
  font-size: 11px !important;
  padding: 4px 10px !important;
  min-height: 26px;
  border-radius: 6px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
  color: #fff !important;
  border: none !important;
}
.dm-nav-today:hover {
  opacity: 0.95;
}
.dm-filter-sep {
  width: 1px;
  height: 20px;
  background: rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
}
.dm-dest-select {
  width: 200px;
}
.dm-dest-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  font-size: 12px;
  min-height: 28px;
}
.dm-shortcuts .dm-filter-label {
  margin-right: 2px;
}
.dm-shortcut-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}
.dm-shortcut-btn {
  font-size: 11px !important;
  padding: 3px 8px !important;
  min-height: 24px;
  border-radius: 6px;
  color: #64748b;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.dm-shortcut-btn:hover {
  color: #475569;
  border-color: #94a3b8;
  background: #f1f5f9;
}
.dm-shortcut-btn.is-active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%);
  color: #4f46e5;
  border-color: rgba(99, 102, 241, 0.4);
  font-weight: 600;
}

/* 表格区域 */
.dm-table-wrap {
  padding: 6px 10px;
  overflow-x: auto;
}
.daily-manage-table :deep(.el-table__cell) {
  padding: 2px 4px;
  font-size: 11px;
  color: #1f2937;
}
.daily-manage-table :deep(.el-table__header th) {
  background: #f5f5f5 !important;
  color: #374151;
  font-size: 11px;
  font-weight: 600;
}
.compact-input :deep(.el-input__inner) {
  height: 28px;
  font-size: 11px;
  text-align: center;
}
.cell-date,
.cell-delivery-date {
  font-size: 11px;
  color: #1f2937;
}
.weekday-saturday {
  color: #0066cc;
}
.weekday-sunday {
  color: #cc0000;
}
.edited-row {
  background: linear-gradient(90deg, rgba(253, 224, 71, 0.12) 0%, rgba(254, 249, 195, 0.08) 100%) !important;
}
.dm-empty {
  text-align: center;
  color: #94a3b8;
  padding: 12px;
  font-size: 12px;
  background: rgba(248, 250, 252, 0.8);
  margin: 0 10px 8px;
  border-radius: 8px;
  border: 1px dashed #e2e8f0;
}
.dm-footer {
  min-height: 4px;
}
.dm-saving-overlay {
  position: fixed;
  inset: 0;
  background: rgba(248, 250, 252, 0.65);
  backdrop-filter: blur(4px);
  z-index: 9999;
}

/* 响应式 */
@media (max-width: 900px) {
  .daily-manage-dialog :deep(.el-dialog) {
    width: 96vw !important;
    max-width: none;
  }
  .dm-filter-inner {
    flex-direction: column;
    align-items: stretch;
  }
  .dm-filter-sep {
    display: none;
  }
  .dm-filter-group {
    flex-wrap: wrap;
  }
  .dm-date-picker {
    width: 100%;
  }
  .dm-dest-select {
    width: 100%;
  }
  .dm-table-wrap {
    padding: 4px 6px;
  }
  .daily-manage-table {
    min-width: 780px;
  }
}
</style>
