<template>
  <div class="pr-page" v-loading="loading">
    <div class="pr-bg" aria-hidden="true">
      <span class="pr-orb pr-orb--1" />
      <span class="pr-orb pr-orb--2" />
      <span class="pr-orb pr-orb--3" />
    </div>

    <header class="pr-toolbar pr-glass pr-animate-in">
      <div class="pr-brand">
        <div class="pr-brand__icon" aria-hidden="true">
          <el-icon :size="22"><Document /></el-icon>
        </div>
        <div class="pr-brand__text">
          <h1>生産検討会資料</h1>
          <p>
            <span class="pr-brand__badge">{{ meetingLabel }}</span>
            <span class="pr-brand__sep">·</span>
            PART 01〜03
          </p>
        </div>
      </div>

      <div class="pr-controls">
        <div class="pr-controls__panel">
          <el-date-picker
            v-model="targetMonth"
            type="month"
            value-format="YYYY-MM"
            format="YYYY年M月"
            placeholder="対象月"
            size="default"
            class="pr-month"
            @change="onMonthChange"
          />
          <span
            v-if="recordStatus"
            class="pr-status"
            :class="recordStatus === 'final' ? 'pr-status--final' : 'pr-status--draft'"
          >
            <span class="pr-status__dot" />
            {{ recordStatus === 'final' ? '確定' : '下書き' }}
          </span>
          <span
            v-if="dataSource"
            class="pr-status"
            :class="dataSource === 'saved' ? 'pr-status--saved' : 'pr-status--live'"
          >
            <span class="pr-status__dot" />
            {{ dataSource === 'saved' ? '保存済' : '自動集計' }}
          </span>
        </div>
      </div>

      <div class="pr-actions">
        <button
          type="button"
          class="pr-action-btn pr-action-btn--ghost"
          :disabled="loading"
          @click="openCapacityDialog"
        >
          <el-icon><Setting /></el-icon>
          <span>工程能力</span>
        </button>
        <button
          type="button"
          class="pr-action-btn pr-action-btn--ghost pr-action-btn--refresh"
          :disabled="loading || !payload"
          @click="onRecalculate"
        >
          <el-icon><Refresh /></el-icon>
          <span>再計算</span>
        </button>
        <button
          type="button"
          class="pr-action-btn pr-action-btn--warn"
          :disabled="!payload"
          @click="onSave('draft')"
        >
          <el-icon><EditPen /></el-icon>
          <span>下書き保存</span>
        </button>
        <button
          type="button"
          class="pr-action-btn pr-action-btn--primary"
          :disabled="!payload"
          @click="onSave('final')"
        >
          <el-icon><CircleCheck /></el-icon>
          <span>確定保存</span>
        </button>
        <button
          type="button"
          class="pr-action-btn pr-action-btn--success"
          :disabled="!payload || pptLoading"
          @click="onDownloadPpt"
        >
          <el-icon><Download /></el-icon>
          <span>{{ pptLoading ? '生成中…' : 'PPT生成' }}</span>
        </button>
      </div>
    </header>

    <div v-if="savedMonths.length" class="pr-saved pr-glass pr-animate-in" style="animation-delay: 0.05s">
      <span class="pr-saved__label">保存済み</span>
      <div
        v-for="m in savedMonths"
        :key="m.target_month"
        class="pr-saved__chip"
        :class="{ active: m.target_month === targetMonth, final: m.status === 'final' }"
      >
        <button type="button" class="pr-saved__chip-main" @click="selectMonth(m.target_month)">
          {{ m.target_month }} · {{ m.status === 'final' ? '確定' : '下書き' }}
        </button>
        <button
          type="button"
          class="pr-saved__chip-del"
          title="削除して最新データから再生成"
          :disabled="loading || deletingMonth === m.target_month"
          @click.stop="onDeleteSaved(m.target_month)"
        >
          <el-icon :size="12"><Close /></el-icon>
        </button>
      </div>
    </div>

    <el-empty v-if="!payload && !loading" class="pr-empty" description="対象月を選択してください" />

    <div v-else-if="payload" class="pr-body pr-glass pr-animate-in" style="animation-delay: 0.1s">
      <el-tabs v-model="activeTab" class="pr-tabs">
        <el-tab-pane name="part01">
          <template #label>
            <span class="pr-tab-label pr-tab-label--blue">01 実績・廃棄率・在庫</span>
          </template>

          <section class="pr-card pr-card--blue pr-card--performance">
            <div class="pr-card__head pr-card__head--performance">
              <h2>{{ payload.part01.performance.month_label }} 工程別実績一覧</h2>
              <div class="pr-col-toggles">
                <button
                  type="button"
                  class="pr-col-toggle"
                  :class="{ 'is-on': showForecastCols }"
                  @click="showForecastCols = !showForecastCols"
                >
                  <span class="pr-col-toggle__indicator" />
                  実見(千本) · 対実見
                </button>
                <button
                  type="button"
                  class="pr-col-toggle"
                  :class="{ 'is-on': showActualCols }"
                  @click="showActualCols = !showActualCols"
                >
                  <span class="pr-col-toggle__indicator" />
                  実績(千本) · 対計画
                </button>
                <button type="button" class="pr-eff-trend-btn" @click="openEfficiencyTrendDialog">
                  <el-icon :size="15"><TrendCharts /></el-icon>
                  時間当たり能率推移
                </button>
              </div>
            </div>
            <div class="pr-table-wrap pr-table-wrap--performance">
              <el-table
                :key="`perf-${showForecastCols}-${showActualCols}`"
                :data="payload.part01.performance.rows"
                border
                class="pr-table pr-table--modern pr-table--performance"
                stripe
              >
                <el-table-column prop="name" label="工程名" min-width="108" fixed />
                <el-table-column label="工程計画(千本)" min-width="128" align="center">
                  <template #default="{ row }">
                    <input
                      v-if="isPerfEditing(row.key, 'plan_th')"
                      class="pr-perf-edit-input"
                      type="number"
                      step="0.1"
                      v-model.number="perfEditDraft"
                      @blur="commitPerfEdit"
                      @keydown.enter.prevent="commitPerfEdit"
                      @keydown.esc.prevent="cancelPerfEdit"
                      @click.stop
                    />
                    <span
                      v-else
                      class="pr-perf-val pr-perf-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startPerfEdit(row, 'plan_th')"
                    >{{ fmtNum(row.plan_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showForecastCols" label="実見(千本)" min-width="118" align="center">
                  <template #default="{ row }">
                    <input
                      v-if="isPerfEditing(row.key, 'forecast_th')"
                      class="pr-perf-edit-input"
                      type="number"
                      step="0.1"
                      v-model.number="perfEditDraft"
                      @blur="commitPerfEdit"
                      @keydown.enter.prevent="commitPerfEdit"
                      @keydown.esc.prevent="cancelPerfEdit"
                      @click.stop
                    />
                    <span
                      v-else
                      class="pr-perf-val pr-perf-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startPerfEdit(row, 'forecast_th')"
                    >{{ fmtNum(row.forecast_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showActualCols" label="実績(千本)" min-width="118" align="center">
                  <template #default="{ row }">
                    <input
                      v-if="isPerfEditing(row.key, 'actual_th')"
                      class="pr-perf-edit-input"
                      type="number"
                      step="0.1"
                      v-model.number="perfEditDraft"
                      @blur="commitPerfEdit"
                      @keydown.enter.prevent="commitPerfEdit"
                      @keydown.esc.prevent="cancelPerfEdit"
                      @click.stop
                    />
                    <span
                      v-else
                      class="pr-perf-actual pr-perf-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startPerfEdit(row, 'actual_th')"
                    >{{ fmtNum(row.actual_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showForecastCols" label="対実見" min-width="108" align="center">
                  <template #default="{ row }">
                    <span :class="deltaClass(row.vs_forecast_th)">{{ fmtDelta(row.vs_forecast_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showActualCols" label="対計画" min-width="108" align="center">
                  <template #default="{ row }">
                    <span :class="deltaClass(row.vs_plan_th)">{{ fmtDelta(row.vs_plan_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="前月時間当たり能率" min-width="140" align="center">
                  <template #default="{ row }">
                    <span v-if="row.key === 'shipping'" class="pr-perf-muted">—</span>
                    <template v-else>
                      <input
                        v-if="isPerfEditing(row.key, 'productivity_prev')"
                        class="pr-perf-edit-input pr-perf-edit-input--prod"
                        type="number"
                        step="1"
                        v-model.number="perfEditDraft"
                        @blur="commitPerfEdit"
                        @keydown.enter.prevent="commitPerfEdit"
                        @keydown.esc.prevent="cancelPerfEdit"
                        @click.stop
                      />
                      <span
                        v-else
                        class="pr-perf-prod pr-perf-val--editable"
                        title="ダブルクリックで編集"
                        @dblclick.stop="startPerfEdit(row, 'productivity_prev')"
                      >{{ fmtProductivity(row.productivity_prev) }}</span>
                    </template>
                  </template>
                </el-table-column>
                <el-table-column label="当月時間当たり能率" min-width="140" align="center">
                  <template #default="{ row }">
                    <span v-if="row.key === 'shipping'" class="pr-perf-muted">—</span>
                    <template v-else>
                      <input
                        v-if="isPerfEditing(row.key, 'productivity_curr')"
                        class="pr-perf-edit-input pr-perf-edit-input--prod"
                        type="number"
                        step="1"
                        v-model.number="perfEditDraft"
                        @blur="commitPerfEdit"
                        @keydown.enter.prevent="commitPerfEdit"
                        @keydown.esc.prevent="cancelPerfEdit"
                        @click.stop
                      />
                      <span
                        v-else
                        class="pr-perf-prod pr-perf-val--editable"
                        title="ダブルクリックで編集"
                        @dblclick.stop="startPerfEdit(row, 'productivity_curr')"
                      >{{ fmtProductivity(row.productivity_curr) }}</span>
                    </template>
                  </template>
                </el-table-column>
                <el-table-column label="増減" min-width="88" align="center">
                  <template #default="{ row }">
                    <template v-if="row.key === 'shipping'">
                      <span class="pr-perf-muted">—</span>
                    </template>
                    <span v-else :class="prodDeltaClass(calcProdDelta(row))">{{ fmtProdDelta(calcProdDelta(row)) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div class="pr-perf-comment">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><ChatDotRound /></el-icon>
                  </span>
                  <div>
                    <strong>コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button
                    round
                    :loading="commentRegenLoading === 'performance'"
                    @click="regenerateSectionComments('performance')"
                  >
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="primary" round @click="openCommentDialog('performance')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>

              <div v-if="perfCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in perfCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>

          <section class="pr-card pr-card--orange">
            <div class="pr-card__head pr-card__head--scrap">
              <div>
                <h2>廃棄率及び廃棄本数</h2>
                <p class="pr-card__sub">
                  {{ scrapMeta.fiscalLabel }}
                  <span v-if="scrapMeta.rangeLabel" class="pr-range-badge">{{ scrapMeta.rangeLabel }}</span>
                </p>
              </div>
              <div class="pr-scrap-head-actions">
                <el-button
                  type="warning"
                  round
                  :loading="scrapPptLoading"
                  :disabled="!payload || scrapPptLoading"
                  @click="onDownloadScrapPpt"
                >
                  <el-icon><Download /></el-icon>
                  <span>{{ scrapPptLoading ? '生成中…' : '廃棄PPT' }}</span>
                </el-button>
                <div class="pr-scrap-range">
                  <span class="pr-scrap-range__label">期間</span>
                  <el-select
                    v-model="scrapRangeFrom"
                    size="small"
                    class="pr-scrap-range__select"
                    :disabled="!scrapMonthOptions.length"
                    @change="onScrapRangeChange"
                  >
                    <el-option
                      v-for="opt in scrapMonthOptions"
                      :key="`from-${opt.value}`"
                      :label="opt.label"
                      :value="opt.value"
                      :disabled="scrapRangeTo != null && opt.value > scrapRangeTo"
                    />
                  </el-select>
                  <span class="pr-scrap-range__tilde">〜</span>
                  <el-select
                    v-model="scrapRangeTo"
                    size="small"
                    class="pr-scrap-range__select"
                    :disabled="!scrapMonthOptions.length"
                    @change="onScrapRangeChange"
                  >
                    <el-option
                      v-for="opt in scrapMonthOptions"
                      :key="`to-${opt.value}`"
                      :label="opt.label"
                      :value="opt.value"
                      :disabled="scrapRangeFrom != null && opt.value < scrapRangeFrom"
                    />
                  </el-select>
                  <el-button size="small" text type="warning" :disabled="!scrapMonthOptions.length" @click="resetScrapRange">
                    リセット
                  </el-button>
                </div>
              </div>
            </div>

            <div class="pr-kpi-grid pr-kpi-grid--scrap">
              <div class="pr-kpi pr-kpi--violet">
                <span class="pr-kpi__label">当月廃棄率（新）</span>
                <strong class="pr-kpi__value">{{ scrapMeta.currentRateNew }}<small>%</small></strong>
                <span class="pr-kpi__hint">年度平均 {{ scrapMeta.avgRateNew }}%</span>
              </div>
              <div class="pr-kpi pr-kpi--rose">
                <span class="pr-kpi__label">当月廃棄率（旧）</span>
                <strong class="pr-kpi__value">{{ scrapMeta.currentRateOld }}<small>%</small></strong>
                <span class="pr-kpi__hint">年度平均 {{ scrapMeta.avgRateOld }}%</span>
              </div>
              <div class="pr-kpi pr-kpi--orange">
                <span class="pr-kpi__label">当月廃棄本数</span>
                <strong class="pr-kpi__value">{{ scrapMeta.currentLossQty }}<small>本</small></strong>
                <span class="pr-kpi__hint">年度平均 {{ scrapMeta.avgLossQty }} 本</span>
              </div>
              <div class="pr-kpi" :class="scrapMeta.improvementNewPositive ? 'pr-kpi--green' : 'pr-kpi--red'">
                <span class="pr-kpi__label">廃棄率（新）改善 pt</span>
                <strong class="pr-kpi__value">{{ scrapMeta.improvementRateNewPt }}<small>pt</small></strong>
                <span class="pr-kpi__hint">前年度比（低いほど良）</span>
              </div>
              <div class="pr-kpi" :class="scrapMeta.improvementOldPositive ? 'pr-kpi--green' : 'pr-kpi--red'">
                <span class="pr-kpi__label">廃棄率（旧）改善 pt</span>
                <strong class="pr-kpi__value">{{ scrapMeta.improvementRateOldPt }}<small>pt</small></strong>
                <span class="pr-kpi__hint">前年度比（低いほど良）</span>
              </div>
            </div>

            <p class="pr-scrap-formula">
              <span class="pr-scrap-formula__tag pr-scrap-formula__tag--new">新</span>
              主ライン（切断〜検査）連乗ロス率
              <span class="pr-scrap-formula__sep">|</span>
              <span class="pr-scrap-formula__tag pr-scrap-formula__tag--old">旧</span>
              全工程（不良＋廃棄）÷ 切断実績
              <span class="pr-scrap-formula__sep">|</span>
              <span class="pr-scrap-formula__tag pr-scrap-formula__tag--qty">本</span>
              不良＋廃棄本数
            </p>

            <div v-if="scrapMeta.monthly.length" class="pr-chart-panel">
              <div class="pr-chart-panel__head">
                <div class="pr-chart-panel__title">
                  <span class="pr-chart-panel__badge">CHART</span>
                  <strong>月次トレンド</strong>
                </div>
                <div class="pr-chart-panel__legend">
                  <span class="pr-chart-chip pr-chart-chip--qty"><i />廃棄本数</span>
                  <span class="pr-chart-chip pr-chart-chip--new"><i />廃棄率（新）</span>
                  <span class="pr-chart-chip pr-chart-chip--old"><i />廃棄率（旧）</span>
                </div>
              </div>
              <div ref="scrapChartRef" class="pr-chart" />
            </div>
            <el-empty v-else description="月度データがありません" :image-size="72" />

            <div v-if="scrapMeta.monthly.length" class="pr-monthly-grid pr-monthly-grid--scrap">
              <div
                v-for="(m, idx) in scrapMeta.monthly"
                :key="`${m.year}-${m.month}`"
                class="pr-month-card pr-month-card--scrap"
                :class="{ 'pr-month-card--current': idx === scrapMeta.monthly.length - 1 }"
              >
                <span class="pr-month-card__label">{{ m.month }}月</span>
                <span class="pr-month-card__rate-new">{{ scrapRate(m, 'new') }}<small>%</small></span>
                <span class="pr-month-card__rate-old">{{ scrapRate(m, 'old') }}<small>%</small></span>
                <span class="pr-month-card__loss">{{ fmtInt(scrapLossQty(m)) }}<small>本</small></span>
              </div>
            </div>

            <div class="pr-perf-comment pr-perf-comment--scrap">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><WarningFilled /></el-icon>
                  </span>
                  <div>
                    <strong>廃棄コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button
                    round
                    :loading="commentRegenLoading === 'scrap'"
                    @click="regenerateSectionComments('scrap')"
                  >
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="warning" round @click="openCommentDialog('scrap')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>

              <div v-if="scrapCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in scrapCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>

          <section class="pr-card pr-card--teal pr-card--inventory">
            <div class="pr-card__head pr-card__head--inventory">
              <div class="pr-inv-title">
                <h2>{{ payload.part01.inventory.inventory_month_label }} 月末在庫</h2>
                <el-popover
                  placement="bottom-start"
                  :width="420"
                  trigger="click"
                  popper-class="pr-inv-help-popper"
                >
                  <template #reference>
                    <button type="button" class="pr-inv-help-btn" title="計算方法・例">
                      <el-icon :size="18"><QuestionFilled /></el-icon>
                    </button>
                  </template>
                  <div class="pr-inv-help">
                    <h4>月末在庫の計算方法</h4>
                    <ul>
                      <li>
                        <strong>稼働日補正内示</strong>
                        <code>工程内示 × (標準{{ payload.part01.inventory.standard_workdays ?? 20 }}日 ÷ 稼働日)</code>
                      </li>
                      <li>
                        <strong>補正在庫率（判定用）</strong>
                        <code>在庫 ÷ 稼働日補正内示</code>
                      </li>
                      <li>
                        <strong>在庫日数（判定用）</strong>
                        <code>在庫 ÷ (工程内示 ÷ 稼働日)</code>
                      </li>
                      <li>
                        <strong>補正率・日数の標準値</strong>
                        切断・成型 0.15（{{ fmtDays((0.15 * (payload.part01.inventory.standard_workdays ?? 20))) }}日）/
                        メッキ・溶接 0.19（{{ fmtDays((0.19 * (payload.part01.inventory.standard_workdays ?? 20))) }}日）/
                        製品 0.36（{{ fmtDays(payload.part01.inventory.product_target_days ?? 7.2) }}日）
                      </li>
                      <li>
                        <strong>製品判定</strong>
                        補正率 ≥ {{ fmtRate(payload.part01.inventory.product_target_rate ?? 0.36) }}
                        かつ 日数 ≥ {{ fmtDays(payload.part01.inventory.product_target_days ?? 7.2) }}日
                      </li>
                    </ul>
                    <h4>計算例</h4>
                    <div class="pr-inv-help__example">
                      <p>切断在庫 <b>50</b> 千本 / ルート按分出荷内示（KT01∪KT02） <b>200</b> 千本 / 稼働日 <b>10</b> 日</p>
                      <p>補正内示 = 200 × (20 ÷ 10) = <b>400</b> 千本</p>
                      <p>補正率 = 50 ÷ 400 = <b>0.13</b></p>
                      <p>在庫日数 = 50 ÷ (200 ÷ 10) = <b>2.5</b> 日</p>
                    </div>
                  </div>
                </el-popover>
              </div>
              <p class="pr-inv-forecast-line">
                {{ payload.part01.inventory.prev_forecast_label }}出荷内示
                <strong>{{ fmtNum(payload.part01.inventory.prev_forecast_th) }}</strong>
                千本
                <span class="pr-inv-forecast-sep">|</span>
                {{ payload.part01.inventory.curr_forecast_label }}出荷内示
                <strong>{{ fmtNum(payload.part01.inventory.curr_forecast_th) }}</strong>
                千本
                <span class="pr-inv-forecast-sep">|</span>
                {{ payload.part01.inventory.prev_forecast_label }}稼働日
                <strong class="pr-inv-forecast-line__wd">{{ invWorkdayDraft.prev || payload.part01.inventory.prev_workdays || '-' }}</strong>
                日
                <span class="pr-inv-forecast-sep">|</span>
                {{ payload.part01.inventory.curr_forecast_label }}稼働日
                <strong class="pr-inv-forecast-line__wd">{{ invWorkdayDraft.curr || payload.part01.inventory.curr_workdays || '-' }}</strong>
                日
              </p>
              <div class="pr-inv-wd__actions">
                <el-button round size="small" @click="openWorkingDaysDialog">年次一覧</el-button>
                <el-button type="success" round size="small" :loading="wdSaving" @click="saveInventoryWorkingDays">
                  稼働日を保存して再計算
                </el-button>
              </div>
            </div>

            <div class="pr-inv-kpi">
              <div
                class="pr-inv-kpi__card pr-inv-kpi__card--product"
                :class="`is-${inventoryProductLevel}`"
              >
                <span class="pr-inv-kpi__label">製品 補正在庫率</span>
                <p class="pr-inv-kpi__value">
                  {{ fmtRate(inventoryProductRow?.curr_rate_adj) }}
                  <small>/ 目標 {{ fmtRate(payload.part01.inventory.product_target_rate ?? 0.36) }}</small>
                </p>
                <span class="pr-inv-kpi__badge">{{ inventoryProductLevelLabel }}</span>
              </div>
              <div
                class="pr-inv-kpi__card pr-inv-kpi__card--product"
                :class="`is-${inventoryProductLevel}`"
              >
                <span class="pr-inv-kpi__label">製品 在庫日数</span>
                <p class="pr-inv-kpi__value">
                  {{ fmtDays(inventoryProductRow?.curr_days) }}
                  <small>日 / 目標 {{ fmtDays(payload.part01.inventory.product_target_days ?? 7.2) }}日</small>
                </p>
                <span class="pr-inv-kpi__hint">判定は補正率・日数</span>
              </div>
            </div>

            <div class="pr-table-wrap pr-table-wrap--performance pr-table-wrap--inventory">
              <el-table
                :data="payload.part01.inventory.rows"
                border
                row-key="key"
                :tree-props="{ children: 'children' }"
                class="pr-table pr-table--modern pr-table--performance pr-table--inventory"
                stripe
                :row-class-name="inventoryRowClassName"
              >
                <el-table-column label="工程名" min-width="128" fixed>
                  <template #default="{ row }">
                    <div class="pr-inv-name-cell">
                      <span class="pr-inv-name-cell__name">{{ row.name }}</span>
                      <span v-if="inventoryTargetLabel(row.key)" class="pr-inv-name-cell__std">
                        標準 {{ inventoryTargetLabel(row.key) }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="前月在庫(千本)" min-width="112" align="center" class-name="col-prev">
                  <template #default="{ row }">
                    <input
                      v-if="isInvEditable(row) && isInvEditing(row.key, 'prev_inventory_th')"
                      class="pr-inv-edit-input pr-inv-edit-input--prev"
                      type="number"
                      step="0.1"
                      v-model.number="invEditDraft"
                      @blur="commitInvEdit"
                      @keydown.enter.prevent="commitInvEdit"
                      @keydown.esc.prevent="cancelInvEdit"
                      @click.stop
                    />
                    <span
                      v-else-if="isInvEditable(row)"
                      class="pr-inv-val pr-inv-val--prev pr-inv-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startInvEdit(row, 'prev_inventory_th')"
                    >{{ fmtNum(row.prev_inventory_th) }}</span>
                    <span v-else class="pr-inv-val pr-inv-val--prev pr-inv-val--parent">{{ fmtNum(row.prev_inventory_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="前月在庫日数" min-width="96" align="center" class-name="col-prev">
                  <template #default="{ row }">
                    <span
                      class="pr-inv-days pr-inv-days--prev"
                      :class="inventoryMetricClass(row, row.prev_days, 'days')"
                    >{{ fmtDays(row.prev_days) }}<small>日</small></span>
                  </template>
                </el-table-column>
                <el-table-column min-width="120" align="center" class-name="col-curr">
                  <template #header>
                    <span
                      class="pr-inv-col-hdr pr-inv-col-hdr--clickable"
                      title="ダブルクリックで在庫基準日を選択"
                      @dblclick.stop="openCurrInvDateDialog"
                    >
                      {{ currInventoryHeaderLabel }}
                    </span>
                  </template>
                  <template #default="{ row }">
                    <input
                      v-if="isInvEditable(row) && isInvEditing(row.key, 'curr_inventory_th')"
                      class="pr-inv-edit-input pr-inv-edit-input--curr"
                      type="number"
                      step="0.1"
                      v-model.number="invEditDraft"
                      @blur="commitInvEdit"
                      @keydown.enter.prevent="commitInvEdit"
                      @keydown.esc.prevent="cancelInvEdit"
                      @click.stop
                    />
                    <span
                      v-else-if="isInvEditable(row)"
                      class="pr-inv-val pr-inv-val--curr pr-inv-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startInvEdit(row, 'curr_inventory_th')"
                    >{{ fmtNum(row.curr_inventory_th) }}</span>
                    <span v-else class="pr-inv-val pr-inv-val--curr pr-inv-val--parent">{{ fmtNum(row.curr_inventory_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="当月在庫日数" min-width="96" align="center" class-name="col-curr">
                  <template #default="{ row }">
                    <span
                      class="pr-inv-days"
                      :class="inventoryMetricClass(row, row.curr_days, 'days')"
                    >{{ fmtDays(row.curr_days) }}<small>日</small></span>
                  </template>
                </el-table-column>
                <el-table-column label="増減(千本)" min-width="96" align="center">
                  <template #default="{ row }">
                    <span :class="deltaClass(row.delta_th)">{{ fmtDelta(row.delta_th) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="pr-perf-comment pr-perf-comment--inventory">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><Box /></el-icon>
                  </span>
                  <div>
                    <strong>在庫コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button
                    round
                    :loading="commentRegenLoading === 'inventory'"
                    @click="regenerateSectionComments('inventory')"
                  >
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="success" round class="pr-inv-comment-btn" @click="openCommentDialog('inventory')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>

              <div v-if="inventoryCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in inventoryCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane name="part02">
          <template #label>
            <span class="pr-tab-label pr-tab-label--blue">02 {{ payload.part02.load_plan.month_label }} 生産計画・負荷率</span>
          </template>

          <section class="pr-card pr-card--blue pr-card--performance pr-card--load-plan">
            <div class="pr-card__head pr-card__head--performance">
              <div class="pr-load-title">
                <h2>{{ payload.part02.load_plan.month_label }} 生産計画・負荷率</h2>
                <el-popover
                  placement="bottom-start"
                  :width="480"
                  trigger="click"
                  popper-class="pr-load-help-popper"
                >
                  <template #reference>
                    <button type="button" class="pr-load-help-btn" title="負荷率の見方・計算式">
                      <el-icon :size="18"><QuestionFilled /></el-icon>
                    </button>
                  </template>
                  <div class="pr-load-help">
                    <h4>負荷率の見方</h4>
                    <div class="pr-load-help__legend">
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--overload">100%超</span>
                        要対策
                      </span>
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--tight">90%以上</span>
                        逼迫
                      </span>
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--ok">60〜90%</span>
                        適正
                      </span>
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--light">60%以下</span>
                        余裕
                      </span>
                    </div>
                    <h4>計算式</h4>
                    <ul>
                      <li>
                        <strong>負荷率</strong>
                        <code>所要H ÷ 定時H × 100</code>
                      </li>
                      <li>
                        <strong>定時H</strong>
                        <code>設備数 × 直数 × 7.6H × 稼働日 × 稼働率</code>
                        <span class="pr-load-help__note">人員は 人数 × 7.6H × 稼働日 × 稼働率</span>
                      </li>
                      <li>
                        <strong>計画(千本)</strong>
                        <code>元計画 × 計画調整率% ÷ 100</code>
                      </li>
                      <li>
                        <strong>所要H</strong>
                        <code>計画(本) ÷ 能率(本/H)</code>
                      </li>
                      <li>
                        <strong>日均H</strong>
                        <code>所要H ÷ 稼働日 ÷ 設備数</code>
                      </li>
                      <li>
                        <strong>設備稼働率</strong>
                        <code>所要H ÷ (設備数 × 暦日 × 24H) × 100</code>
                        <span class="pr-load-help__note">検査除外</span>
                      </li>
                    </ul>
                  </div>
                </el-popover>
              </div>
              <div class="pr-load-cap-actions">
                <button
                  type="button"
                  class="pr-col-toggle pr-col-toggle--load"
                  :class="{ 'is-on': showLoadCapacityCols }"
                  @click="showLoadCapacityCols = !showLoadCapacityCols"
                >
                  <span class="pr-col-toggle__indicator" />
                  設備・能率・稼働日・定時H・所要H
                </button>
                <el-button size="small" round type="primary" plain @click="openLoadCapacityDialog('part02')">
                  <el-icon><Setting /></el-icon>
                  設備・能率・直・稼働日設定
                </el-button>
              </div>
              <p class="pr-load-summary-line">
                出荷対象日
                <strong>{{ payload.part02.load_plan.working_days }}</strong>
                日
                <span class="pr-inv-forecast-sep">|</span>
                内示
                <strong>{{ fmtNum(payload.part02.load_plan.forecast_th) }}</strong>
                千本
                <span class="pr-inv-forecast-sep">|</span>
                日当
                <strong>{{ fmtNum(payload.part02.load_plan.daily_forecast_th) }}</strong>
                千本
              </p>
            </div>

            <div class="pr-kpi-grid pr-kpi-grid--load">
              <div
                class="pr-kpi"
                :class="part02LoadMeta.bottleneckRate >= 100 ? 'pr-kpi--red' : part02LoadMeta.bottleneckRate >= 90 ? 'pr-kpi--orange' : 'pr-kpi--blue'"
              >
                <span class="pr-kpi__label">ボトルネック</span>
                <strong class="pr-kpi__value pr-kpi__value--name">{{ part02LoadMeta.bottleneckName }}</strong>
                <span class="pr-kpi__hint">負荷率 {{ part02LoadMeta.bottleneckRate }}%</span>
              </div>
              <div class="pr-kpi pr-kpi--indigo">
                <span class="pr-kpi__label">平均負荷率</span>
                <strong class="pr-kpi__value">{{ part02LoadMeta.avgRate }}<small>%</small></strong>
                <span class="pr-kpi__hint">全工程平均</span>
              </div>
              <div class="pr-kpi" :class="part02LoadMeta.maxRate >= 100 ? 'pr-kpi--red' : part02LoadMeta.maxRate >= 90 ? 'pr-kpi--orange' : 'pr-kpi--green'">
                <span class="pr-kpi__label">最高負荷率</span>
                <strong class="pr-kpi__value">{{ part02LoadMeta.maxRate }}<small>%</small></strong>
                <span class="pr-kpi__hint">{{ part02LoadMeta.maxRate >= 100 ? '要対策' : part02LoadMeta.maxRate >= 90 ? '逼迫' : '適正' }}</span>
              </div>
              <div class="pr-kpi" :class="part02LoadMeta.overload > 0 ? 'pr-kpi--red' : 'pr-kpi--slate'">
                <span class="pr-kpi__label">100%超</span>
                <strong class="pr-kpi__value">{{ part02LoadMeta.overload }}<small>工程</small></strong>
                <span class="pr-kpi__hint">{{ part02LoadMeta.overload ? '残業を検討' : '該当なし' }}</span>
              </div>
              <div class="pr-kpi" :class="part02LoadMeta.tight > 0 ? 'pr-kpi--orange' : 'pr-kpi--blue'">
                <span class="pr-kpi__label">90%以上</span>
                <strong class="pr-kpi__value">{{ part02LoadMeta.tight }}<small>工程</small></strong>
                <span class="pr-kpi__hint">逼迫ライン</span>
              </div>
            </div>

            <div class="pr-table-wrap pr-table-wrap--performance">
              <el-table
                :key="`load-plan-${showLoadCapacityCols}`"
                :data="payload.part02.load_plan.rows"
                border
                size="small"
                class="pr-table pr-table--modern pr-table--performance pr-table--load"
                stripe
                :row-class-name="loadRowClassName"
              >
                <el-table-column prop="process_name" label="工程名" min-width="96" fixed />
                <el-table-column label="計画(千本)" min-width="96" align="center">
                  <template #default="{ row }">
                    <input
                      v-if="isLoadPlanEditing(row.process_cd, 'part02')"
                      class="pr-perf-edit-input pr-load-plan-edit-input"
                      type="number"
                      step="0.1"
                      v-model.number="loadPlanEditDraft"
                      @blur="commitLoadPlanEdit"
                      @keydown.enter.prevent="commitLoadPlanEdit"
                      @keydown.esc.prevent="cancelLoadPlanEdit"
                      @click.stop
                    />
                    <span
                      v-else
                      class="pr-perf-val pr-perf-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startLoadPlanEdit(row, 'part02')"
                    >{{ fmtNum(row.plan_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="日当(千本)" min-width="96" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-val">{{ fmtNum(row.daily_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="直" min-width="64" align="center">
                  <template #default="{ row }">
                    <span
                      class="pr-shift-badge"
                      :class="shiftBadgeClass(row.shift_label)"
                    >{{ row.shift_label || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="負荷率" min-width="92" align="center">
                  <template #default="{ row }">
                    <span :class="loadRateClass(row.load_rate_pct)">{{ row.load_rate_pct }}%</span>
                  </template>
                </el-table-column>
                <el-table-column label="設備稼働率" min-width="96" align="center">
                  <template #default="{ row }">
                    <span
                      v-if="row.process_cd !== 'inspection' && row.equipment_utilization_pct != null"
                      class="pr-perf-val pr-perf-val--util"
                    >{{ row.equipment_utilization_pct }}%</span>
                    <span v-else class="pr-perf-val pr-perf-val--muted">—</span>
                  </template>
                </el-table-column>
                <el-table-column label="日均H" min-width="80" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-val">{{ row.daily_operation_hours }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="設備" min-width="100" align="center">
                  <template #default="{ row }">
                    <span class="pr-load-cap-val">{{ row.equipment_label || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="能率(本/H)" min-width="88" align="center">
                  <template #default="{ row }">
                    <span class="pr-load-cap-val pr-load-cap-val--num">{{ row.standard_rate || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="稼働日" min-width="72" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-val">{{ row.working_days }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="定時H" min-width="72" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-reg">{{ row.regular_hours }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="所要H" min-width="72" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-prod">{{ row.required_hours }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="pr-perf-comment">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><ChatDotRound /></el-icon>
                  </span>
                  <div>
                    <strong>計画コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button round :loading="commentRegenLoading === 'load_plan_part02'" @click="regenerateSectionComments('load_plan', 'part02')">
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="primary" round @click="openCommentDialog('load_plan', 'part02')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>
              <div v-if="part02LoadCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in part02LoadCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>

          <section class="pr-card pr-card--teal pr-card--inventory">
            <div class="pr-card__head pr-card__head--inventory">
              <div class="pr-inv-title">
                <h2>{{ payload.part02.inventory_forecast.inventory_month_label }} 在庫予測</h2>
              </div>
              <p class="pr-inv-forecast-line">
                {{ payload.part02.inventory_forecast.prev_forecast_label }}出荷内示
                <strong>{{ fmtNum(payload.part02.inventory_forecast.prev_forecast_th) }}</strong>
                千本
                <span class="pr-inv-forecast-sep">|</span>
                {{ payload.part02.inventory_forecast.curr_forecast_label }}出荷内示
                <strong>{{ fmtNum(payload.part02.inventory_forecast.curr_forecast_th) }}</strong>
                千本
              </p>
            </div>

            <div class="pr-table-wrap pr-table-wrap--performance pr-table-wrap--inventory">
              <el-table
                :data="payload.part02.inventory_forecast.rows"
                border
                row-key="key"
                :tree-props="{ children: 'children' }"
                class="pr-table pr-table--modern pr-table--performance pr-table--inventory"
                stripe
                :row-class-name="inventoryRowClassName"
              >
                <el-table-column label="工程名" min-width="130" fixed>
                  <template #default="{ row }">
                    <div class="pr-inv-name-cell">
                      <span class="pr-inv-name-cell__name">{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column min-width="120" align="center" class-name="col-prev">
                  <template #header>
                    <span
                      class="pr-inv-col-hdr pr-inv-col-hdr--clickable"
                      title="ダブルクリックで在庫基準日を選択"
                      @dblclick.stop="openFcPrevInvDateDialog('part02')"
                    >
                      {{ fcPrevInventoryHeaderLabel }}
                    </span>
                  </template>
                  <template #default="{ row }">
                    <span class="pr-inv-val pr-inv-val--prev">{{ fmtNum(row.prev_inventory_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="前月在庫日数" min-width="100" align="center" class-name="col-prev">
                  <template #default="{ row }">
                    <span
                      class="pr-inv-days pr-inv-days--prev"
                      :class="inventoryMetricClass(row, row.prev_days, 'days')"
                    >{{ fmtDays(row.prev_days) }}<small>日</small></span>
                  </template>
                </el-table-column>
                <el-table-column label="予測在庫(千本)" min-width="130" align="center" class-name="col-curr">
                  <template #default="{ row }">
                    <input
                      v-if="isForecastInvEditable(row) && isFcInvEditing(row.key, 'part02')"
                      class="pr-inv-edit-input pr-inv-edit-input--curr pr-inv-edit-input--fc"
                      type="number"
                      step="0.1"
                      v-model.number="fcInvEditDraft"
                      @blur="commitFcInvEdit"
                      @keydown.enter.prevent="commitFcInvEdit"
                      @keydown.esc.prevent="cancelFcInvEdit"
                      @click.stop
                    />
                    <span
                      v-else-if="isForecastInvEditable(row)"
                      class="pr-inv-val pr-inv-val--curr pr-inv-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startFcInvEdit(row, 'part02')"
                    >{{ fmtNum(row.curr_inventory_th) }}</span>
                    <span v-else class="pr-inv-val pr-inv-val--curr pr-inv-val--parent">{{ fmtNum(row.curr_inventory_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="当月在庫日数" min-width="100" align="center" class-name="col-curr">
                  <template #default="{ row }">
                    <span
                      class="pr-inv-days"
                      :class="inventoryMetricClass(row, row.curr_days, 'days')"
                    >{{ fmtDays(row.curr_days) }}<small>日</small></span>
                  </template>
                </el-table-column>
                <el-table-column label="増減(千本)" min-width="110" align="center">
                  <template #default="{ row }">
                    <span :class="deltaClass(row.delta_th)">{{ fmtDelta(row.delta_th) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="pr-perf-comment pr-perf-comment--inventory">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><Box /></el-icon>
                  </span>
                  <div>
                    <strong>在庫予測コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button round :loading="commentRegenLoading === 'inventory_forecast_part02'" @click="regenerateSectionComments('inventory_forecast', 'part02')">
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="success" round class="pr-inv-comment-btn" @click="openCommentDialog('inventory_forecast', 'part02')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>
              <div v-if="inventoryForecastCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in inventoryForecastCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane name="part03">
          <template #label>
            <span class="pr-tab-label pr-tab-label--blue">03 {{ payload.part03.load_plan.month_label }} 生産計画・負荷率</span>
          </template>

          <section class="pr-card pr-card--blue pr-card--performance pr-card--load-plan">
            <div class="pr-card__head pr-card__head--performance">
              <div class="pr-load-title">
                <h2>{{ payload.part03.load_plan.month_label }} 生産計画・負荷率</h2>
                <el-popover
                  placement="bottom-start"
                  :width="480"
                  trigger="click"
                  popper-class="pr-load-help-popper"
                >
                  <template #reference>
                    <button type="button" class="pr-load-help-btn" title="負荷率の見方・計算式">
                      <el-icon :size="18"><QuestionFilled /></el-icon>
                    </button>
                  </template>
                  <div class="pr-load-help">
                    <h4>負荷率の見方</h4>
                    <div class="pr-load-help__legend">
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--overload">100%超</span>
                        要対策
                      </span>
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--tight">90%以上</span>
                        逼迫
                      </span>
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--ok">60〜90%</span>
                        適正
                      </span>
                      <span class="pr-load-help__item">
                        <span class="pr-load-formula__tag pr-load-formula__tag--light">60%以下</span>
                        余裕
                      </span>
                    </div>
                    <h4>計算式</h4>
                    <ul>
                      <li>
                        <strong>負荷率</strong>
                        <code>所要H ÷ 定時H × 100</code>
                      </li>
                      <li>
                        <strong>定時H</strong>
                        <code>設備数 × 直数 × 7.6H × 稼働日 × 稼働率</code>
                        <span class="pr-load-help__note">人員は 人数 × 7.6H × 稼働日 × 稼働率</span>
                      </li>
                      <li>
                        <strong>計画(千本)</strong>
                        <code>元計画 × 計画調整率% ÷ 100</code>
                      </li>
                      <li>
                        <strong>所要H</strong>
                        <code>計画(本) ÷ 能率(本/H)</code>
                      </li>
                      <li>
                        <strong>日均H</strong>
                        <code>所要H ÷ 稼働日 ÷ 設備数</code>
                      </li>
                      <li>
                        <strong>設備稼働率</strong>
                        <code>所要H ÷ (設備数 × 暦日 × 24H) × 100</code>
                        <span class="pr-load-help__note">検査除外</span>
                      </li>
                    </ul>
                  </div>
                </el-popover>
              </div>
              <div class="pr-load-cap-actions">
                <button
                  type="button"
                  class="pr-col-toggle pr-col-toggle--load"
                  :class="{ 'is-on': showLoadCapacityCols }"
                  @click="showLoadCapacityCols = !showLoadCapacityCols"
                >
                  <span class="pr-col-toggle__indicator" />
                  設備・能率・稼働日・定時H・所要H
                </button>
                <el-button size="small" round type="primary" plain @click="openLoadCapacityDialog('part03')">
                  <el-icon><Setting /></el-icon>
                  設備・能率・直・稼働日設定
                </el-button>
              </div>
              <p class="pr-load-summary-line">
                月次稼働日
                <strong>{{ payload.part03.load_plan.working_days }}</strong>
                日
                <span class="pr-inv-forecast-sep">|</span>
                内示
                <strong>{{ fmtNum(payload.part03.load_plan.forecast_th) }}</strong>
                千本
                <span class="pr-inv-forecast-sep">|</span>
                日当
                <strong>{{ fmtNum(payload.part03.load_plan.daily_forecast_th) }}</strong>
                千本
              </p>
            </div>

            <div class="pr-kpi-grid pr-kpi-grid--load">
              <div
                class="pr-kpi"
                :class="part03LoadMeta.bottleneckRate >= 100 ? 'pr-kpi--red' : part03LoadMeta.bottleneckRate >= 90 ? 'pr-kpi--orange' : 'pr-kpi--blue'"
              >
                <span class="pr-kpi__label">ボトルネック</span>
                <strong class="pr-kpi__value pr-kpi__value--name">{{ part03LoadMeta.bottleneckName }}</strong>
                <span class="pr-kpi__hint">負荷率 {{ part03LoadMeta.bottleneckRate }}%</span>
              </div>
              <div class="pr-kpi pr-kpi--indigo">
                <span class="pr-kpi__label">平均負荷率</span>
                <strong class="pr-kpi__value">{{ part03LoadMeta.avgRate }}<small>%</small></strong>
                <span class="pr-kpi__hint">全工程平均</span>
              </div>
              <div class="pr-kpi" :class="part03LoadMeta.maxRate >= 100 ? 'pr-kpi--red' : part03LoadMeta.maxRate >= 90 ? 'pr-kpi--orange' : 'pr-kpi--green'">
                <span class="pr-kpi__label">最高負荷率</span>
                <strong class="pr-kpi__value">{{ part03LoadMeta.maxRate }}<small>%</small></strong>
                <span class="pr-kpi__hint">{{ part03LoadMeta.maxRate >= 100 ? '要対策' : part03LoadMeta.maxRate >= 90 ? '逼迫' : '適正' }}</span>
              </div>
              <div class="pr-kpi" :class="part03LoadMeta.overload > 0 ? 'pr-kpi--red' : 'pr-kpi--slate'">
                <span class="pr-kpi__label">100%超</span>
                <strong class="pr-kpi__value">{{ part03LoadMeta.overload }}<small>工程</small></strong>
                <span class="pr-kpi__hint">{{ part03LoadMeta.overload ? '残業・外注等を検討' : '該当なし' }}</span>
              </div>
              <div class="pr-kpi" :class="part03LoadMeta.tight > 0 ? 'pr-kpi--orange' : 'pr-kpi--blue'">
                <span class="pr-kpi__label">90%以上</span>
                <strong class="pr-kpi__value">{{ part03LoadMeta.tight }}<small>工程</small></strong>
                <span class="pr-kpi__hint">逼迫ライン</span>
              </div>
            </div>

            <div class="pr-table-wrap pr-table-wrap--performance">
              <el-table
                :key="`load-plan-${showLoadCapacityCols}`"
                :data="payload.part03.load_plan.rows"
                border
                size="small"
                class="pr-table pr-table--modern pr-table--performance pr-table--load"
                stripe
                :row-class-name="loadRowClassName"
              >
                <el-table-column prop="process_name" label="工程名" min-width="96" fixed />
                <el-table-column label="計画(千本)" min-width="96" align="center">
                  <template #default="{ row }">
                    <input
                      v-if="isLoadPlanEditing(row.process_cd, 'part03')"
                      class="pr-perf-edit-input pr-load-plan-edit-input"
                      type="number"
                      step="0.1"
                      v-model.number="loadPlanEditDraft"
                      @blur="commitLoadPlanEdit"
                      @keydown.enter.prevent="commitLoadPlanEdit"
                      @keydown.esc.prevent="cancelLoadPlanEdit"
                      @click.stop
                    />
                    <span
                      v-else
                      class="pr-perf-val pr-perf-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startLoadPlanEdit(row, 'part03')"
                    >{{ fmtNum(row.plan_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="日当(千本)" min-width="96" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-val">{{ fmtNum(row.daily_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="直" min-width="64" align="center">
                  <template #default="{ row }">
                    <span
                      class="pr-shift-badge"
                      :class="shiftBadgeClass(row.shift_label)"
                    >{{ row.shift_label || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="負荷率" min-width="92" align="center">
                  <template #default="{ row }">
                    <span :class="loadRateClass(row.load_rate_pct)">{{ row.load_rate_pct }}%</span>
                  </template>
                </el-table-column>
                <el-table-column label="設備稼働率" min-width="96" align="center">
                  <template #default="{ row }">
                    <span
                      v-if="row.process_cd !== 'inspection' && row.equipment_utilization_pct != null"
                      class="pr-perf-val pr-perf-val--util"
                    >{{ row.equipment_utilization_pct }}%</span>
                    <span v-else class="pr-perf-val pr-perf-val--muted">—</span>
                  </template>
                </el-table-column>
                <el-table-column label="日均H" min-width="80" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-val">{{ row.daily_operation_hours }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="設備" min-width="100" align="center">
                  <template #default="{ row }">
                    <span class="pr-load-cap-val">{{ row.equipment_label || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="能率(本/H)" min-width="88" align="center">
                  <template #default="{ row }">
                    <span class="pr-load-cap-val pr-load-cap-val--num">{{ row.standard_rate || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="稼働日" min-width="72" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-val">{{ row.working_days }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="定時H" min-width="72" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-reg">{{ row.regular_hours }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="showLoadCapacityCols" label="所要H" min-width="72" align="center">
                  <template #default="{ row }">
                    <span class="pr-perf-prod">{{ row.required_hours }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="pr-perf-comment">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><ChatDotRound /></el-icon>
                  </span>
                  <div>
                    <strong>計画コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button round :loading="commentRegenLoading === 'load_plan_part03'" @click="regenerateSectionComments('load_plan', 'part03')">
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="primary" round @click="openCommentDialog('load_plan', 'part03')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>
              <div v-if="part03LoadCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in part03LoadCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>

          <section v-if="payload.part03.inventory_forecast" class="pr-card pr-card--teal pr-card--inventory">
            <div class="pr-card__head pr-card__head--inventory">
              <div class="pr-inv-title">
                <h2>{{ payload.part03.inventory_forecast.inventory_month_label }} 在庫予測</h2>
              </div>
              <p class="pr-inv-forecast-line">
                {{ payload.part03.inventory_forecast.prev_forecast_label }}出荷内示
                <strong>{{ fmtNum(payload.part03.inventory_forecast.prev_forecast_th) }}</strong>
                千本
                <span class="pr-inv-forecast-sep">|</span>
                {{ payload.part03.inventory_forecast.curr_forecast_label }}出荷内示
                <strong>{{ fmtNum(payload.part03.inventory_forecast.curr_forecast_th) }}</strong>
                千本
              </p>
            </div>

            <div class="pr-table-wrap pr-table-wrap--performance pr-table-wrap--inventory">
              <el-table
                :data="payload.part03.inventory_forecast.rows"
                border
                row-key="key"
                :tree-props="{ children: 'children' }"
                class="pr-table pr-table--modern pr-table--performance pr-table--inventory"
                stripe
                :row-class-name="inventoryRowClassName"
              >
                <el-table-column label="工程名" min-width="130" fixed>
                  <template #default="{ row }">
                    <div class="pr-inv-name-cell">
                      <span class="pr-inv-name-cell__name">{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column min-width="120" align="center" class-name="col-prev">
                  <template #header>
                    <span
                      class="pr-inv-col-hdr"
                      title="前月の在庫予測「予測在庫(千本)」を転記"
                    >
                      {{ fcPrevInventoryHeaderLabelPart03 }}
                    </span>
                  </template>
                  <template #default="{ row }">
                    <span class="pr-inv-val pr-inv-val--prev">{{ fmtNum(row.prev_inventory_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="前月在庫日数" min-width="100" align="center" class-name="col-prev">
                  <template #default="{ row }">
                    <span
                      class="pr-inv-days pr-inv-days--prev"
                      :class="inventoryMetricClass(row, row.prev_days, 'days')"
                    >{{ fmtDays(row.prev_days) }}<small>日</small></span>
                  </template>
                </el-table-column>
                <el-table-column label="予測在庫(千本)" min-width="130" align="center" class-name="col-curr">
                  <template #default="{ row }">
                    <input
                      v-if="isForecastInvEditable(row) && isFcInvEditing(row.key, 'part03')"
                      class="pr-inv-edit-input pr-inv-edit-input--curr pr-inv-edit-input--fc"
                      type="number"
                      step="0.1"
                      v-model.number="fcInvEditDraft"
                      @blur="commitFcInvEdit"
                      @keydown.enter.prevent="commitFcInvEdit"
                      @keydown.esc.prevent="cancelFcInvEdit"
                      @click.stop
                    />
                    <span
                      v-else-if="isForecastInvEditable(row)"
                      class="pr-inv-val pr-inv-val--curr pr-inv-val--editable"
                      title="ダブルクリックで編集"
                      @dblclick.stop="startFcInvEdit(row, 'part03')"
                    >{{ fmtNum(row.curr_inventory_th) }}</span>
                    <span v-else class="pr-inv-val pr-inv-val--curr pr-inv-val--parent">{{ fmtNum(row.curr_inventory_th) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="当月在庫日数" min-width="100" align="center" class-name="col-curr">
                  <template #default="{ row }">
                    <span
                      class="pr-inv-days"
                      :class="inventoryMetricClass(row, row.curr_days, 'days')"
                    >{{ fmtDays(row.curr_days) }}<small>日</small></span>
                  </template>
                </el-table-column>
                <el-table-column label="増減(千本)" min-width="110" align="center">
                  <template #default="{ row }">
                    <span :class="deltaClass(row.delta_th)">{{ fmtDelta(row.delta_th) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="pr-perf-comment pr-perf-comment--inventory">
              <div class="pr-perf-comment__head">
                <div class="pr-perf-comment__title">
                  <span class="pr-perf-comment__icon" aria-hidden="true">
                    <el-icon :size="22"><Box /></el-icon>
                  </span>
                  <div>
                    <strong>在庫予測コメント</strong>
                  </div>
                </div>
                <div class="pr-perf-comment__actions">
                  <el-button round :loading="commentRegenLoading === 'inventory_forecast_part03'" @click="regenerateSectionComments('inventory_forecast', 'part03')">
                    <el-icon><Refresh /></el-icon>
                    自動再生成
                  </el-button>
                  <el-button type="success" round class="pr-inv-comment-btn" @click="openCommentDialog('inventory_forecast', 'part03')">
                    <el-icon><EditPen /></el-icon>
                    コメント編集
                  </el-button>
                </div>
              </div>
              <div v-if="part03InventoryForecastCommentsDisplay.length" class="pr-perf-comment__body">
                <div
                  v-for="(line, i) in part03InventoryForecastCommentsDisplay"
                  :key="i"
                  class="pr-perf-comment__line"
                  :style="{ animationDelay: `${i * 0.05}s` }"
                >
                  <span class="pr-perf-comment__bullet">■</span>
                  <p class="pr-perf-comment__text">
                    <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                      <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                      <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                      <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                    </template>
                  </p>
                </div>
              </div>
              <div v-else class="pr-perf-comment__empty">
                <el-icon><EditPen /></el-icon>
                <p>コメント未入力</p>
                <span>「再計算」で自動生成されます。その後「コメント編集」で修正できます</span>
              </div>
            </div>
          </section>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog
      v-model="effTrendVisible"
      width="920px"
      class="pr-dialog pr-dialog--eff-trend"
      :show-close="false"
      destroy-on-close
      align-center
      @closed="onEffTrendClosed"
    >
      <template #header>
        <div class="pr-eff-header">
          <div class="pr-eff-header__main">
            <span class="pr-eff-header__icon" aria-hidden="true">
              <el-icon :size="18"><TrendCharts /></el-icon>
            </span>
            <div class="pr-eff-header__text">
              <h3 class="pr-eff-header__title">時間当たり能率推移</h3>
              <p class="pr-eff-header__sub">工程別・月次（本/時・個/時） · 実績なし月は除外相当で —</p>
            </div>
          </div>
          <button type="button" class="pr-eff-header__close" aria-label="閉じる" @click="effTrendVisible = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>
      </template>

      <div class="pr-eff-body" v-loading="effTrendLoading">
        <div class="pr-eff-filters">
          <div class="pr-eff-filters__range">
            <span class="pr-eff-filters__label">期間</span>
            <el-date-picker
              v-model="effTrendStart"
              type="month"
              value-format="YYYY-MM"
              format="YYYY年M月"
              size="small"
              class="pr-eff-month"
              :clearable="false"
            />
            <span class="pr-eff-filters__tilde">〜</span>
            <el-date-picker
              v-model="effTrendEnd"
              type="month"
              value-format="YYYY-MM"
              format="YYYY年M月"
              size="small"
              class="pr-eff-month"
              :clearable="false"
            />
            <el-button size="small" type="primary" round :loading="effTrendLoading" @click="loadEfficiencyTrend">
              表示更新
            </el-button>
          </div>
          <div class="pr-eff-filters__procs">
            <button
              v-for="p in EFF_TREND_PROCESSES"
              :key="p.cd"
              type="button"
              class="pr-eff-proc-chip"
                  :class="[`pr-eff-proc-chip--${p.cd}`, { 'is-on': effTrendSelectedSet.has(p.cd) }]"
              @click="toggleEffTrendProcess(p.cd)"
            >
              <i class="pr-eff-proc-chip__dot" />
              {{ p.name }}
            </button>
          </div>
        </div>

        <div class="pr-eff-chart-card">
          <div class="pr-eff-chart-card__meta">
            <span>{{ effTrendMetaLabel }}</span>
            <span class="pr-eff-chart-card__hint">クリックで工程の表示切替</span>
          </div>
          <div ref="effTrendChartRef" class="pr-eff-chart" />
          <el-empty
            v-if="!effTrendLoading && !effTrendData?.series?.length"
            description="表示データがありません"
            :image-size="72"
          />
        </div>

        <div v-if="effTrendLatestCards.length" class="pr-eff-latest">
          <div
            v-for="card in effTrendLatestCards"
            :key="card.cd"
            class="pr-eff-latest__card"
            :class="`pr-eff-latest__card--${card.cd}`"
          >
            <span class="pr-eff-latest__name">{{ card.name }}</span>
            <strong class="pr-eff-latest__val">
              {{ card.value == null ? '—' : card.value }}
              <small v-if="card.value != null">本/時</small>
            </strong>
            <span class="pr-eff-latest__month">{{ card.monthLabel }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="capacityVisible" title="工程能力パラメータ" width="880px" class="pr-dialog">
      <el-table :data="capacityRows" border size="small">
        <el-table-column prop="process_name" label="工程" width="90" />
        <el-table-column label="設備・人員" min-width="140">
          <template #default="{ row }">
            <el-input v-model="row.equipment_label" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="標準能率(本/H)" width="120">
          <template #default="{ row }">
            <el-input-number v-model="row.standard_rate" :controls="false" size="small" class="pr-num" />
          </template>
        </el-table-column>
        <el-table-column label="稼働直" width="80">
          <template #default="{ row }">
            <el-input v-model="row.shift_label" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="稼働率%" width="90">
          <template #default="{ row }">
            <el-input-number
              v-model="row.utilization_rate_pct"
              :controls="false"
              :min="0.01"
              :max="100"
              :precision="2"
              size="small"
              class="pr-num"
            />
          </template>
        </el-table-column>
        <el-table-column label="計画調整率%" width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.plan_adjust_rate_pct"
              :controls="false"
              :min="0"
              :max="999.99"
              :precision="2"
              size="small"
              class="pr-num"
            />
          </template>
        </el-table-column>
        <el-table-column label="日定時H" width="90">
          <template #default="{ row }">
            <el-input-number v-model="row.daily_regular_hours" :controls="false" size="small" class="pr-num" />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="capacityVisible = false">閉じる</el-button>
        <el-button type="primary" :loading="capacitySaving" @click="saveCapacity">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="loadCapacityVisible"
      width="920px"
      class="pr-dialog pr-dialog--load-cap"
      :show-close="false"
      destroy-on-close
      align-center
    >
      <template #header>
        <div class="pr-lcap-header">
          <div class="pr-lcap-header__main">
            <span class="pr-lcap-header__icon" aria-hidden="true">
              <el-icon :size="18"><Setting /></el-icon>
            </span>
            <div class="pr-lcap-header__text">
              <h3 class="pr-lcap-header__title">設備・能率・直・稼働日設定</h3>
              <p class="pr-lcap-header__sub">
                <span class="pr-lcap-header__month">{{ loadCapacityMonthLabel }}</span>
                工程別パラメータ
                <span v-if="loadCapacitySource === 'default'" class="pr-lcap-header__badge">デフォルトから編集</span>
                <span v-else-if="loadCapacitySource === 'monthly'" class="pr-lcap-header__badge pr-lcap-header__badge--saved">月別保存済</span>
                <span v-if="loadCapacityMonthWd" class="pr-lcap-header__badge">月次参考 {{ loadCapacityMonthWd }}日</span>
              </p>
            </div>
          </div>
          <button type="button" class="pr-lcap-header__close" aria-label="閉じる" @click="loadCapacityVisible = false">
            <el-icon :size="16"><Close /></el-icon>
          </button>
        </div>
      </template>

      <div class="pr-lcap-body">
        <div class="pr-lcap-legend">
          <span class="pr-lcap-legend__chip pr-lcap-legend__chip--equip">設備・人員</span>
          <span class="pr-lcap-legend__chip pr-lcap-legend__chip--rate">能率 本/H</span>
          <span class="pr-lcap-legend__chip pr-lcap-legend__chip--shift">稼働直</span>
          <span class="pr-lcap-legend__chip pr-lcap-legend__chip--wd">稼働日</span>
          <span class="pr-lcap-legend__chip pr-lcap-legend__chip--util">稼働率 %</span>
          <span class="pr-lcap-legend__chip pr-lcap-legend__chip--adj">計画調整率 %</span>
        </div>

        <div class="pr-lcap-formula">
          <span>定時H = 設備×直×7.6×稼働日×稼働率／人員=人数×7.6×稼働日×稼働率</span>
          <span class="pr-lcap-formula__dot">·</span>
          <span>計画(千本) = 元計画 × 計画調整率%</span>
          <span class="pr-lcap-formula__dot">·</span>
          <span>所要H = 計画÷能率</span>
          <span class="pr-lcap-formula__dot">·</span>
          <span>日均H = 所要H÷稼働日÷設備</span>
        </div>

        <div class="pr-lcap-list">
          <div
            v-for="row in loadCapacityRows"
            :key="row.process_cd"
            class="pr-lcap-card"
            :class="loadCapacityCardClass(row.process_cd)"
          >
            <div class="pr-lcap-card__proc">
              <span class="pr-lcap-card__dot" />
              {{ row.process_name }}
            </div>
            <div class="pr-lcap-card__grid">
              <label class="pr-lcap-field">
                <span class="pr-lcap-field__label">設備</span>
                <el-input v-model="row.equipment_label" size="small" placeholder="5.5台" />
              </label>
              <label class="pr-lcap-field">
                <span class="pr-lcap-field__label">能率</span>
                <el-input-number
                  v-model="row.standard_rate"
                  :controls="false"
                  :min="0"
                  size="small"
                  class="pr-lcap-field__num"
                />
              </label>
              <label class="pr-lcap-field">
                <span class="pr-lcap-field__label">直</span>
                <el-input v-model="row.shift_label" size="small" placeholder="2直" />
              </label>
              <label class="pr-lcap-field">
                <span class="pr-lcap-field__label">稼働日</span>
                <el-input-number
                  v-model="row.working_days"
                  :controls="false"
                  :min="0"
                  :max="31"
                  size="small"
                  class="pr-lcap-field__num"
                />
              </label>
              <label class="pr-lcap-field">
                <span class="pr-lcap-field__label">稼働率%</span>
                <el-input-number
                  v-model="row.utilization_rate_pct"
                  :controls="false"
                  :min="0.01"
                  :max="100"
                  :precision="2"
                  size="small"
                  class="pr-lcap-field__num"
                />
              </label>
              <label class="pr-lcap-field">
                <span class="pr-lcap-field__label">計画調整率%</span>
                <el-input-number
                  v-model="row.plan_adjust_rate_pct"
                  :controls="false"
                  :min="0"
                  :max="999.99"
                  :precision="2"
                  size="small"
                  class="pr-lcap-field__num"
                />
              </label>
            </div>
          </div>
        </div>

        <p class="pr-lcap-tip">
          <el-icon :size="13"><QuestionFilled /></el-icon>
          稼働日 0 = 対象月カレンダー。計画調整率は計画(千本)=元計画×調整率%（未設定時は100%）。保存後に再計算します。
        </p>
      </div>

      <template #footer>
        <div class="pr-lcap-footer">
          <el-button size="default" round @click="loadCapacityVisible = false">キャンセル</el-button>
          <el-button type="primary" round :loading="loadCapacitySaving" @click="saveLoadCapacity">
            <el-icon v-if="!loadCapacitySaving"><CircleCheck /></el-icon>
            保存して再計算
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="wdDialogVisible" title="月次稼働日設定" width="720px" class="pr-dialog">
      <div class="pr-wd-dialog__toolbar">
        <span>対象年</span>
        <el-input-number v-model="wdDialogYear" :controls="true" :min="2020" :max="2099" @change="loadWorkingDaysYear" />
        <span class="pr-wd-dialog__hint">DB未登録月はカレンダー推計値です。保存すると budget_working_days に記録されます。</span>
      </div>
      <div class="pr-wd-dialog__grid">
        <label v-for="row in wdDialogRows" :key="`${row.year}-${row.month}`" class="pr-wd-dialog__cell">
          <span>{{ row.month }}月</span>
          <input v-model.number="row.working_days" type="number" min="0" max="31" step="1" class="pr-inv-wd__input" />
          <small :class="row.source === 'saved' ? 'is-saved' : 'is-est'">{{ row.source === 'saved' ? '登録済' : '推計' }}</small>
        </label>
      </div>
      <template #footer>
        <el-button @click="wdDialogVisible = false">閉じる</el-button>
        <el-button type="primary" :loading="wdSaving" @click="saveWorkingDaysDialog">保存して再計算</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="currInvDateDialogVisible"
      title="当月在庫の基準日"
      width="420px"
      class="pr-dialog"
      destroy-on-close
    >
      <p class="pr-inv-date-dialog__hint">選択した日付の在庫を「当月在庫」に反映します。</p>
      <el-date-picker
        v-model="currInvDateDraft"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="日付を選択"
        style="width: 100%"
      />
      <template #footer>
        <el-button @click="currInvDateDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="currInvDateLoading" @click="applyCurrInventoryByDate">反映</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="fcPrevInvDateDialogVisible"
      title="前月在庫の基準日"
      width="420px"
      class="pr-dialog"
      destroy-on-close
    >
      <p class="pr-inv-date-dialog__hint">選択した日付の在庫を「前月在庫」に反映します。</p>
      <el-date-picker
        v-model="fcPrevInvDateDraft"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="日付を選択"
        style="width: 100%"
      />
      <template #footer>
        <el-button @click="fcPrevInvDateDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="fcPrevInvDateLoading" @click="applyFcPrevInventoryByDate">反映</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="commentDialogVisible"
      width="760px"
      class="pr-comment-dialog"
      :class="{
        'pr-comment-dialog--scrap': commentDialogKind === 'scrap',
        'pr-comment-dialog--inventory': commentDialogKind === 'inventory' || commentDialogKind === 'inventory_forecast',
      }"
      destroy-on-close
      align-center
      :show-close="true"
    >
      <template #header>
        <div class="pr-comment-dialog__header">
          <div class="pr-comment-dialog__header-icon">
            <el-icon :size="20"><EditPen /></el-icon>
          </div>
          <div class="pr-comment-dialog__header-text">
            <h3>
              {{
                commentDialogKind === 'scrap'
                  ? '廃棄コメント編集'
                  : commentDialogKind === 'inventory'
                    ? '在庫コメント編集'
                    : commentDialogKind === 'inventory_forecast'
                      ? '在庫予測コメント編集'
                      : commentDialogKind === 'load_plan'
                        ? '計画コメント編集'
                        : '実績コメント編集'
              }}
            </h3>
            <p>1行が PPT の ■ 行 1 つに対応します</p>
          </div>
        </div>
      </template>

      <div class="pr-comment-dialog__layout">
        <section class="pr-comment-dialog__panel pr-comment-dialog__panel--edit">
          <div class="pr-comment-dialog__panel-head">
            <span class="pr-comment-dialog__panel-title">コメント入力</span>
            <span class="pr-comment-dialog__count">{{ commentDraft.length }} 行</span>
          </div>

          <div class="pr-comment-dialog__hint">
            <el-icon><Document /></el-icon>
            <span>
              数字は保存後に自動色分けされます：
              <span class="seg-num seg-num--pos">+12.5</span>
              <span class="seg-num seg-num--neg">△3</span>
            </span>
          </div>

          <div class="pr-comment-dialog__scroll">
            <div class="pr-comment-dialog__lines">
              <div v-for="(_, i) in commentDraft" :key="i" class="pr-comment-dialog__row">
                <div class="pr-comment-dialog__idx-wrap">
                  <span class="pr-comment-dialog__idx">{{ i + 1 }}</span>
                </div>
                <div class="pr-comment-dialog__input-wrap">
                  <el-input
                    v-model="commentDraft[i]"
                    type="textarea"
                    :autosize="{ minRows: 2, maxRows: 5 }"
                    class="pr-comment-dialog__input"
                    :placeholder="
                      commentDialogKind === 'scrap'
                        ? '例：廃棄率（旧）は前月比 △0.15pt、廃棄本数 +1,200'
                        : commentDialogKind === 'inventory' || commentDialogKind === 'inventory_forecast'
                          ? '例：仕掛品在庫は前月比 +12.5 千本'
                          : commentDialogKind === 'load_plan'
                            ? '例：切断は負荷率 105%、残業対応を検討'
                            : '例：切断は計画比 △12.5 千本、時間当たり能率 +3'
                    "
                  />
                </div>
                <button
                  type="button"
                  class="pr-comment-dialog__del"
                  :disabled="commentDraft.length <= 1"
                  title="行を削除"
                  @click="removeCommentDraftLine(i)"
                >
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
          </div>

          <button type="button" class="pr-comment-dialog__add" @click="addCommentDraftLine">
            <el-icon><Plus /></el-icon>
            <span>行を追加</span>
          </button>
        </section>

        <section class="pr-comment-dialog__panel pr-comment-dialog__panel--preview">
          <div class="pr-comment-dialog__panel-head">
            <span class="pr-comment-dialog__panel-title">プレビュー</span>
            <div class="pr-comment-dialog__legend">
              <span class="pr-comment-dialog__legend-item pr-comment-dialog__legend-item--pos">正数</span>
              <span class="pr-comment-dialog__legend-item pr-comment-dialog__legend-item--neg">負数</span>
              <span class="pr-comment-dialog__legend-item pr-comment-dialog__legend-item--text">文字</span>
            </div>
          </div>

          <div v-if="commentDraftPreview.length" class="pr-comment-dialog__preview">
            <div
              v-for="(line, i) in commentDraftPreview"
              :key="`preview-${i}`"
              class="pr-perf-comment__line pr-perf-comment__line--compact pr-comment-dialog__preview-line"
              :style="{ animationDelay: `${i * 0.04}s` }"
            >
              <span class="pr-perf-comment__bullet">■</span>
              <p class="pr-perf-comment__text">
                <template v-for="(seg, j) in parseCommentSegments(line)" :key="j">
                  <span v-if="seg.kind === 'text'" class="seg-text">{{ seg.text }}</span>
                  <span v-else-if="seg.kind === 'pos'" class="seg-num seg-num--pos">{{ seg.text }}</span>
                  <span v-else class="seg-num seg-num--neg">{{ seg.text }}</span>
                </template>
              </p>
            </div>
          </div>
          <div v-else class="pr-comment-dialog__preview-empty">
            <el-icon :size="28"><EditPen /></el-icon>
            <p>プレビュー待ち</p>
            <span>左側に入力すると、ここに表示されます</span>
          </div>
        </section>
      </div>

      <template #footer>
        <div class="pr-comment-dialog__footer">
          <el-button round size="large" @click="commentDialogVisible = false">キャンセル</el-button>
          <el-button
            :type="
              commentDialogKind === 'scrap'
                ? 'warning'
                : commentDialogKind === 'inventory' || commentDialogKind === 'inventory_forecast'
                  ? 'success'
                  : 'primary'
            "
            round
            size="large"
            @click="saveCommentDialog"
          >
            <el-icon><CircleCheck /></el-icon>
            保存して反映
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Close,
  Box,
  ChatDotRound,
  CircleCheck,
  Delete,
  Document,
  Download,
  EditPen,
  Plus,
  QuestionFilled,
  Refresh,
  Setting,
  TrendCharts,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  deleteMeeting,
  downloadMeetingPptx,
  downloadScrapPptx,
  fetchCapacity,
  fetchEfficiencyTrend,
  fetchMeeting,
  fetchSavedMonths,
  generateComments,
  recalculateMeeting,
  saveCapacity as saveCapacityApi,
  saveMeeting,
  saveWorkingDays,
  fetchWorkingDays,
  fetchInventoryByDate,
  type CapacityRow,
  type CommentGenerateKind,
  type EfficiencyTrendData,
  type InventoryRow,
  type InventorySection,
  type LoadPlanRow,
  type PerformanceRow,
  type ProductionReviewData,
  type ScrapMonthlyItem,
  type WorkingDaysMonthItem,
} from '@/api/erp/productionReview'

const CHART_THEME = {
  qtyTop: '#fdba74',
  qtyMid: '#f97316',
  qtyBot: '#c2410c',
  qtyCurrentTop: '#fb923c',
  qtyCurrentBot: '#9a3412',
  rateNew: '#7c3aed',
  rateNewSoft: '#a78bfa',
  rateOld: '#e11d48',
  rateOldSoft: '#fb7185',
  grid: 'rgba(148, 163, 184, 0.28)',
  text: '#64748b',
  axis: '#94a3b8',
}

const loading = ref(false)
const pptLoading = ref(false)
const scrapPptLoading = ref(false)
const deletingMonth = ref('')
const capacityVisible = ref(false)
const capacitySaving = ref(false)
const wdDialogVisible = ref(false)
const wdSaving = ref(false)
const wdDialogYear = ref(new Date().getFullYear())
const wdDialogRows = ref<WorkingDaysMonthItem[]>([])
const invWorkdayDraft = ref({ prev: 0, curr: 0 })
const activeTab = ref('part01')
const targetMonth = ref('')
const payload = ref<ProductionReviewData | null>(null)
const recordStatus = ref('')
const dataSource = ref<'saved' | 'computed' | ''>('')
const savedMonths = ref<{ target_month: string; status: string }[]>([])
const capacityRows = ref<CapacityRow[]>([])
const loadCapacityVisible = ref(false)
const loadCapacitySaving = ref(false)
const loadCapacityRows = ref<CapacityRow[]>([])
const loadCapacityMonth = ref('')
const loadCapacityPart = ref<'part02' | 'part03'>('part02')
const loadCapacitySource = ref<'monthly' | 'default' | ''>('')

const LOAD_CAPACITY_PROCESS_CDS = [
  'cutting',
  'chamfering',
  'molding',
  'plating',
  'inspection',
  'welding',
  'welding_sp',
] as const

const LOAD_CAPACITY_DEFAULT_NAMES: Record<string, string> = {
  cutting: '切断',
  chamfering: '面取',
  molding: '成型',
  plating: 'メッキ',
  inspection: '検査',
  welding: '溶接',
  welding_sp: '溶接SP',
}

const showForecastCols = ref(true)
const showActualCols = ref(true)
const showLoadCapacityCols = ref(true)
const commentDialogVisible = ref(false)
const commentDialogKind = ref<'performance' | 'scrap' | 'inventory' | 'load_plan' | 'inventory_forecast'>('performance')
const commentDialogPart = ref<'part02' | 'part03' | null>(null)
const commentRegenLoading = ref<string | null>(null)
const commentDraft = ref<string[]>([''])
const scrapRangeFrom = ref<string>('')
const scrapRangeTo = ref<string>('')
const scrapChartRef = ref<HTMLElement | null>(null)
let scrapChart: echarts.ECharts | null = null

const EFF_TREND_PROCESSES = [
  { cd: 'cutting', name: '切断', color: '#2563eb' },
  { cd: 'molding', name: '成型', color: '#7c3aed' },
  { cd: 'plating', name: 'メッキ', color: '#0891b2' },
  { cd: 'welding', name: '溶接', color: '#ea580c' },
  { cd: 'inspection', name: '検査', color: '#059669' },
] as const

const EFF_TREND_COLOR: Record<string, string> = Object.fromEntries(
  EFF_TREND_PROCESSES.map((p) => [p.cd, p.color]),
)

const effTrendVisible = ref(false)
const effTrendLoading = ref(false)
const effTrendStart = ref('')
const effTrendEnd = ref('')
const effTrendSelected = ref<string[]>(EFF_TREND_PROCESSES.map((p) => p.cd))
const effTrendData = ref<EfficiencyTrendData | null>(null)
const effTrendChartRef = ref<HTMLElement | null>(null)
let effTrendChart: echarts.ECharts | null = null

const effTrendSelectedSet = computed(() => new Set(effTrendSelected.value))

const effTrendMetaLabel = computed(() => {
  const d = effTrendData.value
  if (!d?.months?.length) return '期間を選択して表示更新'
  return `${d.month_labels[0] ?? d.start_month} 〜 ${d.month_labels[d.month_labels.length - 1] ?? d.end_month}`
})

const effTrendLatestCards = computed(() => {
  const d = effTrendData.value
  if (!d?.series?.length) return []
  const lastIdx = d.months.length - 1
  const monthLabel = d.month_labels[lastIdx] || d.months[lastIdx] || ''
  const selected = effTrendSelectedSet.value
  return d.series
    .filter((s) => selected.has(s.process_cd))
    .map((s) => ({
      cd: s.process_cd,
      name: s.process_name,
      value: s.values[lastIdx] ?? null,
      monthLabel,
    }))
})

function shiftYm(ym: string, delta: number): string {
  const [ys, ms] = ym.split('-')
  const y = Number(ys)
  const m = Number(ms)
  if (!y || !m) return ym
  const idx = y * 12 + (m - 1) + delta
  const ny = Math.floor(idx / 12)
  const nm = (idx % 12) + 1
  return `${ny}-${String(nm).padStart(2, '0')}`
}

function defaultEffTrendRange() {
  const perf = payload.value?.part01?.performance as { month?: string } | undefined
  const end =
    perf?.month && /^\d{4}-\d{2}$/.test(perf.month)
      ? perf.month
      : targetMonth.value
        ? shiftYm(targetMonth.value, -1)
        : ''
  if (!end) {
    const now = new Date()
    const cur = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    effTrendEnd.value = cur
    effTrendStart.value = shiftYm(cur, -11)
    return
  }
  effTrendEnd.value = end
  effTrendStart.value = shiftYm(end, -11)
}

function toggleEffTrendProcess(cd: string) {
  const cur = [...effTrendSelected.value]
  const idx = cur.indexOf(cd)
  if (idx >= 0) {
    if (cur.length <= 1) return
    cur.splice(idx, 1)
  } else {
    cur.push(cd)
  }
  effTrendSelected.value = cur
  renderEffTrendChart()
}

function disposeEffTrendChart() {
  effTrendChart?.dispose()
  effTrendChart = null
}

function onEffTrendClosed() {
  disposeEffTrendChart()
}

function renderEffTrendChart() {
  const el = effTrendChartRef.value
  const d = effTrendData.value
  if (!el || !d?.months?.length) {
    disposeEffTrendChart()
    return
  }
  if (!effTrendChart) {
    effTrendChart = echarts.init(el)
  }
  const selected = effTrendSelectedSet.value
  const series = d.series
    .filter((s) => selected.has(s.process_cd))
    .map((s) => ({
      name: s.process_name,
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      showSymbol: true,
      connectNulls: false,
      data: s.values.map((v) => (v == null ? null : Number(v))),
      label: {
        show: true,
        position: 'top' as const,
        distance: 6,
        fontSize: 11,
        fontWeight: 700 as const,
        color: EFF_TREND_COLOR[s.process_cd] || '#334155',
        formatter: (params: { value?: number | null }) =>
          params.value == null || Number.isNaN(Number(params.value)) ? '' : String(params.value),
      },
      lineStyle: { width: 3, color: EFF_TREND_COLOR[s.process_cd] || '#64748b' },
      itemStyle: {
        color: EFF_TREND_COLOR[s.process_cd] || '#64748b',
        borderWidth: 2,
        borderColor: '#fff',
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: `${EFF_TREND_COLOR[s.process_cd] || '#64748b'}33` },
          { offset: 1, color: `${EFF_TREND_COLOR[s.process_cd] || '#64748b'}05` },
        ]),
      },
      emphasis: {
        focus: 'series' as const,
        label: { show: true, fontSize: 12, fontWeight: 800 as const },
      },
    }))

  effTrendChart.setOption(
    {
      color: EFF_TREND_PROCESSES.map((p) => p.color),
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderWidth: 0,
        padding: [10, 14],
        textStyle: { color: '#f8fafc', fontSize: 12 },
        valueFormatter: (v: unknown) => (v == null || Number.isNaN(Number(v)) ? '—' : `${v} 本/時`),
      },
      legend: {
        top: 4,
        right: 8,
        icon: 'roundRect',
        itemWidth: 12,
        itemHeight: 8,
        textStyle: { color: '#64748b', fontWeight: 700, fontSize: 11 },
      },
      grid: { left: 48, right: 24, top: 48, bottom: 36 },
      xAxis: {
        type: 'category',
        data: d.month_labels.map((lb, i) => lb.replace(/年/, '/').replace(/月/, '') || d.months[i]),
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisLabel: { color: '#64748b', fontWeight: 600, fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '本/時',
        nameTextStyle: { color: '#94a3b8', fontSize: 11, padding: [0, 0, 0, 8] },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)', type: 'dashed' } },
        axisLabel: { color: '#64748b', fontWeight: 600 },
      },
      series,
    },
    true,
  )
  effTrendChart.resize()
}

async function loadEfficiencyTrend() {
  if (!effTrendStart.value || !effTrendEnd.value) {
    ElMessage.warning('開始月と終了月を指定してください')
    return
  }
  if (effTrendStart.value > effTrendEnd.value) {
    ElMessage.warning('終了月は開始月以降を指定してください')
    return
  }
  effTrendLoading.value = true
  try {
    const res = await fetchEfficiencyTrend({
      start_month: effTrendStart.value,
      end_month: effTrendEnd.value,
    })
    effTrendData.value = res.data
    await nextTick()
    renderEffTrendChart()
  } catch {
    ElMessage.error('時間当たり能率推移の取得に失敗しました')
  } finally {
    effTrendLoading.value = false
  }
}

async function openEfficiencyTrendDialog() {
  defaultEffTrendRange()
  effTrendSelected.value = EFF_TREND_PROCESSES.map((p) => p.cd)
  effTrendVisible.value = true
  await nextTick()
  await loadEfficiencyTrend()
}

function scrapMonthKey(m: { year: number; month: number }): string {
  return `${m.year}-${String(m.month).padStart(2, '0')}`
}

function scrapMonthLabel(m: { year: number; month: number }): string {
  return `${m.month}月`
}

const scrapAllMonthly = computed(() => payload.value?.part01?.scrap?.monthly ?? [])

const scrapMonthOptions = computed(() =>
  scrapAllMonthly.value.map((m) => ({
    value: scrapMonthKey(m),
    label: scrapMonthLabel(m),
  })),
)

function resetScrapRange() {
  const all = scrapAllMonthly.value
  if (!all.length) {
    scrapRangeFrom.value = ''
    scrapRangeTo.value = ''
    return
  }
  scrapRangeFrom.value = scrapMonthKey(all[0])
  scrapRangeTo.value = scrapMonthKey(all[all.length - 1])
}

function onScrapRangeChange() {
  const all = scrapAllMonthly.value
  if (!all.length) return
  if (!scrapRangeFrom.value) scrapRangeFrom.value = scrapMonthKey(all[0])
  if (!scrapRangeTo.value) scrapRangeTo.value = scrapMonthKey(all[all.length - 1])
  if (scrapRangeFrom.value > scrapRangeTo.value) {
    ;[scrapRangeFrom.value, scrapRangeTo.value] = [scrapRangeTo.value, scrapRangeFrom.value]
  }
  scheduleScrapChart()
}

watch(scrapAllMonthly, (all) => {
  if (!all.length) {
    scrapRangeFrom.value = ''
    scrapRangeTo.value = ''
    return
  }
  const keys = new Set(all.map(scrapMonthKey))
  const needReset =
    !scrapRangeFrom.value ||
    !scrapRangeTo.value ||
    !keys.has(scrapRangeFrom.value) ||
    !keys.has(scrapRangeTo.value)
  if (needReset) resetScrapRange()
})

const meetingLabel = computed(() => payload.value?.meta?.meeting_month_label || targetMonth.value || '—')

const perfCommentsDisplay = computed(() =>
  (payload.value?.part01?.performance?.comments ?? []).filter((c) => c.trim()),
)

const scrapCommentsDisplay = computed(() =>
  (payload.value?.part01?.scrap?.comments ?? []).filter((c) => c.trim()),
)

const inventoryCommentsDisplay = computed(() =>
  (payload.value?.part01?.inventory?.comments ?? []).filter((c) => c.trim()),
)

type LoadRateLevel = 'overload' | 'tight' | 'ok' | 'light'

function loadRateLevel(pct: number): LoadRateLevel {
  const v = Number(pct) || 0
  if (v >= 100) return 'overload'
  if (v >= 90) return 'tight'
  if (v > 0 && v <= 60) return 'light'
  return 'ok'
}

function loadRateClass(pct: number): string {
  return `pr-load-rate pr-load-rate--${loadRateLevel(pct)}`
}

const LOAD_ROW_CLASS: Record<string, string> = {
  cutting: 'pr-load-row--cutting',
  chamfering: 'pr-load-row--chamfering',
  molding: 'pr-load-row--molding',
  plating: 'pr-load-row--plating',
  inspection: 'pr-load-row--inspection',
  welding: 'pr-load-row--welding',
  welding_sp: 'pr-load-row--welding',
}

function loadRowClassName({ row }: { row: LoadPlanRow }): string {
  return LOAD_ROW_CLASS[row.process_cd] || ''
}

function shiftBadgeClass(shiftLabel?: string): string {
  const m = (shiftLabel || '').match(/(\d+)/)
  const n = m ? Number(m[1]) : 0
  if (n >= 3) return 'pr-shift-badge--3'
  if (n === 2) return 'pr-shift-badge--2'
  if (n === 1) return 'pr-shift-badge--1'
  return 'pr-shift-badge--empty'
}

const LOAD_CAPACITY_CARD_CLASS: Record<string, string> = {
  cutting: 'pr-lcap-card--cutting',
  chamfering: 'pr-lcap-card--chamfering',
  molding: 'pr-lcap-card--molding',
  plating: 'pr-lcap-card--plating',
  inspection: 'pr-lcap-card--inspection',
  welding: 'pr-lcap-card--welding',
  welding_sp: 'pr-lcap-card--welding',
}

function loadCapacityCardClass(processCd: string): string {
  return LOAD_CAPACITY_CARD_CLASS[processCd] || ''
}

const loadCapacityMonthWd = computed(() => {
  const part = loadCapacityPart.value
  return Number(payload.value?.[part]?.load_plan?.working_days) || 0
})

const loadCapacityMonthLabel = computed(() => {
  const m = loadCapacityMonth.value
  if (!/^\d{4}-\d{2}$/.test(m)) return '対象月未設定'
  const [y, mo] = m.split('-')
  return `${Number(y)}年${Number(mo)}月`
})

function computeLoadPlanMeta(rows: LoadPlanRow[]) {
  const list = rows || []
  const rates = list.map((r) => Number(r.load_rate_pct) || 0)
  const maxRate = rates.length ? Math.max(...rates) : 0
  const overload = list.filter((r) => (r.load_rate_pct || 0) >= 100).length
  const tight = list.filter((r) => (r.load_rate_pct || 0) >= 90 && (r.load_rate_pct || 0) < 100).length
  const light = list.filter((r) => (r.load_rate_pct || 0) > 0 && (r.load_rate_pct || 0) <= 60).length
  const avgRate = rates.length ? Math.round(rates.reduce((a, b) => a + b, 0) / rates.length) : 0
  const bottleneck = list.reduce<LoadPlanRow | null>((best, r) => {
    const rate = Number(r.load_rate_pct) || 0
    if (!best || rate > (Number(best.load_rate_pct) || 0)) return r
    return best
  }, null)
  return {
    maxRate,
    overload,
    tight,
    light,
    avgRate,
    bottleneckName: bottleneck?.process_name || '—',
    bottleneckRate: Number(bottleneck?.load_rate_pct) || 0,
  }
}

const LOAD_PLAN_HOURS_PER_SHIFT = 7.6
const LOAD_PLAN_DEFAULT_UTILIZATION_PCT = 96
const LOAD_PLAN_DEFAULT_ADJUST_PCT = 100
const LOAD_PLAN_MAX_HOURS_PER_DAY = 24

type LoadPlanPart = 'part02' | 'part03'
const loadPlanEditCell = ref<{ processCd: string; part: LoadPlanPart } | null>(null)
const loadPlanEditDraft = ref<number | null>(null)

function parseLoadEquipCount(label: string): number {
  const m = (label || '').match(/[\d.]+/)
  return m ? parseFloat(m[0]) : 0
}

function parseLoadShiftCount(shift: string): number {
  const m = (shift || '').match(/(\d+)/)
  return m ? parseInt(m[1], 10) : 0
}

function isLoadPersonnel(label: string): boolean {
  return (label || '').includes('人')
}

function normalizeUtilizationRatePct(value: unknown): number {
  const n = Number(value)
  if (!Number.isFinite(n) || n <= 0) return LOAD_PLAN_DEFAULT_UTILIZATION_PCT
  if (n > 100) return 100
  return Math.round(n * 100) / 100
}

function normalizePlanAdjustRatePct(value: unknown): number {
  const n = Number(value)
  if (!Number.isFinite(n) || n < 0) return LOAD_PLAN_DEFAULT_ADJUST_PCT
  if (n > 999.99) return 999.99
  return Math.round(n * 100) / 100
}

function calcLoadDailyRegularHours(equipment: string, shift: string, utilizationRatePct?: number): number {
  const equip = parseLoadEquipCount(equipment)
  if (equip <= 0) return 0
  const shifts = parseLoadShiftCount(shift) || 1
  const util = normalizeUtilizationRatePct(utilizationRatePct) / 100
  if (isLoadPersonnel(equipment)) {
    return Math.round(equip * LOAD_PLAN_HOURS_PER_SHIFT * util * 100) / 100
  }
  return Math.round(equip * shifts * LOAD_PLAN_HOURS_PER_SHIFT * util * 100) / 100
}

function loadPlanCalendarDays(part: LoadPlanPart): number {
  const lp = part === 'part02' ? payload.value?.part02?.load_plan : payload.value?.part03?.load_plan
  if (lp?.calendar_days && Number(lp.calendar_days) > 0) return Number(lp.calendar_days)
  const monthStr = lp?.month || ''
  const m = monthStr.match(/^(\d{4})-(\d{2})$/)
  if (!m) return 0
  const y = Number(m[1])
  const mo = Number(m[2])
  return new Date(y, mo, 0).getDate()
}

function recomputeLoadPlanRow(row: LoadPlanRow, part: LoadPlanPart) {
  const planTh = Math.round((Number(row.plan_th) || 0) * 10) / 10
  const wd = Number(row.working_days) || 0
  const stdRate = Number(row.standard_rate) || 0
  const equipment = row.equipment_label || ''
  const equipCount = parseLoadEquipCount(equipment)
  const calDays = Number(row.calendar_days) || loadPlanCalendarDays(part)

  row.plan_th = planTh
  row.calendar_days = calDays
  row.daily_th = wd > 0 ? Math.round((planTh / wd) * 10) / 10 : 0

  const utilPct = normalizeUtilizationRatePct(row.utilization_rate_pct)
  row.utilization_rate_pct = utilPct
  row.plan_adjust_rate_pct = normalizePlanAdjustRatePct(row.plan_adjust_rate_pct)
  const dailyReg = Math.round(calcLoadDailyRegularHours(equipment, row.shift_label || '', utilPct))
  row.regular_hours = wd > 0 ? Math.round(dailyReg * wd) : 0

  const planUnits = planTh * 1000
  row.required_hours = stdRate > 0 ? Math.round(planUnits / stdRate) : 0
  row.load_rate_pct = row.regular_hours > 0 ? Math.round((row.required_hours / row.regular_hours) * 100) : 0
  row.daily_operation_hours =
    wd > 0 && row.required_hours > 0 && equipCount > 0
      ? Math.round((row.required_hours / wd / equipCount) * 10) / 10
      : 0

  if (row.process_cd === 'inspection') {
    row.equipment_utilization_pct = null
  } else {
    const denom = equipCount * calDays * LOAD_PLAN_MAX_HOURS_PER_DAY
    row.equipment_utilization_pct =
      denom > 0 && row.required_hours > 0
        ? Math.round((row.required_hours / denom) * 1000) / 10
        : null
  }
}

function isLoadPlanEditing(processCd: string, part: LoadPlanPart) {
  return loadPlanEditCell.value?.processCd === processCd && loadPlanEditCell.value?.part === part
}

function findLoadPlanRow(processCd: string, part: LoadPlanPart): LoadPlanRow | undefined {
  const rows = part === 'part02' ? payload.value?.part02?.load_plan?.rows : payload.value?.part03?.load_plan?.rows
  return rows?.find((r) => r.process_cd === processCd)
}

function startLoadPlanEdit(row: LoadPlanRow, part: LoadPlanPart) {
  loadPlanEditCell.value = { processCd: row.process_cd, part }
  const raw = row.plan_th
  loadPlanEditDraft.value = raw == null || Number.isNaN(Number(raw)) ? 0 : Number(raw)
  nextTick(() => {
    const el = document.querySelector('.pr-load-plan-edit-input') as HTMLInputElement | null
    el?.focus()
    el?.select()
  })
}

function cancelLoadPlanEdit() {
  loadPlanEditCell.value = null
  loadPlanEditDraft.value = null
}

function commitLoadPlanEdit() {
  if (!loadPlanEditCell.value) {
    cancelLoadPlanEdit()
    return
  }
  const { processCd, part } = loadPlanEditCell.value
  const row = findLoadPlanRow(processCd, part)
  if (row) {
    const n = Number(loadPlanEditDraft.value)
    row.plan_th = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0
    recomputeLoadPlanRow(row, part)
  }
  cancelLoadPlanEdit()
}

function isForecastInvEditable(row: InventoryRow): boolean {
  return !(row.children && row.children.length) && !INV_PARENT_KEYS.has(row.key)
}

const fcInvEditKey = ref<string | null>(null)
const fcInvEditPart = ref<'part02' | 'part03'>('part02')
const fcInvEditDraft = ref<number | null>(null)

function isFcInvEditing(key: string, part: 'part02' | 'part03' = 'part02') {
  return fcInvEditKey.value === key && fcInvEditPart.value === part
}

function startFcInvEdit(row: InventoryRow, part: 'part02' | 'part03' = 'part02') {
  if (!isForecastInvEditable(row)) return
  cancelInvEdit()
  fcInvEditKey.value = row.key
  fcInvEditPart.value = part
  fcInvEditDraft.value = Number(row.curr_inventory_th ?? 0)
  nextTick(() => {
    const el = document.querySelector('.pr-inv-edit-input--fc') as HTMLInputElement | null
    el?.focus()
    el?.select()
  })
}

function cancelFcInvEdit() {
  fcInvEditKey.value = null
  fcInvEditDraft.value = null
}

function forecastInvSection(part: 'part02' | 'part03' = 'part02'): InventorySection | null {
  return payload.value?.[part]?.inventory_forecast ?? null
}

function findFcInvRowByKey(key: string, part: 'part02' | 'part03' = 'part02'): InventoryRow | null {
  const rows = forecastInvSection(part)?.rows || []
  for (const row of rows) {
    if (row.key === key) return row
    const child = row.children?.find((c) => c.key === key)
    if (child) return child
  }
  return null
}

function findFcInvParentOf(key: string, part: 'part02' | 'part03' = 'part02'): InventoryRow | null {
  const rows = forecastInvSection(part)?.rows || []
  return rows.find((r) => r.children?.some((c) => c.key === key)) || null
}

function commitFcInvEdit() {
  const part = fcInvEditPart.value
  const inv = forecastInvSection(part)
  if (!fcInvEditKey.value || !inv) {
    cancelFcInvEdit()
    return
  }
  const key = fcInvEditKey.value
  const row = findFcInvRowByKey(key, part)
  if (row) {
    const n = Number(fcInvEditDraft.value)
    row.curr_inventory_th = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0
    recomputeInvDerived(row, inv)
    const parent = findFcInvParentOf(key, part)
    if (parent) {
      refreshInvParentFromChildren(parent, inv)
    }
    refreshWipTotalFromProcesses(inv)
    if (part === 'part02') {
      syncPart03PrevFromPart02Forecast()
    }
  }
  cancelFcInvEdit()
}

/** PART03 前月在庫 ← PART02 予測在庫 */
function syncPart03PrevFromPart02Forecast() {
  const prior = forecastInvSection('part02')
  const target = forecastInvSection('part03')
  if (!prior?.rows?.length || !target?.rows?.length) return

  const priorByKey = new Map<string, InventoryRow>()
  for (const row of prior.rows) {
    priorByKey.set(row.key, row)
    for (const child of row.children || []) {
      priorByKey.set(child.key, child)
    }
  }

  for (const row of target.rows) {
    if (row.key === 'wip_total') continue
    if (row.children?.length) {
      for (const child of row.children) {
        const src = priorByKey.get(child.key)
        if (!src) continue
        child.prev_inventory_th = Math.round(Number(src.curr_inventory_th || 0) * 10) / 10
        recomputeInvDerived(child, target)
      }
      refreshInvParentFromChildren(row, target)
      continue
    }
    const src = priorByKey.get(row.key)
    if (!src) continue
    row.prev_inventory_th = Math.round(Number(src.curr_inventory_th || 0) * 10) / 10
    recomputeInvDerived(row, target)
  }
  refreshWipTotalFromProcesses(target)
  target.prev_inventory_as_of = null
}

const part02LoadCommentsDisplay = computed(() =>
  (payload.value?.part02?.load_plan?.comments ?? []).filter((c) => c.trim()),
)

const part03LoadCommentsDisplay = computed(() =>
  (payload.value?.part03?.load_plan?.comments ?? []).filter((c) => c.trim()),
)

const inventoryForecastCommentsDisplay = computed(() =>
  (payload.value?.part02?.inventory_forecast?.comments ?? []).filter((c) => c.trim()),
)

const part03InventoryForecastCommentsDisplay = computed(() =>
  (payload.value?.part03?.inventory_forecast?.comments ?? []).filter((c) => c.trim()),
)

const part02LoadMeta = computed(() => computeLoadPlanMeta(payload.value?.part02?.load_plan?.rows ?? []))
const part03LoadMeta = computed(() => computeLoadPlanMeta(payload.value?.part03?.load_plan?.rows ?? []))

const inventoryProductRow = computed(() =>
  payload.value?.part01?.inventory?.rows?.find((r) => r.key === 'product') ?? null,
)

const inventoryProductLevel = computed(() => {
  const inv = payload.value?.part01?.inventory
  if (!inv) return 'ok'
  if (inv.product_level) return inv.product_level
  return resolveProductLevel(
    inventoryProductRow.value?.curr_rate_adj,
    inventoryProductRow.value?.curr_days,
    inv.product_target_rate,
    inv.product_target_days,
  )
})

const inventoryProductLevelLabel = computed(() => {
  if (inventoryProductLevel.value === 'danger') return '危険（不足）'
  if (inventoryProductLevel.value === 'high') return '注意（過多）'
  return '適正'
})

const commentDraftPreview = computed(() => commentDraft.value.map((l) => l.trim()).filter((l) => l))

type CommentSegment = { kind: 'text' | 'pos' | 'neg'; text: string }

function parseCommentSegments(line: string): CommentSegment[] {
  const re = /△\d+(?:\.\d+)?%?|[+-]\d+(?:\.\d+)?%?|\d+(?:\.\d+)?%?/g
  const parts: CommentSegment[] = []
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) {
      parts.push({ kind: 'text', text: line.slice(last, m.index) })
    }
    const token = m[0]
    const kind: 'pos' | 'neg' = token.startsWith('△') || token.startsWith('-') ? 'neg' : 'pos'
    parts.push({ kind, text: token })
    last = m.index + token.length
  }
  if (last < line.length) {
    parts.push({ kind: 'text', text: line.slice(last) })
  }
  return parts.length ? parts : [{ kind: 'text', text: line }]
}

function openCommentDialog(
  kind: 'performance' | 'scrap' | 'inventory' | 'load_plan' | 'inventory_forecast',
  part?: 'part02' | 'part03',
) {
  commentDialogKind.value = kind
  commentDialogPart.value = part ?? null
  let existing: string[] = []
  if (kind === 'scrap') {
    existing = payload.value?.part01?.scrap?.comments ?? []
  } else if (kind === 'inventory') {
    existing = payload.value?.part01?.inventory?.comments ?? []
  } else if (kind === 'load_plan') {
    existing =
      part === 'part03'
        ? payload.value?.part03?.load_plan?.comments ?? []
        : payload.value?.part02?.load_plan?.comments ?? []
  } else if (kind === 'inventory_forecast') {
    existing =
      part === 'part03'
        ? payload.value?.part03?.inventory_forecast?.comments ?? []
        : payload.value?.part02?.inventory_forecast?.comments ?? []
  } else {
    existing = payload.value?.part01?.performance?.comments ?? []
  }
  commentDraft.value = existing.length ? [...existing] : ['']
  commentDialogVisible.value = true
}

async function regenerateSectionComments(
  kind: CommentGenerateKind,
  part?: 'part02' | 'part03',
) {
  if (!payload.value) {
    ElMessage.warning('データがありません')
    return
  }
  try {
    await ElMessageBox.confirm(
      '現在の数値（手修正含む）からコメントを自動再生成します。既存コメントは上書きされます。よろしいですか？',
      'コメント自動再生成',
      { type: 'warning', confirmButtonText: '再生成', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }

  const loadingKey =
    (kind === 'load_plan' || kind === 'inventory_forecast') && part
      ? `${kind}_${part}`
      : kind
  let section: Record<string, unknown> | null = null
  if (kind === 'performance') section = payload.value.part01.performance as unknown as Record<string, unknown>
  else if (kind === 'scrap') {
    // UIで選択中の期間（scrapMeta）を反映して再生成
    const s = payload.value.part01.scrap
    const meta = scrapMeta.value
    const monthly = meta.monthly || []
    const last = monthly[monthly.length - 1]
    section = {
      ...(s as unknown as Record<string, unknown>),
      fiscal_year_label: meta.fiscalLabel,
      range_label: meta.rangeLabel,
      monthly,
      current_month_rate_new_pct: Number(meta.currentRateNew),
      current_month_rate_old_pct: Number(meta.currentRateOld),
      current_month_loss_qty: last ? scrapLossQty(last) : 0,
      avg_rate_new_current_fy_pct: Number(meta.avgRateNew),
      avg_rate_old_current_fy_pct: Number(meta.avgRateOld),
      avg_loss_current_fy_qty: monthly.length
        ? Math.round(monthly.reduce((sum, m) => sum + scrapLossQty(m), 0) / monthly.length)
        : 0,
      improvement_rate_new_pt: Number(meta.improvementRateNewPt),
      improvement_rate_old_pt: Number(meta.improvementRateOldPt),
      improvement_rate_pt: Number(meta.improvementRateOldPt),
    }
  } else if (kind === 'inventory') section = payload.value.part01.inventory as unknown as Record<string, unknown>
  else if (kind === 'inventory_forecast') {
    const fc =
      part === 'part03'
        ? payload.value.part03.inventory_forecast
        : payload.value.part02.inventory_forecast
    section = fc as unknown as Record<string, unknown>
  } else if (kind === 'load_plan') {
    const lp = part === 'part03' ? payload.value.part03.load_plan : payload.value.part02.load_plan
    section = lp as unknown as Record<string, unknown>
  }
  if (!section) {
    ElMessage.error('対象データが見つかりません')
    return
  }

  commentRegenLoading.value = loadingKey
  try {
    const res = await generateComments(kind, section)
    const lines = (res.data?.comments || []).filter((c) => String(c || '').trim())
    if (kind === 'performance') payload.value.part01.performance.comments = lines
    else if (kind === 'scrap') payload.value.part01.scrap.comments = lines
    else if (kind === 'inventory') payload.value.part01.inventory.comments = lines
    else if (kind === 'inventory_forecast') {
      if (part === 'part03') {
        if (!payload.value.part03.inventory_forecast) {
          ElMessage.error('対象データが見つかりません')
          return
        }
        payload.value.part03.inventory_forecast.comments = lines
      } else {
        payload.value.part02.inventory_forecast.comments = lines
      }
    } else if (kind === 'load_plan') {
      if (part === 'part03') payload.value.part03.load_plan.comments = lines
      else payload.value.part02.load_plan.comments = lines
    }
    ElMessage.success('コメントを自動再生成しました')
  } catch (e) {
    ElMessage.error((e as Error)?.message || 'コメント再生成に失敗しました')
  } finally {
    commentRegenLoading.value = null
  }
}

function addCommentDraftLine() {
  commentDraft.value.push('')
}

function removeCommentDraftLine(i: number) {
  if (commentDraft.value.length <= 1) return
  commentDraft.value.splice(i, 1)
}

function saveCommentDialog() {
  if (!payload.value) return
  const lines = commentDraft.value.map((l) => l.trim()).filter((l) => l)
  if (commentDialogKind.value === 'scrap') {
    payload.value.part01.scrap.comments ||= []
    payload.value.part01.scrap.comments = lines
    ElMessage.success('廃棄コメントを保存しました')
  } else if (commentDialogKind.value === 'inventory') {
    payload.value.part01.inventory.comments ||= []
    payload.value.part01.inventory.comments = lines
    ElMessage.success('在庫コメントを保存しました')
  } else if (commentDialogKind.value === 'load_plan') {
    if (commentDialogPart.value === 'part03') {
      payload.value.part03.load_plan.comments ||= []
      payload.value.part03.load_plan.comments = lines
    } else {
      payload.value.part02.load_plan.comments ||= []
      payload.value.part02.load_plan.comments = lines
    }
    ElMessage.success('計画コメントを保存しました')
  } else if (commentDialogKind.value === 'inventory_forecast') {
    if (commentDialogPart.value === 'part03') {
      if (!payload.value.part03.inventory_forecast) {
        ElMessage.warning('在庫予測データがありません')
        return
      }
      payload.value.part03.inventory_forecast.comments ||= []
      payload.value.part03.inventory_forecast.comments = lines
    } else {
      payload.value.part02.inventory_forecast.comments ||= []
      payload.value.part02.inventory_forecast.comments = lines
    }
    ElMessage.success('在庫予測コメントを保存しました')
  } else {
    payload.value.part01.performance.comments ||= []
    payload.value.part01.performance.comments = lines
    ElMessage.success('実績コメントを保存しました')
  }
  commentDialogVisible.value = false
}

const scrapMeta = computed(() => {
  const s = payload.value?.part01?.scrap
  const all = s?.monthly ?? []
  const from = scrapRangeFrom.value
  const to = scrapRangeTo.value
  const monthly =
    from && to
      ? all.filter((m) => {
          const k = scrapMonthKey(m)
          return k >= from && k <= to
        })
      : all
  const fiscalLabel =
    s?.fiscal_year_label ??
    (all.length ? `${all[0].month >= 4 ? all[0].year : all[0].year - 1}年度` : '当年度')
  const rangeLabel = monthly.length
    ? `${monthly[0].month}月〜${monthly[monthly.length - 1].month}月`
    : s?.range_label ?? ''
  const last = monthly[monthly.length - 1]
  const avgNew =
    monthly.length > 0
      ? monthly.reduce((sum, m) => sum + Number(m.rate_new_pct ?? m.rate_pct ?? 0), 0) / monthly.length
      : 0
  const avgOld =
    monthly.length > 0
      ? monthly.reduce((sum, m) => sum + Number(m.rate_old_pct ?? m.rate_pct ?? 0), 0) / monthly.length
      : 0
  const avgLoss =
    monthly.length > 0
      ? monthly.reduce((sum, m) => sum + scrapLossQty(m), 0) / monthly.length
      : 0
  const improvementNew =
    Number(s?.avg_rate_new_prev_fy_pct ?? 0) - avgNew
  const improvementOld =
    Number(s?.avg_rate_old_prev_fy_pct ?? s?.avg_rate_prev_fy_pct ?? 0) - avgOld
  return {
    fiscalLabel,
    rangeLabel,
    monthly,
    currentRateNew: Number(last ? last.rate_new_pct ?? last.rate_pct ?? 0 : 0).toFixed(2),
    currentRateOld: Number(last ? last.rate_old_pct ?? last.rate_pct ?? 0 : 0).toFixed(2),
    currentLossQty: fmtInt(last ? scrapLossQty(last) : 0),
    avgRateNew: avgNew.toFixed(2),
    avgRateOld: avgOld.toFixed(2),
    avgLossQty: fmtInt(Math.round(avgLoss)),
    improvementRateNewPt: improvementNew.toFixed(2),
    improvementNewPositive: improvementNew >= 0,
    improvementRateOldPt: improvementOld.toFixed(2),
    improvementOldPositive: improvementOld >= 0,
  }
})

function scrapRate(m: ScrapMonthlyItem, kind: 'new' | 'old'): string {
  const v = kind === 'new' ? m.rate_new_pct ?? m.rate_pct : m.rate_old_pct ?? m.rate_pct
  return Number(v ?? 0).toFixed(2)
}

function scrapLossQty(m: ScrapMonthlyItem): number {
  if (m.loss_qty != null) return m.loss_qty
  if (m.loss_th != null) return Math.round(m.loss_th * 1000)
  if (m.scrap_th != null) return Math.round(m.scrap_th * 1000)
  return 0
}

function fmtInt(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '-'
  return Math.round(Number(v)).toLocaleString()
}

function defaultMonth(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

function fmtNum(v: number | null | undefined, digits = 1): string {
  if (v == null || Number.isNaN(Number(v))) return '-'
  return Number(v).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

function fmtRate(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '-'
  return Number(v).toFixed(2)
}

function fmtDays(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '-'
  return Number(v).toFixed(1)
}

function resolveProductLevel(
  rateAdj: number | null | undefined,
  days: number | null | undefined,
  targetRate?: number | null,
  targetDays?: number | null,
): 'danger' | 'ok' | 'high' {
  const tr = Number(targetRate ?? 0.36)
  const td = Number(targetDays ?? 7.2)
  const r = Number(rateAdj ?? 0)
  const d = Number(days ?? 0)
  if (d < td || r < tr) return 'danger'
  if (d > td * 2) return 'high'
  return 'ok'
}

const DEFAULT_PROCESS_TARGET_RATES: Record<string, number> = {
  cutting: 0.15,
  molding: 0.15,
  plating: 0.19,
  plating_inhouse: 0.19,
  plating_outsource: 0.19,
  welding: 0.19,
  welding_inhouse: 0.19,
  welding_outsource: 0.19,
  product: 0.36,
}

function inventoryTargetFor(rowKey: string, kind: 'rate' | 'days'): number | null {
  const inv = payload.value?.part01?.inventory
  const stdWd = Number(inv?.standard_workdays ?? 20) || 20
  const rateFromApi = inv?.process_target_rates?.[rowKey]
  const rate =
    rateFromApi != null
      ? Number(rateFromApi)
      : DEFAULT_PROCESS_TARGET_RATES[rowKey] != null
        ? DEFAULT_PROCESS_TARGET_RATES[rowKey]
        : rowKey === 'product'
          ? Number(inv?.product_target_rate ?? 0.36)
          : null
  if (rate == null) return null
  if (kind === 'rate') return rate
  const daysFromApi = inv?.process_target_days?.[rowKey]
  if (daysFromApi != null) return Number(daysFromApi)
  if (rowKey === 'product' && inv?.product_target_days != null) return Number(inv.product_target_days)
  return Math.round(rate * stdWd * 10) / 10
}

function inventoryTargetLabel(rowKey: string): string {
  const rate = inventoryTargetFor(rowKey, 'rate')
  const days = inventoryTargetFor(rowKey, 'days')
  if (rate == null || days == null) return ''
  return `${fmtRate(rate)} / ${fmtDays(days)}日`
}

function inventoryMetricClass(
  row: InventoryRow,
  value: number | null | undefined,
  kind: 'rate' | 'days',
): string {
  const target = inventoryTargetFor(row.key, kind)
  if (target == null) return ''
  const v = Number(value ?? 0)
  if (v < target) return 'is-danger'
  if (v > target * 2) return 'is-high'
  return 'is-ok'
}

function refreshInventoryProductLevel() {
  const inv = payload.value?.part01?.inventory
  if (!inv) return
  const product = inv.rows?.find((r) => r.key === 'product')
  inv.product_level = resolveProductLevel(
    product?.curr_rate_adj,
    product?.curr_days,
    inv.product_target_rate,
    inv.product_target_days,
  )
}

function fmtDelta(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '-'
  const n = Number(v)
  if (n > 0) return fmtNum(n)
  if (n < 0) return `△${fmtNum(Math.abs(n))}`
  return fmtNum(0)
}

function fmtProdDelta(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '-'
  const n = Math.round(Number(v))
  if (n > 0) return `+${n}`
  if (n < 0) return `△${Math.abs(n)}`
  return '+0'
}

function fmtProductivity(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return String(Math.round(Number(v)))
}

function calcProdDelta(row: { productivity_prev?: number | null; productivity_curr?: number | null }) {
  if (row.productivity_prev == null || row.productivity_curr == null) return null
  return row.productivity_curr - row.productivity_prev
}

type PerfEditField = 'plan_th' | 'forecast_th' | 'actual_th' | 'productivity_prev' | 'productivity_curr'
const PERF_TH_FIELDS = new Set<PerfEditField>(['plan_th', 'forecast_th', 'actual_th'])
const perfEditCell = ref<{ key: string; field: PerfEditField } | null>(null)
const perfEditDraft = ref<number | null>(null)

function isPerfEditing(key: string, field: PerfEditField) {
  return perfEditCell.value?.key === key && perfEditCell.value?.field === field
}

function startPerfEdit(row: PerformanceRow, field: PerfEditField) {
  if (
    row.key === 'shipping' &&
    (field === 'productivity_prev' || field === 'productivity_curr')
  ) {
    return
  }
  perfEditCell.value = { key: row.key, field }
  const raw = row[field]
  perfEditDraft.value = raw == null || Number.isNaN(Number(raw)) ? 0 : Number(raw)
  nextTick(() => {
    const el = document.querySelector('.pr-perf-edit-input') as HTMLInputElement | null
    el?.focus()
    el?.select()
  })
}

function cancelPerfEdit() {
  perfEditCell.value = null
  perfEditDraft.value = null
}

function recomputePerfDerived(row: PerformanceRow) {
  const plan = Number(row.plan_th) || 0
  const forecast = Number(row.forecast_th) || 0
  const actual = Number(row.actual_th) || 0
  row.plan_th = Math.round(plan * 10) / 10
  row.forecast_th = Math.round(forecast * 10) / 10
  row.actual_th = Math.round(actual * 10) / 10
  row.vs_forecast_th = Math.round((row.forecast_th - row.plan_th) * 10) / 10
  row.vs_plan_th = Math.round((row.actual_th - row.plan_th) * 10) / 10
  if (row.key === 'shipping') {
    row.productivity_prev = null
    row.productivity_curr = null
    row.productivity_delta = null
    return
  }
  if (row.productivity_prev != null && !Number.isNaN(Number(row.productivity_prev))) {
    row.productivity_prev = Math.round(Number(row.productivity_prev))
  }
  if (row.productivity_curr != null && !Number.isNaN(Number(row.productivity_curr))) {
    row.productivity_curr = Math.round(Number(row.productivity_curr))
  }
  row.productivity_delta = calcProdDelta(row)
}

function commitPerfEdit() {
  if (!perfEditCell.value || !payload.value?.part01?.performance) {
    cancelPerfEdit()
    return
  }
  const { key, field } = perfEditCell.value
  const row = payload.value.part01.performance.rows.find((r) => r.key === key)
  if (row) {
    const n = Number(perfEditDraft.value)
    if (PERF_TH_FIELDS.has(field)) {
      row[field] = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0
    } else {
      row[field] = Number.isFinite(n) ? Math.round(n) : 0
    }
    recomputePerfDerived(row)
  }
  cancelPerfEdit()
}

function deltaClass(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v)) || Number(v) === 0) return 'pr-delta pr-delta--zero'
  return Number(v) > 0 ? 'pr-delta pr-delta--pos' : 'pr-delta pr-delta--neg'
}

type InvEditField = 'prev_inventory_th' | 'curr_inventory_th'
const WIP_TOP_KEYS = new Set(['cutting', 'molding', 'plating', 'welding'])
const INV_PARENT_KEYS = new Set(['plating', 'welding'])
const invEditCell = ref<{ key: string; field: InvEditField } | null>(null)
const invEditDraft = ref<number | null>(null)
const currInvDateDialogVisible = ref(false)
const currInvDateDraft = ref<string>('')
const currInvDateLoading = ref(false)
const fcPrevInvDateDialogVisible = ref(false)
const fcPrevInvDateDraft = ref<string>('')
const fcPrevInvDateLoading = ref(false)
const fcPrevInvDatePart = ref<'part02' | 'part03'>('part02')

function formatInvAsOfHeader(prefix: string, asOf?: string | null) {
  if (!asOf) return `${prefix}(千本)`
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(asOf)
  if (!m) return `${prefix} ${asOf}(千本)`
  return `${prefix} ${Number(m[2])}/${Number(m[3])}(千本)`
}

const currInventoryHeaderLabel = computed(() =>
  formatInvAsOfHeader('当月在庫', payload.value?.part01?.inventory?.curr_inventory_as_of),
)

const fcPrevInventoryHeaderLabel = computed(() =>
  formatInvAsOfHeader('前月在庫', payload.value?.part02?.inventory_forecast?.prev_inventory_as_of),
)

const fcPrevInventoryHeaderLabelPart03 = computed(() => '前月在庫(千本)')

function defaultInventoryMonthEndDate(inv: InventorySection): string {
  const label = inv.inventory_month_label || ''
  const lm = /(\d{4})年(\d{1,2})月/.exec(label)
  if (lm) {
    const yy = Number(lm[1])
    const mm = Number(lm[2])
    const last = new Date(yy, mm, 0)
    return `${yy}-${String(mm).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`
  }
  const y = inv.curr_forecast_year
  const m = inv.curr_forecast_month
  if (y && m) {
    const d = new Date(Number(y), Number(m) - 1, 0)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }
  return ''
}

function openCurrInvDateDialog() {
  const inv = payload.value?.part01?.inventory
  if (!inv) {
    ElMessage.warning('在庫データがありません')
    return
  }
  currInvDateDraft.value = inv.curr_inventory_as_of || defaultInventoryMonthEndDate(inv)
  currInvDateDialogVisible.value = true
}

function openFcPrevInvDateDialog(part: 'part02' | 'part03' = 'part02') {
  const inv = forecastInvSection(part)
  if (!inv) {
    ElMessage.warning('在庫予測データがありません')
    return
  }
  fcPrevInvDatePart.value = part
  // 前月在庫のデフォルトは在庫月（inventory_month_label）の前月末
  fcPrevInvDateDraft.value = inv.prev_inventory_as_of || ''
  if (!fcPrevInvDateDraft.value) {
    const label = inv.inventory_month_label || ''
    const lm = /(\d{4})年(\d{1,2})月/.exec(label)
    if (lm) {
      const d = new Date(Number(lm[1]), Number(lm[2]) - 1, 0)
      fcPrevInvDateDraft.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    } else {
      const end = defaultInventoryMonthEndDate(inv)
      if (end) {
        const [yy, mm] = end.split('-').map(Number)
        const d = new Date(yy, mm - 1, 0)
        fcPrevInvDateDraft.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      }
    }
  }
  fcPrevInvDateDialogVisible.value = true
}

async function applyInventoryQtyByDate(
  inv: InventorySection,
  dateStr: string,
  field: 'prev_inventory_th' | 'curr_inventory_th',
) {
  const res = await fetchInventoryByDate(dateStr)
  const qty = res.data?.quantities_th || {}
  for (const row of inv.rows) {
    if (row.children?.length) {
      for (const child of row.children) {
        if (qty[child.key] != null) {
          child[field] = Math.round(Number(qty[child.key]) * 10) / 10
          recomputeInvDerived(child, inv)
        }
      }
      refreshInvParentFromChildren(row, inv)
    } else if (row.key !== 'wip_total' && qty[row.key] != null) {
      row[field] = Math.round(Number(qty[row.key]) * 10) / 10
      recomputeInvDerived(row, inv)
    }
  }
  refreshWipTotalFromProcesses(inv)
  return res
}

async function applyCurrInventoryByDate() {
  const inv = payload.value?.part01?.inventory
  if (!inv?.rows) return
  const dateStr = (currInvDateDraft.value || '').trim()
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    ElMessage.warning('日付を選択してください')
    return
  }
  currInvDateLoading.value = true
  try {
    const res = await applyInventoryQtyByDate(inv, dateStr, 'curr_inventory_th')
    inv.curr_inventory_as_of = res.data?.date || dateStr
    refreshInventoryProductLevel()
    currInvDateDialogVisible.value = false
    ElMessage.success(`${res.data?.date_label || dateStr} の在庫を反映しました`)
  } catch (e) {
    ElMessage.error((e as Error)?.message || '在庫の取得に失敗しました')
  } finally {
    currInvDateLoading.value = false
  }
}

async function applyFcPrevInventoryByDate() {
  const part = fcPrevInvDatePart.value
  const inv = forecastInvSection(part)
  if (!inv?.rows) return
  const dateStr = (fcPrevInvDateDraft.value || '').trim()
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    ElMessage.warning('日付を選択してください')
    return
  }
  fcPrevInvDateLoading.value = true
  try {
    const res = await applyInventoryQtyByDate(inv, dateStr, 'prev_inventory_th')
    inv.prev_inventory_as_of = res.data?.date || dateStr
    fcPrevInvDateDialogVisible.value = false
    ElMessage.success(`${res.data?.date_label || dateStr} の在庫を前月在庫に反映しました`)
  } catch (e) {
    ElMessage.error((e as Error)?.message || '在庫の取得に失敗しました')
  } finally {
    fcPrevInvDateLoading.value = false
  }
}

function isInvEditable(row: InventoryRow) {
  return !(row.children && row.children.length) && !INV_PARENT_KEYS.has(row.key)
}

function isInvEditing(key: string, field: InvEditField) {
  return invEditCell.value?.key === key && invEditCell.value?.field === field
}

function startInvEdit(row: InventoryRow, field: InvEditField) {
  if (!isInvEditable(row)) return
  cancelFcInvEdit()
  invEditCell.value = { key: row.key, field }
  invEditDraft.value = Number(row[field] ?? 0)
  nextTick(() => {
    const el = document.querySelector('.pr-inv-edit-input:not(.pr-inv-edit-input--fc)') as HTMLInputElement | null
    el?.focus()
    el?.select()
  })
}

function cancelInvEdit() {
  invEditCell.value = null
  invEditDraft.value = null
}

function findInvRowByKey(key: string): InventoryRow | null {
  const rows = payload.value?.part01?.inventory?.rows || []
  for (const row of rows) {
    if (row.key === key) return row
    const child = row.children?.find((c) => c.key === key)
    if (child) return child
  }
  return null
}

function findInvParentOf(key: string): InventoryRow | null {
  const rows = payload.value?.part01?.inventory?.rows || []
  return rows.find((r) => r.children?.some((c) => c.key === key)) || null
}

function recomputeInvDerived(row: InventoryRow, invSection?: InventorySection | null) {
  const inv = invSection ?? payload.value?.part01?.inventory
  if (!inv) return
  const prevF = Number(row.prev_forecast_th ?? inv.prev_forecast_th) || 0
  const currF = Number(row.curr_forecast_th ?? inv.curr_forecast_th) || 0
  const prevAdj = Number(row.prev_forecast_adj_th ?? inv.prev_forecast_adj_th ?? prevF) || 0
  const currAdj = Number(row.curr_forecast_adj_th ?? inv.curr_forecast_adj_th ?? currF) || 0
  const prevWd = Number(inv.prev_workdays) || 0
  const currWd = Number(inv.curr_workdays) || 0
  const prevTh = Number(row.prev_inventory_th) || 0
  const currTh = Number(row.curr_inventory_th) || 0
  row.prev_inventory_th = Math.round(prevTh * 10) / 10
  row.curr_inventory_th = Math.round(currTh * 10) / 10
  row.prev_rate = prevF > 0 ? Math.round((row.prev_inventory_th / prevF) * 100) / 100 : 0
  row.curr_rate = currF > 0 ? Math.round((row.curr_inventory_th / currF) * 100) / 100 : 0
  row.prev_rate_adj = prevAdj > 0 ? Math.round((row.prev_inventory_th / prevAdj) * 100) / 100 : 0
  row.curr_rate_adj = currAdj > 0 ? Math.round((row.curr_inventory_th / currAdj) * 100) / 100 : 0
  row.prev_days =
    prevF > 0 && prevWd > 0 ? Math.round(((row.prev_inventory_th * prevWd) / prevF) * 10) / 10 : 0
  row.curr_days =
    currF > 0 && currWd > 0 ? Math.round(((row.curr_inventory_th * currWd) / currF) * 10) / 10 : 0
  row.delta_th = Math.round((row.curr_inventory_th - row.prev_inventory_th) * 10) / 10
}

function refreshInvParentFromChildren(parent: InventoryRow, invSection?: InventorySection | null) {
  if (!parent.children?.length) return
  parent.prev_inventory_th =
    Math.round(parent.children.reduce((s, r) => s + Number(r.prev_inventory_th || 0), 0) * 10) / 10
  parent.curr_inventory_th =
    Math.round(parent.children.reduce((s, r) => s + Number(r.curr_inventory_th || 0), 0) * 10) / 10
  parent.prev_forecast_th =
    Math.round(parent.children.reduce((s, r) => s + Number(r.prev_forecast_th || 0), 0) * 10) / 10
  parent.curr_forecast_th =
    Math.round(parent.children.reduce((s, r) => s + Number(r.curr_forecast_th || 0), 0) * 10) / 10
  parent.prev_forecast_adj_th =
    Math.round(parent.children.reduce((s, r) => s + Number(r.prev_forecast_adj_th || 0), 0) * 10) / 10
  parent.curr_forecast_adj_th =
    Math.round(parent.children.reduce((s, r) => s + Number(r.curr_forecast_adj_th || 0), 0) * 10) / 10
  recomputeInvDerived(parent, invSection)
}

function refreshWipTotalFromProcesses(invSection?: InventorySection | null) {
  const inv = invSection ?? payload.value?.part01?.inventory
  if (!inv?.rows) return
  const tops = inv.rows.filter((r) => WIP_TOP_KEYS.has(r.key))
  const wip = inv.rows.find((r) => r.key === 'wip_total')
  if (!wip) return
  wip.prev_inventory_th =
    Math.round(tops.reduce((s, r) => s + Number(r.prev_inventory_th || 0), 0) * 10) / 10
  wip.curr_inventory_th =
    Math.round(tops.reduce((s, r) => s + Number(r.curr_inventory_th || 0), 0) * 10) / 10
  // 分母は全量出荷内示
  wip.prev_forecast_th = Number(inv.prev_forecast_th) || 0
  wip.curr_forecast_th = Number(inv.curr_forecast_th) || 0
  wip.prev_forecast_adj_th = Number(inv.prev_forecast_adj_th ?? inv.prev_forecast_th) || 0
  wip.curr_forecast_adj_th = Number(inv.curr_forecast_adj_th ?? inv.curr_forecast_th) || 0
  recomputeInvDerived(wip, inv)
}

function commitInvEdit() {
  if (!invEditCell.value || !payload.value?.part01?.inventory) {
    cancelInvEdit()
    return
  }
  const { key, field } = invEditCell.value
  const row = findInvRowByKey(key)
  if (row) {
    const n = Number(invEditDraft.value)
    row[field] = Number.isFinite(n) ? Math.round(n * 10) / 10 : 0
    recomputeInvDerived(row)
    const parent = findInvParentOf(key)
    if (parent) {
      refreshInvParentFromChildren(parent)
    }
    refreshWipTotalFromProcesses()
    refreshInventoryProductLevel()
  }
  cancelInvEdit()
}

function inventoryRowClassName({ row }: { row: InventoryRow }) {
  const classes: string[] = []
  if (row.key === 'product') classes.push(`pr-inv-row--product is-${inventoryProductLevel.value}`)
  if (row.children?.length) classes.push('pr-inv-row--parent')
  if (row.key.startsWith('plating_') || row.key.startsWith('welding_')) classes.push('pr-inv-row--child')
  return classes.join(' ')
}

function prodDeltaClass(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v)) || Number(v) === 0) return 'pr-delta pr-delta--zero'
  return Number(v) > 0 ? 'pr-delta pr-delta--pos' : 'pr-delta pr-delta--neg'
}

function disposeScrapChart() {
  scrapChart?.dispose()
  scrapChart = null
}

function renderScrapChart() {
  if (activeTab.value !== 'part01' || !scrapChartRef.value || !scrapMeta.value.monthly.length) {
    disposeScrapChart()
    return
  }
  if (!scrapChart) {
    scrapChart = echarts.init(scrapChartRef.value)
  }
  const data = scrapMeta.value.monthly
  const labels = data.map((m: ScrapMonthlyItem) => `${m.month}月`)
  const lastIdx = data.length - 1

  const qtyValues = data.map((m) => scrapLossQty(m))
  const rateNewValues = data.map((m) => Number(scrapRate(m, 'new')))
  const rateOldValues = data.map((m) => Number(scrapRate(m, 'old')))
  const qtyMax = Math.max(0, ...qtyValues)
  const rateMax = Math.max(0, ...rateNewValues, ...rateOldValues)

  const qtyAxisMax = (() => {
    const padded = qtyMax * 1.85 || 100
    if (padded <= 100) return Math.ceil(padded / 10) * 10
    if (padded <= 1000) return Math.ceil(padded / 50) * 50
    if (padded <= 10000) return Math.ceil(padded / 500) * 500
    return Math.ceil(padded / 1000) * 1000
  })()
  const rateAxisMax = Math.max(Math.ceil(rateMax * 1.45 * 10) / 10, 2.5)

  scrapChart.setOption(
    {
      color: [CHART_THEME.qtyMid, CHART_THEME.rateNew, CHART_THEME.rateOld],
      animation: true,
      animationDuration: 1100,
      animationDurationUpdate: 700,
      animationEasing: 'cubicOut',
      animationEasingUpdate: 'cubicInOut',
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          crossStyle: { color: '#94a3b8' },
          lineStyle: { color: 'rgba(148, 163, 184, 0.45)', type: 'dashed' },
          shadowStyle: { color: 'rgba(249, 115, 22, 0.06)' },
        },
        backgroundColor: 'rgba(15, 23, 42, 0.94)',
        borderColor: 'transparent',
        borderWidth: 0,
        padding: [12, 14],
        extraCssText:
          'border-radius: 12px; box-shadow: 0 12px 28px rgba(15,23,42,0.28); backdrop-filter: blur(8px);',
        textStyle: { color: '#f8fafc', fontSize: 14 },
        formatter: (params: Array<{ seriesName: string; value: number; marker: string; axisValue: string }>) => {
          if (!params?.length) return ''
          const rows = params
            .filter((p) => p.seriesName === '廃棄本数' || p.seriesName.startsWith('廃棄率'))
            .map((p) => {
              const isQty = p.seriesName === '廃棄本数'
              const val = isQty
                ? `${Number(p.value).toLocaleString()} 本`
                : `${Number(p.value).toFixed(2)} %`
              return `<div style="display:flex;justify-content:space-between;gap:18px;margin:4px 0">
                <span>${p.marker}${p.seriesName}</span>
                <strong style="font-variant-numeric:tabular-nums">${val}</strong>
              </div>`
            })
            .join('')
          return `<div style="font-weight:800;margin-bottom:6px">${params[0].axisValue}</div>${rows}`
        },
      },
      legend: { show: false },
      grid: { left: 62, right: 62, top: 48, bottom: 40 },
      xAxis: {
        type: 'category',
        data: labels,
        boundaryGap: true,
        axisLabel: {
          color: '#475569',
          fontSize: 14,
          fontWeight: 700,
          margin: 12,
        },
        axisLine: { lineStyle: { color: '#cbd5e1', width: 1.5 } },
        axisTick: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: '本',
          min: 0,
          max: qtyAxisMax,
          nameTextStyle: { color: CHART_THEME.qtyBot, fontSize: 13, fontWeight: 700, padding: [0, 0, 0, 8] },
          splitLine: {
            lineStyle: { color: CHART_THEME.grid, type: [4, 6] },
          },
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: {
            color: CHART_THEME.qtyBot,
            fontSize: 12,
            fontWeight: 600,
            formatter: (v: number) => (v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)),
          },
        },
        {
          type: 'value',
          name: '%',
          min: -1,
          max: rateAxisMax,
          nameTextStyle: { color: CHART_THEME.rateNew, fontSize: 13, fontWeight: 700, padding: [0, 8, 0, 0] },
          splitLine: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: {
            color: CHART_THEME.rateOld,
            fontSize: 12,
            fontWeight: 600,
            formatter: '{value}%',
          },
        },
      ],
      series: [
        {
          name: '廃棄本数',
          type: 'bar',
          yAxisIndex: 0,
          barMaxWidth: 42,
          z: 2,
          data: qtyValues.map((value, i) => ({
            value,
            itemStyle: {
              borderRadius: [10, 10, 4, 4],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: i === lastIdx ? CHART_THEME.qtyCurrentTop : CHART_THEME.qtyTop },
                { offset: 0.45, color: i === lastIdx ? CHART_THEME.qtyMid : '#fb923c' },
                { offset: 1, color: i === lastIdx ? CHART_THEME.qtyCurrentBot : CHART_THEME.qtyBot },
              ]),
              shadowColor: i === lastIdx ? 'rgba(194, 65, 12, 0.45)' : 'rgba(249, 115, 22, 0.28)',
              shadowBlur: i === lastIdx ? 18 : 10,
              shadowOffsetY: i === lastIdx ? 8 : 4,
              shadowOffsetX: 2,
            },
          })),
          label: {
            show: true,
            position: 'insideBottom',
            distance: 6,
            fontSize: 13,
            fontWeight: 800,
            color: '#fff7ed',
            textShadowColor: 'rgba(124, 45, 18, 0.55)',
            textShadowBlur: 4,
            formatter: ({ value }: { value: number | null }) =>
              value == null ? '' : Number(value).toLocaleString(),
          },
          labelLayout: { hideOverlap: true },
          emphasis: {
            focus: 'series',
            itemStyle: {
              shadowBlur: 22,
              shadowColor: 'rgba(194, 65, 12, 0.5)',
            },
          },
          animationDelay: (idx: number) => idx * 70,
        },
        {
          name: '廃棄率（新）',
          type: 'line',
          yAxisIndex: 1,
          smooth: 0.35,
          showSymbol: true,
          symbol: 'diamond',
          symbolSize: 12,
          z: 5,
          lineStyle: {
            width: 3.5,
            type: 'solid',
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: CHART_THEME.rateNewSoft },
              { offset: 1, color: CHART_THEME.rateNew },
            ]),
            shadowColor: 'rgba(124, 58, 237, 0.45)',
            shadowBlur: 12,
            shadowOffsetY: 5,
          },
          itemStyle: {
            color: CHART_THEME.rateNew,
            borderColor: '#fff',
            borderWidth: 2.5,
            shadowColor: 'rgba(124, 58, 237, 0.5)',
            shadowBlur: 8,
          },
          label: {
            show: true,
            position: 'top',
            distance: 12,
            fontSize: 13,
            fontWeight: 800,
            color: CHART_THEME.rateNew,
            backgroundColor: 'rgba(237, 233, 254, 0.92)',
            borderRadius: 6,
            padding: [3, 6],
            formatter: ({ value }: { value: number | null }) =>
              value == null ? '' : `${Number(value).toFixed(2)}%`,
          },
          labelLayout: { hideOverlap: true },
          emphasis: {
            focus: 'series',
            scale: 1.35,
            itemStyle: { borderWidth: 3 },
          },
          data: rateNewValues,
          animationDelay: 280,
        },
        {
          name: '廃棄率（旧）',
          type: 'line',
          yAxisIndex: 1,
          smooth: 0.35,
          showSymbol: true,
          symbol: 'circle',
          symbolSize: 11,
          z: 4,
          lineStyle: {
            width: 3.5,
            type: [8, 6],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: CHART_THEME.rateOldSoft },
              { offset: 1, color: CHART_THEME.rateOld },
            ]),
            shadowColor: 'rgba(225, 29, 72, 0.4)',
            shadowBlur: 12,
            shadowOffsetY: 5,
          },
          itemStyle: {
            color: '#fff',
            borderColor: CHART_THEME.rateOld,
            borderWidth: 3,
            shadowColor: 'rgba(225, 29, 72, 0.45)',
            shadowBlur: 8,
          },
          label: {
            show: true,
            position: 'bottom',
            distance: 10,
            fontSize: 13,
            fontWeight: 800,
            color: CHART_THEME.rateOld,
            backgroundColor: 'rgba(255, 228, 230, 0.92)',
            borderRadius: 6,
            padding: [3, 6],
            formatter: ({ value }: { value: number | null }) =>
              value == null ? '' : `${Number(value).toFixed(2)}%`,
          },
          labelLayout: { hideOverlap: true },
          emphasis: {
            focus: 'series',
            scale: 1.35,
          },
          data: rateOldValues,
          animationDelay: 360,
        },
      ],
    },
    true,
  )
  scrapChart.resize()
}

function scheduleScrapChart() {
  if (activeTab.value === 'part01') {
    nextTick(() => renderScrapChart())
  }
}

function onWindowResize() {
  scrapChart?.resize()
  effTrendChart?.resize()
}

async function loadSavedList() {
  const res = await fetchSavedMonths()
  savedMonths.value = res.data || []
}

function ensureCommentArrays(data: ProductionReviewData) {
  data.part01.performance.comments ||= []
  data.part01.scrap.comments ||= []
  data.part01.inventory.comments ||= []
  data.part02.load_plan.comments ||= []
  data.part02.inventory_forecast.comments ||= []
  data.part03.load_plan.comments ||= []
  if (data.part03.inventory_forecast) {
    data.part03.inventory_forecast.comments ||= []
  }
}

async function loadMeeting(month: string) {
  if (!month) return
  loading.value = true
  try {
    const res = await fetchMeeting(month)
    const data = res.data.data
    ensureCommentArrays(data)
    payload.value = data
    syncPart03PrevFromPart02Forecast()
    syncInvWorkdayDraft()
    recordStatus.value = res.data.status || 'draft'
    dataSource.value = res.source
    scheduleScrapChart()
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '読込に失敗しました')
  } finally {
    loading.value = false
  }
}

function onMonthChange() {
  if (targetMonth.value) loadMeeting(targetMonth.value)
}

function selectMonth(month: string) {
  targetMonth.value = month
  loadMeeting(month)
}

async function onRecalculate() {
  if (!targetMonth.value) return
  try {
    await ElMessageBox.confirm(
      '最新データから数値を再集計します。手入力した実績・在庫などの数値は上書きされます（コメントと負荷の手改計画は保持）。よろしいですか？',
      '再計算',
      { type: 'warning', confirmButtonText: '再計算', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  await runRecalculate()
}

async function runRecalculate(options?: { silent?: boolean }) {
  if (!targetMonth.value) return
  loading.value = true
  try {
    const res = await recalculateMeeting(targetMonth.value)
    ensureCommentArrays(res.data)
    payload.value = res.data
    syncInvWorkdayDraft()
    dataSource.value = 'computed'
    await reapplyInventoryAsOfDates()
    scheduleScrapChart()
    if (!options?.silent) {
      ElMessage.success('数値を再計算しました')
    }
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '再計算に失敗しました')
  } finally {
    loading.value = false
  }
}

async function reapplyInventoryAsOfDates() {
  const inv = payload.value?.part01?.inventory
  if (inv?.curr_inventory_as_of && /^\d{4}-\d{2}-\d{2}$/.test(inv.curr_inventory_as_of)) {
    try {
      await applyInventoryQtyByDate(inv, inv.curr_inventory_as_of, 'curr_inventory_th')
      refreshInventoryProductLevel()
    } catch {
      /* 基準日再適用失敗時は月末在庫のまま表示 */
    }
  }
  // part02 のみ基準日再適用。part03 前月在庫は part02 予測在庫から同期する
  const fc = forecastInvSection('part02')
  if (fc?.prev_inventory_as_of && /^\d{4}-\d{2}-\d{2}$/.test(fc.prev_inventory_as_of)) {
    try {
      await applyInventoryQtyByDate(fc, fc.prev_inventory_as_of, 'prev_inventory_th')
    } catch {
      /* ignore */
    }
  }
  syncPart03PrevFromPart02Forecast()
}

async function onDeleteSaved(month: string) {
  if (!month) return
  try {
    await ElMessageBox.confirm(
      `${month} の保存データを削除し、最新データから再集計します。よろしいですか？`,
      '保存データ削除',
      { type: 'warning', confirmButtonText: '削除して再生成', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  deletingMonth.value = month
  try {
    const res = await deleteMeeting(month)
    await loadSavedList()
    if (targetMonth.value === month) {
      recordStatus.value = ''
      await loadMeeting(month)
    }
    ElMessage.success(res.message || '削除しました')
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '削除に失敗しました')
  } finally {
    deletingMonth.value = ''
  }
}

async function onSave(status: 'draft' | 'final') {
  if (!targetMonth.value || !payload.value) return
  loading.value = true
  try {
    const res = await saveMeeting(targetMonth.value, { status, data: payload.value })
    recordStatus.value = res.data.status
    dataSource.value = 'saved'
    await loadSavedList()
    ElMessage.success(res.message || '保存しました')
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '保存に失敗しました')
  } finally {
    loading.value = false
  }
}

async function onDownloadPpt() {
  if (!targetMonth.value || !payload.value) return
  pptLoading.value = true
  try {
    // 画面表示中の数値・コメント・廃棄期間をそのまま PPT に渡す
    const snapshot = JSON.parse(JSON.stringify(payload.value)) as ProductionReviewData
    const meta = scrapMeta.value
    if (snapshot.part01?.scrap) {
      const s = snapshot.part01.scrap
      s.monthly = meta.monthly
      s.fiscal_year_label = meta.fiscalLabel
      s.range_label = meta.rangeLabel
      s.avg_rate_new_current_fy_pct = Number(meta.avgRateNew)
      s.avg_rate_old_current_fy_pct = Number(meta.avgRateOld)
      s.avg_loss_current_fy_qty = meta.monthly.length
        ? Math.round(meta.monthly.reduce((sum, m) => sum + scrapLossQty(m), 0) / meta.monthly.length)
        : 0
      s.current_month_rate_new_pct = Number(meta.currentRateNew)
      s.current_month_rate_old_pct = Number(meta.currentRateOld)
      const last = meta.monthly[meta.monthly.length - 1]
      if (last) {
        s.current_month_loss_qty = scrapLossQty(last)
      }
    }
    for (const row of snapshot.part01?.performance?.rows || []) {
      if (row.key === 'shipping') {
        row.productivity_delta = null
      } else {
        row.productivity_delta = calcProdDelta(row)
      }
    }
    await downloadMeetingPptx(targetMonth.value, snapshot)
    ElMessage.success('PPTをダウンロードしました')
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || 'PPT生成に失敗しました')
  } finally {
    pptLoading.value = false
  }
}

function buildScrapPptPayload() {
  const meta = scrapMeta.value
  const base = payload.value?.part01?.scrap
  return {
    ...(base ? JSON.parse(JSON.stringify(base)) : {}),
    monthly: meta.monthly,
    fiscal_year_label: meta.fiscalLabel,
    range_label: meta.rangeLabel,
    comments: payload.value?.part01?.scrap?.comments || [],
    avg_rate_new_current_fy_pct: Number(meta.avgRateNew),
    avg_rate_old_current_fy_pct: Number(meta.avgRateOld),
    avg_rate_new_prev_fy_pct: Number(payload.value?.part01?.scrap?.avg_rate_new_prev_fy_pct ?? 0),
    avg_rate_old_prev_fy_pct: Number(
      payload.value?.part01?.scrap?.avg_rate_old_prev_fy_pct ??
        payload.value?.part01?.scrap?.avg_rate_prev_fy_pct ??
        0,
    ),
    avg_loss_current_fy_qty: meta.monthly.length
      ? Math.round(meta.monthly.reduce((sum, m) => sum + scrapLossQty(m), 0) / meta.monthly.length)
      : 0,
    current_month_rate_new_pct: Number(meta.currentRateNew),
    current_month_rate_old_pct: Number(meta.currentRateOld),
    current_month_loss_qty: meta.monthly.length
      ? scrapLossQty(meta.monthly[meta.monthly.length - 1])
      : 0,
  }
}

async function onDownloadScrapPpt() {
  if (!targetMonth.value || !payload.value) return
  scrapPptLoading.value = true
  try {
    if (activeTab.value !== 'part01') {
      activeTab.value = 'part01'
      await nextTick()
    }
    renderScrapChart()
    await nextTick()
    // チャート描画完了を少し待つ
    await new Promise((r) => setTimeout(r, 120))
    const chartImage =
      scrapChart && scrapMeta.value.monthly.length
        ? scrapChart.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff7ed',
          })
        : null
    await downloadScrapPptx(targetMonth.value, {
      scrap: buildScrapPptPayload(),
      chart_image_base64: chartImage,
      meeting_label:
        payload.value.meta?.meeting_month_label ||
        payload.value.part01?.scrap?.fiscal_year_label ||
        targetMonth.value,
    })
    ElMessage.success('廃棄PPTをダウンロードしました')
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '廃棄PPT生成に失敗しました')
  } finally {
    scrapPptLoading.value = false
  }
}

async function openCapacityDialog() {
  capacityVisible.value = true
  try {
    const res = await fetchCapacity()
    capacityRows.value = (res.data || []).map((r) => ({
      ...r,
      utilization_rate_pct: normalizeUtilizationRatePct(r.utilization_rate_pct),
      plan_adjust_rate_pct: normalizePlanAdjustRatePct(r.plan_adjust_rate_pct),
    }))
  } catch {
    ElMessage.error('工程能力の読込に失敗しました')
  }
}

async function saveCapacity() {
  capacitySaving.value = true
  try {
    await saveCapacityApi(capacityRows.value)
    ElMessage.success('工程能力を保存しました')
    capacityVisible.value = false
    if (targetMonth.value) await runRecalculate()
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    capacitySaving.value = false
  }
}

function resolveLoadCapacityMonth(part: 'part02' | 'part03'): string {
  const fromPayload = payload.value?.[part]?.load_plan?.month
  if (fromPayload && /^\d{4}-\d{2}$/.test(fromPayload)) return fromPayload
  if (!targetMonth.value || !/^\d{4}-\d{2}$/.test(targetMonth.value)) return ''
  return part === 'part03' ? shiftYm(targetMonth.value, 1) : targetMonth.value
}

function buildLoadCapacityDraftFromApi(
  rows: CapacityRow[],
  part: 'part02' | 'part03',
): CapacityRow[] {
  const byCd = Object.fromEntries(rows.map((r) => [r.process_cd, r]))
  const fromPayload = payload.value?.[part]?.load_plan?.rows ?? []
  const payloadByCd = Object.fromEntries(fromPayload.map((r) => [r.process_cd, r]))
  const monthWd = Number(payload.value?.[part]?.load_plan?.working_days) || 0

  return LOAD_CAPACITY_PROCESS_CDS.map((cd, idx) => {
    const saved = byCd[cd]
    if (saved) {
      return {
        ...saved,
        working_days: Number(saved.working_days) > 0 ? Number(saved.working_days) : monthWd,
        utilization_rate_pct: normalizeUtilizationRatePct(saved.utilization_rate_pct),
        plan_adjust_rate_pct: normalizePlanAdjustRatePct(saved.plan_adjust_rate_pct),
      }
    }
    const fromRow = payloadByCd[cd]
    return {
      process_cd: cd,
      process_name: fromRow?.process_name || LOAD_CAPACITY_DEFAULT_NAMES[cd] || cd,
      equipment_label: fromRow?.equipment_label || '',
      standard_rate: Number(fromRow?.standard_rate) || 0,
      shift_label: fromRow?.shift_label || '',
      working_days: Number(fromRow?.working_days) || monthWd,
      utilization_rate_pct: normalizeUtilizationRatePct(fromRow?.utilization_rate_pct),
      plan_adjust_rate_pct: normalizePlanAdjustRatePct(fromRow?.plan_adjust_rate_pct),
      daily_regular_hours: 8,
      sort_order: idx + 1,
    }
  })
}

async function openLoadCapacityDialog(part: 'part02' | 'part03' = 'part02') {
  const month = resolveLoadCapacityMonth(part)
  if (!month) {
    ElMessage.warning('対象月がありません。再計算してから設定してください')
    return
  }
  loadCapacityPart.value = part
  loadCapacityMonth.value = month
  loadCapacityVisible.value = true
  try {
    const res = await fetchCapacity(month)
    loadCapacitySource.value = (res.source as 'monthly' | 'default') || 'default'
    loadCapacityRows.value = buildLoadCapacityDraftFromApi(res.data || [], part)
  } catch {
    ElMessage.error('設備・能率・直の読込に失敗しました')
  }
}

async function saveLoadCapacity() {
  if (!loadCapacityMonth.value) {
    ElMessage.warning('対象月がありません')
    return
  }
  loadCapacitySaving.value = true
  try {
    await saveCapacityApi(loadCapacityRows.value, loadCapacityMonth.value)
    ElMessage.success(`${loadCapacityMonthLabel.value} の設備・能率・直を保存しました`)
    loadCapacityVisible.value = false
    loadCapacitySource.value = 'monthly'
    if (targetMonth.value) await runRecalculate()
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    loadCapacitySaving.value = false
  }
}

function syncInvWorkdayDraft() {
  const inv = payload.value?.part01?.inventory
  invWorkdayDraft.value = {
    prev: Number(inv?.prev_workdays ?? 0),
    curr: Number(inv?.curr_workdays ?? 0),
  }
}

function parseJpMonthLabel(label?: string): { year: number; month: number } | null {
  const m = (label || '').match(/(\d{4})年(\d{1,2})月/)
  if (!m) return null
  return { year: Number(m[1]), month: Number(m[2]) }
}

function inventoryForecastMonths(): Array<{ year: number; month: number; days: number }> {
  const inv = payload.value?.part01?.inventory
  if (!inv) return []
  const prev =
    inv.prev_forecast_year && inv.prev_forecast_month
      ? { year: Number(inv.prev_forecast_year), month: Number(inv.prev_forecast_month) }
      : parseJpMonthLabel(inv.prev_forecast_label)
  const curr =
    inv.curr_forecast_year && inv.curr_forecast_month
      ? { year: Number(inv.curr_forecast_year), month: Number(inv.curr_forecast_month) }
      : parseJpMonthLabel(inv.curr_forecast_label)
  const items: Array<{ year: number; month: number; days: number }> = []
  if (prev) {
    items.push({
      year: prev.year,
      month: prev.month,
      days: Math.max(0, Math.min(31, Number(invWorkdayDraft.value.prev) || 0)),
    })
  }
  if (curr) {
    items.push({
      year: curr.year,
      month: curr.month,
      days: Math.max(0, Math.min(31, Number(invWorkdayDraft.value.curr) || 0)),
    })
  }
  return items
}

async function saveInventoryWorkingDays() {
  const items = inventoryForecastMonths()
  if (!items.length) {
    ElMessage.warning('対象月がありません。再計算してから入力してください')
    return
  }
  wdSaving.value = true
  try {
    await saveWorkingDays(
      items.map((it) => ({ year: it.year, month: it.month, working_days: it.days })),
    )
    ElMessage.success('稼働日を保存しました')
    if (targetMonth.value) await runRecalculate()
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '稼働日の保存に失敗しました')
  } finally {
    wdSaving.value = false
  }
}

async function loadWorkingDaysYear() {
  try {
    const res = await fetchWorkingDays(wdDialogYear.value)
    wdDialogRows.value = (res.data?.items || []).map((r) => ({ ...r }))
  } catch {
    ElMessage.error('稼働日の読込に失敗しました')
  }
}

async function openWorkingDaysDialog() {
  const inv = payload.value?.part01?.inventory
  wdDialogYear.value = Number(inv?.curr_forecast_year || inv?.prev_forecast_year || new Date().getFullYear())
  wdDialogVisible.value = true
  await loadWorkingDaysYear()
}

async function saveWorkingDaysDialog() {
  if (!wdDialogRows.value.length) return
  wdSaving.value = true
  try {
    await saveWorkingDays(
      wdDialogRows.value.map((r) => ({
        year: r.year,
        month: r.month,
        working_days: Math.max(0, Math.min(31, Number(r.working_days) || 0)),
      })),
    )
    ElMessage.success('稼働日を保存しました')
    wdDialogVisible.value = false
    if (targetMonth.value) await runRecalculate()
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '稼働日の保存に失敗しました')
  } finally {
    wdSaving.value = false
  }
}

onMounted(async () => {
  targetMonth.value = defaultMonth()
  await loadSavedList()
  await loadMeeting(targetMonth.value)
  window.addEventListener('resize', onWindowResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  disposeScrapChart()
  disposeEffTrendChart()
})

watch(
  () => [payload.value?.part01?.scrap, activeTab.value, scrapRangeFrom.value, scrapRangeTo.value] as const,
  () => scheduleScrapChart(),
  { deep: true },
)
</script>

<style scoped>
.pr-page {
  position: relative;
  padding: 16px 20px 40px;
  min-height: 100%;
  overflow-x: hidden;
}

.pr-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(145deg, #f0f4ff 0%, #f8fafc 35%, #eef2ff 70%, #fdf4ff 100%);
}

.pr-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.55;
  animation: pr-float 18s ease-in-out infinite;
}
.pr-orb--1 {
  width: 320px;
  height: 320px;
  top: -80px;
  right: 8%;
  background: radial-gradient(circle, #93c5fd 0%, transparent 70%);
}
.pr-orb--2 {
  width: 280px;
  height: 280px;
  bottom: 10%;
  left: -60px;
  background: radial-gradient(circle, #c4b5fd 0%, transparent 70%);
  animation-delay: -6s;
}
.pr-orb--3 {
  width: 240px;
  height: 240px;
  top: 40%;
  right: -40px;
  background: radial-gradient(circle, #fdba74 0%, transparent 70%);
  animation-delay: -12s;
}

@keyframes pr-float {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(0, -18px, 0) scale(1.05);
  }
}

@keyframes pr-fade-up {
  from {
    opacity: 0;
    transform: translate3d(0, 20px, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.pr-animate-in {
  animation: pr-fade-up 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.pr-glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow:
    0 1px 2px rgb(15 23 42 / 4%),
    0 12px 32px rgb(15 23 42 / 8%),
    inset 0 1px 0 rgb(255 255 255 / 80%);
}

.pr-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 20px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px 14px 16px;
  border-radius: 18px;
  margin-bottom: 12px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.88) 55%, rgba(239, 246, 255, 0.9) 100%);
  border: 1px solid rgba(191, 219, 254, 0.55);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 90%) inset,
    0 -1px 0 rgb(148 163 184 / 8%) inset,
    0 10px 28px rgb(15 23 42 / 8%),
    0 2px 6px rgb(37 99 235 / 6%);
  overflow: hidden;
}
.pr-toolbar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #3b82f6, #0ea5e9 45%, #6366f1);
  box-shadow: 2px 0 10px rgb(59 130 246 / 25%);
}

.pr-brand {
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 0;
}
.pr-brand__icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: linear-gradient(145deg, #60a5fa 0%, #2563eb 48%, #1d4ed8 100%);
  color: #fff;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 45%) inset,
    0 8px 18px rgb(37 99 235 / 38%),
    0 2px 4px rgb(30 64 175 / 25%);
  flex-shrink: 0;
}
.pr-brand__icon::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: 13px;
  border: 1px solid rgb(255 255 255 / 28%);
  pointer-events: none;
}
.pr-brand__text {
  min-width: 0;
}
.pr-brand h1 {
  margin: 0;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: #0f172a;
  line-height: 1.2;
  text-shadow: 0 1px 0 rgb(255 255 255 / 80%);
}
.pr-brand p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 5px 0 0;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  line-height: 1.2;
}
.pr-brand__badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: linear-gradient(180deg, #eff6ff, #dbeafe);
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 800;
  box-shadow: 0 1px 2px rgb(37 99 235 / 10%);
}
.pr-brand__sep {
  color: #cbd5e1;
  font-weight: 400;
}

.pr-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  flex: 1 1 auto;
  justify-content: center;
  min-width: 0;
}
.pr-controls__panel {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 6px 8px 6px 6px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgb(255 255 255 / 95%), rgb(248 250 252 / 92%));
  border: 1px solid rgb(226 232 240 / 95%);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 90%) inset,
    0 4px 12px rgb(15 23 42 / 6%);
}
.pr-month {
  width: 158px;
}
.pr-month :deep(.el-input__wrapper) {
  min-height: 34px;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow:
    0 0 0 1px #cbd5e1 inset,
    0 2px 4px rgb(15 23 42 / 4%) !important;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.pr-month :deep(.el-input__wrapper:hover),
.pr-month :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px #60a5fa inset,
    0 0 0 3px rgb(59 130 246 / 15%),
    0 2px 6px rgb(37 99 235 / 10%) !important;
}
.pr-month :deep(.el-input__inner) {
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.pr-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.01em;
  line-height: 1;
  border: 1px solid transparent;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 35%) inset,
    0 3px 8px rgb(15 23 42 / 10%);
}
.pr-status__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgb(255 255 255 / 45%);
}
.pr-status--draft {
  background: linear-gradient(180deg, #64748b, #475569);
  color: #fff;
  border-color: #334155;
}
.pr-status--draft .pr-status__dot {
  background: #fbbf24;
  box-shadow: 0 0 0 2px rgb(255 255 255 / 25%), 0 0 8px rgb(251 191 36 / 70%);
}
.pr-status--final {
  background: linear-gradient(180deg, #34d399, #059669);
  color: #fff;
  border-color: #047857;
}
.pr-status--final .pr-status__dot {
  background: #ecfdf5;
}
.pr-status--live {
  background: linear-gradient(180deg, #eff6ff, #dbeafe);
  color: #1d4ed8;
  border-color: #93c5fd;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 3px 8px rgb(37 99 235 / 12%);
}
.pr-status--live .pr-status__dot {
  background: #3b82f6;
  box-shadow: 0 0 0 2px rgb(219 234 254), 0 0 8px rgb(59 130 246 / 55%);
}
.pr-status--saved {
  background: linear-gradient(180deg, #fff7ed, #ffedd5);
  color: #c2410c;
  border-color: #fdba74;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 3px 8px rgb(234 88 12 / 12%);
}
.pr-status--saved .pr-status__dot {
  background: #f97316;
}

.pr-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}
.pr-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    filter 0.18s ease,
    background 0.18s ease;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 40%) inset,
    0 4px 10px rgb(15 23 42 / 10%);
}
.pr-action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.03);
}
.pr-action-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 25%) inset,
    0 2px 4px rgb(15 23 42 / 12%);
}
.pr-action-btn:disabled {
  opacity: 0.48;
  cursor: not-allowed;
  transform: none;
  filter: grayscale(0.15);
}
.pr-action-btn .el-icon {
  font-size: 14px;
}
.pr-action-btn--ghost {
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  color: #334155;
  border-color: #cbd5e1;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 90%) inset,
    0 3px 8px rgb(15 23 42 / 7%);
}
.pr-action-btn--ghost:hover:not(:disabled) {
  border-color: #94a3b8;
  color: #0f172a;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 95%) inset,
    0 6px 14px rgb(15 23 42 / 10%);
}
.pr-action-btn--refresh:hover:not(:disabled) {
  border-color: #93c5fd;
  color: #1d4ed8;
  background: linear-gradient(180deg, #eff6ff, #e0f2fe);
}
.pr-action-btn--warn {
  background: linear-gradient(180deg, #fb923c 0%, #f97316 45%, #ea580c 100%);
  color: #fff;
  border-color: #c2410c;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 35%) inset,
    0 6px 14px rgb(234 88 12 / 32%),
    0 2px 4px rgb(154 52 18 / 18%);
}
.pr-action-btn--warn:hover:not(:disabled) {
  box-shadow:
    0 1px 0 rgb(255 255 255 / 40%) inset,
    0 8px 18px rgb(234 88 12 / 40%);
}
.pr-action-btn--primary {
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 42%, #2563eb 100%);
  color: #fff;
  border-color: #1d4ed8;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 35%) inset,
    0 6px 14px rgb(37 99 235 / 34%),
    0 2px 4px rgb(30 64 175 / 18%);
}
.pr-action-btn--primary:hover:not(:disabled) {
  box-shadow:
    0 1px 0 rgb(255 255 255 / 40%) inset,
    0 8px 18px rgb(37 99 235 / 42%);
}
.pr-action-btn--success {
  background: linear-gradient(180deg, #4ade80 0%, #22c55e 42%, #16a34a 100%);
  color: #fff;
  border-color: #15803d;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 35%) inset,
    0 6px 14px rgb(22 163 74 / 32%),
    0 2px 4px rgb(21 128 61 / 18%);
}
.pr-action-btn--success:hover:not(:disabled) {
  box-shadow:
    0 1px 0 rgb(255 255 255 / 40%) inset,
    0 8px 18px rgb(22 163 74 / 40%);
}

.pr-saved {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 10px 14px;
  border-radius: 14px;
  margin-bottom: 12px;
}
.pr-saved__label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}
.pr-saved__chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: 1px solid #cbd5e1;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 999px;
  padding: 2px 4px 2px 10px;
  font-size: 12px;
  transition: all 0.25s ease;
  box-shadow: 0 2px 6px rgb(15 23 42 / 6%);
}
.pr-saved__chip-main {
  border: none;
  background: transparent;
  padding: 3px 4px;
  font: inherit;
  color: inherit;
  cursor: pointer;
}
.pr-saved__chip-del {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
}
.pr-saved__chip-del:hover:not(:disabled) {
  background: #fee2e2;
  color: #dc2626;
}
.pr-saved__chip-del:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pr-saved__chip:hover {
  transform: translateY(-1px);
  border-color: #93c5fd;
}
.pr-saved__chip.active {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff, #e0e7ff);
  color: #1d4ed8;
  box-shadow: 0 4px 12px rgb(59 130 246 / 20%);
}
.pr-saved__chip.final.active {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  color: #047857;
}

.pr-empty {
  position: relative;
  z-index: 1;
}

.pr-body {
  border-radius: 18px;
  overflow: hidden;
}

.pr-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 12px 16px 0;
  background: linear-gradient(180deg, rgb(248 250 252 / 90%), transparent);
}
.pr-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}
.pr-tabs :deep(.el-tabs__item) {
  height: 42px;
  padding: 0 18px;
  font-weight: 600;
  color: #64748b;
  transition: color 0.2s;
}
.pr-tabs :deep(.el-tabs__item.is-active) {
  color: #0f172a;
}
.pr-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}
.pr-tabs :deep(.el-tabs__content) {
  padding: 8px 16px 20px;
}

.pr-tab-label--blue::before,
.pr-tab-label--violet::before,
.pr-tab-label--rose::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}
.pr-tab-label--blue::before {
  background: #3b82f6;
}
.pr-tab-label--violet::before {
  background: #8b5cf6;
}
.pr-tab-label--rose::before {
  background: #f43f5e;
}

.pr-card {
  position: relative;
  margin-bottom: 18px;
  padding: 18px 18px 14px;
  border-radius: 16px;
  background: linear-gradient(160deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgb(226 232 240 / 80%);
  box-shadow:
    0 1px 2px rgb(15 23 42 / 4%),
    0 10px 28px rgb(15 23 42 / 7%);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  animation: pr-fade-up 0.5s ease both;
}
.pr-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 2px 4px rgb(15 23 42 / 5%),
    0 16px 36px rgb(15 23 42 / 10%);
}
.pr-card--blue {
  border-top: 3px solid #3b82f6;
}
.pr-card--performance .pr-card__head h2 {
  font-size: 18px;
}
.pr-card__head--performance {
  align-items: center;
  flex-wrap: wrap;
}
.pr-col-toggles {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}
.pr-col-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.22s ease;
  box-shadow: 0 1px 3px rgb(15 23 42 / 6%);
}
.pr-col-toggle:hover {
  border-color: #93c5fd;
  color: #1d4ed8;
  transform: translateY(-1px);
}
.pr-col-toggle.is-on {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #1e40af;
  box-shadow: 0 4px 12px rgb(59 130 246 / 18%);
}
.pr-col-toggle__indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  transition: background 0.22s ease, box-shadow 0.22s ease;
}
.pr-col-toggle.is-on .pr-col-toggle__indicator {
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 25%);
}
.pr-eff-trend-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid #a5b4fc;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  color: #4338ca;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  box-shadow:
    0 1px 0 rgb(255 255 255 / 80%) inset,
    0 4px 12px rgb(79 70 229 / 16%);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.pr-eff-trend-btn:hover {
  transform: translateY(-1px);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 90%) inset,
    0 6px 16px rgb(79 70 229 / 22%);
}
.pr-card--orange {
  border-top: 3px solid #f97316;
  animation-delay: 0.06s;
}
.pr-card--teal {
  border-top: 3px solid #14b8a6;
  animation-delay: 0.12s;
}
.pr-card--violet {
  border-top: 3px solid #8b5cf6;
}
.pr-card--load-plan {
  animation-delay: 0.04s;
}
.pr-card--load-plan .pr-card__head h2 {
  font-size: 18px;
}
.pr-load-summary-line {
  margin: 0;
  margin-left: auto;
  font-size: 14px;
  color: #475569;
  font-weight: 600;
  line-height: 1.4;
  text-align: right;
}
.pr-load-summary-line strong {
  color: #1d4ed8;
  font-size: 16px;
  font-weight: 800;
  margin: 0 2px;
}
.pr-load-wd-input {
  width: 52px;
  border: 1px solid #93c5fd;
  border-radius: 8px;
  padding: 4px 6px;
  font-size: 15px;
  font-weight: 800;
  text-align: center;
  color: #1e40af;
  background: #fff;
  margin: 0 4px;
}
.pr-load-wd-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 18%);
}
.pr-load-cap-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}
.pr-col-toggle--load {
  padding: 6px 12px;
  font-size: 11px;
}
.pr-load-cap-val {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
}
.pr-load-cap-val--num {
  font-variant-numeric: tabular-nums;
  color: #1d4ed8;
  font-weight: 800;
}

.pr-shift-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  border: 1px solid transparent;
  box-shadow: 0 1px 2px rgb(15 23 42 / 6%);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.pr-shift-badge--1 {
  color: #0369a1;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  border-color: #7dd3fc;
  box-shadow: 0 2px 6px rgb(14 165 233 / 16%);
}
.pr-shift-badge--2 {
  color: #1d4ed8;
  background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
  border-color: #60a5fa;
  box-shadow: 0 2px 8px rgb(37 99 235 / 18%);
}
.pr-shift-badge--3 {
  color: #6d28d9;
  background: linear-gradient(135deg, #ede9fe 0%, #c4b5fd 100%);
  border-color: #a78bfa;
  box-shadow: 0 2px 8px rgb(109 40 217 / 18%);
}
.pr-shift-badge--empty {
  color: #94a3b8;
  background: #f1f5f9;
  border-color: #e2e8f0;
  font-weight: 600;
}
.pr-load-cap-dialog__hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}
.pr-load-cap-dialog__formula {
  display: inline-block;
  margin-top: 4px;
  font-size: 12px;
  color: #475569;
}
.pr-load-cap-dialog__table {
  width: 100%;
}

/* ── 設備・能率・直・稼働日設定ダイアログ ── */
.pr-dialog--load-cap :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgb(15 23 42 / 18%);
}
.pr-dialog--load-cap :deep(.el-dialog__header) {
  margin: 0;
  padding: 0;
}
.pr-dialog--load-cap :deep(.el-dialog__body) {
  padding: 10px 14px 8px;
}
.pr-dialog--load-cap :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.pr-dialog--eff-trend :deep(.el-dialog) {
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 40%);
  box-shadow: 0 24px 64px rgb(15 23 42 / 22%);
}
.pr-dialog--eff-trend :deep(.el-dialog__header) {
  margin: 0;
  padding: 0;
}
.pr-dialog--eff-trend :deep(.el-dialog__body) {
  padding: 0;
}
.pr-eff-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px;
  background: linear-gradient(135deg, #312e81 0%, #4338ca 45%, #6366f1 100%);
  color: #fff;
}
.pr-eff-header__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.pr-eff-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: rgb(255 255 255 / 16%);
  box-shadow: 0 1px 0 rgb(255 255 255 / 25%) inset;
}
.pr-eff-header__title {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.pr-eff-header__sub {
  margin: 3px 0 0;
  font-size: 11px;
  opacity: 0.82;
  font-weight: 600;
}
.pr-eff-header__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 999px;
  background: rgb(255 255 255 / 14%);
  color: #fff;
  cursor: pointer;
}
.pr-eff-header__close:hover {
  background: rgb(255 255 255 / 24%);
}
.pr-eff-body {
  padding: 14px 16px 18px;
  min-height: 420px;
}
.pr-eff-filters {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}
.pr-eff-filters__range {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 14px;
  background: linear-gradient(180deg, #fff, #f8fafc);
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 0 #fff inset, 0 4px 12px rgb(15 23 42 / 5%);
}
.pr-eff-filters__label {
  font-size: 11px;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.04em;
}
.pr-eff-filters__tilde {
  color: #94a3b8;
  font-weight: 700;
}
.pr-eff-month {
  width: 140px;
}
.pr-eff-filters__procs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pr-eff-proc-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.18s ease;
  opacity: 0.55;
}
.pr-eff-proc-chip__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}
.pr-eff-proc-chip.is-on {
  opacity: 1;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgb(15 23 42 / 10%);
}
.pr-eff-proc-chip--cutting.is-on {
  color: #1d4ed8;
  border-color: #93c5fd;
  background: linear-gradient(180deg, #eff6ff, #dbeafe);
}
.pr-eff-proc-chip--molding.is-on {
  color: #6d28d9;
  border-color: #c4b5fd;
  background: linear-gradient(180deg, #f5f3ff, #ede9fe);
}
.pr-eff-proc-chip--plating.is-on {
  color: #0e7490;
  border-color: #67e8f9;
  background: linear-gradient(180deg, #ecfeff, #cffafe);
}
.pr-eff-proc-chip--welding.is-on {
  color: #c2410c;
  border-color: #fdba74;
  background: linear-gradient(180deg, #fff7ed, #ffedd5);
}
.pr-eff-proc-chip--inspection.is-on {
  color: #047857;
  border-color: #6ee7b7;
  background: linear-gradient(180deg, #ecfdf5, #d1fae5);
}
.pr-eff-chart-card {
  position: relative;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow: 0 8px 24px rgb(15 23 42 / 6%);
  padding: 10px 10px 6px;
  overflow: hidden;
}
.pr-eff-chart-card__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 2px 8px 6px;
  font-size: 12px;
  font-weight: 800;
  color: #334155;
}
.pr-eff-chart-card__hint {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
}
.pr-eff-chart {
  width: 100%;
  height: 340px;
}
.pr-eff-latest {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.pr-eff-latest__card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 2px 8px rgb(15 23 42 / 5%);
}
.pr-eff-latest__name {
  font-size: 11px;
  font-weight: 800;
  color: #64748b;
}
.pr-eff-latest__val {
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
}
.pr-eff-latest__val small {
  margin-left: 2px;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
}
.pr-eff-latest__month {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
}
.pr-eff-latest__card--cutting {
  border-left: 3px solid #2563eb;
}
.pr-eff-latest__card--molding {
  border-left: 3px solid #7c3aed;
}
.pr-eff-latest__card--plating {
  border-left: 3px solid #0891b2;
}
.pr-eff-latest__card--welding {
  border-left: 3px solid #ea580c;
}
.pr-eff-latest__card--inspection {
  border-left: 3px solid #059669;
}

.pr-lcap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #1d4ed8 0%, #4f46e5 55%, #6366f1 100%);
  color: #fff;
}
.pr-lcap-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.pr-lcap-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgb(255 255 255 / 18%);
  flex-shrink: 0;
}
.pr-lcap-header__title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1.25;
}
.pr-lcap-header__sub {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgb(255 255 255 / 82%);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.pr-lcap-header__month {
  font-weight: 800;
  color: #fff;
}
.pr-lcap-header__badge {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  background: rgb(255 255 255 / 20%);
  color: #fff;
}
.pr-lcap-header__badge--saved {
  background: rgb(52 211 153 / 35%);
}
.pr-lcap-header__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgb(255 255 255 / 14%);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.pr-lcap-header__close:hover {
  background: rgb(255 255 255 / 28%);
}

.pr-lcap-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pr-lcap-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.pr-lcap-legend__chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.pr-lcap-legend__chip--equip {
  background: #dbeafe;
  color: #1d4ed8;
}
.pr-lcap-legend__chip--rate {
  background: #ede9fe;
  color: #6d28d9;
}
.pr-lcap-legend__chip--shift {
  background: #fce7f3;
  color: #be185d;
}
.pr-lcap-legend__chip--wd {
  background: #ecfdf5;
  color: #047857;
}
.pr-lcap-legend__chip--util {
  background: #ffedd5;
  color: #c2410c;
}
.pr-lcap-legend__chip--adj {
  background: #e0e7ff;
  color: #3730a3;
}

.pr-lcap-formula {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 6px;
  padding: 6px 10px;
  border-radius: 8px;
  background: linear-gradient(90deg, #f8fafc, #f1f5f9);
  border: 1px solid #e2e8f0;
  font-size: 10px;
  font-weight: 600;
  color: #475569;
  line-height: 1.35;
}
.pr-lcap-formula__dot {
  color: #cbd5e1;
  font-weight: 400;
}

.pr-lcap-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-height: min(52vh, 420px);
  overflow-y: auto;
  padding-right: 2px;
}
.pr-lcap-list::-webkit-scrollbar {
  width: 4px;
}
.pr-lcap-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.pr-lcap-card {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 8px;
  align-items: center;
  padding: 6px 8px 6px 6px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.pr-lcap-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgb(15 23 42 / 6%);
}
.pr-lcap-card__proc {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 800;
  color: #0f172a;
  text-align: center;
  line-height: 1.2;
}
.pr-lcap-card__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}
.pr-lcap-card__grid {
  display: grid;
  grid-template-columns: 1.2fr 0.7fr 0.55fr 0.6fr 0.7fr 0.85fr;
  gap: 6px;
  min-width: 0;
}
.pr-lcap-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.pr-lcap-field__label {
  font-size: 9px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  line-height: 1;
}
.pr-lcap-field :deep(.el-input__wrapper) {
  padding: 0 6px;
  min-height: 28px;
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.pr-lcap-field :deep(.el-input__inner) {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
}
.pr-lcap-field__num {
  width: 100%;
}
.pr-lcap-field__num :deep(.el-input__wrapper) {
  padding: 0 6px;
  min-height: 28px;
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.pr-lcap-field__num :deep(.el-input__inner) {
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: left;
}

.pr-lcap-card--cutting {
  border-left: 3px solid #3b82f6;
}
.pr-lcap-card--cutting .pr-lcap-card__dot {
  background: #3b82f6;
}
.pr-lcap-card--chamfering {
  border-left: 3px solid #6366f1;
}
.pr-lcap-card--chamfering .pr-lcap-card__dot {
  background: #6366f1;
}
.pr-lcap-card--molding {
  border-left: 3px solid #8b5cf6;
}
.pr-lcap-card--molding .pr-lcap-card__dot {
  background: #8b5cf6;
}
.pr-lcap-card--plating {
  border-left: 3px solid #a855f7;
}
.pr-lcap-card--plating .pr-lcap-card__dot {
  background: #a855f7;
}
.pr-lcap-card--inspection {
  border-left: 3px solid #d946ef;
}
.pr-lcap-card--inspection .pr-lcap-card__dot {
  background: #d946ef;
}
.pr-lcap-card--welding {
  border-left: 3px solid #ec4899;
}
.pr-lcap-card--welding .pr-lcap-card__dot {
  background: #ec4899;
}

.pr-lcap-tip {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  margin: 0;
  padding: 6px 8px;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  font-size: 10px;
  color: #92400e;
  line-height: 1.4;
}
.pr-lcap-tip .el-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.pr-lcap-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.pr-lcap-footer .el-button--primary {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  border: none;
  font-weight: 700;
  padding-left: 16px;
  padding-right: 18px;
}
.pr-lcap-footer .el-button--primary:hover {
  background: linear-gradient(135deg, #1d4ed8, #4338ca);
}

@media (max-width: 640px) {
  .pr-lcap-card {
    grid-template-columns: 1fr;
    gap: 6px;
  }
  .pr-lcap-card__proc {
    flex-direction: row;
    justify-content: flex-start;
    text-align: left;
  }
  .pr-lcap-card__grid {
    grid-template-columns: 1fr 1fr;
  }
}

.pr-kpi-grid--load {
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.pr-load-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.pr-load-help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: linear-gradient(180deg, #eff6ff, #ffffff);
  color: #2563eb;
  cursor: pointer;
  box-shadow: 0 2px 8px rgb(59 130 246 / 12%);
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
.pr-load-help-btn:hover {
  transform: translateY(-1px);
  background: #dbeafe;
  box-shadow: 0 4px 12px rgb(59 130 246 / 18%);
}

.pr-table--load :deep(.el-table__header th) {
  background: linear-gradient(180deg, #dbeafe 0%, #eff6ff 100%) !important;
  color: #1e3a8a;
  font-size: 13px;
  font-weight: 800;
  padding: 12px 8px !important;
}
.pr-table--load :deep(.el-table__body td) {
  padding: 10px 8px !important;
  font-size: 13px;
}
.pr-table--load :deep(.el-table__body td:first-child) {
  font-weight: 800;
  color: #0f172a;
  text-align: left;
}
.pr-load-row--cutting :deep(td:first-child) {
  border-left: 3px solid #3b82f6;
}
.pr-load-row--chamfering :deep(td:first-child) {
  border-left: 3px solid #6366f1;
}
.pr-load-row--molding :deep(td:first-child) {
  border-left: 3px solid #8b5cf6;
}
.pr-load-row--plating :deep(td:first-child) {
  border-left: 3px solid #a855f7;
}
.pr-load-row--inspection :deep(td:first-child) {
  border-left: 3px solid #d946ef;
}
.pr-load-row--welding :deep(td:first-child) {
  border-left: 3px solid #f43f5e;
}

.pr-load-rate {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.pr-load-rate--overload {
  background: linear-gradient(135deg, #fecaca, #fee2e2);
  color: #b91c1c;
  box-shadow: 0 2px 8px rgb(220 38 38 / 18%);
}
.pr-load-rate--tight {
  background: linear-gradient(135deg, #fed7aa, #ffedd5);
  color: #c2410c;
  box-shadow: 0 2px 8px rgb(249 115 22 / 15%);
}
.pr-load-rate--ok {
  background: linear-gradient(135deg, #bfdbfe, #dbeafe);
  color: #1d4ed8;
}
.pr-load-rate--light {
  background: linear-gradient(135deg, #a7f3d0, #d1fae5);
  color: #047857;
}

.pr-load-edit-input {
  width: 100%;
  min-width: 52px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 5px 7px;
  font-size: 12px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.pr-load-edit-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 14%);
}
.pr-load-edit-input--num {
  min-width: 48px;
  text-align: center;
  font-weight: 700;
}
.pr-load-edit-input--short {
  min-width: 40px;
  text-align: center;
}
.pr-load-edit-input--wide {
  min-width: 100px;
}

.pr-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.pr-card__head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}
.pr-card__sub {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
}
.pr-card__head--scrap {
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 16px;
}
.pr-scrap-head-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
  margin-left: auto;
}
.pr-scrap-range {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff7ed, #ffffff);
  border: 1px solid #fed7aa;
  box-shadow: 0 2px 8px rgb(249 115 22 / 10%);
}
.pr-scrap-range__label {
  font-size: 12px;
  font-weight: 800;
  color: #c2410c;
  margin-right: 2px;
}
.pr-scrap-range__tilde {
  font-size: 13px;
  font-weight: 700;
  color: #9a3412;
}
.pr-scrap-range__select {
  width: 88px;
}
.pr-scrap-range__select :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #fdba74 inset;
}

.pr-range-badge {
  display: inline-block;
  margin: 0 4px;
  padding: 2px 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  color: #c2410c;
  font-weight: 600;
  font-size: 11px;
}

.pr-sub {
  margin: 0 0 10px;
  font-size: 12px;
  color: #64748b;
}

.pr-table-wrap {
  overflow-x: auto;
  border-radius: 10px;
}
.pr-table-wrap--performance {
  border-radius: 14px;
  border: 1px solid #bfdbfe;
  background: #fff;
  box-shadow:
    0 4px 24px rgb(59 130 246 / 12%),
    inset 0 1px 0 rgb(255 255 255 / 90%);
}
.pr-table {
  width: 100%;
}
.pr-table--performance {
  --el-table-border-color: #dbeafe;
}
.pr-table--performance :deep(.el-table__header th) {
  background: linear-gradient(180deg, #dbeafe 0%, #eff6ff 100%) !important;
  color: #1e3a8a;
  font-size: 15px;
  font-weight: 800;
  padding: 16px 12px !important;
  text-align: center;
  letter-spacing: 0.02em;
}
.pr-table--performance :deep(.el-table__header th:first-child) {
  text-align: left;
}
.pr-table--performance :deep(.el-table__body td) {
  padding: 18px 12px !important;
  font-size: 16px;
  text-align: center;
  color: #1e293b;
  transition: background 0.2s ease;
}
.pr-table--performance :deep(.el-table__body td:first-child) {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  text-align: left;
  background: linear-gradient(90deg, rgb(248 250 252 / 95%), transparent);
  border-right: 1px solid #e0e7ff !important;
}
.pr-table--performance :deep(.el-table__row--striped td.el-table__cell) {
  background: #f8faff;
}
.pr-table--performance :deep(.el-table__row--striped td.el-table__cell:first-child) {
  background: linear-gradient(90deg, #f1f5f9, #f8faff);
}
.pr-table--performance :deep(.el-table__row:hover > td.el-table__cell) {
  background: #eff6ff !important;
}
.pr-table--performance :deep(.el-table__fixed-column--left) {
  box-shadow: 4px 0 12px rgb(59 130 246 / 8%);
}
.pr-perf-actual {
  display: inline-block;
  min-width: 52px;
  font-size: 17px;
  font-weight: 800;
  color: #1d4ed8;
  letter-spacing: 0.02em;
}
.pr-perf-prod {
  display: inline-block;
  min-width: 48px;
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  color: #4338ca;
}
.pr-perf-reg {
  display: inline-block;
  min-width: 48px;
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  color: #0d9488;
}
.pr-table--load :deep(.el-table__body td .pr-perf-reg),
.pr-table--load :deep(.el-table__body td .pr-perf-prod) {
  font-size: 16px !important;
  font-weight: 700 !important;
}
.pr-perf-val {
  display: inline-block;
  min-width: 52px;
  font-size: 16px;
  font-weight: 700;
  color: #334155;
}
.pr-perf-val--cap {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  color: #6d28d9;
  font-weight: 800;
}
.pr-perf-val--util {
  font-size: 15px;
  font-variant-numeric: tabular-nums;
  color: #0f766e;
  font-weight: 800;
}
.pr-perf-val--muted {
  color: #94a3b8;
  font-weight: 600;
}
.pr-perf-val--editable {
  padding: 2px 6px;
  border-radius: 6px;
  cursor: text;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}
.pr-perf-val--editable:hover {
  background: rgb(37 99 235 / 6%);
  box-shadow: inset 0 0 0 1px rgb(59 130 246 / 30%);
}
.pr-perf-edit-input {
  width: 88px;
  padding: 4px 6px;
  border: 1px solid #60a5fa;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 800;
  text-align: center;
  color: #1e3a8a;
  outline: none;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 18%);
}
.pr-perf-edit-input--prod {
  width: 72px;
}
.pr-perf-muted {
  font-size: 16px;
  color: #94a3b8;
  font-weight: 600;
}
.pr-table--performance .pr-delta {
  font-size: 15px;
  padding: 4px 10px;
}
.pr-card--inventory {
  padding-top: 14px;
  padding-bottom: 14px;
}
.pr-card--inventory .pr-card__head h2 {
  font-size: 17px;
  margin: 0;
}
.pr-inv-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.pr-inv-help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid #99f6e4;
  border-radius: 999px;
  background: linear-gradient(180deg, #f0fdfa, #ffffff);
  color: #0d9488;
  cursor: pointer;
  box-shadow: 0 2px 8px rgb(20 184 166 / 12%);
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
.pr-inv-help-btn:hover {
  transform: translateY(-1px);
  background: #ccfbf1;
  box-shadow: 0 4px 12px rgb(20 184 166 / 18%);
}
.pr-inv-col-hdr--clickable {
  cursor: pointer;
  user-select: none;
  border-bottom: 1px dashed transparent;
}
.pr-inv-col-hdr--clickable:hover {
  color: #0f766e;
  border-bottom-color: #5eead4;
}
.pr-inv-date-dialog__hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}
.pr-inv-name-cell {
  display: flex;
  flex-direction: column;
  gap: 1px;
  line-height: 1.2;
  padding: 0;
}
.pr-inv-name-cell__name {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}
.pr-inv-name-cell__std {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}
.pr-card__head--inventory {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-bottom: 10px;
}
.pr-inv-forecast-line {
  margin: 0;
  margin-left: auto;
  font-size: 13px;
  color: #475569;
  font-weight: 600;
  line-height: 1.35;
  text-align: right;
}
.pr-inv-forecast-line strong {
  color: #0f766e;
  font-size: 15px;
  font-weight: 800;
  margin: 0 2px;
}
.pr-inv-forecast-line__wd {
  color: #0d9488 !important;
}
.pr-inv-forecast-sep {
  margin: 0 8px;
  color: #94a3b8;
  font-weight: 500;
}
.pr-inv-wd__actions {
  display: flex;
  flex-wrap: wrap;
  flex-shrink: 0;
  gap: 8px;
  margin-left: 4px;
}
.pr-inv-kpi {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0 0 10px;
}
.pr-inv-kpi__card {
  position: relative;
  padding: 8px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #f0fdfa, #ffffff);
  border: 1px solid #99f6e4;
  box-shadow: 0 3px 10px rgb(20 184 166 / 8%);
}
.pr-inv-kpi__card--product.is-danger {
  border-color: #fca5a5;
  background: linear-gradient(180deg, #fef2f2, #ffffff);
  box-shadow: 0 4px 14px rgb(220 38 38 / 10%);
}
.pr-inv-kpi__card--product.is-ok {
  border-color: #6ee7b7;
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
}
.pr-inv-kpi__card--product.is-high {
  border-color: #fcd34d;
  background: linear-gradient(180deg, #fffbeb, #ffffff);
  box-shadow: 0 4px 14px rgb(245 158 11 / 10%);
}
.pr-inv-kpi__label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}
.pr-inv-kpi__value {
  margin: 2px 0 2px;
  font-size: 24px;
  font-weight: 800;
  color: #0f766e;
  line-height: 1.15;
}
.pr-inv-kpi__value small {
  margin-left: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}
.pr-inv-kpi__hint {
  font-size: 11px;
  color: #94a3b8;
}
.pr-inv-wd__input {
  width: 72px;
  padding: 6px 8px;
  border: 1px solid #5eead4;
  border-radius: 8px;
  text-align: center;
  font-size: 15px;
  font-weight: 800;
  color: #0f766e;
  outline: none;
}
.pr-inv-wd__input:focus {
  box-shadow: 0 0 0 3px rgb(20 184 166 / 18%);
}
.pr-wd-dialog__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  font-size: 13px;
  color: #475569;
}
.pr-wd-dialog__hint {
  flex: 1 1 220px;
  font-size: 12px;
  color: #94a3b8;
}
.pr-wd-dialog__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.pr-wd-dialog__cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}
.pr-wd-dialog__cell .pr-inv-wd__input {
  width: 100%;
}
.pr-wd-dialog__cell small.is-saved {
  color: #0d9488;
}
.pr-wd-dialog__cell small.is-est {
  color: #94a3b8;
}
.pr-inv-kpi__badge {
  display: inline-block;
  margin-top: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.is-danger .pr-inv-kpi__badge {
  color: #b91c1c;
  background: #fee2e2;
}
.is-ok .pr-inv-kpi__badge {
  color: #047857;
  background: #d1fae5;
}
.is-high .pr-inv-kpi__badge {
  color: #b45309;
  background: #fef3c7;
}
.pr-inv-rate--raw {
  opacity: 0.72;
  font-weight: 600;
}
.pr-inv-rate--adj {
  font-weight: 800;
}
.pr-inv-days {
  display: inline-block;
  font-size: 17px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f766e;
  line-height: 1.2;
}
.pr-inv-days small {
  margin-left: 1px;
  font-size: 12px;
  font-weight: 700;
}
.pr-inv-rate--adj.is-danger,
.pr-inv-days.is-danger {
  color: #dc2626;
}
.pr-inv-rate--adj.is-ok,
.pr-inv-days.is-ok {
  color: #047857;
}
.pr-inv-rate--adj.is-high,
.pr-inv-days.is-high {
  color: #d97706;
}
.pr-inv-val--parent {
  font-weight: 800;
  opacity: 0.95;
}
.pr-table--inventory :deep(.pr-inv-row--parent > td.el-table__cell) {
  background: #e6fffa !important;
  font-weight: 700;
}
.pr-table--inventory :deep(.pr-inv-row--child > td.el-table__cell) {
  background: #f8fffd !important;
}
.pr-table--inventory :deep(.el-table__expand-icon) {
  color: #0d9488;
  font-size: 14px;
}
.pr-table--inventory :deep(.pr-inv-row--product.is-danger > td.el-table__cell) {
  background: #fef2f2 !important;
}
.pr-table--inventory :deep(.pr-inv-row--product.is-ok > td.el-table__cell) {
  background: #ecfdf5 !important;
}
.pr-table--inventory :deep(.pr-inv-row--product.is-high > td.el-table__cell) {
  background: #fffbeb !important;
}
.pr-table-wrap--inventory {
  border-color: #99f6e4;
  box-shadow:
    0 4px 18px rgb(20 184 166 / 10%),
    inset 0 1px 0 rgb(255 255 255 / 90%);
}
.pr-table--inventory {
  --el-table-border-color: #ccfbf1;
}
.pr-table--performance.pr-table--inventory :deep(.el-table__header th) {
  background: linear-gradient(180deg, #ccfbf1 0%, #f0fdfa 100%) !important;
  color: #115e59;
  font-size: 13px !important;
  font-weight: 800;
  padding: 8px 6px !important;
  letter-spacing: 0.01em;
  line-height: 1.25;
}
.pr-table--performance.pr-table--inventory :deep(.el-table__body td) {
  padding: 7px 6px !important;
  font-size: 15px;
  line-height: 1.2;
}
.pr-table--performance.pr-table--inventory :deep(.el-table__body td:first-child) {
  border-right: 1px solid #99f6e4 !important;
  padding-left: 8px !important;
  font-size: 15px;
}
.pr-table--inventory :deep(.el-table__row--striped td.el-table__cell) {
  background: #f0fdfa;
}
.pr-table--inventory :deep(.el-table__row--striped td.el-table__cell:first-child) {
  background: linear-gradient(90deg, #ecfdf5, #f0fdfa);
}
.pr-table--inventory :deep(.el-table__row:hover > td.el-table__cell) {
  background: #ccfbf1 !important;
}
.pr-table--inventory :deep(.el-table__fixed-column--left) {
  box-shadow: 4px 0 12px rgb(20 184 166 / 8%);
}
.pr-table--inventory :deep(.el-table__placeholder),
.pr-table--inventory :deep(.el-table__indent) {
  width: 12px !important;
  padding-left: 0 !important;
}
.pr-inv-val {
  display: inline-block;
  font-weight: 800;
  font-size: 18px;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.01em;
  line-height: 1.15;
}
.pr-inv-val--prev {
  color: #475569;
  font-size: 17px;
}
.pr-inv-val--curr {
  color: #0d9488;
  font-size: 19px;
}
.pr-inv-val--editable {
  display: inline-block;
  min-width: 3.6em;
  padding: 1px 4px;
  border-radius: 6px;
  cursor: text;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}
.pr-inv-val--editable:hover {
  background: rgb(15 23 42 / 4%);
  box-shadow: inset 0 0 0 1px rgb(20 184 166 / 28%);
}
.pr-inv-edit-input {
  width: 84px;
  padding: 3px 5px;
  border: 1px solid #5eead4;
  border-radius: 7px;
  font-size: 17px;
  font-weight: 800;
  text-align: center;
  outline: none;
  box-shadow: 0 0 0 3px rgb(20 184 166 / 18%);
}
.pr-inv-edit-input--prev {
  color: #475569;
  border-color: #94a3b8;
  box-shadow: 0 0 0 3px rgb(148 163 184 / 22%);
}
.pr-inv-edit-input--curr {
  color: #0f766e;
}
.pr-inv-rate {
  display: inline-block;
  font-weight: 800;
  font-size: 17px;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
}
.pr-inv-rate--prev {
  color: #475569;
  font-size: 16px;
}
.pr-inv-rate--curr {
  color: #0f766e;
  font-size: 18px;
  font-weight: 800;
}
.pr-table--inventory .pr-delta {
  font-size: 16px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  padding: 2px 8px;
}
.pr-table--inventory :deep(.col-prev) {
  background: rgb(248 250 252 / 55%) !important;
}
.pr-table--inventory :deep(.col-curr) {
  background: rgb(240 253 250 / 70%) !important;
}
.pr-table--inventory :deep(.el-table__header th.col-prev) {
  background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 100%) !important;
  color: #475569;
}
.pr-table--inventory :deep(.el-table__header th.col-curr) {
  background: linear-gradient(180deg, #99f6e4 0%, #ccfbf1 100%) !important;
  color: #115e59;
}
.pr-table--inventory :deep(.el-table__row--striped .col-prev) {
  background: rgb(241 245 249 / 80%) !important;
}
.pr-table--inventory :deep(.el-table__row--striped .col-curr) {
  background: rgb(204 251 241 / 55%) !important;
}
.pr-inv-comment-btn {
  --el-button-bg-color: #0d9488;
  --el-button-border-color: #0d9488;
  --el-button-hover-bg-color: #0f766e;
  --el-button-hover-border-color: #0f766e;
}
.pr-table--modern :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  color: #334155;
  font-weight: 700;
}
.pr-table--modern :deep(.el-table__row:hover > td) {
  background: #f0f9ff !important;
}

.pr-num {
  width: 88px;
}
.pr-num-wide {
  width: 100px;
}

.pr-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.pr-kpi {
  position: relative;
  padding: 14px 16px;
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  box-shadow: 0 6px 18px rgb(15 23 42 / 8%);
}
.pr-kpi:hover {
  transform: translateY(-3px) scale(1.01);
}
.pr-kpi::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.12;
  background: radial-gradient(circle at top right, #fff, transparent 60%);
}
.pr-kpi__label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  opacity: 0.9;
  margin-bottom: 6px;
}
.pr-kpi__value {
  display: block;
  font-size: 22px;
  font-weight: 800;
  line-height: 1.1;
}
.pr-kpi__value--name {
  font-size: 20px;
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pr-kpi__value small {
  font-size: 13px;
  font-weight: 600;
  margin-left: 2px;
}
.pr-kpi__hint {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  opacity: 0.85;
}
.pr-kpi--indigo {
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #fff;
}
.pr-kpi--blue {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #fff;
}
.pr-kpi--slate {
  background: linear-gradient(135deg, #475569, #64748b);
  color: #fff;
}
.pr-kpi--green {
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
}
.pr-kpi--red {
  background: linear-gradient(135deg, #dc2626, #f87171);
  color: #fff;
}
.pr-kpi--violet {
  background: linear-gradient(135deg, #6d28d9, #8b5cf6);
  color: #fff;
}
.pr-kpi--rose {
  background: linear-gradient(135deg, #be123c, #f43f5e);
  color: #fff;
}
.pr-kpi--orange {
  background: linear-gradient(135deg, #c2410c, #f97316);
  color: #fff;
}
.pr-kpi-grid--scrap {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.pr-scrap-formula {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  font-size: 12px;
  color: #7c2d12;
  line-height: 1.5;
}
.pr-scrap-formula__sep {
  color: #fdba74;
}
.pr-scrap-formula__tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
}
.pr-scrap-formula__tag--new {
  background: #ede9fe;
  color: #6d28d9;
}
.pr-scrap-formula__tag--old {
  background: #ffe4e6;
  color: #be123c;
}
.pr-scrap-formula__tag--qty {
  background: #ffedd5;
  color: #c2410c;
}

.pr-monthly-grid--scrap {
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
}
.pr-month-card--scrap {
  gap: 6px;
}
.pr-month-card__rate-new {
  font-size: 14px;
  font-weight: 800;
  color: #7c3aed;
}
.pr-month-card__rate-old {
  font-size: 13px;
  font-weight: 700;
  color: #e11d48;
}
.pr-month-card__loss {
  font-size: 15px;
  font-weight: 800;
  color: #ea580c;
}
.pr-month-card__rate-new small,
.pr-month-card__rate-old small,
.pr-month-card__loss small {
  font-size: 10px;
  font-weight: 600;
  margin-left: 1px;
}

.pr-scrap-table-wrap {
  margin-top: 14px;
  margin-bottom: 14px;
}
.pr-table--scrap :deep(.el-table__body td) {
  font-size: 14px;
}
.pr-scrap-val {
  font-weight: 800;
  font-size: 14px;
}
.pr-scrap-val--new {
  color: #6d28d9;
}
.pr-scrap-val--old {
  color: #be123c;
}
.pr-scrap-val--qty {
  color: #c2410c;
}

.pr-chart-panel {
  position: relative;
  padding: 14px 12px 10px;
  margin-bottom: 14px;
  border-radius: 16px;
  background:
    radial-gradient(ellipse at top right, rgba(249, 115, 22, 0.08), transparent 45%),
    radial-gradient(ellipse at bottom left, rgba(124, 58, 237, 0.06), transparent 40%),
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  box-shadow:
    0 1px 2px rgb(15 23 42 / 4%),
    0 12px 28px rgb(15 23 42 / 7%),
    inset 0 1px 0 rgb(255 255 255 / 90%);
  overflow: hidden;
}
.pr-chart-panel::before {
  content: '';
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #f97316, #7c3aed, #e11d48);
  opacity: 0.85;
}
.pr-chart-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  padding: 0 4px;
}
.pr-chart-panel__title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pr-chart-panel__title strong {
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}
.pr-chart-panel__badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  color: #c2410c;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
}
.pr-chart-panel__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.pr-chart-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgb(15 23 42 / 5%);
}
.pr-chart-chip i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}
.pr-chart-chip--qty {
  color: #c2410c;
  border-color: #fdba74;
  background: linear-gradient(135deg, #fff7ed, #ffffff);
}
.pr-chart-chip--qty i {
  background: linear-gradient(180deg, #fdba74, #c2410c);
  box-shadow: 0 2px 4px rgb(194 65 12 / 35%);
}
.pr-chart-chip--new {
  color: #6d28d9;
  border-color: #c4b5fd;
  background: linear-gradient(135deg, #f5f3ff, #ffffff);
}
.pr-chart-chip--new i {
  width: 12px;
  height: 3px;
  border-radius: 2px;
  background: #7c3aed;
  box-shadow: 0 2px 4px rgb(124 58 237 / 35%);
}
.pr-chart-chip--old {
  color: #be123c;
  border-color: #fda4af;
  background: linear-gradient(135deg, #fff1f2, #ffffff);
}
.pr-chart-chip--old i {
  width: 12px;
  height: 3px;
  border-radius: 2px;
  background: repeating-linear-gradient(90deg, #e11d48 0 4px, transparent 4px 7px);
  box-shadow: 0 0 0 1px rgb(225 29 72 / 20%);
}
.pr-chart {
  width: 100%;
  height: clamp(280px, 40vw, 380px);
}

.pr-monthly-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(108px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.pr-month-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 10px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  text-align: center;
  transition: all 0.25s ease;
  box-shadow: 0 2px 8px rgb(15 23 42 / 5%);
}
.pr-month-card:hover {
  transform: translateY(-2px);
  border-color: #fdba74;
}
.pr-month-card--current {
  border-color: #f97316;
  background: linear-gradient(160deg, #fff7ed, #ffffff);
  box-shadow: 0 6px 16px rgb(249 115 22 / 18%);
}
.pr-month-card__label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}
.pr-month-card__scrap {
  font-size: 16px;
  font-weight: 800;
  color: #ea580c;
}
.pr-month-card__scrap small {
  font-size: 10px;
  font-weight: 600;
  margin-left: 2px;
}
.pr-month-card__rate {
  font-size: 12px;
  font-weight: 600;
  color: #6366f1;
}

.pr-delta {
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 12px;
}
.pr-delta--pos {
  color: #047857;
  background: #d1fae5;
}
.pr-delta--neg {
  color: #b91c1c;
  background: #fee2e2;
}
.pr-delta--zero {
  color: #64748b;
  background: #f1f5f9;
}

.pr-perf-comment {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px dashed #bfdbfe;
}
.pr-perf-comment__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.pr-perf-comment__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.pr-comments__head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pr-perf-comment__title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.pr-perf-comment__title strong {
  display: block;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}
.pr-perf-comment__title span {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
}
.pr-perf-comment__icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #2563eb;
  line-height: 1;
}
.pr-perf-comment__icon::before {
  content: '';
  position: absolute;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid currentColor;
  opacity: 0.22;
  transform: scale(1.15);
  pointer-events: none;
}
.pr-perf-comment__icon::after {
  content: '';
  position: absolute;
  right: -2px;
  bottom: -1px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.55;
  box-shadow: 0 0 0 2px #fff;
  pointer-events: none;
}
.pr-perf-comment__icon .el-icon {
  position: relative;
  z-index: 1;
}
.pr-perf-comment--scrap {
  border-top-color: #fdba74;
}
.pr-perf-comment--scrap .pr-perf-comment__icon {
  color: #ea580c;
}
.pr-perf-comment--scrap .pr-perf-comment__bullet {
  color: #ea580c;
}
.pr-perf-comment--scrap .pr-perf-comment__line {
  border-color: #ffedd5;
  box-shadow: 0 4px 14px rgb(249 115 22 / 8%);
}
.pr-perf-comment--scrap .pr-perf-comment__line:hover {
  box-shadow: 0 8px 20px rgb(249 115 22 / 14%);
}
.pr-perf-comment--inventory {
  border-top-color: #99f6e4;
}
.pr-perf-comment--inventory .pr-perf-comment__icon {
  color: #0d9488;
}
.pr-perf-comment--inventory .pr-perf-comment__bullet {
  color: #0d9488;
}
.pr-perf-comment--inventory .pr-perf-comment__line {
  border-color: #ccfbf1;
  box-shadow: 0 4px 14px rgb(20 184 166 / 8%);
}
.pr-perf-comment--inventory .pr-perf-comment__line:hover {
  box-shadow: 0 8px 20px rgb(20 184 166 / 14%);
}
.pr-perf-comment__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pr-perf-comment__line {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e0e7ff;
  box-shadow: 0 4px 14px rgb(59 130 246 / 8%);
  animation: pr-fade-up 0.45s ease both;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.pr-perf-comment__line:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgb(59 130 246 / 12%);
}
.pr-perf-comment__line--compact {
  padding: 10px 12px;
  animation: none;
}
.pr-perf-comment__bullet {
  flex-shrink: 0;
  margin-top: 2px;
  font-size: 13px;
  font-weight: 800;
  color: #3b82f6;
}
.pr-perf-comment__text {
  margin: 0;
  font-size: 15px;
  line-height: 1.75;
  color: #334155;
  word-break: break-word;
}
.seg-text {
  color: #1e293b;
  font-weight: 500;
}
.seg-num {
  font-weight: 800;
  font-size: 16px;
  padding: 0 2px;
  letter-spacing: 0.02em;
}
.seg-num--pos {
  color: #047857;
}
.seg-num--neg {
  color: #dc2626;
}
.pr-perf-comment__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 28px 16px;
  border-radius: 14px;
  border: 1px dashed #cbd5e1;
  background: linear-gradient(180deg, #f8fafc, #ffffff);
  color: #94a3b8;
  text-align: center;
}
.pr-perf-comment__empty .el-icon {
  font-size: 22px;
}
.pr-perf-comment__empty p {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #64748b;
}
.pr-perf-comment__empty span {
  font-size: 13px;
}

.pr-comment-dialog :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgb(255 255 255 / 80%);
  box-shadow:
    0 24px 48px rgb(15 23 42 / 18%),
    0 0 0 1px rgb(59 130 246 / 8%);
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 42%);
}
.pr-comment-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 0;
  border-bottom: none;
}
.pr-comment-dialog :deep(.el-dialog__headerbtn) {
  top: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgb(255 255 255 / 20%);
  z-index: 2;
  transition: all 0.2s ease;
}
.pr-comment-dialog :deep(.el-dialog__headerbtn:hover) {
  background: rgb(255 255 255 / 35%);
}
.pr-comment-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
  font-size: 16px;
}
.pr-comment-dialog :deep(.el-dialog__body) {
  padding: 0 22px 8px;
}
.pr-comment-dialog :deep(.el-dialog__footer) {
  padding: 0;
  border-top: none;
}

.pr-comment-dialog__header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 22px 56px 18px 22px;
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 45%, #6366f1 100%);
  color: #fff;
  position: relative;
  overflow: hidden;
}
.pr-comment-dialog--scrap .pr-comment-dialog__header {
  background: linear-gradient(135deg, #c2410c 0%, #f97316 45%, #fb923c 100%);
}
.pr-comment-dialog--scrap .pr-comment-dialog__idx {
  background: linear-gradient(135deg, #f97316, #ea580c);
  box-shadow: 0 4px 10px rgb(249 115 22 / 28%);
}
.pr-comment-dialog--scrap .pr-comment-dialog__count {
  background: #fff7ed;
  color: #c2410c;
}
.pr-comment-dialog--scrap .pr-comment-dialog__hint {
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border-color: #fdba74;
}
.pr-comment-dialog--scrap .pr-comment-dialog__hint .el-icon {
  color: #ea580c;
}
.pr-comment-dialog--scrap .pr-comment-dialog__add {
  border-color: #fdba74;
  color: #c2410c;
}
.pr-comment-dialog--scrap .pr-comment-dialog__add:hover {
  border-color: #f97316;
  background: #fff7ed;
  box-shadow: 0 6px 16px rgb(249 115 22 / 14%);
}
.pr-comment-dialog--scrap .pr-comment-dialog__footer .el-button--warning {
  padding-left: 22px;
  padding-right: 22px;
  background: linear-gradient(135deg, #ea580c, #f97316);
  border: none;
  color: #fff;
  box-shadow: 0 8px 20px rgb(234 88 12 / 30%);
}
.pr-comment-dialog--scrap .pr-comment-dialog__footer .el-button--warning:hover {
  background: linear-gradient(135deg, #c2410c, #ea580c);
}
.pr-comment-dialog--scrap .pr-perf-comment__bullet {
  color: #ea580c;
}
.pr-comment-dialog--inventory .pr-comment-dialog__header {
  background: linear-gradient(135deg, #0f766e 0%, #14b8a6 45%, #2dd4bf 100%);
}
.pr-comment-dialog--inventory .pr-comment-dialog__idx {
  background: linear-gradient(135deg, #14b8a6, #0d9488);
  box-shadow: 0 4px 10px rgb(20 184 166 / 28%);
}
.pr-comment-dialog--inventory .pr-comment-dialog__count {
  background: #f0fdfa;
  color: #0f766e;
}
.pr-comment-dialog--inventory .pr-comment-dialog__hint {
  background: linear-gradient(135deg, #f0fdfa, #ccfbf1);
  border-color: #99f6e4;
}
.pr-comment-dialog--inventory .pr-comment-dialog__hint .el-icon {
  color: #0d9488;
}
.pr-comment-dialog--inventory .pr-comment-dialog__add {
  border-color: #5eead4;
  color: #0f766e;
}
.pr-comment-dialog--inventory .pr-comment-dialog__add:hover {
  border-color: #14b8a6;
  background: #f0fdfa;
  box-shadow: 0 6px 16px rgb(20 184 166 / 14%);
}
.pr-comment-dialog--inventory .pr-comment-dialog__footer .el-button--success {
  padding-left: 22px;
  padding-right: 22px;
  background: linear-gradient(135deg, #0d9488, #14b8a6);
  border: none;
  color: #fff;
  box-shadow: 0 8px 20px rgb(13 148 136 / 30%);
}
.pr-comment-dialog--inventory .pr-comment-dialog__footer .el-button--success:hover {
  background: linear-gradient(135deg, #0f766e, #0d9488);
}
.pr-comment-dialog--inventory .pr-perf-comment__bullet {
  color: #0d9488;
}
.pr-comment-dialog__header::after {
  content: '';
  position: absolute;
  top: -40px;
  right: -20px;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: rgb(255 255 255 / 12%);
}
.pr-comment-dialog__header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: rgb(255 255 255 / 18%);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 35%);
  flex-shrink: 0;
}
.pr-comment-dialog__header-text h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.pr-comment-dialog__header-text p {
  margin: 4px 0 0;
  font-size: 13px;
  opacity: 0.9;
}

.pr-comment-dialog__layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 16px;
}
.pr-comment-dialog__panel {
  display: flex;
  flex-direction: column;
  min-height: 360px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 4px 16px rgb(15 23 42 / 5%);
}
.pr-comment-dialog__panel--preview {
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border-color: #dbeafe;
}
.pr-comment-dialog__panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}
.pr-comment-dialog__panel-title {
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}
.pr-comment-dialog__count {
  padding: 3px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 800;
}
.pr-comment-dialog__hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f0f9ff, #eff6ff);
  border: 1px solid #bfdbfe;
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
}
.pr-comment-dialog__hint .el-icon {
  margin-top: 2px;
  color: #3b82f6;
  flex-shrink: 0;
}
.pr-comment-dialog__scroll {
  flex: 1;
  overflow-y: auto;
  max-height: 280px;
  padding-right: 4px;
  margin-bottom: 10px;
}
.pr-comment-dialog__scroll::-webkit-scrollbar {
  width: 6px;
}
.pr-comment-dialog__scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 999px;
}
.pr-comment-dialog__lines {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pr-comment-dialog__row {
  display: grid;
  grid-template-columns: 36px 1fr 36px;
  gap: 8px;
  align-items: stretch;
  padding: 8px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.pr-comment-dialog__row:focus-within {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 12%);
  background: #fff;
}
.pr-comment-dialog__idx-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 8px;
}
.pr-comment-dialog__idx {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  box-shadow: 0 4px 10px rgb(59 130 246 / 28%);
}
.pr-comment-dialog__input-wrap {
  min-width: 0;
}
.pr-comment-dialog__input :deep(.el-textarea__inner) {
  border: none;
  background: transparent;
  box-shadow: none !important;
  padding: 8px 4px;
  font-size: 14px;
  line-height: 1.65;
  color: #1e293b;
  resize: none;
}
.pr-comment-dialog__input :deep(.el-textarea__inner::placeholder) {
  color: #94a3b8;
}
.pr-comment-dialog__del {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin-top: 4px;
  border: none;
  border-radius: 10px;
  background: #fff;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgb(15 23 42 / 8%);
}
.pr-comment-dialog__del:hover:not(:disabled) {
  color: #dc2626;
  background: #fee2e2;
  transform: scale(1.05);
}
.pr-comment-dialog__del:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.pr-comment-dialog__add {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border: 1px dashed #93c5fd;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.22s ease;
}
.pr-comment-dialog__add:hover {
  border-color: #3b82f6;
  background: #eff6ff;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgb(59 130 246 / 14%);
}

.pr-comment-dialog__legend {
  display: flex;
  gap: 6px;
}
.pr-comment-dialog__legend-item {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
}
.pr-comment-dialog__legend-item--pos {
  background: #d1fae5;
  color: #047857;
}
.pr-comment-dialog__legend-item--neg {
  background: #fee2e2;
  color: #b91c1c;
}
.pr-comment-dialog__legend-item--text {
  background: #f1f5f9;
  color: #475569;
}

.pr-comment-dialog__preview {
  flex: 1;
  overflow-y: auto;
  max-height: 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
}
.pr-comment-dialog__preview-line {
  animation: pr-fade-up 0.35s ease both;
}
.pr-comment-dialog__preview-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 200px;
  padding: 24px;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
  background: rgb(255 255 255 / 70%);
  color: #94a3b8;
  text-align: center;
}
.pr-comment-dialog__preview-empty p {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #64748b;
}
.pr-comment-dialog__preview-empty span {
  font-size: 12px;
}

.pr-comment-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 22px 20px;
  background: linear-gradient(180deg, transparent, #f8fafc);
  border-top: 1px solid #e2e8f0;
}
.pr-comment-dialog__footer .el-button--primary {
  padding-left: 22px;
  padding-right: 22px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  border: none;
  box-shadow: 0 8px 20px rgb(37 99 235 / 30%);
}
.pr-comment-dialog__footer .el-button--primary:hover {
  background: linear-gradient(135deg, #1d4ed8, #4338ca);
}

@media (max-width: 768px) {
  .pr-comment-dialog__layout {
    grid-template-columns: 1fr;
  }
  .pr-comment-dialog__panel {
    min-height: auto;
  }
  .pr-comment-dialog__scroll {
    max-height: 220px;
  }
  .pr-comment-dialog__preview {
    max-height: 200px;
  }
  .pr-comment-dialog__footer {
    flex-direction: column-reverse;
  }
  .pr-comment-dialog__footer .el-button {
    width: 100%;
    margin: 0;
  }
}

.pr-comments {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}
.pr-comments__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}
.pr-comments__row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.pr-comments__input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.pr-comments__input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgb(99 102 241 / 15%);
}
.pr-link {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}
.pr-link.danger {
  color: #dc2626;
}

.pr-inline-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
}
.pr-inline-input {
  width: 72px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 8px;
  background: #fff;
}

.pr-native-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgb(15 23 42 / 6%);
}
.pr-native-table th,
.pr-native-table td {
  border: 1px solid #e2e8f0;
  padding: 8px 10px;
  vertical-align: middle;
}
.pr-native-table th {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
  font-weight: 700;
  color: #334155;
}
.pr-native-table tbody tr:hover td {
  background: #f8fafc;
}
.pr-cell-input {
  width: 100%;
  min-width: 56px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 4px 6px;
  font-size: 12px;
  background: #fff;
}
.pr-cell-input.num {
  min-width: 48px;
}
.pr-cell-input.wide {
  min-width: 120px;
}

@media (max-width: 768px) {
  .pr-page {
    padding: 12px 12px 28px;
  }
  .pr-toolbar {
    padding: 12px 12px 12px 14px;
  }
  .pr-brand h1 {
    font-size: 16px;
  }
  .pr-controls,
  .pr-actions {
    width: 100%;
    justify-content: flex-start;
  }
  .pr-controls__panel {
    width: 100%;
  }
  .pr-action-btn {
    flex: 1 1 auto;
  }
  .pr-tabs :deep(.el-tabs__content) {
    padding: 6px 8px 16px;
  }
  .pr-card {
    padding: 14px 12px;
  }
  .pr-col-toggles {
    width: 100%;
    justify-content: flex-start;
  }
  .pr-scrap-range {
    width: 100%;
    justify-content: flex-start;
  }
  .pr-inv-forecast-line {
    width: 100%;
    margin-left: 0;
    text-align: left;
    font-size: 13px;
  }
  .pr-inv-forecast-line strong {
    font-size: 15px;
  }
  .pr-inv-wd__actions {
    width: 100%;
    margin-left: 0;
    justify-content: flex-end;
  }
  .pr-inv-kpi {
    grid-template-columns: 1fr;
  }
  .pr-wd-dialog__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .pr-col-toggle {
    flex: 1 1 auto;
    justify-content: center;
    min-width: 0;
    font-size: 11px;
    padding: 6px 10px;
  }
  .pr-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .pr-kpi-grid--load {
    grid-template-columns: repeat(2, 1fr);
  }
  .pr-load-summary-line {
    width: 100%;
    margin-left: 0;
    text-align: left;
    font-size: 13px;
  }
  .pr-load-cap-actions {
    width: 100%;
    margin-left: 0;
    justify-content: flex-start;
  }
  .pr-monthly-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 480px) {
  .pr-kpi-grid {
    grid-template-columns: 1fr;
  }
  .pr-monthly-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

<style>
.pr-inv-help-popper.el-popover {
  padding: 14px 16px;
}
.pr-inv-help-popper .pr-inv-help h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 800;
  color: #0f766e;
}
.pr-inv-help-popper .pr-inv-help h4 + .pr-inv-help__example,
.pr-inv-help-popper .pr-inv-help ul + h4 {
  margin-top: 14px;
}
.pr-inv-help-popper .pr-inv-help ul {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  font-size: 13px;
  line-height: 1.65;
}
.pr-inv-help-popper .pr-inv-help li {
  margin-bottom: 8px;
}
.pr-inv-help-popper .pr-inv-help code {
  display: block;
  margin-top: 2px;
  padding: 4px 8px;
  border-radius: 6px;
  background: #f0fdfa;
  color: #115e59;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
}
.pr-inv-help-popper .pr-inv-help__example {
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  font-size: 12px;
  line-height: 1.7;
  color: #475569;
}
.pr-inv-help-popper .pr-inv-help__example p {
  margin: 0 0 4px;
}
.pr-inv-help-popper .pr-inv-help__example b {
  color: #0f766e;
}

.pr-load-help-popper.el-popover {
  padding: 14px 16px;
}
.pr-load-help-popper .pr-load-help h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 800;
  color: #1d4ed8;
}
.pr-load-help-popper .pr-load-help .pr-load-help__legend + h4,
.pr-load-help-popper .pr-load-help ul + h4 {
  margin-top: 14px;
}
.pr-load-help-popper .pr-load-help__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}
.pr-load-help-popper .pr-load-help__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}
.pr-load-help-popper .pr-load-formula__tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
}
.pr-load-help-popper .pr-load-formula__tag--overload {
  background: #fee2e2;
  color: #b91c1c;
}
.pr-load-help-popper .pr-load-formula__tag--tight {
  background: #ffedd5;
  color: #c2410c;
}
.pr-load-help-popper .pr-load-formula__tag--ok {
  background: #dbeafe;
  color: #1d4ed8;
}
.pr-load-help-popper .pr-load-formula__tag--light {
  background: #d1fae5;
  color: #047857;
}
.pr-load-help-popper .pr-load-help ul {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  font-size: 13px;
  line-height: 1.65;
}
.pr-load-help-popper .pr-load-help li {
  margin-bottom: 8px;
}
.pr-load-help-popper .pr-load-help code {
  display: block;
  margin-top: 2px;
  padding: 4px 8px;
  border-radius: 6px;
  background: #eff6ff;
  color: #1e40af;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
}
.pr-load-help-popper .pr-load-help__note {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
}
</style>
