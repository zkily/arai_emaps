<template>
  <div class="plating-planning-page">
    <header class="page-header">
      <h1 class="page-title">メッキ計画作成</h1>
      <nav class="page-flow" aria-label="作業手順">
        <span class="flow-i">① 在庫</span>
        <span class="flow-dot" />
        <span class="flow-i">② 下書き</span>
        <span class="flow-dot" />
        <span class="flow-i">③ 投入ボード</span>
      </nav>
    </header>

    <el-card shadow="never" class="pp-card pp-card--summary">
      <template #header>
        <div class="section-head-row">
          <span class="pp-card-title pp-card-title--summary">① メッキ前在庫／見込数量（基準日は各ペインで指定）</span>
        </div>
      </template>

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

    <el-card shadow="never" class="pp-card pp-card--draft">
      <template #header>
        <div class="section-head-row">
          <div class="draft-head-main">
            <span class="pp-card-title">② 下書き（ドラッグで登録）</span>
            <span class="draft-head-hint">ドラッグ＆ドロップで行を追加</span>
          </div>
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
            <el-button size="small" @click="openJigAvailabilityDialog">治具使用数設定</el-button>
          </div>
        </div>
      </template>
      <div class="draft-wrap">
        <div class="draft-toolbar" @dragover.prevent @drop.prevent="onDropToDraftTarget">
          <span class="draft-toolbar-title">下書き一覧</span>
          <span class="draft-toolbar-meta">{{ draftItems.length }} 件</span>
        </div>
        <div class="draft-stat-grid">
          <div class="draft-stat-card">
            <span class="draft-stat-label">行数</span>
            <span class="draft-stat-value">{{ draftStats.rowCount }}</span>
          </div>
          <div class="draft-stat-card">
            <span class="draft-stat-label">生産数合計</span>
            <span class="draft-stat-value">{{ draftStats.totalQty }}</span>
          </div>
          <div class="draft-stat-card">
            <span class="draft-stat-label">必要治具本数合計</span>
            <span class="draft-stat-value">{{ draftStats.totalSlots }}</span>
          </div>
        </div>
        <el-table
          ref="draftTableRef"
          :data="draftItems"
          :row-key="(row: DraftItem) => row.uid"
          border
          stripe
          size="small"
          :height="TABLE_H"
          empty-text="①の表から行をドラッグしてください"
          class="pp-table draft-target-table"
        >
          <el-table-column label="#" width="52" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column prop="work_date" label="作業日" width="108" align="center" />
          <el-table-column label="製品名" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="draft-row-drag-handle" :title="row.product_name">{{ row.product_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="plating_machine" label="メッキ治具" width="120" show-overflow-tooltip />
          <el-table-column prop="kake" label="掛け数" width="72" align="right" />
          <el-table-column label="生産数" width="108" align="right">
            <template #default="{ row }">
              <div class="qty-cell-edit">
                <el-input-number
                  v-if="editingQtyUid === row.uid"
                  v-model="editingQtyValue"
                  :min="0"
                  :step="1"
                  controls-position="right"
                  size="small"
                  @keydown.enter.prevent="commitQtyEdit(row.uid)"
                  @blur="commitQtyEdit(row.uid)"
                />
                <span v-else class="qty-readonly" @dblclick="startQtyEdit(row)">
                  {{ row.qty }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="" width="72" align="center" fixed="right">
            <template #default="{ row }">
              <el-button text type="danger" size="small" @click.stop="removeDraftItem(row.uid)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-dialog v-model="jigDialogVisible" title="メッキ治具の使用可能本数" width="680px" class="jig-dialog" destroy-on-close>
      <div class="jig-dialog-meta">
        <span class="jig-meta-pill">作業日：{{ draftWorkDate || '—' }}</span>
        <span class="jig-meta-pill">対象治具：{{ jigAvailabilityRows.length }} 件</span>
      </div>
      <el-table :data="jigAvailabilityRows" border stripe size="small" max-height="420" class="jig-edit-table">
        <el-table-column type="index" label="#" width="52" align="center" />
        <el-table-column prop="plating_machine" label="メッキ治具" min-width="200" show-overflow-tooltip />
        <el-table-column label="使用可能本数" width="180" align="right">
          <template #default="{ row, $index }">
            <el-input-number
              v-model="row.available_qty"
              :min="0"
              :step="1"
              controls-position="right"
              style="width: 130px"
              @keydown.enter.prevent="focusNextJigQtyInput($index)"
            />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="jigDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="savingJigAvailability" @click="saveJigAvailabilityForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="templateDialogVisible"
      title="標準レイアウト"
      width="400px"
      class="tpl-dialog"
      destroy-on-close
    >
      <p class="tpl-dialog-hint">空き枠の列数と段数のみ設定します。品番の割り当ては②の「計画に割当」で行います。</p>
      <div class="tpl-preview-row">
        <span class="tpl-preview-pill">1周 {{ tplFormJigsPerLap }} 本</span>
        <span class="tpl-preview-pill">最大 {{ tplFormMaxLaps }} 周</span>
      </div>
      <div class="tpl-compact-grid">
        <div class="tpl-field">
          <div class="tpl-field-label">1周あたりの治具本数（列数）</div>
          <el-input-number
            v-model="tplFormJigsPerLap"
            :min="1"
            :max="200"
            :step="1"
            controls-position="right"
            class="pp-input-num tpl-input-num"
          />
        </div>
        <div class="tpl-field">
          <div class="tpl-field-label">最大周数（ボード段数）</div>
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
      <template #footer>
        <el-button size="small" @click="templateDialogVisible = false">キャンセル</el-button>
        <el-button size="small" type="primary" @click="confirmStandardTemplate">確定</el-button>
      </template>
    </el-dialog>

    <el-card shadow="never" class="pp-card pp-card--board">
      <template #header>
        <div class="section-head-row">
          <span class="pp-card-title">③ メッキ投入スケジュールボード</span>
          <div class="toolbar-inline">
            <el-button type="primary" size="small" @click="openStandardTemplateDialog">
              標準レイアウト
            </el-button>
            <el-button type="success" size="small" :disabled="!layoutBoardReady || draftItems.length === 0" @click="mergeDraftIntoSchedule">
              計画に割当
            </el-button>
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

      <div v-if="layoutBoardReady" class="board-cond-banner">
        <span class="board-cond-label">レイアウト条件</span>
        <span class="board-cond-val">1周 <strong>{{ layoutJigsPerLap }}</strong> 本</span>
        <span class="board-cond-sep">／</span>
        <span class="board-cond-val">最大 <strong>{{ layoutMaxLaps }}</strong> 周</span>
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

      <div class="lap-board">
        <template v-if="lapGridRows.length > 0">
          <div class="lap-board-scroll">
            <div class="lap-board-grid lap-board-head" :style="lapBoardGridStyle">
              <div class="lap-corner">周</div>
              <div v-for="h in lapColumnHeaders" :key="h.i" class="lap-col-head">
                <span class="lap-col-head-n">{{ h.i }}</span>
                <span class="lap-col-head-s">本</span>
              </div>
            </div>
            <div
              v-for="row in lapGridRows"
              :key="row.lap_no"
              class="lap-board-grid lap-board-body-row"
              :style="lapBoardGridStyle"
              :data-lap-no="String(row.lap_no)"
            >
              <div class="lap-label">第{{ row.lap_no }}周目</div>
              <!-- 割当後：同一周内で隣列かつ同一品番の枠を横方向に結合表示（製品名・本数） -->
              <template v-if="row.mergedLeft != null">
                <div class="lap-merged-host" :style="innerMergedGridStyle">
                  <div
                    v-for="ms in row.mergedLeft"
                    :key="ms.key"
                    class="lap-merged-seg"
                    :class="[
                      'sched-color-' + schedColorIndexForProductCd(ms.product_cd),
                      ms.boardMark === 'manual' ? 'lap-merged-seg--manual' : ms.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                    ]"
                    :style="{ gridColumn: `${ms.startCol} / span ${ms.span}`, gridRow: '1' }"
                  >
                    <span
                      class="lap-merged-text"
                      :title="`${ms.plating_machine}・治具${ms.span}本・生産${ms.slotCount}本`"
                    >{{ formatPlatingBoardLabel(ms.product_name, ms.span) }}</span>
                  </div>
                  <div
                    v-if="(row.mergedTail?.length ?? 0) > 0"
                    class="lap-merged-tail"
                    :style="{ gridColumn: `${lapBoardColCount} / span 1`, gridRow: '1' }"
                  >
                    <div
                      v-for="tc in row.mergedTail"
                      :key="tc.id"
                      class="lap-merged-tail-item"
                      :class="[
                        'sched-color-' + schedColorIndexForProductCd(tc.product_cd),
                        tc.boardMark === 'manual' ? 'lap-merged-seg--manual' : tc.boardMark === 'rush' ? 'lap-merged-seg--rush' : '',
                      ]"
                    >
                      <span
                        class="lap-merged-text"
                        :title="`${tc.plating_machine}・治具1本・生産${tc.qty}本`"
                      >{{ formatPlatingBoardLabel(tc.product_name, 1) }}</span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div
                  v-for="(cell, ci) in row.cells"
                  :key="`${row.lap_no}-${ci}`"
                  class="lap-col"
                  :class="{ 'lap-col--empty': cell.segments.length === 0 }"
                >
                  <div class="lap-track lap-track--grid" :data-lap-no="row.lap_no">
                    <div
                      v-for="seg in cell.segments"
                      :key="`${row.lap_no}-${ci}-${seg.key}`"
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
        <div v-else class="board-empty">
          {{ layoutBoardReady ? '②の「看板に割当」で枠へ割り当てるか、ドラッグで順序を調整してください' : '「標準レイアウト」で1周の本数と表示段数を設定してください' }}
        </div>
      </div>
    </el-card>
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
  deletePlatingDraft,
  fetchPlatingDraftById,
  fetchLatestPlatingDraftByDate,
  updatePlatingDraft,
  type PlatingBoardCardBody,
  type PlatingBoardCardOut,
  type PlatingDraftItemBody,
  type PlatingDraftItemOut,
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
  lap_no: number
  turn_seq: number
  colorIdx: number
  boardMark: BoardMark
}

