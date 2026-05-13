<template>
  <div class="plan-summary-page">
    <header class="toolbar">
      <div class="toolbar-lead">
        <h1 class="toolbar-title">工程別計画試算</h1>
        <span class="toolbar-period">{{ periodLabel }}</span>
      </div>
      <div class="toolbar-actions">
        <el-date-picker
          v-model="periodRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          format="YYYY/MM/DD"
          range-separator="～"
          start-placeholder="開始日"
          end-placeholder="終了日"
          size="small"
          class="period-range-picker"
          :clearable="false"
          :shortcuts="periodRangeShortcuts"
          @change="onPeriodFilterChange"
        />
        <el-button
          type="primary"
          class="ps-action-btn ps-action-btn--primary"
          :loading="loading"
          :icon="Refresh"
          @click="reloadForCurrentPeriod"
        >
          更新
        </el-button>
        <el-button
          type="success"
          plain
          class="ps-action-btn ps-action-btn--excel"
          :disabled="loading || matrixRows.length === 0"
          :icon="Download"
          @click="exportExcel"
        >
          Excel出力
        </el-button>
      </div>
    </header>

    <div class="table-shell" v-loading="loading">
      <div class="table-scroll">
        <el-table
          :data="matrixRows"
          border
          stripe
          size="small"
          class="matrix-table"
          empty-text="データがありません"
          :header-cell-style="headerCellStyle"
          :cell-style="cellStyle"
          :row-class-name="matrixRowClassName"
          :cell-class-name="matrixCellClassName"
        >
          <el-table-column prop="item" label="工程" width="100" fixed="left" class-name="col-item" />
          <el-table-column
            v-for="date in dateColumns"
            :key="date"
            :prop="date"
            :label="formatDateLabel(date)"
            min-width="62"
            align="right"
            class-name="col-num"
          >
            <template #default="{ row }">
              <span class="num-cell">{{ formatNumberDisplay(Number(row[date] ?? 0)) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="rowTotal" label="合計" width="72" align="right" fixed="right" class-name="col-total">
            <template #default="{ row }">
              <span class="total-cell">{{ formatNumberDisplay(Number(row.rowTotal ?? 0)) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <section class="manual-sheet" aria-label="手入力パラメータ">
      <header class="manual-sheet__header">
        <div class="manual-sheet__header-text">
          <span class="manual-sheet__badge">試算パラメータ</span>
          <!-- <span class="manual-sheet__subtitle">表の合計 ÷ 稼働日（整数）</span> -->
        </div>
        <div class="manual-sheet__header-actions">
          <div class="manual-sheet__working" title="稼働日数">
            <span class="manual-sheet__working-label">稼働日</span>
            <div class="manual-sheet__working-value manual-sheet__cell--yellow">
              <el-input-number
                v-model="workingDays"
                :min="0"
                :max="999"
                :precision="0"
                :controls="false"
                size="small"
                class="manual-input-inner"
              />
            </div>
          </div>
          <el-button
            type="warning"
            plain
            size="small"
            class="ps-action-btn ps-action-btn--ghost"
            :icon="Delete"
            @click="onClearManualDraft"
          >
            手入力クリア
          </el-button>
        </div>
      </header>

      <div class="manual-sheet__metrics-band">
        <div class="manual-sheet__metrics-inner">
          <div
            v-for="m in trialToolbarMetricConfigs"
            :key="m.itemName"
            class="manual-sheet__metric"
          >
            <span class="manual-sheet__metric-label">{{ m.label }}</span>
            <el-input
              class="manual-sheet__metric-input"
              size="small"
              readonly
              :model-value="formatNumberDisplay(perDayIntegerByRowItem(m.itemName))"
            />
          </div>
        </div>
      </div>

      <div class="manual-sheet__cards">
        <article class="manual-card manual-card--daily">
          <h3 class="manual-card__title">工程別日当たり生産数</h3>
          <div class="manual-card__body">
            <table class="manual-grid" role="grid">
              <thead>
                <tr>
                  <th v-for="col in processColumnsDailyProductionVisible" :key="`d-h-${col.key}`">{{ col.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td v-for="col in processColumnsDailyProductionVisible" :key="`d-c-${col.key}`" class="manual-sheet__cell--yellow">
                    <el-input-number
                      :model-value="tableInputNumberDisplay(Number(manualDailyPerProcess[col.key] ?? 0))"
                      :min="0"
                      :max="999999999"
                      :precision="0"
                      :controls="false"
                      size="small"
                      class="manual-input-inner"
                      @update:model-value="(v) => { manualDailyPerProcess[col.key] = v ?? 0 }"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="manual-card manual-card--prev">
          <h3 class="manual-card__title manual-card__title--split">
            <span class="manual-card__title-lead">前月繰越数</span>
            <div class="manual-card__carry-toolbar">
              <span class="manual-card__carry-label">在庫参照月</span>
              <el-date-picker
                v-model="prevCarryInventoryMonthYm"
                type="month"
                value-format="YYYY-MM"
                format="YYYY/MM"
                placeholder="YYYY-MM"
                size="small"
                class="manual-card__month-picker"
                :clearable="true"
              />
              <el-button
                type="primary"
                plain
                size="small"
                class="ps-action-btn ps-action-btn--carry"
                :loading="loadingPrevCarryInventory"
                :disabled="!prevCarryInventoryMonthYm"
                @click="fetchPrevCarryInventoryFromSelectedMonth"
              >
                月末在庫反映
              </el-button>
            </div>
          </h3>
          <div class="manual-card__body">
            <table class="manual-grid" role="grid">
              <thead>
                <tr>
                  <th v-for="col in processColumns" :key="`p-h-${col.key}`">{{ carryTableColumnLabel(col) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td
                    v-for="col in processColumns"
                    :key="`p-c-${col.key}`"
                    class="manual-sheet__cell--yellow manual-sheet__cell--prev-carry"
                    title="ダブルクリックで内訳（在庫参照月の月末・製品×ルート）"
                    @dblclick="openPrevCarryBreakdown(col.key)"
                  >
                    <el-input-number
                      :model-value="tableInputNumberDisplay(Number(manualPrevMonthCarry[col.key] ?? 0))"
                      :min="0"
                      :max="999999999"
                      :precision="0"
                      :controls="false"
                      size="small"
                      class="manual-input-inner"
                      @update:model-value="(v) => { manualPrevMonthCarry[col.key] = v ?? 0 }"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="manual-card manual-card--muted">
          <h3 class="manual-card__title">次月繰越数</h3>
          <div class="manual-card__body">
            <table class="manual-grid" role="grid">
              <thead>
                <tr>
                  <th v-for="col in processColumns" :key="`n-h-${col.key}`">{{ carryTableColumnLabel(col) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td v-for="col in processColumns" :key="`n-c-${col.key}`" class="manual-sheet__cell--readonly">
                    {{ formatNumberDisplay(nextMonthCarryDisplayedValue(col.key)) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </section>

    <section
      v-if="dateColumns.length > 0"
      class="plan-process-section"
      aria-label="工程別計画（表格・推移）"
    >
      <div class="plan-process-card table-shell" aria-label="工程計画表格">
        <div class="plan-process-card__head plan-process-section__head">
          <h3 class="plan-process-section__title">工程計画</h3>
          <div class="plan-process-section__actions">
            <el-button size="small" class="ps-action-btn ps-action-btn--soft" @click="resetDailyPlanFromManualDaily">
              工程別日当で再計算
            </el-button>
            <el-button
              type="primary"
              plain
              size="small"
              class="ps-action-btn"
              @click="openProcessRunDaysDialog"
            >
              稼働日設定
            </el-button>
          </div>
        </div>
        <div class="table-scroll">
          <el-table
            :data="planProcessDailyPlanTableData"
            border
            stripe
            size="small"
            class="matrix-table"
            empty-text="データがありません"
            :header-cell-style="headerCellStyle"
            :cell-style="cellStyle"
            :cell-class-name="planDailyPlanTableCellClassName"
          >
            <el-table-column prop="item" label="工程" width="100" fixed="left" class-name="col-item" />
            <el-table-column
              v-for="date in dateColumns"
              :key="'pp-daily-' + date"
              :prop="date"
              :label="formatDateLabel(date)"
              min-width="62"
              align="right"
              class-name="col-num"
            >
              <template #default="{ row }">
                <el-input-number
                  :model-value="tableInputNumberDisplay(Number(row[date] ?? 0))"
                  :min="0"
                  :max="999999999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  class="plan-process-input-inner plan-process-input-inner--daily"
                  @update:model-value="(v) => setDailyPlanManualCell(row._planKey, date, v)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="rowTotal" label="合計" width="72" align="right" fixed="right" class-name="col-total">
              <template #default="{ row }">
                <span
                  class="total-cell"
                  :class="{
                    'plan-process-num--computed': true,
                    'plan-process-num--cutting': (row as PlanProcessMatrixRow)._planKey === 'cutting_plan',
                    'plan-process-num--chamfer': (row as PlanProcessMatrixRow)._planKey === 'chamfering_plan',
                    'plan-process-num--forming': (row as PlanProcessMatrixRow)._planKey === 'forming_plan',
                    'plan-process-num--plating-plan':
                      (row as PlanProcessMatrixRow)._planKey === 'plating_plan',
                    'plan-process-num--welding-plan':
                      (row as PlanProcessMatrixRow)._planKey === 'welding_plan',
                    'plan-process-num--inspection-plan':
                      (row as PlanProcessMatrixRow)._planKey === 'inspection_plan',
                  }"
                >
                  {{ formatNumberDisplay(Number(row.rowTotal ?? 0)) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div
        class="plan-process-card plan-process-card--trajectory-matrix table-shell"
        aria-label="工程計画推移"
      >
        <div class="plan-process-card__head plan-process-section__head plan-process-section__head--traj-tools">
          <h3 class="plan-process-section__title">工程計画推移</h3>
          <el-button
            type="info"
            plain
            circle
            size="small"
            class="ps-traj-help-btn"
            :icon="QuestionFilled"
            aria-label="工程計画推移の計算式を表示"
            @click="planProcessTrajectoryHelpVisible = true"
          />
        </div>
        <div class="table-scroll">
          <el-table
            :data="planProcessTableData"
            border
            stripe
            size="small"
            class="matrix-table"
            empty-text="データがありません"
            :header-cell-style="headerCellStyle"
            :cell-style="cellStyle"
            :cell-class-name="planProcessTableCellClassName"
          >
            <el-table-column prop="item" label="工程" width="100" fixed="left" class-name="col-item" />
          <el-table-column
            v-for="date in dateColumns"
            :key="'pp-traj-' + date"
            :prop="date"
            :label="formatDateLabel(date)"
            min-width="62"
            align="right"
            class-name="col-num"
          >
            <template #default="{ row }">
              <span
                v-if="
                  row._planKey === 'cutting_plan' ||
                  row._planKey === 'chamfering_plan' ||
                  row._planKey === 'forming_plan' ||
                  row._planKey === 'plating_plan' ||
                  row._planKey === 'inspection_plan' ||
                  row._planKey === 'welding_plan' ||
                  row._planKey === 'warehouse_plan'
                "
                class="num-cell plan-process-num--computed"
                :class="{
                  'plan-process-num--cutting': row._planKey === 'cutting_plan',
                  'plan-process-num--chamfer': row._planKey === 'chamfering_plan',
                  'plan-process-num--forming': row._planKey === 'forming_plan',
                  'plan-process-num--plating-plan': row._planKey === 'plating_plan',
                  'plan-process-num--inspection-plan': row._planKey === 'inspection_plan',
                  'plan-process-num--welding-plan': row._planKey === 'welding_plan',
                  'plan-process-num--warehouse-plan': row._planKey === 'warehouse_plan',
                }"
              >
                {{ formatNumberDisplay(Number(row[date] ?? 0)) }}
              </span>
              <el-input-number
                v-else
                :model-value="tableInputNumberDisplay(Number(row[date] ?? 0))"
                :min="0"
                :max="999999999"
                :precision="0"
                :controls="false"
                size="small"
                class="plan-process-input-inner"
                @update:model-value="(v) => planProcessInputCommit(row, date, v)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="rowTotal" label="合計" width="72" align="right" fixed="right" class-name="col-total">
            <template #default="{ row }">
              <span
                class="total-cell"
                :class="{
                  'plan-process-num--computed':
                    (row as PlanProcessMatrixRow)._planKey === 'cutting_plan' ||
                    (row as PlanProcessMatrixRow)._planKey === 'chamfering_plan' ||
                    (row as PlanProcessMatrixRow)._planKey === 'forming_plan' ||
                    (row as PlanProcessMatrixRow)._planKey === 'plating_plan' ||
                    (row as PlanProcessMatrixRow)._planKey === 'inspection_plan' ||
                    (row as PlanProcessMatrixRow)._planKey === 'welding_plan' ||
                    (row as PlanProcessMatrixRow)._planKey === 'warehouse_plan',
                  'plan-process-num--cutting': (row as PlanProcessMatrixRow)._planKey === 'cutting_plan',
                  'plan-process-num--chamfer': (row as PlanProcessMatrixRow)._planKey === 'chamfering_plan',
                  'plan-process-num--forming': (row as PlanProcessMatrixRow)._planKey === 'forming_plan',
                  'plan-process-num--plating-plan':
                    (row as PlanProcessMatrixRow)._planKey === 'plating_plan',
                  'plan-process-num--inspection-plan':
                    (row as PlanProcessMatrixRow)._planKey === 'inspection_plan',
                  'plan-process-num--welding-plan':
                    (row as PlanProcessMatrixRow)._planKey === 'welding_plan',
                  'plan-process-num--warehouse-plan':
                    (row as PlanProcessMatrixRow)._planKey === 'warehouse_plan',
                }"
              >
                {{ formatNumberDisplay(Number(row.rowTotal ?? 0)) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </div>

      <div
        class="plan-process-card plan-process-card--trajectory-chart plan-process-card--trajectory-premium table-shell"
        aria-label="工程計画推移グラフ"
      >
        <div class="plan-process-card__head plan-process-trajectory-section-head">
          <div class="plan-process-trajectory-section-head__lead">
            <span class="plan-process-trajectory-section-head__mark" aria-hidden="true" />
            <div class="plan-process-trajectory-section-head__text">
              <h3 class="plan-process-section__title plan-process-trajectory-section-head__title">
                工程計画推移（折れ線）
              </h3>
              <p class="plan-process-trajectory-section-head__sub">各工程の日次累計を、滑らかな曲線で可視化します。</p>
            </div>
          </div>
        </div>
        <div ref="planProcessTrajectoryChartsRoot" class="plan-process-trajectory-charts-grid">
          <div
            v-for="row in planProcessTableData"
            :key="String(row._planKey)"
            class="plan-process-trajectory-chart-block"
            :class="'plan-process-trajectory-chart-block--' + row._planKey"
          >
            <div class="plan-process-trajectory-chart-block__head">
              <span class="plan-process-trajectory-chart-block__title">{{ row.item }}</span>
              <span class="plan-process-trajectory-chart-block__total" title="期間合計（合計列と同じ）">
                {{ trajectoryChartBlockTotalLabel(row) }}
              </span>
            </div>
            <div class="plan-process-trajectory-chart-wrap">
              <div
                class="plan-process-trajectory-chart"
                :data-trajectory-chart-key="row._planKey"
              />
            </div>
          </div>
        </div>
      </div>
    </section>

    <el-dialog
      v-model="prevCarryBreakdownVisible"
      :title="prevCarryBreakdownDialogTitle"
      width="720px"
      destroy-on-close
      append-to-body
      class="prev-carry-breakdown-dialog"
    >
      <div v-loading="prevCarryBreakdownLoading" class="prev-carry-breakdown-body">
        <p v-if="prevCarryBreakdownAsOfDate" class="prev-carry-breakdown-meta">
          基準日 {{ prevCarryBreakdownAsOfDate }}（在庫参照月 {{ prevCarryBreakdownMonthYm }}）
        </p>
        <el-table
          :data="prevCarryBreakdownRows"
          border
          stripe
          size="small"
          max-height="440"
          :empty-text="prevCarryBreakdownEmptyText"
        >
          <el-table-column prop="product_cd" label="製品コード" min-width="120" />
          <el-table-column prop="product_name" label="製品名" min-width="168" show-overflow-tooltip />
          <el-table-column prop="route_cd" label="ルート" width="96" />
          <el-table-column prop="quantity" label="数量" width="100" align="right">
            <template #default="{ row }">{{ formatNumberDisplay(Number(row.quantity ?? 0)) }}</template>
          </el-table-column>
        </el-table>
        <div v-if="prevCarryBreakdownRows.length" class="prev-carry-breakdown-footer">
          <span>内訳合計</span>
          <strong>{{ formatNumberDisplay(prevCarryBreakdownTotal) }}</strong>
        </div>
        <p class="prev-carry-breakdown-note">
          ※ inactive 製品は除く。メッキ・溶接・検査はルート隣接寄与、切断・面取・成型は当月末の在庫列合計、倉庫は inspection_inventory＋warehouse_inventory の合計です。
        </p>
        <p v-if="prevCarryBreakdownOpenedColKey === 'inspection'" class="prev-carry-breakdown-note">
          ※ 検査内訳は数量が 100 を超える行のみ表示し、内訳合計もその範囲で算出します。
        </p>
      </div>
    </el-dialog>

    <el-dialog
      v-model="processRunDaysDialogVisible"
      width="92%"
      top="3vh"
      destroy-on-close
      append-to-body
      class="process-run-days-dialog process-run-days-dialog--modern"
      :show-close="true"
      align-center
    >
      <template #header>
        <div class="process-run-days-dialog__header">
          <span class="process-run-days-dialog__header-title">工程別稼働日</span>
          <span class="process-run-days-dialog__header-sub">チェック＝当日を稼働</span>
        </div>
      </template>
      <div v-if="periodRange?.[0] && periodRange?.[1]" class="process-run-days-meta">
        <span class="process-run-days-meta__range">{{ periodRange[0] }} ～ {{ periodRange[1] }}</span>
      </div>
      <div class="process-run-days-matrix-wrap">
        <el-table
          :data="processRunDaysDialogRows"
          border
          size="small"
          class="process-run-days-matrix-table"
          :header-cell-class-name="processRunDaysMatrixHeaderCellClass"
        >
          <el-table-column prop="label" fixed="left" align="center" width="56">
            <template #header>
              <span class="run-cal-fixed-head">工程</span>
            </template>
          </el-table-column>
          <el-table-column
            v-for="dateCol in runCalendarDialogDates"
            :key="'cal-' + dateCol"
            align="center"
            min-width="38"
          >
            <template #header>
              <template v-for="m in [runCalendarDayMeta(dateCol)]" :key="dateCol">
                <div
                  class="run-cal-col-head"
                  :class="{ 'run-cal-col-head--weekend': m.weekend }"
                >
                  <span class="run-cal-col-head__date">{{ m.dateLine }}</span>
                  <span class="run-cal-col-head__wd">{{ m.weekdayChar }}</span>
                </div>
              </template>
            </template>
            <template #default="{ row }">
              <el-checkbox
                :model-value="dialogCalendarChecked(row, dateCol)"
                class="process-run-day-checkbox"
                @update:model-value="(v) => toggleDialogCalendar(row, dateCol, !!v)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="process-run-days-dialog__footer">
          <el-button size="small" class="ps-action-btn ps-action-btn--muted" @click="processRunDaysDialogVisible = false">
            キャンセル
          </el-button>
          <el-button
            type="primary"
            size="small"
            class="ps-action-btn ps-action-btn--primary"
            :loading="savingProcessRunDays"
            @click="saveProcessRunDaysFromDialog"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="planProcessTrajectoryHelpVisible"
      width="644px"
      append-to-body
      destroy-on-close
      align-center
      class="plan-process-trajectory-help-dialog"
    >
      <template #header>
        <div class="pth-dialog__header">
          <div class="pth-dialog__header-icon" aria-hidden="true">
            <span class="pth-dialog__header-q">?</span>
          </div>
          <div class="pth-dialog__header-text">
            <span class="pth-dialog__title">工程計画推移の計算式</span>
            <span class="pth-dialog__subtitle">日付列・合計列の算出ルール（読み取り専用）</span>
          </div>
        </div>
      </template>
      <div class="pth-dialog__body">
        <div class="pth-dialog__intro">
          <p>
            日付列の各セルは、<strong>期間開始日から当該日まで</strong>に日次増分を順に加えた累計を、各日で四捨五入した値です。
          </p>
          <p>合計列は、<strong>期間最終日</strong>のセル値です。</p>
        </div>
        <div class="pth-dialog__cards" role="list">
          <div class="pth-card pth-card--cutting" role="listitem">
            <span class="pth-card__label">切断</span>
            <p class="pth-card__formula">
              前月繰越（切断）＋Σ<sub class="pth-sub">i≦日</sub>（ 上段「工程計画」の切断[i] − 上段サマリー表の成型計画数[i] ）<br />
              <span class="pth-card__meta">計算結果が負のときは 0 とする（各日で四捨五入のうえ下限 0）</span>
            </p>
          </div>
          <div class="pth-card pth-card--chamfer" role="listitem">
            <span class="pth-card__label">面取</span>
            <p class="pth-card__formula">
              前月繰越（面取）＋Σ<sub class="pth-sub">i≦日</sub>（（上段サマリー表の面取数[i] − 上段「工程計画」の面取[i]）× 0.998）<br />
              <span class="pth-card__meta">日次係数 0.998（歩留調整）／下限：0</span>
            </p>
          </div>
          <div class="pth-card pth-card--forming" role="listitem">
            <span class="pth-card__label">成型</span>
            <p class="pth-card__formula">
              前月繰越（成型）＋Σ<sub class="pth-sub">i≦日</sub>（ 上段「工程計画」の切断[i] − 上段サマリー表の成型計画数[i] ）<br />
              <span class="pth-card__meta">下限：0</span>
            </p>
          </div>
          <div class="pth-card pth-card--plating" role="listitem">
            <span class="pth-card__label">メッキ</span>
            <p class="pth-card__formula">
              前月繰越（メッキ）＋Σ<sub class="pth-sub">i≦日</sub>（（上段サマリー表のメッキ数[i] − 上段「工程計画」のメッキ[i]）× 0.998）<br />
              <span class="pth-card__meta">日次係数 0.998（歩留調整）／工程計画は手入力を含む日次値／負の値もそのまま表示（下限なし）／稼働日は使用しません</span>
            </p>
          </div>
          <div class="pth-card pth-card--welding" role="listitem">
            <span class="pth-card__label">溶接</span>
            <p class="pth-card__formula">
              前月繰越（溶接）＋Σ<sub class="pth-sub">i≦日</sub>（（上段サマリー表の溶接数[i] − 上段「工程計画」の溶接[i]）× 0.999）<br />
              <span class="pth-card__meta">日次係数 0.999（歩留調整）／下限：0</span>
            </p>
          </div>
          <div class="pth-card pth-card--inspection" role="listitem">
            <span class="pth-card__label">検査</span>
            <p class="pth-card__formula">
              前月繰越（検査）＋Σ<sub class="pth-sub">i≦日</sub>（（上段「工程計画」のメッキ[i] ＋ 上段サマリー表の外注検査数[i] − 上段「工程計画」の検査[i]）× 0.993）<br />
              <span class="pth-card__meta">日次係数 0.993（歩留調整）／工程計画は手入力を含む日次値／下限：0</span>
            </p>
          </div>
          <div class="pth-card pth-card--warehouse" role="listitem">
            <span class="pth-card__label">倉庫</span>
            <p class="pth-card__formula">
              前月繰越（倉庫）＋Σ<sub class="pth-sub">i≦日</sub>（ 上段「工程計画」の検査[i] − 上段サマリー表の内示数[i] ＋ 上段サマリー表の外注内示数[i] ）<br />
              <span class="pth-card__meta">「工程計画」の検査は手入力を含む日次値／下限：0</span>
            </p>
          </div>
        </div>
        <div class="pth-dialog__note">
          <p>
            <strong>用語：</strong>上段「工程計画」は、試算パラメータ直下の日次計画表（工程別日当たり×運行日＋セルの手修正）です。上段サマリー表は、その上の期間別サマリー（内示・面取・メッキなどの各行の日次合計）です。
          </p>
        </div>
      </div>
      <template #footer>
        <div class="pth-dialog__footer">
          <el-button type="primary" class="ps-action-btn pth-dialog__close-btn" @click="planProcessTrajectoryHelpVisible = false">
            閉じる
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, QuestionFilled, Refresh } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import {
  getFormingDailyPlanProcessRunDays,
  getPrevCarryBreakdown,
  getPrevCarryPrePlatingWipTotal,
  getProductionSummarysList,
  putFormingDailyPlanProcessRunDays,
  type PrevCarryBreakdownItem,
} from '@/api/database'
import { fetchProductProcessBOMList } from '@/api/master/productProcessBomMaster'

type MatrixRow = Record<string, string | number>
/** 計画入力用 el-table 行（内部キー） */
type PlanProcessMatrixRow = MatrixRow & { _planKey: string }
type DailyPlanValue = {
  forming: number
  forecastQuantity: number
  outsourcedWarehouseForecastQuantity: number
  chamferingPlan: number
  swPlan: number
  platingPlan: number
  outsourcedPlatingPlan: number
  weldingPlan: number
  outsourcedWeldingPlan: number
  outsourcedWarehousePlan: number
}

function monthStartEnd(ym: string): { startDate: string; endDate: string } {
  const [yearStr, monthStr] = ym.split('-')
  const year = Number(yearStr)
  const month = Number(monthStr)
  const first = new Date(year, month - 1, 1)
  const last = new Date(year, month, 0)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return { startDate: fmt(first), endDate: fmt(last) }
}

function initialPeriodRange(): [string, string] {
  const d = new Date()
  const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  const { startDate, endDate } = monthStartEnd(ym)
  return [startDate, endDate]
}

/** 期間フィルタ（開始日・終了日）。API の startDate / endDate にそのまま渡す */
const periodRange = ref<[string, string]>(initialPeriodRange())
const loading = ref(false)
const dayPlanMap = ref<Record<string, DailyPlanValue>>({})

/** 手入力ブロック：工程列（7 列：倉庫を含み外注メッキ・外注溶接は除外） */
const processColumns = [
  { key: 'cutting', label: '切断' },
  { key: 'chamfering', label: '面取' },
  { key: 'molding', label: '成型' },
  { key: 'plating', label: 'メッキ' },
  { key: 'welding', label: '溶接' },
  { key: 'inspection', label: '検査' },
  { key: 'warehouse', label: '倉庫' },
] as const

/** 「工程別日当たり生産数」表のみ倉庫列を出さない（manualDailyPerProcess.warehouse と計算ロジックはそのまま） */
const processColumnsDailyProductionVisible = processColumns.filter((c) => c.key !== 'warehouse')

type ProcessKey = (typeof processColumns)[number]['key']

/** 前月／次月繰越数テーブルの列見出し（メッキ・溶接・検査のみ「前」を付与） */
const processColumnCarryHeaderLabel: Partial<Record<ProcessKey, string>> = {
  plating: 'メッキ前',
  welding: '溶接前',
  inspection: '検査前',
}

function carryTableColumnLabel(col: { key: ProcessKey; label: string }): string {
  return processColumnCarryHeaderLabel[col.key] ?? col.label
}

/** 前月繰越内訳 API の column パラメータ（snake_case） */
const PREV_CARRY_API_COLUMN: Record<ProcessKey, string> = {
  cutting: 'cutting',
  chamfering: 'chamfering',
  molding: 'molding',
  plating: 'plating',
  welding: 'welding',
  inspection: 'inspection',
  warehouse: 'warehouse',
}

const prevCarryBreakdownVisible = ref(false)
const prevCarryBreakdownLoading = ref(false)
const prevCarryBreakdownRows = ref<PrevCarryBreakdownItem[]>([])
const prevCarryBreakdownTotal = ref(0)
const prevCarryBreakdownAsOfDate = ref('')
const prevCarryBreakdownMonthYm = ref('')
const prevCarryBreakdownColumnLabel = ref('')
/** 内訳ダイアログで開いた工程列（検査時の注意文表示用） */
const prevCarryBreakdownOpenedColKey = ref<ProcessKey | null>(null)

const prevCarryBreakdownEmptyText = computed(() =>
  prevCarryBreakdownOpenedColKey.value === 'inspection'
    ? '該当する行がありません（検査内訳は数量が100を超える行のみ表示）'
    : '該当する行がありません（寄与数量が 0 の製品×ルートは表示しません）',
)

const prevCarryBreakdownDialogTitle = computed(() => {
  const lab = prevCarryBreakdownColumnLabel.value || '工程'
  return `前月繰越 内訳 — ${lab}`
})

/** 内訳一覧を製品名の昇順で並べる（同名は製品コードで安定ソート） */
function sortPrevCarryBreakdownItems(items: PrevCarryBreakdownItem[]): PrevCarryBreakdownItem[] {
  return [...items].sort((a, b) => {
    const na = String(a.product_name ?? '').trim()
    const nb = String(b.product_name ?? '').trim()
    const byName = na.localeCompare(nb, 'ja', { sensitivity: 'base' })
    if (byName !== 0) return byName
    return String(a.product_cd ?? '').localeCompare(String(b.product_cd ?? ''), 'ja')
  })
}

async function openPrevCarryBreakdown(colKey: ProcessKey) {
  const ym = prevCarryInventoryMonthYm.value?.trim()
  if (!ym || !/^\d{4}-\d{2}$/.test(ym)) {
    ElMessage.warning('在庫参照月を選択してから、セルをダブルクリックしてください')
    return
  }
  const col = processColumns.find((c) => c.key === colKey)
  prevCarryBreakdownColumnLabel.value = col ? carryTableColumnLabel(col) : String(colKey)
  prevCarryBreakdownOpenedColKey.value = colKey
  prevCarryBreakdownMonthYm.value = ym
  prevCarryBreakdownVisible.value = true
  prevCarryBreakdownLoading.value = true
  prevCarryBreakdownRows.value = []
  prevCarryBreakdownTotal.value = 0
  prevCarryBreakdownAsOfDate.value = ''
  try {
    const column = PREV_CARRY_API_COLUMN[colKey]
    const res = await getPrevCarryBreakdown({ month: ym, column })
    const payload = res as { data?: { items?: PrevCarryBreakdownItem[]; total?: number; as_of_date?: string } }
    const d = payload?.data
    const rows = Array.isArray(d?.items) ? d.items : []
    prevCarryBreakdownRows.value = sortPrevCarryBreakdownItems(rows)
    prevCarryBreakdownTotal.value = Number(d?.total ?? 0)
    prevCarryBreakdownAsOfDate.value = (d?.as_of_date as string) || ''
  } catch (e) {
    console.error(e)
    ElMessage.error('内訳の取得に失敗しました')
    prevCarryBreakdownVisible.value = false
  } finally {
    prevCarryBreakdownLoading.value = false
  }
}

function emptyProcessNumbers(): Record<ProcessKey, number> {
  const o = {} as Record<ProcessKey, number>
  for (const c of processColumns) o[c.key] = 0
  return o
}

const workingDays = ref(22)
const manualDailyPerProcess = reactive<Record<ProcessKey, number>>(emptyProcessNumbers())
const manualPrevMonthCarry = reactive<Record<ProcessKey, number>>(emptyProcessNumbers())
/** 前月繰越：切断・面取・成型を月末在庫で埋めるときの参照月（YYYY-MM） */
const prevCarryInventoryMonthYm = ref('')
const loadingPrevCarryInventory = ref(false)
/** 次月繰越は白セル（参照用）。算出ロジックは後から差し替え可 */
const manualNextMonthCarry = ref<Record<ProcessKey, number>>(emptyProcessNumbers())

const periodRangeShortcuts = [
  {
    text: '今月',
    value: () => {
      const d = new Date()
      const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const { startDate, endDate } = monthStartEnd(ym)
      return [new Date(startDate), new Date(endDate)] as [Date, Date]
    },
  },
  {
    text: '先月',
    value: () => {
      const d = new Date()
      d.setMonth(d.getMonth() - 1)
      const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const { startDate, endDate } = monthStartEnd(ym)
      return [new Date(startDate), new Date(endDate)] as [Date, Date]
    },
  },
]

const periodLabel = computed(() => {
  const [a, b] = periodRange.value ?? []
  if (!a || !b) return ''
  const fmt = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number)
    if (!y || !m || !d) return iso
    return `${y}年${m}月${d}日`
  }
  return `${fmt(a)} ～ ${fmt(b)}`
})

function formatNumber(value: number): string {
  return value.toLocaleString('ja-JP')
}

/** 表格セル表示：数値が 0 のときは空欄（読み取り専用セル用） */
function formatNumberDisplay(value: number): string {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return ''
  return formatNumber(n)
}

/** el-input-number：値が 0 のときは空欄表示（内部値は従来どおり 0） */
function tableInputNumberDisplay(n: number): number | undefined {
  const x = Number(n)
  if (!Number.isFinite(x) || x === 0) return undefined
  return x
}

/** 列ヘッダーを「M/D」で短く表示 */
function formatDateLabel(isoDate: string): string {
  const parts = isoDate.split('-')
  if (parts.length !== 3) return isoDate
  return `${Number(parts[1])}/${Number(parts[2])}`
}

/** 運行日ダイアログ：列ヘッダ（日付＋曜日、土日は weekend） */
function runCalendarDayMeta(isoDate: string): {
  dateLine: string
  weekdayChar: string
  weekend: boolean
} {
  const s = String(isoDate).slice(0, 10)
  const parts = s.split('-')
  if (parts.length !== 3) {
    return { dateLine: s, weekdayChar: '', weekend: false }
  }
  const y = Number(parts[0])
  const mo = Number(parts[1])
  const day = Number(parts[2])
  const dt = new Date(y, mo - 1, day, 12, 0, 0)
  const wd = dt.getDay()
  const jp = ['日', '月', '火', '水', '木', '金', '土']
  return {
    dateLine: formatDateLabel(s),
    weekdayChar: jp[wd] ?? '',
    weekend: wd === 0 || wd === 6,
  }
}

const headerCellStyle = () => ({
  background: 'var(--ps-header-bg)',
  color: 'var(--ps-header-text)',
  fontWeight: '600',
  fontSize: '10px',
  padding: '3px 2px',
  lineHeight: 1.35,
})

const cellStyle = ({ column }: { column: { property?: string } }) => {
  const base = { padding: '2px 3px', fontSize: '10px', lineHeight: 1.45 }
  if (column.property === 'rowTotal') {
    return { ...base, background: 'var(--ps-total-bg)' }
  }
  return base
}

/** 計画基準行：Element Plus は cell-class-name を el-table のみサポート（列指定は無効） */
function matrixRowClassName({ row }: { row: MatrixRow }) {
  return String(row.item) === '成型計画数' ? 'row-forming-baseline' : ''
}

function matrixCellClassName({ row, column }: { row: MatrixRow; column: { property?: string } }) {
  if (String(row.item) === '成型計画数' && column.property === 'item') {
    return 'col-item-baseline'
  }
  return ''
}

/** product_process_bom.outsourced_warehouse_process が有効な製品のみ true */
function hasOutsourcedWarehouseProcessFlag(v: unknown): boolean {
  if (v === true) return true
  if (typeof v === 'number') return v !== 0
  if (typeof v === 'string') return v === '1' || v.toLowerCase() === 'true'
  return false
}

async function loadOutsourcedWarehouseProductCdSet(): Promise<Set<string>> {
  const set = new Set<string>()
  let page = 1
  /** GET /api/master/product-process-bom の limit は最大 100（バックエンド Query le=100） */
  const limit = 100
  while (true) {
    const res = (await fetchProductProcessBOMList({ page, limit })) as {
      data?: { list?: unknown[] }
      list?: unknown[]
    }
    const list = res?.data?.list ?? res?.list ?? []
    for (const r of list as Array<{ product_cd?: unknown; outsourced_warehouse_process?: unknown }>) {
      if (!hasOutsourcedWarehouseProcessFlag(r?.outsourced_warehouse_process)) continue
      const cd = String(r?.product_cd ?? '').trim()
      if (cd) set.add(cd)
    }
    if (!list.length || list.length < limit) break
    page += 1
  }
  return set
}

const dateColumns = computed(() => Object.keys(dayPlanMap.value).sort((a, b) => a.localeCompare(b)))

/** DB に保存した工程×日的運行チェック（configured=false のときは全日運行） */
const processRunCalendarConfigured = ref(false)
const processRunCalendarMap = ref<Partial<Record<ProcessKey, Set<string>>>>({})
const processRunDaysDialogVisible = ref(false)
/** 工程計画推移：計算式ヘルプダイアログ */
const planProcessTrajectoryHelpVisible = ref(false)
const savingProcessRunDays = ref(false)
/** 運行日ダイアログ内のチェック状態（process_key → date → checked） */
const dialogRunCalendarDraft = reactive<Record<string, Record<string, boolean>>>({})

const processRunDaysDialogRows = computed(() => processColumns.filter((c) => c.key !== 'warehouse'))

const runCalendarDialogDates = computed(() => {
  const raw = periodRange.value
  if (!raw || !Array.isArray(raw) || raw.length !== 2) return []
  const startDate = String(raw[0] ?? '').slice(0, 10)
  const endDate = String(raw[1] ?? '').slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate) || !/^\d{4}-\d{2}-\d{2}$/.test(endDate)) return []
  if (startDate > endDate) return []
  return enumerateIsoDatesInclusive(startDate, endDate)
})

function enumerateIsoDatesInclusive(startIso: string, endIso: string): string[] {
  const out: string[] = []
  const cur = new Date(`${startIso.slice(0, 10)}T12:00:00`)
  const end = new Date(`${endIso.slice(0, 10)}T12:00:00`)
  if (Number.isNaN(cur.getTime()) || Number.isNaN(end.getTime()) || cur > end) return out
  while (cur <= end) {
    const y = cur.getFullYear()
    const m = String(cur.getMonth() + 1).padStart(2, '0')
    const d = String(cur.getDate()).padStart(2, '0')
    out.push(`${y}-${m}-${d}`)
    cur.setDate(cur.getDate() + 1)
  }
  return out
}

function isProcessRunOnCalendarDate(pk: ProcessKey, dateStr: string): boolean {
  if (pk === 'warehouse') {
    if (!processRunCalendarConfigured.value) return true
    const whSet = processRunCalendarMap.value.warehouse
    // 運行日設定 UI に倉庫行が無いため、倉庫用セットが無い場合は全日運行
    if (!whSet || whSet.size === 0) return true
    return whSet.has(dateStr)
  }
  if (!processRunCalendarConfigured.value) return true
  const set = processRunCalendarMap.value[pk]
  if (!set) return false
  return set.has(dateStr)
}

function draftDefaultChecked(pk: ProcessKey, dateStr: string): boolean {
  return isProcessRunOnCalendarDate(pk, dateStr)
}

function dialogCalendarChecked(row: { key: string }, dateCol: string): boolean {
  const pk = row.key as ProcessKey
  return !!dialogRunCalendarDraft[pk]?.[dateCol]
}

function toggleDialogCalendar(row: { key: string }, dateCol: string, checked: boolean) {
  const pk = row.key as ProcessKey
  if (!dialogRunCalendarDraft[pk]) dialogRunCalendarDraft[pk] = {}
  dialogRunCalendarDraft[pk][dateCol] = checked
}

/** 運行日矩阵表ヘッダセル用クラス（工程列／日付列） */
function processRunDaysMatrixHeaderCellClass(data: { column?: { property?: string } }) {
  if (data.column?.property === 'label') return 'run-cal-th-process'
  return 'run-cal-th-date'
}

/** 上表に続く計画入力行（画像どおり） */
const planProcessTableRows: { key: string; item: string }[] = [
  { key: 'cutting_plan', item: '切断' },
  { key: 'chamfering_plan', item: '面取' },
  { key: 'forming_plan', item: '成型' },
  { key: 'plating_plan', item: 'メッキ' },
  { key: 'welding_plan', item: '溶接' },
  { key: 'inspection_plan', item: '検査' },
  { key: 'warehouse_plan', item: '倉庫' },
]

const planProcessGridCells = reactive<Record<string, Record<string, number>>>({})
/** 工程計画表格の手入力（工程キー×日付）。未設定セルは日当×運行日历の自動値を表示 */
const planDailyManualOverrides = reactive<Record<string, Record<string, number>>>({})

function ensurePlanDailyManualShape() {
  const dates = new Set(dateColumns.value)
  for (const r of planProcessTableRows) {
    const row = planDailyManualOverrides[r.key]
    if (!row) continue
    for (const k of Object.keys(row)) {
      if (!dates.has(k)) delete row[k]
    }
    if (Object.keys(row).length === 0) delete planDailyManualOverrides[r.key]
  }
}

/** 工程計画表格の手修正をすべて解除し、工程別日当たり生産数×運行日历の自動値のみ表示する */
function resetDailyPlanFromManualDaily() {
  for (const k of Object.keys(planDailyManualOverrides)) delete planDailyManualOverrides[k]
  ensurePlanDailyManualShape()
  ElMessage.success('工程別日当たり生産数に基づき、工程計画表格を再計算しました')
}

function ensurePlanProcessGridShape() {
  const dates = dateColumns.value
  delete planProcessGridCells.cutting_plan
  delete planProcessGridCells.chamfering_plan
  delete planProcessGridCells.forming_plan
  delete planProcessGridCells.plating_plan
  delete planProcessGridCells.inspection_plan
  delete planProcessGridCells.welding_plan
  delete planProcessGridCells.warehouse_plan
  for (const r of planProcessTableRows) {
    if (
      r.key === 'cutting_plan' ||
      r.key === 'chamfering_plan' ||
      r.key === 'forming_plan' ||
      r.key === 'plating_plan' ||
      r.key === 'inspection_plan' ||
      r.key === 'welding_plan' ||
      r.key === 'warehouse_plan'
    )
      continue
    if (!planProcessGridCells[r.key]) planProcessGridCells[r.key] = {}
    const row = planProcessGridCells[r.key]!
    for (const d of dates) {
      if (row[d] === undefined) row[d] = 0
    }
    for (const k of Object.keys(row)) {
      if (!dates.includes(k)) delete row[k]
    }
  }
}

watch(
  () => dateColumns.value.join('\0'),
  () => {
    ensurePlanProcessGridShape()
    ensurePlanDailyManualShape()
  },
  { immediate: true },
)

/** ブラウザに手入力を保持（リロード後も復元） */
const MANUAL_DRAFT_STORAGE_KEY = 'formingDailyPlanSummary.manualDraft.v1'
type ManualDraftPayloadV1 = {
  v: 1
  workingDays: number
  manualDailyPerProcess: Record<string, number>
  manualPrevMonthCarry: Record<string, number>
  /** 前月繰越カードの在庫参照月（YYYY-MM） */
  prevCarryInventoryMonthYm?: string
  planProcessGridCells: Record<string, Record<string, number>>
  /** 工程計画表格の手修正セル */
  planDailyManualOverrides?: Record<string, Record<string, number>>
}

let suppressManualDraftPersist = false
let manualDraftPersistTimer: ReturnType<typeof setTimeout> | null = null

function clonePlanGridForStorage(): Record<string, Record<string, number>> {
  const out: Record<string, Record<string, number>> = {}
  for (const r of planProcessTableRows) {
    if (
      r.key === 'cutting_plan' ||
      r.key === 'chamfering_plan' ||
      r.key === 'forming_plan' ||
      r.key === 'plating_plan' ||
      r.key === 'inspection_plan' ||
      r.key === 'welding_plan' ||
      r.key === 'warehouse_plan'
    )
      continue
    const row = planProcessGridCells[r.key]
    if (row && Object.keys(row).length) out[r.key] = { ...row }
  }
  return out
}

function clonePlanDailyManualForStorage(): Record<string, Record<string, number>> {
  const out: Record<string, Record<string, number>> = {}
  for (const r of planProcessTableRows) {
    const row = planDailyManualOverrides[r.key]
    if (row && Object.keys(row).length) out[r.key] = { ...row }
  }
  return out
}

function saveManualDraftToStorage() {
  if (suppressManualDraftPersist) return
  try {
    const wd = Math.max(0, Math.min(999, Math.trunc(Number(workingDays.value) || 0)))
    const payload: ManualDraftPayloadV1 = {
      v: 1,
      workingDays: wd,
      manualDailyPerProcess: { ...manualDailyPerProcess },
      manualPrevMonthCarry: { ...manualPrevMonthCarry },
      prevCarryInventoryMonthYm: prevCarryInventoryMonthYm.value || undefined,
      planProcessGridCells: clonePlanGridForStorage(),
      planDailyManualOverrides: clonePlanDailyManualForStorage(),
    }
    localStorage.setItem(MANUAL_DRAFT_STORAGE_KEY, JSON.stringify(payload))
  } catch (e) {
    console.warn('手入力の保存に失敗しました', e)
  }
}

function schedulePersistManualDraft() {
  if (suppressManualDraftPersist) return
  if (manualDraftPersistTimer) clearTimeout(manualDraftPersistTimer)
  manualDraftPersistTimer = setTimeout(() => {
    manualDraftPersistTimer = null
    saveManualDraftToStorage()
  }, 300)
}

function loadManualDraftFromStorage() {
  try {
    const raw = localStorage.getItem(MANUAL_DRAFT_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw) as unknown
    if (!parsed || typeof parsed !== 'object') return
    const p = parsed as Partial<ManualDraftPayloadV1>
    if (p.v !== 1) return
    const wd = Number(p.workingDays)
    if (Number.isFinite(wd)) workingDays.value = Math.max(0, Math.min(999, Math.trunc(wd)))
    if (p.manualDailyPerProcess && typeof p.manualDailyPerProcess === 'object') {
      for (const c of processColumns) {
        const x = Number((p.manualDailyPerProcess as Record<string, unknown>)[c.key])
        if (Number.isFinite(x)) manualDailyPerProcess[c.key] = Math.max(0, Math.trunc(x))
      }
    }
    if (p.manualPrevMonthCarry && typeof p.manualPrevMonthCarry === 'object') {
      for (const c of processColumns) {
        const x = Number((p.manualPrevMonthCarry as Record<string, unknown>)[c.key])
        if (Number.isFinite(x)) manualPrevMonthCarry[c.key] = Math.max(0, Math.trunc(x))
      }
    }
    if (typeof p.prevCarryInventoryMonthYm === 'string' && /^\d{4}-\d{2}$/.test(p.prevCarryInventoryMonthYm)) {
      prevCarryInventoryMonthYm.value = p.prevCarryInventoryMonthYm
    }
    if (p.planProcessGridCells && typeof p.planProcessGridCells === 'object') {
      for (const k of Object.keys(planProcessGridCells)) delete planProcessGridCells[k]
      for (const [rowKey, cells] of Object.entries(p.planProcessGridCells)) {
        if (
          rowKey === 'cutting_plan' ||
          rowKey === 'chamfering_plan' ||
          rowKey === 'forming_plan' ||
          rowKey === 'plating_plan' ||
          rowKey === 'inspection_plan' ||
          rowKey === 'welding_plan' ||
          rowKey === 'warehouse_plan'
        )
          continue
        if (typeof cells !== 'object' || !cells) continue
        planProcessGridCells[rowKey] = {}
        for (const [date, val] of Object.entries(cells)) {
          const n = Number(val)
          planProcessGridCells[rowKey][date] = Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0
        }
      }
    }
    if (p.planDailyManualOverrides && typeof p.planDailyManualOverrides === 'object') {
      for (const k of Object.keys(planDailyManualOverrides)) delete planDailyManualOverrides[k]
      for (const [rowKey, cells] of Object.entries(p.planDailyManualOverrides)) {
        if (typeof cells !== 'object' || !cells) continue
        planDailyManualOverrides[rowKey] = {}
        for (const [date, val] of Object.entries(cells)) {
          const n = Number(val)
          if (Number.isFinite(n)) planDailyManualOverrides[rowKey][date] = Math.max(0, Math.trunc(n))
        }
      }
    }
    ensurePlanProcessGridShape()
    ensurePlanDailyManualShape()
  } catch (e) {
    console.warn('手入力の復元に失敗しました', e)
  }
}

async function onClearManualDraft() {
  try {
    await ElMessageBox.confirm(
      '試算パラメータ（稼働日・工程別日当たり・前月繰越）と工程計画表格・下段の計画手入力をすべて削除します。よろしいですか。',
      '手入力クリア',
      {
        type: 'warning',
        confirmButtonText: 'クリア',
        cancelButtonText: 'キャンセル',
      },
    )
  } catch {
    return
  }
  suppressManualDraftPersist = true
  try {
    localStorage.removeItem(MANUAL_DRAFT_STORAGE_KEY)
    workingDays.value = 22
    Object.assign(manualDailyPerProcess, emptyProcessNumbers())
    Object.assign(manualPrevMonthCarry, emptyProcessNumbers())
    prevCarryInventoryMonthYm.value = ''
    for (const k of Object.keys(planProcessGridCells)) delete planProcessGridCells[k]
    for (const k of Object.keys(planDailyManualOverrides)) delete planDailyManualOverrides[k]
    ensurePlanProcessGridShape()
    ensurePlanDailyManualShape()
    ElMessage.success('手入力をクリアしました')
  } finally {
    suppressManualDraftPersist = false
  }
}

watch(
  [
    workingDays,
    manualDailyPerProcess,
    manualPrevMonthCarry,
    prevCarryInventoryMonthYm,
    planProcessGridCells,
    planDailyManualOverrides,
  ],
  () => schedulePersistManualDraft(),
  { deep: true },
)

/** 選択月の末日の production_summarys を列合計して前月繰越へ反映。倉庫列は各行 inspection_inventory＋warehouse_inventory を加算してから合計（inactive は API 側除外） */
async function fetchPrevCarryInventoryFromSelectedMonth() {
  const ym = prevCarryInventoryMonthYm.value?.trim()
  if (!ym || !/^\d{4}-\d{2}$/.test(ym)) {
    ElMessage.warning('在庫参照月を選択してください')
    return
  }
  loadingPrevCarryInventory.value = true
  try {
    const { endDate } = monthStartEnd(ym)
    const [res, platingRes] = await Promise.all([
      getProductionSummarysList({
        page: 1,
        limit: 50000,
        startDate: endDate,
        endDate,
        excludeInactiveProducts: true,
      }),
      getPrevCarryPrePlatingWipTotal({ month: ym }),
    ])
    const rawList = res as { data?: { list?: unknown[] }; list?: unknown[] }
    const list = rawList?.data?.list ?? rawList?.list ?? []
    let sumCut = 0
    let sumChamf = 0
    let sumMolding = 0
    let sumWarehouse = 0
    for (const row of list as Array<{
      cutting_inventory?: unknown
      chamfering_inventory?: unknown
      molding_inventory?: unknown
      inspection_inventory?: unknown
      warehouse_inventory?: unknown
    }>) {
      sumCut += Number(row?.cutting_inventory ?? 0) || 0
      sumChamf += Number(row?.chamfering_inventory ?? 0) || 0
      sumMolding += Number(row?.molding_inventory ?? 0) || 0
      const inv = Number(row?.inspection_inventory ?? 0) || 0
      const wh = Number(row?.warehouse_inventory ?? 0) || 0
      sumWarehouse += inv + wh
    }
    manualPrevMonthCarry.cutting = Math.max(0, Math.round(sumCut))
    manualPrevMonthCarry.chamfering = Math.max(0, Math.round(sumChamf))
    manualPrevMonthCarry.molding = Math.max(0, Math.round(sumMolding))
    manualPrevMonthCarry.warehouse = Math.max(0, Math.round(sumWarehouse))
    const feed = (platingRes as {
      data?: { total?: unknown; pre_welding_total?: unknown; pre_inspection_total?: unknown }
    })?.data
    manualPrevMonthCarry.plating = Math.max(0, Math.round(Number(feed?.total ?? 0)))
    manualPrevMonthCarry.welding = Math.max(0, Math.round(Number(feed?.pre_welding_total ?? 0)))
    manualPrevMonthCarry.inspection = Math.max(0, Math.round(Number(feed?.pre_inspection_total ?? 0)))
    ElMessage.success(
      `${ym} 月末の在庫を反映しました（inactive 除く／切断・面取・成型は列合計、倉庫は検査在庫＋倉庫在庫、その他はルート隣接、検査列は寄与>100のみ）`,
    )
  } catch (e) {
    console.error(e)
    ElMessage.error('月末在庫の取得に失敗しました')
  } finally {
    loadingPrevCarryInventory.value = false
  }
}

function setPlanProcessCell(rowKey: string, date: string, value: number | undefined) {
  if (
    rowKey === 'cutting_plan' ||
    rowKey === 'chamfering_plan' ||
    rowKey === 'forming_plan' ||
    rowKey === 'plating_plan' ||
    rowKey === 'inspection_plan' ||
    rowKey === 'welding_plan' ||
    rowKey === 'warehouse_plan'
  )
    return
  if (!planProcessGridCells[rowKey]) planProcessGridCells[rowKey] = {}
  const n = Number(value)
  planProcessGridCells[rowKey][date] = Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0
}

function planProcessRowSum(rowKey: string): number {
  const row = planProcessGridCells[rowKey]
  if (!row) return 0
  let s = 0
  for (const d of dateColumns.value) {
    s += Number(row[d] ?? 0)
  }
  return s
}

/**
 * 切断計画（推移）:
 * 前月繰越(切断) +（工程計画表格・切断行の各日の合計累計）−（上表「成型計画数」の日次累計）
 * 各日セル = max(0, round(繰越 + Σ(工程計画切断[i] − 成型計画数[i])), i≦当該日）
 */
const cuttingPlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.cutting ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const cutPlan = mergedDailyPlanCell('cutting_plan', d)
    const forming = Number(dayPlanMap.value[d]?.forming ?? 0)
    cumNet +=
      (Number.isFinite(cutPlan) ? cutPlan : 0) - (Number.isFinite(forming) ? forming : 0)
    cells[d] = Math.max(0, Math.round(safeCarry + cumNet))
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/** 面取推移：日次増分に掛ける係数（歩留・調整） */
const CHAMFERING_TRAJECTORY_DAILY_FACTOR = 0.998

/**
 * 面取計画（推移）:
 * 前月繰越(面取) + Σ((上表「面取数」− 工程計画面取[i]) × 日次係数), i≦当該日
 * 各日セル = max(0, round(繰越 + 累計))
 */
const chamferingPlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.chamfering ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const upperChamfer = Number(dayPlanMap.value[d]?.chamferingPlan ?? 0)
    const planChamfer = mergedDailyPlanCell('chamfering_plan', d)
    const raw =
      (Number.isFinite(upperChamfer) ? upperChamfer : 0) -
      (Number.isFinite(planChamfer) ? planChamfer : 0)
    cumNet += raw * CHAMFERING_TRAJECTORY_DAILY_FACTOR
    cells[d] = Math.max(0, Math.round(safeCarry + cumNet))
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/**
 * 成型計画（推移）:
 * 前月繰越(成型) +（工程計画表格・切断行の累計）−（上表「成型計画数」の累計）
 * 各日セル = max(0, round(繰越 + Σ(工程計画切断[i] − 上表成型[i])), i≦当該日）
 */
const formingPlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.molding ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const upperForming = Number(dayPlanMap.value[d]?.forming ?? 0)
    const planCutting = mergedDailyPlanCell('cutting_plan', d)
    cumNet +=
      (Number.isFinite(planCutting) ? planCutting : 0) -
      (Number.isFinite(upperForming) ? upperForming : 0)
    cells[d] = Math.max(0, Math.round(safeCarry + cumNet))
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/** 検査推移：日次増分に掛ける係数（歩留・調整） */
const INSPECTION_TRAJECTORY_DAILY_FACTOR = 0.993

/**
 * 検査計画（推移）:
 * 前月繰越(検査) + Σ((工程計画メッキ[i] + 上表外注検査数[i] − 工程計画検査[i]) × 日次係数), i≦当該日
 * 工程計画メッキ／検査 = mergedDailyPlanCell（手改含む）。上表外注検査 = outsourcedWarehousePlan
 * 各日セル = max(0, round(繰越 + 累計))
 */
const inspectionPlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.inspection ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const planPlating = mergedDailyPlanCell('plating_plan', d)
    const outsourcedInsp = Number(dayPlanMap.value[d]?.outsourcedWarehousePlan ?? 0)
    const planInspection = mergedDailyPlanCell('inspection_plan', d)
    const raw =
      (Number.isFinite(planPlating) ? planPlating : 0) +
      (Number.isFinite(outsourcedInsp) ? outsourcedInsp : 0) -
      (Number.isFinite(planInspection) ? planInspection : 0)
    cumNet += raw * INSPECTION_TRAJECTORY_DAILY_FACTOR
    cells[d] = Math.max(0, Math.round(safeCarry + cumNet))
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/** 溶接推移：日次増分に掛ける係数（歩留・調整） */
const WELDING_TRAJECTORY_DAILY_FACTOR = 0.999

/**
 * 溶接計画（推移）:
 * 前月繰越(溶接) + Σ((上表「溶接数」− 工程計画溶接[i]) × 日次係数), i≦当該日
 * 各日セル = max(0, round(繰越 + 累計))
 */
const weldingPlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.welding ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const upperWelding = Number(dayPlanMap.value[d]?.weldingPlan ?? 0)
    const planWelding = mergedDailyPlanCell('welding_plan', d)
    const raw =
      (Number.isFinite(upperWelding) ? upperWelding : 0) -
      (Number.isFinite(planWelding) ? planWelding : 0)
    cumNet += raw * WELDING_TRAJECTORY_DAILY_FACTOR
    cells[d] = Math.max(0, Math.round(safeCarry + cumNet))
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/**
 * 倉庫計画（推移）:
 * 前月繰越(倉庫) + Σ(工程計画検査[i] − 上表「内示数」[i] + 上表「外注内示数」[i]), i≦当該日
 * 工程計画検査 = mergedDailyPlanCell('inspection_plan', d)（上段工程計画表の検査行・手改含む）
 * 各日セル = max(0, round(繰越 + 累計))
 */
const warehousePlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.warehouse ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const planInspection = mergedDailyPlanCell('inspection_plan', d)
    const forecast = Number(dayPlanMap.value[d]?.forecastQuantity ?? 0)
    const outsourcedForecast = Number(dayPlanMap.value[d]?.outsourcedWarehouseForecastQuantity ?? 0)
    cumNet +=
      (Number.isFinite(planInspection) ? planInspection : 0) -
      (Number.isFinite(forecast) ? forecast : 0) +
      (Number.isFinite(outsourcedForecast) ? outsourcedForecast : 0)
    cells[d] = Math.max(0, Math.round(safeCarry + cumNet))
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/** メッキ推移：日次増分に掛ける係数（歩留・調整） */
const PLATING_TRAJECTORY_DAILY_FACTOR = 0.998

/**
 * メッキ計画（推移）:
 * 前月繰越(メッキ) + Σ((上表メッキ数[i] − 工程計画メッキ[i]) × 日次係数), i≦当該日
 * 上表メッキ数 = dayPlanMap.platingPlan。工程計画メッキ = mergedDailyPlanCell('plating_plan')（手改含む）
 * 各日セル = round(繰越 + 累計)（負も表示・稼働日は使用しない）
 */
const platingPlanTrajectory = computed(() => {
  const dates = dateColumns.value
  const carry = Number(manualPrevMonthCarry.plating ?? 0)
  const safeCarry = Number.isFinite(carry) ? carry : 0
  const cells: Record<string, number> = {}
  let cumNet = 0
  for (const d of dates) {
    const upperPlating = Number(dayPlanMap.value[d]?.platingPlan ?? 0)
    const planPlating = mergedDailyPlanCell('plating_plan', d)
    const raw =
      (Number.isFinite(upperPlating) ? upperPlating : 0) -
      (Number.isFinite(planPlating) ? planPlating : 0)
    cumNet += raw * PLATING_TRAJECTORY_DAILY_FACTOR
    cells[d] = Math.round(safeCarry + cumNet)
  }
  const rowTotal = dates.length ? cells[dates[dates.length - 1]!]! : 0
  return { cells, rowTotal }
})

/** 次月繰越数：切断・面取・成型・メッキ（メッキ前推移の合計）・溶接・検査・倉庫は工程計画推移の期末合計を表示。他工程は従来の参照用バッファ */
function nextMonthCarryDisplayedValue(colKey: ProcessKey): number {
  if (colKey === 'cutting') return cuttingPlanTrajectory.value.rowTotal
  if (colKey === 'chamfering') return chamferingPlanTrajectory.value.rowTotal
  if (colKey === 'molding') return formingPlanTrajectory.value.rowTotal
  if (colKey === 'plating') return platingPlanTrajectory.value.rowTotal
  if (colKey === 'welding') return weldingPlanTrajectory.value.rowTotal
  if (colKey === 'inspection') return inspectionPlanTrajectory.value.rowTotal
  if (colKey === 'warehouse') return warehousePlanTrajectory.value.rowTotal
  return Number(manualNextMonthCarry.value[colKey] ?? 0)
}

/** 工程計画表格：工程別日当たり（倉庫含む）× DB 運行日历（未設定 DB は全日。倉庫は運行セット無しなら全日） */
const DAILY_PLAN_ROW_TO_PROCESS_KEY: Partial<Record<string, ProcessKey>> = {
  cutting_plan: 'cutting',
  chamfering_plan: 'chamfering',
  forming_plan: 'molding',
  plating_plan: 'plating',
  welding_plan: 'welding',
  inspection_plan: 'inspection',
  warehouse_plan: 'warehouse',
}

function baselineDailyPlanCell(planKey: string, dateStr: string): number {
  const pk = DAILY_PLAN_ROW_TO_PROCESS_KEY[planKey]
  const perDay = pk ? Number(manualDailyPerProcess[pk] ?? 0) : 0
  const safe = Number.isFinite(perDay) ? perDay : 0
  if (!pk || !isProcessRunOnCalendarDate(pk, dateStr)) return 0
  return Math.round(safe)
}

function mergedDailyPlanCell(planKey: string, dateStr: string): number {
  const row = planDailyManualOverrides[planKey]
  if (row && Object.prototype.hasOwnProperty.call(row, dateStr)) {
    const n = Number(row[dateStr])
    if (Number.isFinite(n)) return Math.max(0, Math.trunc(n))
  }
  return baselineDailyPlanCell(planKey, dateStr)
}

function setDailyPlanManualCell(planKey: string, dateStr: string, value: unknown) {
  const n = Number(value)
  if (!Number.isFinite(n)) {
    const r = planDailyManualOverrides[planKey]
    if (r) {
      delete r[dateStr]
      if (Object.keys(r).length === 0) delete planDailyManualOverrides[planKey]
    }
    return
  }
  const t = Math.max(0, Math.trunc(n))
  if (!planDailyManualOverrides[planKey]) planDailyManualOverrides[planKey] = {}
  planDailyManualOverrides[planKey][dateStr] = t
}

const planProcessDailyPlanTableData = computed<PlanProcessMatrixRow[]>(() => {
  if (dateColumns.value.length === 0) return []
  const dates = dateColumns.value
  return planProcessTableRows
    .filter((r) => r.key !== 'warehouse_plan')
    .map((r) => {
    const row = { _planKey: r.key, item: r.item, rowTotal: 0 } as PlanProcessMatrixRow
    let sum = 0
    for (const d of dates) {
      const v = mergedDailyPlanCell(r.key, d)
      row[d] = v
      sum += v
    }
    row.rowTotal = sum
    return row
  })
})

/** 工程計画推移表の工程列表示名（上段「工程計画」表の item とは別） */
function planProcessTrajectoryTableItem(rowMeta: { key: string; item: string }): string {
  const labels: Record<string, string> = {
    cutting_plan: '切断推移',
    chamfering_plan: '面取推移',
    plating_plan: 'メッキ前推移',
    welding_plan: '溶接前推移',
    inspection_plan: '検査前推移',
    warehouse_plan: '倉庫在庫推移',
  }
  return labels[rowMeta.key] ?? rowMeta.item
}

const planProcessTableData = computed<PlanProcessMatrixRow[]>(() => {
  if (dateColumns.value.length === 0) return []
  const cutTraj = cuttingPlanTrajectory.value
  const chamfTraj = chamferingPlanTrajectory.value
  const formTraj = formingPlanTrajectory.value
  const platingTraj = platingPlanTrajectory.value
  const inspTraj = inspectionPlanTrajectory.value
  const weldTraj = weldingPlanTrajectory.value
  const whTraj = warehousePlanTrajectory.value
  return planProcessTableRows.map((r) => {
    if (r.key === 'cutting_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: cutTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = cutTraj.cells[d] ?? 0
      }
      return row
    }
    if (r.key === 'chamfering_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: chamfTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = chamfTraj.cells[d] ?? 0
      }
      return row
    }
    if (r.key === 'forming_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: formTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = formTraj.cells[d] ?? 0
      }
      return row
    }
    if (r.key === 'plating_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: platingTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = platingTraj.cells[d] ?? 0
      }
      return row
    }
    if (r.key === 'inspection_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: inspTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = inspTraj.cells[d] ?? 0
      }
      return row
    }
    if (r.key === 'welding_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: weldTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = weldTraj.cells[d] ?? 0
      }
      return row
    }
    if (r.key === 'warehouse_plan') {
      const row = {
        _planKey: r.key,
        item: planProcessTrajectoryTableItem(r),
        rowTotal: whTraj.rowTotal,
      } as PlanProcessMatrixRow
      for (const d of dateColumns.value) {
        row[d] = whTraj.cells[d] ?? 0
      }
      return row
    }
    const cells = planProcessGridCells[r.key] ?? {}
    const row = { _planKey: r.key, item: planProcessTrajectoryTableItem(r), rowTotal: planProcessRowSum(r.key) } as PlanProcessMatrixRow
    for (const d of dateColumns.value) {
      row[d] = cells[d] ?? 0
    }
    return row
  })
})

/** 工程計画推移グラフ：系列色（上表の数値色と対応） */
const planProcessTrajectoryChartColors: Record<string, string> = {
  cutting_plan: '#0c4a6e',
  chamfering_plan: '#047857',
  forming_plan: '#5b21b6',
  plating_plan: '#0e7490',
  welding_plan: '#4338ca',
  inspection_plan: '#9a3412',
  warehouse_plan: '#0f766e',
}

/** 推移チャート：赤い水平目安線の Y 値（工程キーごと） */
const planProcessTrajectoryAlertY: Record<string, number> = {
  cutting_plan: 95000,
  chamfering_plan: 55000,
  plating_plan: 72000,
  welding_plan: 32000,
  inspection_plan: 60000,
  warehouse_plan: 360000,
}

const planProcessTrajectoryChartsRoot = ref<HTMLDivElement | null>(null)
const planProcessTrajectoryChartInstances = new Map<string, echarts.ECharts>()
let planProcessTrajectoryChartsResizeAttached = false

function onPlanProcessTrajectoryChartsResize() {
  for (const inst of planProcessTrajectoryChartInstances.values()) {
    inst.resize()
  }
}

function detachPlanProcessTrajectoryChartsResize() {
  if (!planProcessTrajectoryChartsResizeAttached) return
  window.removeEventListener('resize', onPlanProcessTrajectoryChartsResize)
  planProcessTrajectoryChartsResizeAttached = false
}

function disposePlanProcessTrajectoryCharts() {
  detachPlanProcessTrajectoryChartsResize()
  for (const inst of planProcessTrajectoryChartInstances.values()) {
    inst.dispose()
  }
  planProcessTrajectoryChartInstances.clear()
}

function trajectoryChartHexToRgba(hex: string, alpha: number): string {
  let h = hex.replace('#', '').trim()
  if (h.length === 3) {
    h = h
      .split('')
      .map((c) => c + c)
      .join('')
  }
  if (h.length !== 6) return `rgba(100, 116, 139, ${alpha})`
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

/** 推移チャート見出し右：期間合計 */
function trajectoryChartBlockTotalLabel(row: PlanProcessMatrixRow): string {
  const n = Number(row.rowTotal ?? 0)
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('ja-JP')
}

function buildSingleTrajectoryChartOption(dates: string[], row: PlanProcessMatrixRow): EChartsOption | null {
  if (dates.length === 0) return null
  const rowKey = String(row._planKey ?? '')
  const color = planProcessTrajectoryChartColors[rowKey] ?? '#64748b'
  const name = String(row.item ?? rowKey)
  const categories = dates.map((d) => formatDateLabel(d))
  const xRotate = dates.length > 18 ? 18 : 0
  const data = dates.map((d) => {
    const v = Number(row[d] ?? 0)
    return Number.isFinite(v) ? v : 0
  })
  const dn = dates.length
  /** 全日データラベル：角度はできるだけ水平に、フォントは読みやすく大きめ */
  const labelRotate = dn > 26 ? 18 : dn > 18 ? 10 : dn > 14 ? 4 : 0
  const topPad = dn > 26 ? 64 : dn > 18 ? 48 : dn > 14 ? 36 : 28
  const bottomPad = dn > 14 ? 42 : 30
  const labelFont = dn > 28 ? 11 : dn > 20 ? 12 : 13
  const areaTop = trajectoryChartHexToRgba(color, 0.28)
  const areaMid = trajectoryChartHexToRgba(color, 0.1)
  const areaBot = trajectoryChartHexToRgba(color, 0.02)
  const fontStack =
    'system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Meiryo", sans-serif'

  const alertY = planProcessTrajectoryAlertY[rowKey]
  const alertMarkLine =
    typeof alertY === 'number' && Number.isFinite(alertY)
      ? {
          markLine: {
            silent: true,
            symbol: 'none',
            animation: true,
            animationDuration: 720,
            lineStyle: {
              color: '#ef4444',
              width: 2,
              type: 'solid' as const,
              cap: 'round' as const,
            },
            label: {
              show: true,
              position: 'insideEndBottom' as const,
              formatter: () => `安全在庫線　${alertY.toLocaleString('ja-JP')}`,
              color: '#b91c1c',
              fontSize: 10,
              fontWeight: 800,
              fontFamily: fontStack,
              distance: 6,
              backgroundColor: 'rgba(255,255,255,0.94)',
              borderColor: 'rgba(239,68,68,0.45)',
              borderWidth: 1,
              borderRadius: 6,
              padding: [3, 8],
            },
            emphasis: { disabled: true },
            data: [{ yAxis: alertY }],
          },
        }
      : {}

  return {
    color: [color],
    textStyle: {
      fontFamily: fontStack,
      fontSize: 11,
    },
    animation: true,
    animationDuration: 820,
    animationDurationUpdate: 480,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicInOut',
    tooltip: {
      trigger: 'axis',
      confine: false,
      borderWidth: 0,
      padding: [10, 14],
      backgroundColor: 'rgba(255,255,255,0.98)',
      extraCssText:
        'box-shadow:0 12px 40px -8px rgba(15,23,42,0.14),0 0 0 1px rgba(148,163,184,0.28);border-radius:12px;backdrop-filter:blur(8px);',
      textStyle: { fontSize: 12, color: '#1e293b', fontWeight: 500 },
      axisPointer: {
        type: 'cross',
        snap: true,
        animation: true,
        animationDurationUpdate: 260,
        crossStyle: {
          color: trajectoryChartHexToRgba(color, 0.35),
          width: 1,
          type: 'dashed',
        },
        label: {
          show: true,
          precision: 0,
          backgroundColor: color,
          color: '#fff',
          fontSize: 10,
          fontWeight: 700,
          borderRadius: 6,
          padding: [3, 6],
          shadowBlur: 6,
          shadowColor: 'rgba(15,23,42,0.12)',
        },
      },
      formatter: (items: unknown) => {
        const arr = Array.isArray(items) ? items : []
        const first = arr[0] as { axisValueLabel?: string; marker?: string; seriesName?: string; value?: number } | undefined
        if (!first) return ''
        const lines = arr.map((raw: unknown) => {
          const it = raw as { marker?: string; seriesName?: string; value?: number }
          const n = Number(it.value)
          const num = Number.isFinite(n) ? n.toLocaleString('ja-JP') : '—'
          return `${it.marker ?? ''}<span style="color:#334155">${it.seriesName ?? ''}</span>　<b style="font-size:13px;font-weight:700;color:${color}">${num}</b>`
        })
        return `<div style="font-size:11px;color:#64748b;font-weight:600;margin-bottom:4px;letter-spacing:0.02em">${first.axisValueLabel ?? ''}</div>${lines.join('<br/>')}`
      },
    },
    grid: {
      left: 48,
      right: 10,
      top: topPad,
      bottom: bottomPad,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: categories,
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.45)', width: 1 } },
      axisTick: { show: false },
      axisLabel: {
        rotate: xRotate,
        fontSize: 10,
        color: '#475569',
        fontWeight: 500,
        margin: 8,
        hideOverlap: true,
      },
      splitLine: {
        show: true,
        lineStyle: { color: 'rgba(226, 232, 240, 0.65)', width: 1, type: 'solid' },
      },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        color: '#64748b',
        fontWeight: 500,
        width: 44,
        overflow: 'truncate',
        formatter: (v: number) => (Number.isFinite(v) ? v.toLocaleString('ja-JP') : ''),
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.28)', width: 1 },
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(248, 250, 252, 0.75)', 'rgba(255, 255, 255, 0.4)'],
        },
      },
    },
    series: [
      {
        name,
        type: 'line',
        smooth: 0.35,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: dates.length > 20 ? 5 : 6,
        lineStyle: {
          width: 2.75,
          color,
          cap: 'round',
          join: 'round',
          shadowBlur: 10,
          shadowColor: trajectoryChartHexToRgba(color, 0.28),
          shadowOffsetY: 3,
        },
        itemStyle: {
          color: '#fff',
          borderWidth: 2,
          borderColor: color,
          shadowBlur: 4,
          shadowColor: 'rgba(15,23,42,0.08)',
        },
        emphasis: {
          lineStyle: { width: 3.5, shadowBlur: 14, shadowColor: trajectoryChartHexToRgba(color, 0.4) },
          itemStyle: {
            color,
            borderColor: '#fff',
            borderWidth: 2.5,
            shadowBlur: 12,
            shadowColor: trajectoryChartHexToRgba(color, 0.45),
          },
          scale: 1.15,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: areaTop },
            { offset: 0.45, color: areaMid },
            { offset: 1, color: areaBot },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          distance: 2,
          rotate: labelRotate,
          fontSize: labelFont,
          color: '#1e293b',
          fontWeight: 700,
          fontFamily: fontStack,
          textBorderColor: 'rgba(255,255,255,0.92)',
          textBorderWidth: 2,
          labelLayout: { hideOverlap: true },
          formatter: (p) => {
            const raw = (p as { value?: unknown }).value
            if (raw == null) return ''
            const n = Number(Array.isArray(raw) ? raw[0] : raw)
            if (!Number.isFinite(n)) return ''
            return n.toLocaleString('ja-JP')
          },
        },
        ...alertMarkLine,
        animationDelay: (idx: number) => Math.min(idx * 14, 280),
        data,
      },
    ],
  } as EChartsOption
}

