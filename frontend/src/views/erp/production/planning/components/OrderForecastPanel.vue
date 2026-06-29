<template>
  <div class="fdp-forecast">
    <el-empty v-if="!months.length" :description="t('formingDailyPlan.noForecast')" />
    <div v-for="m in months" :key="`${m.year}-${m.month}`" class="fdp-forecast__block">
      <div class="fdp-forecast__head">
        <h3 class="fdp-forecast__title">{{ m.year }}/{{ String(m.month).padStart(2, '0') }}</h3>
        <el-tag size="small" type="info">{{ sourceLabel(m.source) }}</el-tag>
        <span class="fdp-forecast__total">
          {{ t('formingDailyPlan.forecastTotal') }}: {{ fmtFormingNumber(m.monthly_total.forecast, false) }}
        </span>
      </div>
      <el-table :data="m.daily" stripe border size="small" :max-height="280">
        <el-table-column prop="date" :label="t('formingDailyPlan.colDate')" width="110" />
        <el-table-column prop="weekday" :label="t('formingDailyPlan.colWeekday')" width="56" />
        <el-table-column prop="forecast_units" :label="t('formingDailyPlan.colForecast')" align="right">
          <template #default="{ row }">{{ fmtFormingNumber(row.forecast_units, false) }}</template>
        </el-table-column>
        <el-table-column prop="order_units" :label="t('formingDailyPlan.colOrder')" align="right">
          <template #default="{ row }">{{ fmtFormingNumber(row.order_units, false) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { OrderForecastMonth } from '@/api/formingDailyPlan'
import { fmtFormingNumber } from './formingDailyPlanConstants'

defineProps<{ months: OrderForecastMonth[] }>()

const { t } = useI18n()

function sourceLabel(source: string) {
  const map: Record<string, string> = {
    order_monthly: t('formingDailyPlan.forecastSourceOrderMonthly'),
    historical_avg: t('formingDailyPlan.forecastSourceHistoricalAvg'),
    pattern_only: t('formingDailyPlan.forecastSourcePatternOnly'),
  }
  return map[source] ?? source
}
</script>

<style scoped>
.fdp-forecast__block {
  margin-bottom: 16px;
}
.fdp-forecast__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.fdp-forecast__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.fdp-forecast__total {
  font-size: 12px;
  color: #606266;
  margin-left: auto;
}
</style>
