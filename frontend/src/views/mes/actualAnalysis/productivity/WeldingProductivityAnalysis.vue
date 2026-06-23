<template>
  <div class="ipa">
    <div class="ipa__bg" aria-hidden="true">
      <div class="ipa__orb ipa__orb--1" />
      <div class="ipa__orb ipa__orb--2" />
      <div class="ipa__orb ipa__orb--3" />
    </div>

    <header class="ipa-hero ipa-fade-in">
      <div class="ipa-hero__main">
        <div class="ipa-hero__icon">
          <el-icon :size="24"><Connection /></el-icon>
          <span class="ipa-hero__icon-glow" />
        </div>
        <div class="ipa-hero__text">
          <div class="ipa-hero__eyebrow">MES · 実績分析</div>
          <h1 class="ipa-hero__title">溶接工程 — 生産性分析</h1>
          <p class="ipa-hero__meta">実績 · 能率 · 不良率 · 稼働</p>
        </div>
      </div>
      <div class="ipa-hero__actions">
        <span v-if="analysisData" class="ipa-hero__range">
          {{ analysisData.start_date }} ～ {{ analysisData.end_date }}
        </span>
        <el-dropdown
          trigger="click"
          :disabled="!analysisData || exportBusy"
          popper-class="ipa-report-dropdown"
          @command="handleReportCommand"
        >
          <el-button class="ipa-btn ipa-btn--report" :loading="exportBusy" round>
            <span class="ipa-btn__inner">
              <el-icon v-if="!exportBusy" class="ipa-btn__icon"><Document /></el-icon>
              <span>レポート</span>
              <el-icon class="ipa-btn__caret"><ArrowDown /></el-icon>
            </span>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="ipa-report-menu">
              <el-dropdown-item
                v-for="item in reportMenuItems"
                :key="item.command"
                :command="item.command"
                :divided="item.divided"
                class="ipa-report-item"
                :class="`ipa-report-item--${item.tone}`"
              >
                <span class="ipa-report-item__icon-wrap">
                  <el-icon><component :is="item.icon" /></el-icon>
                </span>
                <span class="ipa-report-item__text">
                  <span class="ipa-report-item__label">{{ item.label }}</span>
                  <span v-if="item.hint" class="ipa-report-item__hint">{{ item.hint }}</span>
                </span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button class="ipa-btn ipa-btn--refresh" :loading="loading" round @click="() => loadAnalysis()">
          <span class="ipa-btn__inner">
            <el-icon v-if="!loading" class="ipa-btn__icon"><Refresh /></el-icon>
            <span>更新</span>
          </span>
        </el-button>
      </div>
    </header>

    <div class="ipa-toolbar ipa-panel ipa-fade-in ipa-fade-in--d1">
      <div class="ipa-toolbar__fields">
        <div class="ipa-field ipa-field--period">
          <span class="ipa-field__pill"><el-icon><Calendar /></el-icon>期間</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始"
            end-placeholder="終了"
            value-format="YYYY-MM-DD"
            size="small"
            class="ipa-field__control ipa-field__date"
          />
        </div>
        <div class="ipa-field ipa-field--inspector">
          <span class="ipa-field__pill"><el-icon><User /></el-icon>溶接作業者</span>
          <el-select
            v-model="filterOperatorId"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="ipa-field__control ipa-field__inspector-select"
          >
            <el-option label="（すべて）" value="" />
            <el-option v-for="u in operatorOptions" :key="u.id" :label="operatorLabel(u)" :value="u.id" />
          </el-select>
        </div>
        <div class="ipa-field ipa-field--product">
          <span class="ipa-field__pill"><el-icon><Goods /></el-icon>製品名</span>
          <el-select
            v-model="filterProductCd"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="ipa-field__control ipa-field__product-select"
            :loading="loadingProductOptions"
          >
            <el-option label="（すべて）" value="" />
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="productOptionLabel(p)"
              :value="p.product_cd"
            >
              <div class="ipa-product-opt">
                <span class="ipa-product-opt__name">{{ p.product_name || p.product_cd }}</span>
                <span class="ipa-product-opt__cd">{{ p.product_cd }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
        <label class="ipa-check ipa-field ipa-field--check">
          <span class="ipa-field__pill ipa-field__pill--check">オプション</span>
          <el-checkbox v-model="includeIncomplete" size="small">未確定を含む</el-checkbox>
        </label>
      </div>
    </div>

    <div v-loading="loading" class="ipa-body">
      <div class="ipa-kpi">
        <div
          v-for="card in kpiCards"
          :key="card.key"
          class="ipa-kpi__card"
          :class="`ipa-kpi__card--${card.tone}`"
        >
          <div class="ipa-kpi__accent" aria-hidden="true" />
          <div class="ipa-kpi__icon-wrap" :class="`ipa-kpi__icon-wrap--${card.tone}`">
            <el-icon :size="18"><component :is="card.icon" /></el-icon>
          </div>
          <div class="ipa-kpi__content">
            <div class="ipa-kpi__label">{{ card.label }}</div>
            <div class="ipa-kpi__value">{{ card.value }}</div>
            <div class="ipa-kpi__hint">{{ card.hint }}</div>
          </div>
        </div>
      </div>

      <Transition name="ipa-reveal">
        <div v-if="analysisData && contentVisible" key="content" class="ipa-content">
          <section class="ipa-panel ipa-panel--chart ipa-fade-in ipa-fade-in--d3">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><TrendCharts /></el-icon>
                <span class="ipa-panel__title">日別推移</span>
              </div>
              <span class="ipa-panel__badge">生産数 · 能率</span>
            </div>
            <div ref="dailyChartRef" class="ipa-chart ipa-chart--main" />
          </section>

          <div class="ipa-split">
            <section class="ipa-panel ipa-panel--inspector ipa-fade-in ipa-fade-in--d4">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico ipa-panel__ico--inspector"><User /></el-icon>
                  <span class="ipa-panel__title">溶接作業者別</span>
                </div>
                <div class="ipa-panel__badges">
                  <span class="ipa-panel__badge ipa-panel__badge--soft">{{ operatorDisplayRows.length }} 名</span>
                  <span v-if="operatorSectionAvgEfficiency != null" class="ipa-panel__badge ipa-panel__badge--inspector">
                    平均能率 {{ fmtEfficiency(operatorSectionAvgEfficiency) }} 個/時
                  </span>
                </div>
              </div>
              <div ref="operatorChartRef" class="ipa-chart ipa-chart--side ipa-chart--inspector" />
              <el-table
                :data="operatorDisplayRows"
                size="small"
                stripe
                class="ipa-table ipa-table--inspector"
                max-height="240"
              >
                <el-table-column label="#" width="36" align="center">
                  <template #default="{ $index }">
                    <span class="ipa-row-rank" :class="operatorRankClass($index)">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="operator_name" label="溶接作業者" min-width="96" show-overflow-tooltip />
                <el-table-column label="件" width="44" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="68" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良率" width="64" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="平均能率" width="68" align="right">
                  <template #default="{ row }">
                    <span class="ipa-eff-pill ipa-eff-pill--inspector">{{ fmtEfficiency(row.avg_efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>

            <section class="ipa-panel ipa-panel--product ipa-fade-in ipa-fade-in--d5">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico ipa-panel__ico--product"><Goods /></el-icon>
                  <span class="ipa-panel__title">製品別</span>
                </div>
                <div class="ipa-panel__badges">
                  <span class="ipa-panel__badge ipa-panel__badge--soft">{{ productDisplayRows.length }} 品目</span>
                  <span v-if="productSectionTotalQty > 0" class="ipa-panel__badge ipa-panel__badge--product">
                    生産合計 {{ fmtInt(productSectionTotalQty) }}
                  </span>
                </div>
              </div>
              <div ref="productChartRef" class="ipa-chart ipa-chart--side ipa-chart--product" />
              <el-table
                :data="productDisplayRows"
                size="small"
                stripe
                class="ipa-table ipa-table--product"
                max-height="280"
              >
                <el-table-column prop="product_cd" label="CD" width="84">
                  <template #default="{ row }">
                    <span class="ipa-product-cd">{{ row.product_cd }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="product_name" label="製品名" min-width="108" show-overflow-tooltip />
                <el-table-column label="件" width="40" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="68" align="right">
                  <template #default="{ row }">
                    <span class="ipa-num ipa-num--product">{{ fmtInt(row.sum_actual_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column
                  label="不良率"
                  width="75"
                  align="right"
                  sortable
                  :sort-method="sortByProductDefectRate"
                >
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column
                  label="能率"
                  width="70"
                  align="right"
                  sortable
                  :sort-method="sortByProductEfficiency"
                >
                  <template #default="{ row }">
                    <span class="ipa-eff-pill ipa-eff-pill--product">{{ fmtEfficiency(row.avg_efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </div>

          <section v-if="productRankList.length" class="ipa-panel ipa-panel--rank ipa-fade-in ipa-fade-in--d5b">
            <div class="ipa-panel__head ipa-rank-panel__head">
              <div class="ipa-panel__title-wrap">
                <div class="ipa-rank-title-ico" aria-hidden="true">
                  <el-icon :size="16"><Trophy /></el-icon>
                </div>
                <div>
                  <span class="ipa-panel__title">製品別 · 溶接作業者能率ランキング</span>
                  <div class="ipa-rank-panel__desc">製品ごとの溶接作業者能率を順位付けして比較</div>
                </div>
              </div>
              <div class="ipa-panel__badges">
                <span class="ipa-panel__badge ipa-panel__badge--soft">{{ productRankList.length }} 品目</span>
                <span class="ipa-panel__badge ipa-panel__badge--rank">{{ productRankTopOverview.length }} TOP記録</span>
              </div>
            </div>

            <div class="ipa-rank-toolbar">
              <div class="ipa-rank-picker">
                <span class="ipa-rank-picker__label">
                  <el-icon :size="12"><Goods /></el-icon>
                  対象製品
                </span>
                <el-select
                  v-model="rankViewProductCd"
                  filterable
                  size="small"
                  class="ipa-rank-picker__select"
                  placeholder="製品を選択"
                >
                  <el-option
                    v-for="p in productRankList"
                    :key="p.product_cd"
                    :label="productRankOptionLabel(p)"
                    :value="p.product_cd"
                  />
                </el-select>
              </div>
            </div>

            <Transition name="ipa-rank-swap" mode="out-in">
              <div v-if="selectedProductRanking" :key="rankViewProductCd" class="ipa-rank-body">
                <div class="ipa-rank-hero">
                  <div class="ipa-rank-hero__glow" aria-hidden="true" />
                  <div class="ipa-rank-hero__main">
                    <span class="ipa-rank-hero__cd">{{ selectedProductRanking.product_cd }}</span>
                    <h3 class="ipa-rank-hero__name">{{ selectedProductRanking.product_name || '—' }}</h3>
                  </div>
                  <div v-if="selectedProductRankStats" class="ipa-rank-hero__stats">
                    <div class="ipa-rank-hero__stat">
                      <span class="ipa-rank-hero__stat-label">生産合計</span>
                      <span class="ipa-rank-hero__stat-val">{{ fmtInt(selectedProductRanking.sum_actual_qty) }}</span>
                    </div>
                    <div class="ipa-rank-hero__stat">
                      <span class="ipa-rank-hero__stat-label">溶接作業者</span>
                      <span class="ipa-rank-hero__stat-val">{{ selectedProductRankStats.operatorCount }}<small>名</small></span>
                    </div>
                    <div class="ipa-rank-hero__stat ipa-rank-hero__stat--accent">
                      <span class="ipa-rank-hero__stat-label">TOP能率</span>
                      <span class="ipa-rank-hero__stat-val">{{ fmtEfficiency(selectedProductRankStats.topEfficiency) }}<small>個/時</small></span>
                    </div>
                    <div class="ipa-rank-hero__stat">
                      <span class="ipa-rank-hero__stat-label">平均能率</span>
                      <span class="ipa-rank-hero__stat-val">{{ fmtEfficiency(selectedProductRankStats.avgEfficiency) }}<small>個/時</small></span>
                    </div>
                  </div>
                </div>

                <div v-if="podiumOperators.length" class="ipa-podium ipa-podium--hd">
                  <div
                    v-for="(item, idx) in podiumOperators"
                    :key="item.operator_user_id ?? item.operator_name"
                    class="ipa-podium__col"
                    :class="`ipa-podium__col--${item.rank}`"
                    :style="{ '--podium-delay': `${idx * 0.1}s` }"
                  >
                    <div class="ipa-podium__item" :class="`ipa-podium__item--${item.rank}`">
                      <div v-if="item.rank === 1" class="ipa-podium__crown" aria-hidden="true">👑</div>
                      <div class="ipa-podium__medal-wrap">
                        <span class="ipa-podium__medal">{{ rankMedal(item.rank) }}</span>
                      </div>
                      <div class="ipa-podium__name" :title="item.operator_name">{{ item.operator_name }}</div>
                      <div class="ipa-podium__eff">{{ fmtEfficiency(item.efficiency_per_hour) }}</div>
                      <div class="ipa-podium__sub">個/時</div>
                    </div>
                    <div class="ipa-podium__pedestal" :style="{ height: podiumPedestalHeight(item.rank) }">
                      <span class="ipa-podium__pedestal-rank">{{ item.rank }}</span>
                    </div>
                  </div>
                </div>

                <div class="ipa-rank-chart-block">
                  <div class="ipa-rank-chart-block__head">
                    <span class="ipa-rank-chart-block__title">溶接作業者別能率</span>
                    <span class="ipa-rank-chart-block__badge">{{ selectedProductRanking.operators.length }} 名</span>
                  </div>
                  <div ref="productRankChartRef" class="ipa-chart ipa-chart--rank" />
                </div>

                <el-table
                  :data="selectedProductRanking.operators"
                  size="small"
                  stripe
                  class="ipa-table ipa-table--rank"
                  max-height="280"
                  highlight-current-row
                >
                  <el-table-column label="順位" width="64" align="center" fixed>
                    <template #default="{ row }">
                      <span class="ipa-rank-badge" :class="rankBadgeClass(row.rank)">{{ row.rank }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="operator_name" label="溶接作業者" min-width="120" show-overflow-tooltip />
                  <el-table-column label="件" width="48" align="right">
                    <template #default="{ row }">{{ row.session_count }}</template>
                  </el-table-column>
                  <el-table-column label="生産" width="72" align="right">
                    <template #default="{ row }">
                      <span class="ipa-num ipa-num--rank-qty">{{ fmtInt(row.sum_actual_qty) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="能率" width="76" align="right" sortable :sort-method="sortByEfficiency">
                    <template #default="{ row }">
                      <span class="ipa-eff-pill ipa-eff-pill--rank">{{ fmtEfficiency(row.efficiency_per_hour) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="不良率" width="76" align="right" sortable :sort-method="sortByOperatorDefectRate">
                    <template #default="{ row }">
                      <span class="ipa-eff-pill ipa-eff-pill--warn">{{ fmtPct(row.defect_rate_percent) }}</span>
                    </template>
                  </el-table-column>
                </el-table>

                <div v-if="!selectedProductRanking.operators.length" class="ipa-rank-empty">
                  <el-icon :size="28" class="ipa-rank-empty__ico"><WarningFilled /></el-icon>
                  <p>能率を算出できる溶接作業者データがありません</p>
                  <span class="ipa-rank-empty__hint">正味稼働時間が必要です</span>
                </div>
              </div>
            </Transition>

            <div class="ipa-rank-overview">
              <div class="ipa-rank-overview__head">
                <el-icon class="ipa-rank-overview__ico"><List /></el-icon>
                <span class="ipa-rank-overview__title">全製品 · 能率 TOP1 一覧</span>
                <span class="ipa-rank-overview__count">{{ productRankTopOverview.length }}</span>
              </div>
              <el-table
                :data="productRankTopOverview"
                size="small"
                stripe
                class="ipa-table ipa-table--rank-overview"
                max-height="240"
                :row-class-name="rankOverviewRowClass"
              >
                <el-table-column prop="product_cd" label="CD" width="88">
                  <template #default="{ row }">
                    <span class="ipa-product-cd ipa-product-cd--rank">{{ row.product_cd }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
                <el-table-column label="TOP溶接作業者" min-width="110" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="ipa-rank-top-inspector">{{ row.top_operator_name ?? '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="能率" width="76" align="right">
                  <template #default="{ row }">
                    <span class="ipa-eff-pill ipa-eff-pill--rank">{{ fmtEfficiency(row.top_efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="対象人数" width="72" align="center">
                  <template #default="{ row }">{{ row.ranked_operator_count ?? 0 }}</template>
                </el-table-column>
                <el-table-column label="" width="80" align="center">
                  <template #default="{ row }">
                    <button
                      type="button"
                      class="ipa-rank-detail-btn"
                      :class="{ 'ipa-rank-detail-btn--active': rankViewProductCd === row.product_cd }"
                      @click="rankViewProductCd = row.product_cd"
                    >
                      詳細
                    </button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </section>

          <section v-if="defectRows.length" class="ipa-panel ipa-fade-in ipa-fade-in--d6">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><WarningFilled /></el-icon>
                <span class="ipa-panel__title">不良内訳（KT07）</span>
              </div>
            </div>
            <div class="ipa-defect-grid">
              <div v-for="(row, i) in defectRows.slice(0, 8)" :key="row.defect_cd" class="ipa-defect-chip" :style="{ animationDelay: `${i * 50}ms` }">
                <span class="ipa-defect-chip__name">{{ defectLabel(row.defect_cd) }}</span>
                <span class="ipa-defect-chip__qty">{{ fmtInt(row.qty) }}</span>
              </div>
            </div>
          </section>

          <section class="ipa-panel ipa-fade-in ipa-fade-in--d7">
            <div class="ipa-panel__head">
              <div class="ipa-panel__title-wrap">
                <el-icon class="ipa-panel__ico"><List /></el-icon>
                <span class="ipa-panel__title">セッション明細</span>
              </div>
              <div class="ipa-panel__badges">
                <span class="ipa-panel__badge">{{ analysisData.sessions.length }} 件</span>
              </div>
            </div>
            <el-table :data="analysisData.sessions" size="small" class="ipa-table ipa-table--detail" max-height="380">
              <el-table-column prop="production_day" label="生産日" width="102" fixed />
              <el-table-column prop="operator_display_name" label="溶接作業者" width="100" show-overflow-tooltip />
              <el-table-column prop="welding_machine" label="設備" width="88" show-overflow-tooltip />
              <el-table-column prop="product_cd" label="CD" width="88" />
              <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
              <el-table-column label="生産" width="64" align="right">
                <template #default="{ row }">{{ fmtInt(row.actual_production_quantity) }}</template>
              </el-table-column>
              <el-table-column label="不良" width="52" align="right">
                <template #default="{ row }">{{ fmtInt(row.defect_qty) }}</template>
              </el-table-column>
              <el-table-column label="不良率" width="68" align="right">
                <template #default="{ row }">{{ fmtPct(row.defect_rate_percent) }}</template>
              </el-table-column>
              <el-table-column label="能率" width="56" align="right">
                <template #default="{ row }"><span class="ipa-num ipa-num--good">{{ fmtEfficiency(row.efficiency_per_hour) }}</span></template>
              </el-table-column>
              <el-table-column label="稼働" width="56" align="right">
                <template #default="{ row }">{{ row.net_production_min ?? '—' }}</template>
              </el-table-column>
              <el-table-column label="停止" width="52" align="right">
                <template #default="{ row }">{{ row.paused_min ?? '—' }}</template>
              </el-table-column>
              <el-table-column label="状態" width="72" align="center" fixed="right">
                <template #default="{ row }">
                  <span class="ipa-status" :class="row.is_completed ? 'ipa-status--ok' : 'ipa-status--pending'">
                    {{ row.is_completed ? '確定' : '未確定' }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </Transition>

      <div v-if="!loading && !analysisData" class="ipa-empty ipa-fade-in">
        <div class="ipa-empty__icon"><el-icon :size="40"><DataAnalysis /></el-icon></div>
        <p>集計期間を選択してください</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  ArrowDown,
  Calendar,
  CircleCheck,
  DataAnalysis,
  Connection,
  Document,
  Goods,
  List,
  Refresh,
  Timer,
  TrendCharts,
  Trophy,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchWeldingProductivityAnalysis,
  type WeldingProductivityAnalysisData,
  type WeldingProductivityBucket,
  type WeldingProductivityDailyRow,
  type WeldingProductivityOperatorRow,
  type WeldingProductivityProductOperatorRanking,
  type WeldingProductivityProductRow,
  type WeldingProductivitySessionRow,
} from '@/api/weldingManagement'
import type { UserListItem } from '@/api/system'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'
import { fetchWeldingSectionOperators } from '@/views/mes/shared/weldingOperatorFilter'
import { filterWeldingSelectableProducts } from '@/views/mes/shared/weldingProductFilter'
import {
  loadMesDefectItemsForProcess,
  resolveMesDefectItemLabel,
} from '@/views/mes/actualDataCollection/shared/loadProcessDefectItems'
import {
  CHART_INIT_OPTS,
  chartTheme,
  createDailyTrendChartOption,
  createPersonBarChartOption,
  createProductBarChartOption,
  createProductRankChartOption,
  type IpaChartFormatters,
} from './ipaProductivityChartHelpers'
import {
  printWeldingProductivityDailyBatch,
  printWeldingProductivityOperatorProductBatch,
  printWeldingProductivityReport,
  printWeldingProductivitySection,
  type WeldingProductivityDailyBatchItem,
  type WeldingProductivityOperatorProductBatchItem,
  type WeldingProductivityPrintSection,
  type WeldingProductivityReportContext,
  type WeldingProductivityReportFilters,
} from './weldingProductivityReport'

defineOptions({ name: 'MesWeldingProductivityAnalysis' })

type ReportMenuTone = 'indigo' | 'sky' | 'teal' | 'violet' | 'emerald' | 'amber' | 'rose'

const reportMenuItems: Array<{
  command: string
  label: string
  hint?: string
  icon: typeof Document
  tone: ReportMenuTone
  divided?: boolean
}> = [
  {
    command: 'print-full',
    label: '印刷（全体）',
    hint: '全セクション一括出力',
    icon: markRaw(Document),
    tone: 'indigo',
  },
  {
    command: 'print-daily',
    label: '日別推移（印刷）',
    hint: '生産数 · 能率の推移',
    icon: markRaw(TrendCharts),
    tone: 'sky',
    divided: true,
  },
  {
    command: 'print-daily-batch',
    label: '日別推移（溶接作業者別・一括印刷）',
    hint: '溶接作業者ごとに分割出力',
    icon: markRaw(DataAnalysis),
    tone: 'teal',
  },
  {
    command: 'print-operator',
    label: '溶接作業者別（印刷）',
    hint: '溶接作業者別サマリー',
    icon: markRaw(User),
    tone: 'violet',
  },
  {
    command: 'print-operator-product-batch',
    label: '溶接作業者別製品別（一括印刷）',
    hint: '溶接作業者ごとに製品一覧を出力',
    icon: markRaw(Goods),
    tone: 'violet',
  },
  {
    command: 'print-product',
    label: '製品別（印刷）',
    hint: '製品別サマリー',
    icon: markRaw(Goods),
    tone: 'emerald',
  },
  {
    command: 'print-product-rank',
    label: '製品別 · 溶接作業者能率ランキング（印刷）',
    hint: '製品単位の順位表',
    icon: markRaw(List),
    tone: 'rose',
  },
]

const { t, te } = useI18n()

const loading = ref(false)
const exportBusy = ref(false)
const contentVisible = ref(false)
const analysisData = ref<WeldingProductivityAnalysisData | null>(null)
const operatorOptions = ref<UserListItem[]>([])
const filterOperatorId = ref<number | ''>('')
const filterProductCd = ref('')
const includeIncomplete = ref(false)
const productOptions = ref<Product[]>([])
const loadingProductOptions = ref(false)
const defectLabelMap = ref<Map<string, string>>(new Map())
const rankViewProductCd = ref('')
const dailyChartRef = ref<HTMLElement | null>(null)
const operatorChartRef = ref<HTMLElement | null>(null)
const productChartRef = ref<HTMLElement | null>(null)
const productRankChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null
let operatorChart: ECharts | null = null
let productChart: ECharts | null = null
let productRankChart: ECharts | null = null

const EFFICIENCY_UNIT = '個/時'

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])

const emptySummary = (): WeldingProductivityBucket => ({
  session_count: 0,
  completed_session_count: 0,
  sum_actual_qty: 0,
  sum_defect_qty: 0,
  sum_net_production_sec: 0,
  sum_net_production_min: 0,
  sum_paused_sec: 0,
  sum_paused_min: 0,
  defect_rate_percent: null,
  efficiency_per_hour: null,
})

const summary = computed(() => analysisData.value?.summary ?? emptySummary())
const defectRows = computed(() => analysisData.value?.defect_by_item ?? [])

const productRankList = computed((): WeldingProductivityProductOperatorRanking[] => {
  const fromApi = analysisData.value?.by_product_operator_ranking
  if (fromApi?.length) return fromApi
  return buildProductOperatorRankingFromSessions(analysisData.value?.sessions ?? [])
})

function buildProductOperatorRankingFromSessions(
  sessions: WeldingProductivityAnalysisData['sessions'],
): WeldingProductivityProductOperatorRanking[] {
  const productMap = new Map<
    string,
    {
      product_cd: string
      product_name: string
      sum_actual_qty: number
      session_count: number
      operators: Map<string, WeldingProductivityOperatorRow>
    }
  >()

  for (const s of sessions) {
    const productCd = (s.product_cd ?? '').trim() || 'unknown'
    const productName = (s.product_name ?? '').trim() || productCd
    if (!productMap.has(productCd)) {
      productMap.set(productCd, {
        product_cd: productCd,
        product_name: productName,
        sum_actual_qty: 0,
        session_count: 0,
        operators: new Map(),
      })
    }
    const prod = productMap.get(productCd)!
    prod.sum_actual_qty += Number(s.actual_production_quantity ?? 0)
    prod.session_count += 1

    const operatorId = s.mes_operator_user_id
    const operatorKey = operatorId != null ? String(operatorId) : 'none'
    const operatorName = (s.operator_display_name ?? s.mes_operator_name ?? '—').trim() || '—'
    if (!prod.operators.has(operatorKey)) {
      prod.operators.set(operatorKey, {
        operator_user_id: operatorId ?? null,
        operator_name: operatorName,
        session_count: 0,
        sum_actual_qty: 0,
        sum_defect_qty: 0,
        sum_net_production_sec: 0,
        efficiency_per_hour: null,
      })
    }
    const op = prod.operators.get(operatorKey)!
    op.session_count = (op.session_count ?? 0) + 1
    op.sum_actual_qty = (op.sum_actual_qty ?? 0) + Number(s.actual_production_quantity ?? 0)
    op.sum_defect_qty = (op.sum_defect_qty ?? 0) + Number(s.defect_qty ?? 0)
    op.sum_net_production_sec = (op.sum_net_production_sec ?? 0) + Number(s.net_production_sec ?? 0)
  }

  const result: WeldingProductivityProductOperatorRanking[] = []
  for (const prod of productMap.values()) {
    const operators: WeldingProductivityOperatorRow[] = []
    for (const op of prod.operators.values()) {
      const actual = op.sum_actual_qty ?? 0
      const netSec = op.sum_net_production_sec ?? 0
      const defect = op.sum_defect_qty ?? 0
      op.defect_rate_percent = actual > 0 ? Math.round((defect / actual) * 1000) / 10 : null
      op.efficiency_per_hour = actual > 0 && netSec > 0 ? Math.round(actual / (netSec / 3600)) : null
      op.sum_net_production_min = netSec > 0 ? Math.round(netSec / 60) : 0
      if (op.efficiency_per_hour != null) operators.push(op)
    }
    operators.sort((a, b) => (b.efficiency_per_hour ?? 0) - (a.efficiency_per_hour ?? 0))
    operators.forEach((row, i) => {
      row.rank = i + 1
    })
    result.push({
      product_cd: prod.product_cd,
      product_name: prod.product_name,
      sum_actual_qty: prod.sum_actual_qty,
      session_count: prod.session_count,
      operator_count: prod.operators.size,
      ranked_operator_count: operators.length,
      operators,
      top_operator_name: operators[0]?.operator_name ?? null,
      top_efficiency_per_hour: operators[0]?.efficiency_per_hour ?? null,
    })
  }
  return result.sort((a, b) => (b.sum_actual_qty ?? 0) - (a.sum_actual_qty ?? 0))
}

const selectedProductRanking = computed(() => {
  const list = productRankList.value
  if (!list.length) return null
  const cd = rankViewProductCd.value
  return list.find((p) => p.product_cd === cd) ?? list[0] ?? null
})

const podiumOperators = computed(() => {
  const rows = selectedProductRanking.value?.operators ?? []
  const top3 = rows.filter((r) => (r.rank ?? 99) <= 3)
  const order = [2, 1, 3]
  return order
    .map((rank) => top3.find((r) => r.rank === rank))
    .filter((r): r is WeldingProductivityOperatorRow => r != null)
})

const productRankTopOverview = computed(() =>
  productRankList.value.filter((p) => p.top_efficiency_per_hour != null),
)

function productRankOptionLabel(p: WeldingProductivityProductOperatorRanking): string {
  const name = (p.product_name ?? '').trim()
  return name ? `${p.product_cd} · ${name}` : p.product_cd
}

function rankMedal(rank?: number): string {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return String(rank ?? '—')
}

function rankBadgeClass(rank?: number): string {
  if (rank === 1) return 'ipa-rank-badge--gold'
  if (rank === 2) return 'ipa-rank-badge--silver'
  if (rank === 3) return 'ipa-rank-badge--bronze'
  return ''
}

function sortByEfficiency(a: WeldingProductivityOperatorRow, b: WeldingProductivityOperatorRow): number {
  return (b.efficiency_per_hour ?? -1) - (a.efficiency_per_hour ?? -1)
}

function syncRankProductSelection() {
  const list = productRankList.value
  if (!list.length) {
    rankViewProductCd.value = ''
    return
  }
  if (!list.some((p) => p.product_cd === rankViewProductCd.value)) {
    rankViewProductCd.value = list[0].product_cd
  }
}

const kpiCards = computed(() => {
  const s = summary.value
  return [
    {
      key: 'sessions',
      label: '確定セッション',
      value: fmtInt(s.completed_session_count),
      hint: `全 ${fmtInt(s.session_count)} 件`,
      icon: markRaw(CircleCheck),
      tone: 'indigo',
    },
    {
      key: 'actual',
      label: '生産数合計',
      value: fmtInt(s.sum_actual_qty),
      hint: '確定実績合計',
      icon: markRaw(Goods),
      tone: 'sky',
    },
    {
      key: 'defect',
      label: '不良数',
      value: fmtInt(s.sum_defect_qty),
      hint: `不良率 ${fmtPct(s.defect_rate_percent)}`,
      icon: markRaw(WarningFilled),
      tone: 'amber',
    },
    {
      key: 'efficiency',
      label: '総合能率',
      value: fmtEfficiency(s.efficiency_per_hour),
      hint: '個 / 時間',
      icon: markRaw(TrendCharts),
      tone: 'emerald',
    },
    {
      key: 'runtime',
      label: '正味稼働',
      value: fmtDurationMin(s.sum_net_production_min),
      hint: `停止 ${fmtDurationMin(s.sum_paused_min)}`,
      icon: markRaw(Timer),
      tone: 'violet',
    },
  ]
})

function fmtInt(value: number | null | undefined): string {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toLocaleString('ja-JP') : '0'
}

function fmtPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toFixed(1)}%`
}

function fmtEfficiency(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${Math.round(value)}`
}

function fmtDurationMin(min: number | null | undefined): string {
  const n = Number(min ?? 0)
  if (!Number.isFinite(n) || n <= 0) return '—'
  const h = Math.floor(n / 60)
  const m = n % 60
  if (h > 0) return `${h}h${m}m`
  return `${m}m`
}

const chartFormatters: IpaChartFormatters = {
  fmtInt,
  fmtPct,
  fmtEfficiency,
}

type OperatorDisplayRow = WeldingProductivityOperatorRow & {
  avg_efficiency_per_hour: number | null
}

type ProductDisplayRow = WeldingProductivityProductRow & {
  avg_efficiency_per_hour: number | null
}

/** 期間内：生産合計 ÷ 正味稼働時間（個/時） */
function periodAvgEfficiencyFromBucket(row: WeldingProductivityBucket): number | null {
  if (row.efficiency_per_hour != null && Number.isFinite(row.efficiency_per_hour)) {
    return row.efficiency_per_hour
  }
  const qty = Number(row.sum_actual_qty ?? 0)
  const sec = Number(row.sum_net_production_sec ?? 0)
  if (qty <= 0 || sec <= 0) return null
  return Math.round(qty / (sec / 3600))
}

const operatorDisplayRows = computed((): OperatorDisplayRow[] =>
  (analysisData.value?.by_operator ?? [])
    .map((row) => ({
      ...row,
      avg_efficiency_per_hour: periodAvgEfficiencyFromBucket(row),
    }))
    .sort((a, b) => (b.avg_efficiency_per_hour ?? -1) - (a.avg_efficiency_per_hour ?? -1)),
)

const operatorSectionAvgEfficiency = computed((): number | null => {
  const rows = analysisData.value?.by_operator ?? []
  let totalQty = 0
  let totalSec = 0
  for (const row of rows) {
    totalQty += Number(row.sum_actual_qty ?? 0)
    totalSec += Number(row.sum_net_production_sec ?? 0)
  }
  if (totalQty <= 0 || totalSec <= 0) return null
  return Math.round(totalQty / (totalSec / 3600))
})

const productDisplayRows = computed((): ProductDisplayRow[] =>
  (analysisData.value?.by_product ?? [])
    .map((row) => ({
      ...row,
      avg_efficiency_per_hour: periodAvgEfficiencyFromBucket(row),
    }))
    .sort((a, b) => (b.sum_actual_qty ?? 0) - (a.sum_actual_qty ?? 0)),
)

const productSectionTotalQty = computed(() =>
  productDisplayRows.value.reduce((sum, row) => sum + Number(row.sum_actual_qty ?? 0), 0),
)

function operatorRankClass(index: number): string {
  if (index === 0) return 'ipa-row-rank--gold'
  if (index === 1) return 'ipa-row-rank--silver'
  if (index === 2) return 'ipa-row-rank--bronze'
  return ''
}

function sortByOperatorDefectRate(a: WeldingProductivityOperatorRow, b: WeldingProductivityOperatorRow): number {
  return (b.defect_rate_percent ?? -1) - (a.defect_rate_percent ?? -1)
}

function sortByProductDefectRate(a: ProductDisplayRow, b: ProductDisplayRow): number {
  return (b.defect_rate_percent ?? -1) - (a.defect_rate_percent ?? -1)
}

function sortByProductEfficiency(a: ProductDisplayRow, b: ProductDisplayRow): number {
  return (b.avg_efficiency_per_hour ?? -1) - (a.avg_efficiency_per_hour ?? -1)
}

function podiumPedestalHeight(rank?: number): string {
  if (rank === 1) return '72px'
  if (rank === 2) return '56px'
  if (rank === 3) return '44px'
  return '36px'
}

function rankOverviewRowClass({ row }: { row: WeldingProductivityProductOperatorRanking }): string {
  return rankViewProductCd.value === row.product_cd ? 'ipa-rank-overview-row--active' : ''
}

const selectedProductRankStats = computed(() => {
  const ranking = selectedProductRanking.value
  if (!ranking) return null
  const operators = ranking.operators ?? []
  const top = operators[0]
  let totalEff = 0
  let effCount = 0
  for (const row of operators) {
    if (row.efficiency_per_hour != null) {
      totalEff += row.efficiency_per_hour
      effCount += 1
    }
  }
  return {
    topEfficiency: top?.efficiency_per_hour ?? null,
    topOperator: top?.operator_name ?? null,
    avgEfficiency: effCount > 0 ? totalEff / effCount : null,
    operatorCount: ranking.ranked_operator_count ?? operators.length,
  }
})

function operatorLabel(u: UserListItem): string {
  const name = (u.full_name ?? '').trim()
  const username = (u.username ?? '').trim()
  if (name && username) return `${name}（${username}）`
  return name || username || `#${u.id}`
}

function buildOperatorProductRows(
  sessions: WeldingProductivitySessionRow[],
  operatorKey: string,
  includeProduct: (productCd: string) => boolean,
): ProductDisplayRow[] {
  const map = new Map<string, WeldingProductivityProductRow & { sum_net_production_sec: number }>()
  for (const s of sessions) {
    const productCd = (s.product_cd ?? '').trim()
    if (!productCd || !includeProduct(productCd)) continue

    const opKey = s.mes_operator_user_id != null ? String(s.mes_operator_user_id) : 'none'
    if (opKey !== operatorKey) continue

    if (!map.has(productCd)) {
      map.set(productCd, {
        product_cd: productCd,
        product_name: (s.product_name ?? '').trim() || productCd,
        session_count: 0,
        sum_actual_qty: 0,
        sum_defect_qty: 0,
        sum_net_production_sec: 0,
      })
    }
    const prod = map.get(productCd)!
    prod.session_count = (prod.session_count ?? 0) + 1
    prod.sum_actual_qty = (prod.sum_actual_qty ?? 0) + Number(s.actual_production_quantity ?? 0)
    prod.sum_defect_qty = (prod.sum_defect_qty ?? 0) + Number(s.defect_qty ?? 0)
    prod.sum_net_production_sec =
      (prod.sum_net_production_sec ?? 0) + Number(s.net_production_sec ?? s.mes_net_production_sec ?? 0)
  }

  return [...map.values()]
    .map((row) => {
      const actual = row.sum_actual_qty ?? 0
      const defect = row.sum_defect_qty ?? 0
      return {
        ...row,
        defect_rate_percent: actual > 0 ? Math.round((defect / actual) * 1000) / 10 : null,
        avg_efficiency_per_hour: periodAvgEfficiencyFromBucket(row),
      }
    })
    .sort((a, b) => (b.sum_actual_qty ?? 0) - (a.sum_actual_qty ?? 0))
}

function buildReportFilters(): WeldingProductivityReportFilters | null {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) return null

  let operatorFilterLabel = '（すべて）'
  if (filterOperatorId.value !== '') {
    const found = operatorOptions.value.find((u) => u.id === filterOperatorId.value)
    operatorFilterLabel = found ? operatorLabel(found) : `#${filterOperatorId.value}`
  }

  let productFilterLabel = '（すべて）'
  if (filterProductCd.value) {
    const found = productOptions.value.find((p) => p.product_cd === filterProductCd.value)
    productFilterLabel = found
      ? `${found.product_cd} · ${(found.product_name ?? '').trim() || found.product_cd}`
      : filterProductCd.value
  }

  return {
    startDate: start,
    endDate: end,
    operatorLabel: operatorFilterLabel,
    productLabel: productFilterLabel,
    includeIncomplete: includeIncomplete.value,
  }
}

function buildReportContext(): WeldingProductivityReportContext | null {
  const filters = buildReportFilters()
  if (!analysisData.value || !filters) return null

  return {
    filters,
    kpiCards: kpiCards.value.map((card) => ({
      label: card.label,
      value: card.value,
      hint: card.hint,
      tone: card.tone as 'indigo' | 'sky' | 'amber' | 'emerald' | 'violet',
    })),
    charts: {
      daily: captureChartDataUrl(dailyChart),
      operator: captureChartDataUrl(operatorChart),
      product: captureChartDataUrl(productChart),
      productRank: captureChartDataUrl(productRankChart),
    },
    operatorRows: operatorDisplayRows.value,
    productRows: productDisplayRows.value,
    operatorSectionAvgEfficiency: operatorSectionAvgEfficiency.value,
    productSectionTotalQty: productSectionTotalQty.value,
    productRank: {
      selected: selectedProductRanking.value,
      topOverview: productRankTopOverview.value,
      stats: selectedProductRankStats.value,
    },
  }
}

async function prepareChartsForReport(command: string) {
  if (command === 'print-full' || command === 'print-daily') dailyChart?.resize()
  if (command === 'print-full' || command === 'print-operator') operatorChart?.resize()
  if (command === 'print-full' || command === 'print-product') productChart?.resize()
  if (command === 'print-product-rank' || command === 'print-full') {
    await nextTick()
    await renderProductRankChart()
    productRankChart?.resize()
  }
}

async function handleReportCommand(command: string | number | object) {
  const cmd = String(command)

  if (!analysisData.value) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  exportBusy.value = true
  try {
    if (cmd === 'print-daily-batch') {
      await handleBatchDailyByOperatorPrint()
      return
    }

    if (cmd === 'print-operator-product-batch') {
      await handleBatchOperatorProductPrint()
      return
    }

    await prepareChartsForReport(cmd)
    const ctx = buildReportContext()
    if (!ctx) {
      ElMessage.warning('出力する分析データがありません')
      return
    }

    if (cmd === 'print-full') {
      printWeldingProductivityReport(ctx)
      return
    }

    const sectionMap: Record<string, WeldingProductivityPrintSection> = {
      'print-daily': 'daily',
      'print-operator': 'operator',
      'print-product': 'product',
      'print-product-rank': 'product-rank',
    }
    const section = sectionMap[cmd]
    if (section) {
      printWeldingProductivitySection(section, ctx)
      return
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : 'レポート出力に失敗しました')
  } finally {
    exportBusy.value = false
  }
}

function captureChartDataUrl(chart: ECharts | null): string | null {
  if (!chart || chart.isDisposed()) return null
  try {
    return chart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#ffffff',
    })
  } catch {
    return null
  }
}

function waitForChartPaint(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

async function captureDailyChartDataUrl(daily: WeldingProductivityDailyRow[]): Promise<string | null> {
  if (!daily.length) return null
  const el = document.createElement('div')
  el.style.cssText =
    'position:fixed;left:0;top:0;width:960px;height:380px;opacity:0;pointer-events:none;z-index:-1;overflow:hidden;'
  document.body.appendChild(el)
  let chart: ECharts | null = null
  try {
    chart = echarts.init(el, undefined, CHART_INIT_OPTS)
    chart.setOption(
      createDailyTrendChartOption(daily, chartTheme(), chartFormatters, EFFICIENCY_UNIT, { forExport: true }),
      { notMerge: true },
    )
    chart.resize()
    await waitForChartPaint()
    const url = chart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#ffffff',
    })
    return url.startsWith('data:image') ? url : null
  } catch {
    return null
  } finally {
    chart?.dispose()
    el.remove()
  }
}

async function handleBatchDailyByOperatorPrint() {
  const filters = buildReportFilters()
  const [start, end] = dateRange.value ?? []
  if (!filters || !start || !end) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  const operators = operatorOptions.value
  if (!operators.length) {
    ElMessage.warning('溶接作業者が登録されていません')
    return
  }

  const items: WeldingProductivityDailyBatchItem[] = []
  for (const op of operators) {
    const res = await fetchWeldingProductivityAnalysis({
      start_date: start,
      end_date: end,
      mes_operator_user_id: op.id,
      product_cd: filterProductCd.value || null,
      include_incomplete: includeIncomplete.value,
    })
    if (!res.success || !res.data) continue
    const daily = res.data.daily ?? []
    if (!daily.length) continue
    const chartSrc = await captureDailyChartDataUrl(daily)
    if (!chartSrc) continue
    const summary = res.data.summary
    items.push({
      operatorUserId: op.id,
      operatorLabel: operatorLabel(op),
      chartSrc,
      dayCount: daily.length,
      sumActualQty: summary?.sum_actual_qty ?? 0,
      avgEfficiencyPerHour: summary?.efficiency_per_hour ?? null,
    })
  }
  if (!items.length) {
    ElMessage.warning('印刷できる日別データがありません')
    return
  }

  printWeldingProductivityDailyBatch(filters, items)
}

async function handleBatchOperatorProductPrint() {
  const filters = buildReportFilters()
  const [start, end] = dateRange.value ?? []
  if (!filters || !start || !end) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  const operators = operatorOptions.value
  if (!operators.length) {
    ElMessage.warning('溶接作業者が登録されていません')
    return
  }

  const res = await fetchWeldingProductivityAnalysis({
    start_date: start,
    end_date: end,
    product_cd: filterProductCd.value || null,
    include_incomplete: includeIncomplete.value,
  })
  if (!res.success || !res.data) {
    ElMessage.warning('分析データの取得に失敗しました')
    return
  }

  const sessions = res.data.sessions ?? []
  const items: WeldingProductivityOperatorProductBatchItem[] = []

  for (const op of operators) {
    const rows = buildOperatorProductRows(sessions, String(op.id), () => true)
    if (!rows.length) continue

    const sessionCount = rows.reduce((sum, row) => sum + Number(row.session_count ?? 0), 0)
    const sumActualQty = rows.reduce((sum, row) => sum + Number(row.sum_actual_qty ?? 0), 0)
    const totalSec = rows.reduce((sum, row) => sum + Number(row.sum_net_production_sec ?? 0), 0)
    const avgEfficiencyPerHour =
      sumActualQty > 0 && totalSec > 0 ? Math.round(sumActualQty / (totalSec / 3600)) : null

    items.push({
      operatorLabel: operatorLabel(op),
      productCount: rows.length,
      sessionCount,
      sumActualQty,
      avgEfficiencyPerHour,
      productRows: rows,
    })
  }

  if (!items.length) {
    ElMessage.warning('印刷できる溶接作業者別製品データがありません')
    return
  }

  items.sort((a, b) => (b.avgEfficiencyPerHour ?? -1) - (a.avgEfficiencyPerHour ?? -1))
  printWeldingProductivityOperatorProductBatch(filters, items)
}

function productOptionLabel(p: Product): string {
  const name = (p.product_name ?? '').trim()
  return name || p.product_cd
}

async function loadProductOptions() {
  loadingProductOptions.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = filterWeldingSelectableProducts(list)
  } catch {
    productOptions.value = []
  } finally {
    loadingProductOptions.value = false
  }
}

function defectLabel(defectCd: string): string {
  const cd = (defectCd ?? '').trim()
  return defectLabelMap.value.get(cd) ?? resolveMesDefectItemLabel(cd, cd, t, te)
}

async function loadOperators() {
  try {
    operatorOptions.value = await fetchWeldingSectionOperators()
    const allowed = new Set(operatorOptions.value.map((u) => u.id))
    if (filterOperatorId.value !== '' && !allowed.has(filterOperatorId.value)) {
      filterOperatorId.value = ''
    }
  } catch {
    operatorOptions.value = []
  }
}

async function loadDefectLabels() {
  try {
    const items = await loadMesDefectItemsForProcess('KT07')
    const map = new Map<string, string>()
    for (const item of items) map.set(item.id, item.label)
    defectLabelMap.value = map
  } catch {
    defectLabelMap.value = new Map()
  }
}

let analysisRequestSeq = 0
let analysisDebounceTimer: ReturnType<typeof setTimeout> | null = null

async function loadAnalysis(options?: { silent?: boolean }) {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) {
    if (!options?.silent) ElMessage.warning('集計期間を指定してください')
    return
  }
  const seq = ++analysisRequestSeq
  contentVisible.value = false
  loading.value = true
  try {
    const res = await fetchWeldingProductivityAnalysis({
      start_date: start,
      end_date: end,
      mes_operator_user_id: filterOperatorId.value,
      product_cd: filterProductCd.value || null,
      include_incomplete: includeIncomplete.value,
    })
    if (seq !== analysisRequestSeq) return
    if (!res.success || !res.data) throw new Error(res.message || '分析データの取得に失敗しました')
    analysisData.value = res.data
    syncRankProductSelection()
    await nextTick()
    contentVisible.value = true
    await nextTick()
    renderCharts()
    await renderProductRankChart()
  } catch (err) {
    if (seq !== analysisRequestSeq) return
    analysisData.value = null
    ElMessage.error(err instanceof Error ? err.message : '分析データの取得に失敗しました')
  } finally {
    if (seq === analysisRequestSeq) loading.value = false
  }
}

function scheduleLoadAnalysis() {
  if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer)
  analysisDebounceTimer = setTimeout(() => {
    analysisDebounceTimer = null
    void loadAnalysis({ silent: true })
  }, 350)
}

function disposeCharts() {
  dailyChart?.dispose()
  operatorChart?.dispose()
  productChart?.dispose()
  productRankChart?.dispose()
  dailyChart = null
  operatorChart = null
  productChart = null
  productRankChart = null
}

function renderCharts() {
  disposeCharts()
  const data = analysisData.value
  if (!data) return
  const theme = chartTheme()

  const dailyEl = dailyChartRef.value
  if (dailyEl && data.daily.length > 0) {
    dailyChart = echarts.init(dailyEl, undefined, CHART_INIT_OPTS)
    dailyChart.setOption(createDailyTrendChartOption(data.daily, theme, chartFormatters, EFFICIENCY_UNIT))
  }

  const operatorEl = operatorChartRef.value
  const operatorRows = operatorDisplayRows.value
  if (operatorEl && operatorRows.length > 0) {
    operatorChart = echarts.init(operatorEl, undefined, CHART_INIT_OPTS)
    operatorChart.setOption(
      createPersonBarChartOption(
        operatorRows.map((row) => ({
          person_name: row.operator_name,
          avg_efficiency_per_hour: row.avg_efficiency_per_hour,
          sum_actual_qty: row.sum_actual_qty,
          defect_rate_percent: row.defect_rate_percent,
        })),
        theme,
        chartFormatters,
        EFFICIENCY_UNIT,
      ),
    )
  }

  const productEl = productChartRef.value
  const productRows = productDisplayRows.value
  if (productEl && productRows.length > 0) {
    productChart = echarts.init(productEl, undefined, CHART_INIT_OPTS)
    productChart.setOption(createProductBarChartOption(productRows, theme, chartFormatters, EFFICIENCY_UNIT))
  }
}

async function waitForProductRankChartEl(): Promise<HTMLElement | null> {
  for (let i = 0; i < 6; i += 1) {
    await nextTick()
    const el = productRankChartRef.value
    if (el) return el
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => resolve())
    })
  }
  return productRankChartRef.value
}

async function renderProductRankChart(theme = chartTheme()) {
  const ranking = selectedProductRanking.value
  const rows = (ranking?.operators ?? []).filter((r) => r.efficiency_per_hour != null)
  if (!rows.length) {
    productRankChart?.dispose()
    productRankChart = null
    return
  }

  const el = await waitForProductRankChartEl()
  if (!el) return

  productRankChart?.dispose()
  productRankChart = null
  productRankChart = echarts.init(el, undefined, CHART_INIT_OPTS)
  productRankChart.setOption(
    createProductRankChartOption(
      rows.map((row) => ({
        person_name: row.operator_name,
        rank: row.rank,
        efficiency_per_hour: row.efficiency_per_hour,
        sum_actual_qty: row.sum_actual_qty,
        defect_rate_percent: row.defect_rate_percent,
      })),
      theme,
      chartFormatters,
      EFFICIENCY_UNIT,
    ),
  )
  await nextTick()
  productRankChart.resize()
}

function handleResize() {
  dailyChart?.resize()
  operatorChart?.resize()
  productChart?.resize()
  productRankChart?.resize()
}

watch(rankViewProductCd, async () => {
  await renderProductRankChart()
})

watch(
  () => selectedProductRanking.value?.product_cd,
  async () => {
    if (!contentVisible.value) return
    await renderProductRankChart()
  },
)

watch(dateRange, () => {
  scheduleLoadAnalysis()
}, { deep: true })
watch(filterOperatorId, scheduleLoadAnalysis)
watch(filterProductCd, scheduleLoadAnalysis)
watch(includeIncomplete, scheduleLoadAnalysis)

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  await Promise.all([loadOperators(), loadDefectLabels(), loadProductOptions()])
  await loadAnalysis({ silent: true })
})

onBeforeUnmount(() => {
  if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer)
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<style scoped lang="scss">
@use './ipaProductivityAnalysis.shared.scss' as *;
</style>

<style>
.ipa-report-dropdown.el-popper {
  border: 1px solid rgba(226, 232, 240, 0.9) !important;
  border-radius: 14px !important;
  padding: 6px !important;
  background: rgba(255, 255, 255, 0.98) !important;
  backdrop-filter: blur(14px);
  box-shadow:
    0 20px 50px rgba(15, 23, 42, 0.14),
    0 4px 14px rgba(99, 102, 241, 0.08) !important;
}

.ipa-report-dropdown .el-popper__arrow::before {
  border-color: rgba(226, 232, 240, 0.9) !important;
  background: rgba(255, 255, 255, 0.98) !important;
}

.ipa-report-dropdown .ipa-report-menu {
  padding: 4px;
  background: transparent;
  border: none;
  box-shadow: none;
}

.ipa-report-dropdown .el-dropdown-menu__item {
  padding: 0;
  line-height: normal;
  border-radius: 10px;
  margin: 0 0 3px;
}

.ipa-report-dropdown .el-dropdown-menu__item:last-child {
  margin-bottom: 0;
}

.ipa-report-dropdown .el-dropdown-menu__item--divided {
  margin-top: 6px;
  border-top: 1px solid rgba(226, 232, 240, 0.85);
  padding-top: 6px;
}

.ipa-report-dropdown .ipa-report-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  min-width: 300px;
  transition: background 0.18s ease, transform 0.18s ease;
}

.ipa-report-dropdown .ipa-report-item__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  font-size: 15px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.ipa-report-dropdown .ipa-report-item__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.ipa-report-dropdown .ipa-report-item__label {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.35;
}

.ipa-report-dropdown .ipa-report-item__hint {
  font-size: 10px;
  font-weight: 500;
  color: #94a3b8;
  line-height: 1.3;
}

.ipa-report-dropdown .ipa-report-item--indigo .ipa-report-item__icon-wrap {
  color: #4f46e5;
  background: linear-gradient(145deg, #eef2ff, #e0e7ff);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.18);
}

.ipa-report-dropdown .ipa-report-item--sky .ipa-report-item__icon-wrap {
  color: #0284c7;
  background: linear-gradient(145deg, #e0f2fe, #bae6fd);
  box-shadow: 0 2px 6px rgba(14, 165, 233, 0.18);
}

.ipa-report-dropdown .ipa-report-item--teal .ipa-report-item__icon-wrap {
  color: #0d9488;
  background: linear-gradient(145deg, #ccfbf1, #99f6e4);
  box-shadow: 0 2px 6px rgba(20, 184, 166, 0.18);
}

.ipa-report-dropdown .ipa-report-item--violet .ipa-report-item__icon-wrap {
  color: #7c3aed;
  background: linear-gradient(145deg, #f3e8ff, #e9d5ff);
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.18);
}

.ipa-report-dropdown .ipa-report-item--emerald .ipa-report-item__icon-wrap {
  color: #059669;
  background: linear-gradient(145deg, #d1fae5, #a7f3d0);
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.18);
}

.ipa-report-dropdown .ipa-report-item--amber .ipa-report-item__icon-wrap {
  color: #d97706;
  background: linear-gradient(145deg, #fef3c7, #fde68a);
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.18);
}

.ipa-report-dropdown .ipa-report-item--rose .ipa-report-item__icon-wrap {
  color: #e11d48;
  background: linear-gradient(145deg, #ffe4e6, #fecdd3);
  box-shadow: 0 2px 6px rgba(244, 63, 94, 0.18);
}

.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item {
  background: rgba(248, 250, 252, 0.95);
}

.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item__icon-wrap {
  transform: scale(1.06);
}

.ipa-report-dropdown .ipa-report-item--indigo:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--indigo {
  background: rgba(238, 242, 255, 0.75);
}

.ipa-report-dropdown .ipa-report-item--sky:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--sky {
  background: rgba(224, 242, 254, 0.75);
}

.ipa-report-dropdown .ipa-report-item--teal:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--teal {
  background: rgba(204, 251, 241, 0.75);
}

.ipa-report-dropdown .ipa-report-item--violet:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--violet {
  background: rgba(243, 232, 255, 0.75);
}

.ipa-report-dropdown .ipa-report-item--emerald:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--emerald {
  background: rgba(209, 250, 229, 0.75);
}

.ipa-report-dropdown .ipa-report-item--amber:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--amber {
  background: rgba(254, 243, 199, 0.75);
}

.ipa-report-dropdown .ipa-report-item--rose:hover,
.ipa-report-dropdown .el-dropdown-menu__item:not(.is-disabled):hover .ipa-report-item--rose {
  background: rgba(255, 228, 230, 0.75);
}

.ipa-report-dropdown .el-dropdown-menu__item:focus {
  background: transparent;
  color: inherit;
}
</style>
