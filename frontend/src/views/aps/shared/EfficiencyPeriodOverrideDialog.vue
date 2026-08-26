<template>
  <el-dialog
    :model-value="modelValue"
    class="eff-period-dlg"
    width="min(880px, 96vw)"
    top="4vh"
    append-to-body
    destroy-on-close
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
    @open="onOpen"
  >
    <template #header>
      <div class="epd-header">
        <div class="epd-header__icon" aria-hidden="true">
          <el-icon :size="22"><Odometer /></el-icon>
        </div>
        <div class="epd-header__text">
          <div class="epd-header__title-row">
            <span class="epd-header__title">能率期間指定</span>
            <span class="epd-header__badge">製品 × 設備 × 期間</span>
          </div>
          <div class="epd-header__meta">
            <span class="epd-chip epd-chip--line">{{ lineLabel || '—' }}</span>
            <span v-if="machineCd" class="epd-chip epd-chip--code">{{ machineCd }}</span>
          </div>
        </div>
      </div>
    </template>

    <div class="epd-body">
      <div class="epd-hint">
        <div class="epd-hint__item epd-hint__item--active">
          <span class="epd-dot" />
          <span>適用中</span>
        </div>
        <div class="epd-hint__item epd-hint__item--future">
          <span class="epd-dot" />
          <span>予定</span>
        </div>
        <div class="epd-hint__item epd-hint__item--past">
          <span class="epd-dot" />
          <span>終了</span>
        </div>
        <p class="epd-hint__note">
          指定期間内のみ本/Hを上書き（終了日必須）。未指定日は設備能率マスタのままです。
        </p>
      </div>

      <section class="epd-card epd-card--form" :class="{ 'epd-card--editing': editingId != null }">
        <div class="epd-card__head">
          <span class="epd-card__label">{{ editingId != null ? '指定を編集' : '新規指定' }}</span>
          <span v-if="editingId != null" class="epd-card__edit-tag">編集中 #{{ editingId }}</span>
        </div>
        <div class="epd-form-grid">
          <div class="epd-field epd-field--product">
            <label class="epd-field__label">製品 <em>*</em></label>
            <el-select
              v-model="form.product_cd"
              filterable
              clearable
              placeholder="製品を選択"
              :loading="loadingProducts"
              class="epd-field__control"
            >
              <el-option
                v-for="row in productOptions"
                :key="row.product_cd"
                :value="row.product_cd"
                :label="row.label"
                :disabled="!row.product_cd"
              />
            </el-select>
          </div>
          <div class="epd-field epd-field--rate">
            <label class="epd-field__label">能率 <em>*</em></label>
            <div class="epd-rate-wrap">
              <el-input-number
                v-model="form.efficiency_rate"
                :min="0.1"
                :step="1"
                :precision="1"
                controls-position="right"
                class="epd-field__control epd-rate-input"
              />
              <span class="epd-rate-unit">本/H</span>
            </div>
          </div>
          <div class="epd-field">
            <label class="epd-field__label">開始日 <em>*</em></label>
            <el-date-picker
              v-model="form.period_from"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="開始"
              class="epd-field__control"
            />
          </div>
          <div class="epd-field">
            <label class="epd-field__label">終了日 <em>*</em></label>
            <el-date-picker
              v-model="form.period_to"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="終了"
              class="epd-field__control"
            />
          </div>
          <div class="epd-field epd-field--remarks">
            <label class="epd-field__label">備考</label>
            <el-input v-model="form.remarks" clearable maxlength="200" placeholder="任意" class="epd-field__control" />
          </div>
          <div class="epd-field epd-field--actions">
            <el-button
              type="primary"
              class="epd-btn-save"
              :loading="saving"
              :disabled="!canEdit"
              @click="save"
            >
              {{ editingId != null ? '更新する' : '追加する' }}
            </el-button>
            <el-button v-if="editingId != null" class="epd-btn-cancel" @click="resetForm">取消</el-button>
          </div>
        </div>
      </section>

      <section class="epd-card epd-card--list">
        <div class="epd-card__head">
          <span class="epd-card__label">登録一覧</span>
          <span class="epd-card__count">{{ rows.length }} 件</span>
        </div>
        <el-table
          v-loading="loading"
          :data="rows"
          class="epd-table"
          size="small"
          max-height="340"
          empty-text="この設備の期間指定はありません"
          :row-class-name="rowClassName"
        >
          <el-table-column label="状態" width="88" align="center">
            <template #default="{ row }">
              <span class="epd-status" :class="`epd-status--${periodStatus(row)}`">
                {{ periodStatusLabel(row) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="製品" min-width="150">
            <template #default="{ row }">
              <div class="epd-prod-name">{{ row.product_name || '—' }}</div>
              <div class="epd-prod-cd">{{ row.product_cd }}</div>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="100" align="right">
            <template #default="{ row }">
              <span class="epd-rate-pill">{{ formatRate(row.efficiency_rate) }}<small>本/H</small></span>
            </template>
          </el-table-column>
          <el-table-column label="期間" min-width="200">
            <template #default="{ row }">
              <div class="epd-period">
                <span class="epd-period__from">{{ row.period_from }}</span>
                <span class="epd-period__sep">→</span>
                <span class="epd-period__to">{{ row.period_to }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="備考" min-width="120" show-overflow-tooltip prop="remarks" />
          <el-table-column label="操作" width="128" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" :disabled="!canEdit" @click="editRow(row)">
                編集
              </el-button>
              <el-button link type="danger" size="small" :disabled="!canEdit" @click="removeRow(row)">
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <template #footer>
      <div class="epd-footer">
        <el-button class="epd-btn-close" @click="emit('update:modelValue', false)">閉じる</el-button>
        <el-button
          type="warning"
          class="epd-btn-replan"
          :loading="replanning"
          :disabled="!machineCd"
          @click="emit('request-replan')"
        >
          ライン順で再計算
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Odometer } from '@element-plus/icons-vue'
import {
  fetchEfficiencyPeriodOverrides,
  createEfficiencyPeriodOverride,
  updateEfficiencyPeriodOverride,
  deleteEfficiencyPeriodOverride,
  type EfficiencyPeriodOverride,
} from '@/api/aps'

export interface EfficiencyPeriodProductOption {
  product_cd: string
  product_name?: string | null
  label: string
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    machineCd: string
    machinesName?: string | null
    lineLabel?: string
    productOptions: EfficiencyPeriodProductOption[]
    loadingProducts?: boolean
    defaultProductCd?: string
    canEdit?: boolean
    replanning?: boolean
  }>(),
  {
    machinesName: null,
    lineLabel: '',
    loadingProducts: false,
    defaultProductCd: '',
    canEdit: true,
    replanning: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [boolean]
  'request-replan': []
}>()

const loading = ref(false)
const saving = ref(false)
const rows = ref<EfficiencyPeriodOverride[]>([])
const editingId = ref<number | null>(null)
const form = ref({
  product_cd: '',
  efficiency_rate: 45 as number,
  period_from: '',
  period_to: '',
  remarks: '',
})

function todayIso(): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

function formatRate(v: number | null | undefined): string {
  const n = Number(v)
  if (!Number.isFinite(n) || n <= 0) return '—'
  return Number.isInteger(n) ? String(n) : n.toFixed(1)
}

function formatApiError(e: unknown): string {
  const anyE = e as { response?: { data?: { detail?: string | { msg?: string }[] } }; message?: string }
  const detail = anyE?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  return anyE?.message || ''
}

type PeriodStatus = 'active' | 'future' | 'past'

function periodStatus(row: EfficiencyPeriodOverride): PeriodStatus {
  const today = todayIso()
  const from = (row.period_from || '').trim()
  const to = (row.period_to || '').trim()
  if (from && to && from <= today && today <= to) return 'active'
  if (from && from > today) return 'future'
  return 'past'
}

function periodStatusLabel(row: EfficiencyPeriodOverride): string {
  const s = periodStatus(row)
  if (s === 'active') return '適用中'
  if (s === 'future') return '予定'
  return '終了'
}

function rowClassName({ row }: { row: EfficiencyPeriodOverride }): string {
  return `epd-row--${periodStatus(row)}`
}

function resetForm() {
  editingId.value = null
  const today = todayIso()
  form.value = {
    product_cd: (props.defaultProductCd || '').trim(),
    efficiency_rate: 45,
    period_from: today,
    period_to: today,
    remarks: '',
  }
}

async function loadRows() {
  const mcd = (props.machineCd || '').trim()
  if (!mcd) {
    rows.value = []
    return
  }
  loading.value = true
  try {
    const res = await fetchEfficiencyPeriodOverrides({ machineCd: mcd, activeOnly: true })
    rows.value = Array.isArray(res?.data) ? res.data! : []
  } catch (e: unknown) {
    rows.value = []
    ElMessage.error(formatApiError(e) || '能率期間指定の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

async function onOpen() {
  resetForm()
  await loadRows()
}

function editRow(row: EfficiencyPeriodOverride) {
  editingId.value = row.id
  form.value = {
    product_cd: (row.product_cd || '').trim(),
    efficiency_rate: Number(row.efficiency_rate) || 0,
    period_from: row.period_from || '',
    period_to: row.period_to || '',
    remarks: row.remarks || '',
  }
}

async function save() {
  if (!props.canEdit) {
    ElMessage.warning('編集権限がありません')
    return
  }
  const mcd = (props.machineCd || '').trim()
  if (!mcd) {
    ElMessage.warning('設備コードが取得できません')
    return
  }
  const productCd = (form.value.product_cd || '').trim()
  const from = (form.value.period_from || '').trim()
  const to = (form.value.period_to || '').trim()
  const rate = Number(form.value.efficiency_rate)
  if (!productCd) {
    ElMessage.warning('製品を選択してください')
    return
  }
  if (!from || !to) {
    ElMessage.warning('開始日と終了日は必須です')
    return
  }
  if (from > to) {
    ElMessage.warning('開始日は終了日以前にしてください')
    return
  }
  if (!(rate > 0)) {
    ElMessage.warning('能率（本/H）は 0 より大きい値にしてください')
    return
  }
  const opt = props.productOptions.find((r) => r.product_cd === productCd)
  const body = {
    machine_cd: mcd,
    machines_name: (props.machinesName || '').trim() || null,
    product_cd: productCd,
    product_name: (opt?.product_name || '').trim() || null,
    efficiency_rate: rate,
    period_from: from,
    period_to: to,
    remarks: (form.value.remarks || '').trim() || null,
    status: 1,
  }
  saving.value = true
  try {
    if (editingId.value != null) {
      await updateEfficiencyPeriodOverride(editingId.value, body)
      ElMessage.success('能率期間指定を更新しました')
    } else {
      await createEfficiencyPeriodOverride(body)
      ElMessage.success('能率期間指定を追加しました')
    }
    resetForm()
    await loadRows()
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function removeRow(row: EfficiencyPeriodOverride) {
  if (!props.canEdit) {
    ElMessage.warning('編集権限がありません')
    return
  }
  try {
    await ElMessageBox.confirm(
      `${row.product_name || row.product_cd}（${row.period_from}〜${row.period_to}）を削除しますか？`,
      '能率期間指定の削除',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  try {
    await deleteEfficiencyPeriodOverride(row.id)
    ElMessage.success('削除しました')
    if (editingId.value === row.id) resetForm()
    await loadRows()
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '削除に失敗しました')
  }
}

watch(
  () => props.defaultProductCd,
  (cd) => {
    if (editingId.value == null && props.modelValue) {
      form.value.product_cd = (cd || '').trim()
    }
  },
)
</script>

<style scoped lang="scss">
.epd-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding-right: 28px;
}

.epd-header__icon {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #0f766e;
  background: linear-gradient(145deg, #ccfbf1 0%, #99f6e4 55%, #5eead4 100%);
  box-shadow: 0 8px 18px -10px rgba(13, 148, 136, 0.55);
}

.epd-header__text {
  min-width: 0;
  flex: 1;
}

.epd-header__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.epd-header__title {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0f172a;
}

.epd-header__badge {
  font-size: 11px;
  font-weight: 600;
  color: #0f766e;
  background: rgba(15, 118, 110, 0.1);
  border: 1px solid rgba(15, 118, 110, 0.18);
  border-radius: 999px;
  padding: 2px 10px;
}

.epd-header__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.epd-chip {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  line-height: 1.3;
}

.epd-chip--line {
  color: #1e3a8a;
  background: linear-gradient(135deg, #dbeafe, #eff6ff);
  border: 1px solid #bfdbfe;
}

.epd-chip--code {
  color: #334155;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 500;
}

.epd-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.epd-hint {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  padding: 10px 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f0fdfa 50%, #eff6ff 100%);
  border: 1px solid #e2e8f0;
}

.epd-hint__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
}

.epd-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.epd-hint__item--active {
  color: #047857;
  .epd-dot {
    background: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
  }
}

.epd-hint__item--future {
  color: #1d4ed8;
  .epd-dot {
    background: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
  }
}

.epd-hint__item--past {
  color: #64748b;
  .epd-dot {
    background: #94a3b8;
  }
}

.epd-hint__note {
  margin: 0;
  flex: 1 1 220px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.45;
}

.epd-card {
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  background: #fff;
  overflow: hidden;
}

.epd-card--form {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 10px 24px -18px rgba(15, 23, 42, 0.35);
}

.epd-card--editing {
  border-color: #fbbf24;
  box-shadow:
    0 0 0 1px rgba(251, 191, 36, 0.25),
    0 12px 28px -16px rgba(217, 119, 6, 0.35);
}

.epd-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid #eef2f7;
  background: rgba(248, 250, 252, 0.9);
}

.epd-card__label {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.epd-card__edit-tag {
  font-size: 11px;
  font-weight: 600;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 999px;
  padding: 2px 8px;
}

.epd-card__count {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 2px 10px;
}

.epd-form-grid {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) minmax(120px, 0.7fr) minmax(130px, 0.8fr) minmax(130px, 0.8fr);
  gap: 12px 12px;
  padding: 14px;
}

.epd-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.epd-field__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #64748b;
  text-transform: none;

  em {
    color: #ef4444;
    font-style: normal;
    margin-left: 2px;
  }
}

.epd-field__control {
  width: 100%;
}

.epd-field--remarks {
  grid-column: 1 / 3;
}

.epd-field--actions {
  grid-column: 3 / 5;
  flex-direction: row;
  align-items: flex-end;
  justify-content: flex-end;
  gap: 8px;
}

.epd-rate-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.epd-rate-input {
  flex: 1;
}

.epd-rate-unit {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  padding: 6px 8px;
}

.epd-btn-save {
  border: none;
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  box-shadow: 0 8px 16px -10px rgba(13, 148, 136, 0.8);
}

.epd-btn-save:hover {
  background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
}

.epd-table {
  --el-table-header-bg-color: #f8fafc;
  border: none !important;
}

.epd-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.epd-table :deep(th.el-table__cell) {
  color: #64748b;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.03em;
}

.epd-table :deep(tr.epd-row--active) {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.08), transparent 42%);
}

.epd-table :deep(tr.epd-row--future) {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.07), transparent 42%);
}

.epd-table :deep(tr.epd-row--past) {
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.1), transparent 42%);
  color: #64748b;
}