function updatePlanProcessTrajectoryCharts() {
  const root = planProcessTrajectoryChartsRoot.value
  const dates = dateColumns.value
  const rows = planProcessTableData.value
  if (!root || dates.length === 0 || rows.length === 0) {
    disposePlanProcessTrajectoryCharts()
    return
  }

  const activeKeys = new Set(rows.map((r) => String(r._planKey)))
  for (const [k, inst] of [...planProcessTrajectoryChartInstances.entries()]) {
    if (!activeKeys.has(k)) {
      inst.dispose()
      planProcessTrajectoryChartInstances.delete(k)
    }
  }

  for (const row of rows) {
    const key = String(row._planKey)
    const el = root.querySelector(
      `[data-trajectory-chart-key="${key}"]`,
    ) as HTMLDivElement | null
    const opt = buildSingleTrajectoryChartOption(dates, row)
    if (!el || !opt) continue
    let inst = planProcessTrajectoryChartInstances.get(key)
    if (!inst) {
      inst = echarts.init(el, null, { renderer: 'canvas' })
      planProcessTrajectoryChartInstances.set(key, inst)
    }
    inst.setOption(opt, { notMerge: true })
  }

  if (planProcessTrajectoryChartInstances.size > 0) {
    if (!planProcessTrajectoryChartsResizeAttached) {
      window.addEventListener('resize', onPlanProcessTrajectoryChartsResize)
      planProcessTrajectoryChartsResizeAttached = true
    }
    nextTick(() => {
      onPlanProcessTrajectoryChartsResize()
    })
  } else {
    detachPlanProcessTrajectoryChartsResize()
  }
}

