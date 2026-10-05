<template>
  <div class="process-master-container prc-modern pb-std">
    <div class="page-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">⚙️</span>
          <h1 class="main-title pb-hero-title">{{ t('master.process.title') }}</h1>
          <div class="stat-badge">
            <span class="stat-number">{{ tableData.length }}</span>
            <span class="stat-label">{{ t('master.common.items') }}</span>
          </div>
        </div>
        <div class="header-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
          <div class="stat-card stat-card--inhouse">
            <div class="stat-card-number">{{ inHouseCount }}</div>
            <div class="stat-card-label">{{ t('master.process.inHouse') }}</div>
          </div>
          <div class="stat-card stat-card--outsource">
            <div class="stat-card-number">{{ outsourceCount }}</div>
            <div class="stat-card-label">{{ t('master.process.outsource') }}</div>
          </div>
        </div>
        <div class="header-buttons">
          <el-button v-if="canExport" type="warning" @click="generateAndPrintQRCodes" :icon="Printer" class="qr-btn" size="small">
            🏷️ {{ t('master.process.qrPrint') }}
          </el-button>
          <el-button v-if="canCreate" type="primary" @click="openAddDialog" class="add-btn" size="small">
            ➕ {{ t('master.process.addProcess') }}
          </el-button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <el-table :data="tableData" border stripe v-loading="loading" class="modern-table"
        :header-cell-style="{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }"
        :cell-style="{ padding: '5px 8px', fontSize: '12px' }">
        <el-table-column :label="t('master.process.code')" prop="process_cd" width="90" align="center">
          <template #default="{ row }"><span class="code-cell">{{ row.process_cd }}</span></template>
        </el-table-column>
        <el-table-column :label="t('master.process.name')" prop="process_name" min-width="110">
          <template #default="{ row }"><span class="name-cell">{{ row.process_name }}</span></template>
        </el-table-column>
        <el-table-column :label="t('master.process.shortName')" prop="short_name" width="70" align="center" />
        <el-table-column :label="t('master.process.category')" prop="category" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.category" size="small" effect="plain" :class="['category-tag', `cat-${row.category}`]">{{ getCategoryLabel(row.category) }}</el-tag>
            <span v-else class="empty-cell">-</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.process.isOutsource')" prop="is_outsource" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_outsource ? 'danger' : 'success'" size="small" effect="plain">
              {{ row.is_outsource ? t('master.process.outsource') : t('master.process.inHouse') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.process.cycleSec')" prop="default_cycle_sec" width="90" align="right">
          <template #default="{ row }"><span class="number-cell">{{ row.default_cycle_sec }}</span></template>
        </el-table-column>
        <el-table-column :label="t('master.process.yieldPct')" width="75" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{ row.default_yield != null ? (Number(row.default_yield) * 100).toFixed(1) : '100' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('master.process.unit')" prop="capacity_unit" width="55" align="center" />
        <el-table-column :label="t('master.process.remark')" prop="remark" min-width="100" show-overflow-tooltip />
        <el-table-column v-if="canEdit || canDelete" :label="t('master.common.actions')" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button v-if="canEdit" size="small" type="primary" plain @click="openEditDialog(row)" class="action-btn">✏️</el-button>
              <el-button v-if="canDelete" size="small" type="danger" plain @click="handleDelete(row.id)" class="action-btn">🗑️</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="footer-section">
      <div class="result-info"><el-icon>📊</el-icon><span>{{ t('master.process.displayCountShort', { n: tableData.length }) }}</span></div>
    </div>

    <ProcessEditDialog v-model:visible="dialogVisible" :mode="dialogMode" :initial-data="editTarget" @saved="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Printer } from '@element-plus/icons-vue'
import { fetchProcesses, deleteProcess } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import ProcessEditDialog from './ProcessEditDialog.vue'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete, canExport } = useMasterOperationPermission()

const tableData = ref<ProcessItem[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const editTarget = ref<ProcessItem | null>(null)

const outsourceCount = computed(() => tableData.value.filter((p) => p.is_outsource).length)
const inHouseCount = computed(() => tableData.value.length - outsourceCount.value)

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

const categoryKeyMap: Record<string, string> = {
  cut: 'Cut', chamfer: 'Chamfer', swaging: 'Swaging', forming: 'Forming',
  plating: 'Plating', weld: 'Weld', inspect: 'Inspect', warehouse: 'Warehouse',
}
const getCategoryLabel = (val: string) => {
  const key = categoryKeyMap[val]
  return key ? t(`master.process.category${key}`) : val
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await fetchProcesses({ keyword: '', page: 1, pageSize: 1000 })
    tableData.value = res.list ?? res.data?.list ?? []
  } catch (err) { console.error('工程一覧取得失敗', err) }
  finally { loading.value = false }
}

const openAddDialog = () => {
  if (!guardMasterOperation(canCreate)) return
  dialogMode.value = 'add'; editTarget.value = null; dialogVisible.value = true
}
const openEditDialog = (row: ProcessItem) => {
  if (!guardMasterOperation(canEdit)) return
  dialogMode.value = 'edit'; editTarget.value = { ...row }; dialogVisible.value = true
}

const handleDelete = async (id: number | undefined) => {
  if (!guardMasterOperation(canDelete)) return
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.process.confirmDelete'), t('common.confirm'), { confirmButtonText: t('master.common.delete'), cancelButtonText: t('master.common.cancel'), type: 'warning' })
    await deleteProcess(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch { /* cancelled */ }
}

const generateAndPrintQRCodes = async () => {
  if (!guardMasterOperation(canExport)) return
  if (tableData.value.length === 0) {
    ElMessage.warning(t('master.process.noProcessToPrint'))
    return
  }
  try {
    const QRCode = (await import('qrcode')).default
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error(t('master.process.popupBlocked'))
      return
    }
    const sorted = [...tableData.value].sort((a, b) => (a.process_cd || '').localeCompare(b.process_cd || ''))
    const qrCodes: Array<{ dataUrl: string; code: string; name: string }> = []
    for (const p of sorted) {
      if (p.process_cd) {
        try {
          const code = p.process_cd.length > 2 ? p.process_cd.substring(2) : p.process_cd
          const url = await QRCode.toDataURL(code, { width: 95, margin: 2 })
          qrCodes.push({ dataUrl: url, code, name: p.process_name || '' })
        } catch { /* skip */ }
      }
    }
    if (!qrCodes.length) {
      printWindow.close()
      ElMessage.error(t('master.process.qrGenFailed'))
      return
    }
    const perRow = 4, perPage = 28, pages = Math.ceil(qrCodes.length / perPage)
    let html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>工程QR</title><style>@page{size:A4;margin:0}body{margin:0;font-family:Arial,sans-serif}.page{width:210mm;height:297mm;padding:12mm;box-sizing:border-box;display:flex;flex-direction:column}.page:not(:last-child){page-break-after:always}.page-title{text-align:center;font-size:18px;font-weight:bold;margin-bottom:8mm}.qr-grid{display:grid;grid-template-columns:repeat(${perRow},1fr);gap:1.5mm}.qr-item{display:flex;flex-direction:column;align-items:center;padding:1mm;border:1px solid #ddd;border-radius:2px}.qr-code{width:70px;height:70px;margin-bottom:2px}.qr-code-text{font-size:11px;font-weight:bold}.qr-name{font-size:12px;font-weight:bold;word-break:break-all}</style></head><body>`
    for (let i = 0; i < pages; i++) {
      const items = qrCodes.slice(i * perPage, (i + 1) * perPage)
      if (!items.length) break
      html += '<div class="page"><div class="page-title">' + t('master.process.qrPrintTitle') + '</div><div class="qr-grid">'
      items.forEach(({ dataUrl, code, name }) => { html += `<div class="qr-item"><img src="${dataUrl}" class="qr-code"/><div class="qr-code-text">${code}</div>${name ? `<div class="qr-name">${name}</div>` : ''}</div>` })
      html += '</div></div>'
    }
    html += '</body></html>'
    printWindow.document.write(html); printWindow.document.close()
    printWindow.onload = () => { setTimeout(() => { printWindow.print(); printWindow.addEventListener('afterprint', () => setTimeout(() => printWindow.close(), 100)) }, 250) }
    ElMessage.success(t('master.process.qrGenSuccess', { n: qrCodes.length }))
  } catch (e) {
    console.error(e)
    ElMessage.error(t('master.process.qrGenFailed'))
  }
}

onMounted(() => fetchList())
</script>

<style scoped>
.process-master-container { padding: 12px 16px; background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%); min-height: 100vh; }

.page-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 12px 18px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3); }
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.title-row { display: flex; align-items: center; gap: 10px; }
.title-icon { font-size: 1.4rem; }
.main-title { font-size: 1.3rem; font-weight: 700; margin: 0; color: #fff; }
.stat-badge { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); border-radius: 16px; padding: 3px 10px; display: flex; align-items: center; gap: 4px; margin-left: 8px; }
.stat-number { font-size: 1rem; font-weight: 700; color: #fff; }
.stat-label { font-size: 0.7rem; color: rgba(255,255,255,0.9); }
.header-buttons { display: flex; gap: 8px; }
.qr-btn { background: rgba(243,156,18,0.9); border: none; border-radius: 8px; font-weight: 600; color: #fff; }
.qr-btn:hover { background: rgba(243,156,18,1); }
.add-btn { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; font-weight: 600; color: #fff; }
.add-btn:hover { background: rgba(255,255,255,0.25); }

.table-section { background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 12px; }
.modern-table { width: 100%; }
.code-cell { font-family: 'Consolas', monospace; font-weight: 600; color: #667eea; background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.name-cell { font-weight: 500; color: #1e293b; }
.number-cell { font-family: 'Consolas', monospace; font-weight: 500; color: #374151; }
.category-tag { border-radius: 10px; font-size: 10px; }
.empty-cell { color: #cbd5e1; }
.action-buttons { display: flex; gap: 4px; justify-content: center; }
.action-btn { padding: 3px 8px; font-size: 11px; border-radius: 6px; min-width: 32px; }

.footer-section { background: #fff; border-radius: 10px; padding: 8px 16px; display: flex; align-items: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.result-info { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.85rem; }
.result-info strong { color: #667eea; font-weight: 700; }

@media (max-width: 768px) {
  .process-master-container { padding: 8px; }
  .page-header { padding: 10px 12px; }
  .header-content { flex-direction: column; align-items: stretch; gap: 10px; }
  .title-row { justify-content: center; }
  .header-buttons { width: 100%; justify-content: center; }
  .main-title { font-size: 1.1rem; }
  .action-buttons { flex-direction: column; gap: 3px; }
}

:deep(.el-table) { --el-table-border-color: #e2e8f0; --el-table-row-hover-bg-color: #f0f4ff; }
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background-color: #fafbfc; }
:deep(.el-tag) { border-radius: 10px; font-weight: 500; }

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（工程マスタ / slate→cyan）
 * ============================================================ */
.process-master-container.prc-modern {
  --hx-1: #0f172a;
  --hx-2: #334155;
  --hx-3: #0e7490;
  --hx-4: #06b6d4;
  --hx-deep: #164e63;
  --hx-accent: #0891b2;
  --hx-soft: #ecfeff;
  --hx-soft2: #cffafe;
  --hx-line: #a5f3fc;
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(51, 65, 85, 0.08), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(6, 182, 212, 0.08), transparent 60%),
    #f1f5f9;
}

/* ---------- ヒーローヘッダー ---------- */
.prc-modern .page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 34%, var(--hx-3) 70%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(15, 23, 42, 0.7),
    0 4px 12px -6px rgba(14, 116, 144, 0.4),
    inset 0 0 0 1px rgba(255, 255, 255, 0.14);
}

.prc-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.prc-modern .header-content {
  position: relative;
  z-index: 1;
}

.prc-modern .title-row {
  gap: 12px;
}

.prc-modern .title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  font-size: 20px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.08) 100%);
  border: 1px solid rgba(255, 255, 255, 0.34);
  box-shadow:
    0 4px 0 rgba(2, 6, 23, 0.55),
    0 10px 20px -8px rgba(2, 6, 23, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(6px);
  animation: prcIconSpin 5s ease-in-out infinite;
}

.prc-modern .main-title {
  font-size: 20px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(2, 6, 23, 0.4);
}

.prc-modern .stat-badge {
  border: 1px solid rgba(255, 255, 255, 0.26);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

/* 統計カード：3Dチルト＋グレア＋上端アクセント */
.prc-modern .header-stats {
  display: flex;
  gap: 8px;
  margin-left: auto;
  perspective: 700px;
}

.prc-modern .stat-card {
  --sc: #67e8f9;
  position: relative;
  overflow: hidden;
  min-width: 78px;
  padding: 6px 14px;
  color: #fff;
  text-align: center;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.26);
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(10px);
  box-shadow:
    0 10px 22px -12px rgba(2, 6, 23, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition:
    transform 0.18s ease-out,
    box-shadow 0.25s ease;
}

.prc-modern .stat-card--outsource {
  --sc: #fca5a5;
  background: rgba(2, 6, 23, 0.22);
}

.prc-modern .stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--sc);
}

.prc-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.3) 0%,
    transparent 60%
  );
}

.prc-modern .stat-card:hover {
  box-shadow:
    0 16px 28px -12px rgba(2, 6, 23, 0.7),
    inset 0 1px 0 rgba(255, 255, 255, 0.42);
}

.prc-modern .stat-card:hover::after {
  opacity: 1;
}

.prc-modern .stat-card-number {
  font-size: 1.3rem;
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 1px 6px rgba(2, 6, 23, 0.3);
  transform: translateZ(14px);
}

.prc-modern .stat-card-label {
  margin-top: 2px;
  font-size: 0.7rem;
  font-weight: 600;
  opacity: 0.92;
  white-space: nowrap;
}

/* ヘッダーボタン：ガラス調3Dキーキャップ */
.prc-modern .qr-btn,
.prc-modern .add-btn {
  --k-edge: rgba(2, 6, 23, 0.6);
  --k-glow: rgba(2, 6, 23, 0.45);
  color: #fff;
  font-weight: 700;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.18s ease;
}

.prc-modern .qr-btn,
.prc-modern .qr-btn:hover {
  --k-edge: #92400e;
  --k-glow: rgba(217, 119, 6, 0.55);
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%);
}

