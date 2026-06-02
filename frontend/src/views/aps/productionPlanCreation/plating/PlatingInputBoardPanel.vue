<template>
  <div class="plating-input-board-root" :class="`plating-input-board-root--${mode}`">
  <el-card shadow="never" class="pp-card pp-card--board">
    <template #header>
      <div class="section-head-row section-head-row--board section-head-row--one-line">
        <span class="pp-card-title">メッキ投入ボード</span>
        <div class="board-head-period">
          <span class="board-head-period__label">表示期間</span>
          <div class="board-head-period__group">
            <el-date-picker
              v-model="boardFilterDateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="〜"
              start-placeholder="開始"
              end-placeholder="終了"
              size="small"
              class="board-head-period__picker"
              :disabled="boardPeriodFilterLoading"
              :clearable="false"
              @change="onBoardViewRangeChange"
            />
            <div class="board-head-period__nav">
              <el-button
                type="default"
                size="small"
                :icon="ArrowLeft"
                title="前日"
                class="board-head-period__nav-btn instr-btn instr-btn--prev"
                :disabled="boardPeriodFilterLoading"
                @click="shiftBoardViewRange(-1)"
              />
              <el-button
                type="default"
                size="small"
                class="board-head-period__today instr-btn instr-btn--today"
                :disabled="boardPeriodFilterLoading"
                @click="setBoardViewRangeToday"
              >
                今日
              </el-button>
              <el-button
                type="default"
                size="small"
                :icon="ArrowRight"
                title="翌日"
                class="board-head-period__nav-btn instr-btn instr-btn--next"
                :disabled="boardPeriodFilterLoading"
                @click="shiftBoardViewRange(1)"
              />
            </div>
          </div>
        </div>
        <div class="toolbar-inline board-head-toolbar">
            <el-button
              size="small"
              type="default"
              class="board-act-btn board-act-btn--print instr-btn instr-btn--print"
              :icon="Printer"
              :disabled="!layoutBoardReady"
              @click="openPrintScheduleDialog"
            >
              印刷
            </el-button>
            <el-button
              size="small"
              class="instr-btn instr-btn--refresh"
              :icon="Refresh"
              :loading="boardTableLoading"
              @click="reloadBoardView"
            >
              更新
            </el-button>
        </div>
      </div>
    </template>

    <div class="kpi-grid">
      <div class="kpi-chip">
        <span class="kpi-chip-l">総治具数</span>
        <span class="kpi-chip-v">{{ kpi.totalSlots }}</span>
      </div>
      <div class="kpi-chip">
        <span class="kpi-chip-l">使用中</span>
        <span class="kpi-chip-v">{{ kpi.usedSlots }}</span>
      </div>
      <div class="kpi-chip">
        <span class="kpi-chip-l">空き枠</span>
        <span class="kpi-chip-v">{{ kpi.remainSlots }}</span>
      </div>
      <div class="kpi-chip">
        <span class="kpi-chip-l">充填率</span>
        <span class="kpi-chip-v">{{ kpi.utilizationPct }}%</span>
      </div>
      <div class="kpi-chip">
        <span class="kpi-chip-l">見込み時間（分）</span>
        <span class="kpi-chip-v">{{ kpi.estimatedMinutes }}</span>
      </div>
      <div class="kpi-chip">
        <span class="kpi-chip-l">生産数量合計</span>
        <span class="kpi-chip-v">{{ kpi.totalProductQty }}</span>
      </div>
    </div>

    <div
      v-loading="boardTableLoading"
      element-loading-text="読み込み中…"
      class="lap-board"
      :class="{ 'lap-board--loading': boardTableLoading }"
    >
      <template v-if="lapBoardDisplayRows.length > 0">
        <div class="lap-board-outer">
          <div class="lap-board-layout">
            <div class="lap-board-row lap-board-row--head">
              <div class="lap-rail-cell lap-rail-head">周</div>
              <div class="lap-board-grid lap-board-head" :style="lapBoardColsGridStyle">
                <div v-if="useCompactLapHeader" class="lap-col-head-range">
                  <span
                    v-for="mark in compactLapHeaderMarkItems"
                    :key="`head-mark-${mark.value}`"
                    class="lap-col-head-range-mark"
                    :style="{ left: `${mark.leftPct}%` }"
                  >{{ mark.value }}</span>
                </div>
                <div
                  v-else
                  v-for="h in lapColumnHeaders"
                  :key="h.i"
                  class="lap-col-head"
                  :class="{ 'lap-col-head--truncated': h.truncated }"
                  :title="h.truncated ? String(h.i) : undefined"
                >
                  <span class="lap-col-head-digits">
                    <span
                      v-for="(d, di) in h.digits"
                      :key="`${h.i}-${di}`"
                      class="lap-col-head-digit"
                    >{{ d }}</span>
                  </span>
                </div>
              </div>
            </div>
            <template v-for="item in lapBoardDisplayRows" :key="item.key">
              <div v-if="item.kind === 'date'" class="lap-board-row lap-board-row--date">
                <div class="lap-rail-cell lap-rail-date">{{ item.dateLabel }}</div>
                <div class="lap-board-grid lap-board-date-row lap-date-scroll-row" :style="lapBoardColsGridStyle">
                  <div class="lap-date-band-scroll lap-date-memo-zone">
                    <span v-if="getBoardDateMemo(item.work_date)" class="lap-date-memo-text">{{
                      getBoardDateMemo(item.work_date)
                    }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="lap-board-row lap-board-row--lap">
                <div class="lap-rail-cell lap-rail-lap">
                  <span class="lap-label-no">第{{ item.row.lap_display_no }}周目</span>
                  <span
                    class="lap-label-time"
                    :class="{ 'lap-label-time--empty': !lapTimeRangeLabel(item.row.lap_no) }"
                  >{{ lapTimeRangeLabel(item.row.lap_no) || '—' }}</span>
                </div>
                <div class="lap-board-grid lap-board-body-row lap-board-body-row--lap" :style="lapBoardColsGridStyle">
                  <template v-if="item.row.mergedLeft != null">
                    <div class="lap-merged-host" :style="lapBoardColsGridStyle">
                      <div
                        v-for="ms in item.row.mergedLeft"
                        :key="ms.key"
                        class="lap-merged-seg lap-merged-seg--board-jig-block"
                        :class="[
                          'sched-color-' + schedColorIndexForPlatingMachine(ms.plating_machine),
                          ms.boardMark === 'manual' ? 'lap-merged-seg--manual' : ms.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                        ]"
                        :title="boardMergedSegTitle(ms, item.row.lap_no)"
                        :style="{ gridColumn: `${ms.startCol} / span ${ms.span}`, gridRow: '1' }"
                      >
                        <div class="lap-merged-label-stack" :title="boardMergedSegTitle(ms, item.row.lap_no)">
                          <span class="lap-merged-text lap-merged-text--jig">{{
                            formatPlatingBoardLabel(ms.plating_machine, jigBlockFrameCount(ms, item.row.lap_no))
                          }}</span>
                          <span
                            v-if="buildJigBlockProductCalcParts(ms, item.row.lap_no)?.length"
                            class="lap-merged-text lap-merged-text--calc"
                          >
                            <template
                              v-for="(part, pIdx) in buildJigBlockProductCalcParts(ms, item.row.lap_no)"
                              :key="`${ms.key}-prod-${pIdx}`"
                            >
                              <span v-if="pIdx > 0" class="lap-merged-product-sep"> / </span>
                              <span
                                :class="{
                                  'lap-merged-product-label--alt': pIdx >= 1 && !part.untilDepleted && !part.forceRedText,
                                  'lap-merged-product-label--depleted': part.untilDepleted,
                                  'lap-merged-product-label--force-red': part.forceRedText && !part.untilDepleted,
                                }"
                              >{{ part.displayText }}</span>
                            </template>
                          </span>
                        </div>
                      </div>
                      <div
                        v-if="(item.row.mergedTail?.length ?? 0) > 0"
                        class="lap-merged-tail"
                        :style="{ gridColumn: `${lapBoardColCount} / span 1`, gridRow: '1' }"
                      >
                        <div
                          v-for="tc in item.row.mergedTail"
                          :key="tc.id"
                          class="lap-merged-tail-item"
                          :class="[
                            'sched-color-' + schedColorIndexForPlatingMachine(tc.plating_machine),
                            tc.boardMark === 'manual' ? 'lap-merged-seg--manual' : tc.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                          ]"
                        >
                          <span class="lap-merged-text" :title="boardTailCardTitle(tc)">{{
                            formatPlatingBoardLabel(tc.product_name, 1)
                          }}</span>
                        </div>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div
                      v-for="(cell, ci) in item.row.cells"
                      :key="`${item.row.lap_no}-${ci}`"
                      class="lap-col"
                      :class="{ 'lap-col--empty': cell.segments.length === 0 }"
                    >
                      <div class="lap-track lap-track--grid">
                        <div
                          v-for="seg in cell.segments"
                          :key="`${item.row.lap_no}-${ci}-${seg.key}`"
                          class="lap-segment lap-segment--cell"
                          :class="[
                            'sched-color-' + schedColorIndexForPlatingMachine(seg.plating_machine),
                            seg.boardMark === 'manual' ? 'lap-segment--manual' : seg.boardMark === 'rush' ? 'lap-segment--rush' : '',
                          ]"
                          :style="{ flex: seg.slotCount }"
                        >
                          <span class="lap-segment-text" :title="`${seg.plating_machine}・治具1本`">{{
                            formatPlatingBoardLabel(seg.product_name, 1)
                          }}</span>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
      <div v-else-if="!boardTableLoading" class="board-empty">
        {{
          layoutBoardReady
            ? '表示期間内に割当データがありません'
            : `「追加レイアウト」で計画日と段数を指定してください（表示：${boardViewRangeLabel}）`
        }}
      </div>
    </div>

    <el-dialog
      v-model="printScheduleDialogVisible"
      title="印刷範囲の指定"
      width="520px"
      class="print-range-dialog"
      destroy-on-close
      align-center
      @opened="onPrintScheduleDialogOpened"
    >
      <div class="print-range-body">
        <p class="jig-drop-dialog-hint">
          開始・終了の日付と周目を指定してください。指定期間のボード割当のみ印刷します。
        </p>
        <el-form label-position="top" size="small" class="print-range-form">
          <div class="print-range-section">
            <div class="print-range-section__title">開始</div>
            <div class="print-range-fields">
              <el-form-item label="開始日" class="print-range-field">
                <el-date-picker
                  v-model="printStartDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="開始日"
                  size="small"
                  :disabled-date="printScheduleDateDisabled"
                />
              </el-form-item>
              <el-form-item label="開始周目" class="print-range-field">
                <el-select
                  v-if="printStartLapOptions.length > 0"
                  v-model="printStartLap"
                  size="small"
                  placeholder="周目"
                  class="print-range-lap-select"
                >
                  <el-option
                    v-for="opt in printStartLapOptions"
                    :key="`ps-${opt.value}`"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <el-input-number v-else v-model="printStartLap" :min="1" :max="999" :step="1" controls-position="right" size="small" />
              </el-form-item>
            </div>
          </div>
          <div class="print-range-section">
            <div class="print-range-section__title">終了</div>
            <div class="print-range-fields">
              <el-form-item label="終了日" class="print-range-field">
                <el-date-picker
                  v-model="printEndDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="終了日"
                  size="small"
                  :disabled-date="printScheduleDateDisabled"
                />
              </el-form-item>
              <el-form-item label="終了周目" class="print-range-field">
                <el-select
                  v-if="printEndLapOptions.length > 0"
                  v-model="printEndLap"
                  size="small"
                  placeholder="周目"
                  class="print-range-lap-select"
                >
                  <el-option
                    v-for="opt in printEndLapOptions"
                    :key="`pe-${opt.value}`"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <el-input-number v-else v-model="printEndLap" :min="1" :max="999" :step="1" controls-position="right" size="small" />
              </el-form-item>
            </div>
          </div>
        </el-form>
        <p v-if="printRangePreviewLabel" class="print-range-preview">{{ printRangePreviewLabel }}</p>
      </div>
      <template #footer>
        <el-button size="small" @click="printScheduleDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" :icon="Printer" @click="confirmPrintSchedule">印刷</el-button>
      </template>
    </el-dialog>
  </el-card>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { usePlatingInputBoard, type PlatingInputBoardMode } from './usePlatingInputBoard'

