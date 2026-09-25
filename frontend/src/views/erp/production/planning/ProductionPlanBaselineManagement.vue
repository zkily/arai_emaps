<template>
  <div class="plan-baseline-root">
  <div class="plan-baseline-page">
    <!-- 紧凑型页面头部（ガラス＋立体） -->
    <div class="page-header">
      <div class="page-header__orb page-header__orb--a" aria-hidden="true" />
      <div class="page-header__orb page-header__orb--b" aria-hidden="true" />
      <div class="title-wrapper">
        <div class="title-icon-wrapper">
          <el-icon class="title-icon"><TrendCharts /></el-icon>
        </div>
        <div class="title-content">
          <h2>生産計画ベースライン管理</h2>
          <p>基準計画の固定化から、変更計画・実績との差異把握までを一画面で</p>
        </div>
        <el-tooltip content="操作説明を開く" placement="bottom" :show-after="0">
          <el-icon class="help-icon help-icon--header" @click="goHelpPage" :size="18">
            <QuestionFilled />
          </el-icon>
        </el-tooltip>
      </div>
      <div class="page-header__actions">
        <el-button
          class="btn-report-modern"
          :icon="Document"
          @click="handleExportPdfToFolder"
          :loading="exportPdfLoading"
          :disabled="!canExportBaselinePdf"
          size="default"
        >
          レポート生成
        </el-button>
        <el-tooltip
          content="毎週金曜19:00に自動生成・メール添付配信。宛先は報告センター／通知設定で指定"
          placement="bottom"
          :show-after="200"
        >
          <el-button
            class="btn-report-schedule"
            text
            size="small"
            @click="goReportCenter"
          >
            定時配信
          </el-button>
        </el-tooltip>
        <el-button
          type="primary"
          class="btn-refresh-modern"
          :icon="Refresh"
          @click="loadComparison"
          :loading="tableLoading"
          size="default"
        >
          再取得
        </el-button>
      </div>
    </div>

    <!-- Zone: 操作 -->
    <section class="pb-zone pb-zone--action">
      <div class="pb-zone__label">
        <span class="pb-zone__dot" aria-hidden="true" />
        <span>生成・検索</span>
      </div>
    <el-card class="action-card" shadow="never">
      <div class="action-content">
        <div
          class="action-section generate-section"
          :class="{ 'is-locked': !generateSectionEnabled }"
        >
          <div class="action-section__glow" aria-hidden="true" />
          <div class="section-header section-header--with-toggle">
            <div class="section-header__main">
              <div class="section-icon generate-icon-bg">
                <el-icon><DocumentAdd /></el-icon>
              </div>
              <div class="section-title">
                <div class="section-title__row">
                  <h3>ベースライン生成</h3>
                  <span class="section-badge section-badge--gen">GENERATE</span>
                </div>
                <span class="section-desc">成型・溶接・溶接SPは自動集計／切断・面取・メッキ・検査はカレンダーで日付を選んで手入力</span>
              </div>
            </div>
            <div class="section-header__toggle" :class="{ 'is-on': generateSectionEnabled }">
              <span class="section-toggle-label" :class="{ 'is-on': generateSectionEnabled }">
                {{ generateSectionEnabled ? '操作可' : 'ロック中' }}
              </span>
              <el-switch
                v-model="generateSectionEnabled"
                inline-prompt
                active-text="ON"
                inactive-text="OFF"
                style="--el-switch-on-color: #0d9488"
              />
            </div>
          </div>
          <div class="section-controls" :aria-disabled="!generateSectionEnabled">
            <el-date-picker
              v-model="generateForm.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="基準月"
              size="default"
              class="pb-ctl pb-ctl--month"
              :disabled="!generateSectionEnabled"
            />
            <el-select
              v-model="generateForm.processName"
              clearable
              placeholder="全工程"
              size="default"
              class="pb-ctl pb-ctl--process"
              :disabled="!generateSectionEnabled"
            >
              <el-option
                v-for="item in processOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <div class="section-controls__actions">
              <el-button
                type="success"
                class="btn-generate-modern"
                :icon="DocumentAdd"
                @click="handleGenerate"
                :loading="generating"
                :disabled="!generateSectionEnabled"
                size="default"
              >
                生成
              </el-button>
              <el-button
                type="danger"
                class="btn-delete-modern"
                plain
                :icon="Delete"
                @click="handleDeleteBaseline"
                :loading="deleting"
                :disabled="!generateSectionEnabled"
                size="default"
              >
                削除
              </el-button>
              <el-button
                type="warning"
                class="btn-edit-modern"
                plain
                :icon="EditPen"
                @click="openAdjustmentDialog"
                :disabled="!generateSectionEnabled"
                size="default"
              >
                計画を修正
              </el-button>
            </div>
          </div>
        </div>

        <div class="action-divider" aria-hidden="true">
          <span class="action-divider__dot" />
        </div>

        <div class="action-section filter-section">
          <div class="action-section__glow" aria-hidden="true" />
          <div class="section-header">
            <div class="section-header__main">
              <div class="section-icon filter-icon-bg">
                <el-icon><Search /></el-icon>
              </div>
              <div class="section-title">
                <div class="section-title__row">
                  <h3>比較条件</h3>
                  <span class="section-badge section-badge--filter">AUTO</span>
                </div>
                <span class="section-desc">対象月・工程を変更すると自動で再取得（生成・削除後は生成条件に自動同期）</span>
              </div>
            </div>
            <div class="section-header__live">
              <span class="section-live-dot" aria-hidden="true" />
              <span>自動反映</span>
            </div>
          </div>
          <div class="section-controls">
            <el-date-picker
              v-model="compareForm.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="対象月"
              size="default"
              class="pb-ctl pb-ctl--month"
            />
            <el-select
              v-model="compareForm.processName"
              clearable
              placeholder="全工程"
              size="default"
              class="pb-ctl pb-ctl--process"
            >
              <el-option
                v-for="item in processOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <div class="section-controls__hint">
              <el-icon><Refresh /></el-icon>
              <span>条件変更で一覧・KPIを自動更新</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    </section>

    <!-- Zone: KPI -->
    <section class="pb-zone pb-zone--kpi">
      <div class="pb-zone__label">
        <span class="pb-zone__dot" aria-hidden="true" />
        <span>サマリー KPI</span>
      </div>
      <div class="summary-row">
        <div
          class="summary-card"
          v-for="(card, index) in summaryCards"
          :key="card.label"
          :class="[`summary-card--${card.tone}`, { 'is-negative': card.isNegative }]"
          :style="{ animationDelay: `${0.04 + index * 0.055}s` }"
        >
          <div class="summary-card__sheen" aria-hidden="true" />
          <div class="summary-card__glow" aria-hidden="true" />
          <div class="summary-card__ridge" aria-hidden="true" />
          <div class="summary-card-inner">
            <div class="summary-card__top">
              <span class="summary-label">{{ card.label }}</span>
              <span class="summary-card__badge" aria-hidden="true">
                <el-icon :size="13"><component :is="summaryToneIcon(card.tone)" /></el-icon>
              </span>
            </div>
            <div
              class="summary-value"
              :class="{ negative: card.isNegative, positive: !card.isNegative && card.value !== '-' }"
            >
              {{ card.value }}
            </div>
            <div v-if="card.description" class="summary-desc">{{ card.description }}</div>
          </div>
        </div>
      </div>

      <div class="period-compare-row" v-loading="periodCompareLoading">
        <div
          v-for="(block, pIdx) in periodCompareBlocks"
          :key="block.key"
          class="period-compare-card"
          :class="`period-compare-card--${block.key}`"
          :style="{ animationDelay: `${0.18 + pIdx * 0.07}s` }"
        >
          <div class="period-compare-card__glow" aria-hidden="true" />
          <div class="period-compare-card__head">
            <span class="period-compare-card__label">
              <span class="period-compare-card__chip">{{ block.label }}</span>
              <span
                v-if="block.deltaVsPrev"
                class="period-compare-card__delta period-compare-card__delta--inline"
                :class="{
                  'is-up': block.deltaVsPrev.startsWith('+'),
                  'is-down': block.deltaVsPrev.startsWith('-'),
                }"
              >
                達成率 {{ block.deltaVsPrev }}（前月比）
              </span>
            </span>
            <span class="period-compare-card__month">{{ block.monthLabel }}</span>
          </div>
          <div class="period-compare-card__metrics">
            <div class="period-compare-metric period-compare-metric--baseline">
              <span class="period-compare-metric__k">基準計画</span>
              <span class="period-compare-metric__v">{{ block.baselineText }}</span>
            </div>
            <div class="period-compare-metric period-compare-metric--rate">
              <span class="period-compare-metric__k">計画達成率</span>
              <span
                class="period-compare-metric__v"
                :class="{
                  'is-warn': block.achievementNum != null && block.achievementNum < 100,
                  'is-ok': block.achievementNum != null && block.achievementNum >= 100,
                }"
              >
                {{ block.achievementText }}
              </span>
            </div>
            <div class="period-compare-metric period-compare-metric--diff">
              <span class="period-compare-metric__k">計画対実績差</span>
              <span
                class="period-compare-metric__v"
                :class="{ 'is-neg': block.actualDiffNum != null && block.actualDiffNum < 0 }"
              >
                {{ block.actualDiffText }}
              </span>
            </div>
          </div>
          <div v-if="block.deltaVsYoy" class="period-compare-card__delta period-compare-card__delta--yoy">
            達成率 {{ block.deltaVsYoy }}（前年同月比）
          </div>
        </div>
      </div>
    </section>

    <!-- Zone: チャート -->
    <section class="pb-zone pb-zone--analytics">
      <div class="pb-zone__label">
        <span class="pb-zone__dot" aria-hidden="true" />
        <span>推移・ヒートマップ</span>
      </div>
    <div class="analytics-row">
    <el-card class="table-card trend-chart-card" shadow="never">
      <template #header>
        <div class="trend-chart-head">
          <div class="trend-chart-head__lead">
            <div class="trend-chart-head__icon-wrap">
              <el-icon class="trend-chart-head__icon"><TrendCharts /></el-icon>
            </div>
            <div class="trend-chart-head__titles">
              <span class="trend-chart-head__title">日次推移</span>
              <span class="trend-chart-head__sub">基準計画 × 実績（柱状・単位：千・小数1位／差異は柱の中央）</span>
            </div>
            <el-tag
              v-if="activeTrendProcessLabel"
              effect="plain"
              size="small"
              type="primary"
              class="trend-chart-head__tag"
            >
              {{ activeTrendProcessLabel }}
            </el-tag>
          </div>
          <div class="trend-chart-head__controls">
            <el-checkbox v-model="trendShowDiffBars" size="small">差異数値を表示</el-checkbox>
            <el-checkbox v-model="trendShowValueLabels" size="small">数量ラベル</el-checkbox>
          </div>
        </div>
      </template>
      <div class="trend-chart-body" v-loading="tableLoading">
        <div v-if="!activeTrendItems.length" class="trend-chart-empty">
          <el-empty description="比較データがありません。比較条件を変更するか、工程タブを選択してください" :image-size="64" />
        </div>
        <div v-else ref="trendChartRef" class="trend-chart-canvas" />
      </div>
    </el-card>

    <el-card class="table-card heatmap-card" shadow="never">
      <template #header>
        <div class="heatmap-head">
          <div class="heatmap-head__lead">
            <div class="heatmap-head__icon-wrap">
              <el-icon class="heatmap-head__icon"><Calendar /></el-icon>
            </div>
            <div class="heatmap-head__titles">
              <span class="heatmap-head__title">月間ヒートマップ</span>
              <span class="heatmap-head__sub">
                計画達成率・実績差異・実績数量を並べて表示（工程タブ連動）
              </span>
            </div>
            <el-tag v-if="activeTrendProcessLabel" effect="plain" size="small" type="warning">
              {{ activeTrendProcessLabel }}
            </el-tag>
            <el-tag v-if="heatmapMonthLabel" effect="plain" size="small" type="info">
              {{ heatmapMonthLabel }}
            </el-tag>
          </div>
        </div>
      </template>
      <div class="heatmap-body" v-loading="tableLoading">
        <div v-if="!heatmapMonthLabel" class="heatmap-empty">
          <el-empty description="比較データがありません" :image-size="56" />
        </div>
        <div v-else class="heatmap-panels">
          <div
            v-for="panel in heatmapPanels"
            :key="panel.key"
            class="heatmap-panel"
            :class="`heatmap-panel--${panel.key}`"
          >
            <div class="heatmap-panel__head">
              <div class="heatmap-panel__title">{{ panel.title }}</div>
              <div v-if="panel.unit" class="heatmap-panel__unit">{{ panel.unit }}</div>
            </div>
            <div class="heatmap-weekdays">
              <span v-for="w in heatmapWeekdayLabels" :key="`${panel.key}-${w}`">{{ w }}</span>
            </div>
            <div class="heatmap-grid">
              <div
                v-for="(cell, idx) in panel.cells"
                :key="`${panel.key}-${cell.date || 'pad'}-${idx}`"
                class="heatmap-cell"
                :class="{
                  'heatmap-cell--pad': cell.isPad,
                  'heatmap-cell--alert': cell.isAlert,
                  'heatmap-cell--empty': !cell.isPad && cell.value == null,
                  'heatmap-cell--clickable': !cell.isPad && !!cell.date,
                }"
                :style="cell.isPad ? undefined : { background: cell.bgColor }"
                @click="onHeatmapCellClick(cell)"
              >
                <el-tooltip
                  v-if="!cell.isPad && cell.tooltip"
                  :content="cell.tooltip"
                  placement="top"
                  :show-after="200"
                >
                  <div class="heatmap-cell__inner">
                    <span class="heatmap-cell__day">{{ cell.day }}</span>
                    <span v-if="cell.valueText" class="heatmap-cell__val">{{ cell.valueText }}</span>
                  </div>
                </el-tooltip>
                <div v-else-if="!cell.isPad" class="heatmap-cell__inner">
                  <span class="heatmap-cell__day">{{ cell.day }}</span>
                </div>
              </div>
            </div>
            <div class="heatmap-legend">
              <span class="heatmap-legend__label">{{ panel.legend }}</span>
              <div class="heatmap-legend__bar" :class="`heatmap-legend__bar--${panel.key}`" />
              <span class="heatmap-legend__hint">クリックで比較一覧へ</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    </div>
    </section>

    <!-- Zone: 比較一覧 -->
    <section class="pb-zone pb-zone--table">
      <div class="pb-zone__label">
        <span class="pb-zone__dot" aria-hidden="true" />
        <span>工程別 比較一覧</span>
      </div>
    <el-card shadow="never" class="table-card baseline-comparison-card">
      <template #header>
        <div class="comparison-list-head">
          <div class="comparison-list-head__lead">
            <div class="comparison-list-head__icon-wrap">
              <el-icon class="comparison-list-head__icon"><Setting /></el-icon>
            </div>
            <div class="comparison-list-head__titles">
              <span class="comparison-list-head__title">ベースライン比較一覧</span>
              <span class="comparison-list-head__sub">工程別タブで日次の基準・変更・差異を表示</span>
            </div>
            <el-tag
              v-if="comparisonResult?.baselineMonth"
              type="info"
              effect="plain"
              size="small"
              class="comparison-list-head__tag"
            >
              {{ dayjs(comparisonResult.baselineMonth).format('YYYY年MM月') }}
            </el-tag>
            <el-tag
              v-if="totalItemsCount > 0"
              type="primary"
              effect="plain"
              size="small"
              class="comparison-list-head__tag"
            >
              全 {{ totalItemsCount }} 行
            </el-tag>
            <el-tag
              v-if="alertStats.total > 0"
              type="danger"
              effect="dark"
              size="small"
              class="comparison-list-head__tag comparison-list-head__tag--alert"
            >
              アラート {{ alertStats.total }}
            </el-tag>
          </div>
          <div class="comparison-list-head__actions">
            <div class="alert-ctl">
              <el-tooltip
                content="基準計画に対する計画差異／計画対実績差の絶対値が閾値(%)を超える行をハイライトします"
                placement="top"
              >
                <span class="alert-ctl__label">差異閾値</span>
              </el-tooltip>
              <el-input-number
                v-model="alertSettings.thresholdPct"
                :min="1"
                :max="100"
                :step="1"
                size="small"
                controls-position="right"
                class="alert-ctl__input"
              />
              <span class="alert-ctl__unit">%</span>
              <el-checkbox v-model="alertSettings.checkPlanDiff" size="small">計画</el-checkbox>
              <el-checkbox v-model="alertSettings.checkActualDiff" size="small">実績</el-checkbox>
              <el-checkbox v-model="alertSettings.onlyAlerts" size="small">アラートのみ</el-checkbox>
            </div>
            <el-button
              type="success"
              plain
              class="btn-excel-baseline-modern comparison-list-btn"
              :icon="Document"
              @click="handleExportComparisonExcel"
              :loading="exportExcelLoading"
              :disabled="totalItemsCount === 0"
              size="small"
            >
              Excel出力
            </el-button>
            <el-button
              type="primary"
              plain
              class="btn-export-baseline-modern comparison-list-btn"
              :icon="Download"
              @click="handleExportPdfToFolder"
              :loading="exportPdfLoading"
              :disabled="!canExportBaselinePdf"
              size="small"
            >
              工程別報告書発行
            </el-button>
            <el-button
              type="default"
              plain
              class="btn-print-baseline-modern comparison-list-btn"
              :icon="Printer"
              @click="handlePrintBaselineComparison"
              :disabled="totalItemsCount === 0"
              size="small"
            >
              印刷
            </el-button>
          </div>
        </div>
      </template>
      <el-tabs v-model="activeTab" class="comparison-tabs" type="card" v-loading="tableLoading">
        <el-tab-pane
          v-for="process in processTabs"
          :key="process.name"
          :label="process.label"
          :name="process.name"
        >
          <template #label>
            <span class="tab-label" :data-tone="process.name">
              <span class="tab-tone-dot" :style="{ background: processTabTone(process.name).accent }" />
              {{ process.label }}
              <span
                v-if="(alertStats.byProcess.get(process.name) || 0) > 0"
                class="tab-alert-badge"
              >
                {{ alertStats.byProcess.get(process.name) }}
              </span>
            </span>
          </template>
          <el-table
            :data="getProcessTableItems(process.items)"
            border
            stripe
            height="660"
            style="width: 100%"
            empty-text="データがありません"
            class="comparison-table"
            :row-class-name="getComparisonRowClassName"
          >
            <el-table-column
              prop="plan_date"
              label="日付"
              min-width="148"
              width="148"
              fixed="left"
              class-name="col-date"
            >
              <template #default="{ row }">
                <div class="date-cell-wrapper">
                  <el-icon class="date-icon"><Calendar /></el-icon>
                  <span class="date-cell">{{ formatDate(row.plan_date) }}</span>
                  <el-tooltip
                    v-if="isComparisonAlertRow(row)"
                    :content="getAlertReasonText(row)"
                    placement="top"
                  >
                    <el-icon class="alert-row-icon"><WarningFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="基準計画"
              min-width="128"
              align="right"
              class-name="col-baseline"
              label-class-name="th-baseline"
            >
              <template #header>
                <div class="column-header">
                  <span>基準計画</span>
                  <el-tooltip
                    content="ベースライン生成時に固定化された計画値。成型は molding_plan、溶接／溶接SP は welding_plan の日次合計（溶接SP は製品名 FE-7・CH2 RR、それ以外は溶接）。その他は Excel 取込（production_plan_updates）を優先し、無い日はサマリの各 plan 列で補完。"
                    placement="top"
                    effect="dark"
                  >
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div class="number-cell baseline-plan">
                  <span class="number-value">{{ formatNumber(row.baseline_plan) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="変更計画"
              min-width="128"
              align="right"
              class-name="col-current"
              label-class-name="th-current"
            >
              <template #header>
                <div class="column-header">
                  <span>変更計画</span>
                  <el-tooltip
                    content="切断・面取・メッキ・検査・外注倉庫は変更計画＝基準計画（常に同期）。成型は molding_plan、溶接／溶接SP は welding_actual_plan（溶接SP は製品名 FE-7・CH2 RR、サマリのみ、Excel は使用しない。合計 0 の日も反映、該当日サマリが無い日は 0）。上記以外は production_plan_updates を優先し、無い日はサマリの各 plan 列で補完。"
                    placement="top"
                    effect="dark"
                  >
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div class="number-cell current-plan">
                  <span class="number-value">{{ formatNumber(row.current_plan) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="計画差異"
              min-width="128"
              align="right"
              class-name="col-plan-diff"
              label-class-name="th-plan-diff"
            >
              <template #header>
                <div class="column-header">
                  <span>計画差異</span>
                  <el-tooltip content="変更計画 - 基準計画" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div class="number-cell diff-cell" :class="getDiffClass(row.plan_diff)">
                  <el-icon v-if="row.plan_diff > 0" class="trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon v-else-if="row.plan_diff < 0" class="trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  <span class="number-value">{{ formatNumber(row.plan_diff) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="実績合計"
              min-width="140"
              align="right"
              class-name="col-actual"
              label-class-name="th-actual"
            >
              <template #header>
                <div class="column-header">
                  <span>実績合計</span>
                  <el-tooltip
                    content="stock_transaction_logs から当月の日次実績を再集計。溶接／溶接SP は製品名 FE-7・CH2 RR を溶接SP、それ以外を溶接に分割"
                    placement="top"
                    effect="dark"
                  >
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div
                  class="number-cell actual-cell"
                  v-if="row.current_actual !== null && row.current_actual !== undefined"
                >
                  <span class="number-value">{{ formatNumber(row.current_actual) }}</span>
                </div>
                <div class="number-cell" v-else>
                  <span class="number-value number-value--muted">-</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              label="計画対実績差"
              min-width="140"
              align="right"
              class-name="col-actual-diff"
              label-class-name="th-actual-diff"
            >
              <template #header>
                <div class="column-header">
                  <span>計画対実績差</span>
                  <el-tooltip content="ベースライン計画 - 実績" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div
                  class="number-cell diff-cell"
                  :class="getDiffClass(row.actual_diff)"
                  v-if="row.actual_diff !== null && row.actual_diff !== undefined"
                >
                  <el-icon v-if="row.actual_diff > 0" class="trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon v-else-if="row.actual_diff < 0" class="trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  <span class="number-value">{{ formatNumber(row.actual_diff) }}</span>
                </div>
                <div class="number-cell" v-else>
                  <span class="number-value number-value--muted">-</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="tab-total-wrapper" v-if="processTotals.get(process.name)">
            <div class="tab-total-header">
              <div class="tab-total-header__lead">
                <span class="tab-total-header__badge" aria-hidden="true">
                  <el-icon class="total-icon"><DataAnalysis /></el-icon>
                </span>
                <span class="tab-total-label">合計</span>
                <span class="tab-total-process">{{ process.label }}</span>
              </div>
            </div>
            <div class="tab-total-grid">
              <div class="total-item baseline-plan-item">
                <div class="total-item__glow" aria-hidden="true" />
                <div class="total-item-header">
                  <span class="total-item-icon-wrap">
                    <el-icon class="total-item-icon"><Document /></el-icon>
                  </span>
                  <span class="total-item-label">基準計画</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.baselinePlan) }}
                </div>
              </div>
              <div class="total-item current-plan-item">
                <div class="total-item__glow" aria-hidden="true" />
                <div class="total-item-header">
                  <span class="total-item-icon-wrap">
                    <el-icon class="total-item-icon"><DataLine /></el-icon>
                  </span>
                  <span class="total-item-label">変更計画</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.currentPlan) }}
                </div>
              </div>
              <div
                class="total-item plan-diff-item"
                :class="getDiffClass(processTotals.get(process.name)?.planDiff)"
              >
                <div class="total-item__glow" aria-hidden="true" />
                <div class="total-item-header">
                  <span class="total-item-icon-wrap">
                    <el-icon class="total-item-icon"><TrendCharts /></el-icon>
                  </span>
                  <span class="total-item-label">計画差異</span>
                </div>
                <div class="total-item-value">
                  <el-icon
                    v-if="(processTotals.get(process.name)?.planDiff || 0) > 0"
                    class="total-trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon
                    v-else-if="(processTotals.get(process.name)?.planDiff || 0) < 0"
                    class="total-trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  {{ formatNumber(processTotals.get(process.name)?.planDiff) }}
                </div>
              </div>
              <div class="total-item actual-item">
                <div class="total-item__glow" aria-hidden="true" />
                <div class="total-item-header">
                  <span class="total-item-icon-wrap">
                    <el-icon class="total-item-icon"><CircleCheck /></el-icon>
                  </span>
                  <span class="total-item-label">実績</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.currentActual) }}
                </div>
              </div>
              <div
                class="total-item actual-diff-item"
                :class="getDiffClass(processTotals.get(process.name)?.actualDiff)"
              >
                <div class="total-item__glow" aria-hidden="true" />
                <div class="total-item-header">
                  <span class="total-item-icon-wrap">
                    <el-icon class="total-item-icon"><DataAnalysis /></el-icon>
                  </span>
                  <span class="total-item-label">計画対実績差</span>
                </div>
                <div class="total-item-value">
                  <el-icon
                    v-if="(processTotals.get(process.name)?.actualDiff || 0) > 0"
                    class="total-trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon
                    v-else-if="(processTotals.get(process.name)?.actualDiff || 0) < 0"
                    class="total-trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  {{ formatNumber(processTotals.get(process.name)?.actualDiff) }}
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane v-if="processTabs.length === 0" label="データなし" name="empty">
          <el-empty description="データがありません" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
    </section>
  </div>

  <el-dialog
    v-model="adjustmentDialogVisible"
    class="baseline-adjust-dialog pb-gen-dialog pb-gen-dialog--adjust"
    width="980px"
    destroy-on-close
    align-center
    append-to-body
  >
    <template #header>
      <div class="adjustment-header">
        <div class="pb-gen-dialog__icon pb-gen-dialog__icon--adjust" aria-hidden="true">
          <el-icon :size="22"><Setting /></el-icon>
        </div>
        <div class="adjustment-header__text">
          <div class="adjustment-title">ベースライン計画修正</div>
          <p class="adjustment-desc">
            日別の計画値を編集・保存。日付の追加／削除もここから行えます。
          </p>
        </div>
        <div class="adjustment-header__stats">
          <span class="adjustment-stat">
            <em>{{ adjustmentItems.length }}</em>件
          </span>
          <span class="adjustment-stat adjustment-stat--edit" v-if="adjustmentDirtyCount > 0">
            <em>{{ adjustmentDirtyCount }}</em>変更
          </span>
          <el-tag
            v-if="adjustmentForm.baselineMonth"
            size="large"
            effect="dark"
            round
            class="pb-gen-dialog__chip"
          >
            {{ dayjs(adjustmentForm.baselineMonth).format('YYYY年MM月') }}
          </el-tag>
        </div>
      </div>
    </template>

    <div class="adjustment-toolbar">
      <div class="toolbar-left">
        <el-date-picker
          v-model="adjustmentForm.baselineMonth"
          type="month"
          value-format="YYYY-MM-DD"
          placeholder="基準月"
          class="toolbar-month"
        />
        <el-select
          v-model="adjustmentForm.processName"
          clearable
          placeholder="全工程"
          class="toolbar-process"
        >
          <el-option
            v-for="item in processOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select v-model="adjustmentFilterMode" size="default" class="toolbar-filter" placeholder="表示">
          <el-option label="すべて" value="all" />
          <el-option label="編集あり" value="unsaved" />
          <el-option label="比較アラート日" value="alert" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" :icon="Search" @click="loadAdjustmentRecords">
          データ取得
        </el-button>
        <el-button :icon="Refresh" @click="resetAdjustmentForm">リセット</el-button>
      </div>
    </div>

    <div class="adjustment-add-panel">
      <div class="adjustment-add-panel__head">
        <el-icon><Plus /></el-icon>
        <span>日付を追加</span>
        <span class="adjustment-add-panel__hint">基準月内の日付を選び、工程・数量を入れて追加</span>
      </div>
      <div class="adjustment-add-panel__controls">
        <el-date-picker
          v-model="adjustmentAddForm.planDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="追加する日付"
          :disabled-date="disabledAdjustmentAddDate"
          class="adjustment-add-date"
        />
        <el-select
          v-model="adjustmentAddForm.processName"
          placeholder="工程"
          class="adjustment-add-process"
        >
          <el-option
            v-for="item in adjustmentProcessChoices"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-input-number
          v-model="adjustmentAddForm.planQuantity"
          :min="0"
          :max="100000000"
          :step="1"
          :controls="true"
          class="adjustment-add-qty"
          placeholder="数量"
        />
        <el-button
          type="success"
          :icon="Plus"
          :loading="adjustmentAdding"
          @click="handleAddAdjustmentDate"
        >
          追加
        </el-button>
      </div>
    </div>

    <el-table
      v-loading="adjustmentLoading"
      :data="adjustmentDisplayItems"
      class="adjustment-table"
      height="440"
      size="small"
      border
      empty-text="該当するデータがありません。上から日付を追加できます"
      :row-class-name="getAdjustmentRowClassName"
    >
      <el-table-column prop="plan_date" label="日付" width="132" align="center">
        <template #default="{ row }">
          <div class="adjustment-date">
            {{ formatDate(row.plan_date) }}
            <el-tag v-if="row.isNew" size="small" type="success" effect="plain" class="adjustment-new-tag">
              NEW
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="process_name" label="工程" width="140">
        <template #default="{ row }">
          <el-tag
            size="small"
            effect="plain"
            class="adjustment-process-tag"
            :style="{
              '--tone': processTabTone(row.process_name || '').accent,
            }"
          >
            {{ row.process_name || '未指定' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="基準計画" min-width="280">
        <template #default="{ row, $index }">
          <div
            class="plan-editor"
            :class="{ 'is-dirty': Number(row.tempPlanQuantity) !== Number(row.plan_quantity) }"
          >
            <div class="plan-editor-current">
              現在値 <strong>{{ formatNumber(row.plan_quantity) }}</strong>
            </div>
            <el-input-number
              v-model="row.tempPlanQuantity"
              :min="0"
              :max="100000000"
              :step="1"
              :controls="false"
              size="small"
              class="plan-input"
              :ref="(el) => setPlanInputRef(el, $index)"
              @keydown="handlePlanInputKeydown($event, $index)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="210" fixed="right" align="center">
        <template #default="{ row }">
          <div class="adjustment-actions">
            <el-button
              type="primary"
              plain
              size="small"
              :loading="row.saving"
              :disabled="row.deleting"
              @click="() => handleUpdatePlanQuantity(row as PlanBaselineAdjustmentItem)"
            >
              保存
            </el-button>
            <el-button
              type="danger"
              plain
              size="small"
              :icon="Delete"
              :loading="row.deleting"
              :disabled="row.saving"
              @click="() => handleDeleteBaselineRecord(row as PlanBaselineAdjustmentItem)"
            >
              削除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <div class="adjustment-footer">
        <div class="adjustment-footer__note">
          削除＝その日付の行を減らす／追加パネル＝日付を増やす
        </div>
        <div class="adjustment-footer__actions">
          <el-button type="primary" :icon="DocumentAdd" @click="handleBatchSave">
            変更を一括保存
          </el-button>
          <el-button @click="adjustmentDialogVisible = false">閉じる</el-button>
        </div>
      </div>
    </template>
  </el-dialog>

  <!-- 切断・面取・メッキ・検査：カレンダーで日付を選んで同一数量を手入力 -->
  <el-dialog
    v-model="fixedBaselineDialogVisible"
    width="560px"
    align-center
    destroy-on-close
    append-to-body
    class="pb-gen-dialog pb-gen-dialog--manual"
  >
    <template #header>
      <div class="pb-gen-dialog__head">
        <div class="pb-gen-dialog__icon" aria-hidden="true">
          <el-icon :size="22"><EditPen /></el-icon>
        </div>
        <div class="pb-gen-dialog__titles">
          <div class="pb-gen-dialog__title">基準計画の手入力</div>
          <div class="pb-gen-dialog__sub">
            カレンダーで反映日を選択（既定は平日のみ／クリックで追加・解除）。生成後は「計画を修正」で変更可
          </div>
        </div>
        <el-tag
          v-if="fixedBaselineTargetProcess"
          effect="dark"
          round
          class="pb-gen-dialog__chip"
        >
          {{ fixedBaselineTargetProcess }}
        </el-tag>
      </div>
    </template>

    <div class="pb-gen-dialog__body">
      <div class="pb-gen-dialog__meta-row">
        <div class="pb-gen-dialog__meta">
          <span class="pb-gen-dialog__meta-k">対象月</span>
          <span class="pb-gen-dialog__meta-v">
            {{ dayjs(generateForm.baselineMonth).format('YYYY年MM月') }}
          </span>
        </div>
        <div class="pb-gen-dialog__meta">
          <span class="pb-gen-dialog__meta-k">選択</span>
          <span class="pb-gen-dialog__meta-v">{{ fixedBaselineSelectedCount }}日</span>
        </div>
      </div>

      <div class="pb-cal-toolbar">
        <el-button size="small" @click="selectFixedBaselineWeekdays">平日のみ</el-button>
        <el-button size="small" @click="selectFixedBaselineAll">すべて</el-button>
        <el-button size="small" @click="clearFixedBaselineDates">クリア</el-button>
      </div>

      <div class="pb-cal">
        <div class="pb-cal__weekdays">
          <span
            v-for="w in fixedBaselineWeekdayLabels"
            :key="w.label"
            class="pb-cal__wd"
            :class="{ 'is-sun': w.sun, 'is-sat': w.sat }"
          >
            {{ w.label }}
          </span>
        </div>
        <div class="pb-cal__grid">
          <button
            v-for="(cell, idx) in fixedBaselineCalendarCells"
            :key="`${cell.date || 'pad'}-${idx}`"
            type="button"
            class="pb-cal__cell"
            :class="{
              'is-pad': cell.isPad,
              'is-selected': cell.selected,
              'is-sun': cell.isSun,
              'is-sat': cell.isSat,
            }"
            :disabled="cell.isPad"
            @click="toggleFixedBaselineDate(cell.date)"
          >
            <span v-if="!cell.isPad">{{ cell.day }}</span>
          </button>
        </div>
      </div>

      <el-form label-position="top" class="pb-gen-dialog__form">
        <el-form-item label="基準計画数（選択日共通）" required>
          <el-input-number
            v-model="fixedBaselineForm.planQuantity"
            :min="0"
            :max="100000000"
            :step="1"
            :controls="true"
            class="pb-gen-dialog__control"
          />
        </el-form-item>
      </el-form>
      <div class="pb-gen-dialog__hint">
        <el-icon><WarningFilled /></el-icon>
        <span>
          既存の「{{ fixedBaselineTargetProcess }}」ベースラインは削除され、選択した日付だけに入力値が登録されます。
        </span>
      </div>
    </div>

    <template #footer>
      <div class="pb-gen-dialog__footer">
        <el-button @click="fixedBaselineDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="generating" :icon="DocumentAdd" @click="submitFixedBaselineGenerate">
          生成する
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 工程別PDF発行 进度弹窗（append-to-body で即座に最前面へ描画） -->
  <el-dialog
    v-model="exportProgressVisible"
    title="レポート生成"
    width="440px"
    align-center
    append-to-body
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    class="export-pdf-progress-dialog"
  >
    <div class="export-progress-content">
      <div class="export-progress-icon-wrap">
        <el-icon class="export-progress-icon"><Document /></el-icon>
      </div>
      <p class="export-progress-title">全工程統合レポート（PDF）を生成しています</p>
      <p class="export-progress-current">{{ exportProgressCurrent }}</p>
      <div class="export-progress-bar-wrap">
        <el-progress
          :percentage="exportProgressPercent"
          :stroke-width="12"
          :format="(p) => `${p}%`"
          status="success"
          class="export-progress-bar"
        />
      </div>
    </div>
  </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ProductionPlanBaselineManagement' })
import { reactive, ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts,
  Refresh,
  Search,
  DocumentAdd,
  Setting,
  Delete,
  QuestionFilled,
  Calendar,
  ArrowUp,
  ArrowDown,
  DataAnalysis,
  Document,
  CircleCheck,
  DataLine,
  EditPen,
  Download,
  Printer,
  WarningFilled,
  Plus,
} from '@element-plus/icons-vue'
import {
  generatePlanBaseline,
  fetchPlanBaselineComparison,
  deletePlanBaseline,
  deletePlanBaselineRecord,
  fetchPlanBaselineRecords,
  updatePlanBaselinePlanQuantity,
  exportPlanBaselinePdfToFolder,
  type PlanBaselineComparisonItem,
  type PlanBaselineComparisonResult,
  type PlanBaselineComparisonSummary,
  type PlanBaselineRecord,
} from '@/api/planBaseline'
import { fetchScheduledWorkdaysForMonth } from '@/api/master/companyWorkCalendar'
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'
import echarts from '@/utils/echarts'
import { downloadExcelMultiSheet, type ExcelSheetAoa } from '@/utils/excelExport'
import { useApsOperationPermission } from '@/composables/useApsOperationPermission'
import { guardApsOperation } from '@/utils/apsOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useApsOperationPermission()


const router = useRouter()

const goHelpPage = () => {
  // 新标签页打开：不替换当前页面；同时避免当前 SPA 热更新导致路由表未刷新。
  window.open('/erp/production/plan-baseline/help', '_blank', 'noopener')
}

const goReportCenter = () => {
  router.push({ path: '/system/reports', query: { tab: 'schedule' } })
}

const today = dayjs().startOf('month').format('YYYY-MM-DD')
/** 画面初期表示・クリア後の既定工程 */
const DEFAULT_PROCESS_NAME = '成型'

/** ベースライン生成・削除・修正用（比較条件とは独立） */
const generateForm = reactive({
  baselineMonth: today,
  processName: '',
})
/** ベースライン生成カードの操作ロック（OFF で入力・ボタン不可） */
const generateSectionEnabled = ref(false)

/** 比較検索・一覧表示用（既定は全工程。タブ側で成型を優先表示） */
const compareForm = reactive({
  baselineMonth: today,
  processName: '',
})

interface PlanBaselineAdjustmentItem extends PlanBaselineRecord {
  tempPlanQuantity: number
  saving?: boolean
  deleting?: boolean
  isNew?: boolean
}

const processOptions = [
  { label: '全工程', value: '' },
  { label: '切断', value: '切断' },
  { label: '面取', value: '面取' },
  { label: '成型', value: '成型' },
  { label: 'メッキ', value: 'メッキ' },
  { label: '溶接', value: '溶接' },
  { label: '溶接SP', value: '溶接SP' },
  { label: '検査', value: '検査' },
]


const generating = ref(false)
const deleting = ref(false)
const tableLoading = ref(false)
const exportPdfLoading = ref(false)
const exportExcelLoading = ref(false)
const exportProgressVisible = ref(false)
const exportProgressPercent = ref(0)
const exportProgressCurrent = ref('')
const comparisonResult = ref<PlanBaselineComparisonResult | null>(null)
const comparisonItems = ref<PlanBaselineComparisonItem[]>([])
const activeTab = ref('all')

const adjustmentDialogVisible = ref(false)
const adjustmentLoading = ref(false)
const adjustmentAdding = ref(false)
const adjustmentItems = ref<PlanBaselineAdjustmentItem[]>([])
const adjustmentFilterMode = ref<'all' | 'unsaved' | 'alert'>('all')
const planInputRefs = ref<(HTMLInputElement | null)[]>([])
const adjustmentForm = reactive({
  baselineMonth: generateForm.baselineMonth,
  processName: '',
})
const adjustmentAddForm = reactive({
  planDate: '' as string,
  processName: '' as string,
  planQuantity: null as number | null,
})

const adjustmentProcessChoices = computed(() =>
  processOptions.filter((item) => !!item.value),
)

const adjustmentDirtyCount = computed(
  () =>
    adjustmentItems.value.filter(
      (r) => Number(r.tempPlanQuantity) !== Number(r.plan_quantity),
    ).length,
)

function resetAdjustmentAddForm() {
  const month = adjustmentForm.baselineMonth
    ? dayjs(adjustmentForm.baselineMonth).startOf('month')
    : dayjs().startOf('month')
  const todayD = dayjs().startOf('day')
  const defaultDate =
    todayD.year() === month.year() && todayD.month() === month.month()
      ? todayD.format('YYYY-MM-DD')
      : month.format('YYYY-MM-DD')
  adjustmentAddForm.planDate = defaultDate
  adjustmentAddForm.processName =
    adjustmentForm.processName || generateForm.processName || DEFAULT_PROCESS_NAME
  adjustmentAddForm.planQuantity = null
}

function disabledAdjustmentAddDate(d: Date) {
  if (!adjustmentForm.baselineMonth) return true
  const m = dayjs(adjustmentForm.baselineMonth)
  const cur = dayjs(d)
  return cur.year() !== m.year() || cur.month() !== m.month()
}

function getAdjustmentRowClassName({ row }: { row: PlanBaselineAdjustmentItem }) {
  if (row.isNew) return 'adjustment-row--new'
  if (Number(row.tempPlanQuantity) !== Number(row.plan_quantity)) return 'adjustment-row--dirty'
  return ''
}

/** 切断・面取・メッキ・検査はカレンダーで選択した日に同一数量を手入力で生成 */
const FIXED_BASELINE_PROCESS_NAMES = new Set(['切断', '面取', 'メッキ', '検査'])
const fixedBaselineDialogVisible = ref(false)
const fixedBaselineTargetProcess = ref('')
const fixedBaselineForm = reactive({
  selectedDates: [] as string[],
  planQuantity: null as number | null,
})
const fixedBaselineWeekdayLabels = [
  { label: '日', sun: true, sat: false },
  { label: '月', sun: false, sat: false },
  { label: '火', sun: false, sat: false },
  { label: '水', sun: false, sat: false },
  { label: '木', sun: false, sat: false },
  { label: '金', sun: false, sat: false },
  { label: '土', sun: false, sat: true },
]

function listMonthDates(monthStart: string): string[] {
  const start = dayjs(monthStart).startOf('month')
  const end = start.endOf('month')
  const dates: string[] = []
  let cur = start
  while (cur.isBefore(end, 'day') || cur.isSame(end, 'day')) {
    dates.push(cur.format('YYYY-MM-DD'))
    cur = cur.add(1, 'day')
  }
  return dates
}

function defaultWeekdayDates(monthStart: string): string[] {
  return listMonthDates(monthStart).filter((d) => {
    const wd = dayjs(d).day() // 0=日 … 6=土
    return wd >= 1 && wd <= 5
  })
}

const resetFixedBaselineForm = () => {
  const month = generateForm.baselineMonth || dayjs().startOf('month').format('YYYY-MM-DD')
  fixedBaselineForm.selectedDates = defaultWeekdayDates(month)
  fixedBaselineForm.planQuantity = null
}

const fixedBaselineSelectedCount = computed(() => fixedBaselineForm.selectedDates.length)

const fixedBaselineCalendarCells = computed(() => {
  const month = generateForm.baselineMonth
    ? dayjs(generateForm.baselineMonth).startOf('month')
    : dayjs().startOf('month')
  const selected = new Set(fixedBaselineForm.selectedDates)
  const firstDow = month.day() // 0=日
  const daysInMonth = month.daysInMonth()
  const cells: Array<{
    isPad: boolean
    date: string
    day: number | ''
    selected: boolean
    isSun: boolean
    isSat: boolean
  }> = []
  for (let i = 0; i < firstDow; i++) {
    cells.push({ isPad: true, date: '', day: '', selected: false, isSun: false, isSat: false })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const date = month.date(d).format('YYYY-MM-DD')
    const wd = month.date(d).day()
    cells.push({
      isPad: false,
      date,
      day: d,
      selected: selected.has(date),
      isSun: wd === 0,
      isSat: wd === 6,
    })
  }
  while (cells.length % 7 !== 0) {
    cells.push({ isPad: true, date: '', day: '', selected: false, isSun: false, isSat: false })
  }
  return cells
})

function toggleFixedBaselineDate(date: string) {
  if (!date) return
  const idx = fixedBaselineForm.selectedDates.indexOf(date)
  if (idx >= 0) {
    fixedBaselineForm.selectedDates.splice(idx, 1)
  } else {
    fixedBaselineForm.selectedDates.push(date)
    fixedBaselineForm.selectedDates.sort()
  }
}

function selectFixedBaselineWeekdays() {
  const month = generateForm.baselineMonth || dayjs().startOf('month').format('YYYY-MM-DD')
  fixedBaselineForm.selectedDates = defaultWeekdayDates(month)
}

function selectFixedBaselineAll() {
  const month = generateForm.baselineMonth || dayjs().startOf('month').format('YYYY-MM-DD')
  fixedBaselineForm.selectedDates = listMonthDates(month)
}

function clearFixedBaselineDates() {
  fixedBaselineForm.selectedDates = []
}

/** ベースライン比較タブ・報告書PDFの工程表示順 */
const BASELINE_COMPARISON_PROCESS_ORDER = [
  '切断',
  '面取',
  '成型',
  'メッキ',
  '溶接',
  '溶接SP',
  '検査',
] as const

/** 比較一覧タブに出さない工程名 */
const BASELINE_COMPARISON_EXCLUDED_PROCESS_NAMES = new Set([
  '溶接前検査',
  '外注検査前',
  '外注支給前',
  '外注支給前工程',
  '外注メッキ',
  '外注溶接',
])

function baselineComparisonProcessOrderIndex(name: string): number {
  const i = (BASELINE_COMPARISON_PROCESS_ORDER as readonly string[]).indexOf(name)
  return i >= 0 ? i : 1000
}

/** 工程タブの色分け（溶接と溶接SPを明確に区別） */
const PROCESS_TAB_TONES: Record<string, string> = {
  切断: '#2563eb',
  面取: '#16a34a',
  成型: '#d97706',
  メッキ: '#dc2626',
  溶接: '#0284c7',
  溶接SP: '#7c3aed',
  検査: '#0d9488',
}

function processTabTone(name: string) {
  return { accent: PROCESS_TAB_TONES[name] ?? '#64748b' }
}

// 工程別にデータをグループ化
const processTabs = computed(() => {
  if (comparisonItems.value.length === 0) {
    return []
  }

  // 工程名でグループ化
  const processMap = new Map<string, PlanBaselineComparisonItem[]>()

  comparisonItems.value.forEach((item) => {
    const processName = item.process_name || '未指定'
    if (BASELINE_COMPARISON_EXCLUDED_PROCESS_NAMES.has(processName)) {
      return
    }
    if (!processMap.has(processName)) {
      processMap.set(processName, [])
    }
    processMap.get(processName)!.push(item)
  })

  // 各工程のデータを日付順にソート
  const tabs = Array.from(processMap.entries()).map(([processName, items]) => {
    const sortedItems = [...items].sort(
      (a, b) => dayjs(a.plan_date).valueOf() - dayjs(b.plan_date).valueOf(),
    )
    return {
      name: processName,
      label: processName,
      items: sortedItems,
    }
  })

  tabs.sort((a, b) => {
    const ia = baselineComparisonProcessOrderIndex(a.name)
    const ib = baselineComparisonProcessOrderIndex(b.name)
    if (ia !== ib) return ia - ib
    return a.label.localeCompare(b.label, 'ja')
  })

  return tabs
})

const PDF_EXPORT_PROCESS_ORDER = BASELINE_COMPARISON_PROCESS_ORDER

/** 上記順の対象工程のうち、比較データが1件以上あるタブだけ（PDF 発行用） */
const pdfExportTargetTabs = computed(() => {
  const tabMap = new Map(processTabs.value.map((t) => [t.name, t]))
  return PDF_EXPORT_PROCESS_ORDER.map((name) => tabMap.get(name)).filter(
    (tab): tab is (typeof processTabs.value)[number] => !!tab && tab.items.length > 0,
  )
})

const canExportBaselinePdf = computed(
  () => !!comparisonResult.value?.baselineMonth && pdfExportTargetTabs.value.length > 0,
)

// データが更新されたら成型タブを優先してアクティブに
const updateActiveTab = () => {
  if (processTabs.value.length > 0) {
    const currentTabExists = processTabs.value.find((t) => t.name === activeTab.value)
    if (!currentTabExists) {
      const molding = processTabs.value.find((t) => t.name === DEFAULT_PROCESS_NAME)
      activeTab.value = molding?.name ?? processTabs.value[0].name
    }
  }
}

const totalItemsCount = computed(() => {
  return comparisonItems.value.length
})

const ALERT_SETTINGS_KEY = 'plan-baseline-alert-settings'

function loadAlertSettings() {
  try {
    const raw = localStorage.getItem(ALERT_SETTINGS_KEY)
    if (!raw) return null
    return JSON.parse(raw) as Partial<{
      thresholdPct: number
      checkPlanDiff: boolean
      checkActualDiff: boolean
      onlyAlerts: boolean
    }>
  } catch {
    return null
  }
}

const savedAlert = loadAlertSettings()
const alertSettings = reactive({
  thresholdPct: savedAlert?.thresholdPct ?? 5,
  checkPlanDiff: savedAlert?.checkPlanDiff ?? false,
  checkActualDiff: savedAlert?.checkActualDiff ?? true,
  onlyAlerts: savedAlert?.onlyAlerts ?? false,
})

watch(
  alertSettings,
  (v) => {
    try {
      localStorage.setItem(
        ALERT_SETTINGS_KEY,
        JSON.stringify({
          thresholdPct: v.thresholdPct,
          checkPlanDiff: v.checkPlanDiff,
          checkActualDiff: v.checkActualDiff,
          onlyAlerts: v.onlyAlerts,
        }),
      )
    } catch {
      /* ignore quota */
    }
  },
  { deep: true },
)

/** 基準に対する差異率(%)。基準0かつ差異ありは 100 扱い */
function getRelativeDiffPct(
  baseline: number | null | undefined,
  diff: number | null | undefined,
): number | null {
  if (diff == null || Number.isNaN(Number(diff))) return null
  const d = Math.abs(Number(diff))
  if (d === 0) return 0
  const b = Math.abs(Number(baseline ?? 0))
  if (b <= 0) return 100
  return (d / b) * 100
}

function getPlanDiffAlertPct(row: PlanBaselineComparisonItem): number | null {
  return getRelativeDiffPct(row.baseline_plan, row.plan_diff)
}

function getActualDiffAlertPct(row: PlanBaselineComparisonItem): number | null {
  return getRelativeDiffPct(row.baseline_plan, row.actual_diff)
}

function isComparisonAlertRow(row: PlanBaselineComparisonItem): boolean {
  const th = Number(alertSettings.thresholdPct) || 0
  if (th <= 0) return false
  if (alertSettings.checkPlanDiff) {
    const pct = getPlanDiffAlertPct(row)
    if (pct != null && pct > th) return true
  }
  if (alertSettings.checkActualDiff) {
    const pct = getActualDiffAlertPct(row)
    if (pct != null && pct > th) return true
  }
  return false
}

function getAlertReasonText(row: PlanBaselineComparisonItem): string {
  const parts: string[] = []
  const th = Number(alertSettings.thresholdPct) || 0
  if (alertSettings.checkPlanDiff) {
    const pct = getPlanDiffAlertPct(row)
    if (pct != null && pct > th) {
      parts.push(`計画差異 ${pct.toFixed(1)}%（閾値 ${th}%）`)
    }
  }
  if (alertSettings.checkActualDiff) {
    const pct = getActualDiffAlertPct(row)
    if (pct != null && pct > th) {
      parts.push(`計画対実績差 ${pct.toFixed(1)}%（閾値 ${th}%）`)
    }
  }
  return parts.length ? parts.join(' / ') : '閾値超過'
}

function getProcessTableItems(items: PlanBaselineComparisonItem[]) {
  if (!alertSettings.onlyAlerts) return items
  return items.filter((row) => isComparisonAlertRow(row))
}

const highlightedCompareDate = ref<string | null>(null)
let highlightCompareTimer: ReturnType<typeof setTimeout> | undefined

function focusComparisonDate(date: string) {
  if (!date) return
  highlightedCompareDate.value = date
  nextTick(() => {
    const row = document.querySelector(
      '.baseline-comparison-card tr.comparison-row--focus',
    ) as HTMLElement | null
    row?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  })
  if (highlightCompareTimer) clearTimeout(highlightCompareTimer)
  highlightCompareTimer = setTimeout(() => {
    highlightedCompareDate.value = null
  }, 3200)
}

function onHeatmapCellClick(cell: { isPad: boolean; date: string }) {
  if (cell.isPad || !cell.date) return
  focusComparisonDate(cell.date)
}

function getComparisonRowClassName({ row }: { row: PlanBaselineComparisonItem }) {
  const parts: string[] = []
  if (isComparisonAlertRow(row)) parts.push('comparison-row--alert')
  const d = row.plan_date ? dayjs(row.plan_date).format('YYYY-MM-DD') : ''
  if (d && d === highlightedCompareDate.value) parts.push('comparison-row--focus')
  return parts.join(' ')
}

const comparisonAlertKeySet = computed(() => {
  const set = new Set<string>()
  for (const item of comparisonItems.value) {
    if (!isComparisonAlertRow(item) || !item.plan_date) continue
    const proc = item.process_name || '未指定'
    set.add(`${proc}|${dayjs(item.plan_date).format('YYYY-MM-DD')}`)
  }
  return set
})

function isAdjustmentAlertRow(row: PlanBaselineAdjustmentItem): boolean {
  const proc = row.process_name || '未指定'
  const d = row.plan_date ? dayjs(row.plan_date).format('YYYY-MM-DD') : ''
  return comparisonAlertKeySet.value.has(`${proc}|${d}`)
}

const adjustmentDisplayItems = computed(() => {
  let list = adjustmentItems.value
  if (adjustmentFilterMode.value === 'unsaved') {
    list = list.filter((r) => Number(r.tempPlanQuantity) !== Number(r.plan_quantity))
  } else if (adjustmentFilterMode.value === 'alert') {
    list = list.filter((r) => isAdjustmentAlertRow(r))
  }
  return list
})


const alertStats = computed(() => {
  const byProcess = new Map<string, number>()
  let total = 0
  for (const tab of processTabs.value) {
    let n = 0
    for (const row of tab.items) {
      if (isComparisonAlertRow(row)) n++
    }
    byProcess.set(tab.name, n)
    total += n
  }
  return { total, byProcess }
})

const processTotals = computed(() => {
  const totals = new Map<
    string,
    {
      baselinePlan: number
      currentPlan: number
      planDiff: number
      currentActual: number
      actualDiff: number
    }
  >()
  type TabTotals = {
    baselinePlan: number
    currentPlan: number
    planDiff: number
    currentActual: number
    actualDiff: number
  }
  const initial: TabTotals = {
    baselinePlan: 0,
    currentPlan: 0,
    planDiff: 0,
    currentActual: 0,
    actualDiff: 0,
  }
  processTabs.value.forEach((tab) => {
    const aggregate = tab.items.reduce<TabTotals>(
      (acc, item) => {
        acc.baselinePlan += Number(item.baseline_plan ?? 0)
        acc.currentPlan += Number(item.current_plan ?? 0)
        acc.planDiff += Number(item.plan_diff ?? 0)
        if (item.current_actual != null) acc.currentActual += Number(item.current_actual)
        if (item.actual_diff != null) acc.actualDiff += Number(item.actual_diff)
        return acc
      },
      { ...initial },
    )
    totals.set(tab.name, aggregate)
  })
  return totals
})

/** 画面内日次推移チャート（現行工程タブ連動） */
const trendChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
/** 柱の間に差異数値を表示 */
const trendShowDiffBars = ref(true)
/** 柱の上に千単位の数量を表示 */
const trendShowValueLabels = ref(true)

const TREND_UNIT_DIVISOR = 1000

function toTrendUnit(value: number | null | undefined): number | null {
  if (value == null || Number.isNaN(Number(value))) return null
  return Number(value) / TREND_UNIT_DIVISOR
}

function formatTrendUnit(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(Number(value))) return '—'
  const n = Number(value)
  const fixed = digits === 0 ? Math.round(n) : Math.round(n * 10 ** digits) / 10 ** digits
  return fixed.toLocaleString('ja-JP', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

const activeTrendTab = computed(() => {
  return (
    processTabs.value.find((t) => t.name === activeTab.value) ?? processTabs.value[0] ?? null
  )
})

const activeTrendProcessLabel = computed(() => activeTrendTab.value?.label ?? '')
const activeTrendItems = computed(() => activeTrendTab.value?.items ?? [])

type HeatmapMetric = 'achievement' | 'actualDiff' | 'actualQty'
type HeatmapCell = {
  isPad: boolean
  date: string
  day: number | ''
  value: number | null
  valueText: string
  bgColor: string
  isAlert: boolean
  tooltip: string
}

const heatmapWeekdayLabels = ['日', '月', '火', '水', '木', '金', '土']

function getHeatmapMetricValue(row: PlanBaselineComparisonItem, metric: HeatmapMetric): number | null {
  if (metric === 'achievement') {
    const plan = Number(row.current_plan ?? 0)
    if (row.current_actual == null) return null
    if (plan === 0) return null
    return (Number(row.current_actual) / plan) * 100
  }
  if (metric === 'actualDiff') {
    if (row.actual_diff == null && row.current_actual == null) return null
    if (row.actual_diff != null) return Number(row.actual_diff)
    // fallback: 基準計画 − 実績（サマリー定義に合わせる）
    return Number(row.baseline_plan ?? 0) - Number(row.current_actual ?? 0)
  }
  // actualQty：表示用に千単位へ
  if (row.current_actual == null) return null
  return Number(row.current_actual) / 1000
}

function heatmapCellBackground(
  value: number | null,
  metric: HeatmapMetric,
  opts?: { maxAbsDiff?: number; maxQty?: number },
): string {
  if (value == null) return 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)'
  if (metric === 'achievement') {
    if (value >= 100) return 'linear-gradient(165deg, #bbf7d0 0%, #86efac 100%)'
    if (value >= 95) return 'linear-gradient(165deg, #ecfccb 0%, #d9f99d 100%)'
    if (value >= 85) return 'linear-gradient(165deg, #fef9c3 0%, #fde68a 100%)'
    if (value >= 70) return 'linear-gradient(165deg, #ffedd5 0%, #fdba74 100%)'
    return 'linear-gradient(165deg, #fee2e2 0%, #fca5a5 100%)'
  }
  if (metric === 'actualDiff') {
    const maxAbs = Math.max(opts?.maxAbsDiff ?? 0, 1)
    const ratio = Math.min(Math.abs(value) / maxAbs, 1)
    if (value >= 0) {
      if (ratio >= 0.66) return 'linear-gradient(165deg, #bbf7d0 0%, #4ade80 100%)'
      if (ratio >= 0.33) return 'linear-gradient(165deg, #ecfdf5 0%, #a7f3d0 100%)'
      return 'linear-gradient(165deg, #f0fdf4 0%, #dcfce7 100%)'
    }
    if (ratio >= 0.66) return 'linear-gradient(165deg, #fecaca 0%, #f87171 100%)'
    if (ratio >= 0.33) return 'linear-gradient(165deg, #fee2e2 0%, #fca5a5 100%)'
    return 'linear-gradient(165deg, #fff7ed 0%, #fed7aa 100%)'
  }
  // actualQty：多いほど濃い青緑
  const maxQty = Math.max(opts?.maxQty ?? 0, 0.0001)
  const ratio = Math.min(Math.max(value, 0) / maxQty, 1)
  if (ratio >= 0.8) return 'linear-gradient(165deg, #67e8f9 0%, #0891b2 100%)'
  if (ratio >= 0.55) return 'linear-gradient(165deg, #a5f3fc 0%, #22d3ee 100%)'
  if (ratio >= 0.3) return 'linear-gradient(165deg, #cffafe 0%, #67e8f9 100%)'
  if (ratio > 0) return 'linear-gradient(165deg, #ecfeff 0%, #cffafe 100%)'
  return 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)'
}

