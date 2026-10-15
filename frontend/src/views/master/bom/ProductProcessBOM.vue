<template>
  <div class="product-process-bom-container ppb-modern pb-std">
    <header class="ppb-hero page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="pb-bubbles" aria-hidden="true" />
      <div class="ppb-hero__inner">
        <div class="ppb-hero__brand">
          <div class="ppb-hero__icon-wrap">
            <el-icon :size="20"><Tools /></el-icon>
          </div>
          <div class="ppb-hero__titles">
            <h1 class="ppb-hero__title pb-hero-title">製品工程BOM管理</h1>
            <p class="ppb-hero__subtitle pb-hero-desc">工程フラグ・LT を一覧編集（セル変更は自動保存）</p>
          </div>
        </div>
        <div class="ppb-hero__stats">
          <div class="ppb-stat ppb-stat--total">
            <el-icon class="ppb-stat__ico"><List /></el-icon>
            <div class="ppb-stat__body">
              <span class="ppb-stat__num">{{ stats.total || 0 }}</span>
              <span class="ppb-stat__lbl">登録数</span>
            </div>
          </div>
          <div class="ppb-stat ppb-stat--active">
            <el-icon class="ppb-stat__ico"><CircleCheck /></el-icon>
            <div class="ppb-stat__body">
              <span class="ppb-stat__num">{{ stats.active_count || 0 }}</span>
              <span class="ppb-stat__lbl">現行</span>
            </div>
          </div>
          <div class="ppb-stat ppb-stat--halt">
            <el-icon class="ppb-stat__ico"><CircleClose /></el-icon>
            <div class="ppb-stat__body">
              <span class="ppb-stat__num">{{ stats.discontinued_count || 0 }}</span>
              <span class="ppb-stat__lbl">終息</span>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="ppb-workspace">
      <!-- 検索（1行コンパクト） -->
      <section class="ppb-toolbar">
        <div class="ppb-toolbar__compact">
          <div class="ppb-toolbar__search-row">
            <span class="ppb-pill">検索</span>
            <el-input
              v-model="filters.keyword"
              placeholder="製品コード・製品名"
              clearable
              class="ppb-search-input"
              @clear="handleFilter"
              @keyup.enter="handleFilter"
            >
              <template #prefix>
                <el-icon class="ppb-input-prefix"><Search /></el-icon>
              </template>
            </el-input>
          </div>
          <div class="ppb-toolbar__actions">
            <el-button class="tb-btn tb-btn-amber" size="small" @click="clearFilters">
              <el-icon><Refresh /></el-icon>
              <span class="tb-label">クリア</span>
            </el-button>
            <el-button class="tb-btn tb-btn-blue" size="small" @click="handleFilter">
              <el-icon><Search /></el-icon>
              <span class="tb-label">検索</span>
            </el-button>
            <el-button
              v-if="canEdit"
              class="tb-btn tb-btn-green"
              size="small"
              :loading="syncing"
              @click="handleSync"
            >
              <el-icon><Refresh /></el-icon>
              <span class="tb-label">同期</span>
            </el-button>
          </div>
        </div>
      </section>

      <!-- データ一覧 -->
      <section class="ppb-table-section">
        <el-card class="ppb-table-card" shadow="never">
          <template #header>
            <div class="ppb-table-cap">
              <div class="ppb-table-cap__left">
                <span class="ppb-table-cap__dot" />
                <span class="ppb-table-cap__title">登録一覧</span>
                <span class="ppb-table-cap__hint">自動保存 · デバウンス</span>
              </div>
            </div>
          </template>
          <el-table
            class="ppb-el-table"
            :data="bomList"
            v-loading="loading"
            stripe
            border
            size="small"
            style="width: 100%"
            :empty-text="'データがありません'"
            height="100%"
            :row-style="{ height: '34px' }"
            :header-cell-class-name="ppbHeaderCellClass"
            :cell-class-name="ppbBodyCellClass"
            @sort-change="handleSortChange"
            :default-sort="{ prop: 'product_name', order: 'ascending' }"
          >
            <!-- 終息 -->
            <el-table-column label="終息" width="60" align="center" fixed="left">
              <template #default="{ row }">
                <el-checkbox
                  v-model="row.is_discontinued"
                  class="ppb-dot ppb-dot--rose"
                  @change="handleCellChange(row)"
                />
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
                <el-checkbox class="ppb-dot" v-model="row.material_process" @change="handleCellChange(row)" />
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
                <el-checkbox class="ppb-dot" v-model="row.cuting_process" @change="handleCellChange(row)" />
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
                <el-checkbox class="ppb-dot" v-model="row.chamfering_process" @change="handleCellChange(row)" />
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
                <el-checkbox class="ppb-dot" v-model="row.swaging_process" @change="handleCellChange(row)" />
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
                <el-checkbox class="ppb-dot" v-model="row.forming_process" @change="handleCellChange(row)" />
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
                <el-checkbox class="ppb-dot" v-model="row.plating_process" @change="handleCellChange(row)" />
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
                  class="ppb-dot"
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
                <el-checkbox class="ppb-dot" v-model="row.welding_process" @change="handleCellChange(row)" />
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
                  class="ppb-dot"
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
                <el-checkbox class="ppb-dot" v-model="row.inspection_process" @change="handleCellChange(row)" />
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
                  class="ppb-dot"
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
                <el-checkbox class="ppb-dot" v-model="row.pre_plating_welding" @change="handleCellChange(row)" />
              </template>
            </el-table-column>

            <!-- 検査後溶接 -->
            <el-table-column label="検査後溶接" width="100" align="center">
              <template #default="{ row }">
                <el-checkbox
                  class="ppb-dot"
                  v-model="row.post_inspection_welding"
                  @change="handleCellChange(row)"
                />
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

            <!-- 操作列（アイコンのみ） -->
            <el-table-column v-if="canEdit || canDelete" label="操作" width="96" align="center" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons ppb-op-cell">
                  <el-tooltip v-if="canEdit" content="編集" placement="top">
                    <el-button
                      size="small"
                      type="primary"
                      :icon="Edit"
                      circle
                      class="action-btn-edit"
                      @click="handleEdit(row)"
                    />
                  </el-tooltip>
                  <el-tooltip v-if="canDelete" content="削除" placement="top">
                    <el-button
                      size="small"
                      type="danger"
                      :icon="Delete"
                      circle
                      class="action-btn-delete"
                      @click="handleDelete(row)"
                    />
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <div class="pagination-bar">
          <div class="pagination-summary">
            <span class="pagination-summary__item">
              <span class="pagination-summary__label">合計</span>
              <b class="pagination-summary__value">{{ pagination.total.toLocaleString('ja-JP') }}</b>
              <span class="pagination-summary__unit">件</span>
            </span>
            <span class="pagination-summary__item pagination-summary__item--range">
              <span class="pagination-summary__label">表示</span>
              <b class="pagination-summary__value">{{ pageRangeText }}</b>
            </span>
          </div>
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.limit"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="sizes, prev, pager, next, jumper"
            small
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            class="ppb-pagination modern-pagination"
          />
        </div>
      </section>
    </div>

    <!-- 編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      width="1020px"
      :close-on-click-modal="false"
      destroy-on-close
      align-center
      append-to-body
      class="ppb-dialog product-process-dialog"
    >
      <template #header>
        <div class="ppb-dlg-header">
          <div class="ppb-dlg-header__accent" aria-hidden="true" />
          <div class="ppb-dlg-header__main">
            <div class="ppb-dlg-header__icon">
              <el-icon :size="22"><EditPen /></el-icon>
            </div>
            <div>
              <h3 class="ppb-dlg-header__title">製品工程BOM 編集</h3>
              <p class="ppb-dlg-header__desc">タブごとに工程・LT をまとめて確認・更新できます。</p>
            </div>
          </div>
        </div>
      </template>
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
        <div class="ppb-dlg-footer dialog-footer">
          <el-button size="small" round @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" round @click="handleSubmit" :loading="submitting">
            <el-icon class="ppb-dlg-footer__ico"><CircleCheck /></el-icon>
            保存する
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { TableColumnCtx } from 'element-plus'
import {
  Tools,
  Refresh,
  Search,
  Edit,
  Delete,
  List,
  CircleCheck,
  CircleClose,
  EditPen,
} from '@element-plus/icons-vue'
import {
  fetchProductProcessBOMList,
  fetchProductProcessBOMById,
  updateProductProcessBOM,
  deleteProductProcessBOM,
  syncProductInfo,
  type ProductProcessBOM,
} from '@/api/master/productProcessBomMaster'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canEdit, canDelete } = useMasterOperationPermission()

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
const saveTimers = new Map<number, ReturnType<typeof setTimeout>>()

