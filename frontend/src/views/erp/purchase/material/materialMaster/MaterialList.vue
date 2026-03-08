<!-- MaterialList.vue -->
<template>
  <div class="material-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Box />
            </el-icon>
            材料マスタ管理
          </h1>
          <p class="subtitle">材料の登録・編集・仕入先管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ materialList.length }}</div>
            <div class="stat-label">総材料数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeCount }}</div>
            <div class="stat-label">有効材料</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ totalValue.toLocaleString() }}</div>
            <div class="stat-label">総在庫価値（円）</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区 -->
    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">クリア</el-button>
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-material-btn"
            >材料追加</el-button
          >
        </div>
      </div>

      <!-- 筛选区 -->
      <div class="filters-grid">
        <!-- 搜索 -->
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード検索
          </label>
          <el-input
            v-model="filters.keyword"
            placeholder="材料CD・材料名・仕入先・規格"
            clearable
            @input="handleFilter"
            class="filter-input"
          >
            <template #suffix>
              <el-icon v-if="filters.keyword" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
        <!-- 状态 -->
        <div class="filter-item">
          <label class="filter-label"
            ><el-icon> <CircleCheck /> </el-icon>状態</label
          >
          <el-select
            v-model="filters.status"
            placeholder="全て"
            clearable
            @change="handleFilter"
            class="filter-input"
          >
            <el-option label="有効" :value="1">
              <el-tag type="success" size="small">有効</el-tag>
              <span class="status-desc">利用可能</span>
            </el-option>
            <el-option label="無効" :value="0">
              <el-tag type="info" size="small">無効</el-tag>
              <span class="status-desc">利用停止</span>
            </el-option>
          </el-select>
        </div>
        <!-- 材料种类 -->
        <div class="filter-item">
          <label class="filter-label"
            ><el-icon> <Management /> </el-icon>材料種類</label
          >
          <el-select
            v-model="filters.material_type"
            placeholder="全て"
            clearable
            @change="handleFilter"
            class="filter-input"
          >
            <el-option label="鋼材" value="鋼材" />
            <el-option label="鋼管" value="鋼管" />
            <el-option label="樹脂" value="樹脂" />
            <el-option label="アルミ" value="アルミ" />
            <el-option label="その他" value="その他" />
          </el-select>
        </div>
        <!-- 支给区分 -->
        <div class="filter-item">
          <label class="filter-label"
            ><el-icon> <Tickets /> </el-icon>支給区分</label
          >
          <el-select
            v-model="filters.supply_classification"
            placeholder="全て"
            clearable
            @change="handleFilter"
            class="filter-input"
          >
            <el-option label="自給" value="自給" />
            <el-option label="有償" value="有償" />
            <el-option label="無償" value="無償" />
          </el-select>
        </div>
        <!-- 用途 -->
        <div class="filter-item">
          <label class="filter-label"
            ><el-icon> <Tools /> </el-icon>用途</label
          >
          <el-select
            v-model="filters.usegae"
            placeholder="全て"
            clearable
            @change="handleFilter"
            class="filter-input"
          >
            <el-option label="生産用" value="生産用" />
            <el-option label="試作用" value="試作用" />
            <el-option label="支給用" value="支給用" />
            <el-option label="その他" value="その他" />
          </el-select>
        </div>
      </div>

      <!-- 筛选结果摘要 -->
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredList.length }}件 / {{ materialList.length }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag
            v-if="filters.keyword"
            closable
            @close="clearKeywordFilter"
            type="primary"
            size="small"
            >検索: {{ filters.keyword }}</el-tag
          >
          <el-tag
            v-if="filters.status !== ''"
            closable
            @close="clearStatusFilter"
            type="info"
            size="small"
            >状態: {{ filters.status == 1 ? '有効' : '無効' }}</el-tag
          >
          <el-tag
            v-if="filters.material_type"
            closable
            @close="clearMaterialTypeFilter"
            type="success"
            size="small"
            >種類: {{ filters.material_type }}</el-tag
          >
          <el-tag
            v-if="filters.supply_classification"
            closable
            @close="clearSupplyClassificationFilter"
            type="warning"
            size="small"
            >支給: {{ filters.supply_classification }}</el-tag
          >
          <el-tag
            v-if="filters.usegae"
            closable
            @close="clearUsegaeFilter"
            type="danger"
            size="small"
            >用途: {{ filters.usegae }}</el-tag
          >
        </div>
      </div>
    </div>

    <!-- 主表格卡片 -->
    <el-card class="table-card">
      <el-table
        :data="filteredList"
        stripe
        highlight-current-row
        v-loading="loading"
        class="modern-table"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="material_cd" label="材料CD" width="110" align="center" sortable>
          <template #default="{ row }">
            <span class="material-cd">{{ row.material_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="material_name"
          label="材料名"
          min-width="160"
          show-overflow-tooltip
          sortable
        />
        <el-table-column prop="material_type" label="材料種類" width="100" align="center" sortable>
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.material_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="standard_spec" label="規格" width="120" show-overflow-tooltip />
        <el-table-column prop="unit" label="単位" width="60" align="center" />
        <el-table-column prop="diameter" label="直径(mm)" width="90" align="center" sortable>
          <template #default="{ row }">
            <span v-if="row.diameter">{{ row.diameter }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="thickness" label="厚さ(mm)" width="90" align="center" sortable>
          <template #default="{ row }">
            <span v-if="row.thickness">{{ row.thickness }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="pieces_per_bundle" label="束本数" width="80" align="center" sortable>
          <template #default="{ row }">
            <span v-if="row.pieces_per_bundle">{{ row.pieces_per_bundle }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="supply_classification" label="支給区分" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getSupplyClassificationType(row.supply_classification)" size="small">{{
              row.supply_classification
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="usegae" label="用途" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.usegae || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="単価(円/kg)" width="120" align="right" sortable>
          <template #default="{ row }">
            <span v-if="row.unit_price">{{ row.unit_price.toLocaleString() }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全在庫" width="90" align="center" sortable>
          <template #default="{ row }">
            <span v-if="row.safety_stock">{{ row.safety_stock }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状態" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              @change="toggleStatus(row)"
              :loading="row.statusLoading"
              inline-prompt
              active-text="有効"
              inactive-text="無効"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="160" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" link @click="openForm(row)">編集</el-button>
              <el-button size="small" type="info" link @click="viewDetails(row)">詳細</el-button>
              <el-button size="small" type="danger" link @click="deleteMaterial(row.id)"
                >削除</el-button
              >
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="result-section">
      <div class="result-info">表示件数: {{ filteredList.length }} / {{ materialList.length }}</div>
      <div class="result-actions">
        <el-button size="small" @click="exportData" :icon="Download">エクスポート</el-button>
        <el-button size="small" @click="refreshData" :icon="Refresh">更新</el-button>
      </div>
    </div>

    <MaterialEditDialog v-model:visible="formVisible" :data-id="editId" @refresh="fetchList" />

    <!-- 詳細表示ダイアログ -->
    <el-dialog v-model="detailVisible" title="材料詳細情報" width="800px" :destroy-on-close="true">
      <div v-if="selectedMaterial" class="material-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="材料CD">{{
            selectedMaterial.material_cd
          }}</el-descriptions-item>
          <el-descriptions-item label="材料名">{{
            selectedMaterial.material_name
          }}</el-descriptions-item>
          <el-descriptions-item label="材料種類">{{
            selectedMaterial.material_type
          }}</el-descriptions-item>
          <el-descriptions-item label="規格">{{
            selectedMaterial.standard_spec
          }}</el-descriptions-item>
          <el-descriptions-item label="用途">{{ selectedMaterial.usegae }}</el-descriptions-item>
          <el-descriptions-item label="代表品種">{{
            selectedMaterial.representative_model
          }}</el-descriptions-item>
          <el-descriptions-item label="単位">{{ selectedMaterial.unit }}</el-descriptions-item>
          <el-descriptions-item label="直径(mm)">{{
            selectedMaterial.diameter || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="厚さ(mm)">{{
            selectedMaterial.thickness || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="長さ(mm)">{{
            selectedMaterial.length || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="束本数">{{
            selectedMaterial.pieces_per_bundle || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="長尺単重(kg/本)">{{
            selectedMaterial.long_weight || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="支給区分">{{
            selectedMaterial.supply_classification
          }}</el-descriptions-item>
          <el-descriptions-item label="仕入先CD">{{
            selectedMaterial.supplier_cd
          }}</el-descriptions-item>
          <el-descriptions-item label="単重単価(円/kg)">{{
            selectedMaterial.unit_price ? selectedMaterial.unit_price.toLocaleString() : '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="一本単価(円)">{{
            selectedMaterial.single_price ? selectedMaterial.single_price.toLocaleString() : '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="安全在庫">{{
            selectedMaterial.safety_stock || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="リードタイム(日)">{{
            selectedMaterial.lead_time || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="保管場所">{{
            selectedMaterial.storage_location || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="状態">
            <el-tag :type="selectedMaterial.status ? 'success' : 'info'">
              {{ selectedMaterial.status ? '有効' : '無効' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 公差・範囲情報 -->
        <div v-if="hasToleranceData" class="tolerance-section">
          <h4>公差・範囲情報</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="公差範囲">{{
              selectedMaterial.tolerance_range || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="公差１">{{
              selectedMaterial.tolerance_1 || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="公差２">{{
              selectedMaterial.tolerance_2 || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="範囲">{{
              selectedMaterial.range_value || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="最小値">{{
              selectedMaterial.min_value || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="最大値">{{
              selectedMaterial.max_value || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="実力値１">{{
              selectedMaterial.actual_value_1 || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="実力値２">{{
              selectedMaterial.actual_value_2 || '-'
            }}</el-descriptions-item>
            <el-descriptions-item label="実力値３">{{
              selectedMaterial.actual_value_3 || '-'
            }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 備考 -->
        <div v-if="selectedMaterial.note" class="note-section">
          <h4>備考</h4>
          <p class="note-content">{{ selectedMaterial.note }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Filter,
  Refresh,
  Plus,
  Search,
  CircleCheck,
  InfoFilled,
  Management,
  Tickets,
  Tools,
  Download,
} from '@element-plus/icons-vue'
import MaterialEditDialog from './MaterialForm.vue'
import { getMaterialList, deleteMaterialById, updateMaterial } from '@/api/master/materialMaster'
import type { Material as MaterialOrigin } from '@/types/master'

// 扩展 Material 类型，增加 statusLoading 字段
interface Material extends MaterialOrigin {
  statusLoading?: boolean
  supplier?: { name: string }
}

// 筛选相关
const filters = ref({
  keyword: '',
  status: '' as string | number,
  material_type: '',
  supply_classification: '',
  usegae: '',
})

const loading = ref(false)
const materialList = ref<Material[]>([])
const formVisible = ref(false)
const editId = ref<number | null>(null)
const detailVisible = ref(false)
const selectedMaterial = ref<Material | null>(null)

const handleFilter = () => {}

const clearKeywordFilter = () => {
  filters.value.keyword = ''
  handleFilter()
}

const clearStatusFilter = () => {
  filters.value.status = ''
  handleFilter()
}

const clearMaterialTypeFilter = () => {
  filters.value.material_type = ''
  handleFilter()
}

const clearSupplyClassificationFilter = () => {
  filters.value.supply_classification = ''
  handleFilter()
}

const clearUsegaeFilter = () => {
  filters.value.usegae = ''
  handleFilter()
}

const clearFilters = () => {
  filters.value = {
    keyword: '',
    status: '',
    material_type: '',
    supply_classification: '',
    usegae: '',
  }
}

// 统计有効件数
const activeCount = computed(() => materialList.value.filter((row) => row.status == 1).length)

// 计算总在库价值
const totalValue = computed(() => {
  return materialList.value.reduce((total, material) => {
    const value = (material.unit_price || 0) * (material.safety_stock || 0)
    return total + value
  }, 0)
})

const hasActiveFilters = computed(
  () =>
    filters.value.keyword ||
    filters.value.status !== '' ||
    filters.value.material_type ||
    filters.value.supply_classification ||
    filters.value.usegae,
)

// 列表筛选
const filteredList = computed(() => {
  let result = materialList.value
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(
      (row) =>
        row.material_cd?.toLowerCase().includes(keyword) ||
        row.material_name?.toLowerCase().includes(keyword) ||
        row.standard_spec?.toLowerCase().includes(keyword) ||
        row.supplier?.name?.toLowerCase().includes(keyword),
    )
  }
  if (filters.value.status !== '') {
    result = result.filter((row) => row.status === filters.value.status)
  }
  if (filters.value.material_type) {
    result = result.filter((row) => row.material_type === filters.value.material_type)
  }
  if (filters.value.supply_classification) {
    result = result.filter(
      (row) => row.supply_classification === filters.value.supply_classification,
    )
  }
  if (filters.value.usegae) {
    result = result.filter((row) => row.usegae === filters.value.usegae)
  }
  return result
})

// 获取支给区分标签类型
const getSupplyClassificationType = (classification: string) => {
  switch (classification) {
    case '自給':
      return 'success'
    case '有償':
      return 'warning'
    case '無償':
      return 'info'
    default:
      return 'info'
  }
}

// 检查是否有公差数据
const hasToleranceData = computed(() => {
  if (!selectedMaterial.value) return false
  const material = selectedMaterial.value
  return (
    material.tolerance_range ||
    material.tolerance_1 ||
    material.tolerance_2 ||
    material.range_value ||
    material.min_value ||
    material.max_value ||
    material.actual_value_1 ||
    material.actual_value_2 ||
    material.actual_value_3
  )
})

// 数据操作
function fetchList() {
  loading.value = true
  getMaterialList({ keyword: filters.value.keyword })
    .then((res) => {
      console.log('MaterialList fetchList response:', res)
      // res should now be the data array directly from the response interceptor
      materialList.value = (res || []).map((row: MaterialOrigin) => ({
        ...row,
        statusLoading: false,
      }))
    })
    .finally(() => (loading.value = false))
}

function openForm(row: Material | null = null) {
  editId.value = row ? row.id : null
  formVisible.value = true
}

function viewDetails(row: Material) {
  selectedMaterial.value = row
  detailVisible.value = true
}

async function deleteMaterial(id: number) {
  try {
    await ElMessageBox.confirm('この材料を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル',
    })
    await deleteMaterialById(id)
    ElMessage.success('削除しました')
    fetchList()
  } catch {}
}

async function toggleStatus(row: Material) {
  row.statusLoading = true
  try {
    await updateMaterial({ ...row })
    ElMessage.success('状態を更新しました')
  } catch {
    row.status = row.status === 1 ? 0 : 1
    ElMessage.error('状態の更新に失敗しました')
  } finally {
    row.statusLoading = false
  }
}

function handleSortChange({ prop, order }: { prop: string; order: string }) {
  console.log('Sort changed:', prop, order)
  // 这里可以添加排序逻辑
}

function exportData() {
  ElMessage.info('エクスポート機能は準備中です')
}

function refreshData() {
  fetchList()
  ElMessage.success('データを更新しました')
}

onMounted(fetchList)
</script>

<style scoped>
/* 基本容器、头部、统计区块，和customer页面风格一致 */
.material-master-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 8px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 1.8rem;
  color: #2980b9;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 1rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #2980b9 0%, #27ae60 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  text-align: center;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.2);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 操作区块 */
.action-section {
  background: white;
  border-radius: 20px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

/* 筛选标题区 */
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
}

.filter-icon {
  font-size: 1.3rem;
  color: #2980b9;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.clear-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  color: #2980b9;
  transform: scale(1.05);
}

.add-material-btn {
  background: linear-gradient(135deg, #27ae60 0%, #2980b9 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.18);
  transition: all 0.3s;
}

.add-material-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(41, 128, 185, 0.23);
}

.filters-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 24px;
  padding: 32px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-item {
  grid-column: span 1;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 4px;
}

.filter-label .el-icon {
  font-size: 1rem;
  color: #2980b9;
}

.filter-input {
  transition: all 0.3s;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #27ae60;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

.type-desc,
.status-desc {
  font-size: 0.8rem;
  color: #718096;
  margin-left: 8px;
}

/* 筛选摘要 */
.filter-summary {
  padding: 20px 32px;
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
  border-top: 1px solid #e2e8f0;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #4a5568;
  font-weight: 500;
}

.summary-icon {
  color: #2980b9;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filters .el-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.active-filters .el-tag:hover {
  transform: scale(1.05);
}

/* 表格 */
.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 16px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.material-cd {
  font-family: monospace;
  color: #2980b9;
  font-weight: bold;
}

.text-muted {
  color: #a0aec0;
  font-style: italic;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 结果区域 */
.result-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-info {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.result-actions {
  display: flex;
  gap: 8px;
}

/* 詳細ダイアログ */
.material-detail {
  padding: 20px 0;
}

.tolerance-section,
.note-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.tolerance-section h4,
.note-section h4 {
  margin: 0 0 16px;
  color: #2d3748;
  font-size: 1.1rem;
  font-weight: 600;
}

.note-content {
  background: #f7fafc;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #2980b9;
  margin: 0;
  line-height: 1.6;
  color: #4a5568;
}

/* 响应式 */
@media (max-width: 1400px) {
  .filters-grid {
    grid-template-columns: 2fr 1fr 1fr 1fr;
  }

  .filter-item:nth-child(5) {
    grid-column: span 2;
  }
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
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  .search-item {
    grid-column: span 2;
  }

  .filter-item:nth-child(5) {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .material-master-container {
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

  .result-section {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .result-actions {
    justify-content: center;
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

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  .material-master-container {
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

/* 动画效果 */
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

/* ElementPlus覆盖 */
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

:deep(.el-switch) {
  --el-switch-on-color: #2980b9;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: #2d3748;
}

:deep(.el-descriptions__content) {
  color: #4a5568;
}
</style>
