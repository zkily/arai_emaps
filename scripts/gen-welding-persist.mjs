import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..')
const p = path.join(root, 'frontend/src/views/mes/actualDataCollection')

let s = fs.readFileSync(path.join(p, 'inspection/inspectionActualPersist.ts'), 'utf8')
s = s
  .replace(/INSPECTION_ACTUAL_PERSIST_KEY/g, 'WELDING_ACTUAL_PERSIST_KEY')
  .replace(/inspectionActual/g, 'weldingActual')
  .replace(/InspectionActualPersistStoreV2/g, 'WeldingActualPersistStoreV2')
  .replace(/InspectionActualPagePersistSnapshot/g, 'WeldingActualPagePersistSnapshot')
  .replace(/inspectorUserId/g, 'operatorUserId')
  .replace(
    /export function makePersistScopeKey\(productionDay: string\): string \{\n  const day = \(productionDay \?\? ''\)\.trim\(\) \|\| '—'\n  return day\n\}/,
    `export function makePersistScopeKey(productionDay: string, machineId: number | null): string {
  const day = (productionDay ?? '').trim() || '—'
  return \`\${day}::\${machineId ?? 'none'}\`
}`,
  )
  .replace(
    /export interface WeldingActualPersistStoreV2 \{\n  v: 2\n  productionDay: string\n  operatorUserId/,
    `export interface WeldingActualPersistStoreV2 {
  v: 2
  productionDay: string
  selectedWeldingMachineId: number | null
  operatorUserId`,
  )
  .replace(
    /export interface WeldingActualPagePersistSnapshot \{\n  productionDay: string\n  operatorUserId/,
    `export interface WeldingActualPagePersistSnapshot {
  productionDay: string
  selectedWeldingMachineId: number | null
  operatorUserId`,
  )
  .replace(
    /function emptyStoreV2\(\): WeldingActualPersistStoreV2 \{\n  return \{\n    v: 2,\n    productionDay: '',\n    operatorUserId: null,/,
    `function emptyStoreV2(): WeldingActualPersistStoreV2 {
  return {
    v: 2,
    productionDay: '',
    selectedWeldingMachineId: null,
    operatorUserId: null,`,
  )
  .replace(
    /productionDay: typeof parsed\.productionDay === 'string' \? parsed\.productionDay : '',\n      operatorUserId:/,
    `productionDay: typeof parsed.productionDay === 'string' ? parsed.productionDay : '',
      selectedWeldingMachineId:
        parsed.selectedWeldingMachineId != null &&
        Number.isFinite(Number(parsed.selectedWeldingMachineId))
          ? Number(parsed.selectedWeldingMachineId)
          : null,
      operatorUserId:`,
  )
  .replace(
    /const key = makePersistScopeKey\(store\.productionDay\)/g,
    'const key = makePersistScopeKey(store.productionDay, store.selectedWeldingMachineId)',
  )
  .replace(
    /const key = makePersistScopeKey\(payload\.productionDay\)/g,
    'const key = makePersistScopeKey(payload.productionDay, payload.selectedWeldingMachineId)',
  )
  .replace(
    /store\.productionDay = payload\.productionDay\n    store\.operatorUserId/g,
    'store.productionDay = payload.productionDay\n    store.selectedWeldingMachineId = payload.selectedWeldingMachineId\n    store.operatorUserId',
  )
  .replace(
    /export function getScopeSessions\(\n  productionDay: string,\n\):/,
    'export function getScopeSessions(\n  productionDay: string,\n  machineId: number | null,\n):',
  )
  .replace(
    /const key = makePersistScopeKey\(productionDay\)\n  const scope = store\.scopes\[key\]/,
    'const key = makePersistScopeKey(productionDay, machineId)\n  const scope = store.scopes[key]',
  )
  .replace(
    /export function applyPersistedSessionsForScope\(\n  scopeDay: string,\n  rowIds: number\[\],/,
    'export function applyPersistedSessionsForScope(\n  scopeDay: string,\n  machineId: number | null,\n  rowIds: number[],',
  )
  .replace(
    /const scopeSessions = getScopeSessions\(scopeDay\)/,
    'const scopeSessions = getScopeSessions(scopeDay, machineId)',
  )
  .replace(/\*\* MES 検査実績収集/, '/** MES 溶接実績収集')

const monitor = `
export interface WeldingPersistMachineActivity {
  machineId: number
  planId: number
  paused: boolean
}

export function collectWeldingPersistForMonitorDay(productionDay: string): {
  sessionsByPlanId: Map<number, PersistedPlanSession>
  machineActivities: WeldingPersistMachineActivity[]
} {
  const sessionsByPlanId = new Map<number, PersistedPlanSession>()
  const machineActivities: WeldingPersistMachineActivity[] = []
  const store = loadStore()
  if (!store) return { sessionsByPlanId, machineActivities }
  const day = (productionDay ?? '').trim()
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(day)) return { sessionsByPlanId, machineActivities }
  const prefix = \`\${day}::\`
  const now = Date.now()
  for (const [scopeKey, scope] of Object.entries(store.scopes)) {
    if (!scopeKey.startsWith(prefix)) continue
    if (now - scope.savedAt > PERSIST_TTL_MS) continue
    const machinePart = scopeKey.slice(prefix.length)
    if (machinePart === 'none') continue
    const machineId = Number(machinePart)
    if (!Number.isFinite(machineId)) continue
    for (const [planIdStr, sess] of Object.entries(scope.sessions ?? {})) {
      const planId = Number(planIdStr)
      if (!Number.isFinite(planId)) continue
      sessionsByPlanId.set(planId, sess)
      if (sess.wallStart != null && sess.wallEnd == null) {
        machineActivities.push({
          machineId,
          planId,
          paused: sess.pauseSliceStart != null || sess.breakSliceStart != null,
        })
      }
    }
  }
  return { sessionsByPlanId, machineActivities }
}

export function getWeldingPersistOperatorUserId(
  productionDay: string,
  machineId: number,
): number | null {
  const store = loadStore()
  if (!store) return null
  const day = (productionDay ?? '').trim()
  if (store.productionDay !== day || store.selectedWeldingMachineId !== machineId) return null
  const id = store.operatorUserId
  if (id == null || !Number.isFinite(Number(id)) || Number(id) <= 0) return null
  return Number(id)
}
`

s = s.replace(/\nexport function loadWeldingActualPersist/, `${monitor}\nexport function loadWeldingActualPersist`)

fs.writeFileSync(path.join(p, 'welding/weldingActualPersist.ts'), s)
console.log('wrote weldingActualPersist.ts', s.length)
