<template>
  <div class="supply-page pb-std">
    <div class="page-header pb-hero pb-hero--page">
      <div class="spm-hero-fx pb-bubbles" aria-hidden="true" />
      <div class="spm-hero-brand">
        <div class="spm-hero-icon">
          <el-icon :size="20"><Box /></el-icon>
        </div>
        <div class="spm-hero-copy">
          <h1 class="pb-hero-title">補給品管理</h1>
          <p class="pb-hero-desc">現在庫、保管場所、品質状態を台帳で管理します。</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button class="spm-head-btn spm-head-btn--manual" @click="openLocations">
          <el-icon><Location /></el-icon>
          保管場所管理
        </el-button>
        <el-button v-if="canCreate" class="spm-head-btn spm-head-btn--transfer" @click="openTransfer">
          <el-icon><Switch /></el-icon>
          量産品から振替
        </el-button>
        <el-button v-if="canCreate" class="spm-head-btn spm-head-btn--manual" @click="openManual">
          <el-icon><EditPen /></el-icon>
          手動登録
        </el-button>
      </div>
    </div>

    <div class="stat-row">
      <div class="stat-card">
        <span class="stat-card__icon"><el-icon><Box /></el-icon></span>
        <div class="stat-card__body">
          <span>件数</span>
          <strong>{{ summary.count }}</strong>
        </div>
      </div>
      <div class="stat-card stat-card--sky">
        <span class="stat-card__icon"><el-icon><Goods /></el-icon></span>
        <div class="stat-card__body">
          <span>現在庫合計</span>
          <strong>{{ formatNum(summary.on_hand_total) }}</strong>
        </div>
      </div>
      <div class="stat-card stat-card--indigo" title="品質状態が「良好」以外の補給品">
        <span class="stat-card__icon"><el-icon><Medal /></el-icon></span>
        <div class="stat-card__body">
          <span>品質異常</span>
          <strong>{{ summary.quality_issue_count }}</strong>
        </div>
      </div>
      <div class="stat-card stat-card--rose" :class="{ 'stat-card--alert': summary.alert_count > 0 }">
        <span class="stat-card__icon"><el-icon><WarningFilled /></el-icon></span>
        <div class="stat-card__body">
          <span>警告</span>
          <strong>{{ summary.alert_count }}</strong>
        </div>
      </div>
      <div
        class="stat-card stat-card--amber"
        :class="{ 'stat-card--stagnant': summary.stagnant_count > 0 }"
        :title="`最終出庫（未出庫は登録日）から ${stagnantDays} 日以上在庫が残っている補給品`"
      >
        <span class="stat-card__icon"><el-icon><Clock /></el-icon></span>
        <div class="stat-card__body">
          <span>長期滞留</span>
          <strong>{{ summary.stagnant_count }}</strong>
        </div>
      </div>
    </div>

    <div class="toolbar">
      <span class="toolbar__label">対象月</span>
      <el-date-picker
        v-model="monthValue"
        type="month"
        value-format="YYYY-MM"
        placeholder="対象月"
        :clearable="false"
        class="month-picker"
        @change="loadList"
      />
      <el-input
        v-model="keyword"
        clearable
        placeholder="製品CD・製品名・品番・保管場所"
        class="keyword"
        @keyup.enter="loadList"
        @clear="loadList"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="locationFilter"
        clearable
        filterable
        placeholder="保管場所"
        class="filter-select"
        @change="loadList"
      >
        <el-option v-for="item in locations" :key="item.id" :label="item.name" :value="item.name" />
      </el-select>
      <el-select
        v-model="destinationFilter"
        clearable
        filterable
        placeholder="納入先"
        class="filter-select"
        @change="loadList"
      >
        <el-option
          v-for="item in destinationOptions"
          :key="item.cd"
          :label="`${item.cd} ${item.name}`"
          :value="item.cd"
        />
      </el-select>
      <el-checkbox v-model="alertOnly" class="alert-check" @change="loadList">警告のみ</el-checkbox>
      <el-checkbox v-model="stagnantOnly" class="alert-check stagnant-check" @change="loadList">
        滞留のみ
      </el-checkbox>
      <el-button class="search-btn" @click="loadList">
        <el-icon><Search /></el-icon>
        検索
      </el-button>
      <div class="toolbar__right">
        <el-button class="tool-btn" :disabled="!rows.length" :loading="exporting" @click="exportExcel">
          <el-icon><Download /></el-icon>
          Excel出力
        </el-button>
        <el-button class="tool-btn" :disabled="!rows.length" @click="printStocktakeSheet">
          <el-icon><Printer /></el-icon>
          棚卸表印刷
        </el-button>
      </div>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="rows"
        border
        stripe
        size="small"
        class="data-table"
        :row-class-name="rowClass"
        @row-click="openDetail"
      >
        <el-table-column prop="product_cd" label="製品CD" width="80" fixed>
          <template #default="{ row }">
            <span class="cd-text">{{ row.product_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="製品名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="part_number" label="品番" min-width="110" show-overflow-tooltip />
        <el-table-column prop="storage_location" label="保管場所" min-width="120" show-overflow-tooltip />
        <el-table-column prop="shelf_no" label="棚番" width="90" show-overflow-tooltip />
        <el-table-column prop="on_hand_qty" label="現在庫" width="90" align="right">
          <template #default="{ row }">
            <span class="num-strong">{{ formatNum(row.on_hand_qty) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全在庫" width="90" align="right">
          <template #default="{ row }">{{ formatNum(row.safety_stock) }}</template>
        </el-table-column>
        <el-table-column prop="quality_status" label="品質状態" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" round :type="qualityTagType(row.quality_status)">{{ row.quality_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avg_monthly_demand" width="96" align="right">
          <template #header>
            <el-tooltip :content="`対象月を含む直近 ${demandMonths} ヶ月の受注確定本数の月平均`">
              <span>月平均出荷</span>
            </el-tooltip>
          </template>
          <template #default="{ row }">{{ formatDecimal(row.avg_monthly_demand) }}</template>
        </el-table-column>
        <el-table-column prop="idle_months" width="110" align="right" sortable>
          <template #header>
            <el-tooltip content="最終出庫日（未出庫は登録日）から今日までの経過月数">
              <span>滞留月数</span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <span v-if="row.idle_months == null" class="muted">—</span>
            <span v-else :class="{ 'num-warn': row.idle_months >= 12 }" :title="`${row.idle_days} 日`">
              {{ row.idle_months }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="last_out_date" label="最終出庫日" width="106" sortable>
          <template #default="{ row }">
            <span v-if="row.last_out_date">{{ row.last_out_date }}</span>
            <span v-else class="muted">未出庫</span>
          </template>
        </el-table-column>
        <el-table-column label="登録元" width="80">
          <template #default="{ row }">
            <el-tag size="small" round :type="row.source === 'transfer' ? 'warning' : 'info'">
              {{ row.source === 'transfer' ? '振替' : '手動' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="備考" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row as SupplyPartStock)">
              {{ canEdit ? '編集' : '詳細' }}
            </el-button>
            <el-button v-if="canDelete" link type="danger" @click.stop="removeStock(row as SupplyPartStock)">
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="transferVisible"
      width="min(920px, 96vw)"
      top="6vh"
      class="spm-dialog spm-dialog--transfer pb-std"
      :show-close="false"
      destroy-on-close
    >
      <template #header>
        <div class="spm-dialog-hero spm-dialog-hero--amber pb-hero">
          <div class="pb-bubbles" aria-hidden="true" />
          <div class="spm-dialog-icon"><el-icon><Switch /></el-icon></div>
          <div class="spm-dialog-copy">
            <h3>量産品から振替</h3>
            <p>製品種別を補給品にし、最新倉庫在庫をこの台帳へ移して、在庫取引記録に同数の保留（補給品へ振替）を登録します</p>
          </div>
          <el-icon class="spm-close" @click="transferVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div class="spm-dialog-body spm-dialog-body--compact">
        <el-form label-position="top" class="spm-form spm-form--compact">
          <section class="form-section form-section--amber">
            <header class="form-section__title"><span class="form-section__dot" />対象製品</header>
            <div class="transfer-target-row">
              <div>
                <el-form-item label="製品" required>
                  <el-select
                    v-model="transferForm.product_cd"
                    filterable
                    clearable
                    placeholder="製品を選択（製品CD・製品名・品番で絞り込み）"
                    :filter-method="filterProducts"
                    :loading="productSearching"
                    style="width: 100%"
                    @visible-change="onProductDropdown"
                    @change="onTransferProduct"
                  >
                    <el-option
                      v-for="item in productOptions"
                      :key="item.product_cd"
                      :label="`${item.product_cd} ${item.product_name}`"
                      :value="item.product_cd"
                    >
                      <span>{{ item.product_cd }} {{ item.product_name }}</span>
                      <span v-if="item.part_number" class="option-sub">{{ item.part_number }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-alert
                  v-if="preview"
                  :title="previewTitle"
                  :type="preview.already_registered ? 'error' : preview.warning ? 'warning' : 'success'"
                  :closable="false"
                  show-icon
                  class="preview-alert"
                />
              </div>
              <el-form-item label="最新倉庫在庫（振替対象）">
                <el-table
                  v-if="preview?.lines?.length"
                  :data="preview.lines"
                  size="small"
                  border
                  max-height="150"
                  class="preview-table"
                >
                  <el-table-column prop="route_cd" label="ルート" min-width="100">
                    <template #default="{ row }">{{ row.route_cd || 'ルートなし' }}</template>
                  </el-table-column>
                  <el-table-column prop="date" label="基準日" width="110" />
                  <el-table-column prop="warehouse_inventory" label="倉庫在庫" width="90" align="right" />
                </el-table>
                <p v-else class="transfer-preview-empty">製品を選ぶと、ここに表示します</p>
              </el-form-item>
            </div>
          </section>
          <section class="form-section form-section--sky">
            <header class="form-section__title"><span class="form-section__dot" />保管・品質</header>
            <div class="form-grid form-grid--4">
              <el-form-item label="保管場所" required>
                <SupplyLocationSelect
                  v-model="transferForm.storage_location"
                  :locations="locations"
                  :can-manage="canManageLocations"
                  @manage="openLocations"
                />
              </el-form-item>
              <el-form-item label="棚番">
                <el-input v-model="transferForm.shelf_no" maxlength="50" />
              </el-form-item>
              <el-form-item label="安全在庫">
                <el-input-number v-model="transferForm.safety_stock" :min="0" :step="1" controls-position="right" />
              </el-form-item>
              <el-form-item label="品質状態">
                <el-select v-model="transferForm.quality_status" style="width: 100%">
                  <el-option v-for="item in qualityStatuses" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="備考" class="span-4">
                <el-input v-model="transferForm.note" maxlength="500" />
              </el-form-item>
            </div>
          </section>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="dialog-cancel" @click="transferVisible = false">キャンセル</el-button>
          <el-button
            class="dialog-save dialog-save--amber"
            :loading="saving"
            :disabled="!canSubmitTransfer"
            @click="submitTransfer"
          >
            <el-icon><Switch /></el-icon>
            振替する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="manualVisible"
      width="min(920px, 96vw)"
      top="6vh"
      class="spm-dialog spm-dialog--manual pb-std"
      :show-close="false"
      destroy-on-close
    >
      <template #header>
        <div class="spm-dialog-hero pb-hero">
          <div class="pb-bubbles" aria-hidden="true" />
          <div class="spm-dialog-icon"><el-icon><EditPen /></el-icon></div>
          <div class="spm-dialog-copy">
            <h3>手動登録</h3>
            <p>生産データにない補給品も製品と期初数量を入力して登録できます（倉庫在庫は移動しません）</p>
          </div>
          <el-icon class="spm-close" @click="manualVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div class="spm-dialog-body spm-dialog-body--compact">
        <el-form label-position="top" class="spm-form spm-form--compact">
          <section class="form-section">
            <header class="form-section__title"><span class="form-section__dot" />製品情報</header>
            <div class="manual-mode-row">
              <el-form-item label="登録方法">
                <el-radio-group v-model="manualFromMaster" class="mode-switch">
                  <el-radio-button :value="true">製品マスタから選ぶ</el-radio-button>
                  <el-radio-button :value="false">未登録品を入力</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item v-if="manualFromMaster" label="製品">
                <el-select
                  v-model="manualPick"
                  filterable
                  clearable
                  placeholder="種別が補給品・製品CD末尾が 1 の製品から選択"
                  no-data-text="該当する補給品がありません"
                  :filter-method="filterProducts"
                  :loading="productSearching"
                  style="width: 100%"
                  @visible-change="onProductDropdown"
                  @change="onManualProduct"
                >
                  <el-option
                    v-for="item in productOptions"
                    :key="item.product_cd"
                    :label="`${item.product_cd} ${item.product_name}`"
                    :value="item.product_cd"
                  >
                    <span>{{ item.product_cd }} {{ item.product_name }}</span>
                    <span v-if="item.part_number" class="option-sub">{{ item.part_number }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
              <p v-else class="manual-mode-tip">製品マスタにない補給品です。製品CD・製品名を直接入力してください。</p>
            </div>
            <div class="form-grid form-grid--3">
              <el-form-item label="製品CD" required>
                <el-input
                  v-model="manualForm.product_cd"
                  maxlength="50"
                  :disabled="manualFromMaster && !!manualPick"
                />
              </el-form-item>
              <el-form-item label="製品名" required>
                <el-input v-model="manualForm.product_name" maxlength="200" />
              </el-form-item>
              <el-form-item label="品番">
                <el-input v-model="manualForm.part_number" maxlength="50" />
              </el-form-item>
              <el-form-item label="別名">
                <el-input v-model="manualForm.product_alias" maxlength="100" />
              </el-form-item>
              <el-form-item label="納入先CD">
                <el-select
                  v-model="manualForm.destination_cd"
                  filterable
                  clearable
                  placeholder="納入先マスタから選択"
                  style="width: 100%"
                  @change="(cd: string) => onDestinationChange(manualForm, cd)"
                >
                  <el-option
                    v-for="item in destinationOptions"
                    :key="item.cd"
                    :label="`${item.cd} ${item.name}`"
                    :value="item.cd"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="納入先名">
                <el-input v-model="manualForm.destination_name" disabled placeholder="納入先CDから自動入力" />
              </el-form-item>
            </div>
          </section>
          <section class="form-section form-section--sky">
            <header class="form-section__title"><span class="form-section__dot" />在庫・保管・品質</header>
            <div class="form-grid form-grid--4">
              <el-form-item label="期初数量" required>
                <el-input-number v-model="manualForm.opening_qty" :min="0" :step="1" controls-position="right" />
              </el-form-item>
              <el-form-item label="保管場所" required>
                <SupplyLocationSelect
                  v-model="manualForm.storage_location"
                  :locations="locations"
                  :can-manage="canManageLocations"
                  @manage="openLocations"
                />
              </el-form-item>
              <el-form-item label="棚番">
                <el-input v-model="manualForm.shelf_no" maxlength="50" />
              </el-form-item>
              <el-form-item label="安全在庫">
                <el-input-number v-model="manualForm.safety_stock" :min="0" :step="1" controls-position="right" />
              </el-form-item>
              <el-form-item label="品質状態">
                <el-select v-model="manualForm.quality_status" style="width: 100%">
                  <el-option v-for="item in qualityStatuses" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="備考" class="span-3">
                <el-input v-model="manualForm.note" maxlength="500" />
              </el-form-item>
            </div>
          </section>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="dialog-cancel" @click="manualVisible = false">キャンセル</el-button>
          <el-button class="dialog-save" :loading="saving" @click="submitManual">
            <el-icon><Check /></el-icon>
            登録
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="locationVisible"
      width="760px"
      class="spm-dialog pb-std"
      :show-close="false"
      append-to-body
    >
      <template #header>
        <div class="spm-dialog-hero pb-hero">
          <div class="pb-bubbles" aria-hidden="true" />
          <div class="spm-dialog-icon"><el-icon><Location /></el-icon></div>
          <div class="spm-dialog-copy">
            <h3>保管場所管理</h3>
            <p>補給品の保管場所を登録・編集します。名前を変えると、その場所の補給品もまとめて変わります</p>
          </div>
          <el-icon class="spm-close" @click="locationVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div class="spm-dialog-body">
        <section v-if="canCreate || (canEdit && locForm.id)" class="form-section">
          <header class="form-section__title">
            <span class="form-section__dot" />{{ locForm.id ? '保管場所を編集' : '保管場所を追加' }}
          </header>
          <el-form label-position="top" class="spm-form">
            <div class="location-form-grid">
              <el-form-item label="保管場所名" required>
                <el-input v-model="locForm.name" maxlength="100" placeholder="例：第2倉庫 補給品棚" />
              </el-form-item>
              <el-form-item label="表示順">
                <el-input-number v-model="locForm.sort_order" :step="1" controls-position="right" />
              </el-form-item>
              <el-form-item label="使用">
                <el-switch v-model="locForm.is_active" />
              </el-form-item>
            </div>
            <el-form-item label="備考">
              <el-input v-model="locForm.note" maxlength="255" />
            </el-form-item>
            <div class="location-form-actions">
              <el-button v-if="locForm.id" @click="resetLocForm">編集をやめる</el-button>
              <el-button class="dialog-save" :loading="locSaving" @click="saveLocation">
                <el-icon><Check /></el-icon>
                {{ locForm.id ? '更新' : '追加' }}
              </el-button>
            </div>
          </el-form>
        </section>
        <el-table v-loading="locLoading" :data="locations" size="small" border class="location-table">
          <el-table-column prop="name" label="保管場所名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="sort_order" label="表示順" width="70" align="right" />
          <el-table-column prop="usage_count" label="使用中" width="70" align="right" />
          <el-table-column label="状態" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '使用' : '停止' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="note" label="備考" min-width="120" show-overflow-tooltip />
          <el-table-column v-if="canEdit || canDelete" label="操作" width="130" align="center">
            <template #default="{ row }">
              <el-button v-if="canEdit" link type="primary" @click="editLocation(row as SupplyPartLocation)">編集</el-button>
              <el-tooltip
                v-if="canDelete"
                :disabled="row.usage_count === 0"
                content="使用中のため削除できません。使用を停止してください"
              >
                <span>
                  <el-button link type="danger" :disabled="row.usage_count > 0" @click="removeLocation(row as SupplyPartLocation)">
                    削除
                  </el-button>
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="dialog-cancel" @click="locationVisible = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <el-drawer
      v-model="detailVisible"
      size="720px"
      class="spm-drawer pb-std"
      :show-close="false"
      destroy-on-close
      @closed="disposeTrendChart"
    >
      <template #header>
        <div class="spm-dialog-hero pb-hero">
          <div class="pb-bubbles" aria-hidden="true" />
          <div class="spm-dialog-icon"><el-icon><Box /></el-icon></div>
          <div class="spm-dialog-copy">
            <h3>{{ detailTitle }}</h3>
            <p>補給品詳細｜保管・品質の編集と入出庫の登録</p>
          </div>
          <el-icon class="spm-close" @click="detailVisible = false"><Close /></el-icon>
        </div>
      </template>
      <template v-if="detail">
        <el-descriptions :column="2" border size="small" class="detail-desc">
          <el-descriptions-item label="製品CD">{{ detail.stock.product_cd }}</el-descriptions-item>
          <el-descriptions-item label="現在庫">{{ formatNum(detail.stock.on_hand_qty) }}</el-descriptions-item>
          <el-descriptions-item label="品質状態">
            <el-tag size="small" round :type="qualityTagType(detail.stock.quality_status)">
              {{ detail.stock.quality_status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="納入先">
            {{ detail.stock.destination_name || detail.stock.destination_cd || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="最終出庫日">
            {{ detail.stock.last_out_date || '未出庫' }}
            <el-tag v-if="detail.stock.stagnant" size="small" round type="warning" class="tag-gap">
              長期滞留
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="滞留月数">
            {{ detail.stock.idle_months ?? '—' }}
            <span v-if="detail.stock.idle_months != null" class="muted">（{{ detail.stock.idle_days }} 日）</span>
          </el-descriptions-item>
        </el-descriptions>

        <section class="form-section form-section--indigo">
          <h3 class="section-title"><span class="form-section__dot" />在庫推移（直近 12 ヶ月）</h3>
          <div v-loading="trendLoading" class="trend-chart-wrap">
            <div ref="trendChartRef" class="trend-chart" />
          </div>
        </section>

        <section class="form-section">
          <h3 class="section-title"><span class="form-section__dot" />保管・品質</h3>
          <el-form label-position="top" class="spm-form" :disabled="!canEdit">
            <div class="form-grid">
              <el-form-item label="製品CD">
                <el-input :model-value="detail.stock.product_cd" disabled />
              </el-form-item>
              <el-form-item label="製品名">
                <el-input v-model="editForm.product_name" maxlength="200" />
              </el-form-item>
              <el-form-item label="品番">
                <el-input v-model="editForm.part_number" maxlength="50" />
              </el-form-item>
              <el-form-item label="別名">
                <el-input v-model="editForm.product_alias" maxlength="100" />
              </el-form-item>
              <el-form-item label="納入先CD">
                <el-select
                  v-model="editForm.destination_cd"
                  filterable
                  clearable
                  placeholder="納入先マスタから選択"
                  style="width: 100%"
                  @change="(cd: string) => onDestinationChange(editForm, cd)"
                >
                  <el-option
                    v-for="item in destinationOptions"
                    :key="item.cd"
                    :label="`${item.cd} ${item.name}`"
                    :value="item.cd"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="納入先名">
                <el-input v-model="editForm.destination_name" disabled placeholder="納入先CDから自動入力" />
              </el-form-item>
              <el-form-item label="保管場所" required>
                <SupplyLocationSelect
                  v-model="editForm.storage_location"
                  :locations="locations"
                  :keep-value="detail?.stock.storage_location"
                  :can-manage="canManageLocations"
                  @manage="openLocations"
                />
              </el-form-item>
              <el-form-item label="棚番">
                <el-input v-model="editForm.shelf_no" maxlength="50" />
              </el-form-item>
              <el-form-item label="安全在庫">
                <el-input-number v-model="editForm.safety_stock" :min="0" :step="1" controls-position="right" />
              </el-form-item>
              <el-form-item label="品質状態">
                <el-select v-model="editForm.quality_status" style="width: 100%">
                  <el-option v-for="item in qualityStatuses" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
            </div>
            <el-form-item label="備考">
              <el-input v-model="editForm.note" type="textarea" :rows="2" />
            </el-form-item>
            <div v-if="canEdit" class="section-actions">
              <el-button class="dialog-save" :loading="saving" @click="saveCard">
                <el-icon><Check /></el-icon>
                保存
              </el-button>
            </div>
          </el-form>
        </section>

        <section class="form-section form-section--amber">
          <h3 class="section-title"><span class="form-section__dot" />入出庫</h3>
          <el-form v-if="canEdit" inline class="txn-form">
            <el-form-item label="区分">
              <el-select v-model="txnForm.txn_type" style="width: 140px">
                <el-option label="生産入庫" value="production_in" />
                <el-option label="実出荷" value="shipment_out" />
                <el-option label="調整" value="adjust" />
              </el-select>
            </el-form-item>
            <el-form-item :label="txnQtyLabel">
              <el-input-number
                v-model="txnForm.quantity"
                :step="1"
                :min="txnForm.txn_type === 'adjust' ? undefined : 1"
                controls-position="right"
              />
            </el-form-item>
            <el-form-item label="日付">
              <el-date-picker v-model="txnForm.occurred_date" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
            <el-form-item label="備考">
              <el-input v-model="txnForm.note" style="width: 180px" />
            </el-form-item>
            <el-form-item>
              <el-button class="dialog-save dialog-save--amber" :loading="saving" @click="submitTxn">
                <el-icon><Check /></el-icon>
                登録
              </el-button>
            </el-form-item>
          </el-form>
          <p v-if="txnForm.txn_type === 'adjust'" class="dialog-hint dialog-hint--amber">
            調整は増減数です。減らすときはマイナスを入力します。
          </p>
        </section>

        <section class="form-section form-section--indigo">
          <h3 class="section-title"><span class="form-section__dot" />当月出荷（月受注・種別が補給品）</h3>
          <el-table :data="detail.orders" size="small" border empty-text="この月の補給品受注はありません">
            <el-table-column prop="destination_cd" label="納入先CD" width="120" />
            <el-table-column prop="destination_name" label="納入先" min-width="140" />
            <el-table-column prop="forecast_total_units" label="確定本数" width="100" align="right" />
            <el-table-column prop="forecast_units" label="内示本数" width="100" align="right" />
          </el-table>
        </section>

        <section class="form-section form-section--slate">
          <h3 class="section-title"><span class="form-section__dot" />入出庫履歴</h3>
          <el-table :data="detail.transactions" size="small" border empty-text="履歴はありません">
            <el-table-column prop="occurred_date" label="日付" width="110" />
            <el-table-column label="区分" width="110">
              <template #default="{ row }">{{ txnLabel(row.txn_type) }}</template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" align="right" />
            <el-table-column prop="balance_after" label="残高" width="80" align="right" />
            <el-table-column prop="note" label="備考" min-width="180" show-overflow-tooltip />
          </el-table>
        </section>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Check,
  Clock,
  Close,
  Download,
  EditPen,
  Goods,
  Location,
  Printer,
  Search,
  Medal,
  Switch,
  WarningFilled,
} from '@element-plus/icons-vue'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
import echarts from '@/utils/echarts'
import { useInventoryOperationPermission } from '@/composables/useInventoryOperationPermission'
import {
  createSupplyPartLocation,
  createSupplyPartManual,
  createSupplyPartTransaction,
  deleteSupplyPart,
  deleteSupplyPartLocation,
  getSupplyPartDetail,
  getSupplyPartList,
  getSupplyPartLocations,
  getSupplyPartTrend,
  previewSupplyPartTransfer,
  searchSupplyPartProducts,
  transferSupplyPart,
  updateSupplyPart,
  updateSupplyPartLocation,
  type SupplyPartCardForm,
  type SupplyPartDetail,
  type SupplyPartListResponse,
  type SupplyPartLocation,
  type SupplyPartProductOption,
  type SupplyPartStock,
  type SupplyPartTransferPreview,
  type SupplyPartTransferResult,
  type SupplyPartTrendPoint,
} from '@/api/erp/supplyParts'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import SupplyLocationSelect from './SupplyLocationSelect.vue'

const { canCreate, canEdit, canDelete } = useInventoryOperationPermission()
const canManageLocations = computed(() => canCreate.value || canEdit.value)

const locations = ref<SupplyPartLocation[]>([])
const locationVisible = ref(false)
const locLoading = ref(false)
const locSaving = ref(false)
const locForm = reactive({ id: 0, name: '', sort_order: 0, is_active: true, note: '' })

const loading = ref(false)
const saving = ref(false)
const productSearching = ref(false)
const rows = ref<SupplyPartStock[]>([])
const summary = ref(emptySummary())
const locationFilter = ref('')
const destinationFilter = ref('')
const stagnantOnly = ref(false)
const stagnantDays = ref(365)
const demandMonths = ref(6)
const qualityStatuses = ref(['良好', '錆', '汚れ', 'その他'])
const exporting = ref(false)
const trendLoading = ref(false)
const trendChartRef = ref<HTMLDivElement>()
let trendChart: ReturnType<typeof echarts.init> | null = null
const keyword = ref('')
const alertOnly = ref(false)
const monthValue = ref(currentMonth())
const allProducts = ref<SupplyPartProductOption[]>([])
const productKeyword = ref('')
const productOptions = computed(() => {
  const text = productKeyword.value.trim().toLowerCase()
  if (!text) return allProducts.value
  return allProducts.value.filter((item) =>
    [item.product_cd, item.product_name, item.part_number, item.product_alias].some((value) =>
      (value || '').toLowerCase().includes(text)
    )
  )
})
const destinationOptions = ref<{ cd: string; name: string }[]>([])

const transferVisible = ref(false)
const manualVisible = ref(false)
const detailVisible = ref(false)
const preview = ref<SupplyPartTransferPreview | null>(null)
const detail = ref<SupplyPartDetail | null>(null)
const manualFromMaster = ref(true)
const manualPick = ref('')
const pickedProductType = ref('')

const transferForm = reactive(emptyTransfer())
const manualForm = reactive(emptyManual())
const editForm = reactive(emptyCard())
const txnForm = reactive({
  txn_type: 'production_in',
  quantity: 1,
  occurred_date: todayStr(),
  note: '',
})

const detailTitle = computed(() =>
  detail.value ? `${detail.value.stock.product_cd} ${detail.value.stock.product_name}` : '補給品詳細'
)
const previewTitle = computed(() => {
  if (!preview.value) return ''
  if (preview.value.already_registered) return 'この品番はすでに補給品在庫へ登録済みです'
  if (preview.value.warning) return preview.value.warning
  return `入庫数量 ${preview.value.transfer_qty}（倉庫在庫合計 ${preview.value.raw_warehouse_qty}）`
})
const canSubmitTransfer = computed(
  () =>
    !!transferForm.product_cd &&
    !!transferForm.storage_location.trim() &&
    !!preview.value &&
    !preview.value.already_registered
)
const txnQtyLabel = computed(() => (txnForm.txn_type === 'adjust' ? '増減数' : '数量'))

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatNum(value: number | null | undefined) {
  return Number(value || 0).toLocaleString()
}

function formatDecimal(value: number | null | undefined) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })
}

function emptySummary(): SupplyPartListResponse['summary'] {
  return {
    count: 0,
    on_hand_total: 0,
    shipment_total: 0,
    alert_count: 0,
    stagnant_count: 0,
    quality_issue_count: 0,
  }
}

function qualityTagType(status?: string | null) {
  const map: Record<string, 'success' | 'danger' | 'warning' | 'info'> = {
    良好: 'success',
    錆: 'danger',
    汚れ: 'warning',
  }
  return map[status || ''] || 'info'
}

function rowClass({ row }: { row: SupplyPartStock }) {
  return row.below_safety || row.short_of_shipment ? 'supply-row-alert' : ''
}

function txnLabel(type: string) {
  const map: Record<string, string> = {
    transfer_in: '振替入庫',
    manual_in: '手動入庫',
    production_in: '生産入庫',
    shipment_out: '実出荷',
    adjust: '調整',
  }
  return map[type] || type
}

function yearMonth() {
  const [year, month] = monthValue.value.split('-').map((v) => Number(v))
  return { year, month }
}

function emptyCard(): SupplyPartCardForm {
  return {
    product_name: '',
    product_alias: '',
    part_number: '',
    destination_cd: '',
    destination_name: '',
    storage_location: '',
    shelf_no: '',
    safety_stock: 0,
    quality_status: '良好',
    note: '',
  }
}

function emptyTransfer() {
  return { product_cd: '', ...emptyCard() }
}

function emptyManual() {
  return { product_cd: '', opening_qty: 0, ...emptyCard() }
}

function blankToNull(value?: string | null) {
  const text = (value || '').trim()
  return text || null
}

function cardPayload(form: SupplyPartCardForm): SupplyPartCardForm {
  return {
    product_name: (form.product_name || '').trim(),
    product_alias: blankToNull(form.product_alias),
    part_number: blankToNull(form.part_number),
    destination_cd: blankToNull(form.destination_cd),
    destination_name: blankToNull(form.destination_name),
    storage_location: (form.storage_location || '').trim(),
    shelf_no: blankToNull(form.shelf_no),
    safety_stock: Number(form.safety_stock || 0),
    quality_status: form.quality_status || '良好',
    note: blankToNull(form.note),
  }
}

function onDestinationChange(form: SupplyPartCardForm, cd: string) {
  form.destination_name = destinationOptions.value.find((item) => item.cd === cd)?.name || ''
}

async function loadDestinations() {
  try {
    destinationOptions.value = await getDestinationOptions()
  } catch {
    destinationOptions.value = []
  }
}

function showServerError(error: unknown, fallback: string) {
  const status = (error as { response?: { status?: number } }).response?.status
  if (!status || status >= 500) ElMessage.error(fallback)
}

async function loadList() {
  const { year, month } = yearMonth()
  if (!year || !month) return
  loading.value = true
  try {
    const res = (await getSupplyPartList({
      year,
      month,
      keyword: keyword.value.trim() || undefined,
      alert_only: alertOnly.value,
      storage_location: locationFilter.value || undefined,
      destination_cd: destinationFilter.value || undefined,
      stagnant_only: stagnantOnly.value,
    })) as unknown as SupplyPartListResponse
    rows.value = res.list || []
    summary.value = res.summary || emptySummary()
    stagnantDays.value = res.stagnant_days || stagnantDays.value
    demandMonths.value = res.demand_months || demandMonths.value
    if (res.quality_statuses?.length) qualityStatuses.value = res.quality_statuses
  } catch (error) {
    showServerError(error, '一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

async function loadProducts(supplyOnly = false) {
  allProducts.value = []
  productSearching.value = true
  try {
    const res = (await searchSupplyPartProducts(undefined, 2000, supplyOnly)) as unknown as {
      list: SupplyPartProductOption[]
    }
    allProducts.value = res.list || []
  } catch {
    allProducts.value = []
  } finally {
    productSearching.value = false
  }
}

function filterProducts(text: string) {
  productKeyword.value = text || ''
}

function onProductDropdown(visible: boolean) {
  if (visible) productKeyword.value = ''
}

function openTransfer() {
  Object.assign(transferForm, emptyTransfer())
  preview.value = null
  productKeyword.value = ''
  transferVisible.value = true
  loadProducts()
}

async function onTransferProduct(productCd: string) {
  preview.value = null
  if (!productCd) return
  try {
    preview.value = (await previewSupplyPartTransfer(productCd)) as unknown as SupplyPartTransferPreview
  } catch (error) {
    showServerError(error, '倉庫在庫の確認に失敗しました')
  }
}

async function submitTransfer() {
  if (!canSubmitTransfer.value) return
  saving.value = true
  try {
    const res = (await transferSupplyPart({
      product_cd: transferForm.product_cd,
      ...cardPayload(transferForm),
    })) as unknown as SupplyPartTransferResult
    if (res.warning) ElMessage.warning(res.warning)
    else ElMessage.success(`振替しました。補給品へ入庫 ${res.transfer_qty}、在庫取引記録に同数の保留を登録しました。`)
    transferVisible.value = false
    await loadList()
  } catch (error) {
    showServerError(error, '振替に失敗しました')
  } finally {
    saving.value = false
  }
}

function openManual() {
  Object.assign(manualForm, emptyManual())
  manualFromMaster.value = true
  manualPick.value = ''
  pickedProductType.value = ''
  productKeyword.value = ''
  manualVisible.value = true
  loadProducts(true)
}

function clearManualProduct() {
  Object.assign(manualForm, {
    product_cd: '',
    product_name: '',
    part_number: '',
    product_alias: '',
    destination_cd: '',
    destination_name: '',
  })
  pickedProductType.value = ''
}

watch(manualFromMaster, () => {
  manualPick.value = ''
  clearManualProduct()
})

function onManualProduct(productCd: string) {
  const found = allProducts.value.find((item) => item.product_cd === productCd)
  if (!found) {
    clearManualProduct()
    return
  }
  manualForm.product_cd = found.product_cd
  manualForm.product_name = found.product_name
  manualForm.product_alias = found.product_alias || ''
  manualForm.part_number = found.part_number || ''
  manualForm.destination_cd = found.destination_cd || ''
  manualForm.destination_name = found.destination_name || ''
  pickedProductType.value = found.product_type || ''
}

async function submitManual() {
  const productCd = manualForm.product_cd.trim()
  const productName = (manualForm.product_name || '').trim()
  const location = manualForm.storage_location.trim()
  if (!productCd || !productName || !location) {
    ElMessage.warning('製品CD、製品名、保管場所は必須です')
    return
  }
  if (pickedProductType.value && pickedProductType.value !== '補給品') {
    try {
      await ElMessageBox.confirm(
        `この製品の種別は「${pickedProductType.value}」です。手動登録は倉庫在庫を移しません。量産の倉庫在庫を移す場合は振替を使ってください。このまま登録しますか？`,
        '確認',
        { type: 'warning' }
      )
    } catch {
      return
    }
  }
  saving.value = true
  try {
    await createSupplyPartManual({
      ...cardPayload(manualForm),
      product_cd: productCd,
      product_name: productName,
      opening_qty: Number(manualForm.opening_qty || 0),
    })
    ElMessage.success('登録しました')
    manualVisible.value = false
    await loadList()
  } catch (error) {
    showServerError(error, '登録に失敗しました')
  } finally {
    saving.value = false
  }
}

function fillEdit(stock: SupplyPartStock) {
  editForm.product_name = stock.product_name
  editForm.product_alias = stock.product_alias || ''
  editForm.part_number = stock.part_number || ''
  editForm.destination_cd = stock.destination_cd || ''
  editForm.destination_name = stock.destination_name || ''
  editForm.storage_location = stock.storage_location || ''
  editForm.shelf_no = stock.shelf_no || ''
  editForm.safety_stock = stock.safety_stock || 0
  editForm.quality_status = stock.quality_status || '良好'
  editForm.note = stock.note || ''
}

async function openDetail(row: SupplyPartStock) {
  const { year, month } = yearMonth()
  try {
    detail.value = (await getSupplyPartDetail(row.id, year, month)) as unknown as SupplyPartDetail
    fillEdit(detail.value.stock)
    txnForm.txn_type = 'production_in'
    txnForm.quantity = 1
    txnForm.occurred_date = todayStr()
    txnForm.note = ''
    detailVisible.value = true
    loadTrend()
  } catch (error) {
    showServerError(error, '詳細の取得に失敗しました')
  }
}

async function removeStock(row: SupplyPartStock) {
  const lines = [
    `補給品「${escapeHtml(row.product_cd)} ${escapeHtml(row.product_name)}」を削除しますか？`,
    `現在庫 ${formatNum(row.on_hand_qty)} と入出庫履歴もすべて削除され、元に戻せません。`,
  ]
  if (row.source === 'transfer') {
    lines.push('振替時に在庫取引記録へ登録した「補給品へ振替」の保留も削除します（製品種別は変更しません）。')
  }
  try {
    await ElMessageBox.confirm(lines.join('<br>'), '削除の確認', {
      type: 'warning',
      dangerouslyUseHTMLString: true,
      confirmButtonText: '削除する',
      cancelButtonText: 'キャンセル',
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  try {
    const res = (await deleteSupplyPart(row.id)) as unknown as { removed_stock_logs: number }
    ElMessage.success(
      res.removed_stock_logs
        ? `削除しました（在庫取引記録の振替保留 ${res.removed_stock_logs} 件も削除）`
        : '削除しました'
    )
    if (detailVisible.value && detail.value?.stock.id === row.id) detailVisible.value = false
    await loadList()
  } catch (error) {
    showServerError(error, '削除に失敗しました')
  }
}

async function reloadDetail() {
  if (!detail.value) return
  const { year, month } = yearMonth()
  detail.value = (await getSupplyPartDetail(detail.value.stock.id, year, month)) as unknown as SupplyPartDetail
  fillEdit(detail.value.stock)
  loadTrend()
}

async function loadTrend() {
  if (!detail.value) return
  const { year, month } = yearMonth()
  trendLoading.value = true
  try {
    const res = (await getSupplyPartTrend(detail.value.stock.id, year, month)) as unknown as {
      points: SupplyPartTrendPoint[]
    }
    await nextTick()
    renderTrend(res.points || [])
  } catch (error) {
    showServerError(error, '在庫推移の取得に失敗しました')
  } finally {
    trendLoading.value = false
  }
}

function renderTrend(points: SupplyPartTrendPoint[]) {
  const el = trendChartRef.value
  if (!el) return
  let chart = trendChart
  if (!chart || chart.getDom() !== el) {
    chart?.dispose()
    chart = echarts.init(el)
    trendChart = chart
  }
  chart.setOption(
    {
      tooltip: { trigger: 'axis' },
      legend: { top: 0, itemWidth: 12, itemHeight: 8, textStyle: { fontSize: 11 } },
      grid: { left: 44, right: 16, top: 30, bottom: 24 },
      xAxis: {
        type: 'category',
        data: points.map((p) => p.month.slice(2).replace('-', '/')),
        axisLabel: { fontSize: 10 },
      },
      yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10 } },
      series: [
        {
          name: '入庫',
          type: 'bar',
          barMaxWidth: 14,
          itemStyle: { color: '#14b8a6' },
          data: points.map((p) => p.in_qty),
        },
        {
          name: '出庫',
          type: 'bar',
          barMaxWidth: 14,
          itemStyle: { color: '#f59e0b' },
          data: points.map((p) => p.out_qty),
        },
        {
          name: '月末在庫',
          type: 'line',
          smooth: true,
          symbolSize: 5,
          itemStyle: { color: '#4f46e5' },
          data: points.map((p) => p.end_balance),
        },
        {
          name: '受注確定',
          type: 'line',
          symbolSize: 4,
          lineStyle: { type: 'dashed' },
          itemStyle: { color: '#e11d48' },
          data: points.map((p) => p.order_qty),
        },
      ],
    },
    true
  )
  chart.resize()
}

function disposeTrendChart() {
  trendChart?.dispose()
  trendChart = null
}

function onResize() {
  trendChart?.resize()
}

async function exportExcel() {
  if (!rows.value.length) return
  exporting.value = true
  try {
    const workbook = new ExcelJS.Workbook()
    const sheet = workbook.addWorksheet('補給品在庫')
    sheet.columns = [
      { header: '製品CD', key: 'product_cd', width: 12 },
      { header: '製品名', key: 'product_name', width: 28 },
      { header: '品番', key: 'part_number', width: 14 },
      { header: '別名', key: 'product_alias', width: 14 },
      { header: '納入先CD', key: 'destination_cd', width: 10 },
      { header: '納入先名', key: 'destination_name', width: 18 },
      { header: '保管場所', key: 'storage_location', width: 16 },
      { header: '棚番', key: 'shelf_no', width: 10 },
      { header: '現在庫', key: 'on_hand_qty', width: 10 },
      { header: '安全在庫', key: 'safety_stock', width: 10 },
      { header: '品質状態', key: 'quality_status', width: 10 },
      { header: '月平均出荷', key: 'avg_monthly_demand', width: 11 },
      { header: '滞留月数', key: 'idle_months', width: 10 },
      { header: '最終出庫日', key: 'last_out_date', width: 12 },
      { header: '備考', key: 'note', width: 30 },
    ]
    rows.value.forEach((row) => sheet.addRow(row))
    const header = sheet.getRow(1)
    header.font = { bold: true, color: { argb: 'FFFFFFFF' } }
    header.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF0F766E' } }
    sheet.views = [{ state: 'frozen', ySplit: 1 }]
    sheet.autoFilter = { from: 'A1', to: 'O1' }
    const buffer = await workbook.xlsx.writeBuffer()
    saveAs(
      new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
      `補給品在庫_${monthValue.value}.xlsx`
    )
  } catch {
    ElMessage.error('Excel 出力に失敗しました')
  } finally {
    exporting.value = false
  }
}

function escapeHtml(value: unknown) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch] as string
  )
}

function printStocktakeSheet() {
  if (!rows.value.length) return
  const groups = new Map<string, SupplyPartStock[]>()
  ;[...rows.value]
    .sort(
      (a, b) =>
        (a.storage_location || '').localeCompare(b.storage_location || '', 'ja') ||
        (a.shelf_no || '').localeCompare(b.shelf_no || '', 'ja') ||
        a.product_cd.localeCompare(b.product_cd)
    )
    .forEach((row) => {
      const key = row.storage_location || '（保管場所なし）'
      groups.set(key, [...(groups.get(key) || []), row])
    })
  const printedAt = todayStr()
  const pages = [...groups.entries()]
    .map(([location, items]) => {
      const body = items
        .map(
          (row, index) => `<tr>
            <td class="c">${index + 1}</td>
            <td>${escapeHtml(row.shelf_no)}</td>
            <td>${escapeHtml(row.product_cd)}</td>
            <td>${escapeHtml(row.product_name)}</td>
            <td>${escapeHtml(row.part_number)}</td>
            <td class="r">${formatNum(row.on_hand_qty)}</td>
            <td></td><td></td><td></td>
          </tr>`
        )
        .join('')
      return `<section class="page">
        <h1>補給品 棚卸表</h1>
        <div class="meta">
          <span>保管場所：<b>${escapeHtml(location)}</b></span>
          <span>印刷日：${printedAt}</span>
          <span>棚卸日：＿＿＿＿＿＿</span>
          <span>担当：＿＿＿＿＿＿</span>
        </div>
        <table>
          <thead><tr>
            <th style="width:32px">No</th><th style="width:70px">棚番</th><th style="width:80px">製品CD</th>
            <th>製品名</th><th style="width:90px">品番</th><th style="width:70px">帳簿在庫</th>
            <th style="width:70px">実棚数</th><th style="width:60px">差異</th><th style="width:90px">備考</th>
          </tr></thead>
          <tbody>${body}</tbody>
        </table>
        <p class="foot">${items.length} 件</p>
      </section>`
    })
    .join('')
  const win = window.open('', '_blank')
  if (!win) {
    ElMessage.warning('ポップアップがブロックされました。許可してから再度お試しください')
    return
  }
  win.document.write(`<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>補給品棚卸表</title>
    <style>
      @page { size: A4 portrait; margin: 12mm; }
      body { font-family: 'Meiryo', 'Yu Gothic', sans-serif; font-size: 11px; color: #111; margin: 0; }
      .page { page-break-after: always; }
      .page:last-child { page-break-after: auto; }
      h1 { font-size: 18px; margin: 0 0 6px; }
      .meta { display: flex; gap: 18px; margin-bottom: 8px; font-size: 12px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border: 1px solid #555; padding: 5px 4px; height: 18px; }
      th { background: #e5e7eb; font-weight: 700; }
      .r { text-align: right; } .c { text-align: center; }
      .foot { text-align: right; margin: 4px 0 0; }
    </style></head><body>${pages}</body></html>`)
  win.document.close()
  win.focus()
  setTimeout(() => win.print(), 300)
}

async function saveCard() {
  if (!detail.value) return
  if (!editForm.storage_location?.trim()) {
    ElMessage.warning('保管場所は必須です')
    return
  }
  saving.value = true
  try {
    await updateSupplyPart(detail.value.stock.id, {
      ...cardPayload(editForm),
      product_name: (editForm.product_name || '').trim(),
    })
    ElMessage.success('保存しました')
    await reloadDetail()
    await loadList()
  } catch (error) {
    showServerError(error, '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function submitTxn() {
  if (!detail.value) return
  if (!txnForm.occurred_date) {
    ElMessage.warning('日付を入力してください')
    return
  }
  if (txnForm.txn_type !== 'adjust' && Number(txnForm.quantity) <= 0) {
    ElMessage.warning('数量は 1 以上にしてください')
    return
  }
  if (txnForm.txn_type === 'adjust' && Number(txnForm.quantity) === 0) {
    ElMessage.warning('調整数量を入力してください')
    return
  }
  saving.value = true
  try {
    await createSupplyPartTransaction(detail.value.stock.id, {
      txn_type: txnForm.txn_type,
      quantity: Number(txnForm.quantity),
      occurred_date: txnForm.occurred_date,
      note: blankToNull(txnForm.note),
    })
    ElMessage.success('入出庫を登録しました')
    txnForm.note = ''
    await reloadDetail()
    await loadList()
  } catch (error) {
    showServerError(error, '入出庫の登録に失敗しました')
  } finally {
    saving.value = false
  }
}

async function loadLocations() {
  locLoading.value = true
  try {
    const res = (await getSupplyPartLocations(true)) as unknown as { list: SupplyPartLocation[] }
    locations.value = res.list || []
  } catch (error) {
    showServerError(error, '保管場所の取得に失敗しました')
  } finally {
    locLoading.value = false
  }
}

function resetLocForm() {
  Object.assign(locForm, { id: 0, name: '', sort_order: 0, is_active: true, note: '' })
}

function openLocations() {
  resetLocForm()
  locationVisible.value = true
  loadLocations()
}

function editLocation(row: SupplyPartLocation) {
  Object.assign(locForm, {
    id: row.id,
    name: row.name,
    sort_order: row.sort_order,
    is_active: row.is_active,
    note: row.note || '',
  })
}

async function saveLocation() {
  const name = locForm.name.trim()
  if (!name) {
    ElMessage.warning('保管場所名を入力してください')
    return
  }
  const payload = {
    name,
    sort_order: Number(locForm.sort_order || 0),
    is_active: locForm.is_active,
    note: blankToNull(locForm.note),
  }
  locSaving.value = true
  try {
    if (locForm.id) {
      const res = (await updateSupplyPartLocation(locForm.id, payload)) as unknown as {
        renamed_stocks: number
      }
      ElMessage.success(
        res.renamed_stocks
          ? `更新しました。補給品 ${res.renamed_stocks} 件の保管場所も変更しました`
          : '更新しました'
      )
      if (res.renamed_stocks) {
        await loadList()
        if (detailVisible.value) await reloadDetail()
      }
    } else {
      await createSupplyPartLocation(payload)
      ElMessage.success('追加しました')
    }
    resetLocForm()
    await loadLocations()
  } catch (error) {
    showServerError(error, '保管場所の保存に失敗しました')
  } finally {
    locSaving.value = false
  }
}

async function removeLocation(row: SupplyPartLocation) {
  try {
    await ElMessageBox.confirm(`保管場所「${row.name}」を削除しますか？`, '確認', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteSupplyPartLocation(row.id)
    ElMessage.success('削除しました')
    if (locForm.id === row.id) resetLocForm()
    await loadLocations()
  } catch (error) {
    showServerError(error, '保管場所の削除に失敗しました')
  }
}

onMounted(() => {
  loadList()
  loadLocations()
  loadDestinations()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeTrendChart()
})
</script>

<style scoped>
.supply-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
  padding: 16px 20px 28px;
  background: linear-gradient(180deg, #e6f7f5 0%, #f8fafc 240px, #f8fafc 100%);
}

/* ---------- タイトル領域 ---------- */
.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(125deg, #115e59 0%, #0f766e 30%, #0d9488 62%, #0891b2 100%);
  box-shadow: 0 10px 24px -12px rgba(15, 118, 110, 0.5);
}
.spm-hero-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.spm-hero-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.spm-hero-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.spm-hero-copy .pb-hero-title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #fff;
}
.spm-hero-copy .pb-hero-desc {
  margin: 0;
  color: rgba(236, 253, 245, 0.92);
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.page-header .spm-head-btn {
  height: 34px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 700;
}
.page-header .spm-head-btn .el-icon {
  margin-right: 5px;
}
.page-header .spm-head-btn--transfer {
  --k-rgb: 217 119 6;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.75);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #f59e0b, #d97706);
}
.page-header .spm-head-btn--transfer:hover,
.page-header .spm-head-btn--transfer:focus-visible {
  color: #fff;
  border-color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fbbf24, #f59e0b);
}
.page-header .spm-head-btn--manual {
  --k-rgb: 15 118 110;
  color: #0f766e;
  border: 1px solid #fff;
  background: linear-gradient(180deg, #ffffff 0%, #f0fdfa 100%);
}
.page-header .spm-head-btn--manual:hover,
.page-header .spm-head-btn--manual:focus-visible {
  color: #115e59;
  border-color: #fff;
  background: linear-gradient(180deg, #ffffff 0%, #ccfbf1 100%);
}

/* ---------- 統計カード ---------- */
.stat-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.stat-card {
  --accent: #0d9488;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px 10px 17px;
  border-radius: 12px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 7%, #fff) 0%, #fff 70%);
  border: 1px solid color-mix(in srgb, var(--accent) 22%, #e2e8f0);
  box-shadow: 0 4px 12px -8px rgba(15, 23, 42, 0.18);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: var(--accent);
}
.stat-card--sky {
  --accent: #0284c7;
}
.stat-card--indigo {
  --accent: #4f46e5;
}
.stat-card--rose {
  --accent: #94a3b8;
}
.stat-card--alert {
  --accent: #e11d48;
  background: linear-gradient(135deg, #fff1f2 0%, #fff 70%);
}
.stat-card--amber {
  --accent: #94a3b8;
}
.stat-card--stagnant {
  --accent: #d97706;
  background: linear-gradient(135deg, #fffbeb 0%, #fff 70%);
}
.stat-card--amber:not(.stat-card--stagnant) .stat-card__body strong {
  color: #64748b;
}
.stat-card__icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, #fff);
  box-shadow: inset 0 -2px 0 color-mix(in srgb, var(--accent) 16%, transparent);
}
.stat-card__body {
  min-width: 0;
}
.stat-card__body span {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}
.stat-card__body strong {
  display: block;
  margin-top: 1px;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}
.stat-card--rose:not(.stat-card--alert) .stat-card__body strong {
  color: #64748b;
}

/* ---------- 検索バー ---------- */
.toolbar {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 13px 16px 10px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ccebe6;
  box-shadow: 0 4px 12px -8px rgba(15, 118, 110, 0.25);
}
.toolbar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0d9488, #0891b2);
}
.toolbar__label {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #0f766e;
  background: #f0fdfa;
  border: 1px solid #ccfbf1;
}
.month-picker {
  width: 140px;
}
.keyword {
  width: 240px;
}
.filter-select {
  width: 160px;
}
.toolbar :deep(.el-select__wrapper) {
  border-radius: 9px;
  box-shadow: inset 0 0 0 1px #d5e3e1;
}
.toolbar__right {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
.toolbar .tool-btn {
  height: 32px;
  padding: 0 14px;
  border-radius: 9px;
  font-weight: 700;
  color: #0f766e;
  border: 1px solid #99f6e4;
  background: linear-gradient(180deg, #ffffff 0%, #f0fdfa 100%);
}
.toolbar .tool-btn:not(.is-disabled):hover {
  color: #115e59;
  border-color: #2dd4bf;
  background: linear-gradient(180deg, #ffffff 0%, #ccfbf1 100%);
}
.toolbar .tool-btn .el-icon {
  margin-right: 4px;
}
.stagnant-check {
  background: #fffbeb;
  border-color: #fde68a;
}
.stagnant-check :deep(.el-checkbox__label) {
  color: #b45309;
}
.stagnant-check :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #d97706;
  border-color: #d97706;
}
.toolbar :deep(.el-input__wrapper) {
  border-radius: 9px;
  box-shadow: inset 0 0 0 1px #d5e3e1;
  transition: box-shadow 0.15s ease;
}
.toolbar :deep(.el-input__wrapper:hover) {
  box-shadow: inset 0 0 0 1px #5eead4;
}
.toolbar :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px #0d9488,
    0 0 0 3px rgba(13, 148, 136, 0.15);
}
.alert-check {
  height: 32px;
  margin-right: 0;
  padding: 0 12px;
  border-radius: 9px;
  background: #fff1f2;
  border: 1px solid #fecdd3;
}
.alert-check :deep(.el-checkbox__label) {
  font-weight: 700;
  color: #be123c;
}
.alert-check :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #e11d48;
  border-color: #e11d48;
}
.toolbar .search-btn {
  --k-rgb: 13 148 136;
  height: 32px;
  padding: 0 18px;
  border-radius: 9px;
  font-weight: 700;
  color: #fff;
  border: 1px solid #0f766e;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #14b8a6, #0f766e);
}
.toolbar .search-btn:hover,
.toolbar .search-btn:focus-visible {
  color: #fff;
  border-color: #115e59;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #2dd4bf, #0d9488);
}
.toolbar .search-btn .el-icon {
  margin-right: 4px;
}

/* ---------- 一覧 ---------- */
.table-card {
  position: relative;
  overflow: hidden;
  padding: 3px 0 0;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ccebe6;
  box-shadow: 0 6px 18px -12px rgba(15, 118, 110, 0.3);
}
.table-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0d9488, #0891b2);
}
.data-table {
  width: 100%;
  cursor: pointer;
  --el-table-border-color: #e6eef0;
  --el-table-row-hover-bg-color: #f0fdfa;
}
.data-table :deep(th.el-table__cell) {
  font-weight: 700;
  color: #115e59;
  background: #f0fdfa;
}
.data-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #fafdfc;
}
.cd-text {
  font-weight: 700;
  color: #0f766e;
  font-family: Consolas, Monaco, monospace;
}
.num-strong {
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.num-ok {
  color: #047857;
  font-weight: 600;
}
.num-alert {
  color: #e11d48;
  font-weight: 700;
}
.num-warn {
  color: #b45309;
  font-weight: 700;
}
.trend-chart-wrap {
  margin-bottom: 10px;
}
.trend-chart {
  width: 100%;
  height: 240px;
}
.muted {
  color: #94a3b8;
}
.tag-gap {
  margin-left: 4px;
}
.option-sub {
  float: right;
  margin-left: 12px;
  font-size: 12px;
  color: #94a3b8;
}
.location-form-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 80px;
  gap: 0 12px;
}
.location-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.location-table {
  margin-top: 12px;
  width: 100%;
}
:deep(.supply-row-alert) {
  --el-table-tr-bg-color: #fff1f2;
}
:deep(.supply-row-alert.el-table__row--striped td.el-table__cell) {
  background: #fff1f2;
}

/* ============================================================
 * ダイアログ／ドロワー（append 先で scope 属性が付かないため外枠は :global で指定）
 * ============================================================ */
:global(.el-dialog.spm-dialog) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 24px 48px -16px rgba(15, 118, 110, 0.4),
    0 0 0 1px rgba(13, 148, 136, 0.12);
}
:global(.el-dialog.spm-dialog--transfer) {
  box-shadow:
    0 24px 48px -16px rgba(180, 83, 9, 0.38),
    0 0 0 1px rgba(217, 119, 6, 0.12);
}
:global(.el-dialog.spm-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}
:global(.el-dialog.spm-dialog .el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #f6fbfa, #f5f7fb);
}
:global(.el-dialog.spm-dialog .el-dialog__footer) {
  padding: 12px 18px 14px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
:global(.el-drawer.spm-drawer .el-drawer__header) {
  margin: 0;
  padding: 0;
}
:global(.el-drawer.spm-drawer .el-drawer__body) {
  padding: 14px 16px;
  background: #f6f9f9;
}
:global(.el-drawer.spm-drawer .el-descriptions__label) {
  font-weight: 700;
  color: #115e59 !important;
  background: #f0fdfa !important;
}
:global(.el-drawer.spm-drawer .el-table th.el-table__cell) {
  font-weight: 700;
  color: #334155;
  background: #f8fafc;
}

.spm-dialog-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #fff;
  background: linear-gradient(125deg, #115e59 0%, #0f766e 34%, #0d9488 68%, #0891b2 100%);
}
.spm-dialog-hero--amber {
  background: linear-gradient(125deg, #b45309 0%, #d97706 40%, #f59e0b 76%, #fbbf24 100%);
}
.spm-dialog-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.18);
}
.spm-dialog-copy {
  flex: 1;
  min-width: 0;
}
.spm-dialog-copy h3 {
  margin: 0;
  overflow: hidden;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.spm-dialog-copy p {
  margin: 3px 0 0;
  overflow: hidden;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.88);
}
.spm-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 9px;
  font-size: 18px;
  color: #fff;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: background 0.2s ease;
}
.spm-close:hover {
  background: rgba(255, 255, 255, 0.3);
}
.spm-dialog-body {
  padding: 14px 16px 6px;
}
.dialog-hint {
  margin: 0 0 10px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.6;
  color: #115e59;
  background: #f0fdfa;
  border: 1px solid #ccfbf1;
}
.dialog-hint--amber {
  color: #92400e;
  background: #fffbeb;
  border-color: #fde68a;
}

.form-section {
  --accent: #0d9488;
  position: relative;
  overflow: hidden;
  margin-bottom: 10px;
  padding: 12px 14px 4px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #e2e8f0);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.form-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 30%, #fff));
}
.form-section--amber {
  --accent: #d97706;
}
.form-section--sky {
  --accent: #0284c7;
}
.form-section--indigo {
  --accent: #4f46e5;
}
.form-section--slate {
  --accent: #64748b;
}
.form-section__title,
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #334155;
}
.form-section__dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
}
.form-section > .el-table {
  margin-bottom: 10px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.form-grid--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.form-grid--4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.form-grid .span-2 {
  grid-column: span 2;
}
.form-grid .span-3 {
  grid-column: span 3;
}
.form-grid .span-4 {
  grid-column: span 4;
}
.transfer-target-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 0 16px;
  align-items: start;
}
.transfer-target-row .preview-alert {
  margin-bottom: 8px;
}
.transfer-target-row .preview-table {
  width: 100%;
  margin: 0;
}
.transfer-preview-empty {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  height: 32px;
  margin: 0;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
}
.manual-mode-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0 16px;
  align-items: end;
}
.manual-mode-tip {
  margin: 0 0 8px;
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 12px;
  color: #115e59;
  background: #f0fdfa;
  border: 1px dashed #99f6e4;
}
.spm-dialog-body--compact {
  padding: 12px 16px 2px;
}
.spm-dialog-body--compact .form-section {
  margin-bottom: 8px;
  padding: 10px 14px 2px;
}
.spm-dialog-body--compact .form-section__title {
  margin-bottom: 6px;
}
.spm-form.spm-form--compact :deep(.el-form-item) {
  margin-bottom: 8px;
}
.spm-form.spm-form--compact :deep(.el-form-item__label) {
  margin-bottom: 2px !important;
  line-height: 18px;
}
@media (max-width: 760px) {
  .form-grid--3,
  .form-grid--4,
  .manual-mode-row {
    grid-template-columns: 1fr 1fr;
  }
  .transfer-target-row {
    grid-template-columns: 1fr;
  }
  .form-grid .span-3,
  .form-grid .span-4 {
    grid-column: span 2;
  }
}
.spm-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
.spm-form :deep(.el-form-item__label) {
  margin-bottom: 4px !important;
  font-weight: 700;
  color: #475569;
}
.spm-form :deep(.el-input-number) {
  width: 100%;
}
.spm-form :deep(.el-input__wrapper),
.spm-form :deep(.el-select__wrapper),
.spm-form :deep(.el-textarea__inner),
.txn-form :deep(.el-input__wrapper),
.txn-form :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: inset 0 0 0 1px #d5e3e1;
}
.spm-form :deep(.el-input__wrapper:hover),
.spm-form :deep(.el-select__wrapper:hover),
.spm-form :deep(.el-textarea__inner:hover),
.txn-form :deep(.el-input__wrapper:hover),
.txn-form :deep(.el-select__wrapper:hover) {
  box-shadow: inset 0 0 0 1px #5eead4;
}
.spm-form :deep(.el-input__wrapper.is-focus),
.spm-form :deep(.el-select__wrapper.is-focused),
.spm-form :deep(.el-textarea__inner:focus),
.txn-form :deep(.el-input__wrapper.is-focus),
.txn-form :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    inset 0 0 0 1px #0d9488,
    0 0 0 3px rgba(13, 148, 136, 0.14);
}
.spm-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f1f5f9;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}
.mode-switch :deep(.el-radio-button__inner) {
  font-weight: 700;
  color: #0f766e;
}
.mode-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  border-color: #0f766e;
  background: linear-gradient(135deg, #14b8a6, #0f766e);
  box-shadow: -1px 0 0 0 #0f766e;
}
.preview-alert,
.preview-table {
  margin-bottom: 12px;
  border-radius: 10px;
}
.detail-desc {
  margin-bottom: 10px;
  border-radius: 10px;
  overflow: hidden;
}
.txn-form {
  margin-bottom: 2px;
}
.txn-form :deep(.el-form-item) {
  margin-right: 12px;
  margin-bottom: 10px;
}
.txn-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #92400e;
}
.section-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

/* ---------- ダイアログのボタン ---------- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.dialog-cancel {
  --k-rgb: 100 116 139;
  height: 34px;
  border-radius: 9px;
  font-weight: 700;
  color: #475569;
  border: 1px solid #d6dde8;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}
.dialog-save {
  --k-rgb: 13 148 136;
  min-width: 104px;
  height: 34px;
  border-radius: 9px;
  font-weight: 800;
  color: #fff;
  border: 1px solid #0f766e;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #14b8a6, #0f766e);
}
.dialog-save:not(.is-disabled):hover,
.dialog-save:not(.is-disabled):focus-visible {
  color: #fff;
  border-color: #115e59;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #2dd4bf, #0d9488);
}
.dialog-save--amber {
  --k-rgb: 217 119 6;
  border-color: #b45309;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #f59e0b, #d97706);
}
.dialog-save--amber:not(.is-disabled):hover,
.dialog-save--amber:not(.is-disabled):focus-visible {
  border-color: #92400e;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fbbf24, #f59e0b);
}
.dialog-footer .dialog-save.is-disabled,
.dialog-footer .dialog-save.is-disabled:hover {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
  box-shadow: none;
}
.dialog-save .el-icon {
  margin-right: 4px;
}
</style>
