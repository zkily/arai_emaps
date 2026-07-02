# -*- coding: utf-8
"""从面取実績登録页生成メッキ日次実績登録页。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/src/views/mes/actualCollectionRegistration/chamfering/ChamferingActualCollectionRegistration.vue"
DST = ROOT / "frontend/src/views/mes/actualCollectionRegistration/plating/PlatingActualCollectionRegistration.vue"

PLATING_SCRIPT = r'''<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import type { ElInput, ElInputNumber } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  ChatLineSquare,
  Clock,
  DataLine,
  Delete,
  Edit,
  Refresh,
  Warning,
} from '@element-plus/icons-vue'
import { usePlatingManualRegistration } from './usePlatingManualRegistration'

defineOptions({ name: 'PlatingActualCollectionRegistration' })

const reg = usePlatingManualRegistration()
const {
  productionDay,
  loading,
  saving,
  deletingRowId,
  filteredRows,
  listSummaryQtyLabel,
  listSummaryEfficiencyLabel,
  editingRowId,
  form,
  isEdit,
  canSave,
  canEdit,
  canDelete,
  timeSummary,
  formatMinutesLabel,
  computedTotalQty,
  loadRows,
  formatQtyInputValue,
  onPlannedQtyInput,
  onActualQtyInput,
  onDefectQtyInput,
  onDefectPlatingScratchInput,
  onDefectMoyaKaburiInput,
  onDefectNickelInput,
  onDefectContactInput,
  onDefectOtherInput,
  startedAtText,
  endedAtText,
  onStartedAtInput,
  onEndedAtInput,
  onStartedAtBlur,
  onEndedAtBlur,
  onProductionDayChange,
  shiftProductionDay,
  goProductionDayToday,
  resetForm,
  loadRowIntoForm,
  deleteRow,
  submitForm,
  formatMaintenanceMin,
  formatTroubleMin,
  formatWorkHours,
  formatEfficiencyRate,
  isEfficiencyRateOutOfRange,
  dataSourceLabel,
  dataSourceTagType,
  canEditRow,
  canDeleteRow,
  isRowMesInProgress,
  init,
} = reg

const formReady = computed(() => isEdit.value || Boolean(form.value.productionDay?.trim()))

const startedAtInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const endedAtInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const maintenanceMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const troubleMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const chocoMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const plannedStopMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const remarksInputRef = ref<InstanceType<typeof ElInput> | null>(null)

function focusElInput(inputRef: typeof startedAtInputRef): void {
  nextTick(() => {
    inputRef.value?.focus()
    const el = inputRef.value?.$el as HTMLElement | undefined
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

function focusInputNumber(inputRef: typeof maintenanceMinInputRef): void {
  nextTick(() => {
    const root = inputRef.value?.$el as HTMLElement | undefined
    const input = root?.querySelector('input')
    input?.focus()
    input?.select()
    root?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

function onStartedAtEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  onStartedAtBlur()
  focusElInput(endedAtInputRef)
}

function onEndedAtEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  onEndedAtBlur()
  focusInputNumber(maintenanceMinInputRef)
}

function onMaintenanceMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusInputNumber(troubleMinInputRef)
}

function onTroubleMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusInputNumber(chocoMinInputRef)
}

function onChocoMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusInputNumber(plannedStopMinInputRef)
}

function onPlannedStopMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusElInput(remarksInputRef)
}

onMounted(() => {
  void init()
})
</script>
'''

# fix missing computed import in script - add it
PLATING_SCRIPT = PLATING_SCRIPT.replace(
    "import { nextTick, onMounted, ref } from 'vue'",
    "import { computed, nextTick, onMounted, ref } from 'vue'",
)

PLATING_QTY_BLOCK = r'''        <div class="iar-qty iar-field--c2">
          <label class="iar-field__label">
            <span class="iar-step iar-step--2">②</span>生産数
            <span v-if="computedTotalQty > 0" class="iar-qty__hint">実績 {{ computedTotalQty }}</span>
          </label>
          <div class="iar-qty__panel">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">計画数</span>
              <el-input
                :model-value="formatQtyInputValue(form.plannedQty)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="計画数"
                @update:model-value="onPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">実績数</span>
              <el-input
                :model-value="formatQtyInputValue(form.actualQty)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="実績数"
                @update:model-value="onActualQtyInput"
              />
            </div>
          </div>
        </div>'''

PLATING_DEFECT_BLOCK = r'''        <div class="iar-defects-simple iar-field--c4">
          <label class="iar-field__label"><span class="iar-step iar-step--4">④</span>不良</label>
          <div class="iar-qty__panel iar-qty__panel--grid">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">不良計</span>
              <el-input
                :model-value="formatQtyInputValue(form.defectQty)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onDefectQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">メッキ後キズ</span>
              <el-input
                :model-value="formatQtyInputValue(form.defectPlatingScratch)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onDefectPlatingScratchInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">モヤ/カブリ</span>
              <el-input
                :model-value="formatQtyInputValue(form.defectMoyaKaburi)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onDefectMoyaKaburiInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">ニッケル</span>
              <el-input
                :model-value="formatQtyInputValue(form.defectNickel)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onDefectNickelInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">接触</span>
              <el-input
                :model-value="formatQtyInputValue(form.defectContact)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onDefectContactInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">メ他</span>
              <el-input
                :model-value="formatQtyInputValue(form.defectOther)"
                :disabled="!formReady"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onDefectOtherInput"
              />
            </div>
          </div>
        </div>'''

PLATING_LOSS_BLOCK = r'''            <div class="iar-time__losses">
              <div class="iar-time__loss">
                <span class="iar-time__loss-label">メンテ</span>
                <el-input-number
                  ref="maintenanceMinInputRef"
                  v-model="form.maintenanceMin"
                  :min="0"
                  :max="1440"
                  :step="1"
                  :disabled="!formReady"
                  controls-position="right"
                  class="iar-field__control iar-field__min"
                  @keydown.enter="onMaintenanceMinEnter"
                />
                <span class="iar-time__loss-unit">分</span>
              </div>
              <div class="iar-time__loss">
                <span class="iar-time__loss-label">トラブル</span>
                <el-input-number
                  ref="troubleMinInputRef"
                  v-model="form.troubleMin"
                  :min="0"
                  :max="1440"
                  :step="1"
                  :disabled="!formReady"
                  controls-position="right"
                  class="iar-field__control iar-field__min"
                  @keydown.enter="onTroubleMinEnter"
                />
                <span class="iar-time__loss-unit">分</span>
              </div>
              <div class="iar-time__loss">
                <span class="iar-time__loss-label">チョコ停</span>
                <el-input-number
                  ref="chocoMinInputRef"
                  v-model="form.chocoMin"
                  :min="0"
                  :max="1440"
                  :step="1"
                  :disabled="!formReady"
                  controls-position="right"
                  class="iar-field__control iar-field__min"
                  @keydown.enter="onChocoMinEnter"
                />
                <span class="iar-time__loss-unit">分</span>
              </div>
              <div class="iar-time__loss">
                <span class="iar-time__loss-label">計画停止</span>
                <el-input-number
                  ref="plannedStopMinInputRef"
                  v-model="form.plannedStopMin"
                  :min="0"
                  :max="1440"
                  :step="1"
                  :disabled="!formReady"
                  controls-position="right"
                  class="iar-field__control iar-field__min"
                  @keydown.enter="onPlannedStopMinEnter"
                />
                <span class="iar-time__loss-unit">分</span>
              </div>
            </div>'''

PLATING_TABLE_COLUMNS = r'''          <el-table-column label="生産日" width="102" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__date">{{ row.production_day ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="計画" width="72" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.planned_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="実績" width="72" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="不良" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.defect_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span
                class="iar-table__efficiency"
                :class="{ 'iar-table__efficiency--alert': isEfficiencyRateOutOfRange(row) }"
              >
                {{ formatEfficiencyRate(row) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="作業" width="56" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatWorkHours(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="メンテ" width="64" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatMaintenanceMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="トラブル" width="72" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatTroubleMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="取得元" width="72" align="center" header-align="center">
            <template #default="{ row }">
              <el-tag
                :type="dataSourceTagType(row)"
                size="small"
                effect="light"
                class="iar-table__source"
              >
                {{ dataSourceLabel(row) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" min-width="72" align="left" header-align="left" show-overflow-tooltip />'''

EXTRA_STYLE = r'''
.iar-qty__panel--grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.iar-defects-simple {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.iar-time__losses {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.iar-time__loss {
  display: flex;
  align-items: center;
  gap: 6px;
}

.iar-time__loss-label {
  min-width: 4.5em;
  font-size: 12px;
  color: var(--iar-muted, #64748b);
}

.iar-time__loss-unit {
  font-size: 12px;
  color: var(--iar-muted, #64748b);
}
'''


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    m_script = re.search(r"<script setup lang=\"ts\">.*?</script>", text, re.DOTALL)
    m_style = re.search(r"<style scoped>.*</style>\s*$", text, re.DOTALL)
    if not m_script or not m_style:
        raise SystemExit("Could not parse chamfering vue")

    template = text[m_script.end() : text.find("<style scoped>")]
    style = m_style.group(0)

    template = template.replace("面取実績収集登録", "メッキ実績収集登録")
    template = re.sub(
        r'<span class="iar-chip iar-chip--violet"><i>②</i>ライン</span>\s*'
        r'<span class="iar-chip iar-chip--teal"><i>③</i>製品</span>\s*'
        r'<span class="iar-chip iar-chip--amber"><i>④</i>生産数</span>\s*'
        r'<span class="iar-chip iar-chip--indigo"><i>⑤</i>時間</span>\s*'
        r'<span class="iar-chip iar-chip--rose"><i>⑥</i>不良</span>\s*'
        r'<span class="iar-chip iar-chip--slate"><i>⑦</i>備考</span>',
        '<span class="iar-chip iar-chip--amber"><i>②</i>生産数</span>\n'
        '        <span class="iar-chip iar-chip--indigo"><i>③</i>時間</span>\n'
        '        <span class="iar-chip iar-chip--rose"><i>④</i>不良</span>\n'
        '        <span class="iar-chip iar-chip--slate"><i>⑤</i>備考</span>',
        template,
    )
    template = template.replace("生産数・時間・不良・備考", "日次集計 · 生産数 · 時間 · 不良")

    # remove line + product fields (c2, c3)
    template = re.sub(
        r'\s*<div class="iar-field iar-field--c2">.*?</div>\s*<div class="iar-field iar-field--c3">.*?</div>',
        "",
        template,
        count=1,
        flags=re.S,
    )

    # qty block
    qty_block = re.search(
        r'<div class="iar-qty iar-field--c4">.*?</div>\n\n        <div class="iar-time iar-field--c5">',
        template,
        re.DOTALL,
    )
    if not qty_block:
        raise SystemExit("Qty block not found")
    template = (
        template[: qty_block.start()]
        + PLATING_QTY_BLOCK
        + "\n\n        <div class=\"iar-time iar-field--c3\">"
        + template[qty_block.end() :]
    )
    template = template.replace('iar-field--c5', 'iar-field--c3', 1)
    template = template.replace('<span class="iar-step iar-step--5">⑤</span>', '<span class="iar-step iar-step--3">③</span>', 1)

    # defect block
    defect_block = re.search(
        r'<div class="iar-defects-simple iar-field--c6">.*?<div class="iar-remarks iar-field--c7',
        template,
        re.DOTALL,
    )
    if not defect_block:
        raise SystemExit("Defect block not found")
    template = (
        template[: defect_block.start()]
        + PLATING_DEFECT_BLOCK
        + "\n\n        <div class=\"iar-remarks iar-field--c5"
        + template[defect_block.end() :]
    )
    template = template.replace('iar-field--c7', 'iar-field--c5', 1)
    template = template.replace('<span class="iar-step iar-step--7">⑦</span>', '<span class="iar-step iar-step--5">⑤</span>', 1)

    # replace break/stop with 4 losses in time section
    template = re.sub(
        r'<div class="iar-time__pause">.*?</div>\s*<div class="iar-time__pause">.*?</div>',
        PLATING_LOSS_BLOCK.strip(),
        template,
        count=1,
        flags=re.S,
    )
    template = template.replace(':disabled="!productSelected"', ':disabled="!formReady"')

    # remove line filter in list toolbar
    template = re.sub(
        r'<div class="iar-list-toolbar__filter">.*?</div>\s*',
        "",
        template,
        count=1,
        flags=re.S,
    )

    cols_block = re.search(
        r'<el-table-column label="生産日".*?<el-table-column prop="remarks".*?/>',
        template,
        re.DOTALL,
    )
    if not cols_block:
        raise SystemExit("Table columns not found")
    template = template[: cols_block.start()] + PLATING_TABLE_COLUMNS + template[cols_block.end() :]

    if ".iar-qty__panel--grid" not in style:
        style = style[:- len("</style>")] + EXTRA_STYLE + "\n</style>\n"

    DST.write_text(PLATING_SCRIPT + template + style, encoding="utf-8")
    print(f"Wrote {DST}")


if __name__ == "__main__":
    main()
