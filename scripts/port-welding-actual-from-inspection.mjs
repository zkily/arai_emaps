/**
 * Port inspection actual collection → welding actual collection (composable + vue).
 * Run: node scripts/port-welding-actual-from-inspection.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(__dirname, '..')
const inspDir = path.join(root, 'frontend/src/views/mes/actualDataCollection/inspection')
const weldDir = path.join(root, 'frontend/src/views/mes/actualDataCollection/welding')

function replaceAll(s, pairs) {
  let out = s
  for (const [from, to] of pairs) {
    out = out.split(from).join(to)
  }
  return out
}

const commonPairs = [
  ['useInspectionMesCollection', 'useWeldingMesCollection'],
  ['InspectionActualDataCollection', 'WeldingActualDataCollection'],
  ['InspectionMgmtRow', 'WeldingMgmtRow'],
  ['inspectionActualPersist', 'weldingActualPersist'],
  ['inspectionActualOfflineSync', 'weldingActualOfflineSync'],
  ['inspectionActualConfig', 'weldingActualConfig'],
  ['inspectionDataSource', 'weldingDataSource'],
  ['inspectionManagement', 'weldingManagement'],
  ['InspectionManagementListRow', 'WeldingManagementListRow'],
  ['PatchInspectionManagementBody', 'PatchWeldingManagementBody'],
  ['fetchInspectionManagementList', 'fetchWeldingManagementList'],
  ['createInspectionManagement', 'createWeldingManagement'],
  ['patchInspectionManagement', 'patchWeldingManagement'],
  ['INSPECTION_DEFECT_DETECTION_PROCESS_CD', 'WELDING_DEFECT_DETECTION_PROCESS_CD'],
  ['mesInspectionActual', 'mesWeldingActual'],
  ['mes_inspector_user_id', 'mes_operator_user_id'],
  ['inspector_user_id', 'operator_user_id'],
  ['InspectionProductOption', 'WeldingMesProductOption'],
  ['inspectionProductFilter', 'weldingProductFilter'],
  ['filterInspectionProductOptions', 'filterWeldingProductOptions'],
  ['buildClearInspectionMesPatchBody', 'buildClearWeldingMesPatchBody'],
  ['copyInspectionRowFromServer', 'copyWeldingRowFromServer'],
  ['compareInspectionMgmtRows', 'compareWeldingMgmtRows'],
  ['unsubscribeMesInspectionWs', 'unsubscribeMesWeldingWs'],
  ['mes_inspection', 'mes_welding'],
  ['KT09', 'KT07'],
  ['検査', '溶接'],
  ['検査員', '溶接作業者'],
]

// --- composable ---
let comp = fs.readFileSync(path.join(inspDir, 'useInspectionMesCollection.ts'), 'utf8')

// Remove next-assignment imports
comp = comp.replace(
  /  deleteInspectionNextAssignment,\n  fetchInspectionManagementList,\n  fetchMyInspectionNextAssignment,\n/,
  '  fetchWeldingManagementList,\n',
)
comp = comp.replace(
  /  type InspectionNextAssignment,\n  type PatchInspectionManagementBody,/,
  '  type PatchWeldingManagementBody,',
)

// Replace imports block for welding APIs
comp = comp.replace(
  /import { getProductList } from '@\/api\/master\/productMaster'\nimport { getUsers, type PaginatedUserResponse } from '@\/api\/system'\nimport { useUserStore } from '@\/modules\/auth\/stores\/user'/,
  `import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import {
  fetchWeldingMesMachines,
  fetchWeldingMesProducts,
  type WeldingMesMachine,
  type WeldingMesProductOption,
} from '@/api/weldingMesEquipment'`,
)

comp = comp.replace(
  /import { filterInspectionProductOptions } from '\.\/inspectionProductFilter'\n\nexport interface InspectionProductOption \{[^}]+\}\n\n/,
  '',
)

comp = comp.replace(
  /import { resolveInspectionDataSource } from '\.\/inspectionDataSource'\n/,
  "import { resolveWeldingDataSource } from './weldingDataSource'\n",
)

comp = replaceAll(comp, commonPairs)

// Inspector → Operator naming (careful order)
const compPairs = [
  ['inspectorUserId', 'operatorUserId'],
  ['InspectorOption', 'OperatorOption'],
  ['inspectors', 'operators'],
  ['inspectorDisplayNames', 'operatorDisplayNames'],
  ['loadingInspectors', 'loadingOperators'],
  ['loadInspectors', 'loadOperators'],
  ['rowInspectorId', 'rowOperatorId'],
  ['findInProgressRowForInspector', 'findInProgressRowForOperator'],
  ['findOtherActiveRowForInspector', 'findOtherActiveRowForOperator'],
  ['findOpenRowForInspectorProduct', 'findOpenRowForOperatorProduct'],
  ['isInspectorOptionDisabled', 'isOperatorOptionDisabled'],
  ['inspectorOptionLabel', 'operatorOptionLabel'],
  ['inspectorNameById', 'operatorNameById'],
  ['inspectorLabel', 'operatorLabel'],
  ['suppressInspectorUserWatch', 'suppressOperatorUserWatch'],
  ['inspId', 'opId'],
  ['insp_id', 'op_id'],
]
comp = replaceAll(comp, compPairs)

// Remove logged-in inspector / user store block → welding machine + operator
comp = comp.replace(
  /  const userStore = useUserStore\(\)\n  const \{ canCreate/,
  '  const { canCreate',
)

comp = comp.replace(
  /  const loggedInUserId = computed\(\(\) => \{[\s\S]*?\}\)\n\n  const loggedInInspectorLabel = computed\(\(\) => \{[\s\S]*?\}\)\n\n  interface OperatorOption/,
  '  interface OperatorOption',
)

comp = comp.replace(
  /  const myNextAssignment = ref<InspectionNextAssignment \| null>\(null\)\n/,
  '',
)

// Add welding machine state after productionDay
comp = comp.replace(
  /  const productionDay = ref\(getJSTToday\(\)\)\n  const operatorUserId/,
  `  const productionDay = ref(getJSTToday())
  const selectedWeldingMachineId = ref<number | null>(null)
  const machines = ref<WeldingMesMachine[]>([])
  const operatorUserId`,
)

comp = comp.replace(
  /  const loadingProducts = ref\(false\)\n  const loadingOperators/,
  `  const loadingProducts = ref(false)
  const loadingMachines = ref(false)
  const loadingOperators`,
)

comp = comp.replace(
  /  let suppressOperatorUserWatch = false\n  \/\*\* 溶接生産中ストリップ/,
  `  let suppressOperatorUserWatch = false
  let suppressMachineWatch = false
  /** 溶接生産中ストリップ`,
)

// Scope key with machine
comp = comp.replace(
  /function currentScopeKey\(\): string \{\n    return makePersistScopeKey\(\(productionDay\.value \?\? ''\)\.trim\(\)\)\n  \}/,
  `function currentScopeKey(): string {
    return makePersistScopeKey(
      (productionDay.value ?? '').trim(),
      selectedWeldingMachineId.value,
    )
  }

  const selectedWeldingMachineName = computed(() => {
    const id = selectedWeldingMachineId.value
    if (id == null) return ''
    const m = machines.value.find((x) => x.id === id)
    return (m?.machine_name || m?.machine_cd || '').trim()
  })`,
)

// Remove syncInspectorToLoggedInUser and adapt canEditConfirmedHistoryRow
comp = comp.replace(
  /  function syncInspectorToLoggedInUser\(\): void \{[\s\S]*?\}\n\n  function canEditConfirmedHistoryRow/,
  `  function canEditConfirmedHistoryRow`,
)

comp = comp.replace(
  /  function canEditConfirmedHistoryRow\(row: WeldingMgmtRow\): boolean \{\n    if \(!canEdit\.value\) return false\n    const uid = loggedInUserId\.value\n    if \(uid == null\) return false\n    const ri = rowOperatorId\(row\)\n    return ri == null \|\| ri === uid\n  \}/,
  `  function canEditConfirmedHistoryRow(_row: WeldingMgmtRow): boolean {
    return canEdit.value
  }`,
)

comp = comp.replace(
  /  function operatorNameById\(userId: number \| null \| undefined\): string \{\n    if \(userId == null\) return ''\n    if \(userId === loggedInUserId\.value\) return loggedInInspectorLabel\.value\n    return operatorDisplayNames\.value\.get\(userId\) \?\? ''\n  \}/,
  `  function operatorNameById(userId: number | null | undefined): string {
    if (userId == null) return ''
    const hit = operators.value.find((u) => u.id === userId)
    if (hit) return (hit.full_name || hit.username || '').trim() || String(userId)
    return operatorDisplayNames.value.get(userId) ?? ''
  }`,
)

// completed history scope: machine + operator instead of logged-in user only
comp = comp.replace(
  /  function rowMatchesCompletedHistoryScope\(row: WeldingMgmtRow\): boolean \{[\s\S]*?return rowDay === scopeDay\n  \}/,
  `  function rowMatchesCompletedHistoryScope(row: WeldingMgmtRow): boolean {
    if (!isRowProductionCompleted(row)) return false
    const scopeDay = (productionDay.value ?? '').trim().slice(0, 10)
    if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(scopeDay)) return false
    const rowDay = rowProductionDayYmd(row)
    if (rowDay !== scopeDay) return false
    if (!rowMatchesSelectedMachine(row)) return false
    const op = operatorUserId.value
    if (op == null) return true
    const ri = rowOperatorId(row)
    return ri == null || ri === op
  }

  function rowWeldingMachine(row: WeldingMgmtRow): string {
    return (row.welding_machine ?? '').trim()
  }

  function rowMatchesSelectedMachine(row: WeldingMgmtRow): boolean {
    const name = selectedWeldingMachineName.value
    if (!name) return true
    const rm = rowWeldingMachine(row)
    return !rm || rm === name
  }

  function findInProgressRowForMachine(): WeldingMgmtRow | null {
    const machine = selectedWeldingMachineName.value
    if (!machine) return null
    for (const row of managementRows.value) {
      if (!isRowMesProductionActive(row)) continue
      if (rowWeldingMachine(row) === machine) return row
    }
    return null
  }`,
)

// Remove next assignment functions block
comp = comp.replace(
  /  async function refreshMyNextAssignment\(\): Promise<void> \{[\s\S]*?  \}\n\n  let nextAssignmentAutoClearInFlight/,
  '  let nextAssignmentAutoClearInFlight',
)
comp = comp.replace(
  /  let nextAssignmentAutoClearInFlight = false[\s\S]*?  async function applyNextAssignmentProductSelection\(\): Promise<void> \{[\s\S]*?  \}\n\n/,
  '',
)

// Stub next assignment exports for vue compatibility (welding monitor TBD)
const nextStub = `
  const myNextAssignment = ref<null>(null)
  const canApplyNextAssignmentProduct = computed(() => false)
  async function applyNextAssignmentProductSelection(): Promise<void> {}
`

comp = comp.replace(
  /  const inProgressRows = computed/,
  `${nextStub}
  const inProgressRows = computed`,
)

// persist flush includes machine
comp = comp.replace(
  /saveWeldingActualPersist\(\{\n      productionDay: day,\n      operatorUserId:/,
  `saveWeldingActualPersist({
      productionDay: day,
      selectedWeldingMachineId: selectedWeldingMachineId.value,
      operatorUserId:`,
)

comp = comp.replace(
  /function loadLocallyOperatedPlanIds\(day: string\): void \{[\s\S]*?locallyOperatedPlanIds\.value = new Set\(ids\)\n  \}/,
  `function loadLocallyOperatedPlanIds(day: string, machineId: number | null): void {
    const blob = loadWeldingActualPersist()
    const ids =
      blob &&
      makePersistScopeKey(blob.productionDay, blob.selectedWeldingMachineId) ===
        makePersistScopeKey(day, machineId)
        ? blob.operatedPlanIds ?? []
        : []
    locallyOperatedPlanIds.value = new Set(ids)
  }`,
)

// loadPlans machine filter - find calls to loadLocallyOperatedPlanIds(day)
comp = comp.replace(
  /loadLocallyOperatedPlanIds\(dayStr\)/g,
  'loadLocallyOperatedPlanIds(dayStr, selectedWeldingMachineId.value)',
)

// applyPersistedSessionsForScope with machine id
comp = comp.replace(
  /applyPersistedSessionsForScope\(\n      dayStr,\n      rowIds,/,
  `applyPersistedSessionsForScope(
      dayStr,
      selectedWeldingMachineId.value,
      rowIds,`,
)

// restorePageFilters machine
comp = comp.replace(
  /if \(blob\.operatorUserId != null\) operatorUserId\.value = blob\.operatorUserId\n/,
  `if (blob.selectedWeldingMachineId != null) {
      selectedWeldingMachineId.value = blob.selectedWeldingMachineId
    }
    if (blob.operatorUserId != null) operatorUserId.value = blob.operatorUserId
`,
)

// watch machine
const machineWatch = `
  watch(selectedWeldingMachineId, (newId, oldId) => {
    if (suppressMachineWatch) {
      schedulePersist()
      return
    }
    selectedProductCode.value = null
    activePlanId.value = null
    if (newId == null) {
      products.value = []
      managementRows.value = []
      schedulePersist()
      return
    }
    if (oldId != null && newId !== oldId) {
      operatorUserId.value = null
    }
    schedulePersist()
    void loadProducts()
    void loadPlans()
  })
`

if (!comp.includes('watch(selectedWeldingMachineId')) {
  comp = comp.replace(/  watch\(productionDay, \(\) => \{/, `${machineWatch}
  watch(productionDay, () => {`)
}

// loadProducts from welding API
comp = comp.replace(
  /async function loadProducts\(\): Promise<void> \{[\s\S]*?  \}\n\n  async function loadDefectItems/,
  `async function loadMachines(): Promise<void> {
    loadingMachines.value = true
    try {
      machines.value = await fetchWeldingMesMachines()
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesWeldingActual.loadMachinesFailed'))
    } finally {
      loadingMachines.value = false
    }
  }

  async function loadProducts(): Promise<void> {
    const machineId = selectedWeldingMachineId.value
    if (machineId == null) {
      products.value = []
      return
    }
    loadingProducts.value = true
    try {
      products.value = await fetchWeldingMesProducts(machineId)
      const code = selectedProductCode.value
      if (code && !products.value.some((p) => p.product_code === code)) {
        const inProgress =
          activePlanId.value != null && session.value != null && isProductionInProgress(session.value)
        if (!inProgress) selectedProductCode.value = null
      }
    } catch (e) {
      console.error(e)
      products.value = []
      ElMessage.error(t('mesWeldingActual.loadProductsFailed'))
    } finally {
      loadingProducts.value = false
    }
  }

  async function loadDefectItems`,
)

// loadOperators
comp = comp.replace(
  /async function loadOperators\(\): Promise<void> \{[\s\S]*?  \}\n\n  function setupLifecycle/,
  `async function loadOperators(): Promise<void> {
    loadingOperators.value = true
    try {
      const res = (await getUsers({ page: 1, page_size: 500, status: 'active' })) as unknown as PaginatedUserResponse
      operators.value = res?.items ?? []
    } catch {
      ElMessage.error(t('mesWeldingActual.loadOperatorsFailed'))
    } finally {
      loadingOperators.value = false
    }
  }

  function setupLifecycle`,
)

// init
comp = comp.replace(
  /await Promise\.all\(\[loadProducts\(\), loadOperators\(\), loadDefectItems\(\)\]\)\n    await loadPlans\(\)/,
  `await Promise.all([loadMachines(), loadOperators(), loadDefectItems()])
    if (selectedWeldingMachineId.value != null) {
      await loadProducts()
    }
    await loadPlans()`,
)

// return exports
comp = comp.replace(
  /    productionDay,\n    loggedInUserId,\n    loggedInInspectorLabel,/,
  `    productionDay,
    selectedWeldingMachineId,
    machines,
    loadingMachines,`,
)

comp = comp.replace(
  /    inspectors,/,
  '    operators,',
)

comp = comp.replace(
  /    inspectorUserId,/,
  '    operatorUserId,',
)

comp = comp.replace(
  /    loadingInspectors,/,
  '    loadingOperators,',
)

comp = comp.replace(
  /    inspectorNameById,\n    isInspectorOptionDisabled,\n    inspectorOptionLabel,/,
  `    operatorNameById,
    isOperatorOptionDisabled,
    operatorOptionLabel,`,
)

comp = comp.replace(
  /    inspectorLabel,/,
  '    operatorLabel,',
)

// Remove references to loggedInInspectorLabel in return if any left
comp = comp.replace(/loggedInInspectorLabel/g, 'operatorLabel')
comp = comp.replace(/loggedInUserId/g, 'operatorUserId')
comp = comp.replace(/syncInspectorToLoggedInUser\(\)/g, '')

// resolve data source
comp = comp.replace(/resolveInspectionDataSource/g, 'resolveWeldingDataSource')

// ensurePlan create body uses welding_machine
comp = comp.replace(
  /const res = await createWeldingManagement\(\{\n        production_day: day,\n        product_cd: code,\n        product_name: name,\n        mes_operator_user_id: opId,\n      \}\)/,
  `const machine = selectedWeldingMachineName.value
      const res = await createWeldingManagement({
        production_day: day,
        product_cd: code,
        product_name: name,
        welding_machine: machine || undefined,
        mes_operator_user_id: opId,
      })`,
)

fs.writeFileSync(path.join(weldDir, 'useWeldingMesCollection.ts'), comp, 'utf8')
console.log('Wrote useWeldingMesCollection.ts', comp.length)

// --- vue ---
let vue = fs.readFileSync(path.join(inspDir, 'InspectionActualDataCollection.vue'), 'utf8')
vue = replaceAll(vue, commonPairs)
vue = replaceAll(vue, compPairs)
vue = vue.replace(/useInspectionMesCollection/g, 'useWeldingMesCollection')
vue = vue.replace(/inspectionDataSourceTagType/g, 'weldingDataSourceTagType')
vue = vue.replace(/resolveInspectionDataSource/g, 'resolveWeldingDataSource')
vue = vue.replace(/loggedInInspectorLabel/g, 'operatorLabel')
vue = vue.replace(/inspectorUserId/g, 'operatorUserId')
vue = vue.replace(/inspectors/g, 'operators')
vue = vue.replace(/loadingInspectors/g, 'loadingOperators')
vue = vue.replace(/inspectorNameById/g, 'operatorNameById')
vue = vue.replace(/isInspectorOptionDisabled/g, 'isOperatorOptionDisabled')
vue = vue.replace(/inspectorOptionLabel/g, 'operatorOptionLabel')

// Inject welding machine toolbar - find production day section end
const machineToolbar = `
        <div class="toolbar-field-row">
          <span class="toolbar-field-row__label">{{ t('mesWeldingActual.weldingMachine') }}</span>
          <el-select
            v-model="mes.selectedWeldingMachineId.value"
            class="toolbar-field-row__control"
            filterable
            clearable
            :loading="mes.loadingMachines.value"
            :placeholder="t('mesWeldingActual.weldingMachinePlaceholder')"
          >
            <el-option
              v-for="m in mes.machines.value"
              :key="m.id"
              :label="(m.machine_name || m.machine_cd || '').trim() || String(m.id)"
              :value="m.id"
            />
          </el-select>
        </div>
`

if (!vue.includes('weldingMachine')) {
  vue = vue.replace(
    /(<\/div>\s*<\/div>\s*<div class="toolbar-field-row">\s*<span class="toolbar-field-row__label">\{\{ t\('mesWeldingActual\.selectProduct'\))/,
    `${machineToolbar}
        <div class="toolbar-field-row">
          <span class="toolbar-field-row__label">{{ t('mesWeldingActual.selectProduct')`,
  )
}

// Operator select instead of readonly logged-in inspector in toolbar
vue = vue.replace(
  /:model-value="operatorLabel"[\s\S]*?disabled[\s\S]*?readonly/g,
  `v-model="mes.operatorUserId.value"
            class="toolbar-field-row__control"
            filterable
            clearable
            :placeholder="t('mesWeldingActual.inspectorPlaceholder')"`,
)

fs.writeFileSync(path.join(weldDir, 'WeldingActualDataCollection.vue'), vue, 'utf8')
console.log('Wrote WeldingActualDataCollection.vue', vue.length)

// --- weldingDataSource.ts ---
const ds = fs.readFileSync(path.join(inspDir, 'inspectionDataSource.ts'), 'utf8')
  .replace(/Inspection/g, 'Welding')
  .replace(/inspection/g, 'welding')
  .replace(/検査実績収集/g, '溶接実績収集')
fs.writeFileSync(path.join(weldDir, 'weldingDataSource.ts'), ds, 'utf8')
console.log('Wrote weldingDataSource.ts')

console.log('Done. Run type-check and fix remaining issues manually.')