// 分页状态
const pagination = ref({
  page: 1,
  limit: 20,
  total: 0,
})

const pageRangeText = computed(() => {
  const total = pagination.value.total
  if (!total) return '0'
  const start = pagination.value.limit * (pagination.value.page - 1) + 1
  const end = Math.min(pagination.value.limit * pagination.value.page, total)
  return `${start}–${end}`
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

/** 一覧テーブル：列ラベル → 色グループ（ヘッダー・セル共通） */
const PPB_COL_GROUP: Record<string, string> = {
  終息: 'ppb-col-meta',
  製品CD: 'ppb-col-meta',
  製品名: 'ppb-col-meta',
  最低在庫日数: 'ppb-col-stock',
  安全在庫日数: 'ppb-col-stock',
  材料工程: 'ppb-col-g0',
  材料工程LT: 'ppb-col-g0',
  切断工程: 'ppb-col-g1',
  切断工程LT: 'ppb-col-g1',
  面取工程: 'ppb-col-g2',
  面取工程LT: 'ppb-col-g2',
  SW工程: 'ppb-col-g3',
  SW工程LT: 'ppb-col-g3',
  成型工程: 'ppb-col-g0',
  成型工程LT: 'ppb-col-g0',
  メッキ工程: 'ppb-col-g1',
  メッキ工程LT: 'ppb-col-g1',
  外注メッキ工程: 'ppb-col-g2',
  外注メッキ工程LT: 'ppb-col-g2',
  溶接工程: 'ppb-col-g3',
  溶接工程LT: 'ppb-col-g3',
  外注溶接工程: 'ppb-col-g0',
  外注溶接工程LT: 'ppb-col-g0',
  検査工程: 'ppb-col-g1',
  検査工程LT: 'ppb-col-g1',
  外注倉庫工程: 'ppb-col-g2',
  外注倉庫工程LT: 'ppb-col-g2',
  メッキ前溶接: 'ppb-col-g3',
  検査後溶接: 'ppb-col-g0',
  検査後溶接工程LT: 'ppb-col-g0',
  操作: 'ppb-col-act',
}

function ppbHeaderCellClass({ column }: { column: TableColumnCtx<ProductProcessBOM> }) {
  const label = column.label
  return label && typeof label === 'string' ? (PPB_COL_GROUP[label] ?? '') : ''
}

function ppbBodyCellClass({ column }: { column: TableColumnCtx<ProductProcessBOM> }) {
  const label = column.label
  return label && typeof label === 'string' ? (PPB_COL_GROUP[label] ?? '') : ''
}

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
  if (!guardMasterOperation(canEdit)) return
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
  if (!guardMasterOperation(canEdit)) return
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
  if (!guardMasterOperation(canEdit)) return
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
  if (!guardMasterOperation(canDelete)) return
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
  if (!guardMasterOperation(canEdit)) return
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
  --ppb-app-chrome: 84px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  height: calc(100vh - var(--ppb-app-chrome));
  height: calc(100dvh - var(--ppb-app-chrome));
  max-height: calc(100vh - var(--ppb-app-chrome));
  max-height: calc(100dvh - var(--ppb-app-chrome));
  min-height: 0;
  overflow: hidden;
  padding: 12px;
  background:
    radial-gradient(1100px 380px at 0% 0%, rgba(63, 98, 18, 0.1), transparent 60%),
    radial-gradient(900px 380px at 100% 0%, rgba(163, 230, 53, 0.08), transparent 60%),
    linear-gradient(160deg, #f7fee7 0%, #f8fafc 45%, #ecfccb 100%);
}

/* メイン作業面：ツールバー＋表＋ページを一枚に */
.ppb-workspace {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 12px 32px -16px rgba(15, 23, 42, 0.12);
}

/* —— ヒーロー（オリーブ系・他頁と分色） —— */
.ppb-hero {
  position: relative;
  isolation: isolate;
  flex-shrink: 0;
  border-radius: 16px;
  margin-bottom: 0;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #3f6212 0%, #4d7c0f 34%, #65a30d 66%, #a3e635 100%);
  box-shadow:
    0 18px 36px -18px rgba(63, 98, 18, 0.55),
    0 4px 12px -6px rgba(101, 163, 13, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  z-index: 0;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
  pointer-events: none;
}

.ppb-hero__inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 14px;
  width: 100%;
}

.ppb-hero__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.ppb-hero__icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(63, 98, 18, 0.3);
}

.ppb-hero__title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #fff;
}