watch(
  () => planProcessTableData.value,
  () => {
    nextTick(() => updatePlanProcessTrajectoryCharts())
  },
  { deep: true, flush: 'post' },
)

onBeforeUnmount(() => {
  disposePlanProcessTrajectoryCharts()
})

/** 工程計画表格：日付列は手入力（黄系） */
function planDailyPlanTableCellClassName({
  row,
  column,
}: {
  row: PlanProcessMatrixRow
  column: { property?: string }
}) {
  const p = column.property
  const isDateCol = p && /^\d{4}-\d{2}-\d{2}$/.test(String(p))
  if (isDateCol) return 'plan-process-cell--edit plan-process-cell--daily-plan'
  return ''
}

function planProcessTableCellClassName({
  row,
  column,
}: {
  row: PlanProcessMatrixRow
  column: { property?: string }
}) {
  const p = column.property
  const isDateCol = p && /^\d{4}-\d{2}-\d{2}$/.test(String(p))
  if (row._planKey === 'cutting_plan') {
    if (isDateCol) return 'plan-process-cell--traj-cutting'
    return ''
  }
  if (row._planKey === 'chamfering_plan') {
    if (isDateCol) return 'plan-process-cell--traj-chamfer'
    return ''
  }
  if (row._planKey === 'forming_plan') {
    if (isDateCol) return 'plan-process-cell--traj-forming'
    return ''
  }
  if (row._planKey === 'plating_plan') {
    if (isDateCol) return 'plan-process-cell--traj-plating'
    return ''
  }
  if (row._planKey === 'inspection_plan') {
    if (isDateCol) return 'plan-process-cell--traj-inspection'
    return ''
  }
  if (row._planKey === 'welding_plan') {
    if (isDateCol) return 'plan-process-cell--traj-welding'
    return ''
  }
  if (row._planKey === 'warehouse_plan') {
    if (isDateCol) return 'plan-process-cell--traj-warehouse'
    return ''
  }
  if (isDateCol) return 'plan-process-cell--edit'
  return ''
}

