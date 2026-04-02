<template>
  <div
    class="plan-baseline-root"
    :class="{
      'print-baseline': printTarget === 'baseline',
      'print-operation': printTarget === 'operation',
    }"
  >
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
              <span class="section-desc">計画を固定化して比較基準を作成</span>
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

    <!-- 紧凑型表格卡片 -->
    <el-card shadow="hover" class="table-card baseline-comparison-card">
      <template #header>
        <div class="card-header">
          <div class="card-header-left">
            <el-icon class="card-header-icon"><Setting /></el-icon>
            <span class="card-title">ベースライン比較一覧</span>
            <el-tag
              v-if="comparisonResult?.baselineMonth"
              type="info"
              size="small"
              class="month-tag"
            >
              {{ dayjs(comparisonResult.baselineMonth).format('YYYY年MM月') }}
            </el-tag>
          </div>
          <div class="card-header-right">
            <el-tag v-if="totalItemsCount > 0" type="primary" size="small" class="count-tag">
              総件数: {{ totalItemsCount }}
            </el-tag>
            <el-button
              type="primary"
              plain
              class="btn-export-baseline-modern"
              :icon="Download"
              @click="handleExportPdfToFolder"
              :loading="exportPdfLoading"
              :disabled="!canExportBaselinePdf"
              size="default"
            >
              工程別報告書発行
            </el-button>

            <el-button
              type="default"
              plain
              class="btn-print-baseline-modern"
              :icon="Printer"
              @click="handlePrintBaselineComparison"
              :disabled="totalItemsCount === 0"
              size="default"
            >
              印刷
            </el-button>
          </div>
        </div>
      </template>
      <el-tabs v-model="activeTab" type="border-card" v-loading="tableLoading">
        <el-tab-pane
          v-for="process in processTabs"
          :key="process.name"
          :label="process.label"
          :name="process.name"
        >
          <template #label>
            <span class="tab-label">
              <el-icon class="tab-icon"><Setting /></el-icon>
              {{ process.label }}
              <el-tag size="small" type="info" class="tab-count">{{ process.count }}</el-tag>
            </span>
          </template>
          <el-table
            :data="process.items"
            border
            stripe
            height="380"
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
                    content="ベースライン生成時に固定化された計画値"
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
                    content="production_plan_updates を優先し、無い工程は production_summarys の各 plan 列を日次合計"
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

    <!-- 操業度 production_plan_rate（Excel 取込）— スタイルはベースライン比較カードに合わせる -->
    <el-card class="table-card operation-rate-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="card-header-left">
            <el-icon class="card-header-icon"><DataLine /></el-icon>
            <span class="card-title">操業度</span>
            <span class="operation-rate-title-meta">production_plan_rate</span>
            <el-tag v-if="planRateFilter.baselineMonth" type="info" size="small" class="month-tag">
              {{ dayjs(planRateFilter.baselineMonth).format('YYYY年MM月') }}
            </el-tag>
            <el-tag v-if="planRateRows.length > 0" type="primary" size="small" class="count-tag">
              {{ planRateRows.length }} 件
            </el-tag>
          </div>
          <div class="card-header-right operation-rate-header-actions">
            <el-date-picker
              v-model="planRateFilter.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="対象月"
              size="default"
              class="operation-rate-picker"
            />
            <el-select
              v-model="planRateFilter.processName"
              placeholder="工程"
              clearable
              size="default"
              class="operation-rate-select"
            >
              <el-option
                v-for="opt in planRateProcessOptions"
                :key="opt.value === '' ? '_all' : opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <el-button type="primary" :icon="Search" :loading="planRateLoading" @click="loadPlanOperationRate">
              検索
            </el-button>

            <el-button
              type="default"
              plain
              class="btn-print-operation-modern"
              :icon="Printer"
              @click="handlePrintOperationRate"
              :disabled="planRateRows.length === 0"
              size="default"
            >
              印刷
            </el-button>
          </div>
        </div>
      </template>
      <div class="operation-rate-body">
        <el-table
          v-loading="planRateLoading"
          :data="planRateRows"
          border
          stripe
          size="small"
          class="comparison-table operation-rate-table"
          max-height="360"
          empty-text="該当データがありません。月・工程を選んで検索してください。"
        >
          <el-table-column prop="display_month" label="月" width="72" align="center" />
          <el-table-column prop="display_process" label="工程" width="88" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.display_process" size="small" type="info" effect="plain">
                {{ row.display_process }}
              </el-tag>
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column prop="machine_cd" label="ラインCD" min-width="110" show-overflow-tooltip />
          <el-table-column prop="machine_name" label="ライン" min-width="140" show-overflow-tooltip />
          <el-table-column prop="operation_variance" label="操業度差異" width="120" align="right">
            <template #default="{ row }">
              <span
                v-for="(ov, oi) in [operationVarianceRowView(row.operation_variance)]"
                :key="oi"
                class="operation-variance-cell"
                :class="ov.cls"
              >
                {{ ov.text }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="file_name" label="ファイル名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="processed_at" label="取込日時" width="160" align="center" />
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
  fetchPlanOperationRate,
  updatePlanBaselinePlanQuantity,
  exportPlanBaselinePdfToFolder,
  type PlanBaselineComparisonItem,
  type PlanBaselineComparisonResult,
  type PlanBaselineRecord,
  type PlanOperationRateRow,
} from '@/api/planBaseline'
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

