<template>
  <div class="inventory-value-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <Operation class="icon" />
          </div>
          <div class="header-text">
            <h1 class="page-title">棚卸金額管理</h1>
            <p class="page-description">在庫金額の計算・分析・レポート管理</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 期间筛选条件 -->
    <div class="filter-container">
      <div class="filter-row">
        <div class="filter-item">
          <label class="filter-label">期間選択</label>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
            class="date-picker"
          />
        </div>
        <div class="filter-item">
          <label class="filter-label">工程選択</label>
          <el-select
            v-model="selectedProcess"
            placeholder="工程を選択"
            @change="handleProcessChange"
            class="process-select"
          >
            <el-option label="全部" value="all" />
            <el-option
              v-for="process in processList"
              :key="process.process_cd"
              :label="process.process_name"
              :value="process.process_cd"
            />
          </el-select>
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="searchData" :loading="loading" class="search-btn">
            <Search class="btn-icon" />
            検索
          </el-button>
          <el-button @click="clearFilters" class="clear-btn">
            <RefreshLeft class="btn-icon" />
            クリア
          </el-button>
        </div>
      </div>
    </div>

    <!-- 金额统计卡片 -->
    <div class="stats-container">
      <div class="stats-grid">
        <div class="stat-card material-card">
          <div class="stat-header">
            <div class="stat-badge material">材料</div>
          </div>
          <div class="stat-icon">
            <Box class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">
              ¥{{ formatNumber(statistics.total?.material_amount || 0) }}
            </div>
            <div class="stat-label">材料金額</div>
          </div>
        </div>
        <div class="stat-card component-card">
          <div class="stat-header">
            <div class="stat-badge component">部品</div>
          </div>
          <div class="stat-icon">
            <Setting class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">
              ¥{{ formatNumber(statistics.total?.component_amount || 0) }}
            </div>
            <div class="stat-label">部品金額</div>
          </div>
        </div>
        <div class="stat-card stay-card">
          <div class="stat-header">
            <div class="stat-badge stay">ステー</div>
          </div>
          <div class="stat-icon">
            <Tools class="icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">¥{{ formatNumber(statistics.total?.stay_amount || 0) }}</div>
            <div class="stat-label">ステー金額</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签页切换 -->
    <div class="content-tabs">
      <el-card class="tabs-card">
        <el-tabs v-model="activeTab" class="main-tabs">
          <el-tab-pane label="材料" name="material">
            <InventoryValueTable
              ref="materialTableRef"
              :date-range="dateRange"
              item-type="材料"
              :process-code="selectedProcess"
              @data-updated="handleDataUpdated"
            />
          </el-tab-pane>

          <el-tab-pane label="部品" name="component">
            <InventoryValueTable
              ref="componentTableRef"
              :date-range="dateRange"
              item-type="部品"
              :process-code="selectedProcess"
              @data-updated="handleDataUpdated"
            />
          </el-tab-pane>

          <el-tab-pane label="ステー" name="stay">
            <InventoryValueTable
              ref="stayTableRef"
              :date-range="dateRange"
              item-type="ステー"
              :process-code="selectedProcess"
              @data-updated="handleDataUpdated"
            />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation, Search, RefreshLeft, Box, Setting, Tools } from '@element-plus/icons-vue'
import { inventoryValueApi, type InventoryValueParams } from '@/api/inventoryValue'
import InventoryValueTable from './components/InventoryValueTable.vue'

// 类型定义
interface ProcessItem {
  process_cd: string
  process_name: string
}

interface StatisticsData {
  total: {
    total_amount: number
    material_amount: number
    component_amount: number
    stay_amount: number
  }
  byType: any[]
  byProcess: any[]
}

// 响应式数据
const loading = ref(false)
const activeTab = ref('material')

// 组件引用
const materialTableRef = ref()
const componentTableRef = ref()
const stayTableRef = ref()

// 筛选条件
const dateRange = ref<string[]>([])
const selectedProcess = ref('all')
const processList = ref<ProcessItem[]>([])

// 统计数据
const statistics = ref<StatisticsData>({
  total: {
    total_amount: 0,
    material_amount: 0,
    component_amount: 0,
    stay_amount: 0,
  },
  byType: [],
  byProcess: [],
})

// 计算属性
const currentDateRange = computed(() => {
  if (dateRange.value && dateRange.value.length === 2) {
    return {
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
    }
  }
  return { startDate: '', endDate: '' }
})

// 方法
const formatNumber = (value: number | string | undefined, decimals = 0): string => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

// 处理数据更新
const handleDataUpdated = (data: any) => {
  // 更新统计数据
  if (data.statistics) {
    statistics.value = data.statistics
  }
}

