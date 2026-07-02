# -*- coding: utf-8
"""从检验実績登録页生成切断実績登録页。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/src/views/mes/actualCollectionRegistration/inspection/InspectionActualCollectionRegistration.vue"
DST = ROOT / "frontend/src/views/mes/actualCollectionRegistration/cutting/CuttingActualCollectionRegistration.vue"

CUTTING_SCRIPT = r'''<script setup lang="ts">
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
import { useCuttingManualRegistration } from './useCuttingManualRegistration'

defineOptions({ name: 'CuttingActualCollectionRegistration' })

const reg = useCuttingManualRegistration()
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
  computedVariance,
  loadRows,
  onProductChange,
  formatQtyInputValue,
  onPlannedQtyInput,
  onActualQtyInput,
  onVarianceQtyInput,
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

CUTTING_QTY_BLOCK = r'''        <div class="iar-qty iar-field--c4">
          <label class="iar-field__label"><span class="iar-step iar-step--4">④</span>生産数</label>
          <div class="iar-qty__panel">
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">計画</span>
              <el-input
                :model-value="formatQtyInputValue(form.plannedQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="計画"
                @update:model-value="onPlannedQtyInput"
              />
            </div>
            <div class="iar-qty__cell">
              <span class="iar-qty__cell-label">生産</span>
              <el-input
                :model-value="formatQtyInputValue(form.actualQty)"
                :disabled="!productSelected"
                inputmode="numeric"
                class="iar-field__control iar-field__qty"
                placeholder="生産"
                @update:model-value="onActualQtyInput"
              />
            </div>
          </div>
        </div>'''

CUTTING_VARIANCE_BLOCK = r'''        <div class="iar-variance iar-field--c6">
          <label class="iar-field__label">
            <span class="iar-step iar-step--6">⑥</span>差異
          </label>
          <el-input
            :model-value="formatQtyInputValue(computedVariance)"
            :disabled="!productSelected"
            inputmode="numeric"
            class="iar-field__control iar-field__qty"
            placeholder="自動計算（手入力可）"
            @update:model-value="onVarianceQtyInput"
          />
          <p class="iar-variance__hint">計画 − 生産（未入力時は自動）</p>
        </div>'''

CUTTING_TABLE_FILTER = r'''          <el-select
            v-model="lineFilterName"
            clearable
            filterable
            allow-create
            default-first-option
            placeholder="ライン"
            size="small"
            class="iar-filter"
            :loading="loadingLines"
          >
            <el-option
              v-for="u in lineOptions"
              :key="u.line_name"
              :label="lineLabel(u.line_name)"
              :value="u.line_name"
            />
          </el-select>'''

CUTTING_TABLE_COLUMNS = r'''          <el-table-column label="生産日" width="102" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__date">{{ row.production_day ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="ライン" width="96" align="left" header-align="left" show-overflow-tooltip>
            <template #default="{ row }">{{ lineLabel(row.production_line) }}</template>
          </el-table-column>
          <el-table-column prop="product_cd" label="CD" width="84" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="128" align="left" header-align="left" show-overflow-tooltip />
          <el-table-column label="計画" width="64" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.planned_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="生産" width="64" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.actual_quantity ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="差異" width="56" align="right" header-align="right">
            <template #default="{ row }">
              <span class="iar-table__qty">{{ row.quantity_variance ?? '—' }}</span>
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
          <el-table-column label="作業" width="60" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatWorkHours(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="休憩" width="60" align="center" header-align="center">
            <template #default="{ row }">
              <span class="iar-table__pause">{{ formatBreakMin(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="停止" width="60" align="center" header-align="center">
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
.iar-variance {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.iar-variance__hint {
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
}
'''


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    m_script = re.search(r"<script setup lang=\"ts\">.*?</script>", text, re.DOTALL)
    m_style = re.search(r"<style scoped>.*</style>\s*$", text, re.DOTALL)
    if not m_script or not m_style:
        raise SystemExit("Could not parse source vue sections")

    template = text[m_script.end() : text.find("<style scoped>")]
    style = m_style.group(0)

    # Hero
    template = template.replace("検査実績収集登録", "切断実績収集登録")
    template = template.replace(
        '<span class="iar-chip iar-chip--violet"><i>②</i>検査員</span>',
        '<span class="iar-chip iar-chip--violet"><i>②</i>ライン</span>',
    )
    template = template.replace(
        '<span class="iar-chip iar-chip--rose"><i>⑥</i>不良</span>\n        '
        '<span class="iar-chip iar-chip--slate"><i>⑦</i>備考</span>',
        '<span class="iar-chip iar-chip--rose"><i>⑥</i>差異</span>\n        '
        '<span class="iar-chip iar-chip--slate"><i>⑦</i>備考</span>',
    )

    # Line field
    line_field = re.search(
        r'<div class="iar-field iar-field--c2">.*?</div>\n          <div class="iar-field iar-field--c3">',
        template,
        re.DOTALL,
    )
    if not line_field:
        raise SystemExit("Line field block not found")
    new_line_field = '''          <div class="iar-field iar-field--c2">
            <label class="iar-field__label"><span class="iar-step iar-step--2">②</span>ライン</label>
            <el-select
              v-model="form.productionLine"
              filterable
              allow-create
              default-first-option
              clearable
              placeholder="選択または入力"
              class="iar-field__control"
              :loading="loadingLines"
            >
              <template #prefix><el-icon><User /></el-icon></template>
              <el-option
                v-for="u in lineOptions"
                :key="u.line_name"
                :label="lineLabel(u.line_name)"
                :value="u.line_name"
              />
            </el-select>
          </div>
          <div class="iar-field iar-field--c3">'''
    template = template[: line_field.start()] + new_line_field + template[line_field.end() :]

    template = template.replace("!inspectorSelected", "!lineSelected")
    template = template.replace("② 検査員を選択すると", "② ラインを選択すると")
    template = template.replace("生産数・時間・不良・備考", "生産数・時間・差異・備考")

    template = template.replace(
        ':disabled="!inspectorSelected"',
        ':disabled="!lineSelected"',
    )

    # Qty block
    qty_block = re.search(
        r'<div class="iar-qty iar-field--c4">.*?</div>\n\n        <div class="iar-time iar-field--c5">',
        template,
        re.DOTALL,
    )
    if not qty_block:
        raise SystemExit("Qty block not found")
    template = (
        template[: qty_block.start()]
        + CUTTING_QTY_BLOCK
        + "\n\n        <div class=\"iar-time iar-field--c5\">"
        + template[qty_block.end() :]
    )

    # Defect -> variance
    defect_block = re.search(
        r'<div class="iar-defects iar-field--c6">.*?<div class="iar-remarks iar-field--c7',
        template,
        re.DOTALL,
    )
    if not defect_block:
        raise SystemExit("Defect block not found")
    template = (
        template[: defect_block.start()]
        + CUTTING_VARIANCE_BLOCK
        + "\n\n        <div class=\"iar-remarks iar-field--c7"
        + template[defect_block.end() :]
    )

    # Remarks ref
    template = template.replace(
        'class="iar-remarks__input"',
        'ref="remarksInputRef"\n              class="iar-remarks__input"',
        1,
    )

    # Table filter
    filter_block = re.search(
        r'<el-select\s+v-model="inspectorFilterId".*?</el-select>',
        template,
        re.DOTALL,
    )
    if not filter_block:
        raise SystemExit("Filter block not found")
    template = template[: filter_block.start()] + CUTTING_TABLE_FILTER + template[filter_block.end() :]

    # Table columns (first column through remarks, before operation column)
    cols_block = re.search(
        r'<el-table-column label="生産日".*?<el-table-column prop="manual_registration_note".*?/>',
        template,
        re.DOTALL,
    )
    if not cols_block:
        raise SystemExit("Table columns block not found")
    template = template[: cols_block.start()] + CUTTING_TABLE_COLUMNS + template[cols_block.end() :]

    style = style.rstrip()
    if ".iar-variance" not in style:
        style = style[:- len("</style>")] + EXTRA_STYLE + "\n</style>\n"

    out = CUTTING_SCRIPT + template + style
    DST.write_text(out, encoding="utf-8")
    print(f"Wrote {DST} ({len(out.splitlines())} lines)")


if __name__ == "__main__":
    main()
