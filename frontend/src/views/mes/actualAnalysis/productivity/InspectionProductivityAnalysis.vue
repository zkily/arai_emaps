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
          <el-icon :size="24"><DocumentChecked /></el-icon>
          <span class="ipa-hero__icon-glow" />
        </div>
        <div class="ipa-hero__text">
          <div class="ipa-hero__eyebrow">MES · 実績分析</div>
          <h1 class="ipa-hero__title">検査工程 — 生産性分析</h1>
          <p class="ipa-hero__meta"> 実績 · 能率 · 不良率 · 稼働</p>
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
          <span class="ipa-field__pill"><el-icon><User /></el-icon>検査員</span>
          <el-select
            v-model="filterInspectorId"
            placeholder="すべて"
            clearable
            filterable
            size="small"
            class="ipa-field__control ipa-field__inspector-select"
          >
            <el-option label="（すべて）" value="" />
            <el-option v-for="u in inspectorOptions" :key="u.id" :label="inspectorLabel(u)" :value="u.id" />
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
                  <span class="ipa-panel__title">検査員別</span>
                </div>
                <div class="ipa-panel__badges">
                  <span class="ipa-panel__badge ipa-panel__badge--soft">{{ inspectorDisplayRows.length }} 名</span>
                  <span v-if="inspectorSectionAvgEfficiency != null" class="ipa-panel__badge ipa-panel__badge--inspector">
                    平均能率 {{ fmtEfficiency(inspectorSectionAvgEfficiency) }} 本/時
                  </span>
                </div>
              </div>
              <div ref="inspectorChartRef" class="ipa-chart ipa-chart--side ipa-chart--inspector" />
              <el-table
                :data="inspectorDisplayRows"
                size="small"
                stripe
                class="ipa-table ipa-table--inspector"
                max-height="240"
              >
                <el-table-column label="#" width="36" align="center">
                  <template #default="{ $index }">
                    <span class="ipa-row-rank" :class="inspectorRankClass($index)">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="inspector_name" label="検査員" min-width="96" show-overflow-tooltip />
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

          <div v-if="analysisData" class="ipa-weld-rank-split ipa-fade-in ipa-fade-in--d5a">
            <section class="ipa-panel ipa-panel--weld-rank ipa-panel--weld-rank--off">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico ipa-panel__ico--weld-off"><User /></el-icon>
                  <div>
                    <span class="ipa-panel__title">検査員平均能率ランキング</span>
                    <span class="ipa-panel__subtitle">溶接工程なし製品</span>
                  </div>
                </div>
                <span class="ipa-panel__badge ipa-panel__badge--weld-off">{{ inspectorRankWithoutWelding.length }} 名</span>
              </div>
              <el-table
                :data="inspectorRankWithoutWelding"
                size="small"
                stripe
                class="ipa-table ipa-table--weld-off"
                max-height="300"
                empty-text="対象データがありません"
              >
                <el-table-column label="順位" width="52" align="center">
                  <template #default="{ row }">
                    <span class="ipa-rank-badge" :class="rankBadgeClass(row.rank)">{{ row.rank }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="検査員" min-width="96" show-overflow-tooltip>
                  <template #default="{ row }">
                    <button
                      type="button"
                      class="ipa-inspector-link ipa-inspector-link--weld-off"
                      @click="openInspectorProductDialog(row, 'no-welding')"
                    >
                      {{ row.inspector_name }}
                    </button>
                  </template>
                </el-table-column>
                <el-table-column label="件" width="40" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="64" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良率" width="60" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="平均能率" width="68" align="right">
                  <template #default="{ row }">
                    <span class="ipa-eff-pill ipa-eff-pill--weld-off">{{ fmtEfficiency(row.avg_efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>

            <section class="ipa-panel ipa-panel--weld-rank ipa-panel--weld-rank--on">
              <div class="ipa-panel__head">
                <div class="ipa-panel__title-wrap">
                  <el-icon class="ipa-panel__ico ipa-panel__ico--weld-on"><User /></el-icon>
                  <div>
                    <span class="ipa-panel__title">検査員平均能率ランキング</span>
                    <span class="ipa-panel__subtitle">溶接工程あり製品</span>
                  </div>
                </div>
                <span class="ipa-panel__badge ipa-panel__badge--weld-on">
                  {{ inspectorRankWithWelding.length }} 名 · BOM {{ weldingProductBomCount }} 品目
                </span>
              </div>
              <p v-if="weldingProductBomCount === 0" class="ipa-weld-rank-hint ipa-weld-rank-hint--warn">
                製品工程BOMに溶接工程の登録がありません。マスタで溶接フラグを確認してください。
              </p>
              <el-table
                :data="inspectorRankWithWelding"
                size="small"
                stripe
                class="ipa-table ipa-table--weld-on"
                max-height="300"
                empty-text="溶接工程あり製品の検査実績がありません"
              >
                <el-table-column label="順位" width="52" align="center">
                  <template #default="{ row }">
                    <span class="ipa-rank-badge" :class="rankBadgeClass(row.rank)">{{ row.rank }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="検査員" min-width="96" show-overflow-tooltip>
                  <template #default="{ row }">
                    <button
                      type="button"
                      class="ipa-inspector-link ipa-inspector-link--weld-on"
                      @click="openInspectorProductDialog(row, 'with-welding')"
                    >
                      {{ row.inspector_name }}
                    </button>
                  </template>
                </el-table-column>
                <el-table-column label="件" width="40" align="right">
                  <template #default="{ row }">{{ row.session_count }}</template>
                </el-table-column>
                <el-table-column label="生産" width="64" align="right">
                  <template #default="{ row }">{{ fmtInt(row.sum_actual_qty) }}</template>
                </el-table-column>
                <el-table-column label="不良率" width="60" align="right">
                  <template #default="{ row }"><span class="ipa-num ipa-num--warn">{{ fmtPct(row.defect_rate_percent) }}</span></template>
                </el-table-column>
                <el-table-column label="平均能率" width="68" align="right">
                  <template #default="{ row }">
                    <span class="ipa-eff-pill ipa-eff-pill--weld-on">{{ fmtEfficiency(row.avg_efficiency_per_hour) }}</span>
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
                  <span class="ipa-panel__title">製品別 · 検査員能率ランキング</span>
                  <div class="ipa-rank-panel__desc">製品ごとの検査員能率を順位付けして比較</div>
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
                      <span class="ipa-rank-hero__stat-label">検査員</span>
                      <span class="ipa-rank-hero__stat-val">{{ selectedProductRankStats.inspectorCount }}<small>名</small></span>
                    </div>
                    <div class="ipa-rank-hero__stat ipa-rank-hero__stat--accent">
                      <span class="ipa-rank-hero__stat-label">TOP能率</span>
                      <span class="ipa-rank-hero__stat-val">{{ fmtEfficiency(selectedProductRankStats.topEfficiency) }}<small>本/時</small></span>
                    </div>
                    <div class="ipa-rank-hero__stat">
                      <span class="ipa-rank-hero__stat-label">平均能率</span>
                      <span class="ipa-rank-hero__stat-val">{{ fmtEfficiency(selectedProductRankStats.avgEfficiency) }}<small>本/時</small></span>
                    </div>
                  </div>
                </div>

                <div v-if="podiumInspectors.length" class="ipa-podium ipa-podium--hd">
                  <div
                    v-for="(item, idx) in podiumInspectors"
                    :key="item.inspector_user_id ?? item.inspector_name"
                    class="ipa-podium__col"
                    :class="`ipa-podium__col--${item.rank}`"
                    :style="{ '--podium-delay': `${idx * 0.1}s` }"
                  >
                    <div class="ipa-podium__item" :class="`ipa-podium__item--${item.rank}`">
                      <div v-if="item.rank === 1" class="ipa-podium__crown" aria-hidden="true">👑</div>
                      <div class="ipa-podium__medal-wrap">
                        <span class="ipa-podium__medal">{{ rankMedal(item.rank) }}</span>
                      </div>
                      <div class="ipa-podium__name" :title="item.inspector_name">{{ item.inspector_name }}</div>
                      <div class="ipa-podium__eff">{{ fmtEfficiency(item.efficiency_per_hour) }}</div>
                      <div class="ipa-podium__sub">本/時</div>
                    </div>
                    <div class="ipa-podium__pedestal" :style="{ height: podiumPedestalHeight(item.rank) }">
                      <span class="ipa-podium__pedestal-rank">{{ item.rank }}</span>
                    </div>
                  </div>
                </div>

                <div class="ipa-rank-chart-block">
                  <div class="ipa-rank-chart-block__head">
                    <span class="ipa-rank-chart-block__title">検査員別能率</span>
                    <span class="ipa-rank-chart-block__badge">{{ selectedProductRanking.inspectors.length }} 名</span>
                  </div>
                  <div ref="productRankChartRef" class="ipa-chart ipa-chart--rank" />
                </div>

                <el-table
                  :data="selectedProductRanking.inspectors"
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
                  <el-table-column prop="inspector_name" label="検査員" min-width="120" show-overflow-tooltip />
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
                  <el-table-column label="不良率" width="76" align="right" sortable :sort-method="sortByInspectorDefectRate">
                    <template #default="{ row }">
                      <span class="ipa-eff-pill ipa-eff-pill--warn">{{ fmtPct(row.defect_rate_percent) }}</span>
                    </template>
                  </el-table-column>
                </el-table>

                <div v-if="!selectedProductRanking.inspectors.length" class="ipa-rank-empty">
                  <el-icon :size="28" class="ipa-rank-empty__ico"><WarningFilled /></el-icon>
                  <p>能率を算出できる検査員データがありません</p>
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
                <el-table-column label="TOP検査員" min-width="110" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="ipa-rank-top-inspector">{{ row.top_inspector_name ?? '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="能率" width="76" align="right">
                  <template #default="{ row }">
                    <span class="ipa-eff-pill ipa-eff-pill--rank">{{ fmtEfficiency(row.top_efficiency_per_hour) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="対象人数" width="72" align="center">
                  <template #default="{ row }">{{ row.ranked_inspector_count ?? 0 }}</template>
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
                <span class="ipa-panel__title">不良内訳（KT09）</span>
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
                <button
                  type="button"
                  class="ipa-session-csv-btn"
                  :disabled="sessionExportBusy"
                  @click="handleExportSessionsCsv"
                >
                  <el-icon><Download /></el-icon>
                  CSV
                </button>
              </div>
            </div>
            <el-table :data="analysisData.sessions" size="small" class="ipa-table ipa-table--detail" max-height="380">
              <el-table-column prop="production_day" label="生産日" width="102" fixed />
              <el-table-column prop="inspector_display_name" label="検査員" width="100" show-overflow-tooltip />
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

    <el-dialog
      v-model="inspectorProductDialogVisible"
      width="600px"
      :class="[
        'ipa-inspector-product-dialog',
        inspectorProductDialogScope === 'with-welding'
          ? 'ipa-inspector-product-dialog--weld-on'
          : 'ipa-inspector-product-dialog--weld-off',
      ]"
      destroy-on-close
      append-to-body
    >
      <template #header>
        <div v-if="inspectorProductDialogTarget" class="ipa-insp-prod-dlg__header">
          <div class="ipa-insp-prod-dlg__avatar">
            <el-icon :size="20"><User /></el-icon>
          </div>
          <div class="ipa-insp-prod-dlg__head-text">
            <div class="ipa-insp-prod-dlg__title">{{ inspectorProductDialogTarget.inspector_name }}</div>
            <div class="ipa-insp-prod-dlg__subtitle">生産製品一覧 · {{ inspectorProductDialogScopeLabel }}</div>
          </div>
        </div>
      </template>

      <div v-if="inspectorProductDialogTarget" class="ipa-insp-prod-dlg__body">
        <div class="ipa-insp-prod-dlg__summary">
          <div class="ipa-insp-prod-dlg__stat">
            <span class="ipa-insp-prod-dlg__stat-label">品目数</span>
            <span class="ipa-insp-prod-dlg__stat-value">{{ inspectorProductDialogRows.length }}</span>
          </div>
          <div class="ipa-insp-prod-dlg__stat">
            <span class="ipa-insp-prod-dlg__stat-label">セッション</span>
            <span class="ipa-insp-prod-dlg__stat-value">{{ fmtInt(inspectorProductDialogStats.sessionCount) }}</span>
          </div>
          <div class="ipa-insp-prod-dlg__stat">
            <span class="ipa-insp-prod-dlg__stat-label">生産合計</span>
            <span class="ipa-insp-prod-dlg__stat-value">{{ fmtInt(inspectorProductDialogStats.totalQty) }}</span>
          </div>
          <div class="ipa-insp-prod-dlg__stat ipa-insp-prod-dlg__stat--accent">
            <span class="ipa-insp-prod-dlg__stat-label">平均能率</span>
            <span class="ipa-insp-prod-dlg__stat-value">
              {{ fmtEfficiency(inspectorProductDialogTarget.avg_efficiency_per_hour) }}
              <small>本/時</small>
            </span>
          </div>
        </div>
        <div class="ipa-insp-prod-dlg__period">
          集計期間 {{ analysisData?.start_date }} ～ {{ analysisData?.end_date }}
        </div>
        <el-table
          :data="inspectorProductDialogRows"
          size="small"
          stripe
          class="ipa-table ipa-insp-prod-dlg__table"
          max-height="380"
          empty-text="該当する製品実績がありません"
        >
          <el-table-column prop="product_cd" label="CD" width="88">
            <template #default="{ row }">
              <span class="ipa-product-cd ipa-product-cd--dlg">{{ row.product_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="製品名" min-width="132" show-overflow-tooltip />
          <el-table-column label="件" width="44" align="right">
            <template #default="{ row }">{{ row.session_count }}</template>
          </el-table-column>
          <el-table-column label="生産" width="72" align="right">
            <template #default="{ row }">
              <span class="ipa-num ipa-num--dlg-qty">{{ fmtInt(row.sum_actual_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="不良率" width="72" align="right" sortable :sort-method="sortByProductDefectRate">
            <template #default="{ row }">
              <span class="ipa-eff-pill ipa-eff-pill--warn">{{ fmtPct(row.defect_rate_percent) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="64" align="right" sortable :sort-method="sortByProductEfficiency">
            <template #default="{ row }">
              <span
                class="ipa-eff-pill"
                :class="
                  inspectorProductDialogScope === 'with-welding'
                    ? 'ipa-eff-pill--weld-on'
                    : 'ipa-eff-pill--weld-off'
                "
              >
                {{ fmtEfficiency(row.avg_efficiency_per_hour) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
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
  Document,
  DocumentChecked,
  Download,
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
  fetchInspectionManagementInspectors,
  fetchInspectionProductivityAnalysis,
  type InspectionManagementInspectorOption,
  type InspectionProductivityAnalysisData,
  type InspectionProductivityBucket,
  type InspectionProductivityDailyRow,
  type InspectionProductivityInspectorRow,
  type InspectionProductivityProductInspectorRanking,
  type InspectionProductivityProductRow,
  type InspectionProductivitySessionRow,
} from '@/api/inspectionManagement'
import { fetchProductProcessBOMList } from '@/api/master/productProcessBomMaster'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'
import { getJSTToday, parseDateAsJST } from '@/utils/dateFormat'
import { filterInspectionSelectableProducts } from '@/views/mes/shared/inspectionProductFilter'
import {
  loadMesDefectItemsForProcess,
  resolveMesDefectItemLabel,
} from '@/views/mes/actualDataCollection/shared/loadProcessDefectItems'
import {
  exportInspectionSessionsCsv,
  printInspectionProductivityDailyBatch,
  printInspectionProductivityInspectorProductBatch,
  printInspectionProductivityReport,
  printInspectionProductivitySection,
  type InspectionProductivityDailyBatchItem,
  type InspectionProductivityInspectorProductBatchItem,
  type InspectionProductivityPrintSection,
  type InspectionProductivityReportContext,
  type InspectionProductivityReportFilters,
} from './inspectionProductivityReport'

defineOptions({ name: 'MesInspectionProductivityAnalysis' })

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
    label: '日別推移（検査員別・一括印刷）',
    hint: '検査員ごとに分割出力',
    icon: markRaw(DataAnalysis),
    tone: 'teal',
  },
  {
    command: 'print-inspector',
    label: '検査員別（印刷）',
    hint: '検査員別サマリー',
    icon: markRaw(User),
    tone: 'violet',
  },
  {
    command: 'print-inspector-product-batch',
    label: '検査員別製品別（検査員別・一括印刷）',
    hint: '検査員ごとに製品一覧を出力',
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
    command: 'print-weld-rank',
    label: '検査員平均能率ランキング（印刷）',
    hint: '溶接あり / なし比較',
    icon: markRaw(Trophy),
    tone: 'amber',
  },
  {
    command: 'print-product-rank',
    label: '製品別 · 検査員能率ランキング（印刷）',
    hint: '製品単位の順位表',
    icon: markRaw(List),
    tone: 'rose',
  },
]

const { t, te } = useI18n()

const loading = ref(false)
const exportBusy = ref(false)
const sessionExportBusy = ref(false)
const contentVisible = ref(false)
const analysisData = ref<InspectionProductivityAnalysisData | null>(null)
const inspectorOptions = ref<InspectionManagementInspectorOption[]>([])
const filterInspectorId = ref<number | ''>('')
const filterProductCd = ref('')
const includeIncomplete = ref(false)
const productOptions = ref<Product[]>([])
const loadingProductOptions = ref(false)
const defectLabelMap = ref<Map<string, string>>(new Map())
const weldingProductCdSet = ref<Set<string>>(new Set())
const rankViewProductCd = ref('')
const dailyChartRef = ref<HTMLElement | null>(null)
const inspectorChartRef = ref<HTMLElement | null>(null)
const productChartRef = ref<HTMLElement | null>(null)
const productRankChartRef = ref<HTMLElement | null>(null)
let dailyChart: ECharts | null = null
let inspectorChart: ECharts | null = null
let productChart: ECharts | null = null
let productRankChart: ECharts | null = null

function shiftJstDate(isoDay: string, deltaDays: number): string {
  const base = parseDateAsJST(isoDay)
  if (!base) return isoDay
  base.setDate(base.getDate() + deltaDays)
  return base.toISOString().slice(0, 10)
}

const dateRange = ref<[string, string]>([shiftJstDate(getJSTToday(), -29), getJSTToday()])

const emptySummary = (): InspectionProductivityBucket => ({
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

const productRankList = computed((): InspectionProductivityProductInspectorRanking[] => {
  const fromApi = analysisData.value?.by_product_inspector_ranking
  if (fromApi?.length) return fromApi
  return buildProductInspectorRankingFromSessions(analysisData.value?.sessions ?? [])
})

function buildProductInspectorRankingFromSessions(
  sessions: InspectionProductivityAnalysisData['sessions'],
): InspectionProductivityProductInspectorRanking[] {
  const productMap = new Map<
    string,
    {
      product_cd: string
      product_name: string
      sum_actual_qty: number
      session_count: number
      inspectors: Map<string, InspectionProductivityInspectorRow>
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
        inspectors: new Map(),
      })
    }
    const prod = productMap.get(productCd)!
    prod.sum_actual_qty += Number(s.actual_production_quantity ?? 0)
    prod.session_count += 1

    const inspId = s.mes_inspector_user_id
    const inspKey = inspId != null ? String(inspId) : 'none'
    const inspName = (s.inspector_display_name ?? s.mes_inspector_name ?? '—').trim() || '—'
    if (!prod.inspectors.has(inspKey)) {
      prod.inspectors.set(inspKey, {
        inspector_user_id: inspId ?? null,
        inspector_name: inspName,
        session_count: 0,
        sum_actual_qty: 0,
        sum_defect_qty: 0,
        sum_net_production_sec: 0,
        efficiency_per_hour: null,
      })
    }
    const inv = prod.inspectors.get(inspKey)!
    inv.session_count = (inv.session_count ?? 0) + 1
    inv.sum_actual_qty = (inv.sum_actual_qty ?? 0) + Number(s.actual_production_quantity ?? 0)
    inv.sum_defect_qty = (inv.sum_defect_qty ?? 0) + Number(s.defect_qty ?? 0)
    inv.sum_net_production_sec = (inv.sum_net_production_sec ?? 0) + Number(s.net_production_sec ?? 0)
  }

  const result: InspectionProductivityProductInspectorRanking[] = []
  for (const prod of productMap.values()) {
    const inspectors: InspectionProductivityInspectorRow[] = []
    for (const inv of prod.inspectors.values()) {
      const actual = inv.sum_actual_qty ?? 0
      const netSec = inv.sum_net_production_sec ?? 0
      const defect = inv.sum_defect_qty ?? 0
      inv.defect_rate_percent = actual > 0 ? Math.round((defect / actual) * 1000) / 10 : null
      inv.efficiency_per_hour = actual > 0 && netSec > 0 ? Math.round(actual / (netSec / 3600)) : null
      inv.sum_net_production_min = netSec > 0 ? Math.round(netSec / 60) : 0
      if (inv.efficiency_per_hour != null) inspectors.push(inv)
    }
    inspectors.sort((a, b) => (b.efficiency_per_hour ?? 0) - (a.efficiency_per_hour ?? 0))
    inspectors.forEach((row, i) => {
      row.rank = i + 1
    })
    result.push({
      product_cd: prod.product_cd,
      product_name: prod.product_name,
      sum_actual_qty: prod.sum_actual_qty,
      session_count: prod.session_count,
      inspector_count: prod.inspectors.size,
      ranked_inspector_count: inspectors.length,
      inspectors,
      top_inspector_name: inspectors[0]?.inspector_name ?? null,
      top_efficiency_per_hour: inspectors[0]?.efficiency_per_hour ?? null,
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

const podiumInspectors = computed(() => {
  const rows = selectedProductRanking.value?.inspectors ?? []
  const top3 = rows.filter((r) => (r.rank ?? 99) <= 3)
  const order = [2, 1, 3]
  return order
    .map((rank) => top3.find((r) => r.rank === rank))
    .filter((r): r is InspectionProductivityInspectorRow => r != null)
})

const productRankTopOverview = computed(() =>
  productRankList.value.filter((p) => p.top_efficiency_per_hour != null),
)

const selectedProductRankStats = computed(() => {
  const ranking = selectedProductRanking.value
  if (!ranking) return null
  const inspectors = ranking.inspectors ?? []
  const top = inspectors[0]
  let totalEff = 0
  let effCount = 0
  for (const row of inspectors) {
    if (row.efficiency_per_hour != null) {
      totalEff += row.efficiency_per_hour
      effCount += 1
    }
  }
  return {
    topEfficiency: top?.efficiency_per_hour ?? null,
    topInspector: top?.inspector_name ?? null,
    avgEfficiency: effCount > 0 ? totalEff / effCount : null,
    inspectorCount: ranking.ranked_inspector_count ?? inspectors.length,
  }
})

function productRankOptionLabel(p: InspectionProductivityProductInspectorRanking): string {
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

function podiumPedestalHeight(rank?: number): string {
  if (rank === 1) return '72px'
  if (rank === 2) return '56px'
  if (rank === 3) return '44px'
  return '36px'
}

function rankOverviewRowClass({ row }: { row: InspectionProductivityProductInspectorRanking }): string {
  return rankViewProductCd.value === row.product_cd ? 'ipa-rank-overview-row--active' : ''
}

function sortByInspectorDefectRate(
  a: InspectionProductivityInspectorRow,
  b: InspectionProductivityInspectorRow,
): number {
  return (b.defect_rate_percent ?? -1) - (a.defect_rate_percent ?? -1)
}

type InspectorDisplayRow = InspectionProductivityInspectorRow & {
  avg_efficiency_per_hour: number | null
}

/** 期間内：生産合計 ÷ 正味稼働時間（本/時） */
function periodAvgEfficiencyFromBucket(row: InspectionProductivityBucket): number | null {
  if (row.efficiency_per_hour != null && Number.isFinite(row.efficiency_per_hour)) {
    return row.efficiency_per_hour
  }
  const qty = Number(row.sum_actual_qty ?? 0)
  const sec = Number(row.sum_net_production_sec ?? 0)
  if (qty <= 0 || sec <= 0) return null
  return Math.round(qty / (sec / 3600))
}

type ProductDisplayRow = InspectionProductivityProductRow & {
  avg_efficiency_per_hour: number | null
}

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

function inspectorRankClass(index: number): string {
  if (index === 0) return 'ipa-row-rank--gold'
  if (index === 1) return 'ipa-row-rank--silver'
  if (index === 2) return 'ipa-row-rank--bronze'
  return ''
}

const inspectorDisplayRows = computed((): InspectorDisplayRow[] =>
  (analysisData.value?.by_inspector ?? [])
    .map((row) => ({
      ...row,
      avg_efficiency_per_hour: periodAvgEfficiencyFromBucket(row),
    }))
    .sort((a, b) => (b.avg_efficiency_per_hour ?? -1) - (a.avg_efficiency_per_hour ?? -1)),
)

/** 検査員別パネル：期間内の加重平均能率（全検査員の生産合計 ÷ 正味稼働合計） */
const inspectorSectionAvgEfficiency = computed((): number | null => {
  const rows = analysisData.value?.by_inspector ?? []
  let totalQty = 0
  let totalSec = 0
  for (const row of rows) {
    totalQty += Number(row.sum_actual_qty ?? 0)
    totalSec += Number(row.sum_net_production_sec ?? 0)
  }
  if (totalQty <= 0 || totalSec <= 0) return null
  return Math.round(totalQty / (totalSec / 3600))
})

function sortByEfficiency(a: InspectionProductivityInspectorRow, b: InspectionProductivityInspectorRow): number {
  return (b.efficiency_per_hour ?? -1) - (a.efficiency_per_hour ?? -1)
}

function sortByProductDefectRate(a: ProductDisplayRow, b: ProductDisplayRow): number {
  return (b.defect_rate_percent ?? -1) - (a.defect_rate_percent ?? -1)
}

function sortByProductEfficiency(a: ProductDisplayRow, b: ProductDisplayRow): number {
  return (b.avg_efficiency_per_hour ?? -1) - (a.avg_efficiency_per_hour ?? -1)
}

function isProcessFlagOn(value: unknown): boolean {
  return value === true || value === 1 || value === '1'
}

/** product_process_bom.product_cd（数値）と inspection の product_cd（文字列）を突合 */
function normalizeProductCdKey(cd: number | string | null | undefined): string {
  const raw = String(cd ?? '').trim()
  if (!raw) return ''
  if (/^\d+$/.test(raw)) return String(Number.parseInt(raw, 10))
  return raw
}

function addWeldingProductCdKeys(set: Set<string>, cd: number | string | null | undefined) {
  const raw = String(cd ?? '').trim()
  if (!raw) return
  set.add(raw)
  const normalized = normalizeProductCdKey(raw)
  if (normalized) set.add(normalized)
}

function sessionProductHasWelding(productCd: string, welding: Set<string>): boolean {
  const raw = productCd.trim()
  if (!raw) return false
  if (welding.has(raw)) return true
  const normalized = normalizeProductCdKey(raw)
  return normalized ? welding.has(normalized) : false
}

function bomRowHasWeldingProcess(row: {
  welding_process?: unknown
  outsourced_welding_process?: unknown
  post_inspection_welding?: unknown
  pre_plating_welding?: unknown
}): boolean {
  return (
    isProcessFlagOn(row.welding_process) ||
    isProcessFlagOn(row.outsourced_welding_process) ||
    isProcessFlagOn(row.post_inspection_welding) ||
    isProcessFlagOn(row.pre_plating_welding)
  )
}

async function loadWeldingProductFlags() {
  try {
    const all: {
      product_cd?: number | string
      welding_process?: unknown
      outsourced_welding_process?: unknown
      post_inspection_welding?: unknown
      pre_plating_welding?: unknown
    }[] = []
    let page = 1
    const limit = 100
    while (true) {
      const res = await fetchProductProcessBOMList({ page, limit })
      const list = res?.data?.list ?? res?.list ?? []
      if (!list.length) break
      all.push(...list)
      if (list.length < limit) break
      page += 1
    }
    const set = new Set<string>()
    for (const row of all) {
      if (bomRowHasWeldingProcess(row)) {
        addWeldingProductCdKeys(set, row.product_cd)
      }
    }
    weldingProductCdSet.value = set
  } catch {
    weldingProductCdSet.value = new Set()
  }
}

type InspectorAvgRankRow = InspectorDisplayRow & { rank: number }

function buildInspectorAvgRankBySessions(
  sessions: InspectionProductivitySessionRow[],
  includeProduct: (productCd: string) => boolean,
): InspectorAvgRankRow[] {
  const map = new Map<string, InspectionProductivityInspectorRow>()
  for (const s of sessions) {
    const productCd = (s.product_cd ?? '').trim()
    if (!productCd || !includeProduct(productCd)) continue

    const inspId = s.mes_inspector_user_id
    const inspKey = inspId != null ? String(inspId) : 'none'
    const inspName = (s.inspector_display_name ?? s.mes_inspector_name ?? '—').trim() || '—'
    if (!map.has(inspKey)) {
      map.set(inspKey, {
        inspector_user_id: inspId ?? null,
        inspector_name: inspName,
        session_count: 0,
        sum_actual_qty: 0,
        sum_defect_qty: 0,
        sum_net_production_sec: 0,
        efficiency_per_hour: null,
      })
    }
    const inv = map.get(inspKey)!
    inv.session_count = (inv.session_count ?? 0) + 1
    inv.sum_actual_qty = (inv.sum_actual_qty ?? 0) + Number(s.actual_production_quantity ?? 0)
    inv.sum_defect_qty = (inv.sum_defect_qty ?? 0) + Number(s.defect_qty ?? 0)
    inv.sum_net_production_sec = (inv.sum_net_production_sec ?? 0) + Number(s.net_production_sec ?? 0)
  }

  const rows: InspectorAvgRankRow[] = []
  for (const inv of map.values()) {
    const actual = inv.sum_actual_qty ?? 0
    const defect = inv.sum_defect_qty ?? 0
    inv.defect_rate_percent = actual > 0 ? Math.round((defect / actual) * 1000) / 10 : null
    const avg = periodAvgEfficiencyFromBucket(inv)
    if (avg == null) continue
    rows.push({
      ...inv,
      avg_efficiency_per_hour: avg,
      rank: 0,
    })
  }
  rows.sort((a, b) => (b.avg_efficiency_per_hour ?? -1) - (a.avg_efficiency_per_hour ?? -1))
  rows.forEach((row, index) => {
    row.rank = index + 1
  })
  return rows
}

const inspectorRankWithoutWelding = computed((): InspectorAvgRankRow[] => {
  const sessions = analysisData.value?.sessions ?? []
  const welding = weldingProductCdSet.value
  return buildInspectorAvgRankBySessions(sessions, (cd) => !sessionProductHasWelding(cd, welding))
})

const inspectorRankWithWelding = computed((): InspectorAvgRankRow[] => {
  const sessions = analysisData.value?.sessions ?? []
  const welding = weldingProductCdSet.value
  return buildInspectorAvgRankBySessions(sessions, (cd) => sessionProductHasWelding(cd, welding))
})

const weldingProductBomCount = computed(() => weldingProductCdSet.value.size)

type InspectorProductDialogScope = 'no-welding' | 'with-welding'

const inspectorProductDialogVisible = ref(false)
const inspectorProductDialogTarget = ref<InspectorAvgRankRow | null>(null)
const inspectorProductDialogScope = ref<InspectorProductDialogScope>('no-welding')

function inspectorRankRowKey(row: Pick<InspectorAvgRankRow, 'inspector_user_id'>): string {
  return row.inspector_user_id != null ? String(row.inspector_user_id) : 'none'
}

function buildInspectorProductRows(
  sessions: InspectionProductivitySessionRow[],
  inspectorKey: string,
  includeProduct: (productCd: string) => boolean,
): ProductDisplayRow[] {
  const map = new Map<string, InspectionProductivityProductRow & { sum_net_production_sec: number }>()
  for (const s of sessions) {
    const productCd = (s.product_cd ?? '').trim()
    if (!productCd || !includeProduct(productCd)) continue

    const inspKey = s.mes_inspector_user_id != null ? String(s.mes_inspector_user_id) : 'none'
    if (inspKey !== inspectorKey) continue

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
    prod.sum_net_production_sec = (prod.sum_net_production_sec ?? 0) + Number(s.net_production_sec ?? 0)
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

const inspectorProductDialogRows = computed((): ProductDisplayRow[] => {
  const target = inspectorProductDialogTarget.value
  if (!target) return []

  const sessions = analysisData.value?.sessions ?? []
  const welding = weldingProductCdSet.value
  const includeProduct =
    inspectorProductDialogScope.value === 'with-welding'
      ? (cd: string) => sessionProductHasWelding(cd, welding)
      : (cd: string) => !sessionProductHasWelding(cd, welding)

  return buildInspectorProductRows(sessions, inspectorRankRowKey(target), includeProduct)
})

const inspectorProductDialogScopeLabel = computed(() =>
  inspectorProductDialogScope.value === 'with-welding' ? '溶接工程あり製品' : '溶接工程なし製品',
)

const inspectorProductDialogStats = computed(() => {
  const rows = inspectorProductDialogRows.value
  return {
    sessionCount: rows.reduce((sum, row) => sum + Number(row.session_count ?? 0), 0),
    totalQty: rows.reduce((sum, row) => sum + Number(row.sum_actual_qty ?? 0), 0),
  }
})

function openInspectorProductDialog(row: InspectorAvgRankRow, scope: InspectorProductDialogScope) {
  inspectorProductDialogTarget.value = row
  inspectorProductDialogScope.value = scope
  inspectorProductDialogVisible.value = true
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
      hint: '本 / 時間',
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

function inspectorLabel(u: InspectionManagementInspectorOption): string {
  const name = (u.full_name ?? '').trim()
  const username = (u.username ?? '').trim()
  if (name && username) return `${name}（${username}）`
  return name || username || `#${u.id}`
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
    productOptions.value = filterInspectionSelectableProducts(list)
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

function buildReportFilters(): InspectionProductivityReportFilters | null {
  const [start, end] = dateRange.value ?? []
  if (!start || !end) return null

  let inspectorFilterLabel = '（すべて）'
  if (filterInspectorId.value !== '') {
    const found = inspectorOptions.value.find((u) => u.id === filterInspectorId.value)
    inspectorFilterLabel = found ? inspectorLabel(found) : `#${filterInspectorId.value}`
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
    inspectorLabel: inspectorFilterLabel,
    productLabel: productFilterLabel,
    includeIncomplete: includeIncomplete.value,
  }
}

function buildReportContext(): InspectionProductivityReportContext | null {
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
      inspector: captureChartDataUrl(inspectorChart),
      product: captureChartDataUrl(productChart),
      productRank: captureChartDataUrl(productRankChart),
    },
    inspectorRows: inspectorDisplayRows.value,
    productRows: productDisplayRows.value,
    inspectorSectionAvgEfficiency: inspectorSectionAvgEfficiency.value,
    productSectionTotalQty: productSectionTotalQty.value,
    weldRankOff: inspectorRankWithoutWelding.value,
    weldRankOn: inspectorRankWithWelding.value,
    productRank: {
      selected: selectedProductRanking.value,
      topOverview: productRankTopOverview.value,
      stats: selectedProductRankStats.value,
    },
  }
}

async function prepareChartsForReport(command: string) {
  if (command === 'print-full' || command === 'print-daily') dailyChart?.resize()
  if (command === 'print-full' || command === 'print-inspector') inspectorChart?.resize()
  if (command === 'print-full' || command === 'print-product') productChart?.resize()
  if (command === 'print-product-rank') {
    await nextTick()
    renderProductRankChart()
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
      await handleBatchDailyByInspectorPrint()
      return
    }

    if (cmd === 'print-inspector-product-batch') {
      await handleBatchInspectorProductPrint()
      return
    }

    await prepareChartsForReport(cmd)
    const ctx = buildReportContext()
    if (!ctx) {
      ElMessage.warning('出力する分析データがありません')
      return
    }

    if (cmd === 'print-full') {
      printInspectionProductivityReport(ctx)
      return
    }

    const sectionMap: Record<string, InspectionProductivityPrintSection> = {
      'print-daily': 'daily',
      'print-inspector': 'inspector',
      'print-product': 'product',
      'print-weld-rank': 'weld-rank',
      'print-product-rank': 'product-rank',
    }
    const section = sectionMap[cmd]
    if (section) {
      printInspectionProductivitySection(section, ctx)
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

async function captureDailyChartDataUrl(daily: InspectionProductivityDailyRow[]): Promise<string | null> {
  if (!daily.length) return null
  const el = document.createElement('div')
  el.style.cssText =
    'position:fixed;left:0;top:0;width:960px;height:380px;opacity:0;pointer-events:none;z-index:-1;overflow:hidden;'
  document.body.appendChild(el)
  let chart: ECharts | null = null
  try {
    chart = echarts.init(el, undefined, CHART_INIT_OPTS)
    chart.setOption(buildDailyTrendChartOption(daily, chartTheme(), { forExport: true }), { notMerge: true })
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

async function handleBatchDailyByInspectorPrint() {
  const filters = buildReportFilters()
  const [start, end] = dateRange.value ?? []
  if (!filters || !start || !end) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  const inspectors = inspectorOptions.value
  if (!inspectors.length) {
    ElMessage.warning('検査員が登録されていません')
    return
  }

  const items: InspectionProductivityDailyBatchItem[] = []
  for (const insp of inspectors) {
    const res = await fetchInspectionProductivityAnalysis({
      start_date: start,
      end_date: end,
      mes_inspector_user_id: insp.id,
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
      inspectorUserId: insp.id,
      inspectorLabel: inspectorLabel(insp),
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

  printInspectionProductivityDailyBatch(filters, items)
}

async function handleBatchInspectorProductPrint() {
  const filters = buildReportFilters()
  const [start, end] = dateRange.value ?? []
  if (!filters || !start || !end) {
    ElMessage.warning('出力する分析データがありません')
    return
  }

  const inspectors = inspectorOptions.value
  if (!inspectors.length) {
    ElMessage.warning('検査員が登録されていません')
    return
  }

  const res = await fetchInspectionProductivityAnalysis({
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
  const items: InspectionProductivityInspectorProductBatchItem[] = []

  for (const insp of inspectors) {
    const rows = buildInspectorProductRows(sessions, String(insp.id), () => true)
    if (!rows.length) continue

    const sessionCount = rows.reduce((sum, row) => sum + Number(row.session_count ?? 0), 0)
    const sumActualQty = rows.reduce((sum, row) => sum + Number(row.sum_actual_qty ?? 0), 0)
    const totalSec = rows.reduce((sum, row) => sum + Number(row.sum_net_production_sec ?? 0), 0)
    const avgEfficiencyPerHour =
      sumActualQty > 0 && totalSec > 0 ? Math.round(sumActualQty / (totalSec / 3600)) : null

    items.push({
      inspectorLabel: inspectorLabel(insp),
      productCount: rows.length,
      sessionCount,
      sumActualQty,
      avgEfficiencyPerHour,
      productRows: rows,
    })
  }

  if (!items.length) {
    ElMessage.warning('印刷できる検査員別製品データがありません')
    return
  }

  items.sort((a, b) => (b.avgEfficiencyPerHour ?? -1) - (a.avgEfficiencyPerHour ?? -1))
  printInspectionProductivityInspectorProductBatch(filters, items)
}

function handleExportSessionsCsv() {
  if (!analysisData.value) {
    ElMessage.warning('出力する分析データがありません')
    return
  }
  const filters = buildReportFilters()
  if (!filters) {
    ElMessage.warning('集計期間を指定してください')
    return
  }

  sessionExportBusy.value = true
  try {
    exportInspectionSessionsCsv(analysisData.value, filters)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : 'CSV出力に失敗しました')
  } finally {
    sessionExportBusy.value = false
  }
}

async function loadInspectors() {
  const [start, end] = dateRange.value ?? []
  try {
    const res = await fetchInspectionManagementInspectors(
      start && end ? { start_date: start, end_date: end } : undefined,
    )
    inspectorOptions.value = res.data ?? []
    if (filterInspectorId.value !== '') {
      const exists = inspectorOptions.value.some((u) => u.id === filterInspectorId.value)
      if (!exists) filterInspectorId.value = ''
    }
  } catch {
    inspectorOptions.value = []
    if (filterInspectorId.value !== '') filterInspectorId.value = ''
  }
}

async function loadDefectLabels() {
  try {
    const items = await loadMesDefectItemsForProcess('KT09')
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
    const res = await fetchInspectionProductivityAnalysis({
      start_date: start,
      end_date: end,
      mes_inspector_user_id: filterInspectorId.value === '' ? undefined : filterInspectorId.value,
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
  inspectorChart?.dispose()
  productChart?.dispose()
  productRankChart?.dispose()
  dailyChart = null
  inspectorChart = null
  productChart = null
  productRankChart = null
}

const CHART_INIT_OPTS = {
  devicePixelRatio: Math.min(typeof window !== 'undefined' ? window.devicePixelRatio : 2, 2),
}

/** 横向柱状图：多色相渐变（浅 → 深） */
const H_BAR_GRADIENT_STOPS: [string, string][] = [
  ['#818cf8', '#4338ca'],
  ['#34d399', '#047857'],
  ['#fbbf24', '#b45309'],
  ['#f472b6', '#be185d'],
  ['#38bdf8', '#0369a1'],
  ['#a78bfa', '#6d28d9'],
  ['#fb923c', '#c2410c'],
  ['#2dd4bf', '#0f766e'],
  ['#f87171', '#dc2626'],
  ['#4ade80', '#15803d'],
]

function horizontalBarGradient(index: number, highlightFirst = false) {
  if (highlightFirst && index === 0) {
    return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
      { offset: 0, color: '#fde68a' },
      { offset: 1, color: '#d97706' },
    ])
  }
  const [light, dark] = H_BAR_GRADIENT_STOPS[index % H_BAR_GRADIENT_STOPS.length]
  return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: light },
    { offset: 1, color: dark },
  ])
}

function horizontalBarAccentColor(index: number, highlightFirst = false): string {
  if (highlightFirst && index === 0) return '#b45309'
  return H_BAR_GRADIENT_STOPS[index % H_BAR_GRADIENT_STOPS.length][1]
}

/** 横向柱状图一屏可见条数；超出时显示纵向滚动条 */
const H_BAR_VISIBLE_COUNT = 8

function buildHorizontalBarDataZoom(itemCount: number, accent = '#6366f1') {
  if (itemCount <= H_BAR_VISIBLE_COUNT) return []
  const span = Math.min(H_BAR_VISIBLE_COUNT - 1, itemCount - 1)
  return [
    {
      type: 'slider',
      yAxisIndex: 0,
      orient: 'vertical',
      right: 4,
      width: 10,
      startValue: 0,
      endValue: span,
      minValueSpan: span,
      maxValueSpan: span,
      showDetail: false,
      brushSelect: false,
      borderColor: 'transparent',
      backgroundColor: 'rgba(148, 163, 184, 0.18)',
      fillerColor: `${accent}40`,
      handleSize: '65%',
      handleStyle: { color: accent, borderColor: accent },
      moveHandleSize: 0,
      textStyle: { color: 'transparent' },
    },
    {
      type: 'inside',
      yAxisIndex: 0,
      orient: 'vertical',
      zoomOnMouseWheel: false,
      moveOnMouseMove: true,
      moveOnMouseWheel: true,
    },
  ]
}

function horizontalBarGridRight(itemCount: number, base = 52): number {
  return itemCount > H_BAR_VISIBLE_COUNT ? base + 16 : base
}

function chartTheme() {
  return {
    text: '#64748b',
    axis: '#e2e8f0',
    split: 'rgba(148, 163, 184, 0.22)',
  }
}

function buildDailyTrendChartOption(
  daily: InspectionProductivityDailyRow[],
  theme: ReturnType<typeof chartTheme>,
  options?: { forExport?: boolean },
) {
  const forExport = options?.forExport === true
  const days = daily.map((d) => d.day.slice(5))
  const productionData = daily.map((d) => d.sum_actual_qty ?? 0)
  const efficiencyData = daily.map((d) => d.efficiency_per_hour ?? null)
  const barGradient = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: '#7dd3fc' },
    { offset: 0.55, color: '#6366f1' },
    { offset: 1, color: '#4338ca' },
  ])
  const barGradientEmphasis = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: '#bae6fd' },
    { offset: 0.55, color: '#818cf8' },
    { offset: 1, color: '#4f46e5' },
  ])

  return {
    backgroundColor: forExport ? '#ffffff' : 'transparent',
    animation: !forExport,
    animationDuration: forExport ? 0 : 1100,
    animationDurationUpdate: forExport ? 0 : 750,
    animationEasing: 'cubicOut' as const,
    animationEasingUpdate: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(226, 232, 240, 0.95)',
      borderWidth: 1,
      padding: [12, 16],
      extraCssText:
        'border-radius: 14px; box-shadow: 0 16px 48px rgba(15, 23, 42, 0.12), 0 2px 8px rgba(15, 23, 42, 0.06);',
      textStyle: { color: '#334155', fontSize: 12, lineHeight: 20 },
      axisPointer: {
        type: 'line',
        lineStyle: { color: 'rgba(99, 102, 241, 0.35)', width: 1, type: 'solid' as const },
        label: {
          backgroundColor: '#4f46e5',
          color: '#fff',
          borderRadius: 8,
          padding: [5, 8],
          fontSize: 10,
          fontWeight: 600,
        },
      },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const axis = list[0] as { axisValue?: string; dataIndex?: number }
        const idx = axis.dataIndex ?? 0
        const row = daily[idx]
        if (!row) return ''
        const lines = [`<div style="font-weight:700;margin-bottom:8px;color:#0f172a;letter-spacing:0.02em">${row.day}</div>`]
        for (const p of list) {
          const item = p as { seriesName?: string; value?: number | null; color?: string }
          const dot = `<span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:${item.color};margin-right:8px;vertical-align:middle"></span>`
          if (item.seriesName === '生産数') {
            lines.push(`<div style="margin:4px 0">${dot}<span style="color:#64748b">生産数</span> <b style="color:#4338ca">${fmtInt(item.value)}</b></div>`)
          } else if (item.seriesName === '能率') {
            lines.push(`<div style="margin:4px 0">${dot}<span style="color:#64748b">能率</span> <b style="color:#047857">${fmtEfficiency(item.value)}</b> <span style="color:#94a3b8;font-size:11px">本/時</span></div>`)
          }
        }
        return lines.join('')
      },
    },
    legend: {
      data: ['生産数', '能率'],
      top: 4,
      itemWidth: 16,
      itemHeight: 8,
      itemGap: 24,
      icon: 'roundRect',
      textStyle: { color: '#475569', fontSize: 11, fontWeight: 600 },
    },
    grid: { left: 52, right: 52, top: 72, bottom: 28, containLabel: false },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: true,
      axisLine: { lineStyle: { color: theme.axis, width: 1 } },
      axisTick: { show: false },
      axisLabel: {
        color: '#64748b',
        fontSize: 11,
        fontWeight: 500,
        margin: 12,
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '生産数',
        nameTextStyle: { color: '#6366f1', fontSize: 10, fontWeight: 600, padding: [0, 0, 6, 0] },
        axisLabel: { color: theme.text, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: { color: theme.split, type: 'dashed' as const, width: 1 },
        },
      },
      {
        type: 'value',
        name: '能率',
        nameTextStyle: { color: '#059669', fontSize: 10, fontWeight: 600, padding: [0, 0, 6, 0] },
        axisLabel: { color: theme.text, fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '生産数',
        type: 'bar',
        barMaxWidth: 28,
        barCategoryGap: '42%',
        z: 2,
        animationDelay: (idx: number) => idx * 35,
        data: productionData,
        label: {
          show: true,
          position: 'inside',
          verticalAlign: 'middle',
          align: 'center',
          color: '#ffffff',
          fontSize: 9,
          fontWeight: 700,
          textShadowColor: 'rgba(67, 56, 202, 0.55)',
          textShadowBlur: 4,
          formatter: (params: { value?: number | null }) => {
            const v = Number(params.value ?? 0)
            if (!Number.isFinite(v) || v <= 0) return ''
            return fmtInt(v)
          },
        },
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: barGradient,
          borderColor: 'rgba(255, 255, 255, 0.35)',
          borderWidth: 1,
          shadowColor: 'rgba(67, 56, 202, 0.22)',
          shadowBlur: 10,
          shadowOffsetY: 4,
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: barGradientEmphasis,
            shadowBlur: 16,
            shadowOffsetY: 6,
          },
          label: { fontSize: 11 },
        },
      },
      {
        name: '能率',
        type: 'line',
        yAxisIndex: 1,
        z: 3,
        smooth: 0.38,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 7,
        animationDelay: (idx: number) => idx * 30 + 120,
        lineStyle: {
          width: 2.5,
          color: '#10b981',
          cap: 'round',
          join: 'round',
        },
        itemStyle: {
          color: '#10b981',
          borderWidth: 2,
          borderColor: '#ffffff',
        },
        label: {
          show: true,
          position: 'top',
          distance: 12,
          color: '#047857',
          fontSize: 9,
          fontWeight: 700,
          backgroundColor: 'rgba(255, 255, 255, 0.94)',
          padding: [3, 6],
          borderRadius: 6,
          borderColor: 'rgba(16, 185, 129, 0.32)',
          borderWidth: 1,
          shadowColor: 'rgba(16, 185, 129, 0.12)',
          shadowBlur: 6,
          shadowOffsetY: 2,
          formatter: (params: { value?: number | null }) => {
            const v = params.value
            if (v == null || !Number.isFinite(Number(v))) return ''
            return fmtEfficiency(Number(v))
          },
        },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(52, 211, 153, 0.22)' },
            { offset: 0.75, color: 'rgba(16, 185, 129, 0.06)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0)' },
          ]),
        },
        emphasis: {
          focus: 'series',
          scale: 1.45,
          itemStyle: {
            borderWidth: 2.5,
            shadowBlur: 10,
            shadowColor: 'rgba(16, 185, 129, 0.35)',
          },
        },
        data: efficiencyData,
      },
    ],
  }
}

function buildInspectorChartOption(rows: InspectorDisplayRow[], theme: ReturnType<typeof chartTheme>) {
  const names = rows.map((r) => r.inspector_name ?? '—')
  const dataZoom = buildHorizontalBarDataZoom(rows.length, '#6366f1')

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.08)' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(226, 232, 240, 0.95)',
      borderWidth: 1,
      padding: [10, 14],
      extraCssText: 'border-radius: 12px; box-shadow: 0 12px 36px rgba(15, 23, 42, 0.1);',
      textStyle: { color: '#334155', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b style="color:#312e81">${row.inspector_name ?? '—'}</b>`,
          `平均能率 <b style="color:#4f46e5">${fmtEfficiency(row.avg_efficiency_per_hour)}</b> 本/時`,
          `生産 ${fmtInt(row.sum_actual_qty)} · 不良率 ${fmtPct(row.defect_rate_percent)}`,
        ].join('<br/>')
      },
    },
    grid: { left: 92, right: horizontalBarGridRight(rows.length), top: 10, bottom: 12, containLabel: false },
    dataZoom,
    xAxis: {
      type: 'value',
      name: '本/時',
      nameTextStyle: { color: '#6366f1', fontSize: 10, fontWeight: 600 },
      axisLabel: { color: theme.text, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 11, fontWeight: 500, width: 76, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        animationDelay: (idx: number) => idx * 60,
        data: rows.map((r, i) => ({
          value: r.avg_efficiency_per_hour ?? 0,
          label: { color: horizontalBarAccentColor(i) },
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: horizontalBarGradient(i),
            borderColor: 'rgba(255, 255, 255, 0.45)',
            borderWidth: 1,
            shadowColor: 'rgba(15, 23, 42, 0.12)',
            shadowBlur: 8,
            shadowOffsetX: 3,
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 6,
          fontSize: 10,
          fontWeight: 700,
          formatter: (p: { value?: number }) => fmtEfficiency(p.value),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 14, shadowOffsetX: 5 },
        },
      },
    ],
  }
}

function buildProductChartOption(rows: ProductDisplayRow[], theme: ReturnType<typeof chartTheme>) {
  const labels = rows.map((r) => {
    const name = (r.product_name ?? '').trim()
    return name.length > 10 ? `${name.slice(0, 10)}…` : name || r.product_cd || '—'
  })
  const dataZoom = buildHorizontalBarDataZoom(rows.length, '#0ea5e9')

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(14, 165, 233, 0.08)' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(226, 232, 240, 0.95)',
      borderWidth: 1,
      padding: [10, 14],
      extraCssText: 'border-radius: 12px; box-shadow: 0 12px 36px rgba(15, 23, 42, 0.1);',
      textStyle: { color: '#334155', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b style="color:#0c4a6e">${row.product_name ?? row.product_cd}</b>`,
          `<span style="color:#64748b">${row.product_cd}</span>`,
          `生産 <b style="color:#0284c7">${fmtInt(row.sum_actual_qty)}</b>`,
          `能率 ${fmtEfficiency(row.avg_efficiency_per_hour)} 本/時 · 不良率 ${fmtPct(row.defect_rate_percent)}`,
        ].join('<br/>')
      },
    },
    grid: { left: 96, right: horizontalBarGridRight(rows.length), top: 10, bottom: 12, containLabel: false },
    dataZoom,
    xAxis: {
      type: 'value',
      name: '生産数',
      nameTextStyle: { color: '#0284c7', fontSize: 10, fontWeight: 600 },
      axisLabel: { color: theme.text, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 10, fontWeight: 500, width: 80, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        animationDelay: (idx: number) => idx * 60,
        data: rows.map((r, i) => ({
          value: r.sum_actual_qty ?? 0,
          label: { color: horizontalBarAccentColor(i) },
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: horizontalBarGradient(i),
            borderColor: 'rgba(255, 255, 255, 0.45)',
            borderWidth: 1,
            shadowColor: 'rgba(15, 23, 42, 0.12)',
            shadowBlur: 8,
            shadowOffsetX: 3,
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 6,
          fontSize: 10,
          fontWeight: 700,
          formatter: (p: { value?: number }) => fmtInt(p.value),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 14, shadowOffsetX: 5 },
        },
      },
    ],
  }
}

function renderCharts() {
  disposeCharts()
  const data = analysisData.value
  if (!data) return
  const theme = chartTheme()

  const dailyEl = dailyChartRef.value
  if (dailyEl && data.daily.length > 0) {
    dailyChart = echarts.init(dailyEl, undefined, CHART_INIT_OPTS)
    dailyChart.setOption(buildDailyTrendChartOption(data.daily, theme))
  }

  const inspectorEl = inspectorChartRef.value
  const inspectorRows = inspectorDisplayRows.value
  if (inspectorEl && inspectorRows.length > 0) {
    inspectorChart = echarts.init(inspectorEl, undefined, CHART_INIT_OPTS)
    inspectorChart.setOption(buildInspectorChartOption(inspectorRows, theme))
  }

  const productEl = productChartRef.value
  const productRows = productDisplayRows.value
  if (productEl && productRows.length > 0) {
    productChart = echarts.init(productEl, undefined, CHART_INIT_OPTS)
    productChart.setOption(buildProductChartOption(productRows, theme))
  }

  renderProductRankChart(theme)
}

function buildProductRankChartOption(
  rows: InspectionProductivityInspectorRow[],
  theme: ReturnType<typeof chartTheme>,
) {
  const dataZoom = buildHorizontalBarDataZoom(rows.length, '#f59e0b')

  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(245, 158, 11, 0.1)' } },
      backgroundColor: 'rgba(255, 255, 255, 0.96)',
      borderColor: 'rgba(253, 230, 138, 0.9)',
      borderWidth: 1,
      padding: [10, 14],
      extraCssText: 'border-radius: 12px; box-shadow: 0 12px 36px rgba(245, 158, 11, 0.15);',
      textStyle: { color: '#334155', fontSize: 12 },
      formatter(params: unknown) {
        const list = Array.isArray(params) ? params : [params]
        const p = list[0] as { dataIndex?: number }
        const row = rows[p.dataIndex ?? 0]
        if (!row) return ''
        return [
          `<b style="color:#92400e">${row.inspector_name ?? '—'}</b>`,
          `順位 <b style="color:#d97706">#${row.rank ?? '—'}</b>`,
          `能率 <b style="color:#059669">${fmtEfficiency(row.efficiency_per_hour)}</b> 本/時`,
          `生産 ${fmtInt(row.sum_actual_qty)} · 不良率 ${fmtPct(row.defect_rate_percent)}`,
        ].join('<br/>')
      },
    },
    grid: { left: 104, right: horizontalBarGridRight(rows.length, 48), top: 10, bottom: 14, containLabel: false },
    dataZoom,
    xAxis: {
      type: 'value',
      name: '本/時',
      nameTextStyle: { color: '#d97706', fontSize: 10, fontWeight: 600 },
      axisLabel: { color: theme.text, fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: theme.split, type: 'dashed' as const } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => `#${r.rank} ${r.inspector_name ?? '—'}`),
      inverse: true,
      axisLabel: { color: '#334155', fontSize: 11, fontWeight: 500, width: 96, overflow: 'truncate' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 14,
        animationDelay: (idx: number) => idx * 55,
        data: rows.map((r, i) => ({
          value: r.efficiency_per_hour ?? 0,
          label: { color: horizontalBarAccentColor(i, true) },
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: horizontalBarGradient(i, true),
            borderColor: 'rgba(255, 255, 255, 0.5)',
            borderWidth: 1,
            shadowColor: 'rgba(245, 158, 11, 0.22)',
            shadowBlur: 10,
            shadowOffsetX: 3,
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 6,
          fontSize: 10,
          fontWeight: 700,
          formatter: (p: { value?: number }) => fmtEfficiency(p.value),
        },
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 16, shadowOffsetX: 5 },
        },
      },
    ],
  }
}

function renderProductRankChart(theme = chartTheme()) {
  productRankChart?.dispose()
  productRankChart = null
  const ranking = selectedProductRanking.value
  const el = productRankChartRef.value
  const rows = ranking?.inspectors ?? []
  if (!el || rows.length === 0) return

  productRankChart = echarts.init(el, undefined, CHART_INIT_OPTS)
  productRankChart.setOption(buildProductRankChartOption(rows, theme))
}

function handleResize() {
  dailyChart?.resize()
  inspectorChart?.resize()
  productChart?.resize()
  productRankChart?.resize()
}

watch(rankViewProductCd, async () => {
  await nextTick()
  renderProductRankChart()
})

watch(dateRange, () => {
  void loadInspectors()
  scheduleLoadAnalysis()
}, { deep: true })
watch(filterInspectorId, scheduleLoadAnalysis)
watch(filterProductCd, scheduleLoadAnalysis)
watch(includeIncomplete, scheduleLoadAnalysis)

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  await Promise.all([loadInspectors(), loadDefectLabels(), loadProductOptions(), loadWeldingProductFlags()])
  await loadAnalysis({ silent: true })
})

onBeforeUnmount(() => {
  if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer)
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<style scoped>
.ipa {
  position: relative;
  min-height: 100%;
  padding: 10px 12px 16px;
  overflow: hidden;
}

.ipa__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99, 102, 241, 0.12), transparent 55%),
    radial-gradient(ellipse 60% 40% at 100% 20%, rgba(16, 185, 129, 0.08), transparent 50%),
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.ipa__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.45;
  animation: ipa-float 12s ease-in-out infinite;
}

.ipa__orb--1 {
  width: 280px;
  height: 280px;
  top: -80px;
  left: -60px;
  background: rgba(99, 102, 241, 0.35);
}

.ipa__orb--2 {
  width: 220px;
  height: 220px;
  top: 40%;
  right: -40px;
  background: rgba(16, 185, 129, 0.28);
  animation-delay: -4s;
}

.ipa__orb--3 {
  width: 180px;
  height: 180px;
  bottom: 10%;
  left: 35%;
  background: rgba(14, 165, 233, 0.22);
  animation-delay: -8s;
}

@keyframes ipa-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(12px, -16px) scale(1.05); }
}

.ipa-hero,
.ipa-toolbar,
.ipa-body {
  position: relative;
  z-index: 1;
}

.ipa-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.72) 100%);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 8px 32px rgba(15, 23, 42, 0.08),
    0 2px 8px rgba(99, 102, 241, 0.06);
  backdrop-filter: blur(12px);
}

