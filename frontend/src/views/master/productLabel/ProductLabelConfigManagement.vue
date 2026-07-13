<template>
  <div class="plc-page">
    <header class="plc-hero">
      <div class="plc-hero-inner">
        <div class="plc-title-row">
          <span class="plc-title-icon"><el-icon :size="20"><PriceTag /></el-icon></span>
          <div>
            <h1 class="plc-title">成型用ラベル設定</h1>
            <p class="plc-subtitle">現品票（A4縦・2列×3行）の加工用製品名・入数・8枠・印刷色を管理（製品CD末尾「1」のみ）</p>
          </div>
        </div>
        <div class="plc-stat">
          <span class="plc-stat-num">{{ pagination.total }}</span>
          <span class="plc-stat-lbl">登録件数</span>
        </div>
      </div>
    </header>

    <section class="plc-toolbar-card">
      <div class="plc-toolbar">
        <div class="plc-search-wrap">
          <span class="plc-search-label"><el-icon :size="14"><Search /></el-icon> 検索</span>
          <el-input
            v-model="filters.keyword"
            placeholder="製品CD・製品名・加工用製品名で検索"
            clearable
            size="small"
            class="plc-search"
            @input="onKeywordInput"
            @clear="onKeywordClear"
          />
        </div>

        <div class="plc-toolbar-actions">
          <el-button size="small" class="plc-btn plc-btn--refresh" :icon="Refresh" @click="loadList">
            再読込
          </el-button>
          <el-button
            size="small"
            class="plc-btn plc-btn--print"
            :icon="Printer"
            :loading="printingAll"
            :disabled="pagination.total === 0"
            @click="openPrintAllDialog"
          >
            一括印刷
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="plc-btn plc-btn--outsource"
            :icon="Message"
            @click="openOutsourceOrderDialog"
          >
            外注注文
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="plc-btn plc-btn--sync"
            :icon="Download"
            :loading="syncing"
            @click="handleSyncFromMaster"
          >
            マスタ取込
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="plc-btn plc-btn--derive"
            :icon="RefreshRight"
            :loading="derivingAll"
            @click="handleDeriveAll"
          >
            一括枠導出
          </el-button>
          <el-button
            v-if="canCreate"
            size="small"
            class="plc-btn plc-btn--create"
            :icon="Plus"
            @click="openDialog()"
          >
            新規登録
          </el-button>
        </div>
      </div>
    </section>

    <section ref="tableWrapRef" class="plc-table-wrap">
      <div class="plc-result-bar">
        <span class="plc-result-text">{{ pagination.total }} 件中 {{ list.length }} 件を表示</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          :layout="paginationLayout"
          size="small"
          background
          @current-change="loadList"
          @size-change="loadList"
        />
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        stripe
        border
        size="small"
        class="plc-table"
        :header-cell-style="headerCellStyle"
        :default-sort="{ prop: 'master_product_name', order: 'ascending' }"
        :height="tableHeight"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="product_cd" label="製品CD" :width="TABLE_COL.productCd" :fixed="tableFixed" show-overflow-tooltip />
        <el-table-column
          prop="master_product_name"
          label="製品名（マスタ）"
          :min-width="TABLE_COL.masterName"
          sortable="custom"
          show-overflow-tooltip
        />
        <el-table-column label="終息" :width="TABLE_COL.discontinued" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_discontinued ? 'info' : 'success'" size="small" effect="plain">
              {{ row.is_discontinued ? '終息' : '現行' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="label_product_name" label="加工用製品名" :min-width="TABLE_COL.labelName" show-overflow-tooltip />
        <el-table-column prop="process_unit_qty" label="入数" :width="TABLE_COL.qty" align="center">
          <template #default="{ row }">{{ row.process_unit_qty ?? '—' }}</template>
        </el-table-column>
        <el-table-column label="区分" :width="TABLE_COL.supplyType" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="normalizeSupplyType(row.supply_type) === '外注'"
              :disabled="!canEdit"
              size="small"
              inline-prompt
              active-text="外注"
              inactive-text="社内"
              @change="(val: boolean) => handleSupplyTypeChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="用紙色" :width="TABLE_COL.paperColor" align="center">
          <template #default="{ row }">
            <div class="plc-table-color-cell">
              <span class="plc-paper-chip" :style="paperChipStyle(row.paper_color)">
                {{ row.paper_color || '白' }}
              </span>
              <el-select
                v-if="canEdit"
                :model-value="row.paper_color || '白'"
                size="small"
                class="plc-table-color-select"
                @change="(val: string) => saveInlineField(row, { paper_color: val })"
              >
                <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                  <span class="plc-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
                </el-option>
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="製品名色" :width="TABLE_COL.nameColor" align="center">
          <template #default="{ row }">
            <div class="plc-table-color-cell">
              <span class="plc-name-color-preview">
                <span class="plc-color-dot" :style="{ background: normalizeNameColor(row.product_name_color) }" />
                <span>{{ productNameColorLabel(row.product_name_color) }}</span>
              </span>
              <el-select
                v-if="canEdit"
                :model-value="normalizeNameColor(row.product_name_color)"
                size="small"
                class="plc-table-color-select"
                @change="(val: string) => saveInlineField(row, { product_name_color: val })"
              >
                <el-option
                  v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
                  :key="c.value"
                  :label="c.label"
                  :value="c.value"
                >
                  <span class="plc-opt-color">
                    <span class="plc-color-dot" :style="{ background: c.value }" />
                    {{ c.label }}
                  </span>
                </el-option>
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="固定" :width="TABLE_COL.upperLock" align="center">
          <template #default="{ row }">
            <el-switch
              v-if="canEdit"
              :model-value="!!row.upper_slots_locked"
              size="small"
              inline-prompt
              active-text="ON"
              inactive-text="OFF"
              @change="(val: boolean) => handleUpperLockChange(row, val)"
            />
            <el-tag v-else :type="row.upper_slots_locked ? 'warning' : 'info'" size="small" effect="plain">
              {{ row.upper_slots_locked ? 'ON' : 'OFF' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="上段（枠1〜4）" align="center" class-name="plc-slot-group">
          <el-table-column
            v-for="i in 4"
            :key="`top-${i}`"
            :label="topSlotHeader(i)"
            :width="TABLE_COL.slot"
            align="center"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span :class="['plc-slot-cell', 'plc-slot-top', { 'is-empty': slotValue(row, i - 1) === '—' }]">
                {{ slotValue(row, i - 1) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="下段（枠5〜8）" align="center" class-name="plc-slot-group">
          <el-table-column
            v-for="i in 4"
            :key="`bottom-${i}`"
            :label="String(i + 4)"
            :width="TABLE_COL.slot"
            align="center"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span :class="['plc-slot-cell', 'plc-slot-bottom', { 'is-empty': slotValue(row, i + 3) === '—' }]">
                {{ slotValue(row, i + 3) }}
              </span>
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column prop="remark" label="備考" :min-width="TABLE_COL.remark" show-overflow-tooltip>
          <template #default="{ row }">
            <el-input
              v-if="canEdit"
              :model-value="row.remark || ''"
              size="small"
              placeholder="備考"
              maxlength="255"
              clearable
              @change="(val: string) => saveInlineField(row, { remark: val?.trim() || null })"
            />
            <span v-else>{{ row.remark || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" :width="TABLE_COL.action" :fixed="tableFixedRight" align="center">
          <template #default="{ row }">
            <div class="plc-row-actions">
              <el-button
                v-if="canEdit"
                link
                type="primary"
                size="small"
                @click="openDialog(row)"
              >
                編集
              </el-button>
              <el-button
                link
                type="success"
                size="small"
                :loading="printingCd === row.product_cd"
                @click="openPrintDialog(row)"
              >
                印刷
              </el-button>
              <el-button
                v-if="canDelete"
                link
                type="danger"
                size="small"
                @click="handleDelete(row)"
              >
                削除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '成型用ラベル設定の編集' : '成型用ラベル設定の新規登録'"
      :width="editDialogWidth"
      destroy-on-close
      class="plc-dialog"
    >
      <el-form ref="formRef" :model="form" label-position="top" class="plc-form" size="small">
        <el-tabs v-model="editDialogTab" class="plc-edit-tabs">
          <el-tab-pane label="基本情報" name="basic">
            <div class="plc-tab-pane">
              <el-form-item label="製品CD" required>
                <el-select
                  v-model="form.product_cd"
                  filterable
                  :disabled="isEdit"
                  placeholder="製品を選択してください"
                  style="width: 100%"
                  @change="onProductCdChange"
                >
                  <el-option
                    v-for="p in availableProducts"
                    :key="p.product_cd"
                    :label="`${p.product_cd}　${p.product_name}`"
                    :value="p.product_cd"
                    :disabled="!isEdit && p.configured"
                  />
                </el-select>
              </el-form-item>

              <div class="plc-form-section">
                <div class="plc-section-title">製品マスタ情報（参照）</div>
                <div class="plc-form-grid">
                  <el-form-item label="製品名（マスタ）">
                    <el-input :model-value="masterInfo.product_name || '—'" readonly />
                  </el-form-item>
                  <el-form-item label="別名">
                    <el-input :model-value="masterInfo.product_alias || '—'" readonly />
                  </el-form-item>
                  <el-form-item label="工程ルート">
                    <el-input :model-value="masterInfo.route_cd || '—'" readonly />
                  </el-form-item>
                  <el-form-item label="ロットサイズ">
                    <el-input :model-value="formatMasterNumber(masterInfo.lot_size)" readonly />
                  </el-form-item>
                  <el-form-item label="箱入数" class="plc-span-full">
                    <el-input :model-value="formatMasterNumber(masterInfo.unit_per_box)" readonly />
                  </el-form-item>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="印刷設定" name="print">
            <div class="plc-tab-pane">
              <div class="plc-form-section">
                <div class="plc-section-title">ラベル印刷設定</div>
                <div class="plc-form-grid">
                  <el-form-item label="加工用製品名" class="plc-span-full">
                    <el-input v-model="form.label_product_name" placeholder="現場表示用の製品名" />
                  </el-form-item>
                  <el-form-item label="加工入数">
                    <el-input-number
                      v-model="form.process_unit_qty"
                      :min="0"
                      :controls="true"
                      placeholder="手動入力"
                      style="width: 100%"
                    />
                    <div class="plc-field-hint">ロットサイズとは別に、現品票の入数を入力してください</div>
                  </el-form-item>
                  <el-form-item label="備考" class="plc-span-full">
                    <el-input
                      v-model="form.remark"
                      placeholder="現品票の入数行左側に印字（任意）"
                      maxlength="255"
                      clearable
                    />
                  </el-form-item>
                  <el-form-item label="区分">
                    <el-select v-model="form.supply_type" placeholder="区分を選択" style="width: 100%">
                      <el-option v-for="t in SUPPLY_TYPE_OPTIONS" :key="t" :label="t" :value="t" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="用紙色">
                    <el-select v-model="form.paper_color" placeholder="用紙色を選択" style="width: 100%">
                      <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                        <span class="plc-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                  <el-form-item label="製品名色">
                    <el-select v-model="form.product_name_color" placeholder="文字色を選択" style="width: 100%">
                      <el-option
                        v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
                        :key="c.value"
                        :label="c.label"
                        :value="c.value"
                      >
                        <span class="plc-opt-color">
                          <span class="plc-color-dot" :style="{ background: c.value }" />
                          {{ c.label }}
                        </span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="工程枠" name="slots">
            <div class="plc-tab-pane">
              <div class="plc-form-section">
                <div class="plc-section-title plc-section-title-row">
                  <span>8枠（上段・下段）</span>
                  <el-switch
                    v-model="form.upper_slots_locked"
                    inline-prompt
                    active-text="固定ON"
                    inactive-text="固定OFF"
                    size="small"
                  />
                </div>
                <p class="plc-field-hint plc-section-hint">
                  固定ONのとき、枠導出・一括枠導出・マスタ取込では枠1〜8（上段・下段）を上書きしません
                </p>
              </div>

              <div class="plc-form-section">
                <div class="plc-section-title">上段（枠1〜4：成型設備・手直し）</div>
                <div class="plc-form-grid">
                  <el-form-item v-for="i in 4" :key="`top-${i}`" :label="slotLabel(i)">
                    <el-input
                      v-model="form.process_slots[i - 1]"
                      :placeholder="slotPlaceholder(i)"
                      :readonly="i === 4"
                    />
                  </el-form-item>
                </div>
              </div>

              <div class="plc-form-section">
                <div class="plc-section-title">下段（枠5〜8：成型後工程）</div>
                <div class="plc-form-grid">
                  <el-form-item v-for="i in 4" :key="`bottom-${i}`" :label="`枠${i + 4}`">
                    <el-input v-model="form.process_slots[i + 3]" placeholder="工程名" />
                  </el-form-item>
                </div>
              </div>

              <div class="plc-form-actions">
                <el-button
                  v-if="form.product_cd"
                  size="small"
                  type="success"
                  plain
                  :loading="prefilling"
                  @click="handleLoadFromMasterInDialog"
                >
                  マスタから読込
                </el-button>
                <el-button
                  v-if="form.product_cd"
                  size="small"
                  type="warning"
                  plain
                  :loading="deriving"
                  @click="handleDeriveInDialog"
                >
                  枠を再導出
                </el-button>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <div class="plc-dialog-footer">
          <el-button size="small" class="plc-btn-cancel" @click="dialogVisible = false">キャンセル</el-button>
          <el-button size="small" type="primary" class="plc-btn-save" :loading="submitting" @click="handleSubmit">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 一括印刷ダイアログ -->
    <el-dialog
      v-model="printAllDialogVisible"
      title="一覧の一括印刷"
      :width="printDialogWidth"
      destroy-on-close
      class="plc-dialog"
    >
      <div class="plc-print-body">
        <div class="plc-print-all-summary">
          <p class="plc-print-all-lead">
            検索条件に一致する <strong>{{ printAllTargetCount }}</strong> 件を、一覧表形式で印刷します。
          </p>
          <p class="plc-print-hint">用紙: A4 横向。画面上の一覧と同じ列構成で出力します。</p>
        </div>
      </div>
      <template #footer>
        <div class="plc-dialog-footer">
          <el-button size="small" class="plc-btn-cancel" @click="printAllDialogVisible = false">キャンセル</el-button>
          <el-button
            size="small"
            type="success"
            class="plc-btn-print"
            :icon="Printer"
            :loading="printingAll"
            :disabled="printAllTargetCount === 0"
            @click="doPrintAll"
          >
            印刷開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 印刷ダイアログ -->
    <el-dialog v-model="printDialogVisible" title="現品票の印刷" :width="printDialogWidth" destroy-on-close class="plc-dialog">
      <div v-if="printTarget" class="plc-print-body">
        <div class="plc-print-product">
          <span class="plc-print-cd">{{ printTarget.product_cd }}</span>
          <div class="plc-print-name-row">
            <span class="plc-print-name-label">製品名</span>
            <strong class="plc-print-master-name">{{ printTarget.master_product_name || '—' }}</strong>
          </div>
          <div class="plc-print-name-row">
            <span class="plc-print-name-label">加工用製品名</span>
            <strong
              class="plc-print-label-name"
              :style="{ color: normalizeNameColor(printTarget.product_name_color) }"
            >
              {{ printTarget.label_product_name || '—' }}
            </strong>
          </div>
        </div>
        <div class="plc-print-settings">
          <div class="plc-print-settings-row">
            <div class="plc-print-settings-item">
              <span class="plc-print-settings-label">用紙色</span>
              <span class="plc-print-paper-val" :style="paperChipStyle(printTarget.paper_color)">
                {{ printTarget.paper_color || '白' }}
              </span>
            </div>
            <div class="plc-print-settings-item">
              <span class="plc-print-settings-label">製品名色</span>
              <span class="plc-print-name-color">
                <span
                  class="plc-color-dot"
                  :style="{ background: normalizeNameColor(printTarget.product_name_color) }"
                />
                {{ productNameColorLabel(normalizeNameColor(printTarget.product_name_color)) }}
              </span>
            </div>
          </div>
          <div class="plc-print-settings-row plc-print-settings-qty">
            <div v-if="printTarget.remark?.trim()" class="plc-print-remark">
              <span class="plc-print-settings-label">備考</span>
              <span class="plc-print-remark-val">{{ printTarget.remark }}</span>
            </div>
            <div class="plc-print-qty-block">
              <span class="plc-print-settings-label">入数</span>
              <strong class="plc-print-qty-val">{{ printTarget.process_unit_qty ?? '—' }}</strong>
            </div>
          </div>
        </div>
        <el-form label-position="top" size="small">
          <el-form-item label="初マーク">
            <div class="plc-print-initial-row">
              <el-switch
                v-model="printShowInitial"
                inline-prompt
                active-text="ON"
                inactive-text="OFF"
              />
              <span class="plc-print-hint">ONで各ラベル左上に赤丸「初」を印字</span>
            </div>
          </el-form-item>
          <el-form-item label="印刷枚数（A4用紙）">
            <el-input-number v-model="printPages" :min="1" :max="20" style="width: 140px" />
            <span class="plc-print-hint">1枚あたり 6 ラベル（2列×3行）</span>
          </el-form-item>
        </el-form>
        <p class="plc-print-note">用紙色・製品名色をご確認のうえ、印刷を開始してください。</p>
      </div>
      <template #footer>
        <div class="plc-dialog-footer">
          <el-button size="small" class="plc-btn-cancel" @click="printDialogVisible = false">キャンセル</el-button>
          <el-button size="small" type="success" class="plc-btn-print" :icon="Printer" :loading="printing" @click="doPrint">
            印刷開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 外注注文ダイアログ -->
    <el-dialog
      v-model="outsourceDialogVisible"
      title="外注ラベル注文"
      :width="outsourceDialogWidth"
      destroy-on-close
      class="plc-dialog plc-outsource-dialog"
    >
      <div v-loading="outsourceLoading" class="plc-outsource-body">
        <p class="plc-outsource-lead">
          区分が<strong>外注</strong>の製品のみ表示。注文数を入力し、メールで注文一覧と現品票PDFを送信できます。
        </p>
        <el-table :data="outsourceOrderRows" stripe border size="small" max-height="360" class="plc-outsource-table">
          <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip />
          <el-table-column prop="label_product_name" label="加工用製品名" min-width="160" show-overflow-tooltip />
          <el-table-column label="入数" width="72" align="center">
            <template #default="{ row }">{{ row.process_unit_qty ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="用紙色" width="100" align="center">
            <template #default="{ row }">
              <span class="plc-paper-chip" :style="paperChipStyle(row.paper_color)">
                {{ row.paper_color || '白' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="注文数" width="120" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.order_qty"
                :min="0"
                :max="99999"
                :controls="true"
                size="small"
                style="width: 100%"
              />
            </template>
          </el-table-column>
        </el-table>

        <div class="plc-outsource-mail">
          <div class="plc-outsource-mail-head">
            <span>メール送信</span>
            <span v-if="outsourceOrderSendCount > 0" class="plc-outsource-mail-stat">
              送信対象 {{ outsourceOrderSendCount }} 件 / 現品票PDF 約 {{ outsourceLabelPdfCount }} 枚（1枚6品種）
            </span>
          </div>
          <el-alert
            v-if="outsourceEmailPreview && !outsourceEmailPreview.can_send"
            type="warning"
            :closable="false"
            show-icon
            title="メール送信の準備ができていません（SMTP・テンプレート・通知設定を確認）"
            class="plc-outsource-alert"
          />
          <el-form label-width="88px" size="small" class="plc-outsource-form">
            <el-form-item label="送信先" required>
              <el-select
                v-model="outsourceUserIds"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="ユーザーを選択"
                style="width: 100%"
              >
                <el-option
                  v-for="u in outsourceUsers"
                  :key="u.id"
                  :label="`${u.full_name || u.username} (${u.email || 'メール未設定'})`"
                  :value="u.id"
                  :disabled="!u.email"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </div>
      <template #footer>
        <div class="plc-dialog-footer">
          <el-button size="small" class="plc-btn-cancel" @click="outsourceDialogVisible = false">閉じる</el-button>
          <el-button
            size="small"
            class="plc-btn plc-btn--outsource"
            :icon="Message"
            :loading="outsourceSending"
            :disabled="!canSendOutsourceEmail"
            @click="sendOutsourceOrderEmail"
          >
            メール送信
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Download,
  Message,
  Plus,
  PriceTag,
  Printer,
  Refresh,
  RefreshRight,
  Search,
} from '@element-plus/icons-vue'
import {
  PAPER_COLOR_OPTIONS,
  PRODUCT_NAME_COLOR_OPTIONS,
  SUPPLY_TYPE_OPTIONS,
  createProductLabelConfig,
  deleteProductLabelConfig,
  deriveAllProductLabelProcesses,
  deriveProductLabelProcesses,
  fetchAvailableProductsForLabel,
  fetchOutsourceLabelOrders,
  fetchOutsourceOrderEmailPreview,
  fetchProductLabelConfigList,
  fetchProductLabelPrefill,
  importProductLabelFromMaster,
  productNameColorLabel,
  sendOutsourceOrderEmail as apiSendOutsourceOrderEmail,
  syncProductLabelFromMaster,
  updateProductLabelConfig,
  type AvailableProductForLabel,
  type OutsourceOrderEmailPreview,
  type ProductLabelConfig,
  type ProductLabelPrefill,
} from '@/api/master/productLabelConfig'
import { getUsers, type UserListItem } from '@/api/system'
import {
  printProductLabels,
  type ProductLabelPrintInput,
} from '@/views/mes/productionInstruction/productLabel/utils/productLabelPrint'
import { printProductLabelConfigList } from '@/views/master/productLabel/utils/productLabelConfigListPrint'
import { buildLabelEmailAttachments } from '@/views/master/productLabel/utils/productLabelOutsourceOrderPdf'
import { recordLabelQuantityPrint } from '@/api/master/labelQuantity'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const headerCellStyle = {
  background: 'linear-gradient(180deg, #f0fdfa 0%, #ecfeff 100%)',
  color: '#0f766e',
  fontWeight: '700',
  fontSize: '12px',
  padding: '6px 0',
}

/** 表格列宽（px）。固定列用 width，可伸缩列用 minWidth */
const TABLE_COL = {
  productCd: 70,
  masterName: 130,
  discontinued: 64,
  labelName: 150,
  qty: 56,
  remark: 120,
  supplyType: 96,
  paperColor: 118,
  nameColor: 128,
  slot: 85,
  upperLock: 88,
  action: 132,
} as const

const PAPER_CHIP_STYLES: Record<string, { background: string; border: string; color: string }> = {
  白: { background: '#fff', border: '#cbd5e1', color: '#334155' },
  黄: { background: '#fef9c3', border: '#eab308', color: '#854d0e' },
  ピンク: { background: '#fce7f3', border: '#ec4899', color: '#9d174d' },
  緑: { background: '#dcfce7', border: '#22c55e', color: '#166534' },
  青: { background: '#dbeafe', border: '#3b82f6', color: '#1e40af' },
  オレンジ: { background: '#ffedd5', border: '#f97316', color: '#9a3412' },
}

const loading = ref(false)
const submitting = ref(false)
const deriving = ref(false)
const derivingAll = ref(false)
const prefilling = ref(false)
const syncing = ref(false)
const printing = ref(false)
const printingCd = ref('')
const printingAll = ref(false)
const dialogVisible = ref(false)
const editDialogTab = ref<'basic' | 'print' | 'slots'>('basic')
const printDialogVisible = ref(false)
const printAllDialogVisible = ref(false)
const isEdit = ref(false)
const list = ref<ProductLabelConfig[]>([])
const availableProducts = ref<AvailableProductForLabel[]>([])
const printTarget = ref<ProductLabelConfig | null>(null)
const printPages = ref(1)
const printShowInitial = ref(false)
const printAllRows = ref<ProductLabelConfig[]>([])

type OutsourceOrderRow = {
  product_cd: string
  label_product_name: string
  process_unit_qty: number | null
  paper_color: string
  order_qty: number
  config: ProductLabelConfig
}

const outsourceDialogVisible = ref(false)
const outsourceLoading = ref(false)
const outsourceSending = ref(false)
const outsourceOrderRows = ref<OutsourceOrderRow[]>([])
const outsourceEmailPreview = ref<OutsourceOrderEmailPreview | null>(null)
const outsourceUserIds = ref<number[]>([])
const outsourceUsers = ref<UserListItem[]>([])

const tableWrapRef = ref<HTMLElement | null>(null)
const tableHeight = ref(480)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

const tableFixed = computed<'left' | false>(() => (viewportWidth.value >= 900 ? 'left' : false))
const tableFixedRight = computed<'right' | false>(() => (viewportWidth.value >= 900 ? 'right' : false))
const paginationLayout = computed(() =>
  viewportWidth.value < 768 ? 'prev, pager, next' : 'sizes, prev, pager, next'
)
const editDialogWidth = computed(() => (viewportWidth.value < 768 ? 'min(720px, 96vw)' : '720px'))
const printDialogWidth = computed(() => (viewportWidth.value < 480 ? 'min(400px, 96vw)' : '400px'))
const outsourceDialogWidth = computed(() => (viewportWidth.value < 768 ? 'min(900px, 96vw)' : '900px'))
const printAllTargetCount = computed(() => printAllRows.value.length)
const outsourceOrderSendRows = computed(() =>
  outsourceOrderRows.value.filter((row) => (row.order_qty || 0) > 0)
)
const outsourceOrderSendCount = computed(() => outsourceOrderSendRows.value.length)
const outsourceLabelPdfCount = computed(() =>
  outsourceOrderSendCount.value > 0 ? Math.ceil(outsourceOrderSendCount.value / 6) : 0
)
const canSendOutsourceEmail = computed(
  () =>
    !!outsourceEmailPreview.value?.can_send &&
    outsourceOrderSendCount.value > 0 &&
    outsourceUserIds.value.length > 0 &&
    !outsourceSending.value
)

const filters = reactive({ keyword: '' })
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })
const sortConfig = reactive({
  prop: 'master_product_name',
  order: 'asc' as 'asc' | 'desc',
})

let keywordTimer: ReturnType<typeof setTimeout> | null = null

function onKeywordInput() {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => {
    pagination.page = 1
    void loadList()
  }, 350)
}

function onKeywordClear() {
  if (keywordTimer) clearTimeout(keywordTimer)
  pagination.page = 1
  void loadList()
}

function handleSortChange(payload: { prop: string; order: 'ascending' | 'descending' | null }) {
  if (!payload.order) {
    sortConfig.prop = 'master_product_name'
    sortConfig.order = 'asc'
  } else {
    sortConfig.prop = payload.prop || 'master_product_name'
    sortConfig.order = payload.order === 'descending' ? 'desc' : 'asc'
  }
  pagination.page = 1
  void loadList()
}

const emptySlots = (): (string | null)[] => Array.from({ length: 8 }, () => null)

const masterInfo = reactive({
  product_name: '',
  product_alias: '',
  route_cd: '',
  lot_size: null as number | null,
  unit_per_box: null as number | null,
})

const form = reactive({
  id: undefined as number | undefined,
  product_cd: '',
  label_product_name: '',
  process_unit_qty: null as number | null,
  remark: '' as string,
  paper_color: '白' as string | null,
  product_name_color: '#000000',
  supply_type: '社内' as string,
  upper_slots_locked: false,
  process_slots: emptySlots() as (string | null)[],
})

function paperChipStyle(color?: string | null) {
  const key = color || '白'
  const s = PAPER_CHIP_STYLES[key] || PAPER_CHIP_STYLES['白']
  return {
    background: s.background,
    border: `1px solid ${s.border}`,
    color: s.color,
  }
}

function normalizeNameColor(hex?: string | null): string {
  const v = (hex || '#000000').toLowerCase()
  const found = PRODUCT_NAME_COLOR_OPTIONS.find((o) => o.value.toLowerCase() === v)
  return found?.value ?? '#000000'
}

function normalizeSupplyType(value?: string | null): string {
  const v = (value || '社内').trim()
  return SUPPLY_TYPE_OPTIONS.includes(v as (typeof SUPPLY_TYPE_OPTIONS)[number]) ? v : '社内'
}

function handleSupplyTypeChange(row: ProductLabelConfig, isOutsource: boolean) {
  void saveInlineField(row, { supply_type: isOutsource ? '外注' : '社内' })
}

async function saveInlineField(row: ProductLabelConfig, patch: Partial<ProductLabelConfig>) {
  if (!guardMasterOperation(canEdit) || !row.id) return
  try {
    await updateProductLabelConfig(row.id, patch)
    Object.assign(row, patch)
  } catch {
    ElMessage.error('更新に失敗しました')
    await loadList()
  }
}

function topSlotHeader(i: number): string {
  if (i === 4) return '4（手直し）'
  return String(i)
}

function formatMasterNumber(v: number | null | undefined): string {
  if (v == null || v === ('' as unknown as number)) return '—'
  return String(v)
}

function normalizeSlots(row: ProductLabelConfig): (string | null)[] {
  const slots: (string | null)[] = []
  for (let i = 0; i < 8; i++) {
    const fromArr = row.process_slots?.[i]
    if (fromArr != null && String(fromArr).trim()) {
      slots.push(String(fromArr).trim())
      continue
    }
    const field = `process_slot_${i + 1}` as keyof ProductLabelConfig
    const val = row[field]
    slots.push(val != null && String(val).trim() ? String(val).trim() : null)
  }
  return slots
}

function slotValue(row: ProductLabelConfig, index: number): string {
  const val = normalizeSlots(row)[index]
  return val || '—'
}

function slotLabel(i: number): string {
  if (i <= 3) return `枠${i}（成型設備）`
  if (i === 4) return '枠4（手直し）'
  return `枠${i}（成型後工程）`
}

function slotPlaceholder(i: number): string {
  if (i <= 3) return '設備名'
  if (i === 4) return '手直し'
  return '工程名'
}

function configToPrintInput(row: ProductLabelConfig): ProductLabelPrintInput {
  const slots = normalizeSlots(row)
  if (!String(slots[3] || '').trim()) slots[3] = '手直し'
  return {
    product_cd: row.product_cd,
    label_product_name: row.label_product_name || row.master_product_name || '',
    process_unit_qty: row.process_unit_qty ?? null,
    remark: row.remark ?? null,
    product_name_color: row.product_name_color || '#000000',
    route_description: row.route_description || '',
    top_row: {
      machine_1: slots[0] || '',
      machine_2: slots[1] || '',
      machine_3: slots[2] || '',
      machine_4_fixed: slots[3] || '手直し',
    },
    process_slots: slots,
  }
}

function applyMasterInfoOnly(data: ProductLabelPrefill) {
  masterInfo.product_name = data.master_product_name || ''
  masterInfo.product_alias = data.product_alias || ''
  masterInfo.route_cd = data.route_cd || ''
  masterInfo.lot_size = data.lot_size ?? null
  masterInfo.unit_per_box = data.unit_per_box ?? null
}

function applyPrefill(data: ProductLabelPrefill, includeEditable = true) {
  applyMasterInfoOnly(data)
  if (!includeEditable) return
  form.label_product_name = data.label_product_name || ''
  // 入数は手動入力（ロットサイズとは連動しない）
  form.paper_color = data.paper_color || '白'
  form.product_name_color = data.product_name_color || '#000000'
  form.supply_type = normalizeSupplyType(data.supply_type)
  form.process_slots = [...(data.process_slots || emptySlots())]
  while (form.process_slots.length < 8) form.process_slots.push(null)
}

function resetMasterInfo() {
  masterInfo.product_name = ''
  masterInfo.product_alias = ''
  masterInfo.route_cd = ''
  masterInfo.lot_size = null
  masterInfo.unit_per_box = null
}

async function loadList() {
  loading.value = true
  try {
    const res = await fetchProductLabelConfigList({
      keyword: filters.keyword || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order,
    })
    const data = (res as { list?: ProductLabelConfig[]; total?: number }) || res
    list.value = data.list || []
    pagination.total = data.total || 0
  } catch {
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
    requestAnimationFrame(updateLayoutMetrics)
  }
}

async function loadAvailableProducts() {
  try {
    const res = await fetchAvailableProductsForLabel()
    availableProducts.value = res?.data || []
  } catch {
    availableProducts.value = []
  }
}

function resetForm() {
  editDialogTab.value = 'basic'
  form.id = undefined
  form.product_cd = ''
  form.label_product_name = ''
  form.process_unit_qty = null
  form.remark = ''
  form.paper_color = '白'
  form.product_name_color = '#000000'
  form.supply_type = '社内'
  form.upper_slots_locked = false
  form.process_slots = emptySlots()
  resetMasterInfo()
}

async function loadPrefillFromMaster(showMessage = true, overwriteEditable = true) {
  if (!form.product_cd) {
    editDialogTab.value = 'basic'
    ElMessage.warning('製品CDを選択してください')
    return
  }
  prefilling.value = true
  try {
    const res = await fetchProductLabelPrefill(form.product_cd)
    const data = res?.data
    if (!data) {
      ElMessage.error('製品マスタの読込に失敗しました')
      return
    }
    applyPrefill(data, overwriteEditable)
    if (showMessage) {
      ElMessage.success(overwriteEditable ? 'マスタから読込みました' : 'マスタ情報を表示しました')
    }
  } catch {
    ElMessage.error('製品マスタの読込に失敗しました')
  } finally {
    prefilling.value = false
  }
}

async function onProductCdChange() {
  if (!form.product_cd || isEdit.value) return
  await loadPrefillFromMaster(false, true)
}

function openDialog(row?: ProductLabelConfig) {
  if (row ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  resetForm()
  isEdit.value = !!row
  if (row) {
    form.id = row.id
    form.product_cd = row.product_cd
    form.label_product_name = row.label_product_name || ''
    form.process_unit_qty = row.process_unit_qty ?? null
    form.remark = row.remark || ''
    form.paper_color = row.paper_color || '白'
    form.product_name_color = row.product_name_color || '#000000'
    form.supply_type = normalizeSupplyType(row.supply_type)
    form.upper_slots_locked = !!row.upper_slots_locked
    form.process_slots = [...normalizeSlots(row)]
    masterInfo.product_name = row.master_product_name || ''
    void loadPrefillFromMaster(false, false)
  }
  dialogVisible.value = true
}

function updateLayoutMetrics() {
  viewportWidth.value = window.innerWidth
  const wrapTop = tableWrapRef.value?.getBoundingClientRect().top ?? 0
  const bottomGap = viewportWidth.value < 768 ? 12 : 16
  tableHeight.value = Math.max(260, Math.floor(window.innerHeight - wrapTop - bottomGap))
}

async function fetchAllListForPrint(): Promise<ProductLabelConfig[]> {
  const pageSize = 200
  const firstRes = await fetchProductLabelConfigList({
    keyword: filters.keyword || undefined,
    page: 1,
    page_size: pageSize,
    sort_by: sortConfig.prop,
    sort_order: sortConfig.order,
  })
  const firstData = (firstRes as { list?: ProductLabelConfig[]; total?: number }) || firstRes
  const all = [...(firstData.list || [])]
  const total = firstData.total || 0
  let page = 2
  while (all.length < total) {
    const res = await fetchProductLabelConfigList({
      keyword: filters.keyword || undefined,
      page,
      page_size: pageSize,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order,
    })
    const data = (res as { list?: ProductLabelConfig[] }) || res
    all.push(...(data.list || []))
    page += 1
  }
  return all
}

async function openPrintAllDialog() {
  if (pagination.total === 0) {
    ElMessage.warning('印刷対象のデータがありません')
    return
  }
  printingAll.value = true
  try {
    printAllRows.value = await fetchAllListForPrint()
    if (printAllRows.value.length === 0) {
      ElMessage.warning('印刷対象のデータがありません')
      return
    }
    printAllDialogVisible.value = true
  } catch {
    ElMessage.error('印刷対象の取得に失敗しました')
  } finally {
    printingAll.value = false
  }
}

async function doPrintAll() {
  if (printAllRows.value.length === 0) return
  printingAll.value = true
  try {
    printProductLabelConfigList(printAllRows.value, {
      keyword: filters.keyword || undefined,
      total: printAllRows.value.length,
    })
    printAllDialogVisible.value = false
    ElMessage.success('一覧印刷ダイアログを開きました')
  } catch {
    ElMessage.error('一覧印刷の開始に失敗しました')
  } finally {
    printingAll.value = false
  }
}

function mapOutsourceOrderRow(config: ProductLabelConfig): OutsourceOrderRow {
  return {
    product_cd: config.product_cd,
    label_product_name: config.label_product_name || config.master_product_name || '',
    process_unit_qty: config.process_unit_qty ?? null,
    paper_color: config.paper_color || '白',
    order_qty: 0,
    config,
  }
}

async function loadOutsourceUsers() {
  try {
    const res = await getUsers({ page: 1, page_size: 500, status: 'active' })
    outsourceUsers.value = res?.items ?? []
  } catch {
    outsourceUsers.value = []
  }
}

async function openOutsourceOrderDialog() {
  if (!guardMasterOperation(canEdit)) return
  outsourceDialogVisible.value = true
  outsourceLoading.value = true
  outsourceUserIds.value = []
  try {
    const [ordersRes, previewRes] = await Promise.all([
      fetchOutsourceLabelOrders(),
      fetchOutsourceOrderEmailPreview(),
      loadOutsourceUsers(),
    ])
    const orders = (ordersRes as { list?: ProductLabelConfig[] })?.list || []
    outsourceOrderRows.value = orders.map(mapOutsourceOrderRow)
    outsourceEmailPreview.value = previewRes as OutsourceOrderEmailPreview
    if (orders.length === 0) {
      ElMessage.info('外注区分の設定がありません')
    }
  } catch {
    outsourceOrderRows.value = []
    outsourceEmailPreview.value = null
    ElMessage.error('外注注文データの取得に失敗しました')
  } finally {
    outsourceLoading.value = false
  }
}

async function sendOutsourceOrderEmail() {
  if (!guardMasterOperation(canEdit)) return
  if (outsourceOrderSendCount.value === 0) {
    ElMessage.warning('注文数が1以上の行を入力してください')
    return
  }
  if (outsourceUserIds.value.length === 0) {
    ElMessage.warning('送信先ユーザーを選択してください')
    return
  }

  const sendRows = outsourceOrderSendRows.value
  const missingLabel = sendRows.filter((row) => !row.label_product_name?.trim())
  if (missingLabel.length > 0) {
    ElMessage.warning(
      `加工用製品名未設定のためラベル生成できません: ${missingLabel.map((r) => r.product_cd).join(', ')}`
    )
    return
  }

  try {
    await ElMessageBox.confirm(
      `注文 ${sendRows.length} 件をメール送信します（現品票PDF 約 ${outsourceLabelPdfCount.value} 枚）。よろしいですか？`,
      'メール送信確認',
      { type: 'info' }
    )
  } catch {
    return
  }

  outsourceSending.value = true
  try {
    const printInputs: ProductLabelPrintInput[] = sendRows.map((row) =>
      configToPrintInput(row.config)
    )
    const attachments = await buildLabelEmailAttachments(printInputs)
    const res = await apiSendOutsourceOrderEmail({
      user_ids: outsourceUserIds.value,
      items: sendRows.map((row) => ({
        product_cd: row.product_cd,
        order_qty: row.order_qty,
        label_product_name: row.label_product_name,
        master_product_name: row.config.master_product_name,
        process_unit_qty: row.process_unit_qty,
        paper_color: row.paper_color,
      })),
      attachments,
    })
    ElMessage.success(res?.message || 'メールを送信しました')
    outsourceDialogVisible.value = false
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'メール送信に失敗しました'
    ElMessage.error(msg)
  } finally {
    outsourceSending.value = false
  }
}

function openPrintDialog(row: ProductLabelConfig) {
  const name = row.label_product_name || row.master_product_name
  if (!name?.trim()) {
    ElMessage.warning('加工用製品名が未設定のため印刷できません')
    return
  }
  printTarget.value = row
  printPages.value = 1
  printShowInitial.value = false
  printDialogVisible.value = true
}

async function doPrint() {
  if (!printTarget.value) return
  const input = configToPrintInput(printTarget.value)
  if (!input.label_product_name?.trim()) {
    ElMessage.warning('加工用製品名が未設定です')
    return
  }
  printing.value = true
  printingCd.value = printTarget.value.product_cd
  const productCd = printTarget.value.product_cd
  const pages = Math.max(1, Number(printPages.value) || 1)
  try {
    await printProductLabels(input, {
      pages,
      copiesPerPage: 6,
      showInitialMark: printShowInitial.value,
    })
    printDialogVisible.value = false
    ElMessage.success('印刷ダイアログを開きました')
    try {
      await recordLabelQuantityPrint({
        label_type: 'molding',
        items: [
          {
            product_cd: productCd,
            paper_sheets: pages,
            labels_per_sheet: 6,
            label_count: pages * 6,
          },
        ],
      })
    } catch (e) {
      console.warn('ラベル枚数管理への印刷履歴反映に失敗:', e)
      ElMessage.warning('印刷は開始しましたが、枚数管理の履歴更新に失敗しました')
    }
  } catch {
    ElMessage.error('印刷の開始に失敗しました')
  } finally {
    printing.value = false
    printingCd.value = ''
  }
}

async function handleLoadFromMasterInDialog() {
  if (isEdit.value) {
    try {
      await ElMessageBox.confirm(
        '製品マスタの値でラベル設定を上書きします。よろしいですか？',
        '確認',
        { type: 'warning' }
      )
    } catch {
      return
    }
  }
  await loadPrefillFromMaster(true, true)
}

async function handleSubmit() {
  if (isEdit.value ? !guardMasterOperation(canEdit) : !guardMasterOperation(canCreate)) return
  if (!form.product_cd) {
    editDialogTab.value = 'basic'
    ElMessage.warning('製品CDを選択してください')
    return
  }
  submitting.value = true
  try {
    const payload = {
      product_cd: form.product_cd,
      label_product_name: form.label_product_name || null,
      process_unit_qty: form.process_unit_qty,
      remark: form.remark?.trim() || null,
      paper_color: form.paper_color,
      product_name_color: form.product_name_color,
      supply_type: form.supply_type,
      upper_slots_locked: form.upper_slots_locked,
      process_slots: form.process_slots.map((s) => (String(s || '').trim() ? String(s).trim() : null)),
    }
    if (isEdit.value && form.id) {
      await updateProductLabelConfig(form.id, payload)
      ElMessage.success('更新しました')
    } else {
      await createProductLabelConfig(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    await loadList()
    await loadAvailableProducts()
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

async function handleSyncFromMaster() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '製品マスタの未登録製品（製品CD末尾「1」）を一括取込します。枠1〜3：設備、枠4：手直し、枠5〜8：工程を自動設定します。よろしいですか？',
      'マスタ取込',
      { type: 'info' }
    )
    syncing.value = true
    const res = await syncProductLabelFromMaster()
    const added = res?.data?.added ?? 0
    ElMessage.success(`取込完了：${added} 件を追加しました`)
    await loadList()
    await loadAvailableProducts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('マスタ取込に失敗しました')
  } finally {
    syncing.value = false
  }
}

async function handleUpperLockChange(row: ProductLabelConfig, val: boolean) {
  if (!guardMasterOperation(canEdit) || !row.id) return
  const prev = !!row.upper_slots_locked
  try {
    await updateProductLabelConfig(row.id, { upper_slots_locked: val })
    row.upper_slots_locked = val
    ElMessage.success(val ? '固定をONにしました' : '固定をOFFにしました')
  } catch {
    row.upper_slots_locked = prev
    ElMessage.error('固定の更新に失敗しました')
  }
}

async function handleImportFromMaster(row: ProductLabelConfig) {
  if (!guardMasterOperation(canEdit)) return
  try {
    const lockNote = row.upper_slots_locked
      ? '固定ONのため、枠1〜8は維持され導出結果は反映されません。'
      : ''
    await ElMessageBox.confirm(
      `製品 ${row.product_cd} の設定を製品マスタと工程ルートで上書き取込します。${lockNote}よろしいですか？`,
      'マスタ取込',
      { type: 'warning' }
    )
    await importProductLabelFromMaster(row.product_cd)
    ElMessage.success('マスタから取込みました')
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('マスタ取込に失敗しました')
  }
}

async function applyDerivedSlots(productCd: string) {
  deriving.value = true
  try {
    const res = await deriveProductLabelProcesses(productCd)
    const data = res as ProductLabelConfig & { upper_preserved?: boolean }
    const slots = data.process_slots
    if (Array.isArray(slots)) {
      form.process_slots = [...slots]
      while (form.process_slots.length < 8) form.process_slots.push(null)
      ElMessage.success(
        data.upper_preserved ? '固定ONのため枠は維持しました' : '枠を導出しました'
      )
    }
  } catch {
    ElMessage.error('枠導出に失敗しました')
  } finally {
    deriving.value = false
  }
}

async function handleDeriveAll() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '登録済みの全製品について枠を再導出します。固定ONの製品は枠1〜8を維持し、導出結果は反映されません。よろしいですか？',
      '一括枠導出',
      { type: 'warning' }
    )
    derivingAll.value = true
    const res = await deriveAllProductLabelProcesses()
    const updated = res?.data?.updated ?? 0
    const skipped = res?.data?.skipped ?? 0
    const upperPreserved = res?.data?.upper_preserved ?? 0
    const lockNote = upperPreserved > 0 ? `、固定 ${upperPreserved} 件` : ''
    const suffix = skipped > 0 ? `（スキップ ${skipped} 件）` : ''
    ElMessage.success(`一括導出完了：${updated} 件を更新しました${lockNote}${suffix}`)
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('一括枠導出に失敗しました')
  } finally {
    derivingAll.value = false
  }
}

async function handleDerive(row: ProductLabelConfig) {
  if (!guardMasterOperation(canEdit)) return
  try {
    const lockNote = row.upper_slots_locked
      ? '固定ONのため、枠1〜8は維持され導出結果は反映されません。'
      : ''
    await ElMessageBox.confirm(
      `設備能率・工程ルートから8枠を再導出します。${lockNote}よろしいですか？`,
      '枠導出',
      { type: 'warning' }
    )
    deriving.value = true
    const res = await deriveProductLabelProcesses(row.product_cd)
    const preserved = (res as ProductLabelConfig & { upper_preserved?: boolean }).upper_preserved
    ElMessage.success(preserved ? '固定ONのため枠は維持しました' : '枠を導出しました')
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('枠導出に失敗しました')
  } finally {
    deriving.value = false
  }
}

async function handleDeriveInDialog() {
  if (!form.product_cd) {
    editDialogTab.value = 'basic'
    ElMessage.warning('製品CDを選択してください')
    return
  }
  await applyDerivedSlots(form.product_cd)
}

async function handleDelete(row: ProductLabelConfig) {
  if (!guardMasterOperation(canDelete) || !row.id) return
  try {
    await ElMessageBox.confirm(`製品 ${row.product_cd} の設定を削除しますか？`, '削除確認', { type: 'warning' })
    await deleteProductLabelConfig(row.id)
    ElMessage.success('削除しました')
    await loadList()
    await loadAvailableProducts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('削除に失敗しました')
  }
}

onMounted(async () => {
  updateLayoutMetrics()
  window.addEventListener('resize', updateLayoutMetrics)
  await Promise.all([loadList(), loadAvailableProducts()])
  updateLayoutMetrics()
})

onUnmounted(() => {
  if (keywordTimer) clearTimeout(keywordTimer)
  window.removeEventListener('resize', updateLayoutMetrics)
})
</script>

<style scoped>
.plc-page {
  padding: 12px 16px 16px;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background:
    radial-gradient(ellipse 80% 50% at 10% -10%, rgba(13, 148, 136, 0.12), transparent 55%),
    radial-gradient(ellipse 60% 40% at 95% 0%, rgba(8, 145, 178, 0.1), transparent 50%),
    linear-gradient(165deg, #f1f5f9 0%, #ecfdf5 38%, #f8fafc 100%);
}

/* ── ヒーローヘッダー ── */
.plc-hero {
  border-radius: 14px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #0f766e 0%, #0d9488 42%, #0891b2 78%, #0284c7 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.22) inset,
    0 8px 24px rgba(13, 148, 136, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.08);
}

.plc-hero-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.plc-title-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.plc-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 4px 12px rgba(0, 0, 0, 0.15);
}

.plc-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.plc-subtitle {
  margin: 4px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.45;
  max-width: 520px;
}

.plc-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.22);
  flex-shrink: 0;
  min-width: 88px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 4px 14px rgba(0, 0, 0, 0.12);
  transition: transform 0.2s ease, background 0.2s ease;
}

.plc-stat:hover {
  background: rgba(255, 255, 255, 0.22);
  transform: translateY(-1px);
}

.plc-stat-num {
  font-size: 24px;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.plc-stat-lbl {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 2px;
  font-weight: 600;
}

/* ── ツールバーカード ── */
.plc-toolbar-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 16px rgba(15, 118, 110, 0.08),
    0 1px 3px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.plc-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 14px;
}

.plc-search-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 240px;
  flex: 1 1 240px;
  max-width: 360px;
}

.plc-search-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  letter-spacing: 0.02em;
}

.plc-search :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 1px 3px rgba(15, 23, 42, 0.06),
    0 0 0 1px rgba(13, 148, 136, 0.12);
  transition: box-shadow 0.2s ease;
}

