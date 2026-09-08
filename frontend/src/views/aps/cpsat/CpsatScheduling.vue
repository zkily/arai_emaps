<template>
  <div class="cpsat-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">
        <span class="plan-hd-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path
              d="M12 2a1 1 0 0 1 .9.55l1.52 3.08 3.4.5a1 1 0 0 1 .55 1.7l-2.46 2.4.58 3.38a1 1 0 0 1-1.45 1.05L12 13.48l-3.04 1.6a1 1 0 0 1-1.45-1.05l.58-3.38-2.46-2.4a1 1 0 0 1 .55-1.7l3.4-.5L11.1 2.55A1 1 0 0 1 12 2Zm-7 14.5A1.5 1.5 0 0 1 6.5 15h11a1.5 1.5 0 0 1 0 3h-11A1.5 1.5 0 0 1 5 16.5ZM7.5 20A1.5 1.5 0 0 1 9 18.5h6a1.5 1.5 0 0 1 0 3H9A1.5 1.5 0 0 1 7.5 20Z"
            />
          </svg>
        </span>
        <span class="plan-hd-text-wrap">
          <span class="plan-hd-title-text">CP-SAT 最適化ボード</span>
          <span class="plan-hd-sub">日受注は製品CD末尾を1にそろえ、同一交期の日合計を製品マスタのロットサイズで分割します（1ロット=1ジョブ）。求解は会社カレンダーと設備の稼働時間帯を守ります。</span>
        </span>
      </h2>
    </div>

    <section class="plan-card condition-card">
      <div class="card-head condition-head">
        <div>
          <div class="card-kicker">条件マスタ</div>
          <p class="card-note">求解に使う稼働日・設備・ルート等を編集します（変更後はこの画面に戻り、再展開／再求解してください）。</p>
        </div>
      </div>
      <div class="condition-btns">
        <button
          v-for="item in conditionLinks"
          :key="item.path"
          type="button"
          class="condition-btn"
          @click="openCondition(item.path)"
        >
          <span class="condition-btn__title">{{ item.title }}</span>
          <span class="condition-btn__desc">{{ item.desc }}</span>
        </button>
      </div>
    </section>

    <div class="cpsat-top">
      <section class="plan-card filter-card">
        <div class="card-kicker">1. 展開条件</div>
        <el-form :model="form" label-position="top" class="expand-form" @submit.prevent="runExpandAndSolve">
          <el-form-item label="交期">
            <el-date-picker
              v-model="form.dateRange"
              type="daterange"
              unlink-panels
              range-separator="〜"
              start-placeholder="開始"
              end-placeholder="終了"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="製品（空欄は全製品・末尾は1に正規化）">
            <el-select
              v-model="form.productCds"
              multiple
              filterable
              clearable
              collapse-tags
              collapse-tags-tooltip
              placeholder="例: 90011"
              :loading="productsLoading"
              style="width: 100%"
            >
              <el-option
                v-for="p in productOptions"
                :key="p.product_cd"
                :label="`${p.product_cd}  ${p.product_name || ''}`"
                :value="p.product_cd"
              />
            </el-select>
          </el-form-item>
          <div class="form-row">
            <el-form-item label="数量">
              <el-select v-model="form.qtySource" style="width: 100%">
                <el-option label="確定" value="confirmed" />
                <el-option label="内示" value="forecast" />
                <el-option label="確定→内示" value="confirmed_or_forecast" />
              </el-select>
            </el-form-item>
            <el-form-item label="目的">
              <el-select v-model="form.objectiveType" style="width: 100%">
                <el-option label="納期遅れ最小" value="tardiness" />
                <el-option label="メイクスパン最小" value="makespan" />
                <el-option label="加重" value="weighted" />
              </el-select>
            </el-form-item>
          </div>
          <div class="form-row">
            <el-form-item label="最大ジョブ">
              <el-input-number v-model="form.maxJobs" :min="1" :max="2000" :step="10" controls-position="right" style="width: 100%" />
            </el-form-item>
            <el-form-item label="求解上限(秒)">
              <el-input-number v-model="form.maxSolveSeconds" :min="1" :max="600" :step="5" controls-position="right" style="width: 100%" />
            </el-form-item>
          </div>
          <div class="action-row">
            <el-button type="primary" :loading="busy" :disabled="!canExpand" @click="runExpandAndSolve">
              展開して求解
            </el-button>
            <el-button :loading="expanding" :disabled="!canExpand" @click="runExpandOnly">展開のみ</el-button>
            <el-button :loading="solving" :disabled="!selectedRunId" @click="runSolveSelected">再求解</el-button>
          </div>
        </el-form>
      </section>

      <section class="plan-card history-card">
        <div class="card-head">
          <div>
            <div class="card-kicker">2. 実行履歴</div>
            <p class="card-note">クリックで結果を表示。×で削除。最新が左です。</p>
          </div>
          <el-button text :loading="runsLoading" @click="loadRuns">更新</el-button>
        </div>
        <div v-loading="runsLoading" class="run-strip">
          <div
            v-for="run in runs"
            :key="run.id"
            class="run-chip"
            :class="{ 'is-active': run.id === selectedRunId, [`is-${run.status}`]: true }"
            role="button"
            tabindex="0"
            @click="selectRun(run.id)"
            @keydown.enter.prevent="selectRun(run.id)"
          >
            <div class="run-chip__top">
              <span class="run-chip__code">{{ run.run_code || `RUN-${run.id}` }}</span>
              <button
                type="button"
                class="run-chip__del"
                title="削除"
                :disabled="deletingRunId === run.id || run.status === 'running'"
                @click.stop="confirmDeleteRun(run)"
              >
                ×
              </button>
            </div>
            <span class="run-chip__meta">
              {{ statusLabel(run.status) }} · {{ run.job_count }}件
            </span>
            <span class="run-chip__time">{{ formatShortDateTime(run.created_at) }}</span>
          </div>
          <div v-if="!runsLoading && runs.length === 0" class="empty-inline">まだ実行がありません。左の条件で展開してください。</div>
        </div>
      </section>
    </div>

    <div class="stat-grid">
      <div class="stat-card stat-card--status">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-label">ソルバ状態</span>
        <span class="stat-value">{{ currentRun ? solverLabel(currentRun) : '—' }}</span>
        <span class="stat-foot">{{ currentRun?.run_code || '未選択' }}</span>
      </div>
      <div class="stat-card stat-card--jobs">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-label">ジョブ / 工程</span>
        <span class="stat-value">{{ currentRun ? `${currentRun.job_count}` : '—' }}</span>
        <span class="stat-foot">{{ currentRun ? `${currentRun.operation_count} 工程` : '展開後に表示' }}</span>
      </div>
      <div class="stat-card stat-card--span">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-label">メイクスパン</span>
        <span class="stat-value">{{ currentRun?.makespan_sec != null ? formatDuration(currentRun.makespan_sec) : '—' }}</span>
        <span class="stat-foot">最終工程の完了までの時間</span>
      </div>
      <div class="stat-card stat-card--late">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-label">納期遅れ合計</span>
        <span class="stat-value">{{ currentRun?.total_tardiness_sec != null ? formatDuration(currentRun.total_tardiness_sec) : '—' }}</span>
        <span class="stat-foot">{{ lateJobCount }} 件が遅れ</span>
      </div>
      <div class="stat-card stat-card--time">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-label">求解時間</span>
        <span class="stat-value">{{ wallTimeLabel }}</span>
        <span class="stat-foot">会社カレンダー・稼働時間帯を考慮</span>
      </div>
    </div>

    <section v-if="warningChips.length" class="warn-row">
      <span v-for="chip in warningChips" :key="chip" class="warn-chip">{{ chip }}</span>
    </section>

    <section class="plan-card gantt-card" v-loading="jobsLoading">
      <div class="card-head">
        <div>
          <div class="card-kicker">3. 結果</div>
          <h3 class="gantt-title">{{ ganttTitle }}</h3>
          <p v-if="gantt.rangeLabel" class="card-note">{{ gantt.rangeLabel }}</p>
        </div>
        <div class="gantt-tools">
          <el-radio-group v-model="ganttMode" size="small">
            <el-radio-button value="machine">設備ガント</el-radio-button>
            <el-radio-button value="job">ジョブ工程</el-radio-button>
          </el-radio-group>
          <el-radio-group v-model="ganttScale" size="small">
            <el-radio-button value="fit">全体</el-radio-button>
            <el-radio-button value="hour">1時間</el-radio-button>
            <el-radio-button value="detail">詳細</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div v-if="processLegend.length" class="legend">
        <span v-for="item in processLegend" :key="item.code" class="legend-item">
          <i class="legend-dot" :style="{ background: item.color }" />
          {{ item.label }}
        </span>
        <span class="legend-item">
          <i class="legend-swatch legend-swatch--night" />
          夜間 22–6時（求解では非稼働帯に置けません）
        </span>
        <span class="legend-item">
          <i class="legend-swatch legend-swatch--due" />
          納期
        </span>
      </div>

      <div v-if="gantt.rows.length === 0" class="empty-gantt">
        <p v-if="!currentRun">実行を選ぶか、展開して求解するとガントチャートが表示されます。</p>
        <p v-else-if="currentRun.status === 'running'">求解中です。完了後に自動で表示されます。</p>
        <p v-else-if="currentRun.status === 'draft'">まだ求解されていません。「再求解」を押してください。</p>
        <p v-else-if="currentRun.status === 'infeasible'">
          実行不能です。稼働日・時間帯が足りないか、工程が設備に載りません。条件を見直して再求解してください。
        </p>
        <p v-else-if="currentRun.status === 'error' || currentRun.status === 'failed'">
          求解に失敗しました。{{ currentRun.error_message || '再求解を試してください。' }}
        </p>
        <p v-else-if="isSolvedStatus(currentRun.status)">割当済みの工程がありません。</p>
        <p v-else>まだ求解されていません。「再求解」を押してください。</p>
      </div>

      <div v-else class="gantt-layout">
        <div class="gantt-scroll">
        <div class="gantt" :style="gantt.minWidth ? { minWidth: gantt.minWidth + 'px' } : undefined">
          <div class="gantt-axis">
            <div class="gantt-axis__label" />
            <div class="gantt-axis__track">
              <span
                v-for="band in gantt.nightBands"
                :key="band.key"
                class="gantt-night"
                :style="{ left: band.leftPct + '%', width: band.widthPct + '%' }"
              />
              <span v-for="tick in gantt.ticks" :key="tick.key" class="gantt-tick" :style="{ left: tick.leftPct + '%' }">
                {{ tick.label }}
              </span>
            </div>
          </div>
          <div
            v-for="row in gantt.rows"
            :key="row.key"
            class="gantt-row"
            :class="{
              'is-dim': highlightedJobId != null && !row.hasHighlight && row.kind === 'item',
              'gantt-row--process': row.kind === 'process',
            }"
          >
            <div class="gantt-row__label" :title="row.label">
              <i
                v-if="row.kind === 'process' && row.color"
                class="legend-dot"
                :style="{ background: row.color }"
              />
              <b>{{ row.label }}</b>
              <span v-if="row.subLabel">{{ row.subLabel }}</span>
            </div>
            <div class="gantt-row__track">
              <span
                v-for="band in gantt.nightBands"
                :key="band.key"
                class="gantt-night"
                :style="{ left: band.leftPct + '%', width: band.widthPct + '%' }"
              />
              <span
                v-if="row.dueLeftPct != null"
                class="gantt-due"
                :style="{ left: row.dueLeftPct + '%' }"
                title="納期"
              />
              <button
                v-for="bar in row.bars"
                :key="bar.key"
                type="button"
                class="gantt-bar"
                :class="{ 'is-late': bar.isLate, 'is-active': bar.jobId === highlightedJobId }"
                :style="{
                  left: bar.leftPct + '%',
                  width: bar.widthPct + '%',
                  background: bar.color,
                }"
                @mouseenter="showTip($event, bar)"
                @mousemove="moveTip"
                @mouseleave="hideTip"
                @click="toggleJob(bar.jobId)"
              >
                <span v-if="bar.widthPct >= 8 || ganttScale !== 'fit'" class="gantt-bar__text">{{ bar.shortLabel }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <aside v-if="selectedJob" class="job-detail">
        <div class="job-detail__head">
          <div>
            <div class="card-kicker">選択ジョブ</div>
            <h4>{{ selectedJob.product_cd }}  {{ lotLabel(selectedJob) }}</h4>
            <p>{{ selectedJob.product_name || '—' }}</p>
          </div>
          <el-button text @click="highlightedJobId = null">閉じる</el-button>
        </div>
        <div class="job-detail__kpis">
          <span>投入 {{ formatQty(selectedJob.q_start) }} → 出来 {{ formatQty(selectedJob.q_target) }}{{ lotSizeHint(selectedJob) }}</span>
          <span>納期 {{ formatShortDateTime(selectedJob.due_at) }}</span>
          <span :class="selectedJob.tardiness_sec ? 'late-text' : 'ok-text'">
            {{ selectedJob.tardiness_sec ? `遅れ ${formatDuration(selectedJob.tardiness_sec)}` : '定時' }}
          </span>
        </div>
        <ol class="job-timeline">
          <li v-for="op in selectedJob.operations || []" :key="op.id">
            <i class="job-timeline__dot" :style="{ background: processColor(op.process_cd) }" />
            <div>
              <strong>{{ op.process_name || op.process_cd }}</strong>
              <p>{{ machineLabel(op) }}</p>
              <p>{{ formatClockRange(op.start_at, op.end_at) }}</p>
              <p>投入 {{ formatQty(op.q_input) }} → 出来 {{ formatQty(op.q_output) }} · 歩留 {{ op.yield_percent }}%</p>
              <div v-if="op.candidates?.length" class="cand-row">
                <span
                  v-for="c in op.candidates"
                  :key="c.id"
                  class="cand-chip"
                  :class="{ 'is-on': c.is_assigned }"
                >
                  {{ c.machine_name || c.machine_cd }}
                </span>
              </div>
            </div>
          </li>
        </ol>
      </aside>
      </div>
    </section>

    <section class="plan-card table-card" v-loading="jobsLoading">
      <div class="card-head">
        <h3 class="gantt-title">ジョブ一覧</h3>
        <div class="table-tools">
          <el-input v-model="jobQuery" clearable placeholder="製品CD / 名称" style="width: 200px" />
          <el-checkbox v-model="onlyLate">遅れのみ</el-checkbox>
          <span class="table-count">{{ visibleJobs.length }} / {{ jobs.length }} 件</span>
        </div>
      </div>
      <el-table
        :data="visibleJobs"
        stripe
        border
        size="small"
        row-key="id"
        :row-class-name="jobRowClass"
        :expand-row-keys="expandedJobIds"
        max-height="520"
        @row-click="onJobRowClick"
        @expand-change="onExpandChange"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="op-chain">
              <div v-for="(op, idx) in row.operations || []" :key="op.id" class="op-step">
                <div class="op-pill" :style="{ borderColor: processColor(op.process_cd), color: processColor(op.process_cd) }">
                  <strong>{{ op.process_name || op.process_cd }}</strong>
                  <span>{{ machineLabel(op) }}</span>
                  <span>{{ formatClockRange(op.start_at, op.end_at) }}</span>
                  <span>投入 {{ formatQty(op.q_input) }} → 出来 {{ formatQty(op.q_output) }}</span>
                </div>
                <span v-if="idx < (row.operations || []).length - 1" class="op-arrow">→</span>
              </div>
              <div v-if="!(row.operations || []).length" class="empty-inline">工程がありません。</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="job_index" label="#" width="56" />
        <el-table-column label="ロット" width="88">
          <template #default="{ row }">{{ lotLabel(row) }}</template>
        </el-table-column>
        <el-table-column label="製品" min-width="180">
          <template #default="{ row }">
            <div class="prod-cell">
              <b>{{ row.product_cd }}</b>
              <span>{{ row.product_name || '' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="160">
          <template #default="{ row }">
            {{ formatQty(row.q_start) }} → {{ formatQty(row.q_target) }}{{ lotSizeHint(row) }}
          </template>
        </el-table-column>
        <el-table-column label="納期" width="150">
          <template #default="{ row }">{{ formatShortDateTime(row.due_at) }}</template>
        </el-table-column>
        <el-table-column label="完了" width="150">
          <template #default="{ row }">
            {{ lastOpEnd(row) }}
          </template>
        </el-table-column>
        <el-table-column label="遅れ" width="110">
          <template #default="{ row }">
            <span :class="row.tardiness_sec ? 'late-text' : 'ok-text'">
              {{ row.tardiness_sec ? formatDuration(row.tardiness_sec) : '定時' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状態" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.incomplete" type="warning" size="small" effect="light">候補不足</el-tag>
            <el-tag v-else-if="hasSchedule(row)" type="success" size="small" effect="light">割当済</el-tag>
            <el-tag v-else type="info" size="small" effect="light">未求解</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <Teleport to="body">
      <div v-if="tip.visible" class="cpsat-tip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }">
        <div class="cpsat-tip__title">{{ tip.title }}</div>
        <div class="cpsat-tip__line">{{ tip.machine }}</div>
        <div class="cpsat-tip__line">{{ tip.time }}</div>
        <div class="cpsat-tip__line">{{ tip.qty }}</div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProductList } from '@/api/master/productMaster'
import {
  deleteCpsatRun,
  expandCpsatRun,
  getCpsatJob,
  listCpsatJobs,
  listCpsatRuns,
  solveCpsatRun,
  type CpsatJob,
  type CpsatOperation,
  type CpsatRun,
  type ObjectiveType,
  type QtySource,
} from '@/api/cpsat'
import type { Product } from '@/types/master'

defineOptions({ name: 'CpsatScheduling' })

const router = useRouter()

const conditionLinks = [
  {
    title: '稼働日',
    desc: '会社稼働カレンダー',
    path: '/master/company-work-calendar',
  },
  {
    title: '設備稼働',
    desc: '日別時間帯・稼働時間',
    path: '/aps/capacity',
  },
  {
    title: '稼働時間表',
    desc: '設備カレンダー一覧',
    path: '/aps/capacity-matrix',
  },
  {
    title: '設備マスタ',
    desc: 'CP-SAT対象・標準時間',
    path: '/master/machine',
  },
  {
    title: '製品ルート',
    desc: '歩留・待ち・候補機',
    path: '/master/product-process-route',
  },
  {
    title: '工程ルート',
    desc: '工程テンプレ・待ち',
    path: '/master/process-route',
  },
  {
    title: '製品マスタ',
    desc: 'ロットサイズ',
    path: '/master/product',
  },
] as const

function openCondition(path: string) {
  router.push(path)
}

const PROCESS_COLORS: Record<string, string> = {
  KT01: '#2563eb',
  KT02: '#0d9488',
  KT04: '#7c3aed',
  KT05: '#d97706',
  KT07: '#e11d48',
  KT09: '#16a34a',
}

const FALLBACK_COLORS = ['#64748b', '#0284c7', '#9333ea', '#c2410c', '#0f766e', '#be185d']

const form = reactive({
  dateRange: ['2026-09-01', '2026-09-14'] as [string, string] | [],
  productCds: ['90011'] as string[],
  qtySource: 'confirmed' as QtySource,
  objectiveType: 'tardiness' as ObjectiveType,
  maxJobs: 50,
  maxSolveSeconds: 30,
})

const productsLoading = ref(false)
const productOptions = ref<Product[]>([])
const runsLoading = ref(false)
const jobsLoading = ref(false)
const expanding = ref(false)
const solving = ref(false)
const deletingRunId = ref<number | null>(null)
const runs = ref<CpsatRun[]>([])
const currentRun = ref<CpsatRun | null>(null)
const jobs = ref<CpsatJob[]>([])
const selectedRunId = ref<number | null>(null)
const highlightedJobId = ref<number | null>(null)
const ganttMode = ref<'machine' | 'job'>('machine')
const ganttScale = ref<'fit' | 'hour' | 'detail'>('hour')
const jobQuery = ref('')
const onlyLate = ref(false)
const detailJob = ref<CpsatJob | null>(null)

const tip = reactive({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  machine: '',
  time: '',
  qty: '',
})

const busy = computed(() => expanding.value || solving.value)
const canExpand = computed(() => Array.isArray(form.dateRange) && form.dateRange.length === 2)
const expandedJobIds = computed(() => (highlightedJobId.value != null ? [highlightedJobId.value] : []))

const visibleJobs = computed(() => {
  const q = jobQuery.value.trim().toLowerCase()
  return jobs.value.filter((j) => {
    if (onlyLate.value && !(j.tardiness_sec && j.tardiness_sec > 0)) return false
    if (!q) return true
    const hay = `${j.product_cd} ${j.product_name || ''} ${j.order_no || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

const selectedJob = computed(() => {
  if (highlightedJobId.value == null) return null
  return detailJob.value?.id === highlightedJobId.value
    ? detailJob.value
    : visibleJobs.value.find((j) => j.id === highlightedJobId.value) ||
        jobs.value.find((j) => j.id === highlightedJobId.value) ||
        null
})

const lateJobCount = computed(() => jobs.value.filter((j) => (j.tardiness_sec || 0) > 0).length)

const wallTimeLabel = computed(() => {
  const sec = currentRun.value?.wall_time_sec
  if (sec == null) return '—'
  if (sec < 1) return `${Math.round(sec * 1000)} ms`
  return `${sec.toFixed(2)} 秒`
})

interface GanttBar {
  key: string
  jobId: number
  productCd: string
  processCd: string
  processName: string
  machineCd: string
  machineName: string
  startMs: number
  endMs: number
  startAt: string
  endAt: string
  leftPct: number
  widthPct: number
  color: string
  shortLabel: string
  isLate: boolean
  qInput: number
  qOutput: number
}

interface GanttRow {
  key: string
  kind: 'process' | 'item'
  label: string
  subLabel: string
  bars: GanttBar[]
  hasHighlight: boolean
  dueLeftPct: number | null
  processCd?: string
  color?: string
  sortIndex?: number
}

interface GanttTick {
  key: string
  label: string
  leftPct: number
}

interface NightBand {
  key: string
  leftPct: number
  widthPct: number
}

const scheduledOps = computed(() => {
  const out: Array<{ job: CpsatJob; op: CpsatOperation; startMs: number; endMs: number }> = []
  for (const job of jobs.value) {
    for (const op of job.operations || []) {
      if (!op.start_at || !op.end_at || !op.assigned_machine_cd) continue
      const startMs = Date.parse(op.start_at)
      const endMs = Date.parse(op.end_at)
      if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs <= startMs) continue
      out.push({ job, op, startMs, endMs })
    }
  }
  return out
})

const gantt = computed(() => {
  const items = scheduledOps.value
  const empty = { rows: [] as GanttRow[], ticks: [] as GanttTick[], nightBands: [] as NightBand[], rangeLabel: '', minWidth: 0 }
  if (!items.length) return empty
  let minMs = Math.min(...items.map((x) => x.startMs))
  let maxMs = Math.max(...items.map((x) => x.endMs))
  const pad = Math.max(60_000, Math.round((maxMs - minMs) * 0.04))
  minMs -= pad
  maxMs += pad
  const span = Math.max(maxMs - minMs, 1)
  const pxPerHour = ganttScale.value === 'hour' ? 88 : ganttScale.value === 'detail' ? 160 : 0
  const minWidth = pxPerHour ? Math.round(132 + (span / 3_600_000) * pxPerHour) : 0

  const toBar = (job: CpsatJob, op: CpsatOperation, startMs: number, endMs: number): GanttBar => {
    const leftPct = ((startMs - minMs) / span) * 100
    const widthPct = Math.max(((endMs - startMs) / span) * 100, 0.45)
    const machineName = op.assigned_machine_name || op.assigned_machine_cd || ''
    return {
      key: `${job.id}-${op.id}`,
      jobId: job.id,
      productCd: job.product_cd,
      processCd: op.process_cd,
      processName: op.process_name || op.process_cd,
      machineCd: op.assigned_machine_cd || '',
      machineName,
      startMs,
      endMs,
      startAt: op.start_at || '',
      endAt: op.end_at || '',
      leftPct,
      widthPct,
      color: processColor(op.process_cd),
      shortLabel:
        ganttMode.value === 'machine'
          ? `${job.product_cd} ${lotLabel(job)} ${op.process_name || op.process_cd}`
          : op.process_name || op.process_cd,
      isLate: (job.tardiness_sec || 0) > 0,
      qInput: op.q_input,
      qOutput: op.q_output,
    }
  }

  const processRank = new Map<string, number>()
  const processName = new Map<string, string>()
  for (const job of jobs.value) {
    for (const op of job.operations || []) {
      const rank = Number(op.op_index || op.step_no || 99)
      const prev = processRank.get(op.process_cd)
      if (prev == null || rank < prev) processRank.set(op.process_cd, rank)
      if (!processName.has(op.process_cd)) processName.set(op.process_cd, op.process_name || op.process_cd)
    }
  }

  const groups = new Map<string, GanttBar[]>()
  const groupMeta = new Map<string, { processCd: string; machineName: string; job?: CpsatJob; op?: CpsatOperation }>()
  for (const item of items) {
    const key = ganttMode.value === 'machine' ? item.op.assigned_machine_cd || '—' : String(item.job.id)
    if (!groups.has(key)) {
      groups.set(key, [])
      groupMeta.set(key, {
        processCd: item.op.process_cd,
        machineName: item.op.assigned_machine_name || '',
        job: item.job,
        op: item.op,
      })
    }
    groups.get(key)!.push(toBar(item.job, item.op, item.startMs, item.endMs))
    const meta = groupMeta.get(key)!
    if (ganttMode.value === 'machine') {
      const curRank = processRank.get(item.op.process_cd) ?? 99
      const prevRank = processRank.get(meta.processCd) ?? 99
      if (curRank < prevRank) meta.processCd = item.op.process_cd
    }
  }

  const itemRows: GanttRow[] = [...groups.entries()].map(([key, bars]) => {
    bars.sort((a, b) => a.startMs - b.startMs)
    const meta = groupMeta.get(key)
    const job = meta?.job
    const dueMs = job?.due_at ? Date.parse(job.due_at) : NaN
    const dueLeftPct =
      Number.isFinite(dueMs) && dueMs >= minMs && dueMs <= maxMs ? ((dueMs - minMs) / span) * 100 : null
    const machineName = meta?.machineName || ''
    const machineCd = meta?.op?.assigned_machine_cd || key
    return {
      key,
      kind: 'item' as const,
      processCd: meta?.processCd,
      label:
        ganttMode.value === 'machine'
          ? machineCd
          : `${job?.product_cd || ''}  ${job ? lotLabel(job) : ''}`,
      subLabel:
        ganttMode.value === 'machine'
          ? machineName && machineName !== machineCd
            ? machineName
            : processName.get(meta?.processCd || '') || ''
          : job?.product_name || '',
      bars,
      hasHighlight: highlightedJobId.value == null || bars.some((b) => b.jobId === highlightedJobId.value),
      dueLeftPct: ganttMode.value === 'job' ? dueLeftPct : null,
      sortIndex: job?.job_index,
    }
  })

  itemRows.sort((a, b) => {
    if (ganttMode.value === 'machine') {
      const ra = processRank.get(a.processCd || '') ?? 999
      const rb = processRank.get(b.processCd || '') ?? 999
      if (ra !== rb) return ra - rb
      return a.label.localeCompare(b.label, 'ja')
    }
    const ia = a.sortIndex ?? 0
    const ib = b.sortIndex ?? 0
    if (ia !== ib) return ia - ib
    return a.label.localeCompare(b.label, 'ja')
  })

  const rows: GanttRow[] = []
  if (ganttMode.value === 'machine') {
    let lastProc = ''
    for (const row of itemRows) {
      const proc = row.processCd || ''
      if (proc && proc !== lastProc) {
        lastProc = proc
        rows.push({
          key: `proc-${proc}`,
          kind: 'process',
          processCd: proc,
          color: processColor(proc),
          label: processName.get(proc) || proc,
          subLabel: proc,
          bars: [],
          hasHighlight: true,
          dueLeftPct: null,
        })
      }
      rows.push(row)
    }
  } else {
    rows.push(...itemRows)
  }

  const tickCount = Math.max(5, Math.min(pxPerHour ? Math.round(span / 3_600_000) + 1 : span > 36 * 3_600_000 ? 7 : 9, 16))
  const ticks: GanttTick[] = []
  for (let i = 0; i < tickCount; i++) {
    const t = minMs + (span * i) / Math.max(tickCount - 1, 1)
    ticks.push({
      key: `t-${i}`,
      label: formatAxis(t, span),
      leftPct: (i / Math.max(tickCount - 1, 1)) * 100,
    })
  }

  const nightBands: NightBand[] = []
  const hourMs = 3_600_000
  const startHour = Math.floor(minMs / hourMs) * hourMs
  for (let t = startHour; t < maxMs; t += hourMs) {
    const hour = jstHour(t)
    if (hour < 6 || hour >= 22) {
      const left = Math.max(0, ((t - minMs) / span) * 100)
      const right = Math.min(100, ((t + hourMs - minMs) / span) * 100)
      if (right > left) {
        nightBands.push({ key: `n-${t}`, leftPct: left, widthPct: right - left })
      }
    }
  }

  return {
    rows,
    ticks,
    nightBands,
    rangeLabel: `${formatAxis(minMs, span)} 〜 ${formatAxis(maxMs, span)}`,
    minWidth,
  }
})

const ganttTitle = computed(() => {
  if (!currentRun.value) return 'ガントチャート'
  return ganttMode.value === 'machine' ? '設備ガントチャート' : 'ジョブ工程チャート'
})

const processLegend = computed(() => {
  const seen = new Map<string, { name: string; rank: number }>()
  for (const job of jobs.value) {
    for (const op of job.operations || []) {
      const rank = Number(op.op_index || op.step_no || 99)
      const prev = seen.get(op.process_cd)
      if (!prev || rank < prev.rank) {
        seen.set(op.process_cd, { name: op.process_name || op.process_cd, rank })
      }
    }
  }
  return [...seen.entries()]
    .sort((a, b) => a[1].rank - b[1].rank || a[0].localeCompare(b[0], 'ja'))
    .map(([code, info]) => ({
      code,
      label: info.name,
      color: processColor(code),
    }))
})

const warningChips = computed(() => {
  const w = currentRun.value?.warnings
  if (!w) return []
  const chips: string[] = []
  if (w.skipped_no_qty) chips.push(`数量なし ${w.skipped_no_qty}`)
  if (w.skipped_no_due) chips.push(`納期なし ${w.skipped_no_due}`)
  if (w.skipped_no_route) chips.push(`ルートなし ${w.skipped_no_route}`)
  if (w.skipped_no_ops) chips.push(`工程なし ${w.skipped_no_ops}`)
  if (w.incomplete_no_machine) chips.push(`候補機なし ${w.incomplete_no_machine}`)
  if (w.incomplete_zero_ptime) chips.push(`加工時間0 ${w.incomplete_zero_ptime}`)
  return chips
})

function jstHour(ms: number): number {
  const raw = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Tokyo',
    hour: 'numeric',
    hourCycle: 'h23',
  }).format(new Date(ms))
  const hour = Number.parseInt(raw, 10)
  return Number.isFinite(hour) ? hour : 0
}

function machineLabel(op: CpsatOperation): string {
  if (!op.assigned_machine_cd) return '未割当'
  if (op.assigned_machine_name && op.assigned_machine_name !== op.assigned_machine_cd) {
    return `${op.assigned_machine_cd}  ${op.assigned_machine_name}`
  }
  return op.assigned_machine_cd
}

function processColor(code: string): string {
  if (PROCESS_COLORS[code]) return PROCESS_COLORS[code]
  let hash = 0
  for (let i = 0; i < code.length; i++) hash = (hash * 31 + code.charCodeAt(i)) >>> 0
  return FALLBACK_COLORS[hash % FALLBACK_COLORS.length]
}

function isSolvedStatus(status?: string | null): boolean {
  return status === 'optimal' || status === 'feasible' || status === 'solved'
}

function statusLabel(status: string): string {
  if (status === 'solved' || status === 'optimal') return '最適解'
  if (status === 'feasible') return '実行可能解'
  if (status === 'draft') return '展開済'
  if (status === 'running') return '求解中'
  if (status === 'infeasible') return '実行不能'
  if (status === 'failed' || status === 'error') return '失敗'
  return status || '—'
}

function solverLabel(run: CpsatRun): string {
  if (run.solver_status) return run.solver_status
  return statusLabel(run.status)
}

function formatDuration(sec: number | null | undefined): string {
  if (sec == null || Number.isNaN(sec)) return '—'
  const s = Math.max(0, Math.round(sec))
  if (s === 0) return '0秒'
  if (s < 60) return `${s}秒`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}分`
  const h = Math.floor(m / 60)
  const rm = m % 60
  if (h < 48) return rm ? `${h}時間${rm}分` : `${h}時間`
  const d = Math.floor(h / 24)
  const rh = h % 24
  return rh ? `${d}日${rh}時間` : `${d}日`
}

function formatQty(n: number | null | undefined): string {
  return Number(n || 0).toLocaleString('ja-JP')
}

function lotLabel(job: CpsatJob): string {
  const count = Number(job.lot_count || 0)
  const index = Number(job.lot_index || 0)
  if (count > 1 && index > 0) return `L${index}/${count}`
  if (index > 0 && Number(job.lot_size || 0) > 1) return `L${index}`
  return `#${job.job_index}`
}

function lotSizeHint(job: CpsatJob): string {
  const size = Number(job.lot_size || 0)
  return size > 1 ? ` / ロット${formatQty(size)}` : ''
}

function formatShortDateTime(value?: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatAxis(ms: number, spanMs: number): string {
  const d = new Date(ms)
  const opts: Intl.DateTimeFormatOptions =
    spanMs > 36 * 3600_000
      ? { timeZone: 'Asia/Tokyo', month: '2-digit', day: '2-digit', hour: '2-digit' }
      : { timeZone: 'Asia/Tokyo', hour: '2-digit', minute: '2-digit' }
  return d.toLocaleString('ja-JP', opts)
}

function formatClockRange(start?: string | null, end?: string | null): string {
  if (!start || !end) return '未割当'
  return `${formatShortDateTime(start)} 〜 ${formatShortDateTime(end)}`
}

function lastOpEnd(job: CpsatJob): string {
  const ops = job.operations || []
  const last = [...ops].reverse().find((op) => op.end_at)
  return last?.end_at ? formatShortDateTime(last.end_at) : '—'
}

function hasSchedule(job: CpsatJob): boolean {
  return (job.operations || []).some((op) => op.start_at && op.assigned_machine_cd)
}

function jobRowClass({ row }: { row: CpsatJob }): string {
  if (row.id === highlightedJobId.value) return 'job-row-active'
  if ((row.tardiness_sec || 0) > 0) return 'job-row-late'
  return ''
}

function onJobRowClick(row: CpsatJob) {
  toggleJob(row.id)
}

function onExpandChange(row: CpsatJob, expandedRows: CpsatJob[]) {
  highlightedJobId.value = expandedRows.some((r) => r.id === row.id) ? row.id : null
}

function toggleJob(jobId: number) {
  highlightedJobId.value = highlightedJobId.value === jobId ? null : jobId
}

function showTip(ev: MouseEvent, bar: GanttBar) {
  tip.visible = true
  tip.title = `${bar.productCd}  /  ${bar.processName}`
  tip.machine = `設備 ${bar.machineName || bar.machineCd}`
  tip.time = formatClockRange(bar.startAt, bar.endAt)
  tip.qty = `投入 ${formatQty(bar.qInput)} → 出来 ${formatQty(bar.qOutput)}`
  moveTip(ev)
}

function moveTip(ev: MouseEvent) {
  tip.x = ev.clientX + 14
  tip.y = ev.clientY + 16
}

function hideTip() {
  tip.visible = false
}

function expandPayload() {
  const [dueFrom, dueTo] = form.dateRange as [string, string]
  return {
    due_from: dueFrom,
    due_to: dueTo,
    product_cds: form.productCds.length ? form.productCds : null,
    qty_source: form.qtySource,
    max_jobs: form.maxJobs,
    name: form.productCds.length ? form.productCds.slice(0, 3).join(',') : '全製品',
  }
}

async function loadProducts() {
  productsLoading.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = (list as Product[])
      .filter((p) => p.product_cd)
      .sort((a, b) => String(a.product_cd).localeCompare(String(b.product_cd), 'ja'))
  } finally {
    productsLoading.value = false
  }
}

async function loadRuns() {
  runsLoading.value = true
  try {
    runs.value = await listCpsatRuns(40)
  } finally {
    runsLoading.value = false
  }
}

async function confirmDeleteRun(run: CpsatRun) {
  if (run.status === 'running') {
    ElMessage.warning('求解中の実行は削除できません')
    return
  }
  try {
    await ElMessageBox.confirm(
      `${run.run_code || `RUN-${run.id}`} を削除しますか？ジョブ・工程結果もまとめて消えます。`,
      '実行履歴の削除',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  deletingRunId.value = run.id
  try {
    await deleteCpsatRun(run.id)
    ElMessage.success('削除しました')
    if (selectedRunId.value === run.id) {
      selectedRunId.value = null
      currentRun.value = null
      jobs.value = []
      highlightedJobId.value = null
      detailJob.value = null
    }
    await loadRuns()
    if (!selectedRunId.value && runs.value.length) {
      await selectRun(runs.value[0].id)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '削除に失敗しました')
  } finally {
    deletingRunId.value = null
  }
}

async function selectRun(runId: number) {
  selectedRunId.value = runId
  highlightedJobId.value = null
  jobsLoading.value = true
  try {
    const [runList, jobList] = await Promise.all([listCpsatRuns(40), listCpsatJobs(runId, { limit: 500 })])
    runs.value = runList
    currentRun.value = runList.find((r) => r.id === runId) || null
    jobs.value = jobList
  } finally {
    jobsLoading.value = false
  }
}

async function runExpandOnly() {
  if (!canExpand.value) return
  expanding.value = true
  try {
    const run = await expandCpsatRun(expandPayload())
    ElMessage.success(`展開しました（${run.job_count} ジョブ）`)
    await selectRun(run.id)
  } finally {
    expanding.value = false
  }
}

async function runSolveSelected() {
  if (!selectedRunId.value) return
  solving.value = true
  try {
    const run = await solveCpsatRun(selectedRunId.value, {
      max_solve_seconds: form.maxSolveSeconds,
      objective_type: form.objectiveType,
    })
    ElMessage.success(run.solver_status === 'OPTIMAL' ? '最適解を得ました' : `求解完了（${run.solver_status || run.status}）`)
    await selectRun(run.id)
  } finally {
    solving.value = false
  }
}

async function runExpandAndSolve() {
  if (!canExpand.value) return
  expanding.value = true
  try {
    const run = await expandCpsatRun(expandPayload())
    selectedRunId.value = run.id
    solving.value = true
    expanding.value = false
    const solved = await solveCpsatRun(run.id, {
      max_solve_seconds: form.maxSolveSeconds,
      objective_type: form.objectiveType,
    })
    ElMessage.success(`求解完了：${solved.job_count} ジョブ / ${formatDuration(solved.makespan_sec)}`)
    await selectRun(solved.id)
  } finally {
    expanding.value = false
    solving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadProducts(), loadRuns()])
  if (runs.value.length) {
    await selectRun(runs.value[0].id)
  }
})

watch(highlightedJobId, async (id) => {
  if (!id || !selectedRunId.value) {
    detailJob.value = null
    return
  }
  const local = jobs.value.find((j) => j.id === id) || null
  detailJob.value = local
  try {
    const full = await getCpsatJob(selectedRunId.value, id)
    if (highlightedJobId.value === id) detailJob.value = full
  } catch {
    /* list payload is enough if detail fetch fails */
  }
})
</script>

<style scoped>
.cpsat-page {
  padding: 8px 4px 24px;
  background:
    radial-gradient(circle at -10% -20%, rgba(124, 58, 237, 0.1), transparent 32%),
    radial-gradient(circle at 110% -30%, rgba(37, 99, 235, 0.1), transparent 30%),
    #f3f6fb;
  min-height: 100%;
}

.plan-hd {
  margin-bottom: 8px;
  padding: 4px 2px 2px;
}

.plan-hd-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.2px;
  line-height: 1.1;
}

.plan-hd-text-wrap {
  display: inline-flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.plan-hd-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%);
  box-shadow:
    0 6px 14px rgba(124, 58, 237, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.plan-hd-icon svg {
  width: 15px;
  height: 15px;
  fill: #fff;
}

.plan-hd-sub {
  font-weight: 400;
  color: #5f6f86;
  font-size: 12px;
  line-height: 1.1;
}

.condition-card {
  margin-bottom: 10px;
  padding-bottom: 10px;
}

.condition-head {
  margin-bottom: 8px;
}

.condition-btns {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
  gap: 8px;
}

.condition-btn {
  text-align: left;
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-height: 62px;
  transition:
    transform 0.16s ease,
    box-shadow 0.16s ease,
    border-color 0.16s ease;
}

.condition-btn:hover {
  transform: translateY(-1px);
  border-color: #a78bfa;
  box-shadow: 0 8px 16px rgba(124, 58, 237, 0.1);
}

.condition-btn__title {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.condition-btn__desc {
  font-size: 11px;
  color: #64748b;
  line-height: 1.25;
}

.cpsat-top {
  display: grid;
  grid-template-columns: minmax(320px, 400px) 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.plan-card {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(3px);
  padding: 12px 14px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px rgba(15, 23, 42, 0.04);
}

.filter-card {
  border-color: rgba(196, 181, 253, 0.7);
  background:
    linear-gradient(135deg, rgba(245, 243, 255, 0.9) 0%, rgba(239, 246, 255, 0.82) 100%),
    rgba(255, 255, 255, 0.95);
}

.card-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #7c3aed;
  margin-bottom: 6px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.card-note {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.expand-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.expand-form :deep(.el-form-item__label) {
  font-size: 12px;
  color: #475569;
  margin-bottom: 2px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.run-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  min-height: 88px;
}

.run-chip {
  flex: 0 0 168px;
  text-align: left;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

.run-chip__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 6px;
}

.run-chip__del {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #94a3b8;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.run-chip__del:hover:not(:disabled) {
  background: #fee2e2;
  color: #be123c;
}

.run-chip__del:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.run-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.08);
}

.run-chip.is-active {
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.16);
}

.run-chip.is-solved,
.run-chip.is-optimal,
.run-chip.is-feasible {
  background: linear-gradient(180deg, #f5f3ff 0%, #fff 70%);
}

.run-chip__code {
  font-weight: 800;
  color: #0f172a;
  font-size: 12px;
}

.run-chip__meta,
.run-chip__time {
  color: #64748b;
  font-size: 11px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 12px 14px 13px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid rgba(255, 255, 255, 0.52);
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.28) 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.75) inset,
    0 12px 28px rgba(15, 23, 42, 0.08);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.stat-card__glow {
  position: absolute;
  top: -28px;
  right: -18px;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  opacity: 0.55;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 700;
}

.stat-value {
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.stat-foot {
  font-size: 11px;
  color: #94a3b8;
}

.stat-card--status::before,
.stat-card--status .stat-card__glow {
  background: #7c3aed;
}
.stat-card--jobs::before,
.stat-card--jobs .stat-card__glow {
  background: #2563eb;
}
.stat-card--span::before,
.stat-card--span .stat-card__glow {
  background: #0d9488;
}
.stat-card--late::before,
.stat-card--late .stat-card__glow {
  background: #e11d48;
}
.stat-card--time::before,
.stat-card--time .stat-card__glow {
  background: #d97706;
}

.warn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.warn-chip {
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
}

.gantt-card,
.table-card {
  margin-bottom: 10px;
}

.gantt-title {
  margin: 0;
  font-size: 15px;
  color: #0f172a;
}

.gantt-tools {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-bottom: 10px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #475569;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

.legend-swatch {
  width: 14px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}

.legend-swatch--night {
  background: rgba(15, 23, 42, 0.12);
  border: 1px solid #cbd5e1;
}

.legend-swatch--due {
  background: transparent;
  border-left: 2px dashed #e11d48;
  width: 8px;
}

.empty-gantt,
.empty-inline {
  color: #64748b;
  font-size: 13px;
  padding: 18px 8px;
}

.gantt-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.gantt-layout:has(.job-detail) {
  grid-template-columns: minmax(0, 1fr) 300px;
}

.gantt-scroll {
  overflow-x: auto;
  border-radius: 12px;
}

.gantt {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  min-width: 100%;
}

.gantt-axis,
.gantt-row {
  display: grid;
  grid-template-columns: 148px 1fr;
  min-height: 44px;
}

.gantt-axis {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  min-height: 32px;
}

.gantt-row {
  border-bottom: 1px solid #f1f5f9;
}

.gantt-row:nth-child(odd) {
  background: #fcfdff;
}

.gantt-row.is-dim {
  opacity: 0.38;
}

.gantt-row.gantt-row--process {
  min-height: 28px;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
}

.gantt-row--process .gantt-row__label {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 8px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #0f172a;
}

.gantt-row--process .gantt-row__label span {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
}

.gantt-row--process .gantt-row__track {
  min-height: 28px;
  background: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 6px,
    rgba(148, 163, 184, 0.08) 6px,
    rgba(148, 163, 184, 0.08) 7px
  );
}

.gantt-axis__label,
.gantt-row__label {
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  border-right: 1px solid #e2e8f0;
  overflow: hidden;
}

.gantt-row__label {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
  line-height: 1.2;
}

.gantt-row__label span {
  font-weight: 500;
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gantt-axis__track,
.gantt-row__track {
  position: relative;
  min-height: 44px;
}

.gantt-night {
  position: absolute;
  top: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.05);
  pointer-events: none;
}

.gantt-due {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 0;
  border-left: 2px dashed #e11d48;
  z-index: 3;
  pointer-events: none;
}

.gantt-tick {
  position: absolute;
  top: 8px;
  transform: translateX(-50%);
  font-size: 10px;
  color: #94a3b8;
  white-space: nowrap;
  z-index: 1;
}

.gantt-bar {
  position: absolute;
  top: 10px;
  height: 24px;
  border: 0;
  border-radius: 7px;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.16);
  overflow: hidden;
  z-index: 2;
}

.gantt-bar.is-active {
  outline: 2px solid #0f172a;
  outline-offset: 1px;
}

.gantt-bar.is-late {
  box-shadow: 0 0 0 1px rgba(225, 29, 72, 0.45), 0 4px 10px rgba(225, 29, 72, 0.2);
}

.gantt-bar__text {
  display: block;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 700;
  line-height: 24px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.job-detail {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  background: linear-gradient(180deg, #faf8ff 0%, #fff 40%);
  max-height: 560px;
  overflow: auto;
}

.job-detail__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.job-detail h4 {
  margin: 0;
  font-size: 15px;
  color: #0f172a;
}

.job-detail p {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 12px;
}

.job-detail__kpis {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 10px 0 0;
  font-size: 12px;
  color: #334155;
}

.job-timeline {
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
}

.job-timeline li {
  display: grid;
  grid-template-columns: 12px 1fr;
  gap: 8px;
  position: relative;
  padding-bottom: 12px;
}

.job-timeline li:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 12px;
  bottom: 0;
  width: 2px;
  background: #e2e8f0;
}

.job-timeline__dot {
  width: 10px;
  height: 10px;
  margin-top: 4px;
  border-radius: 999px;
  display: inline-block;
}

.job-timeline strong {
  font-size: 13px;
  color: #0f172a;
}

.cand-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.cand-chip {
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 1px 8px;
}

.cand-chip.is-on {
  background: #ede9fe;
  color: #6d28d9;
  font-weight: 700;
}

.table-tools {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.table-count {
  font-size: 12px;
  color: #64748b;
}

.prod-cell {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.prod-cell span {
  color: #64748b;
  font-size: 12px;
}

.late-text {
  color: #e11d48;
  font-weight: 700;
}

.ok-text {
  color: #0d9488;
}

.op-chain {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 8px 12px 12px 48px;
}

.op-step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.op-pill {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: #fff;
  border: 1px solid;
  border-radius: 10px;
  padding: 6px 10px;
  min-width: 140px;
  font-size: 11px;
  color: #475569;
}

.op-pill strong {
  font-size: 12px;
}

.op-arrow {
  color: #94a3b8;
  font-weight: 700;
}

:deep(.job-row-active td) {
  background: #f5f3ff !important;
}

:deep(.job-row-late td) {
  background: #fff7f8 !important;
}

@media (max-width: 1100px) {
  .cpsat-top,
  .stat-grid,
  .gantt-layout,
  .gantt-layout:has(.job-detail) {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
.cpsat-tip {
  position: fixed;
  z-index: 4000;
  pointer-events: none;
  min-width: 180px;
  max-width: 280px;
  background: #0f172a;
  color: #fff;
  border-radius: 10px;
  padding: 8px 10px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.28);
  font-size: 12px;
}

.cpsat-tip__title {
  font-weight: 800;
  margin-bottom: 4px;
}

.cpsat-tip__line {
  color: #cbd5e1;
}
</style>