.prc-modern .add-btn,
.prc-modern .add-btn:hover {
  --k-edge: #155e75;
  --k-glow: rgba(8, 145, 178, 0.55);
  background: linear-gradient(135deg, #22d3ee 0%, #0891b2 55%, #0e7490 100%);
}

.prc-modern .qr-btn:hover,
.prc-modern .add-btn:hover {
  color: #fff;
  filter: brightness(1.06);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.36);
}

.prc-modern .qr-btn:active,
.prc-modern .add-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow);
}

/* ---------- テーブル ---------- */
.prc-modern .table-section,
.prc-modern .footer-section {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid #cbd5e1;
  box-shadow:
    0 14px 28px -22px rgba(15, 23, 42, 0.45),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

.prc-modern .table-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  pointer-events: none;
  background: linear-gradient(90deg, var(--hx-2) 0%, var(--hx-3) 55%, var(--hx-4) 100%);
}

.prc-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: var(--hx-deep) !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, #f8fafc 0%, var(--hx-soft2) 100%) !important;
  border-bottom: 2px solid #67e8f9 !important;
}

.prc-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-accent);
}

.prc-modern .code-cell {
  display: inline-block;
  color: var(--hx-deep);
  font-size: 11.5px;
  font-weight: 700;
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft2) 100%);
  border-radius: 6px;
  box-shadow:
    inset 0 0 0 1px var(--hx-line),
    0 2px 0 var(--hx-line);
  transition: transform 0.15s ease;
}