.plc-search :deep(.el-input__wrapper:hover),
.plc-search :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 8px rgba(13, 148, 136, 0.12),
    0 0 0 1px rgba(13, 148, 136, 0.35);
}

.plc-toolbar-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

/* ── 立体ボタン共通 ── */
.plc-btn {
  border: none !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  letter-spacing: 0.02em;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease !important;
}

.plc-btn:not(:disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.05);
}

.plc-btn:not(:disabled):active {
  transform: translateY(1px);
  filter: brightness(0.97);
}

.plc-btn:disabled {
  opacity: 0.55;
  filter: grayscale(0.2);
}

.plc-btn--refresh {
  color: #475569 !important;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 3px 0 #cbd5e1,
    0 4px 10px rgba(100, 116, 139, 0.2) !important;
}

.plc-btn--refresh:not(:disabled):active {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 1px 0 #cbd5e1,
    0 2px 4px rgba(100, 116, 139, 0.15) !important;
}

.plc-btn--print {
  color: #fff !important;
  background: linear-gradient(180deg, #34d399 0%, #10b981 45%, #059669 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 3px 0 #047857,
    0 4px 12px rgba(5, 150, 105, 0.4) !important;
}

.plc-btn--print:not(:disabled):active {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 1px 0 #047857,
    0 2px 6px rgba(5, 150, 105, 0.3) !important;
}

.plc-btn--outsource {
  color: #fff !important;
  background: linear-gradient(180deg, #a78bfa 0%, #7c3aed 45%, #6d28d9 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 3px 0 #5b21b6,
    0 4px 12px rgba(124, 58, 237, 0.4) !important;
}

.plc-btn--outsource:not(:disabled):active {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.22) inset,
    0 1px 0 #5b21b6,
    0 2px 6px rgba(124, 58, 237, 0.3) !important;
}

.plc-btn--sync {
  color: #fff !important;
  background: linear-gradient(180deg, #22d3ee 0%, #06b6d4 45%, #0891b2 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 3px 0 #0e7490,
    0 4px 12px rgba(8, 145, 178, 0.38) !important;
}

.plc-btn--sync:not(:disabled):active {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 1px 0 #0e7490,
    0 2px 6px rgba(8, 145, 178, 0.28) !important;
}

.plc-btn--derive {
  color: #fff !important;
  background: linear-gradient(180deg, #fbbf24 0%, #f59e0b 45%, #d97706 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.32) inset,
    0 3px 0 #b45309,
    0 4px 12px rgba(217, 119, 6, 0.38) !important;
}

.plc-btn--derive:not(:disabled):active {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.26) inset,
    0 1px 0 #b45309,
    0 2px 6px rgba(217, 119, 6, 0.28) !important;
}

.plc-btn--create {
  color: #fff !important;
  background: linear-gradient(180deg, #2dd4bf 0%, #14b8a6 40%, #0d9488 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 4px 0 #0f766e,
    0 6px 16px rgba(13, 148, 136, 0.45) !important;
  padding-left: 14px !important;
  padding-right: 14px !important;
}

.plc-btn--create:not(:disabled):hover {
  transform: translateY(-3px);
}

.plc-btn--create:not(:disabled):active {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 2px 0 #0f766e,
    0 3px 8px rgba(13, 148, 136, 0.35) !important;
}

.plc-table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  border: 1px solid rgba(13, 148, 136, 0.1);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 6px 20px rgba(15, 118, 110, 0.1),
    0 2px 6px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.plc-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 14px;
  font-size: 11px;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.plc-result-text {
  white-space: nowrap;
  font-weight: 600;
  color: #475569;
}

.plc-table {
  flex: 1;
  min-height: 0;
}

.plc-table :deep(.el-table__inner-wrapper) {
  border-radius: 0 0 12px 12px;
}

.plc-table :deep(.el-table__row:hover > td) {
  background: #f0fdfa !important;
}

.plc-table :deep(.el-table__cell) {
  padding: 5px 0;
  font-size: 12px;
}

.plc-paper-chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
}

.plc-color-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  vertical-align: middle;
}

.plc-inline-select {
  width: 100%;
}

.plc-inline-select :deep(.el-select__wrapper) {
  padding: 0 6px;
  min-height: 26px;
}

.plc-table-color-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: nowrap;
  max-width: 100%;
}

