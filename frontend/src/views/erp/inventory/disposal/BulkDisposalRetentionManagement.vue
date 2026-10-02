<template>
  <div class="bdr-page bdr-modern">
    <div class="page-ambient" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
    </div>

    <div class="bdr-inner">
      <header class="toolbar toolbar-elevated animate-in" style="--delay: 0ms">
        <div class="toolbar-fx" aria-hidden="true">
          <span class="fx-orb orb-a" />
          <span class="fx-orb orb-b" />
          <span class="fx-grid" />
          <span class="fx-sheen" />
        </div>
        <div class="toolbar-brand">
          <div class="brand-icon">
            <el-icon :size="20"><WarningFilled /></el-icon>
          </div>
          <div class="brand-copy">
            <h1 class="toolbar-title">大量廃棄・保留品管理</h1>
            <p class="toolbar-sub">記録登録 · 処理追跡 · 未処理通知 · 在庫消滅</p>
            <div class="toolbar-chips">
              <span class="toolbar-chip">
                <el-icon><Calendar /></el-icon>
                {{ filters.date_range ? `${filters.date_range[0]} ～ ${filters.date_range[1]}` : '発生日 全期間' }}
              </span>
              <span v-if="filters.report_category" class="toolbar-chip">
                <el-icon><Document /></el-icon>
                {{ filters.report_category }}
              </span>
              <span v-if="selectedRows.length" class="toolbar-chip">
                <el-icon><CircleCheckFilled /></el-icon>
                選択 {{ selectedRows.length }}件
              </span>
            </div>
          </div>
        </div>

        <div class="toolbar-actions">
          <button type="button" class="action-btn action-btn--print" :disabled="printing" @click="handlePrint">
            <el-icon v-if="printing" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Printer /></el-icon>
            <span>印刷</span>
          </button>
          <button type="button" class="action-btn action-btn--notify" @click="openNotifyDialog">
            <el-icon><Message /></el-icon>
            <span>未処理通知</span>
            <em v-if="pendingTotal > 0" class="action-badge">{{ pendingTotal > 99 ? '99+' : pendingTotal }}</em>
          </button>
          <button type="button" class="action-btn action-btn--primary" @click="openCreate">
            <el-icon><Plus /></el-icon>
            <span>新規登録</span>
          </button>
        </div>
      </header>

      <section
        class="kpi-grid animate-in"
        style="--delay: 40ms"
        @mousemove="handleKpiTilt"
        @mouseleave="resetKpiTilt"
      >
        <article class="kpi-card kpi-card--total">
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon"><el-icon :size="18"><Document /></el-icon></div>
            <span class="kpi-card__name">総件数</span>
          </header>
          <div class="kpi-card__value">{{ pagination.total.toLocaleString() }}</div>
          <p class="kpi-card__hint">現在の検索条件を含む一覧</p>
        </article>
        <article class="kpi-card kpi-card--pending">
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon"><el-icon :size="18"><WarningFilled /></el-icon></div>
            <span class="kpi-card__name">未処理</span>
          </header>
          <div class="kpi-card__value">{{ pendingTotal.toLocaleString() }}</div>
          <p class="kpi-card__hint">全体の未処理件数</p>
        </article>
        <article class="kpi-card kpi-card--overdue" :class="{ 'is-alert': overdueTotal > 0 }">
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon"><el-icon :size="18"><Timer /></el-icon></div>
            <span class="kpi-card__name">期限超過</span>
          </header>
          <div class="kpi-card__value">{{ overdueTotal.toLocaleString() }}</div>
          <p class="kpi-card__hint">保留品の処理期限超過</p>
        </article>
        <article class="kpi-card kpi-card--done">
          <div class="kpi-card__glow" aria-hidden="true" />
          <header class="kpi-card__head">
            <div class="kpi-icon"><el-icon :size="18"><CircleCheckFilled /></el-icon></div>
            <span class="kpi-card__name">処理済</span>
          </header>
          <div class="kpi-card__value">{{ processedTotal.toLocaleString() }}</div>
          <p class="kpi-card__hint">一覧上の処理済概算</p>
        </article>
      </section>

      <section class="panel panel-elevated filter-panel animate-in" style="--delay: 80ms">
        <div class="panel-head">
          <div class="panel-head-left">
            <span class="panel-accent panel-accent--amber" />
            <div>
              <h3 class="panel-title">検索・絞り込み</h3>
              <p class="panel-sub">区分チップと詳細条件で一覧を絞り込みます</p>
            </div>
          </div>
          <button
            v-if="hasActiveFilters"
            type="button"
            class="link-clear"
            @click="clearFilters"
          >
            条件クリア
          </button>
        </div>

        <div class="chip-row">
          <button
            v-for="chip in categoryChips"
            :key="chip.value"
            type="button"
            class="chip"
            :class="[`chip--cat-${chip.key}`, { 'chip--active': filters.report_category === chip.value }]"
            @click="toggleCategoryChip(chip.value)"
          >
            {{ chip.label }}
          </button>
          <span class="chip-divider" />
          <button
            type="button"
            class="chip chip--status-pending"
            :class="{ 'chip--active': filters.handling_status === '未処理' }"
            @click="toggleStatusChip('未処理')"
          >
            未処理
          </button>
          <button
            type="button"
            class="chip chip--status-done"
            :class="{ 'chip--active': filters.handling_status === '処理済' }"
            @click="toggleStatusChip('処理済')"
          >
            処理済
          </button>
          <button
            type="button"
            class="chip chip--overdue"
            :class="{ 'chip--active': showOverdueOnly }"
            @click="showOverdueOnly = !showOverdueOnly"
          >
            期限超過
          </button>
        </div>

        <el-form :model="filters" class="filter-form" label-position="top" @submit.prevent>
          <div class="filter-grid">
            <el-form-item label="発生日" class="filter-item span-2">
              <el-date-picker
                v-model="filters.date_range"
                type="daterange"
                range-separator="～"
                start-placeholder="開始"
                end-placeholder="終了"
                value-format="YYYY-MM-DD"
                unlink-panels
                size="default"
                class="ctrl-full"
              />
            </el-form-item>
            <el-form-item label="報告区分" class="filter-item">
              <el-select v-model="filters.report_category" clearable placeholder="全て" class="ctrl-full">
                <el-option v-for="item in reportCategoryOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="発生工程" class="filter-item">
              <el-select v-model="filters.process_name" clearable placeholder="全て" class="ctrl-full">
                <el-option v-for="item in processNameOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="製品" class="filter-item">
              <el-select
                v-model="filters.product_cd"
                placeholder="製品"
                clearable
                filterable
                class="ctrl-full"
              >
                <el-option
                  v-for="item in productOptions"
                  :key="item.product_cd"
                  :label="`${item.product_cd} - ${item.product_name || ''}`"
                  :value="item.product_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="キーワード" class="filter-item">
              <el-input
                v-model="filters.keyword"
                placeholder="製品名 / 管理No / 備考"
                clearable
                :prefix-icon="Search"
                class="ctrl-full"
              />
            </el-form-item>
          </div>
        </el-form>
      </section>

      <section class="panel panel-elevated table-panel animate-in" style="--delay: 120ms">
        <div class="panel-head">
          <div class="panel-head-left">
            <span class="panel-accent panel-accent--blue" />
            <div>
              <h3 class="panel-title">記録一覧</h3>
              <p class="panel-sub">
                {{ pagination.total.toLocaleString() }} 件
                <template v-if="selectedRows.length"> · 選択 {{ selectedRows.length }}</template>
              </p>
            </div>
          </div>
          <div class="panel-head-actions">
            <button type="button" class="action-btn action-btn--ghost action-btn--sm" :disabled="printing" @click="handlePrint">
              <el-icon v-if="printing" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Printer /></el-icon>
              <span>{{ selectedRows.length ? '選択を印刷' : '一覧を印刷' }}</span>
            </button>
          </div>
        </div>

        <div class="table-wrap" v-loading="loading">
          <el-table
            :data="recordList"
            size="small"
            stripe
            border
            class="bdr-table"
            :row-class-name="tableRowClassName"
            highlight-current-row
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="42" />
            <el-table-column prop="occurred_date" label="発生日" width="108" sortable>
              <template #default="{ row }">
                <span class="cell-date">{{ row.occurred_date }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="report_category" label="報告区分" width="100">
              <template #default="{ row }">
                <span class="pill" :class="`pill--cat-${categoryKey(row.report_category)}`">
                  {{ row.report_category }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="process_name" label="工程" width="80">
              <template #default="{ row }">
                <span class="pill pill--process" :class="`pill--proc-${processKey(row.process_name)}`">
                  {{ row.process_name }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="製品名" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="cell-product">{{ row.product_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="本数" width="80" align="right">
              <template #default="{ row }">
                <span class="cell-qty">{{ row.quantity?.toLocaleString() }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="handling_status" label="処理" width="88" align="center">
              <template #default="{ row }">
                <span class="pill" :class="row.handling_status === '処理済' ? 'pill--done' : 'pill--pending'">
                  {{ row.handling_status }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="processing_deadline_date" label="処理期限" width="108">
              <template #default="{ row }">
                <span
                  v-if="row.report_category === '保留品' && row.processing_deadline_date"
                  class="cell-deadline"
                  :class="{ 'cell-deadline--overdue': row.is_overdue }"
                >
                  {{ row.processing_deadline_date }}
                </span>
                <span v-else class="cell-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="processed_date" label="処理日" width="108">
              <template #default="{ row }">
                <span class="cell-muted">{{ row.processed_date || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="management_no" label="管理No" width="110" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="cell-mgmt">{{ row.management_no || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="備考" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="cell-muted">{{ row.remarks || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right" align="center">
              <template #default="{ row }">
                <div class="row-actions">
                  <el-button class="act-btn act-edit" link size="small" :icon="Edit" @click="openEdit(row)" />
                  <el-button class="act-btn act-del" link size="small" :icon="Delete" @click="handleDelete(row)" />
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            background
            size="small"
          />
        </div>
      </section>
    </div>

    <!-- 登録・編集 -->
    <el-dialog
      v-model="editDialogVisible"
      width="520px"
      destroy-on-close
      append-to-body
      align-center
      class="bdr-dialog bdr-dialog--edit"
      :show-close="true"
    >
      <template #header>
        <div class="dlg-header">
          <div class="dlg-header-icon" :class="editMode === 'create' ? 'dlg-header-icon--new' : 'dlg-header-icon--edit'">
            <el-icon :size="18"><component :is="editMode === 'create' ? Plus : Edit" /></el-icon>
          </div>
          <div class="dlg-header-text">
            <h3 class="dlg-title">{{ editMode === 'create' ? '新規登録' : '記録編集' }}</h3>
            <p class="dlg-subtitle">大量廃棄・保留品データ</p>
          </div>
          <span class="dlg-badge" :class="editMode === 'create' ? 'dlg-badge--new' : 'dlg-badge--edit'">
            {{ editMode === 'create' ? 'NEW' : 'EDIT' }}
          </span>
        </div>
      </template>

      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-position="top"
        size="small"
        class="edit-form"
        @submit.prevent
      >
        <div class="form-block form-block--basic">
          <div class="block-head">
            <el-icon><Calendar /></el-icon>
            <span>基本情報</span>
          </div>
          <div class="block-body block-body--3col">
            <el-form-item label="発生日" prop="occurred_date">
              <el-date-picker
                v-model="editForm.occurred_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="選択"
                class="ctrl-full"
              />
            </el-form-item>
            <el-form-item label="管理No" prop="management_no" class="mgmt-no-item">
              <el-input
                v-model="editForm.management_no"
                placeholder="13桁"
                class="mgmt-no-input"
                maxlength="13"
              />
            </el-form-item>
            <el-form-item label="発生本数" prop="quantity" class="qty-item">
              <el-input
                v-model="quantityDisplay"
                placeholder="0"
                class="qty-input"
                maxlength="5"
                inputmode="numeric"
              />
            </el-form-item>
          </div>
        </div>

        <div class="form-block form-block--category">
          <div class="block-head">
            <el-icon><WarningFilled /></el-icon>
            <span>報告区分</span>
          </div>
          <el-form-item prop="report_category" class="block-field-no-margin">
            <div class="pick-chip-row">
              <button
                v-for="item in reportCategoryOptions"
                :key="item"
                type="button"
                class="pick-chip"
                :class="[
                  `pick-chip--cat-${categoryKey(item)}`,
                  { 'pick-chip--active': editForm.report_category === item },
                ]"
                @click="selectReportCategory(item)"
              >
                {{ item }}
              </button>
            </div>
          </el-form-item>
        </div>

        <div
          v-if="editForm.report_category === '保留品'"
          class="form-block form-block--deadline"
        >
          <div class="block-head">
            <el-icon><Timer /></el-icon>
            <span>期間内処理期限</span>
            <span class="block-head-hint">未処理の保留品は必須</span>
          </div>
          <el-form-item prop="processing_deadline_date" class="block-field-no-margin deadline-field">
            <el-date-picker
              v-model="editForm.processing_deadline_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="期限日を選択"
              class="deadline-picker"
            />
          </el-form-item>
        </div>

        <div class="form-block form-block--process">
          <div class="block-head">
            <el-icon><SetUp /></el-icon>
            <span>発生工程</span>
          </div>
          <el-form-item prop="process_name" class="block-field-no-margin">
            <div class="pick-chip-row pick-chip-row--wrap">
              <button
                v-for="item in processNameOptions"
                :key="item"
                type="button"
                class="pick-chip pick-chip--sm"
                :class="[
                  `pick-chip--proc-${processKey(item)}`,
                  { 'pick-chip--active': editForm.process_name === item },
                ]"
                @click="editForm.process_name = item"
              >
                {{ item }}
              </button>
            </div>
          </el-form-item>
        </div>

        <div class="form-block form-block--product">
          <div class="block-head">
            <el-icon><Goods /></el-icon>
            <span>製品</span>
          </div>
          <el-form-item prop="product_cd" class="block-field-no-margin">
            <el-select
              v-model="editForm.product_cd"
              placeholder="製品を選択"
              filterable
              clearable
              class="ctrl-full"
              @change="handleProductChange"
            >
              <el-option
                v-for="item in productOptions"
                :key="item.product_cd"
                :label="`${item.product_cd} - ${item.product_name || ''}`"
                :value="item.product_cd"
              />
            </el-select>
          </el-form-item>
        </div>

        <div
          class="form-block form-block--status"
          :class="editForm.handling_status === '処理済' ? 'form-block--done' : 'form-block--pending'"
        >
          <div class="block-head">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>処理状態</span>
          </div>
          <div class="block-body block-body--status">
            <el-form-item prop="handling_status" class="block-field-no-margin status-field">
              <div class="pick-chip-row">
                <button
                  type="button"
                  class="pick-chip pick-chip--status-pending"
                  :class="{ 'pick-chip--active': editForm.handling_status === '未処理' }"
                  @click="setHandlingStatus('未処理')"
                >
                  未処理
                </button>
                <button
                  type="button"
                  class="pick-chip pick-chip--status-done"
                  :class="{ 'pick-chip--active': editForm.handling_status === '処理済' }"
                  @click="setHandlingStatus('処理済')"
                >
                  処理済
                </button>
              </div>
            </el-form-item>
            <el-form-item label="処理日付" prop="processed_date" class="processed-date-field">
              <el-date-picker
                v-model="editForm.processed_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="処理日"
                class="ctrl-full"
                :disabled="editForm.handling_status !== '処理済'"
              />
            </el-form-item>
          </div>
        </div>

        <div class="form-block form-block--remarks">
          <div class="block-head">
            <el-icon><EditPen /></el-icon>
            <span>備考</span>
          </div>
          <el-form-item prop="remarks" class="block-field-no-margin">
            <el-input v-model="editForm.remarks" type="textarea" :rows="2" placeholder="備考（任意）" resize="none" />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="dlg-footer">
          <el-button class="dlg-btn dlg-btn--cancel" @click="editDialogVisible = false">キャンセル</el-button>
          <el-button class="dlg-btn dlg-btn--save" type="primary" :loading="editLoading" @click="handleSave">
            <el-icon v-if="!editLoading"><CircleCheckFilled /></el-icon>
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- メール通知 -->
    <el-dialog
      v-model="notifyDialogVisible"
      title="未処理データ メール通知"
      width="860px"
      destroy-on-close
      append-to-body
      align-center
      class="bdr-dialog bdr-dialog--notify"
    >
      <div v-loading="notifyLoading" class="notify-body">
        <div v-if="notifyPreview" class="notify-hero" :class="{ 'notify-hero--warn': !notifyPreview.can_send }">
          <div class="notify-hero-stat">
            <span class="notify-hero-num">{{ notifyPreview.item_count }}</span>
            <span class="notify-hero-unit">件</span>
          </div>
          <div class="notify-hero-meta">
            <p>合計 <strong>{{ notifyPreview.total_quantity }}</strong> 本の未処理データ</p>
            <p
              v-if="notifyPreview.overdue_count && notifyPreview.overdue_count > 0"
              class="notify-deadline-warn"
            >
              ⚠ 処理期限超過 <strong>{{ notifyPreview.overdue_count }}</strong> 件 — メールに重要提醒として記載されます
            </p>
            <p class="notify-hint">
              {{ selectedRows.length > 0 ? '※ 選択中の未処理行のみ通知' : '※ 全未処理データを通知' }}
            </p>
          </div>
        </div>
        <el-alert
          v-if="notifyPreview?.overdue_count && notifyPreview.overdue_count > 0"
          type="error"
          :closable="false"
          show-icon
          class="notify-alert notify-alert--deadline"
        >
          <template #title>
            重要：処理期限超過の保留品が {{ notifyPreview.overdue_count }} 件含まれます
          </template>
          <p class="notify-deadline-detail">
            送信メールには処理期限を強調表示し、至急対応の提醒を自動挿入します。
          </p>
        </el-alert>
        <el-alert
          v-if="notifyPreview && !notifyPreview.can_send"
          type="warning"
          :closable="false"
          show-icon
          title="送信条件を満たしていません（未処理データ・SMTP・テンプレートを確認）"
          class="notify-alert"
        />
        <el-form label-width="100px" size="default" class="notify-form">
          <el-form-item label="通知先" required>
            <div class="notify-recipient-field">
              <el-select
                v-model="notifyUserIds"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="ユーザーを選択"
                class="full-width"
              >
                <el-option
                  v-for="u in notifyUsers"
                  :key="u.id"
                  :label="`${u.full_name || u.username} (${u.email || 'メール未設定'})`"
                  :value="u.id"
                  :disabled="!u.email"
                />
              </el-select>
              <div class="notify-recipient-actions">
                <span
                  class="notify-saved-hint"
                  :class="{ 'notify-saved-hint--dirty': notifyRecipientsDirty }"
                >
                  <template v-if="notifyRecipientsDirty">※ 通知先に未保存の変更があります</template>
                  <template v-else-if="savedNotifyUserIds.length > 0">
                    保存済み通知先 {{ savedNotifyUserIds.length }} 名
                  </template>
                  <template v-else>通知先は未保存です（保存すると次回から自動で選択されます）</template>
                </span>
                <el-button
                  v-if="notifyRecipientsDirty && savedNotifyUserIds.length > 0"
                  link
                  type="info"
                  size="small"
                  @click="notifyUserIds = [...savedNotifyUserIds]"
                >
                  保存済みに戻す
                </el-button>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :loading="notifySavingRecipients"
                  :disabled="!notifyRecipientsDirty"
                  @click="handleSaveNotifyRecipients"
                >
                  通知先を保存
                </el-button>
              </div>
            </div>
          </el-form-item>
        </el-form>
        <el-table
          v-if="notifyPreview?.items?.length"
          :data="notifyPreview.items"
          size="small"
          max-height="200"
          class="notify-table"
        >
          <el-table-column prop="occurred_date" label="発生日" width="96" />
          <el-table-column prop="report_category" label="区分" width="84" />
          <el-table-column prop="process_name" label="工程" width="72" />
          <el-table-column prop="product_name" label="製品名" min-width="100" show-overflow-tooltip />
          <el-table-column prop="quantity" label="本数" width="64" align="right" />
          <el-table-column prop="processing_deadline_date" label="処理期限" width="108" align="center">
            <template #default="{ row }">
              <span
                v-if="row.report_category === '保留品' && row.processing_deadline_date"
                class="cell-deadline"
                :class="{ 'cell-deadline--overdue': row.is_overdue }"
              >
                <template v-if="row.is_overdue">⚠ </template>{{ row.processing_deadline_date }}
              </span>
              <span v-else class="cell-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="cell-muted">{{ row.remarks || '—' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="notifyDialogVisible = false">キャンセル</el-button>
        <el-button
          type="warning"
          :loading="notifySending"
          :disabled="!notifyPreview?.can_send || notifyUserIds.length === 0"
          @click="handleSendNotify"
        >
          送信
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Delete,
  Edit,
  Document,
  Search,
  Plus,
  Message,
  WarningFilled,
  CircleCheckFilled,
  Calendar,
  SetUp,
  Goods,
  EditPen,
  Timer,
  Printer,
  Loading,
} from '@element-plus/icons-vue'
import { getProductList } from '@/api/master/productMaster'
import { getUsers, type UserListItem } from '@/api/system'
import {
  getBulkDisposalRetentionList,
  getBulkDisposalRetentionOptions,
  createBulkDisposalRetention,
  updateBulkDisposalRetention,
  deleteBulkDisposalRetention,
  previewBulkDisposalRetentionNotification,
  saveBulkDisposalRetentionNotifyRecipients,
  sendBulkDisposalRetentionNotification,
  type BulkDisposalRetentionRecord,
  type BulkDisposalRetentionForm,
  type BulkDisposalRetentionNotifyPreview,
} from '@/api/erp/bulkDisposalRetention'
import {
  buildPrintHtmlDocument,
  escapeHtml,
  openPrintWindow,
  PRINT_POPUP_BLOCKED_MSG,
} from '@/utils/printWindow'

const route = useRoute()

const reportCategoryOptions = ref<string[]>(['大量廃棄', '大量不良', '保留品', '在庫消滅', 'その他'])
const processNameOptions = ref<string[]>(['切断', '面取', '成型', 'メッキ', '溶接', '検査', 'その他'])
const handlingStatusOptions = ref<string[]>(['未処理', '処理済'])
const productOptions = ref<Array<{ product_cd: string; product_name?: string }>>([])

const categoryChips = [
  { label: '大量廃棄', value: '大量廃棄', key: 'disposal' },
  { label: '大量不良', value: '大量不良', key: 'defect' },
  { label: '保留品', value: '保留品', key: 'hold' },
  { label: '在庫消滅', value: '在庫消滅', key: 'vanish' },
  { label: 'その他', value: 'その他', key: 'other' },
]

const loading = ref(false)
const printing = ref(false)
const editLoading = ref(false)
const recordList = ref<BulkDisposalRetentionRecord[]>([])
const selectedRows = ref<BulkDisposalRetentionRecord[]>([])
const pendingTotal = ref(0)
const overdueTotal = ref(0)
const showOverdueOnly = ref(false)

const filters = reactive({
  date_range: null as [string, string] | null,
  report_category: '',
  process_name: '',
  handling_status: '',
  product_cd: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const processedTotal = computed(() => Math.max(0, pagination.total - pendingTotal.value))

const hasActiveFilters = computed(
  () =>
    !!filters.date_range ||
    !!filters.report_category ||
    !!filters.process_name ||
    !!filters.handling_status ||
    !!filters.product_cd ||
    !!filters.keyword ||
    showOverdueOnly.value
)

const editDialogVisible = ref(false)
const editMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const editFormRef = ref<FormInstance>()

const defaultForm = (): BulkDisposalRetentionForm => ({
  occurred_date: dayjs().format('YYYY-MM-DD'),
  report_category: '大量廃棄',
  process_name: '切断',
  product_cd: '',
  product_name: '',
  quantity: 0,
  handling_status: '未処理',
  processed_date: null,
  processing_deadline_date: null,
  management_no: '',
  remarks: '',
})

const editForm = reactive<BulkDisposalRetentionForm>(defaultForm())

const quantityDisplay = computed({
  get: () => String(editForm.quantity ?? 0),
  set: (val: string) => {
    const digits = val.replace(/\D/g, '').slice(0, 5)
    editForm.quantity = digits === '' ? 0 : parseInt(digits, 10)
  },
})

const editRules: FormRules = {
  occurred_date: [{ required: true, message: '発生日を選択してください', trigger: 'change' }],
  report_category: [{ required: true, message: '報告区分を選択してください', trigger: 'change' }],
  process_name: [{ required: true, message: '発生工程を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  quantity: [
    { required: true, message: '発生本数を入力してください', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const n = Number(value)
        if (!Number.isFinite(n) || n < 0) {
          callback(new Error('0以上の数値を入力してください'))
        } else if (n > 99999) {
          callback(new Error('5桁以内で入力してください'))
        } else if (editForm.report_category === '大量不良' && n <= 200) {
          callback(new Error('大量不良の場合、発生本数は200より大きい値にしてください'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  handling_status: [{ required: true, message: '処理を選択してください', trigger: 'change' }],
  processing_deadline_date: [
    {
      validator: (_rule, value, callback) => {
        if (editForm.report_category === '保留品' && editForm.handling_status === '未処理') {
          if (!value) {
            callback(new Error('期間内処理期限を入力してください'))
            return
          }
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

const notifyDialogVisible = ref(false)
const notifyLoading = ref(false)
const notifySending = ref(false)
const notifyPreview = ref<BulkDisposalRetentionNotifyPreview | null>(null)
const notifyUsers = ref<UserListItem[]>([])
const notifyUserIds = ref<number[]>([])
const savedNotifyUserIds = ref<number[]>([])
const notifySavingRecipients = ref(false)
const notifyRecipientsDirty = computed(() => {
  const current = [...new Set(notifyUserIds.value)].sort((a, b) => a - b)
  const saved = [...new Set(savedNotifyUserIds.value)].sort((a, b) => a - b)
  return current.length !== saved.length || current.some((id, i) => id !== saved[i])
})

function categoryKey(cat: string) {
  if (cat === '大量廃棄') return 'disposal'
  if (cat === '大量不良') return 'defect'
  if (cat === '保留品') return 'hold'
  if (cat === '在庫消滅') return 'vanish'
  return 'other'
}

function processKey(proc: string) {
  const map: Record<string, string> = {
    切断: 'cut',
    面取: 'chamfer',
    成型: 'form',
    メッキ: 'plate',
    溶接: 'weld',
    検査: 'inspect',
    その他: 'other',
  }
  return map[proc] || 'other'
}

// KPIカードの3Dチルト（マウス追従）
function handleKpiTilt(e: MouseEvent) {
  const card = (e.target as HTMLElement | null)?.closest<HTMLElement>('.kpi-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.kpi-card').forEach((el) => {
    if (el !== card) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!card) return
  const rect = card.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  card.style.setProperty('--rx', `${((0.5 - py) * 12).toFixed(2)}deg`)
  card.style.setProperty('--ry', `${((px - 0.5) * 12).toFixed(2)}deg`)
  card.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  card.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetKpiTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.kpi-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

function tableRowClassName({ row }: { row: BulkDisposalRetentionRecord }) {
  if (row.is_overdue) return 'row-overdue'
  if (row.handling_status === '未処理') return 'row-pending'
  return ''
}

function selectReportCategory(item: string) {
  editForm.report_category = item
  if (item !== '保留品') {
    editForm.processing_deadline_date = null
  }
}

function toggleCategoryChip(value: string) {
  filters.report_category = filters.report_category === value ? '' : value
}

function toggleStatusChip(value: string) {
  filters.handling_status = filters.handling_status === value ? '' : value
}

function clearFilters() {
  filters.date_range = null
  filters.report_category = ''
  filters.process_name = ''
  filters.handling_status = ''
  filters.product_cd = ''
  filters.keyword = ''
  showOverdueOnly.value = false
}

function handleProductChange(cd: string) {
  const found = productOptions.value.find((p) => p.product_cd === cd)
  editForm.product_name = found?.product_name || ''
}

function handleHandlingStatusChange(status: string | number | boolean | undefined) {
  if (status === '処理済' && !editForm.processed_date) {
    editForm.processed_date = dayjs().format('YYYY-MM-DD')
  }
  if (status === '未処理') {
    editForm.processed_date = null
  }
}

function setHandlingStatus(status: '未処理' | '処理済') {
  editForm.handling_status = status
  handleHandlingStatusChange(status)
}

function handleSelectionChange(rows: BulkDisposalRetentionRecord[]) {
  selectedRows.value = rows
}

function buildListParams(extra?: Record<string, unknown>) {
  const params: Record<string, unknown> = {
    page: pagination.page,
    page_size: pagination.pageSize,
    ...extra,
  }
  if (filters.date_range?.[0]) params.occurred_date_from = filters.date_range[0]
  if (filters.date_range?.[1]) params.occurred_date_to = filters.date_range[1]
  if (filters.report_category) params.report_category = filters.report_category
  if (filters.process_name) params.process_name = filters.process_name
  if (filters.handling_status) params.handling_status = filters.handling_status
  if (filters.product_cd) params.product_cd = filters.product_cd
  if (filters.keyword) params.keyword = filters.keyword
  if (showOverdueOnly.value) params.overdue_only = true
  return params
}

function filterSummaryLabel() {
  const parts: string[] = []
  if (filters.date_range?.[0] && filters.date_range?.[1]) {
    parts.push(`発生日 ${filters.date_range[0]}～${filters.date_range[1]}`)
  }
  if (filters.report_category) parts.push(`区分 ${filters.report_category}`)
  if (filters.process_name) parts.push(`工程 ${filters.process_name}`)
  if (filters.handling_status) parts.push(filters.handling_status)
  if (filters.product_cd) parts.push(`製品 ${filters.product_cd}`)
  if (filters.keyword) parts.push(`KW ${filters.keyword}`)
  if (showOverdueOnly.value) parts.push('期限超過のみ')
  return parts.length ? parts.join(' / ') : '全件（条件なし）'
}

async function fetchPrintRows(): Promise<{ rows: BulkDisposalRetentionRecord[]; scopeLabel: string }> {
  if (selectedRows.value.length > 0) {
    return { rows: [...selectedRows.value], scopeLabel: `選択 ${selectedRows.value.length} 件` }
  }

  const all: BulkDisposalRetentionRecord[] = []
  let page = 1
  const pageSize = 200
  let total = Infinity
  while (all.length < total && page <= 20) {
    const res = await getBulkDisposalRetentionList(buildListParams({ page, page_size: pageSize }))
    const list = res?.list ?? []
    total = res?.total ?? list.length
    all.push(...list)
    if (list.length < pageSize) break
    page += 1
  }
  return { rows: all, scopeLabel: `検索結果 ${all.length} 件` }
}

function buildPrintHtml(rows: BulkDisposalRetentionRecord[], scopeLabel: string) {
  const totalQty = rows.reduce((sum, r) => sum + (Number(r.quantity) || 0), 0)
  const pendingCount = rows.filter((r) => r.handling_status === '未処理').length
  const overdueCount = rows.filter((r) => r.is_overdue).length
  const printedAt = new Date().toLocaleString('ja-JP')

  const bodyRows = rows
    .map((r, i) => {
      const overdue = r.is_overdue ? ' class="overdue"' : ''
      const deadline =
        r.report_category === '保留品' && r.processing_deadline_date
          ? escapeHtml(r.processing_deadline_date)
          : '—'
      return `<tr${overdue}>
        <td class="c">${i + 1}</td>
        <td class="c">${escapeHtml(r.occurred_date || '')}</td>
        <td class="c">${escapeHtml(r.report_category || '')}</td>
        <td class="c">${escapeHtml(r.process_name || '')}</td>
        <td>${escapeHtml(r.product_name || '')}</td>
        <td class="r">${Number(r.quantity || 0).toLocaleString('ja-JP')}</td>
        <td class="c">${escapeHtml(r.handling_status || '')}</td>
        <td class="c">${deadline}</td>
        <td class="c">${escapeHtml(r.processed_date || '—')}</td>
        <td class="c mono">${escapeHtml(r.management_no || '—')}</td>
        <td>${escapeHtml(r.remarks || '—')}</td>
      </tr>`
    })
    .join('')

  const styles = `
    @page { size: A4 landscape; margin: 12mm; }
    * { box-sizing: border-box; }
    body { font-family: "Yu Gothic UI", "Meiryo", sans-serif; color: #0f172a; margin: 0; font-size: 11px; }
    h1 { margin: 0 0 4px; font-size: 18px; letter-spacing: -0.02em; }
    .meta { color: #64748b; margin-bottom: 10px; line-height: 1.5; }
    .kpis { display: flex; gap: 10px; margin-bottom: 12px; }
    .kpi { flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; background: #f8fafc; }
    .kpi strong { display: block; font-size: 16px; margin-top: 2px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #cbd5e1; padding: 4px 6px; vertical-align: top; }
    th { background: #f1f5f9; font-size: 10px; white-space: nowrap; }
    td.c { text-align: center; } td.r { text-align: right; font-variant-numeric: tabular-nums; }
    td.mono { font-family: Consolas, monospace; font-size: 10px; }
    tr.overdue td { background: #fef2f2; }
    .foot { margin-top: 8px; color: #64748b; font-size: 10px; }
  `

  const body = `
    <h1>大量廃棄・保留品管理 一覧</h1>
    <div class="meta">
      印刷範囲：${escapeHtml(scopeLabel)}　／　条件：${escapeHtml(filterSummaryLabel())}<br>
      印刷日時：${escapeHtml(printedAt)}
    </div>
    <div class="kpis">
      <div class="kpi">件数<strong>${rows.length.toLocaleString('ja-JP')}</strong></div>
      <div class="kpi">合計本数<strong>${totalQty.toLocaleString('ja-JP')}</strong></div>
      <div class="kpi">未処理<strong>${pendingCount.toLocaleString('ja-JP')}</strong></div>
      <div class="kpi">期限超過<strong>${overdueCount.toLocaleString('ja-JP')}</strong></div>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th><th>発生日</th><th>報告区分</th><th>工程</th><th>製品名</th>
          <th>本数</th><th>処理</th><th>処理期限</th><th>処理日</th><th>管理No</th><th>備考</th>
        </tr>
      </thead>
      <tbody>${bodyRows || '<tr><td colspan="11" class="c">データなし</td></tr>'}</tbody>
    </table>
    <div class="foot">Smart-EMAP · 大量廃棄・保留品管理</div>
  `

  return buildPrintHtmlDocument('大量廃棄・保留品管理 一覧', styles, body)
}

async function handlePrint() {
  if (printing.value) return
  printing.value = true
  try {
    const { rows, scopeLabel } = await fetchPrintRows()
    if (!rows.length) {
      ElMessage.warning('印刷対象のデータがありません')
      return
    }
    const html = buildPrintHtml(rows, scopeLabel)
    const ok = openPrintWindow(html)
    if (!ok) ElMessage.warning(PRINT_POPUP_BLOCKED_MSG)
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '印刷の準備に失敗しました')
  } finally {
    printing.value = false
  }
}

async function loadOptions() {
  try {
    const res = await getBulkDisposalRetentionOptions()
    if (res?.report_categories?.length) reportCategoryOptions.value = res.report_categories
    if (res?.process_names?.length) processNameOptions.value = res.process_names
    if (res?.handling_statuses?.length) handlingStatusOptions.value = res.handling_statuses
  } catch {
    // fallback
  }
}

async function loadProducts() {
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = list
      .filter((p) => p.product_cd)
      .map((p) => ({ product_cd: p.product_cd, product_name: p.product_name }))
  } catch {
    productOptions.value = []
  }
}

async function loadRecords() {
  loading.value = true
  try {
    const res = await getBulkDisposalRetentionList(buildListParams())
    recordList.value = res?.list ?? []
    pagination.total = res?.total ?? 0
    pendingTotal.value = res?.pending_total ?? 0
    overdueTotal.value = res?.overdue_total ?? 0
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'データ取得に失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editMode.value = 'create'
  editingId.value = null
  Object.assign(editForm, defaultForm())
  editDialogVisible.value = true
}

function openEdit(row: BulkDisposalRetentionRecord) {
  editMode.value = 'edit'
  editingId.value = row.id
  Object.assign(editForm, {
    occurred_date: row.occurred_date,
    report_category: row.report_category,
    process_name: row.process_name,
    product_cd: row.product_cd || '',
    product_name: row.product_name,
    quantity: row.quantity,
    handling_status: row.handling_status,
    processed_date: row.processed_date,
    processing_deadline_date: row.processing_deadline_date,
    management_no: row.management_no || '',
    remarks: row.remarks || '',
  })
  editDialogVisible.value = true
}

async function handleSave() {
  if (!editFormRef.value) return
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  if (!editForm.product_name) handleProductChange(editForm.product_cd || '')

  editLoading.value = true
  try {
    const payload = { ...editForm }
    if (editMode.value === 'create') {
      await createBulkDisposalRetention(payload)
      ElMessage.success('登録しました')
    } else if (editingId.value) {
      await updateBulkDisposalRetention(editingId.value, payload)
      ElMessage.success('更新しました')
    }
    editDialogVisible.value = false
    await loadRecords()
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '保存に失敗しました')
  } finally {
    editLoading.value = false
  }
}

async function handleDelete(row: BulkDisposalRetentionRecord) {
  try {
    await ElMessageBox.confirm(`管理No: ${row.management_no || row.id} を削除しますか？`, '確認', { type: 'warning' })
    await deleteBulkDisposalRetention(row.id)
    ElMessage.success('削除しました')
    await loadRecords()
  } catch {
    // cancelled
  }
}

async function loadNotifyUsers() {
  try {
    const res = await getUsers({ page: 1, page_size: 500, status: 'active' })
    notifyUsers.value = res?.items ?? []
  } catch {
    notifyUsers.value = []
  }
}

async function loadNotifyPreview() {
  notifyLoading.value = true
  try {
    const pendingSelected = selectedRows.value.filter((r) => r.handling_status === '未処理')
    const recordIds = pendingSelected.length > 0 ? pendingSelected.map((r) => r.id).join(',') : undefined
    notifyPreview.value = await previewBulkDisposalRetentionNotification(
      recordIds ? { record_ids: recordIds } : undefined
    )
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : 'プレビュー取得に失敗しました')
    notifyPreview.value = null
  } finally {
    notifyLoading.value = false
  }
}

function selectableNotifyUserIds(ids: number[]) {
  const selectable = new Set(notifyUsers.value.filter((u) => u.email).map((u) => u.id))
  return ids.filter((id) => selectable.has(id))
}

async function openNotifyDialog() {
  notifyUserIds.value = []
  savedNotifyUserIds.value = []
  notifyDialogVisible.value = true
  await Promise.all([loadNotifyUsers(), loadNotifyPreview()])
  savedNotifyUserIds.value = selectableNotifyUserIds(notifyPreview.value?.saved_user_ids ?? [])
  notifyUserIds.value = [...savedNotifyUserIds.value]
}

async function handleSaveNotifyRecipients() {
  notifySavingRecipients.value = true
  try {
    const res = await saveBulkDisposalRetentionNotifyRecipients(notifyUserIds.value)
    savedNotifyUserIds.value = selectableNotifyUserIds(res?.user_ids ?? [])
    ElMessage.success(res?.message || '通知先を保存しました')
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '通知先の保存に失敗しました')
  } finally {
    notifySavingRecipients.value = false
  }
}

async function handleSendNotify() {
  if (notifyUserIds.value.length === 0) {
    ElMessage.warning('通知先ユーザーを選択してください')
    return
  }
  notifySending.value = true
  try {
    const pendingSelected = selectedRows.value.filter((r) => r.handling_status === '未処理')
    const recordIds = pendingSelected.length > 0 ? pendingSelected.map((r) => r.id) : undefined
    const res = await sendBulkDisposalRetentionNotification({
      user_ids: notifyUserIds.value,
      record_ids: recordIds,
    })
    if (!res?.success) {
      ElMessage.error(res?.message || '送信に失敗しました')
      return
    }
    ElMessage.success(res.message || '送信しました')
    notifyDialogVisible.value = false
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '送信に失敗しました')
  } finally {
    notifySending.value = false
  }
}

watch(
  () => [
    filters.date_range,
    filters.report_category,
    filters.process_name,
    filters.handling_status,
    filters.product_cd,
    filters.keyword,
  ],
  () => {
    pagination.page = 1
    loadRecords()
  }
)

watch(() => [pagination.page, pagination.pageSize, showOverdueOnly.value], () => loadRecords())

onMounted(async () => {
  if (route.query.overdue === '1') {
    showOverdueOnly.value = true
    filters.report_category = '保留品'
    filters.handling_status = '未処理'
  }
  await Promise.all([loadOptions(), loadProducts()])
  await loadRecords()
})
</script>

<style scoped lang="scss">
.bdr-page {
  --bdr-rose: #e11d48;
  --bdr-amber: #d97706;
  --bdr-blue: #2563eb;
  --bdr-emerald: #059669;
  --bdr-cyan: #0891b2;
  --bdr-violet: #7c3aed;
  --radius-lg: 16px;
  --radius-md: 12px;
  --radius-sm: 9px;
  --shadow-soft: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.08),
    0 2px 8px rgba(15, 23, 42, 0.04);
  position: relative;
  min-height: 100%;
  padding: 14px 16px 22px;
  box-sizing: border-box;
  overflow: hidden;
  color: #0f172a;
  font-size: 0.875rem;
  line-height: 1.45;
}

.page-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(155deg, #eef4ff 0%, #f7f9fc 38%, #fff8f1 100%);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.42;
  animation: orb-float 18s ease-in-out infinite;
}

.orb-a {
  width: 380px;
  height: 380px;
  top: -120px;
  right: 6%;
  background: radial-gradient(circle, #fda4af 0%, transparent 70%);
}
.orb-b {
  width: 300px;
  height: 300px;
  bottom: 6%;
  left: -70px;
  background: radial-gradient(circle, #fdba74 0%, transparent 70%);
  animation-delay: -6s;
}
.orb-c {
  width: 240px;
  height: 240px;
  top: 46%;
  right: 22%;
  background: radial-gradient(circle, #93c5fd 0%, transparent 70%);
  animation-delay: -11s;
}

@keyframes orb-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(12px, -14px) scale(1.05);
  }
}

.bdr-inner {
  position: relative;
  z-index: 1;
  max-width: 1480px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.animate-in {
  animation: fade-up 0.48s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  min-height: 64px;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
}

.toolbar-elevated {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.94) 100%);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: var(--shadow-soft);
}

.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  box-shadow: 0 8px 18px rgba(239, 68, 68, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.toolbar-title {
  margin: 0;
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.2;
}

.toolbar-sub {
  margin: 2px 0 0;
  font-size: 0.75rem;
  color: #64748b;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 10px;
  font-size: 0.8125rem;
  font-weight: 750;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}
.action-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.action-btn--primary {
  color: #fff;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.28);
}
.action-btn--notify {
  color: #92400e;
  background: linear-gradient(180deg, #fffbeb, #fef3c7);
  border: 1px solid rgba(245, 158, 11, 0.35);
}
.action-btn--print {
  color: #5b21b6;
  background: linear-gradient(180deg, #f5f3ff, #ede9fe);
  border: 1px solid rgba(124, 58, 237, 0.28);
}
.action-btn--ghost {
  color: #334155;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.action-btn--sm {
  padding: 6px 12px;
  font-size: 0.75rem;
  border-radius: 8px;
}

.action-badge {
  position: absolute;
  top: -7px;
  right: -7px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 10px;
  font-weight: 800;
  font-style: normal;
  line-height: 18px;
  text-align: center;
  color: #fff;
  background: #ef4444;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.45);
}

.action-btn .is-loading {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* KPI */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-md);
  padding: 14px 16px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  border: 1px solid rgba(226, 232, 240, 0.98);
  box-shadow: var(--shadow-soft);
}

.kpi-card__glow {
  position: absolute;
  width: 120px;
  height: 120px;
  right: -30px;
  top: -40px;
  border-radius: 50%;
  filter: blur(28px);
  opacity: 0.35;
  pointer-events: none;
}

.kpi-card--total .kpi-card__glow {
  background: #93c5fd;
}
.kpi-card--pending .kpi-card__glow {
  background: #fcd34d;
}
.kpi-card--overdue .kpi-card__glow {
  background: #fda4af;
}
.kpi-card--done .kpi-card__glow {
  background: #6ee7b7;
}

.kpi-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.kpi-icon {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.kpi-card--total .kpi-icon {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}
.kpi-card--pending .kpi-icon {
  background: linear-gradient(135deg, #fbbf24, #d97706);
}
.kpi-card--overdue .kpi-icon {
  background: linear-gradient(135deg, #fb7185, #e11d48);
}
.kpi-card--done .kpi-icon {
  background: linear-gradient(135deg, #34d399, #059669);
}

.kpi-card__name {
  font-size: 0.75rem;
  font-weight: 750;
  color: #64748b;
}

.kpi-card__value {
  font-size: 1.65rem;
  font-weight: 850;
  letter-spacing: -0.03em;
  color: #0f172a;
  line-height: 1.1;
}

.kpi-card__hint {
  margin: 6px 0 0;
  font-size: 0.7rem;
  color: #94a3b8;
}

/* Panels */
.panel {
  border-radius: var(--radius-lg);
  padding: 12px 14px 14px;
}

.panel-elevated {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.96) 100%);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: var(--shadow-soft);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.panel-head-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
}

.panel-accent {
  width: 4px;
  height: 28px;
  border-radius: 99px;
  margin-top: 2px;
  flex-shrink: 0;
}
.panel-accent--amber {
  background: linear-gradient(180deg, #fbbf24, #f59e0b);
}
.panel-accent--blue {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}

.panel-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
}
.panel-sub {
  margin: 2px 0 0;
  font-size: 0.72rem;
  color: #64748b;
}

.panel-head-actions {
  display: flex;
  gap: 8px;
}

.link-clear {
  border: none;
  background: transparent;
  color: #2563eb;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  padding: 4px 6px;
}
.link-clear:hover {
  text-decoration: underline;
}

/* Chips */
.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.chip {
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 750;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;
}
.chip:hover {
  border-color: #cbd5e1;
  color: #334155;
}
.chip--active {
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.14);
}

.chip--cat-disposal.chip--active {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}
.chip--cat-defect.chip--active {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
}
.chip--cat-hold.chip--active {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}
.chip--cat-vanish.chip--active {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}
.chip--cat-other.chip--active {
  background: linear-gradient(135deg, #64748b, #475569);
}
.chip--status-pending.chip--active {
  background: linear-gradient(135deg, #f59e0b, #ea580c);
}
.chip--status-done.chip--active {
  background: linear-gradient(135deg, #10b981, #059669);
}
.chip--overdue.chip--active {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.chip-divider {
  width: 1px;
  height: 20px;
  background: #e2e8f0;
  margin: 0 2px;
  align-self: center;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}
.filter-form :deep(.el-form-item__label) {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 700;
  padding-bottom: 2px;
  line-height: 1.2;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px 10px;
}
.filter-item.span-2 {
  grid-column: span 2;
}
.ctrl-full {
  width: 100%;
}

/* Table */
.table-wrap {
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.98);
  background: #fff;
}

.bdr-table {
  --el-table-border-color: #e2e8f0;
  --el-table-header-bg-color: #f8fafc;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #eff6ff;
  --el-table-current-row-bg-color: #dbeafe;
  --el-table-text-color: #1e293b;
  --el-table-header-text-color: #475569;
}

.bdr-table :deep(th.el-table__cell) {
  font-size: 11px;
  font-weight: 750;
  padding: 8px 0;
  background: #f8fafc !important;
}
.bdr-table :deep(td.el-table__cell) {
  padding: 7px 0;
  font-size: 12px;
}
.bdr-table :deep(.row-pending td.el-table__cell) {
  background: #fffbeb !important;
}
.bdr-table :deep(.row-overdue td.el-table__cell) {
  background: #fef2f2 !important;
}

.cell-date {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.cell-product {
  font-weight: 600;
}
.cell-qty {
  font-weight: 800;
  color: #b45309;
  font-variant-numeric: tabular-nums;
}
.cell-mgmt {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: #475569;
}
.cell-deadline {
  font-weight: 700;
  color: #b45309;
}
.cell-deadline--overdue {
  color: #dc2626;
  font-weight: 850;
}
.cell-muted {
  color: #94a3b8;
  font-size: 11px;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 750;
  white-space: nowrap;
}
.pill--cat-disposal {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.pill--cat-defect {
  background: #f5f3ff;
  color: #6d28d9;
  border: 1px solid #ddd6fe;
}
.pill--cat-hold {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fde68a;
}
.pill--cat-vanish {
  background: #ecfeff;
  color: #0891b2;
  border: 1px solid #a5f3fc;
}
.pill--cat-other {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}
.pill--process {
  border: 1px solid transparent;
}
.pill--proc-cut {
  background: #eff6ff;
  color: #2563eb;
}
.pill--proc-chamfer {
  background: #ecfeff;
  color: #0891b2;
}
.pill--proc-form {
  background: #f5f3ff;
  color: #7c3aed;
}
.pill--proc-plate {
  background: #fdf2f8;
  color: #db2777;
}
.pill--proc-weld {
  background: #fff7ed;
  color: #ea580c;
}
.pill--proc-inspect {
  background: #ecfdf5;
  color: #059669;
}
.pill--proc-other {
  background: #f1f5f9;
  color: #64748b;
}
.pill--pending {
  background: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
}
.pill--done {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.row-actions {
  display: inline-flex;
  gap: 2px;
}
.act-edit {
  color: #2563eb !important;
}
.act-del {
  color: #e11d48 !important;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* Edit form blocks (dialog content) */
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-block {
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
}
.form-block--basic {
  border-left: 3px solid #3b82f6;
}
.form-block--category {
  border-left: 3px solid #ef4444;
}
.form-block--process {
  border-left: 3px solid #8b5cf6;
}
.form-block--product {
  border-left: 3px solid #0ea5e9;
}
.form-block--pending {
  border-left: 3px solid #f59e0b;
  background: linear-gradient(135deg, #fff 0%, #fffbeb 100%);
}
.form-block--done {
  border-left: 3px solid #10b981;
  background: linear-gradient(135deg, #fff 0%, #ecfdf5 100%);
}
.form-block--remarks {
  border-left: 3px solid #94a3b8;
}
.form-block--deadline {
  border-left: 3px solid #f97316;
  background: linear-gradient(135deg, #fff 0%, #fff7ed 100%);
}

.block-head {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 800;
  color: #334155;
}
.block-head-hint {
  margin-left: auto;
  font-size: 10px;
  font-weight: 700;
  color: #ea580c;
}
.block-body--3col {
  display: grid;
  grid-template-columns: 1.1fr 0.85fr 0.75fr;
  gap: 8px;
}
.block-body--status {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: end;
}
.block-field-no-margin {
  margin-bottom: 0 !important;
}
.deadline-picker {
  width: 160px;
  max-width: 100%;
}
.mgmt-no-input {
  width: calc(13ch + 28px);
  max-width: 100%;
}
.mgmt-no-input :deep(.el-input__inner) {
  font-family: ui-monospace, Consolas, monospace;
  letter-spacing: 0.05em;
  font-weight: 600;
}
.qty-input {
  width: 96px;
}
.qty-input :deep(.el-input__inner) {
  text-align: right;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.pick-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pick-chip {
  padding: 5px 11px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 750;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pick-chip--sm {
  padding: 4px 9px;
}
.pick-chip--active {
  color: #fff !important;
  border-color: transparent !important;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.16);
}
.pick-chip--cat-disposal.pick-chip--active {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}
.pick-chip--cat-defect.pick-chip--active {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
}
.pick-chip--cat-hold.pick-chip--active {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}
.pick-chip--cat-vanish.pick-chip--active {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}
.pick-chip--cat-other.pick-chip--active {
  background: linear-gradient(135deg, #64748b, #475569);
}
.pick-chip--proc-cut.pick-chip--active {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}
.pick-chip--proc-chamfer.pick-chip--active {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
}
.pick-chip--proc-form.pick-chip--active {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}
.pick-chip--proc-plate.pick-chip--active {
  background: linear-gradient(135deg, #ec4899, #db2777);
}
.pick-chip--proc-weld.pick-chip--active {
  background: linear-gradient(135deg, #f97316, #ea580c);
}
.pick-chip--proc-inspect.pick-chip--active {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}
.pick-chip--proc-other.pick-chip--active {
  background: linear-gradient(135deg, #94a3b8, #64748b);
}
.pick-chip--status-pending.pick-chip--active {
  background: linear-gradient(135deg, #f59e0b, #ea580c);
}
.pick-chip--status-done.pick-chip--active {
  background: linear-gradient(135deg, #10b981, #059669);
}

.notify-body {
  min-height: 120px;
}
.notify-hero {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 12px 14px;
  margin-bottom: 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff7ed, #fff);
  border: 1px solid #fed7aa;
}
.notify-hero--warn {
  background: linear-gradient(135deg, #fef2f2, #fff);
  border-color: #fecaca;
}
.notify-hero-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.notify-hero-num {
  font-size: 36px;
  font-weight: 850;
  line-height: 1;
  color: #ea580c;
}
.notify-hero-unit {
  font-size: 14px;
  font-weight: 700;
  color: #94a3b8;
}
.notify-hero-meta p {
  margin: 0 0 4px;
  font-size: 13px;
  color: #475569;
}
.notify-hint {
  font-size: 11px !important;
  color: #94a3b8 !important;
}
.notify-deadline-warn {
  margin: 0 0 4px !important;
  font-size: 13px !important;
  font-weight: 750 !important;
  color: #dc2626 !important;
}
.notify-deadline-detail {
  margin: 4px 0 0;
  font-size: 12px;
}
.notify-alert {
  margin-bottom: 10px;
}
.notify-form {
  margin-top: 4px;
}
.notify-recipient-field {
  width: 100%;
}
.notify-recipient-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 6px;
}
.notify-saved-hint {
  margin-right: auto;
  font-size: 12px;
  color: #64748b;
}
.notify-saved-hint--dirty {
  color: #d97706;
  font-weight: 700;
}
.notify-table {
  margin-top: 8px;
  border-radius: 8px;
  overflow: hidden;
}
.full-width {
  width: 100%;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .filter-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .filter-item.span-2 {
    grid-column: span 3;
  }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  .filter-grid {
    grid-template-columns: 1fr 1fr;
  }
  .filter-item.span-2 {
    grid-column: span 2;
  }
  .block-body--3col,
  .block-body--status {
    grid-template-columns: 1fr;
  }
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（大量廃棄・保留品 / amber→orange→rose 警告系）
 * ============================================================ */

/* ---------- ヒーローヘッダー ---------- */
.bdr-modern .toolbar-elevated {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, #b45309 0%, #ea580c 32%, #e11d48 70%, #be185d 100%);
  box-shadow:
    0 18px 36px -18px rgba(190, 18, 60, 0.6),
    0 4px 12px -6px rgba(234, 88, 12, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.16) inset;
}
.bdr-modern .toolbar-fx {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.bdr-modern .toolbar-fx .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(4px);
  animation: bdrOrbFloat 12s ease-in-out infinite;
}
.bdr-modern .toolbar-fx .orb-a {
  width: 260px;
  height: 260px;
  top: -150px;
  right: 26%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 70%);
}
.bdr-modern .toolbar-fx .orb-b {
  width: 200px;
  height: 200px;
  bottom: -120px;
  left: 30%;
  background: radial-gradient(circle, rgba(254, 240, 138, 0.4) 0%, rgba(254, 240, 138, 0) 70%);
  animation-duration: 15s;
  animation-delay: -6s;
}
.bdr-modern .toolbar-fx .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(ellipse at 14% 50%, #000 0%, transparent 70%);
  mask-image: radial-gradient(ellipse at 14% 50%, #000 0%, transparent 70%);
}
.bdr-modern .toolbar-fx .fx-sheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    115deg,
    transparent 38%,
    rgba(255, 255, 255, 0.18) 50%,
    transparent 62%
  );
  background-size: 250% 100%;
  animation: bdrSheen 7s ease-in-out infinite;
}
.bdr-modern .toolbar-brand,
.bdr-modern .toolbar-actions {
  position: relative;
  z-index: 1;
}
.bdr-modern .brand-icon {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.08));
  box-shadow:
    0 10px 20px -8px rgba(76, 5, 25, 0.6),
    0 2px 0 rgba(255, 255, 255, 0.35) inset,
    0 -3px 0 rgba(159, 18, 57, 0.35) inset;
  animation: bdrIconFloat 5.5s ease-in-out infinite;
}
.bdr-modern .toolbar-title {
  font-size: 1.2rem;
  color: #fff;
  letter-spacing: 0.04em;
  text-shadow: 0 2px 6px rgba(76, 5, 25, 0.3);
}
.bdr-modern .toolbar-sub {
  color: rgba(255, 255, 255, 0.86);
}
.bdr-modern .toolbar-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.bdr-modern .toolbar-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
  color: #fff;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 6px 14px -8px rgba(76, 5, 25, 0.55);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}

/* ---------- 操作ボタン：3Dキーキャップ ---------- */
.bdr-modern .action-btn {
  --k-edge: #cbd5e1;
  --k-glow: rgba(15, 23, 42, 0.25);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.bdr-modern .action-btn--primary {
  --k-edge: #1e3a8a;
  --k-glow: rgba(37, 99, 235, 0.55);
}
.bdr-modern .action-btn--notify {
  --k-edge: #f59e0b;
  --k-glow: rgba(146, 64, 14, 0.45);
}
.bdr-modern .action-btn--print {
  --k-edge: #a78bfa;
  --k-glow: rgba(76, 29, 149, 0.45);
}
.bdr-modern .action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  filter: brightness(1.04);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.bdr-modern .action-btn:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow);
}
.bdr-modern .action-btn:disabled {
  box-shadow: none;
}
.bdr-modern .action-badge {
  animation: bdrBadgePulse 2s ease-in-out infinite;
}

/* ---------- KPIカード：3Dチルト＋色分け ---------- */
.bdr-modern .kpi-grid {
  perspective: 900px;
}
.bdr-modern .kpi-card {
  --kpi: #2563eb;
  --kpi-edge: #1e40af;
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition:
    transform 0.18s ease-out,
    box-shadow 0.25s ease;
}
.bdr-modern .kpi-card--pending {
  --kpi: #d97706;
  --kpi-edge: #92400e;
}
.bdr-modern .kpi-card--overdue {
  --kpi: #e11d48;
  --kpi-edge: #9f1239;
}
.bdr-modern .kpi-card--done {
  --kpi: #059669;
  --kpi-edge: #065f46;
}
.bdr-modern .kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--kpi) 55%, #ffffff), var(--kpi));
  pointer-events: none;
}
.bdr-modern .kpi-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    color-mix(in srgb, var(--kpi) 16%, transparent) 0%,
    transparent 60%
  );
  opacity: 0;
  transition: opacity 0.25s ease;
}
.bdr-modern .kpi-card:hover {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 20px 34px -18px color-mix(in srgb, var(--kpi) 55%, transparent),
    0 4px 10px rgba(15, 23, 42, 0.06);
}
.bdr-modern .kpi-card:hover::after {
  opacity: 1;
}
.bdr-modern .kpi-card__glow {
  animation: bdrOrbFloat 10s ease-in-out infinite;
}
.bdr-modern .kpi-icon {
  transform: translateZ(20px);
  box-shadow:
    0 3px 0 var(--kpi-edge),
    0 8px 14px -6px color-mix(in srgb, var(--kpi) 70%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.bdr-modern .kpi-card__value {
  color: color-mix(in srgb, var(--kpi) 45%, #0f172a);
  transform: translateZ(14px);
}
.bdr-modern .kpi-card--overdue.is-alert {
  animation: bdrAlertRing 2.4s ease-in-out infinite;
}
.bdr-modern .kpi-card--overdue.is-alert .kpi-card__value {
  color: #e11d48;
}

/* ---------- パネル ---------- */
.bdr-modern .panel-accent {
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.45);
}
.bdr-modern .panel-accent--blue {
  box-shadow: 0 0 10px rgba(37, 99, 235, 0.4);
}

/* 区分チップ：3Dキーキャップ（区分別カラー） */
.bdr-modern .chip {
  --chip-edge: #475569;
  box-shadow: 0 2px 0 #e2e8f0;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    color 0.15s ease,
    background 0.15s ease;
}
.bdr-modern .chip--cat-disposal,
.bdr-modern .chip--overdue {
  --chip-edge: #991b1b;
}
.bdr-modern .chip--cat-defect {
  --chip-edge: #4c1d95;
}
.bdr-modern .chip--cat-hold {
  --chip-edge: #92400e;
}
.bdr-modern .chip--cat-vanish {
  --chip-edge: #155e75;
}
.bdr-modern .chip--cat-other {
  --chip-edge: #334155;
}
.bdr-modern .chip--status-pending {
  --chip-edge: #9a3412;
}
.bdr-modern .chip--status-done {
  --chip-edge: #065f46;
}
.bdr-modern .chip:not(.chip--active):hover {
  transform: translateY(-2px);
  color: var(--chip-edge);
  border-color: color-mix(in srgb, var(--chip-edge) 35%, #ffffff);
  box-shadow:
    0 4px 0 #e2e8f0,
    0 8px 14px -8px color-mix(in srgb, var(--chip-edge) 60%, transparent);
}
.bdr-modern .chip--active {
  transform: translateY(-1px);
  box-shadow:
    0 3px 0 var(--chip-edge),
    0 8px 14px -6px color-mix(in srgb, var(--chip-edge) 60%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.bdr-modern .chip:active {
  transform: translateY(1px);
}

/* ---------- 記録一覧テーブル ---------- */
.bdr-modern .table-wrap {
  box-shadow: 0 12px 26px -22px rgba(190, 18, 60, 0.45);
}
.bdr-modern .bdr-table :deep(th.el-table__cell) {
  color: #9a3412;
  background: linear-gradient(180deg, #fffaf5 0%, #fdeee4 100%) !important;
  border-bottom: 2px solid #fdba74;
}
.bdr-modern .bdr-table :deep(.row-overdue td.el-table__cell:first-child) {
  box-shadow: inset 4px 0 0 #ef4444;
}
.bdr-modern .bdr-table :deep(.row-pending td.el-table__cell:first-child) {
  box-shadow: inset 4px 0 0 #f59e0b;
}
.bdr-modern .bdr-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 4px 0 0 #2563eb;
}
.bdr-modern .pill {
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.06);
}
.bdr-modern .cell-deadline--overdue {
  animation: bdrBlink 1.6s ease-in-out infinite;
}
.bdr-modern .act-btn {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  transition:
    transform 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}
.bdr-modern .act-edit:hover {
  background: #eff6ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 0 #bfdbfe;
}
.bdr-modern .act-del:hover {
  background: #fff1f2;
  transform: translateY(-1px);
  box-shadow: 0 2px 0 #fecdd3;
}
.bdr-modern .pagination-bar :deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(135deg, #f97316 0%, #e11d48 100%);
  box-shadow:
    0 2px 0 #9f1239,
    0 6px 12px -6px rgba(225, 29, 72, 0.7);
  transform: translateY(-1px);
}

/* ---------- キーフレーム ---------- */
@keyframes bdrOrbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(-18px, 10px, 0) scale(1.08);
  }
}
@keyframes bdrSheen {
  0%,
  100% {
    background-position: 130% 0;
  }
  50% {
    background-position: -30% 0;
  }
}
@keyframes bdrIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(-2px);
  }
}
@keyframes bdrBadgePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5);
  }
  50% {
    box-shadow: 0 0 0 5px rgba(239, 68, 68, 0);
  }
}
@keyframes bdrAlertRing {
  0%,
  100% {
    border-color: rgba(226, 232, 240, 0.98);
  }
  50% {
    border-color: rgba(244, 63, 94, 0.55);
  }
}
@keyframes bdrBlink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.55;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bdr-modern .toolbar-fx .fx-orb,
  .bdr-modern .toolbar-fx .fx-sheen,
  .bdr-modern .brand-icon,
  .bdr-modern .action-badge,
  .bdr-modern .kpi-card__glow,
  .bdr-modern .kpi-card--overdue.is-alert,
  .bdr-modern .cell-deadline--overdue {
    animation: none;
  }
  .bdr-modern .kpi-card {
    transform: none;
    transition: none;
  }
}
</style>

<style>
/* 对话框全局（append-to-body） */
.bdr-dialog .el-dialog {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.22), 0 0 0 1px rgba(15, 23, 42, 0.04);
}
.bdr-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.bdr-dialog .el-dialog__headerbtn {
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
}
.bdr-dialog .el-dialog__headerbtn .el-dialog__close {
  color: rgba(255, 255, 255, 0.65);
  font-size: 16px;
}
.bdr-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff;
}
.bdr-dialog .el-dialog__body {
  padding: 10px 12px 6px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
.bdr-dialog .el-dialog__footer {
  padding: 8px 12px 12px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}
.dlg-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 40px 12px 14px;
}
.dlg-header-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.dlg-header-icon--new {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}
.dlg-header-icon--edit {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}
.dlg-header-text {
  flex: 1;
  min-width: 0;
}
.dlg-title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #f8fafc;
  line-height: 1.2;
}
.dlg-subtitle {
  margin: 2px 0 0;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}
.dlg-badge {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
}
.dlg-badge--new {
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.4);
}
.dlg-badge--edit {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.35);
}
.dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.dlg-btn {
  border-radius: 8px;
  font-weight: 700;
  font-size: 12px;
  padding: 7px 16px;
  height: auto;
}
.dlg-btn--cancel {
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #64748b;
}
.dlg-btn--save {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.bdr-dialog--notify .el-dialog__header {
  padding: 14px 18px 10px;
}
.bdr-dialog--notify .el-dialog__title {
  color: #f8fafc;
  font-weight: 700;
}
</style>