function planProcessInputCommit(row: PlanProcessMatrixRow, date: string, value: number | undefined) {
  if (
    row._planKey === 'cutting_plan' ||
    row._planKey === 'chamfering_plan' ||
    row._planKey === 'forming_plan' ||
    row._planKey === 'plating_plan' ||
    row._planKey === 'inspection_plan' ||
    row._planKey === 'welding_plan' ||
    row._planKey === 'warehouse_plan'
  ) {
    return
  }
  setPlanProcessCell(row._planKey, date, value)
}

const matrixRows = computed<MatrixRow[]>(() => {
  if (dateColumns.value.length === 0) return []
  const forecastRow: MatrixRow = { item: '内示数' }
  const outsourcedForecastRow: MatrixRow = { item: '外注内示数' }
  const formingRow: MatrixRow = { item: '成型計画数' }
  /** 成型計画数 × 1.001（日次、合計は各日の合算） */
  const cuttingRow: MatrixRow = { item: '切断数' }
  const chamferingRow: MatrixRow = { item: '面取数' }
  const swRow: MatrixRow = { item: 'SW数' }
  const kt05Row: MatrixRow = { item: 'メッキ数' }
  const kt06Row: MatrixRow = { item: '外注メッキ数' }
  const weldingRow: MatrixRow = { item: '溶接数' }
  const outsourcedWeldingRow: MatrixRow = { item: '外注溶接数' }
  /** メッキ数 + 外注メッキ数 - 外注検査数（日次で算出し合計は各日の合算） */
  const inspectionCountRow: MatrixRow = { item: '検査数' }
  const outsourcedWarehouseRow: MatrixRow = { item: '外注検査数' }
  let formingTotal = 0
  let cuttingTotal = 0
  let forecastTotal = 0
  let outsourcedForecastTotal = 0
  let chamferingTotal = 0
  let swTotal = 0
  let kt05Total = 0
  let kt06Total = 0
  let weldingTotal = 0
  let outsourcedWeldingTotal = 0
  let inspectionCountTotal = 0
  let outsourcedWarehouseTotal = 0

  for (const d of dateColumns.value) {
    const formingValue = Number(dayPlanMap.value[d]?.forming ?? 0)
    const forecastValue = Number(dayPlanMap.value[d]?.forecastQuantity ?? 0)
    const outsourcedForecastValue = Number(dayPlanMap.value[d]?.outsourcedWarehouseForecastQuantity ?? 0)
    const chamferingValue = Number(dayPlanMap.value[d]?.chamferingPlan ?? 0)
    const swValue = Number(dayPlanMap.value[d]?.swPlan ?? 0)
    const kt05Value = Number(dayPlanMap.value[d]?.platingPlan ?? 0)
    const kt06Value = Number(dayPlanMap.value[d]?.outsourcedPlatingPlan ?? 0)
    const weldingValue = Number(dayPlanMap.value[d]?.weldingPlan ?? 0)
    const outsourcedWeldingValue = Number(dayPlanMap.value[d]?.outsourcedWeldingPlan ?? 0)
    const outsourcedWarehouseValue = Number(dayPlanMap.value[d]?.outsourcedWarehousePlan ?? 0)
    const inspectionCountValue = kt05Value + kt06Value - outsourcedWarehouseValue
    const cuttingValue = Math.round(formingValue * 1.007)
    formingRow[d] = formingValue
    cuttingRow[d] = cuttingValue
    forecastRow[d] = forecastValue
    outsourcedForecastRow[d] = outsourcedForecastValue
    chamferingRow[d] = chamferingValue
    swRow[d] = swValue
    kt05Row[d] = kt05Value
    kt06Row[d] = kt06Value
    weldingRow[d] = weldingValue
    outsourcedWeldingRow[d] = outsourcedWeldingValue
    inspectionCountRow[d] = inspectionCountValue
    outsourcedWarehouseRow[d] = outsourcedWarehouseValue
    formingTotal += formingValue
    cuttingTotal += cuttingValue
    forecastTotal += forecastValue
    outsourcedForecastTotal += outsourcedForecastValue
    chamferingTotal += chamferingValue
    swTotal += swValue
    kt05Total += kt05Value
    kt06Total += kt06Value
    weldingTotal += weldingValue
    outsourcedWeldingTotal += outsourcedWeldingValue
    inspectionCountTotal += inspectionCountValue
    outsourcedWarehouseTotal += outsourcedWarehouseValue
  }

  formingRow.rowTotal = formingTotal
  cuttingRow.rowTotal = cuttingTotal
  forecastRow.rowTotal = forecastTotal
  outsourcedForecastRow.rowTotal = outsourcedForecastTotal
  chamferingRow.rowTotal = chamferingTotal
  swRow.rowTotal = swTotal
  kt05Row.rowTotal = kt05Total
  kt06Row.rowTotal = kt06Total
  weldingRow.rowTotal = weldingTotal
  outsourcedWeldingRow.rowTotal = outsourcedWeldingTotal
  inspectionCountRow.rowTotal = inspectionCountTotal
  outsourcedWarehouseRow.rowTotal = outsourcedWarehouseTotal
  return [
    forecastRow,
    outsourcedForecastRow,
    formingRow,
    cuttingRow,
    chamferingRow,
    swRow,
    kt05Row,
    kt06Row,
    weldingRow,
    outsourcedWeldingRow,
    inspectionCountRow,
    outsourcedWarehouseRow,
  ]
})

