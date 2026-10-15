<template>
  <div class="eqc-page eqc-modern pb-std" :class="`eqc-page--${processCd}`">
    <header class="eqc-hero page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="pb-bubbles" aria-hidden="true" />
      <div class="eqc-hero__main">
        <span class="eqc-mark" aria-hidden="true">{{ mark }}</span>
        <div class="eqc-hero__titles">
          <h1 class="pb-hero-title">{{ processLabel }}設備能力</h1>
          <p class="pb-hero-desc">定時間・直・残業・能率/H・作業率・合格率から、設備の月間負荷を見ます。</p>
        </div>
      </div>
      <div class="eqc-hero__side">
        <nav class="eqc-switch" aria-label="工程">
          <button
            v-for="item in PROCESSES"
            :key="item.cd"
            type="button"
            class="eqc-switch__btn"
            :class="[`is-${item.cd}`, { 'is-on': item.cd === processCd }]"
            @click="goProcess(item.path)"
          >
            {{ item.label }}
          </button>
        </nav>
        <div class="eqc-hero__actions">
          <el-button
            class="tb-btn tb-btn-slate"
            size="small"
            :loading="printingAll"
            :disabled="!listedEquipments.length"
            @click="printAllEquipments"
          >
            <el-icon><Printer /></el-icon>
            <span class="tb-label">全設備印刷</span>
          </el-button>
          <el-button class="tb-btn tb-btn-amber" size="small" @click="openAdd">
            <el-icon><Plus /></el-icon>
            <span class="tb-label">設備を追加</span>
          </el-button>
          <el-button class="tb-btn tb-btn-teal" size="small" @click="openImport">
            <el-icon><Download /></el-icon>
            <span class="tb-label">マスタから取込</span>
            <span v-if="suggestions.length" class="eqc-count">{{ suggestions.length }}</span>
          </el-button>
        </div>
      </div>
    </header>

    <section class="eqc-kpis" aria-label="能力サマリ">
      <span class="eqc-kpis__scope">{{ kpiTitle }}</span>
      <div class="eqc-kpis__strip">
        <article class="eqc-kpi eqc-kpi--blue">
          <span class="eqc-kpi__icon"><el-icon :size="14"><Timer /></el-icon></span>
          <div class="eqc-kpi__body">
            <span class="eqc-kpi__lbl">月間総時間</span>
            <strong>{{ fmtNum(kpi.total_hours) }}<small>H</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--purple">
          <span class="eqc-kpi__icon"><el-icon :size="14"><Histogram /></el-icon></span>
          <div class="eqc-kpi__body">
            <span class="eqc-kpi__lbl">所要時間</span>
            <strong>{{ fmtNum(kpi.occupied_hours) }}<small>H</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--amber">
          <span class="eqc-kpi__icon"><el-icon :size="14"><PieChart /></el-icon></span>
          <div class="eqc-kpi__body">
            <span class="eqc-kpi__lbl">負荷率</span>
            <strong :class="loadToneClass(kpi.occupancy_pct)">{{ fmtNum(kpi.occupancy_pct) }}<small>%</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--green">
          <span class="eqc-kpi__icon"><el-icon :size="14"><CircleCheck /></el-icon></span>
          <div class="eqc-kpi__body">
            <span class="eqc-kpi__lbl">月当判定</span>
            <strong :class="judgeClass(kpi.month_judgment)">{{ judgmentLabel(kpi.month_judgment) }}</strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--teal">
          <span class="eqc-kpi__icon"><el-icon :size="14"><Clock /></el-icon></span>
          <div class="eqc-kpi__body">
            <span class="eqc-kpi__lbl">残時間</span>
            <strong :class="{ 'is-neg': kpi.remain_hours < -0.05 }">{{ fmtNum(kpi.remain_hours) }}<small>H</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--pink">
          <span class="eqc-kpi__icon"><el-icon :size="14"><Odometer /></el-icon></span>
          <div class="eqc-kpi__body">
            <span class="eqc-kpi__lbl">平均能率</span>
            <strong>{{ fmtNum(kpi.avg_hourly) }}<small>本/H</small></strong>
          </div>
        </article>
      </div>
    </section>

    <div class="eqc-body">
      <aside v-loading="listLoading" class="eqc-list">
        <div class="eqc-list__head">
          <el-input v-model="keyword" size="small" clearable placeholder="設備名・コード" />
          <span class="eqc-list__meta">
            <em>{{ listedEquipments.length }}台</em>
            <em class="eqc-list__meta-rate" title="一覧の平均能率">平均能率 <b>{{ fmtNum(aggregate.avg_hourly) }}</b></em>
            <em class="eqc-list__meta-load" title="一覧の平均負荷率">平均負荷 <b :class="loadToneClass(aggregate.occupancy_pct)">{{ fmtNum(aggregate.occupancy_pct) }}%</b></em>
            <b
              v-if="aggregate.month_judgment"
              :class="judgeClass(aggregate.month_judgment)"
            >{{ judgmentLabel(aggregate.month_judgment) }}</b>
          </span>
        </div>
        <button
          v-for="eq in visibleEquipments"
          :key="eq.id"
          type="button"
          class="eqc-card"
          :class="[cardClass(eq), { 'is-on': eq.id === selectedId }]"
          @click="openEquipment(eq.id)"
        >
          <span class="eqc-card__name" :title="eq.machine_cd">{{ eq.machine_name }}</span>
          <span class="eqc-card__metric eqc-card__metric--rate" title="平均能率">
            <small>平均</small>
            <b>{{ fmtNum(cardSummary(eq).avg_hourly) }}</b>
          </span>
          <span class="eqc-card__metric eqc-card__metric--load" title="負荷率">
            <small>負荷</small>
            <b :class="loadToneClass(cardSummary(eq).occupancy_pct)">{{ fmtNum(cardSummary(eq).occupancy_pct) }}%</b>
          </span>
        </button>
        <p v-if="!listLoading && !visibleEquipments.length" class="eqc-muted">
          この工程の設備はまだありません。追加するか、マスタから取り込んでください。
        </p>
      </aside>

      <section v-if="draft" v-loading="detailLoading" class="eqc-detail">
        <div class="eqc-panel">
          <div class="eqc-cond">
            <div class="eqc-cond__group eqc-cond__group--id">
              <span class="eqc-cond__tag">設備</span>
              <label class="eqc-field eqc-field--grow">
                <span>設備名</span>
                <el-input v-model="draft.machine_name" size="small" maxlength="100" @input="touch" />
              </label>
              <label class="eqc-field eqc-field--cd">
                <span>コード</span>
                <el-input v-model="draft.machine_cd" size="small" maxlength="50" @input="touch" />
              </label>
            </div>
            <div class="eqc-cond__group eqc-cond__group--cap">
              <span class="eqc-cond__tag">稼働条件</span>
              <label class="eqc-field eqc-field--sm">
                <span>定時 h/直</span>
                <el-input-number v-model="draft.regular_hours" size="small" :min="0" :max="24" :step="0.1" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" @change="onCondChange" />
              </label>
              <label class="eqc-field eqc-field--xs">
                <span>直</span>
                <el-input-number v-model="draft.shift_count" size="small" :min="1" :max="3" :step="0.1" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" @change="onCondChange" />
              </label>
              <label class="eqc-field eqc-field--sm">
                <span>残業 h/直</span>
                <el-input-number v-model="draft.overtime_hours" size="small" :min="0" :max="12" :step="0.1" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" @change="onCondChange" />
              </label>
              <label class="eqc-field eqc-field--sm">
                <span>稼働日</span>
                <el-input-number v-model="draft.working_days" size="small" :min="0" :max="31" :step="1" :precision="0" :formatter="eqcIntFormatter" :parser="eqcNumParser" :controls="false" @change="onWorkingDaysChange" />
              </label>
            </div>
            <div class="eqc-cond__group eqc-cond__group--calc">
              <span class="eqc-cond__tag">算出</span>
              <div class="eqc-mini eqc-mini--day">
                <span>1日稼働</span>
                <b>{{ fmtNum(headerCalc.daily_available) }}<small>H</small></b>
              </div>
              <div class="eqc-mini eqc-mini--month">
                <span>月間総時間</span>
                <b>{{ fmtNum(headerCalc.total_hours) }}<small>H</small></b>
              </div>
            </div>
          </div>

          <div class="eqc-actions">
            <label class="eqc-month">
              <span>対象月</span>
              <el-button
                class="eqc-month__nav"
                size="small"
                :disabled="!targetMonth"
                title="前月"
                @click="shiftTargetMonth(-1)"
              >
                <el-icon><ArrowLeft /></el-icon>
                <span>前月</span>
              </el-button>
              <el-date-picker
                v-model="targetMonth"
                type="month"
                value-format="YYYY-MM"
                size="small"
                :clearable="false"
                placeholder="年月"
              />
              <el-button
                class="eqc-month__nav"
                size="small"
                :disabled="!targetMonth"
                title="翌月"
                @click="shiftTargetMonth(1)"
              >
                <span>翌月</span>
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </label>
            <div class="eqc-actions__btns">
              <el-button class="tb-btn tb-btn-amber" size="small" :loading="loadingForecast" :disabled="!targetMonth" @click="applyForecast">
                <span class="tb-label">内示を反映</span>
              </el-button>
              <el-button class="tb-btn tb-btn-blue" size="small" @click="addRow">
                <el-icon><Plus /></el-icon>
                <span class="tb-label">行追加</span>
              </el-button>
              <el-button class="tb-btn tb-btn-slate" size="small" :loading="printingOne" @click="printCurrentEquipment">
                <el-icon><Printer /></el-icon>
                <span class="tb-label">印刷</span>
              </el-button>
              <el-button class="tb-btn tb-btn-rose" size="small" @click="removeEquipment">
                <span class="tb-label">削除</span>
              </el-button>
              <el-button class="tb-btn tb-btn-save" size="small" :loading="saving" :disabled="!dirty" @click="save">
                <span class="tb-label">保存</span>
              </el-button>
            </div>
            <div class="eqc-actions__judge">
              <el-button class="tb-btn tb-btn-slate" size="small" @click="formulaOpen = true">
                <el-icon><Document /></el-icon>
                <span class="tb-label">計算式</span>
              </el-button>
              <span class="eqc-chip eqc-chip--slate">日当 <b :class="judgeClass(totals.daily_judgment)">{{ judgmentLabel(totals.daily_judgment) }}</b></span>
              <span class="eqc-chip eqc-chip--green">月当 <b :class="judgeClass(totals.month_judgment)">{{ judgmentLabel(totals.month_judgment) }}</b></span>
              <span class="eqc-chip eqc-chip--amber">負荷 <b :class="loadToneClass(totals.occupancy_pct)">{{ fmtNum(totals.occupancy_pct) }}%</b></span>
            </div>
          </div>
        </div>

        <div v-if="sharedHintCount > 0" class="eqc-shared-banner" role="status">
          <span class="eqc-shared-banner__mark" aria-hidden="true">共</span>
          <div class="eqc-shared-banner__body">
            <strong>同一製品・他設備あり</strong>
            <span>
              この工程では、同じ製品を複数設備で生産できます。本設備に
              <b>{{ sharedHintCount }}</b>
              件（紫バッジ）— 他設備でも登録されています。
            </span>
          </div>
        </div>
        <div class="eqc-table-body">
        <el-table
          :key="`eqc-tbl-${draft.id}`"
          :data="draft.items"
          size="small"
          border
          stripe
          class="eqc-table"
          height="100%"
          :row-style="{ height: '32px' }"
          :row-class-name="eqcRowClassName"
          :default-sort="{ prop: 'part_name', order: 'ascending' }"
          :header-cell-class-name="eqcHeaderCellClass"
          :cell-class-name="eqcBodyCellClass"
          @sort-change="onPartNameSort"
        >
          <el-table-column label="#" width="40" fixed="left" align="center">
            <template #default="{ $index }"><span class="eqc-idx">{{ $index + 1 }}</span></template>
          </el-table-column>
          <el-table-column label="製品CD" width="110" fixed="left">
            <template #default="{ row }">
              <span class="eqc-part-cell">
                <span class="eqc-lock eqc-lock--cd" :title="row.part_no || ''">{{ row.part_no || '—' }}</span>
                <el-tooltip
                  v-if="sharedTipText(row)"
                  :content="sharedTipText(row)"
                  placement="top"
                  effect="dark"
                >
                  <span class="eqc-shared-tag">他設備</span>
                </el-tooltip>
              </span>
            </template>
          </el-table-column>
          <el-table-column
            label="製品名"
            prop="part_name"
            width="125"
            fixed="left"
            sortable
            show-overflow-tooltip
          >
            <template #default="{ row }"><span class="eqc-lock">{{ row.part_name || '—' }}</span></template>
          </el-table-column>
          <el-table-column label="材料" width="130" fixed="left" show-overflow-tooltip>
            <template #default="{ row }"><span class="eqc-lock eqc-lock--mat">{{ row.material || '—' }}</span></template>
          </el-table-column>
          <el-table-column label="内示/月" width="92" align="right">
            <template #default="{ row }">
              <el-input-number v-model="row.monthly_qty" size="small" :min="0" :step="100" :precision="0" :formatter="eqcIntFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="日数" width="72" align="right">
            <template #header><span title="内示に対する稼働日数">日数</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.qty_days" size="small" :min="0" :max="31" :precision="0" :formatter="eqcIntFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="日当" width="72" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).daily_qty, 0) }}</span></template>
          </el-table-column>
          <el-table-column label="能率/H" width="80" align="right">
            <template #header><span title="設備能率テーブルの本/H">能率/H</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.rate_per_hour" size="small" :min="0" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="作業率%" width="76" align="right">
            <template #header><span title="設備マスタの作業率">作業率%</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.availability_pct" size="small" :min="0" :max="100" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="合格率%" width="76" align="right">
            <template #header><span title="廃棄率分析と同口径・直近3ヶ月実績の加重平均">合格率%</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.pass_rate_pct" size="small" :min="0" :max="100" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="生産H" width="72" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).production_hours) }}</span></template>
          </el-table-column>
          <el-table-column label="段取H" width="72" align="right">
            <template #header><span title="月1回のみ。所要時間に1回加算（日数倍しない）">段取H</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.setup_hours" size="small" :min="0" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="稼働H" width="72" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).operating_hours) }}</span></template>
          </el-table-column>
          <el-table-column label="実日数" width="72" align="right">
            <template #default="{ row }">
              <el-input-number v-model="row.actual_days" size="small" :min="0" :max="31" :precision="0" :formatter="eqcIntFormatter" :parser="eqcNumParser" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="加重H" width="72" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).weighted_hours) }}</span></template>
          </el-table-column>
          <el-table-column label="所要H" width="72" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).occupied_hours) }}</span></template>
          </el-table-column>
          <el-table-column label="負荷%" width="64" align="right">
            <template #default="{ row }">
              <span class="eqc-ro eqc-ro--pct" :class="loadToneClass(lineCalc(row).occupancy_pct)">{{ fmtNum(lineCalc(row).occupancy_pct) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="判定" width="52" align="center">
            <template #default="{ row }">
              <b class="eqc-judge" :class="judgeClass(lineCalc(row).daily_judgment)">{{ judgmentLabel(lineCalc(row).daily_judgment) }}</b>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="118" align="center" class-name="eqc-col-ops">
            <template #default="{ row }">
              <div class="eqc-ops">
                <el-button
                  class="eqc-row-btn eqc-row-btn--indigo"
                  size="small"
                  :disabled="!row.part_no && !row.part_name"
                  @click="openTransfer(row)"
                >移転</el-button>
                <el-button class="eqc-row-btn eqc-row-btn--rose" size="small" @click="removeRow(row.key)">削除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </section>

      <section v-else class="eqc-placeholder">
        <el-empty description="設備を選ぶと、品目ごとの能力と負荷を編集できます">
          <el-button class="tb-btn tb-btn-amber" size="small" @click="openAdd">
            <el-icon><Plus /></el-icon>
            <span class="tb-label">設備を追加</span>
          </el-button>
          <el-button class="tb-btn tb-btn-teal" size="small" @click="openImport">
            <el-icon><Download /></el-icon>
            <span class="tb-label">マスタから取込</span>
          </el-button>
        </el-empty>
      </section>
    </div>

    <el-dialog
      v-model="addOpen"
      width="520px"
      class="eqc-dialog pb-std"
      align-center
      :show-close="false"
      append-to-body
    >
      <template #header>
        <div class="eqc-dlg-header eqc-dlg-header--amber">
          <div class="eqc-dlg-header__accent" />
          <div class="eqc-dlg-header__main">
            <span class="eqc-dlg-header__icon"><el-icon :size="20"><Plus /></el-icon></span>
            <div>
              <h3 class="eqc-dlg-header__title">設備を追加</h3>
              <p class="eqc-dlg-header__desc">この工程に新しい設備ヘッダを登録します</p>
            </div>
          </div>
        </div>
      </template>
      <div class="eqc-form">
        <label><span>設備コード</span><el-input v-model="addForm.machine_cd" maxlength="50" /></label>
        <label><span>設備名</span><el-input v-model="addForm.machine_name" maxlength="100" /></label>
        <label><span>定時間 h/直</span><el-input-number v-model="addForm.regular_hours" :min="0" :max="24" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" /></label>
        <label><span>直</span><el-input-number v-model="addForm.shift_count" :min="1" :max="3" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" /></label>
        <label><span>残業 h/直</span><el-input-number v-model="addForm.overtime_hours" :min="0" :max="12" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" /></label>
        <label><span>稼働日数</span><el-input-number v-model="addForm.working_days" :min="0" :max="31" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" /></label>
      </div>
      <template #footer>
        <el-button @click="addOpen = false">キャンセル</el-button>
        <el-button class="eqc-dlg-ok eqc-dlg-ok--green" :loading="saving" @click="createEquipment">追加</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="importOpen"
      width="680px"
      class="eqc-dialog pb-std"
      align-center
      :show-close="false"
      append-to-body
    >
      <template #header>
        <div class="eqc-dlg-header eqc-dlg-header--teal">
          <div class="eqc-dlg-header__accent" />
          <div class="eqc-dlg-header__main">
            <span class="eqc-dlg-header__icon"><el-icon :size="20"><Download /></el-icon></span>
            <div>
              <h3 class="eqc-dlg-header__title">未登録の設備を取り込む</h3>
              <p class="eqc-dlg-header__desc">設備マスタ・設備能率から未登録分を追加します</p>
            </div>
          </div>
        </div>
      </template>
      <p class="eqc-dialog__lead">設備マスタと設備能率から、この工程の未登録設備を追加します。品目も取り込むと、能率/H・作業率・合格率を反映します。</p>
      <el-checkbox v-model="withProducts">品目（設備能率）も取り込む</el-checkbox>
      <el-table
        v-if="suggestions.length"
        :data="suggestions"
        size="small"
        border
        max-height="360"
        class="eqc-import-table"
        @selection-change="onImportPick"
      >
        <el-table-column type="selection" width="42" />
        <el-table-column prop="machine_cd" label="コード" width="140" />
        <el-table-column prop="machine_name" label="設備名" min-width="160" />
        <el-table-column label="出所" width="120">
          <template #default="{ row }">{{ sourceLabel(row.source) }}</template>
        </el-table-column>
        <el-table-column prop="product_count" label="品目" width="70" align="right" />
      </el-table>
      <el-empty v-else description="この工程に該当する未登録設備はありません。設備名に切断・面取・成型・溶接が含まれている必要があります。" />
      <template #footer>
        <el-button @click="importOpen = false">閉じる</el-button>
        <el-button class="eqc-dlg-ok eqc-dlg-ok--teal" :loading="importing" :disabled="!importPick.length" @click="runImport">
          {{ importPick.length }} 台を追加
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="taktOpen"
      width="720px"
      class="eqc-dialog pb-std"
      align-center
      :show-close="false"
      append-to-body
    >
      <template #header>
        <div class="eqc-dlg-header eqc-dlg-header--indigo">
          <div class="eqc-dlg-header__accent" />
          <div class="eqc-dlg-header__main">
            <span class="eqc-dlg-header__icon"><el-icon :size="20"><Timer /></el-icon></span>
            <div>
              <h3 class="eqc-dlg-header__title">タクトトライ</h3>
              <p class="eqc-dlg-header__desc">実測 CT と判定マークを記録します</p>
            </div>
          </div>
        </div>
      </template>
      <template v-if="taktRow">
        <p class="eqc-dialog__lead">{{ taktRow.part_no || '（品番未入力）' }} {{ taktRow.part_name }}</p>
        <div class="eqc-takt">
          <section>
            <h3>1回目</h3>
            <label><span>日付</span><el-date-picker v-model="taktRow.takt1_date" type="date" value-format="YYYY-MM-DD" size="small" @change="touch" /></label>
            <label><span>実測CT（秒）</span><el-input-number v-model="taktRow.takt1_ct" :min="0" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" size="small" @change="touch" /></label>
            <label><span>検査</span><el-select v-model="taktRow.takt1_inspect" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`a-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
            <label><span>準備状況</span><el-select v-model="taktRow.takt1_prep" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`b-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
            <label><span>総合</span><el-select v-model="taktRow.takt1_overall" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`c-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
          </section>
          <section>
            <h3>2回目</h3>
            <label><span>日付</span><el-date-picker v-model="taktRow.takt2_date" type="date" value-format="YYYY-MM-DD" size="small" @change="touch" /></label>
            <label><span>実測CT（秒）</span><el-input-number v-model="taktRow.takt2_ct" :min="0" :precision="1" :formatter="eqcNumFormatter" :parser="eqcNumParser" :controls="false" size="small" @change="touch" /></label>
            <label><span>検査</span><el-select v-model="taktRow.takt2_inspect" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`d-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
            <label><span>準備状況</span><el-select v-model="taktRow.takt2_prep" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`e-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
            <label><span>総合</span><el-select v-model="taktRow.takt2_overall" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`f-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
          </section>
        </div>
        <label class="eqc-takt-note">
          <span>備考</span>
          <el-input v-model="taktRow.remarks" maxlength="255" @input="touch" />
        </label>
      </template>
      <template #footer>
        <el-button class="eqc-dlg-ok eqc-dlg-ok--indigo" @click="taktOpen = false">閉じる</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="formulaOpen"
      width="640px"
      class="eqc-dialog pb-std"
      align-center
      :show-close="false"
      append-to-body
    >
      <template #header>
        <div class="eqc-dlg-header eqc-dlg-header--slate">
          <div class="eqc-dlg-header__accent" />
          <div class="eqc-dlg-header__main">
            <span class="eqc-dlg-header__icon"><el-icon :size="20"><Document /></el-icon></span>
            <div>
              <h3 class="eqc-dlg-header__title">計算式</h3>
              <p class="eqc-dlg-header__desc">生産能力調査と同じ口径です</p>
            </div>
          </div>
        </div>
      </template>
      <ul class="eqc-formula-list">
        <li>総時間 =（定時間 + 残業）× 直 × 稼働日数</li>
        <li>日当数 = 内示/月 ÷ 稼働日数</li>
        <li>生産時間 = 日当数 ÷ (能率/H × 作業率 × 合格率)</li>
        <li>段取H は月1回。日次には ÷ 実生産日数で按分し、所要時間には1回だけ加算（×実日数しない）</li>
        <li>稼働時間 = 生産時間 + 段取り÷実生産日数（生産が無い行は 0）</li>
        <li>加重平均 = 設定稼働日数 ÷ 実生産日数 × 生産時間 + 段取り÷実生産日数</li>
        <li>所要時間 = 設定稼働日数 × 生産時間 + 段取り。負荷率 = 所要時間合計 ÷ 総時間</li>
        <li>日当判定は加重平均が 1 日の稼働可能を超えると ×。月当判定は所要時間が総時間を超えると ×</li>
        <li>能率/H は設備能率、作業率は設備マスタ、合格率は廃棄率分析と同口径の直近3ヶ月実績から取得します</li>
        <li>「内示を反映」は、この設備に登録済みの品目だけ月受注の内示を反映します（他設備の製品・補給品・試作品は追加しません）</li>
        <li>稼働条件（定時・直・残業・稼働日）は手入力でき、変更すると 1日稼働・月間総時間・負荷判定が自動再計算されます。稼働日を変えると明細の日数・実日数にも反映されます</li>
        <li>「印刷」は選択中設備の稼働条件・品目明細を印刷します。「全設備印刷」は工程内の全設備を一覧サマリ付きでまとめて印刷します</li>
      </ul>
      <template #footer>
        <el-button class="eqc-dlg-ok eqc-dlg-ok--slate" @click="formulaOpen = false">閉じる</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="transferOpen"
      width="860px"
      class="eqc-dialog eqc-dialog--transfer pb-std"
      align-center
      :show-close="false"
      append-to-body
    >
      <template #header>
        <div class="eqc-dlg-header eqc-dlg-header--indigo">
          <div class="eqc-dlg-header__accent" />
          <div class="eqc-dlg-header__main">
            <span class="eqc-dlg-header__icon"><el-icon :size="20"><SwitchIcon /></el-icon></span>
            <div>
              <h3 class="eqc-dlg-header__title">他設備へ移転</h3>
              <p class="eqc-dlg-header__desc">この品目を同じ工程の別設備へ移します</p>
            </div>
          </div>
        </div>
      </template>
      <p v-if="transferRow" class="eqc-dialog__lead">
        <b>{{ transferRow.part_no || '（CDなし）' }}</b>
        {{ transferRow.part_name || '' }}
        <span class="eqc-muted">／ 内示 {{ fmtNum(transferRow.monthly_qty, 0) }}</span>
      </p>
      <p class="eqc-dialog__lead">移転先の設備を選んでください。先に同一品番がある場合は内示数量を合算します。</p>
      <el-radio-group v-model="transferTargetId" class="eqc-transfer-list">
        <el-radio
          v-for="eq in transferTargets"
          :key="eq.id"
          :value="eq.id"
          border
          class="eqc-transfer-item"
        >
          <span class="eqc-transfer-item__body">
            <span class="eqc-transfer-item__name">{{ eq.machine_name }}</span>
            <span class="eqc-transfer-item__cd">{{ eq.machine_cd }}</span>
          </span>
        </el-radio>
      </el-radio-group>
      <p v-if="!transferTargets.length" class="eqc-muted">移転先の設備がありません。先に別設備を追加してください。</p>
      <template #footer>
        <el-button @click="transferOpen = false">キャンセル</el-button>
        <el-button
          class="eqc-dlg-ok eqc-dlg-ok--indigo"
          :loading="transferring"
          :disabled="!transferTargetId || !transferTargets.length"
          @click="confirmTransfer"
        >移転する</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { TableColumnCtx } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  CircleCheck,
  Clock,
  Document,
  Download,
  Histogram,
  Odometer,
  PieChart,
  Plus,
  Printer,
  Switch as SwitchIcon,
  Timer,
} from '@element-plus/icons-vue'
import {
  createEquipmentCapacity,
  deleteEquipmentCapacity,
  fetchEquipmentCapacity,
  fetchEquipmentCapacityDetail,
  fetchEquipmentCapacityForecastMonthly,
  importEquipmentCapacityMaster,
  saveEquipmentCapacity,
  transferEquipmentCapacityItem,
  type CapacityItem,
  type CapacitySummary,
  type EquipmentListItem,
  type EquipmentSuggestion,
  type SharedProductInfo,
} from '@/api/erp/productionEquipmentCapacity'
import {
  calcHeader,
  calcLine,
  calcTotals,
  eqcIntFormatter,
  eqcNumFormatter,
  eqcNumParser,
  fmtNum,
  judgmentLabel,
  type Judgment,
  type TotalCalc,
} from './capacityCalc'
import {
  printCapacityReport,
  PRINT_POPUP_BLOCKED_MSG,
  type PrintEquipmentInput,
} from './equipmentCapacityPrint'

const PROCESSES = [
  { cd: 'cutting', label: '切断', path: '/erp/production/equipment-capacity/cutting' },
  { cd: 'chamfering', label: '面取', path: '/erp/production/equipment-capacity/chamfering' },
  { cd: 'forming', label: '成型', path: '/erp/production/equipment-capacity/forming' },
  { cd: 'welding', label: '溶接', path: '/erp/production/equipment-capacity/welding' },
] as const

const MARKS = ['', '○', '△', '×', '－']

interface DraftItem extends CapacityItem {
  key: string
}

interface Draft {
  id: number
  machine_cd: string
  machine_name: string
  regular_hours: number
  shift_count: number
  overtime_hours: number
  working_days: number
  note: string
  items: DraftItem[]
}

/** 列グループ：固定読取 / 入力 / 算出 / 操作 */
const EQC_COL_GROUP: Record<string, string> = {
  '#': 'eqc-col-meta',
  製品CD: 'eqc-col-meta',
  製品名: 'eqc-col-meta',
  材料: 'eqc-col-meta',
  '内示/月': 'eqc-col-edit',
  日数: 'eqc-col-edit',
  '能率/H': 'eqc-col-edit',
  '作業率%': 'eqc-col-edit',
  '合格率%': 'eqc-col-edit',
  段取H: 'eqc-col-edit',
  実日数: 'eqc-col-edit',
  日当: 'eqc-col-calc',
  生産H: 'eqc-col-calc',
  稼働H: 'eqc-col-calc',
  加重H: 'eqc-col-calc',
  所要H: 'eqc-col-calc',
  '負荷%': 'eqc-col-calc',
  判定: 'eqc-col-calc',
  操作: 'eqc-col-act',
}

function eqcHeaderCellClass(data: { column: TableColumnCtx<DraftItem>; rowIndex?: number }) {
  const label = data.column?.label
  return label && typeof label === 'string' ? (EQC_COL_GROUP[label] ?? '') : ''
}

function eqcBodyCellClass(data: {
  row: DraftItem
  column: TableColumnCtx<DraftItem>
  rowIndex: number
  columnIndex: number
}) {
  const label = data.column?.label
  return label && typeof label === 'string' ? (EQC_COL_GROUP[label] ?? '') : ''
}

const route = useRoute()
const router = useRouter()
const processCd = computed(() => String(route.meta.process || 'cutting'))
const processLabel = computed(() => PROCESSES.find((item) => item.cd === processCd.value)?.label || '切断')
const mark = computed(() => ({ cutting: '切', chamfering: '面', forming: '成', welding: '溶' }[processCd.value] || '設'))

function currentMonthValue() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

/** 対象月を delta ヶ月ずらす（-1=前月 / +1=翌月） */
function shiftTargetMonth(delta: number) {
  const raw = (targetMonth.value || currentMonthValue()).trim()
  const [yText, mText] = raw.split('-')
  let year = Number(yText)
  let month = Number(mText)
  if (!year || !month) {
    targetMonth.value = currentMonthValue()
    return
  }
  const d = new Date(year, month - 1 + delta, 1)
  targetMonth.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const listLoading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const importing = ref(false)
const printingOne = ref(false)
const printingAll = ref(false)
const loadingForecast = ref(false)
const hydrating = ref(false)
const dirty = ref(false)
const keyword = ref('')
const targetMonth = ref(currentMonthValue())
const equipments = ref<EquipmentListItem[]>([])
const suggestions = ref<EquipmentSuggestion[]>([])
const sharedProducts = ref<SharedProductInfo[]>([])
const selectedId = ref<number | null>(null)
const draft = ref<Draft | null>(null)

const sharedProductMap = computed(() => {
  const map = new Map<string, SharedProductInfo>()
  for (const row of sharedProducts.value) {
    const key = (row.part_no || '').trim().toLowerCase()
    if (key) map.set(key, row)
  }
  return map
})

function sharedInfoFor(partNo: string | undefined | null) {
  const key = (partNo || '').trim().toLowerCase()
  if (!key) return null
  return sharedProductMap.value.get(key) ?? null
}

function sharedOthers(partNo: string | undefined | null) {
  const info = sharedInfoFor(partNo)
  if (!info) return []
  const selfId = draft.value?.id
  return info.machines.filter((m) => m.id !== selfId)
}

function asDraftItem(row: unknown): DraftItem {
  return row as DraftItem
}

function sharedTipText(row: unknown) {
  const item = asDraftItem(row)
  const others = sharedOthers(item.part_no)
  if (!others.length) return ''
  const list = others
    .map((m) => `${m.machine_name || m.machine_cd}（内示 ${fmtNum(m.monthly_qty, 0)}）`)
    .join('、')
  return `同一工程の他設備でも生産登録あり：${list}`
}

const sharedHintCount = computed(() => {
  if (!draft.value) return 0
  let n = 0
  const seen = new Set<string>()
  for (const item of draft.value.items) {
    const key = (item.part_no || '').trim().toLowerCase()
    if (!key || seen.has(key)) continue
    if (sharedOthers(item.part_no).length) {
      seen.add(key)
      n += 1
    }
  }
  return n
})

function eqcRowClassName(data: { row: DraftItem; rowIndex: number }) {
  return sharedOthers(data.row?.part_no).length ? 'eqc-row--shared' : ''
}

const addOpen = ref(false)
const addForm = reactive({
  machine_cd: '',
  machine_name: '',
  regular_hours: 7.6,
  shift_count: 2,
  overtime_hours: 0,
  working_days: 22,
})

function normalizeProductCd(cd: string) {
  const text = (cd || '').trim()
  if (!text) return ''
  return `${text.slice(0, -1)}1`
}
const importOpen = ref(false)
const importPick = ref<EquipmentSuggestion[]>([])
const withProducts = ref(true)
const taktOpen = ref(false)
const formulaOpen = ref(false)
const taktKey = ref('')
const transferOpen = ref(false)
const transferring = ref(false)
const transferRow = ref<DraftItem | null>(null)
const transferTargetId = ref<number | undefined>(undefined)

const transferTargets = computed(() =>
  listedEquipments.value.filter((eq) => eq.id !== draft.value?.id),
)

let seq = 0
function uid() {
  seq += 1
  return `n-${Date.now()}-${seq}`
}

function touch() {
  if (!hydrating.value) dirty.value = true
}

/** 稼働条件変更 → ヘッダ算出・負荷は computed で自動反映 */
function onCondChange() {
  touch()
}

/** 稼働日変更 → 明細の日数・実日数へ反映し自動再計算 */
function onWorkingDaysChange() {
  if (!draft.value) return
  const days = Math.max(0, Math.round(Number(draft.value.working_days) || 0))
  draft.value.working_days = days
  for (const item of draft.value.items) {
    item.qty_days = days
    item.actual_days = days
  }
  touch()
}

function sortItemsByPartName(
  items: DraftItem[],
  order: 'ascending' | 'descending' | null = 'ascending',
) {
  const dir = order === 'descending' ? -1 : 1
  items.sort((a, b) => {
    const byName = (a.part_name || '').localeCompare(b.part_name || '', 'ja')
    if (byName !== 0) return byName * dir
    return (a.part_no || '').localeCompare(b.part_no || '', 'ja') * dir
  })
}

function onPartNameSort(payload: {
  column?: TableColumnCtx<DraftItem>
  prop: string | null
  order: 'ascending' | 'descending' | null
}) {
  if (!draft.value || payload.prop !== 'part_name') return
  sortItemsByPartName(draft.value.items, payload.order || 'ascending')
}

function blankItem(days: number): DraftItem {
  return {
    key: uid(),
    part_no: '',
    part_name: '',
    material: '',
    material_cd: '',
    monthly_qty: 0,
    qty_days: days,
    rate_per_hour: 0,
    availability_pct: 100,
    pass_rate_pct: 99,
    setup_hours: 0,
    actual_days: days,
    reference_rate: null,
    current_rate: null,
    takt1_date: null,
    takt1_ct: null,
    takt1_inspect: '',
    takt1_prep: '',
    takt1_overall: '',
    takt2_date: null,
    takt2_ct: null,
    takt2_inspect: '',
    takt2_prep: '',
    takt2_overall: '',
    remarks: '',
  }
}

function toDraftItem(raw: CapacityItem, days: number): DraftItem {
  const base = blankItem(days)
  return {
    ...base,
    ...raw,
    key: raw.id ? `id-${raw.id}` : uid(),
    part_no: raw.part_no || '',
    part_name: raw.part_name || '',
    material: raw.material || '',
    material_cd: raw.material_cd || '',
    takt1_inspect: raw.takt1_inspect || '',
    takt1_prep: raw.takt1_prep || '',
    takt1_overall: raw.takt1_overall || '',
    takt2_inspect: raw.takt2_inspect || '',
    takt2_prep: raw.takt2_prep || '',
    takt2_overall: raw.takt2_overall || '',
    remarks: raw.remarks || '',
  }
}

const headerCalc = computed(() =>
  draft.value
    ? calcHeader(draft.value)
    : { daily_available: 0, total_hours: 0 },
)

function lineCalc(item: unknown) {
  return calcLine(asDraftItem(item), headerCalc.value)
}

const totals = computed(() =>
  calcTotals((draft.value?.items || []).map((item) => lineCalc(item)), headerCalc.value),
)

const emptySummary = (): CapacitySummary => ({
  item_count: 0,
  active_count: 0,
  total_hours: 0,
  daily_available: 0,
  production_hours: 0,
  operating_hours: 0,
  occupied_hours: 0,
  occupancy_pct: null,
  remain_hours: 0,
  daily_judgment: null,
  month_judgment: null,
  avg_hourly: 0,
})

function cardSummary(eq: EquipmentListItem): CapacitySummary {
  if (draft.value && draft.value.id === eq.id) {
    return { ...emptySummary(), ...totals.value }
  }
  const summary = eq.summary || emptySummary()
  // 旧 API の peak_hourly 互換
  const legacy = summary as CapacitySummary & { peak_hourly?: number }
  if ((summary.avg_hourly == null || Number.isNaN(summary.avg_hourly)) && legacy.peak_hourly != null) {
    return { ...summary, avg_hourly: Number(legacy.peak_hourly) || 0 }
  }
  return { ...emptySummary(), ...summary, avg_hourly: Number(summary.avg_hourly) || 0 }
}

/** 成型他（FM-026）は仮想設備のため一覧・移転先・取込候補・集計から除外 */
function isIgnoredEquipment(eq: { machine_cd?: string; machine_name?: string }) {
  const name = (eq.machine_name || '').trim()
  const cd = (eq.machine_cd || '').trim().toUpperCase()
  return name === '成型他' || name.includes('成型他') || cd === 'FM-026'
}

const listedEquipments = computed(() =>
  equipments.value
    .filter((eq) => !isIgnoredEquipment(eq))
    .slice()
    .sort((a, b) => {
      const byName = (a.machine_name || '').localeCompare(b.machine_name || '', 'ja')
      if (byName !== 0) return byName
      return (a.machine_cd || '').localeCompare(b.machine_cd || '', 'ja')
    }),
)

const aggregate = computed<TotalCalc>(() => {
  let total = 0
  let daily = 0
  let production = 0
  let operating = 0
  let occupied = 0
  let rateSum = 0
  let rateN = 0
  let loadSum = 0
  let loadN = 0
  let active = 0
  let items = 0
  let dailyNg = false
  let monthNg = false
  for (const eq of listedEquipments.value) {
    const summary = cardSummary(eq)
    total += Number(summary.total_hours) || 0
    daily += Number(summary.daily_available) || 0
    production += Number(summary.production_hours) || 0
    operating += Number(summary.operating_hours) || 0
    occupied += Number(summary.occupied_hours) || 0
    const avg = Number(summary.avg_hourly) || 0
    const cnt = Number(summary.active_count) || 0
    if (avg > 0) {
      const w = cnt > 0 ? cnt : 1
      rateSum += avg * w
      rateN += w
    }
    const load = summary.occupancy_pct
    if (load != null && Number.isFinite(Number(load))) {
      loadSum += Number(load)
      loadN += 1
    }
    active += Number(summary.active_count) || 0
    items += Number(summary.item_count) || 0
    if (summary.daily_judgment === 'ng') dailyNg = true
    if (summary.month_judgment === 'ng') monthNg = true
  }
  return {
    item_count: items,
    active_count: active,
    total_hours: total,
    daily_available: daily,
    production_hours: production,
    operating_hours: operating,
    occupied_hours: occupied,
    // 一覧ヘッダの「平均負荷」は各設備負荷率の単純平均（KPI 合計占有÷総時間とは別）
    occupancy_pct: loadN > 0 ? loadSum / loadN : total > 0 ? (occupied / total) * 100 : null,
    remain_hours: total - occupied,
    daily_judgment: active <= 0 ? null : dailyNg ? 'ng' : 'ok',
    month_judgment: active <= 0 ? null : monthNg ? 'ng' : 'ok',
    avg_hourly: rateN > 0 ? rateSum / rateN : 0,
  }
})

const kpi = computed(() => (draft.value ? totals.value : aggregate.value))
const kpiTitle = computed(() => (draft.value ? draft.value.machine_name : `${processLabel.value} 合計`))
const taktRow = computed(() => draft.value?.items.find((item) => item.key === taktKey.value) ?? null)

const visibleEquipments = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return listedEquipments.value
  return listedEquipments.value.filter((eq) =>
    `${eq.machine_cd} ${eq.machine_name}`.toLowerCase().includes(q),
  )
})

