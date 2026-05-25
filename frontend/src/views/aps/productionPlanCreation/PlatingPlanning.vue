<template>
  <div class="plating-planning-page">
    <header class="page-header">
      <h1 class="page-title">メッキ計画作成（作成中）</h1>
      <nav class="page-flow" aria-label="作業手順">
        <span class="flow-i">① 投入ボード</span>
        <span class="flow-dot" />
        <span class="flow-i">② 在庫</span>
      </nav>
    </header>

    <el-card shadow="never" class="pp-card pp-card--jig">
      <template #header>
        <div class="section-head-row">
          <span class="pp-card-title">メッキ治具</span>
          <div class="toolbar-inline">
            <el-form-item label="作業日" class="mb-0 pp-form-compact">
              <el-date-picker
                v-model="draftWorkDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="作業日を選択"
                size="small"
                class="pp-date"
              />
            </el-form-item>
            <el-button size="small" @click="void loadJigAvailability()">再読込</el-button>
            <el-button type="primary" size="small" :loading="savingJigAvailability" @click="saveJigAvailabilityForm">
              保存
            </el-button>
          </div>
        </div>
      </template>
      <div class="jig-card-meta">
        <span class="jig-meta-pill">作業日：{{ draftWorkDate || '—' }}</span>
        <span class="jig-meta-pill">対象治具：{{ jigAvailabilityRows.length }} 件</span>
        <span class="jig-meta-pill jig-meta-pill--hint">使用可能本数は設備マスタ（available_qty）と連携</span>
      </div>
      <div v-loading="loadingJigAvailability" class="jig-card-list-wrap">
        <div class="jig-card-list">
          <div
            v-for="row in jigAvailabilityRows"
            :key="row.plating_machine"
            class="jig-pick-card"
            draggable="true"
            :title="`${row.plating_machine}・使用可能${Math.max(0, Math.floor(Number(row.available_qty) || 0))}本・①ボードへドラッグで投入`"
            @dragstart="onJigCardDragStart($event, row)"
            @dragend="onJigCardDragEnd"
          >
            <span class="jig-pick-card__label">{{ formatJigPickLabel(row) }}</span>
          </div>
        </div>
        <p v-if="!loadingJigAvailability && jigAvailabilityRows.length === 0" class="jig-card-list-empty">
          データがありません
        </p>
        <p v-else-if="jigAvailabilityRows.length > 0" class="jig-card-list-hint">
          カードを①メッキ投入スケジュールボードへドラッグし、本数を指定して投入
        </p>
      </div>
    </el-card>

    <el-card shadow="never" class="pp-card pp-card--board">
      <template #header>
        <div class="section-head-row">
          <span class="pp-card-title">① メッキ投入スケジュールボード</span>
          <div class="toolbar-inline">
            <el-button type="primary" size="small" @click="openAppendLayoutDialog">
              追加レイアウト
            </el-button>
            <el-button size="small" :disabled="!canUseLapCopy" @click="openLapCopyDialog">周目コピー</el-button>
            <el-button size="small" @click="clearSchedule">ボードをクリア</el-button>
            <el-button
              size="small"
              type="info"
              plain
              :icon="Printer"
              :disabled="!hasPrintableScheduleRows"
              @click="printScheduleBoard"
            >
              印刷
            </el-button>
            <span class="board-legend">オレンジ枠＝標準配置から変更</span>
          </div>
        </div>
      </template>

      <div class="board-cond-banner board-cond-banner--view-range">
        <span class="board-cond-label">表示期間</span>
        <span class="board-cond-val"><strong>{{ boardViewRangeLabel }}</strong></span>
        <span class="board-cond-sep">（本日-2日〜+3日）</span>
      </div>
      <div v-if="layoutBoardReady" class="board-cond-banner">
        <span class="board-cond-label">レイアウト</span>
        <span class="board-cond-val">計画 <strong>{{ layoutBlocksSummary }}</strong></span>
        <span class="board-cond-sep">／</span>
        <span class="board-cond-val">1周 <strong>{{ layoutJigsPerLap }}</strong> 本</span>
        <span class="board-cond-sep">／</span>
        <span class="board-cond-val">計 <strong>{{ layoutMaxLaps }}</strong> 周</span>
        <span class="board-cond-sep">／</span>
        <span class="board-cond-hint">②の製品を治具枠へドラッグで割当・枠内ドラッグで並べ替え</span>
      </div>

      <div class="kpi-grid">
        <div class="kpi-chip">
          <span class="kpi-chip-l">総枠数</span>
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
          <span class="kpi-chip-v">{{ scheduleCards.length }}</span>
        </div>
        <div class="kpi-chip">
          <span class="kpi-chip-l">計画数量</span>
          <span class="kpi-chip-v">{{ kpi.totalPlannedQty }}</span>
        </div>
      </div>

      <div
        class="lap-board"
        :class="{ 'lap-board--jig-drop': jigBoardDragActive }"
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
                  <div v-for="h in lapColumnHeaders" :key="h.i" class="lap-col-head">
                    <span class="lap-col-head-n">{{ h.i }}</span>
                    <span class="lap-col-head-s">本</span>
                  </div>
                </div>
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
                  >
                    <div class="lap-date-band-scroll" />
                  </div>
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
                    <span v-if="lapTimeRangeLabel(item.row.lap_no)" class="lap-label-time">{{
                      lapTimeRangeLabel(item.row.lap_no)
                    }}</span>
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
                <div class="lap-merged-host" :style="innerMergedGridStyle">
                  <div
                    v-for="ms in item.row.mergedLeft"
                    :key="ms.key"
                    class="lap-merged-seg"
                    :class="[
                      'sched-color-' + schedColorIndexForProductCd(ms.product_cd),
                      ms.boardMark === 'manual' ? 'lap-merged-seg--manual' : ms.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                      isJigProductCd(ms.product_cd) ? 'lap-merged-seg--board-draggable' : '',
                      draggingInventoryRow && isJigProductCd(ms.product_cd) ? 'lap-merged-seg--product-drop' : '',
                      productDropHoverBlockKey === ms.key ? 'lap-merged-seg--product-drop-hover' : '',
                    ]"
                    :style="{ gridColumn: `${ms.startCol} / span ${ms.span}`, gridRow: '1' }"
                    :data-block-ids="ms.cardIds.join(',')"
                    @dragover.prevent.stop="onProductToJigBlockDragOver($event, ms)"
                    @dragleave.stop="onProductToJigBlockDragLeave"
                    @drop.prevent.stop="onProductToJigBlockDrop($event, ms, item.row.lap_no)"
                    @dblclick.stop="onBoardMergedSegDblClick(ms, item.row.lap_no)"
                  >
                    <div class="lap-merged-label-stack" :title="boardMergedSegTitle(ms)">
                      <span class="lap-merged-text lap-merged-text--jig">{{
                        formatPlatingBoardLabel(ms.plating_machine, ms.span)
                      }}</span>
                      <span v-if="formatJigBlockProductCalc(ms)" class="lap-merged-text lap-merged-text--calc">{{
                        formatJigBlockProductCalc(ms)
                      }}</span>
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
                        'sched-color-' + schedColorIndexForProductCd(tc.product_cd),
                        tc.boardMark === 'manual' ? 'lap-merged-seg--manual' : tc.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                        isJigProductCd(tc.product_cd) ? 'lap-merged-seg--board-draggable' : '',
                      ]"
                      :data-card-id="tc.id"
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
                        'sched-color-' + schedColorIndexForProductCd(seg.product_cd),
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
                </div>
              </template>
            </div>
          </div>
        </template>
        <div v-else class="board-empty">
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
        <div class="section-head-row">
          <span class="pp-card-title pp-card-title--summary">② メッキ前在庫／見込数量（基準日は各ペインで指定）</span>
        </div>
      </template>
      <p class="summary-drag-hint">行を①の治具枠（例：J曲3段 (20)）へドラッグすると製品を割当し、生産数を表示します</p>

      <el-row :gutter="10" class="pair-row">
        <el-col :xs="24" :md="12" class="summary-col summary-col--left">
          <div class="pane-head pane-head--left">
            <div class="pane-head-top">
              <span class="pane-title">メッキ前在庫</span>
              <el-form-item label="基準日" class="mb-0 pp-form-compact pane-head-date-item">
                <el-date-picker
                  v-model="leftInventoryDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="基準日を選択"
                  size="small"
                  class="pp-date pp-date--pane"
                />
                <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftLeftInventoryDate(-1)" />
                <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftLeftInventoryDate(1)" />
              </el-form-item>
              <div class="pane-head-meta">
                <span class="pane-total-label">在庫合計</span>
                <span class="pane-total-value">{{ leftPrevInventoryTotal }}</span>
              </div>
            </div>
          </div>
          <el-table
            ref="leftTableRef"
            v-loading="loadingPair"
            class="pp-table pp-table--left"
            :data="leftRows"
            border
            stripe
            size="small"
            :height="TABLE_H"
            empty-text="データがありません"
          >
            <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
            <el-table-column prop="plating_machine" label="メッキ治具" width="120" show-overflow-tooltip />
            <el-table-column
              prop="plating_efficiency"
              label="掛け数"
              width="88"
              align="right"
              show-overflow-tooltip
            />
            <el-table-column prop="pre_plating_inventory" label="直前工程在庫" width="120" align="right" />
            <el-table-column label="必要治具本数" width="100" align="right">
              <template #default="{ row }">
                {{ calcRequiredJigCount(row) }}
              </template>
            </el-table-column>
          </el-table>
        </el-col>
        <el-col :xs="24" :md="12" class="summary-col summary-col--right">
          <div class="pane-head pane-head--right">
            <div class="pane-head-top">
              <span class="pane-title">翌日の見込数量</span>
              <el-form-item label="参照日" class="mb-0 pp-form-compact pane-head-date-item">
                <el-date-picker
                  v-model="rightGenDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="参照日を選択"
                  size="small"
                  class="pp-date pp-date--pane"
                />
                <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftRightGenDate(-1)" />
                <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftRightGenDate(1)" />
              </el-form-item>
              <div class="pane-head-meta">
                <span class="pane-total-label">見込合計</span>
                <span class="pane-total-value">{{ rightGenQtyTotal }}</span>
              </div>
            </div>
          </div>
          <el-table
            ref="rightTableRef"
            v-loading="loadingPair"
            class="pp-table pp-table--right"
            :data="rightRows"
            border
            stripe
            size="small"
            :height="TABLE_H"
            empty-text="データがありません"
          >
            <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip />
            <el-table-column prop="plating_machine" label="メッキ治具" width="120" show-overflow-tooltip />
            <el-table-column prop="plating_efficiency" label="掛け数" width="100" align="right" show-overflow-tooltip />
            <el-table-column prop="gen_qty" label="見込数量" width="100" align="right" />
            <el-table-column label="必要治具本数" width="100" align="right">
              <template #default="{ row }">
                {{ calcRequiredJigCountFromQty(row.gen_qty, row.plating_efficiency) }}
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </el-card>

    <el-dialog
      v-model="jigDropDialogVisible"
      title="治具投入数量"
      width="420px"
      class="jig-drop-dialog"
      destroy-on-close
      @closed="resetJigDropDialog"
    >
      <template v-if="jigDropPending">
        <p class="jig-drop-dialog-name">{{ jigDropPending.plating_machine }}</p>
        <div class="jig-drop-dialog-meta">
          <span class="jig-meta-pill">第{{ lapDisplayNo(jigDropPending.target_lap) }}周目</span>
          <span class="jig-meta-pill">当該周 使用可能 {{ jigDropPending.available_max }} 本</span>
          <span class="jig-meta-pill">当該周 配置済 {{ jigDropPending.used_on_board }} 本</span>
          <span class="jig-meta-pill">今回最大 {{ jigDropQtyMax }} 本</span>
        </div>
        <p class="jig-drop-dialog-hint">
          第{{ lapDisplayNo(jigDropPending.target_lap) }}周目の空き枠へ順に配置します（他周目は別枠で再計算・例：20 本 → 当該周の 1〜20 本目）
        </p>
        <el-form-item label="投入本数" class="jig-drop-qty-item">
          <el-input-number
            v-model="jigDropQty"
            :min="1"
            :max="jigDropQtyMax"
            :step="1"
            controls-position="right"
            class="pp-input-num"
          />
        </el-form-item>
      </template>
      <template #footer>
        <el-button size="small" @click="jigDropDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" :disabled="jigDropQtyMax < 1" @click="confirmJigDropToBoard">確定</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="boardJigEditDialogVisible"
      title="ボード上の治具本数"
      width="420px"
      class="jig-drop-dialog"
      destroy-on-close
      @closed="resetBoardJigEditDialog"
    >
      <template v-if="boardJigEditPending">
        <p class="jig-drop-dialog-name">{{ boardJigEditPending.plating_machine }}</p>
        <p class="jig-drop-dialog-hint">第{{ lapDisplayNo(boardJigEditPending.lap_no) }}周目・現在 {{ boardJigEditPending.cardIds.length }} 本</p>
        <div class="jig-drop-dialog-meta">
          <span class="jig-meta-pill">当該周 使用可能 {{ getJigAvailMaxFromMaster(boardJigEditPending.plating_machine) }} 本</span>
          <span class="jig-meta-pill">変更後最大 {{ boardJigEditQtyMax }} 本</span>
        </div>
        <el-form-item label="本数" class="jig-drop-qty-item">
          <el-input-number
            v-model="boardJigEditQty"
            :min="1"
            :max="boardJigEditQtyMax"
            :step="1"
            controls-position="right"
            class="pp-input-num"
          />
        </el-form-item>
      </template>
      <template #footer>
        <el-button size="small" @click="boardJigEditDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" :disabled="boardJigEditQtyMax < 1" @click="confirmBoardJigQtyEdit">
          確定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="lapCopyDialogVisible"
      title="周目データのコピー"
      width="440px"
      class="tpl-dialog lap-copy-dialog"
      destroy-on-close
    >
      <p class="tpl-dialog-hint">指定した周目の割当を別の周目へ複製します（コピー先の既存データは上書きされます）。</p>
      <div class="tpl-compact-grid lap-copy-grid">
        <div class="tpl-field">
          <div class="tpl-field-label">コピー元</div>
          <el-select v-model="lapCopyFrom" size="small" class="lap-copy-select">
            <el-option
              v-for="opt in lapCopyLapOptions"
              :key="`from-${opt.value}`"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
        <div class="tpl-field">
          <div class="tpl-field-label">コピー先</div>
          <el-select v-model="lapCopyTo" size="small" class="lap-copy-select">
            <el-option
              v-for="opt in lapCopyLapOptions"
              :key="`to-${opt.value}`"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
      </div>
      <p class="jig-drop-dialog-hint">
        第{{ lapDisplayNo(lapCopyFrom) }}周目 → 第{{ lapDisplayNo(lapCopyTo) }}周目（{{ lapCopySourceCount }} 枠を複製）
      </p>
      <template #footer>
        <el-button size="small" @click="lapCopyDialogVisible = false">キャンセル</el-button>
        <el-button
          size="small"
          type="primary"
          :disabled="lapCopyFrom === lapCopyTo || lapCopySourceCount === 0"
          @click="confirmCopyLapSchedule"
        >
          コピー
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="templateDialogVisible"
      title="追加レイアウト"
      width="520px"
      class="tpl-dialog"
      destroy-on-close
    >
      <p class="tpl-dialog-hint">
        計画日・開始時刻・段数を指定し、①ボードの<strong>末尾に周目を追加</strong>します（既存の割当は保持）。治具投入はメッキ治具カードをボードへドラッグしてください。
      </p>
      <p v-if="layoutBoardReady && layoutMaxLaps > 0" class="tpl-dialog-append-note">
        現在 {{ layoutMaxLaps }} 周まで表示中。新規追加は各計画日の<strong>第1周目</strong>から（日付ごとに周番号をリセット）。
      </p>
      <div class="tpl-compact-grid tpl-compact-grid--schedule">
        <div class="tpl-field tpl-field--wide">
          <div class="tpl-field-label">計画日</div>
          <el-date-picker
            v-model="tplFormPlanDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="日付を選択"
            size="small"
            class="tpl-date"
          />
        </div>
        <div class="tpl-field">
          <div class="tpl-field-label">開始時刻</div>
          <el-time-picker
            v-model="tplFormStartTime"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="開始時刻"
            size="small"
            class="tpl-time"
          />
        </div>
        <div class="tpl-field">
          <div class="tpl-field-label">1段あたり（分）</div>
          <el-input-number
            v-model="tplFormMinutesPerLap"
            :min="1"
            :max="600"
            :step="5"
            controls-position="right"
            class="pp-input-num tpl-input-num"
          />
        </div>
        <div class="tpl-field">
          <div class="tpl-field-label">1周あたりの治具本数（列数）</div>
          <el-input-number
            v-model="tplFormJigsPerLap"
            :min="1"
            :max="300"
            :step="1"
            controls-position="right"
            class="pp-input-num tpl-input-num"
          />
        </div>
        <div class="tpl-field">
          <div class="tpl-field-label">ボード段数</div>
          <el-input-number
            v-model="tplFormMaxLaps"
            :min="1"
            :max="500"
            :step="1"
            controls-position="right"
            class="pp-input-num tpl-input-num"
          />
        </div>
      </div>
      <div v-if="tplLapSchedulePreview.length > 0" class="tpl-schedule-preview">
        <div class="tpl-schedule-preview-title">各段の予定時刻</div>
        <el-table :data="tplLapSchedulePreview" size="small" border stripe class="tpl-schedule-table">
          <el-table-column prop="board_lap_no" label="ボード周" width="64" align="center">
            <template #default="{ row }">第{{ row.board_lap_no }}周</template>
          </el-table-column>
          <el-table-column prop="lap_no" label="追加段" width="56" align="center">
            <template #default="{ row }">第{{ row.lap_no }}段</template>
          </el-table-column>
          <el-table-column prop="work_date_label" label="日付" width="100" align="center" />
          <el-table-column prop="start" label="開始" width="72" align="center" />
          <el-table-column prop="end" label="終了" width="72" align="center" />
        </el-table>
      </div>
      <template #footer>
        <el-button size="small" @click="templateDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" @click="confirmAppendLayout">追加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import Sortable from 'sortablejs'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Printer } from '@element-plus/icons-vue'