.plc-name-color-preview {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
}

.plc-table-color-select {
  width: 28px;
  flex-shrink: 0;
}

.plc-table-color-select :deep(.el-select__wrapper) {
  padding: 0 4px;
  min-height: 24px;
}

.plc-table-color-select :deep(.el-select__selected-item),
.plc-table-color-select :deep(.el-select__placeholder) {
  display: none;
}

.plc-opt-paper {
  display: inline-block;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.8;
}

.plc-opt-color {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.plc-slot-cell {
  font-size: 11px;
  font-weight: 600;
  color: #334155;
}

.plc-slot-cell.is-empty {
  color: #cbd5e1;
  font-weight: 400;
}

.plc-slot-top {
  color: #0f766e;
}

.plc-slot-bottom {
  color: #475569;
}

.plc-row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex-wrap: nowrap;
}

/* ダイアログ */
.plc-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.15) inset,
    0 20px 50px rgba(15, 23, 42, 0.2),
    0 8px 20px rgba(13, 148, 136, 0.12);
}

.plc-dialog :deep(.el-dialog__header) {
  padding: 12px 16px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 55%, #0284c7 100%);
  border-radius: 12px 12px 0 0;
  margin-right: 0;
}

.plc-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.plc-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.85);
}

.plc-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 6px;
}

