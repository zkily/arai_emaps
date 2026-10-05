<template>
  <!-- 内联模式：直接渲染在页面中（筛选区上方） -->
  <div v-if="inline" class="shipping-calendar-inline">
    <div class="calendar-container">
      <!-- 标题＋月份导航（一行） -->
      <div class="month-navigation">
        <div class="calendar-heading">
          <span class="calendar-heading__icon"><el-icon><Calendar /></el-icon></span>
          <div class="calendar-heading__text">
            <span class="calendar-inline-title">{{ calendarTitle }}</span>
            <span class="calendar-inline-subtitle">{{ calendarSubtitle }}</span>
          </div>
        </div>
        <div class="month-switch">
          <el-button-group>
            <el-button @click="previousMonth" :icon="ArrowLeft" class="prev-month-btn">
              前月
            </el-button>
            <el-button @click="goToCurrentMonth" class="current-month-btn">今月</el-button>
            <el-button @click="nextMonth" :icon="ArrowRight" class="next-month-btn">来月</el-button>
          </el-button-group>
          <div class="current-month">{{ formatMonthFromNumbers(calendarYear, calendarMonth) }}</div>
        </div>
        <el-button type="primary" :icon="Setting" class="group-manage-btn" @click="showGroupManager = true">
          グループ管理
        </el-button>
      </div>
      <div v-if="!hasAnyShippingData" class="no-data-banner">
        <el-icon><Calendar /></el-icon>
        <span>
          {{ formatMonthFromNumbers(calendarYear, calendarMonth) }} は出荷データがありません
        </span>
      </div>
      <div class="calendar-grid">
        <div class="weekday-header">
          <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
        </div>
        <div class="date-grid">
          <div v-for="n in startEmptyDays" :key="`empty-start-${n}`" class="date-cell empty"></div>
          <div
            v-for="date in daysInMonth"
            :key="date"
            class="date-cell"
            :class="{
              today: isToday(date),
              weekend: isWeekend(date),
              'has-data': hasShippingData(date),
            }"
          >
            <div class="date-number">{{ date }}</div>
            <div class="print-buttons" v-if="hasShippingData(date)">
              <div
                v-for="(group, groupIndex) in destinationGroups"
                :key="group.id || groupIndex"
                v-show="!isList || isAllowedGroupForList(group)"
                class="group-button-wrapper"
                :class="{
                  'has-data': hasGroupData(date, groupIndex),
                  'is-printed': isPrinted(date, groupIndex),
                }"
              >
                <el-button
                  :type="getButtonType(date, groupIndex)"
                  size="small"
                  @click="handleGroupPrint(date, groupIndex)"
                  class="group-button pb-btn-plain"
                  :class="{
                    'is-printed': isPrinted(date, groupIndex),
                    [`group-${groupIndex}`]: true,
                  }"
                >
                  <div class="button-content">
                    <span class="button-text">{{ stripReportPrefix(group.groupName) }}</span>
                    <div v-if="isPrinted(date, groupIndex)" class="print-badge">
                      <el-icon class="print-icon"><Check /></el-icon>
                      <span class="print-text">済</span>
                    </div>
                  </div>
                </el-button>
              </div>
            </div>
          </div>
          <div v-for="n in endEmptyDays" :key="`empty-end-${n}`" class="date-cell empty"></div>
        </div>
      </div>
    </div>
  </div>
  <!-- 弹窗模式 -->
  <el-dialog
    v-else
    v-model="visible"
    width="63%"
    :close-on-click-modal="false"
    class="shipping-calendar-dialog"
    @close="handleClose"
  >
    <template #header>
      <div class="dialog-header">
        <span class="dialog-title">{{ calendarTitle }}</span>
        <span class="dialog-subtitle">{{ calendarSubtitle }}</span>
      </div>
    </template>
    <div class="calendar-container">
      <!-- 月份导航 -->
      <div class="month-navigation">
        <el-button-group>
          <el-button @click="previousMonth" :icon="ArrowLeft" class="prev-month-btn">
            前月
          </el-button>
          <el-button @click="goToCurrentMonth" class="current-month-btn">今月</el-button>
          <el-button @click="nextMonth" :icon="ArrowRight" class="next-month-btn">来月</el-button>
        </el-button-group>
        <div class="current-month">
          {{ formatMonthFromNumbers(calendarYear, calendarMonth) }}
        </div>
        <el-button type="primary" :icon="Setting" class="group-manage-btn" @click="showGroupManager = true">
          グループ管理
        </el-button>
      </div>

      <!-- 无数据时的提示条（不隐藏日历，保证每月都能选择/查看） -->
      <div v-if="!hasAnyShippingData" class="no-data-banner">
        <el-icon><Calendar /></el-icon>
        <span>
          {{ formatMonthFromNumbers(calendarYear, calendarMonth) }} は出荷データがありません
        </span>
      </div>

      <!-- 日历网格：始终显示，方便选择任意月份（含 2 月等无数据月份） -->
      <div class="calendar-grid">
        <!-- 星期标题 -->
        <div class="weekday-header">
          <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
        </div>

        <!-- 日期网格 -->
        <div class="date-grid">
          <!-- 空白日期(前月) -->
          <div v-for="n in startEmptyDays" :key="`empty-start-${n}`" class="date-cell empty"></div>

          <!-- 本月日期 -->
          <div
            v-for="date in daysInMonth"
            :key="date"
            class="date-cell"
            :class="{
              today: isToday(date),
              weekend: isWeekend(date),
              'has-data': hasShippingData(date),
            }"
          >
            <div class="date-number">{{ date }}</div>

            <!-- 打印按钮组 -->
            <div class="print-buttons" v-if="hasShippingData(date)">
              <div
                v-for="(group, groupIndex) in destinationGroups"
                :key="group.id || groupIndex"
                v-show="!isList || isAllowedGroupForList(group)"
                class="group-button-wrapper"
                :class="{
                  'has-data': hasGroupData(date, groupIndex),
                  'is-printed': isPrinted(date, groupIndex),
                }"
              >
                <el-button
                  :type="getButtonType(date, groupIndex)"
                  size="small"
                  @click="handleGroupPrint(date, groupIndex)"
                  class="group-button pb-btn-plain"
                  :class="{
                    'is-printed': isPrinted(date, groupIndex),
                    [`group-${groupIndex}`]: true,
                  }"
                >
                  <div class="button-content">
                    <span class="button-text">{{ stripReportPrefix(group.groupName) }}</span>
                    <div v-if="isPrinted(date, groupIndex)" class="print-badge">
                      <el-icon class="print-icon">
                        <Check />
                      </el-icon>
                      <span class="print-text">済</span>
                    </div>
                  </div>
                </el-button>
              </div>
            </div>
          </div>

          <!-- 空白日期(下月) -->
          <div v-for="n in endEmptyDays" :key="`empty-end-${n}`" class="date-cell empty"></div>
        </div>
      </div>
    </div>
  </el-dialog>

  <!-- 分组管理 / 打印预览：内联与弹窗模式共用 -->
  <DestinationGroupManager
    v-model="showGroupManager"
    :page-key="groupsPageKey"
    @groups-updated="handleGroupsUpdated"
  />
  <el-dialog
    v-model="printDialogVisible"
    width="90%"
    :close-on-click-modal="false"
    class="print-preview-dialog"
  >
    <template #header>
      <div class="print-dialog-header">
        <span class="print-dialog-title">
          印刷プレビュー - {{ formatDate(selectedDate) }}
          {{ stripReportPrefix(destinationGroups[selectedGroup]?.groupName) }}
        </span>
        <div class="print-dialog-actions">
          <el-button @click="printDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" @click="executePrint">印刷実行</el-button>
        </div>
      </div>
    </template>
    <div ref="printContent" class="print-content">
      <component
        :is="printComponent"
        v-if="printData && printData.length > 0"
        :data="printData"
        :filters="printFilters"
      />
      <div v-else class="no-data-message">該当するデータがありません</div>
    </div>
  </el-dialog>

  <!-- 隐藏的打印容器，用于直接打印 -->
  <div
    ref="hiddenPrintContainer"
    class="hidden-print-container"
    style="position: absolute; left: -9999px; top: -9999px; visibility: hidden"
  >
    <component
      :is="printComponent"
      v-if="directPrintData && directPrintData.length > 0"
      :data="directPrintData"
      :filters="directPrintFilters"
    />
    <div v-else class="no-data-message">該当するデータがありません</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Setting, Check, Calendar } from '@element-plus/icons-vue'
