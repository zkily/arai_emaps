<template>
  <div class="inventory-carryover-management">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="gradient-orb orb-4"></div>
      <div class="floating-particles">
        <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
      </div>
      <div class="grid-overlay"></div>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-glow"></div>
      <div class="header-content">
        <div class="header-icon">
          <div class="icon-ring"></div>
          <div class="icon-glow"></div>
          <el-icon><Share /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">
            <span class="title-main">棚卸データ繰越管理</span>
            <span class="title-accent">機能</span>
          </h1>
          <p class="page-description">特定月と工程の月末棚卸データを翌月の期初在庫として繰越管理</p>
          <div class="title-underline"></div>
        </div>
      </div>
    </div>

    <!-- 功能选项卡 -->
    <div class="tabs-container">
      <el-tabs v-model="activeTab" class="modern-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="データ繰越" name="carryover">
          <template #label>
            <span class="tab-label">
              <div class="tab-icon">
                <el-icon><Share /></el-icon>
              </div>
              <span class="tab-text">データ繰越</span>
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="繰越履歴管理" name="history">
          <template #label>
            <span class="tab-label">
              <div class="tab-icon">
                <el-icon><Collection /></el-icon>
              </div>
              <span class="tab-text">繰越履歴管理</span>
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 数据繰越选项卡内容 -->
    <div v-if="activeTab === 'carryover'" class="carryover-content">
      <!-- 筛选区 -->
      <el-card class="filter-card" shadow="hover">
        <div class="card-glow"></div>
        <div class="filter-header">
          <div class="filter-title">
            <div class="title-icon">
              <el-icon><ZoomIn /></el-icon>
            </div>
            <div class="title-content">
              <h3>検索フィルター</h3>
              <p>条件を設定して棚卸データを検索</p>
            </div>
          </div>
        </div>
        <div class="filter-content">
          <div class="filter-row">
            <div class="filter-item">
              <label class="filter-label">
                <el-icon><Calendar /></el-icon>
                対象月
              </label>
              <el-date-picker
                v-model="filterParams.month"
                type="month"
                placeholder="月を選択"
                format="YYYY-MM"
                value-format="YYYY-MM"
                class="filter-input modern-input"
                clearable
              />
            </div>
            <div class="filter-item">
              <label class="filter-label">
                <el-icon><Setting /></el-icon>
                工程選択
              </label>
              <el-select
                v-model="filterParams.process_cd"
                placeholder="工程を選択"
                class="filter-input modern-input"
                clearable
                filterable
                :loading="processLoading"
              >
                <el-option
                  v-for="process in processOptions"
                  :key="process.value"
                  :label="process.label"
                  :value="process.value"
                />
              </el-select>
            </div>
            <div class="filter-actions">
              <el-button @click="clearFilters" class="clear-btn modern-btn">
                <el-icon><Refresh /></el-icon>
                <span>クリア</span>
              </el-button>
              <el-button
                type="primary"
                @click="handleSearch"
                class="search-btn modern-btn"
                :loading="loading"
              >
                <el-icon><Search /></el-icon>
                <span>検索</span>
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 数据列表区 -->
      <el-card class="data-card" shadow="hover" v-if="inventoryData.length > 0">
        <div class="card-glow"></div>
        <div class="data-header">
          <div class="data-title">
            <div class="title-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="title-content">
              <h3>棚卸データリスト</h3>
              <p>{{ inventoryData.length }}件のデータが見つかりました</p>
            </div>
          </div>
          <div class="data-actions">
            <el-button @click="selectAll" class="select-all-btn modern-btn" size="small">
              <el-icon><Check /></el-icon>
              <span>全選択</span>
            </el-button>
            <el-button @click="deselectAll" class="deselect-all-btn modern-btn" size="small">
              <el-icon><Close /></el-icon>
              <span>全解除</span>
            </el-button>
            <el-button
              type="primary"
              @click="handleCarryover"
              :disabled="selectedData.length === 0"
              :loading="carryoverLoading"
              class="carryover-btn modern-btn"
            >
              <el-icon><Share /></el-icon>
              <span>選択データ繰越 ({{ selectedData.length }})</span>
            </el-button>
          </div>
        </div>

        <div class="table-container">
          <el-table
            :data="inventoryData"
            v-loading="loading"
            stripe
            highlight-current-row
            @selection-change="handleSelectionChange"
            class="data-table modern-table"
          >
            <el-table-column type="selection" width="55" align="center">
              <template #header>
                <div class="table-header-icon">
                  <el-icon><Check /></el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="product_cd" label="製品CD" width="120" align="center">
              <template #header>
                <div class="table-header">
                  <div class="header-left">
                    <el-icon><Box /></el-icon>
                    <span>製品CD</span>
                  </div>
                  <div class="header-right"></div>
                </div>
              </template>
              <template #default="{ row }">
                <div class="product-code">{{ row.product_cd }}</div>
              </template>
            </el-table-column>
            <el-table-column
              prop="product_name"
              label="製品名"
              min-width="200"
              show-overflow-tooltip
            >
              <template #header>
                <div class="table-header">
                  <div class="header-left">
                    <el-icon><Document /></el-icon>
                    <span>製品名</span>
                  </div>
                  <div class="header-right">
                    <el-icon
                      class="sort-icon"
                      :class="{
                        'sort-active': sortConfig.prop === 'product_name',
                        'sort-asc':
                          sortConfig.prop === 'product_name' && sortConfig.order === 'ascending',
                        'sort-desc':
                          sortConfig.prop === 'product_name' && sortConfig.order === 'descending',
                      }"
                      @click="handleCustomSort('product_name')"
                    >
                      <Sort />
                    </el-icon>
                  </div>
                </div>
              </template>
              <template #default="{ row }">
                <div class="product-name">{{ row.product_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="item" label="項目" width="120" align="center">
              <template #header>
                <div class="table-header">
                  <div class="header-left">
                    <el-icon><Collection /></el-icon>
                    <span>項目</span>
                  </div>
                  <div class="header-right"></div>
                </div>
              </template>
              <template #default="{ row }">
                <el-tag :type="getItemTagType(row.item)" size="small" class="item-tag">{{
                  row.item
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_quantity" label="合計数量" width="140" align="center">
              <template #header>
                <div class="table-header">
                  <div class="header-left">
                    <el-icon><Operation /></el-icon>
                    <span>合計数量</span>
                  </div>
                  <div class="header-right"></div>
                </div>
              </template>
              <template #default="{ row }">
                <div class="quantity-value">{{ formatNumber(row.total_quantity) }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="単位" width="100" align="center">
              <template #header>
                <div class="table-header">
                  <div class="header-left">
                    <el-icon><ScaleToOriginal /></el-icon>
                    <span>単位</span>
                  </div>
                  <div class="header-right"></div>
                </div>
              </template>
              <template #default="{ row }">
                <div class="unit-value">{{ row.unit }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="location_cd" label="保管場所" width="140" align="center">
              <template #header>
                <div class="table-header">
                  <div class="header-left">
                    <el-icon><Location /></el-icon>
                    <span>保管場所</span>
                  </div>
                  <div class="header-right"></div>
                </div>
              </template>
              <template #default="{ row }">
                <el-tag type="info" size="small" class="location-tag">{{ row.location_cd }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- 空数据状态 -->
      <el-empty
        v-if="
          !loading && inventoryData.length === 0 && (filterParams.month || filterParams.process_cd)
        "
        description="検索条件に一致するデータが見つかりません"
        :image-size="120"
        class="empty-state"
      >
        <template #image>
          <div class="empty-icon">
            <el-icon><Search /></el-icon>
          </div>
        </template>
        <template #description>
          <div class="empty-description">
            <h3>データが見つかりません</h3>
            <p>検索条件を変更して再度お試しください</p>
          </div>
        </template>
      </el-empty>
    </div>

    <!-- 繰越履歴管理选项卡内容 -->
    <div v-if="activeTab === 'history'" class="history-content">
      <InventoryCarryoverHistory @refresh="refreshHistoryData" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Share,
  Collection,
  ZoomIn,
  Refresh,
  Search,
  Document,
  Check,
  Close,
  Calendar,
  Setting,
  Box,
  Operation,
  ScaleToOriginal,
  Location,
  Sort,
} from '@element-plus/icons-vue'
import { getCarryoverData, executeCarryover } from '@/api/inventoryCarryover'
import { fetchProcesses } from '@/api/master/processMaster'
import InventoryCarryoverHistory from './components/InventoryCarryoverHistory.vue'

// 响应式数据
const activeTab = ref('carryover')
const loading = ref(false)
const carryoverLoading = ref(false)
const inventoryData = ref<any[]>([])
const selectedData = ref<any[]>([])

// 筛选参数
const filterParams = reactive({
  month: '',
  process_cd: '',
})

// 工程选项
const processOptions = ref<Array<{ value: string; label: string }>>([])
const processLoading = ref(false)

// 排序状态管理
const sortConfig = ref({
  prop: '',
  order: '' as 'ascending' | 'descending' | '',
})

// 加载工程数据
const loadProcessOptions = async () => {
  processLoading.value = true
  try {
    const response = await fetchProcesses({
      page: 1,
      pageSize: 1000, // 获取所有工程数据
    })

    if (response && response.list && Array.isArray(response.list)) {
      processOptions.value = response.list.map((process: any) => ({
        value: process.process_cd,
        label: `${process.process_cd} - ${process.process_name}`,
      }))
    } else {
      console.error('工程データ取得エラー:', response)
      ElMessage.error('工程データの取得に失敗しました')
    }
  } catch (error) {
    console.error('工程データ取得エラー:', error)
    ElMessage.error('工程データの取得に失敗しました')
  } finally {
    processLoading.value = false
  }
}

// 动态背景粒子样式
const getParticleStyle = (index: number) => {
  const size = Math.random() * 4 + 2
  const duration = Math.random() * 20 + 10
  const delay = Math.random() * 5
  return {
    width: `${size}px`,
    height: `${size}px`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
  }
}

// 获取项目标签类型
const getItemTagType = (item: string) => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    材料: 'warning',
    部品: 'success',
    製品: 'primary',
  }
  return typeMap[item] || 'info'
}

// 格式化数字
const formatNumber = (num: number) => {
  return num?.toLocaleString() || '0'
}

// 自定义排序处理
const handleCustomSort = (prop: string) => {
  if (sortConfig.value.prop === prop) {
    // 如果点击的是当前排序列，切换排序顺序
    if (sortConfig.value.order === 'ascending') {
      sortConfig.value.order = 'descending'
    } else if (sortConfig.value.order === 'descending') {
      sortConfig.value.order = ''
      sortConfig.value.prop = ''
    } else {
      sortConfig.value.order = 'ascending'
    }
  } else {
    // 如果点击的是新列，设置为升序
    sortConfig.value.prop = prop
    sortConfig.value.order = 'ascending'
  }

  // 对当前数据进行排序
  if (sortConfig.value.prop && sortConfig.value.order) {
    inventoryData.value.sort((a: any, b: any) => {
      const aVal = a[sortConfig.value.prop] || ''
      const bVal = b[sortConfig.value.prop] || ''

      if (sortConfig.value.order === 'ascending') {
        return aVal.localeCompare(bVal, 'ja')
      } else {
        return bVal.localeCompare(aVal, 'ja')
      }
    })
  } else {
    // 重置为原始顺序（可以重新搜索来恢复原始顺序）
    if (filterParams.month && filterParams.process_cd) {
      handleSearch()
    }
  }
}

// 清除筛选条件
const clearFilters = () => {
  filterParams.month = ''
  filterParams.process_cd = ''
  inventoryData.value = []
  selectedData.value = []
}

// 执行搜索
const handleSearch = async () => {
  if (!filterParams.month || !filterParams.process_cd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }

  loading.value = true
  try {
    const response = await getCarryoverData({
      month: filterParams.month,
      process_cd: filterParams.process_cd,
    })

    console.log('API Response:', response) // デバッグログ追加

    // responseは拦截器によって処理され、成功時は直接dataが返される
    if (response) {
      inventoryData.value = response
      selectedData.value = []
      if (inventoryData.value.length === 0) {
        ElMessage.info('指定条件のデータが見つかりませんでした')
      }
    } else {
      console.error('API Response Error:', response) // デバッグログ追加
      ElMessage.error('データ取得に失敗しました')
    }
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データ取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 全选
const selectAll = () => {
  selectedData.value = [...inventoryData.value]
}

// 全部取消选择
const deselectAll = () => {
  selectedData.value = []
}

// 处理选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedData.value = selection
}

// 执行繰越
const handleCarryover = async () => {
  if (selectedData.value.length === 0) {
    ElMessage.warning('繰越するデータを選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      `選択された ${selectedData.value.length} 件のデータを ${getNextMonth(filterParams.month)} の期初在庫として繰越しますか？`,
      '繰越確認',
      {
        confirmButtonText: '繰越実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    carryoverLoading.value = true

    const response = await executeCarryover({
      month: filterParams.month,
      process_cd: filterParams.process_cd,
      selectedData: selectedData.value,
    })

    console.log('Carryover Response:', response) // デバッグログ追加

    // responseは拦截器によって処理され、成功時は直接dataが返される
    if (response && response.successCount !== undefined) {
      ElMessage.success(`${response.successCount} 件のデータを繰越しました`)
      // 刷新数据
      await handleSearch()
    } else {
      console.error('Carryover Response Error:', response) // デバッグログ追加
      ElMessage.error('繰越処理に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('繰越処理エラー:', error)
      ElMessage.error('繰越処理に失敗しました')
    }
  } finally {
    carryoverLoading.value = false
  }
}

// 获取下个月
const getNextMonth = (month: string) => {
  if (!month) return ''
  const date = new Date(month + '-01')
  date.setMonth(date.getMonth() + 1)
  return date.toISOString().slice(0, 7)
}

// 处理选项卡变化
const handleTabChange = (tabName: string | number) => {
  console.log('タブ切り替え:', tabName)
}

// 刷新历史数据
const refreshHistoryData = () => {
  console.log('履歴データを更新')
}

// 组件挂载
onMounted(() => {
  console.log('棚卸データ繰越管理ページがロードされました')
  loadProcessOptions()
})
</script>

<style lang="scss" scoped>
.inventory-carryover-management {
  min-height: 100vh;
  position: relative;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%);
  overflow: hidden;
}

// 精简的动态背景
.dynamic-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;

  .gradient-orb {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(
      circle,
      rgba(102, 126, 234, 0.08) 0%,
      rgba(118, 75, 162, 0.05) 50%,
      transparent 100%
    );
    backdrop-filter: blur(40px);
    animation: subtle-float 20s infinite ease-in-out;

    &.orb-1 {
      width: 300px;
      height: 300px;
      top: -10%;
      left: -10%;
      animation-delay: 0s;
    }

    &.orb-2 {
      width: 200px;
      height: 200px;
      top: 40%;
      right: -5%;
      animation-delay: 10s;
    }

    &.orb-3 {
      width: 150px;
      height: 150px;
      bottom: -5%;
      left: 30%;
      animation-delay: 15s;
    }

    &.orb-4 {
      width: 100px;
      height: 100px;
      top: 15%;
      right: 25%;
      animation-delay: 5s;
    }
  }

  .floating-particles {
    position: absolute;
    width: 100%;
    height: 100%;

    .particle {
      position: absolute;
      background: radial-gradient(circle, rgba(102, 126, 234, 0.15), transparent);
      border-radius: 50%;
      animation: gentle-float infinite ease-in-out;
    }
  }

  .grid-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image:
      linear-gradient(rgba(102, 126, 234, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(102, 126, 234, 0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: subtle-grid-move 30s linear infinite;
  }
}

@keyframes subtle-float {
  0%,
  100% {
    transform: translateY(0px) scale(1);
    opacity: 0.8;
  }
  50% {
    transform: translateY(-20px) scale(1.05);
    opacity: 1;
  }
}

@keyframes gentle-float {
  0%,
  100% {
    transform: translateY(0px) translateX(0px);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-15px) translateX(5px);
    opacity: 0.8;
  }
}

@keyframes subtle-grid-move {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(40px, 40px);
  }
}

// 页面头部
.page-header {
  position: relative;
  z-index: 10;
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;

  .header-glow {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
    animation: subtle-glow 4s ease-in-out infinite alternate;
  }

  .header-content {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    border: 1px solid rgba(102, 126, 234, 0.1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
      border-color: rgba(102, 126, 234, 0.2);
    }

    .header-icon {
      position: relative;
      width: 60px;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #667eea, #764ba2);
      border-radius: 16px;
      box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4);
      }

      .icon-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        animation: gentle-pulse 4s infinite;
      }

      .icon-glow {
        position: absolute;
        width: 110%;
        height: 110%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        animation: soft-glow-pulse 3s infinite alternate;
      }

      .el-icon {
        font-size: 2rem;
        color: white;
        z-index: 3;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
      }
    }

    .header-text {
      flex: 1;
      color: #1e293b;

      .page-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;

        .title-main {
          background: linear-gradient(135deg, #1e293b, #475569);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .title-accent {
          background: linear-gradient(135deg, #667eea, #764ba2);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-size: 0.8em;
        }
      }

      .page-description {
        font-size: 0.9rem;
        color: #64748b;
        margin: 0;
        line-height: 1.5;
        font-weight: 500;
      }

      .title-underline {
        width: 40px;
        height: 2px;
        background: linear-gradient(90deg, #667eea, transparent);
        margin-top: 0.5rem;
        border-radius: 1px;
      }
    }
  }
}

@keyframes subtle-glow {
  0% {
    opacity: 0.3;
  }
  100% {
    opacity: 0.6;
  }
}

@keyframes gentle-pulse {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.02);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.8;
  }
}

@keyframes soft-glow-pulse {
  0% {
    opacity: 0.3;
    transform: scale(1);
  }
  100% {
    opacity: 0.6;
    transform: scale(1.05);
  }
}

// 选项卡容器
.tabs-container {
  position: relative;
  z-index: 10;
  margin: 0 1rem 1rem 1rem;

  :deep(.modern-tabs) {
    .el-tabs__header {
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(20px);
      border-radius: 12px;
      padding: 0.3rem;
      border: 1px solid rgba(102, 126, 234, 0.1);
      margin: 0;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);

      .el-tabs__nav-wrap {
        &::after {
          display: none;
        }
      }

      .el-tabs__item {
        color: #64748b;
        border: none;
        background: transparent;
        border-radius: 8px;
        margin: 0 0.2rem;
        transition: all 0.3s ease;
        font-weight: 500;

        &.is-active {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
          font-weight: 600;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        &:hover:not(.is-active) {
          background: rgba(102, 126, 234, 0.08);
          color: #667eea;
        }

        .tab-label {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.4rem 0.8rem;

          .tab-icon {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 6px;
            transition: all 0.3s ease;

            .el-icon {
              font-size: 1rem;
            }
          }

          .tab-text {
            font-weight: inherit;
            transition: all 0.3s ease;
            font-size: 0.9rem;
          }
        }

        &.is-active {
          .tab-label {
            .tab-icon {
              background: rgba(255, 255, 255, 0.2);
              transform: scale(1.05);
            }
          }
        }
      }
    }
  }
}

// 卡片通用样式
.filter-card,
.data-card {
  position: relative;
  z-index: 10;
  margin: 0 1rem 1rem 1rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(102, 126, 234, 0.08);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border-color: rgba(102, 126, 234, 0.15);
  }

  .card-glow {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      rgba(102, 126, 234, 0.02) 0%,
      rgba(118, 75, 162, 0.02) 100%
    );
    border-radius: 16px;
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }

  &:hover .card-glow {
    opacity: 1;
  }

  :deep(.el-card__body) {
    padding: 1rem;
    position: relative;
    z-index: 2;
  }
}

// 筛选卡片
.filter-card {
  .filter-header {
    .filter-title {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      margin-bottom: 1rem;

      .title-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);

        .el-icon {
          font-size: 1.2rem;
          color: white;
        }
      }

      .title-content {
        h3 {
          font-size: 1.1rem;
          font-weight: 700;
          color: #1e293b;
          margin: 0 0 0.1rem 0;
        }

        p {
          font-size: 0.8rem;
          color: #64748b;
          margin: 0;
          opacity: 0.9;
        }
      }
    }
  }

  .filter-content {
    .filter-row {
      display: flex;
      align-items: end;
      gap: 1rem;
      flex-wrap: wrap;

      .filter-item {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        min-width: 160px;

        .filter-label {
          font-size: 0.85rem;
          font-weight: 600;
          color: #1e293b;
          display: flex;
          align-items: center;
          gap: 0.4rem;
          margin-bottom: 0.4rem;

          .el-icon {
            color: #667eea;
            font-size: 0.9rem;
          }
        }

        .filter-input {
          width: 100%;

          &.modern-input {
            :deep(.el-input__wrapper) {
              border-radius: 10px;
              border: 1.5px solid #e2e8f0;
              transition: all 0.3s ease;
              box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);

              &:hover {
                border-color: #667eea;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.08);
              }

              &.is-focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.08);
              }
            }
          }
        }
      }

      .filter-actions {
        display: flex;
        gap: 0.6rem;

        .modern-btn {
          border-radius: 8px;
          font-weight: 600;
          padding: 8px 16px;
          display: flex;
          align-items: center;
          gap: 0.3rem;
          transition: all 0.3s ease;
          border: none;
          font-size: 0.9rem;

          .el-icon {
            font-size: 1rem;
          }

          span {
            font-weight: 600;
          }
        }

        .clear-btn {
          background: linear-gradient(135deg, #f8fafc, #e2e8f0);
          color: #64748b;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

          &:hover {
            background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            color: #475569;
          }
        }

        .search-btn {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
          box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);

          &:hover {
            background: linear-gradient(135deg, #5a67d8, #6b46c1);
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
          }
        }
      }
    }
  }
}

