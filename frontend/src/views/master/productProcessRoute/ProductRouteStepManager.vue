<template>
  <transition name="fade-slide" mode="out-in">
    <div class="route-step-manager-container" v-if="true">
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <div class="title-row">
              <span class="title-icon">🛠️</span>
              <h1 class="main-title">製品別工程ルートマスタ</h1>
            </div>
            <p class="subtitle">製品を選択し、工程ステップ・設備を設定します</p>
          </div>
        </div>
      </div>

      <div class="manager-layout">
        <div class="left-panel">
          <ProductList @select="selectProduct" />
        </div>
        <div class="right-panel" v-if="selectedProduct">
          <ProductDetail :product-cd="selectedProduct" />
          <ProductRouteStepTable :product-cd="selectedProduct" />
        </div>
        <div class="right-panel empty" v-else>
          <div class="empty-state">
            <span class="empty-icon">📋</span>
            <p>左の製品一覧から製品を選択してください</p>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ProductList from './ProductList.vue'
import ProductDetail from './ProductDetail.vue'
import ProductRouteStepTable from './ProductRouteStepTable.vue'

const selectedProduct = ref<string | null>(null)

const selectProduct = (productCd: string) => {
  selectedProduct.value = productCd
}
</script>

<style scoped>
.route-step-manager-container {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 14px 20px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 1.5rem;
}

.main-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: #fff;
  letter-spacing: 0.5px;
}

.subtitle {
  color: rgba(255, 255, 255, 0.85);
  margin: 4px 0 0;
  font-size: 0.85rem;
}

.manager-layout {
  display: flex;
  gap: 12px;
  min-height: calc(100vh - 120px);
}

.left-panel {
  width: 320px;
  min-width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.right-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}

.right-panel.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.empty-state {
  text-align: center;
  color: #94a3b8;
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 12px;
}

.empty-state p {
  margin: 0;
  font-size: 0.95rem;
}

@media (max-width: 1024px) {
  .manager-layout {
    flex-direction: column;
  }
  .left-panel {
    width: 100%;
    min-height: 280px;
  }
}
</style>