.prc-modern .modern-table :deep(.el-table__body tr:hover) .code-cell {
  transform: translateY(-1px);
}

.prc-modern .number-cell {
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

/* 工程区分タグ：区分ごとの色分け */
.prc-modern .category-tag {
  --ct: #64748b;
  color: var(--ct);
  font-weight: 700;
  border-color: color-mix(in srgb, var(--ct) 35%, #fff);
  background: color-mix(in srgb, var(--ct) 9%, #fff);
}

.prc-modern .category-tag.cat-cut {
  --ct: #2563eb;
}

.prc-modern .category-tag.cat-chamfer {
  --ct: #0891b2;
}

.prc-modern .category-tag.cat-swaging {
  --ct: #7c3aed;
}

.prc-modern .category-tag.cat-forming {
  --ct: #0284c7;
}

.prc-modern .category-tag.cat-plating {
  --ct: #ca8a04;
}

.prc-modern .category-tag.cat-weld {
  --ct: #c026d3;
}

.prc-modern .category-tag.cat-inspect {
  --ct: #ea580c;
}

.prc-modern .category-tag.cat-warehouse {
  --ct: #059669;
}

.prc-modern .action-btn {
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.prc-modern .action-btn.el-button--primary {
  box-shadow: 0 2px 0 #bfdbfe;
}

.prc-modern .action-btn.el-button--danger {
  box-shadow: 0 2px 0 #fecaca;
}

.prc-modern .action-btn:hover {
  transform: translateY(-1px);
}

.prc-modern .action-btn.el-button--primary:hover {
  box-shadow:
    0 3px 0 #1e40af,
    0 8px 14px -8px rgba(37, 99, 235, 0.6);
}

.prc-modern .action-btn.el-button--danger:hover {
  box-shadow:
    0 3px 0 #991b1b,
    0 8px 14px -8px rgba(220, 38, 38, 0.6);
}

.prc-modern .action-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

/* ---------- フッター ---------- */
.prc-modern .footer-section {
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft) 100%);
}

.prc-modern .result-info {
  padding: 2px 10px;
  color: var(--hx-deep);
  font-weight: 700;
  border-radius: 999px;
  background: var(--hx-soft2);
  box-shadow: inset 0 0 0 1px var(--hx-line);
}

/* ---------- キーフレーム ---------- */

@keyframes prcIconSpin {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) rotate(0deg);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) rotate(30deg);
  }
}

@media (max-width: 768px) {
  .prc-modern .header-stats {
    margin-left: 0;
    justify-content: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .prc-modern .title-icon {
    animation: none;
  }

  .prc-modern .stat-card {
    transform: none;
    transition: none;
  }
}
</style>
