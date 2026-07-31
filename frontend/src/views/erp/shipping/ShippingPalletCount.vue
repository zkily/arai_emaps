<template>
  <div class="pallet-count-page">
    <div class="page-bg" aria-hidden="true">
      <div class="bg-orb orb-a"></div>
      <div class="bg-orb orb-b"></div>
      <div class="bg-grid"></div>
    </div>

    <div class="page-inner">
      <header class="hero glass">
        <div class="hero-main">
          <div class="hero-icon">
            <el-icon :size="26"><Grid /></el-icon>
          </div>
          <div class="hero-text">
            <p class="hero-eyebrow">Shipping · Pallet Count</p>
            <h1 class="hero-title">出荷パレット数管理</h1>
            <p class="hero-desc">グループ別カード／積込日×納入先（同一出荷番号＝1パレット）</p>
          </div>
        </div>
        <div class="hero-actions">
          <el-button class="btn-ghost" @click="showGroupManager = true">
            <el-icon><Setting /></el-icon>
            グループ管理
          </el-button>
          <el-button type="primary" class="btn-primary" :loading="loading" @click="fetchData">
            <el-icon><Search /></el-icon>
            集計
          </el-button>
        </div>
      </header>

      <section class="toolbar glass">
        <div class="toolbar-left">
          <span class="toolbar-label">積込月</span>
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="年月"
            value-format="YYYY-MM"
            :editable="false"
            class="month-picker"
            @change="fetchData"
          />
          <div class="month-quick">
            <button type="button" class="chip" @click="adjustMonth(-1)">
              <el-icon><ArrowLeft /></el-icon>
              前月
            </button>
            <button type="button" class="chip chip-active" @click="setThisMonth">今月</button>
            <button type="button" class="chip" @click="adjustMonth(1)">
              翌月
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
        <div class="legend">
          <span class="legend-item"><i class="dot dot-date"></i>積込日</span>
          <span class="legend-item"><i class="dot dot-advance"></i>先出(東北)</span>
          <span class="legend-item"><i class="dot dot-bin2"></i>2便</span>
          <span class="legend-item"><i class="dot dot-tohoku"></i>小牛田減算</span>
          <span class="legend-item"><i class="dot dot-edit"></i>手動修正</span>
          <span class="legend-item"><i class="dot dot-total"></i>合計</span>
          <span class="legend-hint">納入先セルをダブルクリックで編集</span>
        </div>
      </section>

      <section v-if="pageData.groups.length" class="kpi-row">
        <div class="kpi-card kpi-groups glass-soft">
          <div class="kpi-label">グループ</div>
          <div class="kpi-value">{{ pageData.groups.length }}</div>
        </div>
        <div class="kpi-card kpi-days glass-soft">
          <div class="kpi-label">表示日数</div>
          <div class="kpi-value">{{ displayDayCount }}</div>
        </div>
        <div class="kpi-card kpi-dest glass-soft">
          <div class="kpi-label">納入先合計</div>
          <div class="kpi-value">{{ totalDestinations }}</div>
        </div>
        <div class="kpi-card kpi-pallets glass-soft">
          <div class="kpi-label">パレット合計</div>
          <div class="kpi-value">{{ pageData.grand_total.toLocaleString() }}</div>
        </div>
      </section>

      <section class="cards-section" v-loading="loading">
        <div v-if="!pageData.groups.length && !loading" class="empty-panel glass">
          <el-empty description="グループが未設定です。「グループ管理」で納入先を追加してください。" />
        </div>

        <article
          v-for="(group, gIdx) in pageData.groups"
          :key="group.group_name"
          class="group-card glass"
          :class="[`tone-${gIdx % 5}`, { 'has-advance': group.enable_advance_tohoku }]"
          :style="{ animationDelay: `${gIdx * 0.05}s` }"
        >
          <div class="group-accent" aria-hidden="true"></div>
          <div class="group-card-header">
            <div class="group-title-wrap">
              <span class="group-badge">{{ String(gIdx + 1).padStart(2, '0') }}</span>
              <div class="group-heading">
                <h2 class="group-title">{{ group.group_name }}</h2>
                <div class="group-tags">
                  <span class="meta-pill">納入先 {{ group.destinations.length }}</span>
                  <span v-if="group.enable_advance_tohoku" class="meta-pill meta-advance">
                    先出(東北) → 翌稼働日の小牛田から減算
                  </span>
                </div>
              </div>
            </div>
            <div class="group-header-right">
              <el-radio-group
                v-if="group.enable_bin2 || group.enable_advance_tohoku"
                v-model="owariSideMode"
                size="small"
                class="owari-side-toggle"
              >
                <el-radio-button value="advance">先出(東北)</el-radio-button>
                <el-radio-button value="bin2">2便</el-radio-button>
                <el-radio-button value="both">両方</el-radio-button>
              </el-radio-group>
              <el-button
                class="btn-group-action"
                :disabled="!group.destinations.length"
                @click="printGroupTable(group)"
              >
                <el-icon><Printer /></el-icon>
                印刷
              </el-button>
              <el-button
                type="primary"
                class="btn-group-action"
                :disabled="!group.destinations.length"
                @click="openMailDialog(group)"
              >
                <el-icon><Message /></el-icon>
                メール送信
              </el-button>
              <el-button
                v-if="group.enable_advance_tohoku && (group.advance_total || 0) > 0"
                type="warning"
                class="btn-advance-print"
                :loading="advancePrintLoading"
                @click="printAdvanceSheets"
              >
                <el-icon><Printer /></el-icon>
                先出印刷（{{ group.advance_total }}枚）
              </el-button>
              <div class="group-total-block">
                <span class="group-total-label">合計パレット</span>
                <span class="group-total-value">{{ group.grand_total.toLocaleString() }}</span>
              </div>
            </div>
          </div>

          <div v-if="!group.destinations.length" class="group-empty">
            このグループに納入先がありません
          </div>
          <div v-else class="table-wrap">
            <el-table
              :data="buildTableRows(group)"
              border
              stripe
              size="small"
              class="matrix-table"
              :row-class-name="tableRowClass"
              empty-text="データがありません"
            >
              <el-table-column label="積込日" fixed width="96" align="center" class-name="col-date">
                <template #default="{ row }">
                  <span
                    class="date-cell"
                    :class="{
                      'is-total': row.isTotal,
                      'is-weekend': row.isWeekend,
                    }"
                  >
                    {{ row.dateLabel }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column
                v-for="dest in group.destinations"
                :key="dest.cd"
                min-width="72"
                align="center"
                :class-name="dest.cd === group.tohoku_destination_cd ? 'tohoku-col' : 'dest-col'"
              >
                <template #header>
                  <div class="dest-header" :title="`${dest.cd} ${dest.name}`">
                    <div class="dest-cd">{{ dest.cd }}</div>
                    <div class="dest-name">{{ dest.name }}</div>
                  </div>
                </template>
                <template #default="{ row }">
                  <div
                    v-if="!row.isTotal"
                    class="cell-edit-wrap"
                    :class="{
                      editing: isEditing(row.dateKey!, dest.cd),
                      overridden: isOverridden(group, row.dateKey!, dest.cd),
                    }"
                    @dblclick.stop="startCellEdit(row.dateKey!, dest.cd, row[`d_${dest.cd}`])"
                  >
                    <el-input
                      v-if="isEditing(row.dateKey!, dest.cd)"
                      :ref="(el) => setEditInputRef(el)"
                      v-model="editDraft"
                      type="number"
                      min="0"
                      size="small"
                      class="cell-edit-input"
                      @keydown.enter.prevent="commitCellEdit()"
                      @keydown.esc.prevent="cancelCellEdit()"
                      @blur="commitCellEdit()"
                    />
                    <span
                      v-else
                      :class="[
                        'cell-value',
                        {
                          'is-deducted': !!row.deductHints?.[dest.cd],
                          'is-overridden': isOverridden(group, row.dateKey!, dest.cd),
                        },
                      ]"
                      :title="
                        isOverridden(group, row.dateKey!, dest.cd)
                          ? '手動修正（ダブルクリックで編集）'
                          : row.deductHints?.[dest.cd] || 'ダブルクリックで編集'
                      "
                    >
                      {{ formatCell(row[`d_${dest.cd}`]) }}
                    </span>
                  </div>
                  <span
                    v-else
                    :class="['cell-value', { 'is-total': true }]"
                  >
                    {{ formatCell(row[`d_${dest.cd}`]) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column
                v-if="group.enable_advance_tohoku && showAdvanceCol"
                label="先出(東北)"
                fixed="right"
                width="92"
                align="center"
                class-name="col-advance"
              >
                <template #default="{ row }">
                  <template v-if="row.isTotal">
                    <span class="cell-value is-advance-total">{{ formatCell(row.advanceQty) }}</span>
                  </template>
                  <el-input
                    v-else
                    :model-value="advanceDraft[row.dateKey!] ?? ''"
                    type="number"
                    min="0"
                    size="small"
                    class="advance-input"
                    placeholder=""
                    @update:model-value="(v) => onAdvanceInput(row.dateKey!, String(v ?? ''))"
                    @change="() => saveAdvance(row.dateKey!)"
                  />
                </template>
              </el-table-column>

              <el-table-column
                v-if="group.enable_bin2 && showBin2Col"
                label="2便"
                fixed="right"
                width="72"
                align="center"
                class-name="col-bin2"
              >
                <template #default="{ row }">
                  <template v-if="row.isTotal">
                    <span class="cell-value is-bin2-total">{{ formatBin2Total(row.bin2Qty) }}</span>
                  </template>
                  <button
                    v-else
                    type="button"
                    class="bin2-toggle"
                    :class="{ 'is-on': isBin2On(row.dateKey!), 'is-saving': savingBin2Dates.has(row.dateKey!) }"
                    :disabled="savingBin2Dates.has(row.dateKey!)"
                    :title="isBin2On(row.dateKey!) ? '2便あり（クリックで解除）' : 'クリックで2便にする'"
                    @click="toggleBin2(row.dateKey!)"
                  >
                    <span class="bin2-mark">{{ isBin2On(row.dateKey!) ? '○' : '' }}</span>
                  </button>
                </template>
              </el-table-column>

              <el-table-column
                label="合計"
                fixed="right"
                width="72"
                align="center"
                class-name="col-total"
              >
                <template #default="{ row }">
                  <span class="cell-value is-row-total">{{ formatCell(row.rowTotal) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </article>
      </section>
    </div>

    <DestinationGroupManager
      v-model="showGroupManager"
      page-key="destination_groups_list"
      @groups-updated="handleGroupsUpdated"
    />

    <el-dialog
      v-model="mailDialogVisible"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
      class="pallet-mail-dialog"
      align-center
    >
      <template #header>
        <div class="mail-dlg-header">
          <el-icon :size="18"><Message /></el-icon>
          <div>
            <div class="mail-dlg-title">メール送信</div>
            <div class="mail-dlg-sub">{{ mailGroupName }} のパレット数表を送信</div>
          </div>
        </div>
      </template>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="件名">
          <el-input v-model="mailSubject" maxlength="120" show-word-limit placeholder="件名" />
        </el-form-item>
        <el-form-item label="送信先" required>
          <el-select
            v-model="mailToEmails"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            :loading="mailUsersLoading"
            placeholder="ユーザーを選択（メール登録済み）"
            style="width: 100%"
          >
            <el-option
              v-for="u in mailUserOptions"
              :key="u.id"
              :label="`${u.full_name || u.username}（${u.email}）`"
              :value="u.email"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mailDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="mailSending" @click="sendGroupMail">
          送信
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Grid, Setting, Search, ArrowLeft, ArrowRight, Printer, Message } from '@element-plus/icons-vue'
import DestinationGroupManager from './components/DestinationGroupManager.vue'
import {
  getPalletCountMatrix,
  saveAdvanceTohoku,
  saveBin2,
  saveCellOverride,
  getAdvancePrintSheets,
  sendPalletCountMail,
  type PalletCountGroupCard,
  type PalletCountMatrixData,
  type AdvancePrintSheet,
} from '@/api/shipping/palletCount'
import { getUsers, type UserListItem } from '@/api/system'
import { getJSTToday } from '@/utils/dateFormat'

const loading = ref(false)
const advancePrintLoading = ref(false)
const showGroupManager = ref(false)
const selectedMonth = ref<string>('')
const advanceDraft = ref<Record<string, string>>({})
const bin2On = ref<Record<string, boolean>>({})
const savingDates = ref<Set<string>>(new Set())
const savingBin2Dates = ref<Set<string>>(new Set())
/** オワリ便サイド列の表示切替: advance | bin2 | both */
const owariSideMode = ref<'advance' | 'bin2' | 'both'>('both')

const showAdvanceCol = computed(
  () => owariSideMode.value === 'advance' || owariSideMode.value === 'both',
)
const showBin2Col = computed(
  () => owariSideMode.value === 'bin2' || owariSideMode.value === 'both',
)

const mailDialogVisible = ref(false)
const mailSending = ref(false)
const mailUsersLoading = ref(false)
const mailGroupName = ref('')
const mailSubject = ref('')
const mailToEmails = ref<string[]>([])
const mailUsers = ref<UserListItem[]>([])

const mailUserOptions = computed(() => {
  const seen = new Set<string>()
  const out: UserListItem[] = []
  for (const u of mailUsers.value) {
    const email = String(u.email || '').trim()
    if (!email) continue
    const key = email.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ ...u, email })
  }
  return out
})

/** ダブルクリック編集中のセルキー date|destCd */
const editingCellKey = ref<string | null>(null)
const editDraft = ref('')
const editSaving = ref(false)
let editInputEl: HTMLInputElement | null = null
let suppressNextBlurCommit = false

const pageData = ref<PalletCountMatrixData>({
  dates: [],
  groups: [],
  grand_total: 0,
})

type TableRow = {
  dateLabel: string
  dateKey?: string
  rowTotal: number
  advanceQty?: number
  bin2Qty?: number
  isTotal?: boolean
  isWeekend?: boolean
  deductHints?: Record<string, string>
  [key: string]: string | number | boolean | Record<string, string> | undefined
}

const displayDayCount = computed(() => {
  const days = new Set<string>()
  for (const g of pageData.value.groups) {
    for (const ds of g.dates || []) {
      const hasPallet = (g.row_totals?.[ds] ?? 0) > 0
      const hasAdvance = (g.advance_qty?.[ds] ?? 0) > 0
      const hasBin2 = (g.bin2_qty?.[ds] ?? 0) > 0
      const hasOverride = Object.keys(g.cell_overrides?.[ds] || {}).length > 0
      if (hasPallet || hasAdvance || hasBin2 || hasOverride) days.add(ds)
    }
  }
  return days.size
})

const totalDestinations = computed(() => {
  const cds = new Set<string>()
  for (const g of pageData.value.groups) {
    for (const d of g.destinations || []) cds.add(d.cd)
  }
  return cds.size
})

function currentMonthStr(): string {
  return getJSTToday().slice(0, 7)
}

function monthBounds(ym: string): { start: string; end: string } | null {
  if (!ym || ym.length < 7) return null
  const [ys, ms] = ym.split('-')
  const y = Number(ys)
  const m = Number(ms)
  if (!y || !m) return null
  const lastDay = new Date(y, m, 0).getDate()
  const mm = String(m).padStart(2, '0')
  return {
    start: `${y}-${mm}-01`,
    end: `${y}-${mm}-${String(lastDay).padStart(2, '0')}`,
  }
}

function formatDateLabel(ymd: string): string {
  if (!ymd || ymd.length < 10) return ymd
  const d = new Date(`${ymd}T00:00:00`)
  if (Number.isNaN(d.getTime())) return ymd
  const week = ['日', '月', '火', '水', '木', '金', '土'][d.getDay()]
  return `${ymd.slice(5)}(${week})`
}

function isWeekendYmd(ymd: string): boolean {
  if (!ymd || ymd.length < 10) return false
  const d = new Date(`${ymd}T00:00:00`)
  if (Number.isNaN(d.getTime())) return false
  return d.getDay() === 0 || d.getDay() === 6
}

function formatCell(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return ''
  return n.toLocaleString()
}

function formatBin2Mark(on: boolean | number | undefined): string {
  return Number(on) > 0 ? '○' : ''
}

function formatBin2Total(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return ''
  return String(n)
}

function isBin2On(dateKey: string): boolean {
  if (!dateKey) return false
  if (Object.prototype.hasOwnProperty.call(bin2On.value, dateKey)) {
    return !!bin2On.value[dateKey]
  }
  const owari = pageData.value.groups.find((g) => g.enable_bin2)
  return Number(owari?.bin2_qty?.[dateKey] || 0) > 0
}

function cellKey(dateKey: string, destCd: string) {
  return `${dateKey}|${destCd}`
}

function isEditing(dateKey: string, destCd: string) {
  return editingCellKey.value === cellKey(dateKey, destCd)
}

function isOverridden(group: PalletCountGroupCard, dateKey: string, destCd: string) {
  return group.cell_overrides?.[dateKey]?.[destCd] !== undefined
}

function setEditInputRef(el: unknown) {
  const comp = el as { input?: HTMLInputElement; $el?: HTMLElement } | null
  const input =
    comp?.input ||
    (comp?.$el?.querySelector?.('input') as HTMLInputElement | null) ||
    null
  editInputEl = input
}

function startCellEdit(dateKey: string, destCd: string, currentVal: unknown) {
  if (!dateKey || !destCd || editSaving.value) return
  const n = Number(currentVal)
  editDraft.value = Number.isFinite(n) && n > 0 ? String(n) : ''
  editingCellKey.value = cellKey(dateKey, destCd)
  nextTick(() => {
    editInputEl?.focus()
    editInputEl?.select()
  })
}

function cancelCellEdit() {
  suppressNextBlurCommit = true
  editingCellKey.value = null
  editDraft.value = ''
  nextTick(() => {
    suppressNextBlurCommit = false
  })
}

async function commitCellEdit() {
  if (suppressNextBlurCommit || editSaving.value) return
  const key = editingCellKey.value
  if (!key) return
  const [dateKey, destCd] = key.split('|')
  if (!dateKey || !destCd) {
    editingCellKey.value = null
    return
  }

  const raw = editDraft.value.trim()
  const clear = raw === ''
  const qty = clear ? null : Math.max(0, Math.floor(Number(raw) || 0))

  // 現在の手動値／表示値と比較
  let currentOverride: number | undefined
  let currentDisplay = 0
  for (const g of pageData.value.groups) {
    if (g.cell_overrides?.[dateKey]?.[destCd] !== undefined) {
      currentOverride = Number(g.cell_overrides[dateKey][destCd])
    }
    currentDisplay = Number(g.matrix?.[dateKey]?.[destCd] ?? 0)
  }

  if (clear && currentOverride === undefined) {
    editingCellKey.value = null
    editDraft.value = ''
    return
  }
  if (!clear && qty === currentDisplay && currentOverride === undefined) {
    editingCellKey.value = null
    editDraft.value = ''
    return
  }
  if (!clear && currentOverride !== undefined && qty === currentOverride) {
    editingCellKey.value = null
    editDraft.value = ''
    return
  }

  editSaving.value = true
  try {
    const res: any = await saveCellOverride(
      clear
        ? { shipping_date: dateKey, destination_cd: destCd, clear: true, qty: null }
        : { shipping_date: dateKey, destination_cd: destCd, qty: qty as number },
    )
    if (res?.success === false) {
      ElMessage.error(res?.message || 'セルの保存に失敗しました')
      return
    }
    editingCellKey.value = null
    editDraft.value = ''
    await fetchData()
    ElMessage.success(clear ? '手動修正を解除しました' : '保存しました')
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message || 'セルの保存に失敗しました')
  } finally {
    editSaving.value = false
  }
}

