<template>
  <div class="inventory-carryover-management">
    <div class="dynamic-background" aria-hidden="true">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="floating-particles">
        <div class="particle" v-for="i in 8" :key="i" :style="getParticleStyle(i)"></div>
      </div>
      <div class="grid-overlay"></div>
    </div>

    <div class="page-shell">
      <header class="page-header">
        <div class="header-main">
          <div class="header-icon">
            <el-icon><Share /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="page-title">
              <span class="title-main">棚卸データ繰越管理</span>
              <span class="title-badge">機能</span>
            </h1>
            <p class="page-description">
              特定月・工程の月末棚卸を翌月の期初在庫へ繰越
            </p>
          </div>
        </div>
      </header>

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

    <div v-if="activeTab === 'carryover'" class="carryover-content">
      <el-card class="filter-card" shadow="never">
        <div class="filter-toolbar">
          <div class="filter-toolbar__label">
            <el-icon><ZoomIn /></el-icon>
            <span>検索条件</span>
          </div>
          <div class="filter-toolbar__fields">
            <div class="filter-field">
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
                class="filter-control modern-input"
                clearable
                size="default"
              />
            </div>
            <div class="filter-field">
              <label class="filter-label">
                <el-icon><Setting /></el-icon>
                工程
              </label>
              <el-select
                v-model="filterParams.process_cd"
                placeholder="工程を選択"
                class="filter-control modern-input"
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
          </div>
          <div class="filter-toolbar__actions">
            <el-button @click="clearFilters" class="btn-ghost">
              <el-icon><Refresh /></el-icon>
              クリア
            </el-button>
            <el-button type="primary" @click="handleSearch" class="btn-primary" :loading="loading">
              <el-icon><Search /></el-icon>
              検索
            </el-button>
          </div>
        </div>
      </el-card>

      <el-card class="data-card" shadow="never" v-if="inventoryData.length > 0">
        <div class="data-header">
          <div class="data-title">
            <div class="data-title__icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="data-title__text">
              <h3>棚卸データ</h3>
              <span class="data-count">{{ inventoryData.length }} 件</span>
            </div>
          </div>
          <div class="data-actions">
            <el-button @click="selectAll" class="btn-ghost" size="small">
              <el-icon><Check /></el-icon>
              全選択
            </el-button>
            <el-button @click="deselectAll" class="btn-ghost" size="small">
              <el-icon><Close /></el-icon>
              全解除
            </el-button>
            <el-button
              type="primary"
              @click="handleCarryover"
              :disabled="selectedData.length === 0"
              :loading="carryoverLoading"
              class="btn-carryover"
              size="small"
            >
              <el-icon><Share /></el-icon>
              繰越 ({{ selectedData.length }})
            </el-button>
          </div>
        </div>

        <div class="table-container">
          <el-table
            :data="inventoryData"
            v-loading="loading"
            stripe
            size="small"
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
        :image-size="72"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
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
const getParticleStyle = (_index: number) => {
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
  --icm-accent: #4f46e5;
  --icm-accent2: #7c3aed;
  --icm-surface: rgba(255, 255, 255, 0.92);
  --icm-border: rgba(15, 23, 42, 0.08);
  --icm-text: #0f172a;
  --icm-muted: #64748b;
  --icm-radius: 10px;

  position: relative;
  min-height: 100%;
  background: linear-gradient(160deg, #f1f5f9 0%, #e8eef5 45%, #f8fafc 100%);
  overflow-x: hidden;
}

.dynamic-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;

  .gradient-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(48px);
    opacity: 0.45;
    animation: icm-float 22s ease-in-out infinite;

    &.orb-1 {
      width: 220px;
      height: 220px;
      top: -8%;
      left: -6%;
      background: radial-gradient(circle, rgba(79, 70, 229, 0.12), transparent 70%);
    }

    &.orb-2 {
      width: 160px;
      height: 160px;
      top: 35%;
      right: -4%;
      animation-delay: -7s;
      background: radial-gradient(circle, rgba(124, 58, 237, 0.1), transparent 70%);
    }

    &.orb-3 {
      width: 120px;
      height: 120px;
      bottom: -4%;
      left: 35%;
      animation-delay: -12s;
      background: radial-gradient(circle, rgba(14, 165, 233, 0.08), transparent 70%);
    }
  }

  .floating-particles .particle {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(79, 70, 229, 0.12), transparent);
    animation: icm-drift 18s ease-in-out infinite;
  }

  .grid-overlay {
    position: absolute;
    inset: 0;
    opacity: 0.35;
    background-image:
      linear-gradient(rgba(15, 23, 42, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(15, 23, 42, 0.04) 1px, transparent 1px);
    background-size: 24px 24px;
    mask-image: linear-gradient(180deg, black 0%, transparent 85%);
  }
}

@keyframes icm-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(8px, -12px) scale(1.03);
  }
}

