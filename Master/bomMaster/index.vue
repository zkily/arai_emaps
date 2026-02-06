<template>
  <div class="bom-master-page">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <h1 class="page-title">
            <el-icon>
              <Document />
            </el-icon> 部品構成マスタ（BOM）
          </h1>
          <div class="header-actions">
            <el-button type="primary" @click="handleAddBom">
              <el-icon>
                <Plus />
              </el-icon> 新規構成
            </el-button>
            <el-button type="success" @click="bomManager.switchToTab('reverse')">
              <el-icon>
                <Search />
              </el-icon> 逆引き検索
            </el-button>
          </div>
        </div>
        <div class="tabs-header">
          <el-tabs v-model="bomManager.activeTabName.value" type="card">
            <el-tab-pane name="list" label="構成一覧">
              <!-- タブコンテンツは下部に表示 -->
            </el-tab-pane>
            <el-tab-pane name="reverse" label="逆引き検索">
              <!-- タブコンテンツは下部に表示 -->
            </el-tab-pane>
          </el-tabs>
        </div>
      </template>

      <!-- タブコンテンツ -->
      <div class="tab-content">
        <!-- 構成一覧 -->
        <BomList v-if="bomManager.activeTabName.value === 'list'" ref="bomListRef" />

        <!-- 逆引き検索 -->
        <BomReverseView v-if="bomManager.activeTabName.value === 'reverse'" />
      </div>
    </el-card>

    <!-- Drawer for BOM Tree -->
    <el-drawer v-model="bomManager.showBomTree.value" title="BOM構成展開" size="50%" direction="rtl" :with-header="true"
      destroy-on-close>
      <div class="drawer-header">
        <h3>
          <el-icon>
            <Operation />
          </el-icon>
          製品: {{ bomManager.selectedProduct.value?.product_name }}
        </h3>
        <el-button type="primary" size="small" @click="handleExportTree">
          <el-icon>
            <Download />
          </el-icon> エクスポート
        </el-button>
      </div>
      <BomTreeView v-if="bomManager.selectedProduct.value?.product_id"
        :productId="bomManager.selectedProduct.value?.product_id" ref="treeViewRef" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import BomList from './BomList.vue'
import BomReverseView from './BomReverseView.vue'
import BomTreeView from './BomTreeView.vue'
import { Document, Plus, Search, Operation, Download } from '@element-plus/icons-vue'
import { provideBomManager, BOM_MANAGER_KEY } from './composables/useBomManager'

// BOM管理機能を初期化して提供
const bomManager = provideBomManager()

// コンポーネント参照
const bomListRef = ref<InstanceType<typeof BomList> | null>(null)
const treeViewRef = ref<InstanceType<typeof BomTreeView> | null>(null)

// 新規BOM追加処理
const handleAddBom = () => {
  if (bomListRef.value) {
    bomListRef.value.handleAdd()
  }
}

// ツリーデータのエクスポート
const handleExportTree = () => {
  if (!treeViewRef.value) return

  // CSV形式でエクスポート
  const exportData = (data: any[], level = 0) => {
    let csv = ''
    data.forEach(item => {
      // レベル、部品名、数量、単価の順にCSV行を作成
      const indent = '  '.repeat(level)
      csv += `"${indent}${level === 0 ? '■' : '├'} ${item.component_name}","${item.quantity}","${item.unit_price || 0}"\n`

      // 子要素がある場合は再帰的に処理
      if (item.children && item.children.length) {
        csv += exportData(item.children, level + 1)
      }
    })
    return csv
  }

  const treeData = treeViewRef.value.treeData
  const header = '"部品名","数量","単価"\n'
  const csv = header + exportData(treeData)

  // ダウンロード処理
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `BOM_${bomManager.selectedProduct.value?.product_name || 'export'}.csv`
  link.click()
  window.URL.revokeObjectURL(url)
}

// 親コンポーネントのキーとして自身を提供
provide('bomMasterPage', {
  showBomTree: (product: { product_id: number, product_name: string }) => {
    bomManager.openBomTree(product)
  }
})
</script>

<style scoped>
.bom-master-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.main-card {
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 24px;
  color: #303133;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.tabs-header {
  margin-top: 16px;
}

.tab-content {
  padding: 16px 0;
}

.drawer-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}

.drawer-header h3 {
  margin: 0;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