const scheduleCards = ref<ScheduleCard[]>([])
const standardPositions = ref(new Map<string, { lap_no: number; turn_seq: number }>())
/** API から③ボードを復元する／読込でボードを空にするとき、deep watch による不要な自動保存を抑止 */
const isBoardHydratingFromApi = ref(false)

const TABLE_H = 340

const jigsPerLap = ref(100)
const minutesPerLap = ref(100)

/** ③ボード：標準レイアウト確定後の列数・段数（②の下書き一覧とは別保持。ダイアログで変更） */
const templateDialogVisible = ref(false)
const tplFormJigsPerLap = ref(100)
const tplFormMaxLaps = ref(1)
const layoutBoardReady = ref(false)
const layoutJigsPerLap = ref(100)
const layoutMaxLaps = ref(1)

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

interface DraftItem extends DraftSourceItem {
  uid: string
  /** サーバー行 id（CuttingInstruction の並び替え比較と同様のタイブレーク用） */
  id?: number
  work_date: string
  slots: number
  sort_order: number
}

const draftItems = ref<DraftItem[]>([])
const draftStats = computed(() => {
  const rowCount = draftItems.value.length
  const totalQty = draftItems.value.reduce((s, it) => s + Math.max(0, Math.floor(num(it.qty))), 0)
  const totalSlots = draftItems.value.reduce((s, it) => s + Math.max(0, Math.floor(num(it.slots))), 0)
  return { rowCount, totalQty, totalSlots }
})
const draftTableRef = ref<any>(null)
const draftWorkDate = ref(todayYmdJapan())
/** loadLatestDraft 内で作業日を補正している間は draftWorkDate の watch で再取得しない */
const syncingDraftWorkDateFromLoad = ref(false)
const editingQtyUid = ref<string | null>(null)