/** 試算パラメータ欄：上表「工程」行の合計 ÷ 稼働日（整数・四捨五入） */
const trialToolbarMetricConfigs = [
  { itemName: '内示数', label: '内示数' },
  { itemName: '成型計画数', label: '成型計画数' },
  { itemName: '切断数', label: '切断数' },
  { itemName: '面取数', label: '面取数' },
  { itemName: 'メッキ数', label: 'メッキ数' },
  { itemName: '溶接数', label: '溶接数' },
  { itemName: '検査数', label: '検査数' },
] as const

function perDayIntegerByRowItem(itemName: string): number {
  const wd = Number(workingDays.value)
  if (!Number.isFinite(wd) || wd <= 0) return 0
  const row = matrixRows.value.find((r) => String(r.item) === itemName)
  if (!row) return 0
  const total = Number(row.rowTotal ?? 0)
  if (!Number.isFinite(total)) return 0
  return Math.round(total / wd)
}

function exportExcel() {
  const dates = dateColumns.value
  const rows = matrixRows.value
  if (rows.length === 0 || dates.length === 0) {
    ElMessage.warning('出力するデータがありません')
    return
  }
  const headerRow = ['項目', ...dates, '合計']
  const aoa: (string | number)[][] = [headerRow]
  for (const row of rows) {
    const line: (string | number)[] = [String(row.item)]
    for (const d of dates) {
      line.push(Number(row[d] ?? 0))
    }
    line.push(Number(row.rowTotal ?? 0))
    aoa.push(line)
  }
  const worksheet = XLSX.utils.aoa_to_sheet(aoa)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '工程別計画試算')
  const [s, e] = periodRange.value ?? []
  const safe = [s, e].filter(Boolean).join('_').replace(/[^\d_-]/g, '') || 'export'
  XLSX.writeFile(workbook, `工程別計画試算_${safe}.xlsx`)
}