function tableRowClass({ row }: { row: TableRow }) {
  if (row.isTotal) return 'row-total'
  if (row.isWeekend) return 'row-weekend'
  return ''
}

function syncAdvanceDraft(groups: PalletCountGroupCard[]) {
  const next: Record<string, string> = {}
  const nextBin2: Record<string, boolean> = {}
  for (const g of groups) {
    if (g.enable_advance_tohoku) {
      for (const [ds, qty] of Object.entries(g.advance_qty || {})) {
        if (Number(qty) > 0) next[ds] = String(qty)
      }
    }
    if (g.enable_bin2) {
      for (const [ds, qty] of Object.entries(g.bin2_qty || {})) {
        if (Number(qty) > 0) nextBin2[ds] = true
      }
    }
  }
  advanceDraft.value = next
  bin2On.value = nextBin2
}

function buildTableRows(group: PalletCountGroupCard): TableRow[] {
  const tohokuCd = group.tohoku_destination_cd || ''
  const rows: TableRow[] = (group.dates || [])
    .filter((ds) => {
      const hasPallet = (group.row_totals?.[ds] ?? 0) > 0
      const hasAdvance = (group.advance_qty?.[ds] ?? 0) > 0
      const hasBin2 = (group.bin2_qty?.[ds] ?? 0) > 0
      const hasOverride = Object.keys(group.cell_overrides?.[ds] || {}).length > 0
      return hasPallet || hasAdvance || hasBin2 || hasOverride
    })
    .map((ds) => {
      const deduct = tohokuCd ? Number(group.tohoku_deduct_by_date?.[ds] || 0) : 0
      const row: TableRow = {
        dateLabel: formatDateLabel(ds),
        dateKey: ds,
        rowTotal: group.row_totals?.[ds] ?? 0,
        advanceQty: group.advance_qty?.[ds] ?? 0,
        bin2Qty: group.bin2_qty?.[ds] ?? 0,
        isWeekend: isWeekendYmd(ds),
      }
      for (const dest of group.destinations) {
        row[`d_${dest.cd}`] = group.matrix?.[ds]?.[dest.cd] ?? 0
      }
      if (deduct > 0 && tohokuCd && !isOverridden(group, ds, tohokuCd)) {
        row.deductHints = {
          [tohokuCd]: `先出により −${deduct}`,
        }
      }
      return row
    })

  if (group.destinations.length > 0) {
    const totalRow: TableRow = {
      dateLabel: '合計',
      rowTotal: group.grand_total,
      advanceQty: group.advance_total ?? 0,
      bin2Qty: group.bin2_total ?? 0,
      isTotal: true,
    }
    for (const dest of group.destinations) {
      totalRow[`d_${dest.cd}`] = group.col_totals?.[dest.cd] ?? 0
    }
    rows.push(totalRow)
  }
  return rows
}