import request from '@/utils/request'
import ShippingReport from './ShippingReport.vue'
import ShippingOverviewPrint from './ShippingOverviewPrint.vue'
import ShippingListReport from './ShippingListReport.vue'
import DestinationGroupManager from './DestinationGroupManager.vue'
import { recordPrintHistory } from '@/api/shipping/printHistory'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  /** 为 true 时在页面内联显示（不弹窗），用于报告页/出荷予定表页筛选区上方 */
  inline: {
    type: Boolean,
    default: false,
  },
  /** report=出荷報告書（默认）, schedule=出荷予定表（オワリ便・吉良・社内便等）, list=出荷確認リスト（オワリ便・鈴鹿便・社内便等） */
  reportType: {
    type: String,
    default: 'report',
    validator: (v) => ['report', 'schedule', 'list'].includes(v),
  },
})

const emit = defineEmits(['update:modelValue'])

// 响应式数据
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 获取日本时区的当前日期
const getJapanDate = () => {
  const now = new Date()
  const utc = now.getTime() + now.getTimezoneOffset() * 60000
  const japanTime = new Date(utc + 9 * 3600000) // JST = UTC+9
  return japanTime
}

// 将任意日期转换为日本时区
const toJapanDate = (date) => {
  if (!date) return null
  const utc = date.getTime() + date.getTimezoneOffset() * 60000
  const japanTime = new Date(utc + 9 * 3600000)
  return japanTime
}

// 创建日本时区的日期对象（month 为 0-11）
const createJapanDate = (year, month, day = 1) => {
  const date = new Date()
  date.setFullYear(year)
  date.setMonth(month)
  date.setDate(day)
  date.setHours(12, 0, 0, 0) // 设置为正午，避免夏令时问题
  return date
}

// 从 Date 取得 JST 下的年、月（避免本地时区与日本时区不一致导致 1 月显示 28 天等问题）
const getJstYearMonth = (date) => {
  if (!date) return { year: 0, month: 0 }
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'numeric',
    day: '2-digit',
  })
  const parts = formatter.formatToParts(date)
  const year = parseInt(parts.find((p) => p.type === 'year')?.value ?? date.getFullYear(), 10)
  const month =
    parseInt(parts.find((p) => p.type === 'month')?.value ?? date.getMonth() + 1, 10) - 1
  return { year, month }
}

// 日历当前显示的年、月（仅用数字，彻底避免 Date 时区导致 1 月→3 月、2 月消失）
const calendarYear = ref(getJstYearMonth(getJapanDate()).year)
const calendarMonth = ref(getJstYearMonth(getJapanDate()).month)
const shippingData = ref({}) // 按日期存储出荷数据
const printHistory = ref({}) // 打印历史 {date: {groupIndex: boolean}}
const destinationGroups = ref([])
const showGroupManager = ref(false)
const printDialogVisible = ref(false)
const selectedDate = ref(null)
const selectedGroup = ref(0)
const printData = ref([])
const printContent = ref(null)
const hiddenPrintContainer = ref(null)
const directPrintData = ref([])
const directPrintFilters = ref({})

const weekdays = ['日', '月', '火', '水', '木', '金', '土']

// 显示用：去掉「出荷報告書-」前缀（按钮、打印标题、履历标题统一用短名）
const stripReportPrefix = (name) => (name || '').replace(/^出荷報告書-?/, '')

// reportType=list 时仅显示オワリ便・鈴鹿便・社内便
const LIST_ALLOWED_GROUP_NAMES = ['オワリ便', '鈴鹿便', '社内便']
function isAllowedGroupForList(group) {
  if (!group) return false
  const name = stripReportPrefix(group.groupName || group.group_name || '')
  return LIST_ALLOWED_GROUP_NAMES.includes(name)
}

// reportType=schedule 时：出荷予定表（オワリ便・吉良・社内便等）；report 时：出荷報告書；list 时：出荷確認リスト（オワリ便・鈴鹿便・社内便等）
const isSchedule = computed(() => props.reportType === 'schedule')
const isList = computed(() => props.reportType === 'list')
const groupsPageKey = computed(() => {
  if (isSchedule.value) return 'shipping_overview'
  if (isList.value) return 'shipping_list'
  return 'destination_groups_calendar'
})
const reportTypeForHistory = computed(() => {
  if (isSchedule.value) return 'shipping_schedule_calendar'
  if (isList.value) return 'shipping_list_calendar'
  return 'shipping_calendar'
})
const printComponent = computed(() => {
  if (isSchedule.value) return ShippingOverviewPrint
  if (isList.value) return ShippingListReport
  return ShippingReport
})
const calendarTitle = computed(() => {
  if (isSchedule.value) return '出荷予定表カレンダー'
  if (isList.value) return '出荷確認リストカレンダー'
  return '営業報告カレンダー'
})
const calendarSubtitle = computed(() => {
  if (isSchedule.value) return '（オワリ便・吉良・社内便等のグループ別に印刷）'
  if (isList.value) return '（オワリ便・鈴鹿便・社内便等のグループ別に印刷）'
  return '（発行説明：当日--終了便・社内便 翌日--鈴鹿便）'
})

// 计算属性（直接用数字年月，不经过 Date/JST，保证 1 月 31 天、2 月正常）
const daysInMonth = computed(() => {
  return new Date(calendarYear.value, calendarMonth.value + 1, 0).getDate()
})

const startEmptyDays = computed(() => {
  const firstDay = new Date(calendarYear.value, calendarMonth.value, 1)
  return firstDay.getDay()
})

const endEmptyDays = computed(() => {
  const totalCells = 42 // 6周 × 7天
  const filledCells = startEmptyDays.value + daysInMonth.value
  return Math.max(0, totalCells - filledCells)
})

const printFilters = computed(() => {
  if (!selectedDate.value) return {}

  const dateStr = formatDateString(selectedDate.value)
  const group = destinationGroups.value[selectedGroup.value]

  return {
    dateRange: [dateStr, dateStr],
    destinationCds: group?.destinations?.map((dest) => dest.value) || [],
    selectedGroup: selectedGroup.value,
  }
})

