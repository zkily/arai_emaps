<template>
  <div class="plan-baseline-root">
  <div class="plan-baseline-page">
    <!-- 紧凑型页面头部 -->
    <div class="page-header">
      <div class="title-wrapper">
        <div class="title-icon-wrapper">
          <el-icon class="title-icon"><TrendCharts /></el-icon>
        </div>
        <div class="title-content">
          <h2>生産計画ベースライン管理</h2>
          <p>月次計画を固定化し、現行計画・実績と比較して推移を把握します</p>
        </div>
        <el-tooltip content="操作説明を開く" placement="bottom" :show-after="0">
          <el-icon class="help-icon" @click="goHelpPage" :size="18">
            <QuestionFilled />
          </el-icon>
        </el-tooltip>
      </div>
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

    <!-- 合并的操作区域 -->
    <el-card class="action-card" shadow="hover">
      <div class="action-content">
        <div class="action-section generate-section">
          <div class="section-header">
            <div class="section-icon generate-icon-bg">
              <el-icon><DocumentAdd /></el-icon>
            </div>
            <div class="section-title">
              <h3>ベースライン生成</h3>
              <span class="section-desc">計画を固定化して比較基準を作成（成型・溶接は production_summarys の molding_plan／welding_plan を基準計画に反映）</span>
            </div>
          </div>
          <div class="section-controls">
            <el-date-picker
              v-model="queryForm.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="基準月"
              size="default"
              style="width: 140px"
            />
            <el-select
              v-model="queryForm.processName"
              clearable
              placeholder="全工程"
              size="default"
              style="width: 130px"
            >
              <el-option
                v-for="item in processOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-button
              type="success"
              class="btn-generate-modern"
              :icon="DocumentAdd"
              @click="handleGenerate"
              :loading="generating"
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
              size="default"
            >
              計画を修正
            </el-button>
          </div>
        </div>
        <div class="action-divider"></div>
        <div class="action-section filter-section">
          <div class="section-header">
            <div class="section-icon filter-icon-bg">
              <el-icon><Search /></el-icon>
            </div>
            <div class="section-title">
              <h3>比較条件</h3>
              <span class="section-desc">対象月と工程を指定して比較</span>
            </div>
          </div>
          <div class="section-controls">
            <el-date-picker
              v-model="queryForm.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="対象月"
              size="default"
              style="width: 140px"
            />
            <el-select
              v-model="queryForm.processName"
              clearable
              placeholder="工程"
              size="default"
              style="width: 130px"
            >
              <el-option
                v-for="item in processOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-button
              type="primary"
              class="btn-search-modern"
              :icon="Search"
              @click="loadComparison"
              :loading="tableLoading"
              size="default"
            >
              検索
            </el-button>
            <el-button
              class="btn-clear-modern"
              :icon="Refresh"
              @click="resetForm"
              size="default"
            >
              クリア
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 紧凑型摘要卡片 -->
    <div class="summary-row">
      <div
        class="summary-card"
        v-for="(card, index) in summaryCards"
        :key="card.label"
        :style="{ animationDelay: `${index * 0.05}s` }"
      >
        <div class="summary-card-inner">
          <div class="summary-label">{{ card.label }}</div>
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

    <!-- ベースライン比較一覧（工程別タブ＋表） -->
    <el-card shadow="hover" class="table-card baseline-comparison-card">
      <template #header>
        <div class="comparison-list-head">
          <div class="comparison-list-head__lead">
            <el-icon class="comparison-list-head__icon"><Setting /></el-icon>
            <div class="comparison-list-head__titles">
              <span class="comparison-list-head__title">ベースライン比較一覧</span>
              <span class="comparison-list-head__sub">工程別タブで日次の基準・現行・差異を表示</span>
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
          </div>
          <div class="comparison-list-head__actions">
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
            <span class="tab-label">
              {{ process.label }}
              <span class="tab-count">{{ process.count }}</span>
            </span>
          </template>
          <el-table
            :data="process.items"
            border
            stripe
            height="340"
            style="width: 100%"
            empty-text="データがありません"
            class="comparison-table"
          >
            <el-table-column prop="plan_date" label="日付" width="135" fixed="left">
              <template #default="{ row }">
                <div class="date-cell-wrapper">
                  <el-icon class="date-icon"><Calendar /></el-icon>
                  <span class="date-cell">{{ formatDate(row.plan_date) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="基準計画" width="120" align="right">
              <template #header>
                <div class="column-header">
                  <span>基準計画</span>
                  <el-tooltip
                    content="ベースライン生成時に固定化された計画値。成型・溶接は production_summarys の molding_plan／welding_plan の日次合計。その他は Excel 取込（production_plan_updates）を優先し、無い日はサマリの各 plan 列で補完。"
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
            <el-table-column label="現行計画" width="120" align="right">
              <template #header>
                <div class="column-header">
                  <span>現行計画</span>
                  <el-tooltip
                    content="切断・面取・メッキ・検査・外注メッキ・外注溶接・外注倉庫は現行計画＝基準計画（常に同期）。成型は molding_plan、溶接は welding_actual_plan（サマリのみ、Excel は使用しない。合計 0 の日も反映、該当日サマリが無い日は 0）。上記以外は production_plan_updates を優先し、無い日はサマリの各 plan 列で補完。"
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
            <el-table-column label="計画差異" width="120" align="right">
              <template #header>
                <div class="column-header">
                  <span>計画差異</span>
                  <el-tooltip content="現行計画 - 基準計画" placement="top" effect="dark">
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
            <el-table-column label="現行実績合計" width="140" align="right">
              <template #header>
                <div class="column-header">
                  <span>現行実績合計</span>
                  <el-tooltip
                    content="stock_transaction_logs から当月の日次実績を再集計"
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
                  <span class="number-value" style="color: #94a3b8">-</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="計画対実績差" width="140" align="right">
              <template #header>
                <div class="column-header">
                  <span>計画対実績差</span>
                  <el-tooltip content="ベースライン計画 - 現行実績" placement="top" effect="dark">
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
                  <span class="number-value" style="color: #94a3b8">-</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="tab-total-wrapper" v-if="processTotals.get(process.name)">
            <div class="tab-total-header">
              <el-icon class="total-icon"><DataAnalysis /></el-icon>
              <span class="tab-total-label">合計</span>
            </div>
            <div class="tab-total-grid">
              <div class="total-item current-plan-item">
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><Document /></el-icon>
                  <span class="total-item-label">現行計画</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.currentPlan) }}
                </div>
              </div>
              <div
                class="total-item plan-diff-item"
                :class="getDiffClass(processTotals.get(process.name)?.planDiff)"
              >
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><TrendCharts /></el-icon>
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
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><CircleCheck /></el-icon>
                  <span class="total-item-label">現行実績</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.currentActual) }}
                </div>
              </div>
              <div
                class="total-item actual-diff-item"
                :class="getDiffClass(processTotals.get(process.name)?.actualDiff)"
              >
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><DataLine /></el-icon>
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

    <!-- 操業度：成型計画一覧「設備操業度」と同一データ（fetchSchedulingGrid + 設備別集計） -->
    <el-card class="table-card operation-rate-card" shadow="hover">
      <template #header>
        <div class="operation-rate-head">
          <div class="operation-rate-head__lead">
            <el-icon class="card-header-icon"><DataLine /></el-icon>
            <span class="card-title">操業度</span>
            <span class="operation-rate-title-meta">APS 設備操業度（月次）</span>
            <el-tag v-if="planUtilizationRows.length > 0" type="primary" size="small" class="count-tag">
              {{ planUtilizationRows.length }} 設備
            </el-tag>
          </div>
          <div class="operation-rate-head__controls">
            <span class="operation-rate-ctl-label">集計月</span>
            <el-date-picker
              v-model="planRateFilter.baselineMonth"
              type="month"
              value-format="YYYY-MM"
              format="YYYY年MM月"
              placeholder="月"
              size="small"
              class="operation-rate-picker"
              :clearable="false"
              teleported
            />
            <span class="operation-rate-ctl-label">工程</span>
            <el-select
              v-model="planRateFilter.processCd"
              placeholder="工程を選択"
              filterable
              size="small"
              class="operation-rate-select"
              teleported
            >
              <el-option
                v-for="opt in planRateProcessSelectOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <el-button
              type="default"
              plain
              class="btn-print-operation-modern operation-rate-print-btn"
              :icon="Printer"
              @click="handlePrintOperationRate"
              :disabled="planUtilizationRows.length === 0"
              size="small"
            >
              印刷
            </el-button>
          </div>
        </div>
      </template>
      <div class="operation-rate-body">
        <div class="util-note util-note--baseline">
          <span class="util-note-chip">対象：{{ utilizationMonthLabelJp }}</span>
          <span class="util-note-chip util-note-chip--formula">操業度＝各時間÷理論稼働</span>
          <span class="util-note-chip util-note-chip--formula">差異工時＝上記期間の Σ((実績−計画)/能率)</span>
        </div>
        <el-table
          v-loading="planRateLoading"
          :data="planUtilizationRows"
          border
          stripe
          size="small"
          class="comparison-table operation-rate-table"
          max-height="360"
          empty-text="該当データがありません。集計月・工程を変更すると自動で再読込されます。"
        >
          <el-table-column prop="lineLabel" label="設備" width="80" show-overflow-tooltip />
          <el-table-column prop="scheduleCount" label="指示数" width="72" align="center" />
          <el-table-column width="100" align="right">
            <template #header>
              <span class="util-col-head">理論稼働(H)</span>
            </template>
            <template #default="{ row }">
              <span class="util-num">{{ formatUtilHours(row.availableHours) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="計画数" width="78" align="right">
            <template #default="{ row }">
              <span class="util-num">{{ formatUtilNum(row.plannedQty) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="実績数" width="78" align="right">
            <template #default="{ row }">
              <span class="util-num util-num--actual">{{ formatUtilNum(row.actualQty) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="計画時間(H)" width="102" align="right">
            <template #default="{ row }">
              <span class="util-num">{{ formatUtilHours(row.plannedHours) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="実績時間(H)" width="102" align="right">
            <template #default="{ row }">
              <span class="util-num util-num--actual">{{ formatUtilHours(row.actualHours) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="計画操業度" width="96" align="right">
            <template #default="{ row }">
              <span class="util-num">{{ formatUtilPercent(row.planUtilizationPct) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="実績操業度" width="96" align="right">
            <template #default="{ row }">
              <span class="util-num util-num--actual">{{ formatUtilPercent(row.actualUtilizationPct) }}</span>
            </template>
          </el-table-column>
          <el-table-column width="112" align="right">
            <template #header>
              <span class="util-col-head">操業度差異(H)</span>
            </template>
            <template #default="{ row }">
              <span class="util-num" :class="{ 'util-num--negative': row.diffHours < 0 }">{{
                formatUtilDiffHours(row.diffHours)
              }}</span>
            </template>
          </el-table-column>
          <el-table-column label="差異操業度(%)" width="118" align="right">
            <template #default="{ row }">
              <span class="util-num" :class="{ 'util-num--negative': row.diffUtilizationPct < 0 }">{{
                formatUtilPercent(row.diffUtilizationPct)
              }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>

  <el-dialog
    v-model="adjustmentDialogVisible"
    class="baseline-adjust-dialog"
    destroy-on-close
    align-center
  >
    <template #header>
      <div class="adjustment-header">
        <div>
          <div class="adjustment-title">ベースライン計画修正</div>
          <p class="adjustment-desc">
            基準月の計画値をまとめて再調整。工程で絞り込んで素早く保存できます。
          </p>
        </div>
        <el-tag v-if="adjustmentForm.baselineMonth" size="large" effect="plain">
          {{ dayjs(adjustmentForm.baselineMonth).format('YYYY年MM月') }}
        </el-tag>
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
      </div>
      <div class="toolbar-right">
        <el-button type="primary" :icon="Search" @click="loadAdjustmentRecords">
          データ取得
        </el-button>
        <el-button :icon="Refresh" @click="resetAdjustmentForm">リセット</el-button>
      </div>
    </div>

    <el-table
      v-loading="adjustmentLoading"
      :data="adjustmentItems"
      class="adjustment-table"
      height="480"
      size="small"
      border
      empty-text="該当するデータがありません"
    >
      <el-table-column prop="plan_date" label="日付" width="120" align="center">
        <template #default="{ row }">
          <div class="adjustment-date">{{ formatDate(row.plan_date) }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="process_name" label="工程" width="140">
        <template #default="{ row }">
          <el-tag size="small" type="info" effect="plain">
            {{ row.process_name || '未指定' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="基準計画" min-width="260">
        <template #default="{ row, $index }">
          <div class="plan-editor">
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
      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="{ row }">
          <div class="adjustment-actions">
            <el-button
              type="primary"
              plain
              size="small"
              :loading="row.saving"
              :disabled="row.deleting"
              @click="handleUpdatePlanQuantity(row)"
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
              @click="handleDeleteBaselineRecord(row)"
            >
              削除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <div class="adjustment-footer">
        <el-button type="primary" :icon="DocumentAdd" @click="handleBatchSave">
          変更を一括保存
        </el-button>
        <el-button @click="adjustmentDialogVisible = false">閉じる</el-button>
      </div>
    </template>
  </el-dialog>

  <!-- メッキ・検査：平日一律＋土日任意の基準計画入力 -->
  <el-dialog
    v-model="fixedBaselineDialogVisible"
    title="基準計画の入力"
    width="480px"
    align-center
    destroy-on-close
    class="fixed-baseline-dialog"
  >
    <p class="fixed-baseline-desc">
      工程「<strong>{{ fixedBaselineTargetProcess }}</strong>」は、平日（月〜金）は同じ基準計画を各日に書き込みます。土曜・日曜は通常は書き込みません。必要な場合のみ土日を入力してください。
    </p>
    <el-form label-position="top" class="fixed-baseline-form">
      <el-form-item label="平日（月〜金）の基準計画数（必須）" required>
        <el-input-number
          v-model="fixedBaselineForm.weekdayBaseline"
          :min="1"
          :max="100000000"
          :step="1"
          :controls="true"
          class="fixed-baseline-input"
        />
      </el-form-item>
      <el-form-item label="土曜（任意・未入力の週末は行を作りません）">
        <el-input-number
          v-model="fixedBaselineForm.saturdayBaseline"
          :min="0"
          :max="100000000"
          :step="1"
          :controls="true"
          class="fixed-baseline-input"
        />
      </el-form-item>
      <el-form-item label="日曜（任意）">
        <el-input-number
          v-model="fixedBaselineForm.sundayBaseline"
          :min="0"
          :max="100000000"
          :step="1"
          :controls="true"
          class="fixed-baseline-input"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="fixedBaselineDialogVisible = false">キャンセル</el-button>
      <el-button type="primary" :loading="generating" @click="submitFixedBaselineGenerate">
        生成
      </el-button>
    </template>
  </el-dialog>

  <!-- 工程別PDF発行 进度弹窗（append-to-body で即座に最前面へ描画） -->
  <el-dialog
    v-model="exportProgressVisible"
    title="工程別PDF発行"
    width="420px"
    align-center
    append-to-body
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    class="export-pdf-progress-dialog"
  >
    <div class="export-progress-content">
      <div class="export-progress-icon-wrap">
        <el-icon class="export-progress-icon"><Download /></el-icon>
      </div>
      <p class="export-progress-title">PDFを生成・保存しています</p>
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
import { reactive, ref, computed, onMounted, watch, nextTick } from 'vue'
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
  type PlanBaselineRecord,
} from '@/api/planBaseline'
import {
  fetchLines,
  fetchSchedulingGrid,
  type ScheduleGridRow,
  type SchedulingGridResponse,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'
import * as echarts from 'echarts'

const goHelpPage = () => {
  // 新标签页打开：不替换当前页面；同时避免当前 SPA 热更新导致路由表未刷新。
  window.open('/erp/production/plan-baseline/help', '_blank', 'noopener')
}

const today = dayjs().startOf('month').format('YYYY-MM-DD')

const queryForm = reactive({
  baselineMonth: today,
  processName: '',
})

interface PlanBaselineAdjustmentItem extends PlanBaselineRecord {
  tempPlanQuantity: number
  saving?: boolean
  deleting?: boolean
}

const processOptions = [
  { label: '全工程', value: '' },
  { label: '切断', value: '切断' },
  { label: '面取', value: '面取' },
  { label: '成型', value: '成型' },
  { label: 'メッキ', value: 'メッキ' },
  { label: '溶接', value: '溶接' },
  { label: '検査', value: '検査' },
  { label: '外注メッキ', value: '外注メッキ' },
  { label: '外注溶接', value: '外注溶接' },
]

/** 操業度カード：成型計画一覧「設備操業度」と同じ集計月（東京暦 YYYY-MM） */
function formatYmInJapan(d = new Date()): string {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
  })
    .format(d)
    .slice(0, 7)
}

const planRateFilter = reactive({
  baselineMonth: formatYmInJapan(),
  processCd: '' as string,
})
const planRateProcessList = ref<ProcessItem[]>([])
const planRateProcessSelectOptions = computed(() =>
  planRateProcessList.value.map((p) => ({
    label: `${(p.process_cd || '').trim()} — ${(p.process_name || '').trim()}`,
    value: (p.process_cd || '').trim(),
  })),
)
const planRateLoading = ref(false)

type GanttListRow = ScheduleGridRow & {
  lineLabel: string
  line_id: number
  product_cd?: string | null
}

interface LineUtilizationRow {
  lineId: number
  lineLabel: string
  scheduleCount: number
  availableHours: number
  plannedQty: number
  actualQty: number
  plannedHours: number
  actualHours: number
  diffQty: number
  diffHours: number
  diffUtilizationPct: number
  planUtilizationPct: number
  actualUtilizationPct: number
}

const planUtilMonthDates = ref<string[]>([])
const planUtilMonthRows = ref<GanttListRow[]>([])
const planUtilLineCalendarMap = ref<Record<number, Record<string, number>>>({})
const planUtilLineDefaultHoursMap = ref<Record<number, number>>({})

const utilizationMonthLabelJp = computed(() => {
  const ym = (planRateFilter.baselineMonth || '').trim()
  const p = ym.match(/^(\d{4})-(\d{2})$/)
  if (!p) return '—'
  return `${Number(p[1])}年${Number(p[2])}月`
})

const planUtilizationMonthFullDates = computed(() =>
  [...planUtilMonthDates.value].sort((a, b) => a.localeCompare(b)),
)

function lineLastActualDayInMonth(monthDates: string[], rows: GanttListRow[]): Map<number, string | null> {
  const lastBy = new Map<number, string | null>()
  const lineIds = new Set(rows.map((r) => r.line_id))
  for (const lid of lineIds) lastBy.set(lid, null)
  for (const d of monthDates) {
    const daySum = new Map<number, number>()
    for (const row of rows) {
      const lid = row.line_id
      daySum.set(lid, (daySum.get(lid) ?? 0) + Number(row.actual_daily?.[d] ?? 0))
    }
    for (const [lid, v] of daySum) {
      if (v > 0) lastBy.set(lid, d)
    }
  }
  return lastBy
}

const planUtilizationRows = computed<LineUtilizationRow[]>(() => {
  const monthDates = planUtilizationMonthFullDates.value
  if (monthDates.length === 0) return []

  const rows = planUtilMonthRows.value
  const lastActualByLine = lineLastActualDayInMonth(monthDates, rows)

  const map = new Map<number, LineUtilizationRow>()
  for (const row of rows) {
    const lineId = row.line_id
    const plannedQty = monthDates.reduce((sum, d) => sum + Number(row.daily?.[d] ?? 0), 0)
    const actualQty = monthDates.reduce((sum, d) => sum + Number(row.actual_daily?.[d] ?? 0), 0)
    const rate = Number(row.efficiency_rate ?? 0)
    const plannedHours = rate > 0 ? plannedQty / rate : 0
    const actualHours = rate > 0 ? actualQty / rate : 0
    const endDay = lastActualByLine.get(lineId)
    const diffDates =
      endDay == null || endDay === '' ? ([] as string[]) : monthDates.filter((d) => d <= endDay)
    const diffQtyRow = diffDates.reduce((sum, d) => {
      const p = Number(row.daily?.[d] ?? 0)
      const a = Number(row.actual_daily?.[d] ?? 0)
      return sum + (a - p)
    }, 0)
    const diffHoursRow = rate > 0 ? diffQtyRow / rate : 0
    const item = map.get(lineId) ?? {
      lineId,
      lineLabel: row.lineLabel || `ID ${lineId}`,
      scheduleCount: 0,
      availableHours: 0,
      plannedQty: 0,
      actualQty: 0,
      plannedHours: 0,
      actualHours: 0,
      diffQty: 0,
      diffHours: 0,
      diffUtilizationPct: 0,
      planUtilizationPct: 0,
      actualUtilizationPct: 0,
    }
    item.scheduleCount += 1
    item.plannedQty += plannedQty
    item.actualQty += actualQty
    item.plannedHours += plannedHours
    item.actualHours += actualHours
    item.diffQty += diffQtyRow
    item.diffHours += diffHoursRow
    map.set(lineId, item)
  }
  const result = Array.from(map.values())
  for (const r of result) {
    const calMap = planUtilLineCalendarMap.value[r.lineId] || {}
    const fallback = Number(planUtilLineDefaultHoursMap.value[r.lineId] ?? 0)
    const avail = monthDates.reduce((sum, d) => {
      const h = Number(calMap[d] ?? fallback)
      return sum + (Number.isFinite(h) ? h : 0)
    }, 0)
    r.availableHours = avail
    r.planUtilizationPct = avail > 0 ? (r.plannedHours / avail) * 100 : 0
    r.actualUtilizationPct = avail > 0 ? (r.actualHours / avail) * 100 : 0
    r.diffUtilizationPct = avail > 0 ? (r.diffHours / avail) * 100 : 0
  }
  result.sort((a, b) => a.lineLabel.localeCompare(b.lineLabel, 'ja'))
  return result
})

const generating = ref(false)
const deleting = ref(false)
const tableLoading = ref(false)
const exportPdfLoading = ref(false)
const exportProgressVisible = ref(false)
const exportProgressPercent = ref(0)
const exportProgressCurrent = ref('')
const comparisonResult = ref<PlanBaselineComparisonResult | null>(null)
const comparisonItems = ref<PlanBaselineComparisonItem[]>([])
const activeTab = ref('all')

const adjustmentDialogVisible = ref(false)
const adjustmentLoading = ref(false)
const adjustmentItems = ref<PlanBaselineAdjustmentItem[]>([])
const planInputRefs = ref<(HTMLInputElement | null)[]>([])
const adjustmentForm = reactive({
  baselineMonth: queryForm.baselineMonth,
  processName: '',
})

/** メッキ・検査は平日一律＋土日任意の手入力でベースライン生成 */
const FIXED_BASELINE_PROCESS_NAMES = new Set(['メッキ', '検査'])
const fixedBaselineDialogVisible = ref(false)
const fixedBaselineTargetProcess = ref('')
const fixedBaselineForm = reactive({
  weekdayBaseline: null as number | null,
  saturdayBaseline: null as number | null,
  sundayBaseline: null as number | null,
})

const resetFixedBaselineForm = () => {
  fixedBaselineForm.weekdayBaseline = null
  fixedBaselineForm.saturdayBaseline = null
  fixedBaselineForm.sundayBaseline = null
}

/** ベースライン比較タブ・報告書PDFの工程表示順 */
const BASELINE_COMPARISON_PROCESS_ORDER = [
  '切断',
  '面取',
  '成型',
  'メッキ',
  '溶接',
  '検査',
  '外注メッキ',
  '外注溶接',
] as const

/** 比較一覧タブに出さない工程名 */
const BASELINE_COMPARISON_EXCLUDED_PROCESS_NAMES = new Set([
  '溶接前検査',
  '外注検査前',
  '外注支給前',
  '外注支給前工程',
])

function baselineComparisonProcessOrderIndex(name: string): number {
  const i = (BASELINE_COMPARISON_PROCESS_ORDER as readonly string[]).indexOf(name)
  return i >= 0 ? i : 1000
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
      count: sortedItems.length,
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

// データが更新されたら最初のタブをアクティブに
const updateActiveTab = () => {
  if (processTabs.value.length > 0) {
    const currentTabExists = processTabs.value.find((t) => t.name === activeTab.value)
    if (!currentTabExists) {
      activeTab.value = processTabs.value[0].name
    }
  }
}

const totalItemsCount = computed(() => {
  return comparisonItems.value.length
})

const processTotals = computed(() => {
  const totals = new Map<
    string,
    {
      currentPlan: number
      planDiff: number
      currentActual: number
      actualDiff: number
    }
  >()
  type TabTotals = { currentPlan: number; planDiff: number; currentActual: number; actualDiff: number }
  const initial: TabTotals = { currentPlan: 0, planDiff: 0, currentActual: 0, actualDiff: 0 }
  processTabs.value.forEach((tab) => {
    const aggregate = tab.items.reduce<TabTotals>(
      (acc, item) => {
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

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD')
}

const summaryCards = computed(() => {
  const summary = comparisonResult.value?.summary

  if (!summary) {
    return [
      { label: '基準計画合計', value: '-', isNegative: false, description: 'ベースライン計画合計' },
      { label: '現行計画合計', value: '-', isNegative: false, description: '最新計画合計' },
      {
        label: '計画差異',
        value: '-',
        isNegative: false,
        description: '現行計画 - ベースライン計画',
      },
      {
        label: '現行実績合計',
        value: '-',
        isNegative: false,
        description: '最新実績合計',
      },
      {
        label: '計画対実績差',
        value: '-',
        isNegative: false,
        description: 'ベースライン計画 - 現行実績',
      },
      {
        label: '計画達成率',
        value: '-',
        isNegative: false,
        description: '現行実績 ÷ 現行計画',
      },
      {
        label: '達成率差異',
        value: '-',
        isNegative: false,
        description: '計画対実績差 ÷ 基準計画合計',
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
    },
    {
      label: '現行計画合計',
      value: formatNumber(summary.currentPlanTotal),
      isNegative: currentPlanTotal < 0,
      description: '最新計画合計',
    },
    {
      label: '計画差異',
      value: formatNumber(summary.planDifference),
      isNegative: planDifference < 0,
      description: '現行計画 - ベースライン計画',
    },
    {
      label: '現行実績合計',
      value: summary.currentActualTotal === null ? '-' : formatNumber(summary.currentActualTotal),
      isNegative: false,
      description: '最新実績合計',
    },
    {
      label: '計画対実績差',
      value: summary.actualDifference == null ? '-' : formatNumber(summary.actualDifference),
      isNegative: actualDifference !== 0 && actualDifference < 0,
      description: 'ベースライン計画 - 現行実績',
    },
    {
      label: '計画達成率',
      value: planAchievement === null ? '-' : `${planAchievement.toFixed(1)}%`,
      isNegative: planAchievement !== null && planAchievement < 100,
      description: '現行実績 ÷ 現行計画',
    },
    {
      label: '達成率差異',
      value: achievementDifference === null ? '-' : `${achievementDifference.toFixed(2)}%`,
      isNegative: achievementDifference !== null && achievementDifference < 0,
      description: '計画対実績差 ÷ 基準計画合計',
    },
  ]
})

const formatNumber = (value: number | string | null | undefined) => {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toLocaleString('ja-JP')
}

function formatUtilNum(v: number | null | undefined): string {
  return Number(v ?? 0).toLocaleString()
}

function formatUtilHours(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? n.toFixed(1) : '0.0'
}

function formatUtilDiffHours(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? n.toFixed(0) : '0'
}

function formatUtilPercent(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return '0.0%'
  return `${n.toFixed(1)}%`
}

function monthRangeFromYm(ym: string): [string, string] | null {
  const m = ym.trim().match(/^(\d{4})-(\d{2})$/)
  if (!m) return null
  const y = Number(m[1])
  const mo = Number(m[2])
  if (!Number.isFinite(y) || mo < 1 || mo > 12) return null
  const sd = `${y}-${String(mo).padStart(2, '0')}-01`
  const last = new Date(y, mo, 0).getDate()
  const ed = `${y}-${String(mo).padStart(2, '0')}-${String(last).padStart(2, '0')}`
  return [sd, ed]
}

function compareByLineThenOrder(a: GanttListRow, b: GanttListRow): number {
  const lineCmp = (a.lineLabel || '').localeCompare(b.lineLabel || '', 'ja')
  if (lineCmp !== 0) return lineCmp
  const oa = a.order_no ?? 1_000_000 + a.id
  const ob = b.order_no ?? 1_000_000 + b.id
  if (oa !== ob) return oa - ob
  return a.id - b.id
}

function flattenGridToRows(grid: SchedulingGridResponse, lineNameById: Map<number, string>): GanttListRow[] {
  const flat: GanttListRow[] = []
  for (const block of grid.blocks || []) {
    const label =
      lineNameById.get(block.line_id) ||
      String((block as { line_name?: string }).line_name || '').trim() ||
      block.line_code ||
      `ID ${block.line_id}`
    for (const r of block.rows || []) {
      flat.push({ ...r, lineLabel: label, line_id: block.line_id })
    }
  }
  return flat
}

function selectedPlanRateProcessLabel(): string {
  const cd = (planRateFilter.processCd || '').trim()
  if (!cd) return '—'
  const p = planRateProcessList.value.find((x) => (x.process_cd || '').trim() === cd)
  const nm = (p?.process_name || '').trim()
  return nm ? `${cd} — ${nm}` : cd
}

async function loadPlanProcessOptions() {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const list = res.list ?? res.data?.list ?? []
    const raw = Array.isArray(list) ? list : []
    let filtered = raw.filter((p) => {
      const name = (p.process_name || '').trim()
      const cd = (p.process_cd || '').trim()
      if (name === '成型' || name === '溶接') return true
      if (cd === 'KT04' || cd === 'KT07') return true
      return false
    })
    if (filtered.length === 0) {
      filtered = raw.filter((p) => {
        const cd = (p.process_cd || '').trim()
        return cd === 'KT04' || cd === 'KT07'
      })
    }
    planRateProcessList.value = filtered
    const hasKt04 = planRateProcessList.value.some((p) => (p.process_cd || '').trim() === 'KT04')
    if (hasKt04) {
      planRateFilter.processCd = 'KT04'
    } else if (planRateProcessList.value.length === 1) {
      planRateFilter.processCd = (planRateProcessList.value[0].process_cd || '').trim()
    }
  } catch {
    planRateProcessList.value = []
    ElMessage.error('工程一覧の取得に失敗しました')
  }
}

async function loadPlanUtilizationGrid() {
  const pc = (planRateFilter.processCd || '').trim()
  if (!pc) {
    planUtilMonthDates.value = []
    planUtilMonthRows.value = []
    planUtilLineCalendarMap.value = {}
    planUtilLineDefaultHoursMap.value = {}
    return
  }
  const ym = (planRateFilter.baselineMonth || '').trim()
  const range = monthRangeFromYm(ym)
  if (!range) {
    planUtilMonthDates.value = []
    planUtilMonthRows.value = []
    planUtilLineCalendarMap.value = {}
    planUtilLineDefaultHoursMap.value = {}
    return
  }
  const [sd, ed] = range
  planRateLoading.value = true
  try {
    const [grid, lines] = await Promise.all([
      fetchSchedulingGrid(sd, ed, undefined, pc),
      fetchLines(pc),
    ])
    planUtilMonthDates.value = Array.isArray(grid.dates) ? grid.dates : []
    const lineNameById = new Map<number, string>()
    for (const line of lines || []) {
      const name = String(line.line_name || '').trim()
      const code = String(line.line_code || '').trim()
      lineNameById.set(line.id, name || code || `ID ${line.id}`)
    }
    const flat = flattenGridToRows(grid, lineNameById)
    flat.sort(compareByLineThenOrder)
    planUtilMonthRows.value = flat
    const calendarMap: Record<number, Record<string, number>> = {}
    const defaultMap: Record<number, number> = {}
    for (const block of grid.blocks || []) {
      calendarMap[block.line_id] = block.calendar || {}
      defaultMap[block.line_id] = Number(block.default_work_hours ?? 0)
    }
    planUtilLineCalendarMap.value = calendarMap
    planUtilLineDefaultHoursMap.value = defaultMap
  } catch {
    planUtilMonthDates.value = []
    planUtilMonthRows.value = []
    planUtilLineCalendarMap.value = {}
    planUtilLineDefaultHoursMap.value = {}
    ElMessage.error('操業度データの取得に失敗しました')
  } finally {
    planRateLoading.value = false
  }
}

/** 工程別PDFの「操業度」章用：成型・溶接それぞれの設備操業度を HTML 化するための行取得 */
async function fetchUtilizationRowsForYmProcess(
  ym: string,
  processCd: string,
): Promise<LineUtilizationRow[]> {
  const pc = (processCd || '').trim()
  if (!pc) return []
  const range = monthRangeFromYm(ym.trim())
  if (!range) return []
  const [sd, ed] = range
  const [grid, lines] = await Promise.all([
    fetchSchedulingGrid(sd, ed, undefined, pc),
    fetchLines(pc),
  ])
  const dates = Array.isArray(grid.dates) ? [...grid.dates].sort((a, b) => a.localeCompare(b)) : []
  if (dates.length === 0) return []
  const lineNameById = new Map<number, string>()
  for (const line of lines || []) {
    const name = String(line.line_name || '').trim()
    const code = String(line.line_code || '').trim()
    lineNameById.set(line.id, name || code || `ID ${line.id}`)
  }
  const flat = flattenGridToRows(grid, lineNameById)
  const calendarMap: Record<number, Record<string, number>> = {}
  const defaultMap: Record<number, number> = {}
  for (const block of grid.blocks || []) {
    calendarMap[block.line_id] = block.calendar || {}
    defaultMap[block.line_id] = Number(block.default_work_hours ?? 0)
  }
  const lastActualByLine = lineLastActualDayInMonth(dates, flat)
  const map = new Map<number, LineUtilizationRow>()
  for (const row of flat) {
    const lineId = row.line_id
    const plannedQty = dates.reduce((sum, d) => sum + Number(row.daily?.[d] ?? 0), 0)
    const actualQty = dates.reduce((sum, d) => sum + Number(row.actual_daily?.[d] ?? 0), 0)
    const rate = Number(row.efficiency_rate ?? 0)
    const plannedHours = rate > 0 ? plannedQty / rate : 0
    const actualHours = rate > 0 ? actualQty / rate : 0
    const endDay = lastActualByLine.get(lineId)
    const diffDates =
      endDay == null || endDay === '' ? ([] as string[]) : dates.filter((d) => d <= endDay)
    const diffQtyRow = diffDates.reduce((sum, d) => {
      const p = Number(row.daily?.[d] ?? 0)
      const a = Number(row.actual_daily?.[d] ?? 0)
      return sum + (a - p)
    }, 0)
    const diffHoursRow = rate > 0 ? diffQtyRow / rate : 0
    const item = map.get(lineId) ?? {
      lineId,
      lineLabel: row.lineLabel || `ID ${lineId}`,
      scheduleCount: 0,
      availableHours: 0,
      plannedQty: 0,
      actualQty: 0,
      plannedHours: 0,
      actualHours: 0,
      diffQty: 0,
      diffHours: 0,
      diffUtilizationPct: 0,
      planUtilizationPct: 0,
      actualUtilizationPct: 0,
    }
    item.scheduleCount += 1
    item.plannedQty += plannedQty
    item.actualQty += actualQty
    item.plannedHours += plannedHours
    item.actualHours += actualHours
    item.diffQty += diffQtyRow
    item.diffHours += diffHoursRow
    map.set(lineId, item)
  }
  const result = Array.from(map.values())
  for (const r of result) {
    const calMap = calendarMap[r.lineId] || {}
    const fallback = Number(defaultMap[r.lineId] ?? 0)
    const avail = dates.reduce((sum, d) => {
      const h = Number(calMap[d] ?? fallback)
      return sum + (Number.isFinite(h) ? h : 0)
    }, 0)
    r.availableHours = avail
    r.planUtilizationPct = avail > 0 ? (r.plannedHours / avail) * 100 : 0
    r.actualUtilizationPct = avail > 0 ? (r.actualHours / avail) * 100 : 0
    r.diffUtilizationPct = avail > 0 ? (r.diffHours / avail) * 100 : 0
  }
  result.sort((a, b) => a.lineLabel.localeCompare(b.lineLabel, 'ja'))
  return result
}

const openAdjustmentDialog = () => {
  adjustmentForm.baselineMonth = queryForm.baselineMonth
  adjustmentForm.processName = queryForm.processName || ''
  adjustmentItems.value = []
  planInputRefs.value = []
  adjustmentDialogVisible.value = true
  nextTick(() => {
    loadAdjustmentRecords()
  })
}

const resetAdjustmentForm = () => {
  adjustmentForm.baselineMonth = queryForm.baselineMonth
  adjustmentForm.processName = ''
  adjustmentItems.value = []
  planInputRefs.value = []
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
    }))
    if (records.length === 0) {
      ElMessage.info('該当データがありません')
    }
    planInputRefs.value = []
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースラインデータの取得に失敗しました')
  } finally {
    adjustmentLoading.value = false
  }
}

const handleUpdatePlanQuantity = async (row: PlanBaselineAdjustmentItem) => {
  const planQuantity = Number(row.tempPlanQuantity)
  if (Number.isNaN(planQuantity)) {
    ElMessage.warning('数値を入力してください')
    return
  }
  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
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
    ElMessage.success('修正しました')
  } catch (error: any) {
    ElMessage.error(error?.message || '修正に失敗しました')
  } finally {
    row.saving = false
  }
}

const handleDeleteBaselineRecord = async (row: PlanBaselineAdjustmentItem) => {
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
    targetIndex = Math.min(index + 1, adjustmentItems.value.length - 1)
  } else if (key === 'ArrowUp') {
    targetIndex = Math.max(index - 1, 0)
  } else if (key === 'ArrowRight') {
    targetIndex = Math.min(index + 1, adjustmentItems.value.length - 1)
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

const loadComparison = async () => {
  tableLoading.value = true
  try {
    const data = await fetchPlanBaselineComparison({
      baselineMonth: queryForm.baselineMonth,
      processName: queryForm.processName || undefined,
    })
    comparisonResult.value = data
    comparisonItems.value = data?.items ?? []
  } catch (error: any) {
    ElMessage.error(error?.message || '比較データの取得に失敗しました')
  } finally {
    tableLoading.value = false
  }
}

const runGeneratePlanBaseline = async (payload: Parameters<typeof generatePlanBaseline>[0]) => {
  generating.value = true
  try {
    await generatePlanBaseline(payload)
    ElMessage.success('ベースラインを生成しました')
    await loadComparison()
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースライン生成に失敗しました')
  } finally {
    generating.value = false
  }
}

const submitFixedBaselineGenerate = async () => {
  const w = fixedBaselineForm.weekdayBaseline
  if (w == null || Number(w) <= 0) {
    ElMessage.warning('平日の基準計画数を入力してください（1以上の数）')
    return
  }
  const sat = fixedBaselineForm.saturdayBaseline
  const sun = fixedBaselineForm.sundayBaseline
  const body: Parameters<typeof generatePlanBaseline>[0] = {
    baselineMonth: queryForm.baselineMonth,
    processName: fixedBaselineTargetProcess.value || undefined,
    weekdayBaseline: Number(w),
  }
  if (sat != null && !Number.isNaN(Number(sat))) {
    body.saturdayBaseline = Number(sat)
  }
  if (sun != null && !Number.isNaN(Number(sun))) {
    body.sundayBaseline = Number(sun)
  }
  fixedBaselineDialogVisible.value = false
  await runGeneratePlanBaseline(body)
}

const handleGenerate = async () => {
  if (!queryForm.baselineMonth) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  try {
    await ElMessageBox.confirm(
      '対象月のベースラインを再生成します。既存データは上書きされますがよろしいですか？',
      '確認',
      {
        type: 'warning',
        confirmButtonText: '生成',
        cancelButtonText: 'キャンセル',
      },
    )
  } catch {
    return
  }

  if (FIXED_BASELINE_PROCESS_NAMES.has(queryForm.processName)) {
    fixedBaselineTargetProcess.value = queryForm.processName
    resetFixedBaselineForm()
    fixedBaselineDialogVisible.value = true
    return
  }

  await runGeneratePlanBaseline({
    baselineMonth: queryForm.baselineMonth,
    processName: queryForm.processName || undefined,
  })
}

const handleDeleteBaseline = async () => {
  if (!queryForm.baselineMonth) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  const confirmMessage = queryForm.processName
    ? `基準月「${dayjs(queryForm.baselineMonth).format('YYYY年MM月')}」の「${queryForm.processName}」ベースラインを削除します。よろしいですか？`
    : `基準月「${dayjs(queryForm.baselineMonth).format('YYYY年MM月')}」の全工程ベースラインを削除します。よろしいですか？`
  try {
    await ElMessageBox.confirm(confirmMessage, '確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
  } catch {
    return
  }

  deleting.value = true
  try {
    await deletePlanBaseline({
      baselineMonth: queryForm.baselineMonth,
      processName: queryForm.processName || undefined,
    })
    ElMessage.success('ベースラインを削除しました')
    await loadComparison()
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
const PDF_TABLE_CANVAS_SCALE = 1.5
/** チャート出力の pixelRatio 上限 */
const PDF_CHART_PIXEL_RATIO = 1.5

/** 工程別の比較表をHTMLで描画してキャプチャし、PDFのBlobで返す（日本語フォント対応） */
async function buildProcessPdf(
  processName: string,
  baselineMonth: string,
  items: PlanBaselineComparisonItem[],
  totals: { currentPlan: number; planDiff: number; currentActual: number; actualDiff: number } | undefined,
): Promise<Blob> {
  const monthLabel = dayjs(baselineMonth).format('YYYY年MM月')
  const headers = ['日付', '基準計画', '現行計画', '計画差異', '現行実績合計', '計画対実績差']

  const baselinePlanTotal = items.reduce((sum, row) => sum + Number(row.baseline_plan ?? 0), 0)
  // 稼働日数＝当該工程・当月比較表のデータ行数（工程ごとに行数が異なる）
  const workingDays = items.length
  const avgDailyBaseline =
    workingDays > 0 ? Math.round(baselinePlanTotal / workingDays) : 0
  const statsText =
    workingDays > 0
      ? `稼働日数: ${workingDays}日（${processName}・当月データ件数）　平均日当たり基準計画: ${formatNumber(avgDailyBaseline)}`
      : ''

  const numCell = (value: number | string | null | undefined) => {
    const n = value != null && value !== '' ? Number(value) : NaN
    const red = !Number.isNaN(n) && n < 0 ? ' color: #c62828;' : ''
    return `style="border: 1px solid #bdbdbd; padding: 5px 7px; text-align: right;${red}"`
  }

  const rowHtmlParts = items.map((row, idx) => {
    const rowBg = idx % 2 === 0 ? '#fafafa' : '#fff'
    return `
      <tr style="background: ${rowBg};">
        <td style="border: 1px solid #bdbdbd; padding: 5px 7px;">${formatDate(row.plan_date ?? '') || '-'}</td>
        <td ${numCell(row.baseline_plan)}>${formatNumber(row.baseline_plan) as string}</td>
        <td ${numCell(row.current_plan)}>${formatNumber(row.current_plan) as string}</td>
        <td ${numCell(row.plan_diff)}>${formatNumber(row.plan_diff) as string}</td>
        <td ${numCell(row.current_actual)}>${row.current_actual != null ? (formatNumber(row.current_actual) as string) : '-'}</td>
        <td ${numCell(row.actual_diff)}>${row.actual_diff != null ? (formatNumber(row.actual_diff) as string) : '-'}</td>
      </tr>
    `
  })
  if (totals && items.length > 0) {
    rowHtmlParts.push(`
      <tr style="background: #eceff1; font-weight: bold; border-top: 2px solid #78909c;">
        <td style="border: 1px solid #bdbdbd; padding: 5px 7px;">合計</td>
        <td ${numCell(baselinePlanTotal)}>${formatNumber(baselinePlanTotal)}</td>
        <td ${numCell(totals.currentPlan)}>${formatNumber(totals.currentPlan) as string}</td>
        <td ${numCell(totals.planDiff)}>${formatNumber(totals.planDiff) as string}</td>
        <td ${numCell(totals.currentActual)}>${formatNumber(totals.currentActual) as string}</td>
        <td ${numCell(totals.actualDiff)}>${formatNumber(totals.actualDiff) as string}</td>
      </tr>
    `)
  }
  const rowsHtml = rowHtmlParts.join('')

  const html = `
    <div class="baseline-pdf-root" style="
      font-family: 'Meiryo', 'Hiragino Sans', 'Yu Gothic', sans-serif;
      padding: 20px; background: #fff; width: 650px; box-sizing: border-box;">
      <div class="pdf-title" style="font-size: 17px; font-weight: bold; color: #1565c0; margin-bottom: 6px; padding-bottom: 8px; border-bottom: 2px solid #e3f2fd;">ベースライン計画 - 現行実績 - ${processName}</div>
      <div class="pdf-month-row" style="font-size: 12px; color: #546e7a; margin-bottom: 14px; display: flex; justify-content: space-between;">
        <span>${monthLabel}</span>
        ${statsText ? `<span>${statsText}</span>` : ''}
      </div>
      <table style="width: 100%; border-collapse: collapse; font-size: 12px; line-height: 1.4; border: 1px solid #90a4ae; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
        <thead>
          <tr style="background: linear-gradient(180deg, #37474f 0%, #455a64 100%); color: #fff; font-weight: bold;">
            <th style="border: 1px solid #546e7a; padding: 6px 8px; text-align: left;">${headers[0]}</th>
            ${headers.slice(1).map((h) => `<th style="border: 1px solid #546e7a; padding: 6px 8px; text-align: right;">${h}</th>`).join('')}
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>
  `

  const wrap = document.createElement('div')
  wrap.style.cssText = 'position: fixed; left: -9999px; top: 0; z-index: -1;'
  wrap.innerHTML = html
  document.body.appendChild(wrap)

  const el = wrap.querySelector('.baseline-pdf-root') as HTMLElement
  if (!el) {
    wrap.remove()
    throw new Error('PDF用要素の作成に失敗しました')
  }

  let tableCanvas: HTMLCanvasElement | undefined
  try {
    tableCanvas = await html2canvas(el, {
      scale: PDF_TABLE_CANVAS_SCALE,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
    })
  } finally {
    wrap.remove()
  }
  if (!tableCanvas) {
    throw new Error('PDF表のキャプチャに失敗しました')
  }

  const canvas = tableCanvas
  const imgW = canvas.width
  const imgH = canvas.height
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pageW = 210
  const pageH = 297
  const margin = 10
  const contentW = pageW - margin * 2
  const contentH = pageH - margin * 2

  const scale = contentW / imgW
  const scaledH = imgH * scale

  if (scaledH <= contentH) {
    doc.addImage(canvas.toDataURL('image/png'), 'PNG', margin, margin, contentW, scaledH)
  } else {
    let drawn = 0
    let pageIndex = 0
    while (drawn < imgH) {
      if (pageIndex > 0) doc.addPage([pageW, pageH], 'p')
      const sliceH = Math.min(contentH / scale, imgH - drawn)
      const sy = drawn
      const sourceCanvas = document.createElement('canvas')
      sourceCanvas.width = imgW
      sourceCanvas.height = Math.ceil(sliceH)
      const ctx = sourceCanvas.getContext('2d')
      if (ctx) {
        ctx.drawImage(canvas, 0, sy, imgW, sliceH, 0, 0, imgW, sliceH)
        doc.addImage(sourceCanvas.toDataURL('image/png'), 'PNG', margin, margin, contentW, sliceH * scale)
      }
      drawn += sliceH
      pageIndex++
    }
  }

  // --- 2ページ目: 日別折れ線 + 差異棒グラフ（ECharts で描画・画像取得） ---
  if (items.length > 0) {
    doc.addPage([pageW, pageH], 'p')

    const labels = items.map((row) => formatDate(row.plan_date ?? '') || '')
    const baselineSeries = items.map((row) => Number(row.baseline_plan ?? 0))
    const currentPlanSeries = items.map((row) => Number(row.current_plan ?? 0))
    const currentActualSeries = items.map((row) => Number(row.current_actual ?? 0))
    const planDiffSeries = items.map((row) => Number(row.plan_diff ?? 0))
    const diffColors = planDiffSeries.map((v) => (v >= 0 ? '#4caf50' : '#e53935'))

    const chartDiv = document.createElement('div')
    chartDiv.style.cssText =
      'position: fixed; left: -9999px; top: 0; width: 900px; height: 520px; z-index: -1;'
    document.body.appendChild(chartDiv)

    let chartImg = ''
    let chartInstance: echarts.ECharts | undefined
    try {
      chartInstance = echarts.init(chartDiv, null, {
        renderer: 'canvas',
        devicePixelRatio: Math.min(window.devicePixelRatio || 1, PDF_CHART_PIXEL_RATIO),
      })
      chartInstance.setOption({
        animation: false,
        title: {
          text: `日別計画・実績推移（${monthLabel}／${processName}）`,
          left: 'center',
          textStyle: { fontSize: 14 },
        },
        // PDF 用の静的画像のためツールチップはオフ（描画コスト削減）
        tooltip: { show: false },
        legend: {
          data: ['基準計画', '現行計画', '現行実績合計', '計画差異'],
          top: 28,
        },
        grid: { left: 48, right: 48, top: 56, bottom: 40 },
        xAxis: {
          type: 'category',
          data: labels,
          axisLabel: { rotate: 0, maxInterval: 0 },
        },
        yAxis: [
          {
            type: 'value',
            name: '数量',
            position: 'left',
            axisLabel: { formatter: '{value}' },
            min: 0,
            splitLine: { show: true, lineStyle: { type: 'dashed', opacity: 0.3 } },
          },
          {
            type: 'value',
            name: '計画差異',
            position: 'right',
            axisLabel: { formatter: '{value}' },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            name: '計画差異',
            type: 'bar',
            yAxisIndex: 1,
            z: 1,
            data: planDiffSeries.map((v, i) => ({ value: v, itemStyle: { color: diffColors[i] } })),
            barMaxWidth: 24,
          },
          {
            name: '基準計画',
            type: 'line',
            yAxisIndex: 0,
            z: 2,
            data: baselineSeries,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { width: 2.5 },
            itemStyle: { color: '#1976d2' },
            emphasis: { scale: true, itemStyle: { borderColor: '#fff', borderWidth: 2 } },
          },
          {
            name: '現行計画',
            type: 'line',
            yAxisIndex: 0,
            z: 2,
            data: currentPlanSeries,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { width: 2.5 },
            itemStyle: { color: '#fb8c00' },
            emphasis: { scale: true, itemStyle: { borderColor: '#fff', borderWidth: 2 } },
          },
          {
            name: '現行実績合計',
            type: 'line',
            yAxisIndex: 0,
            z: 2,
            data: currentActualSeries,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { width: 2.5 },
            itemStyle: { color: '#388e3c' },
            emphasis: { scale: true, itemStyle: { borderColor: '#fff', borderWidth: 2 } },
          },
        ],
      })

      await nextFrames(2)
      chartImg = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: PDF_CHART_PIXEL_RATIO,
        backgroundColor: '#fff',
      })
    } finally {
      chartInstance?.dispose()
      chartDiv.remove()
    }

    if (chartImg) {
      const chartWmm = contentW
      const chartHmm = (520 / 900) * chartWmm
      const chartY = margin + (contentH - chartHmm) / 2
      doc.addImage(chartImg, 'PNG', margin, chartY, chartWmm, chartHmm)
    }
  }

  return doc.output('blob')
}

/** 操業度を工程ごとに PDF ページ分け（成型計画一覧の設備操業度と同一集計。データなしは null） */
async function buildOperationRateCombinedPdf(baselineMonth: string): Promise<Blob | null> {
  const ym = dayjs(baselineMonth).format('YYYY-MM')
  const monthLabel = dayjs(`${ym}-01`).format('YYYY年MM月')

  const esc = (s: string) =>
    String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')

  const master = planRateProcessList.value
  const forPdf =
    master.filter((p) => {
      const name = (p.process_name || '').trim()
      const cd = (p.process_cd || '').trim()
      return name === '成型' || name === '溶接' || cd === 'KT04' || cd === 'KT07'
    }).length > 0
      ? master.filter((p) => {
          const name = (p.process_name || '').trim()
          const cd = (p.process_cd || '').trim()
          return name === '成型' || name === '溶接' || cd === 'KT04' || cd === 'KT07'
        })
      : []
  const rawPairs =
    forPdf.length > 0
      ? forPdf.map((p) => ({
          cd: (p.process_cd || '').trim(),
          name: (p.process_name || '').trim() || (p.process_cd || '').trim(),
        }))
      : [
          { cd: 'KT04', name: '成型' },
          { cd: 'KT07', name: '溶接' },
        ]
  const seenCd = new Set<string>()
  const processPairs = rawPairs.filter((p) => {
    if (!p.cd || seenCd.has(p.cd)) return false
    seenCd.add(p.cd)
    return true
  })

  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pageW = 210
  const pageH = 297
  const margin = 10
  const contentW = pageW - margin * 2
  const contentH = pageH - margin * 2

  const appendSectionCanvas = (canvas: HTMLCanvasElement, isFirstSection: boolean) => {
    const imgW = canvas.width
    const imgH = canvas.height
    const scale = contentW / imgW
    const scaledH = imgH * scale

    if (scaledH <= contentH) {
      if (!isFirstSection) doc.addPage([pageW, pageH], 'p')
      doc.addImage(canvas.toDataURL('image/png'), 'PNG', margin, margin, contentW, scaledH)
      return
    }
    let drawn = 0
    let sliceIndex = 0
    while (drawn < imgH) {
      if (sliceIndex > 0 || !isFirstSection) {
        doc.addPage([pageW, pageH], 'p')
      }
      const sliceH = Math.min(contentH / scale, imgH - drawn)
      const sy = drawn
      const sourceCanvas = document.createElement('canvas')
      sourceCanvas.width = imgW
      sourceCanvas.height = Math.ceil(sliceH)
      const ctx = sourceCanvas.getContext('2d')
      if (ctx) {
        ctx.drawImage(canvas, 0, sy, imgW, sliceH, 0, 0, imgW, sliceH)
        doc.addImage(sourceCanvas.toDataURL('image/png'), 'PNG', margin, margin, contentW, sliceH * scale)
      }
      drawn += sliceH
      sliceIndex++
    }
  }

  let isFirstSection = true
  let renderedAny = false
  for (const { cd, name } of processPairs) {
    const utilRows = await fetchUtilizationRowsForYmProcess(ym, cd)
    if (!utilRows.length) continue

    const rowParts = utilRows.map((r, idx) => {
      const bg = idx % 2 === 0 ? '#fafafa' : '#fff'
      const dh = r.diffHours < 0 ? 'color:#c62828;font-weight:600;' : ''
      const dp = r.diffUtilizationPct < 0 ? 'color:#c62828;font-weight:600;' : ''
      return `<tr style="background:${bg};font-size:11px;">
        <td style="border:1px solid #bdbdbd;padding:4px 6px;">${esc(r.lineLabel)}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:center;">${esc(String(r.scheduleCount))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilHours(r.availableHours))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilNum(r.plannedQty))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilNum(r.actualQty))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilHours(r.plannedHours))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilHours(r.actualHours))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilPercent(r.planUtilizationPct))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;">${esc(formatUtilPercent(r.actualUtilizationPct))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;${dh}">${esc(formatUtilDiffHours(r.diffHours))}</td>
        <td style="border:1px solid #bdbdbd;padding:4px 6px;text-align:right;${dp}">${esc(formatUtilPercent(r.diffUtilizationPct))}</td>
      </tr>`
    })

    const tableBlock = `
      <div style="margin-bottom:18px;">
        <div style="font-size:14px;font-weight:700;color:#37474f;margin:12px 0 8px;padding:6px 10px;background:#eceff1;border-left:4px solid #1565c0;">工程：${esc(name)}（${esc(cd)}）</div>
        <table style="width:100%;border-collapse:collapse;font-size:11px;border:1px solid #90a4ae;">
          <thead>
            <tr style="background:linear-gradient(180deg,#37474f 0%,#455a64 100%);color:#fff;">
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">設備</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">指示数</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">理論稼働(H)</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">計画数</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">実績数</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">計画時間(H)</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">実績時間(H)</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">計画操業度</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">実績操業度</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">操業度差異(H)</th>
              <th style="border:1px solid #546e7a;padding:5px 6px;text-align:center;">差異操業度(%)</th>
            </tr>
          </thead>
          <tbody>${rowParts.join('')}</tbody>
        </table>
      </div>`

    const html = `
    <div class="operation-rate-pdf-root" style="font-family:'Meiryo','Hiragino Sans','Yu Gothic',sans-serif;padding:16px;background:#fff;width:1000px;box-sizing:border-box;">
      <div style="font-size:17px;font-weight:bold;color:#1565c0;margin-bottom:6px;padding-bottom:8px;border-bottom:2px solid #e3f2fd;">操業度（設備操業度・工程別）</div>
      <div style="font-size:12px;color:#546e7a;margin-bottom:14px;">${esc(monthLabel)}</div>
      ${tableBlock}
    </div>`

    const wrap = document.createElement('div')
    wrap.style.cssText = 'position: fixed; left: -9999px; top: 0; z-index: -1;'
    wrap.innerHTML = html
    document.body.appendChild(wrap)
    const el = wrap.querySelector('.operation-rate-pdf-root') as HTMLElement
    if (!el) {
      wrap.remove()
      throw new Error('操業度PDF用要素の作成に失敗しました')
    }
    let tableCanvas: HTMLCanvasElement | undefined
    try {
      tableCanvas = await html2canvas(el, {
        scale: PDF_TABLE_CANVAS_SCALE,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
      })
    } finally {
      wrap.remove()
    }
    if (!tableCanvas) throw new Error('操業度PDFのキャプチャに失敗しました')

    appendSectionCanvas(tableCanvas, isFirstSection)
    isFirstSection = false
    renderedAny = true
  }

  if (!renderedAny) return null
  return doc.output('blob')
}

const handleExportPdfToFolder = async () => {
  if (!comparisonResult.value?.baselineMonth || pdfExportTargetTabs.value.length === 0) {
    ElMessage.warning(
      '切断・面取・成型・メッキ・溶接・検査・外注メッキ・外注溶接のいずれにも比較データがありません。条件を確認し、先に検索を実行してください。',
    )
    return
  }
  const tabs = pdfExportTargetTabs.value
  const totalSteps = tabs.length + 1
  exportPdfLoading.value = true
  exportProgressVisible.value = true
  exportProgressPercent.value = 0
  exportProgressCurrent.value = '準備中...'
  // DOM をコミットしモーダルを1〜2フレーム描画してから html2canvas 等の重処理へ（クリック直後に進捗が見えるように）
  await nextTick()
  await nextFrames(2)
  try {
    const baselineMonth = comparisonResult.value.baselineMonth
    const totalsSnapshot = new Map(processTotals.value)
    let completed = 0
    const blobs = await runWithConcurrency(tabs, 3, async (tab) => {
      const blob = await buildProcessPdf(
        tab.name,
        baselineMonth,
        tab.items,
        totalsSnapshot.get(tab.name),
      )
      completed++
      exportProgressCurrent.value = `PDF生成 ${completed} / ${totalSteps}（${tab.name}）`
      exportProgressPercent.value = Math.min(85, Math.round((completed / totalSteps) * 85))
      return blob
    })
    const files: { processName: string; blob: Blob }[] = tabs.map((tab, i) => ({
      processName: tab.name,
      blob: blobs[i],
    }))
    exportProgressCurrent.value = `PDF生成 ${tabs.length} / ${totalSteps}（操業度）`
    exportProgressPercent.value = 88
    const operationRateBlob = await buildOperationRateCombinedPdf(baselineMonth)
    if (operationRateBlob) {
      files.push({ processName: '操業度', blob: operationRateBlob })
    }
    exportProgressCurrent.value = 'サーバーに保存しています...'
    exportProgressPercent.value = 95
    const res = await exportPlanBaselinePdfToFolder(baselineMonth, files)
    exportProgressPercent.value = 100
    exportProgressCurrent.value = '完了'
    if (res.success) {
      ElMessage.success(res.message ?? `${res.saved?.length ?? 0}件のPDFを保存しました`)
    } else {
      ElMessage.error(res.message ?? '保存に失敗しました')
      if (res.errors?.length) console.error('export errors', res.errors)
    }
  } catch (error: any) {
    ElMessage.error(error?.message ?? '工程別PDFの保存に失敗しました')
    console.error(error)
  } finally {
    exportPdfLoading.value = false
    setTimeout(() => {
      exportProgressVisible.value = false
      exportProgressPercent.value = 0
      exportProgressCurrent.value = ''
    }, 400)
  }
}

const resetForm = () => {
  queryForm.baselineMonth = today
  queryForm.processName = ''
  loadComparison()
}

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
  void loadPlanProcessOptions()
})

watch([() => planRateFilter.baselineMonth, () => planRateFilter.processCd], () => {
  void loadPlanUtilizationGrid()
})

/** 印刷用 HTML を隠し iframe で開き、ブラウザの印刷ダイアログのみ出す */
function printWithIframeDoc(html: string, iframeTitle: string) {
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

  const monthSource = comparisonResult.value?.baselineMonth || queryForm.baselineMonth
  const monthLabel = monthSource ? dayjs(monthSource).format('YYYY年MM月') : '—'

  const headCells = ['日付', '基準計画', '現行計画', '計画差異', '現行実績合計', '計画対実績差']
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

/** 操業度：現在一覧（設備操業度と同一集計）を印刷 */
function handlePrintOperationRate() {
  const rows = planUtilizationRows.value
  if (rows.length === 0) return

  const escHtml = (s: string) =>
    String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')

  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

  const rowsHtml = rows
    .map((r) => {
      const negHours = r.diffHours < 0 ? 'neg' : ''
      const negPct = r.diffUtilizationPct < 0 ? 'neg' : ''
      return `<tr>
        <td class="left">${escHtml(r.lineLabel)}</td>
        <td class="num">${escHtml(String(r.scheduleCount))}</td>
        <td class="num">${escHtml(formatUtilHours(r.availableHours))}</td>
        <td class="num">${escHtml(formatUtilNum(r.plannedQty))}</td>
        <td class="num">${escHtml(formatUtilNum(r.actualQty))}</td>
        <td class="num">${escHtml(formatUtilHours(r.plannedHours))}</td>
        <td class="num">${escHtml(formatUtilHours(r.actualHours))}</td>
        <td class="num">${escHtml(formatUtilPercent(r.planUtilizationPct))}</td>
        <td class="num">${escHtml(formatUtilPercent(r.actualUtilizationPct))}</td>
        <td class="num ${negHours}">${escHtml(formatUtilDiffHours(r.diffHours))}</td>
        <td class="num ${negPct}">${escHtml(formatUtilPercent(r.diffUtilizationPct))}</td>
      </tr>`
    })
    .join('')

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>設備操業度（月次）</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { margin: 16px; color: #0f172a; font: 12px/1.4 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif; }
    .hd { margin-bottom: 10px; }
    .tt { font-size: 18px; font-weight: 700; }
    .meta { margin-top: 4px; color: #475569; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; }
    th { background: #eff6ff; font-weight: 700; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .neg { color: #dc2626; font-weight: 700; }
    tbody tr:nth-child(odd) { background: #f8fafc; }
    @media print { @page { size: A4 landscape; margin: 10mm; } }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">設備操業度（月次）</div>
    <div class="meta">集計月：<strong>${escHtml(utilizationMonthLabelJp.value)}</strong>（${escHtml(
      planRateFilter.baselineMonth || '—',
    )}）　工程：${escHtml(
      selectedPlanRateProcessLabel(),
    )}　印刷日時：${escHtml(printedAt)}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th class="left">設備</th>
        <th class="num">指示数</th>
        <th class="num">理論稼働(H)</th>
        <th class="num">計画数</th>
        <th class="num">実績数</th>
        <th class="num">計画時間(H)</th>
        <th class="num">実績時間(H)</th>
        <th class="num">計画操業度</th>
        <th class="num">実績操業度</th>
        <th class="num">操業度差異(H)</th>
        <th class="num">差異操業度(%)</th>
      </tr>
    </thead>
    <tbody>${rowsHtml}</tbody>
  </table>
</body>
</html>`

  printWithIframeDoc(html, '操業度印刷')
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
  border-radius: 50%;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: export-pulse 1.5s ease-in-out infinite;
}
.export-progress-icon {
  font-size: 28px;
  color: #1976d2;
}
.export-progress-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: #37474f;
}
.export-progress-current {
  margin: 0 0 20px;
  font-size: 13px;
  color: #546e7a;
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
  background-color: #e8eaf6;
}
:deep(.export-progress-bar .el-progress-bar__inner) {
  border-radius: 6px;
  background: linear-gradient(90deg, #5c6bc0 0%, #7986cb 50%, #9fa8da 100%) !important;
  transition: width 0.35s ease;
}

.export-pdf-progress-dialog :deep(.el-dialog__header) {
  padding: 16px 20px 12px;
  border-bottom: 1px solid #e8eaf6;
  margin-right: 0;
}
.export-pdf-progress-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: #37474f;
}
.export-pdf-progress-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 24px;
}

@keyframes export-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(25, 118, 210, 0.2);
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
  padding: 6px 8px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
}

/* ==== Modern action button variants（颜色区分）==== */
.btn-refresh-modern,
.btn-generate-modern,
.btn-delete-modern,
.btn-edit-modern,
.btn-search-modern,
.btn-export-baseline-modern,
.btn-print-baseline-modern,
.btn-print-operation-modern,
.btn-clear-modern {
  border-radius: 12px !important;
  font-weight: 650;
  transition: all 0.18s ease;
}

.btn-refresh-modern {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
  border: 1px solid rgba(99, 102, 241, 0.55) !important;
  color: #ffffff !important;
  box-shadow: 0 10px 24px rgba(99, 102, 241, 0.18);
}
.btn-refresh-modern:hover {
  filter: brightness(1.03);
}

.btn-generate-modern {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
  border: 1px solid rgba(34, 197, 94, 0.55) !important;
  color: #ffffff !important;
}
.btn-generate-modern:hover {
  filter: brightness(1.03);
}

.btn-delete-modern {
  background: rgba(239, 68, 68, 0.08) !important;
  border: 1px solid rgba(239, 68, 68, 0.35) !important;
  color: #991b1b !important;
}
.btn-delete-modern:hover {
  background: rgba(239, 68, 68, 0.12) !important;
  border-color: rgba(239, 68, 68, 0.5) !important;
}

.btn-edit-modern {
  background: rgba(245, 158, 11, 0.10) !important;
  border: 1px solid rgba(245, 158, 11, 0.35) !important;
  color: #92400e !important;
}
.btn-edit-modern:hover {
  background: rgba(245, 158, 11, 0.14) !important;
  border-color: rgba(245, 158, 11, 0.52) !important;
}

.btn-search-modern {
  background: rgba(99, 102, 241, 0.10) !important;
  border: 1px solid rgba(99, 102, 241, 0.35) !important;
  color: #3730a3 !important;
}
.btn-search-modern:hover {
  background: rgba(99, 102, 241, 0.14) !important;
  border-color: rgba(99, 102, 241, 0.55) !important;
}

.btn-clear-modern {
  background: rgba(148, 163, 184, 0.12) !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  color: #334155 !important;
}
.btn-clear-modern:hover {
  background: rgba(148, 163, 184, 0.18) !important;
  border-color: rgba(148, 163, 184, 0.55) !important;
}

.btn-export-baseline-modern {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.98) 0%, rgba(37, 99, 235, 0.96) 100%) !important;
  border: 1px solid rgba(37, 99, 235, 0.45) !important;
  color: #ffffff !important;
}
.btn-export-baseline-modern:hover {
  filter: brightness(1.03);
}

.btn-print-baseline-modern,
.btn-print-operation-modern {
  background: rgba(37, 99, 235, 0.08) !important;
  border: 1px solid rgba(37, 99, 235, 0.35) !important;
  color: #1d4ed8 !important;
}
.btn-print-baseline-modern:hover,
.btn-print-operation-modern:hover {
  background: rgba(37, 99, 235, 0.12) !important;
  border-color: rgba(37, 99, 235, 0.55) !important;
}

/* 紧凑型页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 8px;
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
  animation: slideDown 0.4s ease-out;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon-wrapper {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.title-icon {
  font-size: 20px;
  color: white;
}

.title-content h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
  line-height: 1.2;
}

.title-content p {
  margin: 2px 0 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  line-height: 1.3;
}

/* 合并的操作卡片 */
.action-card {
  margin-bottom: 8px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  animation: fadeInUp 0.5s ease-out;
  transition: box-shadow 0.3s ease;
}

.action-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.action-card :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

.action-content {
  display: flex;
  gap: 10px;
  padding: 0;
  align-items: flex-start;
}

.action-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.action-divider {
  width: 1px;
  background: linear-gradient(180deg, transparent, #e2e8f0, transparent);
  margin: 0 4px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.section-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 16px;
  color: white;
  flex-shrink: 0;
}

.generate-icon-bg {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.filter-icon-bg {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.section-title h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
}

.section-desc {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.section-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 紧凑型摘要卡片 */
.summary-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 5px;
  margin-bottom: 6px;
}

.summary-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInScale 0.5s ease-out backwards;
  position: relative;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  border-color: #c7d2fe;
}

.summary-card:hover::before {
  transform: scaleX(1);
}

.summary-card-inner {
  padding: 7px 9px;
}

.summary-label {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  transition: color 0.3s ease;
}

.summary-value.negative {
  color: #ef4444;
}

.summary-value.positive {
  color: #10b981;
}

.summary-desc {
  margin-top: 4px;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.3;
}

/* 表格卡片 */
.table-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 8px;
  animation: fadeInUp 0.6s ease-out;
  transition: box-shadow 0.3s ease;
}

.table-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.table-card:not(.operation-rate-card) :deep(.el-card__header) {
  padding: 8px 12px 10px;
}

.table-card:not(.operation-rate-card) :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

/* ベースライン比較一覧カード：ヘッダー・本文を詰めて現代的に */
.baseline-comparison-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(99, 102, 241, 0.06);
}

.baseline-comparison-card :deep(.el-card__header) {
  padding: 8px 12px 9px !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background: linear-gradient(180deg, #fafbff 0%, #ffffff 100%);
}

.baseline-comparison-card :deep(.el-card__body) {
  padding: 6px 8px 10px !important;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 40%);
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

.comparison-list-head__icon {
  font-size: 20px;
  color: #6366f1;
  flex-shrink: 0;
}

.comparison-list-head__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.comparison-list-head__title {
  font-size: 15px;
  font-weight: 750;
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
  font-weight: 600 !important;
}

.comparison-list-head__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 5px 8px 5px 10px;
  margin-left: auto;
  background: linear-gradient(180deg, #f1f5f9 0%, #e8eef5 100%);
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 11px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.comparison-list-btn {
  border-radius: 10px !important;
  font-weight: 650 !important;
  padding: 5px 12px !important;
}

@media (max-width: 900px) {
  .comparison-list-head__actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
}

/* 操業度（APS 設備操業度）— ベースライン比較 table-card と同系統のヘッダー・本文・表 */
.operation-rate-card {
  animation: fadeInUp 0.65s ease-out 0.06s backwards;
}

.operation-rate-card :deep(.el-card__header) {
  padding: 10px 14px 11px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
}

.operation-rate-card :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

.operation-rate-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 14px;
}

.operation-rate-head__lead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.operation-rate-head__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 6px 10px 6px 12px;
  margin-left: auto;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid rgba(148, 163, 184, 0.42);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.operation-rate-ctl-label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.03em;
  white-space: nowrap;
  user-select: none;
}

.operation-rate-title-meta {
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 0.02em;
}

.operation-rate-picker {
  width: 132px;
  flex: 0 0 auto;
}

.operation-rate-select {
  width: 200px;
  min-width: 160px;
  max-width: 260px;
  flex: 0 1 auto;
}

.operation-rate-print-btn {
  flex: 0 0 auto;
  border-radius: 10px !important;
  padding: 5px 12px !important;
  margin-left: 2px;
}

.operation-rate-head__controls :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.35) inset;
}

.operation-rate-head__controls :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

@media (max-width: 960px) {
  .operation-rate-head__controls {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
}

.operation-rate-body {
  display: flex;
  flex-direction: column;
}

.operation-rate-table {
  border-radius: 8px;
  overflow: hidden;
}

.util-note--baseline {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 8px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
}
.util-note-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #475569;
}
.util-note-chip--formula {
  background: #eef2ff;
  color: #4338ca;
}
.util-col-head {
  font-size: 11px;
  line-height: 1.25;
}
.operation-rate-table :deep(.util-num) {
  font-variant-numeric: tabular-nums;
}
.operation-rate-table :deep(.util-num--actual) {
  color: #0d9488;
}
.operation-rate-table :deep(.util-num--negative) {
  color: #c62828;
  font-weight: 600;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header-icon {
  font-size: 18px;
  color: #6366f1;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.month-tag {
  margin-left: 4px;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.count-tag {
  font-weight: 500;
}

.baseline-adjust-dialog :deep(.el-dialog__body) {
  padding: 16px 20px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 80%);
}

.fixed-baseline-dialog :deep(.el-dialog__body) {
  padding: 16px 20px 8px;
}

.fixed-baseline-desc {
  margin: 0 0 16px;
  font-size: 13px;
  line-height: 1.55;
  color: #475569;
}

.fixed-baseline-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.fixed-baseline-input {
  width: 100%;
}

.adjustment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.adjustment-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
}

.adjustment-desc {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.adjustment-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  padding: 10px 14px;
  background: rgba(148, 163, 184, 0.08);
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.toolbar-month,
.toolbar-process {
  width: 170px;
}

.adjustment-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.adjustment-table :deep(.el-table__header th) {
  background: linear-gradient(90deg, #eef2ff 0%, #f8fafc 100%);
  color: #1e293b;
  font-weight: 600;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
}

.adjustment-table :deep(.el-table__row) {
  transition: background 0.2s ease;
}

.adjustment-actions {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.adjustment-table :deep(.el-table__row:hover > td) {
  background: rgba(99, 102, 241, 0.08);
}

.plan-editor {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 6px 10px;
  background: rgba(237, 242, 247, 0.7);
  border-radius: 8px;
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
  width: 100%;
  padding: 8px 0;
}

.adjustment-footer .el-button:first-child {
  font-weight: 600;
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
  font-weight: 600;
  color: #64748b;
  background: #f8fafc;
  transition:
    color 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__item.is-active) {
  color: #4338ca !important;
  font-weight: 750;
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%) !important;
  border-color: #a5b4fc !important;
  box-shadow: 0 1px 4px rgba(79, 70, 229, 0.12);
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__item:hover) {
  color: #4f46e5;
  border-color: #c7d2fe !important;
}

.baseline-comparison-card :deep(.comparison-tabs.el-tabs--card .el-tabs__nav-scroll) {
  padding: 2px 0;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  margin-left: 2px;
  font-size: 10px;
  font-weight: 700;
  color: #4338ca;
  background: rgba(99, 102, 241, 0.12);
  border-radius: 999px;
}

/* 合計区域（工程タブ下・コンパクト） */
.tab-total-wrapper {
  margin-top: 6px;
  padding: 8px 10px;
  background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
  border: 1px solid rgba(203, 213, 225, 0.85);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.tab-total-wrapper:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.1);
}

.tab-total-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
}

.total-icon {
  font-size: 16px;
  color: #6366f1;
}

.tab-total-label {
  font-weight: 750;
  color: #0f172a;
  font-size: 13px;
  letter-spacing: 0.03em;
}

.tab-total-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(156px, 1fr));
  gap: 6px;
}

.total-item {
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 9px;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}

.total-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.total-item:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.total-item:hover::before {
  transform: scaleX(1);
}

.total-item-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 4px;
}

.total-item-icon {
  font-size: 14px;
  color: #6366f1;
}

.total-item-label {
  font-size: 10px;
  color: #64748b;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.45px;
}

.total-item-value {
  font-size: 16px;
  font-weight: 750;
  color: #1e293b;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 5px;
  line-height: 1.15;
}

/* 不同指标的颜色区分 */
.current-plan-item .total-item-icon {
  color: #3b82f6;
}

.current-plan-item::before {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.current-plan-item .total-item-value {
  color: #3b82f6;
}

.plan-diff-item.diff-positive .total-item-icon {
  color: #10b981;
}

.plan-diff-item.diff-positive::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.plan-diff-item.diff-positive .total-item-value {
  color: #10b981;
}

.plan-diff-item.diff-negative .total-item-icon {
  color: #ef4444;
}

.plan-diff-item.diff-negative::before {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.plan-diff-item.diff-negative .total-item-value {
  color: #ef4444;
}

.actual-item .total-item-icon {
  color: #10b981;
}

.actual-item::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.actual-item .total-item-value {
  color: #10b981;
}

.actual-diff-item.diff-positive .total-item-icon {
  color: #10b981;
}

.actual-diff-item.diff-positive::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.actual-diff-item.diff-positive .total-item-value {
  color: #10b981;
}

.actual-diff-item.diff-negative .total-item-icon {
  color: #ef4444;
}

.actual-diff-item.diff-negative::before {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.actual-diff-item.diff-negative .total-item-value {
  color: #ef4444;
}

.total-trend-icon {
  font-size: 14px;
  font-weight: 600;
}

.total-trend-icon.trend-up {
  color: #10b981;
}

.total-trend-icon.trend-down {
  color: #ef4444;
}

/* 日期单元格样式 */
.date-cell-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
}

.date-icon {
  font-size: 12px;
  color: #6366f1;
  opacity: 0.7;
}

.date-cell {
  font-weight: 500;
  color: #334155;
  font-size: 12px;
}

.negative-number {
  color: #ef4444;
  font-weight: 600;
}

/* 表格（比較一覧・操業度共通クラス） */
:deep(.comparison-table) {
  font-size: 12px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

:deep(.comparison-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.comparison-table .el-table__border-column-patch) {
  display: none;
}

:deep(.comparison-table .el-table__header-wrapper) {
  border-radius: 10px 10px 0 0;
}

:deep(.comparison-table .el-table__header th) {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #6366f1 100%);
  color: white;
  font-weight: 650;
  font-size: 11px;
  padding: 5px 7px;
  border: none;
  text-align: center;
}

:deep(.comparison-table .el-table__header th:first-child) {
  border-radius: 10px 0 0 0;
}

:deep(.comparison-table .el-table__header th .cell) {
  color: white;
  font-weight: 650;
}

:deep(.comparison-table .el-table__body td) {
  padding: 3px 7px;
  border-color: #e8ecf1;
  transition: background-color 0.15s ease;
}

:deep(.comparison-table .el-table__row) {
  transition: background-color 0.15s ease;
}

:deep(.comparison-table .el-table__row:hover > td) {
  background-color: #eef2ff !important;
}

:deep(.comparison-table .el-table__row--striped td) {
  background-color: #f8fafc;
}

:deep(.comparison-table .el-table__row--striped:hover > td) {
  background-color: #e8edff !important;
}

:deep(.comparison-table .el-table__fixed-left-patch) {
  background-color: transparent;
}

:deep(.comparison-table .el-table__fixed) {
  box-shadow: 2px 0 10px rgba(15, 23, 42, 0.06);
}

:deep(.comparison-table .el-table__fixed-left) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__header th) {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #6366f1 100%);
  color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__body td) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row:hover > td) {
  background-color: #eef2ff !important;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped td) {
  background-color: #f8fafc;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped:hover > td) {
  background-color: #e8edff !important;
}

/* 数值单元格样式 */
.number-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
  padding: 2px 4px;
  border-radius: 6px;
  transition: background-color 0.15s ease;
  min-height: 18px;
}

.number-cell:hover {
  background-color: rgba(99, 102, 241, 0.05);
}

.number-value {
  font-weight: 600;
  font-size: 12px;
  color: #1e293b;
  letter-spacing: 0.2px;
}

.baseline-plan .number-value {
  color: #6366f1;
}

.current-plan .number-value {
  color: #3b82f6;
}

.actual-cell .number-value {
  color: #10b981;
}

.diff-cell.diff-positive {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
}

.diff-cell.diff-positive .number-value {
  color: #10b981;
}

.diff-cell.diff-negative {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
}

.diff-cell.diff-negative .number-value {
  color: #ef4444;
}

.diff-cell.diff-zero {
  background: rgba(148, 163, 184, 0.05);
}

.diff-cell.diff-zero .number-value {
  color: #64748b;
}

.trend-icon {
  font-size: 12px;
  font-weight: 600;
}

.trend-icon.trend-up {
  color: #10b981;
}

.trend-icon.trend-down {
  color: #ef4444;
}

/* 表格列头样式 */
.column-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
}

.column-header span {
  color: white;
  font-weight: 600;
}

.help-icon {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  cursor: help;
  transition: all 0.2s ease;
}

.help-icon:hover {
  color: white;
  transform: scale(1.1);
}

/* 动画关键帧 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
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