/** planDate（API）＝基準日。作業日だけ変えたい場合と揃えたいときに使う */
function alignBaseDateToDraftWorkDate() {
  const d = draftWorkDate.value
  if (!d) {
    ElMessage.warning('作業日を先に指定してください')
    return
  }
  leftInventoryDate.value = d
  rightGenDate.value = addDaysYmdJapan(d, 1)
  ElMessage.info(`在庫の基準日を ${d}、見込みの参照日を ${rightGenDate.value} にしました`)
}
const editingQtyValue = ref<number>(0)
const loadingDraft = ref(false)
const savingDraft = ref(false)
const currentDraftId = ref<number | null>(null)
const draggingSource = ref<DraftSourceItem | null>(null)
const jigDialogVisible = ref(false)
const savingJigAvailability = ref(false)
const jigAvailabilityRows = ref<{ machine_id: number | null; plating_machine: string; available_qty: number }[]>([])

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

function cloneSourceToDraft(src: DraftSourceItem): DraftItem {
  const kake = src.kake > 0 ? src.kake : 1
  const qty = Math.max(0, num(src.qty))
  return {
    ...src,
    uid: `di-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    work_date: draftWorkDate.value || todayYmdJapan(),
    slots: Math.ceil(qty / kake),
    sort_order: draftItems.value.length + 1,
  }
}

function onDragFromLeftRow(row: LeftPaneRow, evt?: DragEvent) {
  if (evt?.dataTransfer) {
    evt.dataTransfer.effectAllowed = 'copy'
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
  if (evt?.dataTransfer) {
    evt.dataTransfer.effectAllowed = 'copy'
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

async function onDropToDraftTarget() {
  if (!draggingSource.value) return
  const item = cloneSourceToDraft(draggingSource.value)
  draftItems.value = [...draftItems.value, item]
  refreshDraftSortOrder()
  draggingSource.value = null
  try {
    await persistDraft(false)
  } catch (e) {
    console.error(e)
    ElMessage.error('自動保存に失敗しました。「下書きを保存」から再試行してください')
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
  })
}

/**
 * CuttingInstruction.vue と同様の並び：主キー production_sequence 相当＝sort_order、同順は id、無 id は uid。
 * （参照: cuttingManagementList ソート `(a.production_sequence ?? 0) - (b.production_sequence ?? 0)` 次 `(a.id ?? 0) - (b.id ?? 0)`）
 */
function compareDraftItemBySequence(a: DraftItem, b: DraftItem): number {
  const sa = a.sort_order ?? 0
  const sb = b.sort_order ?? 0
  if (sa !== sb) return sa - sb
  const ida = a.id ?? 0
  const idb = b.id ?? 0
  if (ida !== idb) return ida - idb
  return String(a.uid).localeCompare(String(b.uid))
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

function refreshDraftSortOrder() {
  draftItems.value = draftItems.value.map((it, idx) => ({ ...it, sort_order: idx + 1 }))
}

/** CuttingInstruction.onDropCuttingRowForReorder と同じ：reordered.splice(fromIdx,1); splice(toIdx,0,dragged) */
function reorderDraftListByIndex<T>(list: T[], oldIndex: number, newIndex: number): T[] {
  const reordered = [...list]
  const [dragged] = reordered.splice(oldIndex, 1)
  reordered.splice(newIndex, 0, dragged)
  return reordered
}

/** ② 上下ドラッグ確定後：全行を新順で作り直し、sort_order・qty・slots を一括で整合 */
function applyFullDraftReorderAfterDrag(ordered: DraftItem[]) {
  draftItems.value = ordered.map((it, idx) => {
    const kake = it.kake > 0 ? it.kake : 1
    const qty = Math.max(0, Math.floor(num(it.qty)))
    const slots = Math.max(0, Math.ceil(qty / kake) || 0)
    return {
      ...it,
      sort_order: idx + 1,
      qty,
      slots,
    }
  })
}

function recalcDraftItemSlots(uid: string) {
  const idx = draftItems.value.findIndex((x) => x.uid === uid)
  if (idx < 0) return
  const it = draftItems.value[idx]
  const kake = it.kake > 0 ? it.kake : 1
  draftItems.value[idx] = {
    ...it,
    qty: Math.max(0, Math.floor(num(it.qty))),
    slots: Math.ceil(Math.max(0, num(it.qty)) / kake),
  }
}

function onDraftQtyChange(uid: string, qty: number) {
  const idx = draftItems.value.findIndex((x) => x.uid === uid)
  if (idx < 0) return
  draftItems.value[idx] = {
    ...draftItems.value[idx],
    qty: Math.max(0, Math.floor(num(qty))),
  }
  recalcDraftItemSlots(uid)
  refreshDraftSortOrder()
}

function startQtyEdit(row: DraftItem) {
  editingQtyUid.value = row.uid
  editingQtyValue.value = Math.max(0, Math.floor(num(row.qty)))
}

async function commitQtyEdit(uid: string) {
  if (editingQtyUid.value !== uid) return
  onDraftQtyChange(uid, editingQtyValue.value)
  editingQtyUid.value = null
  try {
    await persistDraft(false)
  } catch (e) {
    console.error(e)
    ElMessage.error('生産数の自動保存に失敗しました。通信状況を確認してください')
  }
}

function removeDraftItem(uid: string) {
  draftItems.value = draftItems.value.filter((x) => x.uid !== uid)
  refreshDraftSortOrder()
}

function clearDraftItems() {
  draftItems.value = []
}

async function deleteCurrentDraft() {
  if (!currentDraftId.value) return
  try {
    await deletePlatingDraft(currentDraftId.value)
    ElMessage.success(`下書き（ID ${currentDraftId.value}）を削除しました`)
    currentDraftId.value = null
    draftItems.value = []
  } catch (e) {
    console.error(e)
    ElMessage.error('サーバー上の下書き削除に失敗しました')
  }
}

function toDraftItemBody(it: DraftItem): PlatingDraftItemBody {
  return {
    sort_order: it.sort_order,
    work_date: it.work_date || null,
    product_cd: it.product_cd,
    product_name: it.product_name,
    plating_machine: it.plating_machine,
    kake: it.kake,
    qty: it.qty,
    slots: it.slots,
    source_type: it.source_type,
    source_row_key: it.source_key,
  }
}

async function buildDraftPayload(items?: PlatingDraftItemBody[]) {
  const board_cards = await mergePersistBoardCards()
  return {
    plan_date: draftWorkDate.value || todayYmdJapan(),
    daily_minutes: PLATING_DAY_MINUTES,
    jigs_per_lap: jigsPerLap.value,
    minutes_per_lap: minutesPerLap.value,
    total_slots: kpi.value.totalSlots,
    used_slots: kpi.value.usedSlots,
    remain_slots: kpi.value.remainSlots,
    items: items ?? draftItems.value.map(toDraftItemBody),
    board_cards,
  }
}

/** 更新時に他作業日の行をマージし、PUT が現在表示分のみで aps_plating_plan_draft_items を誤削除しないようにする */
async function mergePersistItems(): Promise<PlatingDraftItemBody[]> {
  if (!currentDraftId.value) {
    return draftItems.value.map(toDraftItemBody)
  }
  const existing = await fetchPlatingDraftById(currentDraftId.value)
  const wd = draftWorkDate.value || todayYmdJapan()
  const plan = String(existing.plan_date || '').slice(0, 10) || wd
  const kept = existing.items
    .filter((it) => effectiveItemWorkDate(it, plan) !== wd)
    .sort(comparePlatingApiDraftItemBySequence)
    .map(apiItemToBody)
  // 画面上の②の行順＝ draftItems の配列順（ドラッグ後はここが正。sort_order のみで再ソートしない）
  const mine = draftItems.value.map(toDraftItemBody)
  return [...kept, ...mine].map((x, i) => ({ ...x, sort_order: i + 1 }))
}

function scheduleCardsToBoardBodies(workDateYmd: string): PlatingBoardCardBody[] {
  return [...scheduleCards.value]
    .filter((c) => c.qty > 0)
    .sort((a, b) => a.lap_no - b.lap_no || a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    .map((c) => ({
      work_date: workDateYmd,
      lap_no: c.lap_no,
      turn_seq: c.turn_seq,
      product_cd: c.product_cd,
      product_name: c.product_name,
      plating_machine: c.plating_machine,
      kake: c.kake,
      qty: c.qty,
      slots: c.slots,
      board_mark: c.boardMark,
      stable_key: (c.id || '').slice(0, 128) || null,
    }))
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

/** ドラッグ等の高頻度変更：デバウンス後に aps_plating_plan_board_cards へ書込（persistDraft の board_cards 経由） */
function scheduleBoardAutosave() {
  if (isBoardHydratingFromApi.value) return
  if (loadingDraft.value) return
  if (savingDraft.value) return
  if (!draftWorkDate.value) return
  if (draftItems.value.length === 0) return
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
  if (savingDraft.value) return
  if (!draftWorkDate.value) return
  if (draftItems.value.length === 0) return
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
  // 画面上の上から下の順に sort_order を 1…n に揃える（API と行番号表示の整合）
  refreshDraftSortOrder()
  let items: PlatingDraftItemBody[]
  try {
    items = await mergePersistItems()
  } catch (e) {
    console.error(e)
    if (notify) ElMessage.error('下書き明細の取得に失敗しました')
    return
  }
  if (items.length === 0) {
    if (notify) ElMessage.warning('②の下書きに1件以上のデータがありません')
    return
  }
  const body = await buildDraftPayload(items)
  if (currentDraftId.value) {
    await updatePlatingDraft(currentDraftId.value, body)
  } else {
    const created = await createPlatingDraft(body)
    currentDraftId.value = created.id
  }
}

async function saveDraftToBackend() {
  savingDraft.value = true
  try {
    await persistDraft(true)
    ElMessage.success('②の下書きと③のボードを保存しました')
  } catch (e) {
    console.error(e)
    ElMessage.error('下書きの保存に失敗しました')
  } finally {
    savingDraft.value = false
  }
}

type LoadLatestDraftOpts = { autoMode?: boolean; autoSyncWorkDate?: boolean }

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
    const head = await fetchLatestPlatingDraftByDate(planDateForDraft)
    if (!head) {
      draftItems.value = []
      currentDraftId.value = null
      scheduleCards.value = []
      standardPositions.value = new Map()
      layoutBoardReady.value = false
      if (!autoMode) ElMessage.warning('この日付の下書きはありません')
      return
    }
    const planKey = String(head.plan_date || planDateForDraft).slice(0, 10)
    const rowsNormalized = (head.items || []).map((it) => ({
      ...it,
      work_date: effectiveItemWorkDate(it, planKey),
    }))

    let wd = draftWorkDate.value || planDateForDraft
    if (autoSyncWorkDate && rowsNormalized.length > 0) {
      const hasMatch = rowsNormalized.some((it) => it.work_date === wd)
      if (!hasMatch) {
        wd = dominantWorkDateFromItems(rowsNormalized)
      }
    }
    if (wd !== draftWorkDate.value) {
      syncingDraftWorkDateFromLoad.value = true
      draftWorkDate.value = wd
      await nextTick()
      syncingDraftWorkDateFromLoad.value = false
    }

    const display = await fetchPlatingDraftById(head.id, wd)
    currentDraftId.value = display.id
    const displayPlanKey = String(display.plan_date || wd).slice(0, 10)
    draftItems.value = (display.items || [])
      .map((it, idx) => ({
        uid: `ld-${Date.now()}-${idx}-${Math.random().toString(36).slice(2, 6)}`,
        id: it.id,
        work_date: effectiveItemWorkDate(it, displayPlanKey),
        source_key: it.source_row_key || `${it.source_type}-${it.product_cd}-${idx}`,
        source_type: it.source_type as 'left_inventory' | 'right_gen',
        product_cd: it.product_cd,
        product_name: it.product_name,
        plating_machine: it.plating_machine,
        kake: Number(it.kake) || 0,
        qty: Number(it.qty) || 0,
        slots: Number(it.slots) || 0,
        sort_order: Number(it.sort_order) || idx + 1,
      }))
      .sort(compareDraftItemBySequence)
    refreshDraftSortOrder()

    isBoardHydratingFromApi.value = true
    try {
      const jp = Math.max(1, Math.floor(Number(display.jigs_per_lap) || 0))
      if (jp > 0) jigsPerLap.value = jp
      const rawBoard = display.board_cards || []
      if (rawBoard.length > 0) {
        layoutBoardReady.value = true
        layoutJigsPerLap.value = jp > 0 ? jp : layoutJigsPerLap.value
        const maxLap = Math.max(1, ...rawBoard.map((b) => b.lap_no))
        layoutMaxLaps.value = maxLap
        scheduleCards.value = rawBoard
          .slice()
          .sort((a, b) => a.lap_no - b.lap_no || a.turn_seq - b.turn_seq || (a.id ?? 0) - (b.id ?? 0))
          .map((bc, idx) => {
            const mk: BoardMark =
              bc.board_mark === 'rush' || bc.board_mark === 'manual' ? bc.board_mark : 'standard'
            const id = (bc.stable_key || '').trim() || `db-${bc.id}-${idx}`
            return {
              id,
              product_cd: bc.product_cd,
              product_name: bc.product_name,
              plating_machine: bc.plating_machine,
              kake: Number(bc.kake) || 0,
              qty: Number(bc.qty) || 0,
              slots: Number(bc.slots) || 0,
              lap_no: bc.lap_no,
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
      } else {
        scheduleCards.value = []
        standardPositions.value = new Map()
        layoutBoardReady.value = false
      }
    } finally {
      void nextTick(() => {
        setTimeout(() => {
          isBoardHydratingFromApi.value = false
        }, 120)
      })
    }

    if (!autoMode) ElMessage.success(`下書き（ID ${display.id}）を読み込みました`)
  } catch (e) {
    console.error(e)
    if (!autoMode) ElMessage.error('下書きの読み込みに失敗しました')
  } finally {
    loadingDraft.value = false
  }
}

async function loadJigAvailability() {
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
  }
}

async function openJigAvailabilityDialog() {
  await loadJigAvailability()
  jigDialogVisible.value = true
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
    jigDialogVisible.value = false
  } catch (e) {
    console.error(e)
    ElMessage.error('メッキ治具の使用可能本数の保存に失敗しました')
  } finally {
    savingJigAvailability.value = false
  }
}

function focusNextJigQtyInput(currIndex: number) {
  const inputs = Array.from(
    document.querySelectorAll<HTMLInputElement>('.jig-edit-table .el-input-number__input'),
  )
  if (inputs.length === 0) return
  const next = inputs[currIndex + 1]
  if (next) {
    next.focus()
    next.select()
    return
  }
  // 最終行で Enter を押したら先頭行にフォーカスを戻し、連続入力しやすくする
  inputs[0].focus()
  inputs[0].select()
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
  const cycle = minutesPerLap.value
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

function getJigAvailabilityLimitMap(): Map<string, number> {
  const map = new Map<string, number>()
  for (const r of jigAvailabilityRows.value) {
    const key = normalizeMachineKey(r.plating_machine)
    if (!key) continue
    const n = Math.max(0, Math.floor(Number(r.available_qty) || 0))
    map.set(key, n)
  }
  return map
}

interface JigDemand {
  product_cd: string
  product_name: string
  plating_machine: string
  kake: number
  qty: number
  slots: number
}

/** ②下書きの並びで治具の初出順を決め、未登録分は使用可能本数マスタ順、その後は残り */
function buildPlatingMachineOrderForSchedule(
  machinesWithDemandKeys: Set<string>,
  demandByMachine: Map<string, JigDemand[]>,
): string[] {
  const displayForKey = (k: string): string => {
    const arr = demandByMachine.get(k)
    const d0 = arr?.[0]
    const name = d0 && String(d0.plating_machine || '').trim()
    return name || k
  }
  const seen = new Set<string>()
  const ordered: string[] = []
  /** ②テーブルの上から下の行順（draftItems の配列順）で治具の初出順を決める */
  for (const it of draftItems.value) {
    const m = String(it.plating_machine || '').trim()
    if (!m || m === '—') continue
    const k = normalizeMachineKey(m)
    if (!machinesWithDemandKeys.has(k) || seen.has(k)) continue
    seen.add(k)
    ordered.push(displayForKey(k))
  }
  for (const r of jigAvailabilityRows.value) {
    const m = String(r.plating_machine || '').trim()
    if (!m || m === '—') continue
    const k = normalizeMachineKey(m)
    if (!machinesWithDemandKeys.has(k) || seen.has(k)) continue
    seen.add(k)
    ordered.push(displayForKey(k))
  }
  for (const k of machinesWithDemandKeys) {
    if (seen.has(k)) continue
    seen.add(k)
    ordered.push(displayForKey(k))
  }
  return ordered
}

function buildJigCardsFromDemand(demands: JigDemand[], capLaps?: number): ScheduleCard[] {
  const cycle = minutesPerLap.value
  const lapsPerDay = cycle > 0 ? Math.floor(PLATING_DAY_MINUTES / cycle) : 0
  if (lapsPerDay <= 0) return []
  const cap = capLaps != null && capLaps > 0 ? Math.min(lapsPerDay, capLaps) : lapsPerDay
  const lapUpper = Math.max(0, cap)

  const limits = getJigAvailabilityLimitMap()

  const demandByMachine = new Map<string, JigDemand[]>()
  const machinesFromDemand = new Set<string>()
  for (const d of demands) {
    const m = String(d.plating_machine || '').trim()
    if (!m || m === '—') continue
    machinesFromDemand.add(m)
    const key = normalizeMachineKey(m)
    const arr = demandByMachine.get(key) ?? []
    arr.push({ ...d, plating_machine: m })
    demandByMachine.set(key, arr)
  }

  const machinesWithDemand = new Set(Array.from(machinesFromDemand, (m) => normalizeMachineKey(m)))
  const orderedMachines = buildPlatingMachineOrderForSchedule(machinesWithDemand, demandByMachine)

  const out: ScheduleCard[] = []
  let colorCounter = 0
  for (let lap = 1; lap <= lapUpper; lap += 1) {
    let turnSeq = 1
    for (const machine of orderedMachines) {
      const mKey = normalizeMachineKey(machine)
      // 需要のある治具のみ並べ、空回りを避ける
      if (!machinesWithDemand.has(mKey)) continue
      const perLap = limits.get(mKey) ?? 0
      if (perLap <= 0) continue
      const q = demandByMachine.get(mKey) ?? []
      for (let jigIdx = 1; jigIdx <= perLap; jigIdx += 1) {
        const head = q[0]
        if (!head || head.slots <= 0 || head.qty <= 0) continue
        const kake = head.kake > 0 ? head.kake : 1
        const allocQty = Math.min(head.qty, kake)
        head.qty -= allocQty
        head.slots -= 1
        if (head.slots <= 0 || head.qty <= 0) q.shift()
        out.push({
          id: `jig-${lap}-${turnSeq}-${jigIdx}-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`,
          product_cd: head.product_cd,
          product_name: head.product_name,
          plating_machine: machine,
          kake,
          qty: allocQty,
          slots: 1,
          lap_no: lap,
          turn_seq: turnSeq,
          colorIdx: colorCounter++,
          boardMark: 'standard',
        })
      }
      turnSeq += 1
    }
  }
  return out
}

function openStandardTemplateDialog() {
  tplFormJigsPerLap.value = layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value
  const d = boardLapsPerDay.value
  tplFormMaxLaps.value = layoutBoardReady.value ? layoutMaxLaps.value : Math.max(1, Math.min(500, d > 0 ? d : 1))
  templateDialogVisible.value = true
}

function confirmStandardTemplate() {
  const j = Math.floor(Number(tplFormJigsPerLap.value) || 1)
  const laps = Math.floor(Number(tplFormMaxLaps.value) || 1)
  layoutJigsPerLap.value = Math.max(1, Math.min(200, j))
  layoutMaxLaps.value = Math.max(1, Math.min(500, laps))
  layoutBoardReady.value = true
  scheduleCards.value = []
  standardPositions.value = new Map()
  templateDialogVisible.value = false
  void nextTick(() => {
    if (!scheduleCards.value.some((c) => c.qty > 0)) initLapTrackSortables()
  })
  ElMessage.success('空き枠を表示しました。②の「看板に割当」から投入してください')
  void flushBoardPersist()
}

/** ②の下書きをボード枠へ自動割当（標準ロジック） */
function mergeDraftIntoSchedule() {
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「標準レイアウト」で枠の条件を確定してください')
    return
  }
  if (draftItems.value.length === 0) {
    ElMessage.warning('②の下書きにデータがありません')
    return
  }
  const demands: JigDemand[] = draftItems.value.map((it) => ({
      product_cd: it.product_cd,
      product_name: it.product_name,
      plating_machine: it.plating_machine,
      kake: it.kake > 0 ? it.kake : 1,
      qty: Math.max(0, Math.floor(num(it.qty))),
      slots: Math.max(0, Math.floor(num(it.slots))),
    }))
  const built = buildJigCardsFromDemand(demands, layoutMaxLaps.value)
  const pos = new Map<string, { lap_no: number; turn_seq: number }>()
  for (const c of built) pos.set(c.id, { lap_no: c.lap_no, turn_seq: c.turn_seq })
  standardPositions.value = pos
  scheduleCards.value = built
  ElMessage.success(
    `割当てが完了しました（${built.length} 枠・合計 ${built.reduce((s, c) => s + c.qty, 0)} 本）`,
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
  cells: LapGridCell[]
  /** null＝未割当の空枠（列セル表示）／配列＝左側列の横結合バー */
  mergedLeft: LapMergedSegment[] | null
  /** 最終列に積まれる枠（横結合しない） */
  mergedTail: ScheduleCard[] | null
}

/** 1周あたりの治具本数＝列数（レイアウト確定後は layout を優先） */
const lapBoardColCount = computed(() => {
  const j = Math.floor(Number(layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value) || 0)
  return Math.max(1, Math.min(200, j > 0 ? j : 1))
})

/** 各「本」列：約 3 桁分の幅（ch＝数字 0 の幅基準）＋横スクロールで全体を閲覧 */
const lapBoardColTrack = 'minmax(3ch, 3ch)'

const lapBoardGridStyle = computed(() => ({
  gridTemplateColumns: `52px repeat(${lapBoardColCount.value}, ${lapBoardColTrack})`,
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

  return lapNumbers.map((lapNo) => {
    const cards = (byLap.get(lapNo) ?? []).sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    const bins = binCardsIntoColumns(cards, n)
    const cells: LapGridCell[] = bins.map((bin) => ({
      segments: cardsToDisplaySegments(bin),
    }))
    const mergedLeft = cards.length > 0 ? buildMergedLeftSegments(cards, lapNo, n) : null
    const mergedTail = cards.length > 0 ? (binCardsIntoColumns(cards, n)[n - 1] ?? []) : null
    return { lap_no: lapNo, cells, mergedLeft, mergedTail }
  })
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
  const rows = [...document.querySelectorAll<HTMLElement>('.lap-board-body-row')]
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

let draftTableSortable: Sortable | null = null
let lapTrackSortables: Sortable[] = []

function destroyDraftTableSortable() {
  draftTableSortable?.destroy()
  draftTableSortable = null
}

function initDraftTableSortable() {
  destroyDraftTableSortable()
  const tableEl = draftTableRef.value?.$el as HTMLElement | undefined
  if (!tableEl) return
  const tbody = tableEl.querySelector('.el-table__body-wrapper tbody') as HTMLElement | null
  if (!tbody) return
  draftTableSortable = Sortable.create(tbody, {
    animation: 150,
    /** 製品名列のみ掴んで行移動（生産数・削除等はドラッグしない） */
    handle: '.draft-row-drag-handle',
    onEnd: async (evt) => {
      if (evt.oldIndex == null || evt.newIndex == null || evt.oldIndex === evt.newIndex) return
      const arr = reorderDraftListByIndex(draftItems.value, evt.oldIndex, evt.newIndex)
      applyFullDraftReorderAfterDrag(arr)
      await nextTick()
      try {
        await persistDraft(false)
      } catch (e) {
        console.error(e)
        ElMessage.error('並び順の自動保存に失敗しました。通信状況を確認してください')
      }
    },
  })
}

function destroyLapTrackSortables() {
  for (const s of lapTrackSortables) s.destroy()
  lapTrackSortables = []
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
        })
      },
    })
    lapTrackSortables.push(s)
  }
}

/** 数量が入っている割当枠のみ印刷対象 */
const hasPrintableScheduleRows = computed(() => scheduleCards.value.some((c) => num(c.qty) > 0))

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

/** 画面上の lap-board と同じ構造を印刷 HTML に組み立てる */
function buildLapBoardRowPrintHtml(row: LapGridRow, n: number): string {
  const gridStyle = `grid-template-columns:52px repeat(${n},${LAP_PRINT_COL_TRACK})`
  const innerGrid = `grid-template-columns:repeat(${n},${LAP_PRINT_COL_TRACK})`
  const lapLabel = `第${row.lap_no}周目`

  if (row.mergedLeft != null) {
    const leftSegs = row.mergedLeft
      .map((ms) => {
        const ci = schedColorIndexForProductCd(ms.product_cd)
        const mk = boardMarkSegClass(ms.boardMark, true)
        return `<div class="lap-merged-seg sched-color-${ci} ${mk}" style="grid-column:${ms.startCol} / span ${ms.span};grid-row:1"><span class="lap-merged-text">${escapeHtmlForPrint(
          formatPlatingBoardLabel(ms.product_name, ms.span),
        )}</span></div>`
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
  const gridRows = lapGridRows.value
  if (gridRows.length === 0) {
    ElMessage.warning('ボード表示がありません（標準レイアウトと割当を確認してください）')
    return
  }
  const k = kpi.value
  const workDate = draftWorkDate.value || '—'
  const printedAt = dayjs().tz(TZ_JP).format('YYYY-MM-DD HH:mm:ss')
  const layoutDesc = layoutBoardReady.value
    ? `レイアウト：1周 ${layoutJigsPerLap.value} 本／最大 ${layoutMaxLaps.value} 周`
    : 'レイアウト：未確定（標準レイアウト未設定）'

  const n = lapBoardColCount.value
  const headCols = Array.from({ length: n }, (_, i) => i + 1)
    .map(
      (i) =>
        `<div class="lap-col-head"><span class="lap-col-head-n">${i}</span><span class="lap-col-head-s">本</span></div>`,
    )
    .join('')
  const headGridStyle = `grid-template-columns:52px repeat(${n},${LAP_PRINT_COL_TRACK})`
  const boardBody = gridRows.map((row) => buildLapBoardRowPrintHtml(row, n)).join('')

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
      min-width: 0; display: flex; align-items: center; justify-content: center;
      padding: 3px 4px; margin: 2px 0; box-sizing: border-box;
      border: 1px solid rgba(0,0,0,0.06); border-radius: 6px;
    }
    .lap-merged-seg--manual { outline: 2px solid #fa8c16; outline-offset: -1px; z-index: 1; }
    .lap-merged-seg--rush { outline: 2px solid #cf1322; outline-offset: -1px; z-index: 1; }
    .lap-merged-text {
      font-size: 10px; line-height: 1.25; text-align: center; overflow: hidden; text-overflow: ellipsis;
      white-space: nowrap; max-width: 100%; font-weight: 600; color: #303133;
    }
    .lap-merged-tail {
      display: flex; flex-direction: column; gap: 2px; min-width: 0; padding: 2px;
      box-sizing: border-box; border-left: 1px solid #ebeef5;
    }
    .lap-merged-tail-item {
      flex: 0 0 auto; min-height: 22px; display: flex; align-items: center; justify-content: center;
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
      min-height: 20px; display: flex; align-items: center; justify-content: space-between;
      gap: 4px; padding: 2px 4px; border-radius: 2px;
    }
    .lap-segment--manual { outline: 2px solid #fa8c16; outline-offset: -1px; z-index: 1; }
    .lap-segment--rush { outline: 2px solid #cf1322; outline-offset: -1px; z-index: 1; }
    .lap-segment-text {
      font-size: 10px; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
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
  void flushBoardPersist()
}

watch(
  scheduleCards,
  () => {
    const hasCards = scheduleCards.value.some((c) => c.qty > 0)
    if (hasCards) destroyLapTrackSortables()
    else void nextTick(() => initLapTrackSortables())
    scheduleBoardAutosave()
  },
  { deep: true },
)
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
  },
  { flush: 'sync' },
)
watch(draftItems, () => {
  nextTick(initDraftTableSortable)
}, { deep: true })

onMounted(() => {
  void loadLatestDraft({ autoMode: true, autoSyncWorkDate: true })
  loadJigAvailability()
  nextTick(() => {
    bindTableRowDrag(leftTableRef, leftRows.value, 'left')
    bindTableRowDrag(rightTableRef, rightRows.value, 'right')
    initDraftTableSortable()
    initLapTrackSortables()
  })
})

onBeforeUnmount(() => {
  cancelBoardAutosaveTimer()
  destroyDraftTableSortable()
  destroyLapTrackSortables()
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

.pp-card--draft {
  border-color: color-mix(in oklab, var(--el-color-warning) 24%, var(--pp-border));
  background:
    linear-gradient(180deg, color-mix(in oklab, var(--el-color-warning-light-9) 48%, transparent) 0%, transparent 58%),
    var(--el-bg-color);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.035);
}

.pp-card--draft :deep(.el-card__header) {
  background:
    linear-gradient(90deg, color-mix(in oklab, var(--el-color-warning-light-9) 66%, transparent), transparent 72%),
    var(--el-fill-color-blank);
}

.draft-head-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.draft-head-hint {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid color-mix(in oklab, var(--el-color-warning) 42%, var(--el-border-color-lighter));
  background: color-mix(in oklab, var(--el-color-warning-light-9) 78%, var(--el-bg-color));
  color: color-mix(in oklab, var(--el-color-warning) 70%, var(--el-text-color-regular));
  font-size: 11px;
  font-weight: 600;
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

.tpl-dialog-hint {
  margin: 0 0 8px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
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

.draft-wrap {
  border: 1px solid color-mix(in oklab, var(--el-color-warning) 22%, var(--el-border-color-lighter));
  border-radius: 10px;
  overflow: hidden;
  background:
    linear-gradient(180deg, color-mix(in oklab, var(--el-color-warning-light-9) 40%, transparent) 0%, transparent 110px),
    var(--el-fill-color-blank);
}

.draft-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  font-size: 12px;
  border-bottom: 1px solid color-mix(in oklab, var(--el-color-warning) 18%, var(--el-border-color-lighter));
  background:
    linear-gradient(90deg, color-mix(in oklab, var(--el-color-warning-light-8) 52%, transparent), transparent 74%),
    var(--el-bg-color);
}

.draft-toolbar-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.draft-toolbar-meta {
  font-variant-numeric: tabular-nums;
  color: color-mix(in oklab, var(--el-color-warning-dark-2) 56%, var(--el-text-color-secondary));
  font-weight: 600;
  letter-spacing: 0.2px;
}

.draft-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 8px 10px 4px;
}

.draft-stat-card {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 9px;
  border-radius: 9px;
  border: 1px solid color-mix(in oklab, var(--el-color-warning) 26%, var(--el-border-color-lighter));
  background:
    linear-gradient(180deg, color-mix(in oklab, var(--el-color-warning-light-9) 76%, transparent), transparent),
    var(--el-bg-color);
}

.draft-stat-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.draft-stat-value {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: color-mix(in oklab, var(--el-color-warning-dark-2) 82%, var(--el-text-color-primary));
  letter-spacing: 0.2px;
}

.draft-row-drag-handle {
  cursor: grab;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
  color: color-mix(in oklab, var(--el-color-warning-dark-2) 72%, var(--el-text-color-primary));
  font-weight: 600;
  border-bottom: 1px dashed transparent;
  transition: color 120ms ease, border-color 120ms ease;
}

.draft-row-drag-handle:hover {
  color: color-mix(in oklab, var(--el-color-warning-dark-2) 86%, var(--el-text-color-primary));
  border-color: color-mix(in oklab, var(--el-color-warning) 60%, transparent);
}

.draft-row-drag-handle:active {
  cursor: grabbing;
}

.qty-cell-edit {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.qty-cell-edit :deep(.el-input-number) {
  width: 88px;
}

.qty-readonly {
  display: inline-block;
  min-width: 48px;
  text-align: right;
  cursor: text;
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid color-mix(in oklab, var(--el-color-warning-light-7) 45%, transparent);
  background: color-mix(in oklab, var(--el-color-warning-light-9) 60%, var(--el-bg-color));
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.qty-readonly:hover {
  background: color-mix(in oklab, var(--el-color-warning-light-8) 72%, var(--el-bg-color));
  border-color: color-mix(in oklab, var(--el-color-warning) 50%, var(--el-border-color-lighter));
}

.draft-target-table :deep(.el-table__header th) {
  background: color-mix(in oklab, var(--el-color-warning-light-9) 78%, var(--el-bg-color));
}

.draft-target-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: color-mix(in oklab, var(--el-color-warning-light-9) 56%, transparent);
}

@media (max-width: 900px) {
  .draft-stat-grid {
    grid-template-columns: 1fr;
    gap: 6px;
  }
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
}

.lap-board-scroll {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  border-radius: 6px;
  scrollbar-gutter: stable;
}

.lap-board-grid {
  display: grid;
  align-items: stretch;
  gap: 0;
  width: max-content;
  box-sizing: border-box;
}

.lap-board-head {
  margin-bottom: 0;
  border-radius: 6px 6px 0 0;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  border-bottom: none;
  background: var(--el-bg-color);
}

.lap-board-body-row {
  border: 1px solid var(--el-border-color-lighter);
  border-top: none;
  background: var(--el-bg-color);
}

.lap-board-body-row:last-of-type {
  border-radius: 0 0 6px 6px;
}

.lap-corner,
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

.lap-board-body-row .lap-label {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.lap-merged-host {
  grid-column: 2 / -1;
  display: grid;
  align-items: stretch;
  min-height: 38px;
  box-sizing: border-box;
  border-right: none;
}

.lap-merged-seg {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
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

.lap-merged-text {
  font-size: 10px;
  line-height: 1.25;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  font-weight: 600;
  color: var(--el-text-color-primary);
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
  flex: 0 0 auto;
  min-height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px 3px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-sizing: border-box;
}

.lap-col {
  min-width: 0;
  max-width: 100%;
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
  min-height: 36px;
  gap: 2px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--el-fill-color);
}

.lap-segment--cell {
  min-height: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
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
  font-size: 10px;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

.jig-dialog-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
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

.jig-edit-table {
  border-radius: 8px;
  overflow: hidden;
}

.jig-edit-table :deep(.el-table__cell) {
  padding-top: 4px;
  padding-bottom: 4px;
}

.jig-edit-table :deep(.el-input-number) {
  width: 112px !important;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
