<template>
  <div class="planning-page">
    <!-- ─── Page Header ─── -->
    <div class="plan-hd">
      <h2 class="plan-hd-title">成型計画作成</h2>
      <p class="plan-hd-sub">基準開始月・工程・設備の順で指定し、品目と数量を登録。ライン上で順次つなげてガントを表示します。</p>
    </div>

    <!-- ─── Filter Bar ─── -->
    <div class="plan-card setup-section">
      <div class="setup-bar">
        <el-form :inline="true" label-position="left" class="setup-form">
          <el-form-item label="基準開始月">
            <el-date-picker
              v-model="anchorMonth"
              type="month"
              value-format="YYYY-MM"
              placeholder="先頭計画の着手月"
              style="width: 120px"
            />
          </el-form-item>
          <el-form-item label-width="0">
            <el-button type="default" class="btn-soft btn-soft--indigo" @click="openLineReplanAnchorDialog">
              再計算アンカー日設定
            </el-button>
          </el-form-item>
          <el-form-item label="工程" required>
            <el-select
              v-model="selectedProcessCd"
              filterable
              clearable
              placeholder="先に工程を選択"
              style="width: 160px"
              :loading="loadingProcesses"
              @change="onProcessChange"
            >
              <el-option
                v-for="p in processOptions"
                :key="p.process_cd"
                :value="p.process_cd"
                :label="`${p.process_cd} — ${p.process_name}`"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="ライン">
            <el-select
              v-model="selectedLineId"
              placeholder="ラインを選択"
              style="width: 180px"
              :disabled="!selectedProcessCd"
              :loading="loadingLines"
              @change="onLineChange"
            >
              <el-option
                v-for="line in lines"
                :key="line.id"
                :value="line.id"
                :label="productionLineOptionLabel(line)"
              />
            </el-select>
          </el-form-item>
          <el-form-item class="setup-fi-btn" label-width="0">
            <el-button type="primary" class="btn-accent btn-accent--primary" :loading="loadingSchedules" @click="loadSchedules">
              計画を取得
            </el-button>
          </el-form-item>
        </el-form>
        <p
          v-if="selectedProcessCd && !loadingLines && lines.length === 0"
          class="ee-empty-hint"
        >
          この工程に該当する設備がありません（設備マスタの「種別」が工程名または工程CDと一致する行がAPS対象である必要があります）。
        </p>
      </div>
    </div>

    <!-- ─── Add Plan ─── -->
    <div v-if="selectedLineId" class="plan-card add-section">
      <div class="plan-sec-hd add-section-hd">計画追加</div>
      <div class="add-plan-block">
        <div class="add-row add-row--top">
          <el-form :inline="true" :model="newEntry" label-position="left" class="add-form add-form--top">
            <el-form-item label="製品名" required class="add-fi-product">
              <el-select
                v-model="selectedEeId"
                filterable
                clearable
                placeholder="製品を選択"
                class="add-select-product"
                :loading="loadingEeProducts"
                @change="onEeProductChange"
              >
                <el-option
                  v-for="row in eeProducts"
                  :key="row.id"
                  :value="row.id"
                  :label="eeOptionLabel(row)"
                />
              </el-select>
            </el-form-item>
          </el-form>
          <div v-if="eeStatsDisplay" class="ee-stats-chip">
            <div class="ee-stat-chip">
              <span class="ee-stat-label">能率</span>
              <span class="ee-readonly">{{ eeStatsDisplay.efficiency_rate }}</span>
              <span class="ee-readonly-unit">本/H</span>
            </div>
            <div class="ee-stat-chip">
              <span class="ee-stat-label">段取</span>
              <span class="ee-readonly">{{ eeStatsDisplay.step_time ?? '—' }}</span>
              <span class="ee-readonly-unit">分</span>
            </div>
            <div class="ee-stat-chip">
              <span class="ee-stat-label">ロット</span>
              <span class="ee-readonly">{{ eeStatsDisplay.lot_size ?? '—' }}</span>
              <span class="ee-readonly-unit">本/ロット</span>
            </div>
            <div class="ee-stat-chip ee-stat-chip--wide">
              <span class="ee-stat-label">最大日産</span>
              <span class="ee-readonly">{{ eeStatsDisplay.maxDaily }}</span>
              <span class="ee-readonly-unit">個/（⌊能率×{{ EE_DAILY_HOURS_MAX }}⌋）</span>
            </div>
          </div>
        </div>

        <el-form :inline="true" :model="newEntry" label-position="left" class="add-form add-form--main">
          <el-form-item label="入力方式" class="add-fi-tight">
            <el-radio-group v-model="addQtyMode" size="small">
              <el-radio-button value="batch">ロット数</el-radio-button>
              <el-radio-button value="piece">本数</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="追加先" class="add-fi-tight">
            <div class="add-merge-row">
              <el-radio-group v-model="addMergeMode" size="small">
                <el-radio-button value="new">新規行</el-radio-button>
                <el-radio-button
                  value="merge"
                  :disabled="mergeableSchedules.length === 0"
                >
                  既存に合算
                </el-radio-button>
              </el-radio-group>
              <span
                v-if="schedules.length > 0 && mergeableSchedules.length === 0 && (newEntry.product_cd || newEntry.item_name)"
                class="add-merge-hint"
              >
                計画一覧に同一製品がありません
              </span>
            </div>
          </el-form-item>
          <!-- 既存に合算：合算先セレクトのすぐ右にロット数・追加（行末へ押し出さない） -->
          <template v-if="addMergeMode === 'merge'">
            <div class="add-merge-qty-group">
              <el-form-item
                label="合算先"
                required
                class="add-fi-merge add-fi-merge--inline"
              >
                <el-select
                  v-model="mergeTargetScheduleId"
                  filterable
                  clearable
                  placeholder="同一製品の行を選択"
                  class="add-select-merge add-select-merge--inline"
                  :disabled="mergeableSchedules.length === 0"
                >
                  <el-option
                    v-for="s in mergeableSchedules"
                    :key="s.id"
                    :label="mergeTargetOptionLabel(s)"
                    :value="s.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item
                :label="addQtyMode === 'batch' ? 'ロット数' : '本数'"
                required
                class="add-fi-qty add-fi-qty--inline"
              >
                <el-input
                  v-model="plannedQtyInput"
                  clearable
                  size="small"
                  :placeholder="addQtyMode === 'batch' ? 'ロット数' : '本数'"
                  class="add-input-qty"
                  maxlength="6"
                />
              </el-form-item>
              <el-form-item label-width="0" class="add-fi-btn add-fi-btn--inline">
                <div class="add-btn-hint-row">
                  <el-button
                    type="success"
                    class="btn-accent btn-accent--success"
                    size="small"
                    :loading="adding"
                    :disabled="!canAddQty"
                    @click="addSchedule"
                  >
                    追加
                  </el-button>
                  <span v-if="addQtySummary" class="add-qty-hint">{{ addQtySummary }}</span>
                </div>
              </el-form-item>
            </div>
          </template>
          <template v-else>
            <el-form-item
              :label="addQtyMode === 'batch' ? 'ロット数' : '本数'"
              required
              class="add-fi-qty"
            >
              <el-input
                v-model="plannedQtyInput"
                clearable
                size="small"
                :placeholder="addQtyMode === 'batch' ? 'ロット数' : '本数'"
                class="add-input-qty"
                maxlength="6"
              />
            </el-form-item>
            <el-form-item label-width="0" class="add-fi-btn">
              <div class="add-btn-hint-row">
                <el-button
                  type="success"
                  class="btn-accent btn-accent--success"
                  size="small"
                  :loading="adding"
                  :disabled="!canAddQty"
                  @click="addSchedule"
                >
                  追加
                </el-button>
                <span v-if="addQtySummary" class="add-qty-hint">{{ addQtySummary }}</span>
              </div>
            </el-form-item>
          </template>
        </el-form>
      </div>
      <p v-if="selectedLineId && !loadingEeProducts && eeProducts.length === 0" class="ee-empty-hint add-empty-hint">
        この設備に紐づく設備能率（equipment_efficiency）の製品がありません。
      </p>
    </div>

    <!-- ─── Empty State ─── -->
    <div
      v-if="selectedLineId && schedulesFetched && !loadingSchedules && schedules.length === 0"
      class="plan-card schedule-empty"
    >
      <el-empty description="計画データがありません" />
    </div>

    <!-- ─── Schedule List ─── -->
    <div v-if="schedules.length > 0" class="plan-card schedule-section">
      <div class="plan-sec-hd plan-sec-hd--schedule">
        <div class="plan-sec-hd-left">
          計画一覧
          <span class="plan-sec-badge">{{ scheduleCountBadge }}</span>
          <span class="plan-sec-sub">
            {{ showCompletedSchedules ? '完了を含む表示では並べ替えできません' : '行をドラッグして順序を変更' }}
          </span>
        </div>
        <div class="schedule-actions">
          <el-switch
            v-model="showCompletedSchedules"
            size="small"
            inline-prompt
            :active-text="'含む完了'"
            :inactive-text="'未完のみ'"
            class="schedule-completed-switch"
          />
          <el-button
            type="warning"
            size="small"
            class="schedule-replan-btn btn-accent btn-accent--warning"
            :loading="replanning"
            @click="replanAll"
          >
            ライン順で再計算
          </el-button>
        </div>
      </div>
      <el-table
        ref="scheduleTableRef"
        :data="visibleSchedules"
        border
        stripe
        size="small"
        class="schedule-table schedule-table-draggable"
        row-key="id"
      >
        <el-table-column
          label="順位"
          width="64"
          align="center"
        >
      <template #header>
            <span class="schedule-order-head" title="行をドラッグして順序を変更">順位</span>
          </template>
          <template #default="{ row }">
            <span class="order-num schedule-drag-hint" :title="`ID: ${row.id}`">
              {{ row.order_no ?? '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="製品名" width="130" />
        <!-- <el-table-column prop="product_cd" label="製品CD" width="110" /> -->
        <el-table-column label="合計(本)" width="128" align="right">
          <template #default="{ row }">
            <div
              v-if="editingScheduleTotalId === row.id"
              class="total-qty-edit-wrap"
              :data-total-edit-id="row.id"
            >
              <el-input
                v-model="plannedQtyDrafts[row.id]"
                size="small"
                class="total-qty-input"
                maxlength="10"
                :disabled="savingScheduleId === row.id"
                @keydown.esc.stop.prevent="cancelEditTotalQty"
                @keyup.enter.prevent="onTotalQtyEnter(row)"
                @blur="onTotalQtyBlur(row)"
              />
        </div>
            <span
              v-else
              class="total-qty-cell total-qty-editable"
              title="ダブルクリックで数量を変更"
              @dblclick="startEditTotalQty(row)"
            >
              {{ row.planned_process_qty?.toLocaleString() ?? '—' }}
            </span>
      </template>
        </el-table-column>
        <el-table-column prop="daily_capacity" label="標準日産能力" width="110" align="right" />
        <el-table-column prop="setup_time" label="段取（分）" width="98" align="right" />
        <el-table-column prop="start_date" label="開始日" width="100" align="center"/>
        <el-table-column prop="end_date" label="終了日" width="100" align="center"/>
        <el-table-column label="状態" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabelJa(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="進捗" width="120" align="center">
          <template #default="{ row }">
            <div class="schedule-progress-cell">
              <template v-if="scheduleProgressMap[row.id]">
                <el-tag
                  v-for="st in scheduleProgressMap[row.id]"
                  :key="st.status"
                  :type="progressStatusType(st.status)"
                  size="small"
                  effect="dark"
                  class="schedule-progress-tag"
                >
                  {{ progressStatusLabel(st.status) }}{{ st.count > 1 ? `×${st.count}` : '' }}
                </el-tag>
              </template>
              <span v-else class="schedule-progress-none">—</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="removeSchedule(row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ─── Gantt ─── -->
    <div v-if="ganttDates.length > 0 || progressLots.length > 0" class="plan-card gantt-section">
      <div class="gantt-status-legend">
        <span class="legend-item"><i class="legend-dot legend-dot--planned" />計画中</span>
        <span class="legend-item"><i class="legend-dot legend-dot--released" />指示済</span>
        <span class="legend-item"><i class="legend-dot legend-dot--in-progress" />生産中</span>
        <span class="legend-item"><i class="legend-dot legend-dot--completed" />完了</span>
        <span class="legend-item"><i class="legend-dot legend-dot--actual" />実績（成型）</span>
        <span class="legend-item"><i class="legend-dot legend-dot--wait-upstream" />前工程不良</span>
        <span class="legend-item"><i class="legend-dot legend-dot--wait-upstream" />上流待ち</span>
        <div class="gantt-range-wrap">
          <span class="gantt-range-label">表示期間</span>
          <el-date-picker
            v-model="ganttRange"
            type="daterange"
            unlink-panels
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            class="gantt-range-picker"
            @change="onGanttRangeChange"
          />
        </div>
      </div>
      <el-tabs v-model="activeGanttTab" class="gantt-tabs">
        <el-tab-pane label="ガント（日別）" name="daily">
          <div class="gantt-scroll">
            <table class="gantt-table">
              <thead>
                <tr>
                  <th
                    class="gantt-sticky gantt-sticky-line gantt-line-dbl"
                    title="ダブルクリックで稼働時間帯を編集"
                    @dblclick="openLineCapacityFromGantt"
                  >
                    ライン
                  </th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">能率</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th class="gantt-sticky gantt-sticky-actual">実績数</th>
                  <th class="gantt-sticky gantt-sticky-defect" title="表示期間内の不良合計（在庫ログ・不良）">不良数</th>
                  <th class="gantt-sticky gantt-sticky-upstream" title="表示期間内の前工程不良合計（切断・面取）">前工程不良</th>
                  <th
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-date-col"
                    :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
                  >
                    <div class="gantt-date-text">{{ d.slice(5) }}</div>
                    <div class="gantt-wd-text">{{ getWeekday(d) }}</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in ganttRows"
                  :key="row.id"
                  :class="['gantt-row', productPaletteClass(row)]"
                >
                  <td
                    class="gantt-sticky gantt-sticky-line gantt-line-dbl"
                    title="ダブルクリックで稼働時間帯を編集"
                    @dblclick.stop="openLineCapacityFromGantt"
                  >
                    {{ selectedLineDisplayName }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty }}</td>
                  <td class="gantt-sticky gantt-sticky-actual">{{ periodActualForRow(row).toLocaleString() }}</td>
                  <td class="gantt-sticky gantt-sticky-defect">{{ periodDefectForRow(row).toLocaleString() }}</td>
                  <td class="gantt-sticky gantt-sticky-upstream">{{ periodUpstreamDefectForRow(row).toLocaleString() }}</td>
                  <td
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-cell"
                    :class="ganttCellClass(row, d)"
                    :title="ganttCellTitle(row, d)"
                  >
                    <div
                      v-if="
                        (row.daily[d] || 0) !== 0 ||
                        (row.actual_daily?.[d] || 0) !== 0 ||
                        (row.defect_daily?.[d] || 0) !== 0 ||
                        (row.upstream_defect_daily?.[d] || 0) !== 0 ||
                        (row.remaining_daily?.[d] || 0) !== 0
                      "
                      class="gantt-layered"
                    >
                      <span class="gantt-layer gantt-layer--plan"><b class="gl-lbl">計</b>{{ row.daily[d] || 0 }}</span>
                      <span class="gantt-layer gantt-layer--actual"><b class="gl-lbl">実</b>{{ row.actual_daily?.[d] || 0 }}</span>
                      <span class="gantt-layer gantt-layer--defect"><b class="gl-lbl">不</b>{{ row.defect_daily?.[d] || 0 }}</span>
                      <span class="gantt-layer gantt-layer--upstream"><b class="gl-lbl">前</b>{{ row.upstream_defect_daily?.[d] || 0 }}</span>
                      <span class="gantt-layer gantt-layer--remain"><b class="gl-lbl">残</b>{{ row.remaining_daily?.[d] || 0 }}</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="ガント（時間別）" name="hourly">
          <div v-if="hourlyColumns.length === 0" class="gantt-hourly-placeholder">
            <el-empty description="時間帯別データがありません">
              <template #default>
                <p class="hourly-hint">
                  DB マイグレーション <code>099_schedule_slice_allocations.sql</code> 適用後、「ライン順で再計算」を実行すると、稼働時間帯に按分した計画が表示されます。
                </p>
              </template>
            </el-empty>
          </div>
          <div v-else class="gantt-scroll">
            <table class="gantt-table gantt-hourly-table">
              <thead>
                <tr>
                  <th class="gantt-sticky gantt-sticky-line">設備名</th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">能率</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th class="gantt-sticky gantt-sticky-actual">実績数</th>
                  <th
                    v-for="col in hourlyColumns"
                    :key="col.key"
                    class="gantt-hour-col"
                    :class="{ 'is-today': col.work_date === todayIso }"
                  >
                    <div class="gantt-hour-date">{{ col.work_date.slice(5) }}</div>
                    <div class="gantt-hour-range">{{ formatHmShiftedForHourly(col.period_start) }}–{{ formatHmShiftedForHourly(col.period_end) }}</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in hourlyRows"
                  :key="row.schedule_id"
                  :class="['gantt-row', productPaletteClassByName(row.item_name)]"
                >
                  <td class="gantt-sticky gantt-sticky-line">{{ selectedLineDisplayName }}</td>
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty ?? 0 }}</td>
                  <td class="gantt-sticky gantt-sticky-actual">{{ periodActualByScheduleId(row.schedule_id).toLocaleString() }}</td>
                  <td
                    v-for="col in hourlyColumns"
                    :key="col.key"
                    class="gantt-cell gantt-hour-cell"
                    :class="hourlyCellClass(row, col)"
                    :title="hourlyCellTitle(row, col)"
                  >
                    <span v-if="(row.slice_qty[col.key] || 0) > 0" class="gantt-qty">{{ row.slice_qty[col.key] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>

        <!-- ─── 生産進捗（ロット別ステータス甘特） ─── -->
        <el-tab-pane label="生産進捗" name="progress">
          <div v-if="sortedProgressLots.length === 0 && !loadingProgress" class="gantt-hourly-placeholder">
            <el-empty description="進捗データがありません（ライン順で再計算後に表示されます）" />
          </div>
          <div v-else class="gantt-scroll">
            <table class="gantt-table gantt-progress-table">
              <thead>
                <tr>
                  <th class="gantt-sticky gantt-sticky-line">ライン</th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">ロット</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th class="pgs-th-cutting" title="cutting_management（上流切断・実績/計画本数）">切断(本)</th>
                  <th class="pgs-th-status">ステータス</th>
                  <th class="pgs-th-prediction">完了予測</th>
                  <th
                    v-for="d in progressDisplayDates"
                    :key="d"
                    class="gantt-date-col"
                    :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
                  >
                    <div class="gantt-date-text">{{ d.slice(5) }}</div>
                    <div class="gantt-wd-text">{{ getWeekday(d) }}</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(lot, idx) in sortedProgressLots"
                  :key="`${lot.aps_schedule_id}_${lot.lot_number}`"
                  :class="['gantt-row', `gantt-rc-${idx % 10}`]"
                >
                  <td class="gantt-sticky gantt-sticky-line">{{ lot.production_line || selectedLineDisplayName }}</td>
                  <td class="gantt-sticky gantt-sticky-order">{{ lot.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ lot.product_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff pgs-lot-num">#{{ lot.lot_number }}</td>
                  <td
                    class="gantt-sticky gantt-sticky-planned pgs-planned-cell"
                    :title="progressPlannedCellTitle(lot)"
                  >
                    <span class="pgs-planned-main">{{ lot.planned_quantity?.toLocaleString() }}</span>
                    <span v-if="(lot.upstream_defect_qty ?? 0) > 0" class="pgs-eff-sub">
                      有効 {{ formingEffectiveDisplay(lot).toLocaleString() }}（上流不良 {{ (lot.upstream_defect_qty ?? 0).toLocaleString() }}）
                    </span>
                  </td>
                  <td class="pgs-cutting-cell">
                    <span class="pgs-cutting-qty">{{ cuttingProgressDisplay(lot) }}</span>
                    <el-tag
                      v-if="lot.cutting_completed && lot.progress_status === 'IN_PROGRESS'"
                      type="success"
                      size="small"
                      class="pgs-cutting-done-tag"
                    >確定</el-tag>
                  </td>
                  <td class="pgs-status-cell">
                    <el-tag :type="progressStatusType(lot.progress_status)" size="small" effect="dark">
                      {{ progressStatusLabel(lot.progress_status) }}
                    </el-tag>
                  </td>
                  <td class="pgs-prediction-cell">{{ formatPrediction(lot.predicted_completion) }}</td>
                  <td
                    v-for="d in progressDisplayDates"
                    :key="d"
                    class="gantt-cell"
                    :class="progressCellClass(lot, d)"
                    :title="`${lot.product_name} #${lot.lot_number}: ${((progressLotDaily[`${lot.aps_schedule_id}_${lot.lot_number}`] || {})[d]) || ''}個`"
                  >
                    <span
                      v-if="((progressLotDaily[`${lot.aps_schedule_id}_${lot.lot_number}`] || {})[d] || 0) > 0"
                      class="gantt-qty"
                    >{{ (progressLotDaily[`${lot.aps_schedule_id}_${lot.lot_number}`] || {})[d] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <p class="pgs-footnote">
              全ロットを本工程（成型）の計画・実績として表示。日別セルは schedule_details／在庫ログ同期の<strong>成型実績</strong>。
              「計画数」は計画一覧のロット本数。上流不良がある場合は切断+面取の defect を management_code で合算し、<strong>有効</strong>は再計算後の成型ロット本数（aps_batch_plans）に合わせます。
              「ステータス」「切断(本)」は上流（instruction_plans／cutting_management）のみの情報で、行の表示とは独立します。
            </p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- ガント未表示時も DOM に存在させる（v-if 内だとガント未取得の間はダイアログが無く反応しない） -->
    <el-dialog
      v-model="lineReplanAnchorDialogVisible"
      width="min(820px, 96vw)"
      top="5vh"
      append-to-body
      destroy-on-close
      :close-on-click-modal="false"
      @open="onLineReplanAnchorDialogOpen"
      class="plan-line-anchor-dialog"
    >
      <template #header>
        <div class="line-anchor-dlg-header">
          <div class="line-anchor-dlg-header-icon" aria-hidden="true">
            <el-icon :size="26"><Calendar /></el-icon>
          </div>
          <div class="line-anchor-dlg-header-text">
            <div class="line-anchor-dlg-title">再計算アンカー日</div>
            <div class="line-anchor-dlg-meta">
              <el-tag size="small" type="primary" effect="light" class="line-anchor-dlg-tag">
                {{ anchorDialogProcessTag }}
              </el-tag>
              <span class="line-anchor-dlg-meta-note">上記工程に該当する APS 設備のみ（設備マスタの種別＝工程名／工程CD）</span>
            </div>
          </div>
        </div>
      </template>

      <div class="line-anchor-dlg-inner">
        <div class="line-anchor-dlg-hint-card">
          順次再計算の開始日を設備ごとに保存します。保存済みは<strong>最優先</strong>で使われます（今日への繰り上げなし）。クリアすると「基準月1日」と「今日」の従来ロジックに戻ります。
        </div>

        <el-empty
          v-if="!loadingLineReplanAnchors && lineReplanAnchorRows.length === 0"
          description="この工程に該当する設備がありません"
          :image-size="72"
        />
        <el-table
          v-else
          v-loading="loadingLineReplanAnchors"
          :data="lineReplanAnchorRows"
          class="line-anchor-dlg-table"
          border
          stripe
          size="small"
          max-height="420"
          style="width: 100%"
        >
          <el-table-column type="index" label="#" width="48" align="center" />
          <el-table-column prop="line_code" label="設備コード" width="118" />
          <el-table-column prop="line_name" label="設備名" min-width="160" show-overflow-tooltip />
          <el-table-column label="アンカー日" width="220" align="center">
            <template #default="{ row }">
              <el-date-picker
                v-model="row.anchor_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="未設定"
                clearable
                class="line-anchor-dlg-picker"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <div class="line-anchor-dlg-footer">
          <el-button class="btn-soft btn-soft--gray" @click="lineReplanAnchorDialogVisible = false">閉じる</el-button>
          <el-button type="primary" class="btn-accent btn-accent--primary" :loading="savingLineReplanAnchors" @click="saveLineReplanAnchorsFromDialog">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="lineCapacityDialogVisible"
      :title="`設備稼働設定 — ${selectedLineDisplayName}`"
      width="min(960px, 96vw)"
      top="4vh"
      destroy-on-close
      append-to-body
      class="plan-line-capacity-dialog"
    >
      <LineCapacity
        v-if="lineCapacityDialogVisible && selectedLineId != null && lineCapacityDateRange"
        embed
        :preset-line-id="selectedLineId"
        :preset-date-range="lineCapacityDateRange"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'FormingPlanning' })
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Delete } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'
import type { SortableEvent } from 'sortablejs'
import {
  fetchLines,
  fetchSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  replanLineSequence,
  fetchSchedulingGrid,
  fetchSchedulingHourlyGrid,
  fetchEquipmentEfficiencyProducts,
  fetchProductionProgress,
  fetchLineReplanAnchors,
  saveLineReplanAnchors,
  productionLineOptionLabel,
  type ProductionLine,
  type LineReplanAnchorRow,
  type ScheduleOut,
  type ScheduleGridRow,
  type HourlyGridColumn,
  type HourlyGridRow,
  type EquipmentEfficiencyProduct,
  type ProgressLotItem,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import LineCapacity from '../LineCapacity.vue'

/** 日本（Asia/Tokyo）の暦日 YYYY-MM-DD */
function formatYmdInJapan(d: Date): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d)
}

/** ISO 日付文字列 YYYY-MM-DD のグレゴリオ暦上の曜日（0=日）。列ヘッダ日付と一致させる */
function weekdayIndexForIsoDate(isoYmd: string): number {
  const p = isoYmd.trim().split('-').map((v) => Number(v))
  if (p.length !== 3 || p.some((n) => !Number.isFinite(n))) return 0
  const [y, m, d] = p
  return new Date(Date.UTC(y, m - 1, d, 12, 0, 0)).getUTCDay()
}

function firstDayOfMonthIso(month: string): string {
  return `${month}-01`
}

function lastDayOfMonthOffsetIso(month: string, offset: number): string {
  const [y, m] = month.split('-').map((v) => Number(v))
  if (!Number.isFinite(y) || !Number.isFinite(m) || m < 1 || m > 12) return `${month}-28`
  const d = new Date(y, m + offset, 0)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

/** 表示期間と同じ全日列（日次ガントの dates と一致）。暦日は日本時区で積み上げ */
function expandDateRangeIso(startIso: string, endIso: string): string[] {
  const sd = new Date(`${startIso.trim()}T12:00:00+09:00`)
  const ed = new Date(`${endIso.trim()}T12:00:00+09:00`)
  if (Number.isNaN(sd.getTime()) || Number.isNaN(ed.getTime()) || ed < sd) return []
  const out: string[] = []
  let t = sd.getTime()
  const endT = ed.getTime()
  while (t <= endT) {
    out.push(formatYmdInJapan(new Date(t)))
    t += 24 * 60 * 60 * 1000
  }
  return out
}

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const selectedProcessCd = ref<string>('KT04')
const processOptions = ref<ProcessItem[]>([])
const loadingProcesses = ref(false)
const loadingLines = ref(false)
const DEFAULT_ANCHOR_MONTH = '2026-04'
const anchorMonth = ref<string>(DEFAULT_ANCHOR_MONTH)
const anchorDate = ref<string>(firstDayOfMonthIso(DEFAULT_ANCHOR_MONTH))
const lineReplanAnchorDialogVisible = ref(false)
const lineReplanAnchorRows = ref<LineReplanAnchorRow[]>([])
const loadingLineReplanAnchors = ref(false)
const savingLineReplanAnchors = ref(false)
const ganttRange = ref<[string, string]>([
  firstDayOfMonthIso(DEFAULT_ANCHOR_MONTH),
  lastDayOfMonthOffsetIso(DEFAULT_ANCHOR_MONTH, 1),
])
const loadingSchedules = ref(false)
const adding = ref(false)
const replanning = ref(false)
const savingScheduleId = ref<number | null>(null)
const reordering = ref(false)
const schedules = ref<ScheduleOut[]>([])
const showCompletedSchedules = ref(false)
/** 合計(本) インライン編集用の下書き */
const plannedQtyDrafts = ref<Record<number, string>>({})
/** 合計(本) を編集中のスケジュール id（ダブルクリックで編集） */
const editingScheduleTotalId = ref<number | null>(null)
/** Enter 確定直後の blur で二重保存しない */
const skipNextTotalQtyBlur = ref(false)
/** el-table インスタンス（行ドラッグ用） */
const scheduleTableRef = ref<{ $el?: HTMLElement } | null>(null)
let scheduleSortable: Sortable | null = null
const eeProducts = ref<EquipmentEfficiencyProduct[]>([])
const loadingEeProducts = ref(false)
/** equipment_efficiency.id */
const selectedEeId = ref<number | null>(null)

/** 計画追加：ロット数（テキスト入力→追加時に整数化） */
const plannedQtyInput = ref('')
const addQtyMode = ref<'batch' | 'piece'>('batch')
/** 計画追加：新規行 or 同一製品の既存行へ合計(本)を加算 */
const addMergeMode = ref<'new' | 'merge'>('new')
const mergeTargetScheduleId = ref<number | null>(null)

const newEntry = ref({
  item_name: '',
  product_cd: '',
  daily_capacity: 0,
  setup_time: 0,
})

/** 設備能率マスタ由来の標準/最大稼働時間（日） */
const EE_DAILY_HOURS_STANDARD = 15.3
const EE_DAILY_HOURS_MAX = 23.3

/** 選択中の EE 行：表示用能率・段取・最大日産 */
const eeStatsDisplay = computed(() => {
  if (selectedEeId.value == null) return null
  const row = eeProducts.value.find((r) => r.id === selectedEeId.value)
  if (!row) return null
  const rate = Number(row.efficiency_rate) || 0
  const st = row.step_time
  const maxDaily = rate > 0 ? Math.floor(rate * EE_DAILY_HOURS_MAX) : 0
  const lotSize = row.lot_size
  return {
    efficiency_rate: rate,
    step_time: st != null ? st : null,
    maxDaily,
    lot_size: lotSize != null && Number.isFinite(Number(lotSize)) ? Number(lotSize) : null,
  }
})

const ganttDates = ref<string[]>([])
const ganttRows = ref<ScheduleGridRow[]>([])
const hourlyColumns = ref<HourlyGridColumn[]>([])
const hourlyRows = ref<HourlyGridRow[]>([])
/** 生産進捗：全ロットを表示。日別＝成型計画・実績。ステータス・切断(本)列＝上流 instruction/cutting */
const progressLots = ref<ProgressLotItem[]>([])
const progressLotDaily = ref<Record<string, Record<string, number>>>({})
/** 日別セル: ACTUAL | PLANNED | WAIT_UPSTREAM */
const progressLotDailySource = ref<Record<string, Record<string, string>>>({})
const loadingProgress = ref(false)
/** ガント表示タブ：daily | hourly | progress */
const activeGanttTab = ref('daily')
/** 計画を取得 API を一度でも成功で呼んだか（空配列含む） */
const schedulesFetched = ref(false)

/** 生産進捗の日付列：表示期間起点の全日（日次ガントと揃え、実績ゼロの日も列を出す） */
const progressDisplayDates = computed(() => {
  if (ganttDates.value.length > 0) return ganttDates.value
  const month = (anchorMonth.value || DEFAULT_ANCHOR_MONTH).trim()
  const sd = (ganttRange.value?.[0] || anchorDate.value || firstDayOfMonthIso(month)).trim()
  const ed = (ganttRange.value?.[1] || lastDayOfMonthOffsetIso(month, 1)).trim()
  return expandDateRangeIso(sd, ed)
})

/** 計画一覧の各行に対応するロット進捗サマリ（{ status, count }[] per schedule id） */
const scheduleProgressMap = computed(() => {
  const map: Record<number, { status: string; count: number }[]> = {}
  if (progressLots.value.length === 0) return map
  const bySchedule: Record<number, Record<string, number>> = {}
  for (const lot of progressLots.value) {
    const sid = lot.aps_schedule_id
    if (!bySchedule[sid]) bySchedule[sid] = {}
    bySchedule[sid][lot.progress_status] = (bySchedule[sid][lot.progress_status] || 0) + 1
  }
  const order = ['IN_PROGRESS', 'RELEASED', 'PLANNED', 'COMPLETED']
  for (const [sid, counts] of Object.entries(bySchedule)) {
    const arr = Object.entries(counts)
      .map(([status, count]) => ({ status, count }))
      .sort((a, b) => order.indexOf(a.status) - order.indexOf(b.status))
    map[Number(sid)] = arr
  }
  return map
})

/** 生産進捗の行を順位順に安定ソート（同順位内は計画ID→ロット番号） */
const sortedProgressLots = computed(() => {
  return [...progressLots.value].sort((a, b) => {
    const oa = a.order_no ?? 1_000_000 + a.aps_schedule_id
    const ob = b.order_no ?? 1_000_000 + b.aps_schedule_id
    if (oa !== ob) return oa - ob
    if (a.aps_schedule_id !== b.aps_schedule_id) return a.aps_schedule_id - b.aps_schedule_id
    const la = Number(a.lot_number)
    const lb = Number(b.lot_number)
    const na = Number.isFinite(la)
    const nb = Number.isFinite(lb)
    if (na && nb && la !== lb) return la - lb
    return String(a.lot_number).localeCompare(String(b.lot_number))
  })
})

watch(anchorMonth, (v) => {
  if (!v) return
  anchorDate.value = firstDayOfMonthIso(v)
  ganttRange.value = [firstDayOfMonthIso(v), lastDayOfMonthOffsetIso(v, 1)]
})

/** order_no → id 安定ソート（一覧・移動用） */
const sortedSchedules = computed(() => {
  return [...schedules.value].sort((a, b) => {
    const oa = a.order_no ?? 1_000_000 + a.id
    const ob = b.order_no ?? 1_000_000 + b.id
    if (oa !== ob) return oa - ob
    return a.id - b.id
  })
})

/** 未完了行のみ（現場で操作する実行キュー） */
const activeSchedules = computed(() => sortedSchedules.value.filter((s) => s.status !== 'COMPLETED'))

/** 一覧表示対象（既定は未完了のみ、必要時に完了含む） */
const visibleSchedules = computed(() => (showCompletedSchedules.value ? sortedSchedules.value : activeSchedules.value))

const scheduleCountBadge = computed(() => `${visibleSchedules.value.length}/${schedules.value.length}`)

watch([showCompletedSchedules, () => visibleSchedules.value.length], () => {
  initScheduleSortable()
})

/** 計画一覧のうち、追加フォームで選んだ製品と同一の行（product_cd 優先、無ければ品名一致） */
const mergeableSchedules = computed((): ScheduleOut[] => {
  const ep = (newEntry.value.product_cd || '').trim()
  const en = (newEntry.value.item_name || '').trim()
  if (!ep && !en) return []
  return activeSchedules.value.filter((s) => {
    const sp = (s.product_cd || '').trim()
    if (ep && sp) return sp === ep
    if (ep || sp) return false
    return en !== '' && (s.item_name || '').trim() === en
  })
})

function mergeTargetOptionLabel(s: ScheduleOut): string {
  const ord = s.order_no ?? '—'
  const qty = Number(s.planned_process_qty ?? 0)
  const name = (s.item_name || '').trim()
  const shortName = name.length > 28 ? `${name.slice(0, 28)}…` : name
  return `順位 ${ord} · ${shortName || '—'} · 合計 ${qty.toLocaleString()} 本`
}

watch(mergeableSchedules, (list) => {
  if (addMergeMode.value === 'merge' && list.length === 0) {
    addMergeMode.value = 'new'
  }
  if (mergeTargetScheduleId.value != null && !list.some((s) => s.id === mergeTargetScheduleId.value)) {
    mergeTargetScheduleId.value = null
  }
})

watch([addMergeMode, mergeableSchedules], () => {
  if (addMergeMode.value !== 'merge') return
  const list = mergeableSchedules.value
  if (list.length === 1) {
    mergeTargetScheduleId.value = list[0].id
  }
})

/** 計画追加：ロット数→合計本数・合算プレビュー */
const addQtySummary = computed(() => {
  const qtyNum = parseInt((plannedQtyInput.value || '').trim(), 10)
  if (!Number.isFinite(qtyNum) || qtyNum < 1) return ''
  let delta = 0
  let base = ''
  if (addQtyMode.value === 'piece') {
    delta = qtyNum
    base = `追加予定: ${qtyNum.toLocaleString()} 本`
  } else {
    const lotSize = eeStatsDisplay.value?.lot_size
    if (lotSize == null || lotSize <= 0) return ''
    delta = qtyNum * lotSize
    base = `${lotSize.toLocaleString()} × ${qtyNum} = ${delta.toLocaleString()} 本`
  }
  if (addMergeMode.value === 'merge' && mergeTargetScheduleId.value != null && delta > 0) {
    const t = schedules.value.find((s) => s.id === mergeTargetScheduleId.value)
    if (t && mergeableSchedules.value.some((s) => s.id === t.id)) {
      const cur = Number(t.planned_process_qty ?? 0)
      return `${base} → 合算後 ${(cur + delta).toLocaleString()} 本`
    }
  }
  return base
})

/** 計画追加 ボタン有効判定 */
const canAddQty = computed(() => {
  if (selectedEeId.value == null || !newEntry.value.item_name) return false
  const qtyNum = parseInt((plannedQtyInput.value || '').trim(), 10)
  if (!Number.isFinite(qtyNum) || qtyNum < 1) return false
  if (addQtyMode.value === 'batch') {
    const lotSize = eeStatsDisplay.value?.lot_size
    if (lotSize == null || lotSize <= 0) return false
  }
  if (addMergeMode.value === 'merge') {
    if (mergeableSchedules.value.length === 0) return false
    if (mergeTargetScheduleId.value == null) return false
    if (!mergeableSchedules.value.some((s) => s.id === mergeTargetScheduleId.value)) return false
  }
  return true
})

/** ガント左列：現在選択設備の表示名 */
const selectedLineDisplayName = computed(() => {
  if (selectedLineId.value == null) return '—'
  const ln = lines.value.find((l) => l.id === selectedLineId.value)
  if (!ln) return '—'
  const name = ln.line_name?.trim()
  if (name) return name
  return (ln.line_code?.trim() || String(ln.id))
})

/** ガント表示期間＝設備稼働ダイアログの期間 */
const lineCapacityDateRange = computed((): [string, string] | null => {
  const gr = ganttRange.value
  if (Array.isArray(gr) && gr.length >= 2 && gr[0] && gr[1]) return [gr[0], gr[1]]
  return null
})

const lineCapacityDialogVisible = ref(false)

function openLineCapacityFromGantt() {
  if (selectedLineId.value == null) {
    ElMessage.warning('ラインを選択してください')
    return
  }
  if (!lineCapacityDateRange.value) {
    ElMessage.warning('表示期間が設定されていません')
    return
  }
  lineCapacityDialogVisible.value = true
}

function destroyScheduleSortable() {
  scheduleSortable?.destroy()
  scheduleSortable = null
}

function initScheduleSortable() {
  destroyScheduleSortable()
  if (showCompletedSchedules.value) return
  if (visibleSchedules.value.length < 2) return
  nextTick(() => {
    const root = scheduleTableRef.value?.$el
    const tbody = root?.querySelector?.('.el-table__body-wrapper tbody') as HTMLElement | undefined | null
    if (!tbody) return
    scheduleSortable = Sortable.create(tbody, {
      animation: 180,
      ghostClass: 'schedule-sortable-ghost',
      dragClass: 'schedule-sortable-drag',
      filter:
        'input, textarea, button, .el-input-number, .el-input, .el-button, .el-select, .el-radio, .el-radio-group, .el-tag, a',
      // 仅禁止拖拽启动，不阻断输入框的点击/键入
      preventOnFilter: false,
      onEnd: (evt: SortableEvent) => {
        const o = evt.oldIndex
        const n = evt.newIndex
        if (o === undefined || n === undefined || o === n) return
        void persistScheduleOrderAfterDrag(o, n)
      },
    })
  })
}

async function persistScheduleOrderAfterDrag(oldIndex: number, newIndex: number) {
  if (!selectedLineId.value || reordering.value) return
  if (showCompletedSchedules.value) return
  scheduleSortable?.option('disabled', true)

  const allSorted = sortedSchedules.value
  // 未完了行が占有する「全量一覧内の槽位编号（1..N）」。
  // これを回填することで、完了行アンカーを保ったまま重複順位を解消できる。
  const nonCompletedSlots = allSorted
    .map((s, idx) => ({ s, slotOrder: idx + 1 }))
    .filter((x) => x.s.status !== 'COMPLETED')
    .map((x) => x.slotOrder)

  const dragged = visibleSchedules.value.map((s) => s)
  const [moved] = dragged.splice(oldIndex, 1)
  dragged.splice(newIndex, 0, moved)

  const updates: { id: number; order_no: number }[] = []
  dragged.forEach((s, i) => {
    const newOrder = nonCompletedSlots[i] ?? (Math.max(...allSorted.map((x) => x.order_no ?? 0)) + i + 1)
    if (s.order_no !== newOrder) {
      updates.push({ id: s.id, order_no: newOrder })
    }
  })

  if (updates.length === 0) {
    scheduleSortable?.option('disabled', false)
    return
  }

  reordering.value = true
  try {
    await Promise.all(
      updates.map((u) => updateSchedule(u.id, { order_no: u.order_no, run_immediately: false })),
    )
    await replanLineSequence(selectedLineId.value, effectiveReplanAnchorDate())
    await loadSchedules()
    ElMessage.success('生産順を更新しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e))
    await loadSchedules()
  } finally {
    reordering.value = false
    scheduleSortable?.option('disabled', false)
  }
}

async function loadProcessOptions() {
  loadingProcesses.value = true
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const list = res.list ?? res.data?.list ?? []
    processOptions.value = Array.isArray(list) ? list : []
  } catch {
    processOptions.value = []
  } finally {
    loadingProcesses.value = false
    // 默认工程：KT04（如果不存在则保持未选择状态）
    const exists = processOptions.value.some((p) => (p.process_cd || '').trim() === 'KT04')
    if (!exists) {
      selectedProcessCd.value = ''
      return
    }
    // 触发加载设备列表
    void onProcessChange()
  }
}

async function onProcessChange() {
  selectedLineId.value = null
  schedules.value = []
  schedulesFetched.value = false
  ganttDates.value = []
  ganttRows.value = []
  hourlyColumns.value = []
  hourlyRows.value = []
  eeProducts.value = []
  selectedEeId.value = null
  lines.value = []
  const cd = (selectedProcessCd.value || '').trim()
  if (!cd) return
  loadingLines.value = true
  try {
    lines.value = await fetchLines(cd)
  } catch {
    lines.value = []
    ElMessage.error('設備一覧の取得に失敗しました')
  } finally {
    loadingLines.value = false
  }
}

onMounted(() => {
  loadProcessOptions()
})

onBeforeUnmount(() => {
  destroyScheduleSortable()
})

function formatApiError(e: unknown): string {
  const err = e as {
    response?: { data?: { detail?: string | { msg?: string }[]; message?: string } }
    message?: string
  }
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    const parts = d.map((x) => (typeof x === 'object' && x?.msg ? x.msg : String(x))).filter(Boolean)
    if (parts.length) return parts.join('；')
  }
  return err?.response?.data?.message || err?.message || 'エラーが発生しました'
}

function eeOptionLabel(row: EquipmentEfficiencyProduct): string {
  const name = row.product_name?.trim() || ''
  const cd = row.product_cd?.trim() || ''
  if (name && cd) return `${name}（${cd}）`
  return name || cd || `ID:${row.id}`
}

async function loadEeProducts() {
  selectedEeId.value = null
  plannedQtyInput.value = ''
  newEntry.value.item_name = ''
  newEntry.value.product_cd = ''
  newEntry.value.daily_capacity = 0
  newEntry.value.setup_time = 0
  if (!selectedLineId.value) {
    eeProducts.value = []
    return
  }
  loadingEeProducts.value = true
  try {
    eeProducts.value = await fetchEquipmentEfficiencyProducts(selectedLineId.value)
  } catch {
    eeProducts.value = []
  } finally {
    loadingEeProducts.value = false
  }
}

function onEeProductChange(id: number | string | null | undefined) {
  mergeTargetScheduleId.value = null
  if (id === '' || id === null || id === undefined) {
    plannedQtyInput.value = ''
    newEntry.value.item_name = ''
    newEntry.value.product_cd = ''
    newEntry.value.daily_capacity = 0
    newEntry.value.setup_time = 0
    return
  }
  const nid = Number(id)
  const row = eeProducts.value.find((r) => r.id === nid)
  if (!row) return
  newEntry.value.item_name = (row.product_name?.trim() || row.product_cd || '').trim()
  newEntry.value.product_cd = row.product_cd?.trim() || ''
  newEntry.value.setup_time = row.step_time ?? 0
  const rate = Number(row.efficiency_rate) || 0
  newEntry.value.daily_capacity = rate > 0 ? Math.floor(rate * EE_DAILY_HOURS_STANDARD) : 0
}

async function onLineChange() {
  schedules.value = []
  schedulesFetched.value = false
  ganttDates.value = []
  ganttRows.value = []
  hourlyColumns.value = []
  hourlyRows.value = []
  await loadEeProducts()
}

async function loadSchedules() {
  if (!(selectedProcessCd.value || '').trim()) {
    ElMessage.warning('工程を選択してください')
    return
  }
  if (!selectedLineId.value) {
    ElMessage.warning('設備を選択してください')
    return
  }
  loadingSchedules.value = true
  try {
    const data = await fetchSchedules({ lineId: selectedLineId.value })
    schedules.value = Array.isArray(data) ? data : []
    editingScheduleTotalId.value = null
    plannedQtyDrafts.value = {}
    schedulesFetched.value = true
    await loadGantt()
  } catch (e: unknown) {
    schedules.value = []
    schedulesFetched.value = false
    ganttDates.value = []
    ganttRows.value = []
    hourlyColumns.value = []
    hourlyRows.value = []
    ElMessage.error(formatApiError(e))
  } finally {
    loadingSchedules.value = false
    initScheduleSortable()
  }
}

async function addSchedule() {
  if (!(selectedProcessCd.value || '').trim()) {
    ElMessage.warning('工程を選択してください')
    return
  }
  if (!selectedLineId.value || selectedEeId.value == null || !newEntry.value.item_name) {
    ElMessage.warning('設備と品名（設備能率マスタ）を選択してください')
    return
  }
  if (newEntry.value.daily_capacity <= 0) {
    ElMessage.warning('日産能力を入力してください（0 より大きい値）')
    return
  }
  const rawQty = (plannedQtyInput.value || '').trim().replace(/[,，]/g, '')
  if (!rawQty) {
    ElMessage.warning(addQtyMode.value === 'batch' ? 'ロット数を入力してください' : '本数を入力してください')
    return
  }
  const qtyInputNum = parseInt(rawQty, 10)
  if (!Number.isFinite(qtyInputNum) || qtyInputNum < 1) {
    ElMessage.warning(addQtyMode.value === 'batch' ? 'ロット数は 1 以上の整数を入力してください' : '本数は 1 以上の整数を入力してください')
    return
  }

  let deltaPieces: number
  if (addQtyMode.value === 'batch') {
    const lotSize = eeStatsDisplay.value?.lot_size
    if (lotSize == null || lotSize <= 0) {
      ElMessage.warning('ロットサイズが未設定です。製品マスタで lot_size を登録してください。')
      return
    }
    deltaPieces = qtyInputNum * lotSize
  } else {
    deltaPieces = qtyInputNum
  }

  if (addMergeMode.value === 'merge') {
    const targetId = mergeTargetScheduleId.value
    if (targetId == null) {
      ElMessage.warning('合算先の計画行を選択してください')
      return
    }
    if (!mergeableSchedules.value.some((s) => s.id === targetId)) {
      ElMessage.warning('同一製品の計画のみ合算できます')
      return
    }
    const target = schedules.value.find((s) => s.id === targetId)
    if (!target) {
      ElMessage.warning('対象の計画が見つかりません。計画を取得してください')
      return
    }
  }

  adding.value = true
  try {
    if (addMergeMode.value === 'merge') {
      const targetId = mergeTargetScheduleId.value!
      const tg = schedules.value.find((s) => s.id === targetId)!
      const newTotal = Number(tg.planned_process_qty ?? 0) + deltaPieces
      await updateSchedule(targetId, { planned_process_qty: newTotal, run_immediately: false })
      await replanLineSequence(selectedLineId.value!, effectiveReplanAnchorDate())

      selectedEeId.value = null
      plannedQtyInput.value = ''
      newEntry.value.item_name = ''
      newEntry.value.product_cd = ''
      newEntry.value.daily_capacity = 0
      newEntry.value.setup_time = 0
      addMergeMode.value = 'new'
      mergeTargetScheduleId.value = null

      await loadSchedules()
      ElMessage.success('既存計画の合計(本)に加算しました')
      return
    }

    const nextOrder = schedules.value.length > 0
      ? Math.max(...schedules.value.map((s) => s.order_no ?? 0)) + 1
      : 1

    const payload: Parameters<typeof createSchedule>[0] = {
      line_id: selectedLineId.value,
      order_no: nextOrder,
      item_name: newEntry.value.item_name,
      product_cd: newEntry.value.product_cd || undefined,
      daily_capacity: newEntry.value.daily_capacity,
      setup_time: newEntry.value.setup_time,
      start_date: schedules.value.length === 0 ? (anchorDate.value || undefined) : undefined,
      run_immediately: false,
    }
    if (addQtyMode.value === 'batch') {
      const lotSize = eeStatsDisplay.value?.lot_size!
      const plannedTotalQty = qtyInputNum * lotSize
      payload.planned_batch_count = qtyInputNum
      payload.lot_size_snapshot = lotSize
      payload.planned_process_qty = plannedTotalQty
    } else {
      payload.planned_process_qty = qtyInputNum
      payload.planned_batch_count = 0
    }
    await createSchedule(payload)

    selectedEeId.value = null
    plannedQtyInput.value = ''
    newEntry.value.item_name = ''
    newEntry.value.product_cd = ''
    newEntry.value.daily_capacity = 0
    newEntry.value.setup_time = 0

    await loadSchedules()
    addMergeMode.value = 'new'
    mergeTargetScheduleId.value = null
    ElMessage.success('追加しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '追加に失敗しました')
  } finally {
    adding.value = false
  }
}

async function removeSchedule(id: number) {
  try {
    await ElMessageBox.confirm('この計画を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
    await deleteSchedule(id)
    await loadSchedules()
    ElMessage.success('削除しました')
  } catch { /* cancel */ }
}

function startEditTotalQty(row: ScheduleOut) {
  if (savingScheduleId.value != null) return
  editingScheduleTotalId.value = row.id
  plannedQtyDrafts.value[row.id] = String(row.planned_process_qty ?? '')
  nextTick(() => {
    const wrap = document.querySelector(`[data-total-edit-id="${row.id}"]`) as HTMLElement | null
    const input = wrap?.querySelector('input') as HTMLInputElement | null
    input?.focus()
    input?.select()
  })
}

function cancelEditTotalQty() {
  skipNextTotalQtyBlur.value = true
  editingScheduleTotalId.value = null
  nextTick(() => {
    skipNextTotalQtyBlur.value = false
  })
}

function onTotalQtyEnter(row: ScheduleOut) {
  skipNextTotalQtyBlur.value = true
  void saveTotalPlannedQty(row).finally(() => {
    nextTick(() => {
      skipNextTotalQtyBlur.value = false
    })
  })
}

function onTotalQtyBlur(row: ScheduleOut) {
  void nextTick(() => {
    if (skipNextTotalQtyBlur.value) {
      skipNextTotalQtyBlur.value = false
      return
    }
    void saveTotalPlannedQty(row)
  })
}

/** 合計(本) を planned_process_qty として保存（排産は本数が唯一の真理） */
async function saveTotalPlannedQty(row: ScheduleOut) {
  if (editingScheduleTotalId.value !== row.id) return
  const draft = plannedQtyDrafts.value[row.id] ?? ''
  const raw = draft.trim().replace(/[,，]/g, '')
  const val = parseInt(raw, 10)
  if (!Number.isFinite(val) || val < 1) {
    ElMessage.warning('合計(本)は 1 以上の整数を入力してください')
    return
  }
  const cur = Number(row.planned_process_qty ?? 0)
  if (val === cur) {
    editingScheduleTotalId.value = null
    return
  }
  if (!selectedLineId.value) return
  savingScheduleId.value = row.id
  try {
    await updateSchedule(row.id, {
      planned_process_qty: val,
      run_immediately: false,
    })
    await replanLineSequence(selectedLineId.value, effectiveReplanAnchorDate())
    await loadSchedules()
    ElMessage.success('合計(本)を更新しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e))
    await loadSchedulesEditingPreserve(row.id)
  } finally {
    savingScheduleId.value = null
  }
}

/** エラー時は一覧だけ再取得し、合計(本)の編集状態を可能なら維持 */
async function loadSchedulesEditingPreserve(scheduleId: number) {
  if (!selectedLineId.value) return
  loadingSchedules.value = true
  try {
    const data = await fetchSchedules({ lineId: selectedLineId.value })
    schedules.value = Array.isArray(data) ? data : []
    await loadGantt()
    const still = schedules.value.some((s) => s.id === scheduleId)
    if (still && editingScheduleTotalId.value === scheduleId) {
      const s = schedules.value.find((x) => x.id === scheduleId)
      if (s) plannedQtyDrafts.value[scheduleId] = String(s.planned_process_qty ?? '')
    } else {
      editingScheduleTotalId.value = null
    }
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e))
    editingScheduleTotalId.value = null
  } finally {
    loadingSchedules.value = false
    initScheduleSortable()
  }
}

async function replanAll() {
  if (!(selectedProcessCd.value || '').trim() || !selectedLineId.value) return
  replanning.value = true
  try {
    await replanLineSequence(selectedLineId.value, effectiveReplanAnchorDate())
    await loadSchedules()
    ElMessage.success('順次再計算が完了しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '再計算に失敗しました')
  } finally {
    replanning.value = false
  }
}

const todayIso = computed(() => formatYmdInJapan(new Date()))

/**
 * 再計算 API（replan-sequence）のクエリ錨点（フォールバック）。
 * 当該設備に DB（aps_line_replan_anchors）があればサーバ側でそちらが最優先される。
 * ここでは基準月1日と日本の今日の大きい方のみ（過去の月初に固定しない）。
 */
function effectiveReplanAnchorDate(): string {
  const anchor = (anchorDate.value || '').trim()
  const today = todayIso.value
  if (!anchor) return today
  return anchor >= today ? anchor : today
}

function openLineReplanAnchorDialog() {
  if (!(selectedProcessCd.value || '').trim()) {
    ElMessage.warning('先に工程を選択してください')
    return
  }
  lineReplanAnchorDialogVisible.value = true
}

const anchorDialogProcessTag = computed(() => {
  const cd = (selectedProcessCd.value || '').trim()
  if (!cd) return '工程未選択'
  const p = processOptions.value.find((x) => (x.process_cd || '').trim() === cd)
  return p ? `${p.process_cd} — ${p.process_name}` : cd
})

async function onLineReplanAnchorDialogOpen() {
  const pc = (selectedProcessCd.value || '').trim()
  if (!pc) {
    lineReplanAnchorRows.value = []
    return
  }
  loadingLineReplanAnchors.value = true
  try {
    const rows = await fetchLineReplanAnchors(pc)
    lineReplanAnchorRows.value = Array.isArray(rows) ? rows.map((r) => ({ ...r })) : []
  } catch {
    lineReplanAnchorRows.value = []
    ElMessage.error('アンカー一覧の取得に失敗しました')
  } finally {
    loadingLineReplanAnchors.value = false
  }
}

async function saveLineReplanAnchorsFromDialog() {
  savingLineReplanAnchors.value = true
  try {
    await saveLineReplanAnchors(
      lineReplanAnchorRows.value.map((r) => {
        const raw = r.anchor_date != null && r.anchor_date !== '' ? String(r.anchor_date).trim() : ''
        return { line_id: r.line_id, anchor_date: raw || null }
      }),
    )
    ElMessage.success('再計算アンカー日を保存しました')
    lineReplanAnchorDialogVisible.value = false
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '保存に失敗しました')
  } finally {
    savingLineReplanAnchors.value = false
  }
}

/** equipment_efficiency.efficiency_rate（本/H） */
function formatEfficiencyRatePiecesPerH(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  const s = n % 1 === 0 ? String(Math.round(n)) : n.toFixed(1)
  return `${s}本/H`
}

const HOURLY_DISPLAY_SHIFT_MINUTES = 15 * 60

function formatHm(t: string): string {
  if (!t) return ''
  const parts = t.split(':')
  return parts.length >= 2 ? `${parts[0]}:${parts[1]}` : t
}

/** 時間別ガント表示のみ、時刻を +15h 平行移動（00:00→15:00） */
function formatHmShiftedForHourly(t: string): string {
  if (!t) return ''
  const parts = t.split(':')
  if (parts.length < 2) return t
  const hh = Number(parts[0])
  const mm = Number(parts[1])
  if (Number.isNaN(hh) || Number.isNaN(mm)) return formatHm(t)
  const total = ((hh * 60 + mm + HOURLY_DISPLAY_SHIFT_MINUTES) % 1440 + 1440) % 1440
  const outH = Math.floor(total / 60)
  const outM = total % 60
  return `${String(outH).padStart(2, '0')}:${String(outM).padStart(2, '0')}`
}

function hourlyCellTitle(row: HourlyGridRow, col: HourlyGridColumn): string {
  const q = row.slice_qty[col.key] || 0
  if (q <= 0) return ''
  return `${row.item_name}: ${q}個（${col.work_date} ${formatHmShiftedForHourly(col.period_start)}–${formatHmShiftedForHourly(col.period_end)}）`
}

function hourlyCellClass(row: HourlyGridRow, col: HourlyGridColumn): Record<string, boolean> {
  const active = (row.slice_qty[col.key] || 0) > 0
  const actual = periodActualByScheduleIdAndDate(row.schedule_id, col.work_date)
  return { 'gantt-active': active, 'gantt-has-actual': active && actual > 0 }
}

function periodActualForRow(row: ScheduleGridRow): number {
  const m = row.actual_daily || {}
  const dates = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の不良合計（日別セル defect_daily と一致） */
function periodDefectForRow(row: ScheduleGridRow): number {
  const m = row.defect_daily || {}
  const dates = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の前工程不良合計（日別セル upstream_defect_daily と一致） */
function periodUpstreamDefectForRow(row: ScheduleGridRow): number {
  const m = row.upstream_defect_daily || {}
  const dates = ganttDates.value.length > 0 ? ganttDates.value : Object.keys(m)
  return dates.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

function periodActualByScheduleId(scheduleId: number): number {
  const row = ganttRows.value.find((r) => r.id === scheduleId)
  if (!row) return 0
  return periodActualForRow(row)
}

function periodActualByScheduleIdAndDate(scheduleId: number, d: string): number {
  const row = ganttRows.value.find((r) => r.id === scheduleId)
  if (!row) return 0
  return Number(row.actual_daily?.[d] || 0)
}

async function loadGantt() {
  hourlyColumns.value = []
  hourlyRows.value = []
  if (!selectedLineId.value) {
    ganttDates.value = []
    ganttRows.value = []
    return
  }
  const month = (anchorMonth.value || DEFAULT_ANCHOR_MONTH).trim()
  const sd = (ganttRange.value?.[0] || anchorDate.value || firstDayOfMonthIso(month)).trim()
  const ed = (ganttRange.value?.[1] || lastDayOfMonthOffsetIso(month, 1)).trim()

  try {
    const grid = await fetchSchedulingGrid(sd, ed, selectedLineId.value)
    ganttDates.value = grid.dates
    ganttRows.value = grid.blocks.length > 0 ? grid.blocks[0].rows : []
    activeGanttTab.value = 'daily'
    try {
      const hg = await fetchSchedulingHourlyGrid(sd, ed, selectedLineId.value)
      hourlyColumns.value = Array.isArray(hg.columns) ? hg.columns : []
      hourlyRows.value = Array.isArray(hg.rows) ? hg.rows : []
    } catch {
      hourlyColumns.value = []
      hourlyRows.value = []
    }
  } catch {
    ganttDates.value = []
    ganttRows.value = []
    hourlyColumns.value = []
    hourlyRows.value = []
  }
  void loadProgress()
}

async function onGanttRangeChange() {
  if (!selectedLineId.value) return
  await loadGantt()
}

async function loadProgress() {
  if (!selectedLineId.value) {
    progressLots.value = []
    progressLotDaily.value = {}
    progressLotDailySource.value = {}
    return
  }
  loadingProgress.value = true
  try {
    const res = await fetchProductionProgress(selectedLineId.value)
    progressLots.value = res.lots ?? []
    progressLotDaily.value = res.lot_daily ?? {}
    progressLotDailySource.value = res.lot_daily_source ?? {}
  } catch {
    progressLots.value = []
    progressLotDaily.value = {}
    progressLotDailySource.value = {}
  } finally {
    loadingProgress.value = false
  }
}

function progressStatusLabel(s: string): string {
  const m: Record<string, string> = {
    PLANNED: '計画中',
    RELEASED: '指示済',
    IN_PROGRESS: '生産中',
    COMPLETED: '完了',
  }
  return m[s] ?? s
}
function progressStatusType(s: string): 'info' | 'warning' | 'primary' | 'success' {
  if (s === 'COMPLETED') return 'success'
  if (s === 'IN_PROGRESS') return 'primary'
  if (s === 'RELEASED') return 'warning'
  return 'info'
}
function progressCellClass(lot: ProgressLotItem, d: string): Record<string, boolean> {
  const key = `${lot.aps_schedule_id}_${lot.lot_number}`
  const qty = (progressLotDaily.value[key] || {})[d] || 0
  const src = (progressLotDailySource.value[key] || {})[d] || 'PLANNED'
  const base: Record<string, boolean> = { 'gantt-active': qty > 0 }
  if (qty <= 0) return base
  if (src === 'ACTUAL') {
    base['pgs-src-actual'] = true
    return base
  }
  if (src === 'WAIT_UPSTREAM') {
    base['pgs-src-wait-upstream'] = true
    return base
  }
  base[`pgs-${lot.progress_status.toLowerCase()}`] = true
  return base
}
function formatPrediction(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.replace('T', ' ').slice(0, 16)
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)
}

/** cutting_management の実績/計画（成型の日別セル・在庫ログ実績とは別） */
function cuttingProgressDisplay(lot: ProgressLotItem): string {
  if (lot.progress_status !== 'IN_PROGRESS') return '—'
  const p = lot.cutting_planned_qty
  const a = lot.cutting_actual_qty
  if (p == null && a == null) return '—'
  const pn = Number(p ?? 0)
  const an = Number(a ?? 0)
  return `${an.toLocaleString()}/${pn.toLocaleString()}`
}

/** 成型ロットの有効計画本数（API 未対応時は 計画−上流不良） */
function formingEffectiveDisplay(lot: ProgressLotItem): number {
  if (lot.forming_effective_planned_qty != null && lot.forming_effective_planned_qty !== undefined) {
    return Math.max(0, Number(lot.forming_effective_planned_qty))
  }
  const pq = Number(lot.planned_quantity ?? 0)
  const u = Number(lot.upstream_defect_qty ?? 0)
  return Math.max(0, pq - u)
}

function progressPlannedCellTitle(lot: ProgressLotItem): string {
  const u = Number(lot.upstream_defect_qty ?? 0)
  const eff = formingEffectiveDisplay(lot)
  const base = `計画一覧: ${(lot.planned_quantity ?? 0).toLocaleString()} 本`
  if (u <= 0) return `${base}。上流不良なし。成型有効 ${eff.toLocaleString()} 本`
  return `${base}。切断+面取の上流不良 ${u.toLocaleString()} 本。成型有効 ${eff.toLocaleString()} 本（management_code 一致で集計）`
}

function statusType(s: string): 'success' | 'warning' | 'info' {
  if (s === 'COMPLETED') return 'success'
  if (s === 'IN_PROGRESS') return 'warning'
  return 'info'
}

/** 一覧の状態表示（API の英語コード → 日本語） */
function statusLabelJa(s: string): string {
  const map: Record<string, string> = {
    PLANNING: '計画中',
    IN_PROGRESS: '進行中',
    COMPLETED: '完了',
  }
  return map[s] ?? s
}

function isWeekend(d: string): boolean {
  const day = weekdayIndexForIsoDate(d)
  return day === 0 || day === 6
}

function isToday(d: string): boolean {
  return d === formatYmdInJapan(new Date())
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[weekdayIndexForIsoDate(d)]
}

function ganttCellClass(row: ScheduleGridRow, d: string): Record<string, boolean> {
  const qty = row.daily[d] || 0
  const actual = row.actual_daily?.[d] || 0
  const defect = row.defect_daily?.[d] || 0
  const upstream = row.upstream_defect_daily?.[d] || 0
  const remain = row.remaining_daily?.[d] || 0
  const active = qty !== 0 || actual !== 0 || defect !== 0 || upstream !== 0 || remain !== 0
  const inRange = row.start_date && row.end_date && d >= row.start_date && d <= row.end_date
  return {
    'gantt-active': active,
    'gantt-has-actual': actual > 0,
    'gantt-has-defect': defect !== 0,
    'gantt-range': !!inRange && !active,
    'is-weekend': isWeekend(d),
    'is-today': isToday(d),
  }
}

function productPaletteClass(row: ScheduleGridRow): string {
  const base = (row.item_name || '').trim()
  return productPaletteClassByName(base)
}

function productPaletteClassByName(name: string): string {
  const base = (name || '').trim()
  if (!base) return 'gpc-0'
  let h = 0
  for (let i = 0; i < base.length; i += 1) {
    h = ((h << 5) - h + base.charCodeAt(i)) | 0
  }
  return `gpc-${Math.abs(h) % 10}`
}

function ganttCellTitle(row: ScheduleGridRow, d: string): string {
  const planned = row.daily[d] || 0
  const actual = row.actual_daily?.[d] || 0
  const defect = row.defect_daily?.[d] || 0
  const upstream = row.upstream_defect_daily?.[d] || 0
  const remain = row.remaining_daily?.[d] || 0
  if (planned !== 0 || actual !== 0 || defect !== 0 || upstream !== 0 || remain !== 0) {
    return `${row.item_name}: 計画 ${planned} / 実績(良) ${actual} / 不良 ${defect} / 前工程不良 ${upstream} / 残 ${remain}`
  }
  return ''
}
</script>

<style scoped>
/* ══════════════════════════════════════════════════
   Design Tokens
   ══════════════════════════════════════════════════ */
.planning-page {
  /* UI フォント（日本語可読性優先：Windows / macOS ともにクリアなサンセリフ） */
  --font-sans: YuGothic,system-ui, -apple-system, "Segoe UI", "Yu Gothic UI", YuGothic,
    "Meiryo", "Hiragino Sans", Arial, sans-serif;
  --font-mono: Consolas, "Courier New", monospace;
  /* colors */
  --c-bg:        #f1f5f9;
  --c-surface:   #ffffff;
  --c-border:    #dbe3ee;
  --c-border-l:  #e9eef6;
  --c-text-h:    #0f172a;
  --c-text:      #334155;
  --c-text-m:    #475569;
  --c-text-s:    #64748b;
  --c-accent:    #3b82f6;
  --c-success:   #10b981;
  --c-warn:      #f59e0b;
  --c-danger:    #ef4444;
  /* typography */
  --fs-xs:  10.5px;
  --fs-s:   11.5px;
  --fs-base: 13px;
  --fs-m:   14px;
  --fs-lg:  18px;
  /* controls */
  --ctrl-h:  28px;
  --ctrl-fs: 13px;
  --ctrl-px: 10px;
  --ctrl-r:  5px;
  /* spacing */
  --gap-xs:  4px;
  --gap-s:   8px;
  --gap:    12px;
  --gap-l:  16px;
  /* card */
  --card-r:  12px;
  --card-p: 10px 12px;
  --card-sh: 0 2px 8px rgba(15,23,42,.05), 0 8px 20px rgba(15,23,42,.04);
}

/* ══════════════════════════════════════════════════
   Page Shell
   ══════════════════════════════════════════════════ */
.planning-page {
  padding: 10px 14px;
  background:
    radial-gradient(circle at 12% -20%, #e0ecff 0%, transparent 30%),
    radial-gradient(circle at 85% -25%, #dff7ef 0%, transparent 26%),
    var(--c-bg);
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: var(--font-sans);
  font-size: var(--fs-base);
  font-weight: 400;
  line-height: 1.5;
  color: var(--c-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
.planning-page :deep(.el-table),
.planning-page :deep(.el-form-item__label),
.planning-page :deep(.el-button),
.planning-page :deep(.el-input__inner),
.planning-page :deep(.el-select__selected-item),
.planning-page :deep(.el-radio-button__inner),
.planning-page :deep(.el-tabs__item),
.planning-page :deep(.el-tag) {
  font-family: inherit;
}

/* ══════════════════════════════════════════════════
   Page Header
   ══════════════════════════════════════════════════ */
.plan-hd {
  display: flex;
  align-items: center;
  gap: var(--gap);
  padding: 0 2px 2px;
}
.plan-hd-title {
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--c-text-h);
  margin: 0;
  letter-spacing: 0.02em;
  line-height: 1.35;
  flex-shrink: 0;
}
.plan-hd-sub {
  font-size: var(--fs-s);
  color: var(--c-text-m);
  margin: 0;
  line-height: 1.45;
}

/* ══════════════════════════════════════════════════
   Cards
   ══════════════════════════════════════════════════ */
.plan-card {
  background: var(--c-surface);
  border-radius: var(--card-r);
  padding: var(--card-p);
  box-shadow: var(--card-sh);
  border: 1px solid var(--c-border-l);
  backdrop-filter: saturate(115%) blur(2px);
}

/* ══════════════════════════════════════════════════
   Section Heading
   ══════════════════════════════════════════════════ */
.plan-sec-hd {
  font-size: var(--fs-m);
  font-weight: 700;
  color: var(--c-text-h);
  margin: 0 0 6px;
  padding-left: 8px;
  border-left: 3px solid var(--c-accent);
  display: flex;
  align-items: center;
  gap: var(--gap-s);
  line-height: 1.45;
  letter-spacing: 0.01em;
}
.plan-sec-badge {
  font-size: var(--fs-xs);
  font-weight: 600;
  background: var(--c-accent);
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 17px;
}
.plan-sec-sub {
  font-size: var(--fs-xs);
  color: var(--c-text-s);
  font-weight: 400;
  margin-left: auto;
}
/* 計画一覧：タイトル行に再計算ボタン（右側） */
.plan-sec-hd--schedule {
  flex-wrap: nowrap;
  align-items: center;
  gap: var(--gap-s);
}
.plan-sec-hd-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--gap-s);
  min-width: 0;
  flex: 1;
}
.plan-sec-hd--schedule .plan-sec-sub {
  margin-left: 0;
}
.schedule-replan-btn {
  flex-shrink: 0;
  align-self: center;
}
.schedule-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.schedule-completed-switch {
  margin-right: 4px;
}
.schedule-section .schedule-replan-btn {
  height: var(--ctrl-h);
  min-height: var(--ctrl-h);
  padding: 0 12px;
  font-size: var(--fs-base);
  font-weight: 600;
  border-radius: var(--ctrl-r);
}
.schedule-section .schedule-replan-btn :deep(.el-loading-spinner) {
  width: 14px;
  height: 14px;
}

/* ══════════════════════════════════════════════════
   Setup Bar（基準開始月・工程・ライン）— 計画追加と同一の高さ・字サイズ
   ══════════════════════════════════════════════════ */
.setup-bar :deep(.el-form--inline) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  column-gap: var(--gap-s);
  row-gap: 4px;
}
.setup-bar :deep(.el-form--inline .el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}
.setup-bar :deep(.el-form-item__label) {
  display: inline-flex;
  align-items: center;
  height: var(--add-h);
  line-height: var(--add-h);
  font-size: var(--add-fs);
  color: var(--c-text-m);
  padding-right: 5px;
}
.setup-bar :deep(.el-form-item__content) {
  display: inline-flex;
  align-items: center;
  min-height: var(--add-h);
  line-height: var(--add-h);
}
.setup-fi-btn :deep(.el-button) {
  height: var(--add-h);
  min-height: var(--add-h);
  padding: 0 14px;
  font-size: var(--add-fs);
  border-radius: var(--ctrl-r);
}
.setup-section .ee-empty-hint {
  margin: 6px 0 0;
}

/* ══════════════════════════════════════════════════
   Add Section
   ══════════════════════════════════════════════════ */
.plan-card.add-section,
.plan-card.setup-section {
  padding: 8px 10px;
  /* 計画追加・検索条件で共通のコントロール寸法 */
  --add-h:  var(--ctrl-h);
  --add-fs: var(--fs-base);
}
.add-section-hd {
  margin-bottom: 8px !important;
  padding-left: 8px !important;
  font-size: var(--fs-base) !important;
}

/* ── block layout ── */
.add-plan-block { display: flex; flex-direction: column; gap: 6px; }

/* ── row 1: product + stats chip ── */
.add-row--top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
}

/* ── form wrapper ── */
.add-form {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0;
}

/* ── every form-item: inline-flex, vertically centered ── */
.add-form :deep(.el-form-item) {
  display: inline-flex;
  align-items: center;
  margin-bottom: 0;
  margin-right: 10px;
  vertical-align: middle;
}
.add-form :deep(.el-form-item):last-child { margin-right: 0; }

/* ── labels ── */
.add-form :deep(.el-form-item__label) {
  display: inline-flex;
  align-items: center;
  height: var(--add-h);
  line-height: var(--add-h);
  padding-right: 5px;
  font-size: var(--add-fs);
  color: var(--c-text-m);
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── content wrapper ── */
.add-form :deep(.el-form-item__content) {
  display: inline-flex;
  align-items: center;
  min-height: var(--add-h);
  line-height: var(--add-h);
}

/* ── input / select height & font ── */
.plan-card.add-section :deep(.el-input__wrapper),
.plan-card.add-section :deep(.el-select__wrapper),
.plan-card.setup-section :deep(.el-input__wrapper),
.plan-card.setup-section :deep(.el-select__wrapper) {
  height: var(--add-h);
  min-height: var(--add-h);
  box-shadow: 0 0 0 1px var(--c-border) inset;
  border-radius: var(--ctrl-r);
  padding: 0 var(--ctrl-px);
  transition: box-shadow .15s;
}
.plan-card.add-section :deep(.el-input__wrapper:hover),
.plan-card.add-section :deep(.el-select__wrapper:hover),
.plan-card.setup-section :deep(.el-input__wrapper:hover),
.plan-card.setup-section :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}
.plan-card.add-section :deep(.el-input__wrapper.is-focus),
.plan-card.add-section :deep(.el-select__wrapper.is-focus),
.plan-card.setup-section :deep(.el-input__wrapper.is-focus),
.plan-card.setup-section :deep(.el-select__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--c-accent) inset;
}
.plan-card.add-section :deep(.el-input__inner),
.plan-card.add-section :deep(.el-select__selected-item),
.plan-card.add-section :deep(.el-select__placeholder),
.plan-card.setup-section :deep(.el-input__inner),
.plan-card.setup-section :deep(.el-select__selected-item),
.plan-card.setup-section :deep(.el-select__placeholder) {
  font-size: var(--add-fs);
  height: var(--add-h);
  line-height: var(--add-h);
}

/* ── radio-button group ── */
.add-section :deep(.el-radio-group) {
  display: inline-flex;
  align-items: center;
  height: var(--add-h);
}
.add-section :deep(.el-radio-button__inner) {
  height: var(--add-h);
  min-height: var(--add-h);
  line-height: calc(var(--add-h) - 2px);
  padding: 0 10px;
  font-size: var(--add-fs);
  border-radius: 0;
}
.add-section :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: var(--ctrl-r) 0 0 var(--ctrl-r);
}
.add-section :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 var(--ctrl-r) var(--ctrl-r) 0;
}

/* ── 追加 button ── */
.add-fi-btn :deep(.el-button) {
  height: var(--add-h);
  min-height: var(--add-h);
  padding: 0 14px;
  font-size: var(--add-fs);
  border-radius: var(--ctrl-r);
}

/* ── widths ── */
.add-select-product { width: 210px; }
.add-select-merge   { width: min(100%, 300px); }
.add-input-qty      { width: 82px; }
.add-fi-merge       { flex: 1 1 auto; }

/* 既存に合算：合算先・数量・追加を 1 かたまりにし、合算先の右隣に配置（親 flex の行末まで伸ばさない） */
.add-merge-qty-group {
  display: contents;
}
.add-section .add-fi-merge--inline,
.add-section .add-fi-qty--inline,
.add-section .add-fi-btn--inline {
  flex: 0 0 auto;
  align-items: flex-start;
}
.add-select-merge--inline {
  width: 240px;
  min-width: 180px;
  max-width: min(320px, 42vw);
}

/* ── 追加ボタン直後の本数プレビュー ── */
.add-btn-hint-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.add-qty-hint {
  font-size: var(--fs-xs);
  line-height: 1.35;
  color: var(--c-text-m);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  max-width: min(480px, 58vw);
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── merge row ── */
.add-merge-row {
  display: inline-flex;
  align-items: center;
  gap: var(--gap-xs) var(--gap-s);
}
.add-merge-hint {
  font-size: var(--fs-xs);
  color: var(--c-text-s);
  white-space: nowrap;
}

/* ── stats chip bar ── */
.ee-stats-chip {
  display: inline-flex;
  flex-wrap: nowrap;
  align-items: center;
  height: var(--add-h);
  padding: 0 10px 0 12px;
  background: linear-gradient(90deg, #f8fafc 0%, #eff6ff 100%);
  border-radius: var(--ctrl-r);
  border: 1px solid #dde3f0;
  gap: 0;
  flex: 1 1 auto;
  min-width: 0;
}
.ee-stat-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-size: var(--fs-xs);
  padding: 0 10px 0 0;
  margin-right: 8px;
  border-right: 1px solid #e4e9f0;
  line-height: 1.35;
  white-space: nowrap;
}
.ee-stat-chip:last-child { border-right: none; margin-right: 0; padding-right: 0; }
.ee-stat-label    { color: var(--c-text-m); font-size: var(--fs-xs); }
.ee-readonly      { font-weight: 600; color: var(--c-text-h); font-variant-numeric: tabular-nums; font-size: var(--fs-xs); }
.ee-readonly-unit { color: var(--c-text-s); font-size: var(--fs-xs); }

.ee-empty-hint   { margin: 4px 0 0; font-size: var(--fs-base); color: #e6a23c; }
.add-empty-hint  { margin-top: 6px; margin-bottom: 0; }

/* ── Modern button hierarchy ── */
.planning-page :deep(.el-button) {
  border-radius: 8px;
  font-weight: 600;
  transition: transform .12s ease, box-shadow .18s ease, filter .18s ease;
}
.planning-page :deep(.el-button:not(.is-disabled):hover) {
  transform: translateY(-1px);
}

.btn-accent:deep(.el-button),
.btn-accent {
  border: none !important;
  color: #fff !important;
  box-shadow: 0 6px 14px rgba(30, 64, 175, .16);
}
.btn-accent--primary:deep(.el-button),
.btn-accent--primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
}
.btn-accent--success:deep(.el-button),
.btn-accent--success {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
  box-shadow: 0 6px 14px rgba(21, 128, 61, .18);
}
.btn-accent--warning:deep(.el-button),
.btn-accent--warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
  box-shadow: 0 6px 14px rgba(180, 83, 9, .18);
}

.btn-soft:deep(.el-button),
.btn-soft {
  border: 1px solid #d5deeb !important;
  background: #f8fafc !important;
}
.btn-soft--indigo:deep(.el-button),
.btn-soft--indigo {
  color: #334155 !important;
}
.btn-soft--gray:deep(.el-button),
.btn-soft--gray {
  color: #475569 !important;
}

/* ══════════════════════════════════════════════════
   Schedule List
   ══════════════════════════════════════════════════ */
.schedule-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 84px;
}
.schedule-table { width: 100%; }
.schedule-table :deep(.el-table__header th) {
  padding: 5px 6px;
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--c-text-m);
  background: #f7f8fa;
}
.schedule-table :deep(.el-table__cell) { padding: 4px 6px; }
.schedule-table :deep(.el-table__body-wrapper tbody td) { height: 36px; }
.schedule-table :deep(.el-table__body .cell) {
  line-height: 1.45;
  font-variant-numeric: tabular-nums;
}
.schedule-table :deep(.el-table__body-wrapper tbody tr:hover td) {
  background: #f0f6ff !important;
}
.schedule-table-draggable :deep(.el-table__body-wrapper tbody tr) { cursor: grab; }
.schedule-table-draggable :deep(.el-table__body-wrapper tbody tr:active) { cursor: grabbing; }
.schedule-sortable-ghost { opacity: .4; background: #e8f3ff !important; }
.schedule-sortable-drag  { opacity: .97; }
.schedule-order-head { cursor: help; }
.schedule-drag-hint  { font-size: var(--fs-base); font-weight: 700; color: var(--c-text-h); }
.order-num           { font-size: var(--fs-base); font-weight: 700; color: var(--c-text-h); }

/* ── 進捗列（計画一覧） ── */
.schedule-progress-cell { display: flex; flex-wrap: wrap; gap: 2px; justify-content: center; align-items: center; }
.schedule-progress-tag  { font-size: 10px !important; padding: 0 5px !important; height: 18px !important; line-height: 18px !important; }
.schedule-progress-none { color: var(--c-text-s); font-size: var(--fs-s); }

/* ── 合計(本) inline-edit ── */
.total-qty-cell {
  font-size: var(--fs-base);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--c-text-h);
}
.total-qty-editable {
  display: inline-block;
  min-width: 3.5em;
  padding: 1px 5px;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  transition: background .15s, color .15s;
}
.total-qty-editable:hover {
  background: #eef4ff;
  color: var(--c-accent);
}
.total-qty-edit-wrap { display: flex; justify-content: flex-end; width: 100%; }
.total-qty-input { width: 90px; }
.total-qty-input :deep(.el-input__inner) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: var(--fs-base);
}

