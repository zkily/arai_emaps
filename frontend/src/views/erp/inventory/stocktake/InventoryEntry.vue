<template>
  <div class="inventory-entry-page">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="orb orb-4"></div>
      <div class="floating-particles">
        <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
      </div>
    </div>
    <div class="page-header">
      <div class="header-glow"></div>
      <div class="header-content">
        <div class="header-icon">
          <div class="icon-ring"></div>
          <el-icon><DocumentAdd /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">棚卸登録</h1>
          <p class="page-description">材料、部品、ステーなどの棚卸データを効率的に入力</p>
          <div class="title-underline"></div>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          @click="handleNewInput"
          v-if="!showForm"
          class="action-btn primary-btn"
        >
          <div class="btn-glow"></div>
          <el-icon><Plus /></el-icon>
          新規入力
        </el-button>
        <el-button
          type="success"
          @click="handleBatchInput"
          v-if="!showForm"
          class="action-btn success-btn"
        >
          <div class="btn-glow"></div>
          <el-icon><DocumentAdd /></el-icon>
          一括入力
        </el-button>
        <el-button @click="goBack" v-if="showForm" class="action-btn back-btn">
          <div class="btn-glow"></div>
          <el-icon><ArrowLeft /></el-icon>
          一覧に戻る
        </el-button>
      </div>
    </div>

    <!-- 录入表单 -->
    <div v-if="showForm" class="form-container">
      <InventoryEntryForm
        :submitting="submitting"
        :initial-data="lastFormData"
        @submit="handleFormSubmit"
        @cancel="handleFormCancel"
      />
    </div>

    <!-- 录入历史 -->
    <div v-else class="history-container">
      <el-card class="history-card" shadow="hover">
        <template #header>
          <div class="history-header">
            <h3>手入力記録</h3>
            <div class="header-info">
              <el-tag type="info" effect="plain" size="small">手入力データのみ表示</el-tag>
              <div class="filter-controls">
                <el-date-picker
                  v-model="selectedMonth"
                  type="month"
                  placeholder="月を選択"
                  format="YYYY-MM"
                  value-format="YYYY-MM"
                  @change="handleMonthChange"
                  class="month-filter"
                />
                <el-button link @click="clearFilter">
                  <el-icon><Close /></el-icon>
                  クリア
                </el-button>
              </div>
              <el-button link @click="refreshHistory">
                <el-icon><Refresh /></el-icon>
                更新
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="recentEntries"
          border
          stripe
          v-loading="historyLoading"
          class="history-table"
          @sort-change="handleSortChange"
          :default-sort="{ prop: 'updated_at', order: 'descending' }"
          table-layout="fixed"
        >
          <el-table-column
            label="項目"
            prop="item"
            width="110"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              <el-tag :type="getItemTypeColor(scope.row.item)" effect="light">
                {{ scope.row.item }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            label="製品CD"
            prop="product_cd"
            width="160"
            align="center"
            header-align="center"
            sortable
          />
          <el-table-column
            label="製品名"
            prop="product_name"
            min-width="160"
            align="left"
            header-align="center"
            sortable
          />
          <el-table-column
            label="工程名"
            prop="process_name"
            width="140"
            align="center"
            header-align="center"
            sortable
          />
          <el-table-column
            label="数量"
            prop="quantity"
            width="130"
            align="center"
            header-align="center"
            sortable
          >
            <template #default="scope">
              <span :class="getQuantityClass(scope.row.quantity)">{{ scope.row.quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="作業者"
            prop="worker_name"
            width="120"
            align="center"
            header-align="center"
          >
            <template #default="scope">
              <span>{{ scope.row.worker_name || scope.row.remarks || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="入力日時"
            prop="updated_at"
            width="180"
            align="center"
            header-align="center"
            sortable
          >
            <template #default="scope">
              {{ formatDateTime(scope.row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="120"
            align="center"
            header-align="center"
            fixed="right"
          >
            <template #default="scope">
              <el-button
                type="danger"
                size="small"
                link
                @click="handleDelete(scope.row)"
                :loading="scope.row.deleting"
              >
                <el-icon><Delete /></el-icon>
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="empty-state" v-if="recentEntries.length === 0 && !historyLoading">
          <el-empty description="手入力記録がありません">
            <el-button type="primary" @click="handleNewInput">
              <el-icon><Plus /></el-icon>
              入力開始
            </el-button>
          </el-empty>
        </div>
      </el-card>
    </div>

    <!-- 成功提示 -->
    <el-dialog
      v-model="successDialogVisible"
      title="入力完了"
      width="480px"
      center
      :show-close="false"
      class="success-dialog"
    >
      <div class="success-content">
        <div class="success-animation">
          <div class="success-circle">
            <div class="success-checkmark">
              <div class="checkmark-stem"></div>
              <div class="checkmark-kick"></div>
            </div>
          </div>
        </div>
        <h3 class="success-title">入力完了</h3>
        <p class="success-message">棚卸情報の入力が完了しました！</p>
        <div class="success-details">
          <div class="detail-item">
            <span class="detail-label">製品CD:</span>
            <span class="detail-value">{{ lastEntry?.product_cd }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">製品名:</span>
            <span class="detail-value">{{ lastEntry?.product_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">数量:</span>
            <span class="detail-value quantity-highlight">{{ lastEntry?.quantity }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleContinueInput" class="continue-btn">
            <el-icon><Plus /></el-icon>
            続けて入力
          </el-button>
          <el-button type="primary" @click="handleSuccessConfirm" class="confirm-btn">
            <el-icon><CircleCheckFilled /></el-icon>
            完了
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量录入弹窗 -->
    <BatchInventoryEntryDialog v-model:visible="batchDialogVisible" @success="handleBatchSuccess" />

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="削除確認"
      width="480px"
      center
      :show-close="false"
      class="delete-dialog"
    >
      <div class="delete-content">
        <div class="delete-animation">
          <div class="warning-circle">
            <div class="warning-icon">
              <div class="warning-line"></div>
              <div class="warning-dot"></div>
            </div>
          </div>
        </div>
        <h3 class="delete-title">削除確認</h3>
        <p class="delete-message">この記録を削除しますか？</p>
        <div class="delete-details">
          <div class="detail-item">
            <span class="detail-label">項目:</span>
            <span class="detail-value">{{ deleteTarget?.item }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">製品CD:</span>
            <span class="detail-value">{{ deleteTarget?.product_cd }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">製品名:</span>
            <span class="detail-value">{{ deleteTarget?.product_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">数量:</span>
            <span class="detail-value">{{ deleteTarget?.quantity }}</span>
          </div>
        </div>
        <div class="delete-warning">
          <el-icon><WarningFilled /></el-icon>
          この操作は取り消すことができません。
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="deleteDialogVisible = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="danger" @click="confirmDelete" :loading="deleting" class="delete-btn">
            <el-icon><Delete /></el-icon>
            削除
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  ArrowLeft,
  Refresh,
  CircleCheckFilled,
  Delete,
  WarningFilled,
  DocumentAdd,
  Close,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import InventoryEntryForm from './components/InventoryEntryForm.vue'
import BatchInventoryEntryDialog from './components/BatchInventoryEntryDialog.vue'
import {
  createInventoryEntry,
  getRecentEntries,
  deleteInventoryLog,
  type InventoryLog,
} from '@/api/inventory'

// 响应式数据
const showForm = ref(false)
const submitting = ref(false)
const historyLoading = ref(false)
const successDialogVisible = ref(false)
const lastEntry = ref<any>(null)
const lastFormData = ref<any>({})

// 最近录入记录
const recentEntries = ref<InventoryLog[]>([])

// 排序相关状态
const sortBy = ref('updated_at')
const sortOrder = ref<'ascending' | 'descending'>('descending')

// 筛选相关状态
const selectedMonth = ref<string>('')

// 删除相关状态
const deleteDialogVisible = ref(false)
const deleteTarget = ref<InventoryLog | null>(null)
const deleting = ref(false)

// 批量录入相关状态
const batchDialogVisible = ref(false)
const getItemTypeColor = (type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (type) {
    case '材料棚卸':
      return 'success'
    case '部品棚卸':
      return 'warning'
    case '製品棚卸':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取数量样式类
const getQuantityClass = (quantity: number): string => {
  if (quantity <= 0) return 'out-of-stock'
  if (quantity <= 10) return 'low-stock'
  return 'normal-stock'
}

// 格式化日期时间
const formatDateTime = (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm:ss')

// 处理表单提交
const handleFormSubmit = async (data: any) => {
  submitting.value = true

  try {
    // 调用API创建库存记录
    const response = await createInventoryEntry(data)
    console.log('创建库存记录响应:', response)

    // 响应拦截器已经处理了数据结构
    lastEntry.value = response.data || response

    // 保存表单数据用于继续输入
    lastFormData.value = {
      item:
        data.item === '材料棚卸'
          ? '材料'
          : data.item === '部品棚卸'
            ? '部品'
            : data.item === '製品棚卸'
              ? 'ステー'
              : data.item,
      product_cd: data.product_cd,
      product_name: data.product_name,
      process_cd: data.process_cd,
      process_name: data.process_name,
      remarks: data.remarks,
      // 重置数量和时间相关字段
      quantity: 0,
      log_date: dayjs().format('YYYY-MM-DD'),
      log_time: dayjs().format('HH:mm:ss'),
      hd_no: '手入力',
      pack_qty: null,
      case_qty: null,
    }

    successDialogVisible.value = true
    showForm.value = false

    ElMessage.success('棚卸情報の入力が完了しました！')
  } catch (error: any) {
    console.error('创建库存记录失败:', error)
    ElMessage.error('入力に失敗しました。再試行してください: ' + (error.message || error))
  } finally {
    submitting.value = false
  }
}

// 处理表单取消
const handleFormCancel = () => {
  showForm.value = false
}

// 处理成功确认
const handleSuccessConfirm = () => {
  successDialogVisible.value = false
  refreshHistory()
}

// 处理继续输入
const handleContinueInput = () => {
  successDialogVisible.value = false
  showForm.value = true
  // 表单组件会自动使用 lastFormData 作为初始数据
}

// 处理新規入力
const handleNewInput = () => {
  // 清空上次的表单数据
  lastFormData.value = {
    item: '',
    product_cd: '',
    product_name: '',
    process_cd: '',
    process_name: '',
    remarks: '',
    quantity: 0,
    log_date: dayjs().format('YYYY-MM-DD'),
    log_time: dayjs().format('HH:mm:ss'),
    hd_no: '手入力',
    pack_qty: null,
    case_qty: null,
  }
  showForm.value = true
}

// 处理批量录入
const handleBatchInput = () => {
  batchDialogVisible.value = true
}

// 处理批量录入成功
const handleBatchSuccess = () => {
  refreshHistory()
  ElMessage.success('一括棚卸登録が完了しました！')
}

// 处理排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  sortBy.value = prop
  sortOrder.value = order as 'ascending' | 'descending'

  // 对数据进行排序
  recentEntries.value.sort((a: any, b: any) => {
    let aValue = a[prop]
    let bValue = b[prop]

    // 如果是字符串，进行字符串比较
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (order === 'ascending') {
      return aValue > bValue ? 1 : aValue < bValue ? -1 : 0
    } else {
      return aValue < bValue ? 1 : aValue > bValue ? -1 : 0
    }
  })
}

// 处理月份筛选变化
const handleMonthChange = async (month: string) => {
  selectedMonth.value = month
  await filterEntriesByMonth()
}

// 清除筛选
const clearFilter = () => {
  selectedMonth.value = ''
  refreshHistory()
}

// 根据月份筛选记录
const filterEntriesByMonth = async () => {
  if (!selectedMonth.value) {
    refreshHistory()
    return
  }

  historyLoading.value = true
  try {
    // 获取更多数据以支持筛选
    const response = await getRecentEntries(100, '手入力')
    const allEntries = Array.isArray(response) ? response : response.data || []

    // 筛选当前月份的数据
    const filteredEntries = allEntries.filter((entry: any) => {
      const entryDate = dayjs(entry.updated_at)
      const selectedDate = dayjs(selectedMonth.value)
      return entryDate.format('YYYY-MM') === selectedDate.format('YYYY-MM')
    })

    recentEntries.value = filteredEntries
    console.log(`筛选出 ${filteredEntries.length} 条 ${selectedMonth.value} 的记录`)
  } catch (error: any) {
    console.error('月份筛选失败:', error)
    ElMessage.error('月別フィルターに失敗しました')
  } finally {
    historyLoading.value = false
  }
}

// 刷新历史记录
const refreshHistory = async () => {
  historyLoading.value = true

  try {
    console.log('开始获取最近录入记录...')
    // 筛选 hd_no 为 '手入力' 的记录
    const response = await getRecentEntries(50, '手入力') // 增加获取数量以支持筛选
    console.log('API 响应:', response)
    // 响应拦截器已经处理了数据结构，直接使用 response
    const allEntries = Array.isArray(response) ? response : response.data || []

    // 如果有月份筛选，则应用筛选
    if (selectedMonth.value) {
      const filteredEntries = allEntries.filter((entry: any) => {
        const entryDate = dayjs(entry.updated_at)
        const selectedDate = dayjs(selectedMonth.value)
        return entryDate.format('YYYY-MM') === selectedDate.format('YYYY-MM')
      })
      recentEntries.value = filteredEntries
    } else {
      recentEntries.value = allEntries.slice(0, 10) // 默认显示最近10条
    }

    console.log('设置到 recentEntries:', recentEntries.value)
  } catch (error: any) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('履歴記録の取得に失敗しました: ' + (error.message || error))
  } finally {
    historyLoading.value = false
  }
}

// 返回列表
const goBack = () => {
  showForm.value = false
  refreshHistory()
}

// 处理删除
const handleDelete = (row: InventoryLog) => {
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

// 确认删除
const confirmDelete = async () => {
  if (!deleteTarget.value) return

  deleting.value = true
  try {
    await deleteInventoryLog(deleteTarget.value.id)
    ElMessage.success('記録を削除しました')
    deleteDialogVisible.value = false
    deleteTarget.value = null
    refreshHistory() // 刷新列表
  } catch (error: any) {
    console.error('删除失败:', error)
    ElMessage.error('削除に失敗しました: ' + (error.message || error))
  } finally {
    deleting.value = false
  }
}

// 生成粒子样式
const getParticleStyle = (index: number) => {
  const size = Math.random() * 4 + 2
  const left = Math.random() * 100
  const animationDelay = Math.random() * 10
  const animationDuration = Math.random() * 20 + 10

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${animationDelay}s`,
    animationDuration: `${animationDuration}s`,
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  refreshHistory()
})
</script>

<style scoped>
/* 动画定义 */
@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  33% {
    transform: translateY(-20px) rotate(120deg);
  }
  66% {
    transform: translateY(10px) rotate(240deg);
  }
}

@keyframes particleFloat {
  0% {
    transform: translateY(100vh) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px) rotate(360deg);
    opacity: 0;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

@keyframes glow {
  0%,
  100% {
    box-shadow: 0 0 20px rgba(14, 165, 233, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(14, 165, 233, 0.6);
  }
}

@keyframes successCheckmark {
  0% {
    stroke-dashoffset: 100;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes successCircle {
  0% {
    transform: scale(0) rotate(0deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.1) rotate(180deg);
    opacity: 1;
  }
  100% {
    transform: scale(1) rotate(360deg);
    opacity: 1;
  }
}

@keyframes warningPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.inventory-entry-page {
  position: relative;
  padding: 24px;
  background: linear-gradient(
    135deg,
    #f0f9ff 0%,
    #e0f2fe 25%,
    #f0f9ff 50%,
    #e0f2fe 75%,
    #f0f9ff 100%
  );
  min-height: 100vh;
  overflow: hidden;
}

/* 动态背景 */
.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  animation: float 6s ease-in-out infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.3) 0%, rgba(56, 189, 248, 0.1) 70%);
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.4) 0%, rgba(125, 211, 252, 0.1) 70%);
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.orb-3 {
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(125, 211, 252, 0.5) 0%, rgba(186, 230, 253, 0.1) 70%);
  bottom: 20%;
  left: 60%;
  animation-delay: 4s;
}

.orb-4 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.1) 70%);
  top: 50%;
  right: 30%;
  animation-delay: 1s;
}

.floating-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.particle {
  position: absolute;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.6) 0%, rgba(56, 189, 248, 0.3) 70%);
  border-radius: 50%;
  animation: particleFloat linear infinite;
}

.page-header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  box-shadow:
    0 12px 40px rgba(14, 165, 233, 0.15),
    0 6px 20px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  animation: slideInDown 0.8s ease-out;
  z-index: 1;
  overflow: hidden;
}

.header-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.1) 0%, transparent 70%);
  animation: glow 4s ease-in-out infinite;
  pointer-events: none;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.1), transparent);
  transition: left 0.5s;
}

.page-header:hover::before {
  left: 100%;
}

.header-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-text {
  flex: 1;
}

.header-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%);
  border-radius: 20px;
  box-shadow:
    0 8px 25px rgba(14, 165, 233, 0.4),
    0 4px 12px rgba(56, 189, 248, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: iconPulse 3s ease-in-out infinite;
  overflow: hidden;
}

.icon-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border: 2px solid rgba(14, 165, 233, 0.3);
  border-radius: 24px;
  animation: iconPulse 3s ease-in-out infinite reverse;
}

.header-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}

.header-icon :deep(.el-icon) {
  font-size: 24px;
  color: white;
  z-index: 1;
  position: relative;
}

.header-icon:hover {
  transform: translateY(-2px);
  box-shadow:
    0 6px 20px rgba(14, 165, 233, 0.4),
    0 3px 12px rgba(56, 189, 248, 0.3);
}

.page-title {
  margin: 0 0 12px 0;
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 32px;
  font-weight: 900;
  letter-spacing: -0.8px;
  position: relative;
}

.title-underline {
  width: 60px;
  height: 4px;
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
  border-radius: 2px;
  margin-top: 8px;
  animation: shimmer 2s ease-in-out infinite;
}

.page-description {
  margin: 0;
  color: #64748b;
  font-size: 16px;
  font-weight: 500;
  opacity: 0.9;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 20px;
}

.action-btn {
  position: relative;
  border-radius: 16px !important;
  padding: 16px 28px !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden !important;
  border: none !important;
  backdrop-filter: blur(10px) !important;
}

.btn-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.action-btn:hover .btn-glow {
  transform: translateX(100%);
}

.primary-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%) !important;
  box-shadow:
    0 8px 25px rgba(14, 165, 233, 0.4),
    0 4px 12px rgba(56, 189, 248, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
  color: white !important;
}

.primary-btn:hover {
  background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 50%, #38bdf8 100%) !important;
  transform: translateY(-4px) scale(1.02) !important;
  box-shadow:
    0 12px 35px rgba(14, 165, 233, 0.5),
    0 6px 16px rgba(56, 189, 248, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
}

.success-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%) !important;
  box-shadow:
    0 8px 25px rgba(16, 185, 129, 0.4),
    0 4px 12px rgba(5, 150, 105, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
  color: white !important;
}

.success-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%) !important;
  transform: translateY(-4px) scale(1.02) !important;
  box-shadow:
    0 12px 35px rgba(16, 185, 129, 0.5),
    0 6px 16px rgba(5, 150, 105, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
}

.back-btn {
  background: rgba(255, 255, 255, 0.9) !important;
  border: 2px solid rgba(14, 165, 233, 0.3) !important;
  color: #0ea5e9 !important;
  box-shadow:
    0 6px 20px rgba(14, 165, 233, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
}

.back-btn:hover {
  background: rgba(14, 165, 233, 0.1) !important;
  border-color: rgba(14, 165, 233, 0.5) !important;
  transform: translateY(-3px) scale(1.02) !important;
  box-shadow:
    0 10px 30px rgba(14, 165, 233, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
}

.form-container {
  position: relative;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.85));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 28px;
  padding: 40px;
  margin-bottom: 40px;
  box-shadow:
    0 25px 50px rgba(14, 165, 233, 0.15),
    0 12px 24px rgba(0, 0, 0, 0.08),
    0 4px 8px rgba(0, 0, 0, 0.04),
    inset 0 2px 0 rgba(255, 255, 255, 0.9),
    inset 0 -1px 0 rgba(0, 0, 0, 0.05);
  animation: slideInLeft 0.8s ease-out;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
  overflow: hidden;
}

.form-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8, #7dd3fc, #38bdf8, #0ea5e9);
}

.form-container:hover {
  transform: translateY(-8px) scale(1.01);
  box-shadow:
    0 35px 70px rgba(14, 165, 233, 0.2),
    0 18px 36px rgba(0, 0, 0, 0.12),
    0 8px 16px rgba(0, 0, 0, 0.06),
    inset 0 2px 0 rgba(255, 255, 255, 0.95),
    inset 0 -1px 0 rgba(0, 0, 0, 0.08);
  border-color: rgba(255, 255, 255, 0.4);
}

.history-container {
  position: relative;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.85));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 28px;
  padding: 8px;
  box-shadow:
    0 25px 50px rgba(14, 165, 233, 0.15),
    0 12px 24px rgba(0, 0, 0, 0.08),
    0 4px 8px rgba(0, 0, 0, 0.04),
    inset 0 2px 0 rgba(255, 255, 255, 0.9),
    inset 0 -1px 0 rgba(0, 0, 0, 0.05);
  z-index: 1;
  overflow: hidden;
}

.history-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #10b981, #059669, #047857, #059669, #10b981);
}

.history-card {
  border: none;
  border-radius: 20px;
  background: transparent;
  box-shadow: none;
}

.history-card :deep(.el-card__body) {
  padding: 24px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.05) 0%, rgba(56, 189, 248, 0.03) 100%);
  border-radius: 16px 16px 0 0;
  border-bottom: 1px solid rgba(14, 165, 233, 0.1);
}

.history-header h3 {
  margin: 0;
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 20px;
  font-weight: 700;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.month-filter {
  width: 140px;
}

.month-filter :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.month-filter :deep(.el-input__wrapper:hover) {
  border-color: rgba(14, 165, 233, 0.4);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
}

.month-filter :deep(.el-input__wrapper.is-focus) {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
}

.header-info :deep(.el-tag) {
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.2);
  color: #0ea5e9;
  border-radius: 8px;
  font-weight: 500;
}

.header-info :deep(.el-button) {
  color: #0ea5e9;
  font-weight: 600;
}

.header-info :deep(.el-button:hover) {
  color: #0284c7;
}

.history-table {
  border-radius: 20px;
  overflow: hidden;
  border: 2px solid rgba(14, 165, 233, 0.15);
  box-shadow:
    0 8px 32px rgba(14, 165, 233, 0.12),
    0 4px 16px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  backdrop-filter: blur(15px);
  table-layout: fixed;
  width: 100%;
}

.history-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%);
  position: relative;
}

.history-table :deep(.el-table__header)::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8, #7dd3fc, #38bdf8, #0ea5e9);
}

.history-table :deep(.el-table__header th) {
  background: transparent;
  color: #1e293b;
  font-weight: 800;
  font-size: 15px;
  border-bottom: none;
  padding: 24px 20px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  text-shadow: none;
  cursor: pointer;
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-table :deep(.el-table__header th:hover) {
  background: rgba(14, 165, 233, 0.05);
  color: #0ea5e9;
}

.history-table :deep(.el-table__sort-caret) {
  border-color: #0ea5e9;
}

.history-table :deep(.el-table__sort-caret.ascending) {
  border-bottom-color: #0ea5e9;
}

.history-table :deep(.el-table__sort-caret.descending) {
  border-top-color: #0ea5e9;
}

.history-table :deep(.el-table__column-sort) {
  color: #0ea5e9;
}

.history-table :deep(.el-table__row) {
  border-bottom: 1px solid rgba(14, 165, 233, 0.1);
  background: rgba(255, 255, 255, 0.95);
  position: relative;
}

.history-table :deep(.el-table__row:hover) {
  background: rgba(14, 165, 233, 0.05);
}

/* 确保表格列宽度对齐 */
.history-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.history-table :deep(.el-table__header-wrapper) {
  overflow-x: hidden;
}

.history-table :deep(.el-table__body) {
  width: 100%;
}

.history-table :deep(.el-table__header) {
  width: 100%;
}

.history-table :deep(.el-table td) {
  padding: 22px 20px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.08);
  font-size: 15px;
  font-weight: 500;
  color: #374151;
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-table :deep(.el-tag) {
  border-radius: 8px;
  font-weight: 600;
  padding: 4px 12px;
}

.history-table :deep(.el-button) {
  border-radius: 8px;
  font-weight: 600;
}

.history-table :deep(.el-button--danger) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
}

.history-table :deep(.el-button--danger:hover) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

/* 数量样式 */
.out-of-stock {
  color: #ef4444;
  font-weight: 700;
  background: rgba(239, 68, 68, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.low-stock {
  color: #f59e0b;
  font-weight: 700;
  background: rgba(245, 158, 11, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.normal-stock {
  color: #10b981;
  font-weight: 700;
  background: rgba(16, 185, 129, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.empty-state :deep(.el-empty) {
  padding: 40px;
}

.empty-state :deep(.el-empty__description) {
  color: #64748b;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 24px;
}

.empty-state :deep(.el-button) {
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
  border: none;
  border-radius: 12px;
  padding: 14px 28px;
  font-weight: 600;
  font-size: 15px;
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.3);
  transition: all 0.3s ease;
}

.empty-state :deep(.el-button:hover) {
  background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
}

/* 成功对话框样式 */
.success-content {
  text-align: center;
  padding: 48px 40px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  border-radius: 24px;
  position: relative;
  overflow: hidden;
}

.success-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #10b981, #059669, #047857, #059669, #10b981);
}

.success-animation {
  position: relative;
  margin-bottom: 32px;
}

.success-circle {
  width: 100px;
  height: 100px;
  margin: 0 auto;
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 12px 40px rgba(16, 185, 129, 0.4),
    0 6px 20px rgba(5, 150, 105, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.3);
  animation: successCircle 0.8s ease-out;
  position: relative;
  overflow: hidden;
}

.success-circle::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: glow 2s ease-in-out infinite;
}

.success-checkmark {
  position: relative;
  width: 50px;
  height: 50px;
}

.checkmark-stem {
  position: absolute;
  width: 3px;
  height: 20px;
  background-color: white;
  left: 18px;
  top: 15px;
  transform: rotate(45deg);
  border-radius: 2px;
  animation: successCheckmark 0.6s ease-out 0.3s both;
}

.checkmark-kick {
  position: absolute;
  width: 3px;
  height: 12px;
  background-color: white;
  left: 12px;
  top: 21px;
  transform: rotate(-45deg);
  border-radius: 2px;
  animation: successCheckmark 0.6s ease-out 0.5s both;
}

.success-title {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #059669, #047857);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
  animation: slideUp 0.6s ease-out 0.5s both;
}

.success-message {
  font-size: 18px;
  color: #64748b;
  margin: 20px 0;
  font-weight: 500;
  animation: slideUp 0.6s ease-out 0.7s both;
}

.success-details {
  background: linear-gradient(145deg, rgba(16, 185, 129, 0.08), rgba(5, 150, 105, 0.05));
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-radius: 20px;
  padding: 28px;
  margin-top: 32px;
  text-align: left;
  backdrop-filter: blur(10px);
  box-shadow:
    0 8px 32px rgba(16, 185, 129, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: slideUp 0.6s ease-out 0.9s both;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  padding: 12px 0;
  border-bottom: 1px solid rgba(16, 185, 129, 0.1);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
}

.detail-value {
  color: #047857;
  font-weight: 700;
  font-size: 15px;
}

.quantity-highlight {
  background: linear-gradient(135deg, #10b981, #059669);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 18px;
  font-weight: 800;
}

.dialog-footer {
  text-align: center;
  padding-top: 32px;
  animation: slideUp 0.6s ease-out 1.1s both;
}

.continue-btn {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(15px) !important;
  border: 2px solid rgba(16, 185, 129, 0.3) !important;
  color: #059669 !important;
  border-radius: 16px !important;
  padding: 16px 32px !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  margin: 0 12px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative !important;
  overflow: hidden !important;
}

.continue-btn:hover {
  background: rgba(16, 185, 129, 0.1) !important;
  border-color: rgba(16, 185, 129, 0.5) !important;
  transform: translateY(-3px) scale(1.02) !important;
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3) !important;
}

.confirm-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%) !important;
  border: none !important;
  box-shadow:
    0 8px 25px rgba(16, 185, 129, 0.4),
    0 4px 12px rgba(5, 150, 105, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  border-radius: 16px !important;
  padding: 16px 32px !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  margin: 0 12px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative !important;
  overflow: hidden !important;
}

.confirm-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%) !important;
  transform: translateY(-3px) scale(1.02) !important;
  box-shadow:
    0 12px 35px rgba(16, 185, 129, 0.5),
    0 6px 16px rgba(5, 150, 105, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
}

/* 删除对话框样式 */
.delete-content {
  text-align: center;
  padding: 48px 40px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  border-radius: 24px;
  position: relative;
  overflow: hidden;
}

.delete-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #ef4444, #dc2626, #b91c1c, #dc2626, #ef4444);
}

.delete-animation {
  position: relative;
  margin-bottom: 32px;
}

.warning-circle {
  width: 100px;
  height: 100px;
  margin: 0 auto;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 12px 40px rgba(239, 68, 68, 0.4),
    0 6px 20px rgba(220, 38, 38, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.3);
  animation: warningPulse 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.warning-circle::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: glow 2s ease-in-out infinite;
}

.warning-icon {
  position: relative;
  width: 50px;
  height: 50px;
}

.warning-line {
  position: absolute;
  width: 4px;
  height: 30px;
  background-color: white;
  left: 23px;
  top: 8px;
  border-radius: 2px;
  animation: warningPulse 1.5s ease-in-out infinite;
}

.warning-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  background-color: white;
  left: 22px;
  top: 42px;
  border-radius: 50%;
  animation: warningPulse 1.5s ease-in-out infinite 0.3s;
}

.delete-title {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
  animation: slideUp 0.6s ease-out 0.5s both;
}

.delete-message {
  font-size: 18px;
  color: #64748b;
  margin: 20px 0;
  font-weight: 500;
  animation: slideUp 0.6s ease-out 0.7s both;
}

.delete-details {
  background: linear-gradient(145deg, rgba(239, 68, 68, 0.08), rgba(220, 38, 38, 0.05));
  border: 2px solid rgba(239, 68, 68, 0.2);
  border-radius: 20px;
  padding: 28px;
  margin-top: 32px;
  text-align: left;
  backdrop-filter: blur(10px);
  box-shadow:
    0 8px 32px rgba(239, 68, 68, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: slideUp 0.6s ease-out 0.9s both;
}

.delete-details .detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  padding: 12px 0;
  border-bottom: 1px solid rgba(239, 68, 68, 0.1);
}

.delete-details .detail-item:last-child {
  border-bottom: none;
}

.delete-details .detail-label {
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
}

.delete-details .detail-value {
  color: #dc2626;
  font-weight: 700;
  font-size: 15px;
}

.delete-warning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #dc2626;
  font-size: 15px;
  margin-top: 24px;
  font-weight: 600;
  background: linear-gradient(145deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.08));
  padding: 16px 20px;
  border-radius: 12px;
  border: 2px solid rgba(239, 68, 68, 0.2);
  backdrop-filter: blur(10px);
  animation: slideUp 0.6s ease-out 1.1s both;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(15px) !important;
  border: 2px solid rgba(107, 114, 128, 0.3) !important;
  color: #6b7280 !important;
  border-radius: 16px !important;
  padding: 16px 32px !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  margin: 0 12px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.cancel-btn:hover {
  background: rgba(107, 114, 128, 0.1) !important;
  border-color: rgba(107, 114, 128, 0.5) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(107, 114, 128, 0.2) !important;
}

.delete-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%) !important;
  border: none !important;
  box-shadow:
    0 8px 25px rgba(239, 68, 68, 0.4),
    0 4px 12px rgba(220, 38, 38, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  border-radius: 16px !important;
  padding: 16px 32px !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  margin: 0 12px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.delete-btn:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 50%, #991b1b 100%) !important;
  transform: translateY(-3px) scale(1.02) !important;
  box-shadow:
    0 12px 35px rgba(239, 68, 68, 0.5),
    0 6px 16px rgba(220, 38, 38, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .inventory-entry-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .page-title {
    font-size: 20px;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .inventory-entry-page {
    padding: 12px;
  }

  .page-header {
    padding: 16px;
  }

  .page-title {
    font-size: 18px;
  }

  .history-table {
    font-size: 12px;
  }
}
</style>