.ppb-hero__subtitle {
  margin: 0;
  max-width: 520px;
  color: rgba(255, 255, 255, 0.88);
}

.ppb-hero__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ppb-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px 5px 8px;
  min-width: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-left-width: 3px;
  border-left-color: rgba(255, 255, 255, 0.45);
}

.ppb-stat--total {
  border-left-color: #d9f99d;
}

.ppb-stat--active {
  border-left-color: #86efac;
  background: rgba(16, 185, 129, 0.28);
}

.ppb-stat--halt {
  border-left-color: #fda4af;
  background: rgba(190, 18, 60, 0.28);
}

.ppb-stat__ico {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.88);
}

.ppb-stat--active .ppb-stat__ico {
  color: #6ee7b7;
}

.ppb-stat--halt .ppb-stat__ico {
  color: #fca5a5;
}

.ppb-stat__body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.ppb-stat__num {
  font-size: 1rem;
  font-weight: 800;
  color: #fff;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.ppb-stat__lbl {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(226, 232, 240, 0.7);
}

/* —— ツールバー 1行 —— */
.ppb-toolbar {
  flex-shrink: 0;
  position: relative;
  background: linear-gradient(110deg, #f7fee7 0%, #ffffff 60%);
  border-radius: 0;
  padding: 8px 12px 8px 16px;
  margin-bottom: 0;
  border: none;
  border-bottom: 1px solid #d9f99d;
  box-shadow: none;
}
.ppb-toolbar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 4px;
  border-radius: 99px;
  background: linear-gradient(180deg, #a3e635, #65a30d, #3f6212);
}

.ppb-toolbar__actions .tb-btn {
  --k-rgb: 101 163 13;
  --k-fg: #3f6212;
  --k-bd: #bef264;
  --k-tint: #ecfccb;
  --k-tint-h: #d9f99d;
  --k-ico: #65a30d;
  height: 30px !important;
  padding: 0 12px 0 10px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  margin: 0 !important;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  border: 1px solid var(--k-bd) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(63, 98, 18, 0.2) !important;
}
.ppb-toolbar__actions .tb-btn :deep(.el-icon) {
  color: var(--k-ico);
}
.ppb-toolbar__actions .tb-btn:hover:not(:disabled) {
  color: rgb(var(--k-rgb)) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 30%, var(--k-tint-h) 100%) !important;
  transform: translateY(-1px);
}
.ppb-toolbar__actions .tb-btn-blue {
  --k-rgb: 37 99 235;
  --k-fg: #1d4ed8;
  --k-bd: #93c5fd;
  --k-tint: #dbeafe;
  --k-tint-h: #bfdbfe;
  --k-ico: #3b82f6;
}
.ppb-toolbar__actions .tb-btn-amber {
  --k-rgb: 217 119 6;
  --k-fg: #92400e;
  --k-bd: #fcd34d;
  --k-tint: #fef3c7;
  --k-tint-h: #fde68a;
  --k-ico: #d97706;
}
.ppb-toolbar__actions .tb-btn-green {
  --k-rgb: 5 150 105;
  --k-fg: #047857;
  --k-bd: #6ee7b7;
  --k-tint: #d1fae5;
  --k-tint-h: #a7f3d0;
  --k-ico: #10b981;
}