.ipa-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.ipa-hero__icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #10b981 0%, #059669 50%, #047857 100%);
  box-shadow:
    0 4px 14px rgba(16, 185, 129, 0.45),
    0 1px 0 rgba(255, 255, 255, 0.35) inset;
  flex-shrink: 0;
}

.ipa-hero__icon-glow {
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.35), transparent 70%);
  z-index: -1;
  animation: ipa-pulse 3s ease-in-out infinite;
}

@keyframes ipa-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}

.ipa-hero__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6366f1;
}

.ipa-hero__title {
  margin: 2px 0 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.25;
}

.ipa-hero__meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
}

.ipa-hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.ipa-btn {
  height: 34px !important;
  padding: 0 16px !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  letter-spacing: 0.02em;
  border: none !important;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    filter 0.2s ease;
}

.ipa-btn__inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ipa-btn__icon {
  font-size: 14px;
}

.ipa-btn__caret {
  margin-left: 0;
  font-size: 11px;
  opacity: 0.88;
}

.ipa-btn--report {
  background: linear-gradient(135deg, #7c3aed 0%, #6366f1 52%, #4f46e5 100%) !important;
  color: #fff !important;
  box-shadow:
    0 4px 14px rgba(99, 102, 241, 0.42),
    0 1px 0 rgba(255, 255, 255, 0.22) inset;
}

.ipa-btn--report:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.06);
  box-shadow:
    0 8px 22px rgba(99, 102, 241, 0.52),
    0 1px 0 rgba(255, 255, 255, 0.25) inset;
}

