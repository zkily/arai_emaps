<template>
  <div class="order-daily-print-page">
    <!-- 打印标题 -->
    <div class="print-header">
      <h1>📄 日別出荷履歴（印刷用）</h1>
      <div class="print-date">発行日: {{ today }}</div>
    </div>

    <!-- 按納入先分组显示 -->
    <div v-for="group in groupedOrders" :key="group.destination_cd" class="destination-group">
      <div class="group-header">
        <h2>{{ group.destination_name }} ({{ group.destination_cd }})</h2>
      </div>

      <!-- 按日期分组显示 -->
      <div v-for="dateGroup in group.dateGroups" :key="dateGroup.date" class="date-group">
        <h3>{{ dateGroup.date }}</h3>

        <el-table :data="dateGroup.orders" border stripe class="print-table">
          <el-table-column label="製品CD" prop="product_cd" min-width="100" />
          <el-table-column label="製品名" prop="product_name" min-width="150" />
          <el-table-column label="確定箱数" prop="confirmed_boxes" align="right" width="100" />
          <el-table-column label="確定本数" prop="confirmed_units" align="right" width="100" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { fetchDailyOrders } from '@/api/order/order'
import type { OrderDaily, FetchDailyOrdersParams } from '@/types/order'

// 今日の日付
const today = new Date().toLocaleDateString('ja-JP', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit'
})

// 列表数据
const orderList = ref<OrderDaily[]>([])

// 按納入先和日期分组的数据
const groupedOrders = computed(() => {
  // 首先按年月日和产品名称排序
  const sortedList = [...orderList.value].sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year
    if (a.month !== b.month) return a.month - b.month
    if (a.day !== b.day) return a.day - b.day
    return a.product_name.localeCompare(b.product_name, 'ja')
  })

  // 按納入先分组
  const destinationGroups = new Map<string, {
    destination_cd: string;
    destination_name: string;
    orders: OrderDaily[];
  }>()

  sortedList.forEach((order: OrderDaily) => {
    const destinationKey = order.destination_cd
    if (!destinationGroups.has(destinationKey)) {
      destinationGroups.set(destinationKey, {
        destination_cd: order.destination_cd,
        destination_name: order.destination_name,
        orders: []
      })
    }
    destinationGroups.get(destinationKey)!.orders.push(order)
  })

  // 处理每个納入先组内的日期分组
  return Array.from(destinationGroups.values()).map(group => {
    const dateGroups = new Map<string, {
      date: string;
      orders: OrderDaily[];
    }>()

    group.orders.forEach((order: OrderDaily) => {
      const dateKey = `${order.year}年${order.month}月${order.day}日`
      if (!dateGroups.has(dateKey)) {
        dateGroups.set(dateKey, {
          date: dateKey,
          orders: []
        })
      }
      dateGroups.get(dateKey)!.orders.push(order)
    })

    return {
      ...group,
      dateGroups: Array.from(dateGroups.values())
    }
  })
})

// 页面加载后：读取数据并自动打开打印
onMounted(async () => {
  const params: FetchDailyOrdersParams = {
    page: 1,
    pageSize: 1000, // 只取前1000条用于打印
    year: 0
  }
  const res = await fetchDailyOrders(params)
  orderList.value = res?.list ?? []

  // 打印对话框
  setTimeout(() => {
    window.print()
  }, 1000)
})
</script>

<style scoped>
.order-daily-print-page {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.print-header {
  text-align: center;
  margin-bottom: 30px;
  border-bottom: 2px solid #666;
  padding-bottom: 20px;
}

.print-header h1 {
  font-size: 24px;
  margin-bottom: 15px;
  color: #333;
}

.print-date {
  font-size: 14px;
  color: #666;
}

.destination-group {
  margin-bottom: 40px;
  break-inside: avoid;
}

.group-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ddd;
}

.group-header h2 {
  font-size: 18px;
  color: #333;
  margin: 0;
}

.date-group {
  margin-bottom: 30px;
  break-inside: avoid;
}

.date-group h3 {
  font-size: 16px;
  color: #666;
  margin-bottom: 15px;
}

.print-table {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

:deep(.el-table) {
  margin-bottom: 30px;
}

:deep(.el-table th) {
  background-color: #f5f7fa !important;
  color: #333;
  font-weight: 600;
}

@media print {
  .order-daily-print-page {
    padding: 0;
  }

  .print-header {
    margin-bottom: 20px;
    padding-bottom: 15px;
  }

  .print-header h1 {
    font-size: 20px;
    margin-bottom: 10px;
  }

  .print-date {
    font-size: 12px;
  }

  .destination-group {
    margin-bottom: 30px;
    page-break-inside: avoid;
  }

  .group-header h2 {
    font-size: 16px;
  }

  .date-group {
    margin-bottom: 20px;
    page-break-inside: avoid;
  }

  .date-group h3 {
    font-size: 14px;
    margin-bottom: 10px;
  }

  :deep(.el-table) {
    border: 1px solid #dcdfe6;
  }

  :deep(.el-table th),
  :deep(.el-table td) {
    font-size: 11px;
    padding: 6px 4px;
  }

  :deep(.el-table th) {
    background-color: #f5f7fa !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
</style>