@keyframes icm-drift {
  0%,
  100% {
    transform: translate(0, 0);
    opacity: 0.35;
  }
  50% {
    transform: translate(6px, -10px);
    opacity: 0.55;
  }
}

.page-shell {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0.5rem 0.75rem 0.75rem;
}

.page-header {
  margin-bottom: 0.5rem;

  .header-main {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.45rem 0.65rem;
    background: var(--icm-surface);
    backdrop-filter: blur(12px);
    border: 1px solid var(--icm-border);
    border-radius: var(--icm-radius);
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  }

  .header-icon {
    flex-shrink: 0;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 9px;
    background: linear-gradient(135deg, var(--icm-accent), var(--icm-accent2));
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);

    .el-icon {
      font-size: 1.15rem;
      color: #fff;
    }
  }

  .header-text {
    min-width: 0;
    flex: 1;
  }

  .page-title {
    margin: 0;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.35rem;
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--icm-text);
    line-height: 1.25;
  }

  .title-badge {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    background: rgba(79, 70, 229, 0.1);
    color: var(--icm-accent);
    vertical-align: middle;
  }

  .page-description {
    margin: 0.15rem 0 0;
    font-size: 0.75rem;
    color: var(--icm-muted);
    line-height: 1.35;
  }
}

.tabs-container {
  margin-bottom: 0.45rem;

  :deep(.modern-tabs) {
    .el-tabs__header {
      margin: 0;
      background: var(--icm-surface);
      backdrop-filter: blur(12px);
      border: 1px solid var(--icm-border);
      border-radius: var(--icm-radius);
      padding: 0.2rem;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .el-tabs__nav-wrap::after {
      display: none;
    }

    .el-tabs__item {
      border-radius: 7px;
      margin: 0 0.1rem;
      padding: 0 0.35rem !important;
      height: 34px;
      line-height: 34px;
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--icm-muted);
      transition:
        color 0.15s ease,
        background 0.15s ease;

      &.is-active {
        color: #fff;
        font-weight: 600;
        background: linear-gradient(135deg, var(--icm-accent), var(--icm-accent2));
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.22);
      }

      &:hover:not(.is-active) {
        color: var(--icm-accent);
        background: rgba(79, 70, 229, 0.06);
      }

      .tab-label {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0 0.4rem;
      }

      .tab-icon {
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 5px;
        background: rgba(79, 70, 229, 0.1);

        .el-icon {
          font-size: 0.85rem;
        }
      }

      &.is-active .tab-icon {
        background: rgba(255, 255, 255, 0.22);
      }
    }

    .tab-text {
      font-size: 0.8rem;
    }
  }
}

.carryover-content,
.history-content {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.filter-card,
.data-card {
  position: relative;
  z-index: 1;
  background: var(--icm-surface);
  backdrop-filter: blur(12px);
  border: 1px solid var(--icm-border);
  border-radius: var(--icm-radius);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
  }

  :deep(.el-card__body) {
    padding: 0.55rem 0.65rem;
  }
}

.filter-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.5rem 0.75rem;

  &__label {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    flex-shrink: 0;
    padding: 0.25rem 0;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--icm-text);
    letter-spacing: 0.02em;

    .el-icon {
      font-size: 1rem;
      color: var(--icm-accent);
    }
  }

  &__fields {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 0.5rem 0.75rem;
    flex: 1;
    min-width: 0;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    flex-shrink: 0;
  }
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 140px;
  flex: 1 1 160px;

  .filter-label {
    margin: 0;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--icm-muted);
    display: flex;
    align-items: center;
    gap: 0.25rem;

    .el-icon {
      font-size: 0.8rem;
      color: var(--icm-accent);
    }
  }

  .filter-control {
    width: 100%;
  }
}

.modern-input {
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    min-height: 34px;
    box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.1) inset;

    &:hover {
      box-shadow: 0 0 0 1px rgba(79, 70, 229, 0.35) inset;
    }

    &.is-focus {
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) inset;
    }
  }

  :deep(.el-select__wrapper) {
    border-radius: 8px;
    min-height: 34px;
    box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.1) inset;

    &:hover {
      box-shadow: 0 0 0 1px rgba(79, 70, 229, 0.35) inset;
    }

    &.is-focused {
      box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) inset;
    }
  }
}

.btn-ghost {
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.8rem;
  padding: 7px 12px;
  border: 1px solid var(--icm-border);
  background: #fff;
  color: var(--icm-muted);

  &:hover {
    color: var(--icm-accent);
    border-color: rgba(79, 70, 229, 0.25);
    background: rgba(79, 70, 229, 0.04);
  }
}

.btn-primary {
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.8rem;
  padding: 7px 14px;
  border: none;
  background: linear-gradient(135deg, var(--icm-accent), var(--icm-accent2));
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);

  &:hover {
    filter: brightness(1.05);
  }
}

