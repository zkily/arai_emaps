<template>
  <div class="batch-plans-page">
    <header class="batch-head">
      <div class="batch-head__main">
        <h2 class="batch-head__title">
          <el-icon class="batch-head__title-icon"><List /></el-icon>
          APS ロット計画
        </h2>
        <p class="batch-head__desc">
          APS 工単をロット（lot_number）へ展開した計画一覧です。
        </p>
      </div>
    </header>

    <div class="batch-panel batch-panel--filter">
      <div class="batch-panel__accent" aria-hidden="true" />
      <div class="batch-panel__body">
        <el-form :inline="true" label-position="left" size="default" class="filter-form">
          <el-form-item>
            <template #label>
              <span class="filter-form__lbl">
                <el-icon><Calendar /></el-icon>
                生産月
              </span>
            </template>
            <el-date-picker
              v-model="productionMonth"
              type="month"
              value-format="YYYY-MM"
              placeholder="生産月を選択"
              class="filter-form__month"
              clearable
            />
          </el-form-item>

          <el-form-item>
            <template #label>
              <span class="filter-form__lbl">
                <el-icon><Monitor /></el-icon>
                設備
              </span>
            </template>
            <el-select
              v-model="selectedLineId"
              placeholder="設備（ライン）を選択"
              class="filter-form__line"
              clearable
              filterable
              :loading="loadingLines"
            >
              <el-option
                v-for="line in lines"
                :key="line.id"
                :value="line.id"
                :label="productionLineOptionLabel(line)"
              />
            </el-select>
          </el-form-item>

          <el-form-item class="filter-form__actions">
            <el-button type="primary" :icon="Search" :loading="loading" @click="loadBatchPlans">
              検索
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <div class="batch-panel batch-panel--table">
      <div class="batch-panel__accent batch-panel__accent--muted" aria-hidden="true" />
      <div class="batch-panel__body batch-panel__body--table">
        <div class="table-sec-hd">
          <span class="table-sec-hd__title">ロット一覧</span>
          <span class="table-sec-hd__badge">{{ rows.length }}</span>
        </div>

        <div v-loading="loading" class="table-wrap">
          <el-table
            :data="rows"
            border
            stripe
            size="small"
            row-key="id"
            class="batch-table"
          >
            <template #empty>
              <el-empty description="条件に一致するデータがありません" class="table-empty" />
            </template>
            <el-table-column prop="lot_number" label="ロットNo." width="100" align="center">
              <template #default="{ row }">
                <span class="lot-chip">{{ row.lot_number }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="製品名" min-width="260" show-overflow-tooltip />
            <el-table-column prop="production_line" label="ライン" min-width="128" show-overflow-tooltip />
            <el-table-column prop="priority_order" label="順位" width="72" align="center">
              <template #default="{ row }">
                {{ row.priority_order ?? '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="planned_quantity" label="計画本数" width="112" align="right">
              <template #default="{ row }">
                <span class="num-cell">{{ row.planned_quantity?.toLocaleString() ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="production_lot_size" label="総ロット数" width="112" align="right">
              <template #default="{ row }">
                <span class="num-cell">{{
                  row.production_lot_size != null && row.production_lot_size !== ''
                    ? Number(row.production_lot_size).toLocaleString()
                    : '—'
                }}</span>
              </template>
            </el-table-column>
            <el-table-column label="期間" min-width="200">
              <template #default="{ row }">
                <div class="period-cell">
                  <span class="period-cell__dt">{{ formatDateTime(row.start_date) }}</span>
                  <span class="period-cell__sep">〜</span>
                  <span class="period-cell__dt">{{ formatDateTime(row.end_date) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状態" width="132" align="center">
              <template #default="{ row }">
                <el-tag :type="batchPlanStatusTagType(row.status)" size="small" effect="plain" round>
                  {{ batchPlanStatusJa(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Calendar, Monitor, Search } from '@element-plus/icons-vue'
import type { TagProps } from 'element-plus'
import {
  fetchApsBatchPlans,
  fetchLines,
  productionLineOptionLabel,
  type ProductionLine,
  type ApsBatchPlanOut,
} from '@/api/aps'

/** 設備プルダウンは成型工程のみ（fetchLines 無引数＝全工程） */
const FORMING_PROCESS_CD = 'KT04'

const productionMonth = ref<string>(dayjs().format('YYYY-MM'))

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const loadingLines = ref(false)

const rows = ref<ApsBatchPlanOut[]>([])
const loading = ref(false)

onMounted(async () => {
  await loadLines()
  await loadBatchPlans()
})

async function loadLines() {
  loadingLines.value = true
  try {
    lines.value = await fetchLines(FORMING_PROCESS_CD)
    if (
      selectedLineId.value != null &&
      !lines.value.some((l) => l.id === selectedLineId.value)
    ) {
      selectedLineId.value = null
    }
  } catch {
    lines.value = []
    ElMessage.error('設備一覧の取得に失敗しました')
  } finally {
    loadingLines.value = false
  }
}

async function loadBatchPlans() {
  loading.value = true
  try {
    rows.value = await fetchApsBatchPlans({
      productionMonth: productionMonth.value,
      lineId: selectedLineId.value ?? null,
    })
  } catch (e: unknown) {
    rows.value = []
    ElMessage.error(String((e as any)?.message || e))
  } finally {
    loading.value = false
  }
}

function formatDateTime(v: string | null | undefined): string {
  if (!v) return '—'
  const s = String(v).replace('T', ' ')
  return s.length >= 16 ? s.slice(0, 16) : s
}

/** DB は英語コード（例: PLANNED）を返す想定。一覧では日本語ラベルで表示 */
const BATCH_PLAN_STATUS_JA: Record<string, string> = {
  PLANNED: '計画',
  SCHEDULED: '予定済',
  CONFIRMED: '確定',
  RELEASED: '発行済',
  IN_PROGRESS: '進行中',
  RUNNING: '進行中',
  ACTIVE: '進行中',
  COMPLETED: '完了',
  COMPLETE: '完了',
  DONE: '完了',
  FINISHED: '完了',
  CLOSED: '完了',
  CANCELLED: '取消',
  CANCELED: '取消',
  ABORTED: '中止',
  HOLD: '保留',
  PAUSED: '一時停止',
  DRAFT: '下書き',
  PENDING: '未着手',
}

function batchPlanStatusKey(raw: string): string {
  return (raw || '').trim().toUpperCase().replace(/[\s-]+/g, '_')
}

function batchPlanStatusJa(raw: string | null | undefined): string {
  const k = (raw || '').trim()
  if (!k) return '—'
  const mapped = BATCH_PLAN_STATUS_JA[batchPlanStatusKey(k)]
  if (mapped) return mapped
  return k
}

function batchPlanStatusTagType(raw: string | null | undefined): TagProps['type'] {
  const k = (raw || '').trim()
  if (!k) return 'info'
  const u = batchPlanStatusKey(k)
  if (['COMPLETED', 'COMPLETE', 'DONE', 'FINISHED', 'CLOSED', 'CONFIRMED', 'RELEASED'].includes(u)) return 'success'
  if (['CANCELLED', 'CANCELED', 'ABORTED'].includes(u)) return 'danger'
  if (['IN_PROGRESS', 'RUNNING', 'ACTIVE', 'HOLD', 'PAUSED', 'PENDING'].includes(u)) return 'warning'
  if (['PLANNED', 'SCHEDULED', 'DRAFT'].includes(u)) return 'info'
  if (/確定|完了|済|発行/i.test(k)) return 'success'
  if (/取消|中止|破棄/i.test(k)) return 'danger'
  if (/進行|着手|保留|未着手|一時停止/i.test(k)) return 'warning'
  if (/計画|予定|下書き/i.test(k)) return 'info'
  return 'info'
}
</script>

<style scoped>
.batch-plans-page {
  padding: 10px 14px 20px;
  max-width: 1920px;
  margin: 0 auto;
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background:
    radial-gradient(circle at 8% -18%, rgba(64, 158, 255, 0.09), transparent 36%),
    radial-gradient(circle at 102% -14%, rgba(103, 194, 58, 0.07), transparent 30%),
    var(--el-bg-color-page);
}

.batch-head__main {
  min-width: 0;
}

.batch-head__title {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.batch-head__title-icon {
  font-size: 22px;
  color: var(--el-color-primary);
}

.batch-head__desc {
  margin: 0;
  padding-left: 30px;
  font-size: 13px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
}

.batch-panel {
  position: relative;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.batch-panel__accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--el-color-primary-light-3), var(--el-color-primary));
}

.batch-panel__accent--muted {
  background: linear-gradient(180deg, var(--el-color-info-light-5), var(--el-color-info-light-3));
}

.batch-panel__body {
  padding: 14px 16px 14px 18px;
}

.batch-panel__body--table {
  padding-bottom: 16px;
}

.batch-panel--filter .batch-panel__body {
  background: linear-gradient(
    105deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 42%,
    var(--el-bg-color) 100%
  );
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px 16px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.filter-form__lbl {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.filter-form__lbl .el-icon {
  font-size: 15px;
  color: var(--el-color-primary);
}

.filter-form__month {
  width: 168px;
}

.filter-form__line {
  width: min(320px, 100%);
}

.filter-form__actions {
  margin-left: auto;
}

.table-sec-hd {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.table-sec-hd__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.table-sec-hd__badge {
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  border: 1px solid var(--el-color-primary-light-5);
}

.table-wrap {
  min-height: 120px;
  border-radius: 8px;
  overflow: hidden;
}

.table-empty {
  padding: 36px 16px;
}

.table-empty :deep(.el-empty__description) {
  margin-top: 12px;
}

.batch-table {
  width: 100%;
  border-radius: 8px;
}

.batch-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.batch-table :deep(.el-table__header-wrapper th) {
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%) !important;
  color: var(--el-text-color-primary);
}

.batch-table :deep(.el-table__body td) {
  font-size: 13px;
}

.batch-table :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: var(--el-fill-color-light) !important;
}

.lot-chip {
  display: inline-block;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  border: 1px solid var(--el-border-color-lighter);
}

.num-cell {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.period-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.period-cell__sep {
  color: var(--el-text-color-placeholder);
  font-size: 11px;
}

.period-cell__dt {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .filter-form__actions {
    margin-left: 0;
    width: 100%;
  }

  .filter-form__actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