function onAdvanceInput(dateKey: string, raw: string) {
  const cleaned = String(raw ?? '').replace(/[^\d]/g, '')
  if (!cleaned) {
    const { [dateKey]: _, ...rest } = advanceDraft.value
    advanceDraft.value = rest
    return
  }
  advanceDraft.value = { ...advanceDraft.value, [dateKey]: cleaned }
}

async function saveAdvance(dateKey: string) {
  if (!dateKey || savingDates.value.has(dateKey)) return
  const raw = advanceDraft.value[dateKey]
  const qty = raw === undefined || raw === '' ? 0 : Math.max(0, Math.floor(Number(raw) || 0))

  const owari = pageData.value.groups.find((g) => g.enable_advance_tohoku)
  const serverQty = Number(owari?.advance_qty?.[dateKey] || 0)
  if (qty === serverQty) {
    if (qty <= 0) {
      const { [dateKey]: _, ...rest } = advanceDraft.value
      advanceDraft.value = rest
    }
    return
  }

  savingDates.value = new Set(savingDates.value).add(dateKey)
  try {
    const res: any = await saveAdvanceTohoku({ advance_date: dateKey, qty })
    if (res?.success === false) {
      ElMessage.error(res?.message || '先出の保存に失敗しました')
      return
    }
    if (qty > 0) {
      advanceDraft.value = { ...advanceDraft.value, [dateKey]: String(qty) }
    } else {
      const { [dateKey]: _, ...rest } = advanceDraft.value
      advanceDraft.value = rest
    }
    await fetchData()
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message || '先出の保存に失敗しました')
  } finally {
    const next = new Set(savingDates.value)
    next.delete(dateKey)
    savingDates.value = next
  }
}