.data-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  margin-bottom: 0.45rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.data-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;

  &__icon {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: linear-gradient(135deg, #059669, #0d9488);
    box-shadow: 0 2px 6px rgba(5, 150, 105, 0.25);

    .el-icon {
      font-size: 1rem;
      color: #fff;
    }
  }

  &__text {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 0.35rem;

    h3 {
      margin: 0;
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--icm-text);
    }
  }

  .data-count {
    font-size: 0.72rem;
    font-weight: 600;
    color: #fff;
    background: rgba(15, 23, 42, 0.75);
    padding: 0.12rem 0.45rem;
    border-radius: 999px;
  }
}

.data-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  align-items: center;
}

.btn-carryover {
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.78rem;
  padding: 6px 12px;
  border: none;
  background: linear-gradient(135deg, #059669, #047857);
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.28);

  &:hover:not(:disabled) {
    filter: brightness(1.06);
  }

  &:disabled {
    background: #e2e8f0;
    color: #94a3b8;
    box-shadow: none;
  }
}

.table-container {
  margin: 0 -0.15rem;

  :deep(.modern-table) {
    --el-table-header-bg-color: #f8fafc;
    --el-table-row-hover-bg-color: #f0fdf4;

    border-radius: 8px;
    overflow: hidden;
    font-size: 0.78rem;

    .el-table__header th {
      padding: 6px 4px !important;
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--icm-text);
      border-bottom: 1px solid rgba(15, 23, 42, 0.08) !important;
    }

    .el-table__body td {
      padding: 5px 4px !important;
      border-bottom: 1px solid rgba(15, 23, 42, 0.05) !important;
    }

    tr:hover > td {
      transform: none;
    }

    .table-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.25rem;
      width: 100%;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 0.3rem;
      min-width: 0;

      .el-icon {
        flex-shrink: 0;
        font-size: 0.85rem;
        color: var(--icm-accent);
      }

      span {
        font-weight: 700;
        font-size: 0.72rem;
      }
    }

    .sort-icon {
      flex-shrink: 0;
      font-size: 0.75rem;
      color: #94a3b8;
      cursor: pointer;
      transition: color 0.15s ease;

      &:hover {
        color: var(--icm-accent);
      }

      &.sort-active {
        color: var(--icm-accent);
      }

      &.sort-asc {
        color: #059669;
      }

      &.sort-desc {
        color: #dc2626;
      }
    }

    .table-header-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      margin: 0 auto;
      border-radius: 5px;
      background: linear-gradient(135deg, var(--icm-accent), var(--icm-accent2));

      .el-icon {
        color: #fff;
        font-size: 0.75rem;
      }
    }

    .product-code {
      font-family: ui-monospace, 'Cascadia Code', monospace;
      font-size: 0.72rem;
      font-weight: 600;
      color: #1e40af;
      background: #e0e7ff;
      padding: 0.1rem 0.3rem;
      border-radius: 4px;
    }

    .product-name {
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--icm-text);
      line-height: 1.35;
    }

    .item-tag {
      font-weight: 600;
      border-radius: 4px;
    }

    .quantity-value {
      font-weight: 700;
      font-size: 0.8rem;
      color: #047857;
      background: #d1fae5;
      padding: 0.12rem 0.35rem;
      border-radius: 4px;
      display: inline-block;
    }

    .unit-value {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--icm-muted);
      background: #f1f5f9;
      padding: 0.08rem 0.28rem;
      border-radius: 4px;
    }

    .location-tag {
      font-weight: 600;
      border-radius: 4px;
    }
  }
}

.empty-state {
  position: relative;
  z-index: 1;
  margin: 0;
  padding: 1rem 0.75rem;
  background: var(--icm-surface);
  border: 1px solid var(--icm-border);
  border-radius: var(--icm-radius);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);

  :deep(.el-empty__description) {
    margin-top: 0.35rem;
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    margin: 0 auto 0.35rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: #f1f5f9;

    .el-icon {
      font-size: 1.5rem;
      color: #94a3b8;
    }
  }

  .empty-description {
    h3 {
      margin: 0 0 0.25rem;
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--icm-text);
    }

    p {
      margin: 0;
      font-size: 0.78rem;
      color: var(--icm-muted);
    }
  }
}

@media (max-width: 768px) {
  .page-shell {
    padding: 0.4rem 0.5rem 0.65rem;
  }

  .filter-toolbar {
    flex-direction: column;
    align-items: stretch;

    &__actions {
      justify-content: stretch;

      .el-button {
        flex: 1;
      }
    }
  }

  .filter-field {
    flex: 1 1 100%;
    min-width: 0;
  }

  .data-header {
    flex-direction: column;
    align-items: stretch;
  }

  .data-actions {
    justify-content: stretch;

    .el-button {
      flex: 1;
      min-width: 0;
    }
  }
}
</style>