function formatHeatmapValueText(value: number | null, metric: HeatmapMetric): string {
  if (value == null) return ''
  if (metric === 'achievement') return `${value.toFixed(0)}%`
  if (metric === 'actualDiff') {
    // セル表示は千単位・小数1位
    const sen = value / 1000
    const sign = sen > 0 ? '+' : ''
    return `${sign}${sen.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 1 })}`
  }
  // actualQty は既に千単位
  return value.toLocaleString('ja-JP', { minimumFractionDigits: 0, maximumFractionDigits: 1 })
}

function heatmapMetricLabel(metric: HeatmapMetric): string {
  if (metric === 'achievement') return '計画達成率'
  if (metric === 'actualDiff') return '実績差異'
  return '実績数量'
}

const heatmapMonthLabel = computed(() => {
  const src = comparisonResult.value?.baselineMonth || compareForm.baselineMonth
  if (!src) return ''
  return dayjs(src).format('YYYY年MM月')
})

function buildHeatmapCells(metric: HeatmapMetric): HeatmapCell[] {
  const src = comparisonResult.value?.baselineMonth || compareForm.baselineMonth
  if (!src) return []
  const monthStart = dayjs(src).startOf('month')
  const daysInMonth = monthStart.daysInMonth()
  const leadPad = monthStart.day()

  const byDate = new Map<string, PlanBaselineComparisonItem>()
  for (const row of activeTrendItems.value) {
    if (row.plan_date) byDate.set(dayjs(row.plan_date).format('YYYY-MM-DD'), row)
  }

  let maxAbsDiff = 0
  let maxQty = 0
  for (const row of byDate.values()) {
    const diff = getHeatmapMetricValue(row, 'actualDiff')
    if (diff != null) maxAbsDiff = Math.max(maxAbsDiff, Math.abs(diff))
    const qty = getHeatmapMetricValue(row, 'actualQty')
    if (qty != null) maxQty = Math.max(maxQty, qty)
  }

  const cells: HeatmapCell[] = []
  for (let i = 0; i < leadPad; i++) {
    cells.push({
      isPad: true,
      date: '',
      day: '',
      value: null,
      valueText: '',
      bgColor: '',
      isAlert: false,
      tooltip: '',
    })
  }

  const metricLabel = heatmapMetricLabel(metric)
  for (let d = 1; d <= daysInMonth; d++) {
    const date = monthStart.date(d).format('YYYY-MM-DD')
    const row = byDate.get(date)
    const value = row ? getHeatmapMetricValue(row, metric) : null
    const isAlert = row ? isComparisonAlertRow(row) : false
    let displayText = formatHeatmapValueText(value, metric)
    let tipValue = displayText
    if (metric === 'actualDiff' && value != null) {
      tipValue = `${formatNumber(value)}（${displayText} 千）`
    } else if (metric === 'actualQty' && value != null) {
      tipValue = `${displayText} 千`
    } else if (metric === 'achievement' && value != null) {
      tipValue = `${value.toFixed(1)}%`
    }
    const tooltip = row
      ? `${formatDate(date)} ${activeTrendProcessLabel.value || ''}\n${metricLabel}: ${value == null ? '—' : tipValue}${isAlert ? '\n⚠ 閾値超過' : ''}`
      : `${formatDate(date)}：データなし`
    cells.push({
      isPad: false,
      date,
      day: d,
      value,
      valueText: displayText,
      bgColor: heatmapCellBackground(value, metric, { maxAbsDiff, maxQty }),
      isAlert,
      tooltip,
    })
  }
  return cells
}

