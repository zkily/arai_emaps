<template>
  <div class="report-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h3>日別設備計画表</h3>
          <div class="card-subtitle">日付×設備ごとの排産計画を一覧表示</div>
        </div>
      </template>

      <div class="toolbar">
        <el-form :inline="true" label-position="left">
          <el-form-item label="期間">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="〜"
              start-placeholder="開始"
              end-placeholder="終了"
              value-format="YYYY-MM-DD"
              style="width: 280px"
            />
          </el-form-item>
          <el-form-item label="設備">
            <el-select v-model="selectedLineId" placeholder="全て" clearable style="width: 260px">
              <el-option
                v-for="line in lines"
                :key="line.id"
                :value="line.id"
                :label="productionLineOptionLabel(line)"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="loadReport">取得</el-button>
            <el-button @click="printReport">印刷</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-loading="loading">
        <div v-if="groupedData.length === 0 && !loading" class="empty">
          期間を選択して「取得」を押してください
        </div>

        <div v-for="group in groupedData" :key="group.date" class="date-group">
          <div class="date-group-header">{{ group.date }} ({{ getWeekday(group.date) }})</div>
          <div v-for="lineGroup in group.lines" :key="lineGroup.line_code" class="line-block">
            <div class="line-header">
              <span class="line-code">{{ lineGroup.line_code }}</span>
              <el-tag v-if="lineGroup.available_hours != null" size="small" type="info">
                稼働 {{ lineGroup.available_hours.toFixed(1) }}h
              </el-tag>
              <el-tag size="small">合計 {{ lineGroup.total_qty }} 個</el-tag>
            </div>
            <el-table :data="lineGroup.rows" size="small" border stripe class="report-table">
              <el-table-column prop="order_no" label="順番" width="60" align="center" />
              <el-table-column prop="item_name" label="品名" min-width="160" />
              <el-table-column prop="product_cd" label="製品コード" width="120" />
              <el-table-column prop="planned_qty" label="計画数" width="90" align="right" />
              <el-table-column prop="actual_qty" label="実績数" width="90" align="right" />
            </el-table>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchLines,
  fetchDailyEquipmentReport,
  productionLineOptionLabel,
  type ProductionLine,
  type DailyEquipmentReportRow,
} from '@/api/aps'

interface LineBlock {
  line_code: string
  available_hours: number | null
  total_qty: number
  rows: DailyEquipmentReportRow[]
}

interface DateGroup {
  date: string
  lines: LineBlock[]
}

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const loading = ref(false)
const groupedData = ref<DateGroup[]>([])

onMounted(async () => {
  try {
    lines.value = await fetchLines()
  } catch { /* ignore */ }
})

async function loadReport() {
  if (!dateRange.value) {
    ElMessage.warning('期間を選択してください')
    return
  }
  loading.value = true
  try {
    const res = await fetchDailyEquipmentReport(
      dateRange.value[0],
      dateRange.value[1],
      selectedLineId.value ?? undefined,
    )
    const data: DailyEquipmentReportRow[] = res.data || res as any
    groupedData.value = buildGroups(data)
  } catch (e: any) {
    ElMessage.error(e?.message || 'データ取得失敗')
  } finally {
    loading.value = false
  }
}

function buildGroups(rows: DailyEquipmentReportRow[]): DateGroup[] {
  const dateMap = new Map<string, Map<string, LineBlock>>()

  for (const r of rows) {
    if (!dateMap.has(r.schedule_date)) {
      dateMap.set(r.schedule_date, new Map())
    }
    const lineMap = dateMap.get(r.schedule_date)!
    if (!lineMap.has(r.line_code)) {
      lineMap.set(r.line_code, {
        line_code: r.line_code,
        available_hours: r.available_hours,
        total_qty: 0,
        rows: [],
      })
    }
    const block = lineMap.get(r.line_code)!
    block.total_qty += r.planned_qty
    block.rows.push(r)
  }

  const result: DateGroup[] = []
  for (const [d, lineMap] of dateMap) {
    result.push({
      date: d,
      lines: Array.from(lineMap.values()),
    })
  }
  return result.sort((a, b) => a.date.localeCompare(b.date))
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

function printReport() {
  window.print()
}
</script>

<style scoped>
.report-container {
  padding: 20px;
}
.card-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.card-header h3 {
  margin: 0;
}
.card-subtitle {
  font-size: 13px;
  color: #909399;
}
.toolbar {
  margin-bottom: 16px;
}
.empty {
  text-align: center;
  padding: 40px;
  color: #909399;
}
.date-group {
  margin-bottom: 20px;
}
.date-group-header {
  font-size: 16px;
  font-weight: 700;
  padding: 8px 0;
  border-bottom: 2px solid #409eff;
  margin-bottom: 8px;
  color: #303133;
}
.line-block {
  margin-bottom: 12px;
  padding-left: 12px;
}
.line-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.line-code {
  font-weight: 600;
  font-size: 14px;
}
.report-table {
  margin-bottom: 4px;
}

@media print {
  .toolbar, .save-bar { display: none !important; }
  .el-card { box-shadow: none !important; border: none !important; }
}
</style>
