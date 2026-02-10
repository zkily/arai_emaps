<template>
  <div class="master-home-container">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Folder />
            </el-icon>
            {{ t('masterHome.title') }}
          </h1>
          <p class="subtitle">{{ t('masterHome.subtitle') }}</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ masterModules.length }}</div>
            <div class="stat-label">{{ t('masterHome.statLabel') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- マスタカードグリッド -->
    <div class="master-grid">
      <div
        v-for="module in masterModules"
        :key="module.name"
        class="master-card"
        :style="{ '--card-color': module.color, '--card-gradient': module.gradient }"
        @click="navigateTo(module.path)"
      >
        <div class="card-icon-wrapper">
          <el-icon class="card-icon" :size="32">
            <component :is="module.icon" />
          </el-icon>
        </div>
        <div class="card-content">
          <h3 class="card-title">{{ t(module.titleKey) }}</h3>
          <p class="card-description">{{ t(module.descKey) }}</p>
        </div>
        <div class="card-arrow">
          <el-icon :size="20">
            <ArrowRight />
          </el-icon>
        </div>
        <div class="card-decoration"></div>
      </div>
    </div>

    <!-- クイックアクション -->
    <div class="quick-actions">
      <div class="section-title">
        <el-icon class="section-icon"><Lightning /></el-icon>
        <span>{{ t('masterHome.quickActionTitle') }}</span>
      </div>
      <div class="action-buttons">
        <el-button
          v-for="action in quickActions"
          :key="action.name"
          :type="action.type"
          :icon="action.icon"
          size="large"
          @click="navigateTo(action.path)"
          class="action-btn"
        >
          {{ t(action.labelKey) }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Box,
  Coin,
  User,
  Setting,
  Connection,
  OfficeBuilding,
  Van,
  Position,
  Folder,
  ArrowRight,
  Plus,
  List,
} from '@element-plus/icons-vue'
import { markRaw, h, type Component } from 'vue'

const { t } = useI18n()

// Lightning icon (using h() function to avoid JSX issues)
const Lightning = markRaw({
  name: 'Lightning',
  render() {
    return h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      fill: 'currentColor',
      width: '1em',
      height: '1em'
    }, [
      h('path', { d: 'M13 10V3L4 14h7v7l9-11h-7z' })
    ])
  }
}) as Component

const router = useRouter()

interface MasterModule {
  name: string
  titleKey: string
  descKey: string
  path: string
  icon: Component
  color: string
  gradient: string
}

interface QuickAction {
  name: string
  labelKey: string
  path: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  icon: Component
}

const masterModules: MasterModule[] = [
  {
    name: 'product',
    titleKey: 'masterHome.productTitle',
    descKey: 'masterHome.productDesc',
    path: '/master/product',
    icon: markRaw(Box),
    color: '#409EFF',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    name: 'material',
    titleKey: 'masterHome.materialTitle',
    descKey: 'masterHome.materialDesc',
    path: '/master/material',
    icon: markRaw(Coin),
    color: '#67C23A',
    gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
  },
  {
    name: 'supplier',
    titleKey: 'masterHome.supplierTitle',
    descKey: 'masterHome.supplierDesc',
    path: '/master/supplier',
    icon: markRaw(OfficeBuilding),
    color: '#E6A23C',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
  {
    name: 'process',
    titleKey: 'masterHome.processTitle',
    descKey: 'masterHome.processDesc',
    path: '/master/process',
    icon: markRaw(Setting),
    color: '#909399',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  },
  {
    name: 'processRoute',
    titleKey: 'masterHome.processRouteTitle',
    descKey: 'masterHome.processRouteDesc',
    path: '/master/process-route',
    icon: markRaw(Connection),
    color: '#F56C6C',
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  },
  {
    name: 'productProcessRoute',
    titleKey: 'masterHome.productProcessRouteTitle',
    descKey: 'masterHome.productProcessRouteDesc',
    path: '/master/product-process-route',
    icon: markRaw(Setting),
    color: '#909399',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  },
  {
    name: 'customer',
    titleKey: 'masterHome.customerTitle',
    descKey: 'masterHome.customerDesc',
    path: '/master/customer',
    icon: markRaw(User),
    color: '#409EFF',
    gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  },
  {
    name: 'carrier',
    titleKey: 'masterHome.carrierTitle',
    descKey: 'masterHome.carrierDesc',
    path: '/master/carrier',
    icon: markRaw(Van),
    color: '#67C23A',
    gradient: 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',
  },
  {
    name: 'machine',
    titleKey: 'masterHome.machineTitle',
    descKey: 'masterHome.machineDesc',
    path: '/master/machine',
    icon: markRaw(Setting),
    color: '#E6A23C',
    gradient: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
  },
  {
    name: 'destination',
    titleKey: 'masterHome.destinationTitle',
    descKey: 'masterHome.destinationDesc',
    path: '/master/destination',
    icon: markRaw(Position),
    color: '#F56C6C',
    gradient: 'linear-gradient(135deg, #fddb92 0%, #d1fdff 100%)',
  },
  {
    name: 'bom',
    titleKey: 'masterHome.bomTitle',
    descKey: 'masterHome.bomDesc',
    path: '/master/bom',
    icon: markRaw(List),
    color: '#909399',
    gradient: 'linear-gradient(135deg, #c1dfc4 0%, #deecdd 100%)',
  },
]

const quickActions: QuickAction[] = [
  {
    name: 'addProduct',
    labelKey: 'masterHome.addProduct',
    path: '/master/product',
    type: 'primary',
    icon: markRaw(Plus),
  },
  {
    name: 'addMaterial',
    labelKey: 'masterHome.addMaterial',
    path: '/master/material',
    type: 'success',
    icon: markRaw(Plus),
  },
  {
    name: 'addSupplier',
    labelKey: 'masterHome.addSupplier',
    path: '/master/supplier',
    type: 'warning',
    icon: markRaw(Plus),
  },
]

const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
.master-home-container {
  padding: 16px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

/* ページヘッダー */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-icon {
  font-size: 36px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.subtitle {
  margin: 4px 0 0 48px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 12px;
  padding: 12px 24px;
  text-align: center;
  min-width: 100px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.25);
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 2px;
}

/* マスタカードグリッド */
.master-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.master-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.master-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.master-card:hover .card-decoration {
  opacity: 1;
  transform: translateX(0);
}

.master-card:hover .card-arrow {
  transform: translateX(4px);
  opacity: 1;
}

.master-card:hover .card-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.card-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--card-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.card-icon {
  color: #fff;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-description {
  font-size: 13px;
  color: #909399;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-arrow {
  color: #c0c4cc;
  transition: all 0.3s ease;
  opacity: 0.5;
}

.card-decoration {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100%;
  background: var(--card-gradient);
  opacity: 0.08;
  transform: translateX(20px) skewX(-15deg);
  transition: all 0.3s ease;
}

/* クイックアクション */
.quick-actions {
  background: #fff;
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 20px;
  color: #e6a23c;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .master-home-container {
    padding: 12px;
  }

  .page-header {
    padding: 20px;
    border-radius: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .main-title {
    font-size: 22px;
    justify-content: center;
  }

  .subtitle {
    margin-left: 0;
  }

  .master-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .master-card {
    padding: 16px;
    border-radius: 12px;
  }

  .card-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }

  .quick-actions {
    padding: 16px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
  }
}
</style>