const heatmapPanels = computed(() => [
  {
    key: 'achievement' as const,
    title: '計画達成率',
    unit: '',
    legend: '低 ← 達成率 → 高',
    cells: buildHeatmapCells('achievement'),
  },
  {
    key: 'actualDiff' as const,
    title: '実績差異',
    unit: '単位：千',
    legend: '負(赤) ← 差異 → 正(緑)',
    cells: buildHeatmapCells('actualDiff'),
  },
  {
    key: 'actualQty' as const,
    title: '実績数量',
    unit: '単位：千',
    legend: '少 ← 実績数量 → 多',
    cells: buildHeatmapCells('actualQty'),
  },
])

const periodCompareLoading = ref(false)
const periodComparePrev = ref<PlanBaselineComparisonResult | null>(null)
const periodCompareYoy = ref<PlanBaselineComparisonResult | null>(null)

function summaryAchievementPct(summary: PlanBaselineComparisonSummary | undefined | null): number | null {
  if (!summary) return null
  const plan = Number(summary.currentPlanTotal ?? 0)
  const actual = summary.currentActualTotal
  if (actual == null || plan === 0) return null
  return (Number(actual) / plan) * 100
}

function formatDeltaPct(current: number | null, other: number | null): string | null {
  if (current == null || other == null) return null
  const d = current - other
  const sign = d > 0 ? '+' : ''
  return `${sign}${d.toFixed(1)}pt`
}

function buildPeriodCompareBlock(
  key: string,
  label: string,
  monthLabel: string,
  result: PlanBaselineComparisonResult | null | undefined,
  opts?: { deltaVsPrev?: string | null; deltaVsYoy?: string | null },
) {
  const summary = result?.summary
  const achievementNum = summaryAchievementPct(summary)
  const actualDiffNum =
    summary?.actualDifference == null ? null : Number(summary.actualDifference)
  return {
    key,
    label,
    monthLabel,
    baselineText: summary?.baselinePlanTotal == null ? '—' : formatNumber(summary.baselinePlanTotal),
    achievementText: achievementNum == null ? '—' : `${achievementNum.toFixed(1)}%`,
    achievementNum,
    actualDiffText: actualDiffNum == null ? '—' : formatNumber(actualDiffNum),
    actualDiffNum,
    deltaVsPrev: opts?.deltaVsPrev ?? null,
    deltaVsYoy: opts?.deltaVsYoy ?? null,
  }
}

const periodCompareBlocks = computed(() => {
  const cur = comparisonResult.value
  const curMonth = compareForm.baselineMonth
    ? dayjs(compareForm.baselineMonth).format('YYYY年MM月')
    : '—'
  const prevMonth = compareForm.baselineMonth
    ? dayjs(compareForm.baselineMonth).subtract(1, 'month').format('YYYY年MM月')
    : '—'
  const yoyMonth = compareForm.baselineMonth
    ? dayjs(compareForm.baselineMonth).subtract(1, 'year').format('YYYY年MM月')
    : '—'

  const curAch = summaryAchievementPct(cur?.summary)
  const prevAch = summaryAchievementPct(periodComparePrev.value?.summary)
  const yoyAch = summaryAchievementPct(periodCompareYoy.value?.summary)

  return [
    buildPeriodCompareBlock('current', '当月', curMonth, cur, {
      deltaVsPrev: formatDeltaPct(curAch, prevAch),
      deltaVsYoy: formatDeltaPct(curAch, yoyAch),
    }),
    buildPeriodCompareBlock('prev', '前月', prevMonth, periodComparePrev.value),
    buildPeriodCompareBlock('yoy', '前年同月', yoyMonth, periodCompareYoy.value),
  ]
})

async function loadPeriodCompare() {
  if (!compareForm.baselineMonth) {
    periodComparePrev.value = null
    periodCompareYoy.value = null
    return
  }
  periodCompareLoading.value = true
  try {
    const base = dayjs(compareForm.baselineMonth).startOf('month')
    const processName = compareForm.processName || undefined
    const [prevRes, yoyRes] = await Promise.all([
      fetchPlanBaselineComparison({
        baselineMonth: base.subtract(1, 'month').format('YYYY-MM-DD'),
        processName,
      }),
      fetchPlanBaselineComparison({
        baselineMonth: base.subtract(1, 'year').format('YYYY-MM-DD'),
        processName,
      }),
    ])
    periodComparePrev.value = prevRes
    periodCompareYoy.value = yoyRes
  } catch {
    periodComparePrev.value = null
    periodCompareYoy.value = null
  } finally {
    periodCompareLoading.value = false
  }
}

function buildTrendChartOption(items: PlanBaselineComparisonItem[]) {
  const labels = items.map((row) => {
    const d = row.plan_date ? dayjs(row.plan_date).format('MM/DD') : ''
    return d
  })
  const baselineSeries = items.map((row) => toTrendUnit(row.baseline_plan ?? 0) ?? 0)
  const actualSeries = items.map((row) => toTrendUnit(row.current_actual))
  // 差異 = 実績 − 基準計画（実績がない日は null）
  const diffSeries = items.map((row, i) => {
    if (row.current_actual == null) return null
    if (row.actual_diff != null && row.actual_diff !== undefined) {
      return toTrendUnit(row.actual_diff)
    }
    return (actualSeries[i] ?? 0) - baselineSeries[i]
  })

  const showDiffLabels = trendShowDiffBars.value
  const showQtyLabels = trendShowValueLabels.value
  const dayCount = Math.max(items.length, 1)
  // 日付数に応じて柱幅・文字サイズを自動調整（整行を使い切る）
  const barMaxWidth = dayCount <= 10 ? 36 : dayCount <= 16 ? 24 : dayCount <= 22 ? 18 : dayCount <= 31 ? 14 : 10
  const barCategoryGap = dayCount <= 12 ? '36%' : dayCount <= 20 ? '26%' : '16%'
  const barGap = dayCount <= 16 ? '18%' : '12%'
  const axisFontSize = dayCount > 24 ? 9 : 10
  const axisRotate = dayCount > 28 ? 35 : 0
  const dense = dayCount > 20
  const barLabel = {
    show: showQtyLabels,
    position: 'top' as const,
    fontSize: dense ? 9 : 10,
    color: '#475569',
    rotate: 0,
    distance: 4,
    hideOverlap: true,
    formatter: (p: { value?: number | null }) =>
      p.value == null || p.value === 0 ? '' : formatTrendUnit(p.value, 1),
  }

  const series: Array<Record<string, unknown>> = [
    {
      name: '基準計画',
      type: 'bar',
      z: 2,
      data: baselineSeries,
      barMaxWidth,
      barGap,
      barCategoryGap,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#5eead4' },
          { offset: 1, color: '#0d9488' },
        ]),
        borderRadius: [3, 3, 0, 0],
      },
      label: { ...barLabel, color: '#0f766e' },
      emphasis: { focus: 'series' as const },
    },
    {
      name: '実績',
      type: 'bar',
      z: 2,
      data: actualSeries,
      barMaxWidth,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#93c5fd' },
          { offset: 1, color: '#2563eb' },
        ]),
        borderRadius: [3, 3, 0, 0],
      },
      label: { ...barLabel, color: '#1d4ed8' },
      emphasis: { focus: 'series' as const },
    },
  ]

  if (showDiffLabels) {
    // Scatter（已注册）で柱ペア中央に差異を表示。CustomChart 未登録のためこちらを使う
    series.push({
      name: '差異(実績−基準)',
      type: 'scatter',
      z: 10,
      symbol: 'circle',
      symbolSize: 0,
      itemStyle: { color: 'transparent' },
      emphasis: { disabled: true },
      tooltip: { show: false },
      label: { show: true },
      labelLayout: { hideOverlap: false },
      data: labels.map((lab, i) => {
        const diff = diffSeries[i]
        if (diff == null) {
          return { value: [lab, null], label: { show: false } }
        }
        const taller = Math.max(baselineSeries[i], Number(actualSeries[i] ?? 0))
        const midY = taller > 0 ? taller * 0.55 : 0.1
        const sign = diff > 0 ? '+' : ''
        const fill = diff > 0 ? '#15803d' : diff < 0 ? '#dc2626' : '#64748b'
        return {
          value: [lab, midY],
          diff,
          label: {
            show: true,
            formatter: `${sign}${formatTrendUnit(diff, 1)}`,
            color: fill,
            fontSize: dense ? 9 : 11,
            fontWeight: 700,
            backgroundColor: 'rgba(255, 255, 255, 0.94)',
            borderColor: fill,
            borderWidth: 1,
            borderRadius: 4,
            padding: [2, 5],
            align: 'center',
            verticalAlign: 'middle',
          },
        }
      }),
    })
  }

  const legendData = ['基準計画', '実績', ...(showDiffLabels ? ['差異(実績−基準)'] : [])]

  return {
    animationDuration: 420,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'axis' as const,
      axisPointer: { type: 'shadow' as const },
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: (params: unknown) => {
        const list = Array.isArray(params) ? params : [params]
        if (!list.length) return ''
        const head = String(
          (list[0] as { axisValueLabel?: string; name?: string }).axisValueLabel
            ?? (list[0] as { name?: string }).name
            ?? '',
        )
        const lines = [`<div style="margin-bottom:4px;font-weight:700">${head}</div>`]
        for (const raw of list) {
          const p = raw as {
            seriesName?: string
            seriesType?: string
            marker?: string
            dataIndex?: number
            value?: unknown
          }
          if (p.seriesType === 'scatter' || p.seriesName === '差異(実績−基準)') continue
          const val = Array.isArray(p.value) ? p.value[1] : p.value
          const text =
            val == null || val === '' ? '—' : `${formatTrendUnit(Number(val), 1)} 千`
          lines.push(
            `<div style="display:flex;gap:8px;align-items:center">${p.marker ?? ''}<span>${p.seriesName ?? ''}</span><span style="margin-left:auto;font-variant-numeric:tabular-nums">${text}</span></div>`,
          )
        }
        const idx = (list[0] as { dataIndex?: number }).dataIndex
        if (showDiffLabels && idx != null) {
          const diff = diffSeries[idx]
          if (diff != null) {
            const sign = diff > 0 ? '+' : ''
            const color = diff > 0 ? '#4ade80' : diff < 0 ? '#f87171' : '#e2e8f0'
            lines.push(
              `<div style="margin-top:4px;padding-top:4px;border-top:1px solid rgba(148,163,184,0.35);display:flex;gap:8px"><span style="color:${color}">●</span><span>差異(実績−基準)</span><span style="margin-left:auto;color:${color};font-weight:700;font-variant-numeric:tabular-nums">${sign}${formatTrendUnit(diff, 1)} 千</span></div>`,
            )
          }
        }
        return lines.join('')
      },
    },
    legend: {
      data: legendData,
      top: 2,
      left: 'center',
      orient: 'horizontal' as const,
      itemGap: 18,
      itemWidth: 14,
      itemHeight: 8,
      textStyle: { fontSize: 11, color: '#475569', padding: [0, 0, 0, 2] },
      width: '90%',
    },
    grid: {
      left: 8,
      right: 12,
      top: showQtyLabels || showDiffLabels ? 48 : 40,
      bottom: axisRotate ? 42 : 28,
      containLabel: true,
    },
    xAxis: {
      type: 'category' as const,
      data: labels,
      boundaryGap: true,
      axisLabel: {
        interval: 0,
        fontSize: axisFontSize,
        color: '#64748b',
        rotate: axisRotate,
        hideOverlap: false,
        margin: 10,
      },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    yAxis: {
      type: 'value' as const,
      name: '数量（千）',
      nameLocation: 'middle' as const,
      nameGap: 42,
      nameTextStyle: { fontSize: 10, color: '#94a3b8' },
      min: 0,
      splitLine: { lineStyle: { type: 'dashed' as const, color: '#e2e8f0' } },
      axisLabel: {
        fontSize: 10,
        color: '#64748b',
        formatter: (v: number) => formatTrendUnit(v, 1),
      },
    },
    series,
  }
}

function renderTrendChart() {
  const items = activeTrendItems.value
  if (!items.length) {
    if (trendChart) {
      trendChart.dispose()
      trendChart = null
    }
    return
  }
  if (!trendChartRef.value) return
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value, undefined, { renderer: 'canvas' })
  }
  trendChart.setOption(buildTrendChartOption(items), true)
  // 整行幅に合わせて再計算（日付カテゴリを均等配置）
  trendChart.resize()
}

function onTrendChartResize() {
  trendChart?.resize()
}

watch(
  [activeTrendItems, trendShowDiffBars, trendShowValueLabels],
  async () => {
    await nextTick()
    renderTrendChart()
  },
  { deep: true },
)

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD')
}

