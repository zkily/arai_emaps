<template>
  <el-row :gutter="15" class="summary-row">
    <el-col :xs="12" :sm="8" :md="4" v-for="(card, index) in cards" :key="index">
      <el-card class="summary-card">
        <div class="summary-title">{{ card.title }}</div>
        <div class="summary-value">{{ card.value }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface KpiSummary {
  total_amount?: number
  total_quantity?: number
  customer_count?: number
  product_count?: number
  destination_count?: number
  shipping_delay_rate?: number
}

const props = defineProps<{ summary: KpiSummary }>()

const cards = computed(() => [
  { title: '総受注金額', value: props.summary.total_amount ?? 0 },
  { title: '総受注数量', value: props.summary.total_quantity ?? 0 },
  { title: '顧客数', value: props.summary.customer_count ?? 0 },
  { title: '製品数', value: props.summary.product_count ?? 0 },
  { title: '納入先数', value: props.summary.destination_count ?? 0 },
  { title: '出荷遅延率', value: (props.summary.shipping_delay_rate ?? 0) + '%' }
])
</script>

<style scoped>
.summary-row {
  margin-bottom: 15px;
}

.summary-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  text-align: center;
  padding: 20px 10px;
}

.summary-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 22px;
  font-weight: bold;
  color: #409EFF;
}
</style>
