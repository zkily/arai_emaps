<template>
  <div class="bom-tree-view" v-loading="loading">
    <!-- 合計表示 -->
    <div class="cost-summary">
      <el-statistic title="合計コスト" :value="totalCost" :precision="2" prefix="¥">
        <template #suffix>
          <span class="suffix-label">（税抜）</span>
        </template>
      </el-statistic>
    </div>

    <!-- ツリービュー -->
    <div class="tree-container">
      <el-card shadow="hover">
        <el-tree :data="treeData" :props="treeProps" node-key="id" default-expand-all highlight-current
          :expand-on-click-node="false" :render-after-expand="false">
          <template #default="{ node, data }">
            <div class="tree-node">
              <div class="node-content">
                <div class="component-info">
                  <el-tag size="small" :type="getTagType(data.level)" effect="plain" class="level-tag">
                    Lv{{ data.level }}
                  </el-tag>
                  <span class="component-name">
                    <el-icon>
                      <Box />
                    </el-icon>
                    {{ data.component_name }}
                  </span>
                  <span class="quantity-badge">
                    <el-tag size="small" type="info" effect="plain">
                      x{{ formatNumber(data.quantity) }}
                    </el-tag>
                  </span>
                </div>
                <div class="cost-info">
                  <div class="unit-price">
                    単価: <span class="price">¥{{ formatYen(data.unit_price) }}</span>
                  </div>
                  <div class="subtotal">
                    小計: <span class="price highlight">¥{{ formatYen(calculateSubtotal(data)) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-tree>
      </el-card>
    </div>

    <!-- 凡例 -->
    <div class="legend">
      <span class="legend-title">凡例:</span>
      <div class="legend-items">
        <el-tag size="small" type="success" effect="plain">Lv1: 直接部品</el-tag>
        <el-tag size="small" type="warning" effect="plain">Lv2: サブアセンブリ</el-tag>
        <el-tag size="small" type="danger" effect="plain">Lv3+: 深層部品</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchBomTree } from '@/api/master'
import { Box } from '@element-plus/icons-vue'
// @ts-ignore
import type { BomTreeNode } from '@/types/master'

const props = defineProps<{
  productId: number
}>()

const treeData = ref<BomTreeNode[]>([])
const totalCost = ref(0)
const loading = ref(false)

const treeProps = {
  children: 'children',
  label: 'component_name'
}

// フォーマット関数
const formatYen = (val: any) => {
  const num = Number(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

const formatNumber = (val: any) => {
  const num = Number(val)
  return isNaN(num) ? '0' : num.toString()
}

// レベルに応じたタグタイプを取得
const getTagType = (level: number): 'success' | 'warning' | 'danger' | 'info' => {
  if (level === 1) return 'success'
  if (level === 2) return 'warning'
  if (level >= 3) return 'danger'
  return 'info'
}

// 合計コスト計算
const computeTotalCost = (nodes: BomTreeNode[]): number => {
  return nodes.reduce((acc, node) => {
    const subtotal = calculateSubtotal(node)
    const childrenCost = node.children ? computeTotalCost(node.children) : 0
    return acc + subtotal + childrenCost
  }, 0)
}

// 小計計算
const calculateSubtotal = (node: BomTreeNode): number => {
  return (node.unit_price || 0) * (node.quantity || 0)
}

// ツリーデータ取得
const fetchTree = async () => {
  loading.value = true
  try {
    const res = await fetchBomTree(props.productId)
    treeData.value = res
    totalCost.value = computeTotalCost(res)
  } catch (e) {
    ElMessage.error('構成の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 製品IDが変更されたら再取得
watch(() => props.productId, fetchTree, { immediate: true })

// 公開
defineExpose({
  treeData
})
</script>

<style scoped>
.bom-tree-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 16px;
}

.cost-summary {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.suffix-label {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.tree-container {
  border-radius: 8px;
  overflow: hidden;
}

.tree-node {
  width: 100%;
  padding: 8px 0;
}

.node-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.component-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-tag {
  min-width: 48px;
  text-align: center;
}

.component-name {
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.quantity-badge {
  margin-left: 8px;
}

.cost-info {
  display: flex;
  gap: 16px;
  color: #606266;
  font-size: 14px;
}

.price {
  font-weight: 500;
}

.highlight {
  color: #409eff;
}

.legend {
  margin-top: 8px;
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.legend-title {
  margin-right: 8px;
  font-weight: 500;
}

.legend-items {
  display: flex;
  gap: 8px;
}

:deep(.el-tree-node__content) {
  height: auto !important;
  padding: 4px 0;
}

:deep(.el-tree-node.is-expanded > .el-tree-node__children) {
  padding-left: 28px;
}
</style>