async function toggleBin2(dateKey: string) {
  if (!dateKey || savingBin2Dates.value.has(dateKey)) return
  const nextOn = !isBin2On(dateKey)
  const qty = nextOn ? 1 : 0

  savingBin2Dates.value = new Set(savingBin2Dates.value).add(dateKey)
  const prev = { ...bin2On.value }
  bin2On.value = { ...bin2On.value, [dateKey]: nextOn }

  try {
    const res: any = await saveBin2({ shipping_date: dateKey, qty })
    if (res?.success === false) {
      bin2On.value = prev
      ElMessage.error(res?.message || '2便の保存に失敗しました')
      return
    }
    await fetchData()
  } catch (e: any) {
    bin2On.value = prev
    console.error(e)
    ElMessage.error(e?.message || '2便の保存に失敗しました')
  } finally {
    const next = new Set(savingBin2Dates.value)
    next.delete(dateKey)
    savingBin2Dates.value = next
  }
}

function setThisMonth() {
  selectedMonth.value = currentMonthStr()
  fetchData()
}

function adjustMonth(delta: number) {
  const base = selectedMonth.value || currentMonthStr()
  const [ys, ms] = base.split('-').map(Number)
  const d = new Date(ys, ms - 1 + delta, 1)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  selectedMonth.value = `${y}-${m}`
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const params: { start_date?: string; end_date?: string; page_key: string } = {
      page_key: 'destination_groups_list',
    }
    const bounds = monthBounds(selectedMonth.value || currentMonthStr())
    if (bounds) {
      params.start_date = bounds.start
      params.end_date = bounds.end
    }
    const res: any = await getPalletCountMatrix(params)
    const payload = res?.data ?? res
    const data = payload?.data ?? payload
    if (!data || res?.success === false) {
      ElMessage.error(res?.message || '集計に失敗しました')
      return
    }
    const groups = Array.isArray(data.groups) ? data.groups : []
    pageData.value = {
      dates: data.dates || [],
      groups,
      grand_total: Number(data.grand_total || 0),
    }
    syncAdvanceDraft(groups)
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message || '集計に失敗しました')
  } finally {
    loading.value = false
  }
}