.plc-edit-tabs {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.plc-edit-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: linear-gradient(180deg, #f0fdfa 0%, #ecfeff 100%);
  padding: 6px 10px 0;
  border-bottom: 1px solid #e2e8f0;
}

.plc-edit-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.plc-edit-tabs :deep(.el-tabs__item) {
  font-size: 12px;
  font-weight: 600;
  padding: 7px 14px;
  color: #64748b;
  border-radius: 6px 6px 0 0;
  margin-right: 2px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.plc-edit-tabs :deep(.el-tabs__item:hover) {
  color: #0d9488;
  background: rgba(13, 148, 136, 0.08);
}

.plc-edit-tabs :deep(.el-tabs__item.is-active) {
  color: #0f766e;
  background: #fff;
  border-color: #e2e8f0;
  border-bottom-color: #fff;
  font-weight: 700;
}

.plc-edit-tabs :deep(.el-tabs__content) {
  padding: 0;
  min-height: 300px;
  max-height: min(52vh, 440px);
  overflow-y: auto;
  background: #fff;
}

.plc-tab-pane {
  padding: 10px 12px 8px;
}

.plc-form :deep(.el-form-item__label) {
  color: #0f766e;
  font-weight: 700;
  font-size: 11px;
  padding-bottom: 2px;
  line-height: 1.3;
}

.plc-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.plc-form-section {
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.plc-section-title {
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px dashed #cbd5e1;
}

.plc-section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 4px;
}

.plc-section-hint {
  margin: 0 0 6px;
}

.plc-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 10px;
}

.plc-span-full {
  grid-column: 1 / -1;
}

.plc-form-actions {
  display: flex;
  gap: 8px;
  padding-top: 4px;
}

.plc-field-hint {
  margin-top: 4px;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.3;
}

.plc-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.plc-btn-cancel {
  border-radius: 8px;
  font-weight: 600 !important;
  color: #64748b !important;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%) !important;
  border: none !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 0 #cbd5e1,
    0 3px 8px rgba(100, 116, 139, 0.15) !important;
}

.plc-btn-cancel:active {
  transform: translateY(1px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 1px 0 #cbd5e1,
    0 2px 4px rgba(100, 116, 139, 0.12) !important;
}

.plc-btn-save {
  border-radius: 8px;
  font-weight: 700 !important;
  color: #fff !important;
  background: linear-gradient(180deg, #2dd4bf 0%, #14b8a6 50%, #0d9488 100%) !important;
  border: none !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 3px 0 #0f766e,
    0 4px 12px rgba(13, 148, 136, 0.35) !important;
}

.plc-btn-save:active {
  transform: translateY(1px);
}

.plc-btn-print {
  border-radius: 8px;
  font-weight: 700 !important;
  color: #fff !important;
  background: linear-gradient(180deg, #34d399 0%, #10b981 50%, #059669 100%) !important;
  border: none !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 3px 0 #047857,
    0 4px 12px rgba(5, 150, 105, 0.35) !important;
}

.plc-btn-print:active {
  transform: translateY(1px);
}

/* 印刷ダイアログ */
.plc-print-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plc-print-product {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: #f0fdfa;
  border-radius: 8px;
  border: 1px solid #99f6e4;
}

.plc-print-cd {
  font-size: 11px;
  color: #64748b;
  font-family: monospace;
}

.plc-print-name-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}

.plc-print-name-label {
  flex-shrink: 0;
  font-size: 11px;
  color: #64748b;
  min-width: 72px;
}

.plc-print-master-name {
  font-size: 14px;
  color: #0f172a;
  word-break: break-all;
}

.plc-print-label-name {
  font-size: 14px;
  word-break: break-all;
}

.plc-print-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: #fffbeb;
  border: 2px solid #fbbf24;
  border-radius: 8px;
}

.plc-print-settings-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.plc-print-settings-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.plc-print-settings-label {
  font-size: 12px;
  color: #92400e;
  white-space: nowrap;
}

.plc-print-settings-qty {
  padding-top: 8px;
  border-top: 1px dashed #fcd34d;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
}

.plc-print-remark {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
  min-width: 0;
}

.plc-print-remark-val {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
  word-break: break-word;
}

.plc-print-qty-block {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.plc-print-name-color {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.plc-print-qty-val {
  font-size: 16px;
  color: #0f766e;
}

.plc-print-paper-val {
  padding: 2px 12px;
  border-radius: 999px;
  font-size: 16px;
  font-weight: 800;
}

.plc-print-hint {
  margin-left: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.plc-print-initial-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.plc-print-note {
  margin: 0;
  font-size: 11px;
  color: #64748b;
}

.plc-print-all-summary {
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  margin-bottom: 10px;
}

.plc-print-all-lead {
  margin: 0 0 6px;
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
}

.plc-print-all-lead strong {
  color: #0d9488;
  font-size: 16px;
}

.plc-outsource-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plc-outsource-lead {
  margin: 0;
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
}

.plc-outsource-mail {
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.plc-outsource-mail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #0f766e;
}

.plc-outsource-mail-stat {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.plc-outsource-alert {
  margin-bottom: 8px;
}

.plc-outsource-form {
  margin-bottom: 0;
}

@media (max-width: 1200px) {
  .plc-hero-inner {
    flex-wrap: wrap;
  }

  .plc-search-wrap {
    flex: 1 1 220px;
    min-width: 180px;
    max-width: none;
  }
}

@media (max-width: 900px) {
  .plc-page {
    padding: 8px 10px 10px;
  }

  .plc-hero {
    padding: 12px 14px;
  }

  .plc-hero-inner {
    flex-direction: column;
    align-items: stretch;
  }

  .plc-stat {
    align-self: flex-start;
    flex-direction: row;
    gap: 10px;
    padding: 8px 14px;
  }

  .plc-stat-num {
    font-size: 20px;
  }

  .plc-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .plc-search-wrap {
    width: 100%;
    max-width: none;
  }

  .plc-toolbar-actions {
    margin-left: 0;
    width: 100%;
  }

  .plc-toolbar-actions :deep(.plc-btn) {
    flex: 1 1 auto;
    min-width: 0;
  }
}

@media (max-width: 768px) {
  .plc-title {
    font-size: 16px;
  }

  .plc-subtitle {
    font-size: 10px;
  }

  .plc-result-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .plc-result-bar :deep(.el-pagination) {
    justify-content: center;
    flex-wrap: wrap;
  }

  .plc-row-actions {
    flex-direction: column;
    gap: 0;
  }

  .plc-edit-tabs :deep(.el-tabs__content) {
    min-height: 240px;
    max-height: min(48vh, 380px);
  }
}

@media (max-width: 480px) {
  .plc-page {
    padding: 6px 8px 8px;
  }

  .plc-title-icon {
    width: 32px;
    height: 32px;
  }

  .plc-toolbar-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .plc-toolbar-actions :deep(.plc-btn) {
    width: 100%;
    margin: 0;
  }
}
</style>