.ppb-toolbar__compact {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
}

.ppb-toolbar__search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: min(100%, 220px);
  max-width: 400px;
}

.ppb-pill {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 3px 8px;
  border-radius: 6px;
  color: #3f6212;
  background: linear-gradient(180deg, #ecfccb 0%, #d9f99d 100%);
  border: 1px solid #bef264;
}

.ppb-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.ppb-toolbar__actions :deep(.el-button--primary) {
  border: none;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}

.ppb-toolbar__actions :deep(.el-button--primary:hover) {
  filter: brightness(1.05);
}

.ppb-toolbar__actions :deep(.el-button--success.is-plain) {
  --el-button-hover-bg-color: rgba(16, 185, 129, 0.1);
  --el-button-hover-border-color: #10b981;
  --el-button-hover-text-color: #059669;
}

.ppb-input-prefix {
  font-size: 15px;
  color: #94a3b8;
}

.ppb-search-input {
  flex: 1;
  min-width: 0;
}

.ppb-search-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  padding-left: 8px;
  min-height: 30px;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.3) inset;
  transition: box-shadow 0.2s ease;
}

.ppb-search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #a3e635 inset;
}

.ppb-search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(101, 163, 13, 0.35) inset;
}

/* —— テーブル —— */
.ppb-table-section {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 0;
}