// 检查是否有任何出荷数据
const hasAnyShippingData = computed(() => {
  return Object.keys(shippingData.value).length > 0
})

// 方法
onMounted(async () => {
  await loadDestinationGroups()
  await fetchMonthData()
  // 确保分组配置加载完成后再加载打印历史
  await loadPrintHistory()

  // 添加测试功能到全局变量，便于调试
  if (typeof window !== 'undefined') {
    window.shippingCalendarDebug = {
      loadPrintHistory,
      printHistory,
      destinationGroups,
      shippingData,
      calendarYear,
      calendarMonth,
      isPrinted,
      hasShippingData,
      hasGroupData,
      formatDateString,
      createJapanDate,
      addTestData: () => {
        // 添加一些本地测试数据
        const testHistory = {
          '2025-01-08': { 1: true }, // 鈴鹿便
          '2025-01-10': { 0: true }, // オワリ便
          '2025-01-15': { 2: true }, // 社内便
        }
        printHistory.value = { ...printHistory.value, ...testHistory }
        // console.log('🧪 本地测试数据已添加:', testHistory)
      },
      clearData: () => {
        printHistory.value = {}
        // console.log('🧹 打印历史数据已清除')
      },
      addTestDataToAPI: async () => {
        try {
          await loadPrintHistory()
        } catch (error) {
          console.error('❌ 印刷履歴の再読込に失敗:', error)
        }
      },
      runFullAPITest: async () => {
        try {
          await loadPrintHistory()
        } catch (error) {
          console.error('❌ 印刷履歴の再読込に失敗:', error)
        }
      },
      // 新增：测试日期格式修复
      testDateFormatFix: () => {
        console.log('🔧 测试日期格式修复...')
        const testDates = ['2025-1-8', '2025-01-08', '2025-1-15', '2025-01-15']
        testDates.forEach((dateStr) => {
          const dateParts = dateStr.split(/[-/]/)
          if (dateParts.length === 3) {
            const year = dateParts[0]
            const month = dateParts[1].padStart(2, '0')
            const day = dateParts[2].padStart(2, '0')
            const standardDate = `${year}-${month}-${day}`
            console.log(`📅 "${dateStr}" -> "${standardDate}"`)
          }
        })
        console.log('✅ 日期格式修复测试完成')
      },
      // 新增：完整的打印状态测试
      testPrintStatusFix: () => {
        // console.log('🧪 开始测试打印状态修复...')

        // 1. 清除现有历史
        printHistory.value = {}
        console.log('🧹 已清除现有打印历史')

        // 2. 添加测试历史（使用标准化格式）
        const testHistory = {
          '2025-01-08': { 1: true }, // 鈴鹿便
          '2025-01-10': { 0: true }, // オワリ便
          '2025-01-15': { 2: true, 1: true }, // 社内便 + 鈴鹿便
        }
        printHistory.value = testHistory
        console.log('✅ 已添加测试打印历史:', testHistory)

        // 3. 测试isPrinted函数
        const testCases = [
          { date: 8, groupIndex: 1, expected: true, desc: '2025-01-08 鈴鹿便' },
          { date: 8, groupIndex: 0, expected: false, desc: '2025-01-08 オワリ便' },
          { date: 10, groupIndex: 0, expected: true, desc: '2025-01-10 オワリ便' },
          { date: 15, groupIndex: 1, expected: true, desc: '2025-01-15 鈴鹿便' },
          { date: 15, groupIndex: 2, expected: true, desc: '2025-01-15 社内便' },
          { date: 20, groupIndex: 0, expected: false, desc: '2025-01-20 オワリ便（未打印）' },
        ]

        // console.log('🔍 开始测试isPrinted函数...')
        testCases.forEach((testCase) => {
          const result = isPrinted(testCase.date, testCase.groupIndex)
          const status = result === testCase.expected ? '✅ PASS' : '❌ FAIL'
          console.log(`${status} ${testCase.desc}: 期待=${testCase.expected}, 実際=${result}`)
        })

        console.log('🎯 打印状态测试完成！请检查日历界面上的"発行済"状态显示。')
      },
      addTestHistory: (dateStr, groupIndex) => {
        if (!printHistory.value[dateStr]) {
          printHistory.value[dateStr] = {}
        }
        printHistory.value[dateStr][groupIndex] = true
        console.log(`✅ 测试历史已添加: ${dateStr} 组${groupIndex}`)
      },
      clearTestHistory: () => {
        printHistory.value = {}
        console.log('🧹 测试历史已清除')
      },
    }
    // console.log('🔧 调试工具已添加到 window.shippingCalendarDebug')
    // console.log('使用方法:')
    // console.log('- window.shippingCalendarDebug.testPrintStatusFix() // 🆕 测试打印状态修复（推荐）')
    // console.log('- window.shippingCalendarDebug.testDateFormatFix() // 测试日期格式修复')
    // console.log('- window.shippingCalendarDebug.addTestData() // 添加本地测试数据')
    // console.log('- window.shippingCalendarDebug.addTestDataToAPI() // 通过API添加测试数据')
    // console.log('- window.shippingCalendarDebug.runFullAPITest() // 运行完整API测试')
    // console.log('- window.shippingCalendarDebug.loadPrintHistory() // 重新加载打印历史')
    // console.log('- window.shippingCalendarDebug.addTestHistory("2025-01-15", 1) // 添加测试历史')
    // console.log('- window.shippingCalendarDebug.clearTestHistory() // 清除测试历史')
    // console.log('')
    // console.log('🎯 快速测试：运行 window.shippingCalendarDebug.testPrintStatusFix() 来验证修复效果！')
  }
})

// 监听对话框打开状态，打开时重新加载数据
watch(
  () => visible.value,
  async (newVal) => {
    if (newVal) {
      console.log('📂 カレンダーダイアログが開かれました')
      // 对话框打开时重新加载数据
      await loadDestinationGroups()
      await fetchMonthData()
      // 确保分组配置加载完成后再加载打印历史
      if (destinationGroups.value && destinationGroups.value.length > 0) {
        await loadPrintHistory()
      }
    }
  },
  { immediate: false },
)

watch([calendarYear, calendarMonth], async () => {
  console.log(
    '月が変更されました:',
    formatMonthFromNumbers(calendarYear.value, calendarMonth.value),
  )
  await fetchMonthData()
  // 确保分组配置存在后再加载打印历史
  if (destinationGroups.value && destinationGroups.value.length > 0) {
    await loadPrintHistory()
  }
})

// 加载分组配置
async function loadDestinationGroups() {
  try {
    console.log('🔄 分組配置を読み込み中...')
    const response = await request.get(`/api/shipping/destination-groups/${groupsPageKey.value}`)
    console.log('📋 分組配置API応答:', response)

    if (Array.isArray(response)) {
      destinationGroups.value = response.map((group) => ({
        ...group,
        destinations: group.destinations || [],
        groupName: group.group_name,
      }))
    } else {
      destinationGroups.value = []
    }

    console.log('✅ 分組配置読み込み完了:', destinationGroups.value)
  } catch (error) {
    console.error('❌ グループ設定の読み込みに失敗しました:', error)
    ElMessage.error('グループ設定の読み込みに失敗しました')
    destinationGroups.value = []
  }
}

