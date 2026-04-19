<template>
  <div class="route-step-manager">
    <div class="page-bg" aria-hidden="true">
      <div class="page-bg__gradient" />
      <div class="page-bg__orb page-bg__orb--1" />
      <div class="page-bg__orb page-bg__orb--2" />
    </div>

    <div class="route-step-manager__inner">
      <header class="page-header">
        <div class="header-main">
          <div class="header-icon-wrap">
            <el-icon class="header-icon" :size="22"><Tools /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="main-title">製品ルートマスタ</h1>
            <p class="subtitle">製品を選択し、工程ステップ・設備を設定します</p>
          </div>
        </div>
        <div v-if="selectedProduct" class="header-pill">
          <el-icon :size="14"><Box /></el-icon>
          <span class="header-pill__cd">{{ selectedProduct }}</span>
        </div>
      </header>

      <div class="manager-layout">
        <aside class="left-panel">
          <ProductList @select="selectProduct" />
        </aside>
        <main class="right-panel" v-if="selectedProduct">
          <ProductDetail :product-cd="selectedProduct" />
          <ProductRouteStepTable :product-cd="selectedProduct" />
        </main>
        <main class="right-panel right-panel--empty" v-else>
          <div class="empty-state">
            <div class="empty-state__icon-wrap">
              <el-icon :size="36"><Document /></el-icon>
            </div>
            <p class="empty-state__title">製品を選択してください</p>
            <p class="empty-state__hint">左の一覧から製品を選ぶと、工程ルートを編集できます</p>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Tools, Box, Document } from '@element-plus/icons-vue'
import ProductList from './ProductList.vue'
import ProductDetail from './ProductDetail.vue'
import ProductRouteStepTable from './ProductRouteStepTable.vue'

const selectedProduct = ref<string | null>(null)

const selectProduct = (productCd: string) => {
  selectedProduct.value = productCd
}
</script>

<style scoped>
.route-step-manager {
  position: relative;
  min-height: 100%;
  padding: 6px 8px 10px;
  box-sizing: border-box;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.page-bg__gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(145deg, #eef2ff 0%, #f8fafc 45%, #f1f5f9 100%);
}

.page-bg__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(64px);
  opacity: 0.42;
}

.page-bg__orb--1 {
  width: 280px;
  height: 280px;
  top: -100px;
  right: -20%;
  background: #a5b4fc;
}

.page-bg__orb--2 {
  width: 220px;
  height: 220px;
  bottom: 5%;
  left: -8%;
  background: #c4b5fd;
}

.route-step-manager__inner {
  position: relative;
  z-index: 1;
  max-width: 1920px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow:
    0 2px 8px rgba(102, 126, 234, 0.22),
    0 8px 28px -6px rgba(102, 126, 234, 0.35);
}

.header-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.header-icon-wrap {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.22);
  color: #fff;
}

.header-text {
  min-width: 0;
}

.main-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.subtitle {
  margin: 2px 0 0;
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.88);
  line-height: 1.35;
}

.header-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 600;
  max-width: min(320px, 100%);
}

.header-pill__cd {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.manager-layout {
  display: flex;
  gap: 8px;
  align-items: stretch;
  min-height: calc(100vh - 92px);
}

.left-panel {
  width: 300px;
  min-width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 24px -8px rgba(15, 23, 42, 0.1);
  overflow: hidden;
}

.right-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  border-radius: 10px;
}

.right-panel--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px dashed rgba(148, 163, 184, 0.55);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
}

.empty-state {
  text-align: center;
  max-width: 320px;
  padding: 8px 12px;
}

.empty-state__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  margin-bottom: 10px;
  border-radius: 16px;
  background: linear-gradient(145deg, #eef2ff 0%, #e0e7ff 100%);
  color: #6366f1;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.empty-state__title {
  margin: 0 0 6px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #334155;
}

.empty-state__hint {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #94a3b8;
}

@media (max-width: 1024px) {
  .manager-layout {
    flex-direction: column;
    min-height: auto;
  }

  .left-panel {
    width: 100%;
    min-width: 0;
    min-height: 240px;
    max-height: 42vh;
  }

  .right-panel--empty {
    min-height: 220px;
  }
}

@media (max-width: 640px) {
  .route-step-manager {
    padding: 4px 6px 8px;
  }

  .page-header {
    padding: 8px 12px;
  }

  .main-title {
    font-size: 1.05rem;
  }

  .header-pill {
    width: 100%;
    justify-content: center;
    max-width: none;
  }
}
</style>