function judgeClass(value: Judgment) {
  return { 'is-ok': value === 'ok', 'is-ng': value === 'ng' }
}

/** 負荷率の色：〜85%緑 / 〜100%琥珀 / 超100%赤 */
function loadToneClass(pct: number | null | undefined) {
  if (pct == null || !Number.isFinite(Number(pct))) return 'is-load-mute'
  const v = Number(pct)
  if (v > 100) return 'is-load-ng'
  if (v >= 85) return 'is-load-warn'
  return 'is-load-ok'
}

function cardClass(eq: EquipmentListItem) {
  const judgment = cardSummary(eq).month_judgment
  return { 'is-ok': judgment === 'ok', 'is-ng': judgment === 'ng' }
}

function sourceLabel(source: string) {
  if (source === 'machines') return '設備マスタ'
  if (source === 'efficiency') return '設備能率'
  return 'マスタ+能率'
}

function showServerError(error: unknown, fallback: string) {
  const err = error as { response?: { status?: number; data?: { detail?: unknown } } }
  if (err.response?.status !== 500) return
  const detail = err.response.data?.detail
  ElMessage.error(typeof detail === 'string' ? detail : fallback)
}

async function loadList() {
  listLoading.value = true
  try {
    const res = await fetchEquipmentCapacity(processCd.value)
    equipments.value = (res.data?.equipments || []).filter((eq) => !isIgnoredEquipment(eq))
    suggestions.value = (res.data?.suggestions || []).filter((eq) => !isIgnoredEquipment(eq))
    sharedProducts.value = res.data?.shared_products || []
    if (selectedId.value != null && !equipments.value.some((eq) => eq.id === selectedId.value)) {
      selectedId.value = null
      draft.value = null
      dirty.value = false
    }
  } catch (error) {
    equipments.value = []
    suggestions.value = []
    sharedProducts.value = []
    showServerError(error, '設備一覧を取得できませんでした')
  } finally {
    listLoading.value = false
  }
}