.epd-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
}

.epd-status--active {
  color: #047857;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
}

.epd-status--future {
  color: #1d4ed8;
  background: #dbeafe;
  border: 1px solid #93c5fd;
}

.epd-status--past {
  color: #475569;
  background: #e2e8f0;
  border: 1px solid #cbd5e1;
}

.epd-prod-name {
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
}

.epd-prod-cd {
  margin-top: 2px;
  font-size: 11px;
  color: #94a3b8;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.epd-rate-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-weight: 700;
  color: #c2410c;
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 8px;
  padding: 3px 8px;

  small {
    font-size: 10px;
    font-weight: 600;
    color: #ea580c;
  }
}

.epd-period {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.epd-period__from {
  color: #0f766e;
  font-weight: 600;
}

.epd-period__sep {
  color: #94a3b8;
}

.epd-period__to {
  color: #1d4ed8;
  font-weight: 600;
}

.epd-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.epd-btn-replan {
  border: none;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 8px 16px -10px rgba(217, 119, 6, 0.75);
}

@media (max-width: 760px) {
  .epd-form-grid {
    grid-template-columns: 1fr 1fr;
  }

  .epd-field--remarks,
  .epd-field--actions {
    grid-column: 1 / -1;
  }

  .epd-field--actions {
    justify-content: stretch;

    .el-button {
      flex: 1;
    }
  }
}
</style>

<style lang="scss">
.eff-period-dlg.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 28px 56px -18px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 118, 110, 0.12);
}

.eff-period-dlg .el-dialog__header {
  margin-right: 0;
  padding: 16px 18px 12px;
  border-bottom: none;
  background: linear-gradient(135deg, #f0fdfa 0%, #ecfeff 40%, #f8fafc 100%);
}

.eff-period-dlg .el-dialog__body {
  padding: 12px 18px 8px;
  background: #f8fafc;
}

.eff-period-dlg .el-dialog__footer {
  padding: 12px 18px 16px;
  background: #fff;
  border-top: 1px solid #eef2f7;
}
</style>