// 获取月份数据（直接用数字年月拼日期，避免时区）
async function fetchMonthData() {
  try {
    const y = calendarYear.value
    const m = calendarMonth.value
    const lastDay = new Date(y, m + 1, 0).getDate()
    const params = {
      date_from: `${y}-${String(m + 1).padStart(2, '0')}-01`,
      date_to: `${y}-${String(m + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`,
    }

    console.log('📅 月間データを取得中...', params)
    const response = await request.get('/api/shipping/overview', { params })
    console.log('📋 API応答:', response)

    // 处理响应数据 - 支持多种响应格式
    let data = null

    // 检查是否是错误响应
    if (response && response.success === false) {
      console.error('❌ API返回错误:', response.message || '未知のエラー')
      ElMessage.error(response.message || '月間データの取得に失敗しました')
      shippingData.value = {}
      return
    }

    // 处理不同的响应格式
    if (Array.isArray(response)) {
      // 格式1: 直接返回数组
      data = response
      console.log('✅ 直接配列形式でデータを取得:', data.length, '件')
    } else if (response && Array.isArray(response.data)) {
      // 格式2/3: { data: [...] } または { success: true, data: [...] }
      data = response.data
      console.log('✅ data / success 形式でデータを取得:', data.length, '件')
    } else {
      // 未知的响应格式
      console.warn('⚠️ 未知の応答形式:', response)
      data = []
    }

    // 按日期分组数据
    const dateGroupedData = {}
    if (data && Array.isArray(data) && data.length > 0) {
      data.forEach((item) => {
        const date = item.shipping_date
        if (date) {
          if (!dateGroupedData[date]) {
            dateGroupedData[date] = []
          }
          dateGroupedData[date].push(item)
        }
      })
      console.log(
        '✅ 月間データを取得しました:',
        Object.keys(dateGroupedData).length,
        '日分のデータ',
      )
    } else {
      console.log('📭 該当月にデータがありません')
    }

    shippingData.value = dateGroupedData
    console.log('📊 最終的なshippingData:', dateGroupedData)
  } catch (error) {
    console.error('❌ 月間データの取得に失敗しました:', error)
    ElMessage.error('月間データの取得に失敗しました: ' + (error.message || '不明なエラー'))
    shippingData.value = {}
  }
}

// 加载打印历史
async function loadPrintHistory() {
  try {
    // 确保分组配置已加载
    if (!destinationGroups.value || destinationGroups.value.length === 0) {
      console.warn('⚠️ 分组配置未加载，跳过打印历史加载')
      return
    }

    const y = calendarYear.value
    const m = calendarMonth.value
    const lastDay = new Date(y, m + 1, 0).getDate()
    // 后端仅支持 offset/limit，且 limit 最大 500
    const params = {
      date_from: `${y}-${String(m + 1).padStart(2, '0')}-01`,
      date_to: `${y}-${String(m + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`,
      report_type: reportTypeForHistory.value,
      offset: 0,
      limit: 500,
    }

    console.log('🔍 打印履歴を検索中...', params)

    const response = await request.get('/api/shipping/print/history', { params })
    console.log('📋 API応答 (原始):', response)
    console.log('📋 現在の分組配置:', destinationGroups.value)

    // 处理打印历史数据
    const history = {}

    // 尝试从不同的响应格式中提取数据
    let printRecords = null
    if (response?.data?.list && Array.isArray(response.data.list)) {
      printRecords = response.data.list
    } else if (response?.list && Array.isArray(response.list)) {
      printRecords = response.list
    } else if (Array.isArray(response)) {
      printRecords = response
    } else if (response?.data && Array.isArray(response.data)) {
      printRecords = response.data
    }

    console.log('🔍 提取到的打印记录:', printRecords)

    if (printRecords && Array.isArray(printRecords)) {
      console.log(`📊 ${printRecords.length}件の打印履歴を処理中...`)

      printRecords.forEach((record, index) => {
        console.log(`🔍 処理中 ${index + 1}/${printRecords.length}:`, record)

        if (record.report_title && record.status === '成功') {
          // 解析 report_title：新格式 "2025-01-08 鈴鹿便"，旧格式 "出荷報告書カレンダー - 2025-1-8 鈴鹿便"
          const titleMatch =
            record.report_title.match(/^(\d{4}[-/]\d{1,2}[-/]\d{1,2})\s+(.+)$/) ||
            record.report_title.match(
              /出荷報告書カレンダー\s*-\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})\s+(.+)/,
            )

          if (titleMatch) {
            const dateStr = titleMatch[1].trim() // 例如: "2025-1-8"
            const groupName = titleMatch[2].trim() // 例如: "鈴鹿便"

            console.log(`📅 解析した日付: "${dateStr}", グループ名: "${groupName}"`)

            // 将日期格式标准化为 YYYY-MM-DD
            const dateParts = dateStr.split(/[-/]/)
            if (dateParts.length === 3) {
              const year = dateParts[0]
              const month = dateParts[1].padStart(2, '0')
              const day = dateParts[2].padStart(2, '0')
              const standardDate = `${year}-${month}-${day}`

              console.log(`📅 日期标准化: "${dateStr}" -> "${standardDate}"`)

              // 先去掉可能存在的文件扩展名，例如 ".pdf"
              const cleanGroupName = groupName.replace(/\.(pdf|PDF)$/i, '').trim()

              // 根据组名映射到组索引（支持带「出荷報告書-」前缀的存储名与无前缀显示名）
              let groupIndex = destinationGroups.value.findIndex(
                (g) =>
                  g.groupName === cleanGroupName ||
                  stripReportPrefix(g.groupName) === cleanGroupName,
              )

              // 如果无法通过组名匹配，再尝试解析 filters 中的 selectedGroup 信息
              if (groupIndex < 0 && record.filters) {
                try {
                  const filtersObj =
                    typeof record.filters === 'string' ? JSON.parse(record.filters) : record.filters

                  // 1) 尝试使用 selectedGroup
                  if (
                    filtersObj &&
                    typeof filtersObj.selectedGroup === 'number' &&
                    filtersObj.selectedGroup >= 0 &&
                    filtersObj.selectedGroup < destinationGroups.value.length
                  ) {
                    groupIndex = filtersObj.selectedGroup
                    console.log(
                      `🔄 フィルター.selectedGroup からグループインデックスを取得: ${groupIndex}`,
                    )
                  }

                  // 2) 如果仍未找到，则根据 destinationCds 与分组目的地进行匹配
                  if (groupIndex < 0 && Array.isArray(filtersObj?.destinationCds)) {
                    const destSet = new Set(filtersObj.destinationCds.map((cd) => String(cd)))

                    destinationGroups.value.forEach((g, idx) => {
                      if (!g?.destinations || g.destinations.length === 0) return

                      const groupSet = new Set(g.destinations.map((d) => String(d.value)))
                      // 判断是否有交集
                      const hasIntersection = [...destSet].some((cd) => groupSet.has(cd))

                      if (hasIntersection && groupIndex < 0) {
                        groupIndex = idx
                        console.log(
                          `🔄 destinationCds からグループインデックスを取得: ${groupIndex} (グループ名: ${g.groupName})`,
                        )
                      }
                    })
                  }
                } catch (e) {
                  console.warn('⚠️ filters 解析失敗:', e)
                }
              }

              if (groupIndex >= 0) {
                if (!history[standardDate]) {
                  history[standardDate] = {}
                }
                history[standardDate][groupIndex] = true
                console.log(
                  `✅ 打印履歴を登録: ${standardDate} ${groupName} (インデックス${groupIndex})`,
                )
              } else {
                console.warn(`⚠️ 未知のグループ名: "${groupName}"`)
              }
            } else {
              console.warn(`⚠️ 日付解析に失敗: "${dateStr}"`)
            }
          } else {
            console.warn(`⚠️ タイトル解析に失敗: "${record.report_title}"`)
          }
        }
      })
    } else {
      console.log('📭 打印履歴データが見つかりません')
    }

    printHistory.value = history
    console.log('🎯 最終的な打印履歴:', history)
    console.log(`📈 登録された日付数: ${Object.keys(history).length}`)
  } catch (error) {
    console.error('❌ 打印履歴の読み込みに失敗しました:', error)

    // 处理不同的错误类型
    if (error.response) {
      const status = error.response.status
      const errorData = error.response.data

      if (status === 403) {
        // 403 Forbidden - 认证失败
        console.warn('⚠️ 認証エラー (403): 打印履歴の読み込み権限がありません')
        // 不显示错误消息，因为打印历史是可选的，不影响主要功能
        printHistory.value = {}
        return
      } else if (status === 401) {
        // 401 Unauthorized - 未认证
        console.warn('⚠️ 認証エラー (401): ログインが必要です')
        ElMessage.warning('ログインが必要です。打印履歴を読み込めませんでした。')
        printHistory.value = {}
        return
      } else {
        // 其他错误
        const errorMessage = errorData?.message || error.message || '不明なエラー'
        console.error(`❌ APIエラー (${status}):`, errorMessage)
        // 不显示错误消息，因为打印历史是可选的
        printHistory.value = {}
        return
      }
    } else if (error.request) {
      // 请求发送但未收到响应
      console.error('❌ ネットワークエラー: サーバーに接続できませんでした')
      printHistory.value = {}
      return
    } else {
      // 其他错误
      console.error('❌ エラー:', error.message)
      printHistory.value = {}
    }
  }
}

