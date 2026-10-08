<template>
  <el-dialog
    :model-value="modelValue"
    title="工程別一覧（設備別 製品・能率・使用材料）"
    width="94%"
    top="3vh"
    class="eepo-dialog"
    append-to-body
    destroy-on-close
    @update:model-value="(v: boolean) => emit('update:modelValue', v)"
    @open="handleOpen"
  >
    <div class="eepo-toolbar">
      <el-radio-group v-model="processType" size="small" @change="loadData">
        <el-radio-button v-for="p in processTypes" :key="p.value" :value="p.value">
          {{ p.label }}
        </el-radio-button>
      </el-radio-group>
      <el-input
        v-model="keyword"
        placeholder="製品名・設備名で検索…"
        clearable
        size="small"
        class="eepo-search"
        @input="scheduleLoad"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <span class="eepo-summary">
        設備 <b>{{ machineCount }}</b> 台 ／ 製品 <b>{{ rows.length }}</b> 件
      </span>
      <el-button
        v-if="canExport"
        type="success"
        size="small"
        :icon="Printer"
        :disabled="rows.length === 0"
        class="eepo-print-btn"
        @click="handlePrint"
      >
        印刷（A3横）
      </el-button>
    </div>

    <div v-loading="loading" class="eepo-body">
      <el-empty v-if="!loading && sections.length === 0" description="データがありません" />
      <section v-for="sec in sections" :key="sec.processType" class="eepo-section">
        <div class="eepo-section-title" :style="{ '--pc': processColor(sec.processType) }">
          {{ sec.label }}工程
          <small>（設備 {{ sec.machines.length }} 台）</small>
        </div>
        <div class="eepo-grid">
          <div
            v-for="m in sec.machines"
            :key="m.machineCd"
            class="eepo-card"
            :style="{ '--pc': processColor(sec.processType) }"
          >
            <div class="eepo-card-head">
              <span class="eepo-card-name">{{ m.machinesName || '—' }}</span>
              <span v-if="m.machineCd" class="eepo-card-cd">{{ m.machineCd }}</span>
              <span class="eepo-card-count">{{ m.rows.length }}品目</span>
            </div>
            <table class="eepo-table">
              <colgroup>
                <col class="c-name" />
                <col class="c-eff" />
                <col class="c-mat" />
              </colgroup>
              <thead>
                <tr>
                  <th>製品名</th>
                  <th>能率</th>
                  <th>使用材料</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in m.rows" :key="r.id">
                  <td class="left">{{ r.product_name || r.product_cd || '—' }}</td>
                  <td class="num">{{ formatRate(r) }}</td>
                  <td class="left">{{ formatMaterials(r) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Printer, Search } from '@element-plus/icons-vue'
import {
  fetchEquipmentEfficiencyByProcess,
  type EquipmentEfficiencyByProcessRow,
} from '@/api/master/equipmentEfficiencyMaster'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const props = defineProps<{
  modelValue: boolean
  initialProcess?: string
  initialKeyword?: string
}>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const { canExport } = useMasterOperationPermission()

const processTypes = [
  { label: '全て', value: 'all' },
  { label: '切断', value: 'cutting' },
  { label: '面取', value: 'chamfering' },
  { label: '成型', value: 'forming' },
  { label: '溶接', value: 'welding' },
  { label: 'メッキ', value: 'plating' },
  { label: '検査', value: 'inspection' },
  { label: 'その他', value: 'other' },
]

const PROCESS_COLORS: Record<string, string> = {
  cutting: '#2563eb',
  chamfering: '#0891b2',
  forming: '#059669',
  welding: '#dc2626',
  plating: '#ca8a04',
  inspection: '#db2777',
  other: '#64748b',
}
const processColor = (pt: string) => PROCESS_COLORS[pt] || '#4d7c0f'
const processLabel = (pt: string) => processTypes.find((p) => p.value === pt)?.label ?? 'その他'

const processType = ref('all')
const keyword = ref('')
const loading = ref(false)
const rows = ref<EquipmentEfficiencyByProcessRow[]>([])

type MachineGroup = { machineCd: string; machinesName: string; rows: EquipmentEfficiencyByProcessRow[] }
type ProcessSection = { processType: string; label: string; machines: MachineGroup[] }

const compareJa = (a: string, b: string): number =>
  a.localeCompare(b, 'ja', { numeric: true, sensitivity: 'base' })

const sections = computed<ProcessSection[]>(() => {
  const byProcess = new Map<string, Map<string, MachineGroup>>()
  for (const r of rows.value) {
    const pt = r.process_type || 'other'
    let machines = byProcess.get(pt)
    if (!machines) {
      machines = new Map()
      byProcess.set(pt, machines)
    }
    const key = `${r.machine_cd || ''}\t${r.machines_name || ''}`
    let g = machines.get(key)
    if (!g) {
      g = { machineCd: r.machine_cd || '', machinesName: r.machines_name || '', rows: [] }
      machines.set(key, g)
    }
    g.rows.push(r)
  }
  const order = processTypes.map((p) => p.value)
  return [...byProcess.entries()]
    .sort(([a], [b]) => order.indexOf(a) - order.indexOf(b))
    .map(([pt, machines]) => ({
      processType: pt,
      label: processLabel(pt),
      machines: [...machines.values()]
        .sort((a, b) => compareJa(a.machinesName || a.machineCd, b.machinesName || b.machineCd))
        .map((g) => ({
          ...g,
          rows: [...g.rows].sort((a, b) => compareJa(a.product_name || '', b.product_name || '')),
        })),
    }))
})

const machineCount = computed(() => sections.value.reduce((n, s) => n + s.machines.length, 0))

const formatRate = (r: EquipmentEfficiencyByProcessRow): string => {
  const rate = r.efficiency_rate
  if (rate == null || Number.isNaN(Number(rate))) return '—'
  const text = Number(rate).toFixed(1)
  return r.unit ? `${text} ${r.unit}` : text
}

const formatMaterials = (r: EquipmentEfficiencyByProcessRow): string => {
  const list = r.materials || []
  if (list.length === 0) return '—'
  return list.map((m) => m.material_name || m.material_cd).join('、')
}

const loadData = async () => {
  loading.value = true
  try {
    const kw = keyword.value.trim()
    const res = (await fetchEquipmentEfficiencyByProcess({
      processType: processType.value,
      ...(kw ? { keyword: kw } : {}),
    })) as Record<string, any>
    const data = res?.data && Array.isArray(res.data.list) ? res.data : res
    rows.value = Array.isArray(data?.list) ? data.list : []
  } catch (error) {
    console.error('工程別一覧の読み込みに失敗:', error)
    ElMessage.error('工程別一覧の読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

let timer: ReturnType<typeof setTimeout> | null = null
const scheduleLoad = () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(loadData, 350)
}

const handleOpen = () => {
  processType.value = props.initialProcess || 'all'
  keyword.value = props.initialKeyword || ''
  loadData()
}

function escHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const buildPrintHtml = (): string => {
  const title = '設備能率 工程別一覧'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const kw = keyword.value.trim()
  const kwLine = kw ? `キーワード：<strong>${escHtml(kw)}</strong>　` : ''

  const sectionsHtml = sections.value
    .map((sec) => {
      const color = processColor(sec.processType)
      const cards = sec.machines
        .map((m) => {
          const body = m.rows
            .map(
              (r) => `<tr>
                <td class="left">${escHtml(r.product_name || r.product_cd || '—')}</td>
                <td class="num">${escHtml(formatRate(r))}</td>
                <td class="left">${escHtml(formatMaterials(r))}</td>
              </tr>`
            )
            .join('')
          return `<div class="card" style="--pc:${color}">
            <div class="card-hd">
              <span class="nm">${escHtml(m.machinesName || '—')}</span>
              ${m.machineCd ? `<span class="cd">${escHtml(m.machineCd)}</span>` : ''}
              <span class="cnt">${m.rows.length}品目</span>
            </div>
            <table>
              <colgroup><col class="c-name" /><col class="c-eff" /><col class="c-mat" /></colgroup>
              <thead><tr><th>製品名</th><th>能率</th><th>使用材料</th></tr></thead>
              <tbody>${body}</tbody>
            </table>
          </div>`
        })
        .join('')
      return `<section class="sec">
        <div class="sec-title" style="--pc:${color}">${escHtml(sec.label)}工程
          <small>（設備 ${sec.machines.length} 台）</small></div>
        <div class="grid">${cards}</div>
      </section>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body {
      margin: 0;
      padding: 8px 10px;
      color: #0f172a;
      font: 9px/1.3 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif;
      background: #fff;
    }
    .hd {
      display: flex;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 6px;
      padding-bottom: 4px;
      border-bottom: 2px solid #365314;
    }
    .tt { font-size: 14px; font-weight: 800; color: #1a2e05; }
    .meta { color: #475569; font-size: 8.5px; }
    .meta strong { color: #334155; }
    .sec { margin-bottom: 8px; }
    .sec + .sec { break-before: page; page-break-before: always; }
    .sec-title {
      font-size: 11px;
      font-weight: 800;
      color: var(--pc);
      margin: 0 0 5px;
      padding-left: 6px;
      border-left: 4px solid var(--pc);
    }
    .sec-title small { font-size: 8.5px; color: #64748b; font-weight: 600; }
    .grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 6px;
      align-items: start;
    }
    .card {
      border: 1px solid #cbd5e1;
      border-top: 3px solid var(--pc);
      border-radius: 4px;
      overflow: hidden;
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .card-hd {
      display: flex;
      align-items: baseline;
      gap: 6px;
      padding: 3px 6px;
      background: #f1f5f9;
      border-bottom: 1px solid #cbd5e1;
    }
    .card-hd .nm { font-size: 10px; font-weight: 800; color: #0f172a; }
    .card-hd .cd { font-family: Consolas, monospace; font-size: 8.5px; color: #475569; }
    .card-hd .cnt { margin-left: auto; font-size: 8px; color: #64748b; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    col.c-name { width: 40%; }
    col.c-eff { width: 18%; }
    col.c-mat { width: 42%; }
    th, td {
      border-top: 1px solid #e2e8f0;
      padding: 2px 4px;
      word-wrap: break-word;
      overflow-wrap: anywhere;
    }
    th + th, td + td { border-left: 1px solid #e2e8f0; }
    th { background: #f8fafc; font-size: 8px; font-weight: 700; color: #334155; text-align: center; }
    tbody tr:nth-child(even) { background: #fafcff; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
    @media print {
      @page { size: A3 landscape; margin: 8mm; }
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">
      ${kwLine}工程：<strong>${escHtml(processLabel(processType.value))}</strong>
      　設備：<strong>${machineCount.value}</strong> 台
      　製品：<strong>${rows.value.length}</strong> 件
      　印刷日時：${escHtml(printedAt)}
    </div>
  </div>
  ${sectionsHtml}
</body>
</html>`
}

const handlePrint = () => {
  if (!guardMasterOperation(canExport)) return
  if (rows.value.length === 0) {
    ElMessage.warning('印刷対象のデータがありません')
    return
  }
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされました')
    return
  }
  printWindow.document.write(buildPrintHtml())
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.print()
    setTimeout(() => printWindow.close(), 400)
  }
}
</script>

<style scoped>
.eepo-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e5e7eb;
}

.eepo-search {
  width: 240px;
}

.eepo-summary {
  font-size: 12px;
  color: #6b7280;
}

.eepo-summary b {
  color: #4d7c0f;
}

.eepo-print-btn {
  margin-left: auto;
}

.eepo-body {
  min-height: 240px;
  max-height: calc(86vh - 120px);
  overflow-y: auto;
  padding: 10px 2px 4px;
}

.eepo-section + .eepo-section {
  margin-top: 16px;
}

.eepo-section-title {
  font-size: 14px;
  font-weight: 800;
  color: var(--pc);
  padding-left: 8px;
  border-left: 4px solid var(--pc);
  margin-bottom: 8px;
}

.eepo-section-title small {
  font-size: 11px;
  color: #6b7280;
  font-weight: 600;
}

.eepo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 10px;
  align-items: start;
}

.eepo-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-top: 3px solid var(--pc);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.eepo-card-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 6px 10px;
  background: color-mix(in srgb, var(--pc) 7%, #fff);
  border-bottom: 1px solid #e2e8f0;
}

.eepo-card-name {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.eepo-card-cd {
  font-family: 'Consolas', monospace;
  font-size: 11px;
  color: #475569;
}

.eepo-card-count {
  margin-left: auto;
  font-size: 11px;
  color: #6b7280;
}

.eepo-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 12px;
}

.eepo-table col.c-name {
  width: 40%;
}

.eepo-table col.c-eff {
  width: 18%;
}

.eepo-table col.c-mat {
  width: 42%;
}

.eepo-table th,
.eepo-table td {
  padding: 3px 8px;
  border-top: 1px solid #f1f5f9;
  overflow-wrap: anywhere;
}

.eepo-table th + th,
.eepo-table td + td {
  border-left: 1px solid #f1f5f9;
}

.eepo-table th {
  background: #f8fafc;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  text-align: center;
}

.eepo-table tbody tr:nth-child(even) {
  background: #fafcff;
}

.eepo-table .left {
  text-align: left;
}

.eepo-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  white-space: nowrap;
}
</style>
