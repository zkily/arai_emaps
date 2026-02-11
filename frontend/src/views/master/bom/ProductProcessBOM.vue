<template>
  <div class="product-process-bom-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Tools />
            </el-icon>
            製品工程BOM管理
          </h1>
          <p class="subtitle">製品工程の設定・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ stats.total || 0 }}</div>
            <div class="stat-label">登録数</div>
          </div>
          <div class="stat-card stat-card-active">
            <div class="stat-number">{{ stats.active_count || 0 }}</div>
            <div class="stat-label">现行</div>
          </div>
          <div class="stat-card stat-card-discontinued">
            <div class="stat-number">{{ stats.discontinued_count || 0 }}</div>
            <div class="stat-label">終息</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button type="primary" @click="handleFilter" :icon="Search" class="search-btn">
            検索
          </el-button>
          <el-button
            type="success"
            @click="handleSync"
            :icon="Refresh"
            class="sync-btn"
            :loading="syncing"
          >
            製品情報同期
          </el-button>
        </div>
      </div>

      <!-- 筛选内容 -->
      <div class="filters-grid">
        <!-- 关键词搜索 -->
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード
          </label>
          <el-input
            v-model="filters.keyword"
            placeholder="製品コードまたは製品名を入力"
            clearable
            @clear="handleFilter"
            @keyup.enter="handleFilter"
            class="filter-input"
          />
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-section">
      <el-card class="table-card" shadow="never">
        <el-table
          :data="bomList"
          v-loading="loading"
          stripe
          border
          style="width: 100%"
          :empty-text="'データがありません'"
          height="calc(100vh - 360px)"
          :row-style="{ height: '40px' }"
          @sort-change="handleSortChange"
          :default-sort="{ prop: 'product_name', order: 'ascending' }"
        >
          <!-- 終息 -->
          <el-table-column label="終息" width="60" align="center" fixed="left">
            <template #default="{ row }">
              <el-checkbox v-model="row.is_discontinued" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column
            prop="product_cd"
            label="製品CD"
            width="70"
            align="center"
            fixed="left"
            show-overflow-tooltip
          />
          <el-table-column
            prop="product_name"
            label="製品名"
            min-width="130"
            fixed="left"
            show-overflow-tooltip
            sortable
            :default-sort="{ prop: 'product_name', order: 'ascending' }"
          />
          <el-table-column label="最低在庫日数" width="110" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.min_stock_days"
                :min="0"
                :max="999"
                :precision="0"
                :controls="false"
                size="small"
                style="width: 100%"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="安全在庫日数" width="110" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.safety_stock_days"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 材料工程 -->
          <el-table-column label="材料工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.material_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="材料工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.material_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.material_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 切断工程 -->
          <el-table-column label="切断工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.cuting_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="切断工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.cuting_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.cuting_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 面取工程 -->
          <el-table-column label="面取工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.chamfering_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="面取工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.chamfering_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.chamfering_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- SW工程 -->
          <el-table-column label="SW工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.swaging_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="SW工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.swaging_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.swaging_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 成型工程 -->
          <el-table-column label="成型工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.forming_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="成型工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.forming_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.forming_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- メッキ工程 -->
          <el-table-column label="メッキ工程" width="90" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.plating_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="メッキ工程LT" width="110" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.plating_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.plating_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 外注メッキ工程 -->
          <el-table-column label="外注メッキ工程" width="120" align="center">
            <template #default="{ row }">
              <el-checkbox
                v-model="row.outsourced_plating_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="外注メッキ工程LT" width="130" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.outsourced_plating_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.outsourced_plating_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 溶接工程 -->
          <el-table-column label="溶接工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.welding_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="溶接工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.welding_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.welding_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 外注溶接工程 -->
          <el-table-column label="外注溶接工程" width="120" align="center">
            <template #default="{ row }">
              <el-checkbox
                v-model="row.outsourced_welding_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="外注溶接工程LT" width="130" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.outsourced_welding_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.outsourced_welding_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 検査工程 -->
          <el-table-column label="検査工程" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.inspection_process" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="検査工程LT" width="100" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.inspection_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.inspection_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 外注倉庫工程 -->
          <el-table-column label="外注倉庫工程" width="120" align="center">
            <template #default="{ row }">
              <el-checkbox
                v-model="row.outsourced_warehouse_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="外注倉庫工程LT" width="130" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.outsourced_warehouse_process_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.outsourced_warehouse_process"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- メッキ前溶接 -->
          <el-table-column label="メッキ前溶接" width="110" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.pre_plating_welding" @change="handleCellChange(row)" />
            </template>
          </el-table-column>

          <!-- 検査後溶接 -->
          <el-table-column label="検査後溶接" width="100" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.post_inspection_welding" @change="handleCellChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="検査後溶接工程LT" width="130" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.post_inspection_welding_lt"
                :min="0"
                :max="999"
                :precision="0"
                size="small"
                :controls="false"
                style="width: 100%"
                :disabled="!row.post_inspection_welding"
                @change="handleCellChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 操作列 -->
          <el-table-column label="操作" width="160" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  size="small"
                  type="primary"
                  :icon="Edit"
                  @click="handleEdit(row)"
                  class="action-btn-edit"
                >
                  編集
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click="handleDelete(row)"
                  class="action-btn-delete"
                >
                  削除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 分页组件 -->
    <div class="pagination-section">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.limit"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        class="pagination"
      />
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="製品工程BOM編集"
      width="1000px"
      :close-on-click-modal="false"
      class="product-process-dialog"
    >
      <el-form :model="formData" label-width="140px" label-position="left" class="edit-form">
        <el-tabs v-model="activeTab" class="edit-tabs">
          <!-- 基本情報 -->
          <el-tab-pane label="基本情報" name="basic">
            <div class="form-grid">
              <el-form-item label="製品CD">
                <el-input v-model="formData.product_cd" disabled size="small" />
              </el-form-item>
              <el-form-item label="製品名">
                <el-input v-model="formData.product_name" disabled size="small" />
              </el-form-item>
              <el-form-item label="最低在庫日数">
                <el-input-number
                  v-model="formData.min_stock_days"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="安全在庫日数">
                <el-input-number
                  v-model="formData.safety_stock_days"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="終息">
                <el-switch v-model="formData.is_discontinued" size="small" />
              </el-form-item>
            </div>
          </el-tab-pane>

          <!-- 材料・切断工程 -->
          <el-tab-pane label="材料・切断工程" name="material">
            <div class="form-grid">
              <el-form-item label="材料 (工程)">
                <el-switch v-model="formData.material_process" size="small" />
              </el-form-item>
              <el-form-item label="材料工程LT" v-if="formData.material_process">
                <el-input-number
                  v-model="formData.material_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="切断 (工程)">
                <el-switch v-model="formData.cuting_process" size="small" />
              </el-form-item>
              <el-form-item label="切断工程LT" v-if="formData.cuting_process">
                <el-input-number
                  v-model="formData.cuting_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="面取 (工程)">
                <el-switch v-model="formData.chamfering_process" size="small" />
              </el-form-item>
              <el-form-item label="面取工程LT" v-if="formData.chamfering_process">
                <el-input-number
                  v-model="formData.chamfering_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="SW (工程)">
                <el-switch v-model="formData.swaging_process" size="small" />
              </el-form-item>
              <el-form-item label="SW工程LT" v-if="formData.swaging_process">
                <el-input-number
                  v-model="formData.swaging_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </el-tab-pane>

          <!-- 成型・メッキ工程 -->
          <el-tab-pane label="成型・メッキ工程" name="forming">
            <div class="form-grid">
              <el-form-item label="成型 (工程)">
                <el-switch v-model="formData.forming_process" size="small" />
              </el-form-item>
              <el-form-item label="成型工程LT" v-if="formData.forming_process">
                <el-input-number
                  v-model="formData.forming_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="メッキ (工程)">
                <el-switch v-model="formData.plating_process" size="small" />
              </el-form-item>
              <el-form-item label="メッキ工程LT" v-if="formData.plating_process">
                <el-input-number
                  v-model="formData.plating_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="外注メッキ (工程)">
                <el-switch v-model="formData.outsourced_plating_process" size="small" />
              </el-form-item>
              <el-form-item label="外注メッキ工程LT" v-if="formData.outsourced_plating_process">
                <el-input-number
                  v-model="formData.outsourced_plating_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </el-tab-pane>

          <!-- 溶接・検査工程 -->
          <el-tab-pane label="溶接・検査工程" name="welding">
            <div class="form-grid">
              <el-form-item label="溶接 (工程)">
                <el-switch v-model="formData.welding_process" size="small" />
              </el-form-item>
              <el-form-item label="溶接工程LT" v-if="formData.welding_process">
                <el-input-number
                  v-model="formData.welding_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="外注溶接 (工程)">
                <el-switch v-model="formData.outsourced_welding_process" size="small" />
              </el-form-item>
              <el-form-item label="外注溶接工程LT" v-if="formData.outsourced_welding_process">
                <el-input-number
                  v-model="formData.outsourced_welding_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="検査 (工程)">
                <el-switch v-model="formData.inspection_process" size="small" />
              </el-form-item>
              <el-form-item label="検査工程LT" v-if="formData.inspection_process">
                <el-input-number
                  v-model="formData.inspection_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="外注倉庫 (工程)">
                <el-switch v-model="formData.outsourced_warehouse_process" size="small" />
              </el-form-item>
              <el-form-item label="外注倉庫工程LT" v-if="formData.outsourced_warehouse_process">
                <el-input-number
                  v-model="formData.outsourced_warehouse_process_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="メッキ前溶接 (工程)">
                <el-switch v-model="formData.pre_plating_welding" size="small" />
              </el-form-item>
              <el-form-item label="検査後溶接 (工程)">
                <el-switch v-model="formData.post_inspection_welding" size="small" />
              </el-form-item>
              <el-form-item label="検査後溶接工程LT" v-if="formData.post_inspection_welding">
                <el-input-number
                  v-model="formData.post_inspection_welding_lt"
                  :min="0"
                  :max="999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button size="small" @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" @click="handleSubmit" :loading="submitting">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Tools, Filter, Refresh, Search, Edit, Delete } from '@element-plus/icons-vue'