async function loadDetail(id: number) {
  detailLoading.value = true
  hydrating.value = true
  try {
    const res = await fetchEquipmentCapacityDetail(processCd.value, id)
    const data = res.data
    const days = Number(data.working_days) || 22
    draft.value = {
      id: data.id,
      machine_cd: data.machine_cd,
      machine_name: data.machine_name,
      regular_hours: Number(data.regular_hours) || 7.6,
      shift_count: Number(data.shift_count) || 1,
      overtime_hours: Number(data.overtime_hours) || 0,
      working_days: days,
      note: data.note || '',
      items: (data.items?.length ? data.items : [blankItem(days)]).map((item) => toDraftItem(item, days)),
    }
    sortItemsByPartName(draft.value.items, 'ascending')
    selectedId.value = id
    dirty.value = false
  } catch (error) {
    showServerError(error, '設備の明細を取得できませんでした')
  } finally {
    detailLoading.value = false
    await nextTick()
    hydrating.value = false
  }
}

async function confirmDiscard() {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm('保存していない変更があります。破棄して移動しますか？', '確認', {
      type: 'warning',
      confirmButtonText: '破棄して移動',
      cancelButtonText: '戻る',
    })
    dirty.value = false
    return true
  } catch {
    return false
  }
}

async function openEquipment(id: number) {
  if (id === selectedId.value) return
  if (!(await confirmDiscard())) return
  await loadDetail(id)
}

