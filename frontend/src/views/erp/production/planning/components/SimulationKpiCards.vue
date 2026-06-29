<template>
  <section class="fdp-kpi" aria-label="KPI">
    <div class="fdp-kpi__card fdp-kpi__card--plan">
      <div class="fdp-kpi__accent" />
      <span class="fdp-kpi__label">{{ t('formingDailyPlan.kpiMoldingTotal') }}</span>
      <span class="fdp-kpi__value">{{ fmt(kpi?.total_molding_plan) }}</span>
    </div>
    <div class="fdp-kpi__card fdp-kpi__card--min">
      <div class="fdp-kpi__accent" />
      <span class="fdp-kpi__label">{{ t('formingDailyPlan.kpiMinWarehouse') }}</span>
      <span class="fdp-kpi__value" :class="{ 'is-danger': (kpi?.min_warehouse_inventory ?? 0) < 0 }">
        {{ fmt(kpi?.min_warehouse_inventory) }}
      </span>
    </div>
    <div class="fdp-kpi__card fdp-kpi__card--neg">
      <div class="fdp-kpi__accent" />
      <span class="fdp-kpi__label">{{ t('formingDailyPlan.kpiNegDays') }}</span>
      <span class="fdp-kpi__value" :class="{ 'is-warn': (kpi?.negative_warehouse_days ?? 0) > 0 }">
        {{ kpi?.negative_warehouse_days ?? 0 }}
      </span>
    </div>
    <div class="fdp-kpi__card fdp-kpi__card--products">
      <div class="fdp-kpi__accent" />
      <span class="fdp-kpi__label">{{ t('formingDailyPlan.kpiProducts') }}</span>
      <span class="fdp-kpi__value">{{ kpi?.product_count ?? 0 }}</span>
    </div>
    <div v-if="scenarioStatus" class="fdp-kpi__card fdp-kpi__card--status">
      <div class="fdp-kpi__accent" />
      <span class="fdp-kpi__label">{{ t('formingDailyPlan.scenarioStatus') }}</span>
      <span class="fdp-kpi__value fdp-kpi__value--sm">{{ scenarioStatus }}</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { FormingPlanKpi } from '@/api/formingDailyPlan'
import { fmtFormingNumber } from './formingDailyPlanConstants'

defineProps<{
  kpi?: FormingPlanKpi | null
  scenarioStatus?: string
}>()

const { t } = useI18n()

function fmt(v?: number | null) {
  return fmtFormingNumber(v, false)
}
</script>

<style scoped>
.fdp-kpi {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 6px;
  margin-bottom: 8px;
}
.fdp-kpi__card {
  position: relative;
  padding: 6px 10px 7px;
  border-radius: 8px;
  border: 1px solid #e8ecf4;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.fdp-kpi__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}
.fdp-kpi__card--plan .fdp-kpi__accent { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.fdp-kpi__card--min .fdp-kpi__accent { background: linear-gradient(90deg, #0ea5e9, #06b6d4); }
.fdp-kpi__card--neg .fdp-kpi__accent { background: linear-gradient(90deg, #f59e0b, #f97316); }
.fdp-kpi__card--products .fdp-kpi__accent { background: linear-gradient(90deg, #10b981, #34d399); }
.fdp-kpi__card--status .fdp-kpi__accent { background: linear-gradient(90deg, #64748b, #94a3b8); }
.fdp-kpi__label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.02em;
  margin-top: 2px;
}
.fdp-kpi__value {
  display: block;
  font-size: 17px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  line-height: 1.2;
  margin-top: 1px;
}
.fdp-kpi__value--sm {
  font-size: 13px;
  font-weight: 600;
}
.fdp-kpi__value.is-danger {
  color: #ef4444;
}
.fdp-kpi__value.is-warn {
  color: #ea580c;
}
</style>
