<template>
  <div class="modern-kpi-dashboard">
    <!-- 现代化页面头部 -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon>
              <TrendCharts />
            </el-icon>
          </div>
          <div class="title-text">
            <h1 class="page-title">受注KPIダッシュボード</h1>
            <p class="page-subtitle">リアルタイム受注データ分析・パフォーマンス監視</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button class="refresh-btn" @click="loadKpiData" :loading="loading">
            <el-icon>
              <Refresh />
            </el-icon>
            更新
          </el-button>
        </div>
      </div>

      <!-- 装饰元素 -->
      <div class="header-decoration">
        <div class="floating-shape shape-1"></div>
        <div class="floating-shape shape-2"></div>
        <div class="floating-shape shape-3"></div>
      </div>
    </div>

    <!-- 筛选器区域 -->
    <div class="filters-section">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <Filter />
          </el-icon>
          <span>フィルター設定</span>
        </div>
      </div>
      <KpiFilters v-model="filters" @search="loadKpiData" />
    </div>

    <!-- 摘要卡片区域 -->
    <div class="summary-section">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <DataAnalysis />
          </el-icon>
          <span>サマリー指標</span>
        </div>
        <div class="section-badge">
          <span class="badge-text">リアルタイム</span>
        </div>
      </div>
      <KpiSummaryCards :summary="summaryData" />
    </div>

    <!-- 错误信息显示 -->
    <div v-if="errorMessage" class="error-section">
      <el-alert :title="errorMessage" type="error" show-icon :closable="true" class="modern-error-alert" />
    </div>

    <!-- 趋势图表区域 -->
    <div class="charts-section trend-charts">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <TrendCharts />
          </el-icon>
          <span>トレンド分析</span>
        </div>
        <div class="section-badge">
          <span class="badge-text">月次推移</span>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon class="chart-icon">
                <Money />
              </el-icon>
              <span>月別受注金額</span>
            </div>
            <div class="chart-value" v-if="amountData.length > 0">
              ¥{{ amountData[amountData.length - 1]?.toLocaleString() || 0 }}
            </div>
          </div>
          <div class="chart-container">
            <LineChart :labels="amountLabels" :data="amountData" label="受注金額 (¥)" />
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon class="chart-icon">
                <Box />
              </el-icon>
              <span>月別受注数量</span>
            </div>
            <div class="chart-value" v-if="quantityData.length > 0">
              {{ quantityData[quantityData.length - 1]?.toLocaleString() || 0 }}個
            </div>
          </div>
          <div class="chart-container">
            <LineChart :labels="quantityLabels" :data="quantityData" label="受注明細数量" />
          </div>
        </div>
      </div>
    </div>

    <!-- TOP10 排名区域 -->
    <div class="charts-section ranking-charts">
      <div class="section-header">
        <div class="section-title">
          <el-icon class="section-icon">
            <Trophy />
          </el-icon>
          <span>TOP10ランキング</span>
        </div>
        <div class="section-badge">
          <span class="badge-text">パフォーマンス</span>
        </div>
      </div>

      <div class="charts-grid ranking-grid">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon class="chart-icon">
                <User />
              </el-icon>
              <span>顧客TOP10</span>
            </div>
            <div class="chart-stats">
              <span class="stats-count">{{ customerLabels.length }}</span>
              <span class="stats-label">顧客</span>
            </div>
          </div>
          <div class="chart-container">
            <BarChart :labels="customerLabels" :data="customerData" label="受注明細数量" />
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon class="chart-icon">
                <OfficeBuilding />
              </el-icon>
              <span>納入先TOP10</span>
            </div>
            <div class="chart-stats">
              <span class="stats-count">{{ destinationLabels.length }}</span>
              <span class="stats-label">納入先</span>
            </div>
          </div>
          <div class="chart-container">
            <BarChart :labels="destinationLabels" :data="destinationData" label="受注明細数量" />
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon class="chart-icon">
                <Goods />
              </el-icon>
              <span>製品TOP10</span>
            </div>
            <div class="chart-stats">
              <span class="stats-count">{{ productLabels.length }}</span>
              <span class="stats-label">製品</span>
            </div>
          </div>
          <div class="chart-container">
            <BarChart :labels="productLabels" :data="productData" label="受注明細数量" />
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon class="chart-icon">
                <PriceTag />
              </el-icon>
              <span>平均単価推移</span>
            </div>
            <div class="chart-stats">
              <span class="stats-label">単価分析</span>
            </div>
          </div>
          <div class="chart-container">
            <AverageUnitPriceChart ref="avgPriceChart" />
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <el-loading :fullscreen="true" :visible="loading" element-loading-text="データ読み込み中..."
      element-loading-background="rgba(0, 0, 0, 0.8)" />
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  Refresh,
  Filter,
  DataAnalysis,
  Money,
  Box,
  Trophy,
  User,
  OfficeBuilding,
  Goods,
  PriceTag,
} from '@element-plus/icons-vue'
import LineChart from '@/views/erp/order/components/LineChart.vue'
import BarChart from '@/views/erp/order/components/BarChart.vue'
import KpiFilters from '@/views/erp/order/components/KpiFilters.vue'
import KpiSummaryCards from '@/views/erp/order/components/KpiSummaryCards.vue'
import AverageUnitPriceChart from '@/views/erp/order/components/AverageUnitPriceChart.vue'