async function goProcess(path: string) {
  if (path === route.path) return
  await router.push(path)
}

function openAdd() {
  addForm.machine_cd = ''
  addForm.machine_name = ''
  addForm.regular_hours = 7.6
  addForm.shift_count = 2
  addForm.overtime_hours = 0
  addForm.working_days = 22
  addOpen.value = true
}

async function createEquipment() {
  if (!addForm.machine_cd.trim() || !addForm.machine_name.trim()) {
    ElMessage.warning('設備コードと設備名を入力してください')
    return
  }
  saving.value = true
  try {
    const res = await createEquipmentCapacity(processCd.value, { ...addForm })
    addOpen.value = false
    await loadList()
    await loadDetail(res.data.id)
    ElMessage.success('設備を追加しました')
  } catch (error) {
    showServerError(error, '設備を追加できませんでした')
  } finally {
    saving.value = false
  }
}

function openImport() {
  importPick.value = []
  withProducts.value = true
  importOpen.value = true
}

function onImportPick(rows: EquipmentSuggestion[]) {
  importPick.value = rows
}

async function runImport() {
  if (!importPick.value.length) return
  importing.value = true
  try {
    const res = await importEquipmentCapacityMaster(processCd.value, {
      machines: importPick.value.map((row) => ({ machine_cd: row.machine_cd, machine_name: row.machine_name })),
      with_products: withProducts.value,
    })
    importOpen.value = false
    await loadList()
    const first = res.data.created_ids?.[0]
    if (first) await loadDetail(first)
    const skipped = res.data.skipped?.length || 0
    ElMessage.success(`${res.data.created_ids.length} 台を追加しました${skipped ? `（${skipped} 台は既存）` : ''}`)
  } catch (error) {
    showServerError(error, '取り込みに失敗しました')
  } finally {
    importing.value = false
  }
}

function itemPayload(item: DraftItem | CapacityItem) {
  return {
    part_no: item.part_no,
    part_name: item.part_name,
    monthly_qty: item.monthly_qty,
    qty_days: item.qty_days,
    rate_per_hour: item.rate_per_hour,
    availability_pct: item.availability_pct,
    pass_rate_pct: item.pass_rate_pct,
    setup_hours: item.setup_hours,
    actual_days: item.actual_days,
    reference_rate: item.reference_rate,
    current_rate: item.current_rate,
    takt1_date: item.takt1_date,
    takt1_ct: item.takt1_ct,
    takt1_inspect: item.takt1_inspect,
    takt1_prep: item.takt1_prep,
    takt1_overall: item.takt1_overall,
    takt2_date: item.takt2_date,
    takt2_ct: item.takt2_ct,
    takt2_inspect: item.takt2_inspect,
    takt2_prep: item.takt2_prep,
    takt2_overall: item.takt2_overall,
    remarks: item.remarks,
  }
}

