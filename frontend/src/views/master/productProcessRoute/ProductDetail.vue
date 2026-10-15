<template>
  <section class="pd-panel" v-if="product">
    <header class="pd-panel__head">
      <div class="pd-panel__head-main">
        <span class="pd-panel__icon-wrap">
          <el-icon :size="18"><Goods /></el-icon>
        </span>
        <span class="pd-panel__title">製品情報</span>
        <span class="pd-panel__cd">{{ product.product_cd }}</span>
      </div>
    </header>
    <div class="pd-panel__body">
      <el-descriptions :column="2" size="small" border class="pd-desc">
        <el-descriptions-item label="製品CD">
          <span class="pd-val pd-val--mono">{{ product.product_cd }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="製品名">
          <span class="pd-val">{{ product.product_name }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="工程ルートCD">
          <span class="pd-val pd-val--mono">{{ product.route_cd }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="工程ルート名">
          <span class="pd-val">{{ product.route_name }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="納入先" :span="2">
          <span class="pd-val">{{ product.delivery_destination_name || '—' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Goods } from '@element-plus/icons-vue'
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
  { immediate: true },
)
</script>

<style scoped>
.pd-panel {
  flex-shrink: 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #ddd6fe;
  background: #fff;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 8px 20px -10px rgba(76, 29, 149, 0.2);
}

.pd-panel__head {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(125deg, #5b21b6 0%, #7c3aed 55%, #a78bfa 100%);
}

.pd-panel__head-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  width: 100%;
}

.pd-panel__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #fff;
  flex-shrink: 0;
}

.pd-panel__title {
  font-size: 0.82rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.02em;
}

.pd-panel__cd {
  margin-left: auto;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.pd-panel__body {
  padding: 0;
}

.pd-desc {
  --pd-label-w: 108px;
}

.pd-desc :deep(.el-descriptions__header) {
  display: none;
}

.pd-desc :deep(.el-descriptions__body) {
  background: transparent;
}

.pd-desc :deep(.el-descriptions__label) {
  width: var(--pd-label-w) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #6d28d9 !important;
  background: #faf5ff !important;
  padding: 5px 8px !important;
}

.pd-desc :deep(.el-descriptions__content) {
  font-size: 12px !important;
  padding: 5px 10px !important;
  color: #0f172a !important;
  background: #fff !important;
}

.pd-desc :deep(.el-descriptions__cell) {
  padding-bottom: 0 !important;
  border-color: #ede9fe !important;
}

.pd-val {
  line-height: 1.35;
  word-break: break-word;
}

.pd-val--mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
  color: #6d28d9;
}

@media (max-width: 640px) {
  .pd-desc :deep(.el-descriptions__label) {
    width: 96px !important;
  }
}
</style>