const planRateFilter = reactive({
  baselineMonth: today,
  processName: '' as string,
})
const planRateProcessOptions = [
  { label: '全て', value: '' },
  { label: '成型', value: '成型' },
  { label: '溶接', value: '溶接' },
]
const planRateRows = ref<PlanOperationRateRow[]>([])
const planRateLoading = ref(false)

const generating = ref(false)
const deleting = ref(false)
const tableLoading = ref(false)
const exportPdfLoading = ref(false)
const exportProgressVisible = ref(false)
const exportProgressPercent = ref(0)
const exportProgressCurrent = ref('')
type PrintTarget = 'baseline' | 'operation' | ''
const printTarget = ref<PrintTarget>('')
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

/** 操業度差異の生文字列を数値化（カンマ・Unicode マイナス対応） */
function parseOperationVarianceNumber(raw: string): number | null {
  const s = raw
    .replace(/,/g, '')
    .replace(/\u2212/g, '-')
    .replace(/\uFF0D/g, '-')
    .trim()
  if (s === '' || s === '-') return null
  const n = Number(s)
  return Number.isNaN(n) ? null : n
}

/** 操業度差異の表示用テキスト・負数フラグ（一覧・PDF 共通） */
function getOperationVarianceDisplayMeta(v: string | null | undefined): {
  text: string
  negative: boolean
  isEmpty: boolean
} {
  if (v == null || v === '') return { text: '', negative: false, isEmpty: true }
  const raw = String(v).trim()
  const n = parseOperationVarianceNumber(raw)
  if (n !== null) {
    return { text: formatNumber(n), negative: n < 0, isEmpty: false }
  }
  const normalized = raw.replace(/\u2212/g, '-').replace(/\uFF0D/g, '-').replace(/,/g, '').trim()
  const negative = /^-\d/.test(normalized) || /^-\./.test(normalized)
  return { text: raw, negative, isEmpty: false }
}