const filters = ref({
  customer_cd: '',
  product_cd: '',
  destination_cd: '',
  date_range: undefined as [string, string] | undefined,
})

const loading = ref(false)
const errorMessage = ref<string>('')

// 添加类型定义确保与KpiSummaryCards接口一致
interface KpiSummary {
  total_amount?: number
  total_quantity?: number
  customer_count?: number
  product_count?: number
  destination_count?: number
  shipping_delay_rate?: number
}

const summaryData = ref<KpiSummary>({})
const amountLabels = ref<string[]>([])
const amountData = ref<number[]>([])
const quantityLabels = ref<string[]>([])
const quantityData = ref<number[]>([])
const customerLabels = ref<string[]>([])
const customerData = ref<number[]>([])
const destinationLabels = ref<string[]>([])
const destinationData = ref<number[]>([])
const productLabels = ref<string[]>([])
const productData = ref<number[]>([])

const avgPriceChart = ref()

// 辅助函数：处理API返回数据
const processApiResponse = <T,>(response: any, keyName: keyof T, defaultValue: T[] = []): T[] => {
  if (Array.isArray(response)) {
    return response as T[]
  } else if (response && Array.isArray(response.data)) {
    return response.data as T[]
  } else if (response && response.success && Array.isArray(response.data)) {
    return response.data as T[]
  }
  return defaultValue
}

