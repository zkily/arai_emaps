<template>
  <div class="capacity-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h3>設備稼働設定</h3>
          <div class="card-subtitle">各設備の日別稼働時間・時間帯を設定します</div>
        </div>
      </template>

      <div class="toolbar">
        <el-form :inline="true" label-position="left">
          <el-form-item label="設備">
            <el-select v-model="selectedLineId" placeholder="選択" style="width: 280px" @change="loadData">
              <el-option
                v-for="line in lines"
                :key="line.id"
                :value="line.id"
                :label="productionLineOptionLabel(line)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="期間">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="〜"
              start-placeholder="開始"
              end-placeholder="終了"
              value-format="YYYY-MM-DD"
              @change="loadData"
              style="width: 280px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="loadData">取得</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-loading="loading" class="calendar-grid">
        <div v-if="daySlots.length === 0 && !loading" class="empty">設備と期間を選択してください</div>
        <div v-for="day in daySlots" :key="day.work_date" class="day-card" :class="{ 'is-weekend': isWeekend(day.work_date) }">
          <div class="day-header">
            <span class="day-date">{{ formatDate(day.work_date) }}</span>
            <span class="day-weekday">{{ getWeekday(day.work_date) }}</span>
            <el-tag size="small" :type="day.available_hours > 0 ? 'success' : 'info'">
              {{ day.available_hours.toFixed(1) }}h
            </el-tag>
          </div>
          <div class="slots-list">
            <div v-for="(slot, idx) in day.editSlots" :key="idx" class="slot-row">
              <el-time-picker v-model="slot.start_time" placeholder="開始" format="HH:mm" value-format="HH:mm:ss" size="small" style="width: 100px" />
              <span class="slot-sep">〜</span>
              <el-time-picker v-model="slot.end_time" placeholder="終了" format="HH:mm" value-format="HH:mm:ss" size="small" style="width: 100px" />
              <el-button type="danger" size="small" text @click="removeSlot(day, idx)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-button type="primary" size="small" text @click="addSlot(day)">
              <el-icon><Plus /></el-icon> 時間帯追加
            </el-button>
          </div>
          <div class="day-total">合計: {{ calcTotal(day).toFixed(1) }}h</div>
        </div>
      </div>

      <div v-if="daySlots.length > 0" class="save-bar">
        <el-button type="success" size="large" :loading="saving" @click="saveAll">一括保存</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import {
  fetchLines,
  fetchLineCapacitySlots,
  batchUpsertLineCapacitySlots,
  productionLineOptionLabel,
  type ProductionLine,
  type DaySlotsOut,
} from '@/api/aps'

interface EditSlot {
  start_time: string
  end_time: string
}

interface DayEdit extends DaySlotsOut {
  editSlots: EditSlot[]
}

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const loading = ref(false)
const saving = ref(false)
const daySlots = ref<DayEdit[]>([])

onMounted(async () => {
  try {
    const data = await fetchLines()
    lines.value = data
  } catch { /* ignore */ }
})

async function loadData() {
  if (!selectedLineId.value || !dateRange.value) return
  loading.value = true
  try {
    const data = await fetchLineCapacitySlots(selectedLineId.value, dateRange.value[0], dateRange.value[1])
    daySlots.value = data.map(d => ({
      ...d,
      editSlots: d.slots.length > 0
        ? d.slots.map(s => ({ start_time: s.start_time, end_time: s.end_time }))
        : [],
    }))
  } catch (e: any) {
    ElMessage.error(e?.message || 'データ取得失敗')
  } finally {
    loading.value = false
  }
}

function addSlot(day: DayEdit) {
  day.editSlots.push({ start_time: '08:00:00', end_time: '17:00:00' })
}

function removeSlot(day: DayEdit, idx: number) {
  day.editSlots.splice(idx, 1)
}

function calcTotal(day: DayEdit): number {
  let total = 0
  for (const s of day.editSlots) {
    if (s.start_time && s.end_time) {
      const sp = s.start_time.split(':').map(Number)
      const ep = s.end_time.split(':').map(Number)
      const ss = sp[0] * 3600 + sp[1] * 60 + (sp[2] || 0)
      const es = ep[0] * 3600 + ep[1] * 60 + (ep[2] || 0)
      if (es > ss) total += (es - ss) / 3600
    }
  }
  return total
}

async function saveAll() {
  if (!selectedLineId.value) return
  saving.value = true
  try {
    const days = daySlots.value.map(d => ({
      line_id: selectedLineId.value!,
      work_date: d.work_date,
      slots: d.editSlots
        .filter(s => s.start_time && s.end_time)
        .map((s, idx) => ({
          start_time: s.start_time,
          end_time: s.end_time,
          sort_order: idx,
        })),
    }))
    await batchUpsertLineCapacitySlots({ line_id: selectedLineId.value, days })
    ElMessage.success('保存しました')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失敗')
  } finally {
    saving.value = false
  }
}

function formatDate(d: string): string {
  return d.slice(5)
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

function isWeekend(d: string): boolean {
  const day = new Date(d).getDay()
  return day === 0 || day === 6
}
</script>

<style scoped>
.capacity-container {
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
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  min-height: 200px;
}
.day-card {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  background: #fff;
  transition: box-shadow 0.2s;
}
.day-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.day-card.is-weekend {
  background: #fafafa;
  border-color: #dcdfe6;
}
.day-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
}
.day-date {
  font-size: 15px;
}
.day-weekday {
  font-size: 12px;
  color: #909399;
}
.slots-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
.slot-row {
  display: flex;
  align-items: center;
  gap: 4px;
}
.slot-sep {
  font-size: 12px;
  color: #909399;
}
.day-total {
  font-size: 12px;
  color: #606266;
  text-align: right;
  border-top: 1px solid #f0f0f0;
  padding-top: 6px;
}
.save-bar {
  margin-top: 20px;
  text-align: center;
}
.empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: #909399;
}
</style>
