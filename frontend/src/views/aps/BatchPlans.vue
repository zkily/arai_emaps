<template>
  <div class="batch-plans-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">APS ロット計画</h2>
      <p class="plan-hd-sub">APS 工単をロット（lot_number）へ展開した計画一覧</p>
    </div>

    <div class="plan-card filter-card">
      <el-form :inline="true" label-position="left" class="filter-form">
        <el-form-item label="生産月">
          <el-date-picker
            v-model="productionMonth"
            type="month"
            value-format="YYYY-MM"
            placeholder="生産月"
            style="width: 160px"
          />
        </el-form-item>

        <el-form-item label="設備">
          <el-select
            v-model="selectedLineId"
            placeholder="設備（ライン）を選択"
            style="width: 280px"
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

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadBatchPlans">
            検索
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="plan-card table-card">
      <div class="plan-sec-hd">
        ロット一覧
        <span class="plan-sec-badge">{{ rows.length }}</span>
      </div>

      <el-empty v-if="loading === false && rows.length === 0" description="データがありません" />

      <el-table v-else :data="rows" border stripe size="small" row-key="id" class="batch-table">
        <el-table-column prop="lot_number" label="ロットNo." width="90" align="center" />
        <el-table-column prop="product_name" label="製品名" min-width="220" />
        <el-table-column prop="product_cd" label="製品CD" width="110" />
        <el-table-column prop="production_line" label="ライン" min-width="130" />
        <el-table-column prop="priority_order" label="順位" width="70" align="center" />
        <el-table-column prop="planned_quantity" label="計画本数" width="120" align="right">
          <template #default="{ row }">
            {{ row.planned_quantity?.toLocaleString() ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="production_lot_size" label="総ロット数" width="120" align="right" />
        <el-table-column label="期間" min-width="210">
          <template #default="{ row }">
            <div class="period-cell">
              <div>{{ formatDateTime(row.start_date) }}</div>
              <div class="period-sep">〜</div>
              <div>{{ formatDateTime(row.end_date) }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状態" width="110" align="center" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchApsBatchPlans,
  fetchLines,
  productionLineOptionLabel,
  type ProductionLine,
  type ApsBatchPlanOut,
} from '@/api/aps'

const DEFAULT_MONTH = '2026-04'
const productionMonth = ref<string>(DEFAULT_MONTH)

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
    lines.value = await fetchLines(null)
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
  // 2026-04-01T13:00:00 -> 2026-04-01 13:00
  const s = String(v).replace('T', ' ')
  return s.length >= 16 ? s.slice(0, 16) : s
}

const _ = computed(() => rows.value.length) // keep reactivity
</script>

<style scoped>
.batch-plans-page {
  padding: 16px 20px;
  background: #f0f2f5;
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-hd {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 4px 2px 0;
}
.plan-hd-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2329;
  margin: 0;
  letter-spacing: 0.3px;
}
.plan-hd-sub {
  font-size: 12px;
  color: #8f959e;
  margin: 0;
}

.plan-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(0, 21, 41, 0.06), 0 4px 12px rgba(0, 21, 41, 0.04);
}

.filter-card {
  padding: 14px 16px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.table-card {
  padding: 14px 16px;
}

.plan-sec-hd {
  font-size: 13px;
  font-weight: 700;
  color: #1f2329;
  margin: 0 0 12px;
  padding-left: 9px;
  border-left: 3px solid #409eff;
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.3;
}
.plan-sec-badge {
  font-size: 11px;
  font-weight: 600;
  background: #409eff;
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 18px;
}

.period-cell {
  display: grid;
  grid-template-columns: 1fr;
}
.period-sep {
  color: #909399;
  font-size: 11px;
  margin: 2px 0;
}
</style>