import { getProductionSummarysList } from '@/api/database'
import { getMachineList, updateMachine, type MachineListResponse } from '@/api/master/machineMaster'
import type { MachineItem } from '@/types/master'
import {
  createPlatingDraft,
  fetchPlatingDraftById,
  fetchLatestPlatingDraftByDate,
  updatePlatingDraft,
  type PlatingBoardCardBody,
  type PlatingBoardCardOut,
  type PlatingDraftItemBody,
  type PlatingDraftItemOut,
  type PlatingDraftOut,
} from '@/api/platingPlanning'

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

/** ①在庫ペインの日付ピッカー用ショートカット（JST） */
const platingSummaryDateShortcuts = [
  { text: '今日', value: () => dayjs().tz(TZ_JP).startOf('day').toDate() },
  { text: '昨日', value: () => dayjs().tz(TZ_JP).subtract(1, 'day').startOf('day').toDate() },
  { text: '明日', value: () => dayjs().tz(TZ_JP).add(1, 'day').startOf('day').toDate() },
]

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
    work_date: bc.work_date ?? null,
    lap_work_date: bc.lap_work_date ?? null,
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
  /** ボード表示用の周目（複数日マージ時は通し番号） */
  lap_no: number
  /** API 保存時の元 lap_no（draft 内） */
  persist_lap_no?: number
  /** 他 plan_date の draft から読み込んだ行 */
  source_draft_id?: number
  turn_seq: number
  colorIdx: number
  boardMark: BoardMark
}

const scheduleCards = ref<ScheduleCard[]>([])
const standardPositions = ref(new Map<string, { lap_no: number; turn_seq: number }>())
/** API から③ボードを復元する／読込でボードを空にするとき、deep watch による不要な自動保存を抑止 */
const isBoardHydratingFromApi = ref(false)

const TABLE_H = 340

const DEFAULT_JIGS_PER_LAP = 129

/** ①ボード既定表示：本日から -2 日〜 +3 日（JST） */
const BOARD_VIEW_DATE_OFFSET_MIN = -2
const BOARD_VIEW_DATE_OFFSET_MAX = 3

const boardViewRange = computed(() => {
  const today = todayYmdJapan()
  return {
    from: addDaysYmdJapan(today, BOARD_VIEW_DATE_OFFSET_MIN),
    to: addDaysYmdJapan(today, BOARD_VIEW_DATE_OFFSET_MAX),
  }
})

const boardViewRangeLabel = computed(() => {
  const { from, to } = boardViewRange.value
  return `${formatBoardDateLabel(from)}〜${formatBoardDateLabel(to)}`
})

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

function boardCardLapWorkDate(bc: PlatingBoardCardOut, planKey: string): string {
  return String(bc.lap_work_date || bc.work_date || planKey).slice(0, 10)
}