function summaryToneIcon(tone: string) {
  switch (tone) {
    case 'baseline':
      return Document
    case 'current':
      return DataLine
    case 'diff':
      return TrendCharts
    case 'actual':
      return CircleCheck
    case 'actual-diff':
      return DataAnalysis
    case 'rate':
      return DataAnalysis
    case 'rate-diff':
      return TrendCharts
    default:
      return DataLine
  }
}

const summaryCards = computed(() => {
  const summary = comparisonResult.value?.summary

  if (!summary) {
    return [
      {
        label: '基準計画合計',
        value: '-',
        isNegative: false,
        description: 'ベースライン計画合計',
        tone: 'baseline',
      },
      {
        label: '変更計画合計',
        value: '-',
        isNegative: false,
        description: '最新計画合計',
        tone: 'current',
      },
      {
        label: '計画差異',
        value: '-',
        isNegative: false,
        description: '変更計画 - ベースライン計画',
        tone: 'diff',
      },
      {
        label: '実績合計',
        value: '-',
        isNegative: false,
        description: '最新実績合計',
        tone: 'actual',
      },
      {
        label: '計画対実績差',
        value: '-',
        isNegative: false,
        description: 'ベースライン計画 - 実績',
        tone: 'actual-diff',
      },
      {
        label: '計画達成率',
        value: '-',
        isNegative: false,
        description: '実績 ÷ 変更計画',
        tone: 'rate',
      },
      {
        label: '達成率差異',
        value: '-',
        isNegative: false,
        description: '計画対実績差 ÷ 基準計画合計',
        tone: 'rate-diff',
      },
    ]
  }

  const currentPlanTotal = summary.currentPlanTotal ?? 0
  const currentActualTotal = summary.currentActualTotal ?? 0
  const baselinePlanTotal = summary.baselinePlanTotal ?? 0
  const planDifference = summary.planDifference ?? 0
  const actualDifference = summary.actualDifference ?? 0

  const planAchievement =
    currentPlanTotal === 0 ? null : (currentActualTotal / currentPlanTotal) * 100

  const achievementDifference =
    baselinePlanTotal === 0 ? null : (actualDifference / baselinePlanTotal) * 100

  return [
    {
      label: '基準計画合計',
      value: formatNumber(summary.baselinePlanTotal),
      isNegative: baselinePlanTotal < 0,
      description: 'ベースライン計画合計',
      tone: 'baseline',
    },
    {
      label: '変更計画合計',
      value: formatNumber(summary.currentPlanTotal),
      isNegative: currentPlanTotal < 0,
      description: '最新計画合計',
      tone: 'current',
    },
    {
      label: '計画差異',
      value: formatNumber(summary.planDifference),
      isNegative: planDifference < 0,
      description: '変更計画 - ベースライン計画',
      tone: 'diff',
    },
    {
      label: '実績合計',
      value: summary.currentActualTotal === null ? '-' : formatNumber(summary.currentActualTotal),
      isNegative: false,
      description: '最新実績合計',
      tone: 'actual',
    },
    {
      label: '計画対実績差',
      value: summary.actualDifference == null ? '-' : formatNumber(summary.actualDifference),
      isNegative: actualDifference !== 0 && actualDifference < 0,
      description: 'ベースライン計画 - 実績',
      tone: 'actual-diff',
    },
    {
      label: '計画達成率',
      value: planAchievement === null ? '-' : `${planAchievement.toFixed(1)}%`,
      isNegative: planAchievement !== null && planAchievement < 100,
      description: '実績 ÷ 変更計画',
      tone: 'rate',
    },
    {
      label: '達成率差異',
      value: achievementDifference === null ? '-' : `${achievementDifference.toFixed(2)}%`,
      isNegative: achievementDifference !== null && achievementDifference < 0,
      description: '計画対実績差 ÷ 基準計画合計',
      tone: 'rate-diff',
    },
  ]
})

const formatNumber = (value: number | string | null | undefined) => {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toLocaleString('ja-JP')
}


const openAdjustmentDialog = () => {
  adjustmentForm.baselineMonth = generateForm.baselineMonth
  adjustmentForm.processName = generateForm.processName || ''
  adjustmentItems.value = []
  planInputRefs.value = []
  resetAdjustmentAddForm()
  adjustmentDialogVisible.value = true
  nextTick(() => {
    loadAdjustmentRecords()
  })
}

const resetAdjustmentForm = () => {
  adjustmentForm.baselineMonth = generateForm.baselineMonth
  adjustmentForm.processName = ''
  adjustmentItems.value = []
  planInputRefs.value = []
  resetAdjustmentAddForm()
}

const loadAdjustmentRecords = async () => {
  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }
  adjustmentLoading.value = true
  try {
    const records = await fetchPlanBaselineRecords({
      baselineMonth: adjustmentForm.baselineMonth,
      processName: adjustmentForm.processName || undefined,
    })
    adjustmentItems.value = records.map((record) => ({
      ...record,
      plan_date: record.plan_date ? dayjs(record.plan_date).format('YYYY-MM-DD') : record.plan_date,
      process_name: record.process_name || '',
      tempPlanQuantity: Number(record.plan_quantity ?? 0),
      saving: false,
      deleting: false,
      isNew: false,
    }))
    if (records.length === 0) {
      ElMessage.info('該当データがありません。上のパネルから日付を追加できます')
    }
    planInputRefs.value = []
    if (!adjustmentAddForm.processName) {
      resetAdjustmentAddForm()
    } else if (adjustmentForm.processName) {
      adjustmentAddForm.processName = adjustmentForm.processName
    }
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースラインデータの取得に失敗しました')
  } finally {
    adjustmentLoading.value = false
  }
}

const handleAddAdjustmentDate = async () => {
  if (!guardApsOperation(canEdit)) return
  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }
  const planDate = adjustmentAddForm.planDate
  const processName = (adjustmentAddForm.processName || '').trim()
  const qty = adjustmentAddForm.planQuantity
  if (!planDate) {
    ElMessage.warning('追加する日付を選択してください')
    return
  }
  if (!processName) {
    ElMessage.warning('工程を選択してください')
    return
  }
  if (qty == null || Number.isNaN(Number(qty)) || Number(qty) < 0) {
    ElMessage.warning('基準計画数を入力してください（0以上）')
    return
  }

  const month = dayjs(adjustmentForm.baselineMonth)
  const d = dayjs(planDate)
  if (d.year() !== month.year() || d.month() !== month.month()) {
    ElMessage.warning('日付は基準月の範囲内にしてください')
    return
  }

  const existing = adjustmentItems.value.find(
    (item) =>
      item.plan_date === planDate && (item.process_name || '') === processName,
  )
  if (existing) {
    existing.tempPlanQuantity = Number(qty)
    ElMessage.info('既存行の数量を更新しました。保存してください')
    return
  }

  adjustmentAdding.value = true
  try {
    const res = await updatePlanBaselinePlanQuantity({
      baselineMonth: adjustmentForm.baselineMonth,
      planDate,
      processName,
      planQuantity: Number(qty),
    })
    adjustmentItems.value.push({
      plan_date: planDate,
      process_name: processName,
      plan_quantity: Number(qty),
      actual_quantity: 0,
      machine_name: '',
      product_cd: '',
      product_name: '',
      tempPlanQuantity: Number(qty),
      saving: false,
      deleting: false,
      isNew: true,
    })
    adjustmentItems.value.sort((a, b) => {
      const da = `${a.plan_date}|${a.process_name || ''}`
      const db = `${b.plan_date}|${b.process_name || ''}`
      return da.localeCompare(db)
    })
    adjustmentAddForm.planQuantity = null
    ElMessage.success(res.created ? '日付を追加しました' : '数量を更新しました')
    void loadComparison()
  } catch (error: any) {
    ElMessage.error(error?.message || '日付の追加に失敗しました')
  } finally {
    adjustmentAdding.value = false
  }
}

const handleUpdatePlanQuantity = async (row: PlanBaselineAdjustmentItem) => {
  if (!guardApsOperation(canEdit)) return

  const planQuantity = Number(row.tempPlanQuantity)
  if (Number.isNaN(planQuantity)) {
    ElMessage.warning('数値を入力してください')
    return
  }
  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }
  if (!(row.process_name || '').trim()) {
    ElMessage.warning('工程が未設定のため保存できません')
    return
  }
  row.saving = true
  try {
    await updatePlanBaselinePlanQuantity({
      baselineMonth: adjustmentForm.baselineMonth,
      planDate: row.plan_date,
      processName: row.process_name || undefined,
      planQuantity,
    })
    row.plan_quantity = planQuantity
    row.isNew = false
    ElMessage.success('修正しました')
    void loadComparison()
  } catch (error: any) {
    ElMessage.error(error?.message || '修正に失敗しました')
  } finally {
    row.saving = false
  }
}

const handleDeleteBaselineRecord = async (row: PlanBaselineAdjustmentItem) => {
  if (!guardApsOperation(canDelete)) return

  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }
  const dateLabel = formatDate(row.plan_date)
  const procLabel = row.process_name || '未指定'
  try {
    await ElMessageBox.confirm(
      `「${dateLabel}」・工程「${procLabel}」のベースライン行を削除します。よろしいですか？`,
      '削除の確認',
      {
        type: 'warning',
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
      },
    )
  } catch {
    return
  }
  row.deleting = true
  try {
    await deletePlanBaselineRecord({
      baselineMonth: adjustmentForm.baselineMonth,
      planDate: row.plan_date,
      processName: row.process_name || '',
    })
    adjustmentItems.value = adjustmentItems.value.filter(
      (item) =>
        !(
          item.plan_date === row.plan_date &&
          (item.process_name || '') === (row.process_name || '')
        ),
    )
    planInputRefs.value = []
    ElMessage.success('削除しました')
    await loadComparison()
  } catch (error: any) {
    ElMessage.error(error?.message || '削除に失敗しました')
  } finally {
    row.deleting = false
  }
}

const handleBatchSave = async () => {
  if (!guardApsOperation(canCreate)) return

  if (adjustmentItems.value.length === 0) {
    ElMessage.warning('修正対象のデータがありません')
    return
  }

  const modifiedRows = adjustmentItems.value.filter(
    (item) => Number(item.tempPlanQuantity) !== Number(item.plan_quantity),
  )

  if (modifiedRows.length === 0) {
    ElMessage.info('変更された項目がありません')
    return
  }

  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }

  try {
    for (const row of modifiedRows) {
      await handleUpdatePlanQuantity(row)
    }
    ElMessage.success('一括で保存しました')
  } catch (error) {
    // handleUpdatePlanQuantity 内でメッセージ済み
  }
}

const setPlanInputRef = (el: any, index: number) => {
  if (!el) return
  nextTick(() => {
    const inputEl = el.$el?.querySelector('input')
    planInputRefs.value[index] = (inputEl as HTMLInputElement) || null
  })
}

const focusPlanInput = (index: number) => {
  if (index < 0 || index >= planInputRefs.value.length) return
  const inputEl = planInputRefs.value[index]
  if (inputEl) {
    inputEl.focus()
    if (typeof inputEl.select === 'function') {
      inputEl.select()
    }
  }
}

const handlePlanInputKeydown = (event: KeyboardEvent, index: number) => {
  const key = event.key
  let targetIndex: number | null = null
  if (key === 'ArrowDown' || key === 'Enter') {
    targetIndex = Math.min(index + 1, adjustmentDisplayItems.value.length - 1)
  } else if (key === 'ArrowUp') {
    targetIndex = Math.max(index - 1, 0)
  } else if (key === 'ArrowRight') {
    targetIndex = Math.min(index + 1, adjustmentDisplayItems.value.length - 1)
  } else if (key === 'ArrowLeft') {
    targetIndex = Math.max(index - 1, 0)
  }

  if (targetIndex !== null && targetIndex !== index) {
    event.preventDefault()
    focusPlanInput(targetIndex)
  }
}

const getDiffClass = (value: number | string | null | undefined) => {
  if (value === null || value === undefined || value === '') return ''
  const num = Number(value)
  if (Number.isNaN(num)) return ''
  if (num > 0) return 'diff-positive'
  if (num < 0) return 'diff-negative'
  return 'diff-zero'
}

let compareLoadTimer: ReturnType<typeof setTimeout> | null = null

function scheduleCompareLoad() {
  if (!compareForm.baselineMonth) return
  if (compareLoadTimer) clearTimeout(compareLoadTimer)
  compareLoadTimer = setTimeout(() => {
    compareLoadTimer = null
    void loadComparison()
  }, 280)
}

const loadComparison = async () => {
  if (!compareForm.baselineMonth) return
  tableLoading.value = true
  try {
    const data = await fetchPlanBaselineComparison({
      baselineMonth: compareForm.baselineMonth,
      processName: compareForm.processName || undefined,
    })
    comparisonResult.value = data
    comparisonItems.value = data?.items ?? []
    void loadPeriodCompare()
  } catch (error: any) {
    ElMessage.error(error?.message || '比較データの取得に失敗しました')
    periodComparePrev.value = null
    periodCompareYoy.value = null
  } finally {
    tableLoading.value = false
  }
}

/** 生成後に比較条件を揃え、一覧を再読込する */
const syncCompareFromGenerate = async (opts?: { silent?: boolean; reload?: boolean }) => {
  compareForm.baselineMonth = generateForm.baselineMonth
  compareForm.processName = generateForm.processName
  if (opts?.reload !== false) {
    scheduleCompareLoad()
  }
}

const runGeneratePlanBaseline = async (payload: Parameters<typeof generatePlanBaseline>[0]) => {
  if (!guardApsOperation(canCreate)) return

  generating.value = true
  try {
    await generatePlanBaseline(payload)
    ElMessage.success('ベースラインを生成しました')
    await syncCompareFromGenerate({ silent: true })
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースライン生成に失敗しました')
  } finally {
    generating.value = false
  }
}

const submitFixedBaselineGenerate = async () => {
  if (!guardApsOperation(canCreate)) return

  const dates = [...fixedBaselineForm.selectedDates].sort()
  const qty = fixedBaselineForm.planQuantity
  if (!dates.length) {
    ElMessage.warning('反映する日付を1日以上選択してください')
    return
  }
  if (qty == null || Number.isNaN(Number(qty)) || Number(qty) < 0) {
    ElMessage.warning('基準計画数を入力してください（0以上）')
    return
  }

  fixedBaselineDialogVisible.value = false
  await runGeneratePlanBaseline({
    baselineMonth: generateForm.baselineMonth,
    processName: fixedBaselineTargetProcess.value || undefined,
    planDates: dates,
    planQuantity: Number(qty),
  })
}

const handleGenerate = async () => {
  if (!guardApsOperation(canCreate)) return

  if (!generateForm.baselineMonth) {
    ElMessage.warning('対象月を選択してください')
    return
  }

  // 切断・面取・メッキ・検査：手入力ダイアログへ（確認はダイアログ内で実施）
  if (FIXED_BASELINE_PROCESS_NAMES.has(generateForm.processName)) {
    fixedBaselineTargetProcess.value = generateForm.processName
    resetFixedBaselineForm()
    fixedBaselineDialogVisible.value = true
    return
  }

  const processLabel = generateForm.processName || '成型・溶接・溶接SP（自動集計）'
  try {
    await ElMessageBox.confirm(
      `<div class="pb-confirm-box">
        <p class="pb-confirm-box__lead">対象月のベースラインを再生成します。</p>
        <p class="pb-confirm-box__warn">既存の自動集計データは上書きされます。切断・面取・メッキ・検査の手入力分は保持されます。</p>
        <p class="pb-confirm-box__meta">${dayjs(generateForm.baselineMonth).format('YYYY年MM月')}　／　${processLabel}</p>
      </div>`,
      'ベースライン生成の確認',
      {
        type: 'warning',
        dangerouslyUseHTMLString: true,
        confirmButtonText: '生成',
        cancelButtonText: 'キャンセル',
        customClass: 'pb-confirm-dialog',
      },
    )
  } catch {
    return
  }

  await runGeneratePlanBaseline({
    baselineMonth: generateForm.baselineMonth,
    processName: generateForm.processName || undefined,
  })
}

const handleDeleteBaseline = async () => {
  if (!guardApsOperation(canDelete)) return

  if (!generateForm.baselineMonth) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  const confirmMessage = generateForm.processName
    ? `基準月「${dayjs(generateForm.baselineMonth).format('YYYY年MM月')}」の「${generateForm.processName}」ベースラインを削除します。よろしいですか？`
    : `基準月「${dayjs(generateForm.baselineMonth).format('YYYY年MM月')}」の全工程ベースラインを削除します。よろしいですか？`
  try {
    await ElMessageBox.confirm(
      `<div class="pb-confirm-box">
        <p class="pb-confirm-box__lead">${confirmMessage}</p>
        <p class="pb-confirm-box__warn">この操作は取り消せません。</p>
      </div>`,
      'ベースライン削除の確認',
      {
        type: 'warning',
        dangerouslyUseHTMLString: true,
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        customClass: 'pb-confirm-dialog',
      },
    )
  } catch {
    return
  }

  deleting.value = true
  try {
    await deletePlanBaseline({
      baselineMonth: generateForm.baselineMonth,
      processName: generateForm.processName || undefined,
    })
    ElMessage.success('ベースラインを削除しました')
    await syncCompareFromGenerate({ silent: true })
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースライン削除に失敗しました')
  } finally {
    deleting.value = false
  }
}

/** 限定並列で Promise を実行（同時に複数 html2canvas だとメモリを食うため上限付き） */
async function runWithConcurrency<T, R>(
  items: T[],
  concurrency: number,
  worker: (item: T, index: number) => Promise<R>,
): Promise<R[]> {
  if (items.length === 0) return []
  const results: R[] = new Array(items.length)
  let next = 0
  const limit = Math.max(1, Math.min(concurrency, items.length))
  const runWorker = async () => {
    if (!guardApsOperation(canEdit)) return

    while (true) {
      const i = next++
      if (i >= items.length) return
      results[i] = await worker(items[i], i)
    }
  }
  await Promise.all(Array.from({ length: limit }, () => runWorker()))
  return results
}

/** 次の描画フレームまで待機（ECharts の初回レンダ完了を待つ。固定 setTimeout より短くなりがち） */
function nextFrames(n = 2): Promise<void> {
  return new Promise((resolve) => {
    let c = 0
    const step = () => {
      c++
      if (c >= n) resolve()
      else requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  })
}

/** html2canvas の解像度（速度と可読性のバランス） */
const PDF_TABLE_CANVAS_SCALE = 1.75
/** チャート出力の pixelRatio 上限 */
const PDF_CHART_PIXEL_RATIO = 1.75
/** 日語対応フォント（html2canvas 用・jsPDF の text は使わない） */
const PDF_JP_FONT =
  '"Yu Gothic UI","Yu Gothic","Hiragino Sans","Hiragino Kaku Gothic ProN","Meiryo","MS PGothic",sans-serif'

type PdfProcessTotals = {
  baselinePlan: number
  currentPlan: number
  planDiff: number
  currentActual: number
  actualDiff: number
}

async function captureHtmlToCanvas(html: string, widthPx = 760): Promise<HTMLCanvasElement> {
  const wrap = document.createElement('div')
  wrap.style.cssText = `position:fixed;left:-9999px;top:0;z-index:-1;width:${widthPx}px;`
  wrap.innerHTML = html
  document.body.appendChild(wrap)
  const el = wrap.firstElementChild as HTMLElement | null
  if (!el) {
    wrap.remove()
    throw new Error('PDF用要素の作成に失敗しました')
  }
  try {
    const canvas = await html2canvas(el, {
      scale: PDF_TABLE_CANVAS_SCALE,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
      width: widthPx,
      windowWidth: widthPx,
      onclone: (clonedDoc) => {
        clonedDoc.body.style.fontFamily = PDF_JP_FONT
        clonedDoc.documentElement.style.fontFamily = PDF_JP_FONT
      },
    })
    return canvas
  } finally {
    wrap.remove()
  }
}

function addCanvasToPdf(
  doc: jsPDF,
  canvas: HTMLCanvasElement,
  opts?: { newPage?: boolean; margin?: number; fitOnePage?: boolean },
) {
  const margin = opts?.margin ?? 4
  const pageW = doc.internal.pageSize.getWidth()
  const pageH = doc.internal.pageSize.getHeight()
  const contentW = pageW - margin * 2
  const contentH = pageH - margin * 2
  const imgW = canvas.width
  const imgH = canvas.height

  if (opts?.newPage) doc.addPage()

  // 1ページに収める（上寄せ・余白を最小化）
  if (opts?.fitOnePage) {
    const scale = Math.min(contentW / imgW, contentH / imgH)
    const drawW = imgW * scale
    const drawH = imgH * scale
    const x = margin + (contentW - drawW) / 2
    const y = margin // 上下中央揃えだと空白が大きく見えるため上寄せ
    doc.addImage(canvas.toDataURL('image/png'), 'PNG', x, y, drawW, drawH)
    return
  }

  const scale = contentW / imgW
  const scaledH = imgH * scale

  if (scaledH <= contentH) {
    doc.addImage(canvas.toDataURL('image/png'), 'PNG', margin, margin, contentW, scaledH)
    return
  }

  let drawn = 0
  let pageIndex = 0
  while (drawn < imgH) {
    if (pageIndex > 0) doc.addPage()
    const sliceH = Math.min(contentH / scale, imgH - drawn)
    const sourceCanvas = document.createElement('canvas')
    sourceCanvas.width = imgW
    sourceCanvas.height = Math.ceil(sliceH)
    const ctx = sourceCanvas.getContext('2d')
    if (ctx) {
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, sourceCanvas.width, sourceCanvas.height)
      ctx.drawImage(canvas, 0, drawn, imgW, sliceH, 0, 0, imgW, sliceH)
      doc.addImage(
        sourceCanvas.toDataURL('image/png'),
        'PNG',
        margin,
        margin,
        contentW,
        sliceH * scale,
      )
    }
    drawn += sliceH
    pageIndex++
  }
}

function pdfFmtNum(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return formatNumber(v) as string
}

function pdfFmtPct(v: number | null): string {
  return v == null ? '—' : `${v.toFixed(1)}%`
}

function buildHeatmapCellsForItems(
  items: PlanBaselineComparisonItem[],
  metric: HeatmapMetric,
  baselineMonth: string,
  processLabel: string,
): HeatmapCell[] {
  const monthStart = dayjs(baselineMonth).startOf('month')
  const daysInMonth = monthStart.daysInMonth()
  const leadPad = monthStart.day()
  const byDate = new Map<string, PlanBaselineComparisonItem>()
  for (const row of items) {
    if (row.plan_date) byDate.set(dayjs(row.plan_date).format('YYYY-MM-DD'), row)
  }
  let maxAbsDiff = 0
  let maxQty = 0
  for (const row of byDate.values()) {
    const diff = getHeatmapMetricValue(row, 'actualDiff')
    if (diff != null) maxAbsDiff = Math.max(maxAbsDiff, Math.abs(diff))
    const qty = getHeatmapMetricValue(row, 'actualQty')
    if (qty != null) maxQty = Math.max(maxQty, qty)
  }
  const cells: HeatmapCell[] = []
  for (let i = 0; i < leadPad; i++) {
    cells.push({
      isPad: true,
      date: '',
      day: '',
      value: null,
      valueText: '',
      bgColor: '',
      isAlert: false,
      tooltip: '',
    })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const date = monthStart.date(d).format('YYYY-MM-DD')
    const row = byDate.get(date)
    const value = row ? getHeatmapMetricValue(row, metric) : null
    const isAlert = row ? isComparisonAlertRow(row) : false
    cells.push({
      isPad: false,
      date,
      day: d,
      value,
      valueText: formatHeatmapValueText(value, metric),
      bgColor: heatmapCellBackground(value, metric, { maxAbsDiff, maxQty }),
      isAlert,
      tooltip: '',
    })
  }
  while (cells.length % 7 !== 0) {
    cells.push({
      isPad: true,
      date: '',
      day: '',
      value: null,
      valueText: '',
      bgColor: '',
      isAlert: false,
      tooltip: '',
    })
  }
  void processLabel
  return cells
}

function renderHeatmapPanelHtml(
  title: string,
  unit: string,
  legend: string,
  cells: HeatmapCell[],
  key: string,
  compact = false,
): string {
  const cellH = compact ? 32 : 42
  const dayFs = compact ? 8.5 : 10
  const valFs = compact ? 8 : 9
  const gap = compact ? 3 : 4
  const wd = heatmapWeekdayLabels
    .map((w, i) => {
      const color = i === 0 ? '#dc2626' : i === 6 ? '#2563eb' : '#64748b'
      return `<span style="text-align:center;font-size:${compact ? 8 : 10}px;font-weight:800;color:${color};">${w}</span>`
    })
    .join('')
  const grid = cells
    .map((cell) => {
      if (cell.isPad) {
        return `<div style="height:${cellH}px;border-radius:6px;"></div>`
      }
      const bg = cell.bgColor || '#f1f5f9'
      const alert = cell.isAlert ? 'outline:1.5px solid #f59e0b;outline-offset:-1px;' : ''
      return `<div style="height:${cellH}px;border-radius:6px;background:${bg};${alert}display:flex;flex-direction:column;align-items:center;justify-content:center;padding:1px;">
        <div style="font-size:${dayFs}px;font-weight:800;color:#0f172a;line-height:1;">${cell.day}</div>
        <div style="font-size:${valFs}px;font-weight:700;color:#334155;margin-top:1px;font-variant-numeric:tabular-nums;">${cell.valueText || ''}</div>
      </div>`
    })
    .join('')
  const unitHtml = unit
    ? `<span style="font-size:8px;font-weight:700;color:#0f766e;background:rgba(13,148,136,0.1);border:1px solid rgba(13,148,136,0.22);border-radius:999px;padding:1px 5px;">${unit}</span>`
    : ''
  void key
  return `<div style="flex:1;min-width:0;padding:${compact ? 5 : 8}px;border-radius:10px;border:1px solid #e2e8f0;background:linear-gradient(180deg,#fff,#f8fafc);">
    <div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-bottom:4px;position:relative;min-height:16px;">
      <div style="font-size:${compact ? 10 : 12}px;font-weight:800;color:#0f172a;">${title}</div>
      <div style="position:absolute;right:0;top:0;">${unitHtml}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:${gap}px;margin-bottom:2px;">${wd}</div>
    <div style="display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:${gap}px;">${grid}</div>
    <div style="margin-top:4px;font-size:8px;color:#64748b;font-weight:650;">${legend}</div>
  </div>`
}