function normalizePeriodRange(): [string, string] | null {
  const raw = periodRange.value
  if (!raw || !Array.isArray(raw) || raw.length !== 2) return null
  const startDate = String(raw[0] ?? '').slice(0, 10)
  const endDate = String(raw[1] ?? '').slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate) || !/^\d{4}-\d{2}-\d{2}$/.test(endDate)) return null
  if (startDate > endDate) {
    ElMessage.warning('開始日は終了日以前にしてください')
    return null
  }
  return [startDate, endDate]
}

async function loadProcessRunDays() {
  const bounds = normalizePeriodRange()
  if (!bounds) return
  const [startDate, endDate] = bounds
  if (dateColumns.value.length === 0) {
    processRunCalendarConfigured.value = false
    processRunCalendarMap.value = {}
    return
  }
  try {
    const res = await getFormingDailyPlanProcessRunDays({ startDate, endDate })
    const payload = (res as {
      data?: {
        configured?: boolean
        items?: Array<{ process_key: string; dates?: string[] }>
      }
    })?.data
    const configured = payload?.configured === true
    processRunCalendarConfigured.value = configured
    if (!configured) {
      processRunCalendarMap.value = {}
      return
    }
    const items = payload?.items ?? []
    const next: Partial<Record<ProcessKey, Set<string>>> = {}
    for (const it of items) {
      const k = String(it.process_key ?? '').trim().toLowerCase() as ProcessKey
      next[k] = new Set((it.dates ?? []).map((x) => String(x).slice(0, 10)))
    }
    processRunCalendarMap.value = next
  } catch (e) {
    console.warn('運行日の取得に失敗しました', e)
    processRunCalendarConfigured.value = false
    processRunCalendarMap.value = {}
  }
}

function openProcessRunDaysDialog() {
  const dates = runCalendarDialogDates.value
  if (!dates.length) {
    ElMessage.warning('先に期間を選んでください')
    return
  }
  for (const c of processRunDaysDialogRows.value) {
    const row: Record<string, boolean> = {}
    for (const d of dates) {
      row[d] = draftDefaultChecked(c.key, d)
    }
    dialogRunCalendarDraft[c.key] = row
  }
  processRunDaysDialogVisible.value = true
}

async function saveProcessRunDaysFromDialog() {
  const bounds = normalizePeriodRange()
  if (!bounds) return
  const calDates = enumerateIsoDatesInclusive(bounds[0], bounds[1])
  savingProcessRunDays.value = true
  try {
    const items = processRunDaysDialogRows.value.map((c) => ({
      process_key: c.key,
      dates: calDates.filter((d) => dialogRunCalendarDraft[c.key]?.[d]),
    }))
    await putFormingDailyPlanProcessRunDays({
      startDate: bounds[0],
      endDate: bounds[1],
      items,
    })
    await loadProcessRunDays()
    ElMessage.success('運行日を保存しました')
    processRunDaysDialogVisible.value = false
  } catch (e) {
    console.error(e)
    ElMessage.error('保存に失敗しました')
  } finally {
    savingProcessRunDays.value = false
  }
}

/** 期間ピッカー変更時：値確定後に同一期間で再取得 */
function onPeriodFilterChange() {
  void loadData()
}

/** 明示的な「更新」：現在の期間で再取得（ピッカー以外からも呼べる） */
function reloadForCurrentPeriod() {
  void loadData()
}

async function loadData() {
  const bounds = normalizePeriodRange()
  if (!bounds) return
  const [startDate, endDate] = bounds
  loading.value = true
  try {
    const [res, outsourcedWarehouseProducts] = await Promise.all([
      getProductionSummarysList({
        page: 1,
        limit: 50000,
        startDate,
        endDate,
      }),
      loadOutsourcedWarehouseProductCdSet(),
    ])
    const raw = (res as any)?.data?.list ?? (res as any)?.list ?? []
    const byDate = new Map<string, DailyPlanValue>()

    for (const item of raw) {
      const date = String(item?.date ?? '').slice(0, 10)
      if (!date) continue
      const productCd = String(item?.product_cd ?? '').trim()
      const molding = Number(item?.molding_plan ?? 0)
      const forecast = Number(item?.forecast_quantity ?? 0)
      const chamfering = Number(item?.chamfering_plan ?? 0)
      const sw = Number(item?.sw_plan ?? 0)
      const plating = Number(item?.plating_plan ?? 0)
      const outsourcedPlating = Number(item?.outsourced_plating_plan ?? 0)
      const welding = Number(item?.welding_plan ?? 0)
      const outsourcedWelding = Number(item?.outsourced_welding_plan ?? 0)
      const outsourcedWarehouse = Number(item?.outsourced_warehouse_plan ?? 0)
      const current = byDate.get(date) ?? {
        forming: 0,
        forecastQuantity: 0,
        outsourcedWarehouseForecastQuantity: 0,
        chamferingPlan: 0,
        swPlan: 0,
        platingPlan: 0,
        outsourcedPlatingPlan: 0,
        weldingPlan: 0,
        outsourcedWeldingPlan: 0,
        outsourcedWarehousePlan: 0,
      }
      current.forming += Number.isFinite(molding) ? molding : 0
      current.forecastQuantity += Number.isFinite(forecast) ? forecast : 0
      if (productCd && outsourcedWarehouseProducts.has(productCd)) {
        current.outsourcedWarehouseForecastQuantity += Number.isFinite(forecast) ? forecast : 0
      }
      current.chamferingPlan += Number.isFinite(chamfering) ? chamfering : 0
      current.swPlan += Number.isFinite(sw) ? sw : 0
      current.platingPlan += Number.isFinite(plating) ? plating : 0
      current.outsourcedPlatingPlan += Number.isFinite(outsourcedPlating) ? outsourcedPlating : 0
      current.weldingPlan += Number.isFinite(welding) ? welding : 0
      current.outsourcedWeldingPlan += Number.isFinite(outsourcedWelding) ? outsourcedWelding : 0
      current.outsourcedWarehousePlan += Number.isFinite(outsourcedWarehouse) ? outsourcedWarehouse : 0
      byDate.set(date, current)
    }

    dayPlanMap.value = Object.fromEntries(
      Array.from(byDate.entries()).sort(([a], [b]) => a.localeCompare(b)),
    )
    await loadProcessRunDays()
  } catch (error) {
    console.error('工程別計画試算の読み込みに失敗しました', error)
    ElMessage.error('読み込みに失敗しました')
    dayPlanMap.value = {}
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void (async () => {
    suppressManualDraftPersist = true
    try {
      await loadData()
      loadManualDraftFromStorage()
    } finally {
      suppressManualDraftPersist = false
    }
  })()
})
</script>

<style scoped>
.plan-summary-page {
  /* ── Design tokens ── */
  --ps-header-bg: linear-gradient(180deg, #f1f5f9 0%, #e8edf3 100%);
  --ps-header-text: #334155;
  --ps-total-bg: #eef2f7;
  --ps-border: #cbd5e1;
  --ps-toolbar-bg: linear-gradient(145deg, #ffffff 0%, #f5f7fb 48%, #eef2f7 100%);
  --ps-cell-num: #0f172a;
  --ps-baseline-item-bg: linear-gradient(90deg, #dbeafe 0%, #eff6ff 100%);
  --ps-baseline-item-accent: #2563eb;
  --ps-manual-yellow: #fff7d6;
  --ps-manual-yellow-focus: #ffefc2;
  --ps-manual-border: #e2e8f0;
  --ps-manual-border-strong: #cbd5e1;
  --ps-manual-header-bg: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  --ps-manual-surface: #ffffff;
  --ps-manual-readonly-bg: #f8fafc;
  --ps-card-radius: 10px;
  --ps-ring: 0 0 0 1px rgba(15, 23, 42, 0.04);
  --ps-shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --ps-shadow-md: 0 4px 14px -4px rgba(15, 23, 42, 0.08);
  /* card accent colors */
  --ps-daily-accent: #f59e0b;
  --ps-prev-accent: #3b82f6;
  --ps-next-accent: #64748b;
  padding: 6px 8px 12px;
  max-width: 100%;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, 'Segoe UI', 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo', sans-serif;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 12px;
  margin-bottom: 8px;
  padding: 8px 12px;
  background:
    linear-gradient(135deg, rgba(59,130,246,0.04) 0%, transparent 50%),
    linear-gradient(180deg, #ffffff 0%, #f3f6fb 55%, #eaeff6 100%);
  border: 1px solid var(--ps-border);
  border-radius: 12px;
  box-shadow:
    var(--ps-shadow-sm),
    var(--ps-ring),
    0 6px 24px -10px rgba(15,23,42,0.09),
    inset 0 1px 0 rgba(255,255,255,0.9);
}

.toolbar-lead {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-width: 0;
}

.toolbar-title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.2;
}

.toolbar-period {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  padding: 2px 9px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(203, 213, 225, 0.85);
  border-radius: 999px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.period-range-picker {
  width: 250px;
}

.plan-summary-page :deep(.period-range-picker .el-range-editor.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(203, 213, 225, 0.9) inset;
  min-height: 30px;
  padding: 0 8px;
  background: #fff;
  transition: box-shadow 0.15s ease;
}

.plan-summary-page :deep(.period-range-picker .el-range-editor.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(59,130,246,0.5) inset !important;
}

.plan-summary-page :deep(.period-range-picker .el-range-input) {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
}

.table-shell {
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-card-radius);
  overflow: hidden;
  background: #fff;
  box-shadow:
    var(--ps-shadow-sm),
    var(--ps-ring),
    0 4px 16px -8px rgba(15,23,42,0.08);
}

/** ── ボタン共通 ── */
.plan-summary-page :deep(.ps-action-btn.el-button) {
  border-radius: 8px;
  font-weight: 700;
  letter-spacing: 0.025em;
  height: 30px;
  padding: 0 13px;
  font-size: 12px;
  transition:
    transform 0.14s cubic-bezier(0.4,0,0.2,1),
    box-shadow 0.16s ease,
    background 0.15s ease,
    border-color 0.15s ease;
}

.plan-summary-page :deep(.ps-action-btn.el-button:not(.is-disabled):hover) {
  transform: translateY(-1px);
}

.plan-summary-page :deep(.ps-action-btn.el-button:not(.is-disabled):active) {
  transform: translateY(0.5px);
}

/** 更新ボタン（青・プライマリ） */
.plan-summary-page :deep(.ps-action-btn--primary.el-button--primary) {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(37,99,235,0.35), 0 1px 2px rgba(37,99,235,0.2);
  color: #fff;
}

.plan-summary-page :deep(.ps-action-btn--primary.el-button--primary:hover) {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  box-shadow: 0 4px 14px rgba(37,99,235,0.4), 0 2px 4px rgba(37,99,235,0.22);
}

/** Excel出力ボタン（緑） */
.plan-summary-page :deep(.ps-action-btn--excel.el-button--success.is-plain) {
  border-color: rgba(5,150,105,0.45);
  color: #047857;
  background: linear-gradient(180deg, #ffffff 0%, #ecfdf5 100%);
  box-shadow: 0 1px 4px rgba(5,150,105,0.12);
}

.plan-summary-page :deep(.ps-action-btn--excel.el-button--success.is-plain:hover) {
  border-color: #10b981;
  background: #d1fae5;
  color: #065f46;
}

/** クリアボタン（オレンジ系警告） */
.plan-summary-page :deep(.ps-action-btn--ghost.el-button--warning.is-plain) {
  border-color: rgba(217,119,6,0.4);
  color: #92400e;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  box-shadow: 0 1px 4px rgba(217,119,6,0.1);
}

.plan-summary-page :deep(.ps-action-btn--ghost.el-button--warning.is-plain:hover) {
  border-color: #f59e0b;
  background: #fde68a;
  color: #78350f;
}

/** 再計算ボタン（スレート系） */
.plan-summary-page :deep(.ps-action-btn--soft) {
  border: 1px solid rgba(148,163,184,0.55);
  color: #334155;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
  box-shadow: 0 1px 3px rgba(15,23,42,0.06);
}

.plan-summary-page :deep(.ps-action-btn--soft:hover) {
  border-color: rgba(59,130,246,0.5);
  color: #1d4ed8;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
}

/** キャンセル等（ミュート） */
.plan-summary-page :deep(.ps-action-btn--muted) {
  border-color: rgba(203,213,225,0.9);
  color: #64748b;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.plan-summary-page :deep(.ps-action-btn--muted:hover) {
  border-color: #94a3b8;
  color: #334155;
  background: #f1f5f9;
}

.table-scroll {
  overflow-x: auto;
  vertical-align: middle;
}

/** 工程計画表格／推移の縦並び */
.plan-process-section {
  margin-top: 10px;
}

.plan-process-section__title {
  margin: 0;
  padding: 0;
  font-size: 12px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: 0.03em;
  line-height: 1.3;
}

.plan-process-card__head {
  padding: 6px 10px 6px 12px;
  margin: 0;
  border-bottom: 1px solid rgba(226,232,240,0.92);
  background: linear-gradient(180deg, #fcfdfe 0%, #f3f6fa 100%);
}

.plan-process-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.plan-process-section__head--solo {
  justify-content: flex-start;
}

.plan-process-section__head--traj-tools {
  justify-content: space-between;
}

.plan-summary-page :deep(.ps-traj-help-btn.el-button) {
  flex-shrink: 0;
  padding: 4px;
  min-width: 28px;
  border-radius: 999px;
}

.plan-process-trajectory-help-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.18),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.plan-process-trajectory-help-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 0;
  border-bottom: none;
}

.plan-process-trajectory-help-dialog :deep(.el-dialog__headerbtn) {
  top: 14px;
  right: 12px;
}

.plan-process-trajectory-help-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 55%, #eef2f7 100%);
}

.plan-process-trajectory-help-dialog :deep(.el-dialog__footer) {
  margin: 0;
  padding: 0;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.pth-dialog__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 44px 14px 16px;
  background: linear-gradient(125deg, #1e3a8a 0%, #2563eb 42%, #4f46e5 100%);
  color: #fff;
}

.pth-dialog__header-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.pth-dialog__header-q {
  font-size: 20px;
  font-weight: 800;
  line-height: 1;
  opacity: 0.95;
}

.pth-dialog__header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.pth-dialog__title {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1.25;
}

.pth-dialog__subtitle {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.88;
  letter-spacing: 0.02em;
}

.pth-dialog__body {
  padding: 14px 16px 16px;
  max-height: min(70vh, 520px);
  overflow-y: auto;
}

.pth-dialog__intro {
  margin: 0 0 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
  font-size: 12px;
  line-height: 1.6;
  color: #334155;
}

.pth-dialog__intro p {
  margin: 0 0 6px;
}

.pth-dialog__intro p:last-child {
  margin-bottom: 0;
}

.pth-dialog__cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pth-card {
  position: relative;
  padding: 10px 12px 10px 14px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  border-left-width: 4px;
  border-left-style: solid;
}

.pth-card__label {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #0f172a;
  margin-bottom: 4px;
}

.pth-card__formula {
  margin: 0;
  font-size: 11.5px;
  line-height: 1.58;
  color: #334155;
  font-variant-numeric: tabular-nums;
}

.pth-card__meta {
  display: inline-block;
  margin-top: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}

.pth-sub {
  font-size: 10px;
  opacity: 0.9;
}

.pth-card--cutting {
  border-left-color: #0284c7;
}

.pth-card--chamfer {
  border-left-color: #059669;
}

.pth-card--forming {
  border-left-color: #7c3aed;
}

.pth-card--plating {
  border-left-color: #0e7490;
}

.pth-card--welding {
  border-left-color: #4f46e5;
}

.pth-card--inspection {
  border-left-color: #c2410c;
}

.pth-card--warehouse {
  border-left-color: #475569;
}

.pth-dialog__note {
  margin-top: 12px;
  padding: 10px 12px;
  font-size: 11px;
  line-height: 1.55;
  color: #475569;
  background: rgba(255, 251, 235, 0.65);
  border: 1px solid rgba(251, 191, 36, 0.35);
  border-radius: 10px;
}

.pth-dialog__note p {
  margin: 0;
}

.pth-dialog__footer {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px 12px;
}

.pth-dialog__close-btn {
  min-width: 88px;
  border-radius: 8px;
  font-weight: 600;
}

.plan-process-section__head .plan-process-section__title {
  margin-bottom: 0;
}

.plan-process-section__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.process-run-days-dialog--modern {
  --prd-surface: #f8fafc;
  --prd-border: #e2e8f0;
  --prd-accent: #2563eb;
  --prd-weekend: #dc2626;
  --prd-head-bg: linear-gradient(180deg, #f1f5f9 0%, #e8eef5 100%);
}

.process-run-days-dialog--modern :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.18),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.process-run-days-dialog--modern :deep(.el-dialog__header) {
  margin: 0;
  padding: 10px 14px 8px;
  border-bottom: 1px solid var(--prd-border);
  background: var(--prd-head-bg);
}

.process-run-days-dialog__header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: flex-start;
}

.process-run-days-dialog__header-title {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #0f172a;
}

.process-run-days-dialog__header-sub {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
}

.process-run-days-meta {
  margin: 0 0 6px;
  padding: 4px 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  line-height: 1.3;
}

.process-run-days-meta__range {
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #1e40af;
}

.process-run-days-matrix-wrap {
  width: 100%;
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--prd-border);
  background: #fff;
}

.process-run-days-matrix-table {
  font-size: 11px;
}

.process-run-days-matrix-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.process-run-days-matrix-table :deep(td.el-table__cell),
.process-run-days-matrix-table :deep(th.el-table__cell) {
  padding: 2px 1px !important;
}

.process-run-days-matrix-table :deep(thead th.el-table__cell) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
  border-bottom: 1px solid #cbd5e1 !important;
}

