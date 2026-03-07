<template>
  <div class="product-detail-card" v-if="product">
    <div class="page-header compact">
      <div class="header-content">
        <span class="title-icon">🏷️</span>
        <h2 class="sub-title">製品情報</h2>
      </div>
    </div>
    <el-descriptions :column="2" border class="detail-desc">
      <el-descriptions-item label="製品CD">{{ product.product_cd }}</el-descriptions-item>
      <el-descriptions-item label="製品名">{{ product.product_name }}</el-descriptions-item>
      <el-descriptions-item label="工程ルートCD">{{ product.route_cd }}</el-descriptions-item>
      <el-descriptions-item label="工程ルート名">{{ product.route_name }}</el-descriptions-item>
      <el-descriptions-item label="納入先" :span="2">{{ product.delivery_destination_name }}</el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import request from '@/shared/api/request'

const props = defineProps<{ productCd: string }>()

interface ProductInfo {
  product_cd: string
  product_name: string
  route_cd: string
  route_name: string
  delivery_destination_name: string
}

const product = ref<ProductInfo | null>(null)

watch(
  () => props.productCd,
  async (val) => {
    if (val) {
      const res = await request.get(`/api/master/product/process/routes/${encodeURIComponent(val)}`)
      product.value = res?.data ?? res ?? null
    } else {
      product.value = null
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.product-detail-card {
  margin-bottom: 12px;
}

.page-header.compact {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
}

.header-content {
  display: flex;
  align-items: center;
}

.sub-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
}

.title-icon {
  margin-right: 6px;
}

.detail-desc {
  border-radius: 8px;
  overflow: hidden;
}
</style>
