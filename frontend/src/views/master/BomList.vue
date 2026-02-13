<template>
  <div class="bom-home-container">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Connection />
            </el-icon>
            {{ t('bomHome.title') }}
          </h1>
          <p class="subtitle">{{ t('bomHome.subtitle') }}</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ bomModules.length }}</div>
            <div class="stat-label">{{ t('bomHome.statLabel') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- BOMカードグリッド -->
    <div class="bom-grid">
      <div
        v-for="module in bomModules"
        :key="module.name"
        class="bom-card"
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
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Connection, Tools, ArrowRight, Setting } from '@element-plus/icons-vue'
import { markRaw, type Component } from 'vue'

const { t } = useI18n()
const router = useRouter()

interface BomModule {
  name: string
  titleKey: string
  descKey: string
  path: string
  icon: Component
  color: string
  gradient: string
}

const bomModules: BomModule[] = [
  {
    name: 'productProcessBom',
    titleKey: 'bomHome.productProcessBomTitle',
    descKey: 'bomHome.productProcessBomDesc',
    path: '/master/bom/product-process',
    icon: markRaw(Tools),
    color: '#409EFF',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    name: 'productMachineConfig',
    titleKey: 'bomHome.productMachineConfigTitle',
    descKey: 'bomHome.productMachineConfigDesc',
    path: '/master/bom/product-machine-config',
    icon: markRaw(Setting),
    color: '#67C23A',
    gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
  },
  {
    name: 'equipmentEfficiency',
    titleKey: 'bomHome.equipmentEfficiencyTitle',
    descKey: 'bomHome.equipmentEfficiencyDesc',
    path: '/master/bom/equipment-efficiency',
    icon: markRaw(Tools),
    color: '#E6A23C',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
]

const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
.bom-home-container {
  padding: 16px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

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

.bom-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.bom-card {
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

.bom-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.bom-card:hover .card-decoration {
  opacity: 1;
  transform: translateX(0);
}

.bom-card:hover .card-arrow {
  transform: translateX(4px);
  opacity: 1;
}

.bom-card:hover .card-icon-wrapper {
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

@media (max-width: 768px) {
  .bom-home-container {
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

  .bom-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .bom-card {
    padding: 16px;
    border-radius: 12px;
  }

  .card-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }
}
</style>
