<template>
  <div class="kpi-page">
    <div class="page-bg" aria-hidden="true"></div>

    <header class="page-header glass">
      <div class="header-inner">
        <div class="header-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="header-title">{{ t('shipping.inventoryKpi.title') }}</h1>
          <p class="header-desc">{{ t('shipping.inventoryKpi.desc') }}</p>
        </div>
        <el-button
          type="primary"
          :icon="Printer"
          size="small"
          class="header-print-btn"
          :disabled="!printListLength"
          @click="handlePrint"
        >
          {{ t('shipping.print') }}
        </el-button>
      </div>
    </header>

    <section ref="sectionMainRef" class="section-main glass">
      <div class="tabs-bar">
        <button
          v-for="(tab, idx) in tabs"
          :key="tab.name"
          type="button"
          class="tab-btn"
          :class="{ active: activeTab === tab.name }"
          :style="{ '--tab-i': idx }"
          @click="activeTab = tab.name"
        >
          <span class="tab-label">{{ tab.label }}</span>
          <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <div class="tab-panels">
        <Transition name="tab-fade" mode="out-in">
          <div :key="activeTab" class="tab-panel">
            <!-- Turnover -->
            <template v-if="activeTab === 'turnover'">
              <div class="filter-row">
                <el-form inline class="filter-form">
                  <el-form-item :label="t('shipping.inventoryKpi.period')" class="compact">
                    <el-date-picker
                      v-model="turnoverDateRange"
                      type="daterange"
                      range-separator="～"
                      value-format="YYYY-MM-DD"
                      size="small"
                      class="input-sm"
                      :editable="!isTouchDevice"
                    />
                    <span class="period-shortcuts">
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setTurnoverPeriod('prevMonth')">
                        {{ t('shipping.inventoryKpi.prevMonth') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setTurnoverPeriod('currentMonth')">
                        {{ t('shipping.inventoryKpi.currentMonth') }}
                      </el-button>
                    </span>
                  </el-form-item>
                  <el-form-item :label="t('shipping.inventoryKpi.byAmount')" class="compact">
                    <el-switch v-model="turnoverByAmount" size="small" />
                  </el-form-item>
                  <el-button type="primary" size="small" :loading="loading.turnover" class="btn-query" @click="fetchTurnover">
                    {{ t('common.query') }}
                  </el-button>
                </el-form>
              </div>
              <div class="table-wrap glass-inner">
                <el-table :data="turnoverList" stripe size="small" max-height="380" v-loading="loading.turnover" class="kpi-table kpi-table--numeric">
                  <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip sortable />
                  <el-table-column prop="product_name" label="製品名" width="130" show-overflow-tooltip sortable />
                  <el-table-column prop="period_forecast" label="期間需要" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.period_forecast ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="opening_inventory" label="月初" width="72" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.opening_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="closing_inventory" label="月末" width="72" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.closing_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="avg_inventory" label="平均在庫" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.avg_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="turnover" label="回転率" width="90" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ row.turnover != null ? row.turnover.toFixed(2) : '—' }}</span></template>
                  </el-table-column>
                  <el-table-column prop="turnover_days" label="回転日数" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ row.turnover_days != null ? row.turnover_days.toFixed(1) : '—' }}</span></template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- Avg Days -->
            <template v-else-if="activeTab === 'avgDays'">
              <div class="filter-row">
                <el-form inline class="filter-form">
                  <el-form-item :label="t('shipping.inventoryKpi.asOfDate')" class="compact">
                    <el-date-picker v-model="avgDaysAsOf" type="date" value-format="YYYY-MM-DD" size="small" class="input-sm" :editable="!isTouchDevice" />
                    <span class="period-shortcuts">
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setAvgDaysAsOf(-1)">
                        {{ t('shipping.inventoryKpi.prevDay') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setAvgDaysAsOf(0)">
                        {{ t('shipping.inventoryKpi.today') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setAvgDaysAsOf(1)">
                        {{ t('shipping.inventoryKpi.nextDay') }}
                      </el-button>
                    </span>
                  </el-form-item>
                  <el-form-item :label="t('shipping.inventoryKpi.recentDays')" class="compact">
                    <el-select v-model="avgDaysRecent" size="small" class="input-sm" :teleported="true">
                      <el-option :label="30" :value="30" />
                      <el-option :label="60" :value="60" />
                      <el-option :label="90" :value="90" />
                    </el-select>
                  </el-form-item>
                  <el-button type="primary" size="small" :loading="loading.avgDays" class="btn-query" @click="fetchAvgDays">{{ t('common.query') }}</el-button>
                </el-form>
              </div>
              <div class="table-wrap glass-inner">
                <el-table :data="avgDaysList" stripe size="small" max-height="380" v-loading="loading.avgDays" class="kpi-table kpi-table--numeric">
                  <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip sortable />
                  <el-table-column prop="product_name" label="製品名" width="130" show-overflow-tooltip sortable />
                  <el-table-column prop="current_inventory" label="現在在庫" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.current_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="avg_daily_demand" label="1日平均" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.avg_daily_demand ?? 0).toFixed(2) }}</span></template>
                  </el-table-column>
                  <el-table-column prop="avg_inventory_days" label="平均在庫日数" width="120" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ row.avg_inventory_days != null ? row.avg_inventory_days.toFixed(1) + ' 日' : '—' }}</span></template>
                  </el-table-column>
                  <el-table-column :label="t('shipping.inventoryKpi.monthsEquivalent')" width="100" align="right" sortable :sort-method="(a: any, b: any) => ((a.avg_inventory_days ?? 0) / 22) - ((b.avg_inventory_days ?? 0) / 22)">
                    <template #default="{ row }"><span class="cell-num">{{ row.avg_inventory_days != null ? (row.avg_inventory_days / 22).toFixed(1) : '—' }}</span></template>
                  </el-table-column>
                  <el-table-column prop="latest_date" label="基準日" width="98" align="center" sortable />
                </el-table>
              </div>
            </template>

            <!-- Shortage -->
            <template v-else-if="activeTab === 'shortage'">
              <div class="filter-row">
                <el-form inline class="filter-form">
                  <el-form-item :label="t('shipping.inventoryKpi.asOfDate')" class="compact">
                    <el-date-picker v-model="shortageAsOf" type="date" value-format="YYYY-MM-DD" size="small" class="input-sm" :editable="!isTouchDevice" />
                    <span class="period-shortcuts">
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setShortageAsOf(-1)">
                        {{ t('shipping.inventoryKpi.prevDay') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setShortageAsOf(0)">
                        {{ t('shipping.inventoryKpi.today') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setShortageAsOf(1)">
                        {{ t('shipping.inventoryKpi.nextDay') }}
                      </el-button>
                    </span>
                  </el-form-item>
                  <el-form-item :label="t('shipping.inventoryKpi.recentDays')" class="compact">
                    <el-select v-model="shortageRecent" size="small" class="input-sm" :teleported="true">
                      <el-option :label="30" :value="30" />
                      <el-option :label="60" :value="60" />
                      <el-option :label="90" :value="90" />
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="t('shipping.inventoryKpi.safetyMarginDays')" class="compact">
                    <el-input-number v-model="safetyMarginDays" :min="0" :max="30" size="small" controls-position="right" class="input-num" :readonly="isTouchDevice" />
                  </el-form-item>
                  <el-button type="primary" size="small" :loading="loading.shortage" class="btn-query" @click="fetchShortage">{{ t('common.query') }}</el-button>
                </el-form>
              </div>
              <div class="table-wrap glass-inner">
                <el-table :data="shortageList" stripe size="small" max-height="380" v-loading="loading.shortage" class="kpi-table kpi-table--numeric">
                  <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip sortable />
                  <el-table-column prop="product_name" label="製品名" width="130" show-overflow-tooltip sortable />
                  <el-table-column prop="current_inventory" label="現在在庫" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.current_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="avg_inventory_days" label="平均日数" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ row.avg_inventory_days != null ? row.avg_inventory_days.toFixed(1) + ' 日' : '—' }}</span></template>
                  </el-table-column>
                  <el-table-column prop="lead_time" label="リード" width="90" align="right" sortable />
                  <el-table-column prop="threshold_days" label="閾値(日)" width="100" align="right" sortable />
                </el-table>
              </div>
            </template>

            <!-- Overstock -->
            <template v-else-if="activeTab === 'overstock'">
              <div class="filter-row">
                <el-form inline class="filter-form">
                  <el-form-item :label="t('shipping.inventoryKpi.asOfDate')" class="compact">
                    <el-date-picker v-model="overstockAsOf" type="date" value-format="YYYY-MM-DD" size="small" class="input-sm" :editable="!isTouchDevice" />
                    <span class="period-shortcuts">
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setOverstockAsOf(-1)">
                        {{ t('shipping.inventoryKpi.prevDay') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setOverstockAsOf(0)">
                        {{ t('shipping.inventoryKpi.today') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setOverstockAsOf(1)">
                        {{ t('shipping.inventoryKpi.nextDay') }}
                      </el-button>
                    </span>
                  </el-form-item>
                  <el-form-item :label="t('shipping.inventoryKpi.maxTurnoverDays')" class="compact">
                    <el-input-number v-model="maxTurnoverDays" :min="1" :max="365" size="small" controls-position="right" class="input-num" :readonly="isTouchDevice" />
                  </el-form-item>
                  <el-form-item :label="t('shipping.inventoryKpi.daysSinceShip')" class="compact">
                    <el-input-number v-model="daysSinceShip" :min="1" :max="365" size="small" controls-position="right" class="input-num" :readonly="isTouchDevice" />
                  </el-form-item>
                  <el-button type="primary" size="small" :loading="loading.overstock" class="btn-query" @click="fetchOverstock">{{ t('common.query') }}</el-button>
                </el-form>
              </div>
              <div class="table-wrap glass-inner">
                <el-table :data="overstockList" stripe size="small" max-height="380" v-loading="loading.overstock" class="kpi-table kpi-table--numeric">
                  <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip sortable />
                  <el-table-column prop="product_name" label="製品名" width="130" show-overflow-tooltip sortable />
                  <el-table-column prop="current_inventory" label="現在在庫" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.current_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="turnover_days" label="回転日数" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ row.turnover_days != null ? row.turnover_days.toFixed(1) : '—' }}</span></template>
                  </el-table-column>
                  <el-table-column prop="last_ship_date" label="最終出荷" width="100" sortable />
                  <el-table-column prop="days_since_ship" label="経過日" width="90" align="right" sortable />
                  <el-table-column label="判定" width="120" align="center">
                    <template #default="{ row }">
                      <span class="cell-tags">
                        <el-tag v-if="row.over_by_turnover" type="warning" size="small" effect="plain" class="cell-tag">回転</el-tag>
                        <el-tag v-if="row.over_by_ship" type="info" size="small" effect="plain" class="cell-tag">長期未出荷</el-tag>
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- Reorder -->
            <template v-else>
              <div class="filter-row">
                <el-form inline class="filter-form">
                  <el-form-item :label="t('shipping.inventoryKpi.asOfDate')" class="compact">
                    <el-date-picker v-model="reorderAsOf" type="date" value-format="YYYY-MM-DD" size="small" class="input-sm" :editable="!isTouchDevice" />
                    <span class="period-shortcuts">
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setReorderAsOf(-1)">
                        {{ t('shipping.inventoryKpi.prevDay') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setReorderAsOf(0)">
                        {{ t('shipping.inventoryKpi.today') }}
                      </el-button>
                      <el-button size="small" text type="primary" class="shortcut-btn" @click="setReorderAsOf(1)">
                        {{ t('shipping.inventoryKpi.nextDay') }}
                      </el-button>
                    </span>
                  </el-form-item>
                  <el-button type="primary" size="small" :loading="loading.reorder" class="btn-query" @click="fetchReorder">{{ t('common.query') }}</el-button>
                </el-form>
              </div>
              <div class="table-wrap glass-inner">
                <el-table :data="reorderList" stripe size="small" max-height="380" v-loading="loading.reorder" class="kpi-table kpi-table--numeric">
                  <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip sortable />
                  <el-table-column prop="product_name" label="製品名" width="130" show-overflow-tooltip sortable />
                  <el-table-column prop="warehouse_inventory" label="現在在庫" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.warehouse_inventory ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="safety_stock" label="安全在庫" width="100" align="right" sortable>
                    <template #default="{ row }"><span class="cell-num">{{ (row.safety_stock ?? 0).toLocaleString() }}</span></template>
                  </el-table-column>
                  <el-table-column prop="latest_date" label="基準日" width="100" align="center" sortable />
                  <el-table-column label="状態" width="100" align="center">
                    <template #default="{ row }">
                      <el-tag v-if="row.below_reorder" type="danger" size="small" effect="plain" class="cell-tag">発注点以下</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </div>
        </Transition>
      </div>
    </section>

    <!-- 印刷用（非表示） -->
    <div ref="printContentRef" class="print-content-hidden">
      <div class="print-body">
        <div class="print-header">
          <h1 class="print-title">{{ t('shipping.inventoryKpi.title') }} — {{ printTabLabel }}</h1>
          <p class="print-subtitle">{{ printSubtitle }}</p>
          <p class="print-date">{{ printDateLabel }}</p>
        </div>
        <div class="print-table-wrap">
          <!-- 回転率 -->
          <template v-if="activeTab === 'turnover'">
            <table class="print-table">
              <thead>
                <tr>
                  <th class="print-th">製品CD</th>
                  <th class="print-th">製品名</th>
                  <th class="print-th print-th-num">期間需要</th>
                  <th class="print-th print-th-num">月初</th>
                  <th class="print-th print-th-num">月末</th>
                  <th class="print-th print-th-num">平均在庫</th>
                  <th class="print-th print-th-num">回転率</th>
                  <th class="print-th print-th-num">回転日数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in turnoverList" :key="i" class="print-tr">
                  <td class="print-td">{{ row.product_cd || '—' }}</td>
                  <td class="print-td">{{ row.product_name || '—' }}</td>
                  <td class="print-td print-td-num">{{ (row.period_forecast ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ (row.opening_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ (row.closing_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ (row.avg_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ row.turnover != null ? row.turnover.toFixed(2) : '—' }}</td>
                  <td class="print-td print-td-num">{{ row.turnover_days != null ? row.turnover_days.toFixed(1) : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </template>
          <!-- 平均在庫日数 -->
          <template v-else-if="activeTab === 'avgDays'">
            <table class="print-table">
              <thead>
                <tr>
                  <th class="print-th">製品CD</th>
                  <th class="print-th">製品名</th>
                  <th class="print-th print-th-num">現在在庫</th>
                  <th class="print-th print-th-num">1日平均</th>
                  <th class="print-th print-th-num">平均在庫日数</th>
                  <th class="print-th print-th-num">{{ t('shipping.inventoryKpi.monthsEquivalent') }}</th>
                  <th class="print-th">基準日</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in avgDaysList" :key="i" class="print-tr">
                  <td class="print-td">{{ row.product_cd || '—' }}</td>
                  <td class="print-td">{{ row.product_name || '—' }}</td>
                  <td class="print-td print-td-num">{{ (row.current_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ (row.avg_daily_demand ?? 0).toFixed(2) }}</td>
                  <td class="print-td print-td-num">{{ row.avg_inventory_days != null ? row.avg_inventory_days.toFixed(1) + ' 日' : '—' }}</td>
                  <td class="print-td print-td-num">{{ row.avg_inventory_days != null ? (row.avg_inventory_days / 22).toFixed(1) : '—' }}</td>
                  <td class="print-td">{{ row.latest_date || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </template>
          <!-- 欠品アラート -->
          <template v-else-if="activeTab === 'shortage'">
            <table class="print-table">
              <thead>
                <tr>
                  <th class="print-th">製品CD</th>
                  <th class="print-th">製品名</th>
                  <th class="print-th print-th-num">現在在庫</th>
                  <th class="print-th print-th-num">平均日数</th>
                  <th class="print-th print-th-num">リード</th>
                  <th class="print-th print-th-num">閾値(日)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in shortageList" :key="i" class="print-tr">
                  <td class="print-td">{{ row.product_cd || '—' }}</td>
                  <td class="print-td">{{ row.product_name || '—' }}</td>
                  <td class="print-td print-td-num">{{ (row.current_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ row.avg_inventory_days != null ? row.avg_inventory_days.toFixed(1) + ' 日' : '—' }}</td>
                  <td class="print-td print-td-num">{{ row.lead_time ?? '—' }}</td>
                  <td class="print-td print-td-num">{{ row.threshold_days ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </template>
          <!-- 過剰アラート -->
          <template v-else-if="activeTab === 'overstock'">
            <table class="print-table">
              <thead>
                <tr>
                  <th class="print-th">製品CD</th>
                  <th class="print-th">製品名</th>
                  <th class="print-th print-th-num">現在在庫</th>
                  <th class="print-th print-th-num">回転日数</th>
                  <th class="print-th">最終出荷</th>
                  <th class="print-th print-th-num">経過日</th>
                  <th class="print-th">判定</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in overstockList" :key="i" class="print-tr">
                  <td class="print-td">{{ row.product_cd || '—' }}</td>
                  <td class="print-td">{{ row.product_name || '—' }}</td>
                  <td class="print-td print-td-num">{{ (row.current_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ row.turnover_days != null ? row.turnover_days.toFixed(1) : '—' }}</td>
                  <td class="print-td">{{ row.last_ship_date || '—' }}</td>
                  <td class="print-td print-td-num">{{ row.days_since_ship ?? '—' }}</td>
                  <td class="print-td">
                    <span v-if="row.over_by_turnover">回転</span>
                    <span v-if="row.over_by_ship">長期未出荷</span>
                    <span v-if="!row.over_by_turnover && !row.over_by_ship">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </template>
          <!-- 発注点一覧 -->
          <template v-else>
            <table class="print-table">
              <thead>
                <tr>
                  <th class="print-th">製品CD</th>
                  <th class="print-th">製品名</th>
                  <th class="print-th print-th-num">現在在庫</th>
                  <th class="print-th print-th-num">安全在庫</th>
                  <th class="print-th">基準日</th>
                  <th class="print-th">状態</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in reorderList" :key="i" class="print-tr">
                  <td class="print-td">{{ row.product_cd || '—' }}</td>
                  <td class="print-td">{{ row.product_name || '—' }}</td>
                  <td class="print-td print-td-num">{{ (row.warehouse_inventory ?? 0).toLocaleString() }}</td>
                  <td class="print-td print-td-num">{{ (row.safety_stock ?? 0).toLocaleString() }}</td>
                  <td class="print-td">{{ row.latest_date || '—' }}</td>
                  <td class="print-td">{{ row.below_reorder ? '発注点以下' : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Printer } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { getJSTToday } from '@/utils/dateFormat'
import {
  getInventoryTurnover,
  getAvgInventoryDays,
  getShortageAlerts,
  getOverstockAlerts,
  getReorderPointList,
  type TurnoverRow,
  type AvgInventoryDaysRow,
  type ShortageAlertRow,
  type OverstockAlertRow,
  type ReorderPointRow,
} from '@/api/database'

const { t } = useI18n()

/** 手机/平板：禁止日期、下拉、数字框等弹出键盘 */
const isTouchDevice = ref(false)
function detectTouch() {
  return typeof navigator !== 'undefined' && (
    'ontouchstart' in window ||
    ((navigator as { maxTouchPoints?: number }).maxTouchPoints ?? 0) > 0
  )
}
function applyTouchNoKeyboard(container: HTMLElement | null) {
  if (!container || !isTouchDevice.value) return
  container.querySelectorAll<HTMLInputElement>('.el-select .el-input__inner, .el-select input').forEach((el) => {
    el.setAttribute('readonly', 'readonly')
    el.setAttribute('inputmode', 'none')
  })
}

const activeTab = ref('turnover')
const sectionMainRef = ref<HTMLElement | null>(null)

const loading = reactive({
  turnover: false,
  avgDays: false,
  shortage: false,
  overstock: false,
  reorder: false,
})

const turnoverDateRange = ref<[string, string] | null>(null)
const turnoverByAmount = ref(false)
const turnoverList = ref<TurnoverRow[]>([])

const avgDaysAsOf = ref<string | null>(getJSTToday())
const avgDaysRecent = ref(30)
const avgDaysList = ref<AvgInventoryDaysRow[]>([])

const shortageAsOf = ref<string | null>(getJSTToday())
const shortageRecent = ref(30)
const safetyMarginDays = ref(2)
const shortageList = ref<ShortageAlertRow[]>([])

const overstockAsOf = ref<string | null>(getJSTToday())
const maxTurnoverDays = ref(90)
const daysSinceShip = ref(60)
const overstockList = ref<OverstockAlertRow[]>([])

const reorderAsOf = ref<string | null>(getJSTToday())
const reorderList = ref<ReorderPointRow[]>([])

const printContentRef = ref<HTMLElement | null>(null)

const tabs = computed(() => [
  { name: 'turnover', label: t('shipping.inventoryKpi.turnover'), count: turnoverList.value.length },
  { name: 'avgDays', label: t('shipping.inventoryKpi.avgDays'), count: avgDaysList.value.length },
  { name: 'shortage', label: t('shipping.inventoryKpi.shortageAlerts'), count: shortageList.value.length },
  { name: 'overstock', label: t('shipping.inventoryKpi.overstockAlerts'), count: overstockList.value.length },
  { name: 'reorder', label: t('shipping.inventoryKpi.reorderPoint'), count: reorderList.value.length },
])

const printListLength = computed(() => {
  switch (activeTab.value) {
    case 'turnover': return turnoverList.value.length
    case 'avgDays': return avgDaysList.value.length
    case 'shortage': return shortageList.value.length
    case 'overstock': return overstockList.value.length
    case 'reorder': return reorderList.value.length
    default: return 0
  }
})

const printTabLabel = computed(() => {
  const tab = tabs.value.find((x) => x.name === activeTab.value)
  return tab ? tab.label : ''
})

const printSubtitle = computed(() => {
  switch (activeTab.value) {
    case 'turnover': {
      const r = turnoverDateRange.value
      if (r && r.length === 2) return `${t('shipping.inventoryKpi.period')}: ${r[0]} ～ ${r[1]}`
      return t('shipping.inventoryKpi.turnover')
    }
    case 'avgDays':
      return `${t('shipping.inventoryKpi.asOfDate')}: ${avgDaysAsOf.value || '—'}`
    case 'shortage':
      return `${t('shipping.inventoryKpi.asOfDate')}: ${shortageAsOf.value || '—'}`
    case 'overstock':
      return `${t('shipping.inventoryKpi.asOfDate')}: ${overstockAsOf.value || '—'}`
    case 'reorder':
      return `${t('shipping.inventoryKpi.asOfDate')}: ${reorderAsOf.value || '—'}`
    default:
      return ''
  }
})

const printDateLabel = computed(() => {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}`
})

function handlePrint() {
  if (!printListLength.value) {
    ElMessage.warning(t('shipping.inventoryKpi.noDataToPrint') || '印刷するデータがありません')
    return
  }
  nextTick(() => executeFrontendPrint(printContentRef.value))
}

function executeFrontendPrint(contentRef: HTMLElement | null) {
  if (!contentRef || !contentRef.innerHTML.trim()) {
    ElMessage.error(t('shipping.inventoryKpi.printContentFailed') || '印刷内容の取得に失敗しました。')
    return
  }
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error(t('shipping.inventoryKpi.printPopupBlocked') || 'ポップアップがブロックされました。')
    return
  }
  const printHtml = contentRef.innerHTML
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map((el) => el.outerHTML)
    .join('')
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>${t('shipping.inventoryKpi.title')}</title>
        ${styles}
      </head>
      <body>
        <div class="print-container">${printHtml}</div>
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.focus()
    printWindow.print()
    printWindow.close()
  }
}

async function fetchTurnover() {
  let start = ''
  let end = ''
  if (turnoverDateRange.value && turnoverDateRange.value.length === 2) {
    start = turnoverDateRange.value[0]
    end = turnoverDateRange.value[1]
  }
  loading.turnover = true
  try {
    const res = await getInventoryTurnover({
      start_date: start || undefined,
      end_date: end || undefined,
      by_amount: turnoverByAmount.value,
    })
    const d = (res as any)?.data
    turnoverList.value = d?.data?.list ?? d?.list ?? []
  } catch (e: any) {
    ElMessage.error(e?.message || '在庫回転率の取得に失敗しました')
    turnoverList.value = []
  } finally {
    loading.turnover = false
  }
}

async function fetchAvgDays() {
  loading.avgDays = true
  try {
    const res = await getAvgInventoryDays({
      as_of_date: avgDaysAsOf.value || undefined,
      recent_days: avgDaysRecent.value,
    })
    const d = (res as any)?.data
    avgDaysList.value = d?.data?.list ?? d?.list ?? []
  } catch (e: any) {
    ElMessage.error(e?.message || '平均在庫日数の取得に失敗しました')
    avgDaysList.value = []
  } finally {
    loading.avgDays = false
  }
}

async function fetchShortage() {
  loading.shortage = true
  try {
    const res = await getShortageAlerts({
      as_of_date: shortageAsOf.value || undefined,
      recent_days: shortageRecent.value,
      safety_margin_days: safetyMarginDays.value,
    })
    const d = (res as any)?.data
    shortageList.value = d?.data?.list ?? d?.list ?? []
  } catch (e: any) {
    ElMessage.error(e?.message || '欠品アラートの取得に失敗しました')
    shortageList.value = []
  } finally {
    loading.shortage = false
  }
}

async function fetchOverstock() {
  loading.overstock = true
  try {
    const res = await getOverstockAlerts({
      as_of_date: overstockAsOf.value || undefined,
      max_turnover_days: maxTurnoverDays.value,
      days_since_ship: daysSinceShip.value,
    })
    const d = (res as any)?.data
    overstockList.value = d?.data?.list ?? d?.list ?? []
  } catch (e: any) {
    ElMessage.error(e?.message || '過剰アラートの取得に失敗しました')
    overstockList.value = []
  } finally {
    loading.overstock = false
  }
}

async function fetchReorder() {
  loading.reorder = true
  try {
    const res = await getReorderPointList({
      as_of_date: reorderAsOf.value || undefined,
    })
    const d = (res as any)?.data
    reorderList.value = d?.data?.list ?? d?.list ?? []
  } catch (e: any) {
    ElMessage.error(e?.message || '発注点一覧の取得に失敗しました')
    reorderList.value = []
  } finally {
    loading.reorder = false
  }
}

/** 日本標準時（JST）での「当日」を YYYY-MM-DD で取得し、当月・前月の期間を返す */

/** 当月：JST で月初～当日 */
function getCurrentMonthRange(): [string, string] {
  const today = getJSTToday()
  const [y, m] = today.split('-').map(Number)
  const start = `${y}-${String(m).padStart(2, '0')}-01`
  return [start, today]
}

/** 前月：JST で前月1日～前月最終日 */
function getPrevMonthRange(): [string, string] {
  const today = getJSTToday()
  const [y, m] = today.split('-').map(Number)
  const prevY = m === 1 ? y - 1 : y
  const prevM = m === 1 ? 12 : m - 1
  const start = `${prevY}-${String(prevM).padStart(2, '0')}-01`
  const lastDay = new Date(prevY, prevM, 0).getDate()
  const end = `${prevY}-${String(prevM).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
  return [start, end]
}

function setTurnoverPeriod(which: 'prevMonth' | 'currentMonth') {
  turnoverDateRange.value = which === 'currentMonth' ? getCurrentMonthRange() : getPrevMonthRange()
  fetchTurnover()
}

/** JST で基準日から offset 日後の日付を YYYY-MM-DD で返す（前日=-1, 今日=0, 後日=1） */
function getJSTDateOffset(offset: number): string {
  const today = getJSTToday()
  const [y, m, d] = today.split('-').map(Number)
  const date = new Date(y, m - 1, d + offset)
  const yy = date.getFullYear()
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  return `${yy}-${mm}-${dd}`
}

function setAvgDaysAsOf(offset: number) {
  avgDaysAsOf.value = offset === 0 ? getJSTToday() : getJSTDateOffset(offset)
  fetchAvgDays()
}

function setShortageAsOf(offset: number) {
  shortageAsOf.value = offset === 0 ? getJSTToday() : getJSTDateOffset(offset)
  fetchShortage()
}

function setOverstockAsOf(offset: number) {
  overstockAsOf.value = offset === 0 ? getJSTToday() : getJSTDateOffset(offset)
  fetchOverstock()
}

function setReorderAsOf(offset: number) {
  reorderAsOf.value = offset === 0 ? getJSTToday() : getJSTDateOffset(offset)
  fetchReorder()
}

onMounted(() => {
  isTouchDevice.value = detectTouch()
  turnoverDateRange.value = getCurrentMonthRange()
  fetchTurnover()
  nextTick(() => applyTouchNoKeyboard(sectionMainRef.value))
})

watch(activeTab, () => {
  nextTick(() => applyTouchNoKeyboard(sectionMainRef.value))
})
</script>

<style scoped>
.kpi-page {
  --r: 12px;
  --space: 12px;
  --font-ui: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', Meiryo, sans-serif;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --accent: #2563eb;
  --accent-light: rgba(59, 130, 246, 0.12);
  position: relative;
  min-height: 100%;
  padding: var(--space) 14px 20px;
  font-family: var(--font-ui);
  animation: pageIn 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse 100% 80% at 50% -20%, rgba(99, 102, 241, 0.15), transparent),
    radial-gradient(ellipse 80% 50% at 100% 0%, rgba(59, 130, 246, 0.08), transparent),
    radial-gradient(ellipse 60% 40% at 0% 100%, rgba(139, 92, 246, 0.06), transparent),
    linear-gradient(165deg, #f8fafc 0%, #f1f5f9 30%, #e2e8f0 100%);
  pointer-events: none;
}

.glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.04),
    0 1px 0 rgba(255, 255, 255, 0.9) inset;
}

.glass-inner {
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.8),
    0 1px 3px rgba(0, 0, 0, 0.04);
}

.page-header {
  padding: 14px 18px 14px 20px;
  border-radius: var(--r);
  margin-bottom: var(--space);
  animation: slideDown 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(145deg, #4f46e5 0%, #2563eb 50%, #1d4ed8 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.header-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45);
}

.header-text {
  min-width: 0;
}

.header-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.header-desc {
  margin: 4px 0 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1.4;
}

.section-main {
  padding: var(--space) 16px 18px;
  border-radius: var(--r);
  animation: slideUp 0.45s cubic-bezier(0.22, 1, 0.36, 1) 0.05s backwards;
}

.tabs-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.tab-btn {
  --delay: calc(var(--tab-i, 0) * 0.04s);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(10px);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  font-family: var(--font-ui);
  animation: tabIn 0.35s ease-out var(--delay) backwards;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.85);
  color: var(--text-primary);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.15) 0%, rgba(37, 99, 235, 0.12) 100%);
  color: #2563eb;
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.18);
}

.tab-count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.07);
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, color 0.2s ease;
}

.tab-btn.active .tab-count {
  background: rgba(37, 99, 235, 0.22);
  color: #2563eb;
}

.tab-panels {
  min-height: 340px;
}

.tab-panel {
  padding: 0;
}

.filter-row {
  margin-bottom: 12px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item.compact .el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  padding-right: 8px;
}

.input-sm {
  width: 200px;
}

.filter-form :deep(.el-date-editor) {
  width: 220px;
}

.filter-form :deep(.el-date-editor.el-date-editor--daterange) {
  width: 240px;
}

.period-shortcuts {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-left: 8px;
  vertical-align: middle;
}

.shortcut-btn {
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
}

.input-sm :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.input-num {
  width: 88px;
}

.input-num :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.btn-query {
  font-weight: 600;
  border-radius: 10px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn-query:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.38);
}

.table-wrap {
  padding: 10px;
  border-radius: 10px;
}

/* Table: glass + content distinction */
.kpi-table {
  font-size: 12px;
  font-family: var(--font-ui);
  border-radius: 8px;
  overflow: hidden;
}

.kpi-table :deep(.el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

.kpi-table :deep(.el-table__header th) {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--text-muted);
  background: rgba(241, 245, 249, 0.95) !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding: 10px 0;
}

.kpi-table :deep(.el-table__header th .cell) {
  padding-left: 12px;
  padding-right: 12px;
}

.kpi-table :deep(.el-table__body td) {
  font-weight: 500;
  color: var(--text-primary);
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  transition: background-color 0.18s ease;
}

.kpi-table :deep(.el-table__body td .cell) {
  padding-left: 12px;
  padding-right: 12px;
}

.kpi-table :deep(.el-table__row:hover > td) {
  background: rgba(59, 130, 246, 0.06) !important;
}

.kpi-table :deep(.el-table__row) {
  transition: background-color 0.18s ease;
}

/* Numeric cells: tabular figures, subtle emphasis */
.cell-num {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

/* Status/tag cells */
.cell-tags {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  justify-content: center;
}

.cell-tags .cell-tag,
.kpi-table :deep(.el-tag.cell-tag) {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.kpi-table :deep(.el-tag:hover) {
  transform: scale(1.03);
}

/* Sortable header styling */
.kpi-table :deep(.el-table__column-filter-trigger),
.kpi-table :deep(.el-table__sort-icon) {
  margin-left: 4px;
}

/* Tab transition */
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.tab-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.tab-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@keyframes pageIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes tabIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header print button */
.header-inner {
  flex-wrap: wrap;
}
.header-text {
  flex: 1;
  min-width: 0;
}
.header-print-btn {
  flex-shrink: 0;
  font-weight: 600;
  border-radius: 10px;
}
.header-print-btn:not(:disabled):hover {
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.35);
}

/* 印刷用：画面上は非表示 */
.print-content-hidden {
  position: absolute;
  left: -9999px;
  top: 0;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

.print-body {
  padding: 16px;
  font-family: var(--font-ui);
  color: #0f172a;
  min-width: 700px;
}

.print-header {
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 2px solid #2563eb;
}

.print-title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.print-subtitle {
  margin: 0;
  font-size: 13px;
  color: #475569;
}

.print-date {
  margin: 4px 0 0;
  font-size: 11px;
  color: #64748b;
}

.print-table-wrap {
  overflow: auto;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.print-th {
  text-align: left;
  padding: 8px 10px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  font-weight: 700;
  color: #475569;
}

.print-th-num {
  text-align: right;
}

.print-tr:nth-child(even) {
  background: #f8fafc;
}

.print-td {
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  color: #0f172a;
}

.print-td-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ========== 响应式：平板・手机 ========== */
@media (max-width: 1024px) {
  .kpi-page {
    padding: 10px 12px 16px;
  }
  .page-header {
    padding: 12px 14px;
  }
  .section-main {
    padding: 10px 12px 14px;
  }
  .header-inner {
    flex-wrap: wrap;
    gap: 10px;
  }
  .header-print-btn {
    width: 100%;
    margin-top: 4px;
  }
  .filter-form {
    gap: 8px 10px;
  }
  .filter-form :deep(.el-form-item.compact),
  .filter-form :deep(.el-form-item) {
    width: 100%;
    max-width: 100%;
  }
  .input-sm,
  .filter-form :deep(.el-date-editor),
  .filter-form :deep(.el-date-editor.el-date-editor--daterange) {
    width: 100%;
    max-width: 100%;
  }
  .input-num {
    width: 100%;
    max-width: 140px;
  }
  .period-shortcuts {
    margin-left: 0;
    margin-top: 4px;
  }
  .table-wrap {
    padding: 8px;
    overflow-x: auto;
  }
  .kpi-table :deep(.el-table) {
    min-width: 640px;
  }
  .kpi-table :deep(.el-table__header th .cell),
  .kpi-table :deep(.el-table__body td .cell) {
    padding-left: 8px;
    padding-right: 8px;
  }
  .tab-panels {
    min-height: 280px;
  }
}

@media (max-width: 768px) {
  .kpi-page {
    padding: 8px 10px 12px;
    --space: 10px;
  }
  .page-header {
    padding: 10px 12px;
    margin-bottom: 8px;
  }
  .header-icon {
    width: 38px;
    height: 38px;
    font-size: 18px;
  }
  .header-title {
    font-size: 1.05rem;
  }
  .header-desc {
    font-size: 11px;
  }
  .section-main {
    padding: 8px 10px 12px;
  }
  .tabs-bar {
    gap: 6px;
    margin-bottom: 10px;
  }
  .tab-btn {
    padding: 6px 10px;
    font-size: 11px;
  }
  .tab-count {
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    font-size: 10px;
  }
  .filter-row {
    margin-bottom: 10px;
  }
  .filter-form :deep(.el-form-item__label) {
    font-size: 11px;
  }
  .table-wrap {
    padding: 6px;
    margin: 0 -10px;
    border-radius: 8px;
  }
  .kpi-table {
    font-size: 11px;
  }
  .kpi-table :deep(.el-table__header th) {
    font-size: 10px;
    padding: 8px 0;
  }
  .kpi-table :deep(.el-table__body td) {
    padding: 8px 0;
  }
  .tab-panels {
    min-height: 240px;
  }
}

@media (max-width: 480px) {
  .kpi-page {
    padding: 6px 8px 10px;
    --space: 8px;
  }
  .page-header {
    padding: 8px 10px;
    border-radius: 10px;
  }
  .header-inner {
    gap: 8px;
  }
  .header-title {
    font-size: 1rem;
  }
  .section-main {
    padding: 6px 8px 10px;
    border-radius: 10px;
  }
  .tabs-bar {
    gap: 4px;
    margin-bottom: 8px;
  }
  .tab-btn {
    padding: 6px 8px;
    font-size: 10px;
  }
  .btn-query {
    width: 100%;
  }
  .table-wrap {
    margin: 0 -8px;
    padding: 4px;
  }
  .tab-panels {
    min-height: 200px;
  }
}

@media print {
  .print-content-hidden {
    position: static;
    width: auto;
    height: auto;
    overflow: visible;
    opacity: 1;
  }
  .print-body {
    padding: 0;
  }
  .print-title {
    font-size: 16px;
  }
}
</style>