function payload() {
  const current = draft.value
  if (!current) return null
  return {
    machine_cd: current.machine_cd,
    machine_name: current.machine_name,
    regular_hours: current.regular_hours,
    shift_count: current.shift_count,
    overtime_hours: current.overtime_hours,
    working_days: current.working_days,
    note: current.note,
    items: current.items.map((item) => itemPayload(item)),
  }
}

function openTransfer(row: unknown) {
  if (!draft.value) return
  const item = asDraftItem(row)
  if (!item.part_no && !item.part_name) {
    ElMessage.warning('製品CDまたは製品名を入力してから移転してください')
    return
  }
  if (!transferTargets.value.length) {
    ElMessage.warning('移転先の設備がありません。先に別設備を追加してください')
    return
  }
  transferRow.value = item
  transferTargetId.value = transferTargets.value[0]?.id
  transferOpen.value = true
}

async function confirmTransfer() {
  if (!draft.value || !transferRow.value || !transferTargetId.value) return
  const row = transferRow.value
  const targetId = transferTargetId.value
  const targetName =
    transferTargets.value.find((eq) => eq.id === targetId)?.machine_name || '移転先'
  try {
    await ElMessageBox.confirm(
      `「${row.part_no || row.part_name}」を「${targetName}」へ移転します。画面の未保存内容も一緒に保存されます。`,
      '他設備へ移転',
      { type: 'warning', confirmButtonText: '移転する', cancelButtonText: '戻る' },
    )
  } catch {
    return
  }
  transferring.value = true
  try {
    const remaining = draft.value.items.filter((item) => item.key !== row.key)
    const res = await transferEquipmentCapacityItem(processCd.value, draft.value.id, {
      target_capacity_id: targetId,
      item: itemPayload(row),
      source_items: remaining.map((item) => itemPayload(item)),
      source_header: {
        machine_cd: draft.value.machine_cd,
        machine_name: draft.value.machine_name,
        regular_hours: draft.value.regular_hours,
        shift_count: draft.value.shift_count,
        overtime_hours: draft.value.overtime_hours,
        working_days: draft.value.working_days,
        note: draft.value.note,
      },
    })
    transferOpen.value = false
    transferRow.value = null
    dirty.value = false
    await loadList()
    await loadDetail(res.data.source.id)
    const mergedNote = res.data.merged ? '（先方に同一品番があり内示を合算）' : ''
    ElMessage.success(`「${res.data.target_machine_name}」へ移転しました${mergedNote}`)
  } catch (error) {
    showServerError(error, '移転に失敗しました')
  } finally {
    transferring.value = false
  }
}

async function save() {
  const body = payload()
  if (!draft.value || !body) return
  saving.value = true
  try {
    const res = await saveEquipmentCapacity(processCd.value, draft.value.id, body)
    await loadList()
    await loadDetail(res.data.id)
    ElMessage.success('保存しました')
  } catch (error) {
    showServerError(error, '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function removeEquipment() {
  if (!draft.value) return
  try {
    await ElMessageBox.confirm(`「${draft.value.machine_name}」と品目を削除します。`, '削除', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: '戻る',
    })
  } catch {
    return
  }
  try {
    await deleteEquipmentCapacity(processCd.value, draft.value.id)
    dirty.value = false
    selectedId.value = null
    draft.value = null
    await loadList()
    ElMessage.success('削除しました')
  } catch (error) {
    showServerError(error, '削除に失敗しました')
  }
}

function addRow() {
  if (!draft.value) return
  draft.value.items.push(blankItem(Number(draft.value.working_days) || 0))
  touch()
}

function removeRow(key: string) {
  if (!draft.value) return
  draft.value.items = draft.value.items.filter((item) => item.key !== key)
  touch()
}

async function applyForecast() {
  if (!draft.value) {
    ElMessage.warning('先に設備を選択してください')
    return
  }
  if (!targetMonth.value) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  const [yearText, monthText] = targetMonth.value.split('-')
  const year = Number(yearText)
  const month = Number(monthText)
  if (!year || !month) {
    ElMessage.warning('対象月が不正です')
    return
  }
  loadingForecast.value = true
  try {
    const res = await fetchEquipmentCapacityForecastMonthly(processCd.value, year, month)
    const forecastItems = res.data?.items || []
    if (!forecastItems.length) {
      ElMessage.warning(`${targetMonth.value} の内示データがありません`)
      return
    }
    // 当該設備に既にある品目だけ更新（他設備の製品・補給品・試作品は追加しない）
    const byCd = new Map(forecastItems.map((item) => [item.product_cd, item]))
    let updated = 0
    let matchedQty = 0
    for (const row of draft.value.items) {
      const key = normalizeProductCd(row.part_no)
      const hit = byCd.get(key)
      if (!hit) continue
      row.monthly_qty = Number(hit.monthly_qty) || 0
      if (!row.part_name && hit.product_name) row.part_name = hit.product_name
      matchedQty += Number(hit.monthly_qty) || 0
      updated += 1
    }
    touch()
    if (updated === 0) {
      ElMessage.warning(
        `${targetMonth.value} の内示のうち、この設備の品目に一致するものがありません`,
      )
      return
    }
    ElMessage.success(
      `${targetMonth.value} の内示を反映しました（更新 ${updated} 行 / ${fmtNum(matchedQty, 0)} 本）`,
    )
  } catch (error) {
    showServerError(error, '内示の取得に失敗しました')
  } finally {
    loadingForecast.value = false
  }
}

function toPrintEquipment(source: {
  machine_cd: string
  machine_name: string
  regular_hours: number
  shift_count: number
  overtime_hours: number
  working_days: number
  items: Array<{
    part_no?: string
    part_name?: string
    material?: string
    monthly_qty: number
    qty_days: number
    rate_per_hour: number
    availability_pct: number
    pass_rate_pct: number
    setup_hours: number
    actual_days: number
  }>
}): PrintEquipmentInput {
  return {
    machine_cd: source.machine_cd || '',
    machine_name: source.machine_name || '',
    regular_hours: Number(source.regular_hours) || 0,
    shift_count: Number(source.shift_count) || 0,
    overtime_hours: Number(source.overtime_hours) || 0,
    working_days: Number(source.working_days) || 0,
    items: (source.items || []).map((item) => ({
      part_no: item.part_no || '',
      part_name: item.part_name || '',
      material: item.material || '',
      monthly_qty: Number(item.monthly_qty) || 0,
      qty_days: Number(item.qty_days) || 0,
      rate_per_hour: Number(item.rate_per_hour) || 0,
      availability_pct: Number(item.availability_pct) || 0,
      pass_rate_pct: Number(item.pass_rate_pct) || 0,
      setup_hours: Number(item.setup_hours) || 0,
      actual_days: Number(item.actual_days) || 0,
    })),
  }
}

/** 選択中設備の現在画面データを印刷 */
function printCurrentEquipment() {
  if (!draft.value) {
    ElMessage.warning('印刷する設備を選んでください')
    return
  }
  printingOne.value = true
  try {
    const win = printCapacityReport({
      processLabel: processLabel.value,
      targetMonth: targetMonth.value,
      mode: 'single',
      equipments: [toPrintEquipment(draft.value)],
    })
    if (!win) ElMessage.error(PRINT_POPUP_BLOCKED_MSG)
  } catch (error) {
    console.error(error)
    ElMessage.error('印刷レポートの作成に失敗しました')
  } finally {
    printingOne.value = false
  }
}

/** 一覧の全設備を印刷（選択中かつ未保存なら画面値を優先） */
async function printAllEquipments() {
  const list = listedEquipments.value
  if (!list.length) {
    ElMessage.warning('印刷する設備がありません')
    return
  }
  printingAll.value = true
  try {
    const equipments: PrintEquipmentInput[] = []
    for (const eq of list) {
      if (draft.value && draft.value.id === eq.id) {
        equipments.push(toPrintEquipment(draft.value))
        continue
      }
      const res = await fetchEquipmentCapacityDetail(processCd.value, eq.id)
      const data = res.data
      const days = Number(data.working_days) || 0
      equipments.push(
        toPrintEquipment({
          machine_cd: data.machine_cd,
          machine_name: data.machine_name,
          regular_hours: Number(data.regular_hours) || 0,
          shift_count: Number(data.shift_count) || 0,
          overtime_hours: Number(data.overtime_hours) || 0,
          working_days: days,
          items: (data.items || []).map((item) => ({
            ...item,
            qty_days: Number(item.qty_days) || days,
            actual_days: Number(item.actual_days) || days,
          })),
        }),
      )
    }
    const win = printCapacityReport({
      processLabel: processLabel.value,
      targetMonth: targetMonth.value,
      mode: 'all',
      equipments,
    })
    if (!win) ElMessage.error(PRINT_POPUP_BLOCKED_MSG)
  } catch (error) {
    console.error(error)
    const err = error as { response?: { status?: number; data?: { detail?: unknown } } }
    const detail = err.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '全設備の印刷に失敗しました')
  } finally {
    printingAll.value = false
  }
}

function openTakt(key: string) {
  taktKey.value = key
  taktOpen.value = true
}

watch(
  () => processCd.value,
  () => {
    selectedId.value = null
    draft.value = null
    dirty.value = false
    keyword.value = ''
    void loadList()
  },
  { immediate: true },
)

onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm('保存していない変更があります。移動すると破棄されます。', '確認', {
      type: 'warning',
      confirmButtonText: '破棄して移動',
      cancelButtonText: '戻る',
    })
    dirty.value = false
    return true
  } catch {
    return false
  }
})

</script>

