<template>
  <div class="process-master-container">
    <div class="page-header">
      <div class="header-content">
        <div class="title-row">
          <span class="title-icon">⚙️</span>
          <h1 class="main-title">{{ t('master.process.title') }}</h1>
          <div class="stat-badge">
            <span class="stat-number">{{ tableData.length }}</span>
            <span class="stat-label">{{ t('master.common.items') }}</span>
          </div>
        </div>
        <div class="header-buttons">
          <el-button type="warning" @click="generateAndPrintQRCodes" :icon="Printer" class="qr-btn" size="small">
            🏷️ {{ t('master.process.qrPrint') }}
          </el-button>
          <el-button type="primary" @click="openAddDialog" class="add-btn" size="small">
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
            <el-tag v-if="row.category" size="small" effect="plain" class="category-tag">{{ getCategoryLabel(row.category) }}</el-tag>
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
        <el-table-column :label="t('master.common.actions')" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" plain @click="openEditDialog(row)" class="action-btn">✏️</el-button>
              <el-button size="small" type="danger" plain @click="handleDelete(row.id)" class="action-btn">🗑️</el-button>
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
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Printer } from '@element-plus/icons-vue'
import { fetchProcesses, deleteProcess } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import ProcessEditDialog from './ProcessEditDialog.vue'

const { t } = useI18n()

const tableData = ref<ProcessItem[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const editTarget = ref<ProcessItem | null>(null)

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

const openAddDialog = () => { dialogMode.value = 'add'; editTarget.value = null; dialogVisible.value = true }
const openEditDialog = (row: ProcessItem) => { dialogMode.value = 'edit'; editTarget.value = { ...row }; dialogVisible.value = true }

const handleDelete = async (id: number | undefined) => {
  if (id == null) return
  try {
    await ElMessageBox.confirm(t('master.process.confirmDelete'), t('common.confirm'), { confirmButtonText: t('master.common.delete'), cancelButtonText: t('master.common.cancel'), type: 'warning' })
    await deleteProcess(id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch { /* cancelled */ }
}

const generateAndPrintQRCodes = async () => {
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
</style>