const loadKpiData = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const [start_date, end_date] = filters.value.date_range ?? [undefined, undefined]
    const params = {
      customer_cd: filters.value.customer_cd,
      product_cd: filters.value.product_cd,
      destination_cd: filters.value.destination_cd,
      start_date,
      end_date,
    }

    // 获取摘要数据
    const summary = await request.get('/api/order/summary', { params })
    if (summary) {
      // 确保所有数值字段都是数字类型
      summaryData.value = {
        total_amount: typeof summary.total_amount === 'number' ? summary.total_amount : 0,
        total_quantity: typeof summary.total_quantity === 'number' ? summary.total_quantity : 0,
        customer_count: typeof summary.customer_count === 'number' ? summary.customer_count : 0,
        product_count: typeof summary.product_count === 'number' ? summary.product_count : 0,
        destination_count:
          typeof summary.destination_count === 'number' ? summary.destination_count : 0,
        shipping_delay_rate:
          typeof summary.shipping_delay_rate === 'number' ? summary.shipping_delay_rate : 0,
      }
    } else {
      // 重置为默认值
      summaryData.value = {
        total_amount: 0,
        total_quantity: 0,
        customer_count: 0,
        product_count: 0,
        destination_count: 0,
        shipping_delay_rate: 0,
      }
    }

    // 月度金额趋势
    const amount = await request.get('/api/order/order-amount-trend', { params })
    const amountList = processApiResponse<{ ym: string; total_amount?: number }>(amount, 'ym')
    amountLabels.value = amountList.map((x) => x.ym)
    amountData.value = amountList.map((x) => Number(x.total_amount ?? 0))

    // 月度数量趋势
    const quantity = await request.get('/api/order/order-quantity-trend', { params })
    const quantityList = processApiResponse<{ ym: string; total_quantity?: number }>(quantity, 'ym')
    quantityLabels.value = quantityList.map((x) => x.ym)
    quantityData.value = quantityList.map((x) => Number(x.total_quantity ?? 0))

    // 客户TOP10
    const customer = await request.get('/api/order/customer-top10', { params })
    const customerList = processApiResponse<{ customer_name: string; total_quantity?: number }>(
      customer,
      'customer_name',
    )
    customerLabels.value = customerList.map((x) => x.customer_name)
    customerData.value = customerList.map((x) => Number(x.total_quantity ?? 0))

    // 纳入先TOP10
    const destination = await request.get('/api/order/destination-top10', { params })
    const destinationList = processApiResponse<{
      destination_name: string
      destination_cd: string
      total_quantity?: number
    }>(destination, 'destination_name')
    destinationLabels.value = destinationList.map(
      (x) => `${x.destination_name}(${x.destination_cd})`,
    )
    destinationData.value = destinationList.map((x) => Number(x.total_quantity ?? 0))

    // 产品TOP10
    const product = await request.get('/api/order/product-top10', { params })
    const productList = processApiResponse<{ product_name: string; total_quantity?: number }>(
      product,
      'product_name',
    )
    productLabels.value = productList.map((x) => x.product_name)
    productData.value = productList.map((x) => Number(x.total_quantity ?? 0))

    // 平均单价趋势
    const avgPrice = await request.get('/api/order/average-unit-price-trend', { params })
    if (avgPriceChart.value) {
      const avgPriceData = processApiResponse<{ ym: string; avg_unit_price?: number }>(
        avgPrice,
        'ym',
      )
      avgPriceChart.value.setData(avgPriceData)
    }
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : 'KPIデータ取得中にエラーが発生しました'
    console.error('KPI取得エラー:', errorMsg)
    errorMessage.value = errorMsg
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

watch(
  filters,
  () => {
    loadKpiData()
  },
  { deep: true },
)

onMounted(() => loadKpiData())
</script>

<style scoped>
/* 页面容器 */
.modern-kpi-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  background-image:
    radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(16, 185, 129, 0.03) 0%, transparent 50%);
  background-attachment: fixed;
  position: relative;
  overflow-x: hidden;
}

/* SVG网格背景 */
.modern-kpi-dashboard::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(102, 126, 234, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(102, 126, 234, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  z-index: 0;
}

/* 仪表盘头部 */
.dashboard-header {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px 24px;
  margin-bottom: 16px;
  overflow: hidden;
  z-index: 1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 2;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  animation: float 4s ease-in-out infinite;
}

.title-icon .el-icon {
  font-size: 24px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }

  50% {
    transform: translateY(-10px) rotate(2deg);
  }
}

.title-text {
  color: white;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 900;
  margin: 0 0 6px 0;
  background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  letter-spacing: -0.03em;
}

.page-subtitle {
  font-size: 0.875rem;
  margin: 0;
  opacity: 0.95;
  font-weight: 500;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-actions {
  display: flex;
  gap: 16px;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 10px 20px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  font-weight: 700;
  font-size: 0.875rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-3px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.2);
}

.refresh-btn .el-icon {
  font-size: 16px;
  animation: spin 2s linear infinite paused;
}

.refresh-btn:hover .el-icon {
  animation-play-state: running;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

/* 装饰元素 */
.header-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.shape-1 {
  width: 160px;
  height: 160px;
  top: -80px;
  right: 8%;
  animation: rotate 12s linear infinite;
}

.shape-2 {
  width: 100px;
  height: 100px;
  bottom: -50px;
  left: 12%;
  animation: rotate 15s linear infinite reverse;
}

.shape-3 {
  width: 60px;
  height: 60px;
  top: 20%;
  right: 20%;
  animation: rotate 8s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

/* 区域样式 */
.filters-section,
.summary-section,
.charts-section {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 20px;
  margin: 0 20px 16px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.1),
    0 10px 20px -5px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 1;
  animation: slideInUp 0.8s ease-out;
}

.filters-section {
  padding: 12px 20px;
  animation-delay: 0.1s;
}

.summary-section {
  animation-delay: 0.2s;
}

.charts-section {
  animation-delay: 0.3s;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 区域头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
  position: relative;
}

.filters-section .section-header {
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.section-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.15rem;
  font-weight: 800;
  color: #1f2937;
}

.section-icon {
  font-size: 18px;
  color: #667eea;
  animation: pulse 3s infinite;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.section-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.section-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: shine 3s infinite;
}

@keyframes shine {
  0% {
    left: -100%;
  }

  100% {
    left: 100%;
  }
}

.badge-text {
  position: relative;
  z-index: 1;
}

/* 图表网格 */
.charts-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
}