function renderCompactDetailTableHtml(opts: {
  processName: string
  monthLabel: string
  rows: PlanBaselineComparisonItem[]
  totals: {
    baseline: number
    currentPlan: number
    planDiff: number
    currentActual: number
    actualDiff: number
  }
}): string {
  const numCell = (value: number | string | null | undefined) => {
    const n = value != null && value !== '' ? Number(value) : NaN
    const red = !Number.isNaN(n) && n < 0 ? 'color:#dc2626;font-weight:700;' : ''
    return `style="border:1px solid #dbe3ee;padding:5px 5px;text-align:right;font-variant-numeric:tabular-nums;${red}"`
  }
  const thead = `<thead>
        <tr style="background:linear-gradient(135deg,#0f766e 0%,#0d9488 45%,#0284c7 100%);color:#fff;font-weight:800;">
          <th style="border:1px solid rgba(255,255,255,0.2);padding:6px 5px;text-align:left;">日付</th>
          <th style="border:1px solid rgba(255,255,255,0.2);padding:6px 5px;text-align:right;">基準計画</th>
          <th style="border:1px solid rgba(255,255,255,0.2);padding:6px 5px;text-align:right;">変更計画</th>
          <th style="border:1px solid rgba(255,255,255,0.2);padding:6px 5px;text-align:right;">計画差異</th>
          <th style="border:1px solid rgba(255,255,255,0.2);padding:6px 5px;text-align:right;">実績</th>
          <th style="border:1px solid rgba(255,255,255,0.2);padding:6px 5px;text-align:right;">計画対実績差</th>
        </tr>
      </thead>`
  const renderRows = (rows: PlanBaselineComparisonItem[], startIdx: number) =>
    rows
      .map((row, i) => {
        const idx = startIdx + i
        const alert = isComparisonAlertRow(row)
        const rowBg = alert ? '#fff7ed' : idx % 2 === 0 ? '#f8fafc' : '#ffffff'
        const alertMark = alert
          ? `<span style="margin-left:3px;color:#b45309;font-weight:800;">!</span>`
          : ''
        return `<tr style="background:${rowBg};">
        <td style="border:1px solid #dbe3ee;padding:5px 5px;font-weight:700;">${formatDate(row.plan_date ?? '') || '-'}${alertMark}</td>
        <td ${numCell(row.baseline_plan)}>${pdfFmtNum(row.baseline_plan)}</td>
        <td ${numCell(row.current_plan)}>${pdfFmtNum(row.current_plan)}</td>
        <td ${numCell(row.plan_diff)}>${pdfFmtNum(row.plan_diff)}</td>
        <td ${numCell(row.current_actual)}>${row.current_actual != null ? pdfFmtNum(row.current_actual) : '—'}</td>
        <td ${numCell(row.actual_diff)}>${row.actual_diff != null ? pdfFmtNum(row.actual_diff) : '—'}</td>
      </tr>`
      })
      .join('')

  const mid = Math.ceil(opts.rows.length / 2)
  const leftRows = opts.rows.slice(0, mid)
  const rightRows = opts.rows.slice(mid)
  const tableCss = 'width:100%;border-collapse:collapse;font-size:9.5px;line-height:1.45;'
  const leftTable = `<table style="${tableCss}">${thead}<tbody>${renderRows(leftRows, 0) || `<tr><td colspan="6" style="padding:8px;text-align:center;color:#94a3b8;border:1px solid #dbe3ee;">データなし</td></tr>`}</tbody></table>`
  const rightTable = `<table style="${tableCss}">${thead}<tbody>${
    rightRows.length
      ? renderRows(rightRows, mid)
      : `<tr><td colspan="6" style="padding:8px;text-align:center;color:#94a3b8;border:1px solid #dbe3ee;">—</td></tr>`
  }</tbody></table>`

  const totalsBar = opts.rows.length
    ? `<div style="margin-top:6px;display:grid;grid-template-columns:auto repeat(5,1fr);gap:6px;padding:6px 8px;border-radius:8px;background:linear-gradient(90deg,#ecfdf5,#f0f9ff);border:1px solid #99f6e4;font-size:9px;font-weight:800;">
        <div style="color:#0f766e;align-self:center;">合計</div>
        <div style="text-align:right;font-variant-numeric:tabular-nums;">基準 <span style="font-size:11px;">${pdfFmtNum(opts.totals.baseline)}</span></div>
        <div style="text-align:right;font-variant-numeric:tabular-nums;">変更計画 <span style="font-size:11px;">${pdfFmtNum(opts.totals.currentPlan)}</span></div>
        <div style="text-align:right;font-variant-numeric:tabular-nums;color:${opts.totals.planDiff < 0 ? '#dc2626' : '#15803d'};">計画差 <span style="font-size:11px;">${pdfFmtNum(opts.totals.planDiff)}</span></div>
        <div style="text-align:right;font-variant-numeric:tabular-nums;">実績 <span style="font-size:11px;">${pdfFmtNum(opts.totals.currentActual)}</span></div>
        <div style="text-align:right;font-variant-numeric:tabular-nums;color:${opts.totals.actualDiff < 0 ? '#dc2626' : '#15803d'};">対実績差 <span style="font-size:11px;">${pdfFmtNum(opts.totals.actualDiff)}</span></div>
      </div>`
    : ''

  void opts.processName
  void opts.monthLabel
  return `<div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:start;">
        <div>${leftTable}</div>
        <div>${rightTable}</div>
      </div>
      ${totalsBar}
    </div>`
}

async function renderTrendChartImage(
  items: PlanBaselineComparisonItem[],
  processName: string,
  monthLabel: string,
  chartHeight = 280,
): Promise<string> {
  if (!items.length) return ''
  const prevDiff = trendShowDiffBars.value
  const prevQty = trendShowValueLabels.value
  trendShowDiffBars.value = true
  trendShowValueLabels.value = true
  const option = buildTrendChartOption(items) as Record<string, unknown>
  trendShowDiffBars.value = prevDiff
  trendShowValueLabels.value = prevQty

  option.animation = false
  option.animationDuration = 0
  option.tooltip = { show: false }
  option.title = {
    text: `日次推移（基準計画 × 実績・単位：千）`,
    subtext: `${monthLabel} ／ ${processName}`,
    left: 'center',
    top: 2,
    itemGap: 3,
    textStyle: { fontSize: 13, fontWeight: 800, color: '#0f172a', fontFamily: PDF_JP_FONT },
    subtextStyle: { fontSize: 10, color: '#64748b', fontFamily: PDF_JP_FONT, lineHeight: 14 },
  }
  const legend = (option.legend || {}) as Record<string, unknown>
  // タイトル＋サブタイトルの下に配置（重なり防止）
  legend.top = 48
  legend.left = 'center'
  legend.padding = [0, 0, 0, 0]
  legend.textStyle = { ...(legend.textStyle as object), fontFamily: PDF_JP_FONT, fontSize: 10 }
  option.legend = legend
  const grid = (option.grid || {}) as Record<string, unknown>
  grid.top = 76
  grid.bottom = 26
  option.grid = grid
  const xAxis = (option.xAxis || {}) as Record<string, unknown>
  const xLabel = (xAxis.axisLabel || {}) as Record<string, unknown>
  xAxis.axisLabel = { ...xLabel, fontFamily: PDF_JP_FONT, fontSize: 9 }
  option.xAxis = xAxis
  const yAxis = (option.yAxis || {}) as Record<string, unknown>
  yAxis.nameTextStyle = {
    ...((yAxis.nameTextStyle as object) || {}),
    fontFamily: PDF_JP_FONT,
    fontSize: 9,
  }
  const yLabel = (yAxis.axisLabel || {}) as Record<string, unknown>
  yAxis.axisLabel = { ...yLabel, fontFamily: PDF_JP_FONT, fontSize: 9 }
  option.yAxis = yAxis

  const chartDiv = document.createElement('div')
  chartDiv.style.cssText = `position:fixed;left:-9999px;top:0;width:1060px;height:${chartHeight}px;z-index:-1;background:#fff;`
  document.body.appendChild(chartDiv)
  let chartInstance: echarts.ECharts | undefined
  try {
    chartInstance = echarts.init(chartDiv, null, {
      renderer: 'canvas',
      devicePixelRatio: Math.min(window.devicePixelRatio || 1, PDF_CHART_PIXEL_RATIO),
    })
    chartInstance.setOption(option)
    await nextFrames(2)
    return chartInstance.getDataURL({
      type: 'png',
      pixelRatio: PDF_CHART_PIXEL_RATIO,
      backgroundColor: '#fff',
    })
  } finally {
    chartInstance?.dispose()
    chartDiv.remove()
  }
}

/** 全工程を1つのPDFにまとめたレポート（A4横・工程ごとに最大2ページ・工程間は必ず改ページ） */
async function buildCombinedBaselineReportPdf(
  tabs: Array<{ name: string; label: string; items: PlanBaselineComparisonItem[] }>,
  baselineMonth: string,
  totalsMap: Map<string, PdfProcessTotals>,
  onProgress?: (label: string, pct: number) => void,
): Promise<Blob> {
  const monthLabel = dayjs(baselineMonth).format('YYYY年MM月')
  const generatedAt = dayjs().format('YYYY/MM/DD HH:mm')
  const ym = dayjs(baselineMonth).format('YYYY-MM')
  const workingDays = await fetchScheduledWorkdaysForMonth(ym)
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4', compress: true })
  let firstPage = true
  const PAGE_W = 1100

  const pushOnePage = async (html: string, widthPx = PAGE_W) => {
    const canvas = await captureHtmlToCanvas(html, widthPx)
    addCanvasToPdf(doc, canvas, { newPage: !firstPage, fitOnePage: true, margin: 4 })
    firstPage = false
  }

  onProgress?.('表紙を生成中...', 5)
  const processList = tabs
    .map(
      (t, i) =>
        `<div style="display:flex;justify-content:space-between;padding:8px 12px;border-radius:10px;background:${i % 2 ? '#f8fafc' : '#fff'};border:1px solid #e2e8f0;">
          <span style="font-weight:800;color:#0f172a;">${t.name}</span>
          <span style="font-weight:700;color:#64748b;">${t.items.length} 日分（最大2ページ）</span>
        </div>`,
    )
    .join('')
  await pushOnePage(`<div style="font-family:${PDF_JP_FONT};width:${PAGE_W}px;background:#fff;color:#0f172a;">
    <div style="padding:14px 22px;background:linear-gradient(135deg,#0f766e 0%,#0d9488 42%,#0284c7 100%);color:#fff;">
      <div style="font-size:11px;font-weight:800;letter-spacing:0.08em;opacity:0.9;">SMART-EMAPS / PLAN BASELINE REPORT · A4横</div>
      <div style="font-size:22px;font-weight:900;margin-top:6px;">生産計画ベースライン 統合レポート</div>
      <div style="display:flex;gap:28px;margin-top:8px;font-size:13px;font-weight:700;">
        <span>対象月：${monthLabel}</span>
        <span style="opacity:0.92;">発行日時：${generatedAt}</span>
      </div>
    </div>
    <div style="padding:12px 22px 14px;">
      <div style="font-size:13px;font-weight:800;color:#0f766e;margin-bottom:8px;">収録工程（全 ${tabs.length} 工程・1ファイル）</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">${processList}</div>
      <div style="margin-top:10px;padding:10px 12px;border-radius:10px;background:#f8fafc;border:1px solid #e2e8f0;font-size:11px;line-height:1.65;color:#475569;">
        各工程は <strong>最大2ページ</strong>（①KPI＋日別明細［2列］　②日次推移＋ヒートマップ）。工程と工程の間は改ページします。<br/>
        稼働日数（会社カレンダー）：<strong>${workingDays > 0 ? `${workingDays} 日` : '—'}</strong>
      </div>
    </div>
  </div>`)

  const totalTabs = Math.max(tabs.length, 1)
  for (let ti = 0; ti < tabs.length; ti++) {
    const tab = tabs[ti]
    const processName = tab.name
    const items = tab.items
    const totals = totalsMap.get(processName)
    const tone = processTabTone(processName).accent
    const baselinePlanTotal =
      totals != null
        ? Number(totals.baselinePlan)
        : items.reduce((s, r) => s + Number(r.baseline_plan ?? 0), 0)
    const currentPlanTotal =
      totals?.currentPlan ?? items.reduce((s, r) => s + Number(r.current_plan ?? 0), 0)
    const planDiffTotal = totals?.planDiff ?? currentPlanTotal - baselinePlanTotal
    const currentActualTotal =
      totals?.currentActual ?? items.reduce((s, r) => s + Number(r.current_actual ?? 0), 0)
    const actualDiffTotal =
      totals?.actualDiff ??
      items.reduce((s, r) => s + (r.actual_diff != null ? Number(r.actual_diff) : 0), 0)
    const avgDailyBaseline =
      workingDays > 0 ? Math.round(baselinePlanTotal / workingDays) : 0
    const achievementPct =
      currentPlanTotal === 0 ? null : (currentActualTotal / currentPlanTotal) * 100
    const alertCount = items.filter((row) => isComparisonAlertRow(row)).length
    const basePct = ((ti + 0.2) / totalTabs) * 90 + 5
    const totalsObj = {
      baseline: baselinePlanTotal,
      currentPlan: currentPlanTotal,
      planDiff: planDiffTotal,
      currentActual: currentActualTotal,
      actualDiff: actualDiffTotal,
    }

    onProgress?.(`${processName}：1/2ページ`, Math.round(basePct))
    // 工程1ページ目：KPI + 日別明細2列（同一工程内は分割しない）
    await pushOnePage(`<div style="font-family:${PDF_JP_FONT};width:${PAGE_W}px;background:#fff;color:#0f172a;box-sizing:border-box;">
      <div style="padding:6px 12px;background:linear-gradient(135deg,${tone} 0%,#0d9488 70%);color:#fff;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div style="display:flex;align-items:baseline;gap:12px;">
            <div style="font-size:10px;font-weight:800;opacity:0.9;">工程レポート 1/2</div>
            <div style="font-size:17px;font-weight:900;">${processName}</div>
          </div>
          <div style="font-size:12px;font-weight:700;">${monthLabel}</div>
        </div>
      </div>
      <div style="padding:6px 10px 6px;">
        <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin-bottom:5px;">
          <div style="padding:4px 6px;border-radius:7px;background:#f0fdfa;border:1px solid #99f6e4;">
            <div style="font-size:8px;font-weight:800;color:#0f766e;">基準計画</div>
            <div style="font-size:13px;font-weight:900;font-variant-numeric:tabular-nums;">${pdfFmtNum(baselinePlanTotal)}</div>
          </div>
          <div style="padding:4px 6px;border-radius:7px;background:#eff6ff;border:1px solid #bfdbfe;">
            <div style="font-size:8px;font-weight:800;color:#1d4ed8;">変更計画</div>
            <div style="font-size:13px;font-weight:900;">${pdfFmtNum(currentPlanTotal)}</div>
          </div>
          <div style="padding:4px 6px;border-radius:7px;background:#fff7ed;border:1px solid #fed7aa;">
            <div style="font-size:8px;font-weight:800;color:#c2410c;">計画差異</div>
            <div style="font-size:13px;font-weight:900;color:${planDiffTotal < 0 ? '#dc2626' : '#15803d'};">${pdfFmtNum(planDiffTotal)}</div>
          </div>
          <div style="padding:4px 6px;border-radius:7px;background:#ecfdf5;border:1px solid #a7f3d0;">
            <div style="font-size:8px;font-weight:800;color:#047857;">実績</div>
            <div style="font-size:13px;font-weight:900;">${pdfFmtNum(currentActualTotal)}</div>
          </div>
          <div style="padding:4px 6px;border-radius:7px;background:#fff1f2;border:1px solid #fecdd3;">
            <div style="font-size:8px;font-weight:800;color:#be123c;">対実績差</div>
            <div style="font-size:13px;font-weight:900;color:${actualDiffTotal < 0 ? '#dc2626' : '#15803d'};">${pdfFmtNum(actualDiffTotal)}</div>
          </div>
          <div style="padding:4px 6px;border-radius:7px;background:#f5f3ff;border:1px solid #ddd6fe;">
            <div style="font-size:8px;font-weight:800;color:#6d28d9;">達成率</div>
            <div style="font-size:13px;font-weight:900;">${pdfFmtPct(achievementPct)}</div>
          </div>
        </div>
        <div style="font-size:9px;color:#64748b;margin-bottom:4px;">
          平均日当たり基準：<strong>${workingDays > 0 ? pdfFmtNum(avgDailyBaseline) : '—'}</strong>
          　／　アラート：<strong style="color:${alertCount > 0 ? '#c2410c' : '#059669'};">${alertCount}</strong>
          　／　閾値 ${Number(alertSettings.thresholdPct) || 0}%
        </div>
        <div style="font-size:11px;font-weight:800;color:#0f766e;margin-bottom:3px;">日別明細</div>
        ${renderCompactDetailTableHtml({
          processName,
          monthLabel,
          rows: items,
          totals: totalsObj,
        })}
      </div>
    </div>`)

    onProgress?.(`${processName}：2/2ページ`, Math.round(basePct + 12))
    // 工程2ページ目：日次推移 + ヒートマップ（縦スペースを埋める）
    const chartImg = items.length
      ? await renderTrendChartImage(items, processName, monthLabel, 280)
      : ''
    const panelsHtml = [
      {
        title: '計画達成率',
        unit: '',
        legend: '低 ← 達成率 → 高',
        cells: buildHeatmapCellsForItems(items, 'achievement', baselineMonth, processName),
        key: 'achievement',
      },
      {
        title: '実績差異',
        unit: '単位：千',
        legend: '負 ← 差異 → 正',
        cells: buildHeatmapCellsForItems(items, 'actualDiff', baselineMonth, processName),
        key: 'actualDiff',
      },
      {
        title: '実績数量',
        unit: '単位：千',
        legend: '少 ← 数量 → 多',
        cells: buildHeatmapCellsForItems(items, 'actualQty', baselineMonth, processName),
        key: 'actualQty',
      },
    ]
      .map((p) => renderHeatmapPanelHtml(p.title, p.unit, p.legend, p.cells, p.key, true))
      .join('')

    await pushOnePage(`<div style="font-family:${PDF_JP_FONT};width:${PAGE_W}px;background:#fff;color:#0f172a;box-sizing:border-box;">
      <div style="padding:5px 12px;background:linear-gradient(135deg,${tone} 0%,#0284c7 80%);color:#fff;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div style="font-size:14px;font-weight:900;">${processName} — 工程レポート 2/2</div>
          <div style="font-size:11px;font-weight:700;">${monthLabel}</div>
        </div>
      </div>
      <div style="padding:5px 10px 6px;">
        <div style="font-size:11px;font-weight:800;color:#0f766e;margin-bottom:3px;">日次推移（画面と同形式）</div>
        ${
          chartImg
            ? `<img src="${chartImg}" style="width:100%;height:auto;display:block;border:1px solid #e2e8f0;border-radius:8px;" />`
            : `<div style="padding:14px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px;">データなし</div>`
        }
        <div style="font-size:11px;font-weight:800;color:#0f766e;margin:6px 0 3px;">月間ヒートマップ</div>
        <div style="display:flex;gap:8px;align-items:stretch;">${panelsHtml}</div>
      </div>
    </div>`)
  }

  onProgress?.('PDFを結合中...', 98)
  return doc.output('blob')
}


const handleExportComparisonExcel = async () => {
  if (!guardApsOperation(canExport)) return

  if (processTabs.value.length === 0 || totalItemsCount.value === 0) {
    ElMessage.warning('比較データがありません。先に検索を実行してください。')
    return
  }

  exportExcelLoading.value = true
  try {
    const monthSource = comparisonResult.value?.baselineMonth || compareForm.baselineMonth
    const monthLabel = monthSource ? dayjs(monthSource).format('YYYY年MM月') : '—'
    const ym = monthSource ? dayjs(monthSource).format('YYYY-MM') : dayjs().format('YYYY-MM')
    const summary = comparisonResult.value?.summary
    const th = Number(alertSettings.thresholdPct) || 0

    const sheets: ExcelSheetAoa[] = []

    // サマリーシート
    const summaryAoa: (string | number | null | undefined)[][] = [
      ['項目', '値'],
      ['基準月', monthLabel],
      ['比較工程条件', compareForm.processName || '全工程'],
      ['差異閾値(%)', th],
      ['アラート監視（計画）', alertSettings.checkPlanDiff ? 'ON' : 'OFF'],
      ['アラート監視（実績）', alertSettings.checkActualDiff ? 'ON' : 'OFF'],
      ['アラート件数', alertStats.value.total],
      ['比較行数', totalItemsCount.value],
      [],
      ['KPI', '値'],
      ['基準計画合計', summary?.baselinePlanTotal ?? ''],
      ['変更計画合計', summary?.currentPlanTotal ?? ''],
      ['計画差異', summary?.planDifference ?? ''],
      ['実績合計', summary?.currentActualTotal ?? ''],
      ['計画対実績差', summary?.actualDifference ?? ''],
      [],
      ['時点比較', '基準計画', '計画達成率(%)', '計画対実績差'],
      [
        '前月',
        periodComparePrev.value?.summary?.baselinePlanTotal ?? '',
        summaryAchievementPct(periodComparePrev.value?.summary) != null
          ? Number(summaryAchievementPct(periodComparePrev.value?.summary)!.toFixed(2))
          : '',
        periodComparePrev.value?.summary?.actualDifference ?? '',
      ],
      [
        '前年同月',
        periodCompareYoy.value?.summary?.baselinePlanTotal ?? '',
        summaryAchievementPct(periodCompareYoy.value?.summary) != null
          ? Number(summaryAchievementPct(periodCompareYoy.value?.summary)!.toFixed(2))
          : '',
        periodCompareYoy.value?.summary?.actualDifference ?? '',
      ],
      [],
      ['工程', '行数', 'アラート件数', '基準計画合計', '変更計画合計', '計画差異', '実績合計', '計画対実績差'],
    ]

    for (const tab of processTabs.value) {
      const tot = processTotals.value.get(tab.name)
      summaryAoa.push([
        tab.label,
        tab.items.length,
        alertStats.value.byProcess.get(tab.name) || 0,
        tot?.baselinePlan ?? 0,
        tot?.currentPlan ?? 0,
        tot?.planDiff ?? 0,
        tot?.currentActual ?? 0,
        tot?.actualDiff ?? 0,
      ])
    }
    sheets.push({ name: 'サマリー', aoa: summaryAoa })

    const detailHeader = [
      '工程',
      '日付',
      '基準計画',
      '変更計画',
      '計画差異',
      '計画差異率(%)',
      '実績合計',
      '計画対実績差',
      '実績差異率(%)',
      'アラート',
      'アラート理由',
    ]

    const alertAoa: (string | number | null | undefined)[][] = [detailHeader]

    for (const tab of processTabs.value) {
      const aoa: (string | number | null | undefined)[][] = [detailHeader]
      for (const row of tab.items) {
        const planPct = getPlanDiffAlertPct(row)
        const actualPct = getActualDiffAlertPct(row)
        const alert = isComparisonAlertRow(row)
        const line: (string | number | null | undefined)[] = [
          tab.label,
          formatDate(row.plan_date || ''),
          Number(row.baseline_plan ?? 0),
          Number(row.current_plan ?? 0),
          Number(row.plan_diff ?? 0),
          planPct == null ? '' : Number(planPct.toFixed(2)),
          row.current_actual == null ? '' : Number(row.current_actual),
          row.actual_diff == null ? '' : Number(row.actual_diff),
          actualPct == null ? '' : Number(actualPct.toFixed(2)),
          alert ? 'Y' : '',
          alert ? getAlertReasonText(row) : '',
        ]
        aoa.push(line)
        if (alert) alertAoa.push(line)
      }
      // 合計行
      const tot = processTotals.value.get(tab.name)
      if (tot) {
        aoa.push([
          tab.label,
          '合計',
          '',
          tot.currentPlan,
          tot.planDiff,
          '',
          tot.currentActual,
          tot.actualDiff,
          '',
          '',
          '',
        ])
      }
      sheets.push({ name: tab.label, aoa })
    }

    if (alertAoa.length > 1) {
      sheets.push({ name: 'アラート一覧', aoa: alertAoa })
    }

    await downloadExcelMultiSheet(sheets, `生産計画ベースライン比較_${ym}.xlsx`)
    ElMessage.success(`Excelを出力しました（${sheets.length}シート）`)
  } catch (error: any) {
    console.error(error)
    ElMessage.error(error?.message || 'Excel出力に失敗しました')
  } finally {
    exportExcelLoading.value = false
  }
}