function isLapNoInBoardView(lapNo: number, scheduleByLap?: Map<number, LapScheduleSlot>): boolean {
  const map = scheduleByLap ?? new Map(buildGlobalLapSchedule().map((s) => [s.lap_no, s]))
  const wd = map.get(lapNo)?.work_date
  if (!wd) return true
  return isYmdInBoardView(wd)
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

function buildGlobalLapSchedule(): LapScheduleSlot[] {
  if (!layoutBoardReady.value) return []
  if (layoutBlocks.value.length === 0) {
    return buildLapScheduleRows(
      layoutPlanDate.value,
      layoutStartTime.value,
      layoutMinutesPerLap.value,
      layoutMaxLaps.value,
    )
  }
  const out: LapScheduleSlot[] = []
  for (const block of layoutBlocks.value) {
    const rows = buildLapScheduleRows(
      block.plan_date,
      block.start_time,
      block.minutes_per_lap,
      block.lap_count,
    )
    for (const r of rows) {
      out.push({ ...r, lap_no: block.base_lap_no + r.lap_no - 1 })
    }
  }
  return out.sort((a, b) => a.lap_no - b.lap_no).filter((s) => isYmdInBoardView(s.work_date))
}

function currentLayoutLapSchedule(): LapScheduleSlot[] {
  return buildGlobalLapSchedule()
}

/** 計画日（lap_work_date）ごとに 1 から振り直した表示用周番号 */
const lapDisplayNoMap = computed(() => {
  const map = new Map<number, number>()
  const byDate = new Map<string, number[]>()
  for (const s of buildGlobalLapSchedule()) {
    const list = byDate.get(s.work_date) ?? []
    list.push(s.lap_no)
    byDate.set(s.work_date, list)
  }
  for (const laps of byDate.values()) {
    const sorted = [...laps].sort((a, b) => a - b)
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
  return layoutBlocks.value
    .filter((b) => isYmdInBoardView(b.plan_date))
    .map((b) => `${formatBoardDateLabel(b.plan_date)}×${b.lap_count}`)
    .join('＋')
})

const tplLapSchedulePreview = computed(() => {
  const rows = buildLapScheduleRows(
    tplFormPlanDate.value,
    tplFormStartTime.value,
    tplFormMinutesPerLap.value,
    tplFormMaxLaps.value,
  )
  return rows.map((r) => ({ ...r, board_lap_no: r.lap_no }))
})

function syncLayoutBlocksFromDraftHeader() {
  const ml = layoutMaxLaps.value
  if (ml < 1) {
    layoutBlocks.value = []
    return
  }
  layoutBlocks.value = [
    {
      plan_date: layoutPlanDate.value,
      start_time: layoutStartTime.value,
      minutes_per_lap: layoutMinutesPerLap.value,
      jigs_per_lap: layoutJigsPerLap.value,
      lap_count: ml,
      base_lap_no: 1,
    },
  ]
}

function inferLayoutBlocksFromBoard(
  rawBoard: Array<{
    lap_no: number
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
  const maxLap = Math.max(
    header.max_laps,
    rawBoard.length > 0 ? Math.max(...rawBoard.map((b) => b.lap_no)) : 0,
    0,
  )
  if (maxLap < 1) return []

  const lapMeta = new Map<number, { wd: string; start: string }>()
  for (const bc of rawBoard) {
    const ln = bc.lap_no
    if (lapMeta.has(ln)) continue
    const wd = String(bc.lap_work_date || header.plan_date).slice(0, 10)
    const start = normalizeBoardStartTimeHm(bc.lap_start_time || header.board_start_time)
    lapMeta.set(ln, { wd, start })
  }

  const blocks: BoardLayoutBlock[] = []
  let i = 1
  while (i <= maxLap) {
    const meta = lapMeta.get(i)
    const wd = meta?.wd || header.plan_date
    const start = meta?.start || header.board_start_time
    let j = i
    while (j < maxLap) {
      const next = lapMeta.get(j + 1)
      const nextWd = next?.wd || wd
      if (nextWd !== wd) break
      j++
    }
    blocks.push({
      plan_date: wd,
      start_time: normalizeBoardStartTimeHm(start),
      minutes_per_lap: header.minutes_per_lap,
      jigs_per_lap: header.jigs_per_lap,
      lap_count: j - i + 1,
      base_lap_no: i,
    })
    i = j + 1
  }
  return blocks
}

function lapTimeRangeLabel(lapNo: number): string {
  const row = currentLayoutLapSchedule().find((r) => r.lap_no === lapNo)
  return row ? `${row.start}–${row.end}` : ''
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
  /** machines.efficiency（メッキ治具 = machine_name で突合） */
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
const leftTableRef = ref<any>(null)
const rightTableRef = ref<any>(null)

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
/** PUT 時の plan_date（草稿ヘッダー）。追加レイアウトの計画日とは別に固定 */
const draftRecordPlanDate = ref('')
const draggingSource = ref<DraftSourceItem | null>(null)
const loadingJigAvailability = ref(false)
const savingJigAvailability = ref(false)
const jigAvailabilityRows = ref<{ machine_id: number | null; plating_machine: string; available_qty: number }[]>([])
const jigDropDialogVisible = ref(false)
const jigDropPending = ref<{
  plating_machine: string
  available_max: number
  used_on_board: number
  target_lap: number
} | null>(null)
const jigDropQty = ref(1)
const jigDropQtyMax = ref(1)
const jigDropPreferLap = ref<number | null>(null)
const jigBoardDragActive = ref(false)
const jigDropHoverLap = ref<number | null>(null)
const draggingJigToBoard = ref<{
  machine_id: number | null
  plating_machine: string
  available_qty: number
} | null>(null)
const draggingInventoryRow = ref(false)
const productDropHoverBlockKey = ref<string | null>(null)
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
const lapCopyDialogVisible = ref(false)
const lapCopyFrom = ref(1)
const lapCopyTo = ref(2)

/** 左表「直前工程在庫」列の合計 */
const leftPrevInventoryTotal = computed(() =>
  leftRows.value.reduce((s, r) => s + (Number.isFinite(r.pre_plating_inventory) ? r.pre_plating_inventory : 0), 0),
)
const rightGenQtyTotal = computed(() =>
  rightRows.value.reduce((s, r) => s + (Number.isFinite(Number(r.gen_qty)) ? Number(r.gen_qty) : 0), 0),
)

const availableJigMachines = computed(() => {
  const set = new Set<string>()
  for (const r of leftRows.value) {
    const m = (r.plating_machine || '').trim()
    if (m && m !== '—') set.add(m)
  }
  for (const r of rightRows.value) {
    const m = (r.plating_machine || '').trim()
    if (m && m !== '—') set.add(m)
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b))
})

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

/** 必要治具本数 = 直前工程在庫 ÷ 掛け数 */
function calcRequiredJigCount(row: LeftPaneRow): string {
  const kake = parseKakeCount(row.plating_efficiency)
  if (!kake) return '—'
  const val = row.pre_plating_inventory / kake
  if (!Number.isFinite(val)) return '—'
  return val.toFixed(2)
}

function calcRequiredJigCountFromQty(qty: number | string, kakeRaw: string): string {
  const kake = parseKakeCount(kakeRaw)
  if (!kake) return '—'
  const q = Number(qty)
  if (!Number.isFinite(q)) return '—'
  const val = q / kake
  if (!Number.isFinite(val)) return '—'
  return val.toFixed(2)
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
      if (!jigDropDialogVisible.value) draggingSource.value = null
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

async function buildDraftPayload(items: PlatingDraftItemBody[]) {
  const board_cards = await mergePersistBoardCards()
  const planDate = draftRecordPlanDate.value || draftWorkDate.value || todayYmdJapan()
  return {
    plan_date: planDate,
    daily_minutes: PLATING_DAY_MINUTES,
    jigs_per_lap: layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value,
    max_laps: layoutBoardReady.value ? layoutMaxLaps.value : 1,
    minutes_per_lap: layoutBoardReady.value ? layoutMinutesPerLap.value : minutesPerLap.value,
    board_start_time: layoutBoardReady.value ? normalizeBoardStartTimeHm(layoutStartTime.value) : null,
    total_slots: kpi.value.totalSlots,
    used_slots: kpi.value.usedSlots,
    remain_slots: kpi.value.remainSlots,
    items,
    board_cards,
  }
}

/** 更新時に他作業日の明細行を残し、当該作業日分はボードのみで管理する */
async function mergePersistItems(): Promise<PlatingDraftItemBody[]> {
  if (!currentDraftId.value) return []
  const existing = await fetchPlatingDraftById(currentDraftId.value)
  const wd = draftWorkDate.value || todayYmdJapan()
  const plan = String(existing.plan_date || '').slice(0, 10) || wd
  return existing.items
    .filter((it) => effectiveItemWorkDate(it, plan) !== wd)
    .sort(comparePlatingApiDraftItemBySequence)
    .map(apiItemToBody)
    .map((x, i) => ({ ...x, sort_order: i + 1 }))
}

function scheduleCardsToBoardBodies(workDateYmd: string): PlatingBoardCardBody[] {
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  return [...scheduleCardsForCurrentDraft()]
    .filter((c) => c.qty > 0)
    .sort((a, b) => compareLapNoForBoardSort(a.lap_no, b.lap_no, scheduleByLap) || a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    .map((c) => {
      const slot = scheduleByLap.get(c.lap_no)
      return {
        work_date: workDateYmd,
        lap_work_date: slot?.work_date ?? workDateYmd,
        lap_start_time: slot?.start ?? null,
        lap_end_time: slot?.end ?? null,
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
      }
    })
}

/** ボード表示・保存：日历日 → 周目番号 */
function compareLapNoForBoardSort(
  lapA: number,
  lapB: number,
  scheduleByLap: Map<number, LapScheduleSlot>,
): number {
  const da = scheduleByLap.get(lapA)?.work_date ?? ''
  const db = scheduleByLap.get(lapB)?.work_date ?? ''
  if (da !== db) return da.localeCompare(db)
  return lapA - lapB
}

/** 更新時に他作業日のボード行をマージし、PUT で aps_plating_plan_board_cards を誤削除しない */
async function mergePersistBoardCards(): Promise<PlatingBoardCardBody[]> {
  const wd = draftWorkDate.value || todayYmdJapan()
  const mine = scheduleCardsToBoardBodies(wd)
  if (!currentDraftId.value) return mine
  const existing = await fetchPlatingDraftById(currentDraftId.value)
  const plan = String(existing.plan_date || '').slice(0, 10) || wd
  const kept = (existing.board_cards || [])
    .filter((bc) => effectiveItemWorkDate(bc, plan) !== wd)
    .map(apiBoardCardToBody)
  return [...kept, ...mine]
}

let boardAutosaveTimer: ReturnType<typeof setTimeout> | null = null
const BOARD_AUTOSAVE_MS = 600

function cancelBoardAutosaveTimer() {
  if (boardAutosaveTimer != null) {
    clearTimeout(boardAutosaveTimer)
    boardAutosaveTimer = null
  }
}

function canPersistBoard(): boolean {
  if (!draftWorkDate.value) return false
  return layoutBoardReady.value
}

/** ドラッグ等の高頻度変更：デバウンス後に aps_plating_plan_board_cards へ書込（persistDraft の board_cards 経由） */
function scheduleBoardAutosave() {
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
async function flushBoardPersist() {
  cancelBoardAutosaveTimer()
  if (isBoardHydratingFromApi.value) return
  if (loadingDraft.value) return
  if (!canPersistBoard()) return
  try {
    await persistDraft(false)
  } catch (e) {
    console.error(e)
  }
}

async function persistDraft(notify = true) {
  if (!draftWorkDate.value) {
    if (notify) ElMessage.warning('作業日を指定してください')
    return
  }
  let items: PlatingDraftItemBody[]
  try {
    items = await mergePersistItems()
  } catch (e) {
    console.error(e)
    if (notify) ElMessage.error('計画データの取得に失敗しました')
    return
  }
  const body = await buildDraftPayload(items)
  if (currentDraftId.value) {
    await updatePlatingDraft(currentDraftId.value, body)
  } else {
    const created = await createPlatingDraft(body)
    currentDraftId.value = created.id
    draftRecordPlanDate.value = String(created.plan_date || body.plan_date).slice(0, 10)
  }
}

type LoadLatestDraftOpts = { autoMode?: boolean; autoSyncWorkDate?: boolean }

type BoardCardWithDisplayLap = PlatingBoardCardOut & { persist_lap_no: number }

function assignDisplayLapNumbers(boards: PlatingBoardCardOut[]): BoardCardWithDisplayLap[] {
  const sorted = [...boards].sort((a, b) => {
    const planA = String(a.plan_date || '').slice(0, 10)
    const planB = String(b.plan_date || '').slice(0, 10)
    const da = boardCardLapWorkDate(a, planA)
    const db = boardCardLapWorkDate(b, planB)
    if (da !== db) return da.localeCompare(db)
    if (a.lap_no !== b.lap_no) return a.lap_no - b.lap_no
    if (a.turn_seq !== b.turn_seq) return a.turn_seq - b.turn_seq
    return (a.id ?? 0) - (b.id ?? 0)
  })
  const lapKeyToNo = new Map<string, number>()
  let nextLap = 0
  return sorted.map((bc) => {
    const persist_lap_no = Number(bc.lap_no) || 0
    const planKey = String(bc.plan_date || '').slice(0, 10)
    const wd = boardCardLapWorkDate(bc, planKey)
    const key = `${bc.draft_id}-${wd}-${persist_lap_no}`
    if (!lapKeyToNo.has(key)) {
      nextLap += 1
      lapKeyToNo.set(key, nextLap)
    }
    return { ...bc, persist_lap_no, lap_no: lapKeyToNo.get(key)! }
  })
}

/** 表示期間内の各 plan_date からボード行を集約（本日基準 -2〜+3 日） */
async function loadBoardAcrossViewRange(): Promise<{
  boardCards: BoardCardWithDisplayLap[]
  primary: PlatingDraftOut | null
}> {
  const { from, to } = boardViewRange.value
  const dates = enumerateYmdRange(from, to)
  const today = todayYmdJapan()
  const anchor = draftWorkDate.value || today
  const merged: PlatingBoardCardOut[] = []
  let primary: PlatingDraftOut | null = null

  for (const planD of dates) {
    try {
      const head = await fetchLatestPlatingDraftByDate(planD)
      if (!head) continue
      const full = await fetchPlatingDraftById(head.id)
      const planKey = String(full.plan_date || planD).slice(0, 10)
      const inRange = (full.board_cards || []).filter((bc) => isYmdInBoardView(boardCardLapWorkDate(bc, planKey)))
      if (inRange.length > 0) merged.push(...inRange)
      if (planD === anchor) primary = full
      else if (!primary && planD === today) primary = full
    } catch (e) {
      console.error(e)
    }
  }

  if (!primary) {
    const head = await fetchLatestPlatingDraftByDate(anchor)
    if (head) primary = await fetchPlatingDraftById(head.id)
  }

  return { boardCards: assignDisplayLapNumbers(merged), primary }
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
    const { boardCards: mergedBoard, primary } = await loadBoardAcrossViewRange()
    if (!primary) {
      currentDraftId.value = null
      draftRecordPlanDate.value = ''
      scheduleCards.value = []
      standardPositions.value = new Map()
      layoutBoardReady.value = false
      layoutBlocks.value = []
      if (!autoMode) ElMessage.warning('表示期間内の計画データはありません')
      return
    }

    const display = primary
    const planKey = String(display.plan_date || planDateForDraft).slice(0, 10)
    const boardDates = mergedBoard.map((bc) => ({
      work_date: effectiveItemWorkDate(bc, planKey),
    }))

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
    draftRecordPlanDate.value = planKey

    isBoardHydratingFromApi.value = true
    try {
      const jp = Math.max(1, Math.floor(Number(display.jigs_per_lap) || 0))
      const mp = Math.max(1, Math.floor(Number(display.minutes_per_lap) || 100))
      if (jp > 0) jigsPerLap.value = jp
      minutesPerLap.value = mp
      layoutMinutesPerLap.value = mp
      layoutPlanDate.value = String(display.plan_date || planKey).slice(0, 10) || planKey
      layoutStartTime.value = normalizeBoardStartTimeHm(display.board_start_time)
      const maxLapsFromDraft = Math.max(1, Math.floor(Number(display.max_laps) || 0))
      const rawBoard = mergedBoard
      const hasLayout =
        jp > 0 && (Boolean(display.board_start_time) || maxLapsFromDraft >= 1)
      if (hasLayout) {
        layoutBoardReady.value = true
        layoutJigsPerLap.value = jp > 0 ? jp : layoutJigsPerLap.value
        const maxFromCards = rawBoard.length > 0 ? Math.max(...rawBoard.map((b) => b.lap_no)) : 0
        layoutMaxLaps.value = Math.max(maxLapsFromDraft, maxFromCards, 1)
        const inferred = inferLayoutBlocksFromBoard(rawBoard, {
          plan_date: layoutPlanDate.value,
          board_start_time: layoutStartTime.value,
          minutes_per_lap: layoutMinutesPerLap.value,
          jigs_per_lap: layoutJigsPerLap.value,
          max_laps: layoutMaxLaps.value,
        })
        layoutBlocks.value =
          inferred.length > 0
            ? inferred
            : (() => {
                syncLayoutBlocksFromDraftHeader()
                return layoutBlocks.value
              })()
      } else {
        layoutBlocks.value = []
      }
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
              source_draft_id: bc.draft_id,
              turn_seq: bc.turn_seq,
              colorIdx: idx,
              boardMark: mk,
            }
          })
        standardPositions.value = new Map(
          scheduleCards.value
            .filter((c) => c.boardMark === 'standard')
            .map((c) => [c.id, { lap_no: c.lap_no, turn_seq: c.turn_seq }]),
        )
      } else if (!hasLayout) {
        scheduleCards.value = []
        standardPositions.value = new Map()
        layoutBoardReady.value = false
      } else {
        scheduleCards.value = []
        standardPositions.value = new Map()
      }
    } finally {
      void nextTick(() => {
        setTimeout(() => {
          isBoardHydratingFromApi.value = false
        }, 120)
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
  loadingJigAvailability.value = true
  try {
    const res = (await getMachineList({ page: 1, pageSize: 10000 })) as MachineListResponse
    const rows = ((res?.data?.list ?? res?.list ?? []) as MachineItem[]).filter((r) =>
      String(r.machine_cd || '').toUpperCase().includes('PL'),
    )
    const byName = new Map<string, MachineItem>()
    const byCd = new Map<string, MachineItem>()
    for (const r of rows) {
      const n = (r.machine_name || '').trim().toLowerCase()
      const c = (r.machine_cd || '').trim().toLowerCase()
      if (n) byName.set(n, r)
      if (c) byCd.set(c, r)
    }
    const machineNames = availableJigMachines.value.length > 0
      ? availableJigMachines.value
      : Array.from(
          new Set(
            rows
              .map((r) => (r.machine_name || r.machine_cd || '').trim())
              .filter((x) => x !== ''),
          ),
        ).sort((a, b) => a.localeCompare(b))

    jigAvailabilityRows.value = machineNames.map((machine) => ({
      machine_id: (() => {
        const key = machine.trim().toLowerCase()
        const m = byName.get(key) ?? byCd.get(key)
        return m?.id ?? null
      })(),
      plating_machine: machine,
      available_qty: (() => {
        const key = machine.trim().toLowerCase()
        const m = byName.get(key) ?? byCd.get(key)
        return Number(m?.available_qty) || 0
      })(),
    }))
  } catch (e) {
    console.error(e)
    ElMessage.error(
      'メッキ治具の使用可能本数の取得に失敗しました（設備マスタの available_qty を確認してください）',
    )
    jigAvailabilityRows.value = availableJigMachines.value.map((machine) => ({
      machine_id: null,
      plating_machine: machine,
      available_qty: 0,
    }))
  } finally {
    loadingJigAvailability.value = false
  }
}

/** 当該周目に既に配置されている治具本数（他周目は含めない） */
function countBoardSlotsForMachine(platingMachine: string, lapNo: number): number {
  const key = normalizeMachineKey(platingMachine)
  return scheduleCards.value.filter(
    (c) =>
      c.qty > 0 &&
      c.lap_no === lapNo &&
      normalizeMachineKey(c.plating_machine) === key,
  ).length
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
  const usedOnLap = scheduleCards.value.filter((c) => c.qty > 0 && c.lap_no === lapNo).length
  return Math.max(0, lapBoardColCount.value - usedOnLap)
}

function getJigQtyMaxForLap(platingMachine: string, lapNo: number, currentBlockSize = 0): number {
  const avail = getJigAvailMaxFromMaster(platingMachine)
  const usedOnLap = countBoardSlotsForMachine(platingMachine, lapNo)
  const jigMax = Math.max(0, avail - usedOnLap + currentBlockSize)
  const boardMax = countBoardSlotsRemainingOnLap(lapNo) + currentBlockSize
  return Math.max(0, Math.min(jigMax, boardMax))
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
  for (const lap of lapOrder) {
    let nextTurn = 1
    while (out.length < count) {
      const occupied = scheduleCards.value.some(
        (c) => c.qty > 0 && c.lap_no === lap && c.turn_seq === nextTurn,
      )
      if (!occupied) out.push({ lap_no: lap, turn_seq: nextTurn })
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
    const remainBoard = countBoardSlotsRemainingOnLap(targetLap)
    if (remainJig <= 0) {
      ElMessage.warning(
        `${row.plating_machine} は第${lapDisplayNo(targetLap)}周目で使用可能本数を超えています（当該周 ${availableMax} 本・済 ${usedOnLap} 本）`,
      )
    } else if (remainBoard <= 0) {
      ElMessage.warning(`第${lapDisplayNo(targetLap)}周目に空き枠がありません`)
    } else {
      ElMessage.warning(`第${lapDisplayNo(targetLap)}周目へ投入できません`)
    }
    return
  }
  jigDropPending.value = {
    plating_machine: row.plating_machine,
    available_max: availableMax,
    used_on_board: usedOnLap,
    target_lap: targetLap,
  }
  jigDropPreferLap.value = targetLap
  jigDropQtyMax.value = maxQty
  jigDropQty.value = maxQty
  jigDropDialogVisible.value = true
}

function isJigProductCd(productCd: string): boolean {
  return String(productCd || '').startsWith('__jig__')
}

function createJigScheduleCard(platingMachine: string, lapNo: number, turnSeq: number): ScheduleCard {
  const mKey = normalizeMachineKey(platingMachine)
  const productCd = `__jig__${mKey}`
  return {
    id: `jig-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    product_cd: productCd,
    product_name: platingMachine,
    plating_machine: platingMachine,
    kake: 1,
    qty: 1,
    slots: 1,
    lap_no: lapNo,
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

/** 治具枠に製品割当後：例 D01L RR (60) */
function formatJigBlockProductCalc(ms: LapMergedSegment): string | null {
  const cards = getMergedSegCards(ms)
  const product = cards.find((c) => !isJigProductCd(c.product_cd))
  if (!product) return null
  const slots = Math.max(0, Math.floor(Number(ms.span) || 0))
  const kake = product.kake > 0 ? product.kake : 1
  const total = slots * kake
  return `${product.product_name} (${formatQtyDisplay(total)})`
}

function boardMergedSegTitle(ms: LapMergedSegment): string {
  const base = `${ms.plating_machine}・${ms.span}本`
  const calc = formatJigBlockProductCalc(ms)
  if (!isJigProductCd(ms.product_cd)) return base
  const hints = ['②の行をドラッグで製品割当', '行内ドラッグで移動', 'ダブルクリックで本数変更']
  return calc ? `${base}・${calc}・${hints.join('・')}` : `${base}・${hints.join('・')}`
}

function resolveInventoryDragSource(): DraftSourceItem | null {
  return draggingSource.value
}

function assignProductToJigBlock(ms: LapMergedSegment, lapNo: number, src: DraftSourceItem) {
  if (!isJigProductCd(ms.product_cd)) return
  const jigMachine = String(ms.plating_machine || '').trim()
  const srcJig = String(src.plating_machine || '').trim()
  if (srcJig && jigMachine && normalizeMachineKey(srcJig) !== normalizeMachineKey(jigMachine)) {
    ElMessage.warning(`製品のメッキ治具（${srcJig}）と枠（${jigMachine}）が一致しません`)
    return
  }
  const kake = src.kake > 0 ? src.kake : 1
  const slots = Math.max(0, Math.floor(Number(ms.span) || 0))
  const ids = new Set(ms.cardIds)
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (!ids.has(c.id) || c.qty <= 0 || c.lap_no !== lapNo) return c
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
  })
  refreshMarksAgainstStandardPositions()
  const total = slots * kake
  ElMessage.success(
    `${src.product_name} を ${jigMachine}（${slots}本）に割当：${slots}×${formatQtyDisplay(kake)}=${formatQtyDisplay(total)}`,
  )
  void flushBoardPersist()
}

function onProductToJigBlockDragOver(e: DragEvent, ms?: LapMergedSegment) {
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
  assignProductToJigBlock(ms, lapNo, src)
}

function boardTailCardTitle(tc: ScheduleCard): string {
  const base = `${tc.plating_machine}・治具1本`
  return isJigProductCd(tc.product_cd) ? `${base}・ダブルクリックで本数変更` : `${base}・生産${tc.qty}本`
}

function findJigBlockCardIds(cardId: string, lapNo: number): string[] {
  const sorted = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const idx = sorted.findIndex((c) => c.id === cardId)
  if (idx < 0) return []
  const mk = mergeKeyForScheduleCard(sorted[idx])
  let start = idx
  let end = idx
  while (start > 0 && mergeKeyForScheduleCard(sorted[start - 1]) === mk) start -= 1
  while (end < sorted.length - 1 && mergeKeyForScheduleCard(sorted[end + 1]) === mk) end += 1
  return sorted.slice(start, end + 1).map((c) => c.id)
}

function resizeJigBlockOnLap(lapNo: number, cardIds: string[], newQty: number) {
  const block = scheduleCards.value.filter((c) => cardIds.includes(c.id))
  if (block.length === 0) return
  const platingMachine = block[0].plating_machine
  const insertTurn = Math.min(...block.map((c) => c.turn_seq))
  const blockEnd = Math.max(...block.map((c) => c.turn_seq))
  const qty = Math.max(1, Math.floor(Number(newQty) || 0))

  const without = scheduleCards.value.filter((c) => !cardIds.includes(c.id))
  const lapRest = without
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const before = lapRest.filter((c) => c.turn_seq < insertTurn)
  const after = lapRest.filter((c) => c.turn_seq > blockEnd)

  const newBlock: ScheduleCard[] = []
  for (let i = 0; i < qty; i += 1) {
    newBlock.push(createJigScheduleCard(platingMachine, lapNo, insertTurn + i))
  }
  const merged = [...before, ...newBlock, ...after]
  merged.forEach((c, i) => {
    c.turn_seq = i + 1
  })

  const others = without.filter((c) => c.lap_no !== lapNo || c.qty <= 0)
  scheduleCards.value = [...others, ...merged]
  refreshMarksAgainstStandardPositions()
}

function resetBoardJigEditDialog() {
  boardJigEditPending.value = null
  boardJigEditQty.value = 1
  boardJigEditQtyMax.value = 1
}

function openBoardJigQtyEdit(ms: LapMergedSegment, lapNo: number) {
  if (!isJigProductCd(ms.product_cd)) return
  const maxQty = getJigEditQtyMax(ms.plating_machine, lapNo, ms.cardIds.length)
  boardJigEditPending.value = {
    lap_no: lapNo,
    plating_machine: ms.plating_machine,
    product_cd: ms.product_cd,
    product_name: ms.product_name,
    cardIds: [...ms.cardIds],
  }
  boardJigEditQtyMax.value = maxQty
  boardJigEditQty.value = ms.cardIds.length
  boardJigEditDialogVisible.value = true
}

function onBoardMergedSegDblClick(ms: LapMergedSegment, lapNo: number) {
  openBoardJigQtyEdit(ms, lapNo)
}

function onBoardScheduleCardDblClick(card: ScheduleCard) {
  if (!isJigProductCd(card.product_cd)) return
  const cardIds = findJigBlockCardIds(card.id, card.lap_no)
  if (cardIds.length === 0) return
  const maxQty = getJigEditQtyMax(card.plating_machine, card.lap_no, cardIds.length)
  boardJigEditPending.value = {
    lap_no: card.lap_no,
    plating_machine: card.plating_machine,
    product_cd: card.product_cd,
    product_name: card.product_name,
    cardIds,
  }
  boardJigEditQtyMax.value = maxQty
  boardJigEditQty.value = cardIds.length
  boardJigEditDialogVisible.value = true
}

function confirmBoardJigQtyEdit() {
  const pending = boardJigEditPending.value
  if (!pending) return
  const qty = Math.max(1, Math.min(boardJigEditQtyMax.value, Math.floor(Number(boardJigEditQty.value) || 0)))
  const prev = pending.cardIds.length
  if (qty === prev) {
    boardJigEditDialogVisible.value = false
    return
  }
  resizeJigBlockOnLap(pending.lap_no, pending.cardIds, qty)
  boardJigEditDialogVisible.value = false
  const diff = qty - prev
  ElMessage.success(
    diff > 0
      ? `${pending.plating_machine} を ${diff} 本増やしました（計 ${qty} 本）`
      : `${pending.plating_machine} を ${-diff} 本減らしました（計 ${qty} 本）`,
  )
  void flushBoardPersist()
}

function confirmJigDropToBoard() {
  const pending = jigDropPending.value
  if (!pending) return
  const qty = Math.max(1, Math.min(jigDropQtyMax.value, Math.floor(Number(jigDropQty.value) || 0)))
  const slots = findNextSequentialBoardSlots(qty, jigDropPreferLap.value)
  if (slots.length === 0) {
    ElMessage.warning('割り当て可能な枠がありません')
    return
  }
  const newCards: ScheduleCard[] = slots.map((s) =>
    createJigScheduleCard(pending.plating_machine, s.lap_no, s.turn_seq),
  )
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
  jigBoardDragActive.value = true
  if (lapNo != null) jigDropHoverLap.value = lapNo
}

function onJigToBoardDragLeave(e: DragEvent) {
  const rel = e.relatedTarget as Node | null
  const board = (e.currentTarget as HTMLElement | null)
  if (board && rel && board.contains(rel)) return
  jigDropHoverLap.value = null
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

async function saveJigAvailabilityForm() {
  savingJigAvailability.value = true
  try {
    const updates = jigAvailabilityRows.value.filter((r) => r.machine_id != null)
    for (const r of updates) {
      await updateMachine({
        id: Number(r.machine_id),
        available_qty: Math.max(0, Math.floor(Number(r.available_qty) || 0)),
      })
    }
    ElMessage.success('メッキ治具の使用可能本数を保存しました')
    await loadJigAvailability()
  } catch (e) {
    console.error(e)
    ElMessage.error('メッキ治具の使用可能本数の保存に失敗しました')
  } finally {
    savingJigAvailability.value = false
  }
}

/** メッキ治具文字列 → machines.efficiency（machine_name 主、machine_cd 補助） */
interface MachineEfficiencyLookup {
  byMachineName: Map<string, number>
  byMachineCd: Map<string, number>
}

function formatMachineEfficiency(n: number): string {
  if (!Number.isFinite(n)) return '—'
  return String(n)
}

function buildMachineEfficiencyLookup(rows: MachineItem[]): MachineEfficiencyLookup {
  const byMachineName = new Map<string, number>()
  const byMachineCd = new Map<string, number>()
  for (const m of rows) {
    const effRaw = m.efficiency
    if (effRaw === undefined || effRaw === null) continue
    const eff = Number(effRaw)
    if (!Number.isFinite(eff)) continue
    const name = (m.machine_name || '').trim().toLowerCase()
    const cd = (m.machine_cd || '').trim().toLowerCase()
    if (name) byMachineName.set(name, eff)
    if (cd) byMachineCd.set(cd, eff)
  }
  return { byMachineName, byMachineCd }
}

/** メッキ治具（plating_machine）を machines.machine_name（無ければ machine_cd）と照合 */
function lookupJigEfficiency(lookup: MachineEfficiencyLookup, jigRaw: string): string {
  const j = jigRaw.trim().toLowerCase()
  if (!j) return '—'
  let v = lookup.byMachineName.get(j)
  if (v === undefined) v = lookup.byMachineCd.get(j)
  if (v === undefined) return '—'
  return formatMachineEfficiency(v)
}

async function fetchMachineEfficiencyLookup(): Promise<MachineEfficiencyLookup> {
  try {
    const res = (await getMachineList({ page: 1, pageSize: 10000 })) as MachineListResponse
    const list = res?.data?.list ?? res?.list ?? []
    return buildMachineEfficiencyLookup(Array.isArray(list) ? list : [])
  } catch (e) {
    console.warn('fetchMachineEfficiencyLookup:', e)
    return { byMachineName: new Map(), byMachineCd: new Map() }
  }
}

/**
 * メッキ直前工程の翌日「生成」数量と参照した列名。
 */
function pickPrevProcessGen(row: Record<string, unknown>, prevKey: string | null): { qty: number; col: string } {
  if (!prevKey) return { qty: 0, col: '' }
  for (const suf of GEN_SUFFIX_TRY) {
    const col = `${prevKey}${suf}`
    if (Object.prototype.hasOwnProperty.call(row, col) && row[col] != null) {
      return { qty: num(row[col]), col }
    }
  }
  return { qty: 0, col: '' }
}

async function fetchDay(dateStr: string): Promise<Record<string, unknown>[]> {
  const params: Record<string, unknown> = {
    page: 1,
    limit: 50000,
    startDate: dateStr,
    endDate: dateStr,
    sortBy: 'product_cd',
    sortOrder: 'ASC',
  }
  const res = await getProductionSummarysList(params)
  return parseList(res)
}

function buildLeftRow(row: Record<string, unknown>, machineEff: MachineEfficiencyLookup): LeftPaneRow {
  const prev = (row.pre_kt05_plating_prev_process as string) || null
  const jig = row.plating_machine != null ? String(row.plating_machine).trim() : ''
  const productCd = String(row.product_cd ?? '')
  const jigDisp = jig || '—'
  return {
    product_cd: productCd,
    product_name: String(row.product_name ?? ''),
    plating_machine: jigDisp,
    plating_efficiency: lookupJigEfficiency(machineEff, jig),
    pre_plating_prev_label: labelForPrevKey(prev),
    pre_plating_inventory: num(row.pre_kt05_plating_inventory),
  }
}

function buildRightRow(
  row: Record<string, unknown>,
  prevKeyFromBase: string | null,
  machineEff: MachineEfficiencyLookup,
): RightPaneRow {
  const prev =
    (row.pre_kt05_plating_prev_process as string) || prevKeyFromBase
  const { qty, col } = pickPrevProcessGen(row, prev)
  const jig = row.plating_machine != null ? String(row.plating_machine).trim() : ''
  return {
    product_cd: String(row.product_cd ?? ''),
    product_name: String(row.product_name ?? ''),
    plating_machine: jig || '—',
    plating_efficiency: lookupJigEfficiency(machineEff, jig),
    pre_plating_prev_label: labelForPrevKey(prev),
    gen_qty: col ? qty : '—',
    gen_source_col: col || '—',
  }
}

/** 左＝メッキ前在庫の基準日、右＝見込数量の参照日（それぞれ別日付で production_summarys を取得） */
async function loadSummaryPair() {
  if (!leftInventoryDate.value || !rightGenDate.value) {
    ElMessage.warning('左右それぞれ日付を指定してください')
    return
  }
  const d0 = leftInventoryDate.value
  const d1 = rightGenDate.value
  loadingPair.value = true
  leftRows.value = []
  rightRows.value = []
  try {
    const [list0, list1, machineEff] = await Promise.all([
      fetchDay(d0),
      fetchDay(d1),
      fetchMachineEfficiencyLookup(),
    ])
    type Pair = { row: Record<string, unknown>; left: LeftPaneRow; prevKey: string | null }
    const pairs: Pair[] = []

    for (const row of list0) {
      const cd = String(row.product_cd ?? '').trim()
      if (!cd) continue
      const prevBase = (row.pre_kt05_plating_prev_process as string) || null
      const invRaw = row.pre_kt05_plating_inventory
      if (invRaw === null || invRaw === undefined) continue
      const invNum = num(invRaw)
      if (invNum <= 0) continue
      pairs.push({ row, left: buildLeftRow(row, machineEff), prevKey: prevBase })
    }

    pairs.sort((a, b) => {
      const jm = String(a.left.plating_machine).localeCompare(String(b.left.plating_machine))
      if (jm !== 0) return jm
      const rk = processOrderRank(a.prevKey) - processOrderRank(b.prevKey)
      if (rk !== 0) return rk
      return a.left.product_cd.localeCompare(b.left.product_cd)
    })

    const left: LeftPaneRow[] = []
    for (const p of pairs) {
      left.push(p.left)
    }

    // 右表：参照日 d1 のみ表示（見込数量が 0 超の行）
    const right: RightPaneRow[] = []
    for (const row of list1) {
      const prev = (row.pre_kt05_plating_prev_process as string) || null
      const r = buildRightRow(row, prev, machineEff)
      const q = Number(r.gen_qty)
      if (!Number.isFinite(q) || q <= 0) continue
      right.push(r)
    }
    right.sort((a, b) => {
      const jm = String(a.plating_machine).localeCompare(String(b.plating_machine))
      if (jm !== 0) return jm
      const ak = (list1.find((r) => String(r.product_cd ?? '') === a.product_cd)?.pre_kt05_plating_prev_process as string) || null
      const bk = (list1.find((r) => String(r.product_cd ?? '') === b.product_cd)?.pre_kt05_plating_prev_process as string) || null
      const rk = processOrderRank(ak) - processOrderRank(bk)
      if (rk !== 0) return rk
      return String(a.product_name).localeCompare(String(b.product_name))
    })

    leftRows.value = left
    rightRows.value = right
    ElMessage.success(
      `取得しました（左 ${d0}／右 ${d1}）：左 ${left.length} 件（直前在庫が 0 超）／右 ${right.length} 件（見込数量が 0 超）`,
    )
  } catch (e) {
    console.error(e)
    ElMessage.error('生産サマリ（production_summarys）の取得に失敗しました')
  } finally {
    loadingPair.value = false
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

/** 同一品番は常に同じ sched-color-0..7（画面上で品番を識別しやすくする） */
function schedColorIndexForProductCd(productCd: string): number {
  const s = String(productCd ?? '').trim()
  if (!s) return 0
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h) % 8
}

const canUseLapCopy = computed(() => layoutBoardReady.value && layoutMaxLaps.value >= 2)

const lapCopyLapOptions = computed(() => {
  const scheduleByLap = new Map(buildGlobalLapSchedule().map((s) => [s.lap_no, s]))
  return lapGridRows.value.map((r) => {
    const wd = scheduleByLap.get(r.lap_no)?.work_date
    const prefix = wd ? `${formatBoardDateLabel(wd)} ` : ''
    return { value: r.lap_no, label: `${prefix}第${r.lap_display_no}周目` }
  })
})

const lapCopySourceCount = computed(
  () => scheduleCards.value.filter((c) => c.qty > 0 && c.lap_no === lapCopyFrom.value).length,
)

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
  const newCards: ScheduleCard[] = sourceCards.map((c, i) => ({
    ...c,
    id: `lap-copy-${ts}-${i}-${Math.random().toString(36).slice(2, 6)}`,
    lap_no: to,
    turn_seq: c.turn_seq,
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

function openAppendLayoutDialog() {
  tplFormPlanDate.value = draftWorkDate.value || todayYmdJapan()
  tplFormStartTime.value = layoutBoardReady.value ? layoutStartTime.value : DEFAULT_BOARD_START_TIME
  tplFormMinutesPerLap.value = layoutBoardReady.value ? layoutMinutesPerLap.value : minutesPerLap.value
  tplFormJigsPerLap.value = layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value
  const d = boardLapsPerDay.value
  tplFormMaxLaps.value = layoutBoardReady.value
    ? 1
    : Math.max(1, Math.min(500, d > 0 ? d : 1))
  templateDialogVisible.value = true
}

function confirmAppendLayout() {
  const planDate = (tplFormPlanDate.value || '').trim()
  if (!planDate) {
    ElMessage.warning('計画日を指定してください')
    return
  }
  if (tplLapSchedulePreview.value.length === 0) {
    ElMessage.warning('開始時刻・段数を確認してください')
    return
  }
  const j = Math.max(1, Math.min(300, Math.floor(Number(tplFormJigsPerLap.value) || 1)))
  const laps = Math.max(1, Math.min(500, Math.floor(Number(tplFormMaxLaps.value) || 1)))
  const cycle = Math.max(1, Math.min(600, Math.floor(Number(tplFormMinutesPerLap.value) || 1)))
  const startHm = normalizeBoardStartTimeHm(tplFormStartTime.value)
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
  void nextTick(() => {
    if (!scheduleCards.value.some((c) => c.qty > 0)) initLapTrackSortables()
  })
  const preview = buildLapScheduleRows(planDate, startHm, cycle, laps)
  const last = preview[preview.length - 1]
  ElMessage.success(
    last
      ? `${formatBoardDateLabel(planDate)}：第1〜${laps}周目を追加しました（${startHm}〜${last.end}）`
      : `${formatBoardDateLabel(planDate)}：第1〜${laps}周目の空き枠を追加しました`,
  )
  void flushBoardPersist()
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

/** 各「本」列：約 3 桁分の幅（ch＝数字 0 の幅基準）＋横スクロールで全体を閲覧 */
const lapBoardColTrack = 'minmax(3ch, 3ch)'

const lapLabelColWidth = '76px'

/** 右側本数列は横スクロール、周列は各行で sticky 固定 */
const lapBoardColsGridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${lapBoardColCount.value}, ${lapBoardColTrack})`,
}))

/** 印刷 HTML 用（周列＋本数列の一体グリッド） */
const lapBoardGridStyle = computed(() => ({
  gridTemplateColumns: `${lapLabelColWidth} repeat(${lapBoardColCount.value}, ${lapBoardColTrack})`,
}))

/** 横結合バー用：ヘッダー列と同じ本数・同じ列幅 */
const innerMergedGridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${lapBoardColCount.value}, ${lapBoardColTrack})`,
}))

/** ③ボード表示：「製品名 (本数)」例 5A54 (5) — 括弧内は当該表示ブロックのメッキ治具本数 */
function formatPlatingBoardLabel(productName: string, jigUnits: number): string {
  const name = String(productName ?? '').trim() || '空'
  const n = Math.max(0, Math.floor(Number(jigUnits) || 0))
  return `${name} (${n})`
}

const lapColumnHeaders = computed(() =>
  Array.from({ length: lapBoardColCount.value }, (_, i) => ({ i: i + 1 })),
)

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

/** 第1〜(n-1)本まで1列1枚、それ以降は最終列に集約 */
function binCardsIntoColumns(cards: ScheduleCard[], colCount: number): ScheduleCard[][] {
  const n = Math.max(1, colCount)
  const sorted = [...cards]
    .filter((c) => c.qty > 0)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const bins: ScheduleCard[][] = Array.from({ length: n }, () => [])
  sorted.forEach((c, idx) => {
    const col = idx < n - 1 ? idx : n - 1
    bins[col].push(c)
  })
  return bins
}

function mergeKeyForScheduleCard(c: ScheduleCard): string {
  return `${c.product_cd}|${normalizeMachineKey(c.plating_machine)}`
}

function boardMarkRank(m: BoardMark): number {
  if (m === 'rush') return 3
  if (m === 'manual') return 2
  return 1
}

function maxBoardMark(a: BoardMark, b: BoardMark): BoardMark {
  return boardMarkRank(a) >= boardMarkRank(b) ? a : b
}

/** 第 1〜(n-1) 列は各列最大 1 枠：隣列かつ同一品番なら横方向に結合表示 */
function buildMergedLeftSegments(cards: ScheduleCard[], lapNo: number, n: number): LapMergedSegment[] {
  if (n <= 1) return []
  const bins = binCardsIntoColumns(cards, n)
  const slots: (ScheduleCard | undefined)[] = []
  for (let i = 0; i < n - 1; i += 1) slots.push(bins[i]?.[0])

  const out: LapMergedSegment[] = []
  let i = 0
  while (i < slots.length) {
    if (!slots[i]) {
      i += 1
      continue
    }
    const mk = mergeKeyForScheduleCard(slots[i]!)
    let j = i
    let bm: BoardMark = slots[i]!.boardMark ?? 'standard'
    while (j + 1 < slots.length && slots[j + 1] && mergeKeyForScheduleCard(slots[j + 1]!) === mk) {
      j += 1
      bm = maxBoardMark(bm, slots[j]!.boardMark ?? 'standard')
    }
    const slice: ScheduleCard[] = []
    for (let k = i; k <= j; k += 1) {
      if (slots[k]) slice.push(slots[k]!)
    }
    out.push({
      key: `mg-${lapNo}-L-${i}-${slice.map((s) => s.id).join('|')}`,
      startCol: i + 1,
      span: j - i + 1,
      product_cd: slice[0].product_cd,
      product_name: slice[0].product_name || '空',
      plating_machine: slice[0].plating_machine || '—',
      boardMark: bm,
      cardIds: slice.map((s) => s.id),
      slotCount: slice.reduce((s, c) => s + c.qty, 0),
    })
    i = j + 1
  }
  return out
}

const lapGridRows = computed<LapGridRow[]>(() => {
  const n = lapBoardColCount.value
  const byLap = new Map<number, ScheduleCard[]>()
  for (const c of scheduleCards.value) {
    if (c.qty <= 0) continue
    const arr = byLap.get(c.lap_no) ?? []
    arr.push(c)
    byLap.set(c.lap_no, arr)
  }

  let lapNumbers: number[]
  if (layoutBoardReady.value && layoutMaxLaps.value > 0) {
    const maxFromCards = byLap.size > 0 ? Math.max(...byLap.keys()) : 0
    const totalRows = Math.max(layoutMaxLaps.value, maxFromCards)
    lapNumbers = Array.from({ length: totalRows }, (_, i) => i + 1)
  } else {
    lapNumbers = Array.from(byLap.keys()).sort((a, b) => a - b)
    if (lapNumbers.length === 0) return []
  }

  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  if (scheduleByLap.size > 0) {
    lapNumbers.sort((a, b) => compareLapNoForBoardSort(a, b, scheduleByLap))
  }
  lapNumbers = lapNumbers.filter((lapNo) => isLapNoInBoardView(lapNo, scheduleByLap))

  return lapNumbers.map((lapNo) => {
    const cards = (byLap.get(lapNo) ?? []).sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    const bins = binCardsIntoColumns(cards, n)
    const cells: LapGridCell[] = bins.map((bin) => ({
      segments: cardsToDisplaySegments(bin),
    }))
    const mergedLeft = cards.length > 0 ? buildMergedLeftSegments(cards, lapNo, n) : null
    const mergedTail = cards.length > 0 ? (binCardsIntoColumns(cards, n)[n - 1] ?? []) : null
    return {
      lap_no: lapNo,
      lap_display_no: lapDisplayNo(lapNo),
      cells,
      mergedLeft,
      mergedTail,
    }
  })
})

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
    const flat: string[] = []
    for (let i = 0; i < Math.min(n, cols.length); i += 1) {
      if (i < n - 1) {
        const first = cols[i]?.[0]
        if (first) flat.push(first)
      } else {
        flat.push(...(cols[i] ?? []))
      }
    }
    let turn = 1
    for (const id of flat) {
      const c = idToCard.get(id)
      if (!c) continue
      out.push({ ...c, lap_no, turn_seq: turn })
      turn += 1
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
  const orderedIds = readOrderedCardIdsFromLapRow(lapEl)
  if (orderedIds.length === 0) return

  const lapCardMap = new Map(
    scheduleCards.value
      .filter((c) => c.qty > 0 && c.lap_no === lapNo)
      .map((c) => [c.id, c] as const),
  )
  const reordered: ScheduleCard[] = []
  for (const id of orderedIds) {
    const c = lapCardMap.get(id)
    if (c) reordered.push(c)
  }
  for (const c of lapCardMap.values()) {
    if (!orderedIds.includes(c.id)) reordered.push(c)
  }
  reordered.forEach((c, i) => {
    c.turn_seq = i + 1
  })

  const others = scheduleCards.value.filter((c) => c.lap_no !== lapNo || c.qty <= 0)
  scheduleCards.value = [...others, ...reordered]
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

function destroyLapTrackSortables() {
  for (const s of lapTrackSortables) s.destroy()
  lapTrackSortables = []
}

function destroyLapMergedSortables() {
  for (const s of lapMergedSortables) s.destroy()
  lapMergedSortables = []
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
      draggable: '.lap-merged-seg--board-draggable',
      ghostClass: 'lap-merged-seg--ghost',
      onEnd: () => {
        nextTick(() => {
          syncScheduleOrderFromMergedRow(row, lapNo)
          void flushBoardPersist()
        })
      },
    })
    lapMergedSortables.push(s)
  }
  const tails = Array.from(document.querySelectorAll<HTMLElement>('.lap-merged-tail'))
  for (const tail of tails) {
    const row = tail.closest<HTMLElement>('.lap-board-body-row')
    const lapNo = Number(row?.dataset.lapNo) || 0
    if (!row || lapNo <= 0) continue
    const items = tail.querySelectorAll('.lap-merged-tail-item--board-draggable, .lap-merged-tail-item.lap-merged-seg--board-draggable')
    if (items.length < 2) continue
    const s = Sortable.create(tail, {
      animation: 120,
      draggable: '.lap-merged-seg--board-draggable',
      onEnd: () => {
        nextTick(() => {
          syncScheduleOrderFromMergedRow(row, lapNo)
          void flushBoardPersist()
        })
      },
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

/** 数量が入っている割当枠のみ印刷対象 */
const hasPrintableScheduleRows = computed(() =>
  scheduleCards.value.some((c) => num(c.qty) > 0 && isLapNoInBoardView(c.lap_no)),
)

function escapeHtmlForPrint(s: string): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const LAP_PRINT_COL_TRACK = 'minmax(3ch, 3ch)'

function boardMarkSegClass(m: BoardMark, merged: boolean): string {
  if (m === 'manual') return merged ? 'lap-merged-seg--manual' : 'lap-segment--manual'
  if (m === 'rush') return merged ? 'lap-merged-seg--rush' : 'lap-segment--rush'
  return ''
}

function buildLapDateRowPrintHtml(dateLabel: string, n: number): string {
  const gridStyle = `grid-template-columns:76px repeat(${n},${LAP_PRINT_COL_TRACK})`
  return `<div class="lap-board-grid lap-board-date-row" style="${gridStyle}"><div class="lap-date-label">${escapeHtmlForPrint(
    dateLabel,
  )}</div><div class="lap-date-band"></div></div>`
}

/** 画面上の lap-board と同じ構造を印刷 HTML に組み立てる */
function buildLapBoardRowPrintHtml(row: LapGridRow, n: number): string {
  const gridStyle = `grid-template-columns:76px repeat(${n},${LAP_PRINT_COL_TRACK})`
  const innerGrid = `grid-template-columns:repeat(${n},${LAP_PRINT_COL_TRACK})`
  const timeLbl = lapTimeRangeLabel(row.lap_no)
  const lapLabel = timeLbl
    ? `第${row.lap_display_no}周目\n${timeLbl}`
    : `第${row.lap_display_no}周目`

  if (row.mergedLeft != null) {
    const leftSegs = row.mergedLeft
      .map((ms) => {
        const ci = schedColorIndexForProductCd(ms.product_cd)
        const mk = boardMarkSegClass(ms.boardMark, true)
        const calc = formatJigBlockProductCalc(ms)
        const jigLbl = escapeHtmlForPrint(formatPlatingBoardLabel(ms.plating_machine, ms.span))
        const inner = calc
          ? `<span class="lap-merged-text lap-merged-text--jig">${jigLbl}</span><span class="lap-merged-text lap-merged-text--calc">${escapeHtmlForPrint(calc)}</span>`
          : `<span class="lap-merged-text lap-merged-text--jig">${jigLbl}</span>`
        return `<div class="lap-merged-seg sched-color-${ci} ${mk}" style="grid-column:${ms.startCol} / span ${ms.span};grid-row:1"><div class="lap-merged-label-stack">${inner}</div></div>`
      })
      .join('')
    let tailHtml = ''
    const tail = row.mergedTail
    if (tail != null && tail.length > 0) {
      const items = tail
        .map((tc) => {
          const ci = schedColorIndexForProductCd(tc.product_cd)
          const mk = boardMarkSegClass(tc.boardMark, true)
          return `<div class="lap-merged-tail-item sched-color-${ci} ${mk}"><span class="lap-merged-text">${escapeHtmlForPrint(
            formatPlatingBoardLabel(tc.product_name, 1),
          )}</span></div>`
        })
        .join('')
      tailHtml = `<div class="lap-merged-tail" style="grid-column:${n} / span 1;grid-row:1">${items}</div>`
    }
    return `<div class="lap-board-grid lap-board-body-row" style="${gridStyle}"><div class="lap-label">${escapeHtmlForPrint(
      lapLabel,
    )}</div><div class="lap-merged-host" style="${innerGrid}">${leftSegs}${tailHtml}</div></div>`
  }

  const cells = row.cells
    .map((cell) => {
      const segs = cell.segments
        .map((seg) => {
          const ci = schedColorIndexForProductCd(seg.product_cd)
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
  return `<div class="lap-board-grid lap-board-body-row" style="${gridStyle}"><div class="lap-label">${escapeHtmlForPrint(
    lapLabel,
  )}</div>${cells}</div>`
}

function printScheduleBoard() {
  if (!hasPrintableScheduleRows.value) {
    ElMessage.warning('印刷できる割当データがありません')
    return
  }
  const displayRows = lapBoardDisplayRows.value
  if (displayRows.length === 0) {
    ElMessage.warning('ボード表示がありません（追加レイアウトと割当を確認してください）')
    return
  }
  const k = kpi.value
  const workDate = draftWorkDate.value || '—'
  const printedAt = dayjs().tz(TZ_JP).format('YYYY-MM-DD HH:mm:ss')
  const layoutDesc = layoutBoardReady.value
    ? `レイアウト：${layoutBlocksSummary.value}／1周 ${layoutJigsPerLap.value} 本／計 ${layoutMaxLaps.value} 周`
    : 'レイアウト：未確定（追加レイアウト未設定）'

  const n = lapBoardColCount.value
  const headCols = Array.from({ length: n }, (_, i) => i + 1)
    .map(
      (i) =>
        `<div class="lap-col-head"><span class="lap-col-head-n">${i}</span><span class="lap-col-head-s">本</span></div>`,
    )
    .join('')
  const headGridStyle = `grid-template-columns:76px repeat(${n},${LAP_PRINT_COL_TRACK})`
  const boardBody = displayRows
    .map((item) =>
      item.kind === 'date'
        ? buildLapDateRowPrintHtml(item.dateLabel, n)
        : buildLapBoardRowPrintHtml(item.row, n),
    )
    .join('')

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8"/>
  <title>メッキ投入スケジュール ${escapeHtmlForPrint(workDate)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { font-family: 'Segoe UI', 'Hiragino Sans', Meiryo, sans-serif; margin: 12px; color: #303133; font-size: 11pt; background: #fff; }
    .print-meta { margin-bottom: 8px; font-size: 10pt; color: #606266; line-height: 1.5; }
    .print-meta span { display: inline-block; margin-right: 16px; }
    .kpi-grid { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .kpi-chip {
      display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px;
      border: 1px solid #ebeef5; background: #fff;
    }
    .kpi-chip-l { font-size: 11px; color: #909399; }
    .kpi-chip-v { font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums; color: #303133; }
    .lap-board { padding: 6px; border: 1px solid #ebeef5; border-radius: 8px; background: #fff; }
    .lap-board-scroll { width: 100%; overflow: visible; border-radius: 6px; }
    .lap-board-grid {
      display: grid; align-items: stretch; gap: 0; width: max-content; box-sizing: border-box;
    }
    .lap-board-head {
      margin-bottom: 0; border-radius: 6px 6px 0 0; overflow: hidden;
      border: 1px solid #ebeef5; border-bottom: none; background: #fff;
    }
    .lap-board-body-row {
      border: 1px solid #ebeef5; border-top: none; background: #fff;
      break-inside: avoid; page-break-inside: avoid;
    }
    .lap-board-body-row:last-of-type { border-radius: 0 0 6px 6px; }
    .lap-board-date-row {
      border: 1px solid #ebeef5; border-top: none; background: #ecf5ff;
      break-inside: avoid; page-break-inside: avoid;
    }
    .lap-date-label {
      display: flex; align-items: center; justify-content: flex-end; padding: 4px 6px;
      font-size: 11px; font-weight: 700; color: #409eff;
      border-right: 1px solid #d9ecff; background: #ecf5ff;
    }
    .lap-date-band { grid-column: 2 / -1; min-height: 26px; background: #ecf5ff; }
    .lap-corner {
      display: flex; align-items: center; justify-content: center; padding: 5px 3px;
      font-size: 10px; font-weight: 600; color: #909399;
      border-right: 1px solid #ebeef5; background: #f5f7fa;
    }
    .lap-col-head {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 1px; line-height: 1.15; padding: 5px 3px;
      font-size: 10px; font-weight: 600; color: #909399;
      border-right: 1px solid #ebeef5; background: #f5f7fa;
    }
    .lap-col-head-n { font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums; color: #409eff; }
    .lap-col-head-s { font-size: 9px; font-weight: 500; opacity: 0.88; }
    .lap-board-grid > *:last-child { border-right: none; }
    .lap-board-body-row .lap-label {
      display: flex; align-items: center; justify-content: flex-end; padding-right: 6px;
      font-size: 11px; font-weight: 600; color: #909399;
      border-right: 1px solid #ebeef5; background: #fff;
    }
    .lap-merged-host {
      grid-column: 2 / -1; display: grid; align-items: stretch; min-height: 38px;
      box-sizing: border-box; border-right: none;
    }
    .lap-merged-seg {
      position: relative; min-width: 0;
      padding: 3px 4px; margin: 2px 0; box-sizing: border-box;
      border: 1px solid rgba(0,0,0,0.06); border-radius: 6px;
    }
    .lap-merged-seg--manual { outline: 2px solid #fa8c16; outline-offset: -1px; z-index: 1; }
    .lap-merged-seg--rush { outline: 2px solid #cf1322; outline-offset: -1px; z-index: 1; }
    .lap-merged-label-stack {
      position: absolute; top: 2px; right: 3px; left: 3px; bottom: 2px;
      display: flex; flex-direction: column; align-items: stretch; gap: 2px; overflow: hidden;
    }
    .lap-merged-text { line-height: 1.25; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600; color: #303133; }
    .lap-merged-text--jig { align-self: flex-end; font-size: 9px; text-align: right; }
    .lap-merged-text--calc { position: absolute; top: 50%; left: 0; right: 0; transform: translateY(-50%); font-size: 11px; text-align: left; font-weight: 700; color: #409eff; }
    .lap-merged-tail {
      display: flex; flex-direction: column; gap: 2px; min-width: 0; padding: 2px;
      box-sizing: border-box; border-left: 1px solid #ebeef5;
    }
    .lap-merged-tail-item {
      position: relative; flex: 0 0 auto; min-height: 22px;
      padding: 2px 3px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.06); box-sizing: border-box;
    }
    .lap-col {
      min-width: 0; max-width: 100%; border-right: 1px solid #ebeef5; padding: 2px 1px;
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
    .lap-track--grid {
      flex: 1; display: flex; flex-direction: column; min-height: 36px; gap: 2px;
      border-radius: 4px; overflow: hidden; background: #f5f7fa;
    }
    .lap-segment--cell {
      position: relative; min-height: 20px; padding: 2px 4px; border-radius: 2px;
    }
    .lap-segment--manual { outline: 2px solid #fa8c16; outline-offset: -1px; z-index: 1; }
    .lap-segment--rush { outline: 2px solid #cf1322; outline-offset: -1px; z-index: 1; }
    .lap-segment-text {
      position: absolute; top: 2px; right: 3px; left: auto;
      font-size: 9px; line-height: 1.2; text-align: right; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis; max-width: calc(100% - 6px); font-weight: 600;
    }
    @media print {
      @page { size: A3 landscape; margin: 8mm; }
      html, body { margin: 0; padding: 0; }
      * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      .kpi-grid { break-inside: avoid; }
      .lap-board { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="print-meta">
    <span>作業日：${escapeHtmlForPrint(workDate)}</span>
    <span>印刷日時（JST）：${printedAt}</span>
    <span>${escapeHtmlForPrint(layoutDesc)}</span>
  </div>
  <div class="kpi-grid">
    <div class="kpi-chip"><span class="kpi-chip-l">総枠数</span><span class="kpi-chip-v">${k.totalSlots}</span></div>
    <div class="kpi-chip"><span class="kpi-chip-l">使用中</span><span class="kpi-chip-v">${k.usedSlots}</span></div>
    <div class="kpi-chip"><span class="kpi-chip-l">空き枠</span><span class="kpi-chip-v">${k.remainSlots}</span></div>
    <div class="kpi-chip"><span class="kpi-chip-l">充填率</span><span class="kpi-chip-v">${k.utilizationPct}%</span></div>
    <div class="kpi-chip"><span class="kpi-chip-l">見込み時間（分）</span><span class="kpi-chip-v">${k.estimatedMinutes}</span></div>
    <div class="kpi-chip"><span class="kpi-chip-l">割当枠数</span><span class="kpi-chip-v">${scheduleCards.value.length}</span></div>
    <div class="kpi-chip"><span class="kpi-chip-l">計画数量</span><span class="kpi-chip-v">${k.totalPlannedQty}</span></div>
  </div>
  <div class="lap-board">
    <div class="lap-board-scroll">
      <div class="lap-board-grid lap-board-head" style="${headGridStyle}">
        <div class="lap-corner">周</div>
        ${headCols}
      </div>
      ${boardBody}
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
    'left:-12000px',
    'top:0',
    'width:420mm',
    'min-height:297mm',
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
      requestAnimationFrame(doPrint)
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

const kpi = computed(() => {
  const jigs = layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value
  const cycle = minutesPerLap.value
  if (jigs <= 0 || cycle <= 0) {
    const totalPlannedQty = scheduleCards.value.reduce((s, c) => s + Math.max(0, Math.floor(num(c.qty))), 0)
    return { totalSlots: 0, usedSlots: 0, remainSlots: 0, utilizationPct: '—', estimatedMinutes: 0, totalPlannedQty }
  }
  const lapsPerDay = Math.floor(PLATING_DAY_MINUTES / cycle)
  const totalSlots =
    layoutBoardReady.value && layoutMaxLaps.value > 0
      ? layoutMaxLaps.value * jigs
      : lapsPerDay * jigs
  const usedSlots = scheduleCards.value.filter((c) => c.qty > 0).length
  const remainSlots = Math.max(totalSlots - usedSlots, 0)
  const totalPlannedQty = scheduleCards.value.reduce((s, c) => s + Math.max(0, Math.floor(num(c.qty))), 0)
  /** 充填率＝使用中の枠数 / 総枠数（数量ではなく枠ベースで算出） */
  const utilizationPct = totalSlots > 0 ? ((usedSlots / totalSlots) * 100).toFixed(1) : '—'
  const usedLaps = jigs > 0 ? Math.ceil(usedSlots / jigs) : 0
  const estimatedMinutes = usedLaps * cycle
  return { totalSlots, usedSlots, remainSlots, utilizationPct, estimatedMinutes, totalPlannedQty }
})

function clearSchedule() {
  scheduleCards.value = []
  standardPositions.value = new Map()
  layoutBoardReady.value = false
  layoutBlocks.value = []
  void flushBoardPersist()
}

watch(
  scheduleCards,
  () => {
    nextTick(() => initBoardLapSortables())
    scheduleBoardAutosave()
  },
  { deep: true },
)

watch(lapGridRows, () => {
  nextTick(() => initBoardLapSortables())
})
watch(leftRows, () => { nextTick(() => bindTableRowDrag(leftTableRef, leftRows.value, 'left')) })
watch(rightRows, () => { nextTick(() => bindTableRowDrag(rightTableRef, rightRows.value, 'right')) })
watch(
  [leftInventoryDate, rightGenDate],
  () => {
    void loadSummaryPair()
    void loadJigAvailability()
  },
  { immediate: true },
)

watch(
  draftWorkDate,
  () => {
    if (syncingDraftWorkDateFromLoad.value) return
    void loadLatestDraft({ autoMode: true, autoSyncWorkDate: false })
    void loadJigAvailability()
  },
  { flush: 'sync' },
)
onMounted(() => {
  void loadLatestDraft({ autoMode: true, autoSyncWorkDate: true })
  loadJigAvailability()
  nextTick(() => {
    bindTableRowDrag(leftTableRef, leftRows.value, 'left')
    bindTableRowDrag(rightTableRef, rightRows.value, 'right')
    initBoardLapSortables()
  })
})

onBeforeUnmount(() => {
  cancelBoardAutosaveTimer()
  destroyLapTrackSortables()
  destroyLapMergedSortables()
})
</script>

<style scoped>
.plating-planning-page {
  --pp-radius: 12px;
  --pp-border: var(--el-border-color-light);
  padding: 10px 12px 16px;
  max-width: 1680px;
  margin: 0 auto;
  background: var(--el-bg-color-page);
  min-height: 100%;
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px 16px;
  margin-bottom: 10px;
  padding: 2px 2px 8px;
  border-bottom: 1px solid var(--pp-border);
}

.page-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--el-text-color-primary);
}

.page-flow {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.flow-i {
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
}

.flow-dot {
  display: inline-block;
  width: 4px;
  height: 4px;
  margin: 0 6px;
  border-radius: 50%;
  background: var(--el-border-color);
  vertical-align: middle;
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

.jig-card-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.jig-meta-pill--hint {
  color: var(--el-text-color-placeholder);
  background: transparent;
  border: 1px dashed var(--el-border-color-lighter);
}

.pp-card--board :deep(.el-card__body) {
  padding-top: 8px;
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

.lap-copy-grid {
  margin-bottom: 8px;
}

.lap-copy-select {
  width: 100%;
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

.lap-board--jig-drop {
  border-color: color-mix(in oklab, var(--el-color-primary) 55%, var(--el-border-color));
  box-shadow: 0 0 0 2px color-mix(in oklab, var(--el-color-primary-light-5) 40%, transparent);
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

.lap-board-outer {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  scrollbar-gutter: stable;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.lap-board-layout {
  display: flex;
  flex-direction: column;
  width: max-content;
  min-width: 100%;
}

.lap-board-row {
  display: grid;
  grid-template-columns: 76px max-content;
  align-items: stretch;
  border-bottom: 1px solid var(--el-border-color-lighter);
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
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.06);
}

.lap-board-row--head .lap-rail-cell,
.lap-board-row--head .lap-board-grid {
  min-height: 36px;
}

.lap-rail-head {
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
}

.lap-board-row--date .lap-rail-cell,
.lap-board-row--date .lap-board-grid {
  min-height: 28px;
}

.lap-rail-date {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-color-primary);
  background: color-mix(in oklab, var(--el-color-primary-light-9) 85%, var(--el-bg-color));
}

.lap-board-row--lap .lap-rail-cell,
.lap-board-row--lap .lap-board-grid {
  min-height: 38px;
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

.lap-col-head {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 3px;
  font-size: 10px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.lap-col-head {
  flex-direction: column;
  gap: 1px;
  line-height: 1.15;
}

.lap-col-head-n {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-primary);
}

.lap-col-head-s {
  font-size: 9px;
  font-weight: 500;
  opacity: 0.88;
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

.lap-merged-host {
  grid-column: 1 / -1;
  display: grid;
  align-items: stretch;
  min-height: 100%;
  height: 100%;
  box-sizing: border-box;
  border-right: none;
}

.lap-merged-seg {
  position: relative;
  min-width: 0;
  padding: 3px 4px;
  margin: 2px 0;
  box-sizing: border-box;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 6px;
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
  overflow: hidden;
}

.lap-merged-text {
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.lap-merged-text--jig {
  align-self: flex-end;
  font-size: 9px;
  text-align: right;
}

.lap-merged-text--calc {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  font-size: 11px;
  text-align: left;
  font-weight: 700;
  color: color-mix(in oklab, var(--el-color-primary) 75%, var(--el-text-color-primary));
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
  padding: 2px;
  box-sizing: border-box;
  border-left: 1px solid var(--el-border-color-lighter);
}

.lap-merged-tail-item {
  position: relative;
  flex: 0 0 auto;
  min-height: 22px;
  padding: 2px 3px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.06);
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

.lap-track--grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  height: 100%;
  gap: 2px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--el-fill-color);
}

.lap-segment--cell {
  position: relative;
  min-height: 20px;
  padding: 2px 4px;
  border-radius: 2px;
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
  position: absolute;
  top: 2px;
  right: 3px;
  left: auto;
  font-size: 9px;
  line-height: 1.2;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: calc(100% - 6px);
  font-weight: 600;
  color: var(--el-text-color-primary);
  pointer-events: none;
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
  min-height: 52px;
}

.jig-card-list {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
}

.jig-pick-card {
  flex: 0 0 140px;
  width: 140px;
  max-width: 140px;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 6px;
  border-radius: 8px;
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

.jig-pick-card__label {
  display: block;
  width: 100%;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.35;
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

.jig-card-list-hint {
  color: var(--el-text-color-secondary);
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