import {
  fetchProductProcessBOMList,
  fetchProductProcessBOMById,
  updateProductProcessBOM,
  deleteProductProcessBOM,
  syncProductInfo,
  type ProductProcessBOM,
} from '@/api/master/productProcessBomMaster'

// 数据状态
const bomList = ref<ProductProcessBOM[]>([])
const loading = ref(false)
const syncing = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const activeTab = ref('basic')
const formData = ref<Partial<ProductProcessBOM>>({})
// 保存防抖定时器
const saveTimers = new Map<number, NodeJS.Timeout>()

// 分页状态
const pagination = ref({
  page: 1,
  limit: 20,
  total: 0,
})

// 统计信息
const stats = ref({
  total: 0,
  active_count: 0,
  discontinued_count: 0,
})

// 排序状态
const sortConfig = ref({
  prop: 'product_name',
  order: 'asc', // 'asc' 或 'desc'
})

// 筛选状态
const filters = ref({
  keyword: '',
})

// 布尔值转换辅助函数（优化性能，避免重复代码）
const convertBooleanFields = (item: any): ProductProcessBOM => {
  const boolFields = [
    'material_process',
    'cuting_process',
    'chamfering_process',
    'swaging_process',
    'forming_process',
    'plating_process',
    'outsourced_plating_process',
    'welding_process',
    'outsourced_welding_process',
    'inspection_process',
    'outsourced_warehouse_process',
    'pre_plating_welding',
    'post_inspection_welding',
    'is_discontinued',
  ]

  const converted = { ...item }
  boolFields.forEach((field) => {
    converted[field] = converted[field] === 1 || converted[field] === true
  })

  return converted as ProductProcessBOM
}

