<template>
  <el-row :gutter="20">
    <el-col :span="12">
      <el-card :body-style="{ padding: '20px' }" v-loading="loading">
        <div class="card-title">📈 内示差異ランキング（増加）</div>
        <el-table :data="positiveList" stripe border style="margin-top: 10px" :row-class-name="getRowClass">
          <el-table-column label="順位" width="60" align="center">
            <template #default="{ row }">
              <span v-if="row.rank === 1" style="color: gold; font-weight: bold" title="第1位 🥇">🥇</span>
              <span v-else-if="row.rank === 2" style="color: silver; font-weight: bold" title="第2位 🥈">🥈</span>
              <span v-else-if="row.rank === 3" style="color: #cd7f32; font-weight: bold" title="第3位 🥉">🥉</span>
              <span v-else>{{ row.rank }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品CD" width="100" />
          <el-table-column prop="product_name" label="製品名" min-width="150" />
          <el-table-column label="差異本数" width="100" align="right">
            <template #default="{ row }">
              <span style="color: #67C23A; font-weight: bold">{{ formatNumber(row.diff) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>

    <el-col :span="12">
      <el-card :body-style="{ padding: '20px' }" v-loading="loading">
        <div class="card-title">📉 内示差異ランキング（減少）</div>
        <el-table :data="negativeList" stripe border style="margin-top: 10px" :row-class-name="getRowClass">
          <el-table-column label="順位" width="60" align="center">
            <template #default="{ row }">
              <span v-if="row.rank === 1" style="color: gold; font-weight: bold" title="第1位 🥇">🥇</span>
              <span v-else-if="row.rank === 2" style="color: silver; font-weight: bold" title="第2位 🥈">🥈</span>
              <span v-else-if="row.rank === 3" style="color: #cd7f32; font-weight: bold" title="第3位 🥉">🥉</span>
              <span v-else>{{ row.rank }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品CD" width="100" />
          <el-table-column prop="product_name" label="製品名" min-width="150" />
          <el-table-column label="差異本数" width="100" align="right">
            <template #default="{ row }">
              <span style="color: #F56C6C; font-weight: bold">{{ formatNumber(row.diff) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getForecastDiffRanking } from '@/api/order/order'

const props = defineProps<{ year: number; month: number }>()

interface ForecastDiffRankItem {
  rank: number
  product_cd: string
  product_name: string
  diff: number
}

const positiveList = ref<ForecastDiffRankItem[]>([])
const negativeList = ref<ForecastDiffRankItem[]>([])
const loading = ref(false)

const formatNumber = (val: number | string): string => {
  const num = Number(val)
  return isNaN(num) ? '-' : num.toLocaleString()
}

const fetchData = async () => {
  if (!props.year || !props.month) return
  loading.value = true
  try {
    const { positive, negative } = await getForecastDiffRanking({ year: props.year, month: props.month })
    positiveList.value = positive.map((item, idx) => ({ ...item, rank: idx + 1, diff: Number(item.diff) }))
    negativeList.value = negative.map((item, idx) => ({ ...item, rank: idx + 1, diff: Number(item.diff) }))
  } catch (error) {
    console.error('差異ランキング取得失敗', error)
    positiveList.value = []
    negativeList.value = []
  } finally {
    loading.value = false
  }
}
const getRowClass = (row: { row: ForecastDiffRankItem }) => {
  if (row.row.rank === 1) return 'row-gold'
  if (row.row.rank === 2) return 'row-silver'
  if (row.row.rank === 3) return 'row-bronze'
  return ''
}
watch(() => [props.year, props.month], fetchData, { immediate: true })
</script>

<style scoped>
.card-title {
  font-weight: bold;
  margin-bottom: 10px;
  font-size: 16px;
  color: #2c3e50;
}

.rank-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: bold;
  color: white;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
}

.gold {
  background: linear-gradient(to right, #FFD700, #FFA500);
}

.silver {
  background: linear-gradient(to right, #C0C0C0, #A9A9A9);
}

.bronze {
  background: linear-gradient(to right, #CD7F32, #A0522D);
}

.rank-text {
  font-weight: bold;
  color: #606266;
}

.el-table .el-table__row:hover {
  transform: scale(1.02);
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease-in-out;
  z-index: 1;
}

/* 只对前3名高亮行设背景渐变色 */
.row-gold {
  background: linear-gradient(to right, #fff8dc, #ffe082) !important;
}

.row-silver {
  background: linear-gradient(to right, #f0f0f0, #cccccc) !important;
}

.row-bronze {
  background: linear-gradient(to right, #f9e0c7, #d2b48c) !important;
}
</style>
