<template>
  <div class="destination-holiday-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Calendar />
            </el-icon>
            納入先休日設定
          </h1>
          <p class="subtitle">納入先の休日・出勤日の管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ holidayList.length }}</div>
            <div class="stat-label">休日数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ workdayList.length }}</div>
            <div class="stat-label">出勤日数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 納入先筛选区域 -->
    <div class="action-section">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Search />
          </el-icon>
          <span>納入先選択</span>
        </div>
      </div>

      <!-- 筛选内容 -->
      <div class="filters-grid">
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Van />
            </el-icon>
            納入先
          </label>
          <el-select v-model="filters.destination_cd" filterable placeholder="納入先を選択" class="filter-input"
            :loading="optionsLoading">
            <el-option v-for="item in validDestinationOptions" :key="item.cd" :label="`${item.cd} | ${item.name}`"
              :value="item.cd">
              <div class="option-item">
                <el-icon>
                  <Van />
                </el-icon>
                <span class="option-label">{{ item.cd }}</span>
                <span class="option-name">{{ item.name }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
        <div class="filter-actions centered">
          <el-button type="primary" @click="fetchLists" :disabled="!filters.destination_cd" :loading="loading"
            class="load-button">
            <el-icon>
              <Download />
            </el-icon>
            読み込み
          </el-button>
        </div>
      </div>
    </div>

    <!-- 数据内容区域 -->
    <div class="content-wrapper">
      <!-- 休日パネル -->
      <el-card class="data-card holiday-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <h3 class="card-title">
              <el-icon>
                <CircleClose />
              </el-icon>
              休日一覧
            </h3>
            <span class="item-count" v-if="holidayList.length > 0">
              {{ holidayList.length }}件
            </span>
          </div>
        </template>

        <!-- 休日追加区域 -->
        <div class="add-row">
          <el-date-picker v-model="newHolidayDates" type="dates" placeholder="休日を選択" value-format="YYYY-MM-DD"
            class="date-picker" :disabled="!filters.destination_cd" />
          <el-button type="primary" class="add-button" @click="addHoliday"
            :disabled="!filters.destination_cd || !newHolidayDates.length" :loading="actionLoading.holiday">
            <el-icon>
              <Plus />
            </el-icon>
            休日追加
          </el-button>
        </div>

        <!-- 休日列表 -->
        <el-table :data="holidayList" border stripe empty-text="休日データなし" class="modern-table" v-loading="loading"
          :row-class-name="() => 'holiday-row'">
          <el-table-column label="休日日付" align="center" min-width="140">
            <template #default="{ row }">
              <div class="date-cell">
                <el-icon class="date-icon">
                  <Calendar />
                </el-icon>
                <span class="date-text">{{ formatDate(row, null, row.holiday_date) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="曜日" align="center" width="80">
            <template #default="{ row }">
              <el-tag :type="getWeekdayType(row.holiday_date)" size="small" effect="plain" class="weekday-tag">
                {{ getWeekday(row.holiday_date) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="danger" size="small" link class="delete-button" @click="deleteHoliday(row.id)"
                :loading="row.deleting">
                <el-icon>
                  <Delete />
                </el-icon>
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 移动端列表视图 -->
        <div class="mobile-list" v-if="isMobileView && holidayList.length > 0">
          <div v-for="item in holidayList" :key="item.id" class="mobile-item holiday-item">
            <div class="item-info">
              <div class="item-date">{{ formatDate(item, null, item.holiday_date) }}</div>
              <el-tag :type="getWeekdayType(item.holiday_date)" size="small" effect="plain">
                {{ getWeekday(item.holiday_date) }}
              </el-tag>
            </div>
            <div class="item-actions">
              <el-button type="danger" size="small" link @click="deleteHoliday(item.id)" :loading="item.deleting">
                削除
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 臨時出勤日パネル -->
      <el-card class="data-card workday-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <h3 class="card-title">
              <el-icon>
                <CircleCheck />
              </el-icon>
              臨時出勤日一覧
            </h3>
            <span class="item-count" v-if="workdayList.length > 0">
              {{ workdayList.length }}件
            </span>
          </div>
        </template>

        <!-- 出勤日追加区域 -->
        <div class="add-row">
          <el-date-picker v-model="newWorkDate" type="date" placeholder="出勤日を選択" value-format="YYYY-MM-DD"
            class="date-picker" :disabled="!filters.destination_cd" />
          <el-input v-model="newWorkMemo" placeholder="メモ" class="memo-input" :disabled="!filters.destination_cd" />
          <el-button type="success" class="add-button" @click="addWorkDay"
            :disabled="!filters.destination_cd || !newWorkDate" :loading="actionLoading.workday">
            <el-icon>
              <Plus />
            </el-icon>
            出勤日追加
          </el-button>
        </div>

        <!-- 出勤日列表 -->
        <el-table :data="workdayList" border stripe empty-text="臨時出勤日データなし" class="modern-table" v-loading="loading"
          :row-class-name="() => 'workday-row'">
          <el-table-column label="出勤日" align="center" min-width="140">
            <template #default="{ row }">
              <div class="date-cell">
                <el-icon class="date-icon">
                  <Calendar />
                </el-icon>
                <span class="date-text">{{ formatDate(row, null, row.workday_date) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="曜日" align="center" width="80">
            <template #default="{ row }">
              <el-tag :type="getWeekdayType(row.workday_date)" size="small" effect="plain" class="weekday-tag">
                {{ getWeekday(row.workday_date) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="メモ" align="left" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="memo-text">{{ row.memo || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="danger" size="small" link class="delete-button" @click="deleteWorkDay(row.id)"
                :loading="row.deleting">
                <el-icon>
                  <Delete />
                </el-icon>
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 移动端列表视图 -->
        <div class="mobile-list" v-if="isMobileView && workdayList.length > 0">
          <div v-for="item in workdayList" :key="item.id" class="mobile-item workday-item">
            <div class="item-info">
              <div class="item-date">{{ formatDate(item, null, item.workday_date) }}</div>
              <el-tag :type="getWeekdayType(item.workday_date)" size="small" effect="plain">
                {{ getWeekday(item.workday_date) }}
              </el-tag>
            </div>
            <div class="item-memo" v-if="item.memo">{{ item.memo }}</div>
            <div class="item-actions">
              <el-button type="danger" size="small" link @click="deleteWorkDay(item.id)" :loading="item.deleting">
                削除
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getHolidaysByDest,
  getWorkdaysByDest,
  addHolidayDate,
  addWorkdayDate,
  deleteHolidayDate,
  deleteWorkdayDate
} from '@/api/master/destinationMaster'
import { getDestinationOptions } from '@/api/options'
import type { Destination, Holiday, Workday } from '@/types/master'
import {
  Calendar,
  Van,
  Search,
  Download,
  Plus,
  Delete,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'

// 定义组件名称
defineOptions({
  name: 'DestinationHolidayView'
});

// 筛选条件
const filters = reactive({ destination_cd: '' })

// 納入先选项
const destinationOptions = ref<Destination[]>([])
const optionsLoading = ref(false)

// 列表数据
const holidayList = ref<HolidayEx[]>([])
const workdayList = ref<WorkdayEx[]>([])

// 新增用字段
const newHolidayDates = ref<string[]>([])
const newWorkDate = ref('')
const newWorkMemo = ref('')

// 加载状态
const loading = ref(false)
const actionLoading = reactive({
  holiday: false,
  workday: false
})

// 响应式检测是否为移动设备视图
const isMobileView = computed(() => {
  return window.innerWidth <= 768;
})

// HolidayEx、WorkdayEx 类型定义提前并修正语法
type HolidayEx = Holiday & { deleting: boolean }
type WorkdayEx = Omit<Workday, 'workday_date' | 'memo'> & {
  workday_date: string;
  memo?: string;
  deleting: boolean;
}

// 加载データ
const fetchLists = async () => {
  if (!filters.destination_cd) {
    ElMessage.warning('納入先を選択してください')
    return
  }

  loading.value = true
  try {
    const [holidays, workdays] = await Promise.all([
      getHolidaysByDest(filters.destination_cd),
      getWorkdaysByDest(filters.destination_cd)
    ])

    // 添加 deleting 属性，用于控制按钮加载状态
    holidayList.value = holidays.map((h: Holiday) => ({ ...h, deleting: false }))
    workdayList.value = workdays.map((w: any) => ({
      ...w,
      workday_date: w.workday_date ?? w.work_date ?? '',
      memo: w.memo ?? w.reason ?? '',
      deleting: false
    }))

    ElMessage.success('データを読み込みました')
  } catch (error) {
    console.error(error)
    ElMessage.error('データの読み込みに失敗しました')
    holidayList.value = []
    workdayList.value = []
  } finally {
    loading.value = false
  }
}

// 日期格式化
const formatDate = (_row: unknown, _column: unknown, cellValue: string) => {
  if (!cellValue) return ''
  const date = new Date(cellValue)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}年${month}月${day}日`
}

// 获取星期几
const getWeekday = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const weekdays = ['日', '月', '火', '水', '木', '金', '土']
  return weekdays[date.getDay()]
}

// 获取星期几对应的标签类型
const getWeekdayType = (dateStr: string): 'danger' | 'warning' | 'info' => {
  if (!dateStr) return 'info'
  const date = new Date(dateStr)
  const day = date.getDay()
  if (day === 0) return 'danger'  // 周日
  if (day === 6) return 'warning' // 周六
  return 'info'                   // 工作日
}

// 休日追加
const addHoliday = async () => {
  if (!filters.destination_cd || !newHolidayDates.value.length) {
    ElMessage.warning('納入先と日付を選択してください')
    return
  }

  actionLoading.holiday = true
  try {
    // 批量添加所有选中的日期
    await Promise.all(
      newHolidayDates.value.map(date =>
        addHolidayDate(filters.destination_cd, date)
      )
    )
    ElMessage.success('休日を追加しました')
    newHolidayDates.value = []
    fetchLists()
  } catch (error) {
    console.error(error)
    ElMessage.error('休日の追加に失敗しました')
  } finally {
    actionLoading.holiday = false
  }
}

// 休日削除
const deleteHoliday = async (id: number) => {
  const target = holidayList.value.find(h => h.id === id)
  if (!target) return
  (target as HolidayEx).deleting = true
  try {
    await deleteHolidayDate(id)
    ElMessage.success('休日を削除しました')
    fetchLists()
  } catch (error) {
    // console.error(error)
    (ElMessage as any).error('休日の削除に失敗しました')
      (target as HolidayEx).deleting = false
  }
}

// 出勤日追加
const addWorkDay = async () => {
  if (!filters.destination_cd || !newWorkDate.value) {
    ElMessage.warning('納入先と日付を選択してください')
    return
  }

  actionLoading.workday = true
  try {
    await addWorkdayDate(filters.destination_cd, newWorkDate.value, newWorkMemo.value)
    ElMessage.success('出勤日を追加しました')
    newWorkDate.value = ''
    newWorkMemo.value = ''
    fetchLists()
  } catch (error) {
    console.error(error)
    ElMessage.error('出勤日の追加に失敗しました')
  } finally {
    actionLoading.workday = false
  }
}

// 出勤日削除
const deleteWorkDay = async (id: number) => {
  const target = workdayList.value.find(w => w.id === id)
  if (!target) return
  (target as WorkdayEx).deleting = true
  try {
    await deleteWorkdayDate(id)
    ElMessage.success('出勤日を削除しました')
    fetchLists()
  } catch (error) {
    // 只用函数调用，避免类型报错
    if (typeof ElMessage === 'function') {
      ElMessage({ type: 'error', message: '出勤日の削除に失敗しました' })
    }
    (target as WorkdayEx).deleting = false
  }
}

// 过滤出合法納入先
const validDestinationOptions = computed(() =>
  destinationOptions.value.filter(item => item.cd && item.name)
)

// 监听窗口大小变化
onMounted(() => {
  window.addEventListener('resize', () => {
    // 计算属性会自动重新计算
  })
})

// 页面初始化 - 加载納入先选项
onMounted(async () => {
  optionsLoading.value = true
  try {
    const data = await getDestinationOptions()
    destinationOptions.value = data
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    ElMessage.error(msg || '納入先一覧の取得に失敗しました')
  } finally {
    optionsLoading.value = false
  }
})
</script>

<style scoped>
/* 基础变量 */
:root {
  --primary-color: #409eff;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
  --info-color: #909399;
  --text-primary: #303133;
  --text-regular: #606266;
  --text-secondary: #909399;
  --border-color: #dcdfe6;
  --bg-color: #f5f7fa;
  --card-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  --transition-all: all 0.3s ease;
}

/* 主容器 */
.destination-holiday-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 8px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 1.8rem;
  color: #409eff;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 1rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #409eff 0%, #1976d2 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 操作区域 */
.action-section {
  background: white;
  border-radius: 20px;
  padding: 0;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

/* 筛选标题区 */
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
}

.filter-icon {
  font-size: 1.3rem;
  color: #409eff;
}

/* 筛选网格 */
.filters-grid {
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 24px;
  padding: 32px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 4px;
}

.filter-input {
  width: 100%;
  transition: all 0.3s ease;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.filter-actions.centered {
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.load-button {
  width: 100%;
  height: 40px;
  background: linear-gradient(135deg, #409eff 0%, #1976d2 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.load-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.4);
}

/* 选项样式 */
.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-label {
  font-family: monospace;
  font-weight: 500;
  color: #409EFF;
}

.option-name {
  color: #606266;
}

/* 内容区域 */
.content-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.data-card {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.holiday-card .card-title {
  color: #f56c6c;
}

.workday-card .card-title {
  color: #67c23a;
}

.item-count {
  background-color: #f2f6fc;
  color: #909399;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* 添加区域 */
.add-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.date-picker {
  flex: 1;
}

.memo-input {
  flex: 2;
  min-width: 200px;
}

.add-button {
  min-width: 120px;
  transition: all 0.3s ease;
}

.add-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* 表格样式 */
.modern-table {
  width: 100%;
}

.date-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.date-icon {
  color: #409eff;
}

.date-text {
  font-family: monospace;
  font-weight: 500;
}

.weekday-tag {
  min-width: 40px;
}

.memo-text {
  display: block;
  color: var(--text-regular);
  padding: 4px 8px;
}

/* 行样式 */
:deep(.holiday-row td) {
  background-color: #fff8f8 !important;
}

:deep(.workday-row td) {
  background-color: #f8fff8 !important;
}

/* 移动端列表 */
.mobile-list {
  display: none;
  flex-direction: column;
  gap: 12px;
}

.mobile-item {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.holiday-item {
  border-left: 4px solid #f56c6c;
}

.workday-item {
  border-left: 4px solid #67c23a;
}

.item-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-date {
  font-weight: 600;
  font-size: 16px;
}

.item-memo {
  padding: 8px;
  background-color: #f8f8f8;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.item-actions {
  display: flex;
  justify-content: flex-end;
}

/* 动画效果 */
.action-section,
.page-header,
.data-card {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式样式 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }

  .content-wrapper {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .destination-holiday-container {
    padding: 16px;
  }

  .page-header {
    padding: 24px 20px;
  }

  .main-title {
    font-size: 1.6rem;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 24px 20px;
  }

  .modern-table {
    display: none;
  }

  .mobile-list {
    display: flex;
  }

  .add-row {
    flex-direction: column;
  }

  .date-picker,
  .memo-input,
  .add-button {
    width: 100%;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.4rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__header) {
  padding: 16px 20px;
  background-color: #f8fafc;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}
</style>