.ipa-btn--report:active:not(:disabled) {
  transform: translateY(0);
}

.ipa-btn--refresh {
  background: linear-gradient(135deg, #047857 0%, #10b981 52%, #14b8a6 100%) !important;
  color: #fff !important;
  box-shadow:
    0 4px 14px rgba(16, 185, 129, 0.38),
    0 1px 0 rgba(255, 255, 255, 0.22) inset;
}

.ipa-btn--refresh:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.06);
  box-shadow:
    0 8px 22px rgba(16, 185, 129, 0.48),
    0 1px 0 rgba(255, 255, 255, 0.25) inset;
}

.ipa-btn--refresh:active:not(:disabled) {
  transform: translateY(0);
}

.ipa-btn--report.is-disabled,
.ipa-btn--refresh.is-disabled {
  opacity: 0.55;
  filter: grayscale(0.15);
  box-shadow: none !important;
}

.ipa-hero__range {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.ipa-panel {
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.88) 100%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 24px rgba(15, 23, 42, 0.06),
    0 1px 3px rgba(15, 23, 42, 0.04);
  backdrop-filter: blur(10px);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.ipa-panel:hover {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 12px 40px rgba(15, 23, 42, 0.09),
    0 4px 12px rgba(99, 102, 241, 0.06);
}

.ipa-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  margin-bottom: 10px;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(241, 245, 249, 0.92) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 6px 20px rgba(15, 23, 42, 0.07),
    0 2px 6px rgba(99, 102, 241, 0.05);
}