function handleGroupsUpdated() {
  fetchData()
}

function buildAdvancePrintHtml(sheets: AdvancePrintSheet[]): string {
  const pages = sheets
    .map((s) => {
      const name = s.destination_name || '(株)東北INOAC小牛田'
      const title = name.includes('御中') ? name : `${name} 御中`
      return `
      <section class="a5-sheet">
        <table class="a5-table" cellspacing="0" cellpadding="0">
          <tr class="row-title">
            <td colspan="3" class="cell-title">${escapeHtml(title)}</td>
          </tr>
          <tr class="row-compare">
            <td class="cell-portion">${escapeHtml(s.shipping_portion_label)}</td>
            <td class="cell-arrow">→</td>
            <td class="cell-advance">${escapeHtml(s.advance_label)}</td>
          </tr>
          <tr class="row-main">
            <td class="cell-label">出荷日</td>
            <td colspan="2" class="cell-value">${escapeHtml(s.shipping_date_label)}</td>
          </tr>
          <tr class="row-main">
            <td class="cell-label">納入日</td>
            <td colspan="2" class="cell-value">${escapeHtml(s.delivery_date_label)}</td>
          </tr>
        </table>
      </section>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>先出(東北)印刷</title>
  <style>
    @page {
      size: A5 landscape;
      margin: 21mm;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      width: 100%;
      height: 100%;
      background: #fff;
      color: #111;
      font-family: "Yu Gothic", "YuGothic", "Meiryo", "Hiragino Kaku Gothic ProN", "MS PGothic", sans-serif;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .a5-sheet {
      width: 100%;
      height: calc(148mm - 42mm);
      page-break-after: always;
      break-after: page;
      display: flex;
      align-items: stretch;
    }
    .a5-sheet:last-child {
      page-break-after: auto;
      break-after: auto;
    }
    .a5-table {
      width: 100%;
      height: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      border: 2.5px solid #111;
    }
    .a5-table td {
      border: 1px solid #9ca3af;
      vertical-align: middle;
      text-align: center;
      font-weight: 700;
    }
    .row-title .cell-title {
      height: 18%;
      font-size: 30px;
      font-weight: 800;
      letter-spacing: 0.08em;
      border-bottom: 1.5px solid #6b7280;
      padding: 4px 8px;
    }
    .row-compare {
      height: 16%;
    }
    .row-compare td {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 0.04em;
      padding: 4px 6px;
    }
    .cell-portion {
      width: 42%;
    }
    .cell-arrow {
      width: 10%;
      font-size: 26px !important;
      font-weight: 900 !important;
    }
    .cell-advance {
      width: 48%;
      background: #ffff00 !important;
      font-weight: 800;
    }
    .row-main {
      height: 33%;
    }
    .row-main .cell-label {
      width: 42%;
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 0.12em;
      padding: 6px 8px;
    }
    .row-main .cell-value {
      width: 58%;
      font-size: 42px;
      font-weight: 800;
      letter-spacing: 0.06em;
      padding: 6px 10px;
      white-space: nowrap;
    }
    @media print {
      .a5-sheet {
        height: calc(148mm - 42mm);
      }
    }
  </style>
</head>
<body>
${pages}
</body>
</html>`
}

function escapeHtml(s: string): string {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function openPrintWindow(html: string, successMsg?: string, options?: { fitOnePage?: boolean }) {
  const win = window.open('', '_blank')
  if (!win) {
    ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください。')
    return false
  }
  win.document.open()
  win.document.write(html)
  win.document.close()
  win.focus()
  setTimeout(() => {
    if (options?.fitOnePage) {
      try {
        const root = win.document.querySelector('.print-fit') as HTMLElement | null
        const shell = win.document.querySelector('.print-shell') as HTMLElement | null
        if (root && shell) {
          const mm = 96 / 25.4
          // A4 横・余白約 6mm の印字可能領域
          const availW = 285 * mm
          const availH = 198 * mm

          // 一旦等倍で実寸を測る
          root.style.transform = 'none'
          root.style.width = `${availW}px`
          shell.style.width = `${availW}px`
          shell.style.height = 'auto'
          shell.style.overflow = 'visible'

          const w = Math.max(root.scrollWidth, root.offsetWidth, 1)
          const h = Math.max(root.scrollHeight, root.offsetHeight, 1)
          // 幅いっぱいに合わせつつ、高さは1ページ内に収める（拡大も可）
          const scale = Math.min(availW / w, availH / h)

          root.style.transform = `scale(${scale})`
          root.style.transformOrigin = 'top left'
          root.style.width = `${availW / scale}px`
          shell.style.width = `${availW}px`
          shell.style.height = `${Math.ceil(h * scale)}px`
          shell.style.overflow = 'hidden'
        }
      } catch (e) {
        console.warn('print fit scale failed', e)
      }
    }
    win.print()
    win.close()
  }, 320)
  if (successMsg) ElMessage.success(successMsg)
  return true
}

function buildGroupPrintHtml(group: PalletCountGroupCard, start: string, end: string): string {
  const enableAdvance = !!group.enable_advance_tohoku && showAdvanceCol.value
  const enableBin2 = !!group.enable_bin2 && showBin2Col.value
  const rows = buildTableRows(group)
  const destCount = (group.destinations || []).length
  const compact = destCount >= 8
  const destHeaders = (group.destinations || [])
    .map(
      (d) =>
        `<th class="dest"><div class="dest-cd">${escapeHtml(d.cd)}</div><div class="dest-name">${escapeHtml(d.name)}</div></th>`,
    )
    .join('')
  const advanceTh = enableAdvance ? '<th class="advance">先出<br/>(東北)</th>' : ''
  const bin2Th = enableBin2 ? '<th class="bin2">2便</th>' : ''
  const body = rows
    .map((row) => {
      const cells = (group.destinations || [])
        .map((d) => `<td class="num">${escapeHtml(formatCell(row[`d_${d.cd}`]))}</td>`)
        .join('')
      const adv = enableAdvance
        ? `<td class="num advance">${escapeHtml(formatCell(row.advanceQty))}</td>`
        : ''
      const bin2 = enableBin2
        ? `<td class="num bin2">${escapeHtml(
            row.isTotal ? formatBin2Total(row.bin2Qty) : formatBin2Mark(row.bin2Qty),
          )}</td>`
        : ''
      const rowClass = row.isTotal ? ' class="row-sum"' : ''
      return `<tr${rowClass}><td class="date">${escapeHtml(row.dateLabel)}</td>${cells}${adv}${bin2}<td class="num total">${escapeHtml(formatCell(row.rowTotal))}</td></tr>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<title>出荷パレット数 ${escapeHtml(group.group_name)}</title>
<style>
@page {
  size: A4 landscape;
  margin: 6mm;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 297mm;
  min-height: 210mm;
  background: #fff;
  color: #0f172a;
  font-family: "Yu Gothic", "YuGothic", "Meiryo", "Hiragino Kaku Gothic ProN", sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
.print-shell {
  width: 100%;
  max-width: 285mm;
  max-height: 198mm;
  overflow: hidden;
  margin: 0 auto;
}
.print-fit {
  display: block;
  width: 100%;
  vertical-align: top;
}
h1 {
  margin: 0 0 4px;
  font-size: ${compact ? '25px' : '28px'};
  font-weight: 800;
  line-height: 1.25;
}
.meta {
  color: #64748b;
  margin-bottom: 8px;
  font-size: ${compact ? '16px' : '18px'};
  line-height: 1.35;
}
table {
  width: 100% !important;
  border-collapse: collapse;
  table-layout: fixed;
  border: 1.2px solid #334155;
  page-break-inside: avoid;
  break-inside: avoid;
}
thead { display: table-header-group; }
tr, th, td {
  page-break-inside: avoid;
  break-inside: avoid;
}
th, td {
  border: 1px solid #94a3b8;
  padding: ${compact ? '5px 3px' : '7px 5px'};
  text-align: center;
  vertical-align: middle;
  word-break: break-word;
  line-height: 1.84;
}
th {
  background: #f1f5f9;
  font-weight: 700;
  font-size: ${compact ? '15px' : '16px'};
}
th.date-col { width: ${compact ? '7%' : '8%'}; min-width: 56px; }
th.advance { width: 5%; min-width: 48px; font-size: 15px; }
th.bin2 { width: 3.5%; min-width: 36px; }
th.total-col { width: ${compact ? '4.5%' : '5%'}; min-width: 40px; }
th.dest { width: auto; }
th.advance, td.advance { background: #fff7ed; color: #9a3412; }
th.bin2, td.bin2 { background: #f0fdf4; color: #166534; font-size: 21px; font-weight: 800; }
th.total-col, td.total { background: #eff6ff; font-weight: 700; color: #1d4ed8; }
.dest-cd { font-size: ${compact ? '13px' : '15px'}; color: #94a3b8; font-weight: 600; }
.dest-name {
  font-size: ${compact ? '13px' : '16px'};
  font-weight: 700;
  color: #334155;
}
td.date {
  font-weight: 700;
  white-space: nowrap;
  background: #f8fafc;
  font-size: ${compact ? '15px' : '16px'};
}
td.num {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  font-size: ${compact ? '15px' : '16px'};
}
tr.row-sum td { background: #e0f2fe; font-weight: 800; }
@media print {
  html, body {
    width: auto;
    min-height: auto;
    overflow: hidden !important;
  }
  .print-shell, .print-fit, table {
    page-break-after: avoid;
    page-break-inside: avoid;
    break-after: avoid;
    break-inside: avoid;
  }
}
</style>
</head>
<body>
  <div class="print-shell">
    <div class="print-fit">
      <h1>出荷パレット数 — ${escapeHtml(group.group_name)}</h1>
      <div class="meta">積込期間: ${escapeHtml(start)} 〜 ${escapeHtml(end)} ／ 合計パレット: ${Number(group.grand_total || 0).toLocaleString()}</div>
      <table>
        <thead>
          <tr>
            <th class="date-col">積込日</th>
            ${destHeaders}
            ${advanceTh}
            ${bin2Th}
            <th class="total-col">合計</th>
          </tr>
        </thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  </div>
</body>
</html>`
}

function printGroupTable(group: PalletCountGroupCard) {
  const bounds = monthBounds(selectedMonth.value || currentMonthStr())
  if (!bounds) {
    ElMessage.warning('積込月を選択してください')
    return
  }
  if (!group.destinations?.length) {
    ElMessage.warning('印刷対象の納入先がありません')
    return
  }
  const html = buildGroupPrintHtml(group, bounds.start, bounds.end)
  openPrintWindow(html, `「${group.group_name}」を印刷します`, { fitOnePage: true })
}

async function loadMailUsers() {
  mailUsersLoading.value = true
  try {
    const res: any = await getUsers({ page: 1, page_size: 500, status: 'active' })
    const payload = res?.data ?? res
    const items = payload?.items ?? payload?.data?.items ?? []
    mailUsers.value = Array.isArray(items) ? items : []
  } catch (e) {
    console.error(e)
    mailUsers.value = []
    ElMessage.warning('ユーザー一覧の取得に失敗しました')
  } finally {
    mailUsersLoading.value = false
  }
}

async function openMailDialog(group: PalletCountGroupCard) {
  const bounds = monthBounds(selectedMonth.value || currentMonthStr())
  if (!bounds) {
    ElMessage.warning('積込月を選択してください')
    return
  }
  mailGroupName.value = group.group_name
  mailSubject.value = `【出荷パレット数】${group.group_name}（${bounds.start}〜${bounds.end}）`
  mailToEmails.value = []
  mailDialogVisible.value = true
  if (!mailUsers.value.length) {
    await loadMailUsers()
  }
}

async function sendGroupMail() {
  if (mailSending.value) return
  const bounds = monthBounds(selectedMonth.value || currentMonthStr())
  if (!bounds) {
    ElMessage.warning('積込月を選択してください')
    return
  }
  const emails = mailToEmails.value
    .map((e) => String(e || '').trim())
    .filter(Boolean)
  if (!emails.length) {
    ElMessage.warning('送信先ユーザーを選択してください')
    return
  }

  mailSending.value = true
  try {
    const res: any = await sendPalletCountMail({
      start_date: bounds.start,
      end_date: bounds.end,
      group_name: mailGroupName.value,
      to_emails: emails,
      subject: mailSubject.value.trim() || undefined,
    })
    if (res?.success === false) {
      ElMessage.error(res?.message || 'メール送信に失敗しました')
      return
    }
    ElMessage.success(res?.message || 'メールを送信しました')
    mailDialogVisible.value = false
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message || e?.response?.data?.detail || 'メール送信に失敗しました')
  } finally {
    mailSending.value = false
  }
}

async function printAdvanceSheets() {
  if (advancePrintLoading.value) return
  const bounds = monthBounds(selectedMonth.value || currentMonthStr())
  if (!bounds) {
    ElMessage.warning('積込月を選択してください')
    return
  }
  advancePrintLoading.value = true
  try {
    const res: any = await getAdvancePrintSheets({
      start_date: bounds.start,
      end_date: bounds.end,
    })
    const payload = res?.data ?? res
    const data = payload?.data ?? payload
    const sheets: AdvancePrintSheet[] = Array.isArray(data?.sheets) ? data.sheets : []
    if (!sheets.length) {
      ElMessage.warning('印刷対象の先出データがありません')
      return
    }
    const html = buildAdvancePrintHtml(sheets)
    openPrintWindow(html, `${sheets.length}枚を印刷します`)
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message || '先出印刷に失敗しました')
  } finally {
    advancePrintLoading.value = false
  }
}

onMounted(() => {
  selectedMonth.value = currentMonthStr()
  fetchData()
})
</script>

<style scoped>
.pallet-count-page {
  --ink: #0f172a;
  --muted: #64748b;
  --line: rgba(15, 23, 42, 0.08);
  --glass: rgba(255, 255, 255, 0.78);
  --glass-soft: rgba(255, 255, 255, 0.62);
  --accent: #0ea5e9;
  --accent-deep: #0284c7;
  --advance: #d97706;
  --tohoku: #ea580c;
  --total: #2563eb;
  --weekend: #e11d48;
  --ok: #0d9488;
  position: relative;
  min-height: 100%;
  padding: 18px 20px 28px;
  color: var(--ink);
  overflow: hidden;
}

.page-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: linear-gradient(165deg, #e8f4ff 0%, #f1f5f9 42%, #ecfeff 100%);
  pointer-events: none;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(48px);
  opacity: 0.55;
}

.orb-a {
  width: 360px;
  height: 360px;
  top: -120px;
  right: -60px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.35), transparent 70%);
  animation: floaty 16s ease-in-out infinite;
}

.orb-b {
  width: 280px;
  height: 280px;
  bottom: 10%;
  left: -80px;
  background: radial-gradient(circle, rgba(13, 148, 136, 0.22), transparent 70%);
  animation: floaty 18s ease-in-out infinite reverse;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(15, 23, 42, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 23, 42, 0.03) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.35), transparent 85%);
}