.ppb-table-cap {
  display: flex;
  align-items: center;
  width: 100%;
}

.ppb-table-cap__left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ppb-table-cap__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: linear-gradient(135deg, #65a30d, #a3e635);
  box-shadow: 0 0 0 2px rgba(101, 163, 13, 0.22);
}

.ppb-table-cap__title {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.ppb-table-cap__hint {
  font-size: 10px;
  color: #4d7c0f;
  padding: 2px 8px;
  border-radius: 999px;
  background: #ecfccb;
  border: 1px solid #bef264;
}

.ppb-table-card {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 0;
  border: none;
  box-shadow: none;
  overflow: hidden;
}

.ppb-table-card :deep(.el-card__header) {
  flex-shrink: 0;
  padding: 6px 10px;
  border-bottom: 1px solid #d9f99d;
  background:
    linear-gradient(90deg, #65a30d, #a3e635, #bef264) 0 0 / 100% 3px no-repeat,
    linear-gradient(180deg, #f7fee7 0%, #ecfccb 100%);
}

.ppb-table-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.ppb-table-card :deep(.el-table) {
  flex: 1 1 auto;
  height: 100% !important;
  font-size: 11px;
  --el-table-border-color: #e2e8f0;
  --el-table-header-bg-color: #f7fee7;
  --el-table-row-hover-bg-color: #ecfccb;
  --el-table-bg-color: #ffffff;
  --el-bg-color: #ffffff;
}

.ppb-table-card :deep(.el-table__inner-wrapper) {
  height: 100%;
}

.ppb-table-card :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
}

.ppb-table-card :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #f7fee7 0%, #ecfccb 100%) !important;
  color: #365314;
  font-weight: 700;
  font-size: 10px;
  padding: 5px 2px;
  border-bottom: 1px solid #d9f99d !important;
}

.ppb-table-card :deep(.el-table td.el-table__cell) {
  padding: 2px 1px;
  border-bottom: 1px solid #f1f5f9 !important;
  background-color: #ffffff !important;
}

/* ホバーも不透明（固定列透け防止） */
.ppb-table-card :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: #ecfccb !important;
}

