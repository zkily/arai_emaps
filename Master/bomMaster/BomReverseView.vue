<template>
  <div class="bom-reverse-container">
    <!-- コンポーネント選択フォーム -->
    <el-card shadow="hover" class="selection-card">
      <template #header>
        <div class="card-header">
          <h3 class="header-title">
            <el-icon>
              <Connection />
            </el-icon> 部品使用検索
          </h3>
        </div>
      </template>

      <el-form :inline="true" class="selection-form">
        <el-form-item label="部品">
          <el-select v-model="selectedComponentId" filterable placeholder="部品を選択してください" style="width: 350px"
            :loading="loadingComponents" @change="fetchReverseTree">
            <el-option v-for="c in componentOptions" :key="c.id" :label="`${c.component_cd} - ${c.component_name}`"
              :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" :disabled="!selectedComponentId" @click="fetchReverseTree">
            検索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 結果表示 -->
    <el-card v-if="reverseList.length" shadow="hover" class="result-card">
      <template #header>
        <div class="result-header">
          <h3 class="result-title">検索結果</h3>
          <div class="header-actions">
            <el-button type="success" :icon="Download" @click="handleExport">エクスポート</el-button>
            <el-button type="primary" :icon="Printer" @click="handlePrint">印刷</el-button>
          </div>
        </div>
      </template>

      <!-- 結果テーブル -->
      <el-table :data="reverseList" border stripe style="width: 100%" v-loading="loading">
        <el-table-column label="製品CD" prop="product_cd" width="120" sortable />
        <el-table-column label="製品名" prop="product_name" min-width="150" sortable />
        <el-table-column label="使用数量" prop="quantity" width="100" align="right" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        <el-table-column label="レベル" prop="level" width="80" align="center" sortable>
          <template #default="{ row }">
            <el-tag size="small" :type="getLevelType(row.level)" effect="plain">
              Lv{{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="構成パス" prop="path" min-width="300">
          <template #default="{ row }">
            <div class="path-display">
              <el-steps :active="row.level" simple space="12px" finish-status="success">
                <el-step v-for="(item, index) in row.path_items" :key="index" :title="item" />
              </el-steps>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 結果がない場合 -->
    <el-empty v-else-if="searched && !loading" description="使用されている製品が見つかりませんでした" :image-size="200">
      <template #extra>
        <el-button type="primary" @click="resetSearch">検索条件をリセット</el-button>
      </template>
    </el-empty>

    <!-- 初期表示 -->
    <el-card v-else-if="!searched && !loading" shadow="hover" class="instruction-card">
      <div class="instruction-content">
        <el-icon :size="48" class="instruction-icon">
          <InfoFilled />
        </el-icon>
        <h3>部品の使用状況を検索</h3>
        <p>上部の選択ボックスから部品を選択すると、その部品が使われている製品の一覧が表示されます。</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchComponentOptions, fetchBomReverse } from '@/api/master'
import { Search, Download, Printer, Connection, InfoFilled } from '@element-plus/icons-vue'
// @ts-ignore
import type { ComponentOption, BomReverseItem } from '@/types/master'

// データ
const selectedComponentId = ref<number | undefined>(undefined)
const componentOptions = ref<ComponentOption[]>([])
const reverseList = ref<any[]>([])
const loading = ref(false)
const loadingComponents = ref(false)
const searched = ref(false)

// 部品一覧取得
const fetchComponentList = async () => {
  loadingComponents.value = true
  try {
    componentOptions.value = await fetchComponentOptions()
  } catch (e) {
    ElMessage.error('部品一覧の取得に失敗しました')
  } finally {
    loadingComponents.value = false
  }
}

// 逆引き検索
const fetchReverseTree = async () => {
  if (!selectedComponentId.value) return

  loading.value = true
  searched.value = true

  try {
    const raw = await fetchBomReverse(selectedComponentId.value)

    // 結果の整形
    reverseList.value = raw.map(item => {
      // パスを分解
      const pathItems = item.path.split(' < ').map((p: string) => p.trim());

      return {
        product_id: item.product_id,
        product_cd: getProductCode(item.product_id),
        product_name: item.product_name,
        quantity: item.quantity,
        level: item.level,
        path: item.path,
        path_items: pathItems
      }
    })
  } catch (e) {
    ElMessage.error('逆引き検索に失敗しました')
    reverseList.value = []
  } finally {
    loading.value = false
  }
}

// 製品コード取得（実際の実装では製品IDから製品コードを取得する処理が必要）
const getProductCode = (productId: number): string => {
  // コンポーネントオプションから製品コードを検索する（サンプル実装）
  const product = componentOptions.value.find((c: ComponentOption) => c.id === productId)
  return product ? product.component_cd : `P${productId}`
}

// レベルに応じたタグタイプ
const getLevelType = (level: number): 'success' | 'warning' | 'danger' | 'info' => {
  if (level === 1) return 'success'
  if (level === 2) return 'warning'
  if (level >= 3) return 'danger'
  return 'info'
}

// 数値フォーマット
const formatNumber = (val: any) => {
  const num = Number(val)
  return isNaN(num) ? '0' : num.toString()
}

// エクスポート処理
const handleExport = () => {
  const headers = [
    '製品CD', '製品名', '使用数量', 'レベル', '構成パス'
  ]

  const csv = [
    headers.join(','),
    ...reverseList.value.map(row => [
      row.product_cd,
      `"${row.product_name}"`,
      row.quantity,
      row.level,
      `"${row.path}"`
    ].join(','))
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `部品使用状況_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  window.URL.revokeObjectURL(url)
}

// 印刷処理
const handlePrint = () => {
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.warning('ポップアップがブロックされました')
    return
  }

  const componentName = componentOptions.value.find((c: ComponentOption) => c.id === selectedComponentId.value)?.component_name || '選択部品'

  // 印刷用HTML
  const html = `
    <html>
      <head>
        <title>部品使用状況: ${componentName}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { font-size: 18px; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .footer { margin-top: 30px; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <h1>部品使用状況: ${componentName}</h1>
        <table>
          <thead>
            <tr>
              <th>製品CD</th>
              <th>製品名</th>
              <th>使用数量</th>
              <th>レベル</th>
              <th>構成パス</th>
            </tr>
          </thead>
          <tbody>
            ${reverseList.value.map(row => `
              <tr>
                <td>${row.product_cd}</td>
                <td>${row.product_name}</td>
                <td>${row.quantity}</td>
                <td>Lv${row.level}</td>
                <td>${row.path}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        <div class="footer">出力日時: ${new Date().toLocaleString()}</div>
      </body>
    </html>
  `

  printWindow.document.write(html)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.print()
    printWindow.close()
  }
}

// 検索条件リセット
const resetSearch = () => {
  selectedComponentId.value = undefined
  reverseList.value = []
  searched.value = false
}

// ルートから初期値を取得
const route = useRoute()

onMounted(async () => {
  await fetchComponentList()
  const initId = Number(route.query.component_id)
  if (initId) {
    selectedComponentId.value = initId
    await fetchReverseTree()
  }
})
</script>

<style scoped>
.bom-reverse-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selection-card {
  margin-bottom: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 16px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-form {
  display: flex;
  align-items: center;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-title {
  font-size: 16px;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.path-display {
  padding: 8px 0;
}

.instruction-card {
  margin-top: 40px;
}

.instruction-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  text-align: center;
}

.instruction-icon {
  color: #909399;
  margin-bottom: 16px;
}

.instruction-content h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
}

.instruction-content p {
  color: #606266;
  max-width: 500px;
}
</style>