function operationVarianceRowView(v: string | null | undefined) {
  const m = getOperationVarianceDisplayMeta(v)
  return {
    text: m.isEmpty ? '—' : m.text,
    cls: m.negative ? 'operation-variance-cell--negative' : '',
  }
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

const loadPlanOperationRate = async () => {
  if (!planRateFilter.baselineMonth) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  planRateLoading.value = true
  try {
    const monthNum = dayjs(planRateFilter.baselineMonth).month() + 1
    planRateRows.value = await fetchPlanOperationRate({
      monthNum,
      processName: planRateFilter.processName || undefined,
    })
  } catch (error: any) {
    ElMessage.error(error?.message || '操業度データの取得に失敗しました')
    planRateRows.value = []
  } finally {
    planRateLoading.value = false
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

/** 操業度を工程ごとに PDF ページ分け（各工程は新規ページから。表が長い工程は縦に続けて複数ページ）。データなしは null */
async function buildOperationRateCombinedPdf(baselineMonth: string): Promise<Blob | null> {
  const monthNum = dayjs(baselineMonth).month() + 1
  const rows = await fetchPlanOperationRate({ monthNum })
  if (!rows.length) return null

  const esc = (s: string) =>
    String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')

  const processOrder = ['成型', '溶接']
  const groupMap = new Map<string, PlanOperationRateRow[]>()
  for (const r of rows) {
    const key = (r.display_process || '').trim() || 'その他'
    if (!groupMap.has(key)) groupMap.set(key, [])
    groupMap.get(key)!.push(r)
  }
  const groupKeys = [...groupMap.keys()].sort((a, b) => {
    const ia = processOrder.indexOf(a)
    const ib = processOrder.indexOf(b)
    if (ia !== -1 && ib !== -1) return ia - ib
    if (ia !== -1) return -1
    if (ib !== -1) return 1
    return a.localeCompare(b, 'ja')
  })

  const monthLabel = dayjs(baselineMonth).format('YYYY年MM月')
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
  for (const proc of groupKeys) {
    const group = groupMap.get(proc)!
    if (!group.length) continue

    const rowParts = group.map((r, idx) => {
      const bg = idx % 2 === 0 ? '#fafafa' : '#fff'
      const meta = getOperationVarianceDisplayMeta(r.operation_variance)
      const inner = meta.isEmpty ? '-' : esc(meta.text)
      const varStyle = meta.negative ? ' color:#c62828;' : ''
      return `<tr style="background:${bg};">
        <td style="border:1px solid #bdbdbd;padding:5px 8px;">${esc(r.display_month || '')}</td>
        <td style="border:1px solid #bdbdbd;padding:5px 8px;">${esc(r.display_process || '')}</td>
        <td style="border:1px solid #bdbdbd;padding:5px 8px;">${esc(String(r.machine_cd ?? ''))}</td>
        <td style="border:1px solid #bdbdbd;padding:5px 8px;">${esc(String(r.machine_name ?? ''))}</td>
        <td style="border:1px solid #bdbdbd;padding:5px 8px;text-align:right;${varStyle}">${inner}</td>
      </tr>`
    })

    const tableBlock = `
      <div style="margin-bottom:18px;">
        <div style="font-size:14px;font-weight:700;color:#37474f;margin:12px 0 8px;padding:6px 10px;background:#eceff1;border-left:4px solid #1565c0;">工程：${esc(proc)}</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;border:1px solid #90a4ae;">
          <thead>
            <tr style="background:linear-gradient(180deg,#37474f 0%,#455a64 100%);color:#fff;">
              <th style="border:1px solid #546e7a;padding:6px 8px;text-align:center;">月</th>
              <th style="border:1px solid #546e7a;padding:6px 8px;text-align:center;">工程</th>
              <th style="border:1px solid #546e7a;padding:6px 8px;text-align:left;">ラインCD</th>
              <th style="border:1px solid #546e7a;padding:6px 8px;text-align:left;">ライン</th>
              <th style="border:1px solid #546e7a;padding:6px 8px;text-align:right;">操業度差異</th>
            </tr>
          </thead>
          <tbody>${rowParts.join('')}</tbody>
        </table>
      </div>`

    const html = `
    <div class="operation-rate-pdf-root" style="font-family:'Meiryo','Hiragino Sans','Yu Gothic',sans-serif;padding:20px;background:#fff;width:720px;box-sizing:border-box;">
      <div style="font-size:17px;font-weight:bold;color:#1565c0;margin-bottom:6px;padding-bottom:8px;border-bottom:2px solid #e3f2fd;">操業度（工程別）</div>
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
  loadPlanOperationRate()
})

function handlePrintBaselineComparison() {
  printTarget.value = 'baseline'
  nextTick(() => {
    window.print()
  })
}

function handlePrintOperationRate() {
  printTarget.value = 'operation'
  nextTick(() => {
    window.print()
  })
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
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: 6px;
  margin-bottom: 8px;
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
  padding: 8px 10px;
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

/* 操業度（production_plan_rate）— ベースライン比較 table-card と同系統のヘッダー・本文・表 */
.operation-rate-card {
  animation: fadeInUp 0.65s ease-out 0.06s backwards;
}

.operation-rate-card :deep(.el-card__header) {
  padding: 8px 12px 10px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
}

.operation-rate-card :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

.operation-rate-title-meta {
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 0.02em;
}

.operation-rate-header-actions {
  flex-wrap: wrap;
  gap: 8px;
}

.operation-rate-picker {
  width: 150px;
}

.operation-rate-select {
  width: 132px;
}

.operation-rate-body {
  display: flex;
  flex-direction: column;
}

.operation-rate-table {
  border-radius: 8px;
  overflow: hidden;
}

.operation-variance-cell--negative {
  color: #c62828;
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

/* 标签页样式 */
:deep(.el-tabs__header) {
  margin: 0 0 6px 0;
  border-bottom: 2px solid #e2e8f0;
}

:deep(.el-tabs__item) {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-tabs__item.is-active) {
  color: #6366f1;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  background-color: #6366f1;
  height: 2px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-icon {
  font-size: 14px;
  color: #6366f1;
}

.tab-count {
  margin-left: 4px;
  font-size: 11px;
}

/* 合計区域美化 */
.tab-total-wrapper {
  margin-top: 8px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease-out;
}

.tab-total-wrapper:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  transform: translateY(-1px);
}

.tab-total-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid #e2e8f0;
}

.total-icon {
  font-size: 18px;
  color: #6366f1;
}

.tab-total-label {
  font-weight: 700;
  color: #1e293b;
  font-size: 15px;
  letter-spacing: 0.5px;
}

.tab-total-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}

.total-item {
  padding: 8px 10px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  transform: translateY(-2px);
}

.total-item:hover::before {
  transform: scaleX(1);
}

.total-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.total-item-icon {
  font-size: 14px;
  color: #6366f1;
}

.total-item-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.total-item-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  line-height: 1.2;
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

/* 表格样式优化 */
:deep(.comparison-table) {
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

:deep(.comparison-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.comparison-table .el-table__border-column-patch) {
  display: none;
}

:deep(.comparison-table .el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

:deep(.comparison-table .el-table__header th) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-weight: 600;
  font-size: 11px;
  padding: 5px 8px;
  border: none;
  text-align: center;
}

:deep(.comparison-table .el-table__header th:first-child) {
  border-radius: 8px 0 0 0;
}

:deep(.comparison-table .el-table__header th .cell) {
  color: white;
  font-weight: 600;
}

:deep(.comparison-table .el-table__body td) {
  padding: 4px 8px;
  border-color: #e2e8f0;
  transition: all 0.2s ease;
}

:deep(.comparison-table .el-table__row) {
  transition: all 0.2s ease;
}

:deep(.comparison-table .el-table__row:hover > td) {
  background-color: #f0f4ff !important;
  transform: scale(1.01);
}

:deep(.comparison-table .el-table__row--striped td) {
  background-color: #fafbfc;
}

:deep(.comparison-table .el-table__row--striped:hover > td) {
  background-color: #eef2ff !important;
}

:deep(.comparison-table .el-table__fixed-left-patch) {
  background-color: transparent;
}

:deep(.comparison-table .el-table__fixed) {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

:deep(.comparison-table .el-table__fixed-left) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__header th) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__body td) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row:hover > td) {
  background-color: #f0f4ff !important;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped td) {
  background-color: #fafbfc;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped:hover > td) {
  background-color: #eef2ff !important;
}

/* 数值单元格样式 */
.number-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  padding: 3px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
  min-height: 20px;
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
  animation: pulseUp 2s ease-in-out infinite;
}

.trend-icon.trend-down {
  color: #ef4444;
  animation: pulseDown 2s ease-in-out infinite;
}

@keyframes pulseUp {
  0%,
  100% {
    opacity: 1;
    transform: translateY(0);
  }
  50% {
    opacity: 0.7;
    transform: translateY(-2px);
  }
}

@keyframes pulseDown {
  0%,
  100% {
    opacity: 1;
    transform: translateY(0);
  }
  50% {
    opacity: 0.7;
    transform: translateY(2px);
  }
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

@media print {
  /* 打印时仅显示指定区域（同时隐藏按钮/筛选控件） */
  .plan-baseline-root {
    background: #ffffff !important;
  }

  .plan-baseline-root .page-header,
  .plan-baseline-root .action-card,
  .plan-baseline-root .summary-row,
  .plan-baseline-root .el-dialog,
  .plan-baseline-root .el-dialog__wrapper,
  .plan-baseline-root .table-card {
    display: none !important;
  }

  .plan-baseline-root.print-baseline .baseline-comparison-card,
  .plan-baseline-root.print-operation .operation-rate-card {
    display: block !important;
  }

  /* 只保留区域表头左侧信息，隐藏右侧操作（导出/打印/计数等） */
  .plan-baseline-root.print-baseline .baseline-comparison-card .card-header-right .el-button {
    display: none !important;
  }

  .plan-baseline-root.print-operation .operation-rate-card .operation-rate-header-actions > * {
    display: none !important;
  }

  /* 取消表格固定高度与滚动，避免打印时只截到可视区域 */
  .plan-baseline-root.print-baseline .comparison-table,
  .plan-baseline-root.print-operation .operation-rate-table,
  .plan-baseline-root.print-baseline .el-table__body-wrapper,
  .plan-baseline-root.print-operation .el-table__body-wrapper {
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
  }
}
</style>
