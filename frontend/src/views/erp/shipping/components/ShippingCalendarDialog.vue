<template>
  <!-- 内联模式：直接渲染在页面中（筛选区上方） -->
  <div v-if="inline" class="shipping-calendar-inline">
    <div class="calendar-inline-header">
      <span class="calendar-inline-title">営業報告カレンダー</span>
      <span class="calendar-inline-subtitle">（発行説明：当日--終了便・社内便 翌日--鈴鹿便）</span>
    </div>
    <div class="calendar-container">
      <!-- 月份导航 -->
      <div class="month-navigation">
        <el-button-group>
          <el-button @click="previousMonth" :icon="ArrowLeft" class="prev-month-btn">前月</el-button>
          <el-button @click="goToCurrentMonth" class="current-month-btn">今月</el-button>
          <el-button @click="nextMonth" :icon="ArrowRight" class="next-month-btn">来月</el-button>
        </el-button-group>
        <div class="current-month">{{ formatMonthFromNumbers(calendarYear, calendarMonth) }}</div>
        <el-button type="primary" :icon="Setting" @click="showGroupManager = true">グループ管理</el-button>
      </div>
      <div v-if="!hasAnyShippingData" class="no-data-banner">
        <el-icon><Calendar /></el-icon>
        <span>{{ formatMonthFromNumbers(calendarYear, calendarMonth) }} は出荷データがありません</span>
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
            :class="{ today: isToday(date), weekend: isWeekend(date), 'has-data': hasShippingData(date) }"
          >
            <div class="date-number">{{ date }}</div>
            <div class="print-buttons" v-if="hasShippingData(date)">
              <div
                v-for="(group, groupIndex) in destinationGroups"
                :key="group.id || groupIndex"
                class="group-button-wrapper"
                :class="{ 'has-data': hasGroupData(date, groupIndex), 'is-printed': isPrinted(date, groupIndex) }"
              >
                <el-button
                  :type="getButtonType(date, groupIndex)"
                  size="small"
                  @click="handleGroupPrint(date, groupIndex)"
                  class="group-button"
                  :class="{ 'is-printed': isPrinted(date, groupIndex), [`group-${groupIndex}`]: true }"
                >
                  <div class="button-content">
                    <span class="button-text">{{ group.groupName }}</span>
                    <div v-if="isPrinted(date, groupIndex)" class="print-badge">
                      <el-icon class="print-icon"><Check /></el-icon>
                      <span class="print-text">発行済</span>
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
        <span class="dialog-title">営業報告カレンダー</span>
        <span class="dialog-subtitle">（発行説明：当日--終了便・社内便 翌日--鈴鹿便）</span>
      </div>
    </template>
    <div class="calendar-container">
      <!-- 月份导航 -->
      <div class="month-navigation">
        <el-button-group>
          <el-button @click="previousMonth" :icon="ArrowLeft" class="prev-month-btn"
            >前月</el-button
          >
          <el-button @click="goToCurrentMonth" class="current-month-btn">今月</el-button>
          <el-button @click="nextMonth" :icon="ArrowRight" class="next-month-btn">来月</el-button>
        </el-button-group>
        <div class="current-month">
          {{ formatMonthFromNumbers(calendarYear, calendarMonth) }}
        </div>
        <el-button type="primary" :icon="Setting" @click="showGroupManager = true">
          グループ管理
        </el-button>
      </div>

      <!-- 无数据时的提示条（不隐藏日历，保证每月都能选择/查看） -->
      <div v-if="!hasAnyShippingData" class="no-data-banner">
        <el-icon><Calendar /></el-icon>
        <span>{{ formatMonthFromNumbers(calendarYear, calendarMonth) }} は出荷データがありません</span>
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
                  class="group-button"
                  :class="{
                    'is-printed': isPrinted(date, groupIndex),
                    [`group-${groupIndex}`]: true,
                  }"
                >
                  <div class="button-content">
                    <span class="button-text">{{ group.groupName }}</span>
                    <div v-if="isPrinted(date, groupIndex)" class="print-badge">
                      <el-icon class="print-icon">
                        <Check />
                      </el-icon>
                      <span class="print-text">発行済</span>
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
    page-key="destination_groups_calendar"
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
          {{ destinationGroups[selectedGroup]?.groupName }}
        </span>
        <div class="print-dialog-actions">
          <el-button @click="printDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" @click="executePrint">印刷実行</el-button>
        </div>
      </div>
    </template>
    <div ref="printContent" class="print-content">
        <ShippingReport
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
    <ShippingReport
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
import DestinationGroupManager from './DestinationGroupManager.vue'
import { recordPrintHistory } from '@/api/shipping/printHistory'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  /** 为 true 时在页面内联显示（不弹窗），用于报告页筛选区上方 */
  inline: {
    type: Boolean,
    default: false,
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
  const month = (parseInt(parts.find((p) => p.type === 'month')?.value ?? date.getMonth() + 1, 10) - 1)
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
          const dateParts = dateStr.split(/[-\/]/)
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

watch(
  [calendarYear, calendarMonth],
  async () => {
    console.log('月が変更されました:', formatMonthFromNumbers(calendarYear.value, calendarMonth.value))
    await fetchMonthData()
    // 确保分组配置存在后再加载打印历史
    if (destinationGroups.value && destinationGroups.value.length > 0) {
      await loadPrintHistory()
    }
  },
)

// 加载分组配置
async function loadDestinationGroups() {
  try {
    console.log('🔄 分組配置を読み込み中...')
    const response = await request.get(
      '/api/shipping/destination-groups/destination_groups_calendar',
    )
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
      // 格式2: { data: [...] }
      data = response.data
      console.log('✅ dataプロパティでデータを取得:', data.length, '件')
    } else if (response && response.success === true && Array.isArray(response.data)) {
      // 格式3: { success: true, data: [...] }
      data = response.data
      console.log('✅ success形式でデータを取得:', data.length, '件')
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
      report_type: 'shipping_calendar',
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
          // 解析 report_title 格式: '出荷報告書カレンダー - 2025-1-8 鈴鹿便'
          const titleMatch = record.report_title.match(
            /出荷報告書カレンダー\s*-\s*(\d{4}[-\/]\d{1,2}[-\/]\d{1,2})\s+(.+)/,
          )

          if (titleMatch) {
            const dateStr = titleMatch[1].trim() // 例如: "2025-1-8"
            const groupName = titleMatch[2].trim() // 例如: "鈴鹿便"

            console.log(`📅 解析した日付: "${dateStr}", グループ名: "${groupName}"`)

            // 将日期格式标准化为 YYYY-MM-DD
            const dateParts = dateStr.split(/[-\/]/)
            if (dateParts.length === 3) {
              const year = dateParts[0]
              const month = dateParts[1].padStart(2, '0')
              const day = dateParts[2].padStart(2, '0')
              const standardDate = `${year}-${month}-${day}`

              console.log(`📅 日期标准化: "${dateStr}" -> "${standardDate}"`)

              // 先去掉可能存在的文件扩展名，例如 ".pdf"
              const cleanGroupName = groupName.replace(/\.(pdf|PDF)$/i, '').trim()

              // 根据组名映射到组索引
              let groupIndex = destinationGroups.value.findIndex(
                (g) => g.groupName === cleanGroupName,
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
    new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tokyo', day: '2-digit' }).format(getJapanDate()),
    10,
  )
  return todayJst.year === calendarYear.value && todayJst.month === calendarMonth.value && todayDay === date
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
        <title>出荷報告書印刷 - ${formatDate(selectedDate.value)} ${destinationGroups.value[selectedGroup.value]?.groupName}</title>
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

  const groupName = destinationGroups.value[groupIndex]?.groupName || ''

  printWindow.document.write(`
    <html>
      <head>
        <title>出荷報告書印刷 - ${dateStr} ${groupName}</title>
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

    const reportTitle = `出荷報告書カレンダー - ${dateForTitle} ${destinationGroups.value[selectedGroup.value]?.groupName}`

    console.log('記録打印履歴:', {
      report_type: 'shipping_calendar',
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '成功',
    })

    const response = await recordPrintHistory({
      report_type: 'shipping_calendar',
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

    const reportTitle = `出荷報告書カレンダー - ${dateForTitle} ${destinationGroups.value[selectedGroup.value]?.groupName}`

    console.log('記録打印失敗履歴:', {
      report_type: 'shipping_calendar',
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '失敗',
      error_message: errorMessage,
    })

    const response = await recordPrintHistory({
      report_type: 'shipping_calendar',
      report_title: reportTitle,
      filters: printFilters.value,
      record_count: printData.value?.length || 0,
      status: '失敗',
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
    const groupName = destinationGroups.value[groupIndex]?.groupName || ''
    const reportTitle = `出荷報告書カレンダー - ${dateStr} ${groupName}`

    const filters = {
      dateRange: [dateStr, dateStr],
      destinationCds:
        destinationGroups.value[groupIndex]?.destinations?.map((dest) => dest.value) || [],
      selectedGroup: groupIndex,
    }

    console.log('記録直接打印履歴:', {
      report_type: 'shipping_calendar',
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '成功',
    })

    const response = await recordPrintHistory({
      report_type: 'shipping_calendar',
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
    const groupName = destinationGroups.value[groupIndex]?.groupName || ''
    const reportTitle = `出荷報告書カレンダー - ${dateStr} ${groupName}`

    const filters = {
      dateRange: [dateStr, dateStr],
      destinationCds:
        destinationGroups.value[groupIndex]?.destinations?.map((dest) => dest.value) || [],
      selectedGroup: groupIndex,
    }

    console.log('記録直接打印失敗履歴:', {
      report_type: 'shipping_calendar',
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '失敗',
      error_message: errorMessage,
    })

    const response = await recordPrintHistory({
      report_type: 'shipping_calendar',
      report_title: reportTitle,
      filters: filters,
      record_count: directPrintData.value?.length || 0,
      status: '失敗',
      error_message: errorMessage,
    })

    console.log('直接打印失敗履歴の記録に成功しました:', response)
  } catch (error) {
    console.error('直接打印失敗履歴の記録に失敗しました:', error)
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
/* 内联模式：嵌入在报告页筛选区上方 */
.shipping-calendar-inline {
  margin-bottom: 16px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.calendar-inline-header {
  padding: 12px 18px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-inline-title {
  font-weight: 700;
  font-size: 17px;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.calendar-inline-subtitle {
  font-size: 13px;
  color: #475569;
  line-height: 1.4;
}

.shipping-calendar-inline .calendar-container {
  padding: 12px 16px;
}

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

.calendar-container {
  padding: 10px 12px;
  background: #f1f5f9;
  min-height: 380px;
  font-family: 'Helvetica Neue', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

.month-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px 14px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.month-navigation .el-button-group .el-button {
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.prev-month-btn {
  background-color: #f3f4f6;
  color: #6b7280;
  border-color: #e5e7eb;
}

.prev-month-btn:hover {
  background-color: #e5e7eb;
  border-color: #d1d5db;
  color: #374151;
}

.current-month-btn {
  background-color: #2563eb;
  color: white;
  border-color: #2563eb;
  font-weight: 600;
}

.current-month-btn:hover {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.next-month-btn {
  background-color: #f3f4f6;
  color: #6b7280;
  border-color: #e5e7eb;
}

.next-month-btn:hover {
  background-color: #e5e7eb;
  border-color: #d1d5db;
  color: #374151;
}

.current-month {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.month-navigation .el-button--primary {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
  font-weight: 500;
}

.calendar-grid {
  background: #ffffff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 50%, #3b82f6 100%);
  border-bottom: none;
}

.weekday {
  padding: 10px 6px;
  text-align: center;
  font-weight: 700;
  color: #fff;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.15);
}

.date-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: #e5e7eb;
  padding: 1px;
}

.date-cell {
  background: #ffffff;
  min-height: 96px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  transition: all 0.2s ease;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.date-cell.empty {
  background: rgba(248, 250, 252, 0.5);
  opacity: 0.4;
}

.date-cell.today {
  background: #fef3c7;
  border: 2px solid #f59e0b;
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2);
  position: relative;
  overflow: hidden;
}

.date-cell.today::before {
  content: '今日';
  position: absolute;
  top: 3px;
  right: 3px;
  background: #d97706;
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
  z-index: 2;
  letter-spacing: 0.02em;
}

.date-cell.weekend:not(.today) {
  background: #fef2f2;
  border-left: 2px solid #ef4444;
}

.date-cell.has-data:not(.today) {
  background: #f0fdf4;
  border-left: 2px solid #10b981;
}

.date-cell.has-data.weekend:not(.today) {
  background: #fff7ed;
  border-left: 2px solid #f97316;
}

.date-cell:hover:not(.empty) {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.date-number {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  text-align: center;
  margin-bottom: 6px;
  transition: all 0.2s ease;
  position: relative;
  z-index: 1;
  line-height: 1.2;
}

.date-cell.today .date-number {
  color: #b45309;
  font-size: 16px;
  font-weight: 800;
}

.date-cell.weekend .date-number {
  color: #b91c1c;
  font-weight: 700;
}

.date-cell.has-data .date-number {
  color: #047857;
  font-weight: 700;
}

.date-cell.has-data.weekend .date-number {
  color: #c2410c;
  font-weight: 700;
}

.print-buttons {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 4px;
}

.group-button-wrapper {
  position: relative;
  border-radius: 4px;
  transition: all 0.2s ease;
  overflow: hidden;
}

.group-button-wrapper.is-printed {
  background: #d1fae5;
  border: 1px solid #10b981;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.2);
}

.group-button-wrapper.has-data:not(.is-printed) {
  border: 1px solid transparent;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.group-button {
  width: 100%;
  padding: 6px 8px;
  font-size: 12px;
  border-radius: 6px;
  position: relative;
  min-height: 32px;
  font-weight: 600;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

.group-button:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 100%;
}

.button-text {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #1e293b;
  line-height: 1.3;
}

.group-button.is-printed .button-text {
  color: #047857;
  font-weight: 600;
}

.print-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  background: #059669;
  color: #fff;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 2px;
}

.print-icon {
  font-size: 10px;
}

.print-text {
  line-height: 1.2;
  font-size: 9px;
}

/* 现代化按钮颜色区分系统 */
/* 第一组 - 蓝色主题 */
.group-button-wrapper.has-data:not(.is-printed):nth-child(1) {
  background: #dbeafe;
  border-color: #2563eb;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.1);
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(1) .button-text {
  color: #1e40af;
  font-weight: 600;
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(1)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #2563eb;
  border-radius: 4px 4px 0 0;
}

/* 第二组 - 橙色主题 */
.group-button-wrapper.has-data:not(.is-printed):nth-child(2) {
  background: #fed7aa;
  border-color: #f59e0b;
  box-shadow: 0 1px 2px rgba(245, 158, 11, 0.1);
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(2) .button-text {
  color: #92400e;
  font-weight: 600;
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(2)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #f59e0b;
  border-radius: 4px 4px 0 0;
}

/* 第三组 - 紫色主题 */
.group-button-wrapper.has-data:not(.is-printed):nth-child(3) {
  background: #e9d5ff;
  border-color: #9333ea;
  box-shadow: 0 1px 2px rgba(147, 51, 234, 0.1);
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(3) .button-text {
  color: #6b21a8;
  font-weight: 600;
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(3)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #9333ea;
  border-radius: 4px 4px 0 0;
}

/* 第四组 - 绿色主题 */
.group-button-wrapper.has-data:not(.is-printed):nth-child(4) {
  background: #bbf7d0;
  border-color: #10b981;
  box-shadow: 0 1px 2px rgba(16, 185, 129, 0.1);
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(4) .button-text {
  color: #047857;
  font-weight: 600;
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(4)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #10b981;
  border-radius: 4px 4px 0 0;
}

/* 第五组 - 红色主题 */
.group-button-wrapper.has-data:not(.is-printed):nth-child(5) {
  background: #fecaca;
  border-color: #ef4444;
  box-shadow: 0 1px 2px rgba(239, 68, 68, 0.1);
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(5) .button-text {
  color: #991b1b;
  font-weight: 600;
}

.group-button-wrapper.has-data:not(.is-printed):nth-child(5)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #ef4444;
  border-radius: 4px 4px 0 0;
}

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

/* 无数据时的提示条（日历仍显示，可正常切换月份） */
.no-data-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: #fffbeb;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  color: #92400e;
  font-size: 14px;
  font-weight: 500;
}

.no-data-banner .el-icon {
  font-size: 18px;
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
  transition: all 0.2s ease;
}

.no-data-actions .el-button:hover {
  transform: translateY(-1px);
}

.no-data-actions .el-button--primary {
  background: #2563eb;
  border: none;
  color: white;
}

.no-data-actions .el-button--primary:hover {
  background: #1d4ed8;
}

/* 浮动动画 */
@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-10px);
  }
}

/* ========== 响应式设计 ========== */

/* 平板 / 小桌面 */
@media (max-width: 1024px) {
  .shipping-calendar-inline .calendar-container {
    padding: 10px 12px;
  }

  .calendar-container {
    min-height: 360px;
  }

  .date-cell {
    min-height: 88px;
    padding: 6px;
  }

  .date-number {
    font-size: 14px;
  }

  .button-text {
    font-size: 10px;
  }

  .group-button {
    min-height: 28px;
    padding: 5px 6px;
    font-size: 11px;
  }

  .weekday {
    font-size: 13px;
    padding: 8px 4px;
  }
}

/* 手机横屏 / 小平板 */
@media (max-width: 768px) {
  .shipping-calendar-inline {
    margin-bottom: 12px;
    border-radius: 8px;
  }

  .calendar-inline-header {
    padding: 10px 14px;
  }

  .calendar-inline-title {
    font-size: 16px;
  }

  .calendar-inline-subtitle {
    font-size: 12px;
  }

  .shipping-calendar-inline .calendar-container {
    padding: 8px 10px;
  }

  .calendar-container {
    padding: 8px;
    min-height: 320px;
  }

  .month-navigation {
    flex-direction: column;
    gap: 8px;
    text-align: center;
    padding: 8px 12px;
  }

  .month-navigation .el-button-group {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
  }

  .month-navigation .el-button-group .el-button {
    padding: 6px 12px;
    font-size: 13px;
  }

  .current-month {
    font-size: 15px;
    order: -1;
    width: 100%;
  }

  .date-cell {
    min-height: 82px;
    padding: 6px;
  }

  .date-number {
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .group-button {
    min-height: 30px;
    padding: 5px 6px;
    font-size: 11px;
  }

  .button-text {
    font-size: 11px;
    font-weight: 600;
  }

  .print-badge {
    font-size: 8px;
    padding: 2px 4px;
  }

  .print-text {
    font-size: 8px;
  }

  .weekday {
    font-size: 12px;
    padding: 8px 2px;
  }

  .no-data-banner {
    font-size: 13px;
    padding: 8px 12px;
  }

  .no-data-container {
    min-height: 250px;
    padding: 16px 12px;
  }

  .no-data-icon .el-icon {
    font-size: 40px;
  }

  .no-data-title {
    font-size: 16px;
  }

  .no-data-description {
    font-size: 12px;
    margin-bottom: 16px;
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

/* 手机竖屏 */
@media (max-width: 480px) {
  .shipping-calendar-inline {
    margin-bottom: 10px;
    border-radius: 6px;
  }

  .calendar-inline-header {
    padding: 8px 12px;
  }

  .calendar-inline-title {
    font-size: 15px;
  }

  .calendar-inline-subtitle {
    font-size: 11px;
  }

  .calendar-container {
    padding: 6px 8px;
    min-height: 280px;
  }

  .calendar-grid {
    border-radius: 4px;
  }

  .date-grid {
    gap: 1px;
    padding: 1px;
  }

  .date-cell {
    min-height: 72px;
    padding: 4px;
  }

  .date-cell.today::before {
    font-size: 9px;
    padding: 1px 4px;
  }

  .date-number {
    font-size: 13px;
  }

  .group-button {
    min-height: 28px;
    padding: 4px 5px;
    font-size: 10px;
  }

  .button-text {
    font-size: 10px;
  }

  .print-buttons {
    gap: 3px;
  }

  .weekday {
    font-size: 11px;
    padding: 6px 2px;
  }

  .month-navigation .el-button-group .el-button {
    padding: 6px 10px;
    font-size: 12px;
  }

  .current-month {
    font-size: 14px;
  }

  /* 超小屏：日历网格可横向滚动，避免格子过窄 */
  .calendar-grid {
    min-width: 320px;
  }

  .shipping-calendar-inline {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .shipping-calendar-inline .calendar-container {
    min-width: 320px;
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

/* 动画效果 */
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

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.calendar-grid {
  animation: fadeInUp 0.6s ease-out;
}

.date-cell {
  animation: fadeInUp 0.3s ease-out;
}

.group-button-wrapper {
  animation: slideInLeft 0.4s ease-out;
}

.group-button-wrapper:nth-child(1) {
  animation-delay: 0.1s;
}

.group-button-wrapper:nth-child(2) {
  animation-delay: 0.2s;
}

.group-button-wrapper:nth-child(3) {
  animation-delay: 0.3s;
}

/* 打印徽章动画 */
@keyframes printBadgeGlow {
  0% {
    box-shadow: 0 2px 4px rgba(16, 185, 129, 0.4);
  }

  100% {
    box-shadow:
      0 4px 12px rgba(16, 185, 129, 0.6),
      0 0 20px rgba(16, 185, 129, 0.3);
  }
}

@keyframes checkmark {
  0% {
    opacity: 0;
    transform: scale(0.3) rotate(-45deg);
  }

  50% {
    opacity: 1;
    transform: scale(1.2) rotate(0deg);
  }

  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

@keyframes buttonPrintSuccess {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }

  100% {
    transform: scale(1);
  }
}

.group-button-wrapper.is-printed {
  animation: buttonPrintSuccess 0.8s ease-out;
}

/* 悬停效果 */
.group-button-wrapper:hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.group-button-wrapper.is-printed:hover {
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
}

.group-button-wrapper.has-data:not(.is-printed):hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 脉动效果 */
@keyframes pulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.02);
  }

  100% {
    transform: scale(1);
  }
}

.group-button-wrapper.is-printed .print-badge {
  animation: pulse 2s infinite ease-in-out;
}
</style>
