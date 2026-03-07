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
            {{ t('master.material.title') }}
          </h1>
          <p class="subtitle">{{ t('master.material.subtitle') }}</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ materialList.length }}</div>
            <div class="stat-label">{{ t('master.material.totalMaterials') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeCount }}</div>
            <div class="stat-label">{{ t('master.material.activeMaterials') }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ lowStockCount }}</div>
            <div class="stat-label">{{ t('master.material.lowStock') }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>{{ t('master.material.searchFilter') }}</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">{{ t('master.material.clear') }}</el-button>
          <el-button text @click="showColumnSettings" :icon="Setting" class="column-settings-btn"
            >{{ t('master.material.columnSettings') }}</el-button
          >
          <el-button text @click="showPrintSettings" :icon="Printer" class="print-btn"
            >{{ t('master.material.print') }}</el-button
          >
          <el-button
            type="warning"
            @click="generateAndPrintQRCodes"
            :icon="Printer"
            class="qr-code-btn"
          >
            {{ t('master.material.qrPrint') }}
          </el-button>
          <el-button
            type="success"
            @click="exportToCSV"
            :icon="Download"
            :disabled="filteredList.length === 0"
            class="export-csv-btn"
          >
            {{ t('master.material.csvExport') }}
          </el-button>
          <el-button type="primary" @click="openForm()" :icon="Plus" class="add-material-btn"
            >{{ t('master.material.addMaterial') }}</el-button
          >
        </div>
      </div>

      <div class="filters-grid">
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            {{ t('master.material.keywordSearch') }}
          </label>
          <el-input
            v-model="filters.keyword"
            :placeholder="t('master.material.placeholder')"
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
            　<el-option label="鋼管" value="鋼管" />
            <el-option label="鋼材" value="鋼材" />
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
            <el-option label="無償" value="無償" />
            <el-option label="有償" value="有償" />
            <el-option label="自給" value="自給" />
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
        <!-- 保管場所 -->
        <div class="filter-item">
          <label class="filter-label"
            ><el-icon> <Location /> </el-icon>保管場所</label
          >
          <el-input
            v-model="filters.storage_location"
            placeholder="保管場所"
            clearable
            @input="handleFilter"
            class="filter-input"
          />
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
            @close="clearUsageFilter"
            type="danger"
            size="small"
            >用途: {{ filters.usegae }}</el-tag
          >
          <el-tag
            v-if="filters.storage_location"
            closable
            @close="clearStorageLocationFilter"
            type="info"
            size="small"
            >保管: {{ filters.storage_location }}</el-tag
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
        :default-sort="{ prop: 'material_cd', order: 'ascending' }"
      >
        <el-table-column
          v-if="showMaterialCd"
          prop="material_cd"
          label="材料CD"
          width="95"
          align="center"
        >
          <template #default="{ row }">
            <span class="material-cd">{{ row.material_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showMaterialName"
          prop="material_name"
          label="材料名"
          width="140"
          show-overflow-tooltip
          sortable
        />
        <el-table-column
          v-if="showMaterialType"
          prop="material_type"
          label="種類"
          width="90"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getMaterialTypeColor(row.material_type)" size="small">{{
              row.material_type
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showStandardSpec"
          prop="standard_spec"
          label="規格"
          width="100"
          show-overflow-tooltip
        />
        <el-table-column v-if="showDimensions" label="寸法" width="110" align="center">
          <template #default="{ row }">
            <div class="dimension-info">
              <div v-if="row.diameter" class="dimension-item">φ{{ row.diameter }}mm</div>
              <div v-if="row.thickness" class="dimension-item">厚{{ row.thickness }}mm</div>
              <div v-if="row.length" class="dimension-item">L{{ row.length }}mm</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column v-if="showUnit" prop="unit" label="単位" width="80" align="center" />
        <el-table-column
          v-if="showPiecesPerBundle"
          prop="pieces_per_bundle"
          label="束本数"
          width="90"
          align="center"
        />
        <el-table-column
          v-if="showSupplyClassification"
          prop="supply_classification"
          label="支給区分"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.supply_classification === '無償支給' ? 'success' : 'warning'"
              size="small"
              >{{ row.supply_classification }}</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column v-if="showUsage" prop="usegae" label="用途" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.usegae }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showSupplierName"
          prop="supplier_name"
          label="仕入先名"
          min-width="110"
          show-overflow-tooltip
          sortable
        />
        <el-table-column v-if="showPriceInfo" label="価格情報" width="120" align="center">
          <template #default="{ row }">
            <div class="price-info">
              <div v-if="row.unit_price" class="price-item">
                単価: ¥{{ formatNumber(row.unit_price) }}kg
              </div>
              <div v-if="row.single_price" class="price-item">
                本価: ¥{{ formatNumber(row.single_price) }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column v-if="showStockInfo" label="リード" width="120" align="center">
          <template #default="{ row }">
            <div class="stock-info">
              <div
                v-if="row.safety_stock"
                class="stock-item"
                :class="{ 'low-stock': row.safety_stock < 10 }"
              >
                安全: {{ row.safety_stock }}束
              </div>
              <div v-if="row.lead_time" class="stock-item">リード:{{ row.lead_time }}日</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showStorageLocation"
          prop="storage_location"
          label="保管場所"
          width="110"
          show-overflow-tooltip
        />
        <el-table-column v-if="showStatus" prop="status" label="状態" width="85" align="center">
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
        <el-table-column
          v-if="showSupplierCd"
          prop="supplier_cd"
          label="仕入先CD"
          width="120"
          align="center"
        />
        <el-table-column
          v-if="showLongWeight"
          prop="long_weight"
          label="長尺単重"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.long_weight">{{ formatNumber(row.long_weight, 3) }} kg/本</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showToleranceRange"
          prop="tolerance_range"
          label="公差範囲"
          width="110"
          align="center"
        />
        <el-table-column
          v-if="showTolerance1"
          prop="tolerance_1"
          label="公差1"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.tolerance_1">{{ formatNumber(row.tolerance_1, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showTolerance2"
          prop="tolerance_2"
          label="公差2"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.tolerance_2">{{ formatNumber(row.tolerance_2, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showRangeValue"
          prop="range_value"
          label="範囲"
          width="150"
          align="center"
        />
        <el-table-column
          v-if="showMinValue"
          prop="min_value"
          label="最小値"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.min_value">{{ formatNumber(row.min_value, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showMaxValue"
          prop="max_value"
          label="最大値"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.max_value">{{ formatNumber(row.max_value, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showActualValue1"
          prop="actual_value_1"
          label="実力値1"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.actual_value_1">{{ formatNumber(row.actual_value_1, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showActualValue2"
          prop="actual_value_2"
          label="実力値2"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.actual_value_2">{{ formatNumber(row.actual_value_2, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showActualValue3"
          prop="actual_value_3"
          label="実力値3"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.actual_value_3">{{ formatNumber(row.actual_value_3, 2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="showRepresentativeModel"
          prop="representative_model"
          label="代表品種"
          width="150"
          align="center"
        />
        <el-table-column
          v-if="showNote"
          prop="note"
          label="備考"
          width="120"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="showCreatedAt"
          prop="created_at"
          label="作成日時"
          width="170"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          v-if="showUpdatedAt"
          prop="updated_at"
          label="更新日時"
          width="170"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column v-if="showActions" label="操作" fixed="right" width="110" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" link @click="openForm(row)">編集</el-button>
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
    </div>

    <MaterialEditDialog v-model:visible="formVisible" :data-id="editId" @refresh="fetchList" />

    <!-- 列設定ダイアログ -->
    <el-dialog
      v-model="columnSettingsVisible"
      title="列設定"
      width="700px"
      :before-close="() => (columnSettingsVisible = false)"
    >
      <div class="column-settings">
        <p>表示する列を選択してください：</p>
        <div class="column-list">
          <el-checkbox v-model="showMaterialCd" label="材料CD" />
          <el-checkbox v-model="showMaterialName" label="材料名" />
          <el-checkbox v-model="showMaterialType" label="種類" />
          <el-checkbox v-model="showStandardSpec" label="規格" />
          <el-checkbox v-model="showDimensions" label="寸法" />
          <el-checkbox v-model="showUnit" label="単位" />
          <el-checkbox v-model="showPiecesPerBundle" label="束本数" />
          <el-checkbox v-model="showSupplyClassification" label="支給区分" />
          <el-checkbox v-model="showUsage" label="用途" />
          <el-checkbox v-model="showSupplierName" label="仕入先名" />
          <el-checkbox v-model="showSupplierCd" label="仕入先CD" />
          <el-checkbox v-model="showPriceInfo" label="価格情報" />
          <el-checkbox v-model="showLongWeight" label="長尺単重" />
          <el-checkbox v-model="showStockInfo" label="在庫・リード" />
          <el-checkbox v-model="showStorageLocation" label="保管場所" />
          <el-checkbox v-model="showToleranceRange" label="公差範囲" />
          <el-checkbox v-model="showTolerance1" label="公差1" />
          <el-checkbox v-model="showTolerance2" label="公差2" />
          <el-checkbox v-model="showRangeValue" label="範囲" />
          <el-checkbox v-model="showMinValue" label="最小値" />
          <el-checkbox v-model="showMaxValue" label="最大値" />
          <el-checkbox v-model="showActualValue1" label="実力値1" />
          <el-checkbox v-model="showActualValue2" label="実力値2" />
          <el-checkbox v-model="showActualValue3" label="実力値3" />
          <el-checkbox v-model="showRepresentativeModel" label="代表品種" />
          <el-checkbox v-model="showNote" label="備考" />
          <el-checkbox v-model="showCreatedAt" label="作成日時" />
          <el-checkbox v-model="showUpdatedAt" label="更新日時" />
          <el-checkbox v-model="showStatus" label="状態" />
          <el-checkbox v-model="showActions" label="操作" />
        </div>
      </div>
      <template #footer>
        <el-button @click="columnSettingsVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="applyColumnSettings">適用</el-button>
      </template>
    </el-dialog>

    <!-- 印刷設定ダイアログ -->
    <el-dialog
      v-model="printSettingsVisible"
      title="印刷設定"
      width="800px"
      :before-close="() => (printSettingsVisible = false)"
    >
      <div class="print-settings">
        <p>印刷する列を選択してください：</p>
        <div class="print-column-list">
          <!-- 基本情報 -->
          <div class="print-section">
            <h4>基本情報</h4>
            <el-checkbox v-model="printShowMaterialCd" label="材料CD" />
            <el-checkbox v-model="printShowMaterialName" label="材料名" />
            <el-checkbox v-model="printShowMaterialType" label="種類" />
            <el-checkbox v-model="printShowStandardSpec" label="規格" />
            <el-checkbox v-model="printShowUnit" label="単位" />
          </div>

          <!-- 寸法情報 -->
          <div class="print-section">
            <h4>寸法情報</h4>
            <el-checkbox v-model="printShowDiameter" label="直径" />
            <el-checkbox v-model="printShowThickness" label="厚さ" />
            <el-checkbox v-model="printShowLength" label="長さ" />
          </div>

          <!-- 支給・用途情報 -->
          <div class="print-section">
            <h4>支給・用途情報</h4>
            <el-checkbox v-model="printShowSupplyClassification" label="支給区分" />
            <el-checkbox v-model="printShowPiecesPerBundle" label="束本数" />
            <el-checkbox v-model="printShowUsage" label="用途" />
          </div>

          <!-- 仕入先情報 -->
          <div class="print-section">
            <h4>仕入先情報</h4>
            <el-checkbox v-model="printShowSupplierCd" label="仕入先CD" />
            <el-checkbox v-model="printShowSupplierName" label="仕入先名" />
          </div>

          <!-- 価格情報 -->
          <div class="print-section">
            <h4>価格情報</h4>
            <el-checkbox v-model="printShowUnitPrice" label="単重単価" />
            <el-checkbox v-model="printShowLongWeight" label="長尺単重" />
            <el-checkbox v-model="printShowSinglePrice" label="一本単価" />
          </div>

          <!-- 在庫・リード情報 -->
          <div class="print-section">
            <h4>在庫・リード情報</h4>
            <el-checkbox v-model="printShowSafetyStock" label="安全在庫" />
            <el-checkbox v-model="printShowLeadTime" label="リードタイム" />
          </div>

          <!-- 保管・状態情報 -->
          <div class="print-section">
            <h4>保管・状態情報</h4>
            <el-checkbox v-model="printShowStorageLocation" label="保管場所" />
            <el-checkbox v-model="printShowStatus" label="状態" />
          </div>

          <!-- 公差・範囲情報 -->
          <div class="print-section">
            <h4>公差・範囲情報</h4>
            <el-checkbox v-model="printShowToleranceRange" label="公差範囲" />
            <el-checkbox v-model="printShowTolerance1" label="公差1" />
            <el-checkbox v-model="printShowTolerance2" label="公差2" />
            <el-checkbox v-model="printShowRangeValue" label="範囲" />
            <el-checkbox v-model="printShowMinValue" label="最小値" />
            <el-checkbox v-model="printShowMaxValue" label="最大値" />
          </div>

          <!-- 実力値情報 -->
          <div class="print-section">
            <h4>実力値情報</h4>
            <el-checkbox v-model="printShowActualValue1" label="実力値1" />
            <el-checkbox v-model="printShowActualValue2" label="実力値2" />
            <el-checkbox v-model="printShowActualValue3" label="実力値3" />
          </div>

          <!-- その他情報 -->
          <div class="print-section">
            <h4>その他情報</h4>
            <el-checkbox v-model="printShowRepresentativeModel" label="代表品種" />
            <el-checkbox v-model="printShowNote" label="備考" />
            <el-checkbox v-model="printShowCreatedAt" label="作成日時" />
            <el-checkbox v-model="printShowUpdatedAt" label="更新日時" />
          </div>
        </div>
        <div class="print-options">
          <el-divider content-position="left">印刷オプション</el-divider>
          <el-checkbox v-model="printShowHeader" label="ヘッダー情報を表示" />
          <el-checkbox v-model="printShowStats" label="統計情報を表示" />

          <el-divider content-position="left">ソート設定</el-divider>
          <div class="sort-settings">
            <div class="sort-item">
              <label class="sort-label">ソート項目:</label>
              <el-select v-model="printSortBy" placeholder="ソート項目を選択" style="width: 200px">
                <el-option label="仕入先名" value="supplier_name" />
                <el-option label="材料CD" value="material_cd" />
                <el-option label="材料名" value="material_name" />
                <el-option label="種類" value="material_type" />
                <el-option label="規格" value="standard_spec" />
                <el-option label="単位" value="unit" />
                <el-option label="支給区分" value="supply_classification" />
                <el-option label="用途" value="usegae" />
                <el-option label="保管場所" value="storage_location" />
                <el-option label="状態" value="status" />
                <el-option label="作成日時" value="created_at" />
                <el-option label="更新日時" value="updated_at" />
              </el-select>
            </div>
            <div class="sort-item">
              <label class="sort-label">ソート順序:</label>
              <el-select
                v-model="printSortOrder"
                placeholder="ソート順序を選択"
                style="width: 120px"
              >
                <el-option label="昇順" value="asc" />
                <el-option label="降順" value="desc" />
              </el-select>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="printSettingsVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="executePrint">印刷実行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
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
  Location,
  Setting,
  Printer,
  Download,
} from '@element-plus/icons-vue'
import MaterialEditDialog from './MaterialForm.vue'
import {
  getMaterialList,
  deleteMaterialById,
  updateMaterial,
  exportMaterialToCSV,
} from '@/api/master/materialMaster'
import type { Material as MaterialOrigin } from '@/types/master'

const { t } = useI18n()

// Material タイプを拡張し、statusLoading フィールドを追加
interface Material extends MaterialOrigin {
  statusLoading?: boolean
  supplier_name?: string
}

// フィルター関連
const filters = ref({
  keyword: '',
  status: '' as string | number,
  material_type: '',
  supply_classification: '',
  usegae: '',
  storage_location: '',
})
const loading = ref(false)
const materialList = ref<Material[]>([])
const formVisible = ref(false)
const editId = ref<number | null>(null)
const columnSettingsVisible = ref(false)
const printSettingsVisible = ref(false)

// 印刷設定用の変数
const printShowMaterialCd = ref(true)
const printShowMaterialName = ref(true)
const printShowMaterialType = ref(true)
const printShowStandardSpec = ref(true)
const printShowUnit = ref(true)
const printShowDiameter = ref(false)
const printShowThickness = ref(false)
const printShowLength = ref(false)
const printShowSupplyClassification = ref(true)
const printShowPiecesPerBundle = ref(false)
const printShowUsage = ref(true)
const printShowSupplierCd = ref(false)
const printShowSupplierName = ref(true)
const printShowUnitPrice = ref(false)
const printShowLongWeight = ref(false)
const printShowSinglePrice = ref(false)
const printShowSafetyStock = ref(false)
const printShowLeadTime = ref(false)
const printShowStorageLocation = ref(true)
const printShowStatus = ref(true)
const printShowToleranceRange = ref(false)
const printShowTolerance1 = ref(false)
const printShowTolerance2 = ref(false)
const printShowRangeValue = ref(false)
const printShowMinValue = ref(false)
const printShowMaxValue = ref(false)
const printShowActualValue1 = ref(false)
const printShowActualValue2 = ref(false)
const printShowActualValue3 = ref(false)
const printShowRepresentativeModel = ref(false)
const printShowNote = ref(true)
const printShowCreatedAt = ref(false)
const printShowUpdatedAt = ref(false)
const printShowHeader = ref(true)
const printShowStats = ref(true)

// 印刷排序設定
const printSortBy = ref('supplier_name')
const printSortOrder = ref('asc')

// 列表示設定
const showMaterialCd = ref(true)
const showMaterialName = ref(true)
const showMaterialType = ref(true)
const showStandardSpec = ref(true)
const showDimensions = ref(true)
const showUnit = ref(true)
const showPiecesPerBundle = ref(true)
const showSupplyClassification = ref(true)
const showUsage = ref(true)
const showSupplierName = ref(true)
const showSupplierCd = ref(false)
const showPriceInfo = ref(true)
const showLongWeight = ref(false)
const showStockInfo = ref(true)
const showStorageLocation = ref(true)
const showToleranceRange = ref(false)
const showTolerance1 = ref(false)
const showTolerance2 = ref(false)
const showRangeValue = ref(false)
const showMinValue = ref(false)
const showMaxValue = ref(false)
const showActualValue1 = ref(false)
const showActualValue2 = ref(false)
const showActualValue3 = ref(false)
const showRepresentativeModel = ref(false)
const showNote = ref(false)
const showCreatedAt = ref(false)
const showUpdatedAt = ref(false)
const showStatus = ref(true)
const showActions = ref(true)

const handleFilter = () => {}
const clearFilters = () => {
  filters.value = {
    keyword: '',
    status: '',
    material_type: '',
    supply_classification: '',
    usegae: '',
    storage_location: '',
  }
}

// 個別フィルタークリアメソッド
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

const clearUsageFilter = () => {
  filters.value.usegae = ''
  handleFilter()
}

const clearStorageLocationFilter = () => {
  filters.value.storage_location = ''
  handleFilter()
}

const showColumnSettings = () => {
  columnSettingsVisible.value = true
}

const applyColumnSettings = () => {
  columnSettingsVisible.value = false
  ElMessage.success('列設定を適用しました')
}

// 印刷設定表示
const showPrintSettings = () => {
  if (filteredList.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }
  printSettingsVisible.value = true
}

// 印刷実行
const executePrint = () => {
  printSettingsVisible.value = false

  // 印刷用のHTMLを生成
  const printContent = generatePrintContent()

  // 新しいウィンドウを開いて印刷
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.focus()
    printWindow.print()
    printWindow.close()
  }
}

const generatePrintContent = () => {
  const currentDate = new Date().toLocaleString('ja-JP')
  const totalCount = filteredList.value.length
  const activeCount = filteredList.value.filter((item) => item.status === 1).length

  // 印刷用データをソート
  const sortedData = [...filteredList.value].sort((a, b) => {
    let aValue = (a as any)[printSortBy.value]
    let bValue = (b as any)[printSortBy.value]

    // null/undefinedの処理
    if (aValue === null || aValue === undefined) aValue = ''
    if (bValue === null || bValue === undefined) bValue = ''

    // 数値フィールドの処理
    if (
      [
        'diameter',
        'thickness',
        'length',
        'pieces_per_bundle',
        'unit_price',
        'long_weight',
        'single_price',
        'safety_stock',
        'lead_time',
        'tolerance_1',
        'tolerance_2',
        'min_value',
        'max_value',
        'actual_value_1',
        'actual_value_2',
        'actual_value_3',
        'status',
      ].includes(printSortBy.value)
    ) {
      aValue = Number(aValue) || 0
      bValue = Number(bValue) || 0
    }

    // 日時フィールドの処理
    if (['created_at', 'updated_at'].includes(printSortBy.value)) {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    }

    // 文字列の場合は小文字で比較
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (printSortOrder.value === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
    }
  })

  // 印刷用の列設定を定義
  const printColumns = [
    { key: 'index', label: 'No', width: '40px', show: true },
    { key: 'material_cd', label: '材料CD', width: '80px', show: printShowMaterialCd.value },
    { key: 'material_name', label: '材料名', width: '120px', show: printShowMaterialName.value },
    { key: 'material_type', label: '種類', width: '60px', show: printShowMaterialType.value },
    { key: 'standard_spec', label: '規格', width: '100px', show: printShowStandardSpec.value },
    { key: 'unit', label: '単位', width: '50px', show: printShowUnit.value },
    { key: 'diameter', label: '直径', width: '60px', show: printShowDiameter.value },
    { key: 'thickness', label: '厚さ', width: '60px', show: printShowThickness.value },
    { key: 'length', label: '長さ', width: '60px', show: printShowLength.value },
    {
      key: 'supply_classification',
      label: '支給区分',
      width: '80px',
      show: printShowSupplyClassification.value,
    },
    {
      key: 'pieces_per_bundle',
      label: '束本数',
      width: '70px',
      show: printShowPiecesPerBundle.value,
    },
    { key: 'usegae', label: '用途', width: '60px', show: printShowUsage.value },
    { key: 'supplier_cd', label: '仕入先CD', width: '90px', show: printShowSupplierCd.value },
    { key: 'supplier_name', label: '仕入先名', width: '100px', show: printShowSupplierName.value },
    { key: 'unit_price', label: '単重単価', width: '80px', show: printShowUnitPrice.value },
    { key: 'long_weight', label: '長尺単重', width: '80px', show: printShowLongWeight.value },
    { key: 'single_price', label: '一本単価', width: '80px', show: printShowSinglePrice.value },
    { key: 'safety_stock', label: '安全在庫', width: '80px', show: printShowSafetyStock.value },
    { key: 'lead_time', label: 'リードタイム', width: '80px', show: printShowLeadTime.value },
    {
      key: 'storage_location',
      label: '保管場所',
      width: '80px',
      show: printShowStorageLocation.value,
    },
    { key: 'status', label: '状態', width: '50px', show: printShowStatus.value },
    {
      key: 'tolerance_range',
      label: '公差範囲',
      width: '80px',
      show: printShowToleranceRange.value,
    },
    { key: 'tolerance_1', label: '公差1', width: '60px', show: printShowTolerance1.value },
    { key: 'tolerance_2', label: '公差2', width: '60px', show: printShowTolerance2.value },
    { key: 'range_value', label: '範囲', width: '80px', show: printShowRangeValue.value },
    { key: 'min_value', label: '最小値', width: '70px', show: printShowMinValue.value },
    { key: 'max_value', label: '最大値', width: '70px', show: printShowMaxValue.value },
    { key: 'actual_value_1', label: '実力値1', width: '70px', show: printShowActualValue1.value },
    { key: 'actual_value_2', label: '実力値2', width: '70px', show: printShowActualValue2.value },
    { key: 'actual_value_3', label: '実力値3', width: '70px', show: printShowActualValue3.value },
    {
      key: 'representative_model',
      label: '代表品種',
      width: '100px',
      show: printShowRepresentativeModel.value,
    },
    { key: 'note', label: '備考', width: '100px', show: printShowNote.value },
    { key: 'created_at', label: '作成日時', width: '120px', show: printShowCreatedAt.value },
    { key: 'updated_at', label: '更新日時', width: '120px', show: printShowUpdatedAt.value },
  ]

  // 表示する列のみをフィルター
  const visibleColumns = printColumns.filter((col) => col.show)

  let tableRows = ''
  sortedData.forEach((item, index) => {
    let rowCells = ''
    visibleColumns.forEach((col) => {
      let cellValue = '-'
      if (col.key === 'index') {
        cellValue = (index + 1).toString()
      } else if (col.key === 'status') {
        cellValue = item.status === 1 ? '有効' : '無効'
      } else {
        const rawValue = (item as any)[col.key]
        if (rawValue !== null && rawValue !== undefined && rawValue !== '') {
          // 数値フィールドのフォーマット
          if (
            [
              'diameter',
              'thickness',
              'length',
              'pieces_per_bundle',
              'unit_price',
              'long_weight',
              'single_price',
              'safety_stock',
              'lead_time',
              'tolerance_1',
              'tolerance_2',
              'min_value',
              'max_value',
              'actual_value_1',
              'actual_value_2',
              'actual_value_3',
            ].includes(col.key)
          ) {
            if (typeof rawValue === 'number') {
              cellValue = rawValue.toString()
            } else {
              cellValue = rawValue
            }
          } else if (col.key === 'created_at' || col.key === 'updated_at') {
            // 日時のフォーマット
            const date = new Date(rawValue)
            cellValue = date.toLocaleString('ja-JP', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })
          } else {
            cellValue = rawValue.toString()
          }
        }
      }
      rowCells += `<td>${cellValue}</td>`
    })
    tableRows += `<tr>${rowCells}</tr>`
  })

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>材料マスタ一覧 - ${currentDate}</title>
      <style>
        body {
          font-family: 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo UI', sans-serif;
          font-size: 12px;
          line-height: 1.4;
          margin: 20px;
          color: #333;
        }
        .print-header {
          text-align: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #333;
          padding-bottom: 15px;
        }
        .print-title {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 10px;
        }
        .print-subtitle {
          font-size: 14px;
          color: #666;
        }
        .print-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: 20px;
          font-size: 11px;
        }
        .print-stats {
          display: flex;
          gap: 20px;
          margin-bottom: 20px;
        }
        .stat-item {
          background: #f5f5f5;
          padding: 8px 12px;
          border-radius: 4px;
          font-size: 11px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }
        th, td {
          border: 1px solid #ddd;
          padding: 6px 8px;
          text-align: left;
          font-size: 10px;
        }
        th {
          background-color: #f8f9fa;
          font-weight: bold;
          text-align: center;
        }
        tr:nth-child(even) {
          background-color: #f9f9f9;
        }
        .no-data {
          text-align: center;
          padding: 40px;
          color: #999;
        }
        @media print {
          body { margin: 0; }
          .print-header { page-break-after: avoid; }
          table { page-break-inside: auto; }
          tr { page-break-inside: avoid; page-break-after: auto; }
        }
      </style>
    </head>
    <body>
      ${
        printShowHeader.value
          ? `
      <div class="print-header">
        <div class="print-title">材料マスタ一覧</div>
        <div class="print-subtitle">材料の登録・編集・仕入先管理</div>
      </div>

      <div class="print-info">
        <div>印刷日時: ${currentDate}</div>
        <div>印刷者: ${localStorage.getItem('userName') || 'システム'}</div>
      </div>
      `
          : ''
      }

      ${
        printShowStats.value
          ? `
      <div class="print-stats">
        <div class="stat-item">総件数: ${totalCount}件</div>
        <div class="stat-item">有効件数: ${activeCount}件</div>
        <div class="stat-item">無効件数: ${totalCount - activeCount}件</div>
      </div>
      `
          : ''
      }

      ${
        sortedData.length > 0
          ? `
        <table>
          <thead>
            <tr>
              ${visibleColumns.map((col) => `<th style="width: ${col.width};">${col.label}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
            ${tableRows}
          </tbody>
        </table>
      `
          : `
        <div class="no-data">
          表示するデータがありません
        </div>
      `
      }
    </body>
    </html>
  `
}