/** PDF Blob を一時 iframe で開き、ブラウザ印刷ダイアログを出す */
function printPdfBlob(blob: Blob, title: string): Promise<void> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(blob)
    const iframe = document.createElement('iframe')
    iframe.setAttribute('title', title)
    iframe.setAttribute('aria-hidden', 'true')
    iframe.style.cssText =
      'position:fixed;right:0;bottom:0;width:0;height:0;border:0;opacity:0;pointer-events:none'
    document.body.appendChild(iframe)

    let settled = false
    let printOpened = false
    const finish = () => {
      if (settled) return
      settled = true
      window.removeEventListener('focus', onWindowFocus)
      window.removeEventListener('visibilitychange', onVisibility)
      try {
        URL.revokeObjectURL(url)
      } catch {
        /* ignore */
      }
      iframe.remove()
      resolve()
    }

    // 印刷ダイアログを閉じた後（フォーカス復帰）で確実に完了させる
    const onWindowFocus = () => {
      if (!printOpened) return
      setTimeout(finish, 200)
    }
    const onVisibility = () => {
      if (!printOpened || document.visibilityState !== 'visible') return
      setTimeout(finish, 200)
    }
    window.addEventListener('focus', onWindowFocus)
    window.addEventListener('visibilitychange', onVisibility)

    iframe.onload = () => {
      const win = iframe.contentWindow
      if (!win) {
        finish()
        return
      }
      const onAfterPrint = () => {
        win.removeEventListener('afterprint', onAfterPrint)
        setTimeout(finish, 120)
      }
      win.addEventListener('afterprint', onAfterPrint)
      setTimeout(() => {
        try {
          win.focus()
          printOpened = true
          win.print()
          // 一部ブラウザは afterprint を発火しないため短めのフォールバック
          setTimeout(finish, 8000)
        } catch {
          finish()
        }
      }, 200)
    }

    iframe.onerror = () => finish()
    iframe.src = url
  })
}

/** 統合レポート PDF を印刷 */
async function printReportPdfFiles(files: { processName: string; blob: Blob }[]) {
  if (!files.length) return
  ElMessage.info('印刷ダイアログを開きます')
  await printPdfBlob(files[0].blob, files[0].processName || 'ベースラインレポート')
}

const handleExportPdfToFolder = async () => {
  if (!guardApsOperation(canExport)) return

  if (!comparisonResult.value?.baselineMonth || pdfExportTargetTabs.value.length === 0) {
    ElMessage.warning(
      '切断・面取・成型・メッキ・溶接・溶接SP・検査のいずれにも比較データがありません。条件を確認し、先に検索を実行してください。',
    )
    return
  }
  const tabs = pdfExportTargetTabs.value
  exportPdfLoading.value = true
  exportProgressVisible.value = true
  exportProgressPercent.value = 0
  exportProgressCurrent.value = '準備中...'
  await nextTick()
  await nextFrames(2)
  try {
    const baselineMonth = comparisonResult.value.baselineMonth
    const totalsSnapshot = new Map(processTotals.value)
    const blob = await buildCombinedBaselineReportPdf(
      tabs,
      baselineMonth,
      totalsSnapshot,
      (label, pct) => {
        exportProgressCurrent.value = label
        exportProgressPercent.value = Math.min(88, pct)
      },
    )
    const files: { processName: string; blob: Blob }[] = [
      { processName: '全工程統合', blob },
    ]
    exportProgressCurrent.value = 'サーバーに保存しています...'
    exportProgressPercent.value = 92
    const res = await exportPlanBaselinePdfToFolder(baselineMonth, files)
    if (!res.success) {
      ElMessage.error(res.message ?? '保存に失敗しました')
      if (res.errors?.length) console.error('export errors', res.errors)
      return
    }
    ElMessage.success(res.message ?? '統合レポートPDFを保存しました')

    exportProgressCurrent.value = '印刷準備中...'
    exportProgressPercent.value = 100
    await nextTick()
    // 印刷ダイアログ中はボタンを回し続けない（閉じた後も loading が残るのを防止）
    exportPdfLoading.value = false
    exportProgressVisible.value = false
    await nextFrames(2)
    await printReportPdfFiles(files)
    ElMessage.success('レポートの印刷処理が完了しました')
  } catch (error: any) {
    ElMessage.error(error?.message ?? 'レポート生成に失敗しました')
    console.error(error)
  } finally {
    exportPdfLoading.value = false
    exportProgressVisible.value = false
    exportProgressPercent.value = 0
    exportProgressCurrent.value = ''
  }
}

watch(
  () => [compareForm.baselineMonth, compareForm.processName] as const,
  () => {
    scheduleCompareLoad()
  },
)

// タブが更新されたらアクティブタブを調整
watch(
  processTabs,
  () => {
    updateActiveTab()
  },
  { immediate: true },
)

onMounted(() => {
  loadComparison()
  window.addEventListener('resize', onTrendChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onTrendChartResize)
  trendChart?.dispose()
  trendChart = null
  if (highlightCompareTimer) clearTimeout(highlightCompareTimer)
  if (compareLoadTimer) clearTimeout(compareLoadTimer)
})


/** 印刷用 HTML を隠し iframe で開き、ブラウザの印刷ダイアログのみ出す */
function printWithIframeDoc(html: string, iframeTitle: string) {
  if (!guardApsOperation(canExport)) return

  const iframe = document.createElement('iframe')
  iframe.setAttribute('title', iframeTitle)
  iframe.setAttribute('aria-hidden', 'true')
  iframe.style.cssText =
    'position:fixed;right:0;bottom:0;width:0;height:0;border:0;opacity:0;pointer-events:none'
  document.body.appendChild(iframe)

  const idoc = iframe.contentDocument
  const iwin = iframe.contentWindow
  if (!idoc || !iwin) {
    iframe.remove()
    ElMessage.error('印刷を開始できませんでした')
    return
  }

  idoc.open()
  idoc.write(html)
  idoc.close()

  let done = false
  const runPrint = () => {
    if (done) return
    done = true
    try {
      iwin.focus()
      iwin.print()
    } finally {
      setTimeout(() => iframe.remove(), 400)
    }
  }

  iframe.onload = runPrint
  setTimeout(runPrint, 200)
}