// 数据加载
const loadStatistics = async () => {
  try {
    const params: InventoryValueParams = {
      ...currentDateRange.value,
      processCode: selectedProcess.value,
    }
    const response = await inventoryValueApi.getInventoryValueSummary(params)
    if (response.data) {
      statistics.value = response.data
    }
  } catch (error) {
    console.error('统计数据加载失败:', error)
    ElMessage.error('统计数据加载失败')
  }
}

const loadProcessList = async () => {
  try {
    const response = await inventoryValueApi.getProcessList()
    if (response.data) {
      processList.value = response.data as unknown as ProcessItem[]
    }
  } catch (error) {
    console.error('工程列表加载失败:', error)
  }
}

// 事件处理
const handleDateChange = () => {
  searchData()
}

const handleProcessChange = () => {
  searchData()
}

const searchData = () => {
  loadStatistics()
  // 刷新当前激活的表格
  refreshCurrentTable()
}

const clearFilters = () => {
  dateRange.value = []
  selectedProcess.value = 'all'
  searchData()
}

// 刷新当前激活的表格
const refreshCurrentTable = () => {
  switch (activeTab.value) {
    case 'material':
      if (materialTableRef.value) {
        materialTableRef.value.refreshTable()
      }
      break
    case 'component':
      if (componentTableRef.value) {
        componentTableRef.value.refreshTable()
      }
      break
    case 'stay':
      if (stayTableRef.value) {
        stayTableRef.value.refreshTable()
      }
      break
  }
}

// 初始化
onMounted(() => {
  // 设置默认日期范围为当月
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)

  dateRange.value = [firstDay.toISOString().split('T')[0], lastDay.toISOString().split('T')[0]]

  loadProcessList()
  searchData()
})
</script>

<style scoped>
/* 基础样式 */
.inventory-value-management {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.header-icon .icon {
  font-size: 24px;
  color: white;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.4;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
}

/* 筛选容器 */
.filter-container {
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
}

.filter-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 16px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 4px;
}

.date-picker,
.process-select {
  width: 100%;
}

.date-picker :deep(.el-input__wrapper),
.process-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
}

.date-picker :deep(.el-input__wrapper):hover,
.process-select :deep(.el-input__wrapper):hover {
  border-color: #409eff;
}

.date-picker :deep(.el-input__wrapper.is-focus),
.process-select :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.date-picker :deep(.el-input__inner),
.process-select :deep(.el-input__inner) {
  color: #606266;
  font-weight: 400;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: end;
}

/* 按钮样式 */
.search-btn,
.clear-btn {
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
}

.search-btn {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.search-btn:hover {
  background: #337ecc;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.4);
}

.clear-btn {
  background: #f5f7fa;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.clear-btn:hover {
  background: #ecf5ff;
  color: #409eff;
  border-color: #409eff;
}

.btn-icon {
  font-size: 16px;
}

/* 统计卡片 */
.stats-container {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.stat-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stat-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.stat-badge.material {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.stat-badge.component {
  background: linear-gradient(135deg, #67c23a, #529b2e);
}

.stat-badge.stay {
  background: linear-gradient(135deg, #e6a23c, #cf9236);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
}

.material-card .stat-icon {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.component-card .stat-icon {
  background: linear-gradient(135deg, #67c23a, #529b2e);
}

.stay-card .stat-icon {
  background: linear-gradient(135deg, #e6a23c, #cf9236);
}

.stat-icon .icon {
  font-size: 24px;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.2;
}

.stat-label {
  font-size: 16px;
  color: #606266;
  font-weight: 600;
  margin-bottom: 8px;
}

.stat-description {
  font-size: 14px;
  color: #909399;
  font-weight: 400;
  line-height: 1.5;
}

/* 标签页容器 */
.content-tabs {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.tabs-card {
  background: transparent;
  border: none;
  box-shadow: none;
}

.tabs-card :deep(.el-card__body) {
  padding: 0;
}

.main-tabs :deep(.el-tabs__header) {
  background: #fafafa;
  border-bottom: 1px solid #e4e7ed;
  margin: 0;
  padding: 0 24px;
}

.main-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.main-tabs :deep(.el-tabs__item) {
  color: #606266;
  font-weight: 500;
  padding: 16px 24px;
  transition: all 0.3s ease;
  position: relative;
  border-radius: 8px 8px 0 0;
  margin-right: 4px;
}

.main-tabs :deep(.el-tabs__item:hover) {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.main-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 600;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.main-tabs :deep(.el-tabs__active-bar) {
  background: #409eff;
  height: 3px;
  border-radius: 2px;
}

.main-tabs :deep(.el-tabs__content) {
  padding: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .inventory-value-management {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .filter-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .filter-actions {
    justify-content: center;
    margin-top: 8px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .page-title {
    font-size: 20px;
  }

  .stat-value {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .inventory-value-management {
    padding: 12px;
  }

  .page-title {
    font-size: 18px;
  }

  .stat-card {
    padding: 20px;
  }

  .stat-value {
    font-size: 20px;
  }
}
</style>