// 计算统计信息（基于列表数据）
const calculateStats = (list: ProductProcessBOM[]) => {
  const total = list.length
  let active_count = 0
  let discontinued_count = 0

  list.forEach((item) => {
    // is_discontinued为false表示现行，true表示終息
    if (item.is_discontinued === true) {
      discontinued_count++
    } else {
      active_count++
    }
  })

  return {
    total,
    active_count,
    discontinued_count,
  }
}

// 加载数据（支持分页、筛选和排序）
const loadData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      limit: pagination.value.limit,
    }

    // 添加筛选条件
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword
    }

    // 添加排序条件
    if (sortConfig.value.prop) {
      params.sort_by = sortConfig.value.prop
      params.sort_order = sortConfig.value.order
    }

    const result = (await fetchProductProcessBOMList(params)) as any

    // 处理响应数据
    if (result?.success && result.data) {
      // 分页响应格式
      const { list, total } = result.data
      // 尝试从多个位置获取统计信息
      let active_count = result.data.active_count
      let discontinued_count = result.data.discontinued_count

      // 如果result.data中没有，尝试从result根级别获取
      if (active_count === undefined && result.active_count !== undefined) {
        active_count = result.active_count
      }
      if (discontinued_count === undefined && result.discontinued_count !== undefined) {
        discontinued_count = result.discontinued_count
      }

      const convertedList = (list || []).map(convertBooleanFields)
      bomList.value = convertedList
      pagination.value.total = total || 0

      // 更新统计信息（后端返回：active_count=现行 is_discontinued=0, discontinued_count=終息 is_discontinued=1）
      if (
        active_count !== undefined &&
        active_count !== null &&
        discontinued_count !== undefined &&
        discontinued_count !== null
      ) {
        stats.value = {
          total: total || 0,
          active_count,
          discontinued_count,
        }
      } else {
        // 如果后端没有返回统计，使用默认值0（不应该发生，因为后端应该总是返回统计）
        console.warn('后端未返回统计信息，使用默认值0')
        stats.value = {
          total: total || 0,
          active_count: 0,
          discontinued_count: 0,
        }
      }
    } else if (result?.list) {
      // 兼容旧格式
      const convertedList = (result.list || []).map(convertBooleanFields)
      bomList.value = convertedList
      pagination.value.total = result.total || 0
      // 基于列表数据计算统计
      const calculatedStats = calculateStats(convertedList)
      stats.value = {
        total: result.total || 0,
        active_count: calculatedStats.active_count,
        discontinued_count: calculatedStats.discontinued_count,
      }
    } else if (Array.isArray(result)) {
      // 数组格式（兼容）
      const convertedList = result.map(convertBooleanFields)
      bomList.value = convertedList
      pagination.value.total = result.length
      // 基于列表数据计算统计
      const calculatedStats = calculateStats(convertedList)
      stats.value = {
        total: result.length,
        active_count: calculatedStats.active_count,
        discontinued_count: calculatedStats.discontinued_count,
      }
    } else {
      bomList.value = []
      pagination.value.total = 0
      stats.value = {
        total: 0,
        active_count: 0,
        discontinued_count: 0,
      }
    }
  } catch (error: any) {
    console.error('データの読み込みに失敗:', error)
    const errorMessage =
      error?.response?.data?.message || error?.message || 'データの読み込みに失敗しました'
    ElMessage.error(`データの読み込みに失敗しました: ${errorMessage}`)
    bomList.value = []
    pagination.value.total = 0
    stats.value = {
      total: 0,
      active_count: 0,
      discontinued_count: 0,
    }
  } finally {
    loading.value = false
  }
}

