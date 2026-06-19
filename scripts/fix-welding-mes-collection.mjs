import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const file = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  '../frontend/src/views/mes/actualDataCollection/welding/useWeldingMesCollection.ts',
)
let s = fs.readFileSync(file, 'utf8')

s = s
  .replace(/loadInspectionActualPersist/g, 'loadWeldingActualPersist')
  .replace(/saveInspectionActualPersist/g, 'saveWeldingActualPersist')
  .replace(
    /import \{ getMesClientInstanceId, restoreMesClientInstanceFromUserBackup \} from '\.\/mesClientInstance'/,
    "import { getMesClientInstanceId } from './mesClientInstance'",
  )
  .replace(/getMesClientInstanceId\(operatorUserId\.value\)/g, 'getMesClientInstanceId()')
  .replace(/restoreMesClientInstanceFromUserBackup\(operatorUserId\.value\)\n/g, '')
  .replace(/bindContextFromInspector/g, 'bindContextFromSelection')
  .replace(/canInspectorReclaimRow/g, 'canOperatorReclaimRow')
  .replace(
    /function canOperatorReclaimRow\(row: WeldingMgmtRow \| null \| undefined\): boolean \{\n    if \(!row\?\.id \|\| !rowServerMesInProgress\(row\)\) return false\n    const ri = rowOperatorId\(row\)\n    const uid = operatorUserId\.value\n    return ri != null && uid != null && ri === uid\n  \}/,
    `function canOperatorReclaimRow(row: WeldingMgmtRow | null | undefined): boolean {
    if (!row?.id || !rowServerMesInProgress(row)) return false
    const ri = rowOperatorId(row)
    const op = operatorUserId.value
    return ri != null && op != null && ri === op
  }`,
  )

// bindContextFromSelection with machine priority
s = s.replace(
  /\/\*\* 溶接員切替時：当該溶接員の生産中行を優先してフォーカス \*\/\n  function bindContextFromSelection\(\): void \{[\s\S]*?bindActivePlanFromSelection\(\)\n  \}/,
  `/** 設備・溶接作業者切替時：在産行を優先してフォーカス */
  function bindContextFromSelection(): void {
    const inProgMachine = findInProgressRowForMachine()
    if (
      inProgMachine?.product_cd &&
      inProgMachine.id != null &&
      isPlanLocallyOperated(inProgMachine.id)
    ) {
      selectedProductCode.value = inProgMachine.product_cd
      activePlanId.value = inProgMachine.id
      const ri = rowOperatorId(inProgMachine)
      if (ri != null) operatorUserId.value = ri
      return
    }
    const opId = operatorUserId.value
    if (opId != null) {
      const inProg = findInProgressRowForOperator(opId)
      if (inProg?.product_cd && inProg.id != null && isPlanLocallyOperated(inProg.id)) {
        selectedProductCode.value = inProg.product_cd
        activePlanId.value = inProg.id
        return
      }
    }
    bindActivePlanFromSelection()
  }`,
)

// Remove next-assignment block
s = s.replace(
  /  async function syncMyNextAssignment\(\): Promise<void> \{[\s\S]*?  function applyNextAssignmentProductSelection\(\): void \{[\s\S]*?selectedProductCode\.value = code\n  \}\n\n/,
  '',
)

// Remove duplicate stub if full block removed; ensure stub exists once
if (!s.includes('const myNextAssignment = ref<null>(null)')) {
  s = s.replace(
    /  const inProgressRows = computed/,
    `  const myNextAssignment = ref<null>(null)
  const canApplyNextAssignmentProduct = computed(() => false)
  async function applyNextAssignmentProductSelection(): Promise<void> {}

  const inProgressRows = computed`,
  )
}
s = s.replace(
  /  const canApplyNextAssignmentProduct = computed\(\(\) => false\)\n  async function applyNextAssignmentProductSelection\(\): Promise<void> \{\}\n\n  const inProgressRows = computed[\s\S]*?const canApplyNextAssignmentProduct = computed\(\(\) => false\)\n  async function applyNextAssignmentProductSelection\(\): Promise<void> \{\}\n\n  const inProgressRows = computed/,
  `  const myNextAssignment = ref<null>(null)
  const canApplyNextAssignmentProduct = computed(() => false)
  async function applyNextAssignmentProductSelection(): Promise<void> {}

  const inProgressRows = computed`,
)

s = s.replace(/void syncMyNextAssignment\(\)/g, '')
s = s.replace(/await syncMyNextAssignment\(\)\n/g, '')
s = s.replace(/Promise\.all\(\[[\s\S]*?syncMyNextAssignment\(\),[\s\S]*?\]\)/, (m) =>
  m.replace(/,?\s*syncMyNextAssignment\(\),?/, ''),
)

// Fix applyPersistedSessionsForScope call
s = s.replace(
  /const restored = applyPersistedSessionsForScope\(\n        dayStr,\n        rows\.map\(\(r\) => r\.id\),/,
  `const restored = applyPersistedSessionsForScope(
        dayStr,
        selectedWeldingMachineId.value,
        rows.map((r) => r.id),`,
)

// operatorLabel
s = s.replace(
  /const operatorLabel = computed\(\(\) => operatorLabel\.value\)/,
  `const operatorLabel = computed(() => {
    const id = operatorUserId.value
    if (id == null) return ''
    return operatorNameById(id)
  })`,
)

// Remove login-must-match checks
s = s.replace(
  /\n    if \(ri !== operatorUserId\.value\) \{\n      ElMessage\.warning\(t\('mesWeldingActual\.inspectorMustMatchLogin'\)\)\n      return\n    \}/g,
  '',
)
s = s.replace(
  /\n    if \(draft\.operatorUserId !== operatorUserId\.value\) \{\n      ElMessage\.warning\(t\('mesWeldingActual\.inspectorMustMatchLogin'\)\)\n      return\n    \}/g,
  '',
)
s = s.replace(/ElMessage\.warning\(t\('mesWeldingActual\.loginRequiredForInspector'\)\)\n      return\n/g, '')

// operators type
s = s.replace(
  /operators\.value = res\?\.items \?\? \[\]/,
  'operators.value = (res?.items ?? []) as UserListItem[]',
)

fs.writeFileSync(file, s)
console.log('fixed composable', s.length)
