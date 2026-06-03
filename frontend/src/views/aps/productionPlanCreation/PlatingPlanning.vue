<template>
  <div ref="platingPageRef" class="plating-planning-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="title-wrapper">
            <span class="title-icon-wrap" aria-hidden="true">
              <el-icon class="title-icon"><Grid /></el-icon>
            </span>
            <div>
              <h1 class="page-title">メッキ計画作成</h1>
              <p class="page-description">
                メッキ治具を投入ボードへ配置し、各枠に製品を割当てて周目ごとの投入計画を作成します。
              </p>
            </div>
          </div>
        </div>
        <div class="header-badge">
          <span class="header-badge__dot" />
          <span>APS 生産計画</span>
        </div>
      </div>
    </header>

    <el-card
      shadow="never"
      class="pp-card pp-card--jig"
      :class="{ 'pp-card--jig-list-collapsed': !jigCardListExpanded }"
    >
      <template #header>
        <div class="section-head-row section-head-row--jig">
          <div class="section-head-row__start">
            <span class="pp-card-title">メッキ治具</span>
            <el-select
              :model-value="jigFilterProductCd || undefined"
              class="jig-product-filter-select"
              size="small"
              clearable
              filterable
              placeholder="製品で治具を検索"
              :loading="loadingJigAvailability"
              popper-class="jig-product-filter-popper"
              @update:model-value="onJigFilterProductModelUpdate"
              @clear="onJigFilterProductClear"
            >
              <el-option
                v-for="opt in jigProductFilterOptions"
                :key="opt.product_cd"
                :label="opt.label"
                :value="opt.product_cd"
              />
            </el-select>
            <div class="jig-card-meta jig-card-meta--inline">
              <span class="jig-meta-pill">対象治具：{{ jigAvailabilityRows.length }} 件</span>
              <span class="jig-meta-pill">総合計治具数：{{ jigAvailabilityTotalQty }} 本</span>
              <span v-if="jigFilterProductCdActive" class="jig-meta-pill jig-meta-pill--filter">
                該当治具：{{ jigFilteredMatchCount }} 件
              </span>
            </div>
          </div>
          <div class="toolbar-inline">
            <el-button
              class="jig-usage-edit-btn"
              size="small"
              @click="openPlatingJigMasterDialog"
            >
              <el-icon class="jig-usage-edit-btn__icon"><EditPen /></el-icon>
              設備使用数編集
            </el-button>
          </div>
        </div>
      </template>
      <div class="jig-card-body" :class="{ 'jig-card-body--collapsed': !jigCardListExpanded }">
        <div
          v-show="jigCardListExpanded"
          v-loading="loadingJigAvailability"
          class="jig-card-list-wrap"
        >
          <div class="jig-card-list">
            <div
              v-for="row in jigAvailabilityRowsDisplay"
              :key="row.plating_machine"
              class="jig-pick-card"
              :class="{
                'jig-pick-card--filter-match': jigFilterProductCdActive && jigRowMatchesProductFilter(row),
                'jig-pick-card--filter-dim': jigFilterProductCdActive && !jigRowMatchesProductFilter(row),
              }"
              draggable="true"
              @dragstart="onJigCardDragStart($event, row)"
              @dragend="onJigCardDragEnd"
              @dblclick.stop="openJigCardProductsDialog(row)"
            >
              <span class="jig-pick-card__label">{{ formatJigPickLabel(row) }}</span>
            </div>
          </div>
          <p v-if="!loadingJigAvailability && jigAvailabilityRows.length === 0" class="jig-card-list-empty">
            データがありません
          </p>
          <p
            v-else-if="jigFilterProductCdActive && jigFilteredMatchCount === 0"
            class="jig-card-list-empty jig-card-list-empty--filter"
          >
            選択した製品（{{ jigFilterProductLabel }}）に対応するメッキ治具は登録されていません
          </p>
        </div>
        <el-button
          class="jig-card-toggle-btn"
          circle
          size="small"
          :title="jigCardListExpanded ? '治具カードを隠す' : '治具カードを表示'"
          @click="jigCardListExpanded = !jigCardListExpanded"
        >
          <el-icon>
            <ArrowUp v-if="jigCardListExpanded" />
            <ArrowDown v-else />
          </el-icon>
        </el-button>
      </div>
    </el-card>
    <el-dialog
      v-model="jigCardProductsDialogVisible"
      width="460px"
      class="jig-drop-dialog"
      align-center
      destroy-on-close
    >
      <template #header>
        <h4 class="al-header-title">治具の生産可能品種</h4>
      </template>
      <div class="jig-pick-card-tooltip">
        <div class="jig-pick-card-tooltip__head">
          {{ jigCardProductsDialogMachine }} · 使用可能 {{ jigCardProductsDialogAvailableQty }} 本
        </div>
        <div class="jig-pick-card-tooltip__section">生産品種</div>
        <ul v-if="jigCardProductsDialogRows.length" class="jig-pick-card-tooltip__list">
          <li
            v-for="prod in jigCardProductsDialogRows"
            :key="prod.product_cd"
          >
            {{ prod.product_name }}（{{ prod.product_cd }}）
          </li>
        </ul>
        <div v-else class="jig-pick-card-tooltip__empty">登録なし</div>
      </div>
      <template #footer>
        <div class="jd-footer">
          <el-button type="primary" @click="jigCardProductsDialogVisible = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <el-card shadow="never" class="pp-card pp-card--board">
      <template #header>
        <div class="section-head-row section-head-row--board">
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
                  class="board-head-period__nav-btn"
                  :disabled="boardPeriodFilterLoading"
                  @click="shiftBoardViewRange(-1)"
                />
                <el-button
                  type="primary"
                  plain
                  size="small"
                  class="board-head-period__today"
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
                  class="board-head-period__nav-btn"
                  :disabled="boardPeriodFilterLoading"
                  @click="shiftBoardViewRange(1)"
                />
              </div>
            </div>
          </div>
          <div class="toolbar-inline board-head-toolbar">
            <el-button type="primary" size="small" class="board-act-btn board-act-btn--primary" @click="() => openAppendLayoutDialog()">
              追加レイアウト
            </el-button>
            <el-button
              size="small"
              class="board-act-btn board-act-btn--list"
              :disabled="!hasProductionListData"
              @click="openProductionListDialog"
            >
              生産リスト
            </el-button>
            <el-button size="small" class="board-act-btn board-act-btn--copy" :disabled="!canUseLapCopy" @click="openLapCopyDialog">コピー</el-button>
            <el-button
              size="small"
              type="danger"
              plain
              class="board-act-btn board-act-btn--danger"
              :disabled="deletableStartDates.length === 0"
              @click="openDeleteLapsByDateDialog"
            >
              削除
            </el-button>
            <el-button
              size="small"
              type="info"
              plain
              class="board-act-btn board-act-btn--print"
              :icon="Printer"
              :disabled="!layoutBoardReady"
              @click="openPrintScheduleDialog"
            >
              印刷
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
          <span class="kpi-chip-l">割当枠数</span>
          <span class="kpi-chip-v">{{ kpi.usedSlots }}</span>
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
        :class="{
          'lap-board--jig-drop': jigBoardDragActive,
          'lap-board--loading': boardTableLoading,
        }"
        @dragover.prevent="onJigToBoardDragOver"
        @dragleave="onJigToBoardDragLeave"
        @drop.prevent="onJigToBoardDrop($event)"
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
                <div class="lap-op-cell lap-op-head">操作</div>
              </div>
              <template v-for="item in lapBoardDisplayRows" :key="item.key">
                <div
                  v-if="item.kind === 'date'"
                  class="lap-board-row lap-board-row--date"
                >
                  <div class="lap-rail-cell lap-rail-date">{{ item.dateLabel }}</div>
                  <div
                    class="lap-board-grid lap-board-date-row lap-date-scroll-row"
                    :style="lapBoardColsGridStyle"
                    title="ダブルクリックで日付メモを編集"
                    @dblclick.stop="openBoardDateMemoEdit(item.work_date)"
                  >
                    <div class="lap-date-band-scroll lap-date-memo-zone">
                      <span
                        v-if="getBoardDateMemo(item.work_date)"
                        class="lap-date-memo-text"
                      >{{ getBoardDateMemo(item.work_date) }}</span>
                      <span v-else class="lap-date-memo-placeholder">ダブルクリックでメモ入力</span>
                    </div>
                  </div>
                  <div class="lap-op-cell lap-op-date" />
                </div>
                <div
                  v-else
                  class="lap-board-row lap-board-row--lap"
                  :class="{ 'lap-board-row--jig-drop': jigDropHoverLap === item.row.lap_no }"
                >
                  <div
                    class="lap-rail-cell lap-rail-lap"
                    :class="{ 'lap-rail-lap--jig-drop': jigDropHoverLap === item.row.lap_no }"
                  >
                    <span class="lap-label-no">第{{ item.row.lap_display_no }}周目</span>
                    <span
                      class="lap-label-time lap-label-time--editable"
                      :class="{ 'lap-label-time--empty': !lapTimeRangeLabel(item.row.lap_no) }"
                      title="ダブルクリックで開始時刻を編集"
                      @dblclick.stop="openLapStartTimeEdit(item.row.lap_no)"
                    >{{ lapTimeRangeLabel(item.row.lap_no) || '—' }}</span>
                  </div>
                  <div
                    class="lap-board-grid lap-board-body-row lap-board-body-row--lap"
                    :style="lapBoardColsGridStyle"
                    :data-lap-no="String(item.row.lap_no)"
                    @dragover.prevent.stop="onJigToBoardDragOver($event, item.row.lap_no)"
                    @drop.prevent.stop="onJigToBoardDrop($event, item.row.lap_no)"
                  >
              <!-- 割当後：同一周内で隣列かつ同一品番の枠を横方向に結合表示（製品名・本数） -->
              <template v-if="item.row.mergedLeft != null">
                <div class="lap-merged-host" :style="lapBoardColsGridStyle">
                  <div
                    v-for="ms in item.row.mergedLeft"
                    :key="ms.key"
                    class="lap-merged-seg"
                    :class="[
                      'sched-color-' + schedColorIndexForPlatingMachine(ms.plating_machine),
                      ms.boardMark === 'manual' ? 'lap-merged-seg--manual' : ms.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                      'lap-merged-seg--board-jig-block',
                      isJigProductCd(ms.product_cd) ? 'lap-merged-seg--board-draggable' : '',
                      draggingInventoryRow && isJigProductCd(ms.product_cd) ? 'lap-merged-seg--product-drop' : '',
                      productDropHoverBlockKey === ms.key ? 'lap-merged-seg--product-drop-hover' : '',
                    ]"
                    :title="boardMergedSegTitle(ms, item.row.lap_no)"
                    :style="{ gridColumn: `${ms.startCol} / span ${ms.span}`, gridRow: '1' }"
                    :data-block-ids="ms.cardIds.join(',')"
                    :data-lap-no="String(item.row.lap_no)"
                    @dragover.prevent.stop="onProductToJigBlockDragOver($event, ms, item.row.lap_no)"
                    @dragleave.stop="onProductToJigBlockDragLeave"
                    @drop.prevent.stop="onProductToJigBlockDrop($event, ms, item.row.lap_no)"
                    @contextmenu.prevent.stop="onBoardJigBlockContextMenu(ms, item.row.lap_no)"
                    @dblclick.stop="onBoardMergedSegDblClick(ms, item.row.lap_no)"
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
                      :data-card-id="tc.id"
                      :data-lap-no="String(item.row.lap_no)"
                      @dblclick.stop="onBoardScheduleCardDblClick(tc)"
                    >
                      <span
                        class="lap-merged-text"
                        :title="boardTailCardTitle(tc)"
                      >{{ formatPlatingBoardLabel(tc.product_name, 1) }}</span>
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
                  <div class="lap-track lap-track--grid" :data-lap-no="item.row.lap_no">
                    <div
                      v-for="seg in cell.segments"
                      :key="`${item.row.lap_no}-${ci}-${seg.key}`"
                      class="lap-segment lap-segment--cell"
                      :class="[
                        'sched-color-' + schedColorIndexForPlatingMachine(seg.plating_machine),
                        seg.boardMark === 'manual' ? 'lap-segment--manual' : seg.boardMark === 'rush' ? 'lap-segment--rush' : '',
                      ]"
                      :data-seg-key="seg.key"
                      :style="{ flex: seg.slotCount }"
                    >
                      <span
                        class="lap-segment-text"
                        :title="`${seg.plating_machine}・治具1本`"
                      >{{ formatPlatingBoardLabel(seg.product_name, 1) }}</span>
                    </div>
                  </div>
                </div>
              </template>
                  </div>
                  <div class="lap-op-cell lap-op-lap">
                    <el-tooltip content="この周目の後に週を挿入" placement="top">
                      <el-button
                        size="small"
                        type="primary"
                        text
                        class="lap-row-op-btn"
                        :icon="Plus"
                        @click.stop="openAppendLayoutDialog(item.row.lap_no)"
                      />
                    </el-tooltip>
                    <el-tooltip content="次行へコピー" placement="top">
                      <el-button
                        size="small"
                        type="primary"
                        text
                        class="lap-row-op-btn"
                        :icon="DocumentCopy"
                        @click.stop="copyBoardLapRowToNext(item.row.lap_no)"
                      />
                    </el-tooltip>
                    <el-tooltip content="この行をクリア" placement="top">
                      <el-button
                        size="small"
                        type="danger"
                        text
                        class="lap-row-op-btn"
                        :icon="Delete"
                        @click.stop="confirmClearBoardLapRow(item.row.lap_no)"
                      />
                    </el-tooltip>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </template>
        <div v-else-if="!boardTableLoading" class="board-empty">
          {{
            layoutBoardReady
              ? 'メッキ治具カードをここへドラッグして本数を指定してください'
              : `「追加レイアウト」で計画日と段数を指定してください（表示：${boardViewRangeLabel}）`
          }}
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="pp-card pp-card--summary">
      <template #header>
        <div class="section-head-row section-head-row--summary-float">
          <span class="pp-card-title pp-card-title--summary">メッキ前在庫／見込数量</span>
          <div class="summary-head-actions">
            <el-button
              size="small"
              class="summary-print-btn"
              :icon="Printer"
              :loading="summaryPairPrintLoading"
              :disabled="!hasSummaryPairPrintData"
              @click="printSummaryPairTables"
            >
              印刷
            </el-button>
            <template v-if="leftInventoryFloating || rightGenFloating">
            <div class="summary-float-dock-actions">
            <el-button
              v-if="leftInventoryFloating"
              type="primary"
              text
              size="small"
              @click="dockLeftInventoryFloat"
            >
              メッキ前在庫を固定表示
            </el-button>
            <el-button
              v-if="rightGenFloating"
              type="success"
              text
              size="small"
              @click="dockRightGenFloat"
            >
              見込数量を固定表示
            </el-button>
            </div>
            </template>
          </div>
        </div>
      </template>
      <!-- <p class="summary-drag-hint">行を①の治具枠（例：J曲3段 (20)）へドラッグすると製品を割当し、生産数を表示します</p> -->

      <p v-if="leftInventoryFloating && rightGenFloating" class="summary-both-float-hint">
        両方とも浮動表示中です。各ウィンドウの「固定」または上のボタンで元の位置に戻せます。
      </p>
      <el-row v-else :gutter="10" class="pair-row">
        <el-col
          v-if="!leftInventoryFloating"
          :xs="24"
          :md="summaryDockedColSpan"
          class="summary-col summary-col--left"
        >
          <PlatingLeftInventoryPane
            ref="leftPaneRef"
            v-model:inventory-date="leftInventoryDate"
            :loading="loadingPair"
            :rows="leftRows"
            :total="leftPrevInventoryTotal"
            :table-height="TABLE_H"
            :calc-required-jig-count="calcRequiredJigCount"
            show-float-action
            @shift-date="shiftLeftInventoryDate"
            @pop-out="openLeftInventoryFloat"
          />
        </el-col>
        <el-col
          v-if="!rightGenFloating"
          :xs="24"
          :md="summaryDockedColSpan"
          class="summary-col summary-col--right"
        >
          <PlatingRightGenPane
            ref="rightPaneRef"
            v-model:gen-date="rightGenDate"
            :loading="loadingPair"
            :rows="rightRows"
            :total="rightGenQtyTotal"
            :table-height="TABLE_H"
            :calc-required-jig-count="calcRequiredJigCountFromQty"
            show-float-action
            @shift-date="shiftRightGenDate"
            @pop-out="openRightGenFloat"
          />
        </el-col>
      </el-row>
    </el-card>

    <PlatingFloatingPanel
      v-model:visible="leftInventoryFloating"
      title="メッキ前在庫"
      :boundary="platingPageRef"
      :width="560"
      :initial-x="leftInventoryFloatX"
      :initial-y="leftInventoryFloatY"
      @close="onLeftInventoryFloatClose"
    >
      <template #actions>
        <el-button type="primary" text size="small" @click="dockLeftInventoryFloat">固定</el-button>
      </template>
      <PlatingLeftInventoryPane
        ref="leftPaneRef"
        v-model:inventory-date="leftInventoryDate"
        hide-toolbar-title
        :loading="loadingPair"
        :rows="leftRows"
        :total="leftPrevInventoryTotal"
        :table-height="FLOAT_TABLE_H"
        :calc-required-jig-count="calcRequiredJigCount"
        @shift-date="shiftLeftInventoryDate"
      />
    </PlatingFloatingPanel>

    <PlatingFloatingPanel
      v-model:visible="rightGenFloating"
      title="翌日の見込数量"
      :boundary="platingPageRef"
      :width="560"
      :initial-x="rightGenFloatX"
      :initial-y="rightGenFloatY"
      :z-index="41"
      @close="onRightGenFloatClose"
    >
      <template #actions>
        <el-button type="success" text size="small" @click="dockRightGenFloat">固定</el-button>
      </template>
      <PlatingRightGenPane
        ref="rightPaneRef"
        v-model:gen-date="rightGenDate"
        hide-toolbar-title
        :loading="loadingPair"
        :rows="rightRows"
        :total="rightGenQtyTotal"
        :table-height="FLOAT_TABLE_H"
        :calc-required-jig-count="calcRequiredJigCountFromQty"
        @shift-date="shiftRightGenDate"
      />
    </PlatingFloatingPanel>

    <el-dialog
      v-model="jigDropDialogVisible"
      width="360px"
      class="jig-drop-dialog jig-drop-qty-dialog"
      destroy-on-close
      align-center
      :show-close="true"
      @closed="resetJigDropDialog"
    >
      <template #header="{ titleId, titleClass }">
        <h4 :id="titleId" :class="titleClass" class="jd-header-title">治具投入</h4>
      </template>
      <div v-if="jigDropPending" class="jd-body">
        <div class="jd-context">
          <span class="jd-context__machine">{{ jigDropPending.plating_machine }}</span>
          <div class="jd-context__tags">
            <span class="jd-tag">第{{ lapDisplayNo(jigDropPending.target_lap) }}周</span>
            <span class="jd-tag jd-tag--accent">あと {{ jigDropQtyMax }} 本まで</span>
          </div>
        </div>
        <el-form label-position="top" size="small" class="jd-form" @submit.prevent="confirmJigDropToBoard">
          <el-form-item label="投入本数" class="jd-field">
            <el-input-number
              v-model="jigDropQty"
              :min="1"
              :max="jigDropQtyMax"
              :step="1"
              controls-position="right"
              class="jd-qty-input"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="jd-footer">
          <el-button text class="jd-footer__cancel" @click="jigDropDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" :disabled="jigDropQtyMax < 1" @click="confirmJigDropToBoard">投入する</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="productToJigDialogVisible"
      title="治具枠への製品割当"
      width="460px"
      class="jig-drop-dialog product-to-jig-dialog"
      destroy-on-close
      @closed="resetProductToJigDialog"
    >
      <template v-if="productToJigPending">
        <p class="jig-drop-dialog-name">{{ productToJigPending.ms.plating_machine }}</p>
        <div class="jig-drop-dialog-meta">
          <span class="jig-meta-pill">第{{ lapDisplayNo(productToJigPending.lapNo) }}周目</span>
          <span class="jig-meta-pill">枠 {{ productToJigPending.span }} 本</span>
          <span class="jig-meta-pill">割当合計 {{ productAssignSlotsSum }} / {{ productToJigPending.span }}</span>
        </div>
        <p class="jig-drop-dialog-hint">
          異なる製品を同一治具枠に割り当てます。既存を 0 にすると選択製品で全枠を置換できます。
        </p>
        <div class="product-assign-rows">
          <div class="product-assign-row">
            <span class="product-assign-row-label">既存</span>
            <span class="product-assign-row-name" :title="productToJigPending.existing.product_name">{{
              productToJigPending.existing.product_name
            }}</span>
            <el-input-number
              v-model="productAssignExistingSlots"
              :min="0"
              :max="productAssignExistingSlotsMax"
              :step="1"
              size="small"
              controls-position="right"
              class="pp-input-num product-assign-row-qty"
            />
            <span class="product-assign-row-unit">本</span>
          </div>
          <div class="product-assign-row">
            <span class="product-assign-row-label">追加</span>
            <span class="product-assign-row-name" :title="productToJigPending.src.product_name">{{
              productToJigPending.src.product_name
            }}</span>
            <el-input-number
              v-model="productAssignNewSlots"
              :min="0"
              :max="productAssignNewSlotsMax"
              :step="1"
              size="small"
              controls-position="right"
              class="pp-input-num product-assign-row-qty"
            />
            <span class="product-assign-row-unit">本</span>
          </div>
        </div>
        <el-form-item
          v-if="showProductAssignOrder"
          label="左からの順序（前→後）"
          class="product-assign-order-item"
        >
          <el-radio-group v-model="productAssignOrder" size="small">
            <el-radio-button value="existing-first">
              {{ productToJigPending.existing.product_name }} → {{ productToJigPending.src.product_name }}
            </el-radio-button>
            <el-radio-button value="new-first">
              {{ productToJigPending.src.product_name }} → {{ productToJigPending.existing.product_name }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
      </template>
      <template #footer>
        <el-button size="small" @click="productToJigDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" :disabled="!canConfirmProductToJig" @click="confirmProductToJigAssign">
          確定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="boardJigEditDialogVisible"
      width="520px"
      class="jig-drop-dialog board-jig-edit-dialog"
      destroy-on-close
      :show-close="true"
      @closed="resetBoardJigEditDialog"
    >
      <template #header>
        <div class="board-jig-edit-header">
          <h4 class="board-jig-edit-header__title">治具枠の製品割当</h4>
          <p v-if="boardJigEditPending" class="board-jig-edit-header__sub">
            {{ boardJigEditPending.plating_machine }} · 第{{ lapDisplayNo(boardJigEditPending.lap_no) }}周目 ·
            配置 {{ boardJigEditPending.cardIds.length }} 本 / 上限 {{ boardJigEditQtyMax }} 本
          </p>
        </div>
      </template>
      <template v-if="boardJigEditPending">
        <div class="board-jig-edit-body">
          <el-form-item label="治具総本数" class="board-jig-edit-total-item">
            <div class="board-jig-edit-total-slider-wrap" style="--row-hue: 214">
              <div class="jig-edit-product-slider-head">
                <span class="jig-edit-product-slider-min">1</span>
                <span class="jig-edit-product-slider-val board-jig-edit-total-slider-val">
                  {{ Math.floor(Number(boardJigEditQty) || 1) }}<span class="jig-edit-product-unit">本</span>
                </span>
                <span class="jig-edit-product-slider-max">{{ boardJigEditQtyMax }}</span>
              </div>
              <el-slider
                :model-value="Math.floor(Number(boardJigEditQty) || 1)"
                :min="1"
                :max="Math.max(1, boardJigEditQtyMax)"
                :step="1"
                :disabled="boardJigEditQtyMax < 1"
                :format-tooltip="formatBoardJigEditFrameTooltip"
                class="jig-edit-product-slider board-jig-edit-total-slider"
                @update:model-value="(v) => setBoardJigEditQty(Number(v))"
              />
            </div>
          </el-form-item>
          <div class="jig-edit-products">
            <div class="jig-edit-products__head">
              <span class="jig-edit-products__title">割当済み製品（{{ boardJigEditProductFrames.length }} 種）</span>
              <span
                class="jig-edit-products__sum"
                :class="{ 'jig-edit-products__sum--warn': !canConfirmBoardJigEdit }"
              >
                合計 <strong>{{ boardJigEditProductFramesSum }}</strong> / {{ boardJigEditQty }}
                <template v-if="boardJigEditUnassignedFrames > 0"> · 空き {{ boardJigEditUnassignedFrames }}</template>
              </span>
            </div>
            <p v-if="boardJigEditProductFrames.length === 0" class="jig-edit-products__empty">割当済みの製品はありません</p>
            <div
              v-for="(p, pi) in boardJigEditProductFrames"
              :key="p.product_cd"
              class="jig-edit-product-row"
              :style="{ '--row-hue': String(205 + pi * 48) }"
            >
              <span class="jig-edit-product-name" :title="p.product_name">{{ p.product_name }}</span>
              <div class="jig-edit-product-slider-wrap">
                <div class="jig-edit-product-slider-head">
                  <span class="jig-edit-product-slider-min">0</span>
                  <span class="jig-edit-product-slider-val">
                    {{ Math.floor(Number(p.frames) || 0) }}<span class="jig-edit-product-unit">本</span>
                  </span>
                  <span class="jig-edit-product-slider-max">{{ boardJigEditProductFramesSliderMax(p.product_cd) }}</span>
                </div>
                <el-slider
                  :model-value="Math.floor(Number(p.frames) || 0)"
                  :min="0"
                  :max="boardJigEditProductFramesSliderMax(p.product_cd)"
                  :step="1"
                  :show-tooltip="true"
                  :format-tooltip="formatBoardJigEditFrameTooltip"
                  class="jig-edit-product-slider"
                  @update:model-value="(v) => setBoardJigEditProductFrames(p.product_cd, Number(v))"
                />
              </div>
              <span
                class="jig-edit-product-qty"
                :class="{ 'jig-edit-product-qty--depleted': p.untilDepleted, 'jig-edit-product-qty--force-red': p.forceRedText && !p.untilDepleted }"
              >
                {{ p.untilDepleted ? '無くなり次第' : formatQtyDisplay(p.frames * (p.kake > 0 ? p.kake : 1)) }}
              </span>
              <div class="jig-edit-product-switches">
                <el-switch
                  v-model="p.untilDepleted"
                  size="small"
                  inline-prompt
                  active-text="無"
                  inactive-text="数"
                />
                <el-switch
                  v-model="p.forceRedText"
                  size="small"
                  inline-prompt
                  active-text="赤"
                  inactive-text="通"
                />
              </div>
              <el-button
                type="danger"
                link
                size="small"
                class="jig-edit-product-delete"
                :icon="Delete"
                title="この製品の割当を削除"
                @click="removeBoardJigEditProduct(p.product_cd)"
              />
            </div>
            <el-form-item
              v-if="showBoardJigEditProductOrder"
              label="左からの順序（前→後）"
              class="jig-edit-product-order-item"
            >
              <el-radio-group v-model="boardJigEditProductOrder" size="small">
                <el-radio-button value="normal">{{ boardJigEditProductOrderNormalLabel }}</el-radio-button>
                <el-radio-button value="reversed">{{ boardJigEditProductOrderReversedLabel }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </div>
          <div class="board-jig-edit-add">
            <div class="board-jig-edit-add__head">
              <span class="board-jig-edit-add__title">製品を追加</span>
              <el-select
                v-model="boardJigEditAddKey"
                filterable
                clearable
                placeholder="コード・名称で検索"
                size="small"
                class="board-jig-edit-add-select"
                popper-class="bpp-select-popper"
              >
                <el-option-group v-if="boardJigEditAddSummaryOptions.length" label="在庫・見込">
                  <el-option
                    v-for="opt in boardJigEditAddSummaryOptions"
                    :key="opt.pickKey"
                    :label="opt.label"
                    :value="opt.pickKey"
                  />
                </el-option-group>
                <el-option-group v-if="boardJigEditAddCatalogOptions.length" label="治具対応製品">
                  <el-option
                    v-for="opt in boardJigEditAddCatalogOptions"
                    :key="opt.pickKey"
                    :label="opt.label"
                    :value="opt.pickKey"
                  />
                </el-option-group>
              </el-select>
              <span v-if="boardJigEditUnassignedFrames > 0" class="board-jig-edit-add__empty">空き {{ boardJigEditUnassignedFrames }} 本</span>
            </div>
            <el-form label-position="top" size="small" class="board-jig-edit-add-form" @submit.prevent>
              <template v-if="boardJigEditAddKey">
                <div v-if="showBoardJigEditInlineAssign" class="board-jig-edit-inline-assign">
                  <div class="board-jig-edit-inline-rows">
                    <div class="jig-edit-product-row board-jig-edit-inline-row" style="--row-hue: 218">
                      <span class="board-jig-edit-inline-tag">既存</span>
                      <span
                        class="jig-edit-product-name"
                        :title="boardJigEditPrimaryFrame?.product_name"
                      >{{ boardJigEditPrimaryFrame?.product_name }}</span>
                      <div class="jig-edit-product-slider-wrap">
                        <div class="jig-edit-product-slider-head">
                          <span class="jig-edit-product-slider-min">0</span>
                          <span class="jig-edit-product-slider-val">
                            {{ Math.floor(Number(boardJigEditInlineExistingSlots) || 0) }}<span class="jig-edit-product-unit">本</span>
                          </span>
                          <span class="jig-edit-product-slider-max">{{ boardJigEditInlineSpan }}</span>
                        </div>
                        <el-slider
                          :model-value="Math.floor(Number(boardJigEditInlineExistingSlots) || 0)"
                          :min="0"
                          :max="boardJigEditInlineSpan"
                          :step="1"
                          :format-tooltip="formatBoardJigEditFrameTooltip"
                          class="jig-edit-product-slider"
                          @update:model-value="(v) => setBoardJigEditInlineExistingSlots(Number(v))"
                        />
                      </div>
                    </div>
                    <div class="jig-edit-product-row board-jig-edit-inline-row" style="--row-hue: 168">
                      <span class="board-jig-edit-inline-tag">追加</span>
                      <span class="jig-edit-product-name" :title="boardJigEditAddOpt?.src.product_name">{{
                        boardJigEditAddOpt?.src.product_name
                      }}</span>
                      <div class="jig-edit-product-slider-wrap">
                        <div class="jig-edit-product-slider-head">
                          <span class="jig-edit-product-slider-min">0</span>
                          <span class="jig-edit-product-slider-val">
                            {{ Math.floor(Number(boardJigEditInlineNewSlots) || 0) }}<span class="jig-edit-product-unit">本</span>
                          </span>
                          <span class="jig-edit-product-slider-max">{{ boardJigEditInlineSpan }}</span>
                        </div>
                        <el-slider
                          :model-value="Math.floor(Number(boardJigEditInlineNewSlots) || 0)"
                          :min="0"
                          :max="boardJigEditInlineSpan"
                          :step="1"
                          :format-tooltip="formatBoardJigEditFrameTooltip"
                          class="jig-edit-product-slider"
                          @update:model-value="(v) => setBoardJigEditInlineNewSlots(Number(v))"
                        />
                      </div>
                    </div>
                  </div>
                  <div v-if="showBoardJigEditInlineOrder" class="board-jig-edit-inline-order">
                    <span class="board-jig-edit-inline-order__label">左からの順序（前→後）</span>
                    <el-radio-group v-model="boardJigEditInlineOrder" size="small" class="board-jig-edit-inline-order__group">
                      <el-radio-button value="existing-first">
                        {{ boardJigEditPrimaryFrame?.product_name }} → {{ boardJigEditAddOpt?.src.product_name }}
                      </el-radio-button>
                      <el-radio-button value="new-first">
                        {{ boardJigEditAddOpt?.src.product_name }} → {{ boardJigEditPrimaryFrame?.product_name }}
                      </el-radio-button>
                    </el-radio-group>
                  </div>
                </div>
                <template v-else>
                  <el-form-item label="追加本数" class="board-jig-edit-add-field board-jig-edit-add-field--qty">
                    <div class="board-jig-edit-add-slider-wrap" style="--row-hue: 168">
                      <div class="jig-edit-product-slider-head">
                        <span class="jig-edit-product-slider-min">1</span>
                        <span class="jig-edit-product-slider-val">
                          {{ Math.floor(Number(boardJigEditAddSlots) || 1) }}<span class="jig-edit-product-unit">本</span>
                        </span>
                        <span class="jig-edit-product-slider-max">{{ boardJigEditAddSlotsMax }}</span>
                      </div>
                      <el-slider
                        :model-value="Math.floor(Number(boardJigEditAddSlots) || 1)"
                        :min="1"
                        :max="boardJigEditAddSlotsMax"
                        :step="1"
                        :disabled="boardJigEditAddReplaceAll"
                        :format-tooltip="formatBoardJigEditFrameTooltip"
                        class="jig-edit-product-slider"
                        @update:model-value="(v) => (boardJigEditAddSlots = Math.max(1, Math.floor(Number(v) || 1)))"
                      />
                    </div>
                  </el-form-item>
                  <el-checkbox
                    v-if="boardJigEditAddCanReplaceAll"
                    v-model="boardJigEditAddReplaceAll"
                    class="board-jig-edit-add-replace"
                  >
                    全枠を選択製品で置換
                  </el-checkbox>
                </template>
              </template>
            </el-form>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button
          size="small"
          type="primary"
          :disabled="!canConfirmBoardJigEdit || !canConfirmBoardJigEditWithAdd"
          @click="confirmBoardJigQtyEdit"
        >
          確定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="productionListDialogVisible"
      width="720px"
      class="production-list-dialog"
      align-center
      destroy-on-close
      :show-close="true"
    >
      <template #header="{ titleId, titleClass }">
        <div class="prod-list-header">
          <h4 :id="titleId" :class="titleClass" class="prod-list-header__title">生産リスト</h4>
          <span class="prod-list-header__meta">表示：{{ boardViewRangeLabel }}</span>
        </div>
      </template>
      <div v-loading="boardPeriodFilterLoading" class="prod-list-body">
        <el-empty
          v-if="productionListByDay.length === 0"
          description="割当済みの生産データがありません"
          :image-size="72"
        />
        <template v-else>
          <div class="prod-list-days">
            <section
              v-for="group in productionListByDay"
              :key="`prod-day-${group.work_date}`"
              class="prod-list-day"
            >
              <div class="prod-list-day__head">
                <span class="prod-list-day__date">{{ group.work_date_label || group.work_date }}</span>
                <span class="prod-list-day__count">{{ group.rows.length }} 品種</span>
                <span class="prod-list-day__total">
                  生産数合計 {{ formatQtyDisplay(group.total_production_qty) }}
                </span>
              </div>
              <div class="prod-list-day-cols">
                <el-table
                  :data="group.rows_left"
                  size="small"
                  border
                  stripe
                  class="prod-list-table"
                >
                  <el-table-column prop="product_name" label="製品名" min-width="100">
                    <template #default="{ row }">
                      <el-popover
                        placement="top-start"
                        trigger="click"
                        :width="300"
                        popper-class="prod-list-time-popper"
                      >
                        <template #reference>
                          <button type="button" class="prod-list-name-btn" :title="row.product_name">
                            {{ row.product_name }}
                          </button>
                        </template>
                        <div class="prod-list-time-pop">
                          <div class="prod-list-time-pop__title">{{ row.product_name }}</div>
                          <div class="prod-list-time-pop__subtitle">生産時間帯</div>
                          <ul v-if="row.time_periods.length" class="prod-list-time-pop__list">
                            <li v-for="tp in row.time_periods" :key="tp.lap_no">
                              <span class="prod-list-time-pop__lap">第{{ tp.lap_display_no }}周目</span>
                              <span class="prod-list-time-pop__range">{{ tp.time_label }}</span>
                              <span class="prod-list-time-pop__qty">生産数 {{ formatQtyDisplay(tp.production_qty) }}</span>
                            </li>
                          </ul>
                          <p v-else class="prod-list-time-pop__empty">時間情報がありません</p>
                        </div>
                      </el-popover>
                    </template>
                  </el-table-column>
                  <el-table-column prop="production_qty" label="生産数" width="72" align="right">
                    <template #default="{ row }">{{ formatQtyDisplay(row.production_qty) }}</template>
                  </el-table-column>
                </el-table>
                <el-table
                  :data="group.rows_right"
                  size="small"
                  border
                  stripe
                  class="prod-list-table"
                >
                  <el-table-column prop="product_name" label="製品名" min-width="100">
                    <template #default="{ row }">
                      <el-popover
                        placement="top-start"
                        trigger="click"
                        :width="300"
                        popper-class="prod-list-time-popper"
                      >
                        <template #reference>
                          <button type="button" class="prod-list-name-btn" :title="row.product_name">
                            {{ row.product_name }}
                          </button>
                        </template>
                        <div class="prod-list-time-pop">
                          <div class="prod-list-time-pop__title">{{ row.product_name }}</div>
                          <div class="prod-list-time-pop__subtitle">生産時間帯</div>
                          <ul v-if="row.time_periods.length" class="prod-list-time-pop__list">
                            <li v-for="tp in row.time_periods" :key="tp.lap_no">
                              <span class="prod-list-time-pop__lap">第{{ tp.lap_display_no }}周目</span>
                              <span class="prod-list-time-pop__range">{{ tp.time_label }}</span>
                              <span class="prod-list-time-pop__qty">生産数 {{ formatQtyDisplay(tp.production_qty) }}</span>
                            </li>
                          </ul>
                          <p v-else class="prod-list-time-pop__empty">時間情報がありません</p>
                        </div>
                      </el-popover>
                    </template>
                  </el-table-column>
                  <el-table-column prop="production_qty" label="生産数" width="72" align="right">
                    <template #default="{ row }">{{ formatQtyDisplay(row.production_qty) }}</template>
                  </el-table-column>
                </el-table>
              </div>
            </section>
          </div>
          <div v-if="productionListGrandTotal > 0" class="prod-list-grand-total">
            <span class="prod-list-grand-total__label">期間生産数合計</span>
            <span class="prod-list-grand-total__value">{{ formatQtyDisplay(productionListGrandTotal) }}</span>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button size="small" @click="productionListDialogVisible = false">閉じる</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="lapCopyDialogVisible"
      width="420px"
      class="lap-copy-dialog"
      align-center
      destroy-on-close
      :show-close="true"
    >
      <template #header="{ titleId, titleClass }">
        <div class="lap-copy-header">
          <span class="lap-copy-header__icon-wrap" aria-hidden="true">
            <el-icon class="lap-copy-header__icon"><DocumentCopy /></el-icon>
          </span>
          <h4 :id="titleId" :class="titleClass" class="lap-copy-header__title">周目データのコピー</h4>
        </div>
      </template>
      <div class="lap-copy-body">
        <div class="lap-copy-flow">
          <div class="lap-copy-field">
            <span class="lap-copy-field__label">コピー元</span>
            <el-select
              v-model="lapCopyFrom"
              size="small"
              filterable
              class="lap-copy-select"
              placeholder="周目を選択"
            >
              <el-option
                v-for="opt in lapCopyLapOptions"
                :key="`from-${opt.value}`"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>
          <div class="lap-copy-flow__arrow" aria-hidden="true">→</div>
          <div class="lap-copy-field">
            <span class="lap-copy-field__label">コピー先</span>
            <el-select
              v-model="lapCopyTo"
              size="small"
              filterable
              class="lap-copy-select"
              placeholder="周目を選択"
            >
              <el-option
                v-for="opt in lapCopyLapOptions"
                :key="`to-${opt.value}`"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="lap-copy-footer">
          <el-button class="lap-copy-footer__cancel" size="small" @click="lapCopyDialogVisible = false">
            キャンセル
          </el-button>
          <el-button
            class="lap-copy-footer__submit"
            type="primary"
            size="small"
            :disabled="lapCopyFrom === lapCopyTo || lapCopySourceCount === 0"
            @click="confirmCopyLapSchedule"
          >
            コピー<span v-if="lapCopySourceCount > 0">（{{ lapCopySourceCount }} 枠）</span>
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="deleteLapsByDateDialogVisible"
      title="日付単位で周目を削除"
      width="420px"
      class="tpl-dialog lap-delete-date-dialog"
      destroy-on-close
    >
      <p class="tpl-dialog-hint">開始時刻基準の日付を指定して、その日付に属する周目を一括削除します。</p>
      <el-form label-position="top" size="small" class="al-form" @submit.prevent>
        <el-form-item label="削除対象日付">
          <el-date-picker
            v-model="deleteLapsByDateYmd"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="日付"
            class="al-control al-date"
            :clearable="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="deleteLapsByDateDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="danger" :disabled="!deleteLapsByDateYmd" @click="confirmDeleteLapsByDate">
          削除
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="boardDateMemoDialogVisible"
      title="日付行メモ"
      width="480px"
      class="jig-drop-dialog board-date-memo-dialog"
      destroy-on-close
      align-center
    >
      <div class="jd-body">
        <p class="jig-drop-dialog-hint">
          {{ formatBoardDateLabel(boardDateMemoEditYmd) }} のメモを入力してください。
        </p>
        <el-form label-position="top" size="small" class="jd-form" @submit.prevent="confirmBoardDateMemoEdit">
          <el-form-item label="メモ" class="jd-field">
            <el-input
              v-model="boardDateMemoEditValue"
              type="textarea"
              :rows="4"
              maxlength="500"
              show-word-limit
              placeholder="例：特記事項・担当・優先度など"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button size="small" @click="boardDateMemoDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" @click="confirmBoardDateMemoEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="printScheduleDialogVisible"
      width="500px"
      class="print-range-dialog"
      destroy-on-close
      align-center
      :show-close="true"
      @opened="onPrintScheduleDialogOpened"
    >
      <template #header="{ titleId, titleClass }">
        <div class="print-range-header">
          <span class="print-range-header__icon-wrap" aria-hidden="true">
            <el-icon class="print-range-header__icon"><Printer /></el-icon>
          </span>
          <h4 :id="titleId" :class="titleClass" class="print-range-header__title">印刷範囲の指定</h4>
        </div>
      </template>
      <div class="print-range-body">
        <div v-if="printRangePreviewLabel" class="print-range-summary">
          {{ printRangePreviewLabel }}
        </div>
        <el-form label-position="top" size="small" class="print-range-form" @submit.prevent>
          <div class="print-range-flow">
            <section class="print-range-block">
              <span class="print-range-block__tag print-range-block__tag--start">開始</span>
              <div class="print-range-block__fields">
                <el-form-item label="日付" class="print-range-field">
                  <el-date-picker
                    v-model="printStartDate"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="開始日"
                    size="small"
                    class="print-range-date"
                    :disabled-date="printScheduleDateDisabled"
                  />
                </el-form-item>
                <el-form-item label="周目" class="print-range-field">
                  <el-select
                    v-if="printStartLapOptions.length > 0"
                    v-model="printStartLap"
                    size="small"
                    filterable
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
                  <el-input-number
                    v-else
                    v-model="printStartLap"
                    :min="1"
                    :max="999"
                    :step="1"
                    controls-position="right"
                    size="small"
                    class="print-range-lap-num"
                  />
                </el-form-item>
              </div>
            </section>
            <div class="print-range-flow__sep" aria-hidden="true">〜</div>
            <section class="print-range-block">
              <span class="print-range-block__tag print-range-block__tag--end">終了</span>
              <div class="print-range-block__fields">
                <el-form-item label="日付" class="print-range-field">
                  <el-date-picker
                    v-model="printEndDate"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="終了日"
                    size="small"
                    class="print-range-date"
                    :disabled-date="printScheduleDateDisabled"
                  />
                </el-form-item>
                <el-form-item label="周目" class="print-range-field">
                  <el-select
                    v-if="printEndLapOptions.length > 0"
                    v-model="printEndLap"
                    size="small"
                    filterable
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
                  <el-input-number
                    v-else
                    v-model="printEndLap"
                    :min="1"
                    :max="999"
                    :step="1"
                    controls-position="right"
                    size="small"
                    class="print-range-lap-num"
                  />
                </el-form-item>
              </div>
            </section>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="print-range-footer">
          <el-button class="print-range-footer__cancel" size="small" @click="printScheduleDialogVisible = false">
            キャンセル
          </el-button>
          <el-button class="print-range-footer__submit" type="primary" size="small" @click="confirmPrintSchedule">
            <el-icon class="print-range-footer__submit-icon"><Printer /></el-icon>
            印刷
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="lapStartTimeDialogVisible"
      title="開始時刻の変更"
      width="360px"
      class="jig-drop-dialog lap-time-edit-dialog"
      destroy-on-close
      align-center
    >
      <div class="jd-body">
        <p class="jig-drop-dialog-hint">
          第{{ lapDisplayNo(lapStartTimeEditLapNo) }}周目の開始時刻を選択してください。
        </p>
        <el-form label-position="top" size="small" class="jd-form" @submit.prevent="confirmLapStartTimeEdit">
          <el-form-item label="開始時刻" class="jd-field">
            <el-time-picker
              v-model="lapStartTimeEditValue"
              format="HH:mm"
              value-format="HH:mm"
              placeholder="時刻"
              class="al-control al-time"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="jd-footer">
          <el-button text class="jd-footer__cancel" @click="lapStartTimeDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" @click="confirmLapStartTimeEdit">確定</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="templateDialogVisible"
      width="760px"
      class="append-layout-dialog"
      destroy-on-close
      align-center
      :show-close="true"
      @opened="onAppendLayoutDialogOpened"
      @closed="onAppendLayoutDialogClosed"
    >
      <template #header="{ titleId, titleClass }">
        <div class="al-header">
          <h4 :id="titleId" :class="titleClass" class="al-header-title">追加レイアウト</h4>
          <span class="al-header__sub">左で条件を設定、右で予定時刻を確認</span>
        </div>
      </template>
      <div class="al-shell">
        <aside class="al-panel al-panel--form">
          <div class="al-panel__main">
          <div
            v-if="layoutBoardReady && layoutMaxLaps > 0"
            class="al-context"
          >
            <span class="al-tag">表示中 {{ layoutMaxLaps }} 周</span>
            <span class="al-tag al-tag--info">
              {{ tplFormInsertMode === 'insert' ? '指定周の後へ挿入' : '末尾へ追加' }}
            </span>
            <span
              v-if="tplAppendSuggestedLabel && tplFormInsertMode === 'append'"
              class="al-tag al-tag--suggest"
            >次 {{ tplAppendSuggestedLabel }}</span>
          </div>
          <el-form label-position="top" size="small" class="al-form" @submit.prevent>
            <el-form-item
              v-if="layoutBoardReady && layoutMaxLaps > 0"
              label="追加方法"
              class="al-field al-field--full"
            >
              <el-radio-group v-model="tplFormInsertMode" class="al-insert-mode">
                <el-radio value="append">末尾に追加</el-radio>
                <el-radio value="insert">周目の後に挿入</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item
              v-if="tplFormInsertMode === 'insert' && layoutBoardReady"
              label="挿入位置"
              class="al-field al-field--full"
            >
              <el-select
                v-model="tplFormInsertAfterLapNo"
                filterable
                class="al-control al-select-full"
                placeholder="周目を選択"
              >
                <el-option
                  v-for="opt in tplInsertAnchorOptions"
                  :key="opt.lap_no"
                  :label="opt.label"
                  :value="opt.lap_no"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="計画日" class="al-field al-field--full">
              <el-date-picker
                v-model="tplFormPlanDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="日付"
                class="al-control al-date"
              />
            </el-form-item>
            <div class="al-grid">
              <el-form-item label="開始時刻" class="al-field">
                <el-time-picker
                  v-model="tplFormStartTime"
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="時刻"
                  class="al-control al-time"
                />
              </el-form-item>
              <el-form-item label="1段（分）" class="al-field">
                <el-input-number
                  v-model="tplFormMinutesPerLap"
                  :min="1"
                  :max="600"
                  :step="5"
                  controls-position="right"
                  class="al-control al-num"
                />
              </el-form-item>
              <el-form-item label="1周の列数" class="al-field">
                <el-input-number
                  v-model="tplFormJigsPerLap"
                  :min="1"
                  :max="300"
                  :step="1"
                  controls-position="right"
                  class="al-control al-num"
                />
              </el-form-item>
              <el-form-item :label="layoutBoardReady ? '追加段数' : '段数'" class="al-field">
                <el-input-number
                  v-model="tplFormMaxLaps"
                  :min="1"
                  :max="500"
                  :step="1"
                  controls-position="right"
                  class="al-control al-num"
                />
              </el-form-item>
            </div>
          </el-form>
          <p v-if="tplAppendLayoutDuplicate" class="al-duplicate-hint">
            同じ計画日・開始時刻のレイアウトがあります。日付または開始時刻を変更してください。
          </p>
          </div>
          <div class="al-panel__foot">
            <el-button
              type="primary"
              class="al-submit-btn"
              :disabled="tplAppendLayoutDuplicate"
              @click="confirmAppendLayout"
            >
              <el-icon class="al-submit-btn__icon"><Plus /></el-icon>
              追加する
            </el-button>
          </div>
        </aside>
        <section class="al-panel al-panel--preview">
          <div class="al-preview">
            <div class="al-preview__head">
              <span class="al-preview__title">予定時刻</span>
              <span v-if="tplLapSchedulePreview.length > 0" class="al-preview__badge">
                {{ tplLapSchedulePreview.length }} 段
              </span>
            </div>
            <div ref="appendLayoutPreviewBodyRef" class="al-preview__body">
              <div v-if="tplLapSchedulePreview.length > 0" class="al-preview__table-host">
                <el-table
                  :data="tplLapSchedulePreview"
                  size="small"
                  class="al-preview-table"
                  :show-header="true"
                  :height="appendLayoutPreviewTableHeight"
                >
                  <el-table-column prop="board_lap_no" label="周" width="42" align="center" />
                  <el-table-column prop="lap_no" label="段" width="38" align="center" />
                  <el-table-column prop="work_date_label" label="日付" min-width="76" align="center" show-overflow-tooltip />
                  <el-table-column prop="start" label="開始" width="50" align="center" />
                  <el-table-column prop="end" label="終了" width="50" align="center" />
                </el-table>
              </div>
              <div v-else class="al-preview-empty">
                <span class="al-preview-empty__icon" aria-hidden="true">⏱</span>
                <p>計画日・開始時刻・段数を入力すると<br />予定時刻が表示されます</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </el-dialog>

    <el-dialog
      v-model="platingJigMasterDialogVisible"
      width="720px"
      class="plating-jig-master-dialog"
      align-center
      destroy-on-close
      :show-close="true"
      @opened="loadPlatingJigMasterList"
    >
      <template #header="{ titleId, titleClass }">
        <div class="pjm-header">
          <span class="pjm-header__icon-wrap" aria-hidden="true">
            <el-icon class="pjm-header__icon"><EditPen /></el-icon>
          </span>
          <div>
            <h4 :id="titleId" :class="titleClass" class="pjm-header-title">メッキ治具 — 設備使用数編集</h4>
            <p class="pjm-header__sub">使用可能数・稼働状態の確認と更新</p>
          </div>
        </div>
      </template>
      <div class="pjm-body">
        <div class="pjm-toolbar">
          <el-input
            v-model="pjmKeyword"
            size="small"
            clearable
            placeholder="コード・名称で検索"
            class="pjm-search"
            :prefix-icon="Search"
          />
          <div class="pjm-toolbar__actions">
            <el-button class="pjm-btn pjm-btn--primary" size="small" type="primary" @click="openPlatingJigMasterForm()">
              <el-icon class="pjm-btn__icon"><Plus /></el-icon>
              新規登録
            </el-button>
            <el-button
              class="pjm-btn pjm-btn--secondary"
              size="small"
              :loading="pjmLoading"
              @click="loadPlatingJigMasterList"
            >
              再読込
            </el-button>
          </div>
        </div>
        <div class="pjm-table-card">
          <el-table
            v-loading="pjmLoading"
            :data="pjmFilteredList"
            size="small"
            stripe
            class="pjm-table"
            max-height="340"
            empty-text="メッキ設備がありません"
          >
            <el-table-column prop="machine_cd" label="設備CD" width="96" show-overflow-tooltip />
            <el-table-column prop="machine_name" label="設備名" min-width="128" show-overflow-tooltip />
            <el-table-column prop="available_qty" label="使用可能数" width="88" align="center">
              <template #default="{ row }">
                <span class="pjm-qty">{{ row.available_qty != null ? row.available_qty : '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状態" width="168" align="center">
              <template #default="{ row }">
                <el-radio-group
                  :model-value="normalizePjmStatus(row.status)"
                  size="small"
                  class="pjm-status-toggle"
                  :disabled="row.id == null || pjmStatusSavingId === row.id"
                  @change="(v) => onPjmStatusChange(row, v == null ? 'active' : String(v))"
                >
                  <el-radio-button value="active">稼働</el-radio-button>
                  <el-radio-button value="maintenance">保守</el-radio-button>
                  <el-radio-button value="inactive">停止</el-radio-button>
                </el-radio-group>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="備考" min-width="96" show-overflow-tooltip />
            <el-table-column label="操作" width="72" align="center" fixed="right" class-name="pjm-op-col" header-align="center">
              <template #default="{ row }">
                <el-button class="pjm-row-edit" size="small" type="primary" link @click="openPlatingJigMasterForm(row)">
                  <el-icon><EditPen /></el-icon>
                  編集
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <div class="pjm-footer">
          <el-button class="pjm-close-btn" @click="platingJigMasterDialogVisible = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <MachineForm
      v-model:visible="pjmFormVisible"
      :data="pjmEditData"
      lock-machine-type="メッキ"
      @refresh="onPlatingJigMasterSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import Sortable from 'sortablejs'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Delete,
  DocumentCopy,
  EditPen,
  Grid,
  Plus,
  Printer,
  Search,
} from '@element-plus/icons-vue'
import {
  getMachineList,
  updateMachine,
  type MachineListResponse,
} from '@/api/master/machineMaster'
import MachineForm from '@/views/master/machine/MachineForm.vue'
import type { MachineItem } from '@/types/master'
import {
  createPlatingDraft,
  fetchPlatingDraftById,
  fetchLatestPlatingDraftByDate,
  fetchPlatingBoardView,
  fetchPlatingSummaryPair,
  updatePlatingDraft,
  type PlatingBoardCardBody,
  type PlatingBoardCardOut,
  type PlatingBoardDateMemoBody,
  type PlatingBoardDateMemoOut,
  type PlatingDraftItemBody,
  type PlatingDraftItemOut,
  type PlatingDraftLayoutBody,
  type PlatingDraftLayoutOut,
  type PlatingDraftOut,
} from '@/api/platingPlanning'
import {
  fetchEquipmentEfficiencyList,
  type EquipmentEfficiency,
} from '@/api/master/equipmentEfficiencyMaster'
import PlatingFloatingPanel from '@/views/aps/productionPlanCreation/plating/PlatingFloatingPanel.vue'
import PlatingLeftInventoryPane from '@/views/aps/productionPlanCreation/plating/PlatingLeftInventoryPane.vue'
import PlatingRightGenPane from '@/views/aps/productionPlanCreation/plating/PlatingRightGenPane.vue'

defineOptions({ name: 'PlatingPlanning' })

/** メッキ計画画面の暦日は日本（JST）基準（他拠点ブラウザでも同日付が揃う） */
const TZ_JP = 'Asia/Tokyo'

function todayYmdJapan(): string {
  return dayjs().tz(TZ_JP).format('YYYY-MM-DD')
}

function addDaysYmdJapan(isoYmd: string, days: number): string {
  return dayjs.tz(isoYmd, TZ_JP).add(days, 'day').format('YYYY-MM-DD')
}

function shiftYmdJapan(isoYmd: string | undefined | null, days: number): string {
  const base = (isoYmd || '').trim() || todayYmdJapan()
  return addDaysYmdJapan(base, days)
}

/** 下書き明細の work_date のうち件数が最大の日付（同数なら早い日付） */
function dominantWorkDateFromItems(items: { work_date: string }[]): string {
  const counts = new Map<string, number>()
  for (const it of items) {
    const d = (it.work_date || '').trim()
    if (!d) continue
    counts.set(d, (counts.get(d) || 0) + 1)
  }
  if (counts.size === 0) return todayYmdJapan()
  let best = ''
  let bestC = -1
  for (const [d, c] of counts) {
    if (c > bestC || (c === bestC && d < best)) {
      best = d
      bestC = c
    }
  }
  return best || todayYmdJapan()
}

/** バックエンド _items_filter_for_work_date と同様：work_date が NULL のときは plan_date 当日とみなす */
function effectiveItemWorkDate(it: { work_date?: string | null }, planDate: string): string {
  const w = it.work_date
  if (w == null || w === '') return planDate
  return String(w).slice(0, 10)
}

function apiItemToBody(it: PlatingDraftItemOut): PlatingDraftItemBody {
  return {
    sort_order: it.sort_order,
    work_date: it.work_date ?? null,
    product_cd: it.product_cd,
    product_name: it.product_name,
    plating_machine: it.plating_machine,
    kake: it.kake,
    qty: it.qty,
    slots: it.slots,
    source_type: it.source_type,
    source_row_key: it.source_row_key ?? null,
  }
}

function apiBoardCardToBody(bc: PlatingBoardCardOut): PlatingBoardCardBody {
  return {
    lap_work_date: boardCardLapWorkDate(bc),
    lap_start_time: bc.lap_start_time ?? null,
    lap_end_time: bc.lap_end_time ?? null,
    lap_no: bc.lap_no,
    turn_seq: bc.turn_seq,
    product_cd: bc.product_cd,
    product_name: bc.product_name,
    plating_machine: bc.plating_machine,
    kake: bc.kake,
    qty: bc.qty,
    slots: bc.slots,
    board_mark: bc.board_mark,
    stable_key: bc.stable_key ?? null,
    until_depleted: bc.until_depleted ?? false,
    text_red: bc.text_red ?? false,
  }
}

type BoardMark = 'standard' | 'manual' | 'rush'

interface ScheduleCard {
  id: string
  product_cd: string
  product_name: string
  plating_machine: string
  kake: number
  qty: number
  slots: number
  /** ボード表示用の周目（レイアウト上の周番号。読込時は persist と揃える） */
  lap_no: number
  /** API 保存時の元 lap_no（draft 内） */
  persist_lap_no?: number
  /** aps_plating_plan_board_cards.lap_work_date（表示期間フィルタの基準） */
  lap_work_date?: string
  lap_start_time?: string | null
  lap_end_time?: string | null
  /** 他 plan_date の draft から読み込んだ行 */
  source_draft_id?: number
  turn_seq: number
  colorIdx: number
  boardMark: BoardMark
  /** 数量非表示（無くなり次第）；表示は「無くなり次第」とし合計には実数を加算 */
  untilDepleted?: boolean
  /** ボード上の製品名・数量を赤字で強調表示 */
  forceRedText?: boolean
}

const scheduleCards = ref<ScheduleCard[]>([])
const standardPositions = ref(new Map<string, { lap_no: number; turn_seq: number }>())
/** API から③ボードを復元する／読込でボードを空にするとき、deep watch による不要な自動保存を抑止 */
const isBoardHydratingFromApi = ref(false)
/** 空枠補完・一括同期中は watch による自動保存・Sortable 再初期化を抑止 */
let suppressScheduleSideEffects = 0
function withSuppressedScheduleSideEffects<T>(fn: () => T): T {
  suppressScheduleSideEffects += 1
  try {
    return fn()
  } finally {
    suppressScheduleSideEffects -= 1
  }
}

const TABLE_H = 340
const FLOAT_TABLE_H = 300

const DEFAULT_JIGS_PER_LAP = 129

/** ①ボード既定表示：本日のみ（JST） */
function defaultBoardFilterRange(): { from: string; to: string } {
  const today = todayYmdJapan()
  return { from: today, to: today }
}

const boardFilterFrom = ref(defaultBoardFilterRange().from)
const boardFilterTo = ref(defaultBoardFilterRange().to)
const boardPeriodFilterLoading = ref(false)
/** メッキ投入ボードのデータ取得中（初回・期間変更・作業日変更） */
const boardTableLoading = computed(() => loadingDraft.value || boardPeriodFilterLoading.value)

const boardViewRange = computed(() => {
  let from = (boardFilterFrom.value || '').trim().slice(0, 10)
  let to = (boardFilterTo.value || '').trim().slice(0, 10)
  if (!from || !to) return defaultBoardFilterRange()
  if (from > to) {
    const t = from
    from = to
    to = t
  }
  return { from, to }
})

const boardFilterDateRange = computed({
  get(): [string, string] {
    const { from, to } = boardViewRange.value
    return [from, to]
  },
  set(v: [string, string] | null | undefined) {
    if (!v || v.length < 2) return
    boardFilterFrom.value = String(v[0] || '').slice(0, 10)
    boardFilterTo.value = String(v[1] || '').slice(0, 10)
  },
})

const boardViewRangeLabel = computed(() => {
  const { from, to } = boardViewRange.value
  return `${formatBoardDateLabel(from)}〜${formatBoardDateLabel(to)}`
})

let boardViewRangeReloadTimer: ReturnType<typeof setTimeout> | null = null
let boardViewRangeReady = false
/** setBoardViewRangeToday 等で即時再取得する際、watch による二重読込を抑止 */
let skipBoardViewRangeWatchOnce = false

function cancelBoardViewRangeReload() {
  if (boardViewRangeReloadTimer != null) {
    clearTimeout(boardViewRangeReloadTimer)
    boardViewRangeReloadTimer = null
  }
}

/** 表示期間変更時にボードデータを自動再取得（反映ボタン不要） */
async function reloadBoardForViewRange() {
  const { from, to } = boardViewRange.value
  boardFilterFrom.value = from
  boardFilterTo.value = to
  boardPeriodFilterLoading.value = true
  try {
    await loadLatestDraft({ autoMode: true, autoSyncWorkDate: false })
  } finally {
    boardPeriodFilterLoading.value = false
  }
}

function scheduleBoardViewRangeReload() {
  if (!boardViewRangeReady) return
  cancelBoardViewRangeReload()
  boardViewRangeReloadTimer = setTimeout(() => {
    boardViewRangeReloadTimer = null
    void reloadBoardForViewRange()
  }, 280)
}

function shiftBoardViewRange(days: number) {
  const { from, to } = boardViewRange.value
  boardFilterFrom.value = shiftYmdJapan(from, days)
  boardFilterTo.value = shiftYmdJapan(to, days)
}

/** 表示期間の開始・終了をともに本日（JST）にし、データを自動再取得 */
async function setBoardViewRangeToday() {
  cancelBoardViewRangeReload()
  const today = todayYmdJapan()
  skipBoardViewRangeWatchOnce = true
  boardFilterFrom.value = today
  boardFilterTo.value = today
  if (draftWorkDate.value !== today) {
    syncingDraftWorkDateFromLoad.value = true
    draftWorkDate.value = today
    await nextTick()
    syncingDraftWorkDateFromLoad.value = false
  }
  if (!boardViewRangeReady) return
  await reloadBoardForViewRange()
}

function onBoardViewRangeChange(v: [string, string] | null | undefined) {
  if (!v || v.length < 2 || !v[0] || !v[1]) return
  boardFilterFrom.value = String(v[0]).slice(0, 10)
  boardFilterTo.value = String(v[1]).slice(0, 10)
}

function enumerateYmdRange(from: string, to: string): string[] {
  const out: string[] = []
  let d = from
  while (d <= to) {
    out.push(d)
    if (d === to) break
    d = addDaysYmdJapan(d, 1)
  }
  return out
}

function isYmdInBoardView(ymd: string | null | undefined): boolean {
  const d = (ymd || '').trim().slice(0, 10)
  if (!d) return false
  const { from, to } = boardViewRange.value
  return d >= from && d <= to
}

function boardCardLapWorkDate(bc: { lap_work_date?: string | null }): string {
  return String(bc.lap_work_date ?? '').slice(0, 10)
}

/** 表示期間内の board_cards から周目番号集合を構築（layout 照合は persist lap_no を優先） */
function boardLapNosInViewFromCards(
  boardCards: Array<{ lap_no: number; persist_lap_no?: number; lap_work_date?: string | null }>,
): Set<number> {
  const set = new Set<number>()
  for (const bc of boardCards) {
    const wd = boardCardLapWorkDate(bc)
    if (!wd || !isYmdInBoardView(wd)) continue
    const persist = Math.max(1, Math.floor(Number(bc.persist_lap_no ?? bc.lap_no) || 0))
    set.add(persist)
  }
  return set
}

function boardLapNosInViewFromScheduleCards(): Set<number> {
  const set = new Set<number>()
  for (const c of scheduleCards.value) {
    const wd = (c.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    set.add(c.lap_no)
    if (c.persist_lap_no) set.add(c.persist_lap_no)
  }
  return set
}

/** 表示期間内に board_cards（qty>0）が存在する周目のみ */
function boardLapNosWithBoardDataInView(): Set<number> {
  const set = new Set<number>()
  for (const c of scheduleCards.value) {
    if (c.qty <= 0) continue
    const wd = (c.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    set.add(c.lap_no)
  }
  return set
}

function layoutBlockCoversAnyLap(block: { base_lap_no: number; lap_count: number }, lapNos: Set<number>): boolean {
  const start = Math.max(1, Math.floor(Number(block.base_lap_no) || 1))
  const end = start + Math.max(1, Math.floor(Number(block.lap_count) || 1)) - 1
  for (let ln = start; ln <= end; ln += 1) {
    if (lapNos.has(ln)) return true
  }
  return false
}

/** layout_blocks から表示期間内の周目番号を構築（カード未配置でもレイアウト行を表示） */
function boardLapNosFromLayoutBlocksInView(): Set<number> {
  const set = new Set<number>()
  for (const block of layoutBlocks.value) {
    const rows = buildLapScheduleRows(
      block.plan_date,
      block.start_time,
      block.minutes_per_lap,
      block.lap_count,
    )
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i]!
      if (!isYmdInBoardView(row.work_date)) continue
      set.add(block.base_lap_no + i)
    }
  }
  return set
}

function buildBoardLapWorkDateMap(): Map<number, string> {
  const map = new Map<number, string>()
  for (const c of scheduleCards.value) {
    const wd = (c.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    map.set(c.lap_no, wd)
  }
  return map
}

/** board_cards の lap_start_time / lap_end_time（周目ラベル表示用） */
function buildBoardLapTimesMap(): Map<number, { start: string; end: string }> {
  const map = new Map<number, { start: string; end: string }>()
  for (const c of scheduleCards.value) {
    if (map.has(c.lap_no)) continue
    const st = String(c.lap_start_time ?? '').trim()
    const en = String(c.lap_end_time ?? '').trim()
    if (!st && !en) continue
    map.set(c.lap_no, {
      start: st ? normalizeBoardStartTimeHm(st) : '',
      end: en ? normalizeBoardStartTimeHm(en) : '',
    })
  }
  return map
}

const lapCardMetaByLap = computed(() => {
  const map = new Map<number, { work_date: string; start: string; end: string }>()
  for (const c of scheduleCards.value) {
    if (map.has(c.lap_no)) continue
    map.set(c.lap_no, {
      work_date: String(c.lap_work_date || '').slice(0, 10),
      start: normalizeBoardStartTimeHm(c.lap_start_time),
      end: normalizeBoardStartTimeHm(c.lap_end_time),
    })
  }
  return map
})

const boardOccupancyIndex = computed(() => {
  const occupiedTurnsByLap = new Map<number, Set<number>>()
  const occupiedQtyByLap = new Map<number, number>()
  const maxTurnByLap = new Map<number, number>()
  const machineQtyByLap = new Map<number, Map<string, number>>()
  const cardsByLapQty = new Map<number, ScheduleCard[]>()
  const skeletonKeySet = new Set<string>()
  for (const c of scheduleCards.value) {
    const lap = Math.max(1, Math.floor(Number(c.lap_no) || 0))
    const turn = Math.max(1, Math.floor(Number(c.turn_seq) || 0))
    const isOccupied = c.qty > 0
    if (isOccupied) {
      const turnSet = occupiedTurnsByLap.get(lap) ?? new Set<number>()
      turnSet.add(turn)
      occupiedTurnsByLap.set(lap, turnSet)
      occupiedQtyByLap.set(lap, (occupiedQtyByLap.get(lap) ?? 0) + 1)
      maxTurnByLap.set(lap, Math.max(maxTurnByLap.get(lap) ?? 0, turn))
      const mKey = normalizeMachineKey(c.plating_machine)
      const mMap = machineQtyByLap.get(lap) ?? new Map<string, number>()
      mMap.set(mKey, (mMap.get(mKey) ?? 0) + 1)
      machineQtyByLap.set(lap, mMap)
      const lapCards = cardsByLapQty.get(lap) ?? []
      lapCards.push(c)
      cardsByLapQty.set(lap, lapCards)
      continue
    }
    if (isEmptySlotProductCd(c.product_cd)) {
      skeletonKeySet.add(`${lap}:${turn}`)
    }
  }
  for (const lapCards of cardsByLapQty.values()) {
    lapCards.sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  }
  return {
    occupiedTurnsByLap,
    occupiedQtyByLap,
    maxTurnByLap,
    machineQtyByLap,
    cardsByLapQty,
    skeletonKeySet,
  }
})

function occupiedQtyOnLap(lapNo: number): number {
  return boardOccupancyIndex.value.occupiedQtyByLap.get(lapNo) ?? 0
}

function lapCardsWithQty(lapNo: number): ScheduleCard[] {
  return boardOccupancyIndex.value.cardsByLapQty.get(lapNo) ?? []
}

function lapScheduleMetaForCard(lapNo: number): {
  lap_work_date?: string
  lap_start_time?: string | null
  lap_end_time?: string | null
} {
  const times = buildBoardLapTimesMap().get(lapNo)
  const slot = currentLayoutLapSchedule().find((s) => s.lap_no === lapNo)
  const cardMeta = lapCardMetaByLap.value.get(lapNo)
  const wd = (cardMeta?.work_date || slot?.work_date || '').slice(0, 10)
  return {
    lap_work_date: wd || undefined,
    lap_start_time: times?.start || slot?.start || cardMeta?.start || null,
    lap_end_time: times?.end || slot?.end || cardMeta?.end || null,
  }
}

function isLapNoInBoardView(lapNo: number, scheduleByLap?: Map<number, LapScheduleSlot>): boolean {
  const fromCard = lapCardMetaByLap.value.get(lapNo)?.work_date
  const wd = (fromCard || scheduleByLap?.get(lapNo)?.work_date || '').slice(0, 10)
  if (!wd) {
    if (layoutBoardReady.value) return false
    return true
  }
  return isYmdInBoardView(wd)
}

function layoutBlocksInBoardView(): BoardLayoutBlock[] {
  const lapNos = new Set<number>([
    ...boardLapNosInViewFromScheduleCards(),
    ...boardLapNosFromLayoutBlocksInView(),
  ])
  if (lapNos.size === 0) return []
  return layoutBlocks.value.filter((b) => layoutBlockCoversAnyLap(b, lapNos))
}

function recomputeLayoutMaxLapsFromSchedule() {
  const sched = globalLapSchedule.value
  if (sched.length > 0) {
    layoutMaxLaps.value = Math.max(...sched.map((s) => s.lap_no))
  }
}

function scheduleCardsForCurrentDraft(): ScheduleCard[] {
  const id = currentDraftId.value
  if (!id) return scheduleCards.value
  return scheduleCards.value.filter((c) => !c.source_draft_id || c.source_draft_id === id)
}

const jigsPerLap = ref(DEFAULT_JIGS_PER_LAP)
const minutesPerLap = ref(100)

/** ①ボード：追加レイアウトで積み上げる周目ブロック */
interface BoardLayoutBlock {
  plan_date: string
  start_time: string
  minutes_per_lap: number
  jigs_per_lap: number
  lap_count: number
  base_lap_no: number
}

const templateDialogVisible = ref(false)
const tplFormPlanDate = ref(todayYmdJapan())
const tplFormStartTime = ref('08:00')
const tplFormMinutesPerLap = ref(100)
const tplFormJigsPerLap = ref(DEFAULT_JIGS_PER_LAP)
const tplFormMaxLaps = ref(1)
/** 末尾追加 | 指定周目の後に挿入 */
const tplFormInsertMode = ref<'append' | 'insert'>('append')
const tplFormInsertAfterLapNo = ref(1)
const layoutBoardReady = ref(false)
const layoutBlocks = ref<BoardLayoutBlock[]>([])
const layoutPlanDate = ref(todayYmdJapan())
const layoutStartTime = ref('08:00')
const layoutMinutesPerLap = ref(100)
const layoutJigsPerLap = ref(DEFAULT_JIGS_PER_LAP)
const layoutMaxLaps = ref(1)

const DEFAULT_BOARD_START_TIME = '08:00'

function normalizeBoardStartTimeHm(v: string | null | undefined): string {
  const s = String(v ?? '').trim()
  const m = s.match(/^(\d{1,2}):(\d{2})$/)
  if (!m) return DEFAULT_BOARD_START_TIME
  const h = Math.min(23, Math.max(0, Number(m[1])))
  const min = Math.min(59, Math.max(0, Number(m[2])))
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

interface LapScheduleSlot {
  lap_no: number
  work_date: string
  work_date_label: string
  start: string
  end: string
}

function formatBoardDateLabel(ymd: string): string {
  const d = dayjs.tz(ymd, 'YYYY-MM-DD', TZ_JP)
  if (!d.isValid()) return ymd
  return d.format('M/D（ddd）')
}

function buildLapScheduleRows(
  planDate: string,
  startTime: string,
  minutesPerSegment: number,
  lapCount: number,
): LapScheduleSlot[] {
  const d = (planDate || '').trim()
  const t = normalizeBoardStartTimeHm(startTime)
  const cycle = Math.max(1, Math.floor(Number(minutesPerSegment) || 1))
  const laps = Math.max(1, Math.floor(Number(lapCount) || 1))
  if (!d) return []
  const base = dayjs.tz(`${d} ${t}`, 'YYYY-MM-DD HH:mm', TZ_JP)
  if (!base.isValid()) return []
  return Array.from({ length: laps }, (_, i) => {
    const lapNo = i + 1
    const startDt = base.add((lapNo - 1) * cycle, 'minute')
    const endDt = startDt.add(cycle, 'minute')
    const workDate = startDt.format('YYYY-MM-DD')
    return {
      lap_no: lapNo,
      work_date: workDate,
      work_date_label: formatBoardDateLabel(workDate),
      start: startDt.format('HH:mm'),
      end: endDt.format('HH:mm'),
    }
  })
}

function buildGlobalLapScheduleInner(): LapScheduleSlot[] {
  if (!layoutBoardReady.value) return []

  const lapNosWithData = boardLapNosWithBoardDataInView()
  const targetLapNos = new Set<number>([
    ...boardLapNosFromLayoutBlocksInView(),
    ...lapNosWithData,
    ...boardLapNosInViewFromScheduleCards(),
  ])
  if (targetLapNos.size === 0) return []

  const lapDateMap = buildBoardLapWorkDateMap()
  const lapTimesMap = buildBoardLapTimesMap()
  const lapCardMeta = lapCardMetaByLap.value
  const layoutSlotByLap = new Map<number, LapScheduleSlot>()
  for (const block of layoutBlocksInBoardView()) {
    const rows = buildLapScheduleRows(
      block.plan_date,
      block.start_time,
      block.minutes_per_lap,
      block.lap_count,
    )
    for (const r of rows) {
      const lapNo = block.base_lap_no + r.lap_no - 1
      if (!targetLapNos.has(lapNo)) continue
      layoutSlotByLap.set(lapNo, { ...r, lap_no: lapNo })
    }
  }

  const sortMap = new Map<number, LapScheduleSlot>()
  for (const ln of targetLapNos) {
    const layout = layoutSlotByLap.get(ln)
    const wd = (lapDateMap.get(ln) || layout?.work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    const times = lapTimesMap.get(ln)
    const start =
      times?.start ||
      layout?.start ||
      lapCardMeta.get(ln)?.start
    const end =
      times?.end ||
      layout?.end ||
      lapCardMeta.get(ln)?.end
    sortMap.set(ln, {
      lap_no: ln,
      work_date: wd,
      work_date_label: formatBoardDateLabel(wd),
      start: start || '08:00',
      end: end || start || '09:00',
    })
  }
  const result: LapScheduleSlot[] = []
  for (const ln of [...sortMap.keys()].sort((a, b) => compareLapNoForBoardSort(a, b, sortMap))) {
    const slot = sortMap.get(ln)
    if (slot) result.push(slot)
  }
  return result
}

/** 周次スケジュール（layout + board_cards）— 同一 tick 内の重複計算を抑止 */
const globalLapSchedule = computed(() => buildGlobalLapScheduleInner())

function currentLayoutLapSchedule(): LapScheduleSlot[] {
  return globalLapSchedule.value
}

/** 計画日（lap_work_date）ごとに 1 から振り直した表示用周番号（同一日内は開始時刻順） */
const lapDisplayNoMap = computed(() => {
  const map = new Map<number, number>()
  const schedule = globalLapSchedule.value
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const byDate = new Map<string, number[]>()
  for (const s of schedule) {
    const list = byDate.get(s.work_date) ?? []
    list.push(s.lap_no)
    byDate.set(s.work_date, list)
  }
  for (const laps of byDate.values()) {
    const sorted = [...laps].sort((a, b) => compareLapNoForBoardSort(a, b, scheduleByLap))
    sorted.forEach((lapNo, idx) => map.set(lapNo, idx + 1))
  }
  return map
})

function lapDisplayNo(lapNo: number): number {
  return lapDisplayNoMap.value.get(lapNo) ?? lapNo
}

const layoutBlocksSummary = computed(() => {
  if (layoutBlocks.value.length === 0) {
    return layoutBoardReady.value ? formatBoardDateLabel(layoutPlanDate.value) : '—'
  }
  return layoutBlocksInBoardView()
    .map((b) => `${formatBoardDateLabel(b.plan_date)}×${b.lap_count}`)
    .join('＋')
})

/** 予定時刻プレビュー：表頭1行＋データ8行分（超過時はテーブル内スクロール） */
const APPEND_LAYOUT_PREVIEW_HEADER_PX = 34
const APPEND_LAYOUT_PREVIEW_ROW_PX = 28
const APPEND_LAYOUT_PREVIEW_VISIBLE_ROWS = 8
const appendLayoutPreviewTableMaxHeight =
  APPEND_LAYOUT_PREVIEW_HEADER_PX + APPEND_LAYOUT_PREVIEW_ROW_PX * APPEND_LAYOUT_PREVIEW_VISIBLE_ROWS

const appendLayoutPreviewBodyRef = ref<HTMLElement | null>(null)
const appendLayoutPreviewTableHeight = ref(appendLayoutPreviewTableMaxHeight)
let appendLayoutPreviewResizeObs: ResizeObserver | null = null

function updateAppendLayoutPreviewTableHeight() {
  const el = appendLayoutPreviewBodyRef.value
  if (!el) return
  const h = Math.floor(el.clientHeight)
  if (h > 0) {
    appendLayoutPreviewTableHeight.value = Math.max(appendLayoutPreviewTableMaxHeight, h)
  }
}

function setupAppendLayoutPreviewResize() {
  teardownAppendLayoutPreviewResize()
  const el = appendLayoutPreviewBodyRef.value
  if (!el) return
  appendLayoutPreviewResizeObs = new ResizeObserver(() => updateAppendLayoutPreviewTableHeight())
  appendLayoutPreviewResizeObs.observe(el)
}

function teardownAppendLayoutPreviewResize() {
  appendLayoutPreviewResizeObs?.disconnect()
  appendLayoutPreviewResizeObs = null
}

function onAppendLayoutDialogOpened() {
  void nextTick(() => {
    updateAppendLayoutPreviewTableHeight()
    setupAppendLayoutPreviewResize()
  })
}

function onAppendLayoutDialogClosed() {
  teardownAppendLayoutPreviewResize()
}

const tplLapSchedulePreview = computed(() => {
  const rows = buildLapScheduleRows(
    tplFormPlanDate.value,
    tplFormStartTime.value,
    tplFormMinutesPerLap.value,
    tplFormMaxLaps.value,
  )
  const baseLap =
    layoutBoardReady.value && layoutMaxLaps.value > 0 ? Math.max(0, Math.floor(layoutMaxLaps.value)) : 0
  return rows.map((r) => ({ ...r, board_lap_no: baseLap + r.lap_no }))
})

watch(
  [
    templateDialogVisible,
    tplLapSchedulePreview,
    tplFormInsertMode,
    tplFormPlanDate,
    tplFormMaxLaps,
    layoutMaxLaps,
  ],
  () => {
    if (!templateDialogVisible.value) return
    void nextTick(() => updateAppendLayoutPreviewTableHeight())
  },
)

function layoutBlockEndDateTime(block: BoardLayoutBlock) {
  const rows = buildLapScheduleRows(
    block.plan_date,
    block.start_time,
    block.minutes_per_lap,
    block.lap_count,
  )
  if (rows.length === 0) {
    return dayjs.tz(
      `${block.plan_date} ${normalizeBoardStartTimeHm(block.start_time)}`,
      'YYYY-MM-DD HH:mm',
      TZ_JP,
    )
  }
  const last = rows[rows.length - 1]
  const startDt = dayjs.tz(`${last.work_date} ${last.start}`, 'YYYY-MM-DD HH:mm', TZ_JP)
  const cycle = Math.max(1, Math.floor(Number(block.minutes_per_lap) || 1))
  return startDt.add(cycle, 'minute')
}

function getLatestLayoutEndDateTime() {
  const blocks = layoutBlocks.value
  if (blocks.length === 0) return null
  let latest: dayjs.Dayjs | null = null
  for (const b of blocks) {
    const end = layoutBlockEndDateTime(b)
    if (!latest || end.isAfter(latest)) latest = end
  }
  return latest
}

function layoutBlockStartKey(planDate: string, startTime: string): string {
  return `${String(planDate || '').slice(0, 10)}|${normalizeBoardStartTimeHm(startTime)}`
}

function findDuplicateLayoutBlock(planDate: string, startTime: string): BoardLayoutBlock | null {
  const key = layoutBlockStartKey(planDate, startTime)
  return (
    layoutBlocks.value.find(
      (b) => layoutBlockStartKey(b.plan_date, b.start_time) === key,
    ) ?? null
  )
}

const tplAppendLayoutDuplicate = computed(() => {
  if (tplFormInsertMode.value === 'insert') return false
  const planDate = (tplFormPlanDate.value || '').trim()
  if (!planDate) return false
  return findDuplicateLayoutBlock(planDate, tplFormStartTime.value) != null
})

const tplInsertAnchorOptions = computed(() => {
  if (!layoutBoardReady.value) return []
  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  return [...schedule]
    .sort((a, b) => compareLapNoForBoardSort(a.lap_no, b.lap_no, scheduleByLap))
    .map((s) => ({
      lap_no: s.lap_no,
      label: `第${lapDisplayNoMap.value.get(s.lap_no) ?? s.lap_no}周目 ${s.work_date_label} ${s.start}–${s.end}`,
    }))
})

const tplAppendSuggestedLabel = ref('')

function computeNextAppendLayoutDefaults(): {
  planDate: string
  startTime: string
  minutesPerLap: number
  jigsPerLap: number
  maxLaps: number
  suggestedLabel: string
} {
  const d = boardLapsPerDay.value
  const fallbackMaxLaps = Math.max(1, Math.min(500, d > 0 ? d : 1))
  if (!layoutBoardReady.value) {
    const planDate = draftWorkDate.value || todayYmdJapan()
    return {
      planDate,
      startTime: DEFAULT_BOARD_START_TIME,
      minutesPerLap: minutesPerLap.value,
      jigsPerLap: jigsPerLap.value,
      maxLaps: fallbackMaxLaps,
      suggestedLabel: '',
    }
  }

  const blocks = [...layoutBlocks.value].sort((a, b) => a.base_lap_no - b.base_lap_no)
  const lastBlock = blocks[blocks.length - 1]
  const minutes = lastBlock?.minutes_per_lap ?? layoutMinutesPerLap.value
  const jigs = lastBlock?.jigs_per_lap ?? layoutJigsPerLap.value

  const endDt = getLatestLayoutEndDateTime()
  if (endDt?.isValid()) {
    const planDate = endDt.format('YYYY-MM-DD')
    const startTime = endDt.format('HH:mm')
    return {
      planDate,
      startTime,
      minutesPerLap: minutes,
      jigsPerLap: jigs,
      maxLaps: 1,
      suggestedLabel: `${formatBoardDateLabel(planDate)} ${startTime}`,
    }
  }

  const planDate = layoutPlanDate.value || draftWorkDate.value || todayYmdJapan()
  return {
    planDate,
    startTime: layoutStartTime.value,
    minutesPerLap: minutes,
    jigsPerLap: jigs,
    maxLaps: 1,
    suggestedLabel: '',
  }
}

/** layout_blocks 読込後：表示用の週目設定を先頭ブロックに合わせる */
function applyLayoutHeaderFromFirstBlock() {
  const first = [...layoutBlocks.value].sort((a, b) => a.base_lap_no - b.base_lap_no)[0]
  if (!first) return
  layoutPlanDate.value = first.plan_date
  layoutStartTime.value = normalizeBoardStartTimeHm(first.start_time)
  layoutMinutesPerLap.value = first.minutes_per_lap
  layoutJigsPerLap.value = first.jigs_per_lap
}

function inferLayoutBlocksFromBoard(
  rawBoard: Array<{
    lap_no: number
    persist_lap_no?: number
    lap_work_date?: string | null
    lap_start_time?: string | null
    lap_end_time?: string | null
  }>,
  header: {
    plan_date: string
    board_start_time: string
    minutes_per_lap: number
    jigs_per_lap: number
    max_laps: number
  },
): BoardLayoutBlock[] {
  const lapMeta = new Map<number, { wd: string; start: string }>()
  for (const bc of rawBoard) {
    const ln = Math.max(1, Math.floor(Number(bc.persist_lap_no ?? bc.lap_no) || 0))
    if (lapMeta.has(ln)) continue
    const wd = String(bc.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    const start = normalizeBoardStartTimeHm(bc.lap_start_time || header.board_start_time)
    lapMeta.set(ln, { wd, start })
  }
  const lapNos = [...lapMeta.keys()].sort((a, b) => a - b)
  if (lapNos.length === 0) return []

  const blocks: BoardLayoutBlock[] = []
  let idx = 0
  while (idx < lapNos.length) {
    const startLap = lapNos[idx]!
    const meta = lapMeta.get(startLap)!
    let j = idx
    while (j + 1 < lapNos.length) {
      const cur = lapNos[j]!
      const nextLap = lapNos[j + 1]!
      const nextMeta = lapMeta.get(nextLap)!
      if (nextLap !== cur + 1 || nextMeta.wd !== meta.wd) break
      j += 1
    }
    const endLap = lapNos[j]!
    blocks.push({
      plan_date: meta.wd,
      start_time: normalizeBoardStartTimeHm(meta.start),
      minutes_per_lap: header.minutes_per_lap,
      jigs_per_lap: header.jigs_per_lap,
      lap_count: endLap - startLap + 1,
      base_lap_no: startLap,
    })
    idx = j + 1
  }
  return blocks
}

function lapTimeRangeLabel(lapNo: number): string {
  const times = buildBoardLapTimesMap().get(lapNo)
  if (times?.start && times?.end) return `${times.start}–${times.end}`
  if (times?.start) return `${times.start}–`
  if (times?.end) return `–${times.end}`
  const row = currentLayoutLapSchedule().find((r) => r.lap_no === lapNo)
  return row?.start && row?.end ? `${row.start}–${row.end}` : ''
}

function applyLapStartTimeAndCascade(lapNo: number, newStartHm: string): boolean {
  if (!layoutBoardReady.value || layoutBlocks.value.length === 0) return false
  const scheduleBefore = currentLayoutLapSchedule()
  const currentSlot = scheduleBefore.find((r) => r.lap_no === lapNo)
  if (!currentSlot) return false
  const sortedBlocks = [...layoutBlocks.value]
    .map((b) => ({ ...b }))
    .sort((a, b) => a.base_lap_no - b.base_lap_no)
  const targetBlock = sortedBlocks.find(
    (b) => lapNo >= b.base_lap_no && lapNo <= b.base_lap_no + Math.max(1, Math.floor(Number(b.lap_count) || 1)) - 1,
  )
  if (!targetBlock) return false
  const cycleByLap = new Map<number, number>()
  const jigsByLap = new Map<number, number>()
  for (const b of sortedBlocks) {
    const laps = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const cycle = Math.max(1, Math.floor(Number(b.minutes_per_lap) || 1))
    const jigs = Math.max(1, Math.floor(Number(b.jigs_per_lap) || 1))
    for (let i = 0; i < laps; i += 1) {
      const ln = b.base_lap_no + i
      cycleByLap.set(ln, cycle)
      jigsByLap.set(ln, jigs)
    }
  }
  const cycle = cycleByLap.get(lapNo) ?? Math.max(1, Math.floor(Number(targetBlock.minutes_per_lap) || 1))
  const anchorDate = currentSlot.work_date || targetBlock.plan_date
  const startHm = normalizeBoardStartTimeHm(newStartHm)
  const anchorDt = dayjs.tz(`${anchorDate} ${startHm}`, 'YYYY-MM-DD HH:mm', TZ_JP)
  if (!anchorDt.isValid()) return false
  const sortedSchedule = [...scheduleBefore].sort((a, b) => a.lap_no - b.lap_no)
  const startByLap = new Map<number, dayjs.Dayjs>()
  for (const s of sortedSchedule) {
    startByLap.set(s.lap_no, dayjs.tz(`${s.work_date} ${s.start}`, 'YYYY-MM-DD HH:mm', TZ_JP))
  }
  startByLap.set(lapNo, anchorDt)

  let carryEnd = anchorDt.add(cycle, 'minute')
  for (let ln = lapNo + 1; ; ln += 1) {
    const origStart = startByLap.get(ln)
    if (!origStart) break
    if (!carryEnd.isAfter(origStart)) break
    startByLap.set(ln, carryEnd)
    const lnCycle = cycleByLap.get(ln) ?? cycle
    carryEnd = carryEnd.add(lnCycle, 'minute')
  }

  const laps = [...startByLap.keys()].sort((a, b) => a - b)
  if (laps.length === 0) return false
  const rebuilt: BoardLayoutBlock[] = []
  let runStartLap = laps[0]
  let runStartDt = startByLap.get(runStartLap)!
  let runCycle = cycleByLap.get(runStartLap) ?? cycle
  let runJigs = jigsByLap.get(runStartLap) ?? Math.max(1, Math.floor(Number(targetBlock.jigs_per_lap) || 1))
  let runCount = 1

  for (let i = 1; i < laps.length; i += 1) {
    const ln = laps[i]
    const prevLap = laps[i - 1]
    const lnStart = startByLap.get(ln)!
    const prevStart = startByLap.get(prevLap)!
    const expected = prevStart.add(runCycle, 'minute')
    const lnCycle = cycleByLap.get(ln) ?? runCycle
    const lnJigs = jigsByLap.get(ln) ?? runJigs
    const canMerge = lnCycle === runCycle && lnJigs === runJigs && lnStart.isSame(expected)
    if (canMerge) {
      runCount += 1
      continue
    }
    rebuilt.push({
      plan_date: runStartDt.format('YYYY-MM-DD'),
      start_time: runStartDt.format('HH:mm'),
      minutes_per_lap: runCycle,
      jigs_per_lap: runJigs,
      lap_count: runCount,
      base_lap_no: runStartLap,
    })
    runStartLap = ln
    runStartDt = lnStart
    runCycle = lnCycle
    runJigs = lnJigs
    runCount = 1
  }
  rebuilt.push({
    plan_date: runStartDt.format('YYYY-MM-DD'),
    start_time: runStartDt.format('HH:mm'),
    minutes_per_lap: runCycle,
    jigs_per_lap: runJigs,
    lap_count: runCount,
    base_lap_no: runStartLap,
  })

  layoutBlocks.value = rebuilt
  const first = rebuilt[0]
  if (first) {
    layoutPlanDate.value = first.plan_date
    layoutStartTime.value = normalizeBoardStartTimeHm(first.start_time)
  }
  recomputeLayoutMaxLapsFromSchedule()
  syncScheduleCardLapTimesFromLayout()
  return true
}

/** layout 再計算後、board_cards 行の lap_work_date / 時刻を同期 */
function syncScheduleCardLapTimesFromLayout() {
  const byLap = new Map(globalLapSchedule.value.map((s) => [s.lap_no, s]))
  withSuppressedScheduleSideEffects(() => {
    scheduleCards.value = scheduleCards.value.map((c) => {
      const s = byLap.get(c.lap_no)
      if (!s) return c
      return {
        ...c,
        lap_work_date: s.work_date,
        lap_start_time: s.start,
        lap_end_time: s.end,
      }
    })
  })
}

function openLapStartTimeEdit(lapNo: number) {
  const row = currentLayoutLapSchedule().find((r) => r.lap_no === lapNo)
  if (!row) return
  lapStartTimeEditLapNo.value = lapNo
  lapStartTimeEditValue.value = normalizeBoardStartTimeHm(row.start)
  lapStartTimeDialogVisible.value = true
}

function confirmLapStartTimeEdit() {
  const lapNo = lapStartTimeEditLapNo.value
  const value = normalizeBoardStartTimeHm(lapStartTimeEditValue.value)
  if (lapNo < 1 || !value) return
  const ok = applyLapStartTimeAndCascade(lapNo, value)
  if (!ok) {
    ElMessage.warning('開始時刻の更新に失敗しました')
    return
  }
  lapStartTimeDialogVisible.value = false
  ElMessage.success(`第${lapDisplayNo(lapNo)}周目の開始時刻を ${value} に更新しました`)
  void flushBoardPersist()
}

type LapBoardDisplayItem =
  | { kind: 'date'; key: string; work_date: string; dateLabel: string }
  | { kind: 'lap'; key: string; row: LapGridRow }

/** メッキ前在庫（左ペイン）の基準日 */
const leftInventoryDate = ref(todayYmdJapan())
/** 見込数量（右ペイン）の production_summarys 参照日（左と独立） */
const rightGenDate = ref(addDaysYmdJapan(todayYmdJapan(), 1))
const loadingPair = ref(false)

function shiftLeftInventoryDate(days: number) {
  leftInventoryDate.value = shiftYmdJapan(leftInventoryDate.value, days)
}

function shiftRightGenDate(days: number) {
  rightGenDate.value = shiftYmdJapan(rightGenDate.value, days)
}

/** 左ペイン行（社内メッキ KT05 直前工程在庫 &gt; 0 のみ） */
interface LeftPaneRow {
  product_cd: string
  product_name: string
  /** production_summarys.plating_machine（メッキ治具） */
  plating_machine: string
  /** equipment_efficiency.efficiency_rate（治具名＋品番で突合） */
  plating_efficiency: string
  pre_plating_prev_label: string
  /** 社内メッキ(KT05)直前工程の当日在庫（API: pre_kt05_plating_inventory） */
  pre_plating_inventory: number
}

/** 右ペイン行 */
interface RightPaneRow {
  product_cd: string
  product_name: string
  plating_machine: string
  plating_efficiency: string
  pre_plating_prev_label: string
  gen_qty: number | string
  gen_source_col: string
}

const leftRows = ref<LeftPaneRow[]>([])
const rightRows = ref<RightPaneRow[]>([])
const platingPageRef = ref<HTMLElement | null>(null)
const leftPaneRef = ref<InstanceType<typeof PlatingLeftInventoryPane> | null>(null)
const rightPaneRef = ref<InstanceType<typeof PlatingRightGenPane> | null>(null)
const leftInventoryFloating = ref(false)
const rightGenFloating = ref(false)
const leftInventoryFloatX = ref(24)
const leftInventoryFloatY = ref(96)
const rightGenFloatX = ref(592)
const rightGenFloatY = ref(96)

const summaryDockedColSpan = computed(() => {
  const docked = (leftInventoryFloating.value ? 0 : 1) + (rightGenFloating.value ? 0 : 1)
  return docked <= 1 ? 24 : 12
})

function openLeftInventoryFloat() {
  leftInventoryFloating.value = true
  nextTick(() => bindLeftInventoryTableDrag())
}

function dockLeftInventoryFloat() {
  leftInventoryFloating.value = false
  nextTick(() => bindLeftInventoryTableDrag())
}

function onLeftInventoryFloatClose() {
  nextTick(() => bindLeftInventoryTableDrag())
}

function openRightGenFloat() {
  rightGenFloating.value = true
  nextTick(() => bindRightGenTableDrag())
}

function dockRightGenFloat() {
  rightGenFloating.value = false
  nextTick(() => bindRightGenTableDrag())
}

function onRightGenFloatClose() {
  nextTick(() => bindRightGenTableDrag())
}

function bindLeftInventoryTableDrag() {
  const tableRef = leftPaneRef.value?.tableRef
  if (!tableRef) return
  bindTableRowDrag({ value: tableRef }, leftRows.value, 'left')
}

function bindRightGenTableDrag() {
  const tableRef = rightPaneRef.value?.tableRef
  if (!tableRef) return
  bindTableRowDrag({ value: tableRef }, rightRows.value, 'right')
}

interface DraftSourceItem {
  source_key: string
  source_type: 'left_inventory' | 'right_gen'
  product_cd: string
  product_name: string
  plating_machine: string
  kake: number
  qty: number
}

const draftWorkDate = ref(todayYmdJapan())
/** loadLatestDraft 内で作業日を補正している間は draftWorkDate の watch で再取得しない */
const syncingDraftWorkDateFromLoad = ref(false)
const loadingDraft = ref(false)
const currentDraftId = ref<number | null>(null)
const draggingSource = ref<DraftSourceItem | null>(null)
const loadingJigAvailability = ref(false)
let jigAvailabilityLoadPromise: Promise<void> | null = null
let lapSortableInitTimer: ReturnType<typeof setTimeout> | null = null
/** scheduleCards 変更に伴う Sortable 再初期化＋自動保存をまとめてデバウンス */
let boardReactiveEffectsTimer: ReturnType<typeof setTimeout> | null = null
const BOARD_REACTIVE_EFFECTS_MS = 220
const PLATING_MACHINE_TYPE = 'メッキ'
const platingJigMasterDialogVisible = ref(false)
const pjmLoading = ref(false)
const pjmKeyword = ref('')
const pjmList = ref<MachineItem[]>([])
const pjmFormVisible = ref(false)
const pjmEditData = ref<MachineItem | null>(null)
const pjmStatusSavingId = ref<number | null>(null)
const jigCardListExpanded = ref(true)
/** メッキ治具ヘッダ：製品で対応治具を絞り込み */
const jigFilterProductCd = ref('')
const jigAvailabilityRows = ref<{ machine_id: number | null; plating_machine: string; available_qty: number }[]>([])
/** メッキ治具の使用可能本数合計（設備マスタ available_qty） */
const jigAvailabilityTotalQty = computed(() =>
  jigAvailabilityRows.value.reduce(
    (sum, r) => sum + Math.max(0, Math.floor(Number(r.available_qty) || 0)),
    0,
  ),
)
const jigDropDialogVisible = ref(false)
const jigDropPending = ref<{
  plating_machine: string
  available_max: number
  used_on_board: number
  target_lap: number
  layout_max: number
  layout_used: number
  layout_remain: number
} | null>(null)
const jigDropQty = ref(1)
const jigDropQtyMax = ref(1)
const jigDropPreferLap = ref<number | null>(null)
const jigBoardDragActive = ref(false)
const jigDropHoverLap = ref<number | null>(null)
const jigCardProductsDialogVisible = ref(false)
const jigCardProductsDialogMachine = ref('')
const jigCardProductsDialogAvailableQty = ref(0)
const draggingJigToBoard = ref<{
  machine_id: number | null
  plating_machine: string
  available_qty: number
} | null>(null)
const draggingInventoryRow = ref(false)
const productDropHoverBlockKey = ref<string | null>(null)
const productToJigDialogVisible = ref(false)
const productToJigPending = ref<{
  ms: LapMergedSegment
  lapNo: number
  src: DraftSourceItem
  existing: DraftSourceItem
  span: number
} | null>(null)
const productAssignExistingSlots = ref(1)
const productAssignNewSlots = ref(1)
const productAssignOrder = ref<'existing-first' | 'new-first'>('existing-first')
const boardJigEditDialogVisible = ref(false)
const boardJigEditPending = ref<{
  lap_no: number
  plating_machine: string
  product_cd: string
  product_name: string
  cardIds: string[]
} | null>(null)
const boardJigEditQty = ref(1)
const boardJigEditQtyMax = ref(1)

interface BoardJigEditProductFrame {
  product_cd: string
  product_name: string
  frames: number
  kake: number
  untilDepleted: boolean
  forceRedText: boolean
}

const boardJigEditProductFrames = ref<BoardJigEditProductFrame[]>([])
const boardJigEditProductFramesInitial = ref<BoardJigEditProductFrame[]>([])
const boardJigEditProductOrder = ref<'normal' | 'reversed'>('normal')
const boardJigEditInitialQty = ref(1)

const boardJigEditProductFramesSum = computed(() =>
  boardJigEditProductFrames.value.reduce(
    (s, p) => s + Math.max(0, Math.floor(Number(p.frames) || 0)),
    0,
  ),
)

const boardJigEditUnassignedFrames = computed(() =>
  Math.max(
    0,
    Math.floor(Number(boardJigEditQty.value) || 0) - boardJigEditProductFramesSum.value,
  ),
)

const canConfirmBoardJigEdit = computed(() => {
  if (boardJigEditQtyMax.value < 1) return false
  const total = Math.floor(Number(boardJigEditQty.value) || 0)
  return boardJigEditProductFramesSum.value <= total
})

const showBoardJigEditProductOrder = computed(() => {
  const active = boardJigEditProductFrames.value.filter((p) => Math.floor(Number(p.frames) || 0) > 0)
  return active.length >= 2
})

const boardJigEditProductOrderNormalLabel = computed(() => {
  const names = boardJigEditProductFrames.value
    .filter((p) => Math.floor(Number(p.frames) || 0) > 0)
    .map((p) => p.product_name)
  if (names.length < 2) return '現在の順'
  return names.join(' → ')
})

const boardJigEditProductOrderReversedLabel = computed(() => {
  const names = boardJigEditProductFrames.value
    .filter((p) => Math.floor(Number(p.frames) || 0) > 0)
    .map((p) => p.product_name)
  if (names.length < 2) return '逆順'
  return [...names].reverse().join(' → ')
})

function boardJigEditProductFramesMax(productCd: string): number {
  const total = Math.max(0, Math.floor(Number(boardJigEditQty.value) || 0))
  const others = boardJigEditProductFrames.value
    .filter((p) => p.product_cd !== productCd)
    .reduce((s, p) => s + Math.max(0, Math.floor(Number(p.frames) || 0)), 0)
  return Math.max(0, total - others)
}

function formatBoardJigEditFrameTooltip(val: number) {
  return `${Math.floor(Number(val) || 0)} 本`
}

function boardJigEditProductFramesSortedByLargest() {
  return [...boardJigEditProductFrames.value].sort(
    (a, b) => Math.floor(Number(b.frames) || 0) - Math.floor(Number(a.frames) || 0),
  )
}

/** 治具総本数減少：本数の多い製品から順に削減 */
function trimBoardJigEditProductFramesByLargest(amount: number) {
  let remaining = Math.max(0, Math.floor(amount))
  if (remaining <= 0) return
  for (const p of boardJigEditProductFramesSortedByLargest()) {
    if (remaining <= 0) break
    const cur = Math.max(0, Math.floor(Number(p.frames) || 0))
    const take = Math.min(remaining, cur)
    p.frames = cur - take
    remaining -= take
  }
}

/** 治具総本数増加：本数の多い製品から順に加算（上限は治具総本数） */
function growBoardJigEditProductFramesByLargest(amount: number) {
  let remaining = Math.max(0, Math.floor(amount))
  if (remaining <= 0) return
  const total = Math.max(0, Math.floor(Number(boardJigEditQty.value) || 0))
  for (const p of boardJigEditProductFramesSortedByLargest()) {
    if (remaining <= 0) break
    const cur = Math.max(0, Math.floor(Number(p.frames) || 0))
    const others = sumBoardJigEditFramesExcept(p.product_cd)
    const room = Math.max(0, total - others - cur)
    const add = Math.min(remaining, room)
    if (add <= 0) continue
    p.frames = cur + add
    remaining -= add
  }
}

/** 治具総本数スライダー：増減に応じて製品別本数を本数の多い順に自動調整 */
function setBoardJigEditQty(rawVal: number) {
  const max = Math.max(1, boardJigEditQtyMax.value)
  const next = Math.max(1, Math.min(max, Math.floor(Number(rawVal) || 0)))
  const prev = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  if (next === prev) return

  const delta = next - prev
  boardJigEditQty.value = next

  if (boardJigEditProductFrames.value.length === 0) return

  if (delta > 0) {
    growBoardJigEditProductFramesByLargest(delta)
    return
  }

  trimBoardJigEditProductFramesByLargest(-delta)

  const sum = boardJigEditProductFrames.value.reduce(
    (s, p) => s + Math.max(0, Math.floor(Number(p.frames) || 0)),
    0,
  )
  if (sum > next) {
    trimBoardJigEditProductFramesByLargest(sum - next)
  }
}

function sumBoardJigEditFramesExcept(excludeProductCd: string): number {
  return boardJigEditProductFrames.value.reduce((s, p) => {
    if (p.product_cd === excludeProductCd) return s
    return s + Math.max(0, Math.floor(Number(p.frames) || 0))
  }, 0)
}

function boardJigEditProductFramesSliderMax(productCd: string): number {
  const list = boardJigEditProductFrames.value
  if (list.length === 2) {
    const self = list.find((p) => p.product_cd === productCd)
    const other = list.find((p) => p.product_cd !== productCd)
    if (!self || !other) return boardJigEditProductFramesMax(productCd)
    return (
      Math.floor(Number(self.frames) || 0) + Math.floor(Number(other.frames) || 0)
    )
  }
  return boardJigEditProductFramesMax(productCd)
}

/** スライダー変更時、他製品へ本数を自動振替（2 種は合計固定、3 種以上は順次振替） */
/** 割当済み製品行の削除（残り1種は総本数まで自動拡張、0種は空き治具） */
function removeBoardJigEditProduct(productCd: string) {
  const total = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  const remaining = boardJigEditProductFrames.value.filter((p) => p.product_cd !== productCd)
  const removed = boardJigEditProductFrames.value.find((p) => p.product_cd === productCd)

  if (
    boardJigEditAddKey.value &&
    (boardJigEditAddOpt.value?.src.product_cd === productCd ||
      boardJigEditPrimaryFrame.value?.product_cd === productCd)
  ) {
    boardJigEditAddKey.value = ''
  }

  if (remaining.length === 0) {
    boardJigEditProductFrames.value = []
    return
  }

  if (remaining.length === 1) {
    boardJigEditProductFrames.value = [{ ...remaining[0], frames: total }]
    if (removed) ElMessage.success(`${removed.product_name} の割当を削除しました`)
    return
  }

  const list = remaining.map((p) => ({ ...p }))
  let sum = list.reduce((s, p) => s + Math.max(0, Math.floor(Number(p.frames) || 0)), 0)
  let deficit = total - sum
  if (deficit > 0) {
    const ordered = [...list].sort(
      (a, b) => Math.floor(Number(b.frames) || 0) - Math.floor(Number(a.frames) || 0),
    )
    for (const target of ordered) {
      if (deficit <= 0) break
      const hit = list.find((p) => p.product_cd === target.product_cd)
      if (!hit) continue
      hit.frames = Math.floor(Number(hit.frames) || 0) + deficit
      deficit = 0
    }
  }
  boardJigEditProductFrames.value = list

  if (removed) {
    ElMessage.success(`${removed.product_name} の割当を削除しました`)
  }
}

function setBoardJigEditProductFrames(productCd: string, rawVal: number) {
  const list = boardJigEditProductFrames.value
  const total = Math.max(0, Math.floor(Number(boardJigEditQty.value) || 0))
  const idx = list.findIndex((p) => p.product_cd === productCd)
  if (idx < 0) return

  const prevSelf = Math.floor(Number(list[idx].frames) || 0)
  const sliderMax = boardJigEditProductFramesSliderMax(productCd)
  let nextSelf = Math.max(0, Math.min(sliderMax, Math.floor(Number(rawVal) || 0)))
  const delta = nextSelf - prevSelf
  if (delta === 0) return

  if (list.length === 1) {
    list[idx].frames = Math.max(0, Math.min(total, nextSelf))
    return
  }

  if (list.length === 2) {
    const otherIdx = idx === 0 ? 1 : 0
    const pairSum = sliderMax
    nextSelf = Math.max(0, Math.min(pairSum, nextSelf))
    list[idx].frames = nextSelf
    list[otherIdx].frames = pairSum - nextSelf
    return
  }

  list[idx].frames = nextSelf
  let remaining = -delta
  const n = list.length
  for (let step = 1; step <= n && remaining !== 0; step++) {
    const j = (idx + step) % n
    const cur = Math.floor(Number(list[j].frames) || 0)
    if (remaining > 0) {
      const others = sumBoardJigEditFramesExcept(list[j].product_cd)
      const room = Math.max(0, total - others - cur)
      const add = Math.min(remaining, room)
      if (add <= 0) continue
      list[j].frames = cur + add
      remaining -= add
    } else {
      const take = Math.min(cur, -remaining)
      if (take <= 0) continue
      list[j].frames = cur - take
      remaining += take
    }
  }
  if (remaining !== 0) {
    list[idx].frames = Math.max(0, Math.floor(Number(list[idx].frames) || 0) - remaining)
  }
}

function initBoardJigEditProductFrames(pending: NonNullable<typeof boardJigEditPending.value>) {
  const idSet = new Set(pending.cardIds)
  const cards = scheduleCards.value
    .filter(
      (c) =>
        idSet.has(c.id) &&
        c.qty > 0 &&
        c.lap_no === pending.lap_no &&
        !isJigProductCd(c.product_cd),
    )
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const order: string[] = []
  const map = new Map<string, BoardJigEditProductFrame>()
  for (const c of cards) {
    let e = map.get(c.product_cd)
    if (!e) {
      e = {
        product_cd: c.product_cd,
        product_name: String(c.product_name || c.product_cd || '').trim(),
        frames: 0,
        kake: c.kake > 0 ? c.kake : 1,
        untilDepleted: true,
        forceRedText: false,
      }
      map.set(c.product_cd, e)
      order.push(c.product_cd)
    }
    e.frames += 1
    if (!c.untilDepleted) e.untilDepleted = false
    if (c.forceRedText) e.forceRedText = true
  }
  const frames = order.map((cd) => ({ ...map.get(cd)! }))
  boardJigEditProductFrames.value = frames
  boardJigEditProductFramesInitial.value = frames.map((p) => ({ ...p }))
  boardJigEditProductOrder.value = 'normal'
}

function activeBoardJigEditFrameRows(list: BoardJigEditProductFrame[]) {
  return list
    .filter((p) => Math.floor(Number(p.frames) || 0) > 0)
    .map((p) => ({
      product_cd: p.product_cd,
      frames: Math.floor(Number(p.frames) || 0),
    }))
}

function isBoardJigProductFramesReassignDirty(): boolean {
  if (boardJigEditProductOrder.value !== 'normal') return true
  const qty = Math.floor(Number(boardJigEditQty.value) || 0)
  if (qty !== boardJigEditInitialQty.value) return true

  const cur = activeBoardJigEditFrameRows(boardJigEditProductFrames.value)
  const init = activeBoardJigEditFrameRows(boardJigEditProductFramesInitial.value)
  if (cur.length !== init.length) return true

  for (const c of cur) {
    const i = init.find((x) => x.product_cd === c.product_cd)
    if (!i || i.frames !== c.frames) return true
  }
  for (const i of init) {
    if (!cur.some((c) => c.product_cd === i.product_cd)) return true
  }
  return false
}

function isBoardJigDisplayFlagsDirty(): boolean {
  for (const cur of boardJigEditProductFrames.value) {
    const init = boardJigEditProductFramesInitial.value.find((p) => p.product_cd === cur.product_cd)
    if (!init) return true
    if (!!cur.untilDepleted !== !!init.untilDepleted) return true
    if (!!cur.forceRedText !== !!init.forceRedText) return true
  }
  return false
}

function isBoardJigProductAllocationDirty(): boolean {
  return isBoardJigProductFramesReassignDirty() || isBoardJigDisplayFlagsDirty()
}

function productFramesEditDirty(): boolean {
  return isBoardJigProductAllocationDirty() || isBoardJigEditAddDirty()
}

const boardJigEditAddKey = ref('')
const boardJigEditAddSlots = ref(1)
const boardJigEditAddReplaceAll = ref(false)
const boardJigEditInlineExistingSlots = ref(1)
const boardJigEditInlineNewSlots = ref(1)
const boardJigEditInlineOrder = ref<'existing-first' | 'new-first'>('existing-first')

function resetBoardJigEditAddFields() {
  boardJigEditAddKey.value = ''
  boardJigEditAddSlots.value = 1
  boardJigEditAddReplaceAll.value = false
  boardJigEditInlineExistingSlots.value = 1
  boardJigEditInlineNewSlots.value = 1
  boardJigEditInlineOrder.value = 'existing-first'
}

function isBoardJigEditAddDirty(): boolean {
  return !!boardJigEditAddKey.value
}

const boardJigEditAddOptionSets = computed(() => {
  const jig = boardJigEditPending.value?.plating_machine ?? ''
  return buildBoardProductPickOptionSets(jig, true)
})

const boardJigEditAddSummaryOptions = computed(() => boardJigEditAddOptionSets.value.summary)
const boardJigEditAddCatalogOptions = computed(() => boardJigEditAddOptionSets.value.catalog)

const boardJigEditAddAllOptions = computed(() => [
  ...boardJigEditAddSummaryOptions.value,
  ...boardJigEditAddCatalogOptions.value,
])

const boardJigEditAddOpt = computed(() =>
  boardJigEditAddAllOptions.value.find((o) => o.pickKey === boardJigEditAddKey.value),
)

const boardJigEditPrimaryFrame = computed(() => {
  const active = boardJigEditProductFrames.value.filter((p) => Math.floor(Number(p.frames) || 0) > 0)
  if (active.length === 0) return null
  return [...active].sort(
    (a, b) => Math.floor(Number(b.frames) || 0) - Math.floor(Number(a.frames) || 0),
  )[0]
})

const boardJigEditAddSlotsMax = computed(() => {
  const total = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  if (boardJigEditAddReplaceAll.value) return total
  const empty = boardJigEditUnassignedFrames.value
  return Math.max(1, empty > 0 ? empty : total)
})

function countBoardJigEditAssignedActiveTypes(): number {
  return boardJigEditProductFrames.value.filter((p) => Math.floor(Number(p.frames) || 0) > 0).length
}

const showBoardJigEditInlineAssign = computed(() => {
  if (!boardJigEditPending.value || !boardJigEditAddKey.value || boardJigEditAddReplaceAll.value) return false
  if (!boardJigEditAddOpt.value) return false
  const span = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  const primary = boardJigEditPrimaryFrame.value
  if (!primary) return false
  if (primary.product_cd === boardJigEditAddOpt.value.src.product_cd) return false

  // 割当済み 1 種：追加製品選択後は既存/追加スライダーで比率配分（追加が満杯なら置換）
  if (countBoardJigEditAssignedActiveTypes() === 1) return span >= 1

  const want = Math.max(1, Math.floor(Number(boardJigEditAddSlots.value) || 0))
  const empty = boardJigEditUnassignedFrames.value
  if (empty > 0 && want <= empty) return false
  return span >= 2 && want < span
})

function syncBoardJigEditInlineAssignFromPrimary() {
  if (!showBoardJigEditInlineAssign.value) return
  const span = boardJigEditInlineSpan.value
  const primary = boardJigEditPrimaryFrame.value
  if (!primary) return
  const existingCount = Math.min(Math.floor(Number(primary.frames) || 0), span)
  boardJigEditInlineExistingSlots.value = existingCount
  boardJigEditInlineNewSlots.value = span - existingCount
  boardJigEditInlineOrder.value = 'existing-first'
}

const boardJigEditAddCanReplaceAll = computed(() => {
  const total = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  return (
    total > 0 &&
    boardJigEditUnassignedFrames.value < total &&
    boardJigEditProductFramesSum.value > 0 &&
    !showBoardJigEditInlineAssign.value
  )
})

const boardJigEditInlineSpan = computed(() =>
  Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0)),
)

/** 既存・追加の合計＝治具総本数で連動 */
function setBoardJigEditInlineExistingSlots(rawVal: number) {
  const span = boardJigEditInlineSpan.value
  const e = Math.max(0, Math.min(span, Math.floor(Number(rawVal) || 0)))
  boardJigEditInlineExistingSlots.value = e
  boardJigEditInlineNewSlots.value = span - e
}

function setBoardJigEditInlineNewSlots(rawVal: number) {
  const span = boardJigEditInlineSpan.value
  const n = Math.max(0, Math.min(span, Math.floor(Number(rawVal) || 0)))
  boardJigEditInlineNewSlots.value = n
  boardJigEditInlineExistingSlots.value = span - n
}

const boardJigEditInlineSlotsSum = computed(
  () =>
    Math.max(0, Math.floor(Number(boardJigEditInlineExistingSlots.value) || 0)) +
    Math.max(0, Math.floor(Number(boardJigEditInlineNewSlots.value) || 0)),
)

const showBoardJigEditInlineOrder = computed(() => {
  const e = Math.max(0, Math.floor(Number(boardJigEditInlineExistingSlots.value) || 0))
  const n = Math.max(0, Math.floor(Number(boardJigEditInlineNewSlots.value) || 0))
  return e > 0 && n > 0
})

const canConfirmBoardJigEditInline = computed(() => {
  if (!showBoardJigEditInlineAssign.value) return true
  const span = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  const e = Math.max(0, Math.floor(Number(boardJigEditInlineExistingSlots.value) || 0))
  const n = Math.max(0, Math.floor(Number(boardJigEditInlineNewSlots.value) || 0))
  return boardJigEditInlineSlotsSum.value === span && (e > 0 || n > 0)
})

const canConfirmBoardJigEditWithAdd = computed(() => {
  if (!boardJigEditAddKey.value) return true
  if (!boardJigEditAddAllOptions.value.some((o) => o.pickKey === boardJigEditAddKey.value)) return false
  return canConfirmBoardJigEditInline.value
})

watch(boardJigEditAddReplaceAll, (on) => {
  if (on) {
    boardJigEditAddSlots.value = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  }
})

watch(showBoardJigEditInlineAssign, (on) => {
  if (!on) return
  syncBoardJigEditInlineAssignFromPrimary()
})

watch(boardJigEditQty, () => {
  if (!showBoardJigEditInlineAssign.value) return
  const span = boardJigEditInlineSpan.value
  const e = Math.min(Math.floor(Number(boardJigEditInlineExistingSlots.value) || 0), span)
  boardJigEditInlineExistingSlots.value = e
  boardJigEditInlineNewSlots.value = span - e
})

/** 割当済みが空のとき、追加選択を即座に割当済みリストへ反映 */
function promoteBoardJigEditAddToAssignedIfEmpty() {
  if (boardJigEditProductFrames.value.length > 0) return
  const opt = boardJigEditAddOpt.value
  if (!opt) return
  const src = opt.src
  const total = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))
  const frames = boardJigEditAddReplaceAll.value
    ? total
    : Math.max(1, Math.min(total, Math.floor(Number(boardJigEditAddSlots.value) || 0)))
  boardJigEditProductFrames.value = [
    {
      product_cd: src.product_cd,
      product_name: src.product_name,
      frames,
      kake: src.kake > 0 ? src.kake : 1,
      untilDepleted: false,
      forceRedText: false,
    },
  ]
  boardJigEditAddKey.value = ''
}

watch(boardJigEditAddKey, (key) => {
  if (!key) return
  if (boardJigEditProductFrames.value.length === 0) {
    promoteBoardJigEditAddToAssignedIfEmpty()
    return
  }
  syncBoardJigEditInlineAssignFromPrimary()
})

/** 治具別製品一覧（equipment_efficiency から構築、在庫/見込は左右表で補完） */
interface JigProductCatalogRow {
  product_cd: string
  product_name: string
  plating_machine: string
  plating_efficiency: string
  pre_plating_inventory: number | null
  gen_qty: number | null
}
const jigProductCatalogByMachine = ref<Map<string, Map<string, JigProductCatalogRow>>>(new Map())
const productionListDialogVisible = ref(false)
const lapCopyDialogVisible = ref(false)
const lapCopyFrom = ref(1)
const lapCopyTo = ref(2)
const deleteLapsByDateDialogVisible = ref(false)
const deleteLapsByDateYmd = ref('')
const lapStartTimeDialogVisible = ref(false)
const lapStartTimeEditLapNo = ref(0)
const lapStartTimeEditValue = ref('08:00')
const boardDateMemosByYmd = ref<Record<string, string>>({})
const boardDateMemoDialogVisible = ref(false)
const boardDateMemoEditYmd = ref('')
const boardDateMemoEditValue = ref('')

/** 左表「直前工程在庫」列の合計 */
const leftPrevInventoryTotal = computed(() =>
  leftRows.value.reduce((s, r) => s + (Number.isFinite(r.pre_plating_inventory) ? r.pre_plating_inventory : 0), 0),
)
const rightGenQtyTotal = computed(() =>
  rightRows.value.reduce((s, r) => s + (Number.isFinite(Number(r.gen_qty)) ? Number(r.gen_qty) : 0), 0),
)

const summaryPairPrintLoading = ref(false)

const hasSummaryPairPrintData = computed(
  () => leftRows.value.length > 0 || rightRows.value.length > 0,
)

/**
 * メッキ手前までの主ライン工程順（backend DEFAULT_ROUTE_PREFIXES / INVENTORY_PROCESS_CONFIG と整合）
 * 左表は「直前工程」キーでこの順にソートする。
 */
const ROUTE_PROCESS_ORDER: readonly string[] = [
  'cutting',
  'chamfering',
  'molding',
  'plating',
  'welding',
  'inspection',
  'warehouse',
  'outsourced_warehouse',
  'outsourced_plating',
  'outsourced_welding',
  'pre_welding_inspection',
  'pre_inspection',
  'pre_outsourcing',
]

function processOrderRank(prevKey: string | null): number {
  if (!prevKey) return 9999
  const i = ROUTE_PROCESS_ORDER.indexOf(prevKey)
  return i === -1 ? 8000 : i
}

/** 工程 key → 表示名（メッキ前在庫の直前工程用） */
const PROCESS_LABEL: Record<string, string> = {
  cutting: '切断',
  chamfering: '面取',
  molding: '成型',
  plating: 'メッキ',
  welding: '溶接',
  inspection: '検査',
  warehouse: '倉庫',
  outsourced_warehouse: '外注倉庫',
  outsourced_plating: '外注メッキ',
  outsourced_welding: '外注溶接',
  pre_welding_inspection: '溶接前検査',
  pre_inspection: '外注支給前',
  pre_outsourcing: '外注検査前',
}

/** 直前工程の「生成」参照列（実計 → 計画 → 実績） */
const GEN_SUFFIX_TRY: readonly string[] = ['_actual_plan', '_plan', '_actual']

function labelForPrevKey(key: string | null | undefined): string {
  if (!key) return '—'
  return PROCESS_LABEL[key] ?? key
}

function parseList(res: unknown): Record<string, unknown>[] {
  const r = res as { data?: unknown; list?: unknown }
  const data = r?.data ?? r
  const inner = (data as { list?: unknown })?.list ?? (data as { data?: { list?: unknown } })?.data?.list
  return Array.isArray(inner) ? (inner as Record<string, unknown>[]) : []
}

function num(v: unknown): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

/** 文字列の掛け数を数値化（'—' 等は null） */
function parseKakeCount(v: string): number | null {
  const n = Number(v)
  return Number.isFinite(n) && n > 0 ? n : null
}

/** 在庫／見込ペイン：整数表示（小数なし） */
function formatSummaryIntegerDisplay(n: number): string {
  if (!Number.isFinite(n)) return '—'
  return String(Math.round(n))
}

/** 掛け数表示（小数なし） */
function formatSummaryKakeDisplay(raw: string): string {
  if (!raw || raw === '—') return '—'
  const kake = parseKakeCount(raw)
  if (kake == null) return '—'
  return formatSummaryIntegerDisplay(kake)
}

/** 必要治具本数 = 直前工程在庫 ÷ 掛け数 */
function calcRequiredJigCount(row: LeftPaneRow): string {
  const kake = parseKakeCount(row.plating_efficiency)
  if (!kake) return '—'
  const val = row.pre_plating_inventory / kake
  return formatSummaryIntegerDisplay(val)
}

function calcRequiredJigCountFromQty(qty: number | string, kakeRaw: string): string {
  const kake = parseKakeCount(kakeRaw)
  if (!kake) return '—'
  const q = Number(qty)
  if (!Number.isFinite(q)) return '—'
  const val = q / kake
  return formatSummaryIntegerDisplay(val)
}

interface SummaryPrintColumn {
  key: string
  label: string
  align?: 'left' | 'right'
  getValue: (row: LeftPaneRow | RightPaneRow) => string
}

function buildSummaryPrintTableSection(
  title: string,
  metaLine: string,
  columns: SummaryPrintColumn[],
  rows: LeftPaneRow[] | RightPaneRow[],
): string {
  const head = columns
    .map((c) => {
      const align = c.align === 'right' ? ' class="num"' : ''
      return `<th${align}>${escapeHtmlForPrint(c.label)}</th>`
    })
    .join('')
  const body =
    rows.length === 0
      ? `<tr><td colspan="${columns.length}" class="empty">データがありません</td></tr>`
      : rows
          .map((row) => {
            const cells = columns
              .map((c) => {
                const cls = c.align === 'right' ? ' class="num"' : ''
                return `<td${cls}>${escapeHtmlForPrint(c.getValue(row))}</td>`
              })
              .join('')
            return `<tr>${cells}</tr>`
          })
          .join('')
  return `
    <section class="summary-print-block">
      <h2 class="summary-print-block__title">${escapeHtmlForPrint(title)}</h2>
      <p class="summary-print-block__meta">${escapeHtmlForPrint(metaLine)}</p>
      <table class="summary-print-table">
        <thead><tr>${head}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </section>`
}

function buildSummaryPairPrintHtml(): string {
  const printedAt = dayjs().tz(TZ_JP).format('YYYY-MM-DD HH:mm')
  const leftDate = formatBoardDateLabel(leftInventoryDate.value)
  const rightDate = formatBoardDateLabel(rightGenDate.value)
  const leftCols: SummaryPrintColumn[] = [
    { key: 'product_name', label: '製品名', getValue: (r) => String((r as LeftPaneRow).product_name || '—') },
    { key: 'plating_machine', label: 'メッキ治具', getValue: (r) => String((r as LeftPaneRow).plating_machine || '—') },
    {
      key: 'plating_efficiency',
      label: '掛け数',
      align: 'right',
      getValue: (r) => formatSummaryKakeDisplay(String((r as LeftPaneRow).plating_efficiency || '—')),
    },
    {
      key: 'pre_plating_inventory',
      label: '直前工程在庫',
      align: 'right',
      getValue: (r) => formatSummaryIntegerDisplay((r as LeftPaneRow).pre_plating_inventory),
    },
    {
      key: 'jig_count',
      label: '必要治具本数',
      align: 'right',
      getValue: (r) => calcRequiredJigCount(r as LeftPaneRow),
    },
  ]
  const rightCols: SummaryPrintColumn[] = [
    { key: 'product_name', label: '製品名', getValue: (r) => String((r as RightPaneRow).product_name || '—') },
    { key: 'plating_machine', label: 'メッキ治具', getValue: (r) => String((r as RightPaneRow).plating_machine || '—') },
    {
      key: 'plating_efficiency',
      label: '掛け数',
      align: 'right',
      getValue: (r) => formatSummaryKakeDisplay(String((r as RightPaneRow).plating_efficiency || '—')),
    },
    {
      key: 'gen_qty',
      label: '見込数量',
      align: 'right',
      getValue: (r) => formatSummaryIntegerDisplay(Number((r as RightPaneRow).gen_qty)),
    },
    {
      key: 'jig_count',
      label: '必要治具本数',
      align: 'right',
      getValue: (r) => calcRequiredJigCountFromQty((r as RightPaneRow).gen_qty, (r as RightPaneRow).plating_efficiency),
    },
  ]
  const leftMeta = `基準日 ${leftDate} · ${leftRows.value.length} 件 · 直前工程在庫合計 ${formatSummaryIntegerDisplay(leftPrevInventoryTotal.value)}`
  const rightMeta = `基準日 ${rightDate} · ${rightRows.value.length} 件 · 見込数量合計 ${formatSummaryIntegerDisplay(rightGenQtyTotal.value)}`
  const leftSection = buildSummaryPrintTableSection('メッキ前在庫', leftMeta, leftCols, leftRows.value)
  const rightSection = buildSummaryPrintTableSection('見込数量', rightMeta, rightCols, rightRows.value)
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>メッキ前在庫／見込数量</title>
  <style>
    @page { size: A4 portrait; margin: 12mm; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Yu Gothic UI", "Meiryo", "Hiragino Sans", sans-serif;
      font-size: 11px;
      color: #111;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .summary-print-doc { padding: 0; }
    .summary-print-doc__head { margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #2563eb; }
    .summary-print-doc__title { margin: 0 0 4px; font-size: 16px; font-weight: 700; }
    .summary-print-doc__meta { margin: 0; font-size: 11px; color: #475569; }
    .summary-print-block { margin-bottom: 14px; page-break-inside: avoid; }
    .summary-print-block__title { margin: 0 0 4px; font-size: 13px; font-weight: 700; color: #1d4ed8; }
    .summary-print-block__meta { margin: 0 0 6px; font-size: 10px; color: #64748b; }
    .summary-print-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .summary-print-table th,
    .summary-print-table td {
      border: 1px solid #334155;
      padding: 4px 6px;
      vertical-align: top;
      word-break: break-word;
    }
    .summary-print-table th {
      background: #eff6ff;
      font-weight: 700;
      font-size: 10px;
    }
    .summary-print-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
    .summary-print-table td.empty { text-align: center; color: #94a3b8; }
    .summary-print-table th.num { text-align: right; }
  </style>
</head>
<body>
  <div class="summary-print-doc">
    <header class="summary-print-doc__head">
      <h1 class="summary-print-doc__title">メッキ前在庫／見込数量</h1>
      <p class="summary-print-doc__meta">印刷日時：${escapeHtmlForPrint(printedAt)}</p>
    </header>
    ${leftSection}
    ${rightSection}
  </div>
</body>
</html>`
}

function printHtmlViaHiddenIframe(html: string, iframeTitle: string) {
  const iframe = document.createElement('iframe')
  iframe.setAttribute('aria-hidden', 'true')
  iframe.title = iframeTitle
  iframe.style.cssText = [
    'position:fixed',
    'left:-20000px',
    'top:0',
    'width:210mm',
    'height:297mm',
    'border:0',
    'opacity:0',
    'pointer-events:none',
    'z-index:-1',
  ].join(';')
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  const win = iframe.contentWindow
  if (!doc || !win) {
    iframe.remove()
    throw new Error('print-iframe-unavailable')
  }
  const removeIframe = () => {
    try {
      iframe.remove()
    } catch {
      /* ignore */
    }
  }
  let printed = false
  const doPrint = () => {
    if (printed) return
    printed = true
    try {
      win.focus()
      win.print()
    } catch {
      /* ignore */
    }
    win.addEventListener('afterprint', removeIframe, { once: true })
    window.setTimeout(removeIframe, 4000)
  }
  const schedulePrint = () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.setTimeout(doPrint, 50)
      })
    })
  }
  iframe.addEventListener('load', schedulePrint, { once: true })
  doc.open()
  doc.write(html)
  doc.close()
  if (doc.readyState === 'complete') {
    window.setTimeout(schedulePrint, 0)
  }
  window.setTimeout(() => {
    if (!printed) schedulePrint()
  }, 400)
}

function printSummaryPairTables() {
  if (!hasSummaryPairPrintData.value) {
    ElMessage.warning('印刷するデータがありません')
    return
  }
  summaryPairPrintLoading.value = true
  try {
    const html = buildSummaryPairPrintHtml()
    printHtmlViaHiddenIframe(html, 'メッキ前在庫／見込数量 印刷')
  } catch {
    ElMessage.error('印刷の準備に失敗しました')
  } finally {
    summaryPairPrintLoading.value = false
  }
}

function onDragFromLeftRow(row: LeftPaneRow, evt?: DragEvent) {
  draggingInventoryRow.value = true
  if (evt?.dataTransfer) {
    evt.dataTransfer.effectAllowed = 'copy'
    evt.dataTransfer.setData('application/x-plating-inventory', row.product_cd || row.product_name)
    evt.dataTransfer.setData('text/plain', row.product_cd || row.product_name)
  }
  draggingSource.value = {
    source_key: `L-${row.product_cd}-${row.plating_machine}-${Date.now()}`,
    source_type: 'left_inventory',
    product_cd: row.product_cd,
    product_name: row.product_name,
    plating_machine: row.plating_machine,
    kake: parseKakeCount(row.plating_efficiency) ?? 0,
    qty: row.pre_plating_inventory,
  }
}

function onDragFromRightRow(row: RightPaneRow, evt?: DragEvent) {
  draggingInventoryRow.value = true
  if (evt?.dataTransfer) {
    evt.dataTransfer.effectAllowed = 'copy'
    evt.dataTransfer.setData('application/x-plating-inventory', row.product_cd || row.product_name)
    evt.dataTransfer.setData('text/plain', row.product_cd || row.product_name)
  }
  draggingSource.value = {
    source_key: `R-${row.product_cd}-${row.plating_machine}-${Date.now()}`,
    source_type: 'right_gen',
    product_cd: row.product_cd,
    product_name: row.product_name,
    plating_machine: row.plating_machine,
    kake: parseKakeCount(row.plating_efficiency) ?? 0,
    qty: num(row.gen_qty),
  }
}

function bindTableRowDrag(tableRef: { value: any }, rows: LeftPaneRow[] | RightPaneRow[], side: 'left' | 'right') {
  const tableEl = tableRef.value?.$el as HTMLElement | undefined
  if (!tableEl) return
  const trs = tableEl.querySelectorAll('.el-table__body-wrapper tbody tr')
  trs.forEach((tr, idx) => {
    const row = rows[idx]
    if (!row) return
    tr.setAttribute('draggable', 'true')
    tr.classList.add('table-row-draggable')
    ;(tr as HTMLTableRowElement).ondragstart = (ev: DragEvent) => {
      if (side === 'left') onDragFromLeftRow(row as LeftPaneRow, ev)
      else onDragFromRightRow(row as RightPaneRow, ev)
    }
    ;(tr as HTMLTableRowElement).ondragend = () => {
      draggingInventoryRow.value = false
      productDropHoverBlockKey.value = null
      if (!jigDropDialogVisible.value && !productToJigDialogVisible.value && !boardJigEditDialogVisible.value) {
        draggingSource.value = null
      }
    }
  })
}

/** API 明細行用（Cutting と同様：sort_order → id） */
function comparePlatingApiDraftItemBySequence(
  a: { sort_order?: number; id?: number },
  b: { sort_order?: number; id?: number },
): number {
  const sa = a.sort_order ?? 0
  const sb = b.sort_order ?? 0
  if (sa !== sb) return sa - sb
  return (a.id ?? 0) - (b.id ?? 0)
}

/** 追加レイアウトブロック → 保存用 body（カード未配置でも骨格を保持） */
function buildLayoutBlocksForPersist(): PlatingDraftLayoutBody[] {
  if (!layoutBoardReady.value) return []
  return layoutBlocks.value.map((b, i) => ({
    block_seq: i,
    plan_date: b.plan_date,
    start_time: normalizeBoardStartTimeHm(b.start_time),
    minutes_per_lap: Math.max(1, Math.floor(Number(b.minutes_per_lap) || 1)),
    jigs_per_lap: Math.max(1, Math.floor(Number(b.jigs_per_lap) || 1)),
    lap_count: Math.max(1, Math.floor(Number(b.lap_count) || 1)),
    base_lap_no: Math.max(1, Math.floor(Number(b.base_lap_no) || 1)),
  }))
}

function getBoardDateMemo(ymd: string): string {
  return String(boardDateMemosByYmd.value[ymd] ?? '').trim()
}

function applyBoardDateMemosFromDraft(memos: PlatingBoardDateMemoOut[], merge = false) {
  const next = merge ? { ...boardDateMemosByYmd.value } : {}
  for (const row of memos) {
    const d = String(row.lap_work_date ?? '').slice(0, 10)
    if (!d) continue
    next[d] = String(row.memo ?? '')
  }
  boardDateMemosByYmd.value = next
}

function buildBoardDateMemosForPersistFromSnapshot(
  snapshot: PlatingDraftOut | null,
): PlatingBoardDateMemoBody[] {
  const merged = new Map<string, string>()
  for (const row of snapshot?.board_date_memos || []) {
    const d = String(row.lap_work_date ?? '').slice(0, 10)
    if (!d) continue
    merged.set(d, String(row.memo ?? ''))
  }
  for (const [ymd, memo] of Object.entries(boardDateMemosByYmd.value)) {
    if (!ymd) continue
    merged.set(ymd, String(memo ?? '').trim())
  }
  return [...merged.entries()].map(([lap_work_date, memo]) => ({ lap_work_date, memo }))
}

function openBoardDateMemoEdit(ymd: string) {
  const d = String(ymd || '').slice(0, 10)
  if (!d) return
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  boardDateMemoEditYmd.value = d
  boardDateMemoEditValue.value = getBoardDateMemo(d)
  boardDateMemoDialogVisible.value = true
}

async function confirmBoardDateMemoEdit() {
  const ymd = boardDateMemoEditYmd.value
  if (!ymd) return
  const text = boardDateMemoEditValue.value.trim()
  boardDateMemosByYmd.value = { ...boardDateMemosByYmd.value, [ymd]: text }
  boardDateMemoDialogVisible.value = false
  if (!canPersistBoard()) {
    ElMessage.success('メモを入力しました（計画保存後に永続化されます）')
    return
  }
  await flushBoardPersist()
  ElMessage.success('日付メモを保存しました')
}

async function buildDraftPayload(
  items: PlatingDraftItemBody[],
  snapshot: PlatingDraftOut | null,
  persistOpts?: PersistDraftOpts,
) {
  const board_cards = mergePersistBoardCardsFromSnapshot(
    snapshot,
    scheduleCardsToBoardBodies(!!persistOpts?.syncSkeletons),
  )
  const layout_blocks = buildLayoutBlocksForPersist()
  const board_date_memos = buildBoardDateMemosForPersistFromSnapshot(snapshot)
  const firstLayout = layout_blocks[0]
  const planDate =
    (firstLayout?.plan_date || '').trim().slice(0, 10) ||
    draftWorkDate.value ||
    todayYmdJapan()
  return {
    plan_date: planDate,
    daily_minutes: PLATING_DAY_MINUTES,
    jigs_per_lap: layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value,
    max_laps: layoutBoardReady.value ? layoutMaxLaps.value : 1,
    minutes_per_lap: layoutBoardReady.value ? layoutMinutesPerLap.value : minutesPerLap.value,
    board_start_time: firstLayout
      ? normalizeBoardStartTimeHm(firstLayout.start_time)
      : null,
    total_slots: kpi.value.totalSlots,
    used_slots: kpi.value.usedSlots,
    remain_slots: kpi.value.remainSlots,
    items,
    board_cards,
    layout_blocks,
    board_date_memos,
  }
}

/** 更新時に他作業日の明細行を残し、当該作業日分はボードのみで管理する */
function mergePersistItemsFromSnapshot(snapshot: PlatingDraftOut | null): PlatingDraftItemBody[] {
  if (!snapshot) return []
  const wd = draftWorkDate.value || todayYmdJapan()
  const plan = String(snapshot.plan_date || '').slice(0, 10) || wd
  return (snapshot.items || [])
    .filter((it) => effectiveItemWorkDate(it, plan) !== wd)
    .sort(comparePlatingApiDraftItemBySequence)
    .map(apiItemToBody)
    .map((x, i) => ({ ...x, sort_order: i + 1 }))
}

function scheduleCardsToBoardBodies(includeEmptySlots = false): PlatingBoardCardBody[] {
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  const lapTimesMap = buildBoardLapTimesMap()
  const fallbackYmd = draftWorkDate.value || todayYmdJapan()
  return [...scheduleCardsForCurrentDraft()]
    .filter((c) => shouldPersistBoardCard(c) && (includeEmptySlots || c.qty > 0))
    .sort((a, b) => compareLapNoForBoardSort(a.lap_no, b.lap_no, scheduleByLap) || a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    .map((c) => {
      const slot = scheduleByLap.get(c.lap_no)
      const times = lapTimesMap.get(c.lap_no)
      const lapYmd = (c.lap_work_date || '').slice(0, 10) || slot?.work_date || fallbackYmd
      const lapStart =
        times?.start ||
        (c.lap_start_time ? normalizeBoardStartTimeHm(c.lap_start_time) : null) ||
        slot?.start ||
        null
      const lapEnd =
        times?.end ||
        (c.lap_end_time ? normalizeBoardStartTimeHm(c.lap_end_time) : null) ||
        slot?.end ||
        null
      return {
        lap_work_date: lapYmd,
        lap_start_time: lapStart,
        lap_end_time: lapEnd,
        lap_no: c.persist_lap_no ?? c.lap_no,
        turn_seq: c.turn_seq,
        product_cd: c.product_cd,
        product_name: c.product_name,
        plating_machine: c.plating_machine,
        kake: c.kake,
        qty: c.qty,
        slots: c.slots,
        board_mark: c.boardMark,
        stable_key: (c.id || '').slice(0, 128) || null,
        until_depleted: !!c.untilDepleted,
        text_red: !!c.forceRedText,
      }
    })
}

function lapScheduleStartHmForSort(lapNo: number, scheduleByLap: Map<number, LapScheduleSlot>): string {
  const slot = scheduleByLap.get(lapNo)
  const cardStart = lapCardMetaByLap.value.get(lapNo)?.start
  return normalizeBoardStartTimeHm(cardStart || slot?.start || '99:99')
}

/** ボード表示・保存：作業日 → 開始時刻 → 周目番号 */
function compareLapNoForBoardSort(
  lapA: number,
  lapB: number,
  scheduleByLap: Map<number, LapScheduleSlot>,
): number {
  const cardWd = (lapNo: number) => lapCardMetaByLap.value.get(lapNo)?.work_date ?? ''
  const da = cardWd(lapA) || (scheduleByLap.get(lapA)?.work_date ?? '')
  const db = cardWd(lapB) || (scheduleByLap.get(lapB)?.work_date ?? '')
  if (da !== db) return da.localeCompare(db)
  const ta = lapScheduleStartHmForSort(lapA, scheduleByLap)
  const tb = lapScheduleStartHmForSort(lapB, scheduleByLap)
  if (ta !== tb) return ta.localeCompare(tb)
  return lapA - lapB
}

/** 更新時に他作業日のボード行をマージし、PUT で aps_plating_plan_board_cards を誤削除しない */
function mergePersistBoardCardsFromSnapshot(
  snapshot: PlatingDraftOut | null,
  mine: PlatingBoardCardBody[],
): PlatingBoardCardBody[] {
  if (!snapshot) return mine
  const datesInMine = new Set(mine.map((bc) => boardCardLapWorkDate(bc)).filter(Boolean))
  const kept = (snapshot.board_cards || [])
    .filter((bc) => !datesInMine.has(boardCardLapWorkDate(bc)))
    .map(apiBoardCardToBody)
  return [...kept, ...mine]
}

let boardAutosaveTimer: ReturnType<typeof setTimeout> | null = null
/** ドラッグ連続操作時の PUT 間隔（ms） */
const BOARD_AUTOSAVE_MS = 1400
let persistDraftInFlight: Promise<void> | null = null
type PersistDraftOpts = { syncSkeletons?: boolean }

function cancelBoardAutosaveTimer() {
  if (boardAutosaveTimer != null) {
    clearTimeout(boardAutosaveTimer)
    boardAutosaveTimer = null
  }
}

function canPersistBoard(): boolean {
  return layoutBoardReady.value && layoutBlocks.value.length > 0
}

/** 追加レイアウト（layout_blocks ＋ board_cards 空枠）を DB へ即時保存 */
async function flushLayoutPersist(notify = false) {
  cancelBoardAutosaveTimer()
  if (isBoardHydratingFromApi.value || loadingDraft.value) return
  if (!layoutBoardReady.value || layoutBlocks.value.length === 0) {
    if (notify) ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  try {
    await persistDraft(notify, { syncSkeletons: true })
  } catch (e) {
    console.error(e)
    if (notify) ElMessage.error('レイアウトの保存に失敗しました')
    throw e
  }
}

/** ドラッグ等の高頻度変更：デバウンス後に aps_plating_plan_board_cards へ書込（persistDraft の board_cards 経由） */
function scheduleBoardAutosave() {
  if (suppressScheduleSideEffects > 0) return
  if (isBoardHydratingFromApi.value) return
  if (loadingDraft.value) return
  if (!canPersistBoard()) return
  cancelBoardAutosaveTimer()
  boardAutosaveTimer = setTimeout(() => {
    boardAutosaveTimer = null
    void persistDraft(false).catch((e) => console.error(e))
  }, BOARD_AUTOSAVE_MS)
}

/** 再割当・緊急挿し込み・クリア等：デバウンスを解除して直ちに DB へ反映 */
async function flushBoardPersist(opts?: PersistDraftOpts) {
  cancelBoardAutosaveTimer()
  if (isBoardHydratingFromApi.value) return
  if (loadingDraft.value) return
  if (!canPersistBoard()) return
  try {
    await persistDraft(false, opts)
  } catch (e) {
    console.error(e)
  }
}

async function persistDraft(notify = true, opts?: PersistDraftOpts) {
  if (persistDraftInFlight) return persistDraftInFlight
  persistDraftInFlight = (async () => {
    const layout_blocks_preview = buildLayoutBlocksForPersist()
    if (layout_blocks_preview.length === 0) {
      if (notify) ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
      return
    }
    if (!draftWorkDate.value) {
      draftWorkDate.value = layout_blocks_preview[0]!.plan_date
    }
    if (opts?.syncSkeletons) {
      withSuppressedScheduleSideEffects(() => ensureBoardCardSkeletonsForLayout())
    }
    let snapshot: PlatingDraftOut | null = null
    if (currentDraftId.value) {
      try {
        const wd = draftWorkDate.value || todayYmdJapan()
        snapshot = await fetchPlatingDraftById(currentDraftId.value, { workDate: wd })
      } catch (e) {
        console.error(e)
        if (notify) ElMessage.error('計画データの取得に失敗しました')
        return
      }
    }
    const items = mergePersistItemsFromSnapshot(snapshot)
    const body = await buildDraftPayload(items, snapshot, opts)
    if (currentDraftId.value) {
      await updatePlatingDraft(currentDraftId.value, body)
    } else {
      const created = await createPlatingDraft(body)
      currentDraftId.value = created.id
    }
  })().finally(() => {
    persistDraftInFlight = null
  })
  return persistDraftInFlight
}

type LoadLatestDraftOpts = { autoMode?: boolean; autoSyncWorkDate?: boolean }

type BoardCardWithDisplayLap = PlatingBoardCardOut & { persist_lap_no: number }

/** 読込時：保存 lap_no をボード行に復元（空き周目を飛ばしても 1→5 のまま）。同一作業日で他 draft と番号が衝突する場合のみずらす */
function assignDisplayLapNumbers(boards: PlatingBoardCardOut[]): BoardCardWithDisplayLap[] {
  const sorted = [...boards].sort((a, b) => {
    const da = boardCardLapWorkDate(a)
    const db = boardCardLapWorkDate(b)
    if (da !== db) return da.localeCompare(db)
    if (a.lap_no !== b.lap_no) return a.lap_no - b.lap_no
    if (a.turn_seq !== b.turn_seq) return a.turn_seq - b.turn_seq
    return (a.id ?? 0) - (b.id ?? 0)
  })
  const lapKeyToNo = new Map<string, number>()
  const usedLapOnDate = new Map<string, Set<number>>()
  return sorted.map((bc) => {
    const persist_lap_no = Math.max(1, Math.floor(Number(bc.lap_no) || 0))
    const wd = boardCardLapWorkDate(bc)
    const key = `${bc.draft_id}-${wd}-${persist_lap_no}`
    if (!lapKeyToNo.has(key)) {
      const taken = usedLapOnDate.get(wd) ?? new Set<number>()
      let lapNo = persist_lap_no
      while (taken.has(lapNo)) lapNo += 1
      taken.add(lapNo)
      usedLapOnDate.set(wd, taken)
      lapKeyToNo.set(key, lapNo)
    }
    return { ...bc, persist_lap_no, lap_no: lapKeyToNo.get(key)! }
  })
}


/** 表示期間内のボード行＋レイアウトブロックを集約（board_cards は lap_work_date で SQL 期間フィルタ） */
async function loadBoardAcrossViewRange(): Promise<{
  boardCards: BoardCardWithDisplayLap[]
  primary: PlatingDraftOut | null
  layoutBlocks: PlatingDraftLayoutOut[]
  boardDateMemos: PlatingBoardDateMemoOut[]
}> {
  const { from, to } = boardViewRange.value
  const preferredDraftId = currentDraftId.value ? Number(currentDraftId.value) : undefined
  const view = await fetchPlatingBoardView({
    boardFrom: from,
    boardTo: to,
    preferredDraftId: preferredDraftId && preferredDraftId > 0 ? preferredDraftId : undefined,
  })
  return {
    boardCards: assignDisplayLapNumbers(view.board_cards || []),
    primary: view.primary ?? null,
    layoutBlocks: view.layout_blocks || [],
    boardDateMemos: view.board_date_memos || [],
  }
}

/** 集約 layout_blocks：表示期間は board_cards.lap_work_date、または layout の計画日で判定 */
function layoutBlockHasLapsInBoardView(block: {
  plan_date?: string | null
  start_time?: string | null
  minutes_per_lap?: number | null
  lap_count?: number | null
}): boolean {
  const pd = String(block.plan_date || '').slice(0, 10)
  if (!pd) return false
  const rows = buildLapScheduleRows(
    pd,
    block.start_time ?? '',
    Math.max(1, Math.floor(Number(block.minutes_per_lap) || 1)),
    Math.max(1, Math.floor(Number(block.lap_count) || 1)),
  )
  return rows.some((r) => isYmdInBoardView(r.work_date))
}

function normalizeLayoutBlocksForView(
  blocks: PlatingDraftLayoutOut[],
  boardCards: BoardCardWithDisplayLap[] = [],
): BoardLayoutBlock[] {
  if (blocks.length === 0) return []
  const lapNosInView = boardCards.length > 0 ? boardLapNosInViewFromCards(boardCards) : new Set<number>()
  const dedup = new Map<string, PlatingDraftLayoutOut>()
  for (const b of blocks) {
    const baseLap = Math.max(1, Math.floor(Number(b.base_lap_no) || 1))
    const lapCount = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const coveredByCards =
      lapNosInView.size > 0 &&
      layoutBlockCoversAnyLap({ base_lap_no: baseLap, lap_count: lapCount }, lapNosInView)
    const coveredByDate = layoutBlockHasLapsInBoardView(b)
    if (!coveredByCards && !coveredByDate) continue
    const pd = String(b.plan_date || '').slice(0, 10)
    if (!pd) continue
    const start = normalizeBoardStartTimeHm(b.start_time)
    const key = `${pd}|${start}|${b.minutes_per_lap}|${b.jigs_per_lap}|${b.lap_count}|${b.base_lap_no}`
    if (!dedup.has(key)) dedup.set(key, b)
  }
  const sorted = [...dedup.values()].sort((a, b) => {
    const pa = String(a.plan_date || '').slice(0, 10)
    const pb = String(b.plan_date || '').slice(0, 10)
    if (pa !== pb) return pa.localeCompare(pb)
    const sa = normalizeBoardStartTimeHm(a.start_time)
    const sb = normalizeBoardStartTimeHm(b.start_time)
    if (sa !== sb) return sa.localeCompare(sb)
    return (a.base_lap_no || 0) - (b.base_lap_no || 0)
  })
  return sorted.map((b) => {
    const lapCount = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const block: BoardLayoutBlock = {
      plan_date: String(b.plan_date || '').slice(0, 10),
      start_time: normalizeBoardStartTimeHm(b.start_time),
      minutes_per_lap: Math.max(1, Math.floor(Number(b.minutes_per_lap) || 1)),
      jigs_per_lap: Math.max(1, Math.floor(Number(b.jigs_per_lap) || 1)),
      lap_count: lapCount,
      base_lap_no: Math.max(1, Math.floor(Number(b.base_lap_no) || 1)),
    }
    return block
  })
}

async function loadLatestDraft(opts?: boolean | LoadLatestDraftOpts) {
  let autoMode = false
  let autoSyncWorkDate = false
  if (typeof opts === 'boolean') {
    autoMode = opts
    autoSyncWorkDate = opts
  } else if (opts) {
    autoMode = opts.autoMode ?? false
    autoSyncWorkDate = opts.autoSyncWorkDate ?? false
  }
  const planDateForDraft = draftWorkDate.value || todayYmdJapan()
  loadingDraft.value = true
  try {
    const {
      boardCards: mergedBoard,
      primary,
      layoutBlocks: mergedLayoutBlocks,
      boardDateMemos: mergedBoardDateMemos,
    } = await loadBoardAcrossViewRange()
    if (!primary) {
      currentDraftId.value = null
      scheduleCards.value = []
      standardPositions.value = new Map()
      layoutBoardReady.value = false
      layoutBlocks.value = []
      boardDateMemosByYmd.value = {}
      if (!autoMode) ElMessage.warning('表示期間内の計画データはありません')
      return
    }

    const display = primary
    applyBoardDateMemosFromDraft(
      mergedBoardDateMemos.length > 0 ? mergedBoardDateMemos : display.board_date_memos || [],
      true,
    )
    const planKey = String(display.plan_date || planDateForDraft).slice(0, 10)
    const boardDates = mergedBoard
      .map((bc) => ({ work_date: boardCardLapWorkDate(bc) }))
      .filter((it) => Boolean(it.work_date))

    let wd = draftWorkDate.value || planDateForDraft
    if (autoSyncWorkDate && boardDates.length > 0) {
      const hasMatch = boardDates.some((it) => it.work_date === wd)
      if (!hasMatch) {
        wd = dominantWorkDateFromItems(boardDates)
      }
    }
    if (wd !== draftWorkDate.value) {
      syncingDraftWorkDateFromLoad.value = true
      draftWorkDate.value = wd
      await nextTick()
      syncingDraftWorkDateFromLoad.value = false
    }

    currentDraftId.value = display.id

    if (mergedBoard.length > 0) {
      const wdCounts = new Map<string, number>()
      for (const bc of mergedBoard) {
        const wd = boardCardLapWorkDate(bc)
        if (!isYmdInBoardView(wd)) continue
        wdCounts.set(wd, (wdCounts.get(wd) ?? 0) + 1)
      }
      const dominantWd = [...wdCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
      if (dominantWd) layoutPlanDate.value = dominantWd
    }

    isBoardHydratingFromApi.value = true
    let boardStaleSlotsPruned = false
    try {
      const jp = Math.max(1, Math.floor(Number(display.jigs_per_lap) || 0))
      const mp = Math.max(1, Math.floor(Number(display.minutes_per_lap) || 100))
      if (jp > 0) jigsPerLap.value = jp
      minutesPerLap.value = mp
      layoutMinutesPerLap.value = mp
      const rawBoard = mergedBoard
      const persistedBlocks = normalizeLayoutBlocksForView(mergedLayoutBlocks || [], rawBoard)
      let nextBlocks: BoardLayoutBlock[] = persistedBlocks
      if (nextBlocks.length === 0 && rawBoard.length > 0) {
        const legacyPlan = boardCardLapWorkDate(rawBoard[0]!) || todayYmdJapan()
        nextBlocks = inferLayoutBlocksFromBoard(rawBoard, {
          plan_date: legacyPlan,
          board_start_time: normalizeBoardStartTimeHm(display.board_start_time),
          minutes_per_lap: mp,
          jigs_per_lap: jp > 0 ? jp : layoutJigsPerLap.value,
          max_laps: Math.max(1, Math.floor(Number(display.max_laps) || 0)),
        })
      }
      layoutBlocks.value = nextBlocks
      layoutBoardReady.value = layoutBlocks.value.length > 0
      if (layoutBoardReady.value) {
        layoutJigsPerLap.value = layoutBlocks.value[0]!.jigs_per_lap
        applyLayoutHeaderFromFirstBlock()
        recomputeLayoutMaxLapsFromSchedule()
        const maxFromCards = rawBoard.length > 0 ? Math.max(...rawBoard.map((b) => b.lap_no)) : 0
        if (maxFromCards > layoutMaxLaps.value) layoutMaxLaps.value = maxFromCards
      } else {
        layoutBlocks.value = []
      }
      const hasLayout = layoutBoardReady.value
      if (rawBoard.length > 0) {
        const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
        scheduleCards.value = rawBoard
          .slice()
          .sort(
            (a, b) =>
              compareLapNoForBoardSort(a.lap_no, b.lap_no, scheduleByLap) ||
              a.turn_seq - b.turn_seq ||
              (a.id ?? 0) - (b.id ?? 0),
          )
          .map((bc, idx) => {
            const mk: BoardMark =
              bc.board_mark === 'rush' || bc.board_mark === 'manual' ? bc.board_mark : 'standard'
            const id = (bc.stable_key || '').trim() || `db-${bc.draft_id}-${bc.id}-${idx}`
            return {
              id,
              product_cd: bc.product_cd,
              product_name: bc.product_name,
              plating_machine: bc.plating_machine,
              kake: Number(bc.kake) || 0,
              qty: Number(bc.qty) || 0,
              slots: Number(bc.slots) || 0,
              lap_no: Number(bc.lap_no) || 0,
              persist_lap_no: Number(bc.persist_lap_no) || Number(bc.lap_no) || 0,
              lap_work_date: boardCardLapWorkDate(bc),
              lap_start_time: bc.lap_start_time ?? null,
              lap_end_time: bc.lap_end_time ?? null,
              source_draft_id: bc.draft_id,
              turn_seq: bc.turn_seq,
              colorIdx: idx,
              boardMark: mk,
              untilDepleted: !!bc.until_depleted,
              forceRedText: !!bc.text_red,
            }
          })
        standardPositions.value = new Map(
          scheduleCards.value
            .filter((c) => c.boardMark === 'standard')
            .map((c) => [c.id, { lap_no: c.lap_no, turn_seq: c.turn_seq }]),
        )
        withSuppressedScheduleSideEffects(() => {
          boardStaleSlotsPruned = pruneStaleEmptySlots()
          ensureBoardCardSkeletonsForLayout()
          syncScheduleCardLapTimesFromLayout()
        })
      } else if (!hasLayout) {
        scheduleCards.value = []
        standardPositions.value = new Map()
        layoutBoardReady.value = false
      } else {
        scheduleCards.value = []
        standardPositions.value = new Map()
        withSuppressedScheduleSideEffects(() => {
          ensureBoardCardSkeletonsForLayout()
          syncScheduleCardLapTimesFromLayout()
        })
      }
    } finally {
      void nextTick(() => {
        setTimeout(() => {
          isBoardHydratingFromApi.value = false
          scheduleInitBoardLapSortables()
          if (boardStaleSlotsPruned && canPersistBoard()) {
            void flushBoardPersist()
          }
        }, 0)
      })
    }

    if (!autoMode) ElMessage.success(`計画（ID ${display.id}）を読み込みました`)
  } catch (e) {
    console.error(e)
    if (!autoMode) ElMessage.error('計画の読み込みに失敗しました')
  } finally {
    loadingDraft.value = false
  }
}

async function loadJigAvailability() {
  if (jigAvailabilityLoadPromise) return jigAvailabilityLoadPromise
  jigAvailabilityLoadPromise = (async () => {
    loadingJigAvailability.value = true
    try {
      const [res, bundle] = await Promise.all([
        getMachineList({
          machine_type: PLATING_MACHINE_TYPE,
          page: 1,
          pageSize: 10000,
        }),
        fetchEquipmentEfficiencyBundle(),
      ])
      const mergedCatalog = new Map(jigProductCatalogByMachine.value)
      for (const [mk, byProd] of bundle.catalogByMachine) {
        const existing = mergedCatalog.get(mk) ?? new Map<string, JigProductCatalogRow>()
        for (const [cd, row] of byProd) {
          if (!existing.has(cd)) existing.set(cd, row)
        }
        mergedCatalog.set(mk, existing)
      }
      jigProductCatalogByMachine.value = mergedCatalog

      const listRes = res as MachineListResponse
      const rows = ((listRes?.data?.list ?? listRes?.list ?? []) as MachineItem[]).filter(
        (r) =>
          String(r.machine_type || '').trim() === PLATING_MACHINE_TYPE &&
          normalizePjmStatus(r.status) === 'active',
      )
      rows.sort((a, b) =>
        String(a.machine_name || a.machine_cd || '').localeCompare(
          String(b.machine_name || b.machine_cd || ''),
          'ja',
        ),
      )
      jigAvailabilityRows.value = rows.map((m) => ({
        machine_id: m.id ?? null,
        plating_machine: String(m.machine_name || m.machine_cd || '').trim() || '—',
        available_qty: Math.max(0, Math.floor(Number(m.available_qty) || 0)),
      }))
    } catch (e) {
      console.error(e)
      ElMessage.error('メッキ治具の取得に失敗しました（設備マスタを確認してください）')
      jigAvailabilityRows.value = []
    } finally {
      loadingJigAvailability.value = false
      jigAvailabilityLoadPromise = null
    }
  })()
  return jigAvailabilityLoadPromise
}

const pjmFilteredList = computed(() => {
  const k = pjmKeyword.value.trim().toLowerCase()
  if (!k) return pjmList.value
  return pjmList.value.filter(
    (row) =>
      String(row.machine_cd || '')
        .toLowerCase()
        .includes(k) ||
      String(row.machine_name || '')
        .toLowerCase()
        .includes(k),
  )
})

function normalizePjmStatus(s: string | undefined): 'active' | 'maintenance' | 'inactive' {
  if (s === 'maintenance' || s === 'inactive') return s
  return 'active'
}

async function onPjmStatusChange(row: MachineItem, status: string) {
  const next = normalizePjmStatus(status)
  if (row.id == null || normalizePjmStatus(row.status) === next) return
  const prev = row.status
  row.status = next
  pjmStatusSavingId.value = row.id
  try {
    await updateMachine({
      id: row.id,
      machine_cd: row.machine_cd,
      machine_name: row.machine_name,
      machine_type: row.machine_type || PLATING_MACHINE_TYPE,
      status: next,
      available_from: row.available_from,
      available_to: row.available_to,
      calendar_id: row.calendar_id,
      efficiency: row.efficiency,
      available_qty: row.available_qty,
      note: row.note,
    })
    ElMessage.success('状態を更新しました')
    await loadJigAvailability()
  } catch (e) {
    console.error(e)
    row.status = prev
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    pjmStatusSavingId.value = null
  }
}

async function loadPlatingJigMasterList() {
  pjmLoading.value = true
  try {
    const res = (await getMachineList({
      machine_type: PLATING_MACHINE_TYPE,
      page: 1,
      pageSize: 10000,
    })) as MachineListResponse
    const rows = ((res?.data?.list ?? res?.list ?? []) as MachineItem[]).filter(
      (r) => String(r.machine_type || '').trim() === PLATING_MACHINE_TYPE,
    )
    rows.sort((a, b) =>
      String(a.machine_cd || '').localeCompare(String(b.machine_cd || ''), 'ja'),
    )
    pjmList.value = rows
  } catch (e) {
    console.error(e)
    ElMessage.error('設備マスタの取得に失敗しました')
    pjmList.value = []
  } finally {
    pjmLoading.value = false
  }
}

function openPlatingJigMasterDialog() {
  pjmKeyword.value = ''
  platingJigMasterDialogVisible.value = true
}

function openPlatingJigMasterForm(row: MachineItem | null = null) {
  pjmEditData.value = row
    ? { ...row }
    : ({
        machine_type: PLATING_MACHINE_TYPE,
        status: 'active',
        efficiency: 100,
        available_qty: 0,
      } as MachineItem)
  pjmFormVisible.value = true
}

async function onPlatingJigMasterSaved() {
  invalidateEquipmentEfficiencyBundleCache()
  await loadPlatingJigMasterList()
  await loadJigAvailability()
  await loadSummaryPair()
}

/** 当該周目に既に配置されている治具本数（他周目は含めない） */
function countBoardSlotsForMachine(platingMachine: string, lapNo: number): number {
  const key = normalizeMachineKey(platingMachine)
  return boardOccupancyIndex.value.machineQtyByLap.get(lapNo)?.get(key) ?? 0
}

function getJigAvailMaxFromMaster(platingMachine: string): number {
  const row = jigAvailabilityRows.value.find(
    (r) => normalizeMachineKey(r.plating_machine) === normalizeMachineKey(platingMachine),
  )
  return row ? Math.max(0, Math.floor(Number(row.available_qty) || 0)) : 0
}

function resolveJigDropTargetLap(preferLap: number | null): number {
  const maxLaps = layoutMaxLaps.value
  if (preferLap != null && preferLap >= 1 && preferLap <= maxLaps) return preferLap
  return 1
}

/** 当該周目のボード空き枠数（列数ベース） */
function countBoardSlotsRemainingOnLap(lapNo: number): number {
  if (!layoutBoardReady.value) return 0
  return Math.max(0, lapBoardColCount.value - occupiedQtyOnLap(lapNo))
}

/** レイアウト 1 周あたりの治具本数上限と当該周の使用状況 */
function layoutJigCapacityOnLap(lapNo: number): { layoutMax: number; usedOnLap: number; remainOnLap: number } {
  const layoutMax = lapBoardColCount.value
  const usedOnLap = occupiedQtyOnLap(lapNo)
  return {
    layoutMax,
    usedOnLap,
    remainOnLap: Math.max(0, layoutMax - usedOnLap),
  }
}

function warnLayoutJigCapacityExceeded(lapNo: number, requestedQty: number) {
  const { layoutMax, usedOnLap, remainOnLap } = layoutJigCapacityOnLap(lapNo)
  const req = Math.max(0, Math.floor(Number(requestedQty) || 0))
  if (req > 0 && req > remainOnLap) {
    ElMessage.warning(
      `第${lapDisplayNo(lapNo)}周目のレイアウトは1周${layoutMax}本までです（配置済み${usedOnLap}本）。あと${remainOnLap}本まで追加できます（${req}本は入りません）`,
    )
    return
  }
  ElMessage.warning(
    `第${lapDisplayNo(lapNo)}周目はレイアウト上限（${layoutMax}本）に達しています（配置済み${usedOnLap}本）`,
  )
}

function getJigQtyMaxForLap(platingMachine: string, lapNo: number, currentBlockSize = 0): number {
  const avail = getJigAvailMaxFromMaster(platingMachine)
  const usedOnLap = countBoardSlotsForMachine(platingMachine, lapNo)
  const jigMax = Math.max(0, avail - usedOnLap + currentBlockSize)
  const boardMax = countBoardSlotsRemainingOnLap(lapNo) + currentBlockSize
  return Math.max(0, Math.min(jigMax, boardMax))
}

/** 他周目へ移動する治具ブロックが当該周の使用可能本数・列数内に収まるか */
function canPlaceJigBlockOnLap(platingMachine: string, targetLapNo: number, blockSize: number): boolean {
  const size = Math.max(0, Math.floor(Number(blockSize) || 0))
  if (size <= 0 || targetLapNo <= 0) return false
  return size <= getJigQtyMaxForLap(platingMachine, targetLapNo, 0)
}

function warnJigLapCapacityExceeded(platingMachine: string, lapNo: number, blockSize: number) {
  const avail = getJigAvailMaxFromMaster(platingMachine)
  const used = countBoardSlotsForMachine(platingMachine, lapNo)
  const boardRemain = countBoardSlotsRemainingOnLap(lapNo)
  ElMessage.warning(
    `${platingMachine} は第${lapDisplayNo(lapNo)}周目で使用可能 ${avail} 本までです（配置済 ${used} 本・移動 ${blockSize} 本・空き列 ${boardRemain}）`,
  )
}

function getLapNoFromSortableEl(el: HTMLElement | null | undefined): number {
  if (!el) return 0
  const row = el.closest<HTMLElement>('.lap-board-body-row--lap')
  return Number(row?.dataset.lapNo) || 0
}

function isBoardJigSortableContainer(el: HTMLElement | null | undefined): boolean {
  if (!el) return false
  return Boolean(el.closest('.lap-merged-host, .lap-merged-tail'))
}

function getPlatingMachineForCardIds(cardIds: string[]): string {
  const idSet = new Set(cardIds)
  const card = scheduleCards.value.find((c) => idSet.has(c.id) && c.qty > 0)
  return String(card?.plating_machine || '').trim()
}

let lastJigCrossLapWarnAt = 0
let lastJigSameLapWarnAt = 0

function warnJigPartialBlockDrag() {
  const now = Date.now()
  if (now - lastJigSameLapWarnAt > 800) {
    lastJigSameLapWarnAt = now
    ElMessage.warning(
      'メッキ治具はブロック単位でのみ移動できます（結合表示の治具ブロックをドラッグしてください）',
    )
  }
}

/** ドラッグ要素が治具ブロック全体かどうか（結合表示の data-block-ids、または単独でない末尾列） */
function isDraggedFullJigBlock(el: HTMLElement, lapNo: number): boolean {
  if (lapNo <= 0 || el.classList.contains('lap-merged-tail-item')) return false
  const parsed = parseCardIdsFromDragItem(el)
  if (parsed.length === 0) return false
  const blockIds = findJigBlockCardIds(parsed[0], lapNo)
  if (blockIds.length === 0) return false
  if ((el.dataset.blockIds || '').trim()) return true
  const parsedSet = new Set(parsed)
  return blockIds.length === parsed.length && blockIds.every((id) => parsedSet.has(id))
}

function boardJigSortablePut(to: Sortable, from: Sortable, dragEl: HTMLElement): boolean {
  const fromLap = getLapNoFromSortableEl(from.el as HTMLElement)
  const toLap = getLapNoFromSortableEl(to.el as HTMLElement)
  if (fromLap <= 0 || toLap <= 0) return false
  return isDraggedFullJigBlock(dragEl, fromLap)
}

function boardJigSortableOnMove(evt: Sortable.MoveEvent): boolean {
  const toEl = evt.to as HTMLElement
  const fromEl = evt.from as HTMLElement
  if (!isBoardJigSortableContainer(toEl)) return false

  const toLap = getLapNoFromSortableEl(toEl)
  const fromLap = getLapNoFromSortableEl(fromEl)
  if (toLap <= 0 || fromLap <= 0) return false

  const dragged = evt.dragged as HTMLElement
  if (!isDraggedFullJigBlock(dragged, fromLap)) {
    warnJigPartialBlockDrag()
    return false
  }

  if (toEl.classList.contains('lap-merged-tail')) return false

  if (fromLap === toLap) return toEl.classList.contains('lap-merged-host')

  const cardIds = resolveDragBlockCardIds(dragged, fromLap)
  const machine = getPlatingMachineForCardIds(cardIds)
  if (!machine) return false

  if (canPlaceJigBlockOnLap(machine, toLap, cardIds.length)) return true

  const now = Date.now()
  if (now - lastJigCrossLapWarnAt > 800) {
    lastJigCrossLapWarnAt = now
    warnJigLapCapacityExceeded(machine, toLap, cardIds.length)
  }
  return false
}

/** 治具ブロック全体を対象周の末尾へ移動し、ブロック内順序を維持（DOM順による他治具への割り込みを防止） */
function moveJigBlockToLap(cardIds: string[], fromLap: number, toLap: number): boolean {
  const idSet = new Set(cardIds)
  const block = scheduleCards.value
    .filter((c) => idSet.has(c.id))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  if (block.length === 0 || block.length !== cardIds.length) return false

  const rest = scheduleCards.value.filter((c) => !idSet.has(c.id))
  const fromRest = rest
    .filter((c) => c.qty > 0 && c.lap_no === fromLap)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const toRest = rest
    .filter((c) => c.qty > 0 && c.lap_no === toLap)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const remainder = rest.filter((c) => !(c.qty > 0 && (c.lap_no === fromLap || c.lap_no === toLap)))
  // 保存用は persist_lap_no を優先するため、移動時に同期しておく
  const maxTurnOnTo = toRest.reduce((m, c) => Math.max(m, Math.floor(Number(c.turn_seq) || 0)), 0)
  const moved = block.map((c, i) => ({
    ...c,
    lap_no: toLap,
    persist_lap_no: toLap,
    turn_seq: maxTurnOnTo + 1 + i,
  }))
  const mergedTo = [...toRest, ...moved]
  fromRest.forEach((c, i) => {
    c.turn_seq = i + 1
  })

  scheduleCards.value = [...remainder, ...fromRest, ...mergedTo]
  refreshMarksAgainstStandardPositions()
  return true
}

function boardJigSortableOnEnd(evt: Sortable.SortableEvent) {
  const toEl = evt.to as HTMLElement | undefined
  const fromEl = evt.from as HTMLElement | undefined
  if (!toEl || !fromEl || !isBoardJigSortableContainer(toEl)) return

  const toLap = getLapNoFromSortableEl(toEl)
  const fromLap = getLapNoFromSortableEl(fromEl)
  const dragged = evt.item as HTMLElement
  if (toLap <= 0 || fromLap <= 0) return

  if (!isDraggedFullJigBlock(dragged, fromLap)) {
    nextTick(() => initBoardLapSortables())
    return
  }

  const cardIds = resolveDragBlockCardIds(dragged, fromLap)
  if (cardIds.length === 0) {
    nextTick(() => initBoardLapSortables())
    return
  }

  if (fromLap === toLap) {
    const row = toEl.closest<HTMLElement>('.lap-board-body-row--lap')
    if (row) syncJigBlockOrderOnLap(row, toLap)
    nextTick(() => {
      initBoardLapSortables()
      void flushBoardPersist()
    })
    return
  }

  const machine = getPlatingMachineForCardIds(cardIds)
  if (!machine || !canPlaceJigBlockOnLap(machine, toLap, cardIds.length)) {
    const { remainOnLap } = layoutJigCapacityOnLap(toLap)
    if (remainOnLap < cardIds.length) {
      warnLayoutJigCapacityExceeded(toLap, cardIds.length)
    } else {
      warnJigLapCapacityExceeded(machine || '治具', toLap, cardIds.length)
    }
    nextTick(() => initBoardLapSortables())
    return
  }

  if (!moveJigBlockToLap(cardIds, fromLap, toLap)) {
    nextTick(() => initBoardLapSortables())
    return
  }

  ElMessage.success(
    `${machine} を第${lapDisplayNo(fromLap)}周目から第${lapDisplayNo(toLap)}周目へ移動しました（${cardIds.length} 本）`,
  )
  nextTick(() => {
    initBoardLapSortables()
    void flushBoardPersist()
  })
}

function findNextSequentialBoardSlots(
  count: number,
  preferLap?: number | null,
): { lap_no: number; turn_seq: number }[] {
  if (!layoutBoardReady.value || count <= 0) return []
  const maxLaps = layoutMaxLaps.value
  /** 特定周へドロップ時は当該周のみ。未指定時は第1周から順に各周で上限を別計算 */
  const lapOrder: number[] =
    preferLap != null && preferLap >= 1 && preferLap <= maxLaps
      ? [preferLap]
      : Array.from({ length: maxLaps }, (_, i) => i + 1)
  const out: { lap_no: number; turn_seq: number }[] = []
  const pickedCountByLap = new Map<number, number>()
  const pickedTurnsByLap = new Map<number, Set<number>>()
  const { occupiedTurnsByLap, maxTurnByLap } = boardOccupancyIndex.value
  for (const lap of lapOrder) {
    const { remainOnLap } = layoutJigCapacityOnLap(lap)
    if (remainOnLap <= 0) continue
    const maxTurn = maxTurnByLap.get(lap) ?? 0
    const occupiedTurns = occupiedTurnsByLap.get(lap) ?? new Set<number>()
    const pickedTurns = pickedTurnsByLap.get(lap) ?? new Set<number>()
    pickedTurnsByLap.set(lap, pickedTurns)
    /** 当該周へドロップ時は末尾から turn_seq を採番（列 123〜129 など右端配置） */
    let nextTurn =
      preferLap != null && preferLap === lap && maxTurn > 0 ? maxTurn + 1 : 1
    while (out.length < count && (pickedCountByLap.get(lap) ?? 0) < remainOnLap) {
      const occupied = occupiedTurns.has(nextTurn) || pickedTurns.has(nextTurn)
      if (!occupied) {
        out.push({ lap_no: lap, turn_seq: nextTurn })
        pickedTurns.add(nextTurn)
        pickedCountByLap.set(lap, (pickedCountByLap.get(lap) ?? 0) + 1)
      }
      nextTurn += 1
      if (nextTurn > 5000) break
    }
    if (out.length >= count) break
  }
  return out.slice(0, count)
}

function resetJigDropDialog() {
  jigDropPending.value = null
  jigDropPreferLap.value = null
  jigDropQty.value = 1
  jigDropQtyMax.value = 1
}

function openJigDropDialog(
  row: { plating_machine: string; available_qty: number },
  preferLap: number | null,
) {
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  const targetLap = resolveJigDropTargetLap(preferLap)
  const availableMax = getJigAvailMaxFromMaster(row.plating_machine)
  const usedOnLap = countBoardSlotsForMachine(row.plating_machine, targetLap)
  const maxQty = getJigQtyMaxForLap(row.plating_machine, targetLap)
  if (maxQty <= 0) {
    const remainJig = Math.max(0, availableMax - usedOnLap)
    const { layoutMax, usedOnLap: usedLayout, remainOnLap } = layoutJigCapacityOnLap(targetLap)
    if (remainJig <= 0) {
      ElMessage.warning(
        `${row.plating_machine} は第${lapDisplayNo(targetLap)}周目で使用可能本数を超えています（当該周 ${availableMax} 本・済 ${usedOnLap} 本）`,
      )
    } else if (remainOnLap <= 0) {
      ElMessage.warning(
        `第${lapDisplayNo(targetLap)}周目はレイアウト上限（1周${layoutMax}本）です（配置済み${usedLayout}本）。あと0本まで追加できます`,
      )
    } else {
      ElMessage.warning(
        `第${lapDisplayNo(targetLap)}周目へ投入できません（レイアウトあと${remainOnLap}本・マスタ使用可能あと${remainJig}本）`,
      )
    }
    return
  }
  const { layoutMax, usedOnLap: layoutUsed, remainOnLap } = layoutJigCapacityOnLap(targetLap)
  jigDropPending.value = {
    plating_machine: row.plating_machine,
    available_max: availableMax,
    used_on_board: usedOnLap,
    target_lap: targetLap,
    layout_max: layoutMax,
    layout_used: layoutUsed,
    layout_remain: remainOnLap,
  }
  jigDropPreferLap.value = targetLap
  jigDropQtyMax.value = maxQty
  jigDropQty.value = maxQty
  jigDropDialogVisible.value = true
}

function isJigProductCd(productCd: string): boolean {
  return String(productCd || '').startsWith('__jig__')
}

/** レイアウト空枠（board_cards に qty=0 で永続化） */
function isEmptySlotProductCd(productCd: string): boolean {
  return String(productCd || '').startsWith('__slot__')
}

function shouldPersistBoardCard(c: ScheduleCard): boolean {
  return c.qty > 0 || isEmptySlotProductCd(c.product_cd)
}

function createEmptySlotScheduleCard(lapNo: number, turnSeq: number, slot?: LapScheduleSlot): ScheduleCard {
  const persistLap = lapNo
  return {
    id: `slot-${persistLap}-${turnSeq}-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`,
    product_cd: `__slot__${persistLap}-${turnSeq}`,
    product_name: '空き',
    plating_machine: '—',
    kake: 1,
    qty: 0,
    slots: 0,
    lap_no: lapNo,
    persist_lap_no: persistLap,
    lap_work_date: slot?.work_date,
    lap_start_time: slot?.start ?? null,
    lap_end_time: slot?.end ?? null,
    turn_seq: turnSeq,
    colorIdx: 0,
    boardMark: 'standard',
  }
}

/** レイアウト上の各周×列に board_cards 用の空枠行を揃える（追加レイアウト直後・保存前） */
function pruneStaleEmptySlots(): boolean {
  const occupied = new Set<string>()
  for (const c of scheduleCards.value) {
    if (c.qty > 0) occupied.add(`${c.lap_no}:${c.turn_seq}`)
  }
  const before = scheduleCards.value.length
  withSuppressedScheduleSideEffects(() => {
    scheduleCards.value = scheduleCards.value.filter((c) => {
      if (!isEmptySlotProductCd(c.product_cd) || c.qty > 0) return true
      return !occupied.has(`${c.lap_no}:${c.turn_seq}`)
    })
  })
  return scheduleCards.value.length !== before
}

function ensureBoardCardSkeletonsForLayout() {
  if (!layoutBoardReady.value || layoutBlocks.value.length === 0) return
  pruneStaleEmptySlots()
  const jigs = Math.max(1, Math.floor(layoutJigsPerLap.value || 1))
  const schedule = currentLayoutLapSchedule()
  if (schedule.length === 0) return
  const { occupiedTurnsByLap, skeletonKeySet } = boardOccupancyIndex.value
  const newCards: ScheduleCard[] = []
  for (const slot of schedule) {
    const lapNo = slot.lap_no
    const occupiedTurns = occupiedTurnsByLap.get(lapNo) ?? new Set<number>()
    for (let turn = 1; turn <= jigs; turn += 1) {
      if (occupiedTurns.has(turn)) continue
      if (skeletonKeySet.has(`${lapNo}:${turn}`)) continue
      newCards.push(createEmptySlotScheduleCard(lapNo, turn, slot))
    }
  }
  if (newCards.length > 0) {
    withSuppressedScheduleSideEffects(() => {
      scheduleCards.value = [...scheduleCards.value, ...newCards]
    })
  }
}

function removeEmptySlotAt(lapNo: number, turnSeq: number) {
  scheduleCards.value = scheduleCards.value.filter(
    (c) =>
      !(
        c.lap_no === lapNo &&
        c.turn_seq === turnSeq &&
        isEmptySlotProductCd(c.product_cd) &&
        c.qty <= 0
      ),
  )
}

function createJigScheduleCard(platingMachine: string, lapNo: number, turnSeq: number): ScheduleCard {
  const mKey = normalizeMachineKey(platingMachine)
  const productCd = `__jig__${mKey}`
  const meta = lapScheduleMetaForCard(lapNo)
  return {
    id: `jig-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    product_cd: productCd,
    product_name: platingMachine,
    plating_machine: platingMachine,
    kake: 1,
    qty: 1,
    slots: 1,
    lap_no: lapNo,
    lap_work_date: meta.lap_work_date,
    lap_start_time: meta.lap_start_time ?? null,
    lap_end_time: meta.lap_end_time ?? null,
    turn_seq: turnSeq,
    colorIdx: schedColorIndexForProductCd(productCd),
    boardMark: 'manual',
  }
}

function getJigEditQtyMax(platingMachine: string, lapNo: number, currentBlockSize: number): number {
  return Math.max(1, getJigQtyMaxForLap(platingMachine, lapNo, currentBlockSize))
}

function getMergedSegCards(ms: LapMergedSegment): ScheduleCard[] {
  const ids = new Set(ms.cardIds)
  return scheduleCards.value.filter((c) => ids.has(c.id) && c.qty > 0)
}

function formatQtyDisplay(n: number): string {
  const v = Number(n)
  if (!Number.isFinite(v)) return '0'
  return Number.isInteger(v) ? String(v) : v.toFixed(2)
}

/** 同一治具ブロック（当該周・連続する plating_machine）の枠数（結合表示の span より tail 列を含む） */
function jigBlockFrameCount(ms: LapMergedSegment, lapNo: number): number {
  const cards = getMergedSegCards(ms)
  if (cards.length === 0) return Math.max(1, Math.floor(Number(ms.span) || 0))
  return findJigBlockCardIds(cards[0].id, lapNo).length
}

/** 治具ブロック内の当該製品が占有する枠数 */
function countProductFramesInJigBlock(lapNo: number, anchorCardId: string, productCd: string): number {
  const blockIds = new Set(findJigBlockCardIds(anchorCardId, lapNo))
  return scheduleCards.value.filter(
    (c) =>
      blockIds.has(c.id) &&
      c.qty > 0 &&
      c.lap_no === lapNo &&
      c.product_cd === productCd &&
      !isJigProductCd(c.product_cd),
  ).length
}

function formatProductNameWithProductionQty(name: string, productionQty: number): string {
  const n = String(name || '').trim()
  if (!n) return ''
  if (!Number.isFinite(productionQty) || productionQty <= 0) return n
  return `${n} (${formatQtyDisplay(productionQty)})`
}

interface JigBlockProductCalcPart {
  productName: string
  qtyLabel: string
  displayText: string
  untilDepleted: boolean
  forceRedText: boolean
}

/** 治具ブロック内の製品表示（出現順・品番ごとに集計） */
function buildJigBlockProductCalcParts(ms: LapMergedSegment, lapNo: number): JigBlockProductCalcPart[] | null {
  const cards = getMergedSegCards(ms)
  const anchor = cards[0]
  if (!anchor) return null
  const blockIds = new Set(findJigBlockCardIds(anchor.id, lapNo))
  if (blockIds.size === 0) return null

  const blockCards = scheduleCards.value
    .filter((c) => blockIds.has(c.id) && c.qty > 0 && c.lap_no === lapNo && !isJigProductCd(c.product_cd))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  if (blockCards.length === 0) return null

  const order: string[] = []
  const nameByCd = new Map<string, string>()
  const qtyByCd = new Map<string, number>()
  const depletedByCd = new Map<string, boolean>()
  const redByCd = new Map<string, boolean>()
  for (const c of blockCards) {
    if (!nameByCd.has(c.product_cd)) {
      order.push(c.product_cd)
      nameByCd.set(c.product_cd, String(c.product_name || c.product_cd || '').trim())
      depletedByCd.set(c.product_cd, true)
      redByCd.set(c.product_cd, true)
    }
    qtyByCd.set(c.product_cd, (qtyByCd.get(c.product_cd) ?? 0) + cardProductProductionQty(c))
    if (!c.untilDepleted) depletedByCd.set(c.product_cd, false)
    if (!c.forceRedText) redByCd.set(c.product_cd, false)
  }
  const parts: JigBlockProductCalcPart[] = order
    .map((cd) => {
      const name = nameByCd.get(cd)
      if (!name) return null
      const untilDepleted = !!depletedByCd.get(cd)
      const forceRedText = !!redByCd.get(cd)
      const qtyLabel = untilDepleted ? '無くなり次第' : formatQtyDisplay(qtyByCd.get(cd) ?? 0)
      const displayText = untilDepleted ? `${name} (${qtyLabel})` : formatProductNameWithProductionQty(name, qtyByCd.get(cd) ?? 0)
      if (!displayText) return null
      return { productName: name, qtyLabel, displayText, untilDepleted, forceRedText }
    })
    .filter((p): p is JigBlockProductCalcPart => p != null)
  return parts.length > 0 ? parts : null
}

/** 治具枠に製品割当後：製品名 (生産数)（単一製品） */
function formatJigBlockProductCalc(ms: LapMergedSegment, lapNo: number): string | null {
  const parts = buildJigBlockProductCalcParts(ms, lapNo)
  if (!parts || parts.length === 0) return null
  return parts.length === 1 ? parts[0].displayText : null
}

/** 合并块内多个产品：按块内出现顺序去重、「製品名 (生産数)」を "/" で連結 */
function formatJigBlockProductsCalc(ms: LapMergedSegment, lapNo: number): string | null {
  const parts = buildJigBlockProductCalcParts(ms, lapNo)
  if (!parts || parts.length <= 1) return null
  return parts.map((p) => p.displayText).join(' / ')
}

/** 治具ブロック表示幅（治具名・画面1行・印刷の製品名／数量行を個別に評価） */
function estimateJigBlockLayoutNeedCh(ms: LapMergedSegment, lapNo: number): number {
  const jig = formatPlatingBoardLabel(ms.plating_machine, jigBlockFrameCount(ms, lapNo))
  const jigNeedCh = estimateTextWidthCh(jig, 0.98, 1.6)
  const parts = buildJigBlockProductCalcParts(ms, lapNo)
  if (!parts || parts.length === 0) return jigNeedCh

  const sep = ' / '
  const prodNamesLine = parts.map((p) => p.productName).join(sep)
  const prodQtyLine = parts.map((p) => p.qtyLabel).join(sep)
  const displayLine =
    parts.length === 1 ? parts[0].displayText : parts.map((p) => p.displayText).join(sep)

  const screenLineCh = estimateTextWidthCh(displayLine, 1, 1.6)
  const printNameCh = estimateTextWidthCh(prodNamesLine, 0.92, 1.8)
  const printQtyCh = estimateTextWidthCh(prodQtyLine, 0.88, 1.5)
  const longestNameCh = Math.max(
    MIN_LAP_COL_CH,
    ...parts.map((p) => estimateTextWidthCh(p.productName, 1, 1.2)),
  )

  return Math.max(jigNeedCh, screenLineCh, printNameCh, printQtyCh, longestNameCh) + 0.4
}

/** 印刷用：治具ブロック 4 層（治具名・治具数・製品名・製品数） */
function buildJigBlockPrintStackHtml(ms: LapMergedSegment, lapNo: number): string {
  const jigName = escapeHtmlForPrint(String(ms.plating_machine || '').trim() || '—')
  const frames = jigBlockFrameCount(ms, lapNo)
  const jigQty = escapeHtmlForPrint(`(${Math.max(0, Math.floor(Number(frames) || 0))})`)
  const parts = buildJigBlockProductCalcParts(ms, lapNo)

  const prodNameInner =
    parts && parts.length > 0
      ? parts
          .map((part, idx) => {
            const sep = idx > 0 ? '<span class="lap-print-prod-sep"> / </span>' : ''
            const extra =
              part.untilDepleted
                ? 'lap-print-prod--depleted'
                : part.forceRedText
                  ? 'lap-print-prod--force-red'
                  : idx >= 1
                    ? 'lap-print-prod--alt'
                    : ''
            const cls =
              idx >= 1 && !part.forceRedText && !part.untilDepleted
                ? 'lap-print-prod lap-print-prod--alt'
                : extra
                  ? `lap-print-prod lap-print-prod--name ${extra}`
                  : 'lap-print-prod lap-print-prod--name'
            return `${sep}<span class="${cls}">${escapeHtmlForPrint(part.productName)}</span>`
          })
          .join('')
      : ''
  const prodQtyInner =
    parts && parts.length > 0
      ? parts
          .map((part, idx) => {
            const sep = idx > 0 ? '<span class="lap-print-prod-sep"> / </span>' : ''
            const extra = part.untilDepleted
              ? 'lap-print-prod--depleted'
              : part.forceRedText
                ? 'lap-print-prod--force-red'
                : idx >= 1
                  ? 'lap-print-prod--alt'
                  : ''
            const cls = `lap-print-prod lap-print-prod--qty${extra ? ` ${extra}` : ''}`
            return `${sep}<span class="${cls}">${escapeHtmlForPrint(part.qtyLabel)}</span>`
          })
          .join('')
      : ''

  return [
    `<div class="lap-print-layer lap-print-layer--jig-name lap-print-layer--right">${jigName}</div>`,
    `<div class="lap-print-layer lap-print-layer--jig-qty lap-print-layer--right">${jigQty}</div>`,
    `<div class="lap-print-layer lap-print-layer--prod-name lap-print-layer--left">${prodNameInner || '&nbsp;'}</div>`,
    `<div class="lap-print-layer lap-print-layer--prod-qty lap-print-layer--left">${prodQtyInner || '&nbsp;'}</div>`,
  ].join('')
}

interface BoardProductPickOption {
  pickKey: string
  label: string
  src: DraftSourceItem
  jigMatch: boolean
  group: 'summary' | 'catalog'
}

/** 結合表示セグメントを当該治具ブロック全体（尾列含む）に拡張 */
function mergedSegForFullJigBlock(ms: LapMergedSegment, lapNo: number): LapMergedSegment {
  const cards = getMergedSegCards(ms)
  if (cards.length === 0) return ms
  const cardIds = findJigBlockCardIds(cards[0].id, lapNo)
  if (cardIds.length === 0) return ms
  return { ...ms, cardIds, span: cardIds.length }
}

function countEmptyJigSlotsInBlock(ms: LapMergedSegment, lapNo: number): number {
  const cards = getMergedSegCards(ms)
  const anchor = cards[0]
  if (!anchor) return 0
  const blockIds = new Set(findJigBlockCardIds(anchor.id, lapNo))
  return scheduleCards.value.filter(
    (c) =>
      blockIds.has(c.id) &&
      c.qty > 0 &&
      c.lap_no === lapNo &&
      isJigProductCd(c.product_cd),
  ).length
}

function catalogRowToDraftSource(row: JigProductCatalogRow): DraftSourceItem {
  const inv = row.pre_plating_inventory
  const gen = row.gen_qty
  const useLeft = inv != null && inv > 0
  return {
    source_key: `pick-C-${row.product_cd}-${Date.now()}`,
    source_type: useLeft ? 'left_inventory' : 'right_gen',
    product_cd: row.product_cd,
    product_name: row.product_name,
    plating_machine: row.plating_machine,
    kake: parseKakeCount(row.plating_efficiency) ?? 0,
    qty: useLeft ? inv! : gen != null && gen > 0 ? gen : 0,
  }
}

function formatCatalogPickLabel(row: JigProductCatalogRow): string {
  const hints: string[] = []
  if (row.pre_plating_inventory != null) hints.push(`在庫 ${row.pre_plating_inventory}`)
  if (row.gen_qty != null) hints.push(`見込 ${row.gen_qty}`)
  const suffix = hints.length > 0 ? ` · ${hints.join(' · ')}` : ''
  return `${row.product_name}（${row.product_cd}）${suffix}`
}

function buildJigProductCatalogFromEquipmentEfficiency(
  rows: EquipmentEfficiency[],
): Map<string, Map<string, JigProductCatalogRow>> {
  const byMachine = new Map<string, Map<string, JigProductCatalogRow>>()
  for (const row of rows) {
    if (row.status === 0) continue
    const machine = String(row.machines_name ?? '').trim()
    const cd = String(row.product_cd ?? '').trim()
    if (!machine || !cd) continue
    const mk = normalizeMachineKey(machine)
    const byProd = byMachine.get(mk) ?? new Map<string, JigProductCatalogRow>()
    const productName = String(row.product_name ?? '').trim() || cd
    const effRaw = row.efficiency_rate
    const eff = effRaw != null ? Number(effRaw) : NaN
    const plating_efficiency =
      Number.isFinite(eff) && eff > 0 ? formatEfficiencyRate(eff) : '—'
    byProd.set(cd, {
      product_cd: cd,
      product_name: productName,
      plating_machine: machine,
      plating_efficiency,
      pre_plating_inventory: null,
      gen_qty: null,
    })
    byMachine.set(mk, byProd)
  }
  return byMachine
}

/** equipment_efficiency 登録品に、左右ペインの在庫・見込を付与 */
function enrichJigCatalogFromPaneRows(
  catalog: Map<string, Map<string, JigProductCatalogRow>>,
  left: LeftPaneRow[],
  right: RightPaneRow[],
): void {
  for (const row of left) {
    const cd = row.product_cd?.trim()
    if (!cd) continue
    const mk = normalizeMachineKey(row.plating_machine)
    if (!mk || mk === '—') continue
    const cur = catalog.get(mk)?.get(cd)
    if (!cur) continue
    cur.pre_plating_inventory = row.pre_plating_inventory
    if (row.plating_efficiency !== '—') cur.plating_efficiency = row.plating_efficiency
  }
  for (const row of right) {
    const cd = row.product_cd?.trim()
    if (!cd) continue
    const mk = normalizeMachineKey(row.plating_machine)
    if (!mk || mk === '—') continue
    const cur = catalog.get(mk)?.get(cd)
    if (!cur) continue
    const q = num(row.gen_qty)
    if (Number.isFinite(q)) cur.gen_qty = q
    if (row.plating_efficiency !== '—') cur.plating_efficiency = row.plating_efficiency
  }
}

function buildBoardProductPickOptionSets(
  jigMachine: string,
  matchOnly: boolean,
): { summary: BoardProductPickOption[]; catalog: BoardProductPickOption[] } {
  const jk = normalizeMachineKey(jigMachine)
  const summaryMap = new Map<string, BoardProductPickOption>()
  const addSummary = (opt: BoardProductPickOption) => {
    const prev = summaryMap.get(opt.pickKey)
    if (!prev || (opt.jigMatch && !prev.jigMatch)) summaryMap.set(opt.pickKey, opt)
  }
  const summaryCd = new Set<string>()

  for (const row of leftRows.value) {
    const jigMatch = !jk || normalizeMachineKey(row.plating_machine) === jk
    if (matchOnly && jk && !jigMatch) continue
    summaryCd.add(row.product_cd)
    addSummary({
      pickKey: `L|${row.product_cd}`,
      label: `${row.product_name}（${row.product_cd}） · 在庫 ${row.pre_plating_inventory}`,
      src: {
        source_key: `pick-L-${row.product_cd}`,
        source_type: 'left_inventory',
        product_cd: row.product_cd,
        product_name: row.product_name,
        plating_machine: row.plating_machine,
        kake: parseKakeCount(row.plating_efficiency) ?? 0,
        qty: row.pre_plating_inventory,
      },
      jigMatch,
      group: 'summary',
    })
  }
  for (const row of rightRows.value) {
    const jigMatch = !jk || normalizeMachineKey(row.plating_machine) === jk
    if (matchOnly && jk && !jigMatch) continue
    summaryCd.add(row.product_cd)
    addSummary({
      pickKey: `R|${row.product_cd}`,
      label: `${row.product_name}（${row.product_cd}） · 見込 ${row.gen_qty}`,
      src: {
        source_key: `pick-R-${row.product_cd}`,
        source_type: 'right_gen',
        product_cd: row.product_cd,
        product_name: row.product_name,
        plating_machine: row.plating_machine,
        kake: parseKakeCount(row.plating_efficiency) ?? 0,
        qty: num(row.gen_qty),
      },
      jigMatch,
      group: 'summary',
    })
  }

  const catalog: BoardProductPickOption[] = []
  if (jk) {
    const byProd = jigProductCatalogByMachine.value.get(jk)
    if (byProd) {
      for (const row of byProd.values()) {
        if (summaryCd.has(row.product_cd)) continue
        catalog.push({
          pickKey: `C|${row.product_cd}`,
          label: formatCatalogPickLabel(row),
          src: catalogRowToDraftSource(row),
          jigMatch: true,
          group: 'catalog',
        })
      }
      catalog.sort((a, b) => a.label.localeCompare(b.label, 'ja'))
    }
  }

  const summary = [...summaryMap.values()].sort((a, b) => {
    if (a.jigMatch !== b.jigMatch) return a.jigMatch ? -1 : 1
    return a.label.localeCompare(b.label, 'ja')
  })
  return { summary, catalog }
}

async function ensureJigProductCatalogForMachine(jigMachine: string): Promise<void> {
  const jk = normalizeMachineKey(jigMachine)
  if (!jk) return
  if ((jigProductCatalogByMachine.value.get(jk)?.size ?? 0) > 0) return
  try {
    const bundle = await fetchEquipmentEfficiencyBundle()
    const merged = new Map(jigProductCatalogByMachine.value)
    for (const [mk, byProd] of bundle.catalogByMachine) {
      const dest = new Map(merged.get(mk) ?? [])
      for (const [cd, row] of byProd) dest.set(cd, { ...row })
      merged.set(mk, dest)
    }
    enrichJigCatalogFromPaneRows(merged, leftRows.value, rightRows.value)
    jigProductCatalogByMachine.value = merged
  } catch (e) {
    console.warn('ensureJigProductCatalogForMachine:', e)
  }
}

async function openBoardProductPickDialog(ms: LapMergedSegment, lapNo: number) {
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  const block = resolveBoardJigBlock(ms, lapNo)
  if (!block) {
    ElMessage.warning('治具ブロックを特定できません')
    return
  }
  await openBoardJigQtyEditFromBlock(block)
}

function onBoardJigBlockContextMenu(ms: LapMergedSegment, lapNo: number) {
  const block = resolveBoardJigBlock(ms, lapNo)
  if (!block) return
  void openBoardJigQtyEditFromBlock(block)
}

/** 未割当枠へ順に製品を割当（空き枠が無い場合は false） */
function applyProductToEmptyJigSlots(
  ms: LapMergedSegment,
  lapNo: number,
  src: DraftSourceItem,
  slots: number,
): number {
  const cards = getMergedSegCards(ms)
  const anchor = cards[0]
  if (!anchor) return 0
  const blockIds = new Set(findJigBlockCardIds(anchor.id, lapNo))
  const jigMachine = String(ms.plating_machine || '').trim()
  const blockCards = scheduleCards.value
    .filter((c) => blockIds.has(c.id) && c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const updates = new Map<string, ScheduleCard>()
  let assigned = 0
  const n = Math.max(0, Math.floor(Number(slots) || 0))
  for (const c of blockCards) {
    if (assigned >= n) break
    if (!isJigProductCd(c.product_cd)) continue
    updates.set(c.id, cardUpdateFromDraftSource(c, src, jigMachine))
    assigned += 1
  }
  if (assigned <= 0) return 0
  scheduleCards.value = scheduleCards.value.map((c) => updates.get(c.id) ?? c)
  refreshMarksAgainstStandardPositions()
  return assigned
}

function assignProductToJigBlockWithSlots(
  ms: LapMergedSegment,
  lapNo: number,
  src: DraftSourceItem,
  slots: number,
  replaceAll = false,
) {
  const fullMs = mergedSegForFullJigBlock(ms, lapNo)
  const jigMachine = String(fullMs.plating_machine || '').trim()
  const srcJig = String(src.plating_machine || '').trim()
  if (srcJig && jigMachine && normalizeMachineKey(srcJig) !== normalizeMachineKey(jigMachine)) {
    ElMessage.warning(`製品のメッキ治具（${srcJig}）と枠（${jigMachine}）が一致しません`)
    return
  }
  const blockFrames = jigBlockFrameCount(fullMs, lapNo)
  if (replaceAll) {
    applyProductsToJigBlockOrdered(fullMs, lapNo, [{ src, slots: blockFrames }])
    const kake = src.kake > 0 ? src.kake : 1
    ElMessage.success(
      `${src.product_name} で ${jigMachine} の全 ${blockFrames} 枠を置換（${blockFrames}×${formatQtyDisplay(kake)}=${formatQtyDisplay(blockFrames * kake)}）`,
    )
    void flushBoardPersist()
    return
  }
  const want = Math.max(1, Math.floor(Number(slots) || 0))
  const empty = countEmptyJigSlotsInBlock(fullMs, lapNo)
  if (empty > 0) {
    const assigned = applyProductToEmptyJigSlots(fullMs, lapNo, src, Math.min(want, empty))
    if (assigned <= 0) {
      ElMessage.warning('未割当の枠がありません')
      return
    }
    const kake = src.kake > 0 ? src.kake : 1
    ElMessage.success(
      `${src.product_name} を ${jigMachine} の未割当 ${assigned} 枠へ割当（${assigned}×${formatQtyDisplay(kake)}=${formatQtyDisplay(assigned * kake)}）`,
    )
    void flushBoardPersist()
    return
  }
  const existing = getPrimaryExistingProductInJigBlock(fullMs)
  if (want >= blockFrames) {
    applyProductsToJigBlockOrdered(fullMs, lapNo, [{ src, slots: blockFrames }])
    const kake = src.kake > 0 ? src.kake : 1
    ElMessage.success(
      `${src.product_name} を ${jigMachine} の全 ${blockFrames} 枠に割当（${blockFrames}×${formatQtyDisplay(kake)}=${formatQtyDisplay(blockFrames * kake)}）`,
    )
    void flushBoardPersist()
    return
  }
  if (existing && existing.product_cd !== src.product_cd && blockFrames >= 2) {
    openProductToJigDialog(fullMs, lapNo, src, existing)
    return
  }
  applyProductsToJigBlockOrdered(fullMs, lapNo, [{ src, slots: Math.min(want, blockFrames) }])
  const kake = src.kake > 0 ? src.kake : 1
  const n = Math.min(want, blockFrames)
  ElMessage.success(
    `${src.product_name} を ${jigMachine}（${n}本）に割当：${n}×${formatQtyDisplay(kake)}=${formatQtyDisplay(n * kake)}`,
  )
  void flushBoardPersist()
}

function boardMergedSegTitle(ms: LapMergedSegment, lapNo: number): string {
  const frames = jigBlockFrameCount(ms, lapNo)
  const startCol = Math.max(1, Math.floor(Number(ms.startCol) || 1))
  const endCol = Math.min(
    lapBoardColCount.value,
    Math.max(startCol, startCol + Math.max(1, Math.floor(Number(ms.span) || 1)) - 1),
  )
  const colLabel = startCol === endCol ? `第${startCol}列` : `第${startCol}列〜第${endCol}列`
  const base = `${ms.plating_machine}・${frames}本`
  const calc = formatJigBlockProductsCalc(ms, lapNo) ?? formatJigBlockProductCalc(ms, lapNo)
  const hints = [
    `位置: ${colLabel}`,
  ]
  if (!isJigProductCd(ms.product_cd)) {
    return calc ? `${base}・${calc}・${hints.join('・')}` : `${base}・${hints.join('・')}`
  }
  return calc ? `${base}・${calc}・${hints.join('・')}` : `${base}・${hints.join('・')}`
}

function resolveInventoryDragSource(): DraftSourceItem | null {
  return draggingSource.value
}

function getPrimaryExistingProductInJigBlock(ms: LapMergedSegment): DraftSourceItem | null {
  const cards = getMergedSegCards(ms)
    .filter((c) => !isJigProductCd(c.product_cd))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const first = cards[0]
  if (!first) return null
  return {
    source_key: `block-${first.id}`,
    source_type: 'left_inventory',
    product_cd: first.product_cd,
    product_name: first.product_name,
    plating_machine: first.plating_machine,
    kake: first.kake > 0 ? first.kake : 1,
    qty: first.qty,
  }
}

function resetProductToJigDialog() {
  productToJigPending.value = null
  productAssignExistingSlots.value = 1
  productAssignNewSlots.value = 1
  productAssignOrder.value = 'existing-first'
}

const productAssignSlotsSum = computed(() => {
  if (!productToJigPending.value) return 0
  return Math.max(0, Math.floor(Number(productAssignExistingSlots.value) || 0))
    + Math.max(0, Math.floor(Number(productAssignNewSlots.value) || 0))
})

const productAssignExistingSlotsMax = computed(() => {
  const span = productToJigPending.value?.span ?? 1
  const n = Math.max(0, Math.floor(Number(productAssignNewSlots.value) || 0))
  return Math.max(0, span - n)
})

const productAssignNewSlotsMax = computed(() => {
  const span = productToJigPending.value?.span ?? 1
  const e = Math.max(0, Math.floor(Number(productAssignExistingSlots.value) || 0))
  return Math.max(0, span - e)
})

const showProductAssignOrder = computed(() => {
  if (!productToJigPending.value) return false
  const e = Math.max(0, Math.floor(Number(productAssignExistingSlots.value) || 0))
  const n = Math.max(0, Math.floor(Number(productAssignNewSlots.value) || 0))
  return e > 0 && n > 0
})

const canConfirmProductToJig = computed(() => {
  const p = productToJigPending.value
  if (!p) return false
  const e = Math.max(0, Math.floor(Number(productAssignExistingSlots.value) || 0))
  const n = Math.max(0, Math.floor(Number(productAssignNewSlots.value) || 0))
  return productAssignSlotsSum.value === p.span && (e > 0 || n > 0)
})

function openProductToJigDialog(ms: LapMergedSegment, lapNo: number, src: DraftSourceItem, existing: DraftSourceItem) {
  const span = Math.max(1, Math.floor(Number(ms.span) || 1))
  productToJigPending.value = { ms, lapNo, src, existing, span }
  const cards = getMergedSegCards(ms)
  const anchorId = cards[0]?.id ?? ''
  const existingCount = anchorId
    ? countProductFramesInJigBlock(lapNo, anchorId, existing.product_cd)
    : 1
  productAssignExistingSlots.value = Math.min(existingCount, span)
  productAssignNewSlots.value = Math.max(0, span - productAssignExistingSlots.value)
  productAssignOrder.value = 'existing-first'
  productToJigDialogVisible.value = true
}

function scheduleCardToDraftSource(c: ScheduleCard): DraftSourceItem {
  return {
    source_key: `block-${c.id}`,
    source_type: 'left_inventory',
    product_cd: c.product_cd,
    product_name: c.product_name,
    plating_machine: c.plating_machine,
    kake: c.kake > 0 ? c.kake : 1,
    qty: c.qty,
  }
}

/** 増枠時に新規枠へ引き継ぐ製品（単一製品はそれを、複数製品は末尾の割当と同じ） */
function pickProductSourceForJigBlockExpand(block: ScheduleCard[]): DraftSourceItem | null {
  const productCards = block.filter((c) => !isJigProductCd(c.product_cd))
  if (productCards.length === 0) return null
  const unique = new Set(productCards.map((c) => c.product_cd))
  if (unique.size === 1) return scheduleCardToDraftSource(productCards[0])
  return scheduleCardToDraftSource(productCards[productCards.length - 1])
}

function cardUpdateFromDraftSource(
  c: ScheduleCard,
  src: DraftSourceItem,
  jigMachine: string,
): ScheduleCard {
  const kake = src.kake > 0 ? src.kake : 1
  return {
    ...c,
    product_cd: src.product_cd,
    product_name: src.product_name,
    plating_machine: jigMachine || c.plating_machine,
    kake,
    qty: 1,
    slots: 1,
    boardMark: 'manual' as BoardMark,
    colorIdx: schedColorIndexForProductCd(src.product_cd),
  }
}

function applyProductsToJigBlockOrdered(
  ms: LapMergedSegment,
  lapNo: number,
  segments: Array<{ src: DraftSourceItem; slots: number }>,
) {
  const jigMachine = String(ms.plating_machine || '').trim()
  const blockCards = scheduleCards.value
    .filter((c) => ms.cardIds.includes(c.id) && c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const ids = new Set(ms.cardIds)
  let cardIdx = 0
  const updates = new Map<string, ScheduleCard>()
  for (const seg of segments) {
    const n = Math.max(0, Math.floor(Number(seg.slots) || 0))
    for (let i = 0; i < n && cardIdx < blockCards.length; i += 1) {
      const card = blockCards[cardIdx]
      cardIdx += 1
      updates.set(card.id, cardUpdateFromDraftSource(card, seg.src, jigMachine))
    }
  }
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (!ids.has(c.id) || c.qty <= 0 || c.lap_no !== lapNo) return c
    return updates.get(c.id) ?? c
  })
  refreshMarksAgainstStandardPositions()
}

function confirmProductToJigAssign() {
  const p = productToJigPending.value
  if (!p || !canConfirmProductToJig.value) return
  const jigMachine = String(p.ms.plating_machine || '').trim()
  const srcJig = String(p.src.plating_machine || '').trim()
  if (srcJig && jigMachine && normalizeMachineKey(srcJig) !== normalizeMachineKey(jigMachine)) {
    ElMessage.warning(`製品のメッキ治具（${srcJig}）と枠（${jigMachine}）が一致しません`)
    return
  }
  const eSlots = Math.max(0, Math.floor(Number(productAssignExistingSlots.value) || 0))
  const nSlots = Math.max(0, Math.floor(Number(productAssignNewSlots.value) || 0))
  const segments: Array<{ src: DraftSourceItem; slots: number }> = []
  if (productAssignOrder.value === 'existing-first') {
    if (eSlots > 0) segments.push({ src: p.existing, slots: eSlots })
    if (nSlots > 0) segments.push({ src: p.src, slots: nSlots })
  } else {
    if (nSlots > 0) segments.push({ src: p.src, slots: nSlots })
    if (eSlots > 0) segments.push({ src: p.existing, slots: eSlots })
  }
  if (segments.length === 0) return
  applyProductsToJigBlockOrdered(p.ms, p.lapNo, segments)
  let msg: string
  if (eSlots === 0) {
    msg = `${p.src.product_name} で全 ${nSlots} 枠を置換`
  } else if (nSlots === 0) {
    msg = `${p.existing.product_name} を全 ${eSlots} 枠に維持`
  } else {
    const orderLabel =
      productAssignOrder.value === 'existing-first'
        ? `${p.existing.product_name} → ${p.src.product_name}`
        : `${p.src.product_name} → ${p.existing.product_name}`
    msg = `割当完了（${orderLabel}、${p.existing.product_name} ${eSlots}本・${p.src.product_name} ${nSlots}本）`
  }
  ElMessage.success(msg)
  productToJigDialogVisible.value = false
  void flushBoardPersist()
}

function assignProductToJigBlock(ms: LapMergedSegment, lapNo: number, src: DraftSourceItem) {
  if (!isJigProductCd(ms.product_cd)) return
  const jigMachine = String(ms.plating_machine || '').trim()
  const srcJig = String(src.plating_machine || '').trim()
  if (srcJig && jigMachine && normalizeMachineKey(srcJig) !== normalizeMachineKey(jigMachine)) {
    ElMessage.warning(`製品のメッキ治具（${srcJig}）と枠（${jigMachine}）が一致しません`)
    return
  }
  const slots = Math.max(0, Math.floor(Number(ms.span) || 0))
  applyProductsToJigBlockOrdered(ms, lapNo, [{ src, slots }])
  const kake = src.kake > 0 ? src.kake : 1
  const total = slots * kake
  ElMessage.success(
    `${src.product_name} を ${jigMachine}（${slots}本）に割当：${slots}×${formatQtyDisplay(kake)}=${formatQtyDisplay(total)}`,
  )
  void flushBoardPersist()
}

function onProductToJigBlockDragOver(e: DragEvent, ms?: LapMergedSegment, lapNo?: number) {
  // 治具カードのドラッグ中は、製品割当ではなくボード投入ドロップとして扱う
  if (draggingJigToBoard.value || e.dataTransfer?.types?.includes?.('application/x-plating-jig')) {
    onJigToBoardDragOver(e, lapNo)
    return
  }
  if (!draggingInventoryRow.value && !draggingSource.value) return
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
  if (ms) productDropHoverBlockKey.value = ms.key
}

function onProductToJigBlockDragLeave(e: DragEvent) {
  const rel = e.relatedTarget as Node | null
  const el = e.currentTarget as HTMLElement | null
  if (el && rel && el.contains(rel)) return
  productDropHoverBlockKey.value = null
}

function onProductToJigBlockDrop(e: DragEvent, ms: LapMergedSegment, lapNo: number) {
  // 治具カードのドロップは投入ダイアログへフォールバックする
  if (draggingJigToBoard.value || e.dataTransfer?.types?.includes?.('application/x-plating-jig')) {
    onJigToBoardDrop(e, lapNo)
    return
  }
  e.preventDefault()
  e.stopPropagation()
  productDropHoverBlockKey.value = null
  draggingInventoryRow.value = false
  const src = resolveInventoryDragSource()
  draggingSource.value = null
  if (!src) return
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  const existing = getPrimaryExistingProductInJigBlock(ms)
  if (existing && existing.product_cd !== src.product_cd) {
    const span = Math.max(1, Math.floor(Number(ms.span) || 1))
    if (span < 2) {
      applyProductsToJigBlockOrdered(ms, lapNo, [{ src, slots: 1 }])
      ElMessage.success(`${existing.product_name} を ${src.product_name} に置き換えました（枠1本）`)
      void flushBoardPersist()
      return
    }
    openProductToJigDialog(ms, lapNo, src, existing)
    return
  }
  assignProductToJigBlock(ms, lapNo, src)
}

function boardTailCardTitle(tc: ScheduleCard): string {
  const colNo = lapBoardColCount.value
  const colLabel = colNo > 0 ? `第${colNo}列` : ''
  const base = `${tc.plating_machine}・治具1本`
  return colLabel
    ? `${base}・位置: ${colLabel}・ダブルクリックで本数変更・削除`
    : `${base}・ダブルクリックで本数変更・削除`
}

/** 当該周で連続する同一メッキ治具（plating_machine）ブロックのカード ID（製品割当後もブロック全体） */
function findJigBlockCardIds(cardId: string, lapNo: number): string[] {
  const sorted = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const idx = sorted.findIndex((c) => c.id === cardId)
  if (idx < 0) return []
  const mk = normalizeMachineKey(sorted[idx].plating_machine)
  if (!mk) return [sorted[idx].id]
  let start = idx
  let end = idx
  while (start > 0 && normalizeMachineKey(sorted[start - 1].plating_machine) === mk) start -= 1
  while (end < sorted.length - 1 && normalizeMachineKey(sorted[end + 1].plating_machine) === mk) end += 1
  return sorted.slice(start, end + 1).map((c) => c.id)
}

/** 治具本数変更：先頭枠を維持し末尾のみ削除／追加。削除枠の製品は連動して減る */
function resizeJigBlockOnLap(lapNo: number, cardIds: string[], newQty: number): boolean {
  const block = scheduleCards.value
    .filter((c) => cardIds.includes(c.id))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  if (block.length === 0) return false
  const platingMachine = block[0].plating_machine
  const insertTurn = Math.min(...block.map((c) => c.turn_seq))
  const blockEnd = Math.max(...block.map((c) => c.turn_seq))
  const qty = Math.max(1, Math.floor(Number(newQty) || 0))
  const keptIds = new Set(block.slice(0, qty).map((c) => c.id))
  for (const id of cardIds) {
    if (!keptIds.has(id)) standardPositions.value.delete(id)
  }

  const without = scheduleCards.value.filter((c) => !cardIds.includes(c.id))
  const lapRest = without
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const before = lapRest.filter((c) => c.turn_seq < insertTurn)
  const after = lapRest.filter((c) => c.turn_seq > blockEnd)

  const expandSrc = qty > block.length ? pickProductSourceForJigBlockExpand(block) : null
  const newBlock: ScheduleCard[] = [...block.slice(0, qty)]
  for (let i = newBlock.length; i < qty; i += 1) {
    let card = createJigScheduleCard(platingMachine, lapNo, insertTurn + i)
    if (expandSrc) {
      card = cardUpdateFromDraftSource(card, expandSrc, platingMachine)
    }
    newBlock.push(card)
  }
  syncJigBlockCardQtyFields(newBlock)
  const merged = [...before, ...newBlock, ...after]
  merged.forEach((c, i) => {
    c.turn_seq = i + 1
  })

  const others = without.filter((c) => c.lap_no !== lapNo || c.qty <= 0)
  scheduleCards.value = [...others, ...merged]
  refreshMarksAgainstStandardPositions()
  return true
}

/** 製品枠は 1 枠 1 qty。集約 qty が残っている場合は枠数に合わせて正規化 */
function syncJigBlockCardQtyFields(blockCards: ScheduleCard[]) {
  let i = 0
  while (i < blockCards.length) {
    const c = blockCards[i]
    if (isJigProductCd(c.product_cd)) {
      i += 1
      continue
    }
    const productCd = c.product_cd
    let j = i
    while (j < blockCards.length && blockCards[j].product_cd === productCd && !isJigProductCd(blockCards[j].product_cd)) {
      j += 1
    }
    const runLen = j - i
    for (let k = i; k < j; k += 1) {
      blockCards[k].qty = 1
      blockCards[k].slots = 1
    }
    i = j
  }
}

function resetBoardJigEditDialog() {
  boardJigEditPending.value = null
  boardJigEditQty.value = 1
  boardJigEditQtyMax.value = 1
  boardJigEditInitialQty.value = 1
  boardJigEditProductFrames.value = []
  boardJigEditProductFramesInitial.value = []
  boardJigEditProductOrder.value = 'normal'
  resetBoardJigEditAddFields()
}

function boardJigEditFrameToDraftSource(p: BoardJigEditProductFrame): DraftSourceItem {
  const jig = boardJigEditPending.value?.plating_machine ?? ''
  return {
    source_key: `edit-${p.product_cd}`,
    source_type: 'left_inventory',
    product_cd: p.product_cd,
    product_name: p.product_name,
    plating_machine: jig,
    kake: p.kake > 0 ? p.kake : 1,
    qty: 1,
  }
}

/** 追加製品の選択を割当済み製品リストへ反映（確定前のローカル状態） */
function mergeBoardJigEditAddIntoFrames(): boolean {
  const pending = boardJigEditPending.value
  const opt = boardJigEditAddOpt.value
  if (!pending || !opt) return false
  const src = opt.src
  const total = Math.max(1, Math.floor(Number(boardJigEditQty.value) || 0))

  if (boardJigEditAddReplaceAll.value) {
    boardJigEditProductFrames.value = [
      {
        product_cd: src.product_cd,
        product_name: src.product_name,
        frames: total,
        kake: src.kake > 0 ? src.kake : 1,
        untilDepleted: false,
        forceRedText: false,
      },
    ]
    return true
  }

  if (showBoardJigEditInlineAssign.value) {
    const primary = boardJigEditPrimaryFrame.value
    if (!primary) return false
    const eSlots = Math.max(0, Math.floor(Number(boardJigEditInlineExistingSlots.value) || 0))
    const nSlots = Math.max(0, Math.floor(Number(boardJigEditInlineNewSlots.value) || 0))
    const existingSrc = boardJigEditFrameToDraftSource(primary)
    const segments: BoardJigEditProductFrame[] = []
    const pushFrame = (draft: DraftSourceItem, slots: number, flags?: Partial<BoardJigEditProductFrame>) => {
      if (slots <= 0) return
      segments.push({
        product_cd: draft.product_cd,
        product_name: draft.product_name,
        frames: slots,
        kake: draft.kake > 0 ? draft.kake : 1,
        untilDepleted: flags?.untilDepleted ?? false,
        forceRedText: flags?.forceRedText ?? false,
      })
    }
    if (boardJigEditInlineOrder.value === 'existing-first') {
      pushFrame(existingSrc, eSlots, { untilDepleted: primary.untilDepleted, forceRedText: primary.forceRedText })
      pushFrame(src, nSlots)
    } else {
      pushFrame(src, nSlots)
      pushFrame(existingSrc, eSlots, { untilDepleted: primary.untilDepleted, forceRedText: primary.forceRedText })
    }
    boardJigEditProductFrames.value = segments
    boardJigEditProductOrder.value =
      boardJigEditInlineOrder.value === 'existing-first' ? 'normal' : 'reversed'
    return true
  }

  const want = Math.max(1, Math.floor(Number(boardJigEditAddSlots.value) || 0))
  const empty = Math.max(0, total - boardJigEditProductFramesSum.value)
  const addSlots = Math.min(want, empty > 0 ? empty : want)
  if (addSlots <= 0) return false

  const list = boardJigEditProductFrames.value.map((p) => ({ ...p }))
  const hit = list.find((p) => p.product_cd === src.product_cd)
  if (hit) {
    hit.frames = Math.floor(Number(hit.frames) || 0) + addSlots
  } else {
    list.push({
      product_cd: src.product_cd,
      product_name: src.product_name,
      frames: addSlots,
      kake: src.kake > 0 ? src.kake : 1,
      untilDepleted: false,
      forceRedText: false,
    })
  }
  boardJigEditProductFrames.value = list
  return true
}

function resetCardToEmptyJig(c: ScheduleCard, platingMachine: string): ScheduleCard {
  const mKey = normalizeMachineKey(platingMachine)
  const productCd = `__jig__${mKey}`
  return {
    ...c,
    product_cd: productCd,
    product_name: platingMachine,
    plating_machine: platingMachine,
    kake: 1,
    qty: 1,
    slots: 1,
    boardMark: 'manual',
    colorIdx: schedColorIndexForProductCd(productCd),
    untilDepleted: undefined,
    forceRedText: undefined,
  }
}

/** 治具ブロック内の製品割当を左から順に再配置（未割当枠は空き治具） */
function reassignJigBlockProducts(
  lapNo: number,
  cardIds: string[],
  segments: Array<{ src: DraftSourceItem; slots: number }>,
  platingMachine: string,
) {
  const blockCards = scheduleCards.value
    .filter((c) => cardIds.includes(c.id))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const ids = new Set(cardIds)
  let cardIdx = 0
  const updates = new Map<string, ScheduleCard>()
  for (const seg of segments) {
    const n = Math.max(0, Math.floor(Number(seg.slots) || 0))
    for (let i = 0; i < n && cardIdx < blockCards.length; i += 1) {
      const card = blockCards[cardIdx]
      cardIdx += 1
      updates.set(card.id, cardUpdateFromDraftSource(card, seg.src, platingMachine))
    }
  }
  while (cardIdx < blockCards.length) {
    const card = blockCards[cardIdx]
    cardIdx += 1
    updates.set(card.id, resetCardToEmptyJig(card, platingMachine))
  }
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (!ids.has(c.id) || c.qty <= 0 || c.lap_no !== lapNo) return c
    return updates.get(c.id) ?? c
  })
  refreshMarksAgainstStandardPositions()
}

function reassignJigBlockProductsFromEdit(
  pending: NonNullable<typeof boardJigEditPending.value>,
  totalQty: number,
) {
  const anchorId = pending.cardIds[0]
  if (!anchorId) return
  const cardIds = findJigBlockCardIds(anchorId, pending.lap_no).slice(0, totalQty)
  if (cardIds.length === 0) return
  const platingMachine = pending.plating_machine
  const blockCards = scheduleCards.value
    .filter((c) => cardIds.includes(c.id))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  let ordered = boardJigEditProductFrames.value
    .filter((p) => Math.floor(Number(p.frames) || 0) > 0)
    .map((p) => ({ ...p, frames: Math.floor(Number(p.frames) || 0) }))
  if (boardJigEditProductOrder.value === 'reversed') {
    ordered = [...ordered].reverse()
  }
  const segments: Array<{ src: DraftSourceItem; slots: number }> = []
  for (const p of ordered) {
    const srcCard = blockCards.find((c) => c.product_cd === p.product_cd && !isJigProductCd(c.product_cd))
    const src = srcCard ? scheduleCardToDraftSource(srcCard) : boardJigEditFrameToDraftSource(p)
    segments.push({ src, slots: p.frames })
  }
  reassignJigBlockProducts(pending.lap_no, cardIds, segments, platingMachine)
  const idSet = new Set(cardIds)
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (!idSet.has(c.id) || c.lap_no !== pending.lap_no || isJigProductCd(c.product_cd)) return c
    const pe = boardJigEditProductFrames.value.find((x) => x.product_cd === c.product_cd)
    if (!pe) return c
    return { ...c, untilDepleted: pe.untilDepleted, forceRedText: pe.forceRedText }
  })
  boardJigEditPending.value = { ...pending, cardIds: [...cardIds] }
}

function applyBoardJigBlockDisplayFlags(pending: NonNullable<typeof boardJigEditPending.value>) {
  const anchorId = pending.cardIds[0]
  if (!anchorId) return
  const cardIds = findJigBlockCardIds(anchorId, pending.lap_no)
  const idSet = new Set(cardIds)
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (!idSet.has(c.id) || c.lap_no !== pending.lap_no || isJigProductCd(c.product_cd)) return c
    const pe = boardJigEditProductFrames.value.find((x) => x.product_cd === c.product_cd)
    return {
      ...c,
      untilDepleted: pe ? pe.untilDepleted : c.untilDepleted,
      forceRedText: pe ? pe.forceRedText : c.forceRedText,
    }
  })
}

interface BoardJigBlockRef {
  lap_no: number
  plating_machine: string
  product_cd: string
  product_name: string
  cardIds: string[]
}

function resolveBoardJigBlock(ms: LapMergedSegment, lapNo: number): BoardJigBlockRef | null {
  const cards = getMergedSegCards(ms).filter((c) => c.qty > 0 && c.lap_no === lapNo)
  if (cards.length === 0) return null
  const cardIds = findJigBlockCardIds(cards[0].id, lapNo)
  const blockCards = scheduleCards.value
    .filter((c) => cardIds.includes(c.id))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const productCard = blockCards.find((c) => !isJigProductCd(c.product_cd))
  return {
    lap_no: lapNo,
    plating_machine: String(ms.plating_machine || blockCards[0]?.plating_machine || '').trim(),
    product_cd: productCard?.product_cd ?? blockCards[0].product_cd,
    product_name: productCard?.product_name ?? blockCards[0].product_name ?? ms.product_name,
    cardIds,
  }
}

function renumberLapTurnSeqAfterChange(lapNo: number) {
  const lapCards = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  lapCards.forEach((c, i) => {
    c.turn_seq = i + 1
  })
}

function removeJigBlockCards(lapNo: number, cardIds: string[]) {
  const idSet = new Set(cardIds)
  for (const id of cardIds) {
    standardPositions.value.delete(id)
  }
  scheduleCards.value = scheduleCards.value.filter((c) => !(idSet.has(c.id) && c.lap_no === lapNo))
  renumberLapTurnSeqAfterChange(lapNo)
  refreshMarksAgainstStandardPositions()
}

async function confirmClearBoardLapRow(lapNo: number) {
  const lapCards = lapCardsWithQty(lapNo)
  if (lapCards.length === 0) {
    ElMessage.info(`第${lapDisplayNo(lapNo)}周目には削除対象がありません`)
    return
  }
  try {
    await ElMessageBox.confirm(
      `第${lapDisplayNo(lapNo)}周目の ${lapCards.length} 本をボードから削除しますか？`,
      '行クリア',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  const idSet = new Set(lapCards.map((c) => c.id))
  for (const id of idSet) {
    standardPositions.value.delete(id)
  }
  scheduleCards.value = scheduleCards.value.filter((c) => !(c.lap_no === lapNo && idSet.has(c.id)))
  refreshMarksAgainstStandardPositions()
  ElMessage.success(`第${lapDisplayNo(lapNo)}周目をクリアしました`)
  void flushBoardPersist()
}

function resolveNextVisibleLapNo(lapNo: number): number | null {
  const laps = [...new Set(lapGridRows.value.map((r) => r.lap_no))]
    .filter((n) => Number.isFinite(n) && n > 0)
    .sort((a, b) => a - b)
  const idx = laps.findIndex((n) => n === lapNo)
  if (idx < 0 || idx >= laps.length - 1) return null
  return laps[idx + 1] ?? null
}

async function copyBoardLapRowToNext(lapNo: number) {
  const src = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  if (src.length === 0) {
    ElMessage.info(`第${lapDisplayNo(lapNo)}周目にはコピー対象がありません`)
    return
  }
  const nextLap = resolveNextVisibleLapNo(lapNo)
  if (!nextLap) {
    ElMessage.warning('次の行がありません')
    return
  }
  try {
    await ElMessageBox.confirm(
      `第${lapDisplayNo(lapNo)}周目の ${src.length} 本を第${lapDisplayNo(nextLap)}周目へコピーしますか？`,
      '行コピー',
      { type: 'warning', confirmButtonText: 'コピー', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }

  const ts = Date.now()
  const targetLapMeta = lapScheduleMetaForCard(nextLap)
  const dstIds = new Set(
    lapCardsWithQty(nextLap).map((c) => c.id),
  )
  for (const id of dstIds) {
    standardPositions.value.delete(id)
  }
  const copied = src.map((c, i) => ({
    ...c,
    id: `lap-row-copy-${ts}-${i}-${Math.random().toString(36).slice(2, 6)}`,
    lap_no: nextLap,
    persist_lap_no: nextLap,
    turn_seq: i + 1,
    lap_work_date: targetLapMeta.lap_work_date ?? c.lap_work_date,
    lap_start_time: targetLapMeta.lap_start_time ?? c.lap_start_time ?? null,
    lap_end_time: targetLapMeta.lap_end_time ?? c.lap_end_time ?? null,
  }))
  scheduleCards.value = [...scheduleCards.value.filter((c) => c.lap_no !== nextLap), ...copied]
  refreshMarksAgainstStandardPositions()
  ElMessage.success(`第${lapDisplayNo(nextLap)}周目へコピーしました`)
  void flushBoardPersist()
}

async function confirmDeleteBoardJigBlock() {
  const pending = boardJigEditPending.value
  if (!pending || pending.cardIds.length === 0) return
  try {
    await ElMessageBox.confirm(
      `第${lapDisplayNo(pending.lap_no)}周目の ${pending.plating_machine}（${pending.cardIds.length} 本）をボードから削除しますか？`,
      '治具削除',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  removeJigBlockCards(pending.lap_no, pending.cardIds)
  boardJigEditDialogVisible.value = false
  ElMessage.success(`${pending.plating_machine} を ${pending.cardIds.length} 本削除しました`)
  void flushBoardPersist()
}

async function openBoardJigQtyEditFromBlock(block: BoardJigBlockRef) {
  const maxQty = getJigEditQtyMax(block.plating_machine, block.lap_no, block.cardIds.length)
  const pending = {
    lap_no: block.lap_no,
    plating_machine: block.plating_machine,
    product_cd: block.product_cd,
    product_name: block.product_name,
    cardIds: [...block.cardIds],
  }
  boardJigEditPending.value = pending
  boardJigEditQtyMax.value = maxQty
  boardJigEditQty.value = block.cardIds.length
  boardJigEditInitialQty.value = block.cardIds.length
  initBoardJigEditProductFrames(pending)
  resetBoardJigEditAddFields()
  const empty = Math.max(0, block.cardIds.length - boardJigEditProductFramesSum.value)
  boardJigEditAddSlots.value = Math.max(1, empty > 0 ? empty : block.cardIds.length)
  await ensureJigProductCatalogForMachine(block.plating_machine)
  boardJigEditDialogVisible.value = true
}

function onBoardMergedSegDblClick(ms: LapMergedSegment, lapNo: number) {
  const block = resolveBoardJigBlock(ms, lapNo)
  if (!block) return
  void openBoardJigQtyEditFromBlock(block)
}

function onBoardScheduleCardDblClick(card: ScheduleCard) {
  const cardIds = findJigBlockCardIds(card.id, card.lap_no)
  if (cardIds.length === 0) return
  void openBoardJigQtyEditFromBlock({
    lap_no: card.lap_no,
    plating_machine: card.plating_machine,
    product_cd: card.product_cd,
    product_name: card.product_name,
    cardIds,
  })
}

function confirmBoardJigQtyEdit() {
  const pending = boardJigEditPending.value
  if (!pending) return
  if (!canConfirmBoardJigEdit.value) {
    ElMessage.warning('製品別使用本数の合計が治具総本数を超えています')
    return
  }
  if (!canConfirmBoardJigEditWithAdd.value) {
    ElMessage.warning('既存と追加の割当本数の合計が治具総本数と一致しません')
    return
  }
  if (boardJigEditAddKey.value) {
    if (!mergeBoardJigEditAddIntoFrames()) {
      ElMessage.warning('追加する製品の割当を反映できません')
      return
    }
  }
  const qty = Math.max(1, Math.min(boardJigEditQtyMax.value, Math.floor(Number(boardJigEditQty.value) || 0)))
  const prev = pending.cardIds.length
  const hasProducts = boardJigEditProductFrames.value.some((p) => Math.floor(Number(p.frames) || 0) > 0)
  if (qty === prev && !productFramesEditDirty()) {
    boardJigEditDialogVisible.value = false
    return
  }
  const blockBefore = scheduleCards.value
    .filter((c) => pending.cardIds.includes(c.id))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const expandSrc = qty > prev ? pickProductSourceForJigBlockExpand(blockBefore) : null
  if (qty !== prev) {
    if (!resizeJigBlockOnLap(pending.lap_no, pending.cardIds, qty)) {
      ElMessage.warning('治具本数の変更に失敗しました')
      return
    }
    const anchorId = pending.cardIds[0]
    if (anchorId) {
      const refreshed = findJigBlockCardIds(anchorId, pending.lap_no)
      boardJigEditPending.value = { ...pending, cardIds: [...refreshed] }
    }
  }
  if (hasProducts) {
    if (isBoardJigProductFramesReassignDirty()) {
      reassignJigBlockProductsFromEdit(boardJigEditPending.value!, qty)
    } else if (isBoardJigDisplayFlagsDirty()) {
      applyBoardJigBlockDisplayFlags(boardJigEditPending.value!)
    }
  } else if (isBoardJigProductFramesReassignDirty()) {
    reassignJigBlockProductsFromEdit(boardJigEditPending.value!, qty)
  }
  boardJigEditDialogVisible.value = false
  const diff = qty - prev
  const allocationChanged = isBoardJigProductAllocationDirty()
  let msg: string
  if (!hasProducts && allocationChanged) {
    msg = `${pending.plating_machine} の製品割当を解除しました（空き治具）`
  } else if (hasProducts && allocationChanged) {
    const parts = boardJigEditProductFrames.value
      .filter((p) => Math.floor(Number(p.frames) || 0) > 0)
      .map((p) => `${p.product_name} ${Math.floor(Number(p.frames) || 0)}本`)
    msg = `${pending.plating_machine} の製品割当を更新（${parts.join('・')}）`
  } else if (diff !== 0) {
    msg =
      diff > 0
        ? expandSrc
          ? `${pending.plating_machine} を ${diff} 本増やし、${expandSrc.product_name} を追加分に割当（計 ${qty} 本）`
          : `${pending.plating_machine} を ${diff} 本増やしました（計 ${qty} 本）`
        : `${pending.plating_machine} を ${-diff} 本減らしました（計 ${qty} 本）`
  } else {
    msg = `${pending.plating_machine} を更新しました`
  }
  ElMessage.success(msg)
  void flushBoardPersist()
}

function confirmJigDropToBoard() {
  const pending = jigDropPending.value
  if (!pending) return
  const qty = Math.max(1, Math.min(jigDropQtyMax.value, Math.floor(Number(jigDropQty.value) || 0)))
  const targetLap = jigDropPreferLap.value ?? resolveJigDropTargetLap(null)
  const slots = findNextSequentialBoardSlots(qty, jigDropPreferLap.value)
  if (slots.length < qty) {
    const { layoutMax, usedOnLap, remainOnLap } = layoutJigCapacityOnLap(targetLap)
    if (remainOnLap < qty) {
      warnLayoutJigCapacityExceeded(targetLap, qty)
    } else {
      ElMessage.warning(
        `第${lapDisplayNo(targetLap)}周目へ ${qty} 本配置できません（空き枠 ${slots.length} 本のみ）`,
      )
    }
    return
  }
  if (slots.length === 0) {
    warnLayoutJigCapacityExceeded(targetLap, qty)
    return
  }
  const newCards: ScheduleCard[] = slots.map((s) => {
    removeEmptySlotAt(s.lap_no, s.turn_seq)
    return createJigScheduleCard(pending.plating_machine, s.lap_no, s.turn_seq)
  })
  scheduleCards.value = [...scheduleCards.value, ...newCards]
  jigDropDialogVisible.value = false
  ElMessage.success(`${pending.plating_machine} を ${newCards.length} 枠（本）に配置しました`)
  void flushBoardPersist()
}

function onJigCardDragStart(
  e: DragEvent,
  row: { machine_id: number | null; plating_machine: string; available_qty: number },
) {
  if (!layoutBoardReady.value) {
    e.preventDefault()
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  draggingJigToBoard.value = row
  jigBoardDragActive.value = true
  e.dataTransfer?.setData('application/x-plating-jig', row.plating_machine)
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'copy'
}

function onJigCardDragEnd() {
  jigBoardDragActive.value = false
  jigDropHoverLap.value = null
  draggingJigToBoard.value = null
}

function onJigToBoardDragOver(e: DragEvent, lapNo?: number) {
  const types = e.dataTransfer?.types
  if (!draggingJigToBoard.value && !types?.includes?.('application/x-plating-jig')) return
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
  if (!jigBoardDragActive.value) jigBoardDragActive.value = true
  if (lapNo != null && jigDropHoverLap.value !== lapNo) jigDropHoverLap.value = lapNo
}

function onJigToBoardDragLeave(e: DragEvent) {
  const rel = e.relatedTarget as Node | null
  const board = (e.currentTarget as HTMLElement | null)
  if (board && rel && board.contains(rel)) return
  if (jigDropHoverLap.value !== null) jigDropHoverLap.value = null
}

function onJigToBoardDrop(e: DragEvent, lapNo?: number) {
  e.preventDefault()
  jigBoardDragActive.value = false
  jigDropHoverLap.value = null
  const machine =
    draggingJigToBoard.value?.plating_machine ||
    e.dataTransfer?.getData('application/x-plating-jig') ||
    ''
  const row =
    draggingJigToBoard.value ||
    jigAvailabilityRows.value.find((r) => r.plating_machine === machine)
  draggingJigToBoard.value = null
  if (!row) return
  openJigDropDialog(row, lapNo ?? null)
}

/** メッキ治具カード表示：例 J曲3段（22） */
function formatJigPickLabel(row: { plating_machine: string; available_qty: number }): string {
  const name = String(row.plating_machine || '—').trim() || '—'
  const qty = Math.max(0, Math.floor(Number(row.available_qty) || 0))
  return `${name}（${qty}）`
}

/** メッキ治具カード hover：equipment_efficiency 登録の生産品種一覧 */
function jigCardProductRows(platingMachine: string): JigProductCatalogRow[] {
  const jk = normalizeMachineKey(platingMachine)
  const byProd = jigProductCatalogByMachine.value.get(jk)
  if (!byProd || byProd.size === 0) return []
  return [...byProd.values()].sort(
    (a, b) =>
      a.product_name.localeCompare(b.product_name, 'ja') ||
      a.product_cd.localeCompare(b.product_cd, 'ja'),
  )
}

const jigCardProductsDialogRows = computed(() => jigCardProductRows(jigCardProductsDialogMachine.value))

function openJigCardProductsDialog(row: { plating_machine: string; available_qty: number }) {
  jigCardProductsDialogMachine.value = String(row.plating_machine || '').trim()
  jigCardProductsDialogAvailableQty.value = Math.max(0, Math.floor(Number(row.available_qty) || 0))
  jigCardProductsDialogVisible.value = true
}

interface JigProductFilterOption {
  product_cd: string
  product_name: string
  label: string
}

/** 製品ドロップダウン（equipment_efficiency 登録品、品名順） */
const jigProductFilterOptions = computed<JigProductFilterOption[]>(() => {
  const byCd = new Map<string, JigProductFilterOption>()
  for (const byProd of jigProductCatalogByMachine.value.values()) {
    for (const row of byProd.values()) {
      const cd = String(row.product_cd || '').trim()
      if (!cd || byCd.has(cd)) continue
      const name = String(row.product_name || '').trim() || cd
      byCd.set(cd, {
        product_cd: cd,
        product_name: name,
        label: `${name}（${cd}）`,
      })
    }
  }
  return [...byCd.values()].sort((a, b) => a.product_name.localeCompare(b.product_name, 'ja'))
})

/** 製品フィルタ（el-select クリア時は undefined になるため正規化） */
const jigFilterProductCdActive = computed(() => {
  const v = jigFilterProductCd.value
  if (v == null) return ''
  return String(v).trim()
})

function onJigFilterProductModelUpdate(val: string | number | boolean | undefined | null) {
  if (val == null || val === '') {
    jigFilterProductCd.value = ''
    return
  }
  jigFilterProductCd.value = String(val)
}

function onJigFilterProductClear() {
  jigFilterProductCd.value = ''
}

const jigFilteredMachineKeys = computed<Set<string> | null>(() => {
  const cd = jigFilterProductCdActive.value
  if (!cd) return null
  const set = new Set<string>()
  for (const [mk, byProd] of jigProductCatalogByMachine.value) {
    if (byProd.has(cd)) set.add(mk)
  }
  return set
})

const jigFilteredMatchCount = computed(() => {
  const keys = jigFilteredMachineKeys.value
  if (!keys) return jigAvailabilityRows.value.length
  return jigAvailabilityRows.value.filter((r) => keys.has(normalizeMachineKey(r.plating_machine))).length
})

const jigFilterProductLabel = computed(() => {
  const cd = jigFilterProductCdActive.value
  if (!cd) return ''
  return jigProductFilterOptions.value.find((o) => o.product_cd === cd)?.product_name ?? cd
})

function jigRowMatchesProductFilter(row: { plating_machine: string }): boolean {
  const keys = jigFilteredMachineKeys.value
  if (!keys) return true
  return keys.has(normalizeMachineKey(row.plating_machine))
}

/** 製品フィルタ時は該当治具を先頭に並べ替え */
const jigAvailabilityRowsDisplay = computed(() => {
  const rows = jigAvailabilityRows.value
  const keys = jigFilteredMachineKeys.value
  if (!keys) return rows
  return [...rows].sort((a, b) => {
    const am = keys.has(normalizeMachineKey(a.plating_machine))
    const bm = keys.has(normalizeMachineKey(b.plating_machine))
    if (am === bm) {
      return String(a.plating_machine || '').localeCompare(String(b.plating_machine || ''), 'ja')
    }
    return am ? -1 : 1
  })
})

/** equipment_efficiency：治具名＋品番（補助：治具名＋品名）→ efficiency_rate */
interface EquipmentEfficiencyLookup {
  byMachineAndProductCd: Map<string, number>
  byMachineAndProductName: Map<string, number>
}

function formatEfficiencyRate(n: number): string {
  if (!Number.isFinite(n) || n <= 0) return '—'
  return formatSummaryIntegerDisplay(n)
}

function equipmentEfficiencyKey(machine: string, productPart: string): string {
  return `${normalizeMachineKey(machine)}|${productPart.trim().toLowerCase()}`
}

function buildEquipmentEfficiencyLookup(rows: EquipmentEfficiency[]): EquipmentEfficiencyLookup {
  const byMachineAndProductCd = new Map<string, number>()
  const byMachineAndProductName = new Map<string, number>()
  for (const row of rows) {
    if (row.status === 0) continue
    const effRaw = row.efficiency_rate
    if (effRaw === undefined || effRaw === null) continue
    const eff = Number(effRaw)
    if (!Number.isFinite(eff) || eff <= 0) continue
    const machine = String(row.machines_name ?? '').trim()
    if (!machine) continue
    const cd = String(row.product_cd ?? '').trim()
    const name = String(row.product_name ?? '').trim()
    if (cd) byMachineAndProductCd.set(equipmentEfficiencyKey(machine, cd), eff)
    if (name) byMachineAndProductName.set(equipmentEfficiencyKey(machine, name), eff)
  }
  return { byMachineAndProductCd, byMachineAndProductName }
}

/** メッキ治具（plating_machine）＋品番を equipment_efficiency と照合 */
function lookupPlatingEfficiency(
  lookup: EquipmentEfficiencyLookup,
  productCd: string,
  productName: string,
  jigRaw: string,
): string {
  const jig = jigRaw.trim()
  if (!jig) return '—'
  const cd = productCd.trim()
  if (cd) {
    const v = lookup.byMachineAndProductCd.get(equipmentEfficiencyKey(jig, cd))
    if (v !== undefined) return formatEfficiencyRate(v)
  }
  const name = productName.trim()
  if (name) {
    const v = lookup.byMachineAndProductName.get(equipmentEfficiencyKey(jig, name))
    if (v !== undefined) return formatEfficiencyRate(v)
  }
  return '—'
}

interface EquipmentEfficiencyBundle {
  lookup: EquipmentEfficiencyLookup
  catalogByMachine: Map<string, Map<string, JigProductCatalogRow>>
}

let equipmentEfficiencyBundleCache: EquipmentEfficiencyBundle | null = null
let equipmentEfficiencyBundlePromise: Promise<EquipmentEfficiencyBundle> | null = null
let summaryPairRequestSeq = 0

function invalidateEquipmentEfficiencyBundleCache() {
  equipmentEfficiencyBundleCache = null
  equipmentEfficiencyBundlePromise = null
}

async function fetchEquipmentEfficiencyBundle(): Promise<EquipmentEfficiencyBundle> {
  if (equipmentEfficiencyBundleCache) return equipmentEfficiencyBundleCache
  if (equipmentEfficiencyBundlePromise) return equipmentEfficiencyBundlePromise
  const empty: EquipmentEfficiencyBundle = {
    lookup: { byMachineAndProductCd: new Map(), byMachineAndProductName: new Map() },
    catalogByMachine: new Map(),
  }
  equipmentEfficiencyBundlePromise = (async () => {
    try {
      const res = await fetchEquipmentEfficiencyList({
        page: 1,
        pageSize: 10000,
        processType: 'plating',
      })
      const list = (res?.data?.list ?? res?.list ?? []) as EquipmentEfficiency[]
      const bundle = {
        lookup: buildEquipmentEfficiencyLookup(list),
        catalogByMachine: buildJigProductCatalogFromEquipmentEfficiency(list),
      }
      equipmentEfficiencyBundleCache = bundle
      return bundle
    } catch (e) {
      console.warn('fetchEquipmentEfficiencyBundle:', e)
      return empty
    } finally {
      equipmentEfficiencyBundlePromise = null
    }
  })()
  return equipmentEfficiencyBundlePromise
}

/** 左＝メッキ前在庫の基準日、右＝見込数量の参照日（専用 API・KT05 絞り込み） */
async function loadSummaryPair() {
  if (!leftInventoryDate.value || !rightGenDate.value) {
    return
  }
  const reqSeq = ++summaryPairRequestSeq
  const d0 = leftInventoryDate.value
  const d1 = rightGenDate.value
  loadingPair.value = true
  try {
    const data = await fetchPlatingSummaryPair(d0, d1)
    if (reqSeq !== summaryPairRequestSeq) return
    leftRows.value = data.left_inventory.map((r) => ({
      ...r,
      plating_efficiency: formatSummaryKakeDisplay(r.plating_efficiency),
    }))
    rightRows.value = data.right_gen.map((r) => ({
      ...r,
      gen_qty: r.gen_qty as number | string,
      plating_efficiency: formatSummaryKakeDisplay(r.plating_efficiency),
    }))
    const merged = new Map(jigProductCatalogByMachine.value)
    enrichJigCatalogFromPaneRows(merged, leftRows.value, rightRows.value)
    jigProductCatalogByMachine.value = merged
  } catch (e) {
    if (reqSeq !== summaryPairRequestSeq) return
    console.error(e)
    ElMessage.error('生産サマリ（production_summarys）の取得に失敗しました')
  } finally {
    if (reqSeq === summaryPairRequestSeq) loadingPair.value = false
  }
}

// ─── ③ メッキ投入ボード（スケジュール表示）──────────────────

/** 1日あたりの分数（稼働 UI は廃止。投入計算・API の daily_minutes は互換のため 600 固定） */
const PLATING_DAY_MINUTES = 600

const boardLapsPerDay = computed(() => {
  const cycle = layoutBoardReady.value ? layoutMinutesPerLap.value : minutesPerLap.value
  if (cycle <= 0) return 0
  return Math.floor(PLATING_DAY_MINUTES / cycle)
})

function normalizeMachineKey(v: string): string {
  return String(v || '').trim().toLowerCase()
}

/** 同一品番は常に同じ sched-color（在庫/見込リスト等での識別用） */
function schedColorIndexForProductCd(productCd: string): number {
  const s = String(productCd ?? '').trim()
  if (!s) return 0
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h) % 24
}

/** ボード表示用：同一メッキ治具は常に同じ色（24色） */
function schedColorIndexForPlatingMachine(machine: string): number {
  const s = normalizeMachineKey(machine)
  if (!s) return 0
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 33 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h) % 24
}

const canUseLapCopy = computed(() => layoutBoardReady.value && layoutMaxLaps.value >= 2)

const lapCopyLapOptions = computed(() => {
  const scheduleByLap = new Map(globalLapSchedule.value.map((s) => [s.lap_no, s]))
  return lapGridRows.value.map((r) => {
    const wd = scheduleByLap.get(r.lap_no)?.work_date
    const prefix = wd ? `${formatBoardDateLabel(wd)} ` : ''
    return { value: r.lap_no, label: `${prefix}第${r.lap_display_no}周目` }
  })
})

const lapCopySourceCount = computed(
  () => lapCardsWithQty(lapCopyFrom.value).length,
)

const deletableStartDates = computed(() => {
  const seen = new Set<string>()
  const out: string[] = []
  const rows = [...currentLayoutLapSchedule()].sort((a, b) => a.lap_no - b.lap_no)
  for (const r of rows) {
    const d = String(r.work_date || '').slice(0, 10)
    if (!d || seen.has(d)) continue
    seen.add(d)
    out.push(d)
  }
  return out
})

function openDeleteLapsByDateDialog() {
  if (!layoutBoardReady.value || deletableStartDates.value.length === 0) {
    ElMessage.warning('削除対象の日付がありません')
    return
  }
  deleteLapsByDateYmd.value = deletableStartDates.value[0] ?? ''
  deleteLapsByDateDialogVisible.value = true
}

function confirmDeleteLapsByDate() {
  const targetDate = String(deleteLapsByDateYmd.value || '').slice(0, 10)
  if (!targetDate) return
  const schedule = [...currentLayoutLapSchedule()].sort((a, b) => a.lap_no - b.lap_no)
  const deleteLaps = schedule.filter((s) => String(s.work_date || '').slice(0, 10) === targetDate).map((s) => s.lap_no)
  if (deleteLaps.length === 0) {
    ElMessage.warning(`${formatBoardDateLabel(targetDate)} に削除対象の周目はありません`)
    return
  }
  const deleteSet = new Set(deleteLaps)
  const keepLaps = schedule.filter((s) => !deleteSet.has(s.lap_no))
  const newLapNoByOld = new Map<number, number>()
  keepLaps.forEach((s, i) => {
    newLapNoByOld.set(s.lap_no, i + 1)
  })

  if (keepLaps.length === 0) {
    scheduleCards.value = []
    standardPositions.value.clear()
    layoutBlocks.value = []
    layoutBoardReady.value = false
    layoutMaxLaps.value = 0
    deleteLapsByDateDialogVisible.value = false
    ElMessage.success(`${formatBoardDateLabel(targetDate)} の周目をすべて削除しました`)
    void flushBoardPersist()
    return
  }

  const cycleByLap = new Map<number, number>()
  const jigsByLap = new Map<number, number>()
  for (const b of [...layoutBlocks.value].sort((a, b) => a.base_lap_no - b.base_lap_no)) {
    const laps = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const cycle = Math.max(1, Math.floor(Number(b.minutes_per_lap) || 1))
    const jigs = Math.max(1, Math.floor(Number(b.jigs_per_lap) || 1))
    for (let i = 0; i < laps; i += 1) {
      const ln = b.base_lap_no + i
      cycleByLap.set(ln, cycle)
      jigsByLap.set(ln, jigs)
    }
  }

  const rebuiltBlocks: BoardLayoutBlock[] = []
  for (const s of keepLaps) {
    const oldLap = s.lap_no
    const newLap = newLapNoByOld.get(oldLap)
    if (!newLap) continue
    const cycle = cycleByLap.get(oldLap) ?? layoutMinutesPerLap.value
    const jigs = jigsByLap.get(oldLap) ?? layoutJigsPerLap.value
    const start = dayjs.tz(`${s.work_date} ${s.start}`, 'YYYY-MM-DD HH:mm', TZ_JP)
    const prev = rebuiltBlocks[rebuiltBlocks.length - 1]
    if (prev) {
      const prevStart = dayjs.tz(
        `${prev.plan_date} ${normalizeBoardStartTimeHm(prev.start_time)}`,
        'YYYY-MM-DD HH:mm',
        TZ_JP,
      )
      const prevEnd = prevStart.add(prev.minutes_per_lap * prev.lap_count, 'minute')
      if (prev.minutes_per_lap === cycle && prev.jigs_per_lap === jigs && start.isSame(prevEnd)) {
        prev.lap_count += 1
        continue
      }
    }
    rebuiltBlocks.push({
      plan_date: String(s.work_date || '').slice(0, 10),
      start_time: normalizeBoardStartTimeHm(s.start),
      minutes_per_lap: cycle,
      jigs_per_lap: jigs,
      lap_count: 1,
      base_lap_no: newLap,
    })
  }

  const keptCards = scheduleCards.value.filter((c) => !deleteSet.has(c.lap_no))
  const remapped: ScheduleCard[] = []
  for (const c of keptCards) {
    const newLap = newLapNoByOld.get(c.lap_no)
    if (!newLap) continue
    remapped.push({ ...c, lap_no: newLap, persist_lap_no: newLap })
  }
  const byLap = new Map<number, ScheduleCard[]>()
  for (const c of remapped) {
    const arr = byLap.get(c.lap_no) ?? []
    arr.push(c)
    byLap.set(c.lap_no, arr)
  }
  const renumberedCards: ScheduleCard[] = []
  for (const lap of [...byLap.keys()].sort((a, b) => a - b)) {
    const rows = (byLap.get(lap) ?? []).sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    rows.forEach((c, i) => {
      renumberedCards.push({ ...c, turn_seq: i + 1 })
    })
  }
  scheduleCards.value = renumberedCards

  const nextStd = new Map<string, { lap_no: number; turn_seq: number }>()
  for (const [id, pos] of standardPositions.value.entries()) {
    const newLap = newLapNoByOld.get(pos.lap_no)
    if (!newLap) continue
    nextStd.set(id, { lap_no: newLap, turn_seq: pos.turn_seq })
  }
  standardPositions.value = nextStd

  layoutBlocks.value = rebuiltBlocks
  layoutBoardReady.value = rebuiltBlocks.length > 0
  const first = rebuiltBlocks[0]
  if (first) {
    layoutPlanDate.value = first.plan_date
    layoutStartTime.value = normalizeBoardStartTimeHm(first.start_time)
    layoutMinutesPerLap.value = first.minutes_per_lap
    layoutJigsPerLap.value = first.jigs_per_lap
  }
  recomputeLayoutMaxLapsFromSchedule()
  refreshMarksAgainstStandardPositions()
  deleteLapsByDateDialogVisible.value = false
  ElMessage.success(`${formatBoardDateLabel(targetDate)} の周目（${deleteLaps.length}件）を削除しました`)
  void flushBoardPersist()
}

function openLapCopyDialog() {
  if (!canUseLapCopy.value) {
    ElMessage.warning('周目コピーには追加レイアウト後・2周目以上が必要です')
    return
  }
  const rows = lapGridRows.value
  lapCopyFrom.value = rows[0]?.lap_no ?? 1
  lapCopyTo.value = rows.length >= 2 ? rows[1]!.lap_no : rows[0]?.lap_no ?? 1
  lapCopyDialogVisible.value = true
}

function renumberLapTurnSeq(lapNo: number) {
  const lapCards = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  lapCards.forEach((c, i) => {
    c.turn_seq = i + 1
  })
}

function confirmCopyLapSchedule() {
  const from = lapCopyFrom.value
  const to = lapCopyTo.value
  if (!layoutBoardReady.value) return
  if (from === to) {
    ElMessage.warning('コピー元とコピー先は別の周目を指定してください')
    return
  }
  const sourceCards = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === from)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  if (sourceCards.length === 0) {
    ElMessage.warning(`第${lapDisplayNo(from)}周目にコピーするデータがありません`)
    return
  }
  const cols = lapBoardColCount.value
  if (sourceCards.length > cols) {
    ElMessage.warning(
      `第${lapDisplayNo(from)}周目は ${sourceCards.length} 枠あり、1周の列数（${cols} 本）を超えるためコピーできません`,
    )
    return
  }

  const jigTotals = new Map<string, { machine: string; count: number }>()
  for (const c of sourceCards) {
    const key = normalizeMachineKey(c.plating_machine)
    const cur = jigTotals.get(key) ?? { machine: c.plating_machine, count: 0 }
    cur.count += 1
    jigTotals.set(key, cur)
  }
  for (const { machine, count } of jigTotals.values()) {
    const max = getJigAvailMaxFromMaster(machine)
    if (count > max) {
      ElMessage.warning(`${machine} は第${lapDisplayNo(to)}周目で使用可能 ${max} 本までです（コピー内容 ${count} 本）`)
      return
    }
  }

  const ts = Date.now()
  const targetLapMeta = lapScheduleMetaForCard(to)
  const newCards: ScheduleCard[] = sourceCards.map((c, i) => ({
    ...c,
    id: `lap-copy-${ts}-${i}-${Math.random().toString(36).slice(2, 6)}`,
    lap_no: to,
    persist_lap_no: to,
    turn_seq: c.turn_seq,
    lap_work_date: targetLapMeta.lap_work_date ?? c.lap_work_date,
    lap_start_time: targetLapMeta.lap_start_time ?? c.lap_start_time ?? null,
    lap_end_time: targetLapMeta.lap_end_time ?? c.lap_end_time ?? null,
    boardMark: 'manual' as BoardMark,
  }))

  const others = scheduleCards.value.filter((c) => c.lap_no !== to)
  scheduleCards.value = [...others, ...newCards]
  renumberLapTurnSeq(to)
  refreshMarksAgainstStandardPositions()
  lapCopyDialogVisible.value = false
  ElMessage.success(`第${lapDisplayNo(from)}周目の ${newCards.length} 枠を第${lapDisplayNo(to)}周目へコピーしました`)
  void flushBoardPersist()
}

interface TimedLapSlot {
  lap_no: number
  work_date: string
  work_date_label: string
  start: string
  end: string
  minutes_per_lap: number
  jigs_per_lap: number
  src_lap_no: number
}

function buildCycleJigsMapsFromLayout(): { cycleByLap: Map<number, number>; jigsByLap: Map<number, number> } {
  const cycleByLap = new Map<number, number>()
  const jigsByLap = new Map<number, number>()
  for (const b of [...layoutBlocks.value].sort((a, b) => a.base_lap_no - b.base_lap_no)) {
    const laps = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const cycle = Math.max(1, Math.floor(Number(b.minutes_per_lap) || 1))
    const jigs = Math.max(1, Math.floor(Number(b.jigs_per_lap) || 1))
    for (let i = 0; i < laps; i += 1) {
      const ln = b.base_lap_no + i
      cycleByLap.set(ln, cycle)
      jigsByLap.set(ln, jigs)
    }
  }
  return { cycleByLap, jigsByLap }
}

function layoutBlocksFromTimedSlots(slots: TimedLapSlot[]): BoardLayoutBlock[] {
  const rebuilt: BoardLayoutBlock[] = []
  for (const s of slots) {
    const startDt = dayjs.tz(`${s.work_date} ${s.start}`, 'YYYY-MM-DD HH:mm', TZ_JP)
    if (!startDt.isValid()) continue
    const cycle = Math.max(1, Math.floor(Number(s.minutes_per_lap) || 1))
    const jigs = Math.max(1, Math.floor(Number(s.jigs_per_lap) || 1))
    const prev = rebuilt[rebuilt.length - 1]
    if (prev) {
      const prevStart = dayjs.tz(
        `${prev.plan_date} ${normalizeBoardStartTimeHm(prev.start_time)}`,
        'YYYY-MM-DD HH:mm',
        TZ_JP,
      )
      const prevEnd = prevStart.add(prev.minutes_per_lap * prev.lap_count, 'minute')
      if (prev.minutes_per_lap === cycle && prev.jigs_per_lap === jigs && startDt.isSame(prevEnd)) {
        prev.lap_count += 1
        continue
      }
    }
    rebuilt.push({
      plan_date: s.work_date,
      start_time: normalizeBoardStartTimeHm(s.start),
      minutes_per_lap: cycle,
      jigs_per_lap: jigs,
      lap_count: 1,
      base_lap_no: s.lap_no,
    })
  }
  return rebuilt
}

function compareTimedLapSlots(a: TimedLapSlot, b: TimedLapSlot): number {
  const ka = `${a.work_date}|${normalizeBoardStartTimeHm(a.start)}`
  const kb = `${b.work_date}|${normalizeBoardStartTimeHm(b.start)}`
  if (ka !== kb) return ka.localeCompare(kb)
  return a.src_lap_no - b.src_lap_no
}

/** 時刻順に並べ替え → 周目番号 1..N 再採番 → layout / cards を同期 */
function applyBoardScheduleRenumber(timedSlots: TimedLapSlot[]): Map<number, number> {
  const sorted = [...timedSlots].sort(compareTimedLapSlots)
  const oldToNew = new Map<number, number>()
  sorted.forEach((s, i) => {
    const newLap = i + 1
    oldToNew.set(s.src_lap_no, newLap)
    s.lap_no = newLap
  })

  layoutBlocks.value = layoutBlocksFromTimedSlots(sorted)
  layoutBoardReady.value = layoutBlocks.value.length > 0
  layoutMaxLaps.value = sorted.length
  const first = layoutBlocks.value[0]
  if (first) {
    layoutPlanDate.value = first.plan_date
    layoutStartTime.value = normalizeBoardStartTimeHm(first.start_time)
    layoutMinutesPerLap.value = first.minutes_per_lap
    layoutJigsPerLap.value = first.jigs_per_lap
    jigsPerLap.value = first.jigs_per_lap
    minutesPerLap.value = first.minutes_per_lap
  }

  const slotByLap = new Map(sorted.map((s) => [s.lap_no, s]))
  const remapped: ScheduleCard[] = []
  for (const c of scheduleCards.value) {
    const newLap = oldToNew.get(c.lap_no)
    if (!newLap) continue
    const slot = slotByLap.get(newLap)
    remapped.push({
      ...c,
      lap_no: newLap,
      persist_lap_no: newLap,
      lap_work_date: slot?.work_date ?? c.lap_work_date,
      lap_start_time: slot?.start ?? c.lap_start_time,
      lap_end_time: slot?.end ?? c.lap_end_time,
    })
  }
  const byLap = new Map<number, ScheduleCard[]>()
  for (const c of remapped) {
    const arr = byLap.get(c.lap_no) ?? []
    arr.push(c)
    byLap.set(c.lap_no, arr)
  }
  const scheduleByLap = new Map(sorted.map((s) => [s.lap_no, s] as [number, LapScheduleSlot]))
  const renumberedCards: ScheduleCard[] = []
  for (const lap of [...byLap.keys()].sort((a, b) => compareLapNoForBoardSort(a, b, scheduleByLap))) {
    const rows = (byLap.get(lap) ?? []).sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    rows.forEach((c, i) => {
      renumberedCards.push({ ...c, turn_seq: i + 1 })
    })
  }
  scheduleCards.value = renumberedCards

  const nextStd = new Map<string, { lap_no: number; turn_seq: number }>()
  for (const [id, pos] of standardPositions.value.entries()) {
    const newLap = oldToNew.get(pos.lap_no)
    if (!newLap) continue
    nextStd.set(id, { lap_no: newLap, turn_seq: pos.turn_seq })
  }
  standardPositions.value = nextStd

  recomputeLayoutMaxLapsFromSchedule()
  syncScheduleCardLapTimesFromLayout()
  return oldToNew
}

function applyInsertDefaultsAfterAnchor(anchorLapNo: number) {
  const schedule = currentLayoutLapSchedule()
  const anchor = schedule.find((s) => s.lap_no === anchorLapNo)
  if (!anchor) return
  const endDt = dayjs.tz(`${anchor.work_date} ${anchor.end}`, 'YYYY-MM-DD HH:mm', TZ_JP)
  if (endDt.isValid()) {
    tplFormPlanDate.value = endDt.format('YYYY-MM-DD')
    tplFormStartTime.value = endDt.format('HH:mm')
  } else {
    tplFormPlanDate.value = anchor.work_date
    tplFormStartTime.value = normalizeBoardStartTimeHm(anchor.start)
  }
  const { cycleByLap, jigsByLap } = buildCycleJigsMapsFromLayout()
  tplFormMinutesPerLap.value = cycleByLap.get(anchorLapNo) ?? layoutMinutesPerLap.value
  tplFormJigsPerLap.value = jigsByLap.get(anchorLapNo) ?? layoutJigsPerLap.value
}

function openAppendLayoutDialog(insertAfterLapNo?: number) {
  if (insertAfterLapNo != null && insertAfterLapNo > 0) {
    tplFormInsertMode.value = 'insert'
    tplFormInsertAfterLapNo.value = insertAfterLapNo
    tplFormMaxLaps.value = 1
    applyInsertDefaultsAfterAnchor(insertAfterLapNo)
    tplAppendSuggestedLabel.value = ''
  } else {
    tplFormInsertMode.value = 'append'
    const next = computeNextAppendLayoutDefaults()
    tplFormPlanDate.value = next.planDate
    tplFormStartTime.value = next.startTime
    tplFormMinutesPerLap.value = next.minutesPerLap
    tplFormJigsPerLap.value = next.jigsPerLap
    tplFormMaxLaps.value = next.maxLaps
    tplAppendSuggestedLabel.value = next.suggestedLabel
  }
  templateDialogVisible.value = true
}

watch([tplFormInsertMode, tplFormInsertAfterLapNo], () => {
  if (tplFormInsertMode.value !== 'insert' || !layoutBoardReady.value) return
  applyInsertDefaultsAfterAnchor(tplFormInsertAfterLapNo.value)
})

async function confirmInsertLayoutAfterAnchor() {
  const anchorLap = Math.max(1, Math.floor(Number(tplFormInsertAfterLapNo.value) || 0))
  const planDate = (tplFormPlanDate.value || '').trim()
  if (!planDate) {
    ElMessage.warning('計画日を指定してください')
    return
  }
  const startHm = normalizeBoardStartTimeHm(tplFormStartTime.value)
  const j = Math.max(1, Math.min(300, Math.floor(Number(tplFormJigsPerLap.value) || 1)))
  const laps = Math.max(1, Math.min(500, Math.floor(Number(tplFormMaxLaps.value) || 1)))
  const cycle = Math.max(1, Math.min(600, Math.floor(Number(tplFormMinutesPerLap.value) || 1)))
  const preview = buildLapScheduleRows(planDate, startHm, cycle, laps)
  if (preview.length === 0) {
    ElMessage.warning('開始時刻・段数を確認してください')
    return
  }

  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const sorted = [...schedule].sort((a, b) => compareLapNoForBoardSort(a.lap_no, b.lap_no, scheduleByLap))
  const anchorIdx = sorted.findIndex((s) => s.lap_no === anchorLap)
  if (anchorIdx < 0) {
    ElMessage.warning('挿入位置の周目が見つかりません')
    return
  }

  if (layoutJigsPerLap.value !== j) {
    ElMessage.warning(`1周の本数を ${layoutJigsPerLap.value} から ${j} に変更します（挿入する週のみ ${j} 本）`)
  }

  const { cycleByLap, jigsByLap } = buildCycleJigsMapsFromLayout()
  let tempSrc = -1
  const existing: TimedLapSlot[] = sorted.map((s) => ({
    lap_no: s.lap_no,
    work_date: s.work_date,
    work_date_label: s.work_date_label,
    start: s.start,
    end: s.end,
    minutes_per_lap: cycleByLap.get(s.lap_no) ?? layoutMinutesPerLap.value,
    jigs_per_lap: jigsByLap.get(s.lap_no) ?? layoutJigsPerLap.value,
    src_lap_no: s.lap_no,
  }))
  const inserted: TimedLapSlot[] = preview.map((r) => {
    const src = tempSrc
    tempSrc -= 1
    return {
      lap_no: src,
      work_date: r.work_date,
      work_date_label: r.work_date_label,
      start: r.start,
      end: r.end,
      minutes_per_lap: cycle,
      jigs_per_lap: j,
      src_lap_no: src,
    }
  })
  const merged = [...existing.slice(0, anchorIdx + 1), ...inserted, ...existing.slice(anchorIdx + 1)]

  templateDialogVisible.value = false
  withSuppressedScheduleSideEffects(() => {
    applyBoardScheduleRenumber(merged)
    ensureBoardCardSkeletonsForLayout()
  })
  void nextTick(() => {
    if (!scheduleCards.value.some((c) => c.qty > 0)) initLapTrackSortables()
  })

  const last = preview[preview.length - 1]
  try {
    await flushLayoutPersist(false)
    const msg = last
      ? `第${lapDisplayNo(anchorLap)}周目の後に ${laps} 段を挿入し、時刻順に整列しました（${startHm}〜${last.end}）`
      : `第${lapDisplayNo(anchorLap)}周目の後に ${laps} 段を挿入し、時刻順に整列しました`
    ElMessage.success(msg)
  } catch {
    ElMessage.error('レイアウトの保存に失敗しました。再度お試しください')
  }
}

async function confirmAppendLayout() {
  if (tplFormInsertMode.value === 'insert') {
    await confirmInsertLayoutAfterAnchor()
    return
  }
  const planDate = (tplFormPlanDate.value || '').trim()
  if (!planDate) {
    ElMessage.warning('計画日を指定してください')
    return
  }
  const startHm = normalizeBoardStartTimeHm(tplFormStartTime.value)
  if (findDuplicateLayoutBlock(planDate, startHm)) {
    ElMessage.warning(
      `同じ計画日・開始時刻（${formatBoardDateLabel(planDate)} ${startHm}）のレイアウトが既にあります`,
    )
    return
  }
  if (tplLapSchedulePreview.value.length === 0) {
    ElMessage.warning('開始時刻・段数を確認してください')
    return
  }
  const j = Math.max(1, Math.min(300, Math.floor(Number(tplFormJigsPerLap.value) || 1)))
  const laps = Math.max(1, Math.min(500, Math.floor(Number(tplFormMaxLaps.value) || 1)))
  const cycle = Math.max(1, Math.min(600, Math.floor(Number(tplFormMinutesPerLap.value) || 1)))
  const baseLapNo = layoutBoardReady.value && layoutMaxLaps.value > 0 ? layoutMaxLaps.value + 1 : 1

  if (layoutBoardReady.value && layoutJigsPerLap.value !== j) {
    ElMessage.warning(`1周の本数を ${layoutJigsPerLap.value} から ${j} に変更します（ボード全体）`)
  }

  layoutBlocks.value.push({
    plan_date: planDate,
    start_time: startHm,
    minutes_per_lap: cycle,
    jigs_per_lap: j,
    lap_count: laps,
    base_lap_no: baseLapNo,
  })
  layoutMaxLaps.value = baseLapNo + laps - 1
  layoutPlanDate.value = planDate
  layoutStartTime.value = startHm
  layoutMinutesPerLap.value = cycle
  layoutJigsPerLap.value = j
  jigsPerLap.value = j
  minutesPerLap.value = cycle
  layoutBoardReady.value = true
  templateDialogVisible.value = false
  withSuppressedScheduleSideEffects(() => ensureBoardCardSkeletonsForLayout())
  void nextTick(() => {
    if (!scheduleCards.value.some((c) => c.qty > 0)) initLapTrackSortables()
  })
  const preview = buildLapScheduleRows(planDate, startHm, cycle, laps)
  const last = preview[preview.length - 1]
  try {
    await flushLayoutPersist(false)
    const msg = last
      ? `${formatBoardDateLabel(planDate)}：第1〜${laps}周目を追加し、レイアウト・ボード枠をデータベースに保存しました（${startHm}〜${last.end}）`
      : `${formatBoardDateLabel(planDate)}：第1〜${laps}周目を追加し、レイアウト・ボード枠をデータベースに保存しました`
    ElMessage.success(msg)
  } catch {
    ElMessage.error('レイアウトの保存に失敗しました。再度お試しください')
  }
}

interface LapBarSegment {
  key: string
  product_cd: string
  product_name: string
  plating_machine: string
  slotCount: number
  widthPct: number
  boardMark: BoardMark
}

interface LapGridCell {
  segments: LapBarSegment[]
}

interface LapMergedSegment {
  key: string
  startCol: number
  span: number
  product_cd: string
  product_name: string
  plating_machine: string
  boardMark: BoardMark
  cardIds: string[]
  slotCount: number
}

interface LapGridRow {
  lap_no: number
  /** 同一計画日内の表示用周番（1 始まり） */
  lap_display_no: number
  cells: LapGridCell[]
  /** null＝未割当の空枠（列セル表示）／配列＝左側列の横結合バー */
  mergedLeft: LapMergedSegment[] | null
  /** 最終列に積まれる枠（横結合しない） */
  mergedTail: ScheduleCard[] | null
}

/** 1周あたりの治具本数＝列数（レイアウト確定後は layout を優先） */
const lapBoardColCount = computed(() => {
  const j = Math.floor(Number(layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value) || 0)
  return Math.max(1, Math.min(300, j > 0 ? j : 1))
})

/** 列幅：空列・ヘッダー用の下限（ch）、内容に応じて拡張 */
const MIN_LAP_COL_CH = 0.7
/** 製品セル等の单列上限（ch） */
const MAX_LAP_COL_CH = 22
/** メッキ治具が占める单列上限（ch） */
const MAX_LAP_JIG_COL_CH = 6
/** メッキ治具ブロック全体の上限（標準 15 列分の 50%） */
const MAX_LAP_JIG_BLOCK_TOTAL_CH = MAX_LAP_JIG_COL_CH * 7.5

const lapLabelColWidth = '76px'
const COMPACT_LAP_HEADER_THRESHOLD = 12

/** ③ボード表示：「製品名 (本数)」例 5A54 (5) — 括弧内は当該表示ブロックのメッキ治具本数 */
function formatPlatingBoardLabel(productName: string, jigUnits: number): string {
  const name = String(productName ?? '').trim() || '空'
  const n = Math.max(0, Math.floor(Number(jigUnits) || 0))
  return `${name} (${n})`
}

function splitColumnNumberDigits(value: number): string[] {
  const n = Math.max(1, Math.floor(Number(value) || 1))
  return String(n).split('')
}

const useCompactLapHeader = computed(() => lapBoardColCount.value >= COMPACT_LAP_HEADER_THRESHOLD)

function buildCompactHeaderMarks(colCount: number): number[] {
  const n = Math.max(1, Math.floor(Number(colCount) || 1))
  const marks = new Set<number>([1])
  for (let m = 10; m < n; m += 10) marks.add(m)
  marks.add(n)
  return Array.from(marks).sort((a, b) => a - b)
}

function compactHeaderMarkItems(colCount: number, widths: number[]): Array<{ value: number; leftPct: number }> {
  const marks = buildCompactHeaderMarks(colCount)
  const n = Math.max(1, Math.floor(Number(colCount) || 1))
  const padded =
    widths.length >= n
      ? widths.slice(0, n)
      : [...widths, ...Array.from({ length: n - widths.length }, (_, i) => lapColHeaderWidthCh(widths.length + i + 1))]
  const total = padded.reduce((a, b) => a + b, 0) || 1
  return marks.map((m) => {
    const idx = Math.max(1, Math.min(n, m))
    const before = padded.slice(0, idx - 1).reduce((a, b) => a + b, 0)
    const center = before + (padded[idx - 1] ?? 0) / 2
    return { value: m, leftPct: (center / total) * 100 }
  })
}

const compactLapHeaderMarkItems = computed(() =>
  compactHeaderMarkItems(lapBoardColCount.value, lapBoardColumnWidthsCh.value),
)

function buildCompactHeaderMarksHtml(colCount: number, widths: number[]): string {
  return compactHeaderMarkItems(colCount, widths)
    .map((m) => `<span class="lap-col-head-range-mark" style="left:${m.leftPct}%">${m.value}</span>`)
    .join('')
}

/** 列幅（ch）に応じて表頭に縦表示できる桁数（狭い列は下位桁のみ） */
function columnHeaderMaxVisibleDigits(widthCh: number): number {
  return Math.max(1, Math.floor((widthCh + 0.18) / 0.62))
}

function visibleHeaderDigits(colNo: number, widthCh: number): string[] {
  const all = splitColumnNumberDigits(colNo)
  const maxVis = columnHeaderMaxVisibleDigits(widthCh)
  return all.length <= maxVis ? all : all.slice(-maxVis)
}

function buildLapColumnHeadHtml(colNo: number, widthCh: number): string {
  const digits = visibleHeaderDigits(colNo, widthCh)
  const truncated = digits.length < splitColumnNumberDigits(colNo).length
  const title = truncated ? ` title="${colNo}"` : ''
  const inner = digits.map((d) => `<span class="lap-col-head-digit">${d}</span>`).join('')
  const cls = truncated ? ' lap-col-head--truncated' : ''
  return `<div class="lap-col-head${cls}"${title}><span class="lap-col-head-digits">${inner}</span></div>`
}

/** 1枚＝1セグメント（枠単位の削除・ドラッグ・枠色） */
function cardsToDisplaySegments(cards: ScheduleCard[]): LapBarSegment[] {
  const filtered = cards.filter((c) => c.qty > 0)
  const total = filtered.length || 1
  return filtered.map((c) => ({
    key: c.id,
    product_cd: c.product_cd,
    product_name: c.product_name || '空',
    plating_machine: c.plating_machine || '—',
    slotCount: 1,
    widthPct: (1 / total) * 100,
    boardMark: c.boardMark ?? 'standard',
  }))
}

/**
 * turn_seq（1 始まり）を列番号に対応させて配置。
 * - turn_seq 1〜(n-1) → 各列 1 枚
 * - turn_seq >= n → 最終列に集約（レイアウト超過分）
 */
function binCardsIntoColumns(cards: ScheduleCard[], colCount: number): ScheduleCard[][] {
  const n = Math.max(1, colCount)
  const sorted = [...cards]
    .filter((c) => c.qty > 0)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const bins: ScheduleCard[][] = Array.from({ length: n }, () => [])
  for (const c of sorted) {
    const turn = Math.max(0, Math.floor(Number(c.turn_seq) || 0))
    if (turn < 1) {
      bins[n - 1].push(c)
      continue
    }
    if (turn < n) {
      bins[turn - 1].push(c)
    } else {
      bins[n - 1].push(c)
    }
  }
  return bins
}

/** ③ボード治具ブロック結合：同一メッキ治具（machine）なら製品が違っても横結合表示 */
function mergeKeyForScheduleCard(c: ScheduleCard): string {
  return `${normalizeMachineKey(c.plating_machine)}`
}

function boardMarkRank(m: BoardMark): number {
  if (m === 'rush') return 3
  if (m === 'manual') return 2
  return 1
}

function maxBoardMark(a: BoardMark, b: BoardMark): BoardMark {
  return boardMarkRank(a) >= boardMarkRank(b) ? a : b
}

/** 全列を対象に隣接かつ同一メッキ治具なら横結合（最終列も含む。尾列のみの別治具は縦積み） */
function buildMergedLeftSegments(cards: ScheduleCard[], lapNo: number, n: number): LapMergedSegment[] {
  if (n <= 0) return []
  const bins = binCardsIntoColumns(cards, n)
  const colRep: (ScheduleCard | undefined)[] = bins.map((bin) => bin[0])

  const out: LapMergedSegment[] = []
  let i = 0
  while (i < n) {
    if (!colRep[i]) {
      i += 1
      continue
    }
    const mk = mergeKeyForScheduleCard(colRep[i]!)
    let j = i
    let bm: BoardMark = colRep[i]!.boardMark ?? 'standard'
    while (j + 1 < n && colRep[j + 1] && mergeKeyForScheduleCard(colRep[j + 1]!) === mk) {
      j += 1
      bm = maxBoardMark(bm, colRep[j]!.boardMark ?? 'standard')
    }
    const slice: ScheduleCard[] = []
    const cardIds: string[] = []
    for (let k = i; k <= j; k += 1) {
      for (const c of bins[k]) {
        slice.push(c)
        cardIds.push(c.id)
      }
    }
    out.push({
      key: `mg-${lapNo}-L-${i}-${cardIds.join('|')}`,
      startCol: i + 1,
      span: j - i + 1,
      product_cd: slice[0].product_cd,
      product_name: slice[0].product_name || '空',
      plating_machine: slice[0].plating_machine || '—',
      boardMark: bm,
      cardIds,
      slotCount: slice.reduce((s, c) => s + c.qty, 0),
    })
    i = j + 1
  }
  return out
}

function lapNoWorkDateInBoard(lapNo: number, scheduleByLap: Map<number, LapScheduleSlot>): string {
  const fromSchedule = scheduleByLap.get(lapNo)?.work_date
  const fromCard = lapCardMetaByLap.value.get(lapNo)?.work_date
  return (fromSchedule || fromCard || '').slice(0, 10)
}

function collectLapNumbersForBoardGrid(scheduleByLap: Map<number, LapScheduleSlot>): number[] {
  const schedule = currentLayoutLapSchedule()
  const lapNosWithData = boardLapNosWithBoardDataInView()
  const lapNosFromCards = boardLapNosInViewFromScheduleCards()
  const inViewScheduleLaps = schedule
    .filter((s) => isYmdInBoardView(s.work_date))
    .map((s) => s.lap_no)

  if (layoutBoardReady.value) {
    const lapSet = new Set<number>([...inViewScheduleLaps, ...lapNosWithData, ...lapNosFromCards])
    let lapNumbers = [...lapSet].filter((ln) => isYmdInBoardView(lapNoWorkDateInBoard(ln, scheduleByLap)))
    if (lapNumbers.length === 0) return []
    if (scheduleByLap.size > 0) {
      lapNumbers.sort((a, b) => compareLapNoForBoardSort(a, b, scheduleByLap))
    } else {
      lapNumbers.sort((a, b) => a - b)
    }
    return lapNumbers
  }

  let lapNumbers = [...lapNosWithData].sort((a, b) => a - b)
  return lapNumbers.filter((ln) => (lapNosWithData.has(ln)))
}

/** lapGridRows：周目ごとの表示行キャッシュ（変更のない周目は再計算をスキップ） */
let lapGridRowCache = new Map<number, { key: string; row: LapGridRow }>()

function buildLapGridRowCacheKey(lapNo: number, cards: ScheduleCard[], colCount: number): string {
  let key = `${lapNo}|${colCount}|${cards.length}`
  for (const c of cards) {
    key += `;${c.id}:${c.turn_seq}:${c.qty}:${c.product_cd}:${c.plating_machine}:${c.boardMark}`
  }
  return key
}

function buildLapGridRowFromCards(
  lapNo: number,
  cards: ScheduleCard[],
  colCount: number,
  lapDisplayNoValue: number,
): LapGridRow {
  const bins = binCardsIntoColumns(cards, colCount)
  const cells: LapGridCell[] = bins.map((bin) => ({
    segments: cardsToDisplaySegments(bin),
  }))
  const mergedLeft = cards.length > 0 ? buildMergedLeftSegments(cards, lapNo, colCount) : null
  const idsInMerged = new Set<string>()
  if (mergedLeft) {
    for (const seg of mergedLeft) {
      for (const id of seg.cardIds) idsInMerged.add(id)
    }
  }
  const mergedTail = cards.length > 0 ? cards.filter((c) => !idsInMerged.has(c.id)) : null
  const tailOnly = mergedTail != null && mergedTail.length > 0 ? mergedTail : null
  return {
    lap_no: lapNo,
    lap_display_no: lapDisplayNoValue,
    cells,
    mergedLeft,
    mergedTail: tailOnly,
  }
}

const lapGridRows = computed<LapGridRow[]>(() => {
  const n = lapBoardColCount.value
  const cardsByLap = boardOccupancyIndex.value.cardsByLapQty
  const displayNoMap = lapDisplayNoMap.value

  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))

  let lapNumbers = collectLapNumbersForBoardGrid(scheduleByLap)

  if (!layoutBoardReady.value) {
    lapNumbers = lapNumbers.filter((ln) => (cardsByLap.get(ln)?.length ?? 0) > 0)
  }
  if (lapNumbers.length === 0) {
    lapGridRowCache = new Map()
    return []
  }

  const nextCache = new Map<number, { key: string; row: LapGridRow }>()
  const rows: LapGridRow[] = []
  for (const lapNo of lapNumbers) {
    const cards = cardsByLap.get(lapNo) ?? []
    const cacheKey = buildLapGridRowCacheKey(lapNo, cards, n)
    const cached = lapGridRowCache.get(lapNo)
    if (cached?.key === cacheKey) {
      nextCache.set(lapNo, cached)
      rows.push(cached.row)
      continue
    }
    const row = buildLapGridRowFromCards(lapNo, cards, n, displayNoMap.get(lapNo) ?? lapNo)
    const entry = { key: cacheKey, row }
    nextCache.set(lapNo, entry)
    rows.push(row)
  }
  lapGridRowCache = nextCache
  return rows
})

/** 表示文字列のおおよその幅（ch）。CJK は 1 字 ≒ 1ch、ASCII は狭め */
function estimateTextWidthCh(text: string, fontScale = 1, padCh = 1.5): number {
  let ch = 0
  for (const c of String(text ?? '')) {
    ch += c.charCodeAt(0) > 0xff ? 1.08 : 0.58
  }
  return Math.ceil(ch * fontScale) + padCh
}

/** 列ヘッダー数字（縦並び）用の最小幅 */
function lapColHeaderWidthCh(colIndex: number): number {
  if (useCompactLapHeader.value) return MIN_LAP_COL_CH
  const digitCount = splitColumnNumberDigits(colIndex).length
  return Math.max(MIN_LAP_COL_CH, 0.62 + digitCount * 0.42)
}

function formatLapBoardGridColumns(widthsCh: number[]): string {
  return widthsCh
    .map((w) => {
      const wch = Math.max(MIN_LAP_COL_CH, Math.min(MAX_LAP_COL_CH, w))
      return `minmax(${wch.toFixed(1)}ch, ${wch.toFixed(1)}ch)`
    })
    .join(' ')
}

/** 治具ブロック／製品ラベルに必要な幅を列へ配分（同一列は最大値を採用） */
function computeLapBoardColumnWidthsCh(rows: LapGridRow[], colCount: number): number[] {
  const widths = Array.from({ length: colCount }, (_, i) => lapColHeaderWidthCh(i + 1))

  const applySpanNeed = (
    startCol: number,
    span: number,
    needTotalCh: number,
    opts?: { maxTotalCh?: number; maxPerColCh?: number },
  ) => {
    const start = Math.max(0, startCol - 1)
    const spanN = Math.max(1, Math.min(span, colCount - start))
    if (spanN <= 0) return
    let need = Math.max(MIN_LAP_COL_CH, needTotalCh)
    if (opts?.maxTotalCh != null) need = Math.min(need, opts.maxTotalCh)
    const current = widths.slice(start, start + spanN).reduce((a, b) => a + b, 0)
    if (need <= current + 0.02) return

    let perColCap = opts?.maxPerColCh ?? MAX_LAP_COL_CH
    const minPerCol = need / spanN
    if (opts?.maxTotalCh == null && minPerCol > perColCap) {
      perColCap = minPerCol
    }

    const targetPerCol = need / spanN
    for (let i = 0; i < spanN; i++) {
      widths[start + i] = Math.min(perColCap, Math.max(widths[start + i], targetPerCol))
    }
    if (opts?.maxTotalCh == null) {
      let sum = widths.slice(start, start + spanN).reduce((a, b) => a + b, 0)
      if (sum < need - 0.02) {
        const bump = (need - sum) / spanN
        for (let i = 0; i < spanN; i++) {
          widths[start + i] += bump
        }
      }
    }
  }

  for (const row of rows) {
    if (row.mergedLeft) {
      for (const ms of row.mergedLeft) {
        const needCh = estimateJigBlockLayoutNeedCh(ms, row.lap_no)
        const hasProducts = (buildJigBlockProductCalcParts(ms, row.lap_no)?.length ?? 0) > 0
        if (hasProducts) {
          applySpanNeed(ms.startCol, ms.span, needCh)
        } else {
          applySpanNeed(ms.startCol, ms.span, needCh, {
            maxTotalCh: MAX_LAP_JIG_BLOCK_TOTAL_CH,
            maxPerColCh: MAX_LAP_JIG_COL_CH,
          })
        }
      }
    }
    if (row.mergedTail) {
      for (const tc of row.mergedTail) {
        applySpanNeed(
          colCount,
          1,
          estimateTextWidthCh(formatPlatingBoardLabel(tc.product_name, 1), 1, 1.0),
        )
      }
    }
    if (!row.mergedLeft) {
      row.cells.forEach((cell, ci) => {
        for (const seg of cell.segments) {
          applySpanNeed(ci + 1, 1, estimateTextWidthCh(formatPlatingBoardLabel(seg.product_name, 1), 1, 1.0))
        }
      })
    }
  }

  for (let i = 0; i < colCount; i++) {
    if (useCompactLapHeader.value) break
    const no = i + 1
    const vis = visibleHeaderDigits(no, widths[i])
    const headerMin = Math.max(MIN_LAP_COL_CH, vis.length * 0.62 + 0.18)
    widths[i] = Math.max(headerMin, widths[i])
  }
  return widths
}

const lapBoardColumnWidthsCh = computed(() =>
  computeLapBoardColumnWidthsCh(lapGridRows.value, lapBoardColCount.value),
)

const lapColumnHeaders = computed(() => {
  const widths = lapBoardColumnWidthsCh.value
  const colCount = lapBoardColCount.value
  return Array.from({ length: colCount }, (_, i) => {
    const no = i + 1
    const w = widths[i] ?? lapColHeaderWidthCh(no)
    const digits = visibleHeaderDigits(no, w)
    const fullLen = splitColumnNumberDigits(no).length
    return { i: no, digits, truncated: digits.length < fullLen }
  })
})

/** 右側本数列は横スクロール、周列は各行で sticky 固定（列幅は製品名で自動調整） */
const lapBoardColsGridStyle = computed(() => ({
  gridTemplateColumns: formatLapBoardGridColumns(lapBoardColumnWidthsCh.value),
}))

/** 印刷：周列幅 + 本数列の合計 ch（A3 横向いっぱいに近づける） */
/** 画面周列 76px の 90% */
const PRINT_RAIL_COL_W = 'calc(76px * 0.9)'
const PRINT_BOARD_COLS_BUDGET_CH = 118

/** 画面列幅の比率を保ちつつ印刷幅へスケール */
function scaleWidthsToPrintBudget(screenWidths: number[], budgetCh: number): number[] {
  if (screenWidths.length === 0) return []
  const total = screenWidths.reduce((a, b) => a + b, 0) || 1
  const factor = budgetCh / total
  return screenWidths.map((w) => Math.max(0.28, w * factor))
}

/** 周目列：日付が変わる直前に日付区切り行を挿入 */
const lapBoardDisplayRows = computed<LapBoardDisplayItem[]>(() => {
  const laps = lapGridRows.value
  if (laps.length === 0) return []
  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const out: LapBoardDisplayItem[] = []
  let prevDate = ''
  for (const row of laps) {
    const slot = scheduleByLap.get(row.lap_no)
    const wd = slot?.work_date ?? layoutPlanDate.value
    if (wd && wd !== prevDate) {
      out.push({
        kind: 'date',
        key: `date-${wd}-${row.lap_no}`,
        work_date: wd,
        dateLabel: slot?.work_date_label ?? formatBoardDateLabel(wd),
      })
      prevDate = wd
    }
    out.push({ kind: 'lap', key: `lap-${row.lap_no}`, row })
  }
  return out
})

function refreshMarksAgainstStandardPositions() {
  const pos = standardPositions.value
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (c.boardMark === 'rush') return c
    const sp = pos.get(c.id)
    if (!sp) return { ...c, boardMark: 'manual' as BoardMark }
    if (sp.lap_no === c.lap_no && sp.turn_seq === c.turn_seq) return { ...c, boardMark: 'standard' as BoardMark }
    return { ...c, boardMark: 'manual' as BoardMark }
  })
}

/** DOM の列順（binCardsIntoColumns の逆）で周回内のカード順を読み取り、lap_no / turn_seq を更新 */
function readScheduleCardsFromBoardDom(): ScheduleCard[] | null {
  const n = lapBoardColCount.value
  const idToCard = new Map(scheduleCards.value.map((c) => [c.id, c]))
  const rows = [...document.querySelectorAll<HTMLElement>('.lap-board-body-row--lap')]
    .map((el) => ({ lap_no: Number(el.dataset.lapNo) || 0, el }))
    .filter((r) => r.lap_no > 0)
    .sort((a, b) => a.lap_no - b.lap_no)

  const out: ScheduleCard[] = []
  for (const { lap_no, el } of rows) {
    const tracks = [...el.querySelectorAll<HTMLElement>('.lap-track')]
    const cols: string[][] = tracks.map((t) =>
      [...t.querySelectorAll<HTMLElement>('.lap-segment[data-seg-key]')].map((node) => String(node.dataset.segKey || '').trim()).filter(Boolean),
    )
    for (let col = 0; col < Math.min(n, cols.length); col += 1) {
      const ids =
        col < n - 1
          ? (cols[col]?.[0] ? [cols[col]![0]] : [])
          : (cols[col] ?? [])
      ids.forEach((id, stackIdx) => {
        const c = idToCard.get(id)
        if (!c) return
        const turn = col < n - 1 ? col + 1 : n + stackIdx
        out.push({ ...c, lap_no, turn_seq: turn })
      })
    }
  }
  if (out.length === 0) return null
  return out
}

function syncScheduleOrderFromLapTracks() {
  const mapped = readScheduleCardsFromBoardDom()
  if (!mapped || mapped.length === 0) return
  const readIds = new Set(mapped.map((c) => c.id))
  const missing = scheduleCards.value.filter((c) => !readIds.has(c.id))
  scheduleCards.value = [...mapped, ...missing]
  refreshMarksAgainstStandardPositions()
}

function readOrderedCardIdsFromLapRow(lapEl: HTMLElement): string[] {
  const ids: string[] = []
  const host = lapEl.querySelector('.lap-merged-host')
  if (host) {
    host.querySelectorAll<HTMLElement>('.lap-merged-seg[data-block-ids]').forEach((seg) => {
      const raw = seg.dataset.blockIds || ''
      for (const id of raw.split(',')) {
        const t = id.trim()
        if (t) ids.push(t)
      }
    })
  }
  const tail = lapEl.querySelector('.lap-merged-tail')
  if (tail) {
    tail.querySelectorAll<HTMLElement>('.lap-merged-tail-item[data-card-id]').forEach((item) => {
      const id = item.dataset.cardId?.trim()
      if (id) ids.push(id)
    })
  }
  return ids
}

function syncScheduleOrderFromMergedRow(lapEl: HTMLElement, lapNo: number) {
  syncJigBlockOrderOnLap(lapEl, lapNo)
}

/** 同一周目：DOM 上の左→右順で turn_seq＝列番号（1 始まり）に同期 */
function syncJigBlockOrderOnLap(lapEl: HTMLElement, lapNo: number) {
  const host = lapEl.querySelector('.lap-merged-host')
  if (!host) return

  const lapCards = lapCardsWithQty(lapNo)
  const turnById = new Map<string, number>()
  let colCursor = 1
  const n = lapBoardColCount.value

  host.querySelectorAll<HTMLElement>('.lap-merged-seg[data-block-ids]').forEach((seg) => {
    const anchor = parseCardIdsFromDragItem(seg)[0]
    if (!anchor) return
    const fullIds = findJigBlockCardIds(anchor, lapNo)
    const block = lapCards
      .filter((c) => fullIds.includes(c.id))
      .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    for (const c of block) {
      turnById.set(c.id, colCursor)
      colCursor += 1
    }
  })

  const tail = lapEl.querySelector('.lap-merged-tail')
  if (tail) {
    tail.querySelectorAll<HTMLElement>('.lap-merged-tail-item[data-card-id]').forEach((item) => {
      const id = item.dataset.cardId?.trim()
      if (!id) return
      turnById.set(id, Math.max(n, colCursor))
      colCursor += 1
    })
  }

  if (turnById.size === 0) return

  scheduleCards.value = scheduleCards.value.map((c) => {
    const ts = turnById.get(c.id)
    return ts != null ? { ...c, turn_seq: ts } : c
  })
  refreshMarksAgainstStandardPositions()
}

function removeScheduleCard(id: string) {
  const next = scheduleCards.value.filter((c) => c.id !== id)
  const byLap = new Map<number, ScheduleCard[]>()
  for (const c of next) {
    const arr = byLap.get(c.lap_no) ?? []
    arr.push(c)
    byLap.set(c.lap_no, arr)
  }
  const out: ScheduleCard[] = []
  for (const lap of [...byLap.keys()].sort((a, b) => a - b)) {
    const sorted = (byLap.get(lap) ?? []).sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    sorted.forEach((c, i) => {
      out.push({ ...c, turn_seq: i + 1 })
    })
  }
  scheduleCards.value = out
  standardPositions.value.delete(id)
  refreshMarksAgainstStandardPositions()
  void flushBoardPersist()
}

let lapTrackSortables: Sortable[] = []
let lapMergedSortables: Sortable[] = []
const BOARD_JIG_SORTABLE_GROUP = 'plating-board-jig'

function destroyLapTrackSortables() {
  for (const s of lapTrackSortables) s.destroy()
  lapTrackSortables = []
}

function destroyLapMergedSortables() {
  for (const s of lapMergedSortables) s.destroy()
  lapMergedSortables = []
}

function parseCardIdsFromDragItem(el: HTMLElement): string[] {
  const raw = el.dataset.blockIds || el.dataset.cardIds || el.dataset.cardId || ''
  return raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

/** ドラッグ時は治具ブロック単位（同一周で連続する同機台）で cardIds を解決 */
function resolveDragBlockCardIds(el: HTMLElement, lapNo: number): string[] {
  const ids = parseCardIdsFromDragItem(el)
  if (lapNo <= 0 || ids.length === 0) return ids
  const blockIds = findJigBlockCardIds(ids[0], lapNo)
  return blockIds.length > 0 ? blockIds : ids
}

function initLapMergedSortables() {
  destroyLapMergedSortables()
  const hosts = Array.from(document.querySelectorAll<HTMLElement>('.lap-merged-host'))
  for (const host of hosts) {
    const row = host.closest<HTMLElement>('.lap-board-body-row')
    const lapNo = Number(row?.dataset.lapNo) || 0
    if (!row || lapNo <= 0) continue
    const s = Sortable.create(host, {
      animation: 120,
      group: {
        name: BOARD_JIG_SORTABLE_GROUP,
        pull: true,
        put: boardJigSortablePut,
      },
      sort: true,
      draggable: '.lap-merged-seg--board-jig-block',
      ghostClass: 'lap-merged-seg--ghost',
      onMove: boardJigSortableOnMove,
      onEnd: boardJigSortableOnEnd,
    })
    lapMergedSortables.push(s)
  }
}

function initBoardLapSortables() {
  if (scheduleCards.value.some((c) => c.qty > 0)) {
    destroyLapTrackSortables()
    initLapMergedSortables()
  } else {
    destroyLapMergedSortables()
    initLapTrackSortables()
  }
}

function scheduleInitBoardLapSortables() {
  if (suppressScheduleSideEffects > 0) return
  if (isBoardHydratingFromApi.value || loadingDraft.value) return
  if (lapSortableInitTimer != null) clearTimeout(lapSortableInitTimer)
  lapSortableInitTimer = setTimeout(() => {
    lapSortableInitTimer = null
    initBoardLapSortables()
  }, 160)
}

function cancelLapSortableInitTimer() {
  if (lapSortableInitTimer != null) {
    clearTimeout(lapSortableInitTimer)
    lapSortableInitTimer = null
  }
}

function scheduleBoardReactiveSideEffects() {
  if (suppressScheduleSideEffects > 0) return
  if (isBoardHydratingFromApi.value || loadingDraft.value) return
  if (boardReactiveEffectsTimer != null) clearTimeout(boardReactiveEffectsTimer)
  boardReactiveEffectsTimer = setTimeout(() => {
    boardReactiveEffectsTimer = null
    scheduleInitBoardLapSortables()
    scheduleBoardAutosave()
  }, BOARD_REACTIVE_EFFECTS_MS)
}

function cancelBoardReactiveEffectsTimer() {
  if (boardReactiveEffectsTimer != null) {
    clearTimeout(boardReactiveEffectsTimer)
    boardReactiveEffectsTimer = null
  }
}

function initLapTrackSortables() {
  destroyLapTrackSortables()
  const tracks = Array.from(document.querySelectorAll<HTMLElement>('.lap-track'))
  for (const t of tracks) {
    const s = Sortable.create(t, {
      animation: 120,
      group: 'lap-bars',
      draggable: '.lap-segment',
      onEnd: () => {
        nextTick(() => {
          syncScheduleOrderFromLapTracks()
          void flushBoardPersist()
        })
      },
    })
    lapTrackSortables.push(s)
  }
}

interface PrintScheduleRange {
  startDate: string
  startLapDisplay: number
  endDate: string
  endLapDisplay: number
}

const printScheduleDialogVisible = ref(false)
const printStartDate = ref('')
const printStartLap = ref(1)
const printEndDate = ref('')
const printEndLap = ref(1)

function printRangeSortKey(workDate: string, lapDisplay: number): number {
  const d = String(workDate || '').slice(0, 10).replace(/-/g, '')
  const n = Math.max(1, Math.floor(Number(lapDisplay) || 1))
  return Number(d || '0') * 10000 + n
}

function normalizePrintScheduleRange(range: PrintScheduleRange): PrintScheduleRange {
  const a = printRangeSortKey(range.startDate, range.startLapDisplay)
  const b = printRangeSortKey(range.endDate, range.endLapDisplay)
  if (a <= b) return range
  return {
    startDate: range.endDate,
    startLapDisplay: range.endLapDisplay,
    endDate: range.startDate,
    endLapDisplay: range.startLapDisplay,
  }
}

function isLapInPrintScheduleRange(lapNo: number, range: PrintScheduleRange): boolean {
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  const slot = scheduleByLap.get(lapNo)
  const wd = slot?.work_date ?? layoutPlanDate.value
  const display = lapDisplayNo(lapNo)
  const key = printRangeSortKey(wd, display)
  const norm = normalizePrintScheduleRange(range)
  const lo = printRangeSortKey(norm.startDate, norm.startLapDisplay)
  const hi = printRangeSortKey(norm.endDate, norm.endLapDisplay)
  return key >= lo && key <= hi
}

function printLapOptionsForDate(ymd: string): Array<{ value: number; label: string }> {
  const d = String(ymd || '').slice(0, 10)
  if (!d) return []
  return currentLayoutLapSchedule()
    .filter((s) => s.work_date === d)
    .sort((a, b) => a.lap_no - b.lap_no)
    .map((s) => {
      const no = lapDisplayNo(s.lap_no)
      return {
        value: no,
        label: `第${no}周目（${s.start}〜${s.end}）`,
      }
    })
}

const printScheduleAvailableDates = computed(() => {
  const set = new Set<string>()
  for (const s of currentLayoutLapSchedule()) {
    if (s.work_date) set.add(s.work_date)
  }
  return [...set].sort()
})

function printScheduleDateDisabled(date: Date): boolean {
  const ymd = dayjs(date).format('YYYY-MM-DD')
  const avail = printScheduleAvailableDates.value
  if (avail.length === 0) return false
  return !avail.includes(ymd)
}

const printStartLapOptions = computed(() => printLapOptionsForDate(printStartDate.value))
const printEndLapOptions = computed(() => printLapOptionsForDate(printEndDate.value))

const printRangePreviewLabel = computed(() => {
  if (!printStartDate.value || !printEndDate.value) return ''
  const norm = normalizePrintScheduleRange({
    startDate: printStartDate.value,
    startLapDisplay: printStartLap.value,
    endDate: printEndDate.value,
    endLapDisplay: printEndLap.value,
  })
  return `印刷範囲：${formatBoardDateLabel(norm.startDate)} 第${norm.startLapDisplay}周目 〜 ${formatBoardDateLabel(norm.endDate)} 第${norm.endLapDisplay}周目`
})

function syncPrintLapToDateOptions() {
  const startOpts = printStartLapOptions.value
  if (startOpts.length > 0 && !startOpts.some((o) => o.value === printStartLap.value)) {
    printStartLap.value = startOpts[0].value
  }
  const endOpts = printEndLapOptions.value
  if (endOpts.length > 0 && !endOpts.some((o) => o.value === printEndLap.value)) {
    printEndLap.value = endOpts[endOpts.length - 1].value
  }
}

function onPrintScheduleDialogOpened() {
  syncPrintLapToDateOptions()
}

function openPrintScheduleDialog() {
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  const schedule = currentLayoutLapSchedule()
  if (schedule.length === 0) {
    ElMessage.warning('印刷対象の周目がありません')
    return
  }
  const { from, to } = boardViewRange.value
  printStartDate.value = from
  printEndDate.value = to
  const startSlots = schedule.filter((s) => s.work_date === from).sort((a, b) => a.lap_no - b.lap_no)
  const endSlots = schedule.filter((s) => s.work_date === to).sort((a, b) => a.lap_no - b.lap_no)
  printStartLap.value = startSlots.length > 0 ? lapDisplayNo(startSlots[0].lap_no) : 1
  printEndLap.value = endSlots.length > 0 ? lapDisplayNo(endSlots[endSlots.length - 1].lap_no) : 1
  printScheduleDialogVisible.value = true
  nextTick(() => syncPrintLapToDateOptions())
}

function buildLapBoardDisplayRowsForPrint(range: PrintScheduleRange): LapBoardDisplayItem[] {
  const norm = normalizePrintScheduleRange(range)
  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const laps = lapGridRows.value.filter((row) => isLapInPrintScheduleRange(row.lap_no, norm))
  if (laps.length === 0) return []
  const out: LapBoardDisplayItem[] = []
  let prevDate = ''
  for (const row of laps) {
    const slot = scheduleByLap.get(row.lap_no)
    const wd = slot?.work_date ?? layoutPlanDate.value
    if (wd && wd !== prevDate) {
      out.push({
        kind: 'date',
        key: `date-${wd}-${row.lap_no}`,
        work_date: wd,
        dateLabel: slot?.work_date_label ?? formatBoardDateLabel(wd),
      })
      prevDate = wd
    }
    out.push({ kind: 'lap', key: `lap-${row.lap_no}`, row })
  }
  return out
}

function hasPrintableScheduleInRange(range: PrintScheduleRange): boolean {
  const norm = normalizePrintScheduleRange(range)
  return scheduleCards.value.some((c) => num(c.qty) > 0 && isLapInPrintScheduleRange(c.lap_no, norm))
}

function totalProductionQtyForPrintRange(range: PrintScheduleRange): number {
  const norm = normalizePrintScheduleRange(range)
  return scheduleCards.value.reduce((sum, c) => {
    if (num(c.qty) <= 0 || !isLapInPrintScheduleRange(c.lap_no, norm)) return sum
    return sum + cardProductProductionQty(c)
  }, 0)
}

function confirmPrintSchedule() {
  if (!printStartDate.value || !printEndDate.value) {
    ElMessage.warning('開始日と終了日を指定してください')
    return
  }
  const range = normalizePrintScheduleRange({
    startDate: printStartDate.value,
    startLapDisplay: Math.max(1, Math.floor(Number(printStartLap.value) || 1)),
    endDate: printEndDate.value,
    endLapDisplay: Math.max(1, Math.floor(Number(printEndLap.value) || 1)),
  })
  const displayRows = buildLapBoardDisplayRowsForPrint(range)
  if (displayRows.length === 0) {
    ElMessage.warning('選択期間に表示する周目がありません')
    return
  }
  if (!hasPrintableScheduleInRange(range)) {
    ElMessage.warning('選択期間に印刷できる割当データがありません')
    return
  }
  printScheduleDialogVisible.value = false
  executePrintScheduleBoard(displayRows, range)
}

watch([printStartDate, printEndDate], () => {
  if (!printScheduleDialogVisible.value) return
  syncPrintLapToDateOptions()
})

function escapeHtmlForPrint(s: string): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** A3 横向（420×297mm）・印刷余白（上下 1cm、左右 0.7cm） */
const PRINT_A3_PAGE_W_MM = 420
const PRINT_A3_PAGE_H_MM = 297
/** 印刷余白：左右 4mm、上 0.3cm（3mm）、下 0 */
const PRINT_A3_PAD_X_MM = 4
const PRINT_A3_PAD_TOP_MM = 3
const PRINT_A3_PAD_BOTTOM_MM = 0
/** 印刷ボード行高（基準比：97% × 95% × 97% ≈ 89.4%） */
const PRINT_ROW_HEIGHT_MUL = 0.97 * 0.95 * 0.97

/** 印刷ページ内に収めて 1 ページ化（上揃え・列幅比率は維持、はみ出し時はフォント縮小→transform） */
function fitPrintBoardToOnePage(win: Window): void {
  const doc = win.document
  const page = doc.querySelector<HTMLElement>('.print-page')
  const root = doc.querySelector<HTMLElement>('.print-fit-root')
  if (!page || !root) return

  const clearFit = () => {
    root.style.transform = ''
    root.style.width = ''
    root.style.height = ''
  }

  const pageW = page.clientWidth
  const pageH = page.clientHeight
  if (pageW < 1 || pageH < 1) return

  clearFit()
  let fontMul = 1
  root.style.setProperty('--print-font-mul', '1')

  const measure = () => ({ w: root.scrollWidth, h: root.scrollHeight })
  let { w: contentW, h: contentH } = measure()
  if (contentW < 1 || contentH < 1) return

  const minFontMul = 0.48
  for (let i = 0; i < 28 && (contentW > pageW || contentH > pageH) && fontMul > minFontMul; i++) {
    const ratio = Math.min(pageW / contentW, pageH / contentH) * 0.97
    fontMul = Math.max(minFontMul, fontMul * ratio)
    root.style.setProperty('--print-font-mul', String(fontMul))
    clearFit()
    ;({ w: contentW, h: contentH } = measure())
  }

  let scale = Math.min(pageW / contentW, pageH / contentH)
  const scaleFillW = pageW / contentW
  if (scaleFillW > scale && scaleFillW * contentH <= pageH * 0.995) {
    scale = scaleFillW
  }
  const scaledW = contentW * scale
  const offsetX = Math.max(0, (pageW - scaledW) / 2)
  const offsetY = 0

  root.style.transformOrigin = 'top left'
  root.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`
  root.style.width = `${contentW}px`
  root.style.height = `${contentH}px`
}


function boardMarkSegClass(m: BoardMark, merged: boolean): string {
  if (m === 'manual') return merged ? 'lap-merged-seg--manual' : 'lap-segment--manual'
  if (m === 'rush') return merged ? 'lap-merged-seg--rush' : 'lap-segment--rush'
  return ''
}

function buildLapBoardRowGridPrintHtml(row: LapGridRow, n: number, gridCols: string): string {
  if (row.mergedLeft != null) {
    const leftSegs = row.mergedLeft
      .map((ms) => {
        const inner = buildJigBlockPrintStackHtml(ms, row.lap_no)
        return `<div class="lap-merged-seg lap-merged-seg--print-jig" style="grid-column:${ms.startCol} / span ${ms.span};grid-row:1"><div class="lap-merged-label-stack lap-merged-label-stack--print-4">${inner}</div></div>`
      })
      .join('')
    let tailHtml = ''
    const tail = row.mergedTail
    if (tail != null && tail.length > 0) {
      const items = tail
        .map((tc) => {
          const ci = schedColorIndexForPlatingMachine(tc.plating_machine)
          const mk = boardMarkSegClass(tc.boardMark, true)
          return `<div class="lap-merged-tail-item sched-color-${ci} ${mk}"><span class="lap-merged-text">${escapeHtmlForPrint(
            formatPlatingBoardLabel(tc.product_name, 1),
          )}</span></div>`
        })
        .join('')
      tailHtml = `<div class="lap-merged-tail" style="grid-column:${n} / span 1;grid-row:1">${items}</div>`
    }
    return `<div class="lap-merged-host" style="${gridCols}">${leftSegs}${tailHtml}</div>`
  }

  const cells = row.cells
    .map((cell) => {
      const segs = cell.segments
        .map((seg) => {
          const ci = schedColorIndexForPlatingMachine(seg.plating_machine)
          const mk = boardMarkSegClass(seg.boardMark, false)
          return `<div class="lap-segment lap-segment--cell sched-color-${ci} ${mk}" style="flex:${seg.slotCount}"><span class="lap-segment-text">${escapeHtmlForPrint(
            formatPlatingBoardLabel(seg.product_name, 1),
          )}</span></div>`
        })
        .join('')
      const empty = cell.segments.length === 0 ? ' lap-col--empty' : ''
      return `<div class="lap-col${empty}"><div class="lap-track lap-track--grid">${segs}</div></div>`
    })
    .join('')
  return cells
}

/** 画面と同じ lap-board-layout 構造で印刷 HTML を組み立てる */
function buildPrintBoardLayoutHtml(displayRows: LapBoardDisplayItem[], n: number, colWidths: number[]): string {
  const cols = formatLapBoardGridColumns(colWidths)
  const gridCols = `grid-template-columns:${cols}`

  const headCols = useCompactLapHeader.value
    ? `<div class="lap-col-head-range">${buildCompactHeaderMarksHtml(n, colWidths)}</div>`
    : Array.from({ length: n }, (_, i) => {
        const no = i + 1
        const w = colWidths[i] ?? lapColHeaderWidthCh(no)
        return buildLapColumnHeadHtml(no, w)
      }).join('')

  const headRow = `<div class="lap-board-row lap-board-row--head">
    <div class="lap-rail-cell lap-rail-head">周</div>
    <div class="lap-board-grid lap-board-head" style="${gridCols}">${headCols}</div>
  </div>`

  const body = displayRows
    .map((item) => {
      if (item.kind === 'date') {
        const memo = getBoardDateMemo(item.work_date)
        const memoHtml = memo
          ? `<span class="lap-date-memo-text">${escapeHtmlForPrint(memo)}</span>`
          : ''
        return `<div class="lap-board-row lap-board-row--date">
          <div class="lap-rail-cell lap-rail-date">${escapeHtmlForPrint(item.dateLabel)}</div>
          <div class="lap-board-grid lap-board-date-row lap-date-scroll-row" style="${gridCols}">
            <div class="lap-date-band-scroll lap-date-memo-zone">${memoHtml}</div>
          </div>
        </div>`
      }
      const row = item.row
      const timeLbl = lapTimeRangeLabel(row.lap_no)
      const lapNoHtml = `<span class="lap-label-no">第${row.lap_display_no}周目</span>`
      const timeHtml = timeLbl ? `<span class="lap-label-time">${escapeHtmlForPrint(timeLbl)}</span>` : ''
      return `<div class="lap-board-row lap-board-row--lap">
        <div class="lap-rail-cell lap-rail-lap">${lapNoHtml}${timeHtml}</div>
        <div class="lap-board-grid lap-board-body-row lap-board-body-row--lap" style="${gridCols}">
          ${buildLapBoardRowGridPrintHtml(row, n, gridCols)}
        </div>
      </div>`
    })
    .join('')

  return `<div class="lap-board-layout">${headRow}${body}</div>`
}

function formatPrintScheduleRangeLabel(range: PrintScheduleRange): string {
  const norm = normalizePrintScheduleRange(range)
  return `${formatBoardDateLabel(norm.startDate)} 第${norm.startLapDisplay}周目 〜 ${formatBoardDateLabel(norm.endDate)} 第${norm.endLapDisplay}周目`
}

function executePrintScheduleBoard(displayRows: LapBoardDisplayItem[], range: PrintScheduleRange) {
  const workDate = draftWorkDate.value || '—'
  const printedAt = dayjs().tz(TZ_JP).format('YYYY-MM-DD HH:mm:ss')
  const productionTotalLabel = `生産数合計：${formatQtyDisplay(totalProductionQtyForPrintRange(range))}`

  const n = lapBoardColCount.value
  const printColWidths = scaleWidthsToPrintBudget(lapBoardColumnWidthsCh.value.slice(0, n), PRINT_BOARD_COLS_BUDGET_CH)
  const boardLayoutHtml = buildPrintBoardLayoutHtml(displayRows, n, printColWidths)

  const innerW = PRINT_A3_PAGE_W_MM - PRINT_A3_PAD_X_MM * 2
  const innerH = PRINT_A3_PAGE_H_MM - PRINT_A3_PAD_TOP_MM - PRINT_A3_PAD_BOTTOM_MM

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8"/>
  <title>メッキ投入スケジュール ${escapeHtmlForPrint(workDate)}</title>
  <style>
    html {
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
      --print-row-mul: ${PRINT_ROW_HEIGHT_MUL};
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0; padding: 0; width: ${PRINT_A3_PAGE_W_MM}mm; height: ${PRINT_A3_PAGE_H_MM}mm;
      overflow: hidden; background: #fff;
    }
    body {
      font-family: 'Segoe UI', 'Hiragino Sans', Meiryo, sans-serif;
      color: #303133;
      font-size: calc(8pt * var(--print-font-mul, 1));
    }
    .print-page {
      width: ${innerW}mm; height: ${innerH}mm;
      margin: ${PRINT_A3_PAD_TOP_MM}mm ${PRINT_A3_PAD_X_MM}mm ${PRINT_A3_PAD_BOTTOM_MM}mm;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: flex-start;
    }
    .print-fit-root { display: block; width: max-content; max-width: none; flex-shrink: 0; }
    .print-header-block {
      margin-bottom: 2mm;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 4px 10px;
      width: 100%;
    }
    .print-title {
      margin: 0; font-size: 11pt; font-weight: 700; color: #303133; line-height: 1.2;
      flex-shrink: 0;
    }
    .print-meta {
      margin: 0; font-size: 7pt; color: #606266; line-height: 1.25;
      display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: baseline;
      gap: 0 10px; flex: 1 1 auto; text-align: right;
    }
    .print-meta span { display: inline-block; white-space: nowrap; }
    .lap-board { padding: 0; border: 1px solid #d9deea; border-radius: 6px; background: #fff; }
    .lap-board,
    .lap-board * {
      font-weight: 400 !important;
    }
    .lap-board-layout { display: flex; flex-direction: column; width: max-content; }
    .lap-board-row {
      display: grid; grid-template-columns: ${PRINT_RAIL_COL_W} max-content;
      align-items: stretch; border-bottom: 1px solid #ebeef5;
    }
    .lap-board-row:last-child { border-bottom: none; }
    .lap-rail-cell {
      display: flex; flex-direction: column; align-items: flex-end; justify-content: center;
      gap: 1px; padding: 2px 4px; border-right: 1px solid #ebeef5; background: #fff;
    }
    .lap-rail-head {
      align-items: center; justify-content: center;
      font-size: calc(7pt * var(--print-font-mul, 1)); font-weight: 400;
      color: #606266; background: #f5f7fa;
    }
    .lap-rail-date {
      font-size: calc(9pt * var(--print-font-mul, 1)); font-weight: 400; color: #1f5fd6;
      background: color-mix(in oklab, #ecf5ff 90%, #fff);
    }
    .lap-rail-lap {
      font-size: calc(8pt * var(--print-font-mul, 1)); font-weight: 400; color: #606266;
    }
    .lap-label-no { white-space: nowrap; }
    .lap-label-time {
      font-size: calc(7pt * var(--print-font-mul, 1)); font-weight: 400; color: #1f5fd6; white-space: nowrap;
    }
    .lap-board-grid {
      display: grid; align-items: stretch; gap: 0; width: max-content; box-sizing: border-box;
    }
    .lap-board-head { background: #f5f7fa; min-height: calc(18px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894)); }
    .lap-board-body-row--lap { min-height: calc(24px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894)); background: #fff; }
    .lap-board-date-row,
    .lap-date-scroll-row {
      background: color-mix(in oklab, #ecf5ff 85%, #fff);
      min-height: calc(20px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
    }
    .lap-date-band-scroll {
      grid-column: 1 / -1; min-height: calc(20px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
      background: color-mix(in oklab, #ecf5ff 55%, #fff);
    }
    .lap-col-head {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 0; line-height: 1; padding: 1px 1px;
      font-size: calc(6pt * var(--print-font-mul, 1)); font-weight: 400; color: #909399;
      border-right: 1px solid #ebeef5; background: #f5f7fa;
    }
    .lap-col-head-range {
      grid-column: 1 / -1;
      position: relative;
      display: block;
      font-size: calc(6pt * var(--print-font-mul, 1));
      font-weight: 400;
      color: #1f5fd6;
      line-height: 1;
      padding: 1px 3px;
      border-right: none;
      background: #f5f7fa;
      min-height: calc(18px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
      border-top: 1px solid #cddfff;
    }
    .lap-col-head-range-mark {
      position: absolute;
      top: 50%;
      transform: translate(-50%, -50%);
      display: inline-block;
      min-width: 1ch;
      text-align: center;
      white-space: nowrap;
      text-shadow: 0 1px 0 rgba(255, 255, 255, 0.75);
    }
    .lap-col-head-digits { display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 0; }
    .lap-col-head-digit { font-size: calc(6pt * var(--print-font-mul, 1)); font-weight: 400; font-variant-numeric: tabular-nums; line-height: 1; color: #1f5fd6; }
    .lap-board-grid > *:last-child { border-right: none; }
    .lap-merged-host {
      grid-column: 1 / -1; display: grid; align-items: stretch; min-height: calc(30px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
      box-sizing: border-box; overflow: hidden;
    }
    .lap-merged-seg,
    .lap-merged-seg--print-jig,
    .lap-merged-host .lap-merged-seg {
      position: relative; min-width: 0; max-width: 100%;
      padding: 2px 3px; margin: 1px 0; box-sizing: border-box;
      border: 0.5pt solid #000 !important;
      border-radius: 2px;
      overflow: hidden;
      background: #fff !important;
      box-shadow: none !important;
      outline: none !important;
    }
    .lap-merged-seg--manual,
    .lap-merged-seg--rush,
    .lap-merged-seg--print-jig.lap-merged-seg--manual,
    .lap-merged-seg--print-jig.lap-merged-seg--rush {
      outline: none !important;
      border: 0.5pt solid #000 !important;
      background: #fff !important;
    }
    .lap-merged-label-stack {
      position: absolute; top: 1px; right: 2px; left: 2px; bottom: 1px;
      display: flex; flex-direction: column; align-items: stretch; gap: 1px; overflow: hidden;
      pointer-events: none;
    }
    .lap-merged-label-stack--print-4 {
      justify-content: flex-start;
      gap: 0;
    }
    .lap-print-layer {
      line-height: 1.12;
      font-weight: 400;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: clip;
      padding: 0 2px;
      box-sizing: border-box;
      width: 100%;
      font-size: calc(4.5pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--right {
      text-align: right;
      align-self: flex-end;
      color: #000;
    }
    .lap-print-layer--left {
      text-align: left;
      align-self: flex-start;
      color: #1f5fd6;
    }
    .lap-print-layer--jig-name {
      font-size: calc(4pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--jig-qty {
      font-size: calc(4pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--prod-name {
      font-size: calc(5pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--prod-qty {
      font-size: calc(4pt * var(--print-font-mul, 1));
    }
    .lap-print-prod--alt {
      color: #cf1322 !important;
      font-weight: 400 !important;
    }
    .lap-print-prod--depleted {
      color: #cf1322 !important;
      font-weight: 600 !important;
    }
    .lap-print-prod--force-red {
      color: #cf1322 !important;
      font-weight: 700 !important;
    }
    .lap-print-prod-sep {
      color: #303133;
      font-weight: 400;
    }
    .lap-merged-text { line-height: 1.15; font-weight: 400; color: #303133; font-size: calc(5pt * var(--print-font-mul, 1)); }
    .lap-merged-tail {
      display: flex; flex-direction: column; gap: 1px; min-width: 0; max-width: 100%; padding: 1px;
      box-sizing: border-box; border-left: 1px solid #ebeef5; overflow: hidden;
    }
    .lap-merged-tail-item {
      position: relative; flex: 0 0 auto; min-width: 0; max-width: 100%; min-height: 16px;
      padding: 1px 2px; border-radius: 3px; border: 0.5px solid rgba(48,67,96,0.2); box-sizing: border-box; overflow: hidden;
    }
    .lap-merged-tail-item .lap-merged-text { display: block; width: 100%; box-sizing: border-box; }
    .lap-col {
      min-width: 0; max-width: 100%; border-right: 1px solid #ebeef5; padding: 1px;
      display: flex; flex-direction: column; box-sizing: border-box; overflow: hidden;
    }
    .lap-col--empty .lap-track--grid { opacity: 0.55; }
    .sched-color-0 { background: #dbe8d4; }
    .sched-color-1 { background: #c9dce8; }
    .sched-color-2 { background: #edd9c8; }
    .sched-color-3 { background: #d4cce8; }
    .sched-color-4 { background: #c9e4df; }
    .sched-color-5 { background: #e5d9b8; }
    .sched-color-6 { background: #cdd5e0; }
    .sched-color-7 { background: #e0cfcf; }
    .sched-color-8 { background: #d7e7f8; }
    .sched-color-9 { background: #d8f0e2; }
    .sched-color-10 { background: #f8e3d4; }
    .sched-color-11 { background: #e6dcf8; }
    .sched-color-12 { background: #d6ecef; }
    .sched-color-13 { background: #f2e6c9; }
    .sched-color-14 { background: #d8dbe9; }
    .sched-color-15 { background: #f0dadd; }
    .sched-color-16 { background: #d4eaf0; }
    .sched-color-17 { background: #e2edd4; }
    .sched-color-18 { background: #f3dfcf; }
    .sched-color-19 { background: #ddd5ee; }
    .sched-color-20 { background: #cfe8e2; }
    .sched-color-21 { background: #ece2bf; }
    .sched-color-22 { background: #d3d9e6; }
    .sched-color-23 { background: #ebd8d8; }
    .lap-track--grid {
      flex: 1; display: flex; flex-direction: column; min-height: 12px; gap: 1px;
      border-radius: 3px; overflow: hidden; background: #f5f7fa;
    }
    .lap-segment--cell {
      position: relative; min-width: 0; max-width: 100%; min-height: 16px; padding: 1px 2px; border-radius: 2px; overflow: hidden;
    }
    .lap-segment--manual { outline: 2px solid #fa8c16; outline-offset: -1px; z-index: 1; }
    .lap-segment--rush { outline: 2px solid #cf1322; outline-offset: -1px; z-index: 1; }
    .lap-segment-text {
      display: block; font-size: calc(5pt * var(--print-font-mul, 1)); line-height: 1.15;
      text-align: right; white-space: nowrap; overflow: hidden; text-overflow: clip;
      font-weight: 400; box-sizing: border-box;
    }
    @media print {
      @page { size: A3 landscape; margin: ${PRINT_A3_PAD_TOP_MM}mm ${PRINT_A3_PAD_X_MM}mm ${PRINT_A3_PAD_BOTTOM_MM}mm; }
      html, body {
        margin: 0 !important; padding: 0 !important;
        width: ${PRINT_A3_PAGE_W_MM}mm !important; height: ${PRINT_A3_PAGE_H_MM}mm !important;
        overflow: hidden !important;
      }
      * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      .print-page {
        width: ${innerW}mm !important; height: ${innerH}mm !important;
        margin: ${PRINT_A3_PAD_TOP_MM}mm ${PRINT_A3_PAD_X_MM}mm ${PRINT_A3_PAD_BOTTOM_MM}mm !important; overflow: hidden !important;
        page-break-after: avoid; page-break-inside: avoid;
      }
      .print-fit-root, .print-board-target, .lap-board, .lap-board-layout, .lap-board-grid {
        page-break-inside: avoid;
      }
      .lap-merged-host .lap-merged-seg,
      .lap-merged-seg--print-jig {
        border: 0.5pt solid #000 !important;
        outline: none !important;
        background: #fff !important;
        box-shadow: none !important;
      }
      .lap-board,
      .lap-board * {
        font-weight: 400 !important;
      }
    }
  </style>
</head>
<body>
  <div class="print-page">
    <div class="print-fit-root">
      <div class="print-header-block">
        <h1 class="print-title">メッキ投入ボード</h1>
        <div class="print-meta">
          <span>作業日：${escapeHtmlForPrint(workDate)}</span>
          <span>印刷日時：${escapeHtmlForPrint(printedAt)}</span>
          <span>${escapeHtmlForPrint(productionTotalLabel)}</span>
        </div>
      </div>
      <div class="print-board-target">
        <div class="lap-board">${boardLayoutHtml}</div>
      </div>
    </div>
  </div>
</body>
</html>`

  /**
   * window.open + document.write は環境によって印刷プレビューが真っ白になることがある。
   * 実寸の離屏 iframe に書き込み、load／readyState 後に print する。
   */
  const iframe = document.createElement('iframe')
  iframe.setAttribute('aria-hidden', 'true')
  iframe.title = 'メッキ投入スケジュール印刷'
  iframe.style.cssText = [
    'position:fixed',
    'left:-20000px',
    'top:0',
    `width:${PRINT_A3_PAGE_W_MM}mm`,
    `height:${PRINT_A3_PAGE_H_MM}mm`,
    'border:0',
    'opacity:0',
    'pointer-events:none',
    'z-index:-1',
  ].join(';')

  document.body.appendChild(iframe)

  const doc = iframe.contentDocument
  const win = iframe.contentWindow
  if (!doc || !win) {
    iframe.remove()
    ElMessage.error('印刷の準備に失敗しました')
    return
  }

  const removeIframe = () => {
    try {
      iframe.remove()
    } catch {
      /* ignore */
    }
  }

  let printed = false
  const doPrint = () => {
    if (printed) return
    printed = true
    try {
      fitPrintBoardToOnePage(win)
      win.focus()
      win.print()
    } catch {
      /* ignore */
    }
    win.addEventListener('afterprint', removeIframe, { once: true })
    window.setTimeout(removeIframe, 4000)
  }

  const schedulePrint = () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.setTimeout(doPrint, 50)
      })
    })
  }

  /** write の前に登録しないと load を取りこぼす場合がある */
  iframe.addEventListener('load', schedulePrint, { once: true })

  doc.open()
  doc.write(html)
  doc.close()

  if (doc.readyState === 'complete') {
    window.setTimeout(schedulePrint, 0)
  }
  window.setTimeout(() => {
    if (!printed) schedulePrint()
  }, 400)
}

/** 製品枠の生産数量（qty × 掛け数）。治具のみ枠は 0 */
function cardProductProductionQty(c: ScheduleCard): number {
  if (isJigProductCd(c.product_cd) || isEmptySlotProductCd(c.product_cd)) return 0
  const q = Math.max(0, Math.floor(num(c.qty)))
  const k = c.kake > 0 ? c.kake : 1
  return q * k
}

interface ProductionListTimePeriod {
  lap_no: number
  lap_display_no: number
  time_label: string
  /** 当該周目における当該製品の生産数（qty × 掛け数の合計） */
  production_qty: number
}

interface ProductionListRow {
  product_cd: string
  product_name: string
  production_qty: number
  time_periods: ProductionListTimePeriod[]
}

interface ProductionListDayGroup {
  work_date: string
  work_date_label: string
  rows: ProductionListRow[]
  rows_left: ProductionListRow[]
  rows_right: ProductionListRow[]
  total_production_qty: number
}

/** 品種一覧を前半・後半の2列用に分割（奇数時は左列が1件多い） */
function splitProductionListRows(rows: ProductionListRow[]): [ProductionListRow[], ProductionListRow[]] {
  const mid = Math.ceil(rows.length / 2)
  return [rows.slice(0, mid), rows.slice(mid)]
}

interface ProductionListProductAgg {
  product_cd: string
  product_name: string
  production_qty: number
  time_periods: ProductionListTimePeriod[]
}

function productionListTimePeriodForLap(
  lapNo: number,
  lapDisplayNo: number,
  productionQty: number,
): ProductionListTimePeriod {
  return {
    lap_no: lapNo,
    lap_display_no: lapDisplayNo,
    time_label: lapTimeRangeLabel(lapNo) || '—',
    production_qty: Math.max(0, Math.floor(Number(productionQty) || 0)),
  }
}

function mergeProductionListTimePeriods(
  a: ProductionListTimePeriod[],
  b: ProductionListTimePeriod[],
): ProductionListTimePeriod[] {
  const map = new Map<number, ProductionListTimePeriod>()
  for (const t of a) map.set(t.lap_no, { ...t })
  for (const t of b) {
    const cur = map.get(t.lap_no)
    if (cur) {
      cur.production_qty += t.production_qty
    } else {
      map.set(t.lap_no, { ...t })
    }
  }
  return [...map.values()].sort((x, y) => x.lap_no - y.lap_no)
}

function collectProductionProductAggsFromJigBlock(ms: LapMergedSegment): ProductionListProductAgg[] {
  const blockCards = getMergedSegCards(ms)
  const productCards = blockCards.filter((c) => !isJigProductCd(c.product_cd))
  if (productCards.length === 0) return []
  const byProd = new Map<string, ScheduleCard[]>()
  for (const c of productCards) {
    const list = byProd.get(c.product_cd) ?? []
    list.push(c)
    byProd.set(c.product_cd, list)
  }
  const rows: ProductionListProductAgg[] = []
  for (const [productCd, prodCards] of byProd.entries()) {
    const first = prodCards[0]
    const productionQty = prodCards.reduce((s, c) => s + cardProductProductionQty(c), 0)
    if (productionQty <= 0) continue
    rows.push({
      product_cd: productCd,
      product_name: String(first.product_name || first.product_cd || '').trim() || '—',
      production_qty: productionQty,
      time_periods: [],
    })
  }
  return rows
}

function collectProductionProductAggsFromLooseCards(lapNo: number, cards: ScheduleCard[]): ProductionListProductAgg[] {
  const productCards = cards
    .filter((c) => c.qty > 0 && c.lap_no === lapNo && !isJigProductCd(c.product_cd))
  if (productCards.length === 0) return []
  const byProd = new Map<string, ScheduleCard[]>()
  for (const c of productCards) {
    const list = byProd.get(c.product_cd) ?? []
    list.push(c)
    byProd.set(c.product_cd, list)
  }
  const rows: ProductionListProductAgg[] = []
  for (const [productCd, prodCards] of byProd.entries()) {
    const first = prodCards[0]
    const productionQty = prodCards.reduce((s, c) => s + cardProductProductionQty(c), 0)
    if (productionQty <= 0) continue
    rows.push({
      product_cd: productCd,
      product_name: String(first.product_name || first.product_cd || '').trim() || '—',
      production_qty: productionQty,
      time_periods: [],
    })
  }
  return rows
}

function mergeProductionAggsIntoDayMap(
  dayMap: Map<string, Map<string, ProductionListProductAgg>>,
  workDate: string,
  lapNo: number,
  lapDisplayNo: number,
  aggs: ProductionListProductAgg[],
) {
  const wd = workDate.trim()
  if (!wd) return
  let byProd = dayMap.get(wd)
  if (!byProd) {
    byProd = new Map()
    dayMap.set(wd, byProd)
  }
  for (const agg of aggs) {
    const key = agg.product_cd || agg.product_name
    const lapPeriod = productionListTimePeriodForLap(lapNo, lapDisplayNo, agg.production_qty)
    const cur = byProd.get(key)
    if (cur) {
      cur.production_qty += agg.production_qty
      if (!cur.product_name && agg.product_name) cur.product_name = agg.product_name
      cur.time_periods = mergeProductionListTimePeriods(cur.time_periods, [lapPeriod])
    } else {
      byProd.set(key, {
        ...agg,
        time_periods: mergeProductionListTimePeriods(agg.time_periods, [lapPeriod]),
      })
    }
  }
}

function lapWorkDateForProductionList(lapNo: number, scheduleByLap: Map<number, LapScheduleSlot>): string {
  const fromCard = lapCardMetaByLap.value.get(lapNo)?.work_date
  return (fromCard || scheduleByLap.get(lapNo)?.work_date || '').slice(0, 10)
}

function buildProductionListByDay(): ProductionListDayGroup[] {
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  const dayMap = new Map<string, Map<string, ProductionListProductAgg>>()
  for (const lapRow of lapGridRows.value) {
    const lapNo = lapRow.lap_no
    const workDate = lapWorkDateForProductionList(lapNo, scheduleByLap)
    const lapAggs: ProductionListProductAgg[] = []
    if (lapRow.mergedLeft) {
      for (const ms of lapRow.mergedLeft) {
        lapAggs.push(...collectProductionProductAggsFromJigBlock(ms))
      }
    } else {
      const lapCards = lapCardsWithQty(lapNo)
      lapAggs.push(...collectProductionProductAggsFromLooseCards(lapNo, lapCards))
    }
    if (lapRow.mergedTail) {
      for (const tc of lapRow.mergedTail) {
        if (isJigProductCd(tc.product_cd)) continue
        const qty = cardProductProductionQty(tc)
        if (qty <= 0) continue
        const productCd = String(tc.product_cd || '').trim()
        const existing = lapAggs.find((a) => a.product_cd === productCd)
        if (existing) {
          existing.production_qty += qty
        } else {
          lapAggs.push({
            product_cd: productCd,
            product_name: String(tc.product_name || tc.product_cd || '').trim() || '—',
            production_qty: qty,
            time_periods: [],
          })
        }
      }
    }
    mergeProductionAggsIntoDayMap(dayMap, workDate, lapNo, lapRow.lap_display_no, lapAggs)
  }
  return [...dayMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([work_date, byProd]) => {
      const rows = [...byProd.values()]
        .map(({ product_cd, product_name, production_qty, time_periods }) => ({
          product_cd,
          product_name,
          production_qty,
          time_periods: [...time_periods].sort((a, b) => a.lap_no - b.lap_no),
        }))
        .sort((a, b) => a.product_name.localeCompare(b.product_name, 'ja'))
      const total_production_qty = rows.reduce((s, r) => s + r.production_qty, 0)
      const [rows_left, rows_right] = splitProductionListRows(rows)
      return {
        work_date,
        work_date_label: formatBoardDateLabel(work_date),
        rows,
        rows_left,
        rows_right,
        total_production_qty,
      }
    })
    .filter((g) => g.rows.length > 0)
}

const productionListByDay = computed(() => buildProductionListByDay())

const productionListGrandTotal = computed(() =>
  productionListByDay.value.reduce((s, g) => s + g.total_production_qty, 0),
)

const hasProductionListData = computed(() => productionListByDay.value.length > 0)

function openProductionListDialog() {
  if (!hasProductionListData.value) {
    ElMessage.info('表示期間内に割当済みの生産データがありません')
    return
  }
  productionListDialogVisible.value = true
}

const kpi = computed(() => {
  const jigs = layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value
  const cycle = minutesPerLap.value
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  const visibleLapSet = new Set(lapGridRows.value.map((r) => r.lap_no))
  const visibleCards = scheduleCards.value.filter(
    (c) => c.qty > 0 && visibleLapSet.has(c.lap_no) && isLapNoInBoardView(c.lap_no, scheduleByLap),
  )
  const totalProductQty = visibleCards.reduce((s, c) => s + cardProductProductionQty(c), 0)
  if (jigs <= 0 || cycle <= 0) {
    return { totalSlots: 0, usedSlots: 0, remainSlots: 0, utilizationPct: '—', estimatedMinutes: 0, totalProductQty }
  }
  const lapsPerDay = Math.floor(PLATING_DAY_MINUTES / cycle)
  const visibleLapCount = lapGridRows.value.length
  const totalSlots =
    layoutBoardReady.value && visibleLapCount > 0
      ? visibleLapCount * jigs
      : layoutBoardReady.value && layoutMaxLaps.value > 0
        ? layoutMaxLaps.value * jigs
        : lapsPerDay * jigs
  const usedSlots = visibleCards.length
  const remainSlots = Math.max(totalSlots - usedSlots, 0)
  /** 充填率＝使用中の枠数 / 総治具数（数量ではなく枠ベースで算出） */
  const utilizationPct = totalSlots > 0 ? ((usedSlots / totalSlots) * 100).toFixed(1) : '—'
  const usedLaps = jigs > 0 ? Math.ceil(usedSlots / jigs) : 0
  const estimatedMinutes = usedLaps * cycle
  return { totalSlots, usedSlots, remainSlots, utilizationPct, estimatedMinutes, totalProductQty }
})

watch(
  scheduleCards,
  () => {
    scheduleBoardReactiveSideEffects()
  },
  { deep: true },
)
watch(leftRows, () => { nextTick(() => bindLeftInventoryTableDrag()) })
watch(leftInventoryFloating, () => { nextTick(() => bindLeftInventoryTableDrag()) })
watch(rightRows, () => { nextTick(() => bindRightGenTableDrag()) })
watch(rightGenFloating, () => { nextTick(() => bindRightGenTableDrag()) })
watch(
  [leftInventoryDate, rightGenDate],
  () => {
    // 在庫／見込は独立更新（治具再取得は不要）
    void loadSummaryPair()
  },
)

/** 在庫／見込ペイン：ボード読込後に遅延取得（ms） */
const SUMMARY_PANEL_DEFER_MS = 300

async function loadDeferredSummaryPanel() {
  void loadSummaryPair()
}

async function loadPageInitialData() {
  // ①メッキ投入ボード＋②メッキ治具を優先して並列読み込み
  await Promise.all([
    loadLatestDraft({ autoMode: true, autoSyncWorkDate: true }),
    loadJigAvailability(),
  ])
  // ③在庫／見込は最後に遅延読み込み
  window.setTimeout(() => {
    void loadDeferredSummaryPanel()
  }, SUMMARY_PANEL_DEFER_MS)
}

watch(
  draftWorkDate,
  () => {
    if (syncingDraftWorkDateFromLoad.value) return
    void loadLatestDraft({ autoMode: true, autoSyncWorkDate: false })
  },
  { flush: 'sync' },
)

watch(
  [boardFilterFrom, boardFilterTo],
  () => {
    if (skipBoardViewRangeWatchOnce) {
      skipBoardViewRangeWatchOnce = false
      return
    }
    scheduleBoardViewRangeReload()
  },
)

onMounted(() => {
  void loadPageInitialData().finally(() => {
    nextTick(() => {
      bindLeftInventoryTableDrag()
      bindRightGenTableDrag()
      scheduleInitBoardLapSortables()
      boardViewRangeReady = true
    })
  })
})

onBeforeUnmount(() => {
  teardownAppendLayoutPreviewResize()
  cancelBoardAutosaveTimer()
  cancelBoardViewRangeReload()
  cancelBoardReactiveEffectsTimer()
  cancelLapSortableInitTimer()
  destroyLapTrackSortables()
  destroyLapMergedSortables()
  lapGridRowCache = new Map()
})
</script>

<style scoped>
.plating-planning-page {
  --pp-accent: #0d9488;
  --pp-accent-deep: #0f766e;
  --pp-accent-soft: #ccfbf1;
  --pp-surface: rgba(255, 255, 255, 0.96);
  --pp-shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08), 0 2px 8px rgba(15, 23, 42, 0.05);
  --pp-radius: 12px;
  --pp-border: var(--el-border-color-light);
  position: relative;
  padding: 12px 14px 16px;
  max-width: 1680px;
  margin: 0 auto;
  background: linear-gradient(145deg, #f0fdfa 0%, var(--el-bg-color-page) 42%, #f1f5f9 100%);
  min-height: 100%;
}

.plating-planning-page::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 10% 12%, rgba(13, 148, 136, 0.07) 0%, transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(56, 189, 248, 0.05) 0%, transparent 42%);
}

.page-header {
  position: relative;
  z-index: 1;
  margin-bottom: 12px;
  padding: 14px 18px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.85);
  background: var(--pp-surface);
  backdrop-filter: blur(12px);
  box-shadow: var(--pp-shadow-md);
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--pp-accent-deep) 0%, var(--pp-accent) 45%, #38bdf8 100%);
}

.header-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px 16px;
  flex-wrap: wrap;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.title-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.title-icon-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(145deg, #14b8a6 0%, var(--pp-accent) 55%, var(--pp-accent-deep) 100%);
  box-shadow:
    0 6px 14px rgba(13, 148, 136, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.title-icon {
  font-size: 22px;
  color: #fff;
}

.page-title {
  margin: 0 0 6px;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  background: linear-gradient(135deg, #134e4a 0%, var(--pp-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-description {
  margin: 0;
  max-width: 52rem;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-secondary);
}

.header-badge {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: var(--pp-accent-deep);
  background: linear-gradient(180deg, #fff 0%, var(--pp-accent-soft) 100%);
  border: 1px solid rgba(13, 148, 136, 0.22);
  white-space: nowrap;
}

.header-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--pp-accent);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2);
}

.pp-card {
  margin-bottom: 10px;
  border-radius: var(--pp-radius);
  border: 1px solid var(--pp-border);
  background: var(--el-bg-color);
}

.pp-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.pp-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.pp-card--jig {
  border-color: color-mix(in oklab, var(--el-color-success) 22%, var(--pp-border));
  background:
    linear-gradient(180deg, color-mix(in oklab, var(--el-color-success-light-9) 42%, transparent) 0%, transparent 58%),
    var(--el-bg-color);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.035);
}

.pp-card--jig :deep(.el-card__header) {
  background:
    linear-gradient(90deg, color-mix(in oklab, var(--el-color-success-light-9) 62%, transparent), transparent 72%),
    var(--el-fill-color-blank);
}

.pp-card--jig :deep(.el-card__body) {
  position: relative;
  padding: 10px 12px;
}

.pp-card--jig-list-collapsed :deep(.el-card__body) {
  padding: 4px 10px;
}

.jig-card-body {
  position: relative;
  min-height: 0;
}

.jig-card-body--collapsed {
  min-height: 26px;
}

.jig-card-toggle-btn.el-button {
  position: absolute;
  right: 0;
  bottom: 0;
  z-index: 2;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid color-mix(in oklab, var(--el-color-success) 38%, var(--el-border-color-lighter));
  background: color-mix(in oklab, var(--el-color-success-light-9) 75%, #fff);
  color: var(--el-color-success-dark-2);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
}

.jig-card-toggle-btn.el-button:hover {
  border-color: color-mix(in oklab, var(--el-color-success) 55%, var(--el-border-color));
  background: color-mix(in oklab, var(--el-color-success-light-8) 80%, #fff);
  color: var(--el-color-success);
}

.jig-card-toggle-btn .el-icon {
  font-size: 14px;
}

.section-head-row__start {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  min-width: 0;
  flex: 1 1 auto;
}

.section-head-row--jig .pp-card-title {
  flex-shrink: 0;
}

.jig-usage-edit-btn.el-button {
  --jig-btn-border: color-mix(in oklab, var(--el-color-primary) 42%, var(--el-border-color));
  height: 28px;
  padding: 5px 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-radius: 8px;
  border: 1px solid var(--jig-btn-border);
  background: linear-gradient(
    180deg,
    color-mix(in oklab, var(--el-color-primary-light-3) 28%, #fff) 0%,
    var(--el-color-primary) 48%,
    color-mix(in oklab, var(--el-color-primary-dark-2) 88%, #000) 100%
  );
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 2px 6px color-mix(in oklab, var(--el-color-primary) 32%, transparent);
  transition:
    transform 120ms ease,
    box-shadow 120ms ease,
    filter 120ms ease,
    background 120ms ease,
    border-color 120ms ease;
}

.jig-usage-edit-btn.el-button:hover,
.jig-usage-edit-btn.el-button:focus {
  color: #fff;
  border-color: color-mix(in oklab, var(--el-color-primary-light-3) 55%, var(--el-border-color));
  background: linear-gradient(
    180deg,
    color-mix(in oklab, var(--el-color-primary-light-3) 38%, #fff) 0%,
    var(--el-color-primary) 52%,
    color-mix(in oklab, var(--el-color-primary-dark-2) 82%, #000) 100%
  );
  filter: brightness(1.05);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.4) inset,
    0 4px 10px color-mix(in oklab, var(--el-color-primary) 38%, transparent);
}

.jig-usage-edit-btn.el-button:active {
  color: #fff;
  transform: translateY(1px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.2) inset,
    0 1px 3px color-mix(in oklab, var(--el-color-primary) 28%, transparent);
}

.jig-usage-edit-btn__icon {
  margin-right: 4px;
  font-size: 14px;
}

.jig-card-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.jig-card-meta--inline {
  margin-bottom: 0;
}

.jig-product-filter-select {
  width: min(180px, 100%);
  flex: 0 1 180px;
}

.jig-meta-pill--filter {
  border-color: color-mix(in oklab, var(--el-color-warning) 45%, var(--el-border-color-lighter));
  background: color-mix(in oklab, var(--el-color-warning-light-9) 75%, var(--el-bg-color));
  color: var(--el-color-warning-dark-2);
  font-weight: 600;
}

.jig-meta-pill--hint {
  color: var(--el-text-color-placeholder);
  background: transparent;
  border: 1px dashed var(--el-border-color-lighter);
}

.pp-card--board :deep(.el-card__body) {
  padding-top: 8px;
}

.section-head-row--summary-float {
  flex-wrap: wrap;
  gap: 4px 12px;
}

.summary-head-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin-left: auto;
}

.summary-head-actions :deep(.summary-print-btn) {
  color: #516079;
  background: linear-gradient(180deg, #fbfcff 0%, #f1f4f8 100%);
  border-color: #d7deea;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 1px 3px rgba(31, 50, 81, 0.1);
}

.summary-float-dock-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin-left: auto;
}

.summary-both-float-hint {
  margin: 0 0 8px;
  padding: 8px 12px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
  border-radius: 8px;
  border: 1px dashed var(--el-border-color);
  background: var(--el-fill-color-lighter);
}

.pp-card--summary {
  border-color: color-mix(in oklab, var(--el-color-primary) 16%, var(--pp-border));
  background:
    linear-gradient(180deg, color-mix(in oklab, var(--el-color-primary-light-9) 30%, transparent) 0%, transparent 52%),
    var(--el-bg-color);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
}

.pp-card--summary :deep(.el-card__header) {
  background:
    linear-gradient(90deg, color-mix(in oklab, var(--el-color-primary-light-8) 56%, transparent), transparent 72%),
    var(--el-fill-color-blank);
}

.pp-card-title--summary {
  letter-spacing: 0.2px;
}

.summary-drag-hint {
  margin: 0 0 8px;
  font-size: 11px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}

.board-cond-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 10px;
  margin-bottom: 8px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.4;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-text-color-regular);
  border: 1px solid var(--el-color-primary-light-7);
}

.board-cond-label {
  font-weight: 700;
  color: var(--el-color-primary);
  margin-right: 2px;
}

.board-cond-val strong {
  font-variant-numeric: tabular-nums;
}

.board-cond-sep {
  opacity: 0.55;
}

.board-cond-hint {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.section-head-row--board {
  --board-head-ctrl-h: 24px;
  flex-wrap: nowrap;
  gap: 8px 10px;
  align-items: center;
}

.section-head-row--board .pp-card-title {
  flex-shrink: 0;
}

.board-head-period {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  min-width: 0;
}

.board-head-period__label {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  line-height: var(--board-head-ctrl-h, 24px);
}

.board-head-period__group {
  display: inline-flex;
  align-items: stretch;
  height: var(--board-head-ctrl-h, 24px);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
  background: var(--el-fill-color-blank);
  box-shadow: 0 1px 2px rgba(31, 50, 81, 0.06);
}

.board-head-period__picker {
  width: 130px;
  flex-shrink: 0;
}

.board-head-period__picker :deep(.el-input__wrapper) {
  height: var(--board-head-ctrl-h, 24px);
  min-height: var(--board-head-ctrl-h, 24px);
  padding: 0 6px 0 4px;
  box-shadow: none !important;
  border-radius: 0;
  background: transparent;
}

.board-head-period__picker :deep(.el-range__icon) {
  font-size: 13px;
  line-height: 1;
  margin-right: 2px;
}

.board-head-period__picker :deep(.el-range-input) {
  height: calc(var(--board-head-ctrl-h, 24px) - 2px);
  line-height: calc(var(--board-head-ctrl-h, 24px) - 2px);
  font-size: 12px;
}

.board-head-period__picker :deep(.el-range-separator) {
  line-height: var(--board-head-ctrl-h, 24px);
  font-size: 12px;
  padding: 0 2px;
  color: var(--el-text-color-secondary);
}

.board-head-period__nav {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  height: 100%;
  padding: 0 3px;
  border-left: 1px solid var(--el-border-color);
  background: var(--el-fill-color-light);
}

.board-head-period__nav :deep(.el-button) {
  height: var(--board-head-ctrl-h, 24px);
  min-height: var(--board-head-ctrl-h, 24px);
  margin: 0;
  padding: 0;
  border: none;
  border-radius: 4px;
  box-shadow: none;
}

.board-head-period__nav :deep(.board-head-period__nav-btn) {
  width: var(--board-head-ctrl-h, 24px);
  min-width: var(--board-head-ctrl-h, 24px);
}

.board-head-period__nav :deep(.board-head-period__today) {
  min-width: 40px;
  padding: 0 6px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.board-head-period__nav :deep(.el-button + .el-button) {
  margin-left: 2px;
}

.board-head-toolbar :deep(.board-act-btn.el-button--small) {
  height: var(--board-head-ctrl-h, 24px);
  padding-top: 0;
  padding-bottom: 0;
}

.board-head-toolbar {
  margin-left: auto;
  flex-shrink: 0;
}

.board-head-toolbar :deep(.board-act-btn) {
  border-radius: 6px;
  border-width: 1px;
  font-weight: 600;
  letter-spacing: 0.01em;
  transition:
    transform 100ms ease,
    box-shadow 120ms ease,
    filter 120ms ease;
}

.board-head-toolbar :deep(.board-act-btn:not(.is-disabled):hover) {
  transform: translateY(-1px);
  filter: saturate(1.04);
}

.board-head-toolbar :deep(.board-act-btn:not(.is-disabled):active) {
  transform: translateY(0);
}

.board-head-toolbar :deep(.board-act-btn--primary) {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 2px 6px rgba(45, 128, 248, 0.22);
}

.board-head-toolbar :deep(.board-act-btn--list) {
  color: #2d5a87;
  background: linear-gradient(180deg, #ffffff 0%, #eef6fc 100%);
  border-color: #c5d9eb;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.92),
    0 1px 3px rgba(45, 90, 135, 0.12);
}

.board-head-toolbar :deep(.board-act-btn--copy) {
  color: #2f3f57;
  background: linear-gradient(180deg, #ffffff 0%, #eef3fa 100%);
  border-color: #d3ddec;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.92),
    0 1px 3px rgba(31, 50, 81, 0.12);
}

.board-head-toolbar :deep(.board-act-btn--copy.is-disabled) {
  background: linear-gradient(180deg, #fafbfc 0%, #f3f5f8 100%);
  border-color: #e2e7ef;
}

.board-head-toolbar :deep(.board-act-btn--danger) {
  color: #d54b4b;
  background: linear-gradient(180deg, #fff9f9 0%, #ffefef 100%);
  border-color: #f1c7c7;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 1px 3px rgba(219, 90, 90, 0.16);
}

.board-head-toolbar :deep(.board-act-btn--print) {
  color: #516079;
  background: linear-gradient(180deg, #fbfcff 0%, #f1f4f8 100%);
  border-color: #d7deea;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 1px 3px rgba(31, 50, 81, 0.1);
}

@media (max-width: 900px) {
  .section-head-row--board {
    flex-wrap: wrap;
  }

  .board-head-period {
    order: 3;
    flex: 1 1 100%;
  }

  .board-head-period__group {
    flex: 1 1 auto;
    min-width: 0;
    max-width: 320px;
  }

  .board-head-period__picker {
    flex: 1 1 auto;
    width: auto;
    min-width: 0;
    max-width: none;
  }

  .board-head-toolbar {
    margin-left: 0;
  }
}

.tpl-dialog-hint {
  margin: 0 0 8px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.tpl-dialog-append-note {
  margin: 0 0 10px;
  padding: 6px 8px;
  font-size: 11px;
  line-height: 1.4;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 6px;
}

.tpl-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

.tpl-dialog :deep(.el-dialog__header) {
  padding: 10px 12px 8px;
  background:
    linear-gradient(90deg, color-mix(in oklab, var(--el-color-primary-light-8) 56%, transparent), transparent 78%),
    var(--el-fill-color-blank);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tpl-dialog :deep(.el-dialog__body) {
  padding: 10px 12px 8px;
}

.tpl-dialog :deep(.el-dialog__footer) {
  padding: 8px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.tpl-preview-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.tpl-preview-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: color-mix(in oklab, var(--el-color-primary) 70%, var(--el-text-color-primary));
  background: color-mix(in oklab, var(--el-color-primary-light-9) 76%, var(--el-bg-color));
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 56%, var(--el-border-color-lighter));
}

.tpl-compact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.tpl-compact-grid--schedule {
  grid-template-columns: 1fr 1fr;
  margin-bottom: 10px;
}

.tpl-field--wide {
  grid-column: 1 / -1;
}

.tpl-date,
.tpl-time {
  width: 100%;
}

.tpl-schedule-preview {
  margin-top: 4px;
}

.tpl-schedule-preview-title {
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.tpl-schedule-table :deep(.el-table__cell) {
  padding-top: 3px;
  padding-bottom: 3px;
}

.lap-copy-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 45%, var(--el-border-color-lighter));
  box-shadow:
    0 12px 32px color-mix(in oklab, var(--el-color-primary) 12%, transparent),
    0 4px 16px rgba(15, 23, 42, 0.08);
}

.lap-copy-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 10px 14px 8px;
  border-bottom: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 40%, var(--el-border-color-lighter));
  background: linear-gradient(
    90deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 65%, #fff),
    var(--el-fill-color-blank) 72%
  );
}

.lap-copy-dialog :deep(.el-dialog__body) {
  padding: 12px 14px 10px;
}

.lap-copy-dialog :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.lap-copy-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lap-copy-header__icon-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(145deg, var(--el-color-primary-light-3) 0%, var(--el-color-primary) 100%);
  box-shadow: 0 3px 10px color-mix(in oklab, var(--el-color-primary) 30%, transparent);
}

.lap-copy-header__icon {
  font-size: 18px;
  color: #fff;
}

.lap-copy-header__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
}

.lap-copy-body {
  padding: 2px 0;
}

.lap-copy-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: end;
  gap: 8px;
}

.lap-copy-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 8px 9px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, #fff 0%, var(--el-fill-color-blank) 100%);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.lap-copy-field__label {
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  letter-spacing: 0.03em;
}

.lap-copy-flow__arrow {
  padding-bottom: 10px;
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
  color: var(--el-color-primary);
}

.lap-copy-select {
  width: 100%;
}

.lap-copy-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.lap-copy-footer__cancel.el-button {
  font-weight: 600;
  border-radius: 8px;
}

.lap-copy-footer__submit.el-button {
  min-width: 108px;
  font-weight: 700;
  letter-spacing: 0.03em;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-dark-2) 50%, var(--el-border-color));
  background: linear-gradient(
    180deg,
    color-mix(in oklab, var(--el-color-primary-light-3) 30%, #fff) 0%,
    var(--el-color-primary) 48%,
    color-mix(in oklab, var(--el-color-primary-dark-2) 88%, #000) 100%
  );
  box-shadow: 0 2px 8px color-mix(in oklab, var(--el-color-primary) 32%, transparent);
}

.lap-copy-footer__submit.el-button:hover:not(:disabled) {
  filter: brightness(1.05);
}

@media (max-width: 480px) {
  .lap-copy-flow {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }

  .lap-copy-flow__arrow {
    padding: 0;
    text-align: center;
    transform: rotate(90deg);
  }
}

.tpl-field {
  padding: 8px 8px 7px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: color-mix(in oklab, var(--el-fill-color-light) 68%, var(--el-bg-color));
}

.tpl-field-label {
  margin-bottom: 6px;
  font-size: 11px;
  line-height: 1.3;
  color: var(--el-text-color-secondary);
}

.tpl-input-num :deep(.el-input-number) {
  width: 100%;
}

@media (max-width: 520px) {
  .tpl-compact-grid {
    grid-template-columns: 1fr;
  }
}

.pp-card-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.section-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 10px;
}

.toolbar-inline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.toolbar-inline :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.pp-form-compact :deep(.el-form-item__label) {
  padding-right: 6px;
  font-size: 12px;
}

.pp-input-num :deep(.el-input-number) {
  width: 120px;
}

.pp-input-num-sm :deep(.el-input-number) {
  width: 112px;
}

.pp-date {
  width: 128px;
}

.pair-row {
  align-items: stretch;
}

.summary-col {
  border-radius: 12px;
  padding: 8px 8px 6px;
  transition: box-shadow 160ms ease, transform 160ms ease;
}

.summary-col:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.summary-col--left {
  background: linear-gradient(180deg, color-mix(in oklab, var(--el-color-primary-light-9) 62%, transparent), transparent 66%);
}

.summary-col--right {
  background: linear-gradient(180deg, color-mix(in oklab, var(--el-color-success-light-9) 64%, transparent), transparent 66%);
}

.pane-head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 6px;
}

.pane-head-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
}

.pane-head-date-item :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.pane-head .pane-title {
  margin-bottom: 0;
  flex: 0 1 auto;
  min-width: 0;
}

.pp-date--pane {
  width: 138px;
}

.pane-head--left .pane-title {
  color: color-mix(in oklab, var(--el-color-primary) 78%, var(--el-text-color-primary));
}

.pane-head--right .pane-title {
  color: color-mix(in oklab, var(--el-color-success) 72%, var(--el-text-color-primary));
}

.pane-head-meta {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 999px;
  width: fit-content;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.pane-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.pane-dim {
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.pane-total-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.pane-total-value {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-primary);
  letter-spacing: 0.2px;
}

.pp-table :deep(.el-table__cell) {
  padding-top: 4px;
  padding-bottom: 4px;
}

.pp-table :deep(.el-table__header .cell) {
  font-size: 12px;
  font-weight: 600;
}

.pp-table :deep(.el-table__header th) {
  background: color-mix(in oklab, var(--el-fill-color-light) 88%, var(--el-bg-color));
}

.pp-table :deep(.el-table__row) {
  transition: background-color 140ms ease;
}

.pp-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 54%, transparent);
}

.pp-table--left :deep(.el-table__header th) {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 78%, var(--el-bg-color));
}

.pp-table--right :deep(.el-table__header th) {
  background: color-mix(in oklab, var(--el-color-success-light-9) 82%, var(--el-bg-color));
}

.pp-table--right :deep(.el-table__row:hover > td.el-table__cell) {
  background: color-mix(in oklab, var(--el-color-success-light-9) 56%, transparent);
}

:deep(.table-row-draggable td) {
  cursor: grab;
}

:deep(.table-row-draggable:active td) {
  cursor: grabbing;
}

.kpi-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.kpi-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.kpi-chip-l {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.kpi-chip-v {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-primary);
}

.lap-board {
  min-height: 64px;
  padding: 6px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  transition:
    border-color 120ms ease,
    box-shadow 120ms ease;
}

.lap-board--loading {
  min-height: 280px;
}

.lap-board--jig-drop {
  border-color: color-mix(in oklab, var(--el-color-primary) 55%, var(--el-border-color));
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--el-color-primary-light-5) 40%, transparent);
}

.lap-merged-seg--board-jig-block {
  cursor: grab;
  user-select: none;
}

.lap-merged-seg--board-jig-block:active {
  cursor: grabbing;
}

.lap-board-row--jig-drop .lap-rail-lap,
.lap-board-row--jig-drop .lap-board-body-row {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 65%, transparent);
}

.jig-drop-dialog-name {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
}

.jig-drop-dialog-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.jig-drop-dialog-hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.45;
}

.jig-drop-qty-item {
  margin-bottom: 0;
}

.board-jig-edit-dialog :deep(.el-dialog__header) {
  padding: 12px 16px 8px;
  margin-right: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.board-jig-edit-dialog :deep(.el-dialog__body) {
  padding: 10px 16px 12px;
}

.board-jig-edit-dialog :deep(.el-dialog__footer) {
  padding: 8px 16px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.board-jig-edit-dialog :deep(.el-form-item) {
  margin-bottom: 8px;
}

.board-jig-edit-dialog :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.board-jig-edit-header__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.02em;
}

.board-jig-edit-header__sub {
  margin: 2px 0 0;
  font-size: 11px;
  line-height: 1.35;
  color: var(--el-text-color-secondary);
}

.board-jig-edit-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.board-jig-edit-total-item :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  padding-bottom: 2px;
  line-height: 1.2;
}

.board-jig-edit-total-slider-wrap {
  width: 100%;
  padding: 2px 6px 0;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
}

.board-jig-edit-total-slider-val {
  font-size: 13px;
  color: var(--el-color-primary);
}

.board-jig-edit-total-item :deep(.el-form-item__content) {
  line-height: 1;
}

.jig-edit-products {
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.jig-edit-products__empty {
  margin: 0;
  padding: 6px 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
}

.board-jig-edit-add {
  padding-top: 8px;
  border-top: 1px dashed var(--el-border-color-lighter);
}

.board-jig-edit-add__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.board-jig-edit-add__title {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.board-jig-edit-add-select {
  flex: 1;
  min-width: 0;
}

.board-jig-edit-add__empty {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.board-jig-edit-add-form :deep(.el-form-item) {
  margin-bottom: 6px;
}

.board-jig-edit-add-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  padding-bottom: 2px;
}

.board-jig-edit-add-slider-wrap {
  width: 100%;
  padding: 4px 6px 0;
}

.board-jig-edit-add-replace {
  margin: 0 0 6px;
}

.board-jig-edit-inline-assign {
  padding: 0;
}

.board-jig-edit-inline-order {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--el-border-color-lighter);
}

.board-jig-edit-inline-order__label {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.board-jig-edit-inline-order__group {
  flex: 1;
  min-width: 0;
  display: inline-flex;
  flex-wrap: nowrap;
}

.board-jig-edit-inline-order__group :deep(.el-radio-button) {
  flex: 1;
  min-width: 0;
}

.board-jig-edit-inline-order__group :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 6px 8px;
  font-size: 11px;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.board-jig-edit-inline-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.board-jig-edit-inline-row {
  grid-template-columns: auto minmax(0, 0.75fr) minmax(140px, 1.8fr);
}

.board-jig-edit-inline-tag {
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.jig-edit-products__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.jig-edit-products__title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.jig-edit-products__sum {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.jig-edit-products__sum--warn {
  color: var(--el-color-danger);
  font-weight: 600;
}

.board-jig-edit-dialog .jig-edit-product-row {
  display: grid;
  grid-template-columns: minmax(0, 0.85fr) minmax(140px, 1.8fr) auto minmax(72px, auto) 28px;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  margin-bottom: 6px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: linear-gradient(135deg, #fff 0%, hsl(var(--row-hue, 210) 40% 97%) 100%);
  box-shadow: inset 3px 0 0 hsl(var(--row-hue, 210) 65% 52%);
}

.board-jig-edit-dialog .jig-edit-product-row:last-child {
  margin-bottom: 0;
}

.board-jig-edit-dialog .jig-edit-product-slider :deep(.el-slider__runway) {
  margin: 4px 0 0;
}

.jig-edit-product-switches {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  flex-wrap: nowrap;
}

.jig-edit-product-delete {
  justify-self: center;
  padding: 0;
  min-height: auto;
}

.jig-edit-product-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.jig-edit-product-slider-wrap {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 2px;
  min-width: 0;
  padding: 0 4px;
}

.jig-edit-product-slider-head {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  line-height: 1;
}

.jig-edit-product-slider-min {
  text-align: left;
}

.jig-edit-product-slider-max {
  text-align: right;
}

.jig-edit-product-slider-val {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
  color: hsl(var(--row-hue, 210) 55% 38%);
}

.jig-edit-product-slider-val .jig-edit-product-unit {
  margin-left: 1px;
  font-size: 11px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.jig-edit-product-slider {
  width: 100%;
  margin: 0;
  padding-inline: 2px;
}

.jig-edit-product-slider :deep(.el-slider__runway) {
  height: 8px;
  margin: 6px 0 2px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
}

.jig-edit-product-slider :deep(.el-slider__bar) {
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    hsl(var(--row-hue, 210) 70% 72%),
    hsl(var(--row-hue, 210) 62% 46%)
  );
}

.jig-edit-product-slider :deep(.el-slider__button) {
  width: 18px;
  height: 18px;
  border-width: 2px;
  border-color: hsl(var(--row-hue, 210) 62% 46%);
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.18);
  transition: transform 0.15s ease;
}

.jig-edit-product-slider :deep(.el-slider__button:hover),
.jig-edit-product-slider :deep(.el-slider__button.dragging) {
  transform: scale(1.08);
}

.jig-edit-product-unit {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.jig-edit-product-qty {
  font-size: 11px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
  min-width: 52px;
  text-align: right;
}

.jig-edit-product-qty--depleted {
  color: var(--el-color-danger);
  font-weight: 600;
}

.jig-edit-product-qty--force-red {
  color: var(--el-color-danger);
  font-weight: 700;
}

.board-jig-edit-dialog .jig-edit-product-order-item {
  margin: 6px 0 0;
}

.board-jig-edit-dialog .jig-edit-product-order-item :deep(.el-form-item__label) {
  font-size: 12px;
  padding-bottom: 2px;
  line-height: 1.2;
}

.board-jig-edit-dialog .jig-edit-product-order-item :deep(.el-radio-group) {
  display: inline-flex;
  flex-wrap: nowrap;
}

.product-assign-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.product-assign-row {
  display: grid;
  grid-template-columns: 40px 1fr auto 20px;
  align-items: center;
  gap: 8px;
}

.product-assign-row-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.product-assign-row-name {
  font-size: 12px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-assign-row-qty {
  width: 108px;
}

.product-assign-row-unit {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.product-assign-order-item {
  margin-bottom: 0;
}

.board-product-pick-dialog :deep(.el-dialog),
.append-layout-dialog :deep(.el-dialog),
.jig-drop-qty-dialog :deep(.el-dialog),
.lap-time-edit-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow:
    0 12px 32px color-mix(in oklab, var(--el-color-primary) 12%, transparent),
    0 4px 16px rgba(15, 23, 42, 0.08);
}

.append-layout-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 10px 14px 0;
}

.append-layout-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 6px;
}

.append-layout-dialog :deep(.el-dialog__footer) {
  display: none;
}

.al-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 10px;
}

.al-header-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
}

.al-header__sub {
  font-size: 11px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.al-shell {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(300px, 1.05fr);
  gap: 10px;
  align-items: stretch;
}

.al-panel {
  min-width: 0;
  min-height: 0;
  height: 100%;
}

.al-panel--form {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 8px 10px 10px;
  border-radius: 10px;
  background: linear-gradient(
    165deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 55%, #fff) 0%,
    var(--el-fill-color-blank) 48%
  );
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 40%, var(--el-border-color-lighter));
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.al-panel__main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.al-panel__foot {
  flex-shrink: 0;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 35%, var(--el-border-color-lighter));
}

.al-submit-btn.el-button {
  width: 100%;
  height: 36px;
  margin: 0;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-dark-2) 55%, #000);
  background: linear-gradient(
    180deg,
    color-mix(in oklab, var(--el-color-primary-light-3) 32%, #fff) 0%,
    var(--el-color-primary) 46%,
    color-mix(in oklab, var(--el-color-primary-dark-2) 90%, #000) 100%
  );
  box-shadow:
    0 2px 6px color-mix(in oklab, var(--el-color-primary) 35%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.al-submit-btn.el-button:hover:not(:disabled) {
  filter: brightness(1.05);
  box-shadow:
    0 4px 12px color-mix(in oklab, var(--el-color-primary) 40%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

.al-submit-btn.el-button:disabled {
  opacity: 0.55;
  filter: grayscale(0.15);
}

.al-submit-btn__icon {
  margin-right: 4px;
  font-size: 15px;
}

.al-panel--preview {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.al-context {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 5px 6px;
  border-radius: 6px;
  background: color-mix(in oklab, var(--el-color-primary-light-9) 35%, transparent);
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-8) 50%, var(--el-border-color-lighter));
}

.al-tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 7px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.al-tag--info {
  color: var(--el-color-primary);
  background: color-mix(in oklab, var(--el-color-primary-light-9) 90%, #fff);
  border-color: var(--el-color-primary-light-7);
}

.al-tag--suggest {
  color: var(--el-color-success);
  background: color-mix(in oklab, var(--el-color-success-light-9) 90%, #fff);
  border-color: var(--el-color-success-light-7);
}

.al-duplicate-hint {
  margin: 0;
  padding: 5px 7px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.35;
  color: var(--el-color-danger);
  background: color-mix(in oklab, var(--el-color-danger-light-9) 80%, #fff);
  border: 1px solid color-mix(in oklab, var(--el-color-danger-light-7) 55%, transparent);
}

.al-form {
  flex: none;
}

.al-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.al-form :deep(.el-form-item__label) {
  padding-bottom: 1px;
  line-height: 1.15;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.al-insert-mode {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
}

.al-insert-mode :deep(.el-radio) {
  margin-right: 0;
  height: 24px;
}

.al-field--full {
  margin-bottom: 4px;
}

.al-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 6px;
}

.al-control {
  width: 100%;
}

.al-control :deep(.el-input__wrapper),
.al-control :deep(.el-select__wrapper) {
  border-radius: 8px;
}

.al-date,
.al-time {
  width: 100%;
}

.al-num {
  width: 100%;
}

.al-num :deep(.el-input-number) {
  width: 100%;
}

.al-preview {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 100%;
  border-radius: 10px;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 35%, var(--el-border-color-lighter));
  overflow: hidden;
  background: var(--el-bg-color);
  box-shadow:
    0 2px 8px rgba(15, 23, 42, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.al-preview__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  flex-shrink: 0;
  padding: 6px 10px;
  background: linear-gradient(
    90deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 70%, #fff),
    var(--el-fill-color-blank)
  );
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.al-preview__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-color-primary);
  letter-spacing: 0.04em;
}

.al-preview__badge {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  color: var(--el-color-primary);
  background: #fff;
  border: 1px solid var(--el-color-primary-light-7);
}

.al-preview__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: v-bind('appendLayoutPreviewTableMaxHeight + "px"');
  overflow: hidden;
}

.al-preview__table-host {
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.al-preview-table {
  width: 100%;
  height: 100%;
}

.al-preview-table :deep(.el-table__header th) {
  padding: 4px 0;
  font-size: 11px;
}

.al-preview-table :deep(.el-table__body td) {
  padding: 3px 0;
  font-size: 11px;
}

.al-preview-empty {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: v-bind('appendLayoutPreviewTableMaxHeight + "px"');
  padding: 8px;
  text-align: center;
  color: var(--el-text-color-placeholder);
  background: color-mix(in oklab, var(--el-fill-color-light) 40%, transparent);
}

.al-preview-empty__icon {
  font-size: 22px;
  opacity: 0.55;
}

.al-preview-empty p {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
}

@media (max-width: 680px) {
  .al-shell {
    grid-template-columns: 1fr;
  }
}

.production-list-dialog :deep(.el-dialog__body) {
  padding: 12px 16px 8px;
  max-height: min(72vh, 640px);
  overflow-y: auto;
}

.prod-list-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 12px;
}

.prod-list-header__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.prod-list-header__meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.prod-list-body {
  min-height: 120px;
}

.prod-list-days {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prod-list-day-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 12px;
  align-items: start;
}

.prod-list-day {
  min-width: 0;
}

.prod-list-day__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin-bottom: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
}

.prod-list-day__date {
  font-size: 13px;
  font-weight: 700;
  color: var(--el-color-primary);
  font-variant-numeric: tabular-nums;
}

.prod-list-day__count {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.prod-list-day__total {
  width: 100%;
  margin-top: 2px;
  font-size: 12px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.prod-list-grand-total {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.prod-list-grand-total__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.prod-list-grand-total__value {
  font-size: 15px;
  font-weight: 700;
  color: var(--el-color-primary);
  font-variant-numeric: tabular-nums;
}

.prod-list-table {
  width: 100%;
}

.prod-list-name-btn {
  display: block;
  max-width: 100%;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-weight: 600;
  color: var(--el-color-primary);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prod-list-name-btn:hover {
  color: var(--el-color-primary-dark-2);
  text-decoration: underline;
}

@media (max-width: 560px) {
  .prod-list-day-cols {
    grid-template-columns: 1fr;
  }
}

.prod-list-table :deep(.el-table__cell) {
  font-size: 12px;
}

.al-preview-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.al-preview-table :deep(.el-table__header th) {
  padding: 4px 0;
  font-size: 10px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-blank);
}

.al-preview-table :deep(.el-table__body td) {
  padding: 3px 0;
  font-size: 11px;
}

.al-preview-table :deep(.el-table__body-wrapper) {
  max-height: 148px;
  overflow-y: auto;
}

@media (max-width: 420px) {
  .al-grid {
    grid-template-columns: 1fr;
  }
}

.plating-jig-master-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid color-mix(in oklab, var(--el-color-success) 28%, var(--el-border-color-lighter));
  box-shadow:
    0 12px 32px color-mix(in oklab, var(--el-color-success) 12%, transparent),
    0 4px 16px rgba(15, 23, 42, 0.08);
}

.plating-jig-master-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 12px 14px 10px;
  border-bottom: 1px solid color-mix(in oklab, var(--el-color-success-light-7) 50%, var(--el-border-color-lighter));
  background: linear-gradient(
    90deg,
    color-mix(in oklab, var(--el-color-success-light-9) 70%, #fff),
    var(--el-fill-color-blank) 72%
  );
}

.plating-jig-master-dialog :deep(.el-dialog__body) {
  padding: 10px 12px 8px;
  background: linear-gradient(180deg, #f8fffe 0%, var(--el-bg-color) 100%);
}

.plating-jig-master-dialog :deep(.el-dialog__footer) {
  padding: 6px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.pjm-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.pjm-header__icon-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(145deg, #34d399 0%, var(--el-color-success) 55%, #059669 100%);
  box-shadow: 0 4px 12px color-mix(in oklab, var(--el-color-success) 35%, transparent);
}

.pjm-header__icon {
  font-size: 20px;
  color: #fff;
}

.pjm-header-title {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: color-mix(in oklab, #065f46 55%, var(--el-text-color-primary));
}

.pjm-header__sub {
  margin: 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.pjm-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pjm-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  padding: 7px 9px;
  border-radius: 10px;
  border: 1px solid color-mix(in oklab, var(--el-color-success) 22%, var(--el-border-color-lighter));
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.pjm-search {
  flex: 1 1 160px;
  min-width: 140px;
}

.pjm-search :deep(.el-input__wrapper) {
  box-shadow: 0 1px 2px rgba(31, 56, 88, 0.05) inset;
}

.pjm-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.pjm-btn {
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(31, 56, 88, 0.06);
}

.pjm-btn__icon {
  margin-right: 3px;
  font-size: 13px;
}

.pjm-btn--primary {
  border: 1px solid color-mix(in oklab, var(--el-color-success-dark-2) 40%, var(--el-border-color));
  background: linear-gradient(
    180deg,
    color-mix(in oklab, var(--el-color-success-light-3) 35%, #fff) 0%,
    var(--el-color-success) 100%
  );
  box-shadow: 0 2px 6px color-mix(in oklab, var(--el-color-success) 28%, transparent);
}

.pjm-btn--secondary {
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, #fff 0%, var(--el-fill-color-light) 100%);
  color: var(--el-text-color-regular);
}

.pjm-table-card {
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  background: #fff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.pjm-table {
  width: 100%;
}

.pjm-table :deep(.el-table__header th) {
  padding: 5px 0;
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  background: linear-gradient(
    180deg,
    var(--el-fill-color-light) 0%,
    color-mix(in oklab, var(--el-color-primary-light-9) 40%, var(--el-fill-color-light)) 100%
  );
}

.pjm-table :deep(.el-table__body td) {
  padding: 4px 0;
  font-size: 12px;
}

.pjm-qty {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-success-dark-2);
}

.pjm-table :deep(.pjm-op-col .cell) {
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.pjm-row-edit.el-button {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 4px;
  font-weight: 600;
}

.pjm-row-edit .el-icon {
  font-size: 13px;
}

.pjm-footer {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.pjm-close-btn.el-button {
  min-width: 88px;
  height: 32px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: linear-gradient(180deg, #fff 0%, var(--el-fill-color-light) 100%);
}

.pjm-status-toggle {
  flex-wrap: nowrap;
}

.pjm-status-toggle :deep(.el-radio-button__inner) {
  padding: 4px 8px;
  font-size: 11px;
}

.print-range-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 45%, var(--el-border-color-lighter));
  box-shadow:
    0 12px 32px color-mix(in oklab, var(--el-color-primary) 12%, transparent),
    0 4px 16px rgba(15, 23, 42, 0.08);
}

.print-range-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 10px 14px 8px;
  border-bottom: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 40%, var(--el-border-color-lighter));
  background: linear-gradient(
    90deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 65%, #fff),
    var(--el-fill-color-blank) 72%
  );
}

.print-range-dialog :deep(.el-dialog__body) {
  padding: 10px 14px 8px;
}

.print-range-dialog :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.print-range-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.print-range-header__icon-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(145deg, #60a5fa 0%, var(--el-color-primary) 55%, #1d4ed8 100%);
  box-shadow: 0 3px 10px color-mix(in oklab, var(--el-color-primary) 30%, transparent);
}

.print-range-header__icon {
  font-size: 18px;
  color: #fff;
}

.print-range-header__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
}

.print-range-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.print-range-summary {
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--el-color-primary);
  text-align: center;
  border-radius: 8px;
  background: color-mix(in oklab, var(--el-color-primary-light-9) 75%, #fff);
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 45%, var(--el-border-color-lighter));
}

.print-range-form {
  margin: 0;
}

.print-range-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: stretch;
  gap: 8px;
}

.print-range-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 8px 9px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, #fff 0%, var(--el-fill-color-blank) 100%);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.print-range-block__tag {
  display: inline-flex;
  align-self: flex-start;
  height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.print-range-block__tag--start {
  color: var(--el-color-success-dark-2);
  background: color-mix(in oklab, var(--el-color-success-light-9) 85%, #fff);
  border: 1px solid color-mix(in oklab, var(--el-color-success-light-7) 55%, transparent);
}

.print-range-block__tag--end {
  color: var(--el-color-warning-dark-2);
  background: color-mix(in oklab, var(--el-color-warning-light-9) 85%, #fff);
  border: 1px solid color-mix(in oklab, var(--el-color-warning-light-7) 55%, transparent);
}

.print-range-block__fields {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.print-range-flow__sep {
  display: flex;
  align-items: center;
  padding-top: 28px;
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
  color: var(--el-text-color-secondary);
}

.print-range-field {
  margin-bottom: 0;
}

.print-range-field :deep(.el-form-item__label) {
  padding-bottom: 1px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.print-range-date,
.print-range-lap-select,
.print-range-lap-num {
  width: 100%;
}

.print-range-lap-num :deep(.el-input-number) {
  width: 100%;
}

.print-range-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.print-range-footer__cancel.el-button {
  font-weight: 600;
  border-radius: 8px;
}

.print-range-footer__submit.el-button {
  min-width: 100px;
  font-weight: 700;
  letter-spacing: 0.03em;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-dark-2) 50%, var(--el-border-color));
  background: linear-gradient(
    180deg,
    color-mix(in oklab, var(--el-color-primary-light-3) 30%, #fff) 0%,
    var(--el-color-primary) 48%,
    color-mix(in oklab, var(--el-color-primary-dark-2) 88%, #000) 100%
  );
  box-shadow: 0 2px 8px color-mix(in oklab, var(--el-color-primary) 32%, transparent);
}

.print-range-footer__submit-icon {
  margin-right: 4px;
  font-size: 14px;
}

@media (max-width: 480px) {
  .print-range-flow {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }

  .print-range-flow__sep {
    justify-content: center;
    padding: 0;
  }
}

.board-product-pick-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 12px 16px 0;
}

.board-product-pick-dialog :deep(.el-dialog__body) {
  padding: 8px 16px 4px;
}

.board-product-pick-dialog :deep(.el-dialog__footer) {
  padding: 8px 16px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.bpp-header-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
}

.bpp-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bpp-context {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(
    135deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 80%, #fff) 0%,
    var(--el-fill-color-blank) 100%
  );
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 55%, var(--el-border-color-lighter));
}

.bpp-context__machine {
  font-size: 13px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3;
  word-break: break-all;
}

.bpp-context__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-end;
}

.bpp-tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 7px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.bpp-tag--warn {
  color: var(--el-color-warning-dark-2);
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-7);
}

.bpp-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.bpp-form :deep(.el-form-item__label) {
  padding-bottom: 2px;
  line-height: 1.2;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.bpp-field--qty :deep(.el-form-item__content) {
  line-height: 1;
}

.bpp-select {
  width: 100%;
}

.bpp-select :deep(.el-select__wrapper) {
  min-height: 32px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}

.bpp-actions-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
}

.bpp-field--qty {
  flex: 0 0 auto;
}

.bpp-qty-input {
  width: 108px;
}

.bpp-qty-input :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.bpp-filter {
  margin: 0 0 2px;
  height: 32px;
  align-self: flex-end;
}

.bpp-filter :deep(.el-checkbox__label) {
  font-size: 12px;
  color: var(--el-text-color-regular);
  padding-left: 6px;
}

.bpp-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.bpp-footer__cancel {
  margin-right: auto;
  padding-left: 4px;
  padding-right: 4px;
}

.jig-drop-qty-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 12px 16px 0;
}

.jig-drop-qty-dialog :deep(.el-dialog__body) {
  padding: 8px 16px 4px;
}

.jig-drop-qty-dialog :deep(.el-dialog__footer) {
  padding: 8px 16px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.lap-time-edit-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 10px 14px 0;
}

.lap-time-edit-dialog :deep(.el-dialog__body) {
  padding: 6px 14px 2px;
}

.lap-time-edit-dialog :deep(.el-dialog__footer) {
  padding: 6px 14px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.lap-time-edit-dialog .jd-body {
  gap: 6px;
}

.lap-time-edit-dialog .jig-drop-dialog-hint {
  margin: 0 0 6px;
  font-size: 11px;
  line-height: 1.35;
}

.lap-time-edit-dialog .jd-form :deep(.el-form-item__label) {
  padding-bottom: 1px;
}

.lap-time-edit-dialog .jd-field {
  margin-bottom: 0;
}

.jd-header-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--el-text-color-primary);
}

.jd-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.jd-context {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(
    135deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 80%, #fff) 0%,
    var(--el-fill-color-blank) 100%
  );
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 55%, var(--el-border-color-lighter));
}

.jd-context__machine {
  font-size: 13px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3;
  word-break: break-all;
}

.jd-context__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-end;
}

.jd-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.jd-tag--accent {
  color: var(--el-color-primary);
  background: color-mix(in oklab, var(--el-color-primary-light-9) 70%, #fff);
  border-color: color-mix(in oklab, var(--el-color-primary-light-5) 40%, var(--el-border-color-lighter));
}

.jd-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.jd-form :deep(.el-form-item__label) {
  padding-bottom: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  line-height: 1.3;
}

.jd-qty-input {
  width: 100%;
}

.jd-qty-input :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.jd-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.jd-footer__cancel {
  margin-right: auto;
  padding-left: 4px;
  padding-right: 4px;
  color: var(--el-text-color-secondary);
}

.product-assign-order-item :deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
}

.product-assign-order-item :deep(.el-radio-button) {
  width: 100%;
}

.product-assign-order-item :deep(.el-radio-button__inner) {
  width: 100%;
  white-space: normal;
  line-height: 1.35;
  padding: 8px 10px;
}

.lap-board-outer {
  --lap-board-head-h: 34px;
  --lap-board-lap-row-h: 38px;
  --lap-board-visible-laps: 11;
  --lap-board-op-col-w: 88px;
  width: 100%;
  max-width: 100%;
  max-height: calc(var(--lap-board-head-h) + var(--lap-board-visible-laps) * var(--lap-board-lap-row-h));
  overflow: auto;
  scrollbar-gutter: stable;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, var(--el-border-color) 70%, var(--el-border-color-lighter));
  background: linear-gradient(180deg, color-mix(in oklab, var(--el-fill-color-light) 35%, var(--el-bg-color)) 0%, var(--el-bg-color) 20%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.lap-board-layout {
  display: flex;
  flex-direction: column;
  width: max-content;
  min-width: 100%;
}

.lap-board-row {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr) var(--lap-board-op-col-w);
  width: 100%;
  align-items: stretch;
  border-bottom: 1px solid color-mix(in oklab, var(--el-border-color-lighter) 75%, var(--el-border-color));
}

.lap-board-row:last-child {
  border-bottom: none;
}

.lap-rail-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  padding: 4px 6px 4px 4px;
  box-sizing: border-box;
  position: sticky;
  left: 0;
  z-index: 2;
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  box-shadow: 2px 0 8px rgba(31, 50, 81, 0.08);
}

.lap-board-row--head {
  position: sticky;
  top: 0;
  z-index: 4;
  background: color-mix(in oklab, var(--el-fill-color-light) 68%, var(--el-bg-color));
}

.lap-board-row--head .lap-rail-cell,
.lap-board-row--head .lap-board-grid,
.lap-board-row--head .lap-op-cell {
  min-height: var(--lap-board-head-h);
}

.lap-rail-head {
  z-index: 5;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: color-mix(in oklab, var(--el-text-color-primary) 72%, var(--el-text-color-secondary));
  background: var(--el-fill-color-light);
}

.lap-board-row--head .lap-col-head {
  align-self: stretch;
  min-height: 100%;
  background: var(--el-fill-color-light);
}

.lap-board-row--date .lap-rail-cell,
.lap-board-row--date .lap-board-grid,
.lap-board-row--date .lap-op-cell {
  min-height: 28px;
}

.lap-board-row--lap .lap-rail-cell,
.lap-board-row--lap .lap-board-grid,
.lap-board-row--lap .lap-op-cell {
  min-height: var(--lap-board-lap-row-h);
}

.lap-rail-date {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-color-primary);
  background: color-mix(in oklab, var(--el-color-primary-light-9) 85%, var(--el-bg-color));
}

.lap-rail-lap {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-blank);
}

.lap-rail-lap--jig-drop {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 65%, var(--el-fill-color-blank));
}

.lap-board-grid {
  display: grid;
  align-items: stretch;
  gap: 0;
  width: max-content;
  min-width: 100%;
  box-sizing: border-box;
}

.lap-board-head {
  margin-bottom: 0;
  overflow: hidden;
  border-bottom: none;
  background: var(--el-bg-color);
}

.lap-board-body-row {
  background: var(--el-bg-color);
  height: 100%;
}

.lap-board-date-row,
.lap-date-scroll-row {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 72%, var(--el-bg-color));
  height: 100%;
}

.lap-date-band-scroll {
  grid-column: 1 / -1;
  min-height: 28px;
  background: color-mix(in oklab, var(--el-color-primary-light-9) 45%, var(--el-bg-color));
}

.lap-date-memo-zone {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 28px;
  padding: 4px 10px;
  box-sizing: border-box;
  cursor: text;
  user-select: none;
}

.lap-date-memo-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.35;
  white-space: pre-wrap;
  word-break: break-word;
}

.lap-date-memo-placeholder {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-style: italic;
}

.lap-board-row--date .lap-board-grid:hover .lap-date-memo-placeholder {
  color: var(--el-color-primary);
}

.lap-col-head {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px 2px;
  font-size: 9px;
  font-weight: 400;
  color: color-mix(in oklab, var(--el-text-color-primary) 72%, var(--el-text-color-secondary));
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

.lap-col-head {
  flex-direction: column;
  gap: 0;
  line-height: 1.05;
}

.lap-col-head-range {
  grid-column: 1 / -1;
  position: relative;
  display: block;
  font-size: 8.5px;
  font-weight: 600;
  color: #1f5fd6;
  line-height: 1.05;
  padding: 2px 3px;
  min-height: 20px;
  border-top: 1px solid color-mix(in oklab, var(--el-color-primary-light-7) 45%, var(--el-border-color-lighter));
  background: linear-gradient(180deg, color-mix(in oklab, var(--el-color-primary-light-9) 38%, var(--el-fill-color-light)) 0%, var(--el-fill-color-light) 95%);
}

.lap-col-head-range-mark {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  display: inline-block;
  min-width: 1ch;
  text-align: center;
  white-space: nowrap;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.75);
}

.lap-col-head-digits {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  max-width: 100%;
  overflow: hidden;
}

.lap-col-head-digit {
  font-size: 8.5px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  color: #1f5fd6;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.72);
}

.lap-col-head--truncated .lap-col-head-digit {
  opacity: 0.92;
}

.lap-board-grid > *:last-child {
  border-right: none;
}

.lap-label-no {
  white-space: nowrap;
}

.lap-label-time {
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: color-mix(in oklab, var(--el-color-primary) 65%, var(--el-text-color-secondary));
  white-space: nowrap;
}

.lap-label-time--editable {
  cursor: pointer;
  text-decoration: underline dotted color-mix(in oklab, var(--el-color-primary) 55%, transparent);
  text-underline-offset: 2px;
}

.lap-label-time--empty {
  color: var(--el-text-color-placeholder);
  font-weight: 600;
  text-decoration: none;
}

.lap-row-op-btn {
  margin-top: 0;
  padding: 0;
  min-height: 24px;
}

.lap-op-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 6px;
  box-sizing: border-box;
  min-width: var(--lap-board-op-col-w);
  max-width: var(--lap-board-op-col-w);
  position: sticky;
  right: 0;
  z-index: 8;
  border-left: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  box-shadow: -2px 0 8px rgba(31, 50, 81, 0.08);
}

.lap-op-head {
  z-index: 6;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: color-mix(in oklab, var(--el-text-color-primary) 72%, var(--el-text-color-secondary));
  background: var(--el-fill-color-light);
}

.lap-op-date {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 85%, var(--el-bg-color));
}

.lap-op-lap {
  background: var(--el-fill-color-blank);
}

.lap-merged-host {
  grid-column: 1 / -1;
  display: grid;
  align-items: stretch;
  min-height: 100%;
  height: 100%;
  box-sizing: border-box;
  border-right: none;
  overflow: hidden;
}

.lap-merged-seg {
  position: relative;
  min-width: 0;
  max-width: 100%;
  max-inline-size: 100%;
  padding: 3px 4px;
  margin: 2px 0;
  box-sizing: border-box;
  border: 0.5px solid rgba(48, 67, 96, 0.2);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 0.5px 0 rgba(255, 255, 255, 0.45);
}

.lap-merged-seg--manual {
  outline: 2px solid #fa8c16;
  outline-offset: -1px;
  z-index: 1;
}

.lap-merged-seg--rush {
  outline: 2px solid #cf1322;
  outline-offset: -1px;
  z-index: 1;
}

.lap-merged-seg--board-draggable {
  cursor: grab;
  user-select: none;
}

.lap-merged-seg--board-draggable:active {
  cursor: grabbing;
}

.lap-merged-seg--ghost {
  opacity: 0.5;
}

.lap-merged-tail-item.lap-merged-seg--board-draggable {
  cursor: grab;
}

.lap-merged-label-stack {
  position: absolute;
  top: 2px;
  right: 3px;
  left: 3px;
  bottom: 2px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 2px;
  pointer-events: none;
  overflow: visible;
}

.lap-merged-text {
  line-height: 1.25;
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-break: break-word;
  max-width: 100%;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.lap-merged-text--jig {
  align-self: flex-end;
  font-size: 9px;
  text-align: right;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
  word-break: normal;
  padding: 0 2px;
  box-sizing: border-box;
}

.lap-merged-text--calc {
  position: static;
  left: auto;
  right: auto;
  bottom: auto;
  top: auto;
  transform: none;
  font-size: 11px;
  text-align: left;
  font-weight: 700;
  color: color-mix(in oklab, var(--el-color-primary) 75%, var(--el-text-color-primary));
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
  word-break: normal;
  padding: 0 2px;
  box-sizing: border-box;
}

.lap-merged-product-label--alt {
  color: var(--el-color-danger);
  font-weight: 700;
}

.lap-merged-product-label--depleted {
  color: var(--el-color-danger);
  font-weight: 700;
}

.lap-merged-product-label--force-red {
  color: var(--el-color-danger);
  font-weight: 700;
}

.lap-merged-product-sep {
  color: var(--el-text-color-regular);
  font-weight: 400;
}

.lap-merged-seg--product-drop {
  outline: 2px dashed color-mix(in oklab, var(--el-color-primary) 55%, transparent);
  outline-offset: -2px;
}

.lap-merged-seg--product-drop-hover {
  background: color-mix(in oklab, var(--el-color-primary-light-8) 45%, transparent) !important;
}

.lap-merged-tail {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  max-width: 100%;
  padding: 2px;
  box-sizing: border-box;
  border-left: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}

.lap-merged-tail-item {
  position: relative;
  flex: 0 0 auto;
  min-width: 0;
  max-width: 100%;
  min-height: 22px;
  padding: 2px 3px;
  border-radius: 4px;
  border: 0.5px solid rgba(48, 67, 96, 0.2);
  box-sizing: border-box;
  overflow: hidden;
}

.lap-merged-tail-item .lap-merged-text {
  display: block;
  width: 100%;
  box-sizing: border-box;
}

.lap-col {
  min-width: 0;
  max-width: 100%;
  height: 100%;
  border-right: 1px solid var(--el-border-color-lighter);
  padding: 2px 1px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.lap-col--empty .lap-track--grid {
  opacity: 0.55;
}

.sched-color-0 { background: #dbe8d4; }
.sched-color-1 { background: #c9dce8; }
.sched-color-2 { background: #edd9c8; }
.sched-color-3 { background: #d4cce8; }
.sched-color-4 { background: #c9e4df; }
.sched-color-5 { background: #e5d9b8; }
.sched-color-6 { background: #cdd5e0; }
.sched-color-7 { background: #e0cfcf; }
.sched-color-8 { background: #d7e7f8; }
.sched-color-9 { background: #d8f0e2; }
.sched-color-10 { background: #f8e3d4; }
.sched-color-11 { background: #e6dcf8; }
.sched-color-12 { background: #d6ecef; }
.sched-color-13 { background: #f2e6c9; }
.sched-color-14 { background: #d8dbe9; }
.sched-color-15 { background: #f0dadd; }
.sched-color-16 { background: #d4eaf0; }
.sched-color-17 { background: #e2edd4; }
.sched-color-18 { background: #f3dfcf; }
.sched-color-19 { background: #ddd5ee; }
.sched-color-20 { background: #cfe8e2; }
.sched-color-21 { background: #ece2bf; }
.sched-color-22 { background: #d3d9e6; }
.sched-color-23 { background: #ebd8d8; }

.lap-track--grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  height: 100%;
  gap: 2px;
  border-radius: 4px;
  overflow: hidden;
  background: color-mix(in oklab, var(--el-fill-color-light) 68%, var(--el-fill-color));
}

.lap-segment--cell {
  position: relative;
  min-width: 0;
  max-width: 100%;
  min-height: 20px;
  padding: 2px 4px;
  border-radius: 2px;
  overflow: hidden;
}

.lap-segment--manual {
  outline: 2px solid #fa8c16;
  outline-offset: -1px;
  z-index: 1;
}

.lap-segment--rush {
  outline: 2px solid #cf1322;
  outline-offset: -1px;
  z-index: 1;
}

.board-legend {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.lap-segment-text {
  display: block;
  position: static;
  top: auto;
  right: auto;
  left: auto;
  font-size: 9.5px;
  line-height: 1.18;
  text-align: right;
  white-space: normal;
  overflow: visible;
  text-overflow: clip;
  max-width: none;
  word-break: break-word;
  box-sizing: border-box;
  font-weight: 600;
  color: var(--el-text-color-primary);
  pointer-events: none;
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
}

.board-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  min-height: 72px;
}

.mb-0 {
  margin-bottom: 0;
}

.jig-meta-pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.jig-card-list-wrap {
  min-height: 44px;
  padding-right: 30px;
  padding-bottom: 2px;
}


.jig-card-list {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 6px;
}

.jig-pick-card {
  flex: 0 0 120px;
  width: 120px;
  max-width: 120px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 4px;
  border-radius: 6px;
  border: 1px solid color-mix(in oklab, var(--el-color-success) 36%, var(--el-border-color-lighter));
  background: color-mix(in oklab, var(--el-color-success-light-9) 72%, var(--el-bg-color));
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  cursor: grab;
  user-select: none;
  transition:
    border-color 120ms ease,
    box-shadow 120ms ease,
    transform 120ms ease;
}

.jig-pick-card:hover {
  border-color: color-mix(in oklab, var(--el-color-success) 55%, var(--el-border-color));
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
}

.jig-pick-card:active {
  cursor: grabbing;
}

.jig-pick-card--filter-match {
  border-color: color-mix(in oklab, var(--el-color-warning) 58%, var(--el-border-color-lighter));
  background: color-mix(in oklab, var(--el-color-warning-light-9) 82%, var(--el-bg-color));
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--el-color-warning) 28%, transparent);
}

.jig-pick-card--filter-dim {
  opacity: 0.32;
  filter: grayscale(0.35);
}

.jig-pick-card__label {
  display: block;
  width: 100%;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.3;
  text-align: center;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.jig-card-list-empty,
.jig-card-list-hint {
  margin: 6px 0 0;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.jig-card-list-empty--filter {
  color: var(--el-color-warning-dark-2);
}

.jig-card-list-hint {
  color: var(--el-text-color-secondary);
}

@media (max-width: 900px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .header-badge {
    align-self: flex-start;
  }
}
</style>

<style lang="scss">
.prod-list-time-popper.el-popper {
  padding: 10px 12px !important;
}

.prod-list-time-pop__title {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  word-break: break-word;
}

.prod-list-time-pop__subtitle {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.prod-list-time-pop__list {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
}

.prod-list-time-pop__list li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
  padding: 4px 0;
  border-top: 1px solid var(--el-border-color-lighter);
  font-size: 12px;
  line-height: 1.4;
}

.prod-list-time-pop__list li:first-child {
  border-top: none;
  padding-top: 0;
}

.prod-list-time-pop__lap {
  font-weight: 600;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.prod-list-time-pop__range {
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-regular);
}

.prod-list-time-pop__qty {
  margin-left: auto;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.prod-list-time-pop__empty {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.jig-pick-card-tooltip-popper.el-popper {
  max-width: min(360px, 92vw);
}

.jig-pick-card-tooltip {
  max-width: 340px;
  font-size: 12px;
  line-height: 1.45;
}

.jig-pick-card-tooltip__head {
  font-weight: 600;
  margin-bottom: 6px;
}

.jig-pick-card-tooltip__section {
  font-weight: 600;
  font-size: 11px;
  margin-bottom: 4px;
  padding-top: 4px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.jig-pick-card-tooltip__list {
  margin: 0;
  padding: 0 0 0 1.1em;
  max-height: 220px;
  overflow-y: auto;
}

.jig-pick-card-tooltip__list li {
  margin: 2px 0;
}

.jig-pick-card-tooltip__empty {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}
</style>

<style lang="scss">
.bpp-select-popper.el-select__popper {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.1);
}

.bpp-select-popper .el-select-group__title {
  padding: 6px 12px 2px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--el-text-color-secondary);
}

.bpp-select-popper .el-select-dropdown__item {
  font-size: 12px;
  line-height: 1.35;
  padding-top: 6px;
  padding-bottom: 6px;
}
</style>