.ranking-grid {
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
}

/* 图表卡片 */
.chart-card {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.4s ease;
  position: relative;
  overflow: hidden;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #10b981 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.chart-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.chart-card:hover::before {
  opacity: 1;
}

/* 图表头部 */
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
}

.chart-icon {
  font-size: 16px;
  color: #667eea;
  padding: 6px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.chart-card:hover .chart-icon {
  background: rgba(102, 126, 234, 0.2);
  transform: scale(1.1);
}

.chart-value {
  font-size: 1.1rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.chart-stats {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stats-count {
  font-size: 1.3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stats-label {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 600;
}

/* 图表容器 */
.chart-container {
  min-height: 250px;
  position: relative;
}

/* 错误区域 */
.error-section {
  margin: 0 20px 16px;
  animation: slideInUp 0.6s ease-out;
}

.modern-error-alert {
  border-radius: 16px;
  border: 1px solid rgba(239, 68, 68, 0.2);
  background: rgba(254, 242, 242, 0.95);
  backdrop-filter: blur(10px);
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .ranking-grid {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  }
}

@media (max-width: 1200px) {
  .dashboard-header {
    padding: 20px 20px;
  }

  .filters-section,
  .summary-section,
  .charts-section {
    margin: 0 16px 12px;
    padding: 16px;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .charts-grid,
  .ranking-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .modern-kpi-dashboard {
    background-attachment: local;
  }

  .dashboard-header {
    padding: 16px 16px;
    margin-bottom: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .title-section {
    gap: 12px;
  }

  .title-icon {
    width: 48px;
    height: 48px;
  }

  .title-icon .el-icon {
    font-size: 20px;
  }

  .page-title {
    font-size: 1.35rem;
  }

  .page-subtitle {
    font-size: 0.8rem;
  }

  .filters-section,
  .summary-section,
  .charts-section {
    margin: 0 12px 12px;
    padding: 16px;
    border-radius: 16px;
  }

  .chart-card {
    padding: 12px;
  }

  .section-title {
    font-size: 1rem;
  }

  .floating-shape {
    display: none;
  }
}

@media (max-width: 480px) {
  .dashboard-header {
    padding: 12px 12px;
  }

  .filters-section,
  .summary-section,
  .charts-section {
    margin: 0 8px 10px;
    padding: 12px;
  }

  .page-title {
    font-size: 1.15rem;
  }

  .title-section {
    gap: 10px;
  }

  .title-icon {
    width: 40px;
    height: 40px;
  }

  .title-icon .el-icon {
    font-size: 18px;
  }

  .chart-card {
    padding: 12px;
  }

  .chart-container {
    min-height: 220px;
  }
}

/* 暗黑模式支持 */
@media (prefers-color-scheme: dark) {
  .modern-kpi-dashboard {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  }

  .filters-section,
  .summary-section,
  .charts-section {
    background: rgba(31, 41, 55, 0.95);
    border-color: rgba(75, 85, 99, 0.5);
  }

  .chart-card {
    background: rgba(31, 41, 55, 0.8);
    border-color: rgba(75, 85, 99, 0.3);
  }

  .section-title,
  .chart-title {
    color: #f9fafb;
  }

  .section-header {
    border-bottom-color: rgba(75, 85, 99, 0.3);
  }

  .stats-label {
    color: #9ca3af;
  }
}

/* 性能优化 */
.chart-card,
.section-badge,
.refresh-btn {
  will-change: transform;
}

.floating-shape {
  will-change: transform;
}
</style>