@keyframes floaty {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-12px, 16px);
  }
}

.page-inner {
  position: relative;
  z-index: 1;
  max-width: 1480px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.glass {
  background: var(--glass);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 10px 28px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(14px);
}

.glass-soft {
  background: var(--glass-soft);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(10px);
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 16px;
  flex-wrap: wrap;
}

.hero-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.hero-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #0ea5e9, #0369a1);
  box-shadow: 0 8px 18px rgba(2, 132, 199, 0.28);
  flex-shrink: 0;
}

.hero-eyebrow {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-deep);
  font-weight: 700;
}

.hero-title {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.hero-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.hero-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-ghost {
  border-radius: 10px;
  border-color: rgba(14, 165, 233, 0.25);
  background: rgba(255, 255, 255, 0.7);
  color: var(--ink);
}

.btn-primary {
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  box-shadow: 0 6px 16px rgba(2, 132, 199, 0.25);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 14px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.month-picker {
  width: 140px;
}

.month-quick {
  display: inline-flex;
  gap: 6px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.85);
  color: var(--ink);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    transform 0.15s ease;
}

.chip:hover {
  border-color: rgba(14, 165, 233, 0.45);
  transform: translateY(-1px);
}

.chip-active {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.16), rgba(2, 132, 199, 0.1));
  border-color: rgba(14, 165, 233, 0.45);
  color: var(--accent-deep);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.dot-date {
  background: #64748b;
}
.dot-advance {
  background: var(--advance);
}