/* ══════════════════════════════════════════════════
   Gantt Section
   ══════════════════════════════════════════════════ */
.gantt-tabs :deep(.el-tabs__content)  { padding: 0; }
.gantt-tabs :deep(.el-tabs__header)   { margin-bottom: 10px; }
.gantt-tabs :deep(.el-tabs__item) {
  font-size: var(--fs-base);
  font-weight: 700;
  height: 36px;
  line-height: 36px;
  letter-spacing: 0.02em;
  transition: color .2s;
}
.gantt-tabs :deep(.el-tabs__active-bar) { height: 3px; border-radius: 2px; }
.gantt-hourly-placeholder {
  min-height: 128px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hourly-hint {
  max-width: 460px;
  font-size: var(--fs-base);
  color: var(--c-text-m);
  line-height: 1.6;
  margin: 0 auto;
  text-align: center;
}

/* ── Gantt Table ── */
.gantt-scroll {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--c-border-l);
}
.gantt-scroll::-webkit-scrollbar { height: 7px; }
.gantt-scroll::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 4px; }
.gantt-scroll::-webkit-scrollbar-thumb { background: #c1c9d4; border-radius: 4px; }
.gantt-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.gantt-table {
  border-collapse: collapse;
  font-size: var(--fs-base);
  font-family: var(--font-sans);
  white-space: nowrap;
  -webkit-font-smoothing: antialiased;
}
.gantt-table th,
.gantt-table td {
  border: 1px solid #e8ecf2;
  padding: 0 5px;
  text-align: center;
  height: 30px;
  vertical-align: middle;
}
.gantt-table thead th {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  font-weight: 700;
  color: var(--c-text-m);
  font-size: var(--fs-s);
  letter-spacing: 0.02em;
  border-bottom: 2px solid #d4dae5;
}
.gantt-table tbody tr { transition: background .12s ease; }
.gantt-table tbody tr:hover td:not(.gantt-active):not(.gantt-has-actual) {
  background: #f8fafd;
}

/* ── Sticky Columns ── */
.gantt-sticky {
  position: sticky;
  background: #fbfcfe;
  background-color: #fbfcfe !important;
  z-index: 100;
  text-align: left;
  border-right: 0 !important;
  box-sizing: border-box;
  background-clip: padding-box;
  overflow: hidden;
  box-shadow: inset -1px 0 0 #e2e6ed, 2px 0 0 #fbfcfe;
}
.gantt-table thead .gantt-sticky {
  background: #e8edf5 !important;
  background-color: #e8edf5 !important;
  z-index: 110;
  border-right: 0 !important;
  box-shadow: inset -1px 0 0 #d4dae5, 2px 0 0 #e8edf5;
}
.gantt-sticky-line {
  left: 0; width: 80px; min-width: 80px; max-width: 80px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-weight: 600; color: var(--c-text-m); font-size: var(--fs-s);
}
.gantt-line-dbl {
  cursor: pointer;
  user-select: none;
}
.gantt-table tbody .gantt-line-dbl:hover,
.gantt-table thead .gantt-line-dbl:hover {
  background-color: rgba(64, 158, 255, 0.1) !important;
}
.plan-line-anchor-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.plan-line-anchor-dialog :deep(.el-dialog__body) {
  padding: 0 20px 16px;
}
.plan-line-anchor-dialog :deep(.el-dialog__footer) {
  padding: 12px 20px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.line-anchor-dlg-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  text-align: left;
}
.line-anchor-dlg-header-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, rgba(64, 158, 255, 0.18), rgba(64, 158, 255, 0.06));
  color: var(--el-color-primary);
}
.line-anchor-dlg-header-text {
  min-width: 0;
  flex: 1;
}
.line-anchor-dlg-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  letter-spacing: 0.02em;
  line-height: 1.35;
}
.line-anchor-dlg-meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}
.line-anchor-dlg-tag {
  font-weight: 500;
}
.line-anchor-dlg-meta-note {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.line-anchor-dlg-inner {
  padding-top: 16px;
}
.line-anchor-dlg-hint-card {
  margin-bottom: 14px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
.line-anchor-dlg-hint-card strong {
  color: var(--el-color-primary);
  font-weight: 600;
}
.line-anchor-dlg-table {
  border-radius: 8px;
  overflow: hidden;
}
.line-anchor-dlg-table :deep(.el-table__header th) {
  font-weight: 600;
  background: var(--el-fill-color-light) !important;
}
.line-anchor-dlg-picker {
  width: 100%;
  max-width: 200px;
}
.line-anchor-dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;
}
.plan-line-capacity-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 14px;
  max-height: calc(100vh - 130px);
  overflow-y: auto;
}
.gantt-sticky-order {
  left: 80px; width: 44px; min-width: 44px; max-width: 44px; text-align: center;
  color: var(--c-text-s); font-size: var(--fs-s);
}
.gantt-sticky-name {
  left: 124px; width: 132px; min-width: 132px; max-width: 132px;
  text-align: left; padding-left: 8px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.gantt-sticky-eff {
  left: 256px; width: 70px; min-width: 70px; max-width: 70px;
  text-align: right; font-variant-numeric: tabular-nums;
  font-weight: 600; font-size: var(--fs-s);
  font-family: var(--font-mono); color: var(--c-text-m);
}
.gantt-sticky-planned {
  left: 326px; width: 56px; min-width: 56px; max-width: 56px;
  text-align: right; font-variant-numeric: tabular-nums;
  font-weight: 600; font-size: var(--fs-s);
  font-family: var(--font-mono); color: var(--c-text-h);
}
.gantt-sticky-actual {
  left: 382px; width: 72px; min-width: 72px; max-width: 72px;
  text-align: right; font-variant-numeric: tabular-nums;
  font-weight: 700; font-size: var(--fs-s);
  font-family: var(--font-mono); color: #0f766e;
  box-shadow: inset -1px 0 0 #d4dae5;
}
.gantt-sticky-defect {
  left: 454px; width: 64px; min-width: 64px; max-width: 64px;
  text-align: right; font-variant-numeric: tabular-nums;
  font-weight: 700; font-size: var(--fs-s);
  font-family: var(--font-mono); color: #b45309;
  box-shadow: inset -1px 0 0 #d4dae5, 3px 0 6px rgba(0,21,41,.06);
}
.gantt-sticky-upstream {
  left: 518px; width: 86px; min-width: 86px; max-width: 86px;
  text-align: right; font-variant-numeric: tabular-nums;
  font-weight: 700; font-size: var(--fs-s);
  font-family: var(--font-mono); color: #6d28d9;
  box-shadow: inset -1px 0 0 #d4dae5, 3px 0 6px rgba(0,21,41,.06);
}
.gantt-table thead .gantt-sticky-actual {
  box-shadow: inset -1px 0 0 #c9d1de;
}
.gantt-table thead .gantt-sticky-defect {
  box-shadow: inset -1px 0 0 #c9d1de, 3px 0 6px rgba(0,21,41,.06);
}
.gantt-table thead .gantt-sticky-upstream {
  box-shadow: inset -1px 0 0 #c9d1de, 3px 0 6px rgba(0,21,41,.06);
}
.gantt-name {
  font-weight: 700; color: var(--c-text-h);
  letter-spacing: 0.01em; font-size: var(--fs-s);
}

/* ── Date Columns ── */
.gantt-date-col { min-width: 44px; padding: 4px 2px 3px !important; }
.gantt-date-text {
  font-size: var(--fs-s); font-weight: 700;
  font-family: var(--font-mono); letter-spacing: -0.02em;
  color: var(--c-text-m);
}
.gantt-wd-text {
  font-size: 9.5px; color: var(--c-text-s); margin-top: 1px;
  font-weight: 600; letter-spacing: 0.04em;
}
.gantt-date-col.is-weekend .gantt-date-text,
.gantt-date-col.is-weekend .gantt-wd-text { color: #dc2626; font-weight: 800; }
.gantt-date-col.is-weekend { background: transparent; }
.gantt-date-col.is-today {
  background: linear-gradient(180deg, #fefce8 0%, #fef3c7 100%);
  border-bottom: 2px solid #f59e0b !important;
}

/* ── Data Cells ── */
.gantt-cell {
  min-width: 44px; height: 38px;
  transition: background .12s ease, box-shadow .12s ease;
}
.gantt-qty {
  font-size: var(--fs-s); font-weight: 700; line-height: 1;
  font-variant-numeric: tabular-nums; font-family: var(--font-mono);
}
.gantt-table tbody td.gantt-cell {
  text-align: left;
  padding-left: 4px;
}
.gantt-layered {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 1px;
  line-height: 1;
  padding: 2px 0;
}
.gantt-layer {
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  letter-spacing: -0.01em;
}
.gantt-layer--plan {
  color: rgba(255, 255, 255, 0.97);
  font-weight: 800;
  font-size: 10.5px;
}
.gantt-layer--actual {
  color: rgba(255, 255, 255, 0.82);
  font-size: 9.5px;
  font-weight: 600;
}
.gantt-layer--defect {
  color: rgba(254, 243, 199, 0.98);
  font-size: 9.5px;
  font-weight: 600;
}
.gantt-layer--upstream {
  color: rgba(233, 213, 255, 0.98);
  font-size: 9.5px;
  font-weight: 600;
}
.gantt-layer--remain {
  color: rgba(255, 255, 255, 0.92);
  font-size: 9.5px;
  font-weight: 600;
}
.gl-lbl {
  font-weight: 500; opacity: .7;
  margin-right: 1px; font-size: 9px;
  font-family: var(--font-sans);
}
.gantt-cell.is-weekend:not(.gantt-active) { background: transparent; }
.gantt-cell.is-today:not(.gantt-active):not(.gantt-has-actual):not(.gantt-has-defect) {
  background: #fefce8; box-shadow: none;
}
.gantt-cell.gantt-range { background: #f0f5ff; }
.gantt-cell.gantt-active {
  box-shadow: inset 0 1px 0 rgba(255,255,255,.15), inset 0 -1px 0 rgba(0,0,0,.08);
}

/* ── Hourly Columns ── */
.gantt-hour-col {
  min-width: 54px; vertical-align: bottom; padding: 4px 2px 3px !important;
}
.gantt-hour-date {
  font-size: var(--fs-xs); color: var(--c-text-m); font-weight: 700;
  font-family: var(--font-mono); letter-spacing: -0.02em;
}
.gantt-hour-range {
  font-size: 9.5px; color: var(--c-text-s); font-weight: 600;
  font-family: var(--font-mono);
}
.gantt-hour-cell { min-width: 54px; }
.gantt-hour-col.is-today {
  background: linear-gradient(180deg, #fefce8 0%, #fef3c7 100%);
  border-bottom: 2px solid #f59e0b !important;
}

/* ─── Per-Row Color Palette (10 colors, used in progress Gantt) ─── */
.gantt-rc-0 td.gantt-active { background: #3b82f6; color: #fff; }
.gantt-rc-0 td.gantt-range  { background: #eff6ff; }
.gantt-rc-1 td.gantt-active { background: #10b981; color: #fff; }
.gantt-rc-1 td.gantt-range  { background: #ecfdf5; }
.gantt-rc-2 td.gantt-active { background: #8b5cf6; color: #fff; }
.gantt-rc-2 td.gantt-range  { background: #f5f3ff; }
.gantt-rc-3 td.gantt-active { background: #f59e0b; color: #fff; }
.gantt-rc-3 td.gantt-range  { background: #fffbeb; }
.gantt-rc-4 td.gantt-active { background: #ec4899; color: #fff; }
.gantt-rc-4 td.gantt-range  { background: #fdf2f8; }
.gantt-rc-5 td.gantt-active { background: #0ea5e9; color: #fff; }
.gantt-rc-5 td.gantt-range  { background: #f0f9ff; }
.gantt-rc-6 td.gantt-active { background: #f43f5e; color: #fff; }
.gantt-rc-6 td.gantt-range  { background: #fff1f2; }
.gantt-rc-7 td.gantt-active { background: #84cc16; color: #fff; }
.gantt-rc-7 td.gantt-range  { background: #f7fee7; }
.gantt-rc-8 td.gantt-active { background: #6366f1; color: #fff; }
.gantt-rc-8 td.gantt-range  { background: #eef2ff; }
.gantt-rc-9 td.gantt-active { background: #14b8a6; color: #fff; }
.gantt-rc-9 td.gantt-range  { background: #f0fdfa; }

/* 状态图例 + 表示期间 */
.gantt-status-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px 16px;
  margin: 0 0 8px;
  padding: 5px 8px;
  font-size: var(--fs-s);
  color: var(--c-text-m);
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #edf0f5;
}
.legend-item {
  display: inline-flex; align-items: center; gap: 5px;
  white-space: nowrap; font-weight: 500;
}
.gantt-range-wrap {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.gantt-range-label {
  font-size: var(--fs-xs);
  color: var(--c-text-m);
  white-space: nowrap;
  font-weight: 600;
}
.gantt-range-picker { width: 240px; }
.gantt-range-picker :deep(.el-input__wrapper) {
  min-height: 24px; height: 24px;
  font-size: var(--fs-s);
  padding-top: 0; padding-bottom: 0;
  border-radius: 5px;
}
.gantt-range-picker :deep(.el-range-input) {
  font-size: var(--fs-s); font-family: var(--font-mono);
}
.gantt-range-picker :deep(.el-range-separator) { font-size: var(--fs-xs); }
.legend-dot {
  width: 10px; height: 10px; border-radius: 3px;
  display: inline-block; box-shadow: 0 1px 2px rgba(0,0,0,.12);
}
.legend-dot--planned { background: linear-gradient(135deg, #94a3b8, #64748b); }
.legend-dot--released { background: linear-gradient(135deg, #fbbf24, #d97706); }
.legend-dot--in-progress { background: linear-gradient(135deg, #60a5fa, #2563eb); }
.legend-dot--completed { background: linear-gradient(135deg, #34d399, #059669); }
.legend-dot--actual { background: linear-gradient(135deg, #0f766e, #115e59); }
.legend-dot--wait-upstream { background: linear-gradient(135deg, #a78bfa, #7c3aed); }

.gantt-row.grs-planned td.gantt-active { background: linear-gradient(135deg, #94a3b8, #64748b) !important; color: #fff; }
.gantt-row.grs-released td.gantt-active { background: linear-gradient(135deg, #fbbf24, #d97706) !important; color: #fff; }
.gantt-row.grs-in_progress td.gantt-active { background: linear-gradient(135deg, #60a5fa, #2563eb) !important; color: #fff; }
.gantt-row.grs-completed td.gantt-active { background: linear-gradient(135deg, #34d399, #059669) !important; color: #fff; }

/* 日別 / 時間別 甘特：按产品着色（同产品稳定同色・10色） */
.gantt-row.gpc-0 td.gantt-active { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: #fff; }
.gantt-row.gpc-1 td.gantt-active { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #fff; }
.gantt-row.gpc-2 td.gantt-active { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: #fff; }
.gantt-row.gpc-3 td.gantt-active { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: #fff; }
.gantt-row.gpc-4 td.gantt-active { background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); color: #fff; }
.gantt-row.gpc-5 td.gantt-active { background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); color: #fff; }
.gantt-row.gpc-6 td.gantt-active { background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%); color: #fff; }
.gantt-row.gpc-7 td.gantt-active { background: linear-gradient(135deg, #84cc16 0%, #65a30d 100%); color: #fff; }
.gantt-row.gpc-8 td.gantt-active { background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: #fff; }
.gantt-row.gpc-9 td.gantt-active { background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); color: #fff; }

/* 有实绩时统一用深青色覆盖 */
td.gantt-has-actual {
  background: linear-gradient(135deg, #0f766e 0%, #115e59 100%) !important;
  color: #fff !important;
}

/* ══════════════════════════════════════════════════
   Progress Gantt (生産進捗)
   ══════════════════════════════════════════════════ */
.pgs-th-status,
.pgs-th-prediction {
  position: sticky;
  z-index: 100;
  background: #e8edf5 !important;
  background-color: #e8edf5 !important;
  font-size: var(--fs-s);
  white-space: nowrap;
  font-weight: 700;
}
/* 生産進捗：計画数右端 382px の次に「切断」、その次ステータス・完了予測 */
.pgs-th-cutting {
  position: sticky;
  left: 382px;
  width: 88px; min-width: 88px; max-width: 88px;
  z-index: 100;
  background: #e8edf5 !important;
  font-size: var(--fs-s);
  white-space: nowrap;
  font-weight: 700;
  box-shadow: inset -1px 0 0 #d4dae5, 2px 0 0 #e8edf5;
}
.pgs-th-status     { left: 470px; width: 80px; min-width: 80px; max-width: 80px;
  box-shadow: inset -1px 0 0 #d4dae5, 2px 0 0 #e8edf5; }
.pgs-th-prediction { left: 550px; width: 110px; min-width: 110px; max-width: 110px;
  box-shadow: inset -1px 0 0 #d4dae5, 3px 0 6px rgba(0,21,41,.06); }
.pgs-cutting-cell {
  position: sticky;
  left: 382px;
  width: 88px; min-width: 88px; max-width: 88px;
  z-index: 100;
  background: #fbfcfe;
  background-color: #fbfcfe !important;
  box-shadow: inset -1px 0 0 #e2e6ed, 2px 0 0 #fbfcfe;
  text-align: center;
  vertical-align: middle;
  font-size: var(--fs-xs);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  color: var(--c-text-h);
}
.pgs-cutting-qty { display: block; line-height: 1.25; }
.pgs-cutting-done-tag { margin-top: 2px; transform: scale(0.92); transform-origin: center top; }
.pgs-status-cell {
  position: sticky;
  left: 470px; width: 80px; min-width: 80px; max-width: 80px;
  z-index: 100;
  background: #fbfcfe;
  background-color: #fbfcfe !important;
  box-shadow: inset -1px 0 0 #e2e6ed, 2px 0 0 #fbfcfe;
  text-align: center;
}
.pgs-prediction-cell {
  position: sticky;
  left: 550px; width: 110px; min-width: 110px; max-width: 110px;
  z-index: 100;
  background: #fbfcfe;
  background-color: #fbfcfe !important;
  box-shadow: inset -1px 0 0 #e2e6ed, 3px 0 6px rgba(0,21,41,.06);
  text-align: center;
  font-size: var(--fs-xs);
  color: var(--c-text-m);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
.pgs-footnote {
  margin: 10px 4px 0;
  font-size: var(--fs-xs);
  color: var(--c-text-s);
  line-height: 1.5;
  max-width: 920px;
}
.pgs-footnote strong { color: var(--c-text-m); font-weight: 600; }
.pgs-lot-num { font-weight: 700; text-align: center; font-family: var(--font-mono); }

.pgs-planned-cell {
  vertical-align: middle;
  line-height: 1.25;
}
.pgs-planned-main {
  display: block;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}
.pgs-eff-sub {
  display: block;
  margin-top: 2px;
  font-size: 10px;
  color: var(--c-text-s);
  font-weight: 500;
  white-space: nowrap;
}

/* 実績セル（成型 schedule_details.actual_qty／在庫ログ同期の成型実績） */
.gantt-progress-table td.pgs-src-actual.gantt-active {
  background: linear-gradient(135deg, #0f766e, #115e59) !important;
  color: #fff !important;
}
/* 上流待ち：未指示 or 工単欠料、いまは計画按分のみ */
.gantt-progress-table td.pgs-src-wait-upstream.gantt-active {
  background: linear-gradient(135deg, #a78bfa, #7c3aed) !important;
  color: #fff !important;
}
/* 成型計画のみ（指示済〜）— ロットステータス別 */
.gantt-progress-table td.pgs-planned.gantt-active   { background: linear-gradient(135deg, #94a3b8, #64748b) !important; color: #fff; }
.gantt-progress-table td.pgs-released.gantt-active   { background: linear-gradient(135deg, #fbbf24, #d97706) !important; color: #fff; }
.gantt-progress-table td.pgs-in_progress.gantt-active { background: linear-gradient(135deg, #60a5fa, #2563eb) !important; color: #fff; }
.gantt-progress-table td.pgs-completed.gantt-active   { background: linear-gradient(135deg, #34d399, #059669) !important; color: #fff; }
</style>
