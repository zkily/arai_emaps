<template>
  <div class="product-process-bom-container">
    <!-- 顶部英雄区 -->
    <header class="ppb-hero">
      <div class="ppb-hero__accent" aria-hidden="true" />
      <div class="ppb-hero__grid" />
      <div class="ppb-hero__inner">
        <div class="ppb-hero__brand">
          <div class="ppb-hero__icon-wrap">
            <el-icon :size="20"><Tools /></el-icon>
          </div>
          <div class="ppb-hero__titles">
            <h1 class="ppb-hero__title">製品工程BOM管理</h1>
            <p class="ppb-hero__subtitle">工程フラグ・LT を一覧編集（セル変更は自動保存）</p>
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
            <el-button size="small" @click="clearFilters" :icon="Refresh">クリア</el-button>
            <el-button type="primary" size="small" @click="handleFilter" :icon="Search">検索</el-button>
            <el-button type="success" size="small" plain @click="handleSync" :icon="Refresh" :loading="syncing">
              同期
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
          style="width: 100%"
          :empty-text="'データがありません'"
          height="calc(100vh - 228px)"
          :row-style="{ height: '34px' }"
          :header-cell-class-name="ppbHeaderCellClass"
          :cell-class-name="ppbBodyCellClass"
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

          <!-- 操作列（アイコンのみ） -->
          <el-table-column label="操作" width="96" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons ppb-op-cell">
                <el-tooltip content="編集" placement="top">
                  <el-button
                    size="small"
                    type="primary"
                    :icon="Edit"
                    circle
                    class="action-btn-edit"
                    @click="handleEdit(row)"
                  />
                </el-tooltip>
                <el-tooltip content="削除" placement="top">
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
      </section>

      <!-- ページネーション -->
      <div class="ppb-pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          class="ppb-pagination"
        />
      </div>
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
import { ref, onMounted } from 'vue'
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
  return label && typeof label === 'string' ? PPB_COL_GROUP[label] ?? '' : ''
}

function ppbBodyCellClass({ column }: { column: TableColumnCtx<ProductProcessBOM> }) {
  const label = column.label
  return label && typeof label === 'string' ? PPB_COL_GROUP[label] ?? '' : ''
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
  padding: 8px 10px 10px;
  box-sizing: border-box;
  background:
    radial-gradient(ellipse 90% 55% at 0% -8%, rgba(99, 102, 241, 0.12), transparent 45%),
    radial-gradient(ellipse 70% 45% at 100% 5%, rgba(14, 165, 233, 0.1), transparent 40%),
    radial-gradient(ellipse 60% 40% at 50% 100%, rgba(139, 92, 246, 0.06), transparent 50%),
    linear-gradient(165deg, #f8fafc 0%, #f1f5f9 45%, #eef2f7 100%);
}

/* メイン作業面：ツールバー＋表＋ページを一枚に */
.ppb-workspace {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 12px 32px -16px rgba(15, 23, 42, 0.12);
  overflow: hidden;
}

/* —— ヒーロー（コンパクト） —— */
.ppb-hero {
  position: relative;
  border-radius: 12px;
  margin-bottom: 8px;
  overflow: hidden;
  box-shadow:
    0 10px 24px -14px rgba(15, 23, 42, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.12) inset;
}

.ppb-hero__accent {
  height: 3px;
  width: 100%;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 40%, #0ea5e9 100%);
}

.ppb-hero__grid {
  position: absolute;
  inset: 0;
  opacity: 0.05;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.35) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.35) 1px, transparent 1px);
  background-size: 20px 20px;
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
  padding: 10px 14px;
  background:
    linear-gradient(125deg, rgba(255, 255, 255, 0.06) 0%, transparent 42%),
    linear-gradient(135deg, #1e1b4b 0%, #312e81 32%, #4338ca 68%, #5b21b6 100%);
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
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}

.ppb-hero__title {
  margin: 0 0 1px;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #fff;
  line-height: 1.2;
}

.ppb-hero__subtitle {
  margin: 0;
  max-width: 520px;
  font-size: 10px;
  line-height: 1.35;
  color: rgba(226, 232, 240, 0.82);
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
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-left-width: 3px;
  border-left-color: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(8px);
  transition: background 0.2s ease, border-color 0.2s ease;
}

.ppb-stat:hover {
  background: rgba(255, 255, 255, 0.12);
}

.ppb-stat--total {
  border-left-color: #7dd3fc;
}

.ppb-stat--active {
  border-left-color: #4ade80;
}

.ppb-stat--halt {
  border-left-color: #fb923c;
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
  background: linear-gradient(180deg, #fafbff 0%, #ffffff 100%);
  border-radius: 0;
  padding: 6px 10px;
  margin-bottom: 0;
  border: none;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: none;
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
  color: #4f46e5;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid rgba(99, 102, 241, 0.22);
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
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.4) inset;
}

.ppb-search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.28) inset;
}