// 有効件数統計
const activeCount = computed(() => materialList.value.filter((row) => row.status == 1).length)

// 無効件数統計
const lowStockCount = computed(() => materialList.value.filter((row) => row.status === 0).length)

const hasActiveFilters = computed(
  () =>
    filters.value.keyword ||
    filters.value.status !== '' ||
    filters.value.material_type ||
    filters.value.supply_classification ||
    filters.value.usegae ||
    filters.value.storage_location,
)

// リストフィルター
const filteredList = computed(() => {
  let result = materialList.value
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(
      (row) =>
        row.material_cd?.toLowerCase().includes(keyword) ||
        row.material_name?.toLowerCase().includes(keyword) ||
        row.standard_spec?.toLowerCase().includes(keyword) ||
        row.supplier_name?.toLowerCase().includes(keyword),
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
  if (filters.value.storage_location) {
    result = result.filter((row) =>
      row.storage_location?.toLowerCase().includes(filters.value.storage_location.toLowerCase()),
    )
  }
  return result
})

// データ操作
function fetchList() {
  loading.value = true
  getMaterialList({ keyword: filters.value.keyword, page: 1, pageSize: 10000 })
    .then((res) => {
      const list = res?.data?.list ?? res?.list ?? []
      materialList.value = list.map((row: MaterialOrigin) => ({
        ...row,
        statusLoading: false,
      }))
    })
    .finally(() => (loading.value = false))
}

function openForm(row: Material | null = null) {
  editId.value = row && row.id != null ? row.id : null
  formVisible.value = true
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

// ユーティリティ関数
function getMaterialTypeColor(type: string): 'primary' | 'success' | 'info' | 'warning' | 'danger' {
  const colorMap: Record<string, 'primary' | 'success' | 'info' | 'warning' | 'danger'> = {
    鋼材: 'danger',
    樹脂: 'success',
    アルミ: 'warning',
    その他: 'info',
  }
  return colorMap[type] || 'info'
}

function formatNumber(num: number, decimals: number = 0) {
  return new Intl.NumberFormat('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

function formatDateTime(dateString: string) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 生成并打印所有材料CD的二维码
const generateAndPrintQRCodes = async () => {
  const materialsToUse = filteredList.value.length > 0 ? filteredList.value : materialList.value

  if (materialsToUse.length === 0) {
    ElMessage.warning('印刷する材料がありません')
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

    // 按材料名排序
    const sortedMaterials = [...materialsToUse].sort((a, b) => {
      const nameA = a.material_name || ''
      const nameB = b.material_name || ''
      return nameA.localeCompare(nameB, 'ja')
    })

    // 生成所有二维码
    const qrCodes: Array<{
      dataUrl: string
      material_cd: string
      material_name: string
    }> = []
    for (const material of sortedMaterials) {
      if (material.material_cd) {
        try {
          const qrDataUrl = await QRCode.toDataURL(material.material_cd, {
            width: 95,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF',
            },
          })
          qrCodes.push({
            dataUrl: qrDataUrl,
            material_cd: material.material_cd,
            material_name: material.material_name || '',
          })
        } catch (error) {
          console.error(`QRコード生成エラー (${material.material_cd}):`, error)
        }
      }
    }

    if (qrCodes.length === 0) {
      printWindow.close()
      ElMessage.error('QRコードの生成に失敗しました')
      return
    }

    // 创建打印HTML（A4纸纵向布局）
    const qrCodesPerRow = 5 // A4纵向每行5个
    const qrCodesPerPage = 40 // A4纵向可以放40个二维码（每行5个，共8行）
    const totalPages = qrCodes.length > 0 ? Math.ceil(qrCodes.length / qrCodesPerPage) : 0

    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>材料QRコード印刷</title>
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
            grid-template-rows: repeat(8, 1fr);
            gap: 1.2mm;
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
          .qr-material-name {
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

      // 获取这一页的二维码数据（已经按材料名排序）
      const pageQRCodes = qrCodes.slice(startIndex, endIndex)

      // 如果这一页没有数据，跳过（防止空白页）
      if (pageQRCodes.length === 0) {
        break
      }

      html += `<div class="page">`
      html += `<div class="page-title">材料マスタQR</div>`
      html += `<div class="qr-grid">`

      // 横向填充：第1行从左到右，然后第2行从左到右，以此类推
      for (let i = 0; i < pageQRCodes.length; i++) {
        const { dataUrl, material_name } = pageQRCodes[i]
        // 计算在网格中的位置（横向填充）
        const col = i % qrCodesPerRow // 列索引（0-3）
        const row = Math.floor(i / qrCodesPerRow) // 行索引（0-6）
        const gridColumn = col + 1 // CSS Grid 列从1开始
        const gridRow = row + 1 // CSS Grid 行从1开始

        html += `
          <div class="qr-item" style="grid-column: ${gridColumn}; grid-row: ${gridRow};">
            <img src="${dataUrl}" alt="QRコード" class="qr-code" />
            ${material_name ? `<div class="qr-material-name">${material_name}</div>` : ''}
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

// 导出CSV文件
const exportToCSV = async () => {
  try {
    loading.value = true

    const allDataResponse = await getMaterialList({
      keyword: filters.value.keyword,
      page: 1,
      pageSize: 10000,
    })

    const allMaterialsData: Material[] =
      allDataResponse?.data?.list ?? allDataResponse?.list ?? []

    // 应用其他筛选条件
    let filteredData = allMaterialsData
    if (filters.value.status !== '') {
      filteredData = filteredData.filter((row) => row.status === filters.value.status)
    }
    if (filters.value.material_type) {
      filteredData = filteredData.filter((row) => row.material_type === filters.value.material_type)
    }
    if (filters.value.supply_classification) {
      filteredData = filteredData.filter(
        (row) => row.supply_classification === filters.value.supply_classification,
      )
    }
    if (filters.value.usegae) {
      filteredData = filteredData.filter((row) => row.usegae === filters.value.usegae)
    }
    if (filters.value.storage_location) {
      filteredData = filteredData.filter((row) =>
        row.storage_location?.toLowerCase().includes(filters.value.storage_location.toLowerCase()),
      )
    }

    if (filteredData.length === 0) {
      ElMessage.warning('出力する材料がありません')
      return
    }

    // 准备导出数据：只包含材料CD和材料名
    const exportData = filteredData.map((material) => ({
      material_cd: material.material_cd || '',
      material_name: material.material_name || '',
    }))

    // 调用后端API导出CSV
    await exportMaterialToCSV(exportData)

    ElMessage.success(`${exportData.length}件のデータをCSVファイルに出力しました`)
  } catch (error) {
    console.error('CSV出力エラー:', error)
    ElMessage.error('CSVファイルの出力に失敗しました')
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
/* 基本容器、头部、统计区块 */
.material-master-container {
  padding: 6px;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 6px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 2px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.9);
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-size: 0.8rem;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  color: white;
  padding: 6px 12px;
  border-radius: 10px;
  text-align: center;
  min-width: 70px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.stat-card:nth-child(3) {
  background: rgba(239, 68, 68, 0.3);
}

.stat-number {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 2px;
  white-space: nowrap;
}

/* 操作区块 */
.action-section {
  background: white;
  border-radius: 10px;
  margin-bottom: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

/* 筛选标题区 */
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
}

.filter-icon {
  font-size: 1rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.clear-btn {
  color: #64748b;
  transition: all 0.2s ease;
  padding: 6px 10px !important;
  font-size: 12px !important;
}

.clear-btn:hover {
  color: #667eea;
}

.add-material-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition: all 0.2s;
}

.add-material-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.qr-code-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: none;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.25);
  transition: all 0.2s ease;
}

.qr-code-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}

.export-csv-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
  transition: all 0.2s ease;
  color: white;
}

.export-csv-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.export-csv-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filters-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
  gap: 10px;
  padding: 10px 14px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.search-item {
  grid-column: span 1;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 2px;
}

.filter-label .el-icon {
  font-size: 0.85rem;
  color: #667eea;
}

.filter-input {
  transition: all 0.2s;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.search-active {
  color: #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.type-desc,
.status-desc {
  font-size: 0.7rem;
  color: #64748b;
  margin-left: 6px;
}

/* 筛选摘要 */
.filter-summary {
  padding: 8px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.summary-icon {
  color: #667eea;
  font-size: 14px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.active-filters .el-tag {
  cursor: pointer;
  transition: all 0.2s;
  font-size: 11px;
  border-radius: 4px;
  padding: 0 6px;
  height: 22px;
}

.active-filters .el-tag:hover {
  transform: scale(1.02);
}

/* 表格 */
.table-card {
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  margin-bottom: 6px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

.material-cd {
  font-family: 'Monaco', 'Menlo', monospace;
  color: #667eea;
  font-weight: 600;
  font-size: 11px;
}

.dimension-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-size: 11px;
  line-height: 1.2;
}

.dimension-item {
  color: #475569;
  font-weight: 500;
}

.price-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-size: 11px;
  line-height: 1.2;
}

.price-item {
  color: #10b981;
  font-weight: 500;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-size: 11px;
  line-height: 1.2;
}

.stock-item {
  color: #475569;
  font-weight: 500;
}

.low-stock {
  color: #ef4444;
  font-weight: 600;
}

.action-buttons-table {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* 结果区域 */
.result-section {
  background: white;
  border-radius: 8px;
  padding: 8px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  text-align: center;
  border: 1px solid #e2e8f0;
}

.result-info {
  color: #64748b;
  font-size: 12px;
}

/* 响应式 */
@media (max-width: 1400px) {
  .filters-grid {
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 10px;
  }
  .search-item {
    grid-column: span 2;
  }
}

@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .header-stats {
    align-self: stretch;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .filters-grid {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .search-item {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .material-master-container {
    padding: 4px;
  }
  .page-header {
    padding: 8px 12px;
    border-radius: 10px;
  }
  .main-title {
    font-size: 1.15rem;
  }
  .filter-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
    padding: 10px 12px;
  }
  .filter-actions {
    justify-content: flex-start;
  }
  .filters-grid {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 10px 12px;
  }
  .search-item {
    grid-column: span 1;
  }
  .filter-summary {
    padding: 8px 12px;
  }
  .stat-card {
    min-width: 60px;
    padding: 5px 8px;
  }
  .stat-number {
    font-size: 1.1rem;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* 动画效果 */
.table-card,
.page-header,
.action-section,
.result-section {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
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
  padding: 8px 12px;
  font-size: 0.85rem;
}

:deep(.el-table td) {
  padding: 6px 12px;
  font-size: 0.85rem;
  line-height: 1.3;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-tag) {
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.75rem;
  padding: 2px 6px;
  height: auto;
  line-height: 1.2;
}

:deep(.el-switch) {
  --el-switch-on-color: #2980b9;
}

:deep(.el-button--small) {
  padding: 4px 8px;
  font-size: 0.75rem;
  height: auto;
  line-height: 1.2;
}

:deep(.el-input__inner) {
  font-size: 0.85rem;
}

:deep(.el-select .el-input__inner) {
  font-size: 0.85rem;
}

/* 列設定ダイアログ */
.column-settings {
  padding: 16px 0;
}

.column-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.column-settings-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.column-settings-btn:hover {
  color: #2980b9;
  transform: scale(1.05);
}

.print-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.print-btn:hover {
  color: #e67e22;
  transform: scale(1.05);
}

/* 印刷設定ダイアログ */
.print-settings {
  padding: 16px 0;
}

.print-column-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 16px;
  max-height: 500px;
  overflow-y: auto;
  padding: 10px;
}

.print-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e9ecef;
}

.print-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 5px;
}

.print-section .el-checkbox {
  display: block;
  margin-bottom: 8px;
  margin-right: 0;
}

.print-options {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.print-options .el-divider {
  margin: 16px 0;
}

.sort-settings {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.sort-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  white-space: nowrap;
}
</style>
