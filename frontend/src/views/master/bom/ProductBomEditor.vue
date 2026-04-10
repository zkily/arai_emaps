<template>
  <div class="bom-editor">
    <header class="pbe-hero">
      <div class="pbe-hero__accent" aria-hidden="true" />
      <div class="pbe-hero__inner">
        <div class="pbe-hero__brand">
          <div class="pbe-hero__icon">
            <el-icon :size="20"><Document /></el-icon>
          </div>
          <div class="pbe-hero__text">
            <h1 class="pbe-hero__title">製品BOM表管理</h1>
            <p class="pbe-hero__sub">製品を選ぶと左に工程順、右にBOMの材料・部品（版選択後）· 下に構成ツリー</p>
          </div>
        </div>
        <el-button type="primary" size="small" :icon="Plus" @click="openCreateDialog">新規BOM</el-button>
      </div>
    </header>

    <!-- 製品 → BOM版 -->
    <el-card class="pbe-toolbar-card filter-card" shadow="never">
      <el-form :inline="true" class="pbe-filter-form filter-form" label-width="68px">
        <el-form-item label="製品">
          <el-select
            v-model="selectedProductCd"
            filterable
            clearable
            placeholder="製品を選択"
            class="pbe-filt-product"
            size="small"
            :loading="loadingProducts"
            @change="onProductChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="`${p.product_cd} — ${p.product_name || ''}`"
              :value="p.product_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="BOM版">
          <el-select
            v-model="selectedHeaderId"
            clearable
            placeholder="先に製品を選択"
            class="pbe-filt-header"
            size="small"
            :disabled="!selectedProductCd"
            :loading="loadingProductHeaders"
            @change="onHeaderIdChange"
          >
            <el-option
              v-for="h in productHeaders"
              :key="h.id"
              :label="`${h.revision} · ${bomTypeLabel(h.bom_type)} · ${statusLabel(h.status)}`"
              :value="h.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" :icon="Search" :disabled="!selectedHeaderId" @click="reloadTreeAndFilter">
            再取得
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 製品選択後：左=工程順 右=材料・部品（BOM版選択後） -->
    <div v-if="selectedProductCd" class="pbe-main-split">
      <el-card class="pbe-main-split__left pbe-panel pbe-route-panel" shadow="never">
        <template #header>
          <div class="pbe-panel-cap">
            <span class="pbe-panel-cap__dot" />
            <span>工程順</span>
            <span v-if="mainRouteCd" class="pbe-panel-cap__meta">{{ mainRouteCd }}</span>
          </div>
        </template>
        <div v-loading="loadingMainRoute" class="pbe-route-panel__body">
          <el-empty
            v-if="!loadingMainRoute && !mainRouteSteps.length"
            description="工程ルート未設定"
            :image-size="48"
          />
          <el-table
            v-else-if="mainRouteSteps.length"
            :data="mainRouteSteps"
            size="small"
            stripe
            class="pbe-table pbe-route-table"
            style="width: 100%"
          >
            <el-table-column prop="step_no" label="順" width="44" align="center" />
            <el-table-column prop="process_cd" label="工程CD" min-width="92" show-overflow-tooltip />
            <el-table-column label="工程名" min-width="108" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.process_name || '—' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <div class="pbe-main-split__right">
        <div v-if="selectedHeaderId" class="pbe-mats-parts-stack">
          <el-card class="panel-card pbe-panel" shadow="never">
            <template #header>
              <div class="pbe-panel-cap">
                <span class="pbe-panel-cap__dot" />
                <span>材料</span>
                <span class="pbe-panel-cap__meta">{{ materialRows.length }} 件</span>
              </div>
            </template>
            <el-table
              :data="materialRows"
              v-loading="loadingTree"
              class="pbe-table pbe-table--center-cells"
              size="small"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="line_no" label="行番" width="70" align="center" header-align="center" />
              <el-table-column
                prop="component_material_cd"
                label="材料CD"
                width="120"
                align="center"
                header-align="center"
              />
              <el-table-column label="材料名" min-width="140" align="center" header-align="center" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ masterMaterialName(row.component_material_cd) }}
                </template>
              </el-table-column>
              <el-table-column prop="qty_per" label="所要量" width="90" align="center" header-align="center" />
              <el-table-column prop="uom" label="単位" width="70" align="center" header-align="center" />
              <el-table-column label="工程名" min-width="120" align="center" header-align="center" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ mainRouteProcessName(row.consume_process_cd) }}
                </template>
              </el-table-column>
              <el-table-column prop="remarks" label="備考" min-width="100" align="center" header-align="center" show-overflow-tooltip />
            </el-table>
          </el-card>
          <el-card class="panel-card pbe-panel" shadow="never">
            <template #header>
              <div class="pbe-panel-cap">
                <span class="pbe-panel-cap__dot pbe-panel-cap__dot--violet" />
                <span>部品</span>
                <span class="pbe-panel-cap__meta">{{ partRows.length }} 件</span>
              </div>
            </template>
            <el-table
              :data="partRows"
              v-loading="loadingTree"
              class="pbe-table pbe-table--center-cells"
              size="small"
              stripe
              style="width: 100%"
            >
              <el-table-column prop="line_no" label="行番" width="70" align="center" header-align="center" />
              <el-table-column label="子品目種別" width="100" align="center" header-align="center">
                <template #default="{ row }">
                  <el-tag :type="componentTypeTagMap[row.component_type] || 'info'" size="small">
                    {{ componentTypeLabel[row.component_type] || row.component_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="component_product_cd"
                label="部品CD"
                width="120"
                align="center"
                header-align="center"
              />
              <el-table-column label="製品名" min-width="140" align="center" header-align="center" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ masterProductName(row.component_product_cd) }}
                </template>
              </el-table-column>
              <el-table-column prop="qty_per" label="所要量" width="90" align="center" header-align="center" />
              <el-table-column prop="uom" label="単位" width="70" align="center" header-align="center" />
              <el-table-column label="工程名" min-width="120" align="center" header-align="center" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ mainRouteProcessName(row.consume_process_cd) }}
                </template>
              </el-table-column>
              <el-table-column prop="remarks" label="備考" min-width="100" align="center" header-align="center" show-overflow-tooltip />
            </el-table>
          </el-card>
        </div>
        <el-card v-else class="panel-card pbe-panel pbe-panel--placeholder" shadow="never">
          <template #header>
            <div class="pbe-panel-cap">
              <span class="pbe-panel-cap__dot pbe-panel-cap__dot--slate" />
              <span>材料・部品</span>
            </div>
          </template>
          <div class="pbe-panel-placeholder-body">
            <el-empty
              :description="productHeaders.length ? '上の BOM版を選択してください' : 'BOMヘッダがありません。新規BOMを作成してください'"
              :image-size="64"
            />
          </div>
        </el-card>
      </div>
    </div>

    <!-- BOM構成ツリー（選択中の版） -->
    <el-card v-if="selectedHeader" class="tree-card pbe-tree-card" shadow="never">
      <template #header>
        <div class="tree-card-header pbe-tree-cap">
          <div class="pbe-tree-cap__left">
            <span class="pbe-panel-cap__dot" />
            <span>BOMツリー · {{ selectedHeader.parent_product_cd }} / Rev.{{ selectedHeader.revision }}</span>
          </div>
          <div class="pbe-tree-cap__actions">
            <el-radio-group v-model="bomTreeViewMode" size="small" class="pbe-tree-view-toggle pbe-tree-view-toggle--wide">
              <el-radio-button value="table">
                <span class="pbe-tree-view-toggle__inner"><el-icon><List /></el-icon>表</span>
              </el-radio-button>
              <el-radio-button value="blocks">
                <span class="pbe-tree-view-toggle__inner"><el-icon><Grid /></el-icon>多階層</span>
              </el-radio-button>
              <el-radio-button value="direct">
                <span class="pbe-tree-view-toggle__inner"><el-icon><Bottom /></el-icon>直下</span>
              </el-radio-button>
              <el-radio-button value="flat">
                <span class="pbe-tree-view-toggle__inner"><el-icon><Histogram /></el-icon>展開集計</span>
              </el-radio-button>
            </el-radio-group>
            <el-button type="primary" link size="small" @click="openEditDialog(selectedHeader)">編集</el-button>
          </div>
        </div>
      </template>
      <div v-if="!selectedHeader" class="empty-tree">
        <el-empty description="BOM版を選択してください" />
      </div>
      <div v-else class="pbe-tree-card-body">
        <div class="pbe-tree-filter-bar">
          <el-input
            v-model="treeFilterText"
            placeholder="CD・名称・工程・備考で絞り込み"
            clearable
            size="small"
            class="pbe-tree-filter-input"
          />
          <p v-if="bomTreeViewMode !== 'table'" class="pbe-tree-viz-hint">{{ bomVizModeHint }}</p>
        </div>
        <div v-loading="loadingTree" class="pbe-tree-content">
          <el-table
            v-show="bomTreeViewMode === 'table'"
            :data="bomTreeFiltered"
            class="pbe-table pbe-tree-table"
            row-key="id"
            :tree-props="{ children: 'children' }"
            default-expand-all
            size="small"
            style="width: 100%"
          >
        <el-table-column prop="line_no" label="行番" width="70" />
        <el-table-column prop="component_type" label="子品目種別" width="110">
          <template #default="{ row }">
            <el-tag :type="componentTypeTagMap[row.component_type] || 'info'" size="small">
              {{ componentTypeLabel[row.component_type] || row.component_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="子品目CD" width="160">
          <template #default="{ row }">
            {{ row.component_product_cd || row.component_material_cd || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="マスタ名称" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{
              row.component_material_cd
                ? masterMaterialName(row.component_material_cd)
                : row.component_product_cd
                  ? masterProductName(row.component_product_cd)
                  : '—'
            }}
          </template>
        </el-table-column>
        <el-table-column prop="qty_per" label="所要量" width="100" align="right" />
        <el-table-column prop="uom" label="単位" width="70" />
        <el-table-column prop="scrap_rate" label="ロス率(%)" width="100" align="right" />
        <el-table-column prop="consume_process_cd" label="投入工程" width="120" />
        <el-table-column prop="remarks" label="備考" min-width="120" />
          </el-table>

          <!-- ブロック型：多階層（図の Multi-level に近い表現） -->
          <div v-show="bomTreeViewMode === 'blocks'" class="bom-viz-wrap">
            <div class="bom-viz-legend">
              <span class="bom-viz-legend__item bom-viz-legend__item--assy">子を持つ行（構成の階層）</span>
              <span class="bom-viz-legend__item bom-viz-legend__item--leaf">末端（材料・単体部品）</span>
            </div>
            <el-empty v-if="!bomBlockRows.length" description="構成行がありません" :image-size="64" />
            <div v-else class="bom-viz-block-list">
              <div
                v-for="{ line, depth } in bomBlockRows"
                :key="line.id"
                class="bom-viz-row"
                :style="{ '--bom-depth': depth }"
              >
                <div
                  class="bom-viz-card"
                  :class="bomLineHasChildren(line) ? 'bom-viz-card--assy' : 'bom-viz-card--leaf'"
                >
                  <div class="bom-viz-card__main">
                    <span class="bom-viz-card__cd">{{ line.component_product_cd || line.component_material_cd || '—' }}</span>
                    <span class="bom-viz-card__name">{{ bomLineDisplayName(line) }}</span>
                    <el-tag :type="componentTypeTagMap[line.component_type] || 'info'" size="small" effect="plain" class="bom-viz-type-tag">
                      {{ componentTypeLabel[line.component_type] || line.component_type }}
                    </el-tag>
                  </div>
                  <div class="bom-viz-card__qty">
                    <span class="bom-viz-qty-mark">×</span>
                    <span class="bom-viz-qty-val">{{ line.qty_per }}</span>
                    <span class="bom-viz-qty-uom">{{ line.uom }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ブロック型：直下（親製品の直接子のみ） -->
          <div v-show="bomTreeViewMode === 'direct'" class="bom-viz-wrap">
            <el-empty v-if="!bomDirectBlockRows.length" description="構成行がありません" :image-size="64" />
            <div v-else class="bom-viz-block-list">
              <div v-for="{ line } in bomDirectBlockRows" :key="line.id" class="bom-viz-row bom-viz-row--root">
                <div
                  class="bom-viz-card"
                  :class="bomLineHasChildren(line) ? 'bom-viz-card--assy' : 'bom-viz-card--leaf'"
                >
                  <div class="bom-viz-card__main">
                    <span class="bom-viz-card__cd">{{ line.component_product_cd || line.component_material_cd || '—' }}</span>
                    <span class="bom-viz-card__name">{{ bomLineDisplayName(line) }}</span>
                    <el-tag :type="componentTypeTagMap[line.component_type] || 'info'" size="small" effect="plain" class="bom-viz-type-tag">
                      {{ componentTypeLabel[line.component_type] || line.component_type }}
                    </el-tag>
                  </div>
                  <div class="bom-viz-card__qty">
                    <span class="bom-viz-qty-mark">×</span>
                    <span class="bom-viz-qty-val">{{ line.qty_per }}</span>
                    <span class="bom-viz-qty-uom">{{ line.uom }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 展開集計：階層をたどり末端の所要量を積み上げ（図の Flattened に相当） -->
          <div v-show="bomTreeViewMode === 'flat'" class="bom-viz-wrap bom-viz-wrap--flat">
            <p class="bom-flat-note">1 単位の親に対する末端部材・部品の合計所要量（階層の数量を乗算して集計）</p>
            <el-empty v-if="!bomFlattenRollupList.length" description="末端行がありません" :image-size="64" />
            <div v-else class="bom-flat-list">
              <div
                v-for="row in bomFlattenRollupList"
                :key="row.key"
                class="bom-viz-card bom-viz-card--leaf bom-viz-card--rollup"
                :class="row.kind === 'material' ? 'bom-viz-card--mat' : 'bom-viz-card--part'"
              >
                <div class="bom-viz-card__main">
                  <span class="bom-viz-card__cd">{{ row.cd }}</span>
                  <span class="bom-viz-card__name">{{ row.name }}</span>
                  <el-tag size="small" effect="plain" :type="row.kind === 'material' ? 'warning' : 'primary'">
                    {{ row.kind === 'material' ? '材料' : '部品' }}
                  </el-tag>
                </div>
                <div class="bom-viz-card__qty">
                  <span class="bom-viz-qty-mark">計</span>
                  <span class="bom-viz-qty-val">{{ formatRollupQty(row.totalQty) }}</span>
                  <span class="bom-viz-qty-uom">{{ row.uom }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 全BOMヘッダ一覧 -->
    <el-card class="search-card pbe-search-card" shadow="never">
      <template #header>
        <div class="pbe-panel-cap">
          <span class="pbe-panel-cap__dot pbe-panel-cap__dot--slate" />
          <span>全BOMヘッダ</span>
        </div>
      </template>
      <el-form :inline="true" class="search-form pbe-search-form">
        <el-form-item label="親製品">
          <el-input v-model="searchProductCd" placeholder="CDで検索" clearable class="pbe-search-cd" size="small" @keyup.enter="loadHeaders" />
        </el-form-item>
        <el-form-item label="状態">
          <el-select v-model="searchStatus" clearable placeholder="全て" class="pbe-search-status" size="small">
            <el-option label="有効" value="active" />
            <el-option label="履歴" value="historical" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" :icon="Search" @click="loadHeaders">検索</el-button>
          <el-button size="small" @click="resetSearch">クリア</el-button>
        </el-form-item>
      </el-form>
      <el-table
        :data="headers"
        v-loading="loadingHeaders"
        class="pbe-table pbe-headers-table"
        highlight-current-row
        size="small"
        stripe
        @current-change="onGlobalHeaderSelect"
        style="width: 100%"
      >
        <el-table-column prop="parent_product_cd" label="親製品CD" width="140" />
        <el-table-column prop="parent_product_name" label="製品名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="bom_type" label="種別" width="100">
          <template #default="{ row }">
            <el-tag :type="row.bom_type === 'production' ? 'success' : 'info'" size="small">
              {{ bomTypeLabel(row.bom_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="revision" label="版番" width="70" />
        <el-table-column prop="status" label="状態" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="effective_from" label="有効開始" width="110" />
        <el-table-column prop="effective_to" label="有効終了" width="110" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)">編集</el-button>
            <el-popconfirm title="削除しますか？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">削除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap pbe-pagination">
        <el-pagination
          small
          layout="total, prev, pager, next"
          :total="headerTotal"
          :page-size="pageSize"
          v-model:current-page="currentPage"
          @current-change="loadHeaders"
        />
      </div>
    </el-card>

    <!-- 新規/編集：工程順ガイド付き -->
    <el-dialog
      v-model="dialogVisible"
      class="bom-form-dialog"
      width="min(1180px, 96vw)"
      destroy-on-close
      align-center
      :show-close="true"
      append-to-body
      @closed="onBomDialogClosed"
    >
      <template #header>
        <div class="bom-dlg-header">
          <div class="bom-dlg-header-mark" aria-hidden="true" />
          <div class="bom-dlg-header-text">
            <div class="bom-dlg-title">{{ isEditing ? 'BOM編集' : '新規BOM作成' }}</div>
            <div class="bom-dlg-sub">保存時に行番・投入工程を自動付与</div>
          </div>
        </div>
      </template>
      <!-- ダイアログ内は Element Plus を日本語ロケールに固定（アプリ言語が他言語でも日付・表の文言が日本語になる） -->
      <el-config-provider :locale="bomDialogElLocale">
      <div v-loading="dialogRouteLoading" class="bom-dialog-inner">
        <div class="bom-dialog-hero">
          <div class="bom-dialog-hero-top">
            <span class="bom-chip">BOMヘッダ</span>
            <div class="hero-meta hero-meta--inline">
              <el-tag v-if="dialogRouteCd" type="primary" effect="light" size="small" class="hero-tag-soft">ルート {{ dialogRouteCd }}</el-tag>
              <el-tag v-else-if="formData.parent_product_cd" type="warning" effect="light" size="small" class="hero-tag-soft">ルート未設定</el-tag>
              <span v-if="dialogRouteSteps.length" class="hero-step-pill">{{ dialogRouteSteps.length }} 工程</span>
            </div>
          </div>
          <el-form :model="formData" label-width="76px" size="small" class="bom-hero-form">
            <el-row :gutter="8" class="bom-hero-row">
              <el-col :xs="24" :lg="10">
                <el-form-item label="親製品CD" required>
                  <el-select
                    v-if="!isEditing"
                    v-model="formData.parent_product_cd"
                    filterable
                    clearable
                    placeholder="製品マスタから選択"
                    style="width: 100%"
                    :loading="loadingProducts"
                    @change="onDialogParentProductChange"
                  >
                    <el-option
                      v-for="p in productOptions"
                      :key="p.product_cd"
                      :label="`${p.product_cd} — ${p.product_name || ''}`"
                      :value="p.product_cd"
                    />
                  </el-select>
                  <el-input v-else v-model="formData.parent_product_cd" disabled />
                </el-form-item>
              </el-col>
              <el-col :xs="8" :sm="6" :lg="4">
                <el-form-item label="種別">
                  <el-select v-model="formData.bom_type" style="width: 100%" placeholder="選択してください">
                    <el-option label="製造" value="production" />
                    <el-option label="設計" value="engineering" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="8" :sm="6" :lg="4">
                <el-form-item label="版番">
                  <el-input v-model="formData.revision" placeholder="例: 1" />
                </el-form-item>
              </el-col>
              <el-col :xs="8" :sm="6" :lg="6">
                <el-form-item label="基準数量">
                  <el-input-number v-model="formData.base_quantity" :min="1" :step="1" :precision="0" style="width: 100%" controls-position="right" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="8" class="bom-hero-row">
              <el-col :xs="12" :sm="6" :lg="4">
                <el-form-item label="単位">
                  <el-input v-model="formData.uom" placeholder="例: 個" />
                </el-form-item>
              </el-col>
              <el-col :xs="12" :sm="9" :lg="10">
                <el-form-item label="有効開始">
                  <el-date-picker v-model="formData.effective_from" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="日付を選択" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="9" :lg="10">
                <el-form-item label="有効終了">
                  <el-date-picker v-model="formData.effective_to" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="日付を選択" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="備考" class="bom-fi-remarks">
              <el-input
                v-model="formData.remarks"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 3 }"
                placeholder="ヘッダ備考"
              />
            </el-form-item>
          </el-form>
        </div>

        <div class="bom-process-head">
          <span class="section-label">工程順明細</span>
          <span class="section-hint">各工程に材料行・部品行を追加</span>
        </div>

        <el-alert
          v-if="formData.parent_product_cd && !dialogRouteLoading && !dialogRouteSteps.length"
          type="warning"
          :closable="false"
          show-icon
          class="bom-route-alert"
        >
          <template #title>
            <span class="bom-alert-title">工程ルート未設定。下の「その他・未分類」で入力するか、製品別ルートを登録してください。</span>
          </template>
        </el-alert>

        <el-scrollbar v-if="dialogRouteSteps.length" max-height="min(52vh, 440px)" class="bom-steps-scroll">
          <div class="bom-steps-rail">
            <div v-for="step in dialogRouteSteps" :key="step.step_no" class="bom-step-block">
              <div class="bom-step-index" :title="`ステップ ${step.step_no}`">{{ step.step_no }}</div>
              <div class="bom-step-body">
                <div class="process-step-card process-step-card--modern">
                  <div class="step-card-head step-card-head--row">
                    <span class="step-name">{{ step.process_name || step.process_cd }}</span>
                    <el-tag size="small" effect="plain" type="info" class="step-cd-tag step-cd-tag--dense">{{ step.process_cd }}</el-tag>
                  </div>

                  <div class="step-lines-toolbar">
                    <el-button type="primary" size="small" :icon="Plus" @click="addStepLine(step, 'material')">材料行</el-button>
                    <el-button size="small" :icon="Plus" @click="addStepLine(step, 'part')">部品行</el-button>
                  </div>
                  <p
                    v-if="isCuttingProcessStep(step) && dialogParentMaterialCd"
                    class="bom-cut-material-hint"
                  >
                    製品マスタ材料 <code>{{ dialogParentMaterialCd }}</code> を「材料行」追加時に既定（一覧先頭）。
                  </p>
                  <p
                    v-else-if="isCuttingProcessStep(step) && !dialogParentMaterialCd"
                    class="bom-cut-material-hint bom-cut-material-hint--warn"
                  >
                    親製品に材料CDなし。製品マスタの <code>material_cd</code> で切断工程の材料を自動提案。
                  </p>

                  <el-table
                  :data="processLinesByStep[step.step_no] || []"
                  border
                  stripe
                  size="small"
                  class="step-lines-table bom-dlg-table"
                  empty-text="行を追加"
                >
                  <el-table-column label="種別" width="132" align="center">
                    <template #default="{ row }">
                      <el-select v-if="lineUiKind(row) === 'material'" v-model="row.component_type" style="width: 100%">
                        <el-option label="原材料" value="material" />
                        <el-option label="外購品" value="purchased" />
                        <el-option label="ファントム" value="phantom" />
                      </el-select>
                      <el-select v-else v-model="row.component_type" style="width: 100%">
                        <el-option label="子階品" value="subassy" />
                        <el-option label="外購品" value="purchased" />
                        <el-option label="ファントム" value="phantom" />
                      </el-select>
                    </template>
                  </el-table-column>
                  <el-table-column label="材料" min-width="240">
                    <template #default="{ row }">
                      <template v-if="lineUiKind(row) === 'material'">
                        <el-select
                          v-model="row.component_material_cd"
                          filterable
                          clearable
                          placeholder="材料マスタから選択"
                          style="width: 100%"
                          @change="onLineMaterialPicked(row)"
                        >
                          <el-option
                            v-for="m in sortedMaterialOptionsForStep(step)"
                            :key="m.material_cd"
                            :label="materialOptionLabel(m, step)"
                            :value="m.material_cd"
                          />
                        </el-select>
                      </template>
                      <span v-else class="bom-line-cell-muted">—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="部品" min-width="240">
                    <template #default="{ row }">
                      <template v-if="lineUiKind(row) === 'part'">
                        <el-select
                          v-model="row.component_product_cd"
                          filterable
                          clearable
                          placeholder="部品マスタから選択"
                          style="width: 100%"
                          @change="onLineProductPicked(row)"
                        >
                          <el-option
                            v-for="p in dialogPartSelectOptions"
                            :key="p.part_cd"
                            :label="`${p.part_cd} ${p.part_name}`"
                            :value="p.part_cd"
                          />
                        </el-select>
                      </template>
                      <span v-else class="bom-line-cell-muted">—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="所要量" width="100" align="right">
                    <template #default="{ row }">
                      <el-input-number
                        v-model="row.qty_per"
                        :min="0"
                        :precision="0"
                        :step="1"
                        controls-position="right"
                        style="width: 100%"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column label="単位" width="88" align="center">
                    <template #default="{ row }">
                      <el-input v-model="row.uom" />
                    </template>
                  </el-table-column>
                  <el-table-column label="備考" min-width="160">
                    <template #default="{ row }">
                      <el-input v-model="row.remarks" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="72" align="center" fixed="right">
                    <template #default="{ $index }">
                      <el-button link type="danger" @click="removeStepLine(step.step_no, $index)">削除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>

        <div class="orphan-card orphan-card--modern">
          <div class="orphan-card-head">
            <span class="orphan-title">その他・未分類</span>
            <span class="orphan-hint">ルート外・工程未紐づけ</span>
          </div>
          <div class="step-lines-toolbar">
            <el-button type="primary" size="small" :icon="Plus" @click="addOrphanLine('material')">材料行</el-button>
            <el-button size="small" :icon="Plus" @click="addOrphanLine('part')">部品行</el-button>
          </div>
          <el-table :data="orphanLines" border stripe size="small" empty-text="なし" class="bom-dlg-table" max-height="220">
            <el-table-column label="種別" width="132" align="center">
              <template #default="{ row }">
                <el-select v-if="lineUiKind(row) === 'material'" v-model="row.component_type" style="width: 100%">
                  <el-option label="原材料" value="material" />
                  <el-option label="外購品" value="purchased" />
                  <el-option label="ファントム" value="phantom" />
                </el-select>
                <el-select v-else v-model="row.component_type" style="width: 100%">
                  <el-option label="子階品" value="subassy" />
                  <el-option label="外購品" value="purchased" />
                  <el-option label="ファントム" value="phantom" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="材料" min-width="220">
              <template #default="{ row }">
                <template v-if="lineUiKind(row) === 'material'">
                  <el-select
                    v-model="row.component_material_cd"
                    filterable
                    clearable
                    placeholder="材料マスタから選択"
                    style="width: 100%"
                    @change="onLineMaterialPicked(row)"
                  >
                    <el-option
                      v-for="m in materialSelectList"
                      :key="m.material_cd"
                      :label="`${m.material_cd} ${m.material_name}`"
                      :value="m.material_cd"
                    />
                  </el-select>
                </template>
                <span v-else class="bom-line-cell-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="部品" min-width="220">
              <template #default="{ row }">
                <template v-if="lineUiKind(row) === 'part'">
                  <el-select
                    v-model="row.component_product_cd"
                    filterable
                    clearable
                    placeholder="部品マスタから選択"
                    style="width: 100%"
                    @change="onLineProductPicked(row)"
                  >
                    <el-option
                      v-for="p in dialogPartSelectOptions"
                      :key="p.part_cd"
                      :label="`${p.part_cd} ${p.part_name}`"
                      :value="p.part_cd"
                    />
                  </el-select>
                </template>
                <span v-else class="bom-line-cell-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="所要量" width="100" align="right">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.qty_per"
                  :min="0"
                  :precision="0"
                  :step="1"
                  controls-position="right"
                  style="width: 100%"
                />
              </template>
            </el-table-column>
            <el-table-column label="単位" width="88" align="center">
              <template #default="{ row }">
                <el-input v-model="row.uom" />
              </template>
            </el-table-column>
            <el-table-column label="投入工程CD" width="128">
              <template #default="{ row }">
                <el-input v-model="row.consume_process_cd" placeholder="工程CD" />
              </template>
            </el-table-column>
            <el-table-column label="備考" min-width="140">
              <template #default="{ row }">
                <el-input v-model="row.remarks" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="72" align="center" fixed="right">
              <template #default="{ $index }">
                <el-button link type="danger" @click="removeOrphanLine($index)">削除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      </el-config-provider>
      <template #footer>
        <div class="bom-dlg-footer">
          <el-button size="small" @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import jaElLocale from 'element-plus/dist/locale/ja.js'
import { Plus, Search, Document, List, Grid, Bottom, Histogram } from '@element-plus/icons-vue'
import {
  getBomHeaders,
  getBomTree,
  createBomHeader,
  updateBomHeader,
  deleteBomHeader,
  type BomHeader,
  type BomLine,
  type BomLinePayload,
} from '@/api/master/productBom'
import { getProductList } from '@/api/master/productMaster'
import { getMaterialList } from '@/api/master/materialMaster'
import { getPartList, type PartMasterRow } from '@/api/master/partMaster'
import request from '@/shared/api/request'
import type { Product } from '@/types/master'
import type { Material } from '@/types/master'

/** 製品別工程ルートAPIのステップ行 */
interface ProductRouteStepLite {
  step_no: number
  process_cd: string
  process_name?: string
  route_cd?: string
}

/** BOM 新規/編集ダイアログ専用：Element Plus 日本語 */
const bomDialogElLocale = jaElLocale

const componentTypeLabel: Record<string, string> = {
  material: '原材料',
  purchased: '外購品',
  subassy: '子階品',
  phantom: 'Phantom',
}
const componentTypeTagMap: Record<string, 'warning' | 'success' | 'primary' | 'info' | 'danger'> = {
  material: 'warning',
  purchased: 'success',
  subassy: 'primary',
  phantom: 'info',
}

function bomTypeLabel(t: string) {
  if (t === 'production') return '製造'
  if (t === 'engineering') return '設計'
  return t
}
function statusLabel(s: string) {
  if (s === 'active') return '有効'
  if (s === 'historical') return '履歴'
  return s
}

const loadingProducts = ref(false)
const productOptions = ref<Product[]>([])
const selectedProductCd = ref<string>('')

const productHeaders = ref<BomHeader[]>([])
const loadingProductHeaders = ref(false)
const selectedHeaderId = ref<number | undefined>(undefined)
const selectedHeader = computed(() => productHeaders.value.find((h) => h.id === selectedHeaderId.value) ?? null)

const materialNameByCd = ref<Record<string, string>>({})
/** 材料マスタの単位（所要量の既定に使用） */
const materialUnitByCd = ref<Record<string, string>>({})
const productNameByCd = ref<Record<string, string>>({})
/** 部品マスタ（BOM 子行の component_product_cd に部品 CD を格納） */
const partNameByCd = ref<Record<string, string>>({})
const partUnitByCd = ref<Record<string, string>>({})
/** BOMダイアログ用プルダウン */
const materialSelectList = ref<{ material_cd: string; material_name: string }[]>([])
const partSelectList = ref<{ part_cd: string; part_name: string }[]>([])

const dialogRouteLoading = ref(false)
const dialogRouteSteps = ref<ProductRouteStepLite[]>([])
const dialogRouteCd = ref('')
/** ダイアログ内のみ：材料行 / 部品行を分離表示するための印（API には送らない） */
type DialogLineRow = BomLinePayload & { __uiKind?: 'material' | 'part' }

const processLinesByStep = ref<Record<number, DialogLineRow[]>>({})
const orphanLines = ref<DialogLineRow[]>([])
const treeData = ref<BomLine[]>([])
const flatLinesForProcess = ref<BomLine[]>([])
const loadingTree = ref(false)

/** メイン画面左カラム：選択製品の工程ルート */
const mainRouteSteps = ref<ProductRouteStepLite[]>([])
const mainRouteCd = ref('')
const loadingMainRoute = ref(false)

async function loadMainProductRoute(productCd: string) {
  mainRouteSteps.value = []
  mainRouteCd.value = ''
  if (!productCd?.trim()) return
  loadingMainRoute.value = true
  try {
    const productRes = await request.get(`/api/master/product/process/routes/${encodeURIComponent(productCd)}`)
    const product = (productRes as { data?: { route_cd?: string } })?.data ?? productRes
    const routeCd = (product as { route_cd?: string })?.route_cd || ''
    mainRouteCd.value = routeCd
    if (!routeCd) return
    const stepsRes = await request.get(
      `/api/master/product/process/routes/${encodeURIComponent(productCd)}/${encodeURIComponent(routeCd)}`
    )
    const raw = (stepsRes as { data?: unknown })?.data ?? stepsRes
    const steps = Array.isArray(raw) ? (raw as ProductRouteStepLite[]) : []
    mainRouteSteps.value = [...steps].sort((a, b) => (a.step_no ?? 0) - (b.step_no ?? 0))
  } catch {
    mainRouteSteps.value = []
    mainRouteCd.value = ''
  } finally {
    loadingMainRoute.value = false
  }
}

const materialRows = computed(() =>
  flatLinesForProcess.value.filter((r) => r.component_material_cd && String(r.component_material_cd).trim() !== '')
)
const partRows = computed(() =>
  flatLinesForProcess.value.filter((r) => r.component_product_cd && String(r.component_product_cd).trim() !== '')
)

function masterMaterialName(cd: string | null | undefined) {
  if (!cd) return '—'
  return materialNameByCd.value[cd] ?? cd
}
function masterProductName(cd: string | null | undefined) {
  if (!cd) return '—'
  return partNameByCd.value[cd] || productNameByCd.value[cd] || cd
}

/** 左カラム工程順（選択製品）に基づき投入工程CD→工程名 */
function mainRouteProcessName(processCd: string | null | undefined) {
  const c = String(processCd || '').trim()
  if (!c) return '—'
  const step = mainRouteSteps.value.find((s) => String(s.process_cd || '').trim() === c)
  const name = step?.process_name?.trim()
  return name || c
}

/** ダイアログ内：有効部品＋現在行にあってマスタに無い CD（旧製品参照の編集用） */
const dialogPartSelectOptions = computed(() => {
  const list = partSelectList.value
  const seen = new Set(list.map((p) => p.part_cd))
  const extras: { part_cd: string; part_name: string }[] = []
  const addCd = (cd: string | null | undefined) => {
    const c = String(cd || '').trim()
    if (!c || seen.has(c)) return
    seen.add(c)
    extras.push({ part_cd: c, part_name: masterProductName(c) })
  }
  for (const rows of Object.values(processLinesByStep.value)) {
    for (const row of rows) {
      if (lineUiKind(row) === 'part') addCd(row.component_product_cd)
    }
  }
  for (const row of orphanLines.value) {
    if (lineUiKind(row) === 'part') addCd(row.component_product_cd)
  }
  extras.sort((a, b) => a.part_cd.localeCompare(b.part_cd))
  return [...extras, ...list]
})

/** メイン画面：表 / ブロック多階層 / 直下 / 展開集計 */
const bomTreeViewMode = ref<'table' | 'blocks' | 'direct' | 'flat'>('table')
const treeFilterText = ref('')

const bomVizModeHint = computed(() => {
  switch (bomTreeViewMode.value) {
    case 'blocks':
      return '階層をインデント付きブロックで表示（子を持つ行は緑系、末端は青系）。'
    case 'direct':
      return '親製品の直下の構成行のみ表示（下位階層は折りたたんだイメージ）。'
    case 'flat':
      return 'ツリーを末端まで展開し、同一 CD の所要量を合算します。'
    default:
      return ''
  }
})

function filterBomLineTree(nodes: BomLine[], query: string): BomLine[] {
  const q = query.trim().toLowerCase()
  if (!q) return nodes
  const out: BomLine[] = []
  for (const n of nodes) {
    const cd = String(n.component_product_cd || n.component_material_cd || '').toLowerCase()
    const nm = (
      n.component_material_cd
        ? masterMaterialName(n.component_material_cd)
        : n.component_product_cd
          ? masterProductName(n.component_product_cd)
          : ''
    ).toLowerCase()
    const proc = String(n.consume_process_cd || '').toLowerCase()
    const rem = String(n.remarks || '').toLowerCase()
    const selfMatch =
      cd.includes(q) ||
      nm.includes(q) ||
      proc.includes(q) ||
      rem.includes(q) ||
      String(n.line_no).includes(q) ||
      String(n.qty_per).includes(q)
    const kids = filterBomLineTree(n.children || [], q)
    if (selfMatch || kids.length) {
      out.push({ ...n, children: kids.length ? kids : [] })
    }
  }
  return out
}

const bomTreeFiltered = computed(() => filterBomLineTree(treeData.value, treeFilterText.value))

function bomLineHasChildren(line: BomLine): boolean {
  return !!(line.children && line.children.length > 0)
}

function bomLineDisplayName(line: BomLine): string {
  if (line.component_material_cd) return masterMaterialName(line.component_material_cd)
  if (line.component_product_cd) return masterProductName(line.component_product_cd)
  return '—'
}

function flattenBomWithDepth(nodes: BomLine[], depth = 0): { line: BomLine; depth: number }[] {
  const rows: { line: BomLine; depth: number }[] = []
  for (const it of nodes) {
    rows.push({ line: it, depth })
    const ch = it.children?.length ? it.children : []
    if (ch.length) rows.push(...flattenBomWithDepth(ch, depth + 1))
  }
  return rows
}

const bomBlockRows = computed(() => flattenBomWithDepth(bomTreeFiltered.value))

const bomDirectBlockRows = computed(() => bomTreeFiltered.value.map((line) => ({ line })))

interface BomRollupRow {
  key: string
  cd: string
  name: string
  kind: 'material' | 'part'
  totalQty: number
  uom: string
}

function rollupBomExploded(nodes: BomLine[], parentFactor: number, map: Map<string, BomRollupRow>) {
  for (const it of nodes) {
    const q = Number(it.qty_per)
    const qtyPer = Number.isFinite(q) && q >= 0 ? q : 0
    const factor = parentFactor * qtyPer
    const ch = it.children?.length ? it.children : []
    if (ch.length) {
      rollupBomExploded(ch, factor, map)
      continue
    }
    const mc = it.component_material_cd && String(it.component_material_cd).trim()
    const pc = it.component_product_cd && String(it.component_product_cd).trim()
    if (!mc && !pc) continue
    const key = mc ? `m:${mc}` : `p:${pc}`
    const kind: 'material' | 'part' = mc ? 'material' : 'part'
    const cd = mc || pc || ''
    const name = mc ? masterMaterialName(mc) : masterProductName(pc)
    const uom = it.uom || '—'
    const prev = map.get(key)
    if (prev) {
      prev.totalQty += factor
    } else {
      map.set(key, { key, cd, name, kind, totalQty: factor, uom })
    }
  }
}

const bomFlattenRollupList = computed(() => {
  const m = new Map<string, BomRollupRow>()
  rollupBomExploded(bomTreeFiltered.value, 1, m)
  return Array.from(m.values()).sort((a, b) => {
    const t = a.kind.localeCompare(b.kind)
    if (t !== 0) return t
    return a.cd.localeCompare(b.cd)
  })
})

function formatRollupQty(n: number): string {
  if (!Number.isFinite(n)) return '0'
  if (Math.abs(n - Math.round(n)) < 1e-9) return String(Math.round(n))
  return n.toLocaleString('ja-JP', { maximumFractionDigits: 6 })
}

function flattenBomTree(nodes: BomLine[]): BomLine[] {
  const out: BomLine[] = []
  function walk(items: BomLine[]) {
    for (const it of items) {
      out.push(it)
      if (it.children?.length) walk(it.children)
    }
  }
  walk(nodes)
  return out
}

/** 材料/部品パネル用：選択中のBOM版の全行（階層をフラット化） */
function syncFlatLinesFromTree() {
  if (!treeData.value.length) {
    flatLinesForProcess.value = []
    return
  }
  flatLinesForProcess.value = flattenBomTree(treeData.value)
}

async function loadMasterLookups() {
  try {
    const [matRes, prodRes] = await Promise.all([
      getMaterialList({ page: 1, pageSize: 10000 }),
      getProductList({ page: 1, pageSize: 10000 }),
    ])
    const mats = matRes?.data?.list ?? matRes?.list ?? []
    const prods = prodRes?.data?.list ?? prodRes?.list ?? []
    const mm: Record<string, string> = {}
    const mu: Record<string, string> = {}
    for (const m of mats as Material[]) {
      if (m.material_cd) {
        mm[m.material_cd] = m.material_name || m.material_cd
        if (m.unit) mu[m.material_cd] = m.unit
      }
    }
    materialUnitByCd.value = mu
    const pm: Record<string, string> = {}
    for (const p of prods as Product[]) {
      if (p.product_cd) pm[p.product_cd] = p.product_name || p.product_cd
    }
    materialNameByCd.value = mm
    productNameByCd.value = pm
    materialSelectList.value = Object.entries(mm)
      .map(([material_cd, material_name]) => ({ material_cd, material_name }))
      .sort((a, b) => a.material_cd.localeCompare(b.material_cd))

    try {
      const pageSize = 10000
      let page = 1
      const partRows: PartMasterRow[] = []
      let partTotal = 0
      let firstPart = true
      while (firstPart || partRows.length < partTotal) {
        firstPart = false
        const pr = await getPartList({ page, pageSize, status: 1 })
        const plist = pr?.data?.list ?? []
        partTotal = pr?.data?.total ?? 0
        partRows.push(...plist)
        if (plist.length < pageSize) break
        page += 1
      }
      const pnm: Record<string, string> = {}
      const pum: Record<string, string> = {}
      for (const pt of partRows) {
        if (pt.part_cd) {
          pnm[pt.part_cd] = pt.part_name || pt.part_cd
          if (pt.uom) pum[pt.part_cd] = pt.uom
        }
      }
      partNameByCd.value = pnm
      partUnitByCd.value = pum
      partSelectList.value = Object.entries(pnm)
        .map(([part_cd, part_name]) => ({ part_cd, part_name }))
        .sort((a, b) => a.part_cd.localeCompare(b.part_cd))
    } catch {
      partNameByCd.value = {}
      partUnitByCd.value = {}
      partSelectList.value = []
      ElMessage.warning('部品マスタの取得に失敗しました。部品プルダウンが空になる場合があります')
    }
  } catch {
    ElMessage.warning('マスタの取得に失敗しました。名称はコードのみ表示される場合があります')
    materialUnitByCd.value = {}
    partNameByCd.value = {}
    partUnitByCd.value = {}
    partSelectList.value = []
  }
}

async function loadProductOptions() {
  loadingProducts.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = list as Product[]
  } catch {
    ElMessage.error('製品一覧の取得に失敗しました')
    productOptions.value = []
  } finally {
    loadingProducts.value = false
  }
}

async function loadHeadersForProduct() {
  if (!selectedProductCd.value) {
    productHeaders.value = []
    selectedHeaderId.value = undefined
    mainRouteSteps.value = []
    mainRouteCd.value = ''
    return
  }
  loadingProductHeaders.value = true
  try {
    const res = await getBomHeaders({
      parent_product_cd: selectedProductCd.value,
      page: 1,
      limit: 200,
    })
    const d = (res as any)?.data ?? res
    const list = d?.list ?? []
    productHeaders.value = list
    const active = list.find((h: BomHeader) => h.status === 'active')
    selectedHeaderId.value = active?.id ?? list[0]?.id
    await reloadTreeAndFilter()
  } catch {
    ElMessage.error('当該製品のBOMヘッダ取得に失敗しました')
    productHeaders.value = []
  } finally {
    loadingProductHeaders.value = false
  }
  await loadMainProductRoute(selectedProductCd.value)
}

async function onProductChange() {
  flatLinesForProcess.value = []
  treeData.value = []
  await loadHeadersForProduct()
}

async function onHeaderIdChange() {
  flatLinesForProcess.value = []
  await reloadTreeAndFilter()
}

async function reloadTreeAndFilter() {
  const id = selectedHeaderId.value
  if (!id) {
    treeData.value = []
    flatLinesForProcess.value = []
    return
  }
  loadingTree.value = true
  try {
    const res = await getBomTree(id)
    const d = (res as any)?.data ?? res
    treeData.value = d?.tree ?? []
    syncFlatLinesFromTree()
  } catch {
    ElMessage.error('BOMツリーの取得に失敗しました')
    treeData.value = []
    flatLinesForProcess.value = []
  } finally {
    loadingTree.value = false
  }
}

// ——— 全BOMヘッダ一覧 ———
const searchProductCd = ref('')
const searchStatus = ref('')
const currentPage = ref(1)
const pageSize = 20
const headerTotal = ref(0)
const headers = ref<BomHeader[]>([])
const loadingHeaders = ref(false)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const defaultLine = (): DialogLineRow => ({
  line_no: 10,
  component_type: 'material',
  component_product_cd: null,
  component_material_cd: null,
  qty_per: 1,
  uom: '個',
  scrap_rate: 0,
  consume_process_cd: null,
  consume_step_no: null,
  remarks: null,
})

function inferUiKind(ln: BomLinePayload): 'material' | 'part' {
  const p = ln.component_product_cd && String(ln.component_product_cd).trim()
  if (p) return 'part'
  return 'material'
}

function lineUiKind(row: BomLinePayload): 'material' | 'part' {
  const k = (row as DialogLineRow).__uiKind
  if (k === 'material' || k === 'part') return k
  return inferUiKind(row)
}

function sanitizedPayloadLine(ln: DialogLineRow, kind: 'material' | 'part'): BomLinePayload {
  const { __uiKind: _u, ...rest } = ln
  const out: BomLinePayload = { ...rest }
  if (kind === 'material') {
    out.component_product_cd = null
  } else {
    out.component_material_cd = null
  }
  return out
}

/** 新規BOM作成ダイアログの既定有効期間（YYYY-MM-DD） */
const DEFAULT_NEW_BOM_EFFECTIVE_FROM = '2026-04-01'
const DEFAULT_NEW_BOM_EFFECTIVE_TO = '2032-03-31'

const formData = reactive({
  parent_product_cd: '',
  bom_type: 'production',
  revision: '1',
  status: 'active',
  effective_from: null as string | null,
  effective_to: null as string | null,
  base_quantity: 1,
  uom: '個',
  remarks: null as string | null,
  lines: [] as BomLinePayload[],
})

/** BOMダイアログで選択中の親製品（製品マスタの material_cd 参照用） */
const dialogParentProduct = computed(() =>
  productOptions.value.find((p) => p.product_cd === formData.parent_product_cd) ?? null
)
const dialogParentMaterialCd = computed(() => dialogParentProduct.value?.material_cd?.trim() || '')

/** 切断系工程：製品マスタの材料を既定の投入材料とする */
function isCuttingProcessStep(step: ProductRouteStepLite): boolean {
  const name = (step.process_name || '').trim()
  const cd = (step.process_cd || '').trim().toUpperCase()
  if (name.includes('切断') || name.includes('カット')) return true
  if (cd.includes('CUT')) return true
  return false
}

/** 切断工程では製品の material_cd を先頭に（材料マスタ未登録時は合成1件を先頭に） */
function sortedMaterialOptionsForStep(step: ProductRouteStepLite): { material_cd: string; material_name: string }[] {
  const list = materialSelectList.value
  const pm = dialogParentMaterialCd.value
  if (!pm || !isCuttingProcessStep(step)) return list
  const idx = list.findIndex((x) => x.material_cd === pm)
  if (idx >= 0) {
    const next = [...list]
    const [one] = next.splice(idx, 1)
    return [one, ...next]
  }
  return [{ material_cd: pm, material_name: masterMaterialName(pm) }, ...list]
}

function materialOptionLabel(m: { material_cd: string; material_name: string }, step: ProductRouteStepLite) {
  const base = `${m.material_cd} ${m.material_name}`
  if (dialogParentMaterialCd.value && m.material_cd === dialogParentMaterialCd.value && isCuttingProcessStep(step)) {
    return `${base}（製品マスタ）`
  }
  return base
}

function resetBomDialogProcessState() {
  processLinesByStep.value = {}
  orphanLines.value = []
  dialogRouteSteps.value = []
  dialogRouteCd.value = ''
}

function onBomDialogClosed() {
  resetBomDialogProcessState()
}

async function loadDialogRouteAndPrices(productCd: string) {
  if (!productCd?.trim()) {
    dialogRouteSteps.value = []
    dialogRouteCd.value = ''
    return
  }
  dialogRouteLoading.value = true
  try {
    const productRes = await request.get(`/api/master/product/process/routes/${encodeURIComponent(productCd)}`)
    const product = (productRes as { data?: { route_cd?: string } })?.data ?? productRes
    const routeCd = (product as { route_cd?: string })?.route_cd || ''
    dialogRouteCd.value = routeCd
    if (!routeCd) {
      dialogRouteSteps.value = []
      return
    }
    const stepsRes = await request.get(
      `/api/master/product/process/routes/${encodeURIComponent(productCd)}/${encodeURIComponent(routeCd)}`
    )
    const raw = (stepsRes as { data?: unknown })?.data ?? stepsRes
    const steps = Array.isArray(raw) ? (raw as ProductRouteStepLite[]) : []
    dialogRouteSteps.value = [...steps].sort((a, b) => (a.step_no ?? 0) - (b.step_no ?? 0))
  } catch {
    ElMessage.error('製品工程順の取得に失敗しました')
    dialogRouteSteps.value = []
    dialogRouteCd.value = ''
  } finally {
    dialogRouteLoading.value = false
  }
}

function initEmptyStepBuckets() {
  const rec: Record<number, DialogLineRow[]> = {}
  for (const s of dialogRouteSteps.value) {
    rec[s.step_no] = []
  }
  processLinesByStep.value = rec
  orphanLines.value = []
}

function distributeLinesToSteps(lines: BomLinePayload[]) {
  const steps = dialogRouteSteps.value
  if (!steps.length) {
    processLinesByStep.value = {}
    orphanLines.value = lines.map((l) => ({ ...l, __uiKind: inferUiKind(l) }))
    return
  }
  const stepNoSet = new Set(steps.map((s) => s.step_no))
  const rec: Record<number, DialogLineRow[]> = {}
  for (const s of steps) {
    rec[s.step_no] = []
  }
  const orphan: DialogLineRow[] = []
  for (const ln of lines) {
    const row: DialogLineRow = { ...ln, __uiKind: inferUiKind(ln) }
    let placed = false
    const sn = ln.consume_step_no
    if (sn != null && stepNoSet.has(Number(sn))) {
      rec[Number(sn)]!.push(row)
      placed = true
    } else {
      const match = steps.find((s) => s.process_cd === ln.consume_process_cd)
      if (match) {
        rec[match.step_no]!.push(row)
        placed = true
      }
    }
    if (!placed) orphan.push(row)
  }
  processLinesByStep.value = rec
  orphanLines.value = orphan
}

function mergeProcessLinesIntoFormData() {
  const ordered = [...dialogRouteSteps.value].sort((a, b) => a.step_no - b.step_no)
  let lineNo = 10
  const merged: BomLinePayload[] = []
  for (const s of ordered) {
    const block = processLinesByStep.value[s.step_no] || []
    for (const ln of block) {
      const kind = lineUiKind(ln)
      const base = sanitizedPayloadLine(ln, kind)
      merged.push({
        ...base,
        consume_process_cd: s.process_cd,
        consume_step_no: s.step_no,
        line_no: lineNo,
      })
      lineNo += 10
    }
  }
  for (const ln of orphanLines.value) {
    const kind = lineUiKind(ln)
    merged.push({ ...sanitizedPayloadLine(ln, kind), line_no: lineNo })
    lineNo += 10
  }
  formData.lines = merged
}

function lineTemplateForStep(step: ProductRouteStepLite, kind: 'material' | 'part'): DialogLineRow {
  const base = defaultLine()
  base.consume_process_cd = step.process_cd
  base.consume_step_no = step.step_no
  base.line_no = 10
  base.__uiKind = kind
  if (kind === 'material') {
    base.component_type = 'material'
    base.component_product_cd = null
    base.component_material_cd = null
    if (isCuttingProcessStep(step)) {
      const mc = dialogParentMaterialCd.value
      if (mc) {
        base.component_material_cd = mc
        const u = materialUnitByCd.value[mc]
        if (u) base.uom = u
      }
    }
  } else {
    base.component_type = 'subassy'
    base.component_material_cd = null
    base.component_product_cd = null
  }
  return base
}

function addStepLine(step: ProductRouteStepLite, kind: 'material' | 'part') {
  if (!processLinesByStep.value[step.step_no]) {
    processLinesByStep.value[step.step_no] = []
  }
  processLinesByStep.value[step.step_no].push(lineTemplateForStep(step, kind))
}

function removeStepLine(stepNo: number, idx: number) {
  processLinesByStep.value[stepNo]?.splice(idx, 1)
}

function onLineMaterialPicked(row: DialogLineRow) {
  if (lineUiKind(row) !== 'material') return
  if (row.component_material_cd) {
    row.component_product_cd = null
    if (row.component_type !== 'material' && row.component_type !== 'phantom' && row.component_type !== 'purchased') {
      row.component_type = 'material'
    }
  }
}

function onLineProductPicked(row: DialogLineRow) {
  if (lineUiKind(row) !== 'part') return
  if (row.component_product_cd) {
    row.component_material_cd = null
    if (row.component_type === 'material') {
      row.component_type = 'subassy'
    }
    const cd = String(row.component_product_cd).trim()
    const u = partUnitByCd.value[cd]
    if (u) row.uom = u
  }
}

function addOrphanLine(kind: 'material' | 'part') {
  const line = defaultLine()
  line.consume_step_no = null
  line.__uiKind = kind
  if (kind === 'material') {
    line.component_type = 'material'
    line.component_product_cd = null
    line.component_material_cd = null
  } else {
    line.component_type = 'subassy'
    line.component_material_cd = null
    line.component_product_cd = null
  }
  orphanLines.value.push(line)
}

function removeOrphanLine(idx: number) {
  orphanLines.value.splice(idx, 1)
}

async function onDialogParentProductChange(cd: string) {
  formData.parent_product_cd = cd || ''
  resetBomDialogProcessState()
  if (!cd) return
  await loadDialogRouteAndPrices(cd)
  initEmptyStepBuckets()
  if (!dialogRouteSteps.value.length) {
    ElMessage.warning('この製品に工程ルートが未設定です。「その他・未分類」で明細を入力できます。')
  }
}

async function loadHeaders() {
  loadingHeaders.value = true
  try {
    const params: Record<string, unknown> = { page: currentPage.value, limit: pageSize }
    if (searchProductCd.value) params.keyword = searchProductCd.value
    if (searchStatus.value) params.status = searchStatus.value
    const res = await getBomHeaders(params)
    const d = (res as any)?.data ?? res
    headers.value = d?.list ?? []
    headerTotal.value = d?.total ?? 0
  } catch {
    ElMessage.error('BOMヘッダ一覧の取得に失敗しました')
  } finally {
    loadingHeaders.value = false
  }
}

/** 下部一覧の行選択で上部の製品・BOM版を同期 */
function onGlobalHeaderSelect(row: BomHeader | null) {
  if (!row) return
  selectedProductCd.value = row.parent_product_cd
  loadHeadersForProduct().then(() => {
    selectedHeaderId.value = row.id
    reloadTreeAndFilter()
  })
}

function resetSearch() {
  searchProductCd.value = ''
  searchStatus.value = ''
  currentPage.value = 1
  loadHeaders()
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  resetBomDialogProcessState()
  Object.assign(formData, {
    parent_product_cd: selectedProductCd.value || '',
    bom_type: 'production',
    revision: '1',
    status: 'active',
    effective_from: DEFAULT_NEW_BOM_EFFECTIVE_FROM,
    effective_to: DEFAULT_NEW_BOM_EFFECTIVE_TO,
    base_quantity: 1,
    uom: '個',
    remarks: null,
    lines: [],
  })
  dialogVisible.value = true
  const cd = formData.parent_product_cd
  if (cd) {
    loadDialogRouteAndPrices(cd).then(() => {
      initEmptyStepBuckets()
      if (!dialogRouteSteps.value.length) {
        ElMessage.warning('この製品に工程ルートが未設定です。「その他・未分類」で明細を入力できます。')
      }
    })
  }
}

async function openEditDialog(row: BomHeader) {
  isEditing.value = true
  editingId.value = row.id
  resetBomDialogProcessState()
  Object.assign(formData, {
    parent_product_cd: row.parent_product_cd,
    bom_type: row.bom_type,
    revision: row.revision,
    status: row.status,
    effective_from: row.effective_from,
    effective_to: row.effective_to,
    base_quantity: row.base_quantity,
    uom: row.uom,
    remarks: row.remarks,
    lines: [],
  })
  dialogVisible.value = true
  await loadDialogRouteAndPrices(row.parent_product_cd)
  let lines: BomLinePayload[] = row.lines?.map((l) => ({ ...l })) ?? []
  if (lines.length === 0) {
    try {
      const res = await getBomTree(row.id)
      const d = (res as any)?.data ?? res
      const flat: BomLinePayload[] = []
      function flatten(items: BomLine[]) {
        for (const it of items) {
          flat.push({ ...it })
          if (it.children?.length) flatten(it.children)
        }
      }
      flatten(d?.tree ?? [])
      lines = flat
    } catch {
      lines = []
    }
  }
  distributeLinesToSteps(lines)
}

async function handleSave() {
  if (!formData.parent_product_cd) {
    ElMessage.warning('親製品CDを入力してください')
    return
  }
  mergeProcessLinesIntoFormData()
  saving.value = true
  try {
    if (isEditing.value && editingId.value) {
      await updateBomHeader(editingId.value, { ...formData })
      ElMessage.success('更新しました')
    } else {
      await createBomHeader({ ...formData })
      ElMessage.success('作成しました')
    }
    dialogVisible.value = false
    loadHeaders()
    if (selectedProductCd.value === formData.parent_product_cd) {
      await loadHeadersForProduct()
    }
    if (selectedHeaderId.value) await reloadTreeAndFilter()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteBomHeader(id)
    ElMessage.success('削除しました')
    if (selectedHeaderId.value === id) {
      selectedHeaderId.value = undefined
      treeData.value = []
      flatLinesForProcess.value = []
    }
    loadHeaders()
    if (selectedProductCd.value) await loadHeadersForProduct()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

onMounted(() => {
  loadHeaders()
  loadProductOptions()
  loadMasterLookups()
})
</script>

<style scoped>
.bom-editor {
  min-height: 100vh;
  padding: 10px 12px 12px;
  background:
    radial-gradient(ellipse 95% 65% at 0% -12%, rgba(99, 102, 241, 0.1), transparent 46%),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

/* ページヒーロー */
.pbe-hero {
  position: relative;
  border-radius: 12px;
  margin-bottom: 10px;
  overflow: hidden;
  box-shadow: 0 8px 24px -8px rgba(15, 23, 42, 0.22);
}

.pbe-hero__accent {
  height: 3px;
  background: linear-gradient(90deg, #0ea5e9, #6366f1, #8b5cf6);
}

.pbe-hero__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 45%, #1d4ed8 100%);
}

.pbe-hero__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.pbe-hero__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.pbe-hero__title {
  margin: 0 0 2px;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #fff;
  line-height: 1.2;
}

.pbe-hero__sub {
  margin: 0;
  font-size: 11px;
  line-height: 1.35;
  color: rgba(226, 232, 240, 0.88);
}

/* フィルタツールバー */
.pbe-toolbar-card.filter-card {
  margin-bottom: 10px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
}

.pbe-toolbar-card :deep(.el-card__body) {
  padding: 8px 12px;
}

.pbe-filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
}

.pbe-filter-form.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.pbe-filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.pbe-filt-product {
  width: 220px;
}

.pbe-filt-header {
  width: 260px;
}

.pbe-main-split {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 10px;
  min-height: 0;
}

.pbe-main-split__left {
  flex: 0 0 clamp(260px, 28vw, 320px);
  width: clamp(260px, 28vw, 320px);
  min-width: 240px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pbe-main-split__right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pbe-mats-parts-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pbe-route-panel {
  display: flex;
  flex-direction: column;
  min-height: 120px;
  max-height: min(62vh, 520px);
}

.pbe-route-panel :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.pbe-route-panel__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.pbe-route-table {
  min-height: 0;
}

.pbe-panel--placeholder :deep(.el-card__body) {
  padding: 0;
}

.pbe-panel-placeholder-body {
  padding: 12px 8px 16px;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-card {
  width: 100%;
}

@media (max-width: 960px) {
  .pbe-main-split {
    flex-direction: column;
  }

  .pbe-main-split__left {
    flex: none;
    width: 100%;
    max-height: min(40vh, 320px);
  }
}

.pbe-panel {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.pbe-panel :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc, #f8fafc);
}

.pbe-panel-cap {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.pbe-panel-cap__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  flex-shrink: 0;
}

.pbe-panel-cap__dot--violet {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
}

.pbe-panel-cap__dot--slate {
  background: linear-gradient(135deg, #64748b, #94a3b8);
}

.pbe-panel-cap__meta {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.pbe-table {
  font-size: 12px;
}

.pbe-table :deep(.el-table th.el-table__cell) {
  font-size: 11px;
  font-weight: 700;
  padding: 6px 0;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  color: #334155;
}

.pbe-table :deep(.el-table td.el-table__cell) {
  padding: 5px 0;
}

.pbe-table :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: rgba(99, 102, 241, 0.04) !important;
}

.pbe-table--center-cells :deep(.el-table .cell) {
  text-align: center;
}

.pbe-panel :deep(.el-card__body) {
  padding: 0;
}

.hint-card {
  margin-bottom: 10px;
}

.pbe-hint {
  border-radius: 12px;
  border: 1px dashed rgba(148, 163, 184, 0.45);
}

.pbe-hint :deep(.el-card__body) {
  padding: 16px 12px;
}

.pbe-hint :deep(.el-empty__description) {
  margin-top: 8px;
  font-size: 13px;
}

.tree-card {
  margin-bottom: 10px;
}

.pbe-tree-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
  overflow: hidden;
}

.pbe-tree-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc, #f8fafc);
}

.pbe-tree-cap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
}

.pbe-tree-cap__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.pbe-tree-cap__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.pbe-tree-view-toggle :deep(.el-radio-button__inner) {
  padding: 4px 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.pbe-tree-view-toggle__inner {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.pbe-tree-card-body {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pbe-tree-filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 8px 12px;
  border-bottom: 1px solid #f1f5f9;
  background: #fafbfc;
}

.pbe-tree-filter-input {
  max-width: 320px;
}

.pbe-tree-viz-hint {
  margin: 0;
  flex: 1 1 200px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

.pbe-tree-view-toggle--wide :deep(.el-radio-button__inner) {
  padding: 4px 8px;
}

.pbe-tree-content {
  min-height: 120px;
  max-height: 560px;
  overflow: auto;
}

/* —— BOM ビジュアル：図のようなブロック＋所要量 —— */
.bom-viz-wrap {
  padding: 10px 12px 14px;
  background: #f8fafc;
}

.bom-viz-wrap--flat {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.bom-viz-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 10px;
  font-size: 11px;
  color: #475569;
}

.bom-viz-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.bom-viz-legend__item::before {
  content: '';
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

.bom-viz-legend__item--assy::before {
  background: linear-gradient(135deg, #bbf7d0, #86efac);
}

.bom-viz-legend__item--leaf::before {
  background: linear-gradient(135deg, #bae6fd, #7dd3fc);
}

.bom-viz-block-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bom-viz-row {
  position: relative;
  padding-left: calc(var(--bom-depth, 0) * 22px);
  border-left: 2px solid #cbd5e1;
  margin-left: 6px;
}

.bom-viz-row--root {
  border-left-color: transparent;
  padding-left: 0;
  margin-left: 0;
}

.bom-viz-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 44px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  background: #fff;
  transition: box-shadow 0.15s ease;
}

.bom-viz-card:hover {
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.07);
}

.bom-viz-card--assy {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 55%, #ecfdf5 100%);
  border-color: rgba(22, 163, 74, 0.28);
}

.bom-viz-card--leaf {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0f9ff 100%);
  border-color: rgba(14, 165, 233, 0.3);
}

.bom-viz-card__main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  min-width: 0;
  flex: 1;
}

.bom-viz-card__cd {
  font-weight: 700;
  font-size: 12px;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.bom-viz-card__name {
  font-size: 13px;
  color: #334155;
  word-break: break-word;
}

.bom-viz-type-tag {
  flex-shrink: 0;
}

.bom-viz-card__qty {
  display: flex;
  align-items: baseline;
  gap: 2px 6px;
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.bom-viz-qty-mark {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.bom-viz-qty-val {
  font-size: 15px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}

.bom-viz-qty-uom {
  font-size: 11px;
  color: #64748b;
}

.bom-flat-note {
  margin: 0 0 10px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.45;
}

.bom-flat-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bom-viz-card--rollup.bom-viz-card--mat {
  border-left: 3px solid #f59e0b;
}

.bom-viz-card--rollup.bom-viz-card--part {
  border-left: 3px solid #6366f1;
}

.pbe-tree-card :deep(.el-card__body) {
  padding: 0;
}

.search-card {
  margin-bottom: 10px;
}

.pbe-search-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
}

.pbe-search-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc, #f8fafc);
}

.pbe-search-card :deep(.el-card__body) {
  padding: 8px 12px 10px;
}

.pbe-search-form.search-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.pbe-search-cd {
  width: 160px;
}

.pbe-search-status {
  width: 100px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 0;
}

.pbe-pagination {
  padding: 6px 10px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}

.empty-tree {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100px;
}

.tree-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

/* —— BOM ダイアログ：適度な余白・標準コンポーネントサイズ —— */
.bom-line-cell-muted {
  display: inline-block;
  padding: 2px 0;
  font-size: 12px;
  color: #94a3b8;
  user-select: none;
}

.bom-form-dialog {
  --bom-accent: #2563eb;
  --bom-accent2: #4f46e5;
  --bom-line: #e2e8f0;
  --bom-surface: #f8fafc;
}
.bom-form-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 20px 44px -12px rgba(15, 23, 42, 0.22),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}
.bom-form-dialog :deep(.el-dialog__header) {
  padding: 6px 10px 5px;
  margin: 0;
  border-bottom: 1px solid var(--bom-line);
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}
.bom-form-dialog :deep(.el-dialog__body) {
  padding: 6px 10px 6px;
  background: var(--bom-surface);
}
.bom-form-dialog :deep(.el-dialog__footer) {
  padding: 6px 10px 7px;
  border-top: 1px solid var(--bom-line);
  background: #fff;
}
.bom-dlg-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bom-dlg-header-mark {
  width: 3px;
  height: 28px;
  border-radius: 3px;
  background: linear-gradient(180deg, var(--bom-accent) 0%, var(--bom-accent2) 100%);
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.28);
}
.bom-dlg-title {
  font-size: 0.9375rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.bom-dlg-sub {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 0;
  line-height: 1.3;
  max-width: 56em;
}
.bom-dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}
.bom-dialog-inner {
  min-height: 48px;
}
.bom-dialog-hero {
  background: #fff;
  border: 1px solid var(--bom-line);
  border-radius: 8px;
  padding: 6px 8px 5px;
  margin-bottom: 6px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.bom-dialog-hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f1f5f9;
}
.bom-chip {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #64748b;
}
.hero-meta--inline {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.hero-tag-soft {
  font-weight: 600;
}
.hero-tag-soft :deep(.el-tag__content) {
  line-height: 1.2;
}
.hero-step-pill {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 999px;
}
.bom-hero-form :deep(.el-form-item) {
  margin-bottom: 4px;
}
.bom-hero-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
  font-size: 12px;
  padding-right: 6px;
}
.bom-fi-remarks {
  margin-bottom: 0 !important;
}
.bom-hero-row {
  margin-bottom: 0 !important;
}
.bom-process-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 4px;
  flex-wrap: wrap;
}
.section-label {
  font-weight: 700;
  font-size: 12px;
  color: #0f172a;
  flex-shrink: 0;
}
.section-hint {
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.35;
  flex: 1;
  min-width: 0;
}
.bom-route-alert {
  margin-bottom: 4px;
}
.bom-form-dialog :deep(.bom-route-alert.el-alert) {
  padding: 4px 8px;
}
.bom-route-alert :deep(.el-alert__title) {
  font-size: 12px;
  line-height: 1.4;
}
.bom-route-alert :deep(.el-alert__icon) {
  font-size: 14px;
  width: 14px;
}
.bom-alert-title {
  font-size: 12px;
}
.bom-steps-scroll {
  margin-bottom: 4px;
  padding-right: 0;
}
.bom-steps-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}
.bom-steps-rail {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bom-step-block {
  display: flex;
  gap: 0;
  align-items: stretch;
}
.bom-step-index {
  flex: 0 0 26px;
  width: 26px;
  align-self: stretch;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 6px;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(180deg, var(--bom-accent) 0%, #1d4ed8 100%);
  border-radius: 6px 0 0 6px;
  line-height: 1;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}
.bom-step-body {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--bom-line);
  border-left: none;
  border-radius: 0 8px 8px 0;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
.process-step-card--modern {
  padding: 6px 8px 6px 6px;
}
.step-card-head--row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.step-name {
  font-weight: 700;
  font-size: 13px;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.step-cd-tag {
  font-weight: 600;
}
.bom-form-dialog :deep(.step-cd-tag--dense.el-tag) {
  height: 22px;
  padding: 0 6px;
  font-size: 11px;
}
.step-lines-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
}

.step-lines-toolbar :deep(.el-button) {
  padding: 4px 10px;
}
.step-lines-table {
  width: 100%;
}
.bom-dlg-table :deep(.el-table__header th) {
  padding: 3px 0;
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  background: #f1f5f9 !important;
}
.bom-dlg-table :deep(.el-table__body td.el-table__cell) {
  padding: 2px 0;
  vertical-align: middle;
}
.bom-dlg-table :deep(.el-table .cell) {
  padding: 0 6px;
  line-height: 1.35;
}
.bom-dlg-table :deep(.el-input__wrapper),
.bom-dlg-table :deep(.el-select .el-input__wrapper) {
  min-height: 26px;
  padding: 0 8px;
}
.bom-dlg-table :deep(.el-input-number .el-input__wrapper) {
  padding-left: 6px;
  padding-right: 6px;
}
.orphan-card--modern {
  border: 1px solid var(--bom-line);
  border-radius: 8px;
  background: #fff;
  padding: 6px 8px 6px;
  margin-top: 2px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
.orphan-card-head {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px dashed #e2e8f0;
}
.orphan-title {
  font-weight: 700;
  font-size: 12px;
  color: #0f172a;
}
.orphan-hint {
  font-size: 11px;
  color: #64748b;
}

.bom-cut-material-hint {
  margin: 0 0 4px;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.35;
  color: #475569;
  background: #eff6ff;
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 6px;
}

.bom-cut-material-hint code {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.85);
}

.bom-cut-material-hint--warn {
  background: #fffbeb;
  border-color: rgba(245, 158, 11, 0.35);
  color: #92400e;
}

@media (max-width: 768px) {
  .pbe-filt-product,
  .pbe-filt-header,
  .pbe-search-cd {
    width: 100%;
  }
}
</style>