.process-run-days-matrix-table :deep(th.run-cal-th-process) {
  vertical-align: middle;
}

.process-run-days-matrix-table :deep(th.run-cal-th-date) {
  vertical-align: middle;
}

.run-cal-fixed-head {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  letter-spacing: 0.06em;
}

.run-cal-col-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  line-height: 1.15;
  padding: 2px 0;
  min-height: 34px;
}

.run-cal-col-head__date {
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

.run-cal-col-head__wd {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}

.run-cal-col-head--weekend .run-cal-col-head__date,
.run-cal-col-head--weekend .run-cal-col-head__wd {
  color: var(--prd-weekend);
}

.process-run-day-checkbox {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.process-run-day-checkbox :deep(.el-checkbox__inner) {
  width: 15px;
  height: 15px;
  border-radius: 4px;
}

.process-run-day-checkbox :deep(.el-checkbox__inner::after) {
  height: 7px;
  left: 5px;
  width: 3px;
}

.process-run-days-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.process-run-days-dialog--modern :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid var(--prd-border);
  background: var(--prd-surface);
}

.process-run-days-dialog--modern :deep(.el-dialog__body) {
  padding: 8px 12px 10px;
  max-height: min(80vh, 900px);
  overflow: auto;
  background: var(--prd-surface);
}

.plan-process-section .plan-process-card + .plan-process-card {
  margin-top: 10px;
}

/** 試算パラメータブロック直下：工程別計画（上表と同じ matrix-table スタイル・左右固定列） */
.plan-process-card {
  margin-top: 0;
}

.plan-process-card.table-shell {
  box-shadow: var(--ps-shadow-sm), var(--ps-ring), var(--ps-shadow-md);
}

/** 推移折れ線：ツールチップが親の overflow に切れないよう可視域を広げる */
.plan-process-card--trajectory-chart.table-shell {
  overflow: visible;
}

/** 推移折れ線ブロック全体：プレミアムカード */
.plan-process-card--trajectory-premium.table-shell {
  border-radius: 14px;
  background:
    linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.99) 45%, rgba(241, 245, 249, 0.96) 100%);
  box-shadow:
    var(--ps-shadow-sm),
    var(--ps-ring),
    0 18px 48px -20px rgba(15, 23, 42, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.plan-process-card--trajectory-premium > .plan-process-card__head.plan-process-trajectory-section-head {
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.55) 0%, rgba(248, 250, 252, 0.92) 100%);
}

.plan-process-trajectory-section-head {
  padding: 8px 12px 9px 14px;
}

.plan-process-trajectory-section-head__lead {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.plan-process-trajectory-section-head__mark {
  flex-shrink: 0;
  width: 4px;
  height: 36px;
  margin-top: 2px;
  border-radius: 999px;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 38%, #0ea5e9 100%);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.plan-process-trajectory-section-head__text {
  min-width: 0;
  flex: 1;
}

.plan-process-trajectory-section-head__title {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #0f172a;
  line-height: 1.35;
}

.plan-process-trajectory-section-head__sub {
  margin: 2px 0 0;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  line-height: 1.45;
  letter-spacing: 0.02em;
}

.plan-process-trajectory-charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  padding: 14px 14px 16px;
  box-sizing: border-box;
}

.plan-process-trajectory-chart-block {
  position: relative;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.97) 0%, rgba(252, 252, 253, 0.99) 40%, rgba(248, 250, 252, 0.96) 100%);
  padding: 10px 12px 8px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.035),
    0 14px 36px -16px rgba(15, 23, 42, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.88);
  overflow: hidden;
  transition:
    box-shadow 0.28s cubic-bezier(0.4, 0, 0.2, 1),
    border-color 0.25s ease,
    transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.plan-process-trajectory-chart-block::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  opacity: 0;
  background: radial-gradient(120% 80% at 100% 0%, rgba(99, 102, 241, 0.06), transparent 55%);
  transition: opacity 0.28s ease;
}

.plan-process-trajectory-chart-block:hover {
  border-color: rgba(148, 163, 184, 0.5);
  box-shadow:
    0 2px 6px rgba(15, 23, 42, 0.05),
    0 20px 44px -18px rgba(15, 23, 42, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
}

.plan-process-trajectory-chart-block:hover::before {
  opacity: 1;
}

.plan-process-trajectory-chart-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
  min-width: 0;
}

.plan-process-trajectory-chart-block__title {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: 0.03em;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-process-trajectory-chart-block__total {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #475569;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

.plan-process-trajectory-chart-block--cutting_plan {
  border-left: 3px solid #0c4a6e;
}

.plan-process-trajectory-chart-block--chamfering_plan {
  border-left: 3px solid #047857;
}

.plan-process-trajectory-chart-block--forming_plan {
  border-left: 3px solid #5b21b6;
}

.plan-process-trajectory-chart-block--plating_plan {
  border-left: 3px solid #0e7490;
}

.plan-process-trajectory-chart-block--welding_plan {
  border-left: 3px solid #4338ca;
}

.plan-process-trajectory-chart-block--inspection_plan {
  border-left: 3px solid #9a3412;
}

.plan-process-trajectory-chart-block--warehouse_plan {
  border-left: 3px solid #0f766e;
}

.plan-process-trajectory-chart-block--cutting_plan .plan-process-trajectory-chart-block__total {
  color: #0c4a6e;
  border-color: rgba(12, 74, 110, 0.2);
  background: linear-gradient(180deg, rgba(240, 249, 255, 0.95), rgba(224, 242, 254, 0.65));
}

.plan-process-trajectory-chart-block--chamfering_plan .plan-process-trajectory-chart-block__total {
  color: #047857;
  border-color: rgba(4, 120, 87, 0.2);
  background: linear-gradient(180deg, rgba(236, 253, 245, 0.95), rgba(209, 250, 229, 0.65));
}

.plan-process-trajectory-chart-block--forming_plan .plan-process-trajectory-chart-block__total {
  color: #5b21b6;
  border-color: rgba(91, 33, 182, 0.2);
  background: linear-gradient(180deg, rgba(245, 243, 255, 0.95), rgba(237, 233, 254, 0.65));
}

.plan-process-trajectory-chart-block--plating_plan .plan-process-trajectory-chart-block__total {
  color: #0e7490;
  border-color: rgba(14, 116, 144, 0.2);
  background: linear-gradient(180deg, rgba(236, 254, 255, 0.95), rgba(207, 250, 254, 0.65));
}

.plan-process-trajectory-chart-block--welding_plan .plan-process-trajectory-chart-block__total {
  color: #4338ca;
  border-color: rgba(67, 56, 202, 0.2);
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.95), rgba(224, 231, 255, 0.65));
}

.plan-process-trajectory-chart-block--inspection_plan .plan-process-trajectory-chart-block__total {
  color: #9a3412;
  border-color: rgba(154, 52, 18, 0.2);
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.95), rgba(255, 237, 213, 0.65));
}

.plan-process-trajectory-chart-block--warehouse_plan .plan-process-trajectory-chart-block__total {
  color: #0f766e;
  border-color: rgba(15, 118, 110, 0.2);
  background: linear-gradient(180deg, rgba(240, 253, 250, 0.95), rgba(204, 251, 241, 0.65));
}

.plan-process-trajectory-chart-wrap {
  border-radius: 10px;
  padding: 4px 2px 2px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.65) 0%, rgba(255, 255, 255, 0.5) 100%);
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.65);
}

.plan-process-trajectory-chart {
  width: 100%;
  height: 248px;
  min-height: 200px;
  box-sizing: border-box;
}

/** 工程別計画テーブル全体：上表 matrix-table（11px）より 1 段階小さく統一 */
.plan-process-card .matrix-table {
  font-size: 10px;
}

.plan-process-card .matrix-table :deep(.total-cell),
.plan-process-card .matrix-table :deep(.num-cell) {
  font-size: 10px;
}

.plan-process-card .matrix-table :deep(.col-item .cell) {
  font-size: 10px;
}

.plan-process-card .matrix-table :deep(td.plan-process-cell--edit.el-table__cell) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--ps-manual-yellow) 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--edit.el-table__cell) {
  background: linear-gradient(180deg, #fff9e8 0%, #fff3cd 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--edit.el-table__cell) {
  background: linear-gradient(180deg, #fff7d6 0%, var(--ps-manual-yellow-focus) 100%) !important;
}

/** 切断計画：算出セル（青系・推移・読み取り専用） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-cutting.el-table__cell) {
  background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-cutting.el-table__cell) {
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-cutting.el-table__cell) {
  background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 100%) !important;
}

/** 面取計画：算出セル（緑系・切断行と区別） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-chamfer.el-table__cell) {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-chamfer.el-table__cell) {
  background: linear-gradient(180deg, #ecfdf5 0%, #a7f3d0 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-chamfer.el-table__cell) {
  background: linear-gradient(180deg, #d1fae5 0%, #6ee7b7 100%) !important;
}

.plan-process-num--computed {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

/** 工程計画推移テーブルのみ：数字は通常字重（上の工程計画表は据え置き） */
.plan-process-card--trajectory-matrix .matrix-table :deep(.plan-process-num--computed),
.plan-process-card--trajectory-matrix .matrix-table :deep(.num-cell),
.plan-process-card--trajectory-matrix .matrix-table :deep(.total-cell) {
  font-weight: 400;
}

.plan-process-card--trajectory-matrix .matrix-table :deep(.plan-process-input-inner .el-input__inner) {
  font-weight: 400;
}

.plan-process-num--cutting {
  color: #0c4a6e;
}

.plan-process-num--chamfer {
  color: #047857;
}

.plan-process-num--forming {
  color: #5b21b6;
}

.plan-process-num--inspection-plan {
  color: #9a3412;
}

.plan-process-num--plating-plan {
  color: #0e7490;
}

.plan-process-num--welding-plan {
  color: #4338ca;
}

.plan-process-num--warehouse-plan {
  color: #0f766e;
}

/** メッキ計画：算出セル（青緑系・(上表メッキ数−工程計画メッキ)×0.998 の累計） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-plating.el-table__cell) {
  background: linear-gradient(180deg, #ecfeff 0%, #cffafe 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-plating.el-table__cell) {
  background: linear-gradient(180deg, #ecfeff 0%, #a5f3fc 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-plating.el-table__cell) {
  background: linear-gradient(180deg, #cffafe 0%, #67e8f9 100%) !important;
}

/** 検査計画：算出セル（橙系・(工程計画メッキ＋外注検査−工程計画検査)×0.993 の累計） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-inspection.el-table__cell) {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-inspection.el-table__cell) {
  background: linear-gradient(180deg, #fff7ed 0%, #fed7aa 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-inspection.el-table__cell) {
  background: linear-gradient(180deg, #ffedd5 0%, #fdba74 100%) !important;
}

/** 溶接計画：算出セル（紫系・インディゴ寄り） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-welding.el-table__cell) {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-welding.el-table__cell) {
  background: linear-gradient(180deg, #eef2ff 0%, #c7d2fe 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-welding.el-table__cell) {
  background: linear-gradient(180deg, #e0e7ff 0%, #a5b4fc 100%) !important;
}

/** 倉庫計画：算出セル（スレート系・面取の緑系と区別） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-warehouse.el-table__cell) {
  background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-warehouse.el-table__cell) {
  background: linear-gradient(180deg, #f1f5f9 0%, #cbd5e1 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-warehouse.el-table__cell) {
  background: linear-gradient(180deg, #e2e8f0 0%, #94a3b8 100%) !important;
}

/** 成型計画：算出セル（紫系・他行と区別） */
.plan-process-card .matrix-table :deep(td.plan-process-cell--traj-forming.el-table__cell) {
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%) !important;
}

.plan-process-card .matrix-table :deep(tr.el-table__row--striped td.plan-process-cell--traj-forming.el-table__cell) {
  background: linear-gradient(180deg, #f5f3ff 0%, #ddd6fe 100%) !important;
}

.plan-process-card .matrix-table :deep(tr:hover > td.plan-process-cell--traj-forming.el-table__cell) {
  background: linear-gradient(180deg, #ede9fe 0%, #c4b5fd 100%) !important;
}

.plan-process-card .matrix-table :deep(.plan-process-input-inner.el-input-number) {
  width: 100%;
}

.plan-process-card .matrix-table :deep(.plan-process-input-inner .el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
  padding: 0 2px;
  min-height: 22px;
  border-radius: 4px;
}

.plan-process-card .matrix-table :deep(.plan-process-input-inner .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.45) inset !important;
}

.plan-process-card .matrix-table :deep(.plan-process-input-inner .el-input__inner) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 10px;
  font-weight: 600;
  color: #0f172a;
}

.plan-process-card .matrix-table :deep(.plan-process-input-inner--daily .el-input__wrapper) {
  padding: 0 1px;
}

.matrix-table {
  width: max-content;
  min-width: 100%;
  --el-table-header-bg-color: transparent;
  --el-table-border-color: var(--ps-border);
  font-size: 10px;
}

.matrix-table :deep(.el-table__header-wrapper th.el-table__cell) {
  border-color: var(--ps-border) !important;
}

.matrix-table :deep(.el-table__body-wrapper td.el-table__cell) {
  border-color: rgba(226, 232, 240, 0.95) !important;
}

.matrix-table :deep(.el-table__header .cell),
.matrix-table :deep(.el-table__body .cell) {
  padding-left: 3px;
  padding-right: 3px;
  line-height: 1.42;
}

.matrix-table :deep(.el-table__row--striped td) {
  background: #f7f9fc !important;
}

/** 計画基準行：斑马纹 hover 的 !important 会压过内联 style，需整行用更高优先级覆盖 */
.matrix-table :deep(tr.row-forming-baseline > td.el-table__cell) {
  background: #f0f9ff !important;
}

.matrix-table :deep(tr.row-forming-baseline > td.col-item-baseline.el-table__cell) {
  background: var(--ps-baseline-item-bg) !important;
  box-shadow: inset 3px 0 0 var(--ps-baseline-item-accent);
}

.matrix-table :deep(tr.row-forming-baseline > td.col-total.el-table__cell) {
  background: #e0f2fe !important;
}

.matrix-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #eef6ff !important;
}

