<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Monitor,
  Refresh,
  VideoPlay,
  VideoPause,
  CircleCheck,
  WarningFilled,
  Timer,
  DataLine,
  User,
  Coffee,
  Calendar,
  Goods,
  TrendCharts,
  FullScreen,
} from '@element-plus/icons-vue'
import {
  formatDuration,
  formatHistoryTime,
  formatHistoryTimeOnly,
  fmtMonitorEfficiency,
  fmtMonitorDefectRate,
  historyCardTitle,
  historyProductionQtyTotal,
  inspectorEfficiencyRankClass,
  isMonitorEfficiencyOutOfRange,
  processHistoryTitle,
  statusLabel,
  statusTagType,
} from './monitorHelpers'
import type { MonitorProcessKey } from './monitorTypes'
import { useProcessMonitor } from './useProcessMonitor'

const props = defineProps<{
  processKey: MonitorProcessKey
}>()

defineOptions({ name: 'ProcessMonitorPage' })

const { t } = useI18n()
const {
  config,
  intlLocale,
  productionDay,
  loading,
  autoRefresh,
  processSummary,
  overallStats,
  currentTime,
  lastFetchError,
  fullscreen,
  fetchAll,
  onDateChange,
  onAutoRefreshChange,
  toggleFullscreen,
  goToInspectionRegistration,
  hasInitialData,
  nextAssignDialogVisible,
  nextAssignSubmitting,
  nextAssignTarget,
  nextAssignProductCd,
  monitorProducts,
  loadingMonitorProducts,
  nextAssignPanelVisible,
  nextAssignPanelRows,
  nextAssignPanelActiveRows,
  nextAssignPanelIdleRows,
  nextAssignPanelBadgeCount,
  inspectionInspectorOptions,
  loadingInspectionInspectors,
  nextAssignPickInspector,
  nextAssignInspectorUserId,
  openNextAssignPanel,
  closeNextAssignPanel,
  openNextAssignDialogForRow,
  openNextAssignCreateDialog,
  closeNextAssignDialog,
  saveNextAssignment,
  clearNextAssignment,
  hasNextAssignmentForInspector,
} = useProcessMonitor(props.processKey)

const proc = processSummary

const nextAssignDialogInspectorUserId = computed(() => {
  if (nextAssignPickInspector.value) return nextAssignInspectorUserId.value
  return nextAssignTarget.value?.inspectorUserId ?? null
})
</script>