// 单元格变化处理（带防抖自动保存，优化性能）
const handleCellChange = (row: ProductProcessBOM) => {
  if (!row?.product_cd) return

  // 清除之前的定时器
  const existingTimer = saveTimers.get(row.product_cd)
  if (existingTimer) clearTimeout(existingTimer)

  // 设置新的防抖定时器（800ms后保存，减少频繁请求）
  const timer = setTimeout(async () => {
    try {
      await updateProductProcessBOM(row.product_cd, row)
      ElMessage.success({ message: '保存しました', duration: 2000, showClose: false })
      saveTimers.delete(row.product_cd)
    } catch (error) {
      console.error('保存に失敗:', error)
      ElMessage.error({ message: '保存に失敗しました', duration: 3000 })
      saveTimers.delete(row.product_cd)
    }
  }, 800)

  saveTimers.set(row.product_cd, timer)
}

// 同步产品信息
const handleSync = async () => {
  syncing.value = true
  try {
    const result = await syncProductInfo()
    // 响应拦截器返回完整响应对象，所以需要访问result.data
    const insertedCount = result?.data?.inserted_count || 0
    const updatedCount = result?.data?.updated_count || 0
    const totalProcessed = result?.data?.total_processed || 0

    if (insertedCount > 0 || updatedCount > 0) {
      ElMessage.success({
        message: `製品情報を同期しました（新規: ${insertedCount}件、更新: ${updatedCount}件、処理済み: ${totalProcessed}件）`,
        duration: 4000,
      })
    } else {
      ElMessage.info({
        message: result?.data?.message || '同期するデータがありませんでした',
        duration: 3000,
      })
    }
    // 同步后刷新当前页数据
    await loadData()
  } catch (error: any) {
    console.error('同期に失敗:', error)
    const errorMessage = error?.response?.data?.message || error?.message || '同期に失敗しました'
    ElMessage.error(`同期に失敗しました: ${errorMessage}`)
  } finally {
    syncing.value = false
  }
}