.dot-bin2 {
  background: #16a34a;
}
.dot-tohoku {
  background: var(--tohoku);
}
.dot-edit {
  background: #7c3aed;
}
.dot-total {
  background: var(--total);
}

.legend-hint {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.kpi-card {
  border-radius: 14px;
  padding: 12px 14px;
  position: relative;
  overflow: hidden;
  animation: rise 0.35s ease both;
}

.kpi-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.kpi-groups::before {
  background: #0d9488;
}
.kpi-days::before {
  background: #0284c7;
}
.kpi-dest::before {
  background: #7c3aed;
}
.kpi-pallets::before {
  background: #ea580c;
}

.kpi-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.02em;
}

.kpi-value {
  margin-top: 4px;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.kpi-groups .kpi-value {
  color: #0f766e;
}
.kpi-days .kpi-value {
  color: #0369a1;
}
.kpi-dest .kpi-value {
  color: #6d28d9;
}
.kpi-pallets .kpi-value {
  color: #c2410c;
}

.cards-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 140px;
}

.empty-panel {
  border-radius: 16px;
  padding: 28px 12px;
}

.group-card {
  position: relative;
  border-radius: 16px;
  padding: 12px 12px 12px 14px;
  overflow: hidden;
  animation: rise 0.4s ease both;
}

.group-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
}