defineOptions({ name: 'PlatingInputBoardPanel' })

const props = withDefaults(
  defineProps<{
    mode?: PlatingInputBoardMode
  }>(),
  { mode: 'instruction' },
)

const board = usePlatingInputBoard(props.mode)
const {
  ArrowLeft,
  ArrowRight,
  Printer,
  boardFilterDateRange,
  boardPeriodFilterLoading,
  boardTableLoading,
  boardViewRangeLabel,
  onBoardViewRangeChange,
  shiftBoardViewRange,
  setBoardViewRangeToday,
  layoutBoardReady,
  kpi,
  lapBoardDisplayRows,
  lapBoardColsGridStyle,
  lapColumnHeaders,
  useCompactLapHeader,
  compactLapHeaderMarkItems,
  lapBoardColCount,
  schedColorIndexForPlatingMachine,
  formatPlatingBoardLabel,
  buildJigBlockProductCalcParts,
  boardMergedSegTitle,
  boardTailCardTitle,
  lapTimeRangeLabel,
  getBoardDateMemo,
  jigBlockFrameCount,
  openPrintScheduleDialog,
  printScheduleDialogVisible,
  printStartDate,
  printEndDate,
  printStartLap,
  printEndLap,
  printStartLapOptions,
  printEndLapOptions,
  printScheduleDateDisabled,
  printRangePreviewLabel,
  onPrintScheduleDialogOpened,
  confirmPrintSchedule,
  reloadBoardView,
} = board
</script>

<style scoped src="./platingInputBoardPanel.scss"></style>