/** 現アクティブタブの比較テーブル行だけを印刷（ページ全体ではない） */
function handlePrintBaselineComparison() {
  if (!guardApsOperation(canExport)) return

  const tab =
    processTabs.value.find((t) => t.name === activeTab.value) ?? processTabs.value[0]
  if (!tab?.items?.length) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  const esc = (v: unknown) => {
    const s = v == null || v === '' ? '—' : String(v)
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
  }

  const monthSource = comparisonResult.value?.baselineMonth || compareForm.baselineMonth
  const monthLabel = monthSource ? dayjs(monthSource).format('YYYY年MM月') : '—'

  const headCells = ['日付', '基準計画', '変更計画', '計画差異', '実績合計', '計画対実績差']
  const headerRow = headCells.map((h) => `<th>${esc(h)}</th>`).join('')

  const wrapDiff = (v: number | null | undefined) => {
    const t = formatNumber(v ?? null)
    if (v === null || v === undefined) {
      return `<td class="td-num"><span class="diff-muted">${esc(t)}</span></td>`
    }
    const c = getDiffClass(v)
    const inner =
      c === 'diff-negative'
        ? `<span class="diff-neg">${esc(t)}</span>`
        : c === 'diff-positive'
          ? `<span class="diff-pos">${esc(t)}</span>`
          : esc(t)
    return `<td class="td-num">${inner}</td>`
  }

  const bodyRows = tab.items
    .map((row) => {
      const dateStr = formatDate(row.plan_date ?? '')
      const actualCell =
        row.current_actual !== null && row.current_actual !== undefined
          ? `<td class="td-num">${esc(formatNumber(row.current_actual))}</td>`
          : `<td class="td-num"><span class="diff-muted">-</span></td>`
      return `<tr>
<td class="td-date">${esc(dateStr)}</td>
<td class="td-num">${esc(formatNumber(row.baseline_plan))}</td>
<td class="td-num">${esc(formatNumber(row.current_plan))}</td>
${wrapDiff(row.plan_diff ?? null)}
${actualCell}
${wrapDiff(row.actual_diff ?? null)}
</tr>`
    })
    .join('')

  let sumBaseline = 0
  let sumCurrent = 0
  let sumPlanDiff = 0
  let sumActual = 0
  let sumActualDiff = 0
  let actualSumCount = 0
  let actualDiffSumCount = 0
  for (const row of tab.items) {
    sumBaseline += Number(row.baseline_plan ?? 0)
    sumCurrent += Number(row.current_plan ?? 0)
    sumPlanDiff += Number(row.plan_diff ?? 0)
    if (row.current_actual !== null && row.current_actual !== undefined) {
      sumActual += Number(row.current_actual)
      actualSumCount += 1
    }
    if (row.actual_diff !== null && row.actual_diff !== undefined) {
      sumActualDiff += Number(row.actual_diff)
      actualDiffSumCount += 1
    }
  }
  const actualTotalCell =
    actualSumCount > 0
      ? `<td class="td-num">${esc(formatNumber(sumActual))}</td>`
      : `<td class="td-num"><span class="diff-muted">-</span></td>`
  const actualDiffTotalCell =
    actualDiffSumCount > 0 ? wrapDiff(sumActualDiff) : wrapDiff(null)

  const footerRow = `<tr class="row-total">
<td class="td-date">${esc('合計')}</td>
<td class="td-num">${esc(formatNumber(sumBaseline))}</td>
<td class="td-num">${esc(formatNumber(sumCurrent))}</td>
${wrapDiff(sumPlanDiff)}
${actualTotalCell}
${actualDiffTotalCell}
</tr>`

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>ベースライン比較</title>
  <style>
    @page { margin: 12mm; }
    body { font-family: 'Segoe UI', 'Meiryo', 'Hiragino Sans', sans-serif; font-size: 11px; color: #111; }
    h1 { font-size: 15px; margin: 0 0 6px; font-weight: 700; }
    .meta { font-size: 10px; color: #333; margin: 0 0 10px; line-height: 1.5; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #333; padding: 4px 5px; vertical-align: top; word-wrap: break-word; }
    th { background: #eee; text-align: center; font-weight: 600; }
    .td-date { text-align: center; }
    .td-num { text-align: right; }
    .diff-neg { color: #c62828; font-weight: 600; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .diff-pos { color: #047857; font-weight: 600; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .diff-muted { color: #64748b; }
    .row-total td { background: #f3f4f6; font-weight: 600; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .row-total .td-date { font-weight: 700; }
  </style>
</head>
<body>
  <h1>ベースライン比較一覧</h1>
  <p class="meta">基準月：${esc(monthLabel)}　工程：${esc(tab.label)}　件数：${tab.items.length}</p>
  <table>
    <thead><tr>${headerRow}</tr></thead>
    <tbody>${bodyRows}</tbody>
    <tfoot>${footerRow}</tfoot>
  </table>
</body>
</html>`

  printWithIframeDoc(html, 'ベースライン比較印刷')
}

</script>

<style scoped>
/* 工程別PDF発行 进度弹窗 */
.export-progress-content {
  padding: 8px 0 16px;
  text-align: center;
}
.export-progress-icon-wrap {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 14px;
  background: linear-gradient(145deg, #ccfbf1 0%, #99f6e4 100%);
  border: 1px solid rgba(13, 148, 136, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 1px 0 #fff, 0 4px 12px rgba(13, 148, 136, 0.18);
  animation: export-pulse 1.5s ease-in-out infinite;
}
.export-progress-icon {
  font-size: 28px;
  color: #0f766e;
}
.export-progress-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
}
.export-progress-current {
  margin: 0 0 20px;
  font-size: 13px;
  color: #64748b;
  min-height: 20px;
}
.export-progress-bar-wrap {
  padding: 0 8px;
}
.export-progress-bar {
  --el-progress-bar-height: 12px;
  --el-progress-text-size: 13px;
}
:deep(.export-progress-bar .el-progress-bar__outer) {
  border-radius: 6px;
  background-color: #e2e8f0;
}
:deep(.export-progress-bar .el-progress-bar__inner) {
  border-radius: 6px;
  background: linear-gradient(90deg, #0d9488 0%, #14b8a6 50%, #2dd4bf 100%) !important;
  transition: width 0.35s ease;
}

.export-pdf-progress-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}
.export-pdf-progress-dialog :deep(.el-dialog__header) {
  padding: 16px 20px 12px;
  border-bottom: 1px solid #ccfbf1;
  margin-right: 0;
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%);
}
.export-pdf-progress-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}
.export-pdf-progress-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 24px;
}

@keyframes export-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(13, 148, 136, 0.2);
  }
  50% {
    transform: scale(1.03);
    box-shadow: 0 0 0 8px rgba(25, 118, 210, 0);
  }
}

/* 页面基础样式 */
.plan-baseline-root {
  display: block;
  width: 100%;
}

.plan-baseline-page {
  --pb-ink: #0f172a;
  --pb-sub: #64748b;
  --pb-line: #d4dce8;
  --pb-elev-inset: inset 0 1px 0 rgba(255, 255, 255, 0.95);
  --pb-elev-1: 0 2px 4px rgba(15, 23, 42, 0.06), 0 6px 18px rgba(15, 23, 42, 0.07);
  --pb-elev-2: 0 4px 8px rgba(15, 23, 42, 0.08), 0 12px 28px rgba(15, 23, 42, 0.1);
  --pb-shadow-hover: 0 6px 14px rgba(15, 23, 42, 0.1), 0 14px 32px rgba(14, 116, 144, 0.12);
  --pb-zone-kpi: #0d9488;
  --pb-zone-analytics: #0284c7;
  --pb-zone-table: #4f46e5;
  padding: 10px 12px 16px;
  min-height: 100vh;
  box-sizing: border-box;
  background:
    radial-gradient(920px 440px at 6% -8%, rgba(153, 246, 228, 0.38) 0%, transparent 55%),
    radial-gradient(780px 400px at 100% 0%, rgba(186, 230, 253, 0.42) 0%, transparent 50%),
    radial-gradient(640px 320px at 55% 100%, rgba(254, 243, 199, 0.22) 0%, transparent 55%),
    linear-gradient(180deg, #eef6f7 0%, #e8eef4 48%, #f1f5f9 100%);
}

/* 機能ゾーン（色分け見出し） */
.pb-zone {
  margin-bottom: 12px;
  animation: fadeInUp 0.48s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.pb-zone--action {
  --zone-accent: #059669;
  animation-delay: 0s;
}
.pb-zone--kpi {
  --zone-accent: var(--pb-zone-kpi);
  animation-delay: 0.04s;
}
.pb-zone--analytics {
  --zone-accent: var(--pb-zone-analytics);
  animation-delay: 0.08s;
}
.pb-zone--table {
  --zone-accent: var(--pb-zone-table);
  animation-delay: 0.12s;
}
.pb-zone__label {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 8px 2px;
  padding: 3px 10px 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--zone-accent) 78%, #0f172a);
  background: color-mix(in srgb, var(--zone-accent) 12%, #ffffff);
  border: 1px solid color-mix(in srgb, var(--zone-accent) 28%, #e2e8f0);
  box-shadow: inset 0 1px 0 #fff, 0 1px 3px rgba(15, 23, 42, 0.04);
}
.pb-zone__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--zone-accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--zone-accent) 22%, transparent);
}

/* ==== Modern action button variants（颜色区分＋立体）==== */
.btn-refresh-modern,
.btn-generate-modern,
.btn-delete-modern,
.btn-edit-modern,
.btn-search-modern,
.btn-export-baseline-modern,
.btn-print-baseline-modern,
.btn-clear-modern {
  border-radius: 10px !important;
  font-weight: 700 !important;
  letter-spacing: 0.01em;
  transition:
    transform 0.15s ease,
    box-shadow 0.18s ease,
    filter 0.18s ease,
    background 0.18s ease,
    border-color 0.18s ease !important;
}

.btn-refresh-modern:active,
.btn-generate-modern:active,
.btn-delete-modern:active,
.btn-edit-modern:active,
.btn-search-modern:active,
.btn-export-baseline-modern:active,
.btn-print-baseline-modern:active,
.btn-clear-modern:active {
  transform: translateY(1px);
}

.btn-refresh-modern {
  background: linear-gradient(180deg, #5eead4 0%, #14b8a6 48%, #0f766e 100%) !important;
  border: 1px solid rgba(15, 118, 110, 0.55) !important;
  color: #ffffff !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 0 rgba(15, 118, 110, 0.25),
    0 8px 18px rgba(20, 184, 166, 0.28);
}
.btn-refresh-modern:hover {
  filter: brightness(1.04);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    0 3px 0 rgba(15, 118, 110, 0.22),
    0 10px 22px rgba(20, 184, 166, 0.34);
}

.btn-generate-modern {
  background: linear-gradient(180deg, #4ade80 0%, #22c55e 48%, #16a34a 100%) !important;
  border: 1px solid rgba(21, 128, 61, 0.5) !important;
  color: #ffffff !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 0 rgba(21, 128, 61, 0.22),
    0 8px 16px rgba(34, 197, 94, 0.28);
}
.btn-generate-modern:hover {
  filter: brightness(1.04);
}

.btn-delete-modern {
  background: linear-gradient(180deg, #fff 0%, #fef2f2 100%) !important;
  border: 1px solid rgba(239, 68, 68, 0.42) !important;
  color: #b91c1c !important;
  box-shadow: inset 0 1px 0 #fff, 0 2px 6px rgba(239, 68, 68, 0.12);
}
.btn-delete-modern:hover {
  background: linear-gradient(180deg, #fff5f5 0%, #fee2e2 100%) !important;
  border-color: rgba(239, 68, 68, 0.6) !important;
  transform: translateY(-1px);
}

.btn-edit-modern {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%) !important;
  border: 1px solid rgba(245, 158, 11, 0.45) !important;
  color: #92400e !important;
  box-shadow: inset 0 1px 0 #fff, 0 2px 6px rgba(245, 158, 11, 0.14);
}
.btn-edit-modern:hover {
  background: linear-gradient(180deg, #fff7ed 0%, #fde68a 100%) !important;
  border-color: rgba(245, 158, 11, 0.62) !important;
  transform: translateY(-1px);
}

.btn-search-modern {
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%) !important;
  border: 1px solid rgba(29, 78, 216, 0.5) !important;
  color: #ffffff !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 0 rgba(29, 78, 216, 0.22),
    0 8px 16px rgba(59, 130, 246, 0.28);
}
.btn-search-modern:hover {
  filter: brightness(1.04);
}

.btn-clear-modern {
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%) !important;
  border: 1px solid rgba(148, 163, 184, 0.5) !important;
  color: #334155 !important;
  box-shadow: inset 0 1px 0 #fff, 0 2px 5px rgba(15, 23, 42, 0.06);
}
.btn-clear-modern:hover {
  background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
  border-color: rgba(100, 116, 139, 0.55) !important;
  transform: translateY(-1px);
}

.btn-sync-modern {
  border-radius: 10px !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, #ecfeff 0%, #cffafe 100%) !important;
  border: 1px solid rgba(13, 148, 136, 0.4) !important;
  color: #0f766e !important;
  box-shadow: inset 0 1px 0 #fff, 0 2px 6px rgba(13, 148, 136, 0.12);
  transition:
    transform 0.15s ease,
    box-shadow 0.18s ease,
    filter 0.18s ease !important;
}
.btn-sync-modern:hover {
  filter: brightness(1.03);
  transform: translateY(-1px);
}
.btn-sync-modern:active {
  transform: translateY(1px);
}

.btn-export-baseline-modern {
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 50%, #1d4ed8 100%) !important;
  border: 1px solid rgba(29, 78, 216, 0.5) !important;
  color: #ffffff !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.32),
    0 2px 0 rgba(29, 78, 216, 0.2),
    0 6px 14px rgba(37, 99, 235, 0.28);
}
.btn-export-baseline-modern:hover {
  filter: brightness(1.04);
}

.btn-excel-baseline-modern {
  background: linear-gradient(180deg, #4ade80 0%, #22c55e 50%, #15803d 100%) !important;
  border: 1px solid rgba(21, 128, 61, 0.5) !important;
  color: #ffffff !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.32),
    0 2px 0 rgba(21, 128, 61, 0.2),
    0 6px 14px rgba(34, 197, 94, 0.26);
}
.btn-excel-baseline-modern:hover {
  filter: brightness(1.04);
}
.btn-excel-baseline-modern:active {
  transform: translateY(1px);
}

.btn-print-baseline-modern {
  background: linear-gradient(180deg, #fff 0%, #eff6ff 100%) !important;
  border: 1px solid rgba(37, 99, 235, 0.4) !important;
  color: #1d4ed8 !important;
  box-shadow: inset 0 1px 0 #fff, 0 2px 6px rgba(37, 99, 235, 0.1);
}
.btn-print-baseline-modern:hover {
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%) !important;
  border-color: rgba(37, 99, 235, 0.6) !important;
  transform: translateY(-1px);
}

.pb-ctl--month {
  width: 140px;
}
.pb-ctl--process {
  width: 148px;
}
.pb-ctl :deep(.el-input__wrapper) {
  border-radius: 9px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  box-shadow:
    0 0 0 1px rgba(148, 163, 184, 0.4) inset,
    0 1px 2px rgba(15, 23, 42, 0.04) !important;
  transition: box-shadow 0.18s ease;
}
.pb-ctl :deep(.el-input__wrapper:hover),
.pb-ctl :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px rgba(13, 148, 136, 0.55) inset,
    0 2px 8px rgba(13, 148, 136, 0.12) !important;
}

/* 页面头部（ガラス＋立体） */
.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 10px 14px;
  border-radius: 12px;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background:
    linear-gradient(135deg, rgba(13, 148, 136, 0.96) 0%, rgba(14, 116, 144, 0.94) 48%, rgba(37, 99, 235, 0.92) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    0 2px 4px rgba(15, 118, 110, 0.2),
    0 10px 28px rgba(14, 116, 144, 0.28);
  animation: slideDown 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.page-header__orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(2px);
}
.page-header__orb--a {
  width: 140px;
  height: 140px;
  top: -56px;
  right: 18%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.28), transparent 68%);
  animation: orbFloat 6s ease-in-out infinite;
}
.page-header__orb--b {
  width: 90px;
  height: 90px;
  bottom: -40px;
  left: 12%;
  background: radial-gradient(circle, rgba(167, 243, 208, 0.35), transparent 70%);
  animation: orbFloat 7.5s ease-in-out infinite reverse;
}

.title-wrapper {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0.12));
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 11px;
  backdrop-filter: blur(10px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    0 4px 12px rgba(15, 23, 42, 0.18);
  animation: iconPulse 2.8s ease-in-out infinite;
}

.title-icon {
  font-size: 20px;
  color: white;
}

.title-content h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: white;
  line-height: 1.2;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 2px rgba(15, 23, 42, 0.2);
}

.title-content p {
  margin: 2px 0 0;
  color: rgba(255, 255, 255, 0.88);
  font-size: 12px;
  line-height: 1.3;
}

.help-icon--header {
  color: rgba(255, 255, 255, 0.9) !important;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition:
    transform 0.18s ease,
    background 0.18s ease;
}
.help-icon--header:hover {
  background: rgba(255, 255, 255, 0.22);
  transform: scale(1.08);
}

.page-header .btn-refresh-modern {
  position: relative;
  z-index: 1;
}

.page-header__actions {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-report-modern {
  border: none !important;
  border-radius: 10px !important;
  font-weight: 800 !important;
  letter-spacing: 0.02em;
  color: #0f766e !important;
  background: linear-gradient(180deg, #ffffff 0%, #ecfdf5 100%) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    0 1px 0 rgba(13, 148, 136, 0.2),
    0 4px 12px rgba(15, 23, 42, 0.12) !important;
}

.btn-report-modern:hover {
  color: #fff !important;
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important;
}

.btn-report-modern.is-disabled,
.btn-report-modern:disabled {
  opacity: 0.55 !important;
  color: #64748b !important;
  background: rgba(255, 255, 255, 0.55) !important;
}

/* 操作卡片（生成 / 比較条件） */
.action-card {
  margin-bottom: 8px;
  border-radius: 16px !important;
  border: 1px solid rgba(203, 213, 225, 0.9) !important;
  background:
    radial-gradient(120% 80% at 0% 0%, rgba(16, 185, 129, 0.07), transparent 42%),
    radial-gradient(100% 70% at 100% 0%, rgba(59, 130, 246, 0.08), transparent 40%),
    linear-gradient(180deg, #ffffff 0%, #f8fafc 58%, #f1f5f9 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 0 rgba(148, 163, 184, 0.18),
    0 10px 28px rgba(15, 23, 42, 0.07);
  animation: fadeInUp 0.5s cubic-bezier(0.22, 1, 0.36, 1);
  transition:
    box-shadow 0.25s ease,
    transform 0.2s ease;
}

.action-card:hover {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 0 rgba(148, 163, 184, 0.22),
    0 14px 34px rgba(15, 23, 42, 0.1);
}

.action-card :deep(.el-card__body) {
  padding: 12px 14px 14px;
}

.action-content {
  display: flex;
  gap: 12px;
  padding: 0;
  align-items: stretch;
}

.action-section {
  --sec-accent: #0d9488;
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px 12px 16px;
  border-radius: 14px;
  background:
    linear-gradient(165deg, #ffffff 0%, color-mix(in srgb, var(--sec-accent) 6%, #ffffff) 48%, #f8fafc 100%);
  border: 1px solid color-mix(in srgb, var(--sec-accent) 22%, #e2e8f0);
  box-shadow:
    inset 0 1px 0 #fff,
    0 1px 0 color-mix(in srgb, var(--sec-accent) 10%, #cbd5e1),
    0 8px 18px rgba(15, 23, 42, 0.05);
  overflow: hidden;
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    border-color 0.22s ease;
}

.action-section:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 #fff,
    0 2px 0 color-mix(in srgb, var(--sec-accent) 14%, #cbd5e1),
    0 12px 24px rgba(15, 23, 42, 0.08);
}

.action-section__glow {
  position: absolute;
  right: -40px;
  top: -48px;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--sec-accent) 28%, transparent), transparent 68%);
  pointer-events: none;
  z-index: 0;
}

.action-section::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 4px;
  border-radius: 0 4px 4px 0;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--sec-accent) 88%, #fff),
    var(--sec-accent)
  );
  box-shadow: 1px 0 10px color-mix(in srgb, var(--sec-accent) 42%, transparent);
  z-index: 1;
}

.action-section::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--sec-accent),
    color-mix(in srgb, var(--sec-accent) 20%, transparent)
  );
  opacity: 0.9;
  z-index: 1;
}

.generate-section {
  --sec-accent: #059669;
}

.filter-section {
  --sec-accent: #2563eb;
}

.action-divider {
  width: 18px;
  align-self: stretch;
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-divider::before {
  content: '';
  position: absolute;
  top: 12%;
  bottom: 12%;
  width: 1px;
  background: linear-gradient(180deg, transparent, #cbd5e1 20%, #94a3b8 50%, #cbd5e1 80%, transparent);
}

.action-divider__dot {
  position: relative;
  z-index: 1;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(145deg, #e2e8f0, #94a3b8);
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.15);
}

.section-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
}

.section-header--with-toggle {
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.filter-section .section-header {
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.section-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.section-header__toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  padding: 5px 10px 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.4);
  box-shadow: inset 0 1px 0 #fff, 0 1px 4px rgba(15, 23, 42, 0.05);
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.section-header__toggle.is-on {
  border-color: rgba(13, 148, 136, 0.4);
  background: rgba(204, 251, 241, 0.55);
  box-shadow: inset 0 1px 0 #fff, 0 2px 8px rgba(13, 148, 136, 0.15);
}

.section-header__live {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: #1d4ed8;
  background: rgba(219, 234, 254, 0.7);
  border: 1px solid rgba(59, 130, 246, 0.28);
  box-shadow: inset 0 1px 0 #fff;
}

.section-live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.45);
  animation: sectionLivePulse 1.8s ease-out infinite;
}

@keyframes sectionLivePulse {
  0% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.45);
  }
  70% {
    box-shadow: 0 0 0 7px rgba(37, 99, 235, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
  }
}

.section-toggle-label {
  font-size: 11px;
  font-weight: 800;
  color: #94a3b8;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.section-toggle-label.is-on {
  color: #0f766e;
}

.generate-section.is-locked .section-controls {
  opacity: 0.52;
  filter: grayscale(0.18);
  pointer-events: none;
}

.generate-section.is-locked {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.75) 100%);
  border-color: rgba(203, 213, 225, 0.95);
}

.section-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font-size: 17px;
  color: white;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    0 4px 12px rgba(15, 23, 42, 0.16);
}

.generate-icon-bg {
  background: linear-gradient(145deg, #34d399 0%, #059669 100%);
}

.filter-icon-bg {
  background: linear-gradient(145deg, #60a5fa 0%, #2563eb 100%);
}

.section-title {
  min-width: 0;
}

.section-title__row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.section-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
  letter-spacing: 0.01em;
}

.section-badge {
  display: inline-flex;
  align-items: center;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.06em;
  line-height: 1.4;
}

.section-badge--gen {
  color: #047857;
  background: rgba(167, 243, 208, 0.55);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.section-badge--filter {
  color: #1d4ed8;
  background: rgba(191, 219, 254, 0.65);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.section-desc {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 3px;
  line-height: 1.4;
}

.section-controls {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: inset 0 1px 0 #fff, 0 1px 3px rgba(15, 23, 42, 0.04);
}

.section-controls__actions {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-left: 2px;
  padding-left: 10px;
  border-left: 1px dashed rgba(148, 163, 184, 0.55);
}

.section-controls__hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  background: rgba(241, 245, 249, 0.9);
  border: 1px solid rgba(203, 213, 225, 0.8);
}

.section-controls__hint .el-icon {
  color: #2563eb;
}

@media (max-width: 1100px) {
  .action-content {
    flex-direction: column;
  }
  .action-divider {
    width: 100%;
    height: 18px;
  }
  .action-divider::before {
    top: 50%;
    bottom: auto;
    left: 8%;
    right: 8%;
    width: auto;
    height: 1px;
    background: linear-gradient(90deg, transparent, #cbd5e1 20%, #94a3b8 50%, #cbd5e1 80%, transparent);
  }
  .section-controls__hint {
    margin-left: 0;
    width: 100%;
  }
  .section-controls__actions {
    margin-left: 0;
    padding-left: 0;
    border-left: none;
    width: 100%;
  }
}

/* KPI 摘要（色分け＋立体＋アニメ） */
.summary-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.summary-card {
  --card-accent: #0d9488;
  --card-tint: color-mix(in srgb, var(--card-accent) 12%, #ffffff);
  --card-tint-deep: color-mix(in srgb, var(--card-accent) 18%, #f8fafc);
  position: relative;
  isolation: isolate;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--card-accent) 28%, #e2e8f0);
  background:
    linear-gradient(155deg, #ffffff 0%, var(--card-tint) 42%, var(--card-tint-deep) 100%);
  overflow: hidden;
  transform-style: preserve-3d;
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease,
    border-color 0.22s ease;
  animation: kpiCardIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) backwards;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    inset 0 -1px 0 color-mix(in srgb, var(--card-accent) 8%, transparent),
    0 2px 0 color-mix(in srgb, var(--card-accent) 16%, #cbd5e1),
    0 8px 18px rgba(15, 23, 42, 0.07);
}

.summary-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--card-accent) 92%, #fff), var(--card-accent));
  box-shadow: 1px 0 10px color-mix(in srgb, var(--card-accent) 45%, transparent);
  z-index: 2;
}

.summary-card::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--card-accent), color-mix(in srgb, var(--card-accent) 35%, transparent));
  opacity: 0.85;
  z-index: 2;
}

.summary-card__sheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    115deg,
    transparent 0%,
    rgba(255, 255, 255, 0.55) 38%,
    transparent 58%
  );
  transform: translateX(-120%);
  animation: kpiSheen 4.8s ease-in-out infinite;
  pointer-events: none;
  z-index: 1;
  opacity: 0.55;
}

.summary-card__glow {
  position: absolute;
  top: -36%;
  right: -22%;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--card-accent) 38%, transparent), transparent 70%);
  pointer-events: none;
  opacity: 0.9;
  z-index: 0;
  animation: kpiGlowPulse 3.2s ease-in-out infinite;
}

.summary-card__ridge {
  position: absolute;
  right: 10px;
  bottom: 8px;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--card-accent) 22%, transparent);
  background: color-mix(in srgb, var(--card-accent) 8%, transparent);
  transform: rotate(18deg);
  pointer-events: none;
  z-index: 0;
  opacity: 0.7;
}

.summary-card:hover {
  transform: translateY(-5px) scale(1.015);
  border-color: color-mix(in srgb, var(--card-accent) 55%, #cbd5e1);
  box-shadow:
    inset 0 1px 0 #fff,
    0 3px 0 color-mix(in srgb, var(--card-accent) 22%, #94a3b8),
    0 14px 28px color-mix(in srgb, var(--card-accent) 22%, transparent),
    0 8px 16px rgba(15, 23, 42, 0.08);
}

.summary-card:hover .summary-card__glow {
  opacity: 1;
  transform: scale(1.12);
}

.summary-card:active {
  transform: translateY(-1px) scale(1.005);
}

.summary-card--baseline { --card-accent: #0d9488; }
.summary-card--current { --card-accent: #0284c7; }
.summary-card--diff { --card-accent: #f59e0b; }
.summary-card--actual { --card-accent: #059669; }
.summary-card--actual-diff { --card-accent: #e11d48; }
.summary-card--rate { --card-accent: #4f46e5; }
.summary-card--rate-diff { --card-accent: #c026d3; }

.summary-card.is-negative {
  --card-accent: #ef4444;
}

.summary-card-inner {
  position: relative;
  z-index: 2;
  padding: 11px 12px 10px 14px;
}

.summary-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 6px;
}

.summary-label {
  font-size: 10px;
  color: color-mix(in srgb, var(--card-accent) 55%, #64748b);
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1.2;
}

.summary-card__badge {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #fff;
  background: linear-gradient(145deg, color-mix(in srgb, var(--card-accent) 78%, #fff), var(--card-accent));
  border: 1px solid color-mix(in srgb, var(--card-accent) 55%, #fff);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 6px color-mix(in srgb, var(--card-accent) 35%, transparent);
  flex-shrink: 0;
}

.summary-value {
  font-size: 19px;
  font-weight: 800;
  color: var(--pb-ink);
  line-height: 1.12;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
  transition: color 0.25s ease, transform 0.25s ease;
}

.summary-card:hover .summary-value {
  transform: translateY(-1px);
}

.summary-value.negative {
  color: #dc2626;
}

.summary-value.positive {
  color: color-mix(in srgb, var(--card-accent) 82%, #0f172a);
}

.summary-desc {
  margin-top: 5px;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.3;
}

/* 当月 / 前月 / 前年同月 */
.period-compare-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 8px;
  min-height: 96px;
}

.period-compare-card {
  --pc-accent: #0d9488;
  position: relative;
  overflow: hidden;
  padding: 12px 12px 10px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--pc-accent) 30%, #e2e8f0);
  background:
    linear-gradient(160deg, #ffffff 0%, color-mix(in srgb, var(--pc-accent) 10%, #fff) 48%, #f8fafc 100%);
  box-shadow:
    inset 0 1px 0 #fff,
    0 2px 0 color-mix(in srgb, var(--pc-accent) 14%, #cbd5e1),
    0 10px 22px rgba(15, 23, 42, 0.07);
  transition:
    transform 0.25s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.25s ease;
  animation: kpiCardIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.period-compare-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--pc-accent), color-mix(in srgb, var(--pc-accent) 30%, transparent));
}

.period-compare-card__glow {
  position: absolute;
  width: 120px;
  height: 120px;
  right: -30px;
  top: -40px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--pc-accent) 28%, transparent), transparent 68%);
  pointer-events: none;
  opacity: 0.85;
}

.period-compare-card:hover {
  transform: translateY(-4px);
  box-shadow:
    inset 0 1px 0 #fff,
    0 3px 0 color-mix(in srgb, var(--pc-accent) 18%, #94a3b8),
    0 16px 30px color-mix(in srgb, var(--pc-accent) 18%, transparent);
}

.period-compare-card--current { --pc-accent: #0d9488; }
.period-compare-card--prev { --pc-accent: #0284c7; }
.period-compare-card--yoy { --pc-accent: #7c3aed; }

.period-compare-card__head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.period-compare-card__label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.period-compare-card__chip {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--pc-accent) 85%, #0f172a);
  background: color-mix(in srgb, var(--pc-accent) 14%, #fff);
  border: 1px solid color-mix(in srgb, var(--pc-accent) 28%, #e2e8f0);
  box-shadow: inset 0 1px 0 #fff;
}

.period-compare-card__month {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.period-compare-card__metrics {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.period-compare-metric {
  padding: 7px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: inset 0 1px 0 #fff, 0 1px 3px rgba(15, 23, 42, 0.04);
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.period-compare-card:hover .period-compare-metric {
  transform: translateY(-1px);
}

.period-compare-metric--baseline {
  border-color: rgba(13, 148, 136, 0.28);
  background: linear-gradient(180deg, #fff 0%, #f0fdfa 100%);
}
.period-compare-metric--rate {
  border-color: rgba(2, 132, 199, 0.28);
  background: linear-gradient(180deg, #fff 0%, #f0f9ff 100%);
}
.period-compare-metric--diff {
  border-color: rgba(225, 29, 72, 0.22);
  background: linear-gradient(180deg, #fff 0%, #fff1f2 100%);
}

.period-compare-metric__k {
  display: block;
  font-size: 9px;
  font-weight: 750;
  color: #94a3b8;
  letter-spacing: 0.04em;
  margin-bottom: 3px;
}

.period-compare-metric__v {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}

.period-compare-metric__v.is-warn {
  color: #d97706;
}
.period-compare-metric__v.is-ok {
  color: #059669;
}
.period-compare-metric__v.is-neg {
  color: #dc2626;
}

.period-compare-card__delta {
  position: relative;
  z-index: 1;
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  color: #0f766e;
  background: rgba(13, 148, 136, 0.1);
  border: 1px solid rgba(13, 148, 136, 0.22);
  white-space: nowrap;
}

.period-compare-card__delta--inline {
  margin-top: 0;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.01em;
  font-variant-numeric: tabular-nums;
}

.period-compare-card__delta--inline.is-up {
  color: #15803d;
  background: rgba(22, 163, 74, 0.1);
  border-color: rgba(22, 163, 74, 0.25);
}

.period-compare-card__delta--inline.is-down {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.22);
}

.period-compare-card__delta--yoy {
  color: #6d28d9;
  background: rgba(124, 58, 237, 0.1);
  border-color: rgba(124, 58, 237, 0.22);
  margin-left: 0;
}

@media (max-width: 1280px) {
  .summary-row {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .summary-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .period-compare-row {
    grid-template-columns: 1fr;
  }
  .period-compare-card__metrics {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}

/* 推移 / ヒートマップ（各々独占1行） */
.analytics-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 8px;
}

.analytics-row > .trend-chart-card,
.analytics-row > .heatmap-card {
  width: 100%;
  margin-bottom: 0;
}

/* 日次推移チャート：日付で整行を使い切る */
.trend-chart-card {
  animation: fadeInUp 0.52s cubic-bezier(0.22, 1, 0.36, 1) 0.03s backwards;
  border-color: rgba(99, 102, 241, 0.28) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 4px rgba(15, 23, 42, 0.05),
    0 10px 26px rgba(99, 102, 241, 0.08);
}

.trend-chart-card :deep(.el-card__header) {
  padding: 9px 12px 10px !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background:
    radial-gradient(ellipse 50% 80% at 0% 0%, rgba(99, 102, 241, 0.1), transparent 55%),
    linear-gradient(180deg, #fafbff 0%, #ffffff 100%);
}

.trend-chart-card :deep(.el-card__body) {
  padding: 6px 8px 8px !important;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 45%);
}

.trend-chart-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
}

.trend-chart-head__lead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  min-width: 0;
}

.trend-chart-head__icon-wrap {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(145deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid #c7d2fe;
  box-shadow: inset 0 1px 0 #fff, 0 2px 6px rgba(99, 102, 241, 0.18);
  flex-shrink: 0;
}

.trend-chart-head__icon {
  font-size: 18px;
  color: #4f46e5;
}

.trend-chart-head__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.trend-chart-head__title {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.02em;
  line-height: 1.2;
}

.trend-chart-head__sub {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  line-height: 1.25;
}

.trend-chart-head__tag {
  border-radius: 8px !important;
  font-weight: 650 !important;
}

.trend-chart-head__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  padding: 5px 10px;
  margin-left: auto;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  border: 1px solid rgba(148, 163, 184, 0.45);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9), 0 2px 6px rgba(15, 23, 42, 0.06);
}

.trend-chart-body {
  width: 100%;
  min-height: 280px;
}

.trend-chart-canvas {
  width: 100%;
  height: clamp(280px, 36vw, 400px);
  min-height: 280px;
}

.trend-chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  padding: 8px;
}

@media (max-width: 900px) {
  .trend-chart-head__controls {
    margin-left: 0;
    width: 100%;
  }
  .trend-chart-canvas {
    height: 260px;
    min-height: 240px;
  }
}

/* 月間ヒートマップ（コンパクト縮小） */
.heatmap-card {
  animation: fadeInUp 0.52s cubic-bezier(0.22, 1, 0.36, 1) 0.04s backwards;
  border-color: rgba(245, 158, 11, 0.32) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 4px rgba(15, 23, 42, 0.05),
    0 10px 26px rgba(245, 158, 11, 0.08);
}

.heatmap-card :deep(.el-card__header) {
  padding: 7px 10px 8px !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background:
    radial-gradient(ellipse 50% 80% at 0% 0%, rgba(251, 191, 36, 0.12), transparent 55%),
    linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
}

.heatmap-card :deep(.el-card__body) {
  padding: 6px 8px 8px !important;
}

.heatmap-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 8px;
}

.heatmap-head__lead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  min-width: 0;
}

.heatmap-head__icon-wrap {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(145deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #fcd34d;
  box-shadow: inset 0 1px 0 #fff, 0 2px 6px rgba(245, 158, 11, 0.2);
}

.heatmap-head__icon {
  font-size: 15px;
  color: #d97706;
}

.heatmap-head__titles {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.heatmap-head__title {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.heatmap-head__sub {
  font-size: 10px;
  color: #64748b;
}


.heatmap-body {
  min-height: 0;
}

.heatmap-panels {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  align-items: start;
}

.heatmap-panel {
  position: relative;
  padding: 8px 8px 7px;
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: inset 0 1px 0 #fff, 0 2px 8px rgba(15, 23, 42, 0.05);
}

.heatmap-panel--achievement {
  border-color: rgba(16, 185, 129, 0.35);
  background:
    radial-gradient(ellipse 60% 50% at 0% 0%, rgba(16, 185, 129, 0.08), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);
}
.heatmap-panel--actualDiff {
  border-color: rgba(245, 158, 11, 0.4);
  background:
    radial-gradient(ellipse 60% 50% at 0% 0%, rgba(245, 158, 11, 0.1), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #fffbeb 100%);
}
.heatmap-panel--actualQty {
  border-color: rgba(6, 182, 212, 0.4);
  background:
    radial-gradient(ellipse 60% 50% at 0% 0%, rgba(6, 182, 212, 0.1), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
}

.heatmap-panel__head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 22px;
  margin-bottom: 6px;
  padding: 0 72px;
}

.heatmap-panel__title {
  font-size: 12px;
  font-weight: 800;
  color: #0f172a;
  text-align: center;
  letter-spacing: 0.02em;
  margin: 0;
}

.heatmap-panel__unit {
  position: absolute;
  top: 0;
  right: 0;
  margin: 0;
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 700;
  color: #0f766e;
  background: rgba(13, 148, 136, 0.1);
  border: 1px solid rgba(13, 148, 136, 0.22);
  white-space: nowrap;
  line-height: 1.2;
  box-shadow: inset 0 1px 0 #fff;
}

.heatmap-weekdays {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 3px;
  margin-bottom: 4px;
}

.heatmap-weekdays span {
  text-align: center;
  font-size: 10px;
  font-weight: 750;
  color: #94a3b8;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
}

.heatmap-cell {
  aspect-ratio: 1;
  min-height: 42px;
  border-radius: 6px;
  border: 1px solid rgba(203, 213, 225, 0.65);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65), 0 1px 2px rgba(15, 23, 42, 0.05);
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease;
}

.heatmap-cell--pad {
  visibility: hidden;
  border: none;
  box-shadow: none;
  min-height: 0;
}

.heatmap-cell:not(.heatmap-cell--pad):hover {
  transform: scale(1.06);
  z-index: 1;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.12);
}

.heatmap-cell--alert {
  outline: 1.5px solid rgba(234, 88, 12, 0.75);
  outline-offset: -1px;
}

.heatmap-cell--clickable {
  cursor: pointer;
}

.heatmap-cell--clickable:active {
  transform: scale(0.96);
}

.heatmap-cell__inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 3px 2px;
  cursor: default;
}

.heatmap-cell__day {
  font-size: 11px;
  font-weight: 800;
  color: #334155;
  line-height: 1;
}

.heatmap-cell__val {
  font-size: 11px;
  font-weight: 750;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.heatmap-legend {
  margin-top: 5px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.heatmap-legend__label {
  font-size: 9px;
  color: #64748b;
  font-weight: 650;
}

.heatmap-legend__bar {
  height: 6px;
  width: 100%;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.8);
}

.heatmap-legend__bar--achievement {
  background: linear-gradient(90deg, #fca5a5 0%, #fde68a 35%, #bbf7d0 70%, #4ade80 100%);
}

.heatmap-legend__bar--actualDiff {
  background: linear-gradient(90deg, #f87171 0%, #fed7aa 45%, #bbf7d0 75%, #22c55e 100%);
}

.heatmap-legend__bar--actualQty {
  background: linear-gradient(90deg, #ecfeff 0%, #a5f3fc 40%, #22d3ee 70%, #0891b2 100%);
}

.heatmap-legend__hint {
  font-size: 8px;
  color: #94a3b8;
  font-weight: 600;
}

.heatmap-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

@media (max-width: 1100px) {
  .heatmap-panels {
    grid-template-columns: 1fr;
  }
}

.toolbar-filter {
  width: 140px;
}

/* 表格卡片 */
.table-card {
  border-radius: 12px !important;
  border: 1px solid var(--pb-line) !important;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
  box-shadow: var(--pb-elev-inset), var(--pb-elev-1);
  margin-bottom: 8px;
  animation: fadeInUp 0.55s cubic-bezier(0.22, 1, 0.36, 1);
  transition:
    box-shadow 0.25s ease,
    transform 0.2s ease;
}

.table-card:hover {
  box-shadow: var(--pb-elev-inset), var(--pb-elev-2);
}

.table-card :deep(.el-card__header) {
  padding: 8px 12px 10px;
}

.table-card :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

/* ベースライン比較一覧カード */
.baseline-comparison-card {
  border-radius: 14px !important;
  border: 1px solid rgba(13, 148, 136, 0.28) !important;
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 0 rgba(13, 148, 136, 0.08),
    0 12px 28px rgba(15, 23, 42, 0.08);
}

.baseline-comparison-card :deep(.el-card__header) {
  padding: 10px 14px 11px !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background:
    radial-gradient(ellipse 55% 80% at 0% 0%, rgba(13, 148, 136, 0.12), transparent 55%),
    linear-gradient(180deg, #f0fdfa 0%, #ffffff 100%);
}

.baseline-comparison-card :deep(.el-card__body) {
  padding: 8px 10px 12px !important;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 42%);
}

.comparison-list-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
}

.comparison-list-head__lead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  min-width: 0;
}

.comparison-list-head__icon-wrap {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  background: linear-gradient(145deg, #5eead4 0%, #0d9488 100%);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    0 3px 10px rgba(13, 148, 136, 0.28);
  flex-shrink: 0;
}

.comparison-list-head__icon {
  font-size: 18px;
  color: #fff;
}

.comparison-list-head__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.comparison-list-head__title {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.02em;
  line-height: 1.2;
}

.comparison-list-head__sub {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  line-height: 1.25;
}

.comparison-list-head__tag {
  border-radius: 8px !important;
  font-weight: 650 !important;
}

.comparison-list-head__tag--alert {
  animation: alertPulse 1.8s ease-in-out infinite;
}

.alert-ctl {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  padding: 4px 8px;
  margin-right: 2px;
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
  border-radius: 10px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.alert-ctl__label {
  font-size: 11px;
  font-weight: 750;
  color: #9a3412;
  letter-spacing: 0.02em;
  white-space: nowrap;
  cursor: help;
}

.alert-ctl__input {
  width: 88px;
}

.alert-ctl__input :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.alert-ctl__unit {
  font-size: 11px;
  font-weight: 700;
  color: #c2410c;
  margin-right: 2px;
}

.alert-ctl :deep(.el-checkbox) {
  margin-right: 0;
  height: auto;
}

.alert-ctl :deep(.el-checkbox__label) {
  font-size: 11px;
  font-weight: 650;
  color: #9a3412;
  padding-left: 4px;
}

.tab-alert-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  margin-left: 2px;
  border-radius: 999px;
  background: linear-gradient(180deg, #fb7185 0%, #e11d48 100%);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 1px 3px rgba(225, 29, 72, 0.35);
}

.alert-row-icon {
  font-size: 14px;
  color: #ea580c;
  margin-left: 2px;
  animation: alertPulse 1.6s ease-in-out infinite;
}

@keyframes alertPulse {
  0%,
  100% {
    opacity: 1;
    filter: brightness(1);
  }
  50% {
    opacity: 0.82;
    filter: brightness(1.08);
  }
}

:deep(.comparison-table .comparison-row--alert > td) {
  background: linear-gradient(90deg, rgba(254, 243, 199, 0.95) 0%, rgba(255, 237, 213, 0.75) 100%) !important;
}

:deep(.comparison-table .comparison-row--alert:hover > td) {
  background: linear-gradient(90deg, rgba(253, 230, 138, 0.98) 0%, rgba(254, 215, 170, 0.88) 100%) !important;
}

:deep(.comparison-table .comparison-row--focus > td) {
  background: linear-gradient(90deg, rgba(191, 219, 254, 0.95) 0%, rgba(199, 210, 254, 0.85) 100%) !important;
  animation: rowFocusPulse 1.2s ease-in-out 2;
}

:deep(.comparison-table .comparison-row--focus:hover > td) {
  background: linear-gradient(90deg, rgba(147, 197, 253, 0.98) 0%, rgba(165, 180, 252, 0.9) 100%) !important;
}

@keyframes rowFocusPulse {
  0%,
  100% {
    box-shadow: inset 0 0 0 0 rgba(59, 130, 246, 0);
  }
  50% {
    box-shadow: inset 0 0 0 2px rgba(59, 130, 246, 0.55);
  }
}

:deep(.comparison-table .el-table__fixed-left .comparison-row--alert > td) {
  background: linear-gradient(90deg, rgba(254, 243, 199, 0.98) 0%, rgba(255, 237, 213, 0.9) 100%) !important;
}

:deep(.comparison-table .el-table__fixed-left .comparison-row--alert:hover > td) {
  background: linear-gradient(90deg, rgba(253, 230, 138, 0.98) 0%, rgba(254, 215, 170, 0.92) 100%) !important;
}

.comparison-list-head__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 6px 8px 6px 10px;
  margin-left: auto;
  background: linear-gradient(180deg, #f8fafc 0%, #e8eef5 100%);
  border: 1px solid rgba(148, 163, 184, 0.45);
  border-radius: 12px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 2px 6px rgba(15, 23, 42, 0.06);
}

.comparison-list-btn {
  border-radius: 10px !important;
  font-weight: 700 !important;
  padding: 5px 12px !important;
}

@media (max-width: 900px) {
  .comparison-list-head__actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
}


.count-tag {
  font-weight: 650;
  border-radius: 8px !important;
}

.baseline-adjust-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 8px 24px rgba(15, 23, 42, 0.12),
    0 24px 48px rgba(13, 148, 136, 0.12);
}

.baseline-adjust-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 16px 20px 0;
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%);
}

.baseline-adjust-dialog :deep(.el-dialog__body) {
  padding: 16px 20px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 80%);
}

.baseline-adjust-dialog :deep(.el-dialog__footer) {
  padding: 12px 20px 16px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.pb-gen-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 10px 28px rgba(15, 23, 42, 0.14),
    0 28px 56px rgba(13, 148, 136, 0.1);
}

.pb-gen-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 18px 20px 0;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0f9ff 55%, #ffffff 100%);
}

.pb-gen-dialog :deep(.el-dialog__body) {
  padding: 14px 20px 8px;
}

.pb-gen-dialog :deep(.el-dialog__footer) {
  padding: 12px 20px 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border-top: 1px solid #e2e8f0;
}

.pb-gen-dialog__head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding-bottom: 12px;
}

.pb-gen-dialog__icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0f766e;
  background: linear-gradient(145deg, #ccfbf1 0%, #99f6e4 100%);
  border: 1px solid rgba(13, 148, 136, 0.28);
  box-shadow: inset 0 1px 0 #fff, 0 2px 8px rgba(13, 148, 136, 0.18);
}

.pb-gen-dialog__icon--adjust {
  color: #0369a1;
  background: linear-gradient(145deg, #e0f2fe 0%, #bae6fd 100%);
  border-color: rgba(2, 132, 199, 0.28);
  box-shadow: inset 0 1px 0 #fff, 0 2px 8px rgba(2, 132, 199, 0.16);
}

.pb-gen-dialog__titles {
  flex: 1;
  min-width: 0;
}

.pb-gen-dialog__title {
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.01em;
}

.pb-gen-dialog__sub {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
}

.pb-gen-dialog__chip {
  flex-shrink: 0;
  font-weight: 700 !important;
  border: none !important;
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important;
}

.pb-gen-dialog__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pb-gen-dialog__meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pb-gen-dialog__meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.pb-gen-dialog__meta-k {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
}

.pb-gen-dialog__meta-v {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.pb-cal-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pb-cal {
  padding: 12px;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: inset 0 1px 0 #fff;
}

.pb-cal__weekdays,
.pb-cal__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
}

.pb-cal__weekdays {
  margin-bottom: 8px;
}

.pb-cal__wd {
  text-align: center;
  font-size: 11px;
  font-weight: 800;
  color: #64748b;
}

.pb-cal__wd.is-sun {
  color: #dc2626;
}

.pb-cal__wd.is-sat {
  color: #2563eb;
}

.pb-cal__cell {
  height: 36px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.12s ease;
}

.pb-cal__cell:not(.is-pad):hover {
  background: rgba(13, 148, 136, 0.08);
  border-color: rgba(13, 148, 136, 0.25);
}

.pb-cal__cell.is-pad {
  cursor: default;
  pointer-events: none;
}

.pb-cal__cell.is-sun:not(.is-selected) {
  color: #dc2626;
}

.pb-cal__cell.is-sat:not(.is-selected) {
  color: #2563eb;
}

.pb-cal__cell.is-selected {
  color: #fff;
  background: linear-gradient(145deg, #0d9488 0%, #0891b2 100%);
  border-color: rgba(13, 148, 136, 0.55);
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.28);
}

.pb-cal__cell.is-selected.is-sun {
  background: linear-gradient(145deg, #e11d48 0%, #f43f5e 100%);
  border-color: rgba(225, 29, 72, 0.45);
  box-shadow: 0 2px 8px rgba(225, 29, 72, 0.22);
}

.pb-cal__cell.is-selected.is-sat {
  background: linear-gradient(145deg, #2563eb 0%, #3b82f6 100%);
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.22);
}

.pb-cal__cell:active:not(.is-pad) {
  transform: scale(0.96);
}

.pb-gen-dialog__form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.pb-gen-dialog__form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #334155;
}

.pb-gen-dialog__control {
  width: 100%;
}

.pb-gen-dialog__hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.5;
  color: #92400e;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.pb-gen-dialog__hint .el-icon {
  margin-top: 1px;
  flex-shrink: 0;
  color: #d97706;
}

.pb-gen-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.pb-confirm-dialog {
  border-radius: 14px !important;
  overflow: hidden;
}

.pb-confirm-dialog .el-message-box__header {
  padding-top: 16px;
}

.pb-confirm-dialog .el-message-box__title {
  font-weight: 800;
  color: #0f172a;
}

.pb-confirm-box__lead {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
  line-height: 1.55;
}

.pb-confirm-box__warn {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  color: #b45309;
}

.pb-confirm-box__meta {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: #0f766e;
  font-variant-numeric: tabular-nums;
}

.adjustment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.adjustment-header__text {
  flex: 1;
  min-width: 0;
}

.adjustment-header__stats {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.adjustment-stat {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  background: rgba(13, 148, 136, 0.1);
  border: 1px solid rgba(13, 148, 136, 0.22);
}

.adjustment-stat em {
  font-style: normal;
  font-size: 14px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.adjustment-stat--edit {
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.3);
}

.adjustment-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 4px;
}

.adjustment-desc {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.adjustment-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 14px 0 12px;
  padding: 10px 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: inset 0 1px 0 #fff;
}

.toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.toolbar-month,
.toolbar-process {
  width: 160px;
}

.toolbar-filter {
  width: 140px;
}

.adjustment-add-panel {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0f9ff 55%, #ffffff 100%);
  border: 1px solid rgba(13, 148, 136, 0.28);
  box-shadow: inset 0 1px 0 #fff, 0 2px 10px rgba(13, 148, 136, 0.08);
}

.adjustment-add-panel__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 800;
  color: #0f766e;
}

.adjustment-add-panel__hint {
  margin-left: 4px;
  font-size: 11px;
  font-weight: 650;
  color: #64748b;
}

.adjustment-add-panel__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.adjustment-add-date {
  width: 160px;
}

.adjustment-add-process {
  width: 140px;
}

.adjustment-add-qty {
  width: 150px;
}

.adjustment-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.adjustment-table :deep(.el-table__header th) {
  background: linear-gradient(135deg, #0f766e 0%, #0d9488 48%, #0891b2 100%);
  color: #fff;
  font-weight: 700;
  border-bottom: none;
}

.adjustment-table :deep(.el-table__header th .cell) {
  color: #fff;
}

.adjustment-table :deep(.el-table__row) {
  transition: background 0.2s ease;
}

.adjustment-table :deep(.adjustment-row--new > td) {
  background: linear-gradient(90deg, rgba(204, 251, 241, 0.9) 0%, rgba(236, 253, 245, 0.7) 100%) !important;
}

.adjustment-table :deep(.adjustment-row--dirty > td) {
  background: linear-gradient(90deg, rgba(254, 243, 199, 0.85) 0%, rgba(255, 251, 235, 0.7) 100%) !important;
}

.adjustment-actions {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.adjustment-table :deep(.el-table__row:hover > td) {
  background: rgba(13, 148, 136, 0.08) !important;
}

.adjustment-date {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

.adjustment-new-tag {
  border-radius: 999px !important;
  font-weight: 800 !important;
}

.adjustment-process-tag {
  font-weight: 700 !important;
  color: color-mix(in srgb, var(--tone, #64748b) 80%, #0f172a) !important;
  background: color-mix(in srgb, var(--tone, #64748b) 12%, #fff) !important;
  border-color: color-mix(in srgb, var(--tone, #64748b) 28%, #e2e8f0) !important;
}

.plan-editor {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 6px 10px;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 10px;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.plan-editor.is-dirty {
  background: #fffbeb;
  border-color: rgba(245, 158, 11, 0.45);
}

.plan-editor-current {
  font-size: 12px;
  color: #475569;
}

.plan-input {
  display: flex;
  align-items: center;
}

.plan-input :deep(.el-input-number__increase),
.plan-input :deep(.el-input-number__decrease) {
  display: none;
}

.plan-input :deep(.el-input-number) {
  width: 140px;
}

.plan-input :deep(.el-input__inner) {
  text-align: right;
}

.adjustment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  width: 100%;
  flex-wrap: wrap;
}

.adjustment-footer__note {
  font-size: 11px;
  font-weight: 650;
  color: #64748b;
}

.adjustment-footer__actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.adjustment-footer__actions .el-button:first-child {
  font-weight: 700;
}

/* ベースライン比較：工程タブ（card 型・コンパクト） */
.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card) {
  border: none;
  background: transparent;
  box-shadow: none;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card > .el-tabs__header) {
  margin: 0 0 6px;
  border: none;
  background: transparent;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__nav-wrap) {
  margin-bottom: 0;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__nav) {
  border: none;
  gap: 5px;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card > .el-tabs__header .el-tabs__nav-wrap) {
  border-bottom: none;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__item) {
  border: 1px solid rgba(203, 213, 225, 0.95) !important;
  border-radius: 9px !important;
  height: 32px;
  line-height: 30px;
  padding: 0 12px !important;
  font-size: 12px;
  font-weight: 650;
  color: #64748b;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
  box-shadow: inset 0 1px 0 #fff, 0 1px 2px rgba(15, 23, 42, 0.04);
  transition:
    color 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.15s ease;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__item.is-active) {
  font-weight: 800;
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 #fff,
    0 3px 8px rgba(15, 23, 42, 0.1);
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__item:hover) {
  transform: translateY(-1px);
  filter: none;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__nav-scroll) {
  padding: 2px 0;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-tone-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='切断'])) {
  color: #1d4ed8;
  background: #eff6ff;
  border-color: #93c5fd !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='切断']).is-active) {
  color: #1e40af !important;
  background: linear-gradient(180deg, #ffffff 0%, #dbeafe 100%) !important;
  border-color: #60a5fa !important;
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='面取'])) {
  color: #15803d;
  background: #f0fdf4;
  border-color: #86efac !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='面取']).is-active) {
  color: #166534 !important;
  background: linear-gradient(180deg, #ffffff 0%, #dcfce7 100%) !important;
  border-color: #4ade80 !important;
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='成型'])) {
  color: #b45309;
  background: #fffbeb;
  border-color: #fcd34d !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='成型']).is-active) {
  color: #92400e !important;
  background: linear-gradient(180deg, #ffffff 0%, #fef3c7 100%) !important;
  border-color: #fbbf24 !important;
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='メッキ'])) {
  color: #b91c1c;
  background: #fef2f2;
  border-color: #fca5a5 !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='メッキ']).is-active) {
  color: #991b1b !important;
  background: linear-gradient(180deg, #ffffff 0%, #fee2e2 100%) !important;
  border-color: #f87171 !important;
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='溶接'])) {
  color: #0369a1;
  background: #f0f9ff;
  border-color: #7dd3fc !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='溶接']).is-active) {
  color: #075985 !important;
  background: linear-gradient(180deg, #ffffff 0%, #e0f2fe 100%) !important;
  border-color: #38bdf8 !important;
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='溶接SP'])) {
  color: #6d28d9;
  background: #f5f3ff;
  border-color: #c4b5fd !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='溶接SP']).is-active) {
  color: #5b21b6 !important;
  background: linear-gradient(180deg, #ffffff 0%, #ede9fe 100%) !important;
  border-color: #a78bfa !important;
}

.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='検査'])) {
  color: #0f766e;
  background: #f0fdfa;
  border-color: #5eead4 !important;
}
.baseline-comparison-card :deep(.el-tabs__item:has([data-tone='検査']).is-active) {
  color: #115e59 !important;
  background: linear-gradient(180deg, #ffffff 0%, #ccfbf1 100%) !important;
  border-color: #2dd4bf !important;
}

/* 合計区域（色分け＋立体） */
.tab-total-wrapper {
  --total-accent: #0d9488;
  margin-top: 10px;
  padding: 12px 12px 11px;
  background:
    radial-gradient(ellipse 50% 80% at 0% 0%, rgba(13, 148, 136, 0.1), transparent 55%),
    linear-gradient(165deg, #ffffff 0%, #f0fdfa 45%, #f8fafc 100%);
  border: 1px solid rgba(13, 148, 136, 0.28);
  border-radius: 14px;
  box-shadow:
    inset 0 1px 0 #fff,
    0 2px 0 rgba(13, 148, 136, 0.1),
    0 10px 22px rgba(15, 23, 42, 0.07);
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease,
    transform 0.22s ease;
  animation: kpiCardIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.tab-total-wrapper:hover {
  border-color: rgba(13, 148, 136, 0.45);
  box-shadow:
    inset 0 1px 0 #fff,
    0 3px 0 rgba(13, 148, 136, 0.12),
    0 14px 28px rgba(13, 148, 136, 0.12);
  transform: translateY(-2px);
}

.tab-total-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(167, 243, 208, 0.65);
}

.tab-total-header__lead {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.tab-total-header__badge {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  background: linear-gradient(145deg, #5eead4 0%, #0d9488 100%);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 8px rgba(13, 148, 136, 0.3);
}

.total-icon {
  font-size: 15px;
  color: #fff;
}

.tab-total-label {
  font-weight: 800;
  color: #0f172a;
  font-size: 14px;
  letter-spacing: 0.04em;
}

.tab-total-process {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 750;
  color: #0f766e;
  background: rgba(13, 148, 136, 0.12);
  border: 1px solid rgba(13, 148, 136, 0.25);
  box-shadow: inset 0 1px 0 #fff;
}

.tab-total-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.total-item {
  --item-accent: #64748b;
  position: relative;
  isolation: isolate;
  padding: 10px 11px 9px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--item-accent) 28%, #e2e8f0);
  background: linear-gradient(
    155deg,
    #ffffff 0%,
    color-mix(in srgb, var(--item-accent) 10%, #fff) 48%,
    color-mix(in srgb, var(--item-accent) 14%, #f8fafc) 100%
  );
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 #fff,
    0 2px 0 color-mix(in srgb, var(--item-accent) 12%, #cbd5e1),
    0 4px 12px rgba(15, 23, 42, 0.05);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease,
    border-color 0.2s ease;
  animation: kpiCardIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.total-item:nth-child(1) { animation-delay: 0.02s; }
.total-item:nth-child(2) { animation-delay: 0.05s; }
.total-item:nth-child(3) { animation-delay: 0.08s; }
.total-item:nth-child(4) { animation-delay: 0.11s; }
.total-item:nth-child(5) { animation-delay: 0.14s; }

.total-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--item-accent) 85%, #fff), var(--item-accent));
  box-shadow: 1px 0 8px color-mix(in srgb, var(--item-accent) 40%, transparent);
  z-index: 1;
}

.total-item::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--item-accent), transparent 80%);
  opacity: 0.75;
  z-index: 1;
}

.total-item__glow {
  position: absolute;
  top: -40%;
  right: -20%;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--item-accent) 32%, transparent), transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.total-item:hover {
  transform: translateY(-3px) scale(1.01);
  border-color: color-mix(in srgb, var(--item-accent) 48%, #cbd5e1);
  box-shadow:
    inset 0 1px 0 #fff,
    0 3px 0 color-mix(in srgb, var(--item-accent) 18%, #94a3b8),
    0 12px 22px color-mix(in srgb, var(--item-accent) 18%, transparent);
}

.total-item-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.total-item-icon-wrap {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #fff;
  background: linear-gradient(145deg, color-mix(in srgb, var(--item-accent) 75%, #fff), var(--item-accent));
  border: 1px solid color-mix(in srgb, var(--item-accent) 45%, #fff);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    0 2px 6px color-mix(in srgb, var(--item-accent) 30%, transparent);
  flex-shrink: 0;
}

.total-item-icon {
  font-size: 12px;
  color: #fff;
}

.total-item-label {
  font-size: 10px;
  color: color-mix(in srgb, var(--item-accent) 45%, #64748b);
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.total-item-value {
  position: relative;
  z-index: 1;
  font-size: 17px;
  font-weight: 800;
  color: color-mix(in srgb, var(--item-accent) 78%, #0f172a);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 4px;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}

.baseline-plan-item { --item-accent: #0d9488; }
.current-plan-item { --item-accent: #0284c7; }
.plan-diff-item { --item-accent: #d97706; }
.actual-item { --item-accent: #059669; }
.actual-diff-item { --item-accent: #e11d48; }

.plan-diff-item.diff-positive,
.actual-diff-item.diff-positive {
  --item-accent: #059669;
}

.plan-diff-item.diff-negative,
.actual-diff-item.diff-negative {
  --item-accent: #dc2626;
}

.plan-diff-item.diff-zero,
.actual-diff-item.diff-zero {
  --item-accent: #64748b;
}

.total-trend-icon {
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.total-trend-icon.trend-up {
  color: #059669;
}

.total-trend-icon.trend-down {
  color: #dc2626;
}

/* 表格（比較一覧）— 幅確保・改行なし・色分け */
:deep(.comparison-table) {
  font-size: 12px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(203, 213, 225, 0.9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 4px 14px rgba(15, 23, 42, 0.06);
}

:deep(.comparison-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.comparison-table .el-table__border-column-patch) {
  display: none;
}

:deep(.comparison-table .el-table__header-wrapper) {
  border-radius: 12px 12px 0 0;
}

:deep(.comparison-table .el-table__header th) {
  background: linear-gradient(135deg, #0f766e 0%, #0d9488 48%, #0891b2 100%);
  color: white;
  font-weight: 700;
  font-size: 12px;
  padding: 9px 10px;
  border: none;
  text-align: center;
  white-space: nowrap !important;
}

:deep(.comparison-table .el-table__header th .cell) {
  color: white;
  font-weight: 700;
  white-space: nowrap !important;
  overflow: visible;
  line-height: 1.25;
  padding: 0 4px;
}

:deep(.comparison-table .el-table__header th.th-baseline) {
  background: linear-gradient(180deg, #0f766e 0%, #0d9488 100%);
}
:deep(.comparison-table .el-table__header th.th-current) {
  background: linear-gradient(180deg, #0369a1 0%, #0284c7 100%);
}
:deep(.comparison-table .el-table__header th.th-plan-diff) {
  background: linear-gradient(180deg, #b45309 0%, #d97706 100%);
}
:deep(.comparison-table .el-table__header th.th-actual) {
  background: linear-gradient(180deg, #047857 0%, #059669 100%);
}
:deep(.comparison-table .el-table__header th.th-actual-diff) {
  background: linear-gradient(180deg, #be123c 0%, #e11d48 100%);
}

:deep(.comparison-table .el-table__header th:first-child) {
  border-radius: 12px 0 0 0;
  background: linear-gradient(180deg, #134e4a 0%, #0f766e 100%);
}

:deep(.comparison-table .el-table__body td) {
  padding: 6px 10px;
  border-color: #e8ecf1;
  transition: background-color 0.15s ease;
}

:deep(.comparison-table .el-table__body td .cell) {
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.35;
}

:deep(.comparison-table .el-table__row) {
  transition: background-color 0.15s ease;
}

:deep(.comparison-table .el-table__row:hover > td) {
  background-color: #ecfeff !important;
}

:deep(.comparison-table .el-table__row--striped td) {
  background-color: #f8fafc;
}

:deep(.comparison-table .el-table__row--striped:hover > td) {
  background-color: #e0f2fe !important;
}

:deep(.comparison-table .el-table__fixed-left-patch) {
  background-color: transparent;
}

:deep(.comparison-table .el-table__fixed) {
  box-shadow: 3px 0 12px rgba(15, 23, 42, 0.08);
}

:deep(.comparison-table .el-table__fixed-left) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__header th) {
  background: linear-gradient(180deg, #134e4a 0%, #0f766e 100%);
  color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__body td) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row:hover > td) {
  background-color: #ecfeff !important;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped td) {
  background-color: #f8fafc;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped:hover > td) {
  background-color: #e0f2fe !important;
}

:deep(.comparison-table td.col-baseline) {
  background-image: linear-gradient(90deg, rgba(13, 148, 136, 0.04), transparent 40%);
}
:deep(.comparison-table td.col-current) {
  background-image: linear-gradient(90deg, rgba(2, 132, 199, 0.04), transparent 40%);
}
:deep(.comparison-table td.col-actual) {
  background-image: linear-gradient(90deg, rgba(5, 150, 105, 0.04), transparent 40%);
}

/* 数值单元格样式 */
.number-cell {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 8px;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
  min-height: 24px;
  max-width: 100%;
  white-space: nowrap;
}

.number-cell:hover {
  background-color: rgba(13, 148, 136, 0.06);
}

.number-value {
  font-weight: 700;
  font-size: 13px;
  color: #0f172a;
  letter-spacing: 0.01em;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.number-value--muted {
  color: #94a3b8 !important;
  font-weight: 600;
}

.baseline-plan .number-value {
  color: #0f766e;
}

.current-plan .number-value {
  color: #0369a1;
}

.actual-cell .number-value {
  color: #047857;
}

.diff-cell.diff-positive {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.16) 0%, rgba(5, 150, 105, 0.07) 100%);
  border: 1px solid rgba(16, 185, 129, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.diff-cell.diff-positive .number-value {
  color: #059669;
}

.diff-cell.diff-negative {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.16) 0%, rgba(220, 38, 38, 0.07) 100%);
  border: 1px solid rgba(239, 68, 68, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.diff-cell.diff-negative .number-value {
  color: #dc2626;
}

.diff-cell.diff-zero {
  background: rgba(148, 163, 184, 0.06);
}

.diff-cell.diff-zero .number-value {
  color: #64748b;
}

.trend-icon {
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.trend-icon.trend-up {
  color: #10b981;
}

.trend-icon.trend-down {
  color: #ef4444;
}

/* 表格列头样式 */
.column-header {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  width: auto;
  max-width: 100%;
  white-space: nowrap;
}

.column-header span {
  color: white;
  font-weight: 700;
  white-space: nowrap;
}

.date-cell-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  max-width: 100%;
}

.date-cell {
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.date-icon {
  color: #0d9488;
  flex-shrink: 0;
}

.help-icon {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  cursor: help;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.help-icon:hover {
  color: white;
  transform: scale(1.1);
}

/* 动画关键帧 */
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

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.94) translateY(6px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes kpiCardIn {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.96);
    filter: blur(2px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@keyframes kpiSheen {
  0%,
  55% {
    transform: translateX(-130%);
  }
  75%,
  100% {
    transform: translateX(130%);
  }
}

@keyframes kpiGlowPulse {
  0%,
  100% {
    opacity: 0.75;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@keyframes orbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(10px, 8px, 0);
  }
}

@keyframes iconPulse {
  0%,
  100% {
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.5),
      0 4px 12px rgba(15, 23, 42, 0.18);
  }
  50% {
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.55),
      0 6px 16px rgba(255, 255, 255, 0.22),
      0 0 0 4px rgba(255, 255, 255, 0.08);
  }
}

@media (prefers-reduced-motion: reduce) {
  .page-header,
  .action-card,
  .summary-card,
  .table-card,
  .trend-chart-card,
  .heatmap-card,
  .period-compare-card,
  .tab-total-wrapper,
  .page-header__orb,
  .title-icon-wrapper {
    animation: none !important;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .action-content {
    flex-direction: column;
  }

  .action-divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    margin: 4px 0;
  }

  .section-controls {
    width: 100%;
  }

  .section-controls > * {
    flex: 1;
    min-width: 0;
  }

  .summary-row {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }

  .tab-total-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .plan-baseline-page {
    padding: 6px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .summary-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .tab-total-grid {
    grid-template-columns: 1fr;
  }

  .tab-total-wrapper {
    padding: 8px 10px;
  }

  .total-item {
    padding: 8px 10px;
  }

  .total-item-value {
    font-size: 16px;
  }
}

</style>
