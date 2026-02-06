<!-- ✅ src/views/master/ProductRouteStepManager.vue -->
<template>
  <div class="route-step-manager">
    <!-- 左側：製品一覧 -->
    <div class="left-panel">
      <ProductList @select="selectProduct" />
    </div>

    <!-- 右側：製品情報 + 工程ステップ -->
    <div class="right-panel" v-if="selectedProduct">
      <ProductDetail :productCd="selectedProduct" />
      <ProductRouteStepTable :productCd="selectedProduct" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ProductList from './ProductList.vue'
import ProductDetail from './ProductDetail.vue'
import ProductRouteStepTable from './ProductRouteStepTable.vue'

// ✅ 左側で選択された製品CD
const selectedProduct = ref<string | null>(null)

// ✅ 製品選択イベント
const selectProduct = (productCd: string) => {
  selectedProduct.value = productCd
}
</script>

<style scoped>
.route-step-manager {
  display: flex;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.left-panel {
  width: 30%;
  min-width: 250px;
  height: 100%;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}

.right-panel {
  width: 70%;
  padding: 15px;
  overflow-y: auto;
}
</style>