// 数据卡片
.data-card {
  .data-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #e2e8f0;

    .data-title {
      display: flex;
      align-items: center;
      gap: 0.6rem;

      .title-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #10b981, #059669);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);

        .el-icon {
          font-size: 1.2rem;
          color: white;
        }
      }

      .title-content {
        h3 {
          font-size: 1.1rem;
          font-weight: 700;
          color: #1e293b;
          margin: 0 0 0.1rem 0;
        }

        p {
          font-size: 0.8rem;
          color: #64748b;
          margin: 0;
          opacity: 0.9;
        }
      }
    }

    .data-actions {
      display: flex;
      gap: 0.6rem;

      .select-all-btn {
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        color: #1d4ed8;
        border: 1.5px solid #93c5fd;
        padding: 6px 12px;
        font-size: 0.85rem;
        border-radius: 8px;

        &:hover {
          background: linear-gradient(135deg, #bfdbfe, #93c5fd);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(29, 78, 216, 0.2);
        }
      }

      .deselect-all-btn {
        background: linear-gradient(135deg, #fef2f2, #fecaca);
        color: #dc2626;
        border: 1.5px solid #fca5a5;
        padding: 6px 12px;
        font-size: 0.85rem;
        border-radius: 8px;

        &:hover {
          background: linear-gradient(135deg, #fecaca, #fca5a5);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
        }
      }

      .carryover-btn {
        background: linear-gradient(135deg, #10b981, #059669);
        border: none;
        box-shadow: 0 2px 12px rgba(16, 185, 129, 0.3);
        color: white;
        padding: 8px 16px;
        font-size: 0.9rem;
        border-radius: 8px;

        &:hover:not(:disabled) {
          background: linear-gradient(135deg, #059669, #047857);
          transform: translateY(-1px);
          box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
        }

        &:disabled {
          background: linear-gradient(135deg, #f8fafc, #e2e8f0);
          color: #94a3b8;
          box-shadow: none;
          transform: none;
        }
      }
    }
  }

  .table-container {
    :deep(.modern-table) {
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);

      .el-table__header {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);

        th {
          background: transparent !important;
          color: #1e293b;
          font-weight: 700;
          font-size: 0.85rem;
          padding: 0.6rem 0.5rem;
          border-bottom: 1.5px solid #e2e8f0;

          .table-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;

            .header-left {
              display: flex;
              align-items: center;
              gap: 0.5rem;

              .el-icon {
                color: #667eea;
                font-size: 1rem;
              }

              span {
                font-weight: 700;
              }
            }

            .header-right {
              display: flex;
              align-items: center;

              .sort-icon {
                color: #9ca3af;
                font-size: 0.8rem;
                cursor: pointer;
                transition: all 0.3s ease;

                &:hover {
                  color: #667eea;
                  transform: scale(1.1);
                }

                &.sort-active {
                  color: #667eea;
                }

                &.sort-asc {
                  color: #10b981;
                  transform: rotate(180deg);
                }

                &.sort-desc {
                  color: #ef4444;
                }
              }
            }
          }

          .table-header-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 6px;
            margin: 0 auto;

            .el-icon {
              color: white;
              font-size: 0.9rem;
            }
          }
        }
      }

      .el-table__body {
        tr {
          transition: all 0.3s ease;

          &:hover > td {
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe) !important;
            transform: scale(1.005);
          }

          td {
            padding: 0.6rem 0.5rem;
            border-bottom: 1px solid #f1f5f9;
            transition: all 0.3s ease;

            .product-code {
              font-family: 'Monaco', 'Menlo', monospace;
              font-weight: 600;
              color: #1e40af;
              background: linear-gradient(135deg, #dbeafe, #bfdbfe);
              padding: 0.15rem 0.3rem;
              border-radius: 4px;
              font-size: 0.75rem;
            }

            .product-name {
              font-weight: 500;
              color: #1e293b;
              font-size: 0.9rem;
            }

            .item-tag {
              font-weight: 600;
              border-radius: 6px;
              padding: 0.15rem 0.4rem;
              font-size: 0.8rem;
            }

            .quantity-value {
              font-weight: 700;
              color: #059669;
              font-size: 1rem;
              background: linear-gradient(135deg, #d1fae5, #a7f3d0);
              padding: 0.3rem 0.5rem;
              border-radius: 5px;
              display: inline-block;
            }

            .unit-value {
              font-weight: 600;
              color: #64748b;
              background: #f1f5f9;
              padding: 0.15rem 0.3rem;
              border-radius: 4px;
              font-size: 0.8rem;
            }

            .location-tag {
              font-weight: 600;
              border-radius: 6px;
              padding: 0.15rem 0.4rem;
              font-size: 0.8rem;
            }
          }
        }
      }
    }
  }
}

// 空状态
.empty-state {
  position: relative;
  z-index: 10;
  margin: 1.5rem 1rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 2rem 1.5rem;
  border: 1px solid rgba(102, 126, 234, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  text-align: center;

  .empty-icon {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);

    .el-icon {
      font-size: 2rem;
      color: #94a3b8;
    }
  }

  .empty-description {
    h3 {
      font-size: 1.2rem;
      font-weight: 700;
      color: #1e293b;
      margin: 0 0 0.5rem 0;
    }

    p {
      font-size: 0.9rem;
      color: #64748b;
      margin: 0;
      opacity: 0.9;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .page-header {
    padding: 1rem;

    .header-content {
      flex-direction: column;
      text-align: center;
      gap: 1rem;

      .header-icon {
        width: 60px;
        height: 60px;

        .el-icon {
          font-size: 2rem;
        }
      }

      .header-text {
        .page-title {
          font-size: 2rem;
        }

        .page-description {
          font-size: 1rem;
        }
      }
    }
  }

  .filter-card,
  .data-card {
    margin: 0 1rem 1rem 1rem;

    :deep(.el-card__body) {
      padding: 1.5rem;
    }
  }

  .filter-content .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;

    .filter-item {
      min-width: auto;
    }

    .filter-actions {
      justify-content: center;
    }
  }

  .data-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;

    .data-actions {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
}
</style>