.ipa-toolbar__fields {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  flex: 1;
  min-width: 0;
}

.ipa-field {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  min-height: 32px;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 2px 6px rgba(15, 23, 42, 0.06),
    0 1px 2px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}

.ipa-field:hover {
  transform: translateY(-1px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 12px rgba(15, 23, 42, 0.09);
}

.ipa-field:focus-within {
  border-color: rgba(99, 102, 241, 0.45);
  box-shadow:
    0 0 0 3px rgba(99, 102, 241, 0.12),
    0 2px 8px rgba(99, 102, 241, 0.15);
}

.ipa-field__pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 0 11px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
  border-right: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: inset -1px 0 0 rgba(0, 0, 0, 0.04);
}

.ipa-field__pill .el-icon {
  font-size: 13px;
}

.ipa-field--period .ipa-field__pill {
  color: #3730a3;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
}

.ipa-field--inspector .ipa-field__pill {
  color: #6b21a8;
  background: linear-gradient(180deg, #faf5ff 0%, #f3e8ff 100%);
}

.ipa-field--product .ipa-field__pill {
  color: #047857;
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
}

.ipa-field--check .ipa-field__pill {
  color: #92400e;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}

.ipa-field--check {
  cursor: default;
}

.ipa-field--check .ipa-field__pill--check {
  padding: 0 9px;
  font-size: 10px;
}

.ipa-field__control {
  flex: 1;
  min-width: 0;
}

.ipa-field__date {
  width: 228px !important;
}

.ipa-field__inspector-select {
  width: 168px;
}

.ipa-field--product {
  flex: 1;
  min-width: 200px;
  max-width: 300px;
}

.ipa-field__product-select {
  width: 100%;
  min-width: 140px;
}

/* 入力枠をフラット化してラベルと一体化 */
.ipa-field :deep(.el-input__wrapper),
.ipa-field :deep(.el-select__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  min-height: 30px !important;
  padding-left: 8px !important;
  padding-right: 8px !important;
}

.ipa-field :deep(.el-input__wrapper:hover),
.ipa-field :deep(.el-select__wrapper:hover),
.ipa-field :deep(.el-input__wrapper.is-focus),
.ipa-field :deep(.el-select__wrapper.is-focused) {
  box-shadow: none !important;
}

.ipa-field :deep(.el-range-editor.el-input__wrapper) {
  padding: 0 8px !important;
}

.ipa-field :deep(.el-range-input) {
  font-size: 12px;
  color: #334155;
}

.ipa-field :deep(.el-select .el-input__inner),
.ipa-field :deep(.el-input__inner) {
  font-size: 12px;
  color: #334155;
}

.ipa-field--check {
  padding-right: 10px;
  gap: 0;
}

.ipa-field--check :deep(.el-checkbox) {
  height: 30px;
  padding: 0 4px 0 8px;
  display: inline-flex;
  align-items: center;
}

.ipa-field--check :deep(.el-checkbox__label) {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding-left: 6px;
}

.ipa-check {
  display: flex;
  align-items: stretch;
}

.ipa-product-opt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.ipa-product-opt__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #334155;
}

.ipa-product-opt__cd {
  flex-shrink: 0;
  font-family: ui-monospace, monospace;
  font-size: 10px;
  color: #94a3b8;
}


.ipa-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ipa-kpi {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.ipa-kpi__card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 12px 11px 10px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid transparent;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 3px 0 rgba(15, 23, 42, 0.04),
    0 6px 16px rgba(15, 23, 42, 0.08);
}

.ipa-kpi__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 12px 12px 0 0;
}