<style scoped>
/* ぼかし禁止・タイポ基準：本文 13px / ラベル 12px / 数値 15px */
.eqc-page,
.eqc-page *,
.eqc-page *::before,
.eqc-page *::after {
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
}
.eqc-page {
  --eqc-app-chrome: 84px;
  --eqc-fs: 13px;
  --eqc-fs-sm: 12px;
  --eqc-fs-lg: 15px;
  --eqc-fs-xl: 16px;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 6px 8px 8px;
  height: calc(100vh - var(--eqc-app-chrome));
  height: calc(100dvh - var(--eqc-app-chrome));
  max-height: calc(100vh - var(--eqc-app-chrome));
  max-height: calc(100dvh - var(--eqc-app-chrome));
  min-height: 0;
  overflow: hidden;
  font-size: var(--eqc-fs);
  color: #0f172a;
  background:
    radial-gradient(880px 240px at 0% 0%, var(--eqc-bg1), transparent 60%),
    radial-gradient(640px 220px at 100% 0%, var(--eqc-bg2), transparent 55%),
    #f4f7fb;
}
.eqc-page--cutting {
  --eqc-hero: linear-gradient(125deg, #0f172a 0%, #1e3a8a 42%, #2563eb 72%, #38bdf8 100%);
  --eqc-shadow: rgba(30, 58, 138, 0.45);
  --eqc-bg1: rgba(37, 99, 235, 0.16);
  --eqc-bg2: rgba(14, 165, 233, 0.1);
  --eqc-accent: #2563eb;
  --eqc-soft: #eff6ff;
  --eqc-soft2: #dbeafe;
}
.eqc-page--chamfering {
  --eqc-hero: linear-gradient(125deg, #134e4a 0%, #0f766e 40%, #14b8a6 72%, #5eead4 100%);
  --eqc-shadow: rgba(15, 118, 110, 0.45);
  --eqc-bg1: rgba(13, 148, 136, 0.16);
  --eqc-bg2: rgba(45, 212, 191, 0.12);
  --eqc-accent: #0f766e;
  --eqc-soft: #f0fdfa;
  --eqc-soft2: #ccfbf1;
}
/* 成型：深緑→翠绿（製品工程BOMのオリーブと区別） */
.eqc-page--forming {
  --eqc-hero: linear-gradient(125deg, #14532d 0%, #15803d 38%, #22c55e 72%, #86efac 100%);
  --eqc-shadow: rgba(21, 128, 61, 0.48);
  --eqc-bg1: rgba(22, 163, 74, 0.14);
  --eqc-bg2: rgba(74, 222, 128, 0.12);
  --eqc-accent: #15803d;
  --eqc-soft: #f0fdf4;
  --eqc-soft2: #dcfce7;
}
.eqc-page--welding {
  --eqc-hero: linear-gradient(125deg, #7c2d12 0%, #c2410c 42%, #f97316 74%, #fdba74 100%);
  --eqc-shadow: rgba(154, 52, 18, 0.42);
  --eqc-bg1: rgba(234, 88, 12, 0.16);
  --eqc-bg2: rgba(251, 146, 60, 0.12);
  --eqc-accent: #c2410c;
  --eqc-soft: #fff7ed;
  --eqc-soft2: #ffedd5;
}

.eqc-hero {
  position: relative;
  isolation: isolate;
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  gap: 10px 14px;
  flex-wrap: wrap;
  color: #fff;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: var(--eqc-hero);
  box-shadow:
    0 10px 22px -14px var(--eqc-shadow),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
}
.eqc-hero__main,
.eqc-hero__side {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 0;
}
.eqc-hero__main {
  flex: 1 1 auto;
}
.eqc-hero__side {
  flex: 0 1 auto;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}
.eqc-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(0, 0, 0, 0.12);
}
.eqc-hero__titles {
  min-width: 0;
}
.eqc-hero h1 {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #fff;
}
.eqc-hero .pb-hero-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.88);
}
.eqc-switch,
.eqc-hero__actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  align-items: center;
  justify-content: flex-end;
}
.eqc-hero__actions {
  padding-left: 10px;
  margin-left: 2px;
  border-left: 1px solid rgba(255, 255, 255, 0.4);
}
.eqc-switch__btn {
  border: 1.5px solid transparent;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: var(--eqc-fs);
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.12s ease, color 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
}
/* 工程色：切断=青 / 面取=ティール / 成型=緑 / 溶接=橙 */
.eqc-switch__btn.is-cutting {
  background: #2563eb;
  border-color: #93c5fd;
  box-shadow: inset 0 -1px 0 rgba(0, 0, 0, 0.12);
}
.eqc-switch__btn.is-chamfering {
  background: #0d9488;
  border-color: #5eead4;
  box-shadow: inset 0 -1px 0 rgba(0, 0, 0, 0.12);
}
.eqc-switch__btn.is-forming {
  background: #16a34a;
  border-color: #86efac;
  box-shadow: inset 0 -1px 0 rgba(0, 0, 0, 0.12);
}
.eqc-switch__btn.is-welding {
  background: #ea580c;
  border-color: #fdba74;
  box-shadow: inset 0 -1px 0 rgba(0, 0, 0, 0.12);
}
.eqc-switch__btn:not(.is-on) {
  opacity: 0.72;
}
.eqc-switch__btn:not(.is-on):hover {
  opacity: 0.92;
}
.eqc-switch__btn.is-on {
  opacity: 1;
  background: #fff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.18);
}
.eqc-switch__btn.is-cutting.is-on { color: #1d4ed8; border-color: #fff; }
.eqc-switch__btn.is-chamfering.is-on { color: #0f766e; border-color: #fff; }
.eqc-switch__btn.is-forming.is-on { color: #166534; border-color: #fff; }
.eqc-switch__btn.is-welding.is-on { color: #9a3412; border-color: #fff; }

/* タイトル上の白カプセル */
.eqc-hero__actions .tb-btn {
  --k-rgb: 217 119 6;
  --k-fg: #92400e;
  --k-bd: #fcd34d;
  --k-tint: #fef3c7;
  --k-tint-h: #fde68a;
  --k-ico: #d97706;
  height: 32px !important;
  padding: 0 14px 0 12px !important;
  border-radius: 999px !important;
  font-size: var(--eqc-fs-sm) !important;
  font-weight: 700 !important;
  margin: 0 !important;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  border: 1px solid var(--k-bd) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(15, 23, 42, 0.22) !important;
}
.eqc-hero__actions .tb-btn :deep(.el-icon) {
  color: var(--k-ico);
  font-size: 15px;
}
.eqc-hero__actions .tb-btn-teal {
  --k-rgb: 13 148 136;
  --k-fg: #0f766e;
  --k-bd: #5eead4;
  --k-tint: #ccfbf1;
  --k-tint-h: #99f6e4;
  --k-ico: #14b8a6;
}
.eqc-hero__actions .tb-btn-slate {
  --k-rgb: 71 85 105;
  --k-fg: #334155;
  --k-bd: #cbd5e1;
  --k-tint: #f1f5f9;
  --k-tint-h: #e2e8f0;
  --k-ico: #64748b;
}
.eqc-hero__actions .tb-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 30%, var(--k-tint-h) 100%) !important;
}
.eqc-count {
  margin-left: 6px;
  min-width: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #0f766e;
  color: #fff;
  font-size: var(--eqc-fs-sm);
  font-weight: 800;
}

.eqc-kpis {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 2px 0;
}
.eqc-kpis__scope {
  flex-shrink: 0;
  margin: 0;
  font-size: var(--eqc-fs-sm);
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #475569;
  padding: 5px 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.eqc-kpis__strip {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.eqc-kpi {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  padding: 6px 12px 6px 6px;
  min-height: 36px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--accent) 28%, #e2e8f0);
  border-left: 3px solid var(--accent);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.eqc-kpi--blue { --accent: #3b82f6; }
.eqc-kpi--purple { --accent: #8b5cf6; }
.eqc-kpi--amber { --accent: #f59e0b; }
.eqc-kpi--green { --accent: #10b981; }
.eqc-kpi--teal { --accent: #14b8a6; }
.eqc-kpi--pink { --accent: #ec4899; }
.eqc-kpi__icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--accent);
  flex-shrink: 0;
}
.eqc-kpi__body {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.eqc-kpi__lbl {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  line-height: 1.2;
}
.eqc-kpi strong {
  font-size: var(--eqc-fs-lg);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  line-height: 1.15;
  white-space: nowrap;
}
.eqc-kpi small {
  margin-left: 2px;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}

.eqc-body {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(200px, 252px) minmax(0, 1fr);
  gap: 6px;
  overflow: hidden;
}
.eqc-list,
.eqc-detail,
.eqc-placeholder {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  min-width: 0;
  min-height: 0;
}
.eqc-list {
  padding: 8px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, var(--eqc-soft) 0%, #ffffff 40px);
}
.eqc-list__head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
  flex-shrink: 0;
}
.eqc-list__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  font-size: var(--eqc-fs-sm);
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.eqc-list__meta em {
  font-style: normal;
  font-weight: 700;
}
.eqc-list__meta-rate {
  color: #4338ca;
}
.eqc-list__meta-rate b {
  font-weight: 800;
  color: #3730a3;
}
.eqc-list__meta-load {
  color: #64748b;
}
.eqc-list__meta-load b {
  font-weight: 800;
}
.eqc-card {
  width: 100%;
  text-align: left;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 6px;
  cursor: pointer;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.eqc-card:hover {
  border-color: color-mix(in srgb, var(--eqc-accent) 45%, #e2e8f0);
  background: var(--eqc-soft);
}
.eqc-card.is-on {
  border-color: var(--eqc-accent);
  background: var(--eqc-soft2);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--eqc-accent) 35%, transparent);
}
.eqc-card.is-ok { box-shadow: inset 3px 0 0 #10b981; }
.eqc-card.is-ng { box-shadow: inset 3px 0 0 #e11d48; }
.eqc-card.is-on.is-ok {
  box-shadow:
    inset 3px 0 0 #10b981,
    0 0 0 1px color-mix(in srgb, var(--eqc-accent) 35%, transparent);
}
.eqc-card.is-on.is-ng {
  box-shadow:
    inset 3px 0 0 #e11d48,
    0 0 0 1px color-mix(in srgb, var(--eqc-accent) 35%, transparent);
}
.eqc-card__name {
  flex: 1 1 auto;
  min-width: 0;
  font-weight: 800;
  font-size: var(--eqc-fs-lg);
  color: #0f172a;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.eqc-card__metric {
  flex: 0 0 auto;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}
.eqc-card__metric small {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.02em;
  opacity: 0.85;
}
.eqc-card__metric b {
  font-size: var(--eqc-fs);
  font-weight: 800;
}
.eqc-card__metric--rate {
  color: #4338ca;
  min-width: 52px;
}
.eqc-card__metric--rate small { color: #6366f1; }
.eqc-card__metric--load {
  min-width: 48px;
  padding-left: 6px;
  border-left: 1px solid #e2e8f0;
}
.eqc-card__metric--load small { color: #64748b; }
.is-load-ok { color: #059669 !important; }
.is-load-warn { color: #d97706 !important; }
.is-load-ng { color: #e11d48 !important; }
.is-load-mute { color: #94a3b8 !important; }

.eqc-detail {
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
}
.eqc-shared-banner {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid #c4b5fd;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  color: #4c1d95;
}
.eqc-shared-banner__mark {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, #7c3aed, #8b5cf6);
}
.eqc-shared-banner__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  font-size: var(--eqc-fs-sm);
  line-height: 1.4;
}
.eqc-shared-banner__body strong {
  font-size: var(--eqc-fs);
  font-weight: 800;
  color: #5b21b6;
}
.eqc-shared-banner__body b {
  color: #6d28d9;
  font-weight: 800;
}
.eqc-part-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  min-width: 0;
}
.eqc-part-cell .eqc-lock--cd {
  flex: 1 1 auto;
  min-width: 0;
}
.eqc-shared-tag {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  padding: 0 5px;
  height: 18px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #5b21b6;
  background: #ede9fe;
  border: 1px solid #c4b5fd;
  cursor: help;
  white-space: nowrap;
  line-height: 1;
}
.eqc-table :deep(.eqc-row--shared > td.el-table__cell) {
  background-color: #faf5ff !important;
}
.eqc-table :deep(.eqc-row--shared.el-table__row--striped > td.el-table__cell) {
  background-color: #f3e8ff !important;
}
.eqc-table :deep(.eqc-row--shared:hover > td.el-table__cell) {
  background-color: #e9d5ff !important;
}
.eqc-table :deep(.eqc-row--shared > td.el-table__cell.eqc-col-meta) {
  background-color: #f3e8ff !important;
}
.eqc-table :deep(.eqc-row--shared.el-table__row--striped > td.el-table__cell.eqc-col-meta) {
  background-color: #ede9fe !important;
}
.eqc-table :deep(.eqc-row--shared:hover > td.el-table__cell.eqc-col-meta) {
  background-color: #ddd6fe !important;
}

/* 条件＋操作を一枚のパネルに */
.eqc-panel {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.eqc-cond {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px 10px;
  padding: 10px 10px 8px;
  background:
    linear-gradient(90deg, var(--eqc-accent) 0 3px, transparent 3px),
    linear-gradient(180deg, var(--eqc-soft) 0%, #ffffff 100%);
}
.eqc-cond__group {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 6px 8px;
  padding: 8px 8px 6px;
  border-radius: 8px;
  border: 1px solid transparent;
  position: relative;
}
.eqc-cond__tag {
  position: absolute;
  top: -7px;
  left: 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  padding: 0 6px;
  border-radius: 4px;
  line-height: 16px;
  color: #fff;
}
.eqc-cond__group--id {
  flex: 1 1 220px;
  min-width: 180px;
  background: #eff6ff;
  border-color: #bfdbfe;
}
.eqc-cond__group--id .eqc-cond__tag { background: #2563eb; }
.eqc-cond__group--cap {
  flex: 0 1 auto;
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.eqc-cond__group--cap .eqc-cond__tag { background: #16a34a; }
.eqc-cond__group--calc {
  flex: 0 0 auto;
  background: #fff7ed;
  border-color: #fed7aa;
}
.eqc-cond__group--calc .eqc-cond__tag { background: #ea580c; }

.eqc-field,
.eqc-form label,
.eqc-takt label,
.eqc-takt-note {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: var(--eqc-fs-sm);
  font-weight: 700;
  color: #64748b;
}
.eqc-field--grow { flex: 1 1 140px; min-width: 120px; }
.eqc-field--cd { width: 100px; flex: 0 0 100px; }
.eqc-field--sm { width: 76px; flex: 0 0 76px; }
.eqc-field--xs { width: 48px; flex: 0 0 48px; }
.eqc-field :deep(.el-input__wrapper),
.eqc-field :deep(.el-input-number .el-input__wrapper) {
  min-height: 30px !important;
  padding: 0 8px !important;
  border-radius: 7px !important;
  box-shadow: 0 0 0 1px #cbd5e1 inset !important;
  background: #fff !important;
}
.eqc-field :deep(.el-input__inner),
.eqc-field :deep(.el-input-number .el-input__inner) {
  height: 28px !important;
  font-size: var(--eqc-fs) !important;
  font-weight: 600;
}
.eqc-field :deep(.el-input-number) { width: 100%; }
.eqc-mini {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 88px;
  padding: 4px 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #fed7aa;
}
.eqc-mini span {
  font-size: 11px;
  font-weight: 700;
  color: #9a3412;
}
.eqc-mini b {
  font-size: var(--eqc-fs-lg);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #9a3412;
  line-height: 1.2;
}
.eqc-mini--month {
  border-color: #fdba74;
  background: linear-gradient(180deg, #fffbeb, #ffedd5);
}
.eqc-mini--month span,
.eqc-mini--month b { color: #c2410c; }
.eqc-mini small {
  font-size: 11px;
  font-weight: 700;
  margin-left: 2px;
}

.eqc-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 8px;
  align-items: center;
  padding: 8px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
}
.eqc-actions__btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
}
.eqc-month {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--eqc-fs-sm);
  font-weight: 800;
  color: #475569;
  padding: 3px 6px 3px 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.eqc-month__nav {
  height: 26px !important;
  padding: 0 8px !important;
  margin: 0 !important;
  border-radius: 6px !important;
  border: 1px solid #cbd5e1 !important;
  background: #f8fafc !important;
  color: #334155 !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  gap: 2px;
}
.eqc-month__nav :deep(.el-icon) {
  font-size: 12px;
}
.eqc-month__nav:hover:not(:disabled) {
  background: #e2e8f0 !important;
  border-color: #94a3b8 !important;
  color: #0f172a !important;
}
.eqc-month :deep(.el-date-editor) {
  width: 112px;
}
.eqc-month :deep(.el-input__wrapper) {
  min-height: 28px !important;
  box-shadow: none !important;
  background: transparent !important;
}
.eqc-month :deep(.el-input__inner) {
  font-size: var(--eqc-fs) !important;
  font-weight: 700;
}
.eqc-actions__judge {
  margin-left: auto;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.eqc-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: var(--eqc-fs-sm);
  font-weight: 700;
  color: #475569;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.eqc-chip b {
  font-variant-numeric: tabular-nums;
  font-size: var(--eqc-fs);
}
.eqc-chip--slate { border-color: #cbd5e1; background: #f8fafc; }
.eqc-chip--green { border-color: #86efac; background: #f0fdf4; color: #166534; }
.eqc-chip--amber { border-color: #fcd34d; background: #fffbeb; color: #92400e; }

/* 明細ツールバー tb-btn */
.eqc-actions .tb-btn,
.eqc-placeholder .tb-btn {
  --k-rgb: 37 99 235;
  --k-fg: #1d4ed8;
  --k-bd: #93c5fd;
  --k-tint: #dbeafe;
  --k-tint-h: #bfdbfe;
  --k-ico: #3b82f6;
  height: 30px !important;
  padding: 0 12px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  margin: 0 !important;
  font-size: var(--eqc-fs-sm) !important;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  border: 1px solid var(--k-bd) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.1),
    0 1px 3px -1px rgba(15, 23, 42, 0.1) !important;
}
.eqc-actions .tb-btn :deep(.el-icon),
.eqc-placeholder .tb-btn :deep(.el-icon) {
  color: var(--k-ico);
  font-size: 15px;
}
.eqc-actions .tb-btn:hover:not(:disabled),
.eqc-placeholder .tb-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 30%, var(--k-tint-h) 100%) !important;
}
.eqc-actions .tb-btn-slate { --k-rgb: 71 85 105; --k-fg: #334155; --k-bd: #cbd5e1; --k-tint: #f1f5f9; --k-tint-h: #e2e8f0; --k-ico: #64748b; }
.eqc-actions .tb-btn-amber { --k-rgb: 217 119 6; --k-fg: #92400e; --k-bd: #fcd34d; --k-tint: #fef3c7; --k-tint-h: #fde68a; --k-ico: #d97706; }
.eqc-actions .tb-btn-blue { --k-rgb: 37 99 235; --k-fg: #1d4ed8; --k-bd: #93c5fd; --k-tint: #dbeafe; --k-tint-h: #bfdbfe; --k-ico: #3b82f6; }
.eqc-actions .tb-btn-teal { --k-rgb: 13 148 136; --k-fg: #0f766e; --k-bd: #5eead4; --k-tint: #ccfbf1; --k-tint-h: #99f6e4; --k-ico: #14b8a6; }
.eqc-actions .tb-btn-indigo { --k-rgb: 79 70 229; --k-fg: #4338ca; --k-bd: #a5b4fc; --k-tint: #e0e7ff; --k-tint-h: #c7d2fe; --k-ico: #6366f1; }
.eqc-actions .tb-btn-green { --k-rgb: 5 150 105; --k-fg: #047857; --k-bd: #6ee7b7; --k-tint: #d1fae5; --k-tint-h: #a7f3d0; --k-ico: #10b981; }
.eqc-actions .tb-btn-rose { --k-rgb: 225 29 72; --k-fg: #be123c; --k-bd: #fda4af; --k-tint: #ffe4e6; --k-tint-h: #fecdd3; --k-ico: #e11d48; }
.eqc-actions .tb-btn-save {
  --k-rgb: 5 150 105;
  color: #fff !important;
  background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
  border-color: #059669 !important;
  box-shadow: 0 2px 8px -2px rgba(5, 150, 105, 0.45) !important;
}
.eqc-actions .tb-btn-save:disabled,
.eqc-actions .tb-btn-save.is-disabled {
  opacity: 0.45;
  filter: grayscale(0.2);
}
.eqc-actions .tb-btn-save:hover:not(:disabled) {
  color: #fff !important;
  background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
}
.eqc-placeholder .tb-btn-amber { --k-rgb: 217 119 6; --k-fg: #92400e; --k-bd: #fcd34d; --k-tint: #fef3c7; --k-tint-h: #fde68a; --k-ico: #d97706; }
.eqc-placeholder .tb-btn-teal { --k-rgb: 13 148 136; --k-fg: #0f766e; --k-bd: #5eead4; --k-tint: #ccfbf1; --k-tint-h: #99f6e4; --k-ico: #14b8a6; }

.eqc-field :deep(.el-input-number) { width: 100%; }
.eqc-placeholder { display: grid; place-items: center; }
.eqc-muted { color: #64748b; font-size: var(--eqc-fs-sm); line-height: 1.5; }
.is-ok { color: #059669; }
.is-ng { color: #e11d48; }
.is-neg { color: #e11d48; }

.eqc-table-body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
}
.eqc-table-body :deep(.el-table) {
  flex: 1 1 auto;
  height: 100% !important;
}
.eqc-table-body :deep(.el-table__inner-wrapper) {
  height: 100%;
}
.eqc-table-body :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
}

/* テーブル：紧凑行高・可读字号・列分色・入力は枠なし */
.eqc-table {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  height: 100% !important;
  font-size: var(--eqc-fs);
  --el-table-border-color: #e8eef5;
  --el-table-header-bg-color: var(--eqc-soft2);
  --el-table-row-hover-bg-color: var(--eqc-soft);
  --el-table-bg-color: #ffffff;
}
.eqc-table :deep(.el-table__header .el-table__cell) {
  padding: 6px 4px !important;
}
.eqc-table :deep(.el-table__body .el-table__cell) {
  padding: 3px 4px !important;
}
.eqc-table :deep(.el-table__cell .cell) {
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25;
}
.eqc-table :deep(th.el-table__cell) {
  background: linear-gradient(180deg, var(--eqc-soft) 0%, var(--eqc-soft2) 100%) !important;
  color: #334155;
  font-weight: 700;
  font-size: var(--eqc-fs-sm);
  line-height: 1.25;
}
.eqc-table :deep(td.el-table__cell) {
  background-color: #ffffff !important;
}
.eqc-table :deep(.el-table__row--striped td.el-table__cell) {
  background-color: #f8fafc !important;
}
.eqc-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: var(--eqc-soft) !important;
}

/* 読取固定列 */
.eqc-table :deep(th.el-table__cell.eqc-col-meta) {
  background: linear-gradient(180deg, #e0e7ff 0%, #c7d2fe 100%) !important;
  color: #312e81 !important;
}
.eqc-table :deep(td.el-table__cell.eqc-col-meta) {
  background-color: #eef2ff !important;
}
.eqc-table :deep(.el-table__row--striped td.el-table__cell.eqc-col-meta) {
  background-color: #e0e7ff !important;
}
.eqc-table :deep(.el-table__body tr:hover > td.el-table__cell.eqc-col-meta) {
  background-color: #c7d2fe !important;
}

/* 入力列 */
.eqc-table :deep(th.el-table__cell.eqc-col-edit) {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%) !important;
  color: #065f46 !important;
}
.eqc-table :deep(td.el-table__cell.eqc-col-edit) {
  background-color: #f0fdf4 !important;
}
.eqc-table :deep(.el-table__row--striped td.el-table__cell.eqc-col-edit) {
  background-color: #dcfce7 !important;
}
.eqc-table :deep(.el-table__body tr:hover > td.el-table__cell.eqc-col-edit) {
  background-color: #bbf7d0 !important;
}

/* 算出列 */
.eqc-table :deep(th.el-table__cell.eqc-col-calc) {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%) !important;
  color: #9a3412 !important;
}
.eqc-table :deep(td.el-table__cell.eqc-col-calc) {
  background-color: #fffbeb !important;
}
.eqc-table :deep(.el-table__row--striped td.el-table__cell.eqc-col-calc) {
  background-color: #fef3c7 !important;
}
.eqc-table :deep(.el-table__body tr:hover > td.el-table__cell.eqc-col-calc) {
  background-color: #fde68a !important;
}

.eqc-table :deep(th.el-table__cell.eqc-col-act) {
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
  color: #1e293b !important;
}
.eqc-table :deep(td.el-table__cell.eqc-col-act) {
  background-color: #f8fafc !important;
}
.eqc-table :deep(.el-table__row--striped td.el-table__cell.eqc-col-act) {
  background-color: #f1f5f9 !important;
}
.eqc-table :deep(.el-table__body tr:hover > td.el-table__cell.eqc-col-act) {
  background-color: #e2e8f0 !important;
}

.eqc-table :deep(th.el-table-fixed-column--left),
.eqc-table :deep(td.el-table-fixed-column--left),
.eqc-table :deep(th.el-table-fixed-column--right),
.eqc-table :deep(td.el-table-fixed-column--right) {
  background-clip: padding-box !important;
  z-index: 3 !important;
}
.eqc-table :deep(.el-table__header th.el-table-fixed-column--left.is-last-column),
.eqc-table :deep(.el-table__body td.el-table-fixed-column--left.is-last-column) {
  border-right: 1px solid #a5b4fc !important;
  box-shadow: 6px 0 10px -6px rgba(49, 46, 129, 0.28);
}
.eqc-table :deep(.el-table__header th.el-table-fixed-column--right.is-first-column),
.eqc-table :deep(.el-table__body td.el-table-fixed-column--right.is-first-column) {
  border-left: 1px solid #cbd5e1 !important;
  box-shadow: -6px 0 10px -6px rgba(15, 23, 42, 0.22);
}

/* 入力セル：枠なし・セル一体 */
.eqc-num {
  width: 100%;
}
.eqc-num :deep(.el-input) {
  width: 100%;
}
.eqc-num :deep(.el-input__wrapper) {
  padding: 0 6px !important;
  min-height: 26px !important;
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}
.eqc-num :deep(.el-input__wrapper:hover),
.eqc-num :deep(.el-input__wrapper.is-focus) {
  background: #ffffff !important;
  box-shadow: inset 0 -2px 0 #22c55e !important;
}
.eqc-num :deep(.el-input__inner) {
  height: 26px !important;
  line-height: 26px !important;
  font-size: var(--eqc-fs) !important;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: right;
  color: #0f172a;
}

.eqc-idx {
  font-size: var(--eqc-fs-sm);
  font-weight: 700;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.eqc-lock {
  display: block;
  font-size: var(--eqc-fs);
  font-weight: 600;
  color: #1e293b;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 0;
}
.eqc-lock--cd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 700;
  color: #3730a3;
  letter-spacing: 0.01em;
}
.eqc-lock--mat {
  font-size: var(--eqc-fs-sm);
  font-weight: 600;
  color: #475569;
}
.eqc-ro {
  display: inline-block;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: var(--eqc-fs);
  color: #9a3412;
  padding: 2px 0;
}
.eqc-ro--pct { font-weight: 800; }
.eqc-kpi strong.is-load-ok small,
.eqc-kpi strong.is-load-warn small,
.eqc-kpi strong.is-load-ng small,
.eqc-kpi strong.is-load-mute small {
  color: inherit;
  opacity: 0.85;
}
.eqc-judge {
  font-size: var(--eqc-fs-xl);
  line-height: 1;
}

.eqc-ops {
  display: inline-flex;
  flex-wrap: nowrap;
  gap: 4px;
  align-items: center;
  justify-content: center;
}
.eqc-row-btn {
  height: 26px !important;
  padding: 0 10px !important;
  margin: 0 !important;
  border-radius: 999px !important;
  font-size: var(--eqc-fs-sm) !important;
  font-weight: 700 !important;
}
.eqc-row-btn--indigo {
  color: #4338ca !important;
  background: #eef2ff !important;
  border: 1px solid #c7d2fe !important;
}
.eqc-row-btn--indigo:hover {
  color: #fff !important;
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  border-color: transparent !important;
}
.eqc-row-btn--rose {
  color: #be123c !important;
  background: #fff1f2 !important;
  border: 1px solid #fecdd3 !important;
}
.eqc-row-btn--rose:hover {
  color: #fff !important;
  background: linear-gradient(135deg, #f43f5e, #e11d48) !important;
  border-color: transparent !important;
}

/* —— レスポンシブ —— */
@media (max-width: 1280px) {
  .eqc-body {
    grid-template-columns: minmax(180px, 220px) minmax(0, 1fr);
  }
  .eqc-hero .pb-hero-desc {
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

@media (max-width: 1100px) {
  .eqc-hero {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .eqc-hero__main {
    width: 100%;
  }
  .eqc-hero__side {
    width: 100%;
    margin-left: 0;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 8px;
  }
  .eqc-switch {
    flex-wrap: wrap;
  }
  .eqc-hero__actions {
    padding-left: 0;
    margin-left: 0;
    border-left: none;
    flex-wrap: wrap;
  }
  .eqc-body {
    grid-template-columns: minmax(160px, 200px) minmax(0, 1fr);
  }
}

@media (max-width: 960px) {
  .eqc-page {
    height: auto;
    max-height: none;
    overflow: auto;
    padding: 6px;
  }
  .eqc-body {
    grid-template-columns: 1fr;
    overflow: visible;
    gap: 8px;
  }
  .eqc-list {
    max-height: min(280px, 36vh);
    overflow: auto;
  }
  .eqc-detail,
  .eqc-placeholder {
    overflow: visible;
    min-height: 360px;
  }
  .eqc-table-body {
    min-height: 280px;
    max-height: none;
  }
  .eqc-cond__group {
    flex: 1 1 100%;
  }
  .eqc-actions__judge {
    margin-left: 0;
    width: 100%;
  }
  .eqc-kpis__strip {
    width: 100%;
  }
  .eqc-kpi {
    flex: 1 1 calc(33.333% - 6px);
    min-width: 120px;
  }
}

@media (max-width: 768px) {
  .eqc-page {
    --eqc-app-chrome: 72px;
    gap: 5px;
    padding: 4px 5px 6px;
  }
  .eqc-mark {
    width: 34px;
    height: 34px;
    border-radius: 10px;
  }
  .eqc-hero .pb-hero-desc {
    display: none;
  }
  .eqc-switch {
    width: 100%;
  }
  .eqc-switch__btn {
    flex: 1 1 0;
    text-align: center;
    padding: 6px 8px;
    min-width: 0;
  }
  .eqc-hero__actions {
    width: 100%;
  }
  .eqc-hero__actions .tb-btn {
    flex: 1 1 auto;
  }
  .eqc-kpi {
    flex: 1 1 calc(50% - 5px);
    min-width: 0;
  }
  .eqc-kpis__scope {
    width: 100%;
  }
  .eqc-field--grow,
  .eqc-field--cd,
  .eqc-field--sm,
  .eqc-field--xs {
    flex: 1 1 calc(50% - 6px);
    width: auto;
    min-width: 96px;
  }
  .eqc-actions__btns {
    width: 100%;
  }
  .eqc-month {
    width: 100%;
    justify-content: space-between;
  }
  .eqc-month :deep(.el-date-editor) {
    width: 140px;
  }
  .eqc-list {
    max-height: min(240px, 32vh);
  }
  .eqc-card__name {
    font-size: var(--eqc-fs);
  }
}

@media (max-width: 480px) {
  .eqc-page {
    --eqc-fs: 12px;
    --eqc-fs-sm: 11px;
    --eqc-fs-lg: 14px;
    --eqc-fs-xl: 15px;
  }
  .eqc-kpi {
    flex: 1 1 calc(50% - 4px);
    padding: 5px 8px 5px 5px;
    min-height: 32px;
    border-radius: 8px;
  }
  .eqc-kpi__icon {
    width: 22px;
    height: 22px;
    border-radius: 6px;
  }
  .eqc-switch__btn {
    font-size: var(--eqc-fs-sm);
    padding: 5px 6px;
  }
  .eqc-hero__actions .tb-btn {
    height: 30px !important;
    padding: 0 10px 0 8px !important;
  }
  .eqc-field--grow,
  .eqc-field--cd,
  .eqc-field--sm,
  .eqc-field--xs {
    flex: 1 1 100%;
  }
  .eqc-mini {
    flex: 1 1 calc(50% - 4px);
  }
  .eqc-actions .tb-btn {
    flex: 1 1 calc(50% - 4px);
    justify-content: center;
  }
  .eqc-chip {
    flex: 1 1 auto;
    justify-content: center;
  }
  .eqc-card {
    padding: 7px 8px;
    gap: 6px;
  }
  .eqc-card__metric {
    min-width: 0;
  }
  .eqc-card__metric--rate,
  .eqc-card__metric--load {
    min-width: 44px;
  }
}

@media (max-width: 360px) {
  .eqc-kpi {
    flex: 1 1 100%;
  }
  .eqc-actions .tb-btn {
    flex: 1 1 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .eqc-kpi:hover { transform: none; }
  .eqc-actions .tb-btn:hover:not(:disabled),
  .eqc-hero__actions .tb-btn:hover:not(:disabled) { transform: none; }
}
</style>

<style>
.eqc-dialog.el-dialog {
  border-radius: 14px;
  overflow: hidden;
}
.eqc-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
}
.eqc-dialog .el-dialog__body {
  padding: 12px 14px 8px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}
.eqc-dialog .el-dialog__footer {
  padding: 10px 14px 12px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.eqc-dlg-header__accent {
  height: 3px;
}
.eqc-dlg-header--amber .eqc-dlg-header__accent {
  background: linear-gradient(90deg, #b45309, #f59e0b, #fcd34d);
}
.eqc-dlg-header--teal .eqc-dlg-header__accent {
  background: linear-gradient(90deg, #0f766e, #14b8a6, #5eead4);
}
.eqc-dlg-header--indigo .eqc-dlg-header__accent {
  background: linear-gradient(90deg, #4338ca, #6366f1, #a5b4fc);
}
.eqc-dlg-header--slate .eqc-dlg-header__accent {
  background: linear-gradient(90deg, #334155, #64748b, #94a3b8);
}
.eqc-dlg-header__main {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px 14px 10px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}
.eqc-dlg-header__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
}
.eqc-dlg-header--amber .eqc-dlg-header__icon {
  background: linear-gradient(145deg, #d97706, #f59e0b);
  box-shadow: 0 8px 18px rgba(217, 119, 6, 0.35);
}
.eqc-dlg-header--teal .eqc-dlg-header__icon {
  background: linear-gradient(145deg, #0f766e, #14b8a6);
  box-shadow: 0 8px 18px rgba(15, 118, 110, 0.35);
}
.eqc-dlg-header--indigo .eqc-dlg-header__icon {
  background: linear-gradient(145deg, #4f46e5, #6366f1);
  box-shadow: 0 8px 18px rgba(79, 70, 229, 0.35);
}
.eqc-dlg-header--slate .eqc-dlg-header__icon {
  background: linear-gradient(145deg, #475569, #64748b);
  box-shadow: 0 8px 18px rgba(71, 85, 105, 0.35);
}
.eqc-dlg-header__title {
  margin: 0 0 2px;
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
}
.eqc-dlg-header__desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}
.eqc-dlg-ok {
  border: none !important;
  color: #fff !important;
  font-weight: 700 !important;
}
.eqc-dlg-ok--green {
  background: linear-gradient(135deg, #047857, #10b981) !important;
  box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
}
.eqc-dlg-ok--teal {
  background: linear-gradient(135deg, #0f766e, #14b8a6) !important;
  box-shadow: 0 4px 14px rgba(15, 118, 110, 0.35);
}
.eqc-dlg-ok--indigo {
  background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
}
.eqc-dlg-ok--slate {
  background: linear-gradient(135deg, #475569, #64748b) !important;
  box-shadow: 0 4px 14px rgba(71, 85, 105, 0.35);
}
.eqc-formula-list {
  margin: 0;
  padding: 14px 16px 14px 30px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #334155;
  font-size: 13px;
  line-height: 1.75;
}
.eqc-formula-list li + li {
  margin-top: 4px;
}
.eqc-dialog .eqc-form,
.eqc-dialog .eqc-takt {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.eqc-dialog .eqc-takt section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.eqc-dialog .eqc-takt h3 { margin: 0; font-size: 13px; color: #0f172a; }
.eqc-dialog .eqc-dialog__lead { margin: 0 0 8px; color: #475569; font-size: 13px; }
.eqc-dialog .eqc-import-table { margin-top: 8px; }
.eqc-dialog .eqc-takt-note {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 10px;
  font-size: 12px;
  color: #64748b;
}
.eqc-transfer-list {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
  max-height: min(420px, 55vh);
  overflow: auto;
  padding: 2px;
}
.eqc-transfer-item.el-radio {
  margin: 0 !important;
  height: auto !important;
  width: 100%;
  min-width: 0;
  justify-content: flex-start;
  align-items: flex-start;
  padding: 8px 10px !important;
  border-radius: 10px !important;
  white-space: normal !important;
}
.eqc-transfer-item :deep(.el-radio__label) {
  padding-left: 6px;
  line-height: 1.25;
  white-space: normal;
  width: 100%;
  min-width: 0;
}
.eqc-transfer-item__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.eqc-transfer-item__name {
  font-weight: 800;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.eqc-transfer-item__cd {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .eqc-transfer-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 720px) {
  .eqc-dialog.el-dialog {
    width: calc(100vw - 24px) !important;
    max-width: 860px;
    margin: 12px auto !important;
  }
  .eqc-dialog .eqc-form,
  .eqc-dialog .eqc-takt {
    grid-template-columns: 1fr;
  }
  .eqc-transfer-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 480px) {
  .eqc-transfer-list {
    grid-template-columns: 1fr;
  }
}
</style>