// 月份导航（只改数字年月，不碰 Date，彻底避免 1 月→3 月）
function previousMonth() {
  if (calendarMonth.value === 0) {
    calendarYear.value -= 1
    calendarMonth.value = 11
  } else {
    calendarMonth.value -= 1
  }
}

function nextMonth() {
  if (calendarMonth.value === 11) {
    calendarYear.value += 1
    calendarMonth.value = 0
  } else {
    calendarMonth.value += 1
  }
}

function goToCurrentMonth() {
  const { year, month } = getJstYearMonth(getJapanDate())
  calendarYear.value = year
  calendarMonth.value = month
}

// 日期相关方法（直接用 calendarYear/calendarMonth，不经过 Date 时区）
function isToday(date) {
  const todayJst = getJstYearMonth(getJapanDate())
  const todayDay = parseInt(
    new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tokyo', day: '2-digit' }).format(
      getJapanDate(),
    ),
    10,
  )
  return (
    todayJst.year === calendarYear.value &&
    todayJst.month === calendarMonth.value &&
    todayDay === date
  )
}

function isWeekend(date) {
  const dayOfWeek = new Date(calendarYear.value, calendarMonth.value, date).getDay()
  return dayOfWeek === 0 || dayOfWeek === 6
}

function hasShippingData(date) {
  const dateStr = `${calendarYear.value}-${String(calendarMonth.value + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
  return !!shippingData.value[dateStr]
}

function hasGroupData(date, groupIndex) {
  const dateStr = `${calendarYear.value}-${String(calendarMonth.value + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
  const dayData = shippingData.value[dateStr]
  if (!dayData || !Array.isArray(dayData)) return false

  const group = destinationGroups.value[groupIndex]
  if (!group?.destinations || group.destinations.length === 0) return false

  const groupDestinations = group.destinations.map((dest) => dest.value)
  return dayData.some((item) => groupDestinations.includes(item.destination_cd))
}

function getShippingCount(date) {
  const dateStr = `${calendarYear.value}-${String(calendarMonth.value + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
  const dayData = shippingData.value[dateStr]
  return dayData ? dayData.length : 0
}

function isPrinted(date, groupIndex) {
  const dateStr = `${calendarYear.value}-${String(calendarMonth.value + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
  const isAlreadyPrinted = printHistory.value[dateStr]?.[groupIndex] || false

  // 详细的调试信息
  const debugInfo = {
    date,
    groupIndex,
    groupName: destinationGroups.value[groupIndex]?.groupName,
    dateStr,
    historyForDate: printHistory.value[dateStr],
    allPrintHistory: printHistory.value,
    printHistoryKeys: Object.keys(printHistory.value),
    isAlreadyPrinted,
    hasShippingData: hasShippingData(date),
    hasGroupData: hasGroupData(date, groupIndex),
  }

  // 始终显示调试信息以便诊断问题
  if (hasShippingData(date) && hasGroupData(date, groupIndex)) {
    if (isAlreadyPrinted) {
      console.log(`✅ 発行済み確認 [${dateStr}][${groupIndex}]:`, debugInfo)
    } else {
      console.log(`⭕ 未発行 [${dateStr}][${groupIndex}]:`, debugInfo)
      // 显示可用的打印历史键以便调试
      console.log(`🔍 利用可能な履歴キー:`, Object.keys(printHistory.value))
      if (printHistory.value[dateStr]) {
        console.log(`🔍 該当日の履歴:`, printHistory.value[dateStr])
      }
    }
  }

  return isAlreadyPrinted
}

function getButtonType(date, groupIndex) {
  if (isPrinted(date, groupIndex)) {
    return 'success'
  }
  return hasGroupData(date, groupIndex) ? 'primary' : 'info'
}

// 打印处理 - 直接打印，不显示预览
async function handleGroupPrint(date, groupIndex) {
  try {
    const group = destinationGroups.value[groupIndex]

    if (!group?.destinations || group.destinations.length === 0) {
      ElMessage.warning('グループに納入先が設定されていません')
      return
    }

    // 用日历数字拼日期，避免 Date 时区导致请求错日、取不到数据
    const dateStr = `${calendarYear.value}-${String(calendarMonth.value + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
    selectedDate.value = new Date(dateStr + 'T12:00:00')
    selectedGroup.value = groupIndex

    // 获取打印数据（传 dateStr 保证 API 请求日期正确）
    await fetchDirectPrintData(dateStr, groupIndex)

    if (!directPrintData.value || directPrintData.value.length === 0) {
      ElMessage.warning('該当するデータがありません')
      return
    }

    // 等待一下让组件渲染完成
    await new Promise((resolve) => setTimeout(resolve, 100))

    // 直接执行打印
    await executeDirectPrint(dateStr, groupIndex)
  } catch (error) {
    console.error('印刷処理に失敗しました:', error)
    ElMessage.error('印刷処理に失敗しました')
  }
}

async function fetchPrintData(date, groupIndex) {
  try {
    const dateStr = formatDateString(date)
    const group = destinationGroups.value[groupIndex]

    if (!group?.destinations || group.destinations.length === 0) {
      printData.value = []
      return
    }

    const destinationCds = group.destinations.map((dest) => dest.value)

    const params = {
      date_from: dateStr,
      date_to: dateStr,
      destination_cds: destinationCds.join(','),
    }

    const response = await request.get('/api/shipping/overview', { params })

    // 处理响应数据
    let data = null
    if (Array.isArray(response)) {
      data = response
    } else if (response && Array.isArray(response.data)) {
      data = response.data
    }

    printData.value = data || []
    console.log('印刷データを取得しました:', printData.value)
  } catch (error) {
    console.error('印刷データの取得に失敗しました:', error)
    ElMessage.error('印刷データの取得に失敗しました')
    printData.value = []
  }
}

// 获取直接打印数据（dateStr 为 YYYY-MM-DD，避免时区导致请求错日）
async function fetchDirectPrintData(dateStr, groupIndex) {
  try {
    const group = destinationGroups.value[groupIndex]

    if (!group?.destinations || group.destinations.length === 0) {
      directPrintData.value = []
      directPrintFilters.value = {}
      return
    }

    const destinationCds = group.destinations.map((dest) => dest.value)

    const params = {
      date_from: dateStr,
      date_to: dateStr,
      destination_cds: destinationCds.join(','),
    }

    const response = await request.get('/api/shipping/overview', { params })

    // 处理响应数据
    let data = null
    if (Array.isArray(response)) {
      data = response
    } else if (response && Array.isArray(response.data)) {
      data = response.data
    }

    directPrintData.value = data || []
    directPrintFilters.value = {
      dateRange: [dateStr, dateStr],
      destinationCds: destinationCds,
      selectedGroup: groupIndex,
    }
    console.log('直接印刷データを取得しました:', directPrintData.value)
  } catch (error) {
    console.error('直接印刷データの取得に失敗しました:', error)
    ElMessage.error('印刷データの取得に失敗しました')
    directPrintData.value = []
    directPrintFilters.value = {}
  }
}

async function executePrint() {
  if (!printContent.value || !printData.value || printData.value.length === 0) {
    ElMessage.error('印刷内容の取得に失敗しました')
    await recordPrintFailure('印刷内容の取得に失敗しました')
    return
  }

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました')
    await recordPrintFailure('ポップアップがブロックされました')
    return
  }

  const printHtml = printContent.value.innerHTML
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((el) => el.outerHTML)
    .join('')

  printWindow.document.write(`
    <html>
      <head>
        <title>${formatDate(selectedDate.value)} ${stripReportPrefix(destinationGroups.value[selectedGroup.value]?.groupName)}</title>
        ${styles}
      </head>
      <body>
        <div class="print-container">
          ${printHtml}
        </div>
      </body>
    </html>
  `)

  printWindow.document.close()

  printWindow.onload = async () => {
    printWindow.focus()
    printWindow.print()
    printWindow.close()

    // 记录打印成功
    await recordPrintSuccess()

    // 更新打印状态
    updatePrintStatus()
  }

  printDialogVisible.value = false
}

// 直接打印函数，不显示预览对话框（dateStr 为 YYYY-MM-DD）
async function executeDirectPrint(dateStr, groupIndex) {
  if (!hiddenPrintContainer.value || !directPrintData.value || directPrintData.value.length === 0) {
    ElMessage.error('印刷内容の取得に失敗しました')
    await recordDirectPrintFailure('印刷内容の取得に失敗しました', dateStr, groupIndex)
    return
  }

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました')
    await recordDirectPrintFailure('ポップアップがブロックされました', dateStr, groupIndex)
    return
  }

  const printHtml = hiddenPrintContainer.value.innerHTML
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((el) => el.outerHTML)
    .join('')

  const groupName = stripReportPrefix(destinationGroups.value[groupIndex]?.groupName || '')

  printWindow.document.write(`
    <html>
      <head>
        <title>${dateStr} ${groupName}</title>
        ${styles}
      </head>
      <body>
        <div class="print-container">
          ${printHtml}
        </div>
      </body>
    </html>
  `)

  printWindow.document.close()

  printWindow.onload = async () => {
    printWindow.focus()
    printWindow.print()
    printWindow.close()

    // 记录打印成功
    await recordDirectPrintSuccess(dateStr, groupIndex)

    // 更新打印状态
    updatePrintStatus(dateStr, groupIndex)
  }
}

async function recordPrintSuccess() {
  try {
    // 使用标准化的日期格式：YYYY-MM-DD（带前导零，与isPrinted函数保持一致）
    const year = selectedDate.value.getFullYear()
    const month = selectedDate.value.getMonth() + 1
    const day = selectedDate.value.getDate()
    const dateForTitle = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`

    const reportTitle = `${dateForTitle} ${stripReportPrefix(destinationGroups.value[selectedGroup.value]?.groupName)}`

    console.log('記録打印履歴:', {
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '成功',
    })

    const response = await recordPrintHistory({
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '成功',
    })

    console.log('打印履歴の記録に成功しました:', response)
    ElMessage.success('打印履歴を記録しました')
  } catch (error) {
    console.error('打印履歴の記録に失敗しました:', error)
    ElMessage.error('打印履歴の記録に失敗しました')
  }
}

async function recordPrintFailure(errorMessage) {
  try {
    // 使用标准化的日期格式：YYYY-MM-DD（带前导零，与isPrinted函数保持一致）
    const year = selectedDate.value.getFullYear()
    const month = selectedDate.value.getMonth() + 1
    const day = selectedDate.value.getDate()
    const dateForTitle = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`

    const reportTitle = `${dateForTitle} ${stripReportPrefix(destinationGroups.value[selectedGroup.value]?.groupName)}`

    console.log('記録打印失敗履歴:', {
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '失败',
      error_message: errorMessage,
    })

    const response = await recordPrintHistory({
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '失败',
      error_message: errorMessage,
    })

    console.log('打印失敗履歴の記録に成功しました:', response)
  } catch (error) {
    console.error('打印失敗履歴の記録に失敗しました:', error)
  }
}

// 记录直接打印成功（dateStr 为 YYYY-MM-DD）
async function recordDirectPrintSuccess(dateStr, groupIndex) {
  try {
    const groupName = stripReportPrefix(destinationGroups.value[groupIndex]?.groupName || '')
    const reportTitle = `${dateStr} ${groupName}`

    const filters = {
      dateRange: [dateStr, dateStr],
      destinationCds:
        destinationGroups.value[groupIndex]?.destinations?.map((dest) => dest.value) || [],
      selectedGroup: groupIndex,
    }

    console.log('記録直接打印履歴:', {
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '成功',
    })

    const response = await recordPrintHistory({
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '成功',
    })

    console.log('直接打印履歴の記録に成功しました:', response)
    ElMessage.success('打印履歴を記録しました')
  } catch (error) {
    console.error('直接打印履歴の記録に失敗しました:', error)
    ElMessage.error('打印履歴の記録に失敗しました')
  }
}

// 记录直接打印失败（dateStr 为 YYYY-MM-DD）
async function recordDirectPrintFailure(errorMessage, dateStr, groupIndex) {
  try {
    const groupName = stripReportPrefix(destinationGroups.value[groupIndex]?.groupName || '')
    const reportTitle = `${dateStr} ${groupName}`

    const filters = {
      dateRange: [dateStr, dateStr],
      destinationCds:
        destinationGroups.value[groupIndex]?.destinations?.map((dest) => dest.value) || [],
      selectedGroup: groupIndex,
    }

    console.log('記録直接打印失敗履歴:', {
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '失败',
      error_message: errorMessage,
    })

    const response = await recordPrintHistory({
      report_type: reportTypeForHistory.value,
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '失败',
      error_message: errorMessage,
    })

    console.log('直接打印失敗履歴の記録に成功しました:', response)
  } catch (error) {
    console.warn('直接打印失敗履歴の記録に失敗しました（サーバー記録のみ）:', error)
  }
}

function updatePrintStatus(dateOrStr = null, groupIndex = null) {
  const targetGroupIndex = groupIndex !== null ? groupIndex : selectedGroup.value
  const dateStr =
    dateOrStr != null
      ? typeof dateOrStr === 'string'
        ? dateOrStr
        : formatDateString(dateOrStr)
      : selectedDate.value
        ? formatDateString(selectedDate.value)
        : null

  if (!dateStr) return

  if (!printHistory.value[dateStr]) {
    printHistory.value[dateStr] = {}
  }
  printHistory.value[dateStr][targetGroupIndex] = true
}

// 分组更新处理
async function handleGroupsUpdated(groups) {
  if (Array.isArray(groups)) {
    destinationGroups.value = groups
    // 分组更新后重新加载打印历史
    await loadPrintHistory()
  }
}

// 工具方法（按数字年月格式化，不依赖 Date 时区）
function formatMonthFromNumbers(year, month) {
  const d = new Date(Date.UTC(year, month, 1, 3, 0, 0))
  return d.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    timeZone: 'Asia/Tokyo',
  })
}

function formatMonth(date) {
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    timeZone: 'Asia/Tokyo',
  })
}

function formatDate(date) {
  return date
    .toLocaleDateString('ja-JP', {
      timeZone: 'Asia/Tokyo',
    })
    .replace(/\//g, '-')
}

function formatDateString(date) {
  // 确保使用日本时区格式化日期字符串
  const japanDate = new Date(date.getTime() + date.getTimezoneOffset() * 60000 + 9 * 3600000)
  return japanDate.toISOString().slice(0, 10)
}

function handleClose() {
  visible.value = false
}
</script>

<style scoped>
/* ===== 内联模式：各出荷帳票ページの絞り込み上部に埋め込み ===== */
.shipping-calendar-inline {
  margin-bottom: 12px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  overflow: hidden;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(67, 56, 202, 0.45);
}

.calendar-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.calendar-heading__icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #fff;
  border-radius: 9px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(49, 46, 129, 0.3),
    0 4px 10px -4px rgba(99, 102, 241, 0.6);
}

.calendar-heading__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.calendar-inline-title {
  font-size: 14px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.02em;
  color: #1e1b4b;
}

.calendar-inline-subtitle {
  font-size: 11px;
  line-height: 1.4;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.shipping-calendar-inline .calendar-container {
  padding: 0;
  background: #fff;
}

.shipping-calendar-inline .month-navigation {
  margin: 0;
  border: none;
  border-bottom: 1px solid #e0e7ff;
  border-radius: 0;
  background: linear-gradient(180deg, #fbfbff 0%, #f3f4ff 100%);
  box-shadow: none;
}

.shipping-calendar-inline .no-data-banner {
  margin: 8px 10px 0;
}

.shipping-calendar-inline .calendar-grid {
  margin: 8px 10px 10px;
}

/* ===== ダイアログモード ===== */
.shipping-calendar-dialog {
  border-radius: 8px;
}

.shipping-calendar-dialog :deep(.el-dialog) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.shipping-calendar-dialog :deep(.el-dialog__header) {
  background: #ffffff;
  color: #000000;
  padding: 12px 16px;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid #e5e7eb;
}

.shipping-calendar-dialog :deep(.el-dialog__title) {
  color: #000000;
  font-weight: 600;
  font-size: 16px;
}

.shipping-calendar-dialog .dialog-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shipping-calendar-dialog .dialog-title {
  color: #000000;
  font-weight: 600;
  font-size: 16px;
  line-height: 1.4;
}

.shipping-calendar-dialog .dialog-subtitle {
  color: #000000;
  font-weight: 400;
  font-size: 12px;
  line-height: 1.4;
}

.shipping-calendar-dialog :deep(.el-dialog__body) {
  padding: 12px;
}

/* ===== 共通：カレンダー本体 ===== */
.calendar-container {
  padding: 10px 12px;
  background: #f8fafc;
  font-family:
    'Noto Sans JP',
    'Hiragino Sans',
    'Yu Gothic UI',
    Meiryo,
    'Segoe UI',
    system-ui,
    sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* 見出し・月切替・グループ管理（左／中央／右） */
.month-navigation {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.month-navigation > :last-child {
  justify-self: end;
}

.month-switch {
  display: flex;
  align-items: center;
  gap: 12px;
}

.month-navigation .el-button-group .el-button {
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 700;
}

.prev-month-btn,
.next-month-btn {
  --k-rgb: 79 70 229;
  color: #475569;
  background: #fff;
  border-color: #e2e8f0;
}

.prev-month-btn:hover,
.next-month-btn:hover,
.prev-month-btn:focus-visible,
.next-month-btn:focus-visible {
  color: #4338ca;
  background: #eef2ff;
  border-color: #c7d2fe;
}

.current-month-btn {
  --k-rgb: 79 70 229;
  color: #fff;
  border-color: #4f46e5;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
}

.current-month-btn:hover,
.current-month-btn:focus-visible {
  color: #fff;
  border-color: #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #818cf8 0%, #8b5cf6 100%);
}

.current-month {
  min-width: 112px;
  text-align: center;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #1e1b4b;
  font-variant-numeric: tabular-nums;
}

.group-manage-btn.el-button {
  --k-rgb: 79 70 229;
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 700;
  border-color: #4f46e5;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
}

/* グリッド */
.calendar-grid {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  background: linear-gradient(180deg, #f8faff 0%, #eef2ff 100%);
  border-bottom: 1px solid #e0e7ff;
}

.weekday {
  padding: 6px 4px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #475569;
}

.weekday:first-child {
  color: #dc2626;
}

.weekday:last-child {
  color: #2563eb;
}

.date-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  margin-bottom: -1px;
}

.date-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  min-height: 58px;
  padding: 4px 5px 5px;
  background: #fff;
  border-right: 1px solid #eef2f7;
  border-bottom: 1px solid #eef2f7;
  transition: background-color 0.15s ease;
}

.date-cell:nth-child(7n) {
  border-right: none;
}

.date-cell.empty {
  background: #f8fafc;
}

/* 列位置で日曜（1列目）・土曜（7列目）を色分け */
.date-cell.weekend:nth-child(7n + 1):not(.today) {
  background: #fff8f8;
}

.date-cell.weekend:nth-child(7n):not(.today) {
  background: #f7faff;
}

.date-cell.has-data:not(.today):hover {
  background: #fafaff;
}

.date-cell.today {
  background: #eef2ff;
  box-shadow: inset 0 0 0 2px #6366f1;
}

.date-number {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 700;
  line-height: 20px;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
}

.date-cell:nth-child(7n + 1) .date-number {
  color: #dc2626;
}

.date-cell:nth-child(7n) .date-number {
  color: #2563eb;
}

.date-cell:not(.has-data):not(.today) .date-number {
  opacity: 0.5;
}

.date-cell.today .date-number {
  color: #4338ca;
  font-weight: 800;
}

.date-cell.today .date-number::after {
  content: '今日';
  padding: 0 6px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 0.04em;
  color: #fff;
  border-radius: 999px;
  background: #6366f1;
}

/* 便グループの印刷ボタン（セル幅に応じて横並び） */
.print-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
  gap: 3px;
}

.group-button-wrapper {
  --g: #2563eb;
  --g-bg: #eff6ff;
  --g-bd: #bfdbfe;
  --g-tx: #1e40af;
  position: relative;
  min-width: 0;
}

.group-button-wrapper:nth-child(2) {
  --g: #d97706;
  --g-bg: #fffbeb;
  --g-bd: #fde68a;
  --g-tx: #92400e;
}

.group-button-wrapper:nth-child(3) {
  --g: #7c3aed;
  --g-bg: #f5f3ff;
  --g-bd: #ddd6fe;
  --g-tx: #5b21b6;
}

.group-button-wrapper:nth-child(4) {
  --g: #0891b2;
  --g-bg: #ecfeff;
  --g-bd: #a5f3fc;
  --g-tx: #155e75;
}

.group-button-wrapper:nth-child(5) {
  --g: #e11d48;
  --g-bg: #fff1f2;
  --g-bd: #fecdd3;
  --g-tx: #9f1239;
}

.group-button-wrapper:nth-child(n + 6) {
  --g: #475569;
  --g-bg: #f8fafc;
  --g-bd: #cbd5e1;
  --g-tx: #334155;
}

.group-button.el-button {
  width: 100%;
  height: 24px;
  min-height: 24px;
  margin: 0;
  padding: 0 5px 0 8px;
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
  border-radius: 6px;
  border: 1px dashed #d8dee8;
  background: #f8fafc;
  box-shadow: none;
  transition:
    transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.18s ease,
    background-color 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease;
}

.group-button.el-button > :deep(span) {
  width: 100%;
  min-width: 0;
}

.group-button.el-button:hover {
  color: #64748b;
  background: #fff;
  border-color: #cbd5e1;
}

.group-button-wrapper.has-data .group-button.el-button {
  color: var(--g-tx);
  border: 1px solid var(--g-bd);
  background: var(--g-bg);
  box-shadow:
    inset 3px 0 0 var(--g),
    inset 0 1px 0 #ffffff,
    0 1px 2px rgba(15, 23, 42, 0.05);
}

.group-button-wrapper.has-data .group-button.el-button:hover {
  color: var(--g-tx);
  background: #fff;
  border-color: var(--g);
  transform: translateY(-1px);
  box-shadow:
    inset 3px 0 0 var(--g),
    0 4px 10px -4px color-mix(in srgb, var(--g) 60%, transparent);
}

.group-button-wrapper.is-printed .group-button.el-button {
  color: #047857;
  border: 1px solid #a7f3d0;
  background: #ecfdf5;
  box-shadow:
    inset 3px 0 0 #10b981,
    inset 0 1px 0 #ffffff;
}

.group-button-wrapper.is-printed .group-button.el-button:hover {
  color: #065f46;
  background: #d1fae5;
  border-color: #34d399;
  transform: translateY(-1px);
  box-shadow:
    inset 3px 0 0 #10b981,
    0 4px 10px -4px rgba(16, 185, 129, 0.55);
}

.group-button.el-button:active {
  transform: translateY(1px);
}

.group-button.el-button:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--g) 50%, transparent);
  outline-offset: 1px;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  min-width: 0;
}

/* 印刷済：便名と「済」を上下2段 */
.group-button-wrapper.is-printed .group-button.el-button {
  height: auto;
  padding-top: 3px;
  padding-bottom: 3px;
}

.group-button-wrapper.is-printed .button-content {
  flex-direction: column;
  gap: 2px;
}

.group-button-wrapper.is-printed .button-text {
  max-width: 100%;
  line-height: 1.2;
}

.button-text {
  min-width: 0;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  color: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.print-badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 1px;
  height: 15px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  border-radius: 4px;
  background: #10b981;
}

.print-icon {
  font-size: 10px;
}

.print-text {
  font-size: 10px;
  line-height: 1;
}

/* 無データ月の案内（カレンダーは表示したまま） */
.no-data-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 12px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
}

.no-data-banner .el-icon {
  font-size: 15px;
}

/* ===== 印刷プレビュー ===== */
.print-preview-dialog {
  border-radius: 8px;
}

.print-preview-dialog :deep(.el-dialog) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.print-preview-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 8px 8px 0 0;
}

.print-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.print-dialog-title {
  color: white;
  font-weight: 600;
  font-size: 15px;
}

.print-dialog-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  font-size: 13px;
  margin-left: 8px;
  padding: 6px 12px;
}

.print-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 12px;
  background: #ffffff;
}

.no-data-message {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  font-size: 16px;
}

/* 无数据提示样式（保留供打印等场景） */
.no-data-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 24px 16px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.no-data-content {
  text-align: center;
  max-width: 400px;
}

.no-data-icon {
  margin-bottom: 16px;
}

.no-data-icon .el-icon {
  font-size: 48px;
  color: #d1d5db;
}

.no-data-title {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.no-data-description {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.no-data-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.no-data-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  font-size: 13px;
  padding: 8px 16px;
}

.no-data-actions .el-button--primary {
  background: #2563eb;
  border: none;
  color: white;
}

.no-data-actions .el-button--primary:hover {
  background: #1d4ed8;
}

/* ========== 响应式设计 ========== */
@media (max-width: 1280px) {
  .print-buttons {
    grid-template-columns: repeat(auto-fill, minmax(56px, 1fr));
  }

  .group-button.el-button {
    padding: 0 4px 0 7px;
  }

  .button-text {
    font-size: 11px;
  }
}

@media (max-width: 1024px) {
  .calendar-inline-subtitle {
    display: none;
  }

  .date-cell {
    min-height: 54px;
    padding: 3px 4px 4px;
  }
}

@media (max-width: 768px) {
  .shipping-calendar-inline {
    margin-bottom: 10px;
    border-radius: 10px;
  }

  .month-navigation {
    grid-template-columns: 1fr;
    justify-items: center;
    gap: 8px;
    padding: 8px 10px;
  }

  .month-navigation > :last-child {
    justify-self: center;
  }

  .current-month {
    font-size: 16px;
  }

  .print-buttons {
    grid-template-columns: 1fr;
  }

  .weekday {
    font-size: 11px;
    letter-spacing: 0.04em;
  }

  .no-data-container {
    min-height: 250px;
    padding: 16px 12px;
  }

  .no-data-actions {
    flex-direction: column;
    align-items: center;
  }

  .no-data-actions .el-button {
    width: 100%;
    max-width: 180px;
    margin-bottom: 6px;
  }
}

@media (max-width: 480px) {
  .shipping-calendar-inline {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .shipping-calendar-inline .calendar-container {
    min-width: 360px;
  }

  .month-switch {
    flex-direction: column;
    gap: 6px;
  }

  .date-number {
    font-size: 12px;
  }

  .button-text {
    font-size: 10px;
  }
}

/* 滚动条美化 */
.print-content::-webkit-scrollbar {
  width: 8px;
}

.print-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.print-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  border-radius: 4px;
}

.print-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
}
</style>
