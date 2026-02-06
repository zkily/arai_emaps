<template>
  <div class="process-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">⚙️</el-icon>
            工程マスタ管理
          </h1>
          <p class="subtitle">工程情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ tableData.length }}</div>
            <div class="stat-label">総工程数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区 -->
    <div class="action-section">
      <div class="action-header">
        <div class="action-title">
          <span>操作</span>
        </div>
        <div class="action-buttons">
          <el-button
            type="warning"
            @click="generateAndPrintQRCodes"
            :icon="Printer"
            class="qr-code-btn"
          >
            QRコード印刷
          </el-button>
          <el-button type="primary" @click="openAddDialog" class="add-btn">工程追加</el-button>
        </div>
      </div>
    </div>

    <!-- 主表格卡片 -->
    <el-card class="table-card">
      <el-table :data="tableData" border stripe v-loading="loading" class="modern-table">
        <el-table-column label="コード" prop="process_cd" width="80" align="center" />
        <el-table-column label="名称" prop="process_name" min-width="80" />
        <el-table-column label="略称" prop="short_name" />
        <el-table-column label="分類" prop="category" width="100" />
        <el-table-column label="区分" prop="is_outsource" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_outsource ? 'danger' : 'success'">
              {{ row.is_outsource ? '外注' : '社内' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="標準サイクル(s)"
          prop="default_cycle_sec"
          width="150"
          align="center"
        />
        <el-table-column label="歩留(%)" prop="default_yield" width="90" align="center" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" link @click="openEditDialog(row)"
                >編集</el-button
              >
              <el-button size="small" type="danger" link @click="handleDelete(row.id)"
                >削除</el-button
              >
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="result-section">
      <div class="result-info">表示件数: {{ tableData.length }}件</div>
    </div>

    <!-- ✏️ ダイアログ -->
    <ProcessEditDialog
      v-model:visible="dialogVisible"
      :mode="dialogMode"
      :initialData="editTarget"
      @saved="fetchList"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Printer } from '@element-plus/icons-vue'
import { fetchProcesses, deleteProcess } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import ProcessEditDialog from './ProcessEditDialog.vue'

const tableData = ref<ProcessItem[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const editTarget = ref<ProcessItem | null>(null)

const fetchList = async () => {
  loading.value = true
  try {
    const res = await fetchProcesses({
      keyword: '',
      page: 1,
      pageSize: 100,
    })
    tableData.value = res.list
  } catch (err) {
    console.error('工程一覧取得失敗', err)
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  dialogMode.value = 'add'
  editTarget.value = null
  dialogVisible.value = true
}

const openEditDialog = (row: ProcessItem) => {
  dialogMode.value = 'edit'
  editTarget.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('この工程を削除してもよろしいですか？', '確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
    await deleteProcess(id)
    ElMessage.success('削除しました')
    fetchList()
  } catch {
    // Cancel の場合は無視
  }
}

// 生成并打印所有工程CD的二维码
const generateAndPrintQRCodes = async () => {
  const processesToUse = tableData.value

  if (processesToUse.length === 0) {
    ElMessage.warning('印刷する工程がありません')
    return
  }

  try {
    // 动态导入 qrcode 库
    let QRCode: any
    try {
      QRCode = (await import('qrcode')).default
    } catch (error) {
      ElMessage.error(
        'QRコードライブラリが見つかりません。以下のコマンドでインストールしてください: npm install qrcode',
      )
      return
    }

    // 创建打印窗口内容
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください')
      return
    }

    // 按工程CD排序
    const sortedProcesses = [...processesToUse].sort((a, b) => {
      const codeA = a.process_cd || ''
      const codeB = b.process_cd || ''
      return codeA.localeCompare(codeB)
    })

    // 生成所有二维码（去掉代码前两位）
    const qrCodes: Array<{
      dataUrl: string
      process_cd: string
      process_code: string
      process_name: string
    }> = []
    for (const process of sortedProcesses) {
      if (process.process_cd) {
        try {
          // 去掉代码前两位，例如：KT01 → 01
          const processCode =
            process.process_cd.length > 2 ? process.process_cd.substring(2) : process.process_cd

          const qrDataUrl = await QRCode.toDataURL(processCode, {
            width: 95,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF',
            },
          })
          qrCodes.push({
            dataUrl: qrDataUrl,
            process_cd: process.process_cd,
            process_code: processCode,
            process_name: process.process_name || '',
          })
        } catch (error) {
          console.error(`QRコード生成エラー (${process.process_cd}):`, error)
        }
      }
    }

    if (qrCodes.length === 0) {
      printWindow.close()
      ElMessage.error('QRコードの生成に失敗しました')
      return
    }

    // 创建打印HTML（A4纸纵向布局）
    const qrCodesPerRow = 4 // A4纵向每行4个
    const qrCodesPerPage = 28 // A4纵向可以放28个二维码（每行4个，共7行）
    const totalPages = qrCodes.length > 0 ? Math.ceil(qrCodes.length / qrCodesPerPage) : 0

    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>工程QRコード印刷</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 0;
          }
          body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
          }
          .page {
            width: 210mm;
            height: 297mm;
            padding: 12mm;
            margin: 0;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
          }
          .page:not(:last-child) {
            page-break-after: always;
          }
          .page:last-child {
            page-break-after: avoid;
          }
          .page-title {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8mm;
            color: #333;
            flex-shrink: 0;
          }
          .qr-grid {
            display: grid;
            grid-template-columns: repeat(${qrCodesPerRow}, 1fr);
            grid-template-rows: repeat(7, 1fr);
            gap: 1.5mm;
            width: 100%;
            height: 100%;
            align-content: start;
          }
          .qr-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1mm;
            border: 1px solid #ddd;
            border-radius: 2px;
            page-break-inside: avoid;
            box-sizing: border-box;
          }
          .qr-code {
            width: 70px;
            height: 70px;
            margin-bottom: 2px;
            flex-shrink: 0;
          }
          .qr-process-code {
            font-size: 11px;
            font-weight: bold;
            text-align: center;
            color: #000;
            margin-top: 2px;
            padding: 0 2px;
          }
          .qr-process-name {
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            color: #000;
            word-break: break-all;
            line-height: 1.3;
            margin-top: 2px;
            padding: 0 2px;
          }
          @media print {
            body {
              margin: 0;
              padding: 0;
            }
            .page {
              margin: 0;
              padding: 12mm;
            }
          }
        </style>
      </head>
      <body>
    `

    // 生成每一页（横向填充）
    for (let page = 0; page < totalPages; page++) {
      const startIndex = page * qrCodesPerPage
      const endIndex = Math.min(startIndex + qrCodesPerPage, qrCodes.length)

      // 如果这一页没有内容，跳过
      if (startIndex >= qrCodes.length || endIndex <= startIndex) {
        break
      }

      // 获取这一页的二维码数据（已经按工程CD排序）
      const pageQRCodes = qrCodes.slice(startIndex, endIndex)

      // 如果这一页没有数据，跳过（防止空白页）
      if (pageQRCodes.length === 0) {
        break
      }

      html += `<div class="page">`
      html += `<div class="page-title">工程マスタQR</div>`
      html += `<div class="qr-grid">`

      // 横向填充：第1行从左到右，然后第2行从左到右，以此类推
      for (let i = 0; i < pageQRCodes.length; i++) {
        const { dataUrl, process_code, process_name } = pageQRCodes[i]
        // 计算在网格中的位置（横向填充）
        const col = i % qrCodesPerRow // 列索引（0-3）
        const row = Math.floor(i / qrCodesPerRow) // 行索引（0-6）
        const gridColumn = col + 1 // CSS Grid 列从1开始
        const gridRow = row + 1 // CSS Grid 行从1开始

        html += `
          <div class="qr-item" style="grid-column: ${gridColumn}; grid-row: ${gridRow};">
            <img src="${dataUrl}" alt="QRコード" class="qr-code" />
            <div class="qr-process-code">${process_code}</div>
            ${process_name ? `<div class="qr-process-name">${process_name}</div>` : ''}
          </div>
        `
      }

      html += `</div></div>`
    }

    html += `
      </body>
      </html>
    `

    // 写入打印窗口
    printWindow.document.write(html)
    printWindow.document.close()

    // 等待内容加载完成后打印
    printWindow.onload = () => {
      setTimeout(() => {
        let isClosed = false
        let fallbackTimeout: ReturnType<typeof setTimeout> | null = null

        // 关闭窗口的函数
        const closeWindow = () => {
          if (!isClosed) {
            isClosed = true
            // 清除备用定时器
            if (fallbackTimeout) {
              clearTimeout(fallbackTimeout)
              fallbackTimeout = null
            }
            // 延迟关闭，确保打印对话框已经完全关闭
            setTimeout(() => {
              try {
                printWindow.close()
              } catch (error) {
                console.error('窗口关闭エラー:', error)
              }
            }, 100)
          }
        }

        // 监听 afterprint 事件（打印对话框关闭后触发，无论是打印还是取消）
        printWindow.addEventListener('afterprint', closeWindow)

        // 监听窗口焦点变化（当打印对话框关闭，窗口重新获得焦点时）
        let focusTimeout: ReturnType<typeof setTimeout> | null = null
        printWindow.addEventListener('focus', () => {
          // 延迟关闭，确保打印对话框已经完全关闭
          if (focusTimeout) {
            clearTimeout(focusTimeout)
          }
          focusTimeout = setTimeout(() => {
            closeWindow()
          }, 300)
        })

        // 备用方案：如果 afterprint 事件不触发，使用定时器（5秒后自动关闭）
        fallbackTimeout = setTimeout(() => {
          if (!isClosed) {
            closeWindow()
          }
        }, 5000)

        // 开始打印
        printWindow.print()
      }, 250)
    }

    ElMessage.success(`${qrCodes.length}件のQRコードを生成しました`)
  } catch (error) {
    console.error('QRコード生成エラー:', error)
    ElMessage.error('QRコードの生成に失敗しました')
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.process-master-container {
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.4rem;
  color: #2980b9;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 0.85rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #2980b9 0%, #27ae60 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 10px;
  text-align: center;
  min-width: 100px;
  box-shadow: 0 2px 8px rgba(41, 128, 185, 0.2);
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.8rem;
  opacity: 0.9;
  margin-top: 2px;
}

.action-section {
  background: white;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.action-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.action-title {
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.clear-btn {
  color: #718096;
  transition: all 0.3s;
}

.clear-btn:hover {
  color: #2980b9;
  transform: scale(1.05);
}

.add-btn {
  background: linear-gradient(135deg, #27ae60 0%, #2980b9 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(41, 128, 185, 0.18);
  transition: all 0.3s;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(41, 128, 185, 0.23);
}

.qr-code-btn {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3);
  transition: all 0.3s ease;
}

.qr-code-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(243, 156, 18, 0.4);
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 12px;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.result-section {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.result-info {
  color: #7f8c8d;
  font-size: 0.85rem;
}

@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .search-item {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .process-master-container {
    padding: 12px;
  }

  .page-header {
    padding: 18px 10px;
  }

  .main-title {
    font-size: 1.5rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 16px 10px;
  }

  .filter-actions > * {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 14px;
    padding: 14px 8px;
  }

  .search-item {
    grid-column: span 1;
  }

  .filter-summary {
    padding: 10px 10px;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.2rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

@media (prefers-color-scheme: dark) {
  .process-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .action-section,
  .table-card,
  .result-section {
    background: rgba(45, 55, 72, 0.88);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .main-title {
    color: #e2e8f0;
  }

  .subtitle,
  .result-info {
    color: #a0aec0;
  }
}

.table-card,
.page-header,
.action-section,
.result-section {
  animation: fadeInUp 0.6s;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}
</style>