/* 列グループ色：必ず不透明 Hex（左右固定列の下に中身が見えるのを防止） */
.ppb-table-card :deep(th.el-table__cell.ppb-col-meta) {
  background: linear-gradient(180deg, #e0e7ff 0%, #c7d2fe 100%) !important;
  color: #312e81 !important;
  border-bottom-color: #a5b4fc !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-meta) {
  background-color: #eef2ff !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-stock) {
  background: linear-gradient(180deg, #fef3c7 0%, #fde68a 100%) !important;
  color: #78350f !important;
  border-bottom-color: #fcd34d !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-stock) {
  background-color: #fffbeb !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g0) {
  background: linear-gradient(180deg, #ccfbf1 0%, #99f6e4 100%) !important;
  color: #115e59 !important;
  border-bottom-color: #5eead4 !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g0) {
  background-color: #f0fdfa !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g1) {
  background: linear-gradient(180deg, #ede9fe 0%, #ddd6fe 100%) !important;
  color: #5b21b6 !important;
  border-bottom-color: #c4b5fd !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g1) {
  background-color: #f5f3ff !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g2) {
  background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 100%) !important;
  color: #0c4a6e !important;
  border-bottom-color: #7dd3fc !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g2) {
  background-color: #f0f9ff !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g3) {
  background: linear-gradient(180deg, #ffedd5 0%, #fed7aa 100%) !important;
  color: #7c2d12 !important;
  border-bottom-color: #fdba74 !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g3) {
  background-color: #fff7ed !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-act) {
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
  color: #1e293b !important;
  border-bottom-color: #cbd5e1 !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-act) {
  background-color: #f8fafc !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-meta) {
  background-color: #e0e7ff !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-stock) {
  background-color: #fef3c7 !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g0) {
  background-color: #ccfbf1 !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g1) {
  background-color: #ede9fe !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g2) {
  background-color: #e0f2fe !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g3) {
  background-color: #ffedd5 !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-act) {
  background-color: #f1f5f9 !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-meta) {
  background-color: #c7d2fe !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-stock) {
  background-color: #fde68a !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g0) {
  background-color: #99f6e4 !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g1) {
  background-color: #ddd6fe !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g2) {
  background-color: #bae6fd !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g3) {
  background-color: #fed7aa !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-act) {
  background-color: #e2e8f0 !important;
}

/* EP2 sticky 固定列：不透明＋影で下層スクロール内容を完全に隠す */
.ppb-table-card :deep(th.el-table-fixed-column--left),
.ppb-table-card :deep(td.el-table-fixed-column--left) {
  background-clip: padding-box !important;
  z-index: 3 !important;
}

.ppb-table-card :deep(th.el-table-fixed-column--left.ppb-col-meta),
.ppb-table-card :deep(td.el-table-fixed-column--left.ppb-col-meta) {
  background-color: #eef2ff !important;
}

.ppb-table-card :deep(th.el-table-fixed-column--left.ppb-col-meta) {
  background: linear-gradient(180deg, #e0e7ff 0%, #c7d2fe 100%) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table-fixed-column--left.ppb-col-meta) {
  background-color: #e0e7ff !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table-fixed-column--left.ppb-col-meta) {
  background-color: #c7d2fe !important;
}

.ppb-table-card :deep(th.el-table-fixed-column--right),
.ppb-table-card :deep(td.el-table-fixed-column--right) {
  background-clip: padding-box !important;
  z-index: 3 !important;
}

.ppb-table-card :deep(th.el-table-fixed-column--right.ppb-col-act),
.ppb-table-card :deep(td.el-table-fixed-column--right.ppb-col-act) {
  background-color: #f8fafc !important;
}

.ppb-table-card :deep(th.el-table-fixed-column--right.ppb-col-act) {
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table-fixed-column--right.ppb-col-act) {
  background-color: #f1f5f9 !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table-fixed-column--right.ppb-col-act) {
  background-color: #e2e8f0 !important;
}

.ppb-table-card :deep(.el-table__header th.el-table-fixed-column--left.is-last-column),
.ppb-table-card :deep(.el-table__body td.el-table-fixed-column--left.is-last-column) {
  border-right: 1px solid #a5b4fc !important;
  box-shadow: 6px 0 10px -6px rgba(49, 46, 129, 0.28);
}

.ppb-table-card :deep(.el-table__header th.el-table-fixed-column--right.is-first-column),
.ppb-table-card :deep(.el-table__body td.el-table-fixed-column--right.is-first-column) {
  border-left: 1px solid #cbd5e1 !important;
  box-shadow: -6px 0 10px -6px rgba(15, 23, 42, 0.22);
}

.ppb-table-card :deep(.el-table__body-wrapper) {
  will-change: scroll-position;
}

.ppb-table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.ppb-table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.ppb-table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.ppb-table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.ppb-table-card :deep(.el-input-number .el-input__wrapper) {
  border-radius: 8px;
}

.ppb-table-card :deep(.el-input-number .el-input__inner) {
  text-align: center;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.ppb-table-card :deep(.el-checkbox.ppb-dot) {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.ppb-table-card :deep(.el-checkbox.ppb-dot .el-checkbox__input) {
  line-height: 1;
}

.ppb-table-card :deep(.el-checkbox.ppb-dot .el-checkbox__inner) {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  background: #ffffff;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background-color 0.2s ease;
}

.ppb-table-card :deep(.el-checkbox.ppb-dot .el-checkbox__inner::after) {
  width: 8px;
  height: 8px;
  border: none;
  border-radius: 50%;
  background: #65a30d;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%) scale(0);
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.ppb-table-card :deep(.el-checkbox.ppb-dot.is-checked .el-checkbox__inner) {
  border-color: #65a30d;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(101, 163, 13, 0.18);
}

.ppb-table-card :deep(.el-checkbox.ppb-dot.is-checked .el-checkbox__inner::after) {
  transform: translate(-50%, -50%) scale(1);
  background: linear-gradient(135deg, #65a30d, #a3e635);
}

.ppb-table-card :deep(.el-checkbox.ppb-dot.ppb-dot--rose.is-checked .el-checkbox__inner) {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}

.ppb-table-card :deep(.el-checkbox.ppb-dot.ppb-dot--rose.is-checked .el-checkbox__inner::after) {
  background: linear-gradient(135deg, #dc2626, #f87171);
}

.ppb-table-card :deep(.el-checkbox.ppb-dot:hover .el-checkbox__inner) {
  border-color: #94a3b8;
}

.ppb-table-card :deep(.el-checkbox.ppb-dot.is-checked:hover .el-checkbox__inner) {
  border-color: #4d7c0f;
}

.ppb-table-card :deep(.el-checkbox.ppb-dot.ppb-dot--rose.is-checked:hover .el-checkbox__inner) {
  border-color: #b91c1c;
}

/* ページネーション */
.pagination-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 10px;
  padding: 5px 10px 8px;
  border-top: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}
.pagination-summary {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}
.pagination-summary__item {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
  font-size: 12px;
  color: #475569;
}
.pagination-summary__label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}
.pagination-summary__value {
  font-weight: 700;
  color: #4d7c0f;
  font-variant-numeric: tabular-nums;
}
.pagination-summary__unit {
  font-size: 11px;
  color: #64748b;
}
.pagination-summary__item--range .pagination-summary__value {
  color: #0ea5e9;
}
.pagination-bar .modern-pagination {
  margin-left: auto;
}
.pagination-bar :deep(.el-pagination) {
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 4px;
  font-size: 12px;
}
.pagination-bar :deep(.el-pagination .el-pager li),
.pagination-bar :deep(.el-pagination button) {
  min-width: 26px;
  height: 26px;
  line-height: 26px;
}
.pagination-bar :deep(.el-pager li.is-active) {
  color: #fff;
  font-weight: 700;
  background: linear-gradient(135deg, #4d7c0f 0%, #65a30d 55%, #a3e635 100%);
}

/* 行アクション（アイコンのみ） */
.action-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap;
}

.ppb-op-cell {
  line-height: 1;
}

.action-btn-edit {
  width: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  border: none !important;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
  box-shadow: 0 1px 6px rgba(37, 99, 235, 0.3);
}

.action-btn-edit:hover {
  filter: brightness(1.06);
}

.action-btn-delete {
  width: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  border: none !important;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  box-shadow: 0 1px 6px rgba(239, 68, 68, 0.28);
}

.action-btn-delete:hover {
  filter: brightness(1.05);
}

.action-btn-edit :deep(.el-icon),
.action-btn-delete :deep(.el-icon) {
  font-size: 14px;
}

/* —— ダイアログ —— */
.product-process-dialog.ppb-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 20px 50px -14px rgba(15, 23, 42, 0.35),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.product-process-dialog.ppb-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.product-process-dialog.ppb-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 12px;
  z-index: 2;
}

.product-process-dialog.ppb-dialog :deep(.el-dialog__close) {
  color: #64748b;
  font-size: 18px;
}

.product-process-dialog.ppb-dialog :deep(.el-dialog__close:hover) {
  color: #0f172a;
}

.product-process-dialog.ppb-dialog :deep(.el-dialog__body) {
  padding: 0 12px 12px;
  background: linear-gradient(180deg, #eef2f7 0%, #e2e8f0 100%);
}

.ppb-dlg-header {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.ppb-dlg-header__accent {
  height: 3px;
  background: linear-gradient(90deg, #3f6212, #65a30d, #a3e635);
}

.ppb-dlg-header__main {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px 40px 10px 14px;
}

.ppb-dlg-header__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(145deg, #4d7c0f 0%, #65a30d 100%);
  box-shadow: 0 8px 20px rgba(63, 98, 18, 0.35);
}

.ppb-dlg-header__title {
  margin: 0 0 4px;
  font-size: 1rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.ppb-dlg-header__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: #64748b;
}

.ppb-dlg-footer.dialog-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 12px !important;
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%) !important;
  border-top: 1px solid #e2e8f0 !important;
}

.ppb-dlg-footer__ico {
  margin-right: 6px;
  vertical-align: middle;
}

.ppb-dlg-footer :deep(.el-button--primary) {
  border: none;
  background: linear-gradient(135deg, #4d7c0f 0%, #65a30d 100%);
  box-shadow: 0 4px 16px rgba(63, 98, 18, 0.35);
}

.ppb-dlg-footer :deep(.el-button--primary:hover) {
  filter: brightness(1.05);
}

/* 編集フォーム */
.edit-form {
  background: #fff;
  border-radius: 10px;
  padding: 10px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
}

.edit-tabs {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
}

.edit-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 6px 10px 0;
  border-bottom: 1px solid #e2e8f0;
}

.edit-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.edit-tabs :deep(.el-tabs__item) {
  font-size: 12px;
  font-weight: 600;
  padding: 7px 14px;
  color: #6b7280;
  border-radius: 6px 6px 0 0;
  margin-right: 2px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.edit-tabs :deep(.el-tabs__item:hover) {
  color: #4d7c0f;
  background: #ecfccb;
}

.edit-tabs :deep(.el-tabs__item.is-active) {
  color: #3f6212;
  background: #fff;
  border-color: #e2e8f0;
  border-bottom-color: #fff;
  font-weight: 700;
}

.edit-tabs :deep(.el-tabs__content) {
  padding: 10px 12px;
  min-height: 280px;
  max-height: min(52vh, 420px);
  overflow-y: auto;
  background: white;
}

/* 表单网格布局 - 紧凑设计 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 12px;
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
  border-color: #a3e635;
}

.edit-tabs :deep(.el-input__inner:focus),
.edit-tabs :deep(.el-input-number .el-input__inner:focus) {
  border-color: #65a30d;
  box-shadow: 0 0 0 3px rgba(101, 163, 13, 0.2);
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
  background-color: #65a30d;
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

@media (max-width: 1200px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}

@media (max-width: 900px) {
  .ppb-hero__inner {
    flex-direction: column;
    align-items: stretch;
  }

  .ppb-hero__stats {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .product-process-bom-container {
    padding: 10px;
  }

  .ppb-hero__title {
    font-size: 1.15rem;
  }

  .ppb-toolbar__compact {
    flex-direction: column;
    align-items: stretch;
  }

  .ppb-toolbar__search-row {
    max-width: none;
  }

  .ppb-toolbar__actions {
    justify-content: stretch;
  }

  .ppb-toolbar__actions :deep(.el-button) {
    flex: 1;
  }
}
</style>