.ipa-kpi__card--indigo {
  background: linear-gradient(160deg, #ffffff 0%, #f5f7ff 45%, #eef2ff 100%);
  border-color: rgba(99, 102, 241, 0.2);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(99, 102, 241, 0.1),
    0 8px 20px rgba(99, 102, 241, 0.12);
}

.ipa-kpi__card--indigo .ipa-kpi__accent {
  background: linear-gradient(90deg, #6366f1, #818cf8);
}

.ipa-kpi__card--indigo .ipa-kpi__label { color: #6366f1; }
.ipa-kpi__card--indigo .ipa-kpi__value { color: #4338ca; }
.ipa-kpi__card--indigo .ipa-kpi__hint { color: #818cf8; }

.ipa-kpi__card--sky {
  background: linear-gradient(160deg, #ffffff 0%, #f0f9ff 45%, #e0f2fe 100%);
  border-color: rgba(14, 165, 233, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(14, 165, 233, 0.1),
    0 8px 20px rgba(14, 165, 233, 0.12);
}

.ipa-kpi__card--sky .ipa-kpi__accent {
  background: linear-gradient(90deg, #0ea5e9, #38bdf8);
}

.ipa-kpi__card--sky .ipa-kpi__label { color: #0284c7; }
.ipa-kpi__card--sky .ipa-kpi__value { color: #0369a1; }
.ipa-kpi__card--sky .ipa-kpi__hint { color: #38bdf8; }

.ipa-kpi__card--amber {
  background: linear-gradient(160deg, #ffffff 0%, #fff7ed 45%, #ffedd5 100%);
  border-color: rgba(249, 115, 22, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(249, 115, 22, 0.1),
    0 8px 20px rgba(249, 115, 22, 0.12);
}

.ipa-kpi__card--amber .ipa-kpi__accent {
  background: linear-gradient(90deg, #f97316, #fb923c);
}

.ipa-kpi__card--amber .ipa-kpi__label { color: #ea580c; }
.ipa-kpi__card--amber .ipa-kpi__value { color: #c2410c; }
.ipa-kpi__card--amber .ipa-kpi__hint { color: #fb923c; }

.ipa-kpi__card--emerald {
  background: linear-gradient(160deg, #ffffff 0%, #ecfdf5 40%, #d1fae5 100%);
  border-color: rgba(16, 185, 129, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 4px 0 rgba(16, 185, 129, 0.12),
    0 10px 24px rgba(16, 185, 129, 0.16);
}

.ipa-kpi__card--emerald .ipa-kpi__accent {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.ipa-kpi__card--emerald .ipa-kpi__label { color: #059669; }
.ipa-kpi__card--emerald .ipa-kpi__value { color: #047857; font-size: 22px; }
.ipa-kpi__card--emerald .ipa-kpi__hint { color: #34d399; }

.ipa-kpi__card--violet {
  background: linear-gradient(160deg, #ffffff 0%, #f5f3ff 45%, #ede9fe 100%);
  border-color: rgba(139, 92, 246, 0.22);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 3px 0 rgba(139, 92, 246, 0.1),
    0 8px 20px rgba(139, 92, 246, 0.12);
}

.ipa-kpi__card--violet .ipa-kpi__accent {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.ipa-kpi__card--violet .ipa-kpi__label { color: #7c3aed; }
.ipa-kpi__card--violet .ipa-kpi__value { color: #6d28d9; }
.ipa-kpi__card--violet .ipa-kpi__hint { color: #a78bfa; }

.ipa-kpi__icon-wrap {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  color: #fff;
  flex-shrink: 0;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 4px 10px rgba(15, 23, 42, 0.18);
}

.ipa-kpi__icon-wrap--indigo {
  background: linear-gradient(145deg, #818cf8 0%, #6366f1 50%, #4f46e5 100%);
}

.ipa-kpi__icon-wrap--sky {
  background: linear-gradient(145deg, #38bdf8 0%, #0ea5e9 50%, #0284c7 100%);
}

.ipa-kpi__icon-wrap--amber {
  background: linear-gradient(145deg, #fb923c 0%, #f97316 50%, #ea580c 100%);
}

.ipa-kpi__icon-wrap--emerald {
  background: linear-gradient(145deg, #34d399 0%, #10b981 50%, #059669 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.4) inset,
    0 5px 14px rgba(16, 185, 129, 0.35);
}

.ipa-kpi__icon-wrap--violet {
  background: linear-gradient(145deg, #a78bfa 0%, #8b5cf6 50%, #7c3aed 100%);
}

.ipa-kpi__content {
  position: relative;
  z-index: 1;
  min-width: 0;
  flex: 1;
}

.ipa-kpi__label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.ipa-kpi__value {
  margin-top: 3px;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}

.ipa-kpi__hint {
  margin-top: 3px;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ipa-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ipa-panel--chart,
.ipa-split > .ipa-panel,
.ipa-content > .ipa-panel {
  padding: 12px 14px 10px;
}

.ipa-panel--chart {
  background: #ffffff;
  border-color: rgba(226, 232, 240, 0.95);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 32px rgba(15, 23, 42, 0.06);
}

.ipa-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.ipa-panel__title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ipa-panel__ico {
  font-size: 15px;
  color: #6366f1;
}

.ipa-panel__title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.ipa-panel__badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.ipa-panel__badge {
  font-size: 10px;
  font-weight: 600;
  color: #6366f1;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.1);
}

.ipa-panel__badge--soft {
  color: #64748b;
  background: rgba(148, 163, 184, 0.14);
}

.ipa-panel__badge--inspector {
  color: #4338ca;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.18);
}

.ipa-panel__badge--product {
  color: #0369a1;
  background: rgba(14, 165, 233, 0.12);
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.ipa-session-csv-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid rgba(99, 102, 241, 0.28);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  font-size: 10px;
  font-weight: 700;
  color: #4338ca;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ipa-session-csv-btn:hover:not(:disabled) {
  background: #eef2ff;
  border-color: rgba(99, 102, 241, 0.45);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.12);
}

.ipa-session-csv-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ipa-panel--inspector {
  background: linear-gradient(165deg, #ffffff 0%, #f5f3ff 100%);
  border-color: rgba(99, 102, 241, 0.16);
  box-shadow: 0 4px 24px rgba(99, 102, 241, 0.06);
}

.ipa-panel--product {
  background: linear-gradient(165deg, #ffffff 0%, #f0f9ff 100%);
  border-color: rgba(14, 165, 233, 0.16);
  box-shadow: 0 4px 24px rgba(14, 165, 233, 0.06);
}

.ipa-panel__ico--inspector {
  color: #6366f1;
}

.ipa-panel__ico--product {
  color: #0ea5e9;
}

.ipa-chart {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.6) 0%, rgba(255, 255, 255, 0.3) 100%);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.ipa-chart--main {
  height: 320px;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 1);
}

.ipa-chart--side {
  height: 196px;
  margin-bottom: 10px;
  border-radius: 12px;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 1);
}

.ipa-chart--inspector {
  border-color: rgba(199, 210, 254, 0.7);
}

.ipa-chart--product {
  border-color: rgba(186, 230, 253, 0.85);
}

.ipa-chart--rank {
  height: 220px;
  margin-bottom: 0;
  border: none;
  border-radius: 0 0 12px 12px;
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
  box-shadow: none;
}

.ipa-panel--rank {
  padding: 14px 16px 12px;
  background:
    radial-gradient(ellipse 80% 60% at 100% 0%, rgba(251, 191, 36, 0.12) 0%, transparent 55%),
    linear-gradient(165deg, #ffffff 0%, #fffbeb 48%, #fef3c7 100%);
  border-color: rgba(245, 158, 11, 0.22);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 32px rgba(245, 158, 11, 0.08);
  position: relative;
  overflow: hidden;
}

.ipa-panel--rank::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
  background-size: 200% 100%;
  animation: ipa-rank-shimmer 4s ease-in-out infinite;
}

.ipa-rank-panel__head {
  margin-bottom: 10px;
}

.ipa-rank-title-ico {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  color: #d97706;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border: 1px solid rgba(245, 158, 11, 0.3);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.ipa-rank-panel__desc {
  margin-top: 2px;
  font-size: 10px;
  font-weight: 500;
  color: #94a3b8;
}

.ipa-panel__badge--rank {
  color: #b45309;
  background: rgba(251, 191, 36, 0.18);
  border: 1px solid rgba(245, 158, 11, 0.28);
}

.ipa-rank-toolbar {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(253, 230, 138, 0.55);
  backdrop-filter: blur(8px);
}

.ipa-rank-picker {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ipa-rank-picker__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #92400e;
  white-space: nowrap;
}

.ipa-rank-picker__select {
  flex: 1;
  max-width: 420px;
}

.ipa-rank-picker__select :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.2) inset;
  transition: box-shadow 0.2s ease;
}

.ipa-rank-picker__select :deep(.el-input__wrapper:hover),
.ipa-rank-picker__select :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.45) inset, 0 4px 12px rgba(245, 158, 11, 0.12);
}

.ipa-rank-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ipa-rank-hero {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  padding: 14px 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(254, 243, 199, 0.35) 100%);
  border: 1px solid rgba(251, 191, 36, 0.35);
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.1);
  overflow: hidden;
}

.ipa-rank-hero__glow {
  position: absolute;
  top: -40%;
  right: -10%;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.25) 0%, transparent 70%);
  pointer-events: none;
  animation: ipa-rank-glow 5s ease-in-out infinite;
}

.ipa-rank-hero__main {
  position: relative;
  flex: 1;
  min-width: 160px;
}

.ipa-rank-hero__cd {
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  font-weight: 800;
  color: #b45309;
  padding: 3px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(245, 158, 11, 0.25);
  letter-spacing: 0.03em;
}

.ipa-rank-hero__name {
  margin: 6px 0 0;
  font-size: 15px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.ipa-rank-hero__stats {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  flex: 1.4;
  min-width: 280px;
}

.ipa-rank-hero__stat {
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(226, 232, 240, 0.9);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.ipa-rank-hero__stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
}

.ipa-rank-hero__stat--accent {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-color: rgba(245, 158, 11, 0.35);
}

.ipa-rank-hero__stat-label {
  display: block;
  font-size: 9px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.ipa-rank-hero__stat-val {
  display: block;
  margin-top: 2px;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.ipa-rank-hero__stat-val small {
  margin-left: 2px;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}

.ipa-rank-hero__stat--accent .ipa-rank-hero__stat-val {
  color: #b45309;
}

.ipa-podium--hd {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 10px;
  align-items: end;
  padding: 8px 4px 0;
}

.ipa-podium__col {
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: ipa-podium-rise 0.65s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--podium-delay, 0s);
}

.ipa-podium__item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 12px 10px 14px;
  border-radius: 14px 14px 4px 4px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease;
}

.ipa-podium__col:hover .ipa-podium__item {
  transform: translateY(-6px);
}

.ipa-podium__item--1 {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 50%, #ffffff 100%);
  border-color: rgba(245, 158, 11, 0.4);
  box-shadow: 0 12px 32px rgba(245, 158, 11, 0.22);
}

.ipa-podium__item--2 {
  border-color: rgba(148, 163, 184, 0.5);
}

.ipa-podium__item--3 {
  border-color: rgba(251, 146, 60, 0.35);
}

.ipa-podium__crown {
  position: absolute;
  top: -14px;
  font-size: 18px;
  animation: ipa-crown-bob 2.5s ease-in-out infinite;
  filter: drop-shadow(0 2px 4px rgba(245, 158, 11, 0.4));
}

.ipa-podium__medal-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.ipa-podium__col--1 .ipa-podium__medal-wrap {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.3);
}

.ipa-podium__medal {
  font-size: 22px;
  line-height: 1;
}

.ipa-podium__name {
  margin-top: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ipa-podium__eff {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 800;
  color: #059669;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.ipa-podium__col--1 .ipa-podium__eff {
  color: #b45309;
  font-size: 24px;
}

.ipa-podium__sub {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
}

.ipa-podium__pedestal {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72%;
  margin-top: 4px;
  border-radius: 0 0 8px 8px;
  background: linear-gradient(180deg, #e2e8f0, #cbd5e1);
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.5);
  transition: height 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.ipa-podium__col--1 .ipa-podium__pedestal {
  background: linear-gradient(180deg, #fde68a, #f59e0b);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}

.ipa-podium__col--2 .ipa-podium__pedestal {
  background: linear-gradient(180deg, #e2e8f0, #94a3b8);
}

.ipa-podium__col--3 .ipa-podium__pedestal {
  background: linear-gradient(180deg, #fed7aa, #ea580c);
}

.ipa-podium__pedestal-rank {
  font-size: 14px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.ipa-rank-chart-block {
  border-radius: 12px;
  border: 1px solid rgba(253, 230, 138, 0.6);
  background: #ffffff;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.08);
}

.ipa-rank-chart-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: linear-gradient(90deg, rgba(254, 243, 199, 0.6), rgba(255, 255, 255, 0.9));
  border-bottom: 1px solid rgba(253, 230, 138, 0.5);
}

.ipa-rank-chart-block__title {
  font-size: 11px;
  font-weight: 700;
  color: #92400e;
}

.ipa-rank-chart-block__badge {
  font-size: 10px;
  font-weight: 700;
  color: #b45309;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(251, 191, 36, 0.2);
}

.ipa-rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: #475569;
  background: #f1f5f9;
}

.ipa-rank-badge--gold {
  color: #92400e;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.ipa-rank-badge--silver {
  color: #475569;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
}

.ipa-rank-badge--bronze {
  color: #9a3412;
  background: linear-gradient(135deg, #ffedd5, #fed7aa);
}

.ipa-num--lg {
  font-size: 13px;
}

.ipa-rank-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 28px 20px;
  text-align: center;
  border: 1px dashed rgba(245, 158, 11, 0.35);
  border-radius: 12px;
  background: rgba(255, 251, 235, 0.5);
}

.ipa-rank-empty__ico {
  color: #f59e0b;
  opacity: 0.7;
}

.ipa-rank-empty p {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
}

.ipa-rank-empty__hint {
  font-size: 11px;
  color: #94a3b8;
}

.ipa-rank-overview {
  margin-top: 14px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(253, 230, 138, 0.45);
}

.ipa-rank-overview__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.ipa-rank-overview__ico {
  font-size: 14px;
  color: #d97706;
}

.ipa-rank-overview__title {
  flex: 1;
  font-size: 12px;
  font-weight: 700;
  color: #78350f;
}

.ipa-rank-overview__count {
  font-size: 10px;
  font-weight: 700;
  color: #b45309;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(251, 191, 36, 0.2);
}

.ipa-rank-top-inspector {
  font-weight: 600;
  color: #334155;
}

.ipa-rank-detail-btn {
  padding: 3px 10px;
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 10px;
  font-weight: 700;
  color: #b45309;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ipa-rank-detail-btn:hover {
  background: #fef3c7;
  border-color: rgba(245, 158, 11, 0.55);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(245, 158, 11, 0.15);
}

.ipa-rank-detail-btn--active {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}

.ipa-rank-swap-enter-active,
.ipa-rank-swap-leave-active {
  transition: opacity 0.28s ease, transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.ipa-rank-swap-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.ipa-rank-swap-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.ipa-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.ipa-weld-rank-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.ipa-panel--weld-rank {
  padding: 12px 14px 10px;
}

.ipa-panel--weld-rank--off {
  background: linear-gradient(165deg, #ffffff 0%, #f0fdf4 100%);
  border-color: rgba(16, 185, 129, 0.18);
  box-shadow: 0 4px 24px rgba(16, 185, 129, 0.06);
}

.ipa-panel--weld-rank--on {
  background: linear-gradient(165deg, #ffffff 0%, #fff7ed 100%);
  border-color: rgba(249, 115, 22, 0.2);
  box-shadow: 0 4px 24px rgba(249, 115, 22, 0.07);
}

.ipa-panel__subtitle {
  display: block;
  margin-top: 2px;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.01em;
}

.ipa-panel__ico--weld-off {
  color: #059669;
}

.ipa-panel__ico--weld-on {
  color: #ea580c;
}

.ipa-panel__badge--weld-off {
  color: #047857;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.ipa-panel__badge--weld-on {
  color: #c2410c;
  background: rgba(249, 115, 22, 0.12);
  border: 1px solid rgba(249, 115, 22, 0.22);
}

.ipa-table--weld-off :deep(.el-table__header th) {
  background: linear-gradient(180deg, #d1fae5, #a7f3d0) !important;
  color: #047857;
}

.ipa-table--weld-off :deep(.el-table__body tr:hover > td) {
  background: rgba(16, 185, 129, 0.07) !important;
}

.ipa-table--weld-on :deep(.el-table__header th) {
  background: linear-gradient(180deg, #ffedd5, #fed7aa) !important;
  color: #c2410c;
}

.ipa-table--weld-on :deep(.el-table__body tr:hover > td) {
  background: rgba(249, 115, 22, 0.07) !important;
}

.ipa-eff-pill--weld-off {
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.16);
}

.ipa-eff-pill--weld-on {
  color: #c2410c;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.18);
}

.ipa-weld-rank-hint {
  margin: 0 0 8px;
  font-size: 11px;
  line-height: 1.45;
  color: #64748b;
}

.ipa-weld-rank-hint--warn {
  color: #c2410c;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(254, 243, 199, 0.65);
  border: 1px solid rgba(251, 146, 60, 0.35);
}

.ipa-inspector-link {
  max-width: 100%;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: transparent;
  text-underline-offset: 2px;
  transition: color 0.15s ease, text-decoration-color 0.15s ease;
}

.ipa-inspector-link--weld-off {
  color: #047857;
}

.ipa-inspector-link--weld-off:hover {
  color: #059669;
  text-decoration-color: rgba(5, 150, 105, 0.45);
}

.ipa-inspector-link--weld-on {
  color: #c2410c;
}

.ipa-inspector-link--weld-on:hover {
  color: #ea580c;
  text-decoration-color: rgba(234, 88, 12, 0.45);
}

.ipa-inspector-product-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.16);
}

.ipa-inspector-product-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 16px 18px 14px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.ipa-inspector-product-dialog :deep(.el-dialog__body) {
  padding: 14px 18px 18px;
}

.ipa-inspector-product-dialog--weld-off :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 72%);
}

.ipa-inspector-product-dialog--weld-on :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #fff7ed 0%, #ffffff 72%);
}

.ipa-insp-prod-dlg__header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ipa-insp-prod-dlg__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
}

.ipa-inspector-product-dialog--weld-off .ipa-insp-prod-dlg__avatar {
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.22);
}

.ipa-inspector-product-dialog--weld-on .ipa-insp-prod-dlg__avatar {
  color: #ea580c;
  border: 1px solid rgba(249, 115, 22, 0.25);
}

.ipa-insp-prod-dlg__title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.ipa-insp-prod-dlg__subtitle {
  margin-top: 2px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.ipa-insp-prod-dlg__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ipa-insp-prod-dlg__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.ipa-insp-prod-dlg__stat {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.ipa-inspector-product-dialog--weld-off .ipa-insp-prod-dlg__stat--accent {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  border-color: rgba(16, 185, 129, 0.25);
}

.ipa-inspector-product-dialog--weld-on .ipa-insp-prod-dlg__stat--accent {
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border-color: rgba(249, 115, 22, 0.28);
}

.ipa-insp-prod-dlg__stat-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}

.ipa-insp-prod-dlg__stat-value {
  display: block;
  margin-top: 2px;
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.ipa-insp-prod-dlg__stat-value small {
  margin-left: 2px;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}

.ipa-inspector-product-dialog--weld-off .ipa-insp-prod-dlg__stat--accent .ipa-insp-prod-dlg__stat-value {
  color: #047857;
}

.ipa-inspector-product-dialog--weld-on .ipa-insp-prod-dlg__stat--accent .ipa-insp-prod-dlg__stat-value {
  color: #c2410c;
}

.ipa-insp-prod-dlg__period {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
}

.ipa-insp-prod-dlg__table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.ipa-inspector-product-dialog--weld-off .ipa-insp-prod-dlg__table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #d1fae5, #a7f3d0) !important;
  color: #047857;
}

.ipa-inspector-product-dialog--weld-on .ipa-insp-prod-dlg__table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #ffedd5, #fed7aa) !important;
  color: #c2410c;
}

.ipa-inspector-product-dialog--weld-off .ipa-insp-prod-dlg__table :deep(.el-table__body tr:hover > td) {
  background: rgba(16, 185, 129, 0.06) !important;
}

.ipa-inspector-product-dialog--weld-on .ipa-insp-prod-dlg__table :deep(.el-table__body tr:hover > td) {
  background: rgba(249, 115, 22, 0.06) !important;
}

.ipa-product-cd--dlg {
  font-size: 10px;
}

.ipa-num--dlg-qty {
  color: #334155;
  font-weight: 700;
}

.ipa-eff-pill--warn {
  color: #c2410c;
  background: rgba(254, 243, 199, 0.75);
  border: 1px solid rgba(251, 146, 60, 0.35);
}

@media (max-width: 640px) {
  .ipa-insp-prod-dlg__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.ipa-defect-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ipa-defect-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border: 1px solid rgba(251, 146, 60, 0.25);
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.1);
  animation: ipa-kpi-in 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition: transform 0.2s ease;
}

.ipa-defect-chip:hover {
  transform: translateY(-2px);
}

.ipa-defect-chip__name {
  font-size: 11px;
  font-weight: 600;
  color: #9a3412;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ipa-defect-chip__qty {
  font-size: 13px;
  font-weight: 800;
  color: #c2410c;
}

.ipa-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f1f5f9, #e2e8f0) !important;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  padding: 6px 0;
}

.ipa-table :deep(.el-table__body td) {
  font-size: 11px;
  padding: 5px 0;
}

.ipa-table :deep(.el-table__row) {
  transition: background 0.15s ease;
}

.ipa-table :deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.06) !important;
}

.ipa-table--inspector :deep(.el-table__header th) {
  background: linear-gradient(180deg, #ede9fe, #e0e7ff) !important;
  color: #4338ca;
}

.ipa-table--inspector :deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.07) !important;
}

.ipa-table--product :deep(.el-table__header th) {
  background: linear-gradient(180deg, #e0f2fe, #bae6fd) !important;
  color: #0369a1;
}

.ipa-table--product :deep(.el-table__body tr:hover > td) {
  background: rgba(14, 165, 233, 0.07) !important;
}

.ipa-table--rank {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(253, 230, 138, 0.5);
}

.ipa-table--rank :deep(.el-table__header th) {
  background: linear-gradient(180deg, #fef3c7, #fde68a) !important;
  color: #92400e;
}

.ipa-table--rank :deep(.el-table__body tr:hover > td) {
  background: rgba(245, 158, 11, 0.07) !important;
}

.ipa-table--rank-overview {
  border-radius: 10px;
  overflow: hidden;
}

.ipa-table--rank-overview :deep(.el-table__header th) {
  background: linear-gradient(180deg, #fffbeb, #fef3c7) !important;
  color: #92400e;
}

.ipa-table--rank-overview :deep(.el-table__body tr:hover > td) {
  background: rgba(251, 191, 36, 0.08) !important;
}

.ipa-table--rank-overview :deep(.ipa-rank-overview-row--active > td) {
  background: rgba(254, 243, 199, 0.55) !important;
}

.ipa-num--rank-qty {
  font-weight: 700;
  color: #334155;
}

.ipa-product-cd--rank {
  color: #b45309;
}

.ipa-eff-pill--rank {
  color: #b45309;
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.28);
}

.ipa-row-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 4px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  background: rgba(148, 163, 184, 0.15);
}

.ipa-row-rank--gold {
  color: #92400e;
  background: linear-gradient(135deg, #fde68a, #fcd34d);
}

.ipa-row-rank--silver {
  color: #475569;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
}

.ipa-row-rank--bronze {
  color: #9a3412;
  background: linear-gradient(135deg, #fed7aa, #fdba74);
}

.ipa-product-cd {
  font-size: 10px;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #0369a1;
  letter-spacing: 0.02em;
}

.ipa-eff-pill {
  display: inline-block;
  min-width: 28px;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.ipa-eff-pill--inspector {
  color: #4338ca;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.ipa-eff-pill--product {
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.ipa-num--product {
  color: #0284c7;
}

.ipa-num {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.ipa-num--good {
  color: #059669;
}

.ipa-num--warn {
  color: #ea580c;
}

.ipa-status {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.ipa-status--ok {
  color: #047857;
  background: rgba(16, 185, 129, 0.15);
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.2);
}

.ipa-status--pending {
  color: #64748b;
  background: rgba(148, 163, 184, 0.2);
}

.ipa-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 20px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px dashed rgba(148, 163, 184, 0.4);
  color: #64748b;
  font-size: 13px;
}

.ipa-empty__icon {
  color: #94a3b8;
  opacity: 0.7;
}

/* Animations */
.ipa-fade-in {
  animation: ipa-fade-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ipa-fade-in--d1 { animation-delay: 0.05s; }
.ipa-fade-in--d2 { animation-delay: 0.1s; }
.ipa-fade-in--d3 { animation-delay: 0.15s; }
.ipa-fade-in--d4 { animation-delay: 0.2s; }
.ipa-fade-in--d5 { animation-delay: 0.25s; }
.ipa-fade-in--d5b { animation-delay: 0.28s; }
.ipa-fade-in--d6 { animation-delay: 0.3s; }
.ipa-fade-in--d7 { animation-delay: 0.35s; }

@keyframes ipa-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes ipa-kpi-in {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes ipa-rank-shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes ipa-rank-glow {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}

@keyframes ipa-podium-rise {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes ipa-crown-bob {
  0%, 100% { transform: translateY(0) rotate(-5deg); }
  50% { transform: translateY(-4px) rotate(5deg); }
}

.ipa-reveal-enter-active {
  transition: opacity 0.4s ease, transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.ipa-reveal-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.ipa-reveal-enter-from,
.ipa-reveal-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (max-width: 1200px) {
  .ipa-kpi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ipa-split,
  .ipa-weld-rank-split {
    grid-template-columns: 1fr;
  }

  .ipa-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .ipa-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .ipa-kpi {
    grid-template-columns: 1fr;
  }

  .ipa-field__date {
    width: 100% !important;
  }

  .ipa-field__control {
    width: 100%;
  }

  .ipa-rank-hero__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    min-width: 0;
  }

  .ipa-podium--hd {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .ipa-podium__col {
    flex-direction: row;
    gap: 10px;
  }

  .ipa-podium__pedestal {
    width: 48px;
    height: 48px !important;
    margin-top: 0;
    border-radius: 10px;
  }
}
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