<template>
  <div
    class="monitor-page"
    :class="{
      'monitor-page--inspection': processKey === 'inspection',
      'monitor-page--fullscreen': fullscreen && processKey === 'inspection',
    }"
    v-loading="loading && !hasInitialData"
  >
    <div class="monitor-header">
      <div class="monitor-header__left">
        <span v-if="processKey === 'inspection'" class="monitor-header__brand" aria-hidden="true">
          <el-icon :size="22"><Monitor /></el-icon>
        </span>
        <el-icon v-else :size="26" :color="config.headerIconColor"><Monitor /></el-icon>
        <div class="monitor-header__titles">
          <h1 class="monitor-header__title">{{ config.pageTitle }}</h1>
        </div>
        <span class="monitor-header__clock">{{ currentTime }}</span>
        <span
          v-if="processKey === 'inspection' && lastFetchError"
          class="monitor-header__sync monitor-header__sync--error"
          :title="lastFetchError"
        >
          取得失敗
        </span>
      </div>
      <div class="monitor-header__right">
        <div
          v-if="processKey === 'inspection'"
          class="monitor-header__date-filter"
        >
          <label class="monitor-header__date-label" for="monitor-production-day">
            <span class="monitor-header__date-label-icon" aria-hidden="true">
              <el-icon :size="15"><Calendar /></el-icon>
            </span>
            <span class="monitor-header__date-label-text">{{ t('mesInspectionActual.productionDay') }}</span>
          </label>
          <el-date-picker
            id="monitor-production-day"
            v-model="productionDay"
            type="date"
            value-format="YYYY-MM-DD"
            size="small"
            class="monitor-header__date-picker"
            @change="onDateChange"
          />
        </div>
        <el-date-picker
          v-else
          v-model="productionDay"
          type="date"
          value-format="YYYY-MM-DD"
          size="small"
          style="width: 150px"
          @change="onDateChange"
        />
        <div v-if="processKey === 'inspection'" class="monitor-header__toolbar-divider" aria-hidden="true" />
        <el-switch
          v-model="autoRefresh"
          active-text="自動更新"
          size="small"
          :class="{ 'monitor-header__auto-switch': processKey === 'inspection' }"
          @change="onAutoRefreshChange"
        />
        <el-button
          v-if="processKey === 'inspection'"
          size="small"
          :icon="FullScreen"
          circle
          class="monitor-header__fullscreen-btn"
          :title="fullscreen ? '全画面解除' : '全画面'"
          @click="toggleFullscreen"
        />
        <el-button
          size="small"
          :icon="Refresh"
          circle
          class="monitor-header__refresh-btn"
          @click="fetchAll"
        />
      </div>
    </div>

    <div class="kpi-row" :class="{ 'kpi-row--inspection': processKey === 'inspection' }">
      <div class="kpi-card kpi-card--running">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--running">
          <el-icon :size="22"><VideoPlay /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalRunning }}</div>
          <div class="kpi-card__label">稼働中</div>
        </div>
      </div>
      <div class="kpi-card kpi-card--paused">
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--paused">
          <el-icon :size="22"><VideoPause /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalPaused }}</div>
          <div class="kpi-card__label">一時停止</div>
        </div>
      </div>
      <template v-if="processKey === 'inspection'">
        <div class="kpi-card kpi-card--break">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--break">
            <el-icon :size="22"><Coffee /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">{{ overallStats.totalBreak }}</div>
            <div class="kpi-card__label">休憩中</div>
          </div>
        </div>
        <div
          v-if="overallStats.totalCommStale > 0"
          class="kpi-card kpi-card--comm-stale"
        >
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--comm-stale">
            <el-icon :size="22"><WarningFilled /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">{{ overallStats.totalCommStale }}</div>
            <div class="kpi-card__label">通信断</div>
          </div>
        </div>
        <div
          class="kpi-card kpi-card--avg-efficiency"
          :class="{ 'kpi-card--eff-alert': isMonitorEfficiencyOutOfRange(overallStats.avgEfficiency) }"
        >
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--avg-efficiency">
            <el-icon :size="22"><TrendCharts /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">
              {{ fmtMonitorEfficiency(overallStats.avgEfficiency) }}<span
                v-if="overallStats.avgEfficiency != null"
                class="kpi-card__sub"
              >本/時</span>
            </div>
            <div class="kpi-card__label">平均能率</div>
          </div>
        </div>
        <div class="kpi-card kpi-card--production">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--production">
            <el-icon :size="22"><Goods /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">{{ overallStats.totalActual.toLocaleString() }}</div>
            <div class="kpi-card__label">生産数</div>
          </div>
        </div>
        <div v-if="overallStats.totalDefect > 0" class="kpi-card kpi-card--defect">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--defect">
            <el-icon :size="22"><WarningFilled /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">{{ overallStats.totalDefect }}</div>
            <div class="kpi-card__label">不良数</div>
          </div>
        </div>
        <div class="kpi-card kpi-card--defect-rate">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--defect-rate">
            <el-icon :size="22"><WarningFilled /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">
              {{ fmtMonitorDefectRate(overallStats.defectRatePercent) }}
            </div>
            <div class="kpi-card__label">不良率</div>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-card kpi-card--completed">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--completed">
            <el-icon :size="22"><CircleCheck /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">{{ overallStats.totalCompleted }}</div>
            <div class="kpi-card__label">完了</div>
          </div>
        </div>
        <div class="kpi-card kpi-card--waiting">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--waiting">
            <el-icon :size="22"><Timer /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">{{ overallStats.totalWaiting }}</div>
            <div class="kpi-card__label">待機中</div>
          </div>
        </div>
        <div class="kpi-card kpi-card--machines">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--machines">
            <el-icon :size="22"><DataLine /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">
              {{ overallStats.runningMachines
              }}<span class="kpi-card__sub">/{{ overallStats.totalMachines }}</span>
            </div>
            <div class="kpi-card__label">設備稼働</div>
          </div>
        </div>
        <div class="kpi-card kpi-card--rate">
          <div class="kpi-card__icon-wrap kpi-card__icon-wrap--rate">
            <el-icon :size="22"><DataLine /></el-icon>
          </div>
          <div class="kpi-card__body">
            <div class="kpi-card__value">
              {{ overallStats.completionRate }}<span class="kpi-card__sub">%</span>
            </div>
            <div class="kpi-card__label">完了率</div>
          </div>
        </div>
      </template>
      <div
        v-if="processKey !== 'inspection' && overallStats.totalDefect > 0"
        class="kpi-card kpi-card--defect"
      >
        <div class="kpi-card__icon-wrap kpi-card__icon-wrap--defect">
          <el-icon :size="22"><WarningFilled /></el-icon>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">{{ overallStats.totalDefect }}</div>
          <div class="kpi-card__label">不良数</div>
        </div>
      </div>
    </div>

    <div
      class="process-layout"
      :class="processKey === 'inspection' ? 'process-layout--inspection' : 'process-layout--single'"
    >
      <section
        class="process-section process-section--runtime"
        :class="{ 'inspection-runtime-panel': processKey === 'inspection' }"
      >
        <header v-if="processKey === 'inspection'" class="inspection-runtime-panel__head">
          <span class="inspection-runtime-panel__icon" aria-hidden="true">
            <el-icon :size="16"><Monitor /></el-icon>
          </span>
          <h3 class="inspection-runtime-panel__title">{{ proc.label }}</h3>
          <el-tooltip
            :content="t('mesInspectionActual.nextAssignmentAssign')"
            placement="top"
          >
            <button
              type="button"
              class="inspection-runtime-panel__next-btn"
              :aria-label="t('mesInspectionActual.nextAssignmentAssign')"
              @click="openNextAssignPanel"
            >
              <el-icon :size="16"><Goods /></el-icon>
              <span
                v-if="nextAssignPanelBadgeCount > 0"
                class="inspection-runtime-panel__next-badge"
              >{{ nextAssignPanelBadgeCount }}</span>
            </button>
          </el-tooltip>
          <span class="inspection-runtime-panel__head-spacer" aria-hidden="true" />
          <span class="inspection-runtime-panel__hint">本日</span>
          <span class="inspection-runtime-panel__count">{{ proc.machines.length }}</span>
        </header>
        <div v-else class="process-section__header" :style="{ background: proc.gradient }">
          <span class="process-section__icon">{{ proc.icon }}</span>
          <span class="process-section__name">{{ proc.label }}</span>
          <div class="process-section__badges">
            <el-tag size="small" type="success" effect="dark" v-if="proc.inProgressPlans > 0" round>
              稼働 {{ proc.inProgressPlans }}
            </el-tag>
            <el-tag size="small" type="warning" effect="dark" v-if="proc.pausedPlans > 0" round>
              停止 {{ proc.pausedPlans }}
            </el-tag>
            <el-tag size="small" type="primary" effect="dark" v-if="proc.breakPlans > 0" round>
              休憩 {{ proc.breakPlans }}
            </el-tag>
          </div>
        </div>

        <div class="machine-list" v-if="proc.machines.length > 0">
          <div
            v-for="machine in proc.machines"
            :key="machine.id != null ? `${proc.key}-${machine.id}` : machine.name"
            class="machine-card"
            :class="[
              'machine-card--' + machine.status,
              {
                'machine-card--comm-stale': processKey === 'inspection' && machine.commStale,
              },
            ]"
          >
            <div class="machine-card__top">
              <div class="machine-card__top-left">
                <span class="machine-card__name">{{ machine.name }}</span>
                <span
                  v-if="processKey === 'welding' && machine.currentProduct"
                  class="machine-card__product-inline"
                  :title="machine.currentProduct"
                >{{ machine.currentProduct }}</span>
                <span
                  v-if="
                    machine.elapsedSec > 0 ||
                    machine.status === 'paused' ||
                    machine.status === 'break'
                  "
                  class="machine-card__title-metrics"
                >
                  <span v-if="machine.elapsedSec > 0" class="machine-card__title-metric">
                    <span class="machine-card__title-metric-label">経過</span>
                    <span class="machine-card__title-metric-value machine-card__stat-value--time">{{
                      formatDuration(machine.elapsedSec)
                    }}</span>
                  </span>
                  <span v-if="machine.status === 'paused'" class="machine-card__title-metric">
                    <span class="machine-card__title-metric-label">一時停止</span>
                    <span class="machine-card__title-metric-value machine-card__stat-value--pause">
                      <template v-if="machine.pausedSec > 0">{{
                        formatDuration(machine.pausedSec)
                      }}</template>
                      <template v-else>—</template>
                    </span>
                  </span>
                  <span v-if="machine.status === 'break'" class="machine-card__title-metric">
                    <span class="machine-card__title-metric-label">休憩</span>
                    <span class="machine-card__title-metric-value machine-card__stat-value--break">
                      <template v-if="machine.breakSec > 0">{{
                        formatDuration(machine.breakSec)
                      }}</template>
                      <template v-else>—</template>
                    </span>
                  </span>
                  <span
                    v-if="processKey === 'inspection' && machine.commStale && machine.lastCommAt"
                    class="machine-card__title-metric machine-card__title-metric--comm-stale"
                  >
                    <span class="machine-card__title-metric-label">最終通信</span>
                    <span class="machine-card__title-metric-value">{{
                      formatHistoryTimeOnly(machine.lastCommAt, intlLocale)
                    }}</span>
                  </span>
                </span>
              </div>
              <div class="machine-card__top-right">
                <span
                  v-if="
                    machine.operatorName &&
                    (machine.status === 'running' ||
                      machine.status === 'paused' ||
                      machine.status === 'break')
                  "
                  class="machine-card__operator-inline"
                  :title="machine.operatorName"
                >
                  <el-icon :size="13"><User /></el-icon>
                  <span class="machine-card__operator-inline-name">{{ machine.operatorName }}</span>
                </span>
                <el-tag
                  v-if="processKey === 'inspection' && machine.commStale"
                  size="small"
                  type="danger"
                  effect="plain"
                  round
                  class="machine-card__comm-stale-tag"
                >
                  通信断
                </el-tag>
                <el-tag size="small" :type="statusTagType(machine.status)" effect="plain" round>
                  <span v-if="machine.status === 'running'" class="machine-card__pulse"></span>
                  {{ statusLabel(machine.status) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        <div
          v-else
          :class="
            processKey === 'inspection' ? 'inspection-runtime-panel__empty' : 'process-section__empty'
          "
        >
          <el-empty
            :description="
              processKey === 'inspection' && proc.totalPlans > 0
                ? '稼働中の検査はありません'
                : '本日の計画はありません'
            "
            :image-size="48"
          />
        </div>
      </section>

      <section
        v-if="processKey === 'inspection'"
        class="inspection-defect-panel"
      >
        <header class="inspection-defect-panel__head">
          <span class="inspection-defect-panel__icon" aria-hidden="true">
            <el-icon :size="16"><WarningFilled /></el-icon>
          </span>
          <h3 class="inspection-defect-panel__title">{{ t('mesInspectionActual.defectByItem') }}</h3>
          <span class="inspection-defect-panel__hint">本日</span>
          <span class="inspection-defect-panel__count">{{ proc.defectListRows?.length ?? 0 }}</span>
        </header>
        <div
          v-if="(proc.defectListRows?.length ?? 0) > 0"
          class="inspection-defect-table-wrap"
        >
          <el-table
            :data="proc.defectListRows ?? []"
            size="small"
            stripe
            class="inspection-defect-table"
            :empty-text="'不良なし'"
          >
            <el-table-column
              label="検査員"
              prop="inspectorName"
              class-name="inspection-defect-col--char7"
              label-class-name="inspection-defect-col--char7"
              show-overflow-tooltip
            />
            <el-table-column label="稼働状態" width="92" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="statusTagType(row.status)" effect="plain" round>
                  <span v-if="row.status === 'running'" class="machine-card__pulse"></span>
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="製品名"
              prop="productName"
              class-name="inspection-defect-col--product"
              label-class-name="inspection-defect-col--product"
              min-width="48"
              show-overflow-tooltip
            />
            <el-table-column
              label="不良項目"
              prop="defectItemLabel"
              class-name="inspection-defect-col--char7"
              label-class-name="inspection-defect-col--char7"
              show-overflow-tooltip
            />
            <el-table-column label="不良数" prop="defectQty" width="68" align="right">
              <template #default="{ row }">
                <span class="inspection-defect-table__qty">{{ row.defectQty.toLocaleString() }}</span>
              </template>
            </el-table-column>
            <el-table-column label="不良発生時刻" width="88" align="center">
              <template #default="{ row }">
                <span class="inspection-defect-table__time">{{
                  formatHistoryTimeOnly(row.defectOccurredAt, intlLocale)
                }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else class="inspection-defect-panel__empty">
          <el-empty description="本日の不良はありません" :image-size="48" />
        </div>
      </section>

      <section
        v-if="processKey === 'inspection'"
        class="inspection-efficiency-panel"
      >
        <header class="inspection-efficiency-panel__head">
          <span class="inspection-efficiency-panel__icon" aria-hidden="true">
            <el-icon :size="16"><User /></el-icon>
          </span>
          <h3 class="inspection-efficiency-panel__title">検査員能率</h3>
          <span class="inspection-efficiency-panel__hint">本日</span>
          <span
            v-if="proc.inspectorAvgEfficiency != null"
            class="inspection-efficiency-panel__avg"
            :class="{
              'inspection-efficiency-panel__avg--alert': isMonitorEfficiencyOutOfRange(
                proc.inspectorAvgEfficiency,
              ),
            }"
          >
            平均 {{ fmtMonitorEfficiency(proc.inspectorAvgEfficiency) }} 本/時
          </span>
          <span class="inspection-efficiency-panel__count">{{
            proc.inspectorEfficiencyRows?.length ?? 0
          }}</span>
        </header>
        <div
          v-if="(proc.inspectorEfficiencyRows?.length ?? 0) > 0"
          class="inspection-efficiency-table-wrap"
        >
          <el-table
            :data="proc.inspectorEfficiencyRows ?? []"
            size="small"
            stripe
            class="inspection-efficiency-table"
            :empty-text="'能率データなし'"
          >
            <el-table-column label="順位" width="52" align="center">
              <template #default="{ row }">
                <span
                  class="inspection-efficiency-rank"
                  :class="inspectorEfficiencyRankClass(row.rank)"
                >{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column label="検査員" prop="inspectorName" min-width="96" show-overflow-tooltip />
            <el-table-column label="件数" prop="sessionCount" width="52" align="right" />
            <el-table-column label="生産数" min-width="72" align="right">
              <template #default="{ row }">
                <span class="inspection-efficiency-table__qty">{{
                  row.sumActualQty.toLocaleString()
                }}</span>
              </template>
            </el-table-column>
            <el-table-column label="平均能率" width="88" align="right">
              <template #default="{ row }">
                <span
                  class="inspection-efficiency-table__eff"
                  :class="{
                    'inspection-efficiency-table__eff--alert': isMonitorEfficiencyOutOfRange(
                      row.efficiencyPerHour,
                    ),
                  }"
                >{{
                  fmtMonitorEfficiency(row.efficiencyPerHour)
                }}</span>
                <span class="inspection-efficiency-table__unit">本/時</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else class="inspection-efficiency-panel__empty">
          <el-empty description="本日の能率データはありません" :image-size="48" />
        </div>
      </section>

      <section v-if="proc.historyRows.length > 0" class="process-history-panel">
        <header class="process-history-panel__head">
          <span class="process-history-panel__icon" aria-hidden="true">
            <el-icon :size="16"><CircleCheck /></el-icon>
          </span>
          <h3 class="process-history-panel__title">{{ processHistoryTitle(processKey, t) }}</h3>
          <el-button
            v-if="processKey === 'inspection'"
            type="primary"
            link
            size="small"
            class="process-history-panel__link"
            @click="goToInspectionRegistration"
          >
            実績登録
          </el-button>
          <span class="process-history-panel__qty-total">
            <span class="process-history-panel__qty-total-label">{{
              t('mesWeldingActual.historyProductionQtyTotal')
            }}</span>
            <span class="process-history-panel__qty-total-value">{{
              historyProductionQtyTotal(proc.historyRows).toLocaleString()
            }}</span>
          </span>
          <span class="process-history-panel__count">{{ proc.historyRows.length }}</span>
        </header>
        <div class="history-card-list">
          <div
            v-for="row in proc.historyRows"
            :key="`${proc.key}-hist-${row.id}`"
            class="history-card"
            :class="{ 'history-card--clickable': processKey === 'inspection' }"
            :role="processKey === 'inspection' ? 'button' : undefined"
            :tabindex="processKey === 'inspection' ? 0 : undefined"
            @click="processKey === 'inspection' ? goToInspectionRegistration() : undefined"
            @keydown.enter="processKey === 'inspection' ? goToInspectionRegistration() : undefined"
          >
            <div class="history-card__top">
              <div class="history-card__top-left">
                <span class="history-card__name" :title="historyCardTitle(processKey, row)">{{
                  historyCardTitle(processKey, row)
                }}</span>
                <span v-if="row.elapsedSec > 0" class="history-card__title-metrics">
                  <span class="history-card__title-metric">
                    <span class="history-card__title-metric-label">経過</span>
                    <span
                      class="history-card__title-metric-value history-card__title-metric-value--time"
                    >{{ formatDuration(row.elapsedSec) }}</span>
                  </span>
                </span>
              </div>
              <div class="history-card__top-right">
                <span
                  v-if="row.operatorName && row.operatorName !== '—'"
                  class="history-card__operator-inline"
                  :title="row.operatorName"
                >
                  <el-icon :size="13"><User /></el-icon>
                  <span class="history-card__operator-inline-name">{{ row.operatorName }}</span>
                </span>
                <el-tag size="small" type="success" effect="plain" round>
                  {{ statusLabel('completed') }}
                </el-tag>
              </div>
            </div>
            <div class="history-card__stats">
              <span class="history-card__stat">
                <span class="history-card__stat-label">{{ t('mesWeldingActual.productionQty') }}</span>
                <span class="history-card__stat-value">{{ row.actualQty.toLocaleString() }}</span>
              </span>
              <span class="history-card__stat">
                <span class="history-card__stat-label">{{ t('mesWeldingActual.defectQty') }}</span>
                <span
                  class="history-card__stat-value"
                  :class="{ 'history-card__stat-value--defect': row.defectQty > 0 }"
                >{{ row.defectQty > 0 ? row.defectQty.toLocaleString() : '—' }}</span>
              </span>
              <span class="history-card__stat">
                <span class="history-card__stat-label">{{ t('mesWeldingActual.productionStart') }}</span>
                <span class="history-card__stat-value history-card__stat-value--time">{{
                  formatHistoryTime(row.startedAt, intlLocale)
                }}</span>
              </span>
              <span class="history-card__stat">
                <span class="history-card__stat-label">{{ t('mesWeldingActual.productionEnd') }}</span>
                <span class="history-card__stat-value history-card__stat-value--time">{{
                  formatHistoryTime(row.endedAt, intlLocale)
                }}</span>
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <el-drawer
      v-if="processKey === 'inspection'"
      v-model="nextAssignPanelVisible"
      class="next-assign-panel"
      direction="rtl"
      size="min(440px, 92vw)"
      :show-close="true"
      destroy-on-close
      @closed="closeNextAssignPanel"
    >
      <template #header>
        <div class="next-assign-panel__head">
          <span class="next-assign-panel__head-icon" aria-hidden="true">
            <el-icon :size="16"><Goods /></el-icon>
          </span>
          <div class="next-assign-panel__head-text">
            <h4 class="next-assign-panel__title">{{ t('mesInspectionActual.nextAssignmentPanelTitle') }}</h4>
            <p class="next-assign-panel__subtitle">{{ t('mesInspectionActual.nextAssignmentPanelSubtitle') }}</p>
          </div>
        </div>
      </template>
      <div class="next-assign-panel__toolbar">
        <button
          type="button"
          class="next-assign-panel__add-btn"
          @click="openNextAssignCreateDialog"
        >
          <el-icon :size="14"><User /></el-icon>
          {{ t('mesInspectionActual.nextAssignmentAddInspector') }}
        </button>
      </div>
      <div v-if="nextAssignPanelRows.length === 0" class="next-assign-panel__empty">
        <el-empty
          :description="t('mesInspectionActual.nextAssignmentPanelEmpty')"
          :image-size="64"
        />
      </div>
      <div v-else class="next-assign-panel__sections">
        <section v-if="nextAssignPanelActiveRows.length > 0" class="next-assign-panel__section">
          <h5 class="next-assign-panel__section-title">
            {{ t('mesInspectionActual.nextAssignmentPanelActiveSection') }}
          </h5>
          <div class="next-assign-panel__list">
            <article
              v-for="row in nextAssignPanelActiveRows"
              :key="row.key"
              class="next-assign-panel__card"
              :class="[
                `next-assign-panel__card--${row.status}`,
                { 'next-assign-panel__card--comm-stale': row.commStale },
              ]"
            >
              <div class="next-assign-panel__card-top">
                <div class="next-assign-panel__card-main">
                  <span class="next-assign-panel__product" :title="row.currentProductLabel">{{
                    row.currentProductLabel
                  }}</span>
                  <span class="next-assign-panel__inspector" :title="row.inspectorName">
                    <el-icon :size="13"><User /></el-icon>
                    {{ row.inspectorName }}
                  </span>
                </div>
                <div class="next-assign-panel__card-tags">
                  <el-tag
                    v-if="row.commStale"
                    size="small"
                    type="danger"
                    effect="plain"
                    round
                  >
                    通信断
                  </el-tag>
                  <el-tag size="small" :type="statusTagType(row.status)" effect="plain" round>
                    <span v-if="row.status === 'running'" class="machine-card__pulse"></span>
                    {{ statusLabel(row.status) }}
                  </el-tag>
                </div>
              </div>
              <div class="next-assign-panel__metrics">
                <span v-if="(row.elapsedSec ?? 0) > 0" class="next-assign-panel__metric">
                  <span class="next-assign-panel__metric-label">経過</span>
                  <span class="next-assign-panel__metric-value next-assign-panel__metric-value--time">{{
                    formatDuration(row.elapsedSec ?? 0)
                  }}</span>
                </span>
                <span v-if="row.status === 'paused'" class="next-assign-panel__metric">
                  <span class="next-assign-panel__metric-label">一時停止</span>
                  <span class="next-assign-panel__metric-value next-assign-panel__metric-value--pause">
                    {{ (row.pausedSec ?? 0) > 0 ? formatDuration(row.pausedSec ?? 0) : '—' }}
                  </span>
                </span>
                <span v-if="row.status === 'break'" class="next-assign-panel__metric">
                  <span class="next-assign-panel__metric-label">休憩</span>
                  <span class="next-assign-panel__metric-value next-assign-panel__metric-value--break">
                    {{ (row.breakSec ?? 0) > 0 ? formatDuration(row.breakSec ?? 0) : '—' }}
                  </span>
                </span>
              </div>
              <div
                class="next-assign-panel__actions"
                :class="{ 'next-assign-panel__actions--assigned': Boolean(row.nextProductName) }"
              >
                <div
                  v-if="row.nextProductName"
                  class="machine-card__next-chip"
                  :title="`${row.nextProductCd ?? ''} · ${row.nextProductName}`"
                >
                  <span class="machine-card__next-chip-icon" aria-hidden="true">
                    <el-icon :size="12"><Goods /></el-icon>
                  </span>
                  <span class="machine-card__next-chip-label">{{
                    t('mesInspectionActual.nextAssignmentShort')
                  }}</span>
                  <span class="machine-card__next-chip-value">{{ row.nextProductName }}</span>
                </div>
                <button
                  type="button"
                  class="machine-card__next-glass-btn"
                  :title="t('mesInspectionActual.nextAssignmentAssign')"
                  @click="openNextAssignDialogForRow(row)"
                >
                  <span class="machine-card__next-glass-btn__shine" aria-hidden="true" />
                  <span class="machine-card__next-glass-btn__glow" aria-hidden="true" />
                  <span class="machine-card__next-glass-btn__icon" aria-hidden="true">
                    <el-icon :size="13"><Goods /></el-icon>
                  </span>
                  <span class="machine-card__next-glass-btn__text">{{
                    t('mesInspectionActual.nextAssignmentAssign')
                  }}</span>
                </button>
              </div>
            </article>
          </div>
        </section>

        <section v-if="nextAssignPanelIdleRows.length > 0" class="next-assign-panel__section">
          <h5 class="next-assign-panel__section-title">
            {{ t('mesInspectionActual.nextAssignmentPanelIdleSection') }}
          </h5>
          <div class="next-assign-panel__list">
            <article
              v-for="row in nextAssignPanelIdleRows"
              :key="row.key"
              class="next-assign-panel__card next-assign-panel__card--idle"
            >
              <div class="next-assign-panel__card-top">
                <div class="next-assign-panel__card-main">
                  <span class="next-assign-panel__product" :title="row.inspectorName">{{
                    row.inspectorName
                  }}</span>
                  <span class="next-assign-panel__inspector next-assign-panel__inspector--hint">
                    {{ t('mesInspectionActual.nextAssignmentStatusIdle') }}
                  </span>
                </div>
                <div class="next-assign-panel__card-tags">
                  <el-tag size="small" type="info" effect="plain" round>
                    {{ t('mesInspectionActual.nextAssignmentStatusIdle') }}
                  </el-tag>
                </div>
              </div>
              <div
                class="next-assign-panel__actions"
                :class="{ 'next-assign-panel__actions--assigned': Boolean(row.nextProductName) }"
              >
                <div
                  v-if="row.nextProductName"
                  class="machine-card__next-chip"
                  :title="`${row.nextProductCd ?? ''} · ${row.nextProductName}`"
                >
                  <span class="machine-card__next-chip-icon" aria-hidden="true">
                    <el-icon :size="12"><Goods /></el-icon>
                  </span>
                  <span class="machine-card__next-chip-label">{{
                    t('mesInspectionActual.nextAssignmentFirstShort')
                  }}</span>
                  <span class="machine-card__next-chip-value">{{ row.nextProductName }}</span>
                </div>
                <button
                  type="button"
                  class="machine-card__next-glass-btn"
                  :title="t('mesInspectionActual.nextAssignmentFirstAssign')"
                  @click="openNextAssignDialogForRow(row)"
                >
                  <span class="machine-card__next-glass-btn__shine" aria-hidden="true" />
                  <span class="machine-card__next-glass-btn__glow" aria-hidden="true" />
                  <span class="machine-card__next-glass-btn__icon" aria-hidden="true">
                    <el-icon :size="13"><Goods /></el-icon>
                  </span>
                  <span class="machine-card__next-glass-btn__text">{{
                    row.nextProductName
                      ? t('mesInspectionActual.nextAssignmentAssign')
                      : t('mesInspectionActual.nextAssignmentFirstAssign')
                  }}</span>
                </button>
              </div>
            </article>
          </div>
        </section>
      </div>
    </el-drawer>

    <el-dialog
      v-if="processKey === 'inspection'"
      v-model="nextAssignDialogVisible"
      class="next-assign-dialog"
      width="min(420px, 92vw)"
      align-center
      destroy-on-close
      :show-close="!nextAssignSubmitting"
      @closed="closeNextAssignDialog"
    >
      <template #header>
        <div class="next-assign-dialog__head">
          <span class="next-assign-dialog__head-icon" aria-hidden="true">
            <el-icon :size="16"><Goods /></el-icon>
          </span>
          <span class="next-assign-dialog__head-title">{{
            nextAssignTarget?.isFirstProduct
              ? t('mesInspectionActual.nextAssignmentFirstDialogTitle')
              : t('mesInspectionActual.nextAssignmentDialogTitle')
          }}</span>
        </div>
      </template>
      <template v-if="nextAssignTarget">
        <div class="next-assign-dialog__context">
          <div v-if="nextAssignPickInspector" class="next-assign-dialog__field next-assign-dialog__field--dialog">
            <label class="next-assign-dialog__label" for="next-assign-inspector-select">{{
              t('mesInspectionActual.inspector')
            }}</label>
            <el-select
              id="next-assign-inspector-select"
              v-model="nextAssignInspectorUserId"
              filterable
              clearable
              size="small"
              class="next-assign-dialog__select"
              :placeholder="t('mesInspectionActual.inspectorPlaceholder')"
              :loading="loadingInspectionInspectors"
            >
              <el-option
                v-for="insp in inspectionInspectorOptions"
                :key="insp.id"
                :label="insp.full_name || insp.username"
                :value="insp.id"
              />
            </el-select>
          </div>
          <div v-else class="next-assign-dialog__context-row">
            <span class="next-assign-dialog__ctx-label">{{ t('mesInspectionActual.inspector') }}</span>
            <span class="next-assign-dialog__ctx-value next-assign-dialog__ctx-value--inspector">
              <el-icon :size="13"><User /></el-icon>
              {{ nextAssignTarget.inspectorName }}
            </span>
          </div>
          <div v-if="!nextAssignTarget.isFirstProduct" class="next-assign-dialog__context-row">
            <span class="next-assign-dialog__ctx-label">{{
              t('mesInspectionActual.nextAssignmentCurrent')
            }}</span>
            <span
              class="next-assign-dialog__ctx-value next-assign-dialog__ctx-value--product"
              :title="nextAssignTarget.currentProductLabel"
            >
              {{ nextAssignTarget.currentProductLabel }}
            </span>
          </div>
        </div>
        <div class="next-assign-dialog__fields">
          <div class="next-assign-dialog__field">
            <label class="next-assign-dialog__label" for="next-assign-product-select">{{
              nextAssignTarget.isFirstProduct
                ? t('mesInspectionActual.nextAssignmentFirstProduct')
                : t('mesInspectionActual.nextAssignmentProduct')
            }}</label>
            <el-select
              id="next-assign-product-select"
              v-model="nextAssignProductCd"
              filterable
              clearable
              size="small"
              class="next-assign-dialog__select"
              :placeholder="t('mesInspectionActual.productPlaceholder')"
              :loading="loadingMonitorProducts"
            >
              <el-option
                v-for="p in monitorProducts"
                :key="p.product_code"
                :label="`${p.product_code} · ${p.product_name}`"
                :value="p.product_code"
              />
            </el-select>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="next-assign-dialog__footer">
          <button
            type="button"
            class="next-assign-dialog__btn next-assign-dialog__btn--cancel"
            :disabled="nextAssignSubmitting"
            @click="closeNextAssignDialog"
          >
            {{ t('common.cancel') }}
          </button>
          <div class="next-assign-dialog__footer-actions">
            <button
              v-if="
                nextAssignDialogInspectorUserId != null &&
                hasNextAssignmentForInspector(nextAssignDialogInspectorUserId)
              "
              type="button"
              class="next-assign-dialog__btn next-assign-dialog__btn--clear"
              :disabled="nextAssignSubmitting"
              @click="clearNextAssignment"
            >
              <span
                v-if="nextAssignSubmitting"
                class="next-assign-dialog__btn-spinner"
                aria-hidden="true"
              />
              {{ t('mesInspectionActual.nextAssignmentClear') }}
            </button>
            <button
              type="button"
              class="next-assign-dialog__btn next-assign-dialog__btn--save"
              :disabled="nextAssignSubmitting"
              @click="saveNextAssignment"
            >
              <span
                v-if="nextAssignSubmitting"
                class="next-assign-dialog__btn-spinner next-assign-dialog__btn-spinner--light"
                aria-hidden="true"
              />
              {{ t('mesInspectionActual.nextAssignmentSave') }}
            </button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped src="./processMonitorPage.scss" lang="scss"></style>