.matrix-table :deep(tr.row-forming-baseline:hover > td.el-table__cell) {
  background: #dbeafe !important;
}

.matrix-table :deep(tr.row-forming-baseline:hover > td.col-item-baseline.el-table__cell) {
  background: linear-gradient(90deg, #bfdbfe 0%, #e0f2fe 100%) !important;
}

.matrix-table :deep(tr.row-forming-baseline:hover > td.col-total.el-table__cell) {
  background: #bae6fd !important;
}

.matrix-table :deep(.col-total) {
  font-variant-numeric: tabular-nums;
}

.matrix-table :deep(.col-item .cell) {
  font-size: 10px;
  font-weight: 600;
  color: #1e293b;
}

.matrix-table :deep(tr.row-forming-baseline > td.col-item-baseline .cell) {
  font-weight: 700;
  color: #1e3a8a;
}

.matrix-table :deep(.col-num .cell) {
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}

.num-cell {
  font-variant-numeric: tabular-nums;
  color: var(--ps-cell-num);
  font-size: 10px;
}

.total-cell {
  font-weight: 600;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  font-size: 10px;
}

/* ----- 手入力：再レイアウト・モダン UI ----- */
.manual-sheet {
  --ms-radius: 12px;
  --ms-gap: 8px;
  --ms-card-radius: 11px;
  margin-top: 8px;
  padding: 10px 12px 12px;
  background:
    radial-gradient(130% 90% at 100% 0%, rgba(59,130,246,0.06) 0%, transparent 52%),
    radial-gradient(90% 60% at 0% 100%, rgba(99,102,241,0.045) 0%, transparent 48%),
    linear-gradient(168deg, #f4f6fa 0%, #eef1f7 42%, #e8edf5 100%);
  border: 1px solid rgba(148,163,184,0.38);
  border-radius: var(--ms-radius);
  box-shadow:
    0 4px 20px -10px rgba(15,23,42,0.14),
    0 1px 0 rgba(255,255,255,0.9) inset,
    var(--ps-ring);
  max-width: 100%;
  box-sizing: border-box;
}

.manual-sheet__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
  margin-bottom: 8px;
}

.manual-sheet__header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.manual-sheet__header-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
}

.manual-sheet__subtitle {
  font-size: 10px;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.02em;
  line-height: 1.3;
}

.manual-sheet__badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #312e81;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 55%, #c7d2fe 160%);
  border: 1px solid rgba(129,140,248,0.5);
  border-radius: 999px;
  box-shadow:
    0 1px 2px rgba(49,46,129,0.07),
    inset 0 1px 0 rgba(255,255,255,0.88);
}

.manual-sheet__badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  box-shadow: 0 0 0 2px rgba(99,102,241,0.22);
}

.manual-sheet__metrics-band {
  margin-bottom: 8px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.92);
  border-radius: 9px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.88) inset,
    0 2px 10px -4px rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(8px);
}

.manual-sheet__metrics-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 6px 8px;
}

@media (max-width: 720px) {
  .manual-sheet__metrics-inner {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 4px;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
  }

  .manual-sheet__metric {
    flex-shrink: 0;
  }
}

.manual-sheet__metric {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  padding: 4px 6px 5px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.manual-sheet__metric:hover {
  border-color: rgba(129, 140, 248, 0.45);
  box-shadow: 0 2px 10px -4px rgba(59, 130, 246, 0.2);
}

.manual-sheet__metric-label {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  line-height: 1.2;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.manual-sheet__metric-input {
  width: 76px;
  max-width: 100%;
}

.manual-sheet :deep(.manual-sheet__metric-input .el-input__wrapper) {
  padding: 0 6px;
  min-height: 26px;
  background: linear-gradient(180deg, #fafbfc 0%, #f8fafc 100%) !important;
  box-shadow: 0 0 0 1px #e2e8f0 inset !important;
  border-radius: 7px;
  transition: box-shadow 0.15s ease;
}

.manual-sheet :deep(.manual-sheet__metric-input .el-input__inner) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 10px;
  font-weight: 700;
  color: #0f172a;
  cursor: default;
}

.manual-sheet__working {
  display: inline-flex;
  align-items: stretch;
  border: 1px solid rgba(148,163,184,0.48);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  height: 30px;
  box-shadow:
    0 1px 6px -2px rgba(15,23,42,0.09),
    inset 0 1px 0 rgba(255,255,255,0.95);
  flex-shrink: 0;
}

.manual-sheet__working-label {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  min-width: 52px;
  font-size: 10px;
  font-weight: 700;
  color: #475569;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-right: 1px solid var(--ps-manual-border);
  letter-spacing: 0.02em;
}

.manual-sheet__working-value {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  padding: 0 6px;
}

.manual-sheet__cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ms-gap);
  align-items: start;
}

@media (max-width: 1100px) {
  .manual-sheet__cards {
    grid-template-columns: 1fr;
  }
}

/* ── manual-card 基底 ── */
.manual-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: rgba(255,255,255,0.96);
  border: 1px solid rgba(226,232,240,0.88);
  border-top: 3px solid var(--ps-daily-accent);
  border-radius: var(--ms-card-radius);
  box-shadow:
    0 4px 22px -12px rgba(15,23,42,0.14),
    0 1px 0 rgba(255,255,255,0.95) inset;
  overflow: hidden;
  transition:
    box-shadow 0.22s cubic-bezier(0.4,0,0.2,1),
    border-color 0.2s ease,
    transform 0.22s cubic-bezier(0.4,0,0.2,1);
}

.manual-card:hover {
  border-color: rgba(148,163,184,0.7);
  box-shadow:
    0 10px 32px -12px rgba(15,23,42,0.18),
    0 1px 0 rgba(255,255,255,0.95) inset;
  transform: translateY(-1px);
}

/** 色別 top-border */
.manual-card--daily { border-top-color: #f59e0b; }
.manual-card--prev  { border-top-color: #3b82f6; }
.manual-card--muted { border-top-color: #94a3b8; }

.manual-card--muted {
  background: rgba(248,250,252,0.98);
  border-color: rgba(203,213,225,0.7);
}

.manual-card--muted .manual-card__title { color: #475569; }

/* カードタイトル（共通・行高を3カードで統一） */
.manual-card__title {
  position: relative;
  margin: 0;
  padding: 5px 10px 5px 13px;
  min-height: 30px;
  box-sizing: border-box;
  font-size: 11px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.03em;
  line-height: 1.25;
  border-bottom: 1px solid rgba(226,232,240,0.9);
  background: linear-gradient(90deg, rgba(59,130,246,0.06) 0%, rgba(255,255,255,0) 55%);
  display: flex;
  align-items: center;
  gap: 7px;
}

.manual-card__title::before {
  content: '';
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(145deg, #3b82f6, #6366f1);
  box-shadow: 0 0 0 2px rgba(59,130,246,0.22);
}

/* daily card accent */
.manual-card--daily .manual-card__title {
  background: linear-gradient(90deg, rgba(245,158,11,0.08) 0%, rgba(255,255,255,0) 55%);
}
.manual-card--daily .manual-card__title::before {
  background: linear-gradient(145deg, #f59e0b, #d97706);
  box-shadow: 0 0 0 2px rgba(245,158,11,0.22);
}

/* prev card accent */
.manual-card--prev .manual-card__title {
  background: linear-gradient(90deg, rgba(59,130,246,0.09) 0%, rgba(255,255,255,0) 55%);
}
.manual-card--prev .manual-card__title::before {
  background: linear-gradient(145deg, #3b82f6, #2563eb);
  box-shadow: 0 0 0 2px rgba(59,130,246,0.24);
}

/* muted card accent */
.manual-card--muted .manual-card__title {
  background: linear-gradient(90deg, rgba(148,163,184,0.1) 0%, rgba(255,255,255,0) 55%);
}
.manual-card--muted .manual-card__title::before {
  background: #94a3b8;
  box-shadow: 0 0 0 2px rgba(148,163,184,0.24);
}

.manual-card__title--split {
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 8px 10px;
  align-items: center;
  padding-top: 3px;
  padding-bottom: 3px;
}

@media (max-width: 520px) {
  .manual-card__title--split {
    flex-wrap: wrap;
    row-gap: 6px;
  }
}

.manual-card__title--split::before {
  display: none;
}

.manual-card__title-lead {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.manual-card__title-lead::before {
  content: '';
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(145deg, #3b82f6, #2563eb);
  box-shadow: 0 0 0 2px rgba(59,130,246,0.24);
}

.manual-card__carry-toolbar {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 5px 6px;
  flex-shrink: 0;
  padding-right: 4px;
}

.manual-card__carry-label {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.02em;
  white-space: nowrap;
  line-height: 1.2;
}

.manual-card__month-picker {
  width: 108px;
  flex-shrink: 0;
}

/* 在庫参照月：コンパクト高さ（タイトル行と日当たりカードに揃える） */
.manual-sheet :deep(.manual-card__month-picker .el-input__wrapper) {
  min-height: 24px !important;
  height: 24px;
  padding: 0 6px;
  border-radius: 6px;
}

.manual-sheet :deep(.manual-card__month-picker .el-input__inner) {
  height: 22px;
  line-height: 22px;
  font-size: 11px;
  font-weight: 600;
}

.manual-sheet :deep(.manual-card__month-picker .el-input__prefix) {
  margin-right: 2px;
}

.manual-sheet :deep(.manual-card__month-picker .el-input__prefix-inner > :last-child) {
  margin-right: 0;
}

.manual-sheet :deep(.manual-card__month-picker .el-input__suffix-inner > :first-child) {
  margin-left: 0;
}

.manual-card__body {
  padding: 0;
}

.manual-grid {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  background: transparent;
}

.manual-grid th,
.manual-grid td {
  border-right: 1px solid rgba(226,232,240,0.9);
  border-bottom: 1px solid rgba(226,232,240,0.9);
  text-align: center;
  vertical-align: middle;
  font-size: 11px;
}

.manual-grid th:last-child,
.manual-grid td:last-child {
  border-right: none;
}

.manual-grid thead tr:first-child th {
  border-top: none;
}

.manual-grid th {
  padding: 5px 3px;
  font-weight: 700;
  font-size: 10px;
  color: #475569;
  background: linear-gradient(180deg, #f8fafc 0%, #f0f4f8 100%);
  letter-spacing: 0.02em;
}

.manual-grid td {
  padding: 1px 2px;
  height: 30px;
}

.manual-card--daily .manual-grid th {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  color: #78350f;
}

.manual-card--prev .manual-grid th {
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  color: #1e40af;
}

.manual-card--muted .manual-grid th {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  color: #64748b;
}

.manual-sheet__cell--yellow {
  background: linear-gradient(180deg, #fffbeb 0%, var(--ps-manual-yellow) 100%);
  transition: background 0.15s ease;
}

.manual-sheet__cell--yellow:focus-within {
  background: linear-gradient(180deg, #fff7d6 0%, var(--ps-manual-yellow-focus) 100%);
}

.manual-sheet__cell--prev-carry {
  cursor: pointer;
}

.manual-sheet__cell--prev-carry:hover {
  outline: 1px dashed rgba(59, 130, 246, 0.4);
  outline-offset: -1px;
}

.prev-carry-breakdown-dialog.el-dialog {
  border-radius: 11px;
  overflow: hidden;
  box-shadow:
    0 22px 44px -14px rgba(15, 23, 42, 0.16),
    0 0 0 1px rgba(15, 23, 42, 0.05);
}

.prev-carry-breakdown-dialog .el-dialog__header {
  padding: 8px 12px 6px;
  margin: 0;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc 0%, #f1f5f9 100%);
}

.prev-carry-breakdown-dialog .el-dialog__body {
  padding: 8px 10px 10px;
}

.prev-carry-breakdown-meta {
  margin: 0 0 6px;
  font-size: 11px;
  color: #64748b;
}

.prev-carry-breakdown-footer {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
  color: #334155;
}

.prev-carry-breakdown-footer strong {
  font-variant-numeric: tabular-nums;
  font-size: 15px;
  color: #0f172a;
}

.prev-carry-breakdown-note {
  margin: 12px 0 0;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.45;
}

.manual-sheet__cell--readonly {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  color: #1e293b;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: -0.01em;
}

.manual-sheet :deep(.manual-input-inner.el-input-number) {
  width: 100%;
}

.manual-sheet :deep(.manual-input-inner .el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
  padding: 0 2px;
  min-height: 24px;
  border-radius: 5px;
}

.manual-sheet :deep(.manual-input-inner .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.45) inset !important;
}

.manual-sheet :deep(.manual-input-inner .el-input__inner) {
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-size: 10px;
  font-weight: 700;
  color: #0f172a;
}

/* ── 全局微动画 ── */
@keyframes ps-fade-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.plan-summary-page > .toolbar {
  animation: ps-fade-in 0.28s cubic-bezier(0.4,0,0.2,1) both;
}

.plan-summary-page > .table-shell {
  animation: ps-fade-in 0.32s cubic-bezier(0.4,0,0.2,1) 0.04s both;
}

.manual-sheet {
  animation: ps-fade-in 0.34s cubic-bezier(0.4,0,0.2,1) 0.08s both;
}

.plan-process-section {
  animation: ps-fade-in 0.36s cubic-bezier(0.4,0,0.2,1) 0.12s both;
}

/* Matrix table 行 hover 过渡 */
.matrix-table :deep(.el-table__body tr > td.el-table__cell) {
  transition: background 0.13s ease;
}

/* manual-card 中 table row hover 效果 */
.manual-grid td {
  transition: background 0.12s ease;
}

/* 月末在庫反映：ツールバー内は高さを抑え、タイトル行と揃える */
.plan-summary-page :deep(.manual-card__carry-toolbar .ps-action-btn--carry.el-button) {
  height: 24px;
  min-height: 24px;
  padding: 0 9px;
  font-size: 11px;
  letter-spacing: 0.02em;
}

.manual-card--prev :deep(.manual-card__carry-toolbar .ps-action-btn--carry.el-button--primary) {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  box-shadow: 0 1px 4px rgba(37,99,235,0.28);
  color: #fff;
}

.manual-card--prev :deep(.manual-card__carry-toolbar .ps-action-btn--carry.el-button--primary:hover) {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  box-shadow: 0 3px 10px rgba(37,99,235,0.34);
  transform: translateY(-0.5px);
}

/* metric-input focus outline */
.manual-sheet :deep(.manual-sheet__metric-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(99,102,241,0.4) inset !important;
}

/* manual-grid td の番号：フォント統一 */
.manual-sheet__cell--readonly {
  letter-spacing: -0.01em;
}
</style>
