# -*- coding: utf-8
"""从切断実績登録页生成面取実績登録页。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/src/views/mes/actualCollectionRegistration/cutting/CuttingActualCollectionRegistration.vue"
DST = ROOT / "frontend/src/views/mes/actualCollectionRegistration/chamfering/ChamferingActualCollectionRegistration.vue"

CHAMFERING_SCRIPT = r'''<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
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
  User,
  Warning,
} from '@element-plus/icons-vue'
import { useChamferingManualRegistration } from './useChamferingManualRegistration'

defineOptions({ name: 'ChamferingActualCollectionRegistration' })

const reg = useChamferingManualRegistration()
const {
  productionDay,
  lineFilterName,
  loading,
  saving,
  deletingRowId,
  filteredRows,
  listSummaryQtyLabel,
  listSummaryEfficiencyLabel,
  products,
  loadingProducts,
  lineOptions,
  loadingLines,
  editingRowId,
  form,
  isEdit,
  canSave,
  canEdit,
  canDelete,
  timeSummary,
  formatMinutesLabel,
  lineLabel,
  computedTotalQty,
  loadRows,
  onProductChange,
  formatQtyInputValue,
  onChamferPlannedQtyInput,
  onChamferActualQtyInput,
  onSwPlannedQtyInput,
  onSwActualQtyInput,
  onChamferDefectQtyInput,
  onSwDefectQtyInput,
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
  formatBreakMin,
  formatStopMin,
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

const lineSelected = computed(() => Boolean(form.value.productionLine?.trim()))
const productSelected = computed(() => isEdit.value || Boolean(form.value.productCd?.trim()))

const startedAtInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const endedAtInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const breakMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const stopMinInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const remarksInputRef = ref<InstanceType<typeof ElInput> | null>(null)

function focusElInput(inputRef: typeof startedAtInputRef): void {
  nextTick(() => {
    inputRef.value?.focus()
    const el = inputRef.value?.$el as HTMLElement | undefined
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

function focusInputNumber(inputRef: typeof breakMinInputRef): void {
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
  focusInputNumber(breakMinInputRef)
}

function onBreakMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusInputNumber(stopMinInputRef)
}

function onStopMinEnter(e: Event): void {
  if (!(e instanceof KeyboardEvent) || e.key !== 'Enter') return
  e.preventDefault()
  focusElInput(remarksInputRef)
}

onMounted(() => {
  void init()
})
</script>
'''

CHAMFERING_QTY_BLOCK = r'''        <div class="iar-qty iar-field--c4">
          <label class="iar-field__label">
            <span class="iar-step iar-step--4">④</span>生産数
            <span v-if="computedTotalQty > 0" class="iar-qty__hint">総数 {{ computedTotalQty }}</span>
          </label>
          <div class="iar-qty__panel iar-qty__panel--quad">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">面取計画</span>
              <el-input
                :model-value="formatQtyInputValue(form.chamferPlannedQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="面取計画"
                @update:model-value="onChamferPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">面取生産</span>
              <el-input
                :model-value="formatQtyInputValue(form.chamferActualQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="面取生産"
                @update:model-value="onChamferActualQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">SW計画</span>
              <el-input
                :model-value="formatQtyInputValue(form.swPlannedQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="SW計画"
                @update:model-value="onSwPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">SW生産</span>
              <el-input
                :model-value="formatQtyInputValue(form.swActualQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="SW生産"
                @update:model-value="onSwActualQtyInput"
              />
            </div>
          </div>
        </div>'''

CHAMFERING_DEFECT_BLOCK = r'''        <div class="iar-defects-simple iar-field--c6">
          <label class="iar-field__label"><span class="iar-step iar-step--6">⑥</span>不良</label>
          <div class="iar-qty__panel">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">面取不良</span>
              <el-input
                :model-value="formatQtyInputValue(form.chamferDefectQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onChamferDefectQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">SW不良</span>
              <el-input
                :model-value="formatQtyInputValue(form.swDefectQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="0"
                @update:model-value="onSwDefectQtyInput"
              />
            </div>
          </div>
        </div>'''

CHAMFERING_TABLE_COLUMNS = r'''          <el-table-column label="生産日" width="102" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__date">{{ row.production_day ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="ライン" width="88" align="left" header-align="left" show-overflow-tooltip>
            <template #default="{ row }">{{ lineLabel(row.production_line) }}</template>
          </el-table-column>
          <el-table-column prop="product_cd" label="CD" width="76" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="110" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column label="面取" width="52" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.chamfer_actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="SW" width="52" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.sw_actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="総数" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.total_production_qty ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="能率" width="52" align="right" header-align="right">
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
          <el-table-column label="休憩" width="56" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatBreakMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="停止" width="56" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatStopMin(row) }}</span>
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
.iar-qty__panel--quad {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.iar-defects-simple {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
'''


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    m_script = re.search(r"<script setup lang=\"ts\">.*?</script>", text, re.DOTALL)
    m_style = re.search(r"<style scoped>.*</style>\s*$", text, re.DOTALL)
    if not m_script or not m_style:
        raise SystemExit("Could not parse cutting vue")

    template = text[m_script.end() : text.find("<style scoped>")]
    style = m_style.group(0)

    template = template.replace("切断実績収集登録", "面取実績収集登録")
    template = template.replace(
        '<span class="iar-chip iar-chip--rose"><i>⑥</i>差異</span>',
        '<span class="iar-chip iar-chip--rose"><i>⑥</i>不良</span>',
    )
    template = template.replace("生産数・時間・差異・備考", "生産数・時間・不良・備考")

    qty_block = re.search(
        r'<div class="iar-qty iar-field--c4">.*?</div>\n\n        <div class="iar-time iar-field--c5">',
        template,
        re.DOTALL,
    )
    if not qty_block:
        raise SystemExit("Qty block not found")
    template = (
        template[: qty_block.start()]
        + CHAMFERING_QTY_BLOCK
        + "\n\n        <div class=\"iar-time iar-field--c5\">"
        + template[qty_block.end() :]
    )

    variance_block = re.search(
        r'<div class="iar-variance iar-field--c6">.*?<div class="iar-remarks iar-field--c7',
        template,
        re.DOTALL,
    )
    if not variance_block:
        raise SystemExit("Variance block not found")
    template = (
        template[: variance_block.start()]
        + CHAMFERING_DEFECT_BLOCK
        + "\n\n        <div class=\"iar-remarks iar-field--c7"
        + template[variance_block.end() :]
    )

    cols_block = re.search(
        r'<el-table-column label="生産日".*?<el-table-column prop="remarks".*?/>',
        template,
        re.DOTALL,
    )
    if not cols_block:
        raise SystemExit("Table columns not found")
    template = template[: cols_block.start()] + CHAMFERING_TABLE_COLUMNS + template[cols_block.end() :]

    if ".iar-qty__panel--quad" not in style:
        style = style[:- len("</style>")] + EXTRA_STYLE + "\n</style>\n"

    DST.write_text(CHAMFERING_SCRIPT + template + style, encoding="utf-8")
    print(f"Wrote {DST} ({len((CHAMFERING_SCRIPT + template + style).splitlines())} lines)")


if __name__ == "__main__":
    main()