// 筛选处理
const handleFilter = () => {
  // 筛选时重置到第一页
  pagination.value.page = 1
  loadData()
}

// 清除筛选
const clearFilters = () => {
  filters.value = {
    keyword: '',
  }
  pagination.value.page = 1
  loadData()
}

// 分页大小变化
const handleSizeChange = (size: number) => {
  pagination.value.limit = size
  pagination.value.page = 1
  loadData()
}

// 页码变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadData()
}

// 排序变化处理
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  if (prop && order) {
    sortConfig.value.prop = prop
    sortConfig.value.order = order === 'ascending' ? 'asc' : 'desc'
    pagination.value.page = 1 // 排序时重置到第一页
    loadData()
  }
}

// 编辑处理
const handleEdit = async (row: ProductProcessBOM) => {
  try {
    // 获取完整数据
    const result = await fetchProductProcessBOMById(row.product_cd)
    // 转换布尔值字段
    formData.value = convertBooleanFields(result)
    isEdit.value = true
    activeTab.value = 'basic'
    dialogVisible.value = true
  } catch (error: any) {
    console.error('データの取得に失敗:', error)
    ElMessage.error('データの取得に失敗しました')
  }
}

// 删除处理
const handleDelete = async (row: ProductProcessBOM) => {
  try {
    await ElMessageBox.confirm(
      `製品CD: ${row.product_cd} の製品工程BOMを削除しますか？`,
      '削除確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    await deleteProductProcessBOM(row.product_cd)
    ElMessage.success('製品工程BOMを削除しました')
    await loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('削除に失敗:', error)
      const errorMessage = error?.response?.data?.message || error?.message || '削除に失敗しました'
      ElMessage.error(`削除に失敗しました: ${errorMessage}`)
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formData.value.product_cd) {
    ElMessage.error('製品CDがありません')
    return
  }

  submitting.value = true
  try {
    await updateProductProcessBOM(formData.value.product_cd, formData.value)
    ElMessage.success('製品工程BOMを更新しました')
    dialogVisible.value = false
    await loadData()
  } catch (error: any) {
    console.error('保存に失敗:', error)
    const errorMessage = error?.response?.data?.message || error?.message || '保存に失敗しました'
    ElMessage.error(`保存に失敗しました: ${errorMessage}`)
  } finally {
    submitting.value = false
  }
}

// 初始化
onMounted(async () => {
  await loadData()
})
</script>

<style scoped>
.product-process-bom-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 12px;
}

