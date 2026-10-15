<template>
  <div class="route-step-manager prr-modern pb-std">
    <div class="page-ambient" aria-hidden="true" />

    <div class="route-step-manager__inner">
      <header class="page-header page-toolbar pb-hero pb-hero--page">
        <div class="page-toolbar-glow" aria-hidden="true" />
        <div class="page-header-fx pb-bubbles" aria-hidden="true" />
        <div class="header-main">
          <div class="header-icon-wrap">
            <el-icon class="header-icon" :size="22"><Tools /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="main-title pb-hero-title">製品ルートマスタ</h1>
            <p class="subtitle pb-hero-desc">製品を選択し、工程ステップ・設備を設定します</p>
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
        <main v-if="selectedProduct" class="right-panel">
          <ProductDetail :product-cd="selectedProduct" />
          <ProductRouteStepTable class="right-panel__steps" :product-cd="selectedProduct" />
        </main>
        <main v-else class="right-panel right-panel--empty">
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
  --prr-app-chrome: 84px;
  position: relative;
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  height: calc(100vh - var(--prr-app-chrome));
  height: calc(100dvh - var(--prr-app-chrome));
  max-height: calc(100vh - var(--prr-app-chrome));
  max-height: calc(100dvh - var(--prr-app-chrome));
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.page-ambient {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(1100px 380px at 0% 0%, rgba(109, 40, 217, 0.1), transparent 60%),
    radial-gradient(900px 380px at 100% 0%, rgba(167, 139, 250, 0.08), transparent 60%),
    linear-gradient(160deg, #f5f3ff 0%, #f8fafc 45%, #faf5ff 100%);
}

.route-step-manager__inner {
  position: relative;
  z-index: 1;
  width: 100%;
  box-sizing: border-box;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.page-header {
  flex-shrink: 0;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #4c1d95 0%, #6d28d9 34%, #8b5cf6 66%, #c4b5fd 100%);
  box-shadow:
    0 18px 36px -18px rgba(76, 29, 149, 0.55),
    0 4px 12px -6px rgba(139, 92, 246, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  z-index: 0;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
  pointer-events: none;
}

.page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.header-main,
.header-pill {
  position: relative;
  z-index: 1;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.header-icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(76, 29, 149, 0.3);
}

.header-text {
  min-width: 0;
}

.main-title {
  margin: 0;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.02em;
}

.subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.88);
}

.header-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
  max-width: min(320px, 100%);
}

.header-pill__cd {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.manager-layout {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.left-panel {
  width: 300px;
  min-width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #ddd6fe;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  position: relative;
}

.left-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 3;
  pointer-events: none;
  background: linear-gradient(90deg, #4c1d95 0%, #8b5cf6 55%, #c4b5fd 100%);
}

.right-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.right-panel__steps {
  flex: 1 1 auto;
  min-height: 0;
}

.right-panel--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 1px dashed #c4b5fd;
  background:
    radial-gradient(420px 220px at 50% 38%, rgba(139, 92, 246, 0.08), transparent 70%),
    #fff;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.06);
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
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: linear-gradient(145deg, #8b5cf6 0%, #6d28d9 55%, #4c1d95 100%);
  box-shadow: 0 8px 20px -8px rgba(109, 40, 217, 0.55);
}

.empty-state__title {
  margin: 0 0 6px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #4c1d95;
}

.empty-state__hint {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #94a3b8;
}

@media (max-width: 1024px) {
  .route-step-manager {
    height: auto;
    max-height: none;
    overflow: auto;
  }

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

  .right-panel {
    min-height: 420px;
  }
}

@media (max-width: 640px) {
  .route-step-manager {
    padding: 8px;
  }

  .header-pill {
    width: 100%;
    justify-content: center;
    max-width: none;
  }
}
</style>