.tone-0 .group-accent {
  background: linear-gradient(180deg, #0ea5e9, #0284c7);
}
.tone-1 .group-accent {
  background: linear-gradient(180deg, #14b8a6, #0d9488);
}
.tone-2 .group-accent {
  background: linear-gradient(180deg, #f59e0b, #d97706);
}
.tone-3 .group-accent {
  background: linear-gradient(180deg, #6366f1, #4f46e5);
}
.tone-4 .group-accent {
  background: linear-gradient(180deg, #f43f5e, #e11d48);
}

.tone-0 {
  --tone: #0284c7;
}
.tone-1 {
  --tone: #0d9488;
}
.tone-2 {
  --tone: #d97706;
}
.tone-3 {
  --tone: #4f46e5;
}
.tone-4 {
  --tone: #e11d48;
}

.group-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding-left: 4px;
  flex-wrap: wrap;
}

.group-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
}

.group-badge {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  color: #fff;
  background: var(--tone, #0284c7);
  box-shadow: 0 6px 14px color-mix(in srgb, var(--tone, #0284c7) 35%, transparent);
  flex-shrink: 0;
}

.group-heading {
  min-width: 0;
}

.group-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--ink);
  letter-spacing: -0.01em;
}

.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  background: rgba(148, 163, 184, 0.16);
}

.meta-advance {
  color: #92400e;
  background: rgba(245, 158, 11, 0.16);
}

.group-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.btn-advance-print,
.btn-group-action {
  border-radius: 10px;
  font-weight: 700;
}

.owari-side-toggle {
  margin-right: 2px;
}

.owari-side-toggle :deep(.el-radio-button__inner) {
  font-weight: 700;
  padding: 6px 10px;
}

.mail-dlg-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.mail-dlg-title {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
}

.mail-dlg-sub {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
}

.group-total-block {
  text-align: right;
  padding: 6px 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(14, 165, 233, 0.1));
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.group-total-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: var(--muted);
}

.group-total-value {
  display: block;
  margin-top: 2px;
  font-size: 22px;
  font-weight: 800;
  color: var(--total);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
}

.group-empty {
  padding: 18px;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}

.table-wrap {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(255, 255, 255, 0.72);
}

.dest-header {
  line-height: 1.15;
  white-space: normal;
  padding: 2px 0;
}

.dest-cd {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 600;
}

.dest-name {
  font-size: 11px;
  color: #334155;
  font-weight: 700;
}

.date-cell {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  font-variant-numeric: tabular-nums;
}

.date-cell.is-weekend {
  color: var(--weekend);
}

.date-cell.is-total {
  color: var(--total);
}

.cell-value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 12px;
  color: #1e293b;
}

.cell-value.is-deducted {
  color: var(--tohoku);
  background: rgba(234, 88, 12, 0.1);
  border-radius: 6px;
  padding: 1px 6px;
}

.cell-value.is-overridden {
  color: #6d28d9;
  background: rgba(124, 58, 237, 0.12);
  border-radius: 6px;
  padding: 1px 6px;
  box-shadow: inset 0 0 0 1px rgba(124, 58, 237, 0.25);
}

.cell-edit-wrap {
  min-height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: cell;
  border-radius: 6px;
  transition: background 0.12s ease;
}

.cell-edit-wrap:hover:not(.editing) {
  background: rgba(14, 165, 233, 0.08);
}

.cell-edit-wrap.overridden:not(.editing) {
  background: rgba(124, 58, 237, 0.06);
}

.cell-edit-input {
  width: 64px;
}

.cell-edit-input :deep(.el-input__wrapper) {
  padding: 0 4px;
  border-radius: 8px;
  background: rgba(124, 58, 237, 0.08);
  box-shadow: 0 0 0 1px rgba(124, 58, 237, 0.35) inset;
}

.cell-edit-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 12px;
  height: 24px;
  line-height: 24px;
  font-weight: 700;
  color: #5b21b6;
}

.cell-value.is-row-total,
.cell-value.is-total {
  color: var(--total);
}

.cell-value.is-advance-total {
  color: var(--advance);
}

.cell-value.is-bin2-total {
  color: #16a34a;
}

.advance-input {
  width: 76px;
}

.advance-input :deep(.el-input__wrapper) {
  padding: 0 4px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.12);
  box-shadow: 0 0 0 1px rgba(217, 119, 6, 0.25) inset;
}

.advance-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 12px;
  height: 24px;
  line-height: 24px;
  color: #92400e;
  font-weight: 700;
}

.bin2-toggle {
  width: 36px;
  height: 28px;
  margin: 0 auto;
  padding: 0;
  border-radius: 8px;
  border: 1.5px solid rgba(22, 163, 74, 0.35);
  background: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.bin2-toggle:hover:not(:disabled) {
  border-color: #16a34a;
  background: rgba(22, 163, 74, 0.08);
}

.bin2-toggle.is-on {
  background: rgba(22, 163, 74, 0.16);
  border-color: #16a34a;
  box-shadow: 0 0 0 1px rgba(22, 163, 74, 0.2) inset;
}

.bin2-toggle.is-saving,
.bin2-toggle:disabled {
  opacity: 0.55;
  cursor: wait;
}

.bin2-mark {
  font-size: 16px;
  font-weight: 800;
  color: #166534;
  line-height: 1;
}

.matrix-table {
  --el-table-border-color: rgba(148, 163, 184, 0.28);
  --el-table-header-bg-color: #f8fafc;
}

.matrix-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  padding: 6px 2px;
  color: #475569;
  font-weight: 700;
}

.matrix-table :deep(.el-table__cell) {
  padding: 4px 2px;
}

.matrix-table :deep(.el-table__body td) {
  height: 30px;
}

.matrix-table :deep(.cell) {
  padding: 0 3px;
  line-height: 1.2;
}

.matrix-table :deep(td.col-date) {
  background: rgba(100, 116, 139, 0.04);
}

.matrix-table :deep(td.tohoku-col) {
  background: rgba(234, 88, 12, 0.06);
}

.matrix-table :deep(th.tohoku-col) {
  background: rgba(234, 88, 12, 0.1) !important;
  color: #9a3412 !important;
}

.matrix-table :deep(td.col-advance),
.matrix-table :deep(th.col-advance) {
  background: rgba(245, 158, 11, 0.1) !important;
}

.matrix-table :deep(th.col-advance) {
  color: #92400e !important;
}

.matrix-table :deep(td.col-bin2),
.matrix-table :deep(th.col-bin2) {
  background: rgba(22, 163, 74, 0.1) !important;
}

.matrix-table :deep(th.col-bin2) {
  color: #166534 !important;
}

.matrix-table :deep(td.col-total),
.matrix-table :deep(th.col-total) {
  background: rgba(37, 99, 235, 0.08) !important;
}

.matrix-table :deep(th.col-total) {
  color: #1d4ed8 !important;
}

.matrix-table :deep(tr.row-weekend > td) {
  background: rgba(244, 63, 94, 0.03);
}

.matrix-table :deep(tr.row-total > td) {
  background: rgba(37, 99, 235, 0.07) !important;
  font-weight: 800;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 960px) {
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .pallet-count-page {
    padding: 12px;
  }
  .hero-title {
    font-size: 18px;
  }
  .kpi-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