/* 页面头部 - 紧凑现代设计 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.25);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  pointer-events: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.title-section {
  flex: 1;
  color: white;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: white;
  letter-spacing: -0.5px;
}

.title-icon {
  font-size: 24px;
}

.subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-weight: 400;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  border-radius: 6px;
  padding: 10px 16px;
  text-align: center;
  min-width: 80px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.stat-card-active {
  background: rgba(16, 185, 129, 0.25);
  border-color: rgba(16, 185, 129, 0.4);
}

.stat-card-active:hover {
  background: rgba(16, 185, 129, 0.35);
}

.stat-card-discontinued {
  background: rgba(239, 68, 68, 0.25);
  border-color: rgba(239, 68, 68, 0.4);
}

.stat-card-discontinued:hover {
  background: rgba(239, 68, 68, 0.35);
}

.stat-number {
  font-size: 20px;
  font-weight: 700;
  color: white;
  margin-bottom: 2px;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

/* 功能操作区域 - 紧凑设计 */
.action-section {
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.filter-icon {
  font-size: 16px;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.filters-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  max-width: 400px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}

.filter-input {
  width: 100%;
}

/* 表格区域 - 紧凑现代设计 */
.table-section {
  margin-bottom: 12px;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

/* 表格样式优化 */
.table-card :deep(.el-table) {
  font-size: 13px;
}

.table-card :deep(.el-table th) {
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
  padding: 8px 0;
  border-bottom: 2px solid #e5e7eb;
}

.table-card :deep(.el-table td) {
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.table-card :deep(.el-table--border) {
  border: none;
}

.table-card :deep(.el-table--border::after) {
  display: none;
}

.table-card :deep(.el-table--border::before) {
  display: none;
}

/* 输入框和复选框样式优化 */
.table-card :deep(.el-input-number) {
  width: 100%;
}

.table-card :deep(.el-input-number .el-input__inner) {
  padding: 4px 8px;
  font-size: 12px;
  text-align: center;
}

.table-card :deep(.el-checkbox) {
  display: flex;
  justify-content: center;
}

.table-card :deep(.el-checkbox__input) {
  width: 18px;
  height: 18px;
}

.table-card :deep(.el-checkbox__inner) {
  width: 18px;
  height: 18px;
  border-radius: 4px;
}

/* 分页区域 - 紧凑设计 */
.pagination-section {
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.pagination {
  justify-content: flex-end;
}

.pagination :deep(.el-pagination__total) {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.pagination :deep(.el-pagination__sizes) {
  margin-right: 16px;
}

.pagination :deep(.el-pagination__jump) {
  margin-left: 16px;
}

/* 对话框样式优化 */
.product-process-dialog :deep(.el-dialog__body) {
  padding: 16px;
}

.product-process-dialog :deep(.el-tabs__content) {
  padding: 12px 0;
}

.product-process-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
}

/* 按钮样式优化 */
.filter-actions :deep(.el-button) {
  padding: 6px 12px;
  font-size: 12px;
}

.filter-actions :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.filter-actions :deep(.el-button--primary:hover) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.filter-actions :deep(.el-button--success) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
}

.filter-actions :deep(.el-button--success:hover) {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  transform: translateY(-1px);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .product-process-bom-container {
    padding: 8px;
  }

  .page-header {
    padding: 12px 16px;
  }

  .main-title {
    font-size: 18px;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .action-section {
    padding: 10px 12px;
  }
}

/* 性能优化 - 减少重绘 */
.table-card :deep(.el-table__body-wrapper) {
  will-change: scroll-position;
}

/* 滚动条美化 */
.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 操作按钮样式 - 美化 */
.action-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
}

.action-btn-edit {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.action-btn-edit:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.action-btn-delete {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 4px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  color: white;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
  transition: all 0.3s ease;
}

.action-btn-delete:hover {
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
  box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
}

/* 对话框样式 - 现代UI美化 */
.product-process-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.product-process-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  margin: 0;
  border-bottom: none;
}

.product-process-dialog :deep(.el-dialog__title) {
  color: white;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.product-process-dialog :deep(.el-dialog__headerbtn) {
  top: 16px;
  right: 20px;
}

.product-process-dialog :deep(.el-dialog__close) {
  color: white;
  font-size: 18px;
}

.product-process-dialog :deep(.el-dialog__close:hover) {
  color: rgba(255, 255, 255, 0.8);
}

.product-process-dialog :deep(.el-dialog__body) {
  padding: 16px;
  background: #f8fafc;
}

/* 表单样式 */
.edit-form {
  background: white;
  border-radius: 8px;
  padding: 12px;
}

.edit-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.edit-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: #f9fafb;
  padding: 8px 12px 0;
  border-bottom: 2px solid #e5e7eb;
}

.edit-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.edit-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  font-weight: 600;
  padding: 10px 20px;
  color: #6b7280;
  border-radius: 6px 6px 0 0;
  margin-right: 4px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.edit-tabs :deep(.el-tabs__item:hover) {
  color: #667eea;
  background: rgba(102, 126, 234, 0.08);
}

.edit-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
  background: white;
  border-color: #e5e7eb;
  border-bottom-color: white;
  font-weight: 700;
}

.edit-tabs :deep(.el-tabs__content) {
  padding: 16px;
  min-height: 350px;
  max-height: 450px;
  overflow-y: auto;
  background: white;
}

/* 表单网格布局 - 紧凑设计 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 16px;
}

.edit-tabs :deep(.el-form-item) {
  margin-bottom: 0;
}

.edit-tabs :deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
  font-size: 12px;
  padding-bottom: 4px;
  line-height: 1.4;
}

.edit-tabs :deep(.el-input),
.edit-tabs :deep(.el-input-number) {
  width: 100%;
}

.edit-tabs :deep(.el-input__inner),
.edit-tabs :deep(.el-input-number .el-input__inner) {
  border-radius: 6px;
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
  font-size: 13px;
  padding: 6px 10px;
}

.edit-tabs :deep(.el-input__inner:hover),
.edit-tabs :deep(.el-input-number .el-input__inner:hover) {
  border-color: #667eea;
}

.edit-tabs :deep(.el-input__inner:focus),
.edit-tabs :deep(.el-input-number .el-input__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.edit-tabs :deep(.el-input.is-disabled .el-input__inner) {
  background-color: #f3f4f6;
  border-color: #e5e7eb;
  color: #6b7280;
}

.edit-tabs :deep(.el-switch) {
  height: 22px;
}

.edit-tabs :deep(.el-switch__core) {
  height: 22px;
  border-radius: 11px;
  width: 44px;
}

.edit-tabs :deep(.el-switch__core::after) {
  width: 18px;
  height: 18px;
}

.edit-tabs :deep(.el-switch.is-checked .el-switch__core) {
  background-color: #667eea;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.dialog-footer :deep(.el-button) {
  padding: 8px 20px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.dialog-footer :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.dialog-footer :deep(.el-button--primary:hover) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.dialog-footer :deep(.el-button--default) {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.dialog-footer :deep(.el-button--default:hover) {
  background: #f9fafb;
  border-color: #9ca3af;
}

/* 滚动条美化 */
.edit-tabs :deep(.el-tabs__content)::-webkit-scrollbar {
  width: 6px;
}

.edit-tabs :deep(.el-tabs__content)::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.edit-tabs :deep(.el-tabs__content)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.edit-tabs :deep(.el-tabs__content)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>