/* —— テーブル —— */
.ppb-table-section {
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
  background: linear-gradient(135deg, #6366f1, #0ea5e9);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.ppb-table-cap__title {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.ppb-table-cap__hint {
  font-size: 10px;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.ppb-table-card {
  border-radius: 0;
  border: none;
  box-shadow: none;
  overflow: hidden;
}

.ppb-table-card :deep(.el-card__header) {
  padding: 6px 10px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.ppb-table-card :deep(.el-card__body) {
  padding: 0;
}

.ppb-table-card :deep(.el-table) {
  font-size: 11px;
  --el-table-border-color: transparent;
  --el-table-header-bg-color: #f1f5f9;
}

.ppb-table-card :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%) !important;
  color: #334155;
  font-weight: 700;
  font-size: 10px;
  padding: 5px 2px;
  border-bottom: 1px solid #e2e8f0 !important;
}

.ppb-table-card :deep(.el-table td.el-table__cell) {
  padding: 2px 1px;
  border-bottom: 1px solid #f1f5f9 !important;
}

.ppb-table-card :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: rgba(99, 102, 241, 0.06) !important;
}

/* 列グループ色（工程ブロックを識別しやすく） */
.ppb-table-card :deep(th.el-table__cell.ppb-col-meta) {
  background: linear-gradient(180deg, #e0e7ff 0%, #c7d2fe 100%) !important;
  color: #312e81 !important;
  border-bottom-color: #a5b4fc !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-meta) {
  background-color: rgba(99, 102, 241, 0.06) !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-stock) {
  background: linear-gradient(180deg, #fef3c7 0%, #fde68a 100%) !important;
  color: #78350f !important;
  border-bottom-color: #fcd34d !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-stock) {
  background-color: rgba(245, 158, 11, 0.08) !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g0) {
  background: linear-gradient(180deg, #ccfbf1 0%, #99f6e4 100%) !important;
  color: #115e59 !important;
  border-bottom-color: #5eead4 !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g0) {
  background-color: rgba(45, 212, 191, 0.07) !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g1) {
  background: linear-gradient(180deg, #ede9fe 0%, #ddd6fe 100%) !important;
  color: #5b21b6 !important;
  border-bottom-color: #c4b5fd !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g1) {
  background-color: rgba(139, 92, 246, 0.07) !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g2) {
  background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 100%) !important;
  color: #0c4a6e !important;
  border-bottom-color: #7dd3fc !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g2) {
  background-color: rgba(14, 165, 233, 0.07) !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-g3) {
  background: linear-gradient(180deg, #ffedd5 0%, #fed7aa 100%) !important;
  color: #7c2d12 !important;
  border-bottom-color: #fdba74 !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-g3) {
  background-color: rgba(249, 115, 22, 0.07) !important;
}

.ppb-table-card :deep(th.el-table__cell.ppb-col-act) {
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
  color: #1e293b !important;
  border-bottom-color: #cbd5e1 !important;
}

.ppb-table-card :deep(td.el-table__cell.ppb-col-act) {
  background-color: rgba(148, 163, 184, 0.08) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-meta) {
  background-color: rgba(99, 102, 241, 0.09) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-stock) {
  background-color: rgba(245, 158, 11, 0.11) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g0) {
  background-color: rgba(45, 212, 191, 0.1) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g1) {
  background-color: rgba(139, 92, 246, 0.1) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g2) {
  background-color: rgba(14, 165, 233, 0.1) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-g3) {
  background-color: rgba(249, 115, 22, 0.1) !important;
}

.ppb-table-card :deep(.el-table__row--striped td.el-table__cell.ppb-col-act) {
  background-color: rgba(148, 163, 184, 0.12) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-meta) {
  background-color: rgba(99, 102, 241, 0.14) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-stock) {
  background-color: rgba(245, 158, 11, 0.16) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g0) {
  background-color: rgba(45, 212, 191, 0.14) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g1) {
  background-color: rgba(139, 92, 246, 0.14) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g2) {
  background-color: rgba(14, 165, 233, 0.14) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-g3) {
  background-color: rgba(249, 115, 22, 0.14) !important;
}

.ppb-table-card :deep(.el-table__body tr:hover > td.el-table__cell.ppb-col-act) {
  background-color: rgba(148, 163, 184, 0.18) !important;
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

.ppb-table-card :deep(.el-checkbox) {
  display: flex;
  justify-content: center;
}

.ppb-table-card :deep(.el-checkbox__inner) {
  border-radius: 6px;
}

/* ページネーション */
.ppb-pagination-wrap {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 4px 10px 6px;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  border-radius: 0;
  border: none;
  border-top: 1px solid #e2e8f0;
  box-shadow: none;
}

.ppb-pagination-wrap :deep(.el-pagination) {
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 4px;
}

.ppb-pagination-wrap :deep(.el-pagination .el-select .el-input__wrapper) {
  min-height: 28px;
}

.ppb-pagination :deep(.el-pagination__total) {
  font-weight: 600;
  color: #64748b;
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
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
  box-shadow: 0 1px 6px rgba(79, 70, 229, 0.3);
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
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #0ea5e9);
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
  background: linear-gradient(145deg, #7c3aed 0%, #6366f1 100%);
  box-shadow: 0 8px 20px rgba(124, 58, 237, 0.35);
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
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  box-shadow: 0 4px 16px rgba(79, 70, 229, 0.35);
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
  color: #4f46e5;
  background: rgba(99, 102, 241, 0.08);
}

.edit-tabs :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
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
  border-color: #818cf8;
}

.edit-tabs :deep(.el-input__inner:focus),
.edit-tabs :deep(.el-input-number .el-input__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
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
  background-color: #6366f1;
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
