<template>
  <div class="rpt-page">
    <div class="rpt-ambient" aria-hidden="true">
      <div class="rpt-orb rpt-orb--a" />
      <div class="rpt-orb rpt-orb--b" />
      <div class="rpt-orb rpt-orb--c" />
    </div>

    <div class="rpt-inner">
    <header class="rpt-toolbar animate-in" style="--delay: 0ms">
      <div class="rpt-brand">
        <div class="rpt-brand__icon">
          <el-icon :size="20"><DataBoard /></el-icon>
        </div>
        <div>
          <h1 class="rpt-brand__title">
            在庫報告管理
            <button type="button" class="rpt-help-btn" title="用語・算出方法の説明" @click="helpVisible = true">
              <el-icon><QuestionFilled /></el-icon>
            </button>
          </h1>
          <p class="rpt-brand__meta">{{ reportTypeLabel }}報告 · {{ selectedPeriodLabel }}</p>
        </div>
      </div>

      <div class="rpt-filters">
        <el-select v-model="fiscalYear" size="small" class="rpt-fy" filterable>
          <el-option v-for="y in fiscalYearOptions" :key="y" :label="`${y}年度`" :value="y" />
        </el-select>
        <el-radio-group v-model="reportType" size="small" class="rpt-period-type">
          <el-radio-button value="quarter">四半期</el-radio-button>
          <el-radio-button value="half">半期</el-radio-button>
          <el-radio-button value="annual">年間</el-radio-button>
        </el-radio-group>
        <el-radio-group v-if="reportType !== 'annual'" v-model="quarter" size="small" class="rpt-quarter">
          <el-radio-button v-for="opt in periodOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <div class="rpt-actions">
        <el-button size="small" class="rpt-btn rpt-btn--slate" :loading="loading" @click="loadSavedList">
          <el-icon><FolderOpened /></el-icon>
          保存一覧
        </el-button>
        <el-button size="small" class="rpt-btn rpt-btn--emerald" :loading="loading" @click="onGenerate">
          <el-icon><MagicStick /></el-icon>
          レポート生成
        </el-button>
        <el-button size="small" class="rpt-btn rpt-btn--amber" :disabled="!payload" @click="onSave('draft')">
          <el-icon><EditPen /></el-icon>
          下書き保存
        </el-button>
        <el-button size="small" class="rpt-btn rpt-btn--blue" :disabled="!payload" @click="onSave('final')">
          <el-icon><CircleCheck /></el-icon>
          確定保存
        </el-button>
        <el-button size="small" class="rpt-btn rpt-btn--violet" :disabled="!payload" @click="onPrint">
          <el-icon><Printer /></el-icon>
          印刷
        </el-button>
      </div>
    </header>

    <div v-if="savedList.length" class="rpt-saved-bar animate-in" style="--delay: 40ms">
      <span class="rpt-saved-bar__label">保存済み</span>
      <button
        v-for="s in savedList"
        :key="s.id"
        type="button"
        class="rpt-saved-chip"
        :class="s.status === 'final' ? 'is-final' : 'is-draft'"
        @click="onLoadSaved(s.id)"
      >
        <i class="rpt-saved-chip__dot" />
        {{ s.label }} · {{ s.status === 'final' ? '確定' : '下書き' }}
      </button>
    </div>

    <el-empty v-if="!payload && !loading" class="rpt-empty" description="年度・報告期間を選び「レポート生成」を実行してください" />

    <div v-else v-loading="loading" class="rpt-body">
      <section v-if="payload" class="rpt-kpi animate-in" :class="`is-${reportType}`" style="--delay: 80ms">
        <div class="rpt-kpi__card theme-wip">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Box /></el-icon></span>
            <div class="rpt-kpi__label">期末仕掛品</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ fmtInt(m.closing_wip_qty) }}</strong>
              <small>本</small>
            </div>
          </div>
        </div>
        <div class="rpt-kpi__card theme-product">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Goods /></el-icon></span>
            <div class="rpt-kpi__label">期末製品</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ fmtInt(m.closing_product_qty) }}</strong>
              <small>本</small>
            </div>
          </div>
        </div>
        <div class="rpt-kpi__card theme-defect">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><WarningFilled /></el-icon></span>
            <div class="rpt-kpi__label">不良率（全工程）</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ fmtPct(m.defect_rate_percent) }}</strong>
              <small>連乘損失率</small>
            </div>
          </div>
        </div>
        <div class="rpt-kpi__card theme-scrap">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Delete /></el-icon></span>
            <div class="rpt-kpi__label">廃棄率（全工程）</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ fmtPct(m.scrap_rate_percent) }}</strong>
              <small>連乘損失率</small>
            </div>
          </div>
        </div>
        <div class="rpt-kpi__card theme-qty">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Histogram /></el-icon></span>
            <div class="rpt-kpi__label">不良／廃棄本数</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ fmtInt(m.defect_qty) }} / {{ fmtInt(m.scrap_qty) }}</strong>
              <small>不良 / 廃棄</small>
            </div>
          </div>
        </div>
        <div class="rpt-kpi__card theme-match">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><CircleCheck /></el-icon></span>
            <div class="rpt-kpi__label">棚卸一致率</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ fmtPct(m.match_rate) }}</strong>
              <small>差異 |Σ| {{ fmtInt(m.diff_abs) }}</small>
            </div>
          </div>
        </div>
        <div
          class="rpt-kpi__card theme-bulk"
          :class="{ 'is-warn': monthlyKpiRows.some((m) => m.bulk_disposal_pending > 0) }"
        >
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Bell /></el-icon></span>
            <div class="rpt-kpi__label">大量廃棄・保留</div>
          </div>
          <div class="rpt-kpi__months">
            <div v-for="m in monthlyKpiRows" :key="m.month" class="rpt-kpi__month">
              <span>{{ m.month_label }}</span>
              <strong>{{ m.bulk_disposal_count }}件</strong>
              <small>未処理 {{ m.bulk_disposal_pending }} / {{ fmtInt(m.bulk_disposal_quantity) }}本</small>
            </div>
          </div>
        </div>
      </section>

      <section v-if="payload?.highlights?.length" class="rpt-highlights animate-in" style="--delay: 120ms">
        <div
          v-for="(h, i) in payload.highlights"
          :key="i"
          class="rpt-hl"
          :class="hlThemeClass(h)"
        >
          <span class="rpt-hl__ico">
            <el-icon><component :is="hlIcon(h.type)" /></el-icon>
          </span>
          <div class="rpt-hl__body">
            <strong class="rpt-hl__title">{{ h.title }}</strong>
            <!-- eslint-disable-next-line vue/no-v-html : バックエンド生成テキストをエスケープ後に数値のみ装飾 -->
            <span class="rpt-hl__text" v-html="hlRichText(h.text)" />
          </div>
        </div>
      </section>

      <section v-if="previousPeriod" class="rpt-qoq animate-in" style="--delay: 140ms">
        <div class="rpt-qoq__lead">
          <span class="rpt-qoq__badge"><el-icon><TrendCharts /></el-icon></span>
          <div class="rpt-qoq__caption">
            <strong>前期間比（期末在庫）</strong>
            <small>vs {{ previousPeriod.label }}</small>
          </div>
        </div>
        <div class="rpt-qoq__stats">
          <div class="rpt-qoq__stat rpt-qoq__stat--total" :data-dir="deltaDir(previousPeriod.delta_total_qty)">
            <span class="rpt-qoq__stat-label">合計</span>
            <span class="rpt-qoq__stat-value">
              <el-icon class="rpt-qoq__arrow"><component :is="deltaArrow(previousPeriod.delta_total_qty)" /></el-icon>
              {{ fmtSigned(previousPeriod.delta_total_qty) }}
              <i>本</i>
            </span>
          </div>
          <div class="rpt-qoq__stat" :data-dir="deltaDir(previousPeriod.delta_wip_qty)">
            <span class="rpt-qoq__stat-label">仕掛品</span>
            <span class="rpt-qoq__stat-value">
              <el-icon class="rpt-qoq__arrow"><component :is="deltaArrow(previousPeriod.delta_wip_qty)" /></el-icon>
              {{ fmtSigned(previousPeriod.delta_wip_qty) }}
              <i>本</i>
            </span>
          </div>
          <div class="rpt-qoq__stat" :data-dir="deltaDir(previousPeriod.delta_product_qty)">
            <span class="rpt-qoq__stat-label">製品</span>
            <span class="rpt-qoq__stat-value">
              <el-icon class="rpt-qoq__arrow"><component :is="deltaArrow(previousPeriod.delta_product_qty)" /></el-icon>
              {{ fmtSigned(previousPeriod.delta_product_qty) }}
              <i>本</i>
            </span>
          </div>
        </div>
      </section>

      <div class="rpt-charts animate-in" style="--delay: 160ms">
        <div class="rpt-chart-card accent-blue">
          <div class="rpt-chart-card__title">
            <el-icon><Box /></el-icon>
            月末在庫（仕掛品・製品）
          </div>
          <div ref="invChartRef" class="rpt-chart-host" />
        </div>
        <div class="rpt-chart-card accent-rose">
          <div class="rpt-chart-card__title">
            <el-icon><TrendCharts /></el-icon>
            不良率・廃棄率推移
          </div>
          <div ref="scrapRateChartRef" class="rpt-chart-host" />
        </div>
        <div class="rpt-chart-card accent-amber">
          <div class="rpt-chart-card__title">
            <el-icon><Histogram /></el-icon>
            不良・廃棄本数（月別）
          </div>
          <div ref="scrapQtyChartRef" class="rpt-chart-host" />
        </div>
        <div class="rpt-chart-card accent-violet">
          <div class="rpt-chart-card__title">
            <el-icon><DataAnalysis /></el-icon>
            棚卸差異（月別×工程）
          </div>
          <div ref="diffChartRef" class="rpt-chart-host" />
        </div>
      </div>

      <section class="rpt-edit-launcher animate-in" style="--delay: 180ms">
        <div class="rpt-edit-launcher__info">
          <span class="rpt-edit-launcher__icon"><el-icon><EditPen /></el-icon></span>
          <span class="rpt-edit-launcher__text">
            <strong>廃棄率・不良本数・廃棄本数（手動修正）</strong>
            <small>報告用の数値を月別に上書きできます。修正はグラフへ即時反映されます。</small>
          </span>
        </div>
        <div class="rpt-edit-launcher__actions">
          <el-tag v-if="scrapOverrideCount > 0" type="warning" effect="light" round>
            修正 {{ scrapOverrideCount }} 件
          </el-tag>
          <el-button class="rpt-btn rpt-btn--edit" @click="scrapEditDialogVisible = true">
            <el-icon><EditPen /></el-icon>修正する
          </el-button>
        </div>
      </section>

      <el-dialog
        v-model="scrapEditDialogVisible"
        class="rpt-edit-dialog"
        width="1040px"
        top="6vh"
        :close-on-click-modal="false"
      >
        <template #header>
          <div class="rpt-edit-dialog__head">
            <span class="rpt-edit-dialog__icon"><el-icon><EditPen /></el-icon></span>
            <span class="rpt-edit-dialog__titles">
              <strong>廃棄率・不良本数・廃棄本数（手動修正）</strong>
              <small>計算値をベースに、報告用の値を月別に修正できます</small>
            </span>
          </div>
        </template>
        <el-table :data="scrapEditRows" size="small" border class="rpt-table rpt-edit-table">
          <el-table-column prop="month_label" label="月" width="72" align="center" fixed>
            <template #default="{ row }">
              <span class="rpt-edit-table__month">{{ row.month_label }}</span>
            </template>
          </el-table-column>
          <el-table-column label="廃棄率(%)" align="center">
            <el-table-column label="計算値" width="104" align="right" class-name="col-calc">
              <template #default="{ row }">{{ fmtPct(row.calc_rate) }}</template>
            </el-table-column>
            <el-table-column label="報告用" width="148" align="right" class-name="col-edit">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.edit_rate"
                  size="small"
                  :step="0.01"
                  :precision="2"
                  controls-position="right"
                  class="rpt-num"
                  :class="{ 'is-modified': row.edit_rate !== row.calc_rate }"
                  @change="onScrapEdit"
                />
              </template>
            </el-table-column>
          </el-table-column>
          <el-table-column label="不良本数" align="center">
            <el-table-column label="計算値" width="104" align="right" class-name="col-calc">
              <template #default="{ row }">{{ fmtInt(row.calc_defect) }}</template>
            </el-table-column>
            <el-table-column label="報告用" width="148" align="right" class-name="col-edit">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.edit_defect"
                  size="small"
                  :step="1"
                  :precision="0"
                  controls-position="right"
                  class="rpt-num"
                  :class="{ 'is-modified': row.edit_defect !== row.calc_defect }"
                  @change="onScrapEdit"
                />
              </template>
            </el-table-column>
          </el-table-column>
          <el-table-column label="廃棄本数" align="center">
            <el-table-column label="計算値" width="104" align="right" class-name="col-calc">
              <template #default="{ row }">{{ fmtInt(row.calc_scrap) }}</template>
            </el-table-column>
            <el-table-column label="報告用" width="148" align="right" class-name="col-edit">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.edit_scrap"
                  size="small"
                  :step="1"
                  :precision="0"
                  controls-position="right"
                  class="rpt-num"
                  :class="{ 'is-modified': row.edit_scrap !== row.calc_scrap }"
                  @change="onScrapEdit"
                />
              </template>
            </el-table-column>
          </el-table-column>
          <el-table-column label="コメント" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.note" size="small" placeholder="説明・特記事項" @change="onScrapEdit" />
            </template>
          </el-table-column>
        </el-table>
        <div class="rpt-edit-dialog__hint">
          <el-icon><InfoFilled /></el-icon>
          修正した値は黄色でハイライトされ、グラフ・KPIに即時反映されます。保存すると報告書に記録されます。
        </div>
        <template #footer>
          <div class="rpt-edit-dialog__footer">
            <el-button text type="warning" @click="resetScrapOverrides">
              <el-icon><RefreshLeft /></el-icon>修正リセット
            </el-button>
            <el-button type="primary" class="rpt-btn rpt-btn--edit" @click="scrapEditDialogVisible = false">
              閉じる
            </el-button>
          </div>
        </template>
      </el-dialog>

      <section class="rpt-block accent-violet animate-in" style="--delay: 200ms">
        <div class="rpt-block__head">
          <span class="rpt-block__title"><el-icon><ScaleToOriginal /></el-icon>理論在庫 vs 棚卸差異（月別・工程別）</span>
        </div>
        <el-table
          :data="payload?.diff_by_month_process || []"
          size="small"
          border
          max-height="360"
          class="rpt-table rpt-diff-table"
          :row-class-name="diffRowClass"
        >
          <el-table-column prop="month_label" label="月" width="82" fixed align="center">
            <template #default="{ row }">
              <span class="diff-month-badge" :class="`diff-month-badge--${diffMonthIdx(row.month_label)}`">
                {{ row.month_label }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="process_name" label="工程" width="120">
            <template #default="{ row }">
              <span class="diff-proc">{{ row.process_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="process_cd" label="工程CD" width="90">
            <template #default="{ row }">
              <span class="diff-proc-cd">{{ row.process_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="theoretical_qty" label="理論在庫" width="110" align="right">
            <template #default="{ row }">{{ fmtInt(row.theoretical_qty) }}</template>
          </el-table-column>
          <el-table-column prop="stocktake_qty" label="棚卸在庫" width="110" align="right">
            <template #default="{ row }">{{ fmtInt(row.stocktake_qty) }}</template>
          </el-table-column>
          <el-table-column prop="diff_qty" label="差異" width="100" align="right">
            <template #default="{ row }">
              <span class="diff-strong" :class="deltaClass(row.diff_qty)">{{ fmtSigned(row.diff_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="diff_rate" label="差異率%" width="100" align="right">
            <template #default="{ row }">{{ row.diff_rate == null ? '—' : fmtPct(row.diff_rate) }}</template>
          </el-table-column>
          <el-table-column prop="match_rate" label="一致率%" width="100" align="right">
            <template #default="{ row }">
              <span class="diff-match" :class="matchRateClass(row.match_rate)">{{ fmtPct(row.match_rate) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <div class="rpt-two-col animate-in" style="--delay: 220ms">
        <section class="rpt-block accent-blue">
          <div class="rpt-block__head">
            <span class="rpt-block__title"><el-icon><List /></el-icon>差異が大きい品目（上位）</span>
          </div>
          <el-table :data="payload?.top_mismatch || []" size="small" border max-height="320" class="rpt-table rpt-top-table">
            <el-table-column label="#" width="52" align="center">
              <template #default="{ $index }">
                <span class="top-rank" :class="`top-rank--${Math.min($index + 1, 4)}`">{{ $index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="month_label" label="月" width="76" align="center">
              <template #default="{ row }">
                <span class="diff-month-badge" :class="`diff-month-badge--${diffMonthIdx(row.month_label)}`">
                  {{ row.month_label }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="product_cd" label="製品CD" width="110">
              <template #default="{ row }">
                <span class="diff-proc-cd">{{ row.product_cd }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="diff-proc">{{ row.product_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="process_name" label="工程" width="100" />
            <el-table-column prop="theoretical_qty" label="理論" width="80" align="right">
              <template #default="{ row }">
                <span class="diff-num">{{ fmtInt(Number(row.theoretical_qty)) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="stocktake_qty" label="棚卸" width="80" align="right">
              <template #default="{ row }">
                <span class="diff-num">{{ fmtInt(Number(row.stocktake_qty)) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="diff_qty" label="差異" width="80" align="right">
              <template #default="{ row }">
                <span class="diff-strong" :class="deltaClass(Number(row.diff_qty))">{{ fmtSigned(Number(row.diff_qty)) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rpt-block accent-amber">
          <div class="rpt-block__head">
            <span class="rpt-block__title"><el-icon><Bell /></el-icon>大量廃棄・保留品（対象期間）</span>
          </div>
          <el-table
            :data="payload?.bulk_disposal?.items || []"
            size="small"
            border
            max-height="320"
            class="rpt-table rpt-bulk-table"
          >
            <el-table-column prop="occurred_date" label="発生日" width="108">
              <template #default="{ row }">
                <span class="bulk-date">{{ row.occurred_date || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="report_category" label="区分" width="96" align="center">
              <template #default="{ row }">
                <span class="bulk-chip" :class="bulkCategoryClass(row.report_category)">
                  {{ row.report_category || '—' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="process_name" label="工程" width="80" />
            <el-table-column prop="product_name" label="製品" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="diff-proc">{{ row.product_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="本数" width="90" align="right">
              <template #default="{ row }">
                <span class="diff-strong bulk-qty">{{ fmtInt(Number(row.quantity)) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="handling_status" label="状態" width="88" align="center">
              <template #default="{ row }">
                <span class="bulk-chip" :class="bulkStatusClass(row.handling_status)">
                  {{ row.handling_status || '—' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </div>

      <section class="rpt-block accent-teal rpt-notes animate-in" style="--delay: 240ms">
        <div class="rpt-block__head">
          <span class="rpt-block__title"><el-icon><Document /></el-icon>報告メモ</span>
          <el-button size="small" class="rpt-btn rpt-btn--violet" :disabled="!payload" @click="onAutoAnalysis">
            <el-icon><MagicStick /></el-icon>
            自動分析を挿入
          </el-button>
        </div>
        <div class="rpt-notes__grid">
          <div class="rpt-notes__field">
            <label>エグゼクティブサマリ</label>
            <el-input
              v-model="executiveSummary"
              type="textarea"
              :rows="4"
              placeholder="本期要点・数値ハイライト・判断事項…"
            />
          </div>
          <div class="rpt-notes__field">
            <label>改善アクション</label>
            <el-input
              v-model="actionItems"
              type="textarea"
              :rows="4"
              placeholder="差異原因の調査、廃棄削減施策、担当・期限…"
            />
          </div>
          <div class="rpt-notes__full rpt-notes__field">
            <label>備考</label>
            <el-input v-model="notes" type="textarea" :rows="2" placeholder="補足説明" />
          </div>
        </div>
      </section>

      <section class="rpt-block accent-slate rpt-ideas animate-in" style="--delay: 260ms">
        <div class="rpt-block__head">
          <span class="rpt-block__title"><el-icon><MagicStick /></el-icon>報告向け・追加で使える観点</span>
        </div>
        <ul>
          <li>前期間比・前年同期比（在庫・廃棄率・一致率）</li>
          <li>仕掛品／製品構成比の変化と滞留リスク</li>
          <li>棚卸差異 Top 品目の原因コメント欄（今回の手動メモ欄で運用可）</li>
          <li>大量廃棄・保留品の未処理件数と期限超過アラート</li>
          <li>工程別廃棄率ヒートマップと目標ライン（例: 2%）の並記</li>
          <li>在庫金額（棚卸金額管理と連携）での金額ベース報告</li>
        </ul>
      </section>
    </div>
    </div>

    <el-dialog
      v-model="helpVisible"
      class="rpt-help-dialog"
      width="860px"
      top="5vh"
    >
      <template #header>
        <div class="rpt-help-dialog__head">
          <span class="rpt-help-dialog__icon"><el-icon><QuestionFilled /></el-icon></span>
          <span class="rpt-help-dialog__titles">
            <strong>用語・算出方法の説明</strong>
            <small>このページで使われる名詞の定義と計算ロジック</small>
          </span>
        </div>
      </template>
      <div class="rpt-help">
        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-blue">期間・集計対象</h3>
          <dl>
            <dt>年度・報告期間</dt>
            <dd>年度は4月始まり。四半期はQ1=4–6月、Q2=7–9月、Q3=10–12月、Q4=1–3月。半期は上期=4–9月・下期=10–3月、年間は4–3月の12か月です。</dd>
            <dt>集計対象の除外</dt>
            <dd>製品名に「加工」を含む製品は、ページ内すべての統計から除外されます。製品側の棚卸集計は製品CD末尾が「1」の行のみが対象です。</dd>
            <dt>月末時点（as of）</dt>
            <dd>各月の集計は、その月の生産集計データが存在する最終日時点のスナップショットで行います。</dd>
          </dl>
        </section>

        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-teal">在庫指標</h3>
          <dl>
            <dt>月末在庫（仕掛品・製品）</dt>
            <dd>
              生産集計の工程別在庫列を月末時点で合算します。
              <b>仕掛品</b>＝切断・面取・成型・メッキ・外注メッキ・溶接・外注溶接・溶接前検査・外注支給前・外注検査前の在庫合計、
              <b>製品</b>＝検査・倉庫・外注倉庫の在庫合計。
            </dd>
            <dt>前期間比</dt>
            <dd>選択期間末月の月末在庫と、同じ報告単位の前期間末月との差分。四半期は前Q、半期は前半期、年間は前年度と比較します。</dd>
          </dl>
        </section>

        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-amber">品質指標</h3>
          <dl>
            <dt>不良率／廃棄率（全工程）</dt>
            <dd>
              工程実績を単純合算すると同一製品が工程間で重複するため、<b>全工程の連乗方式</b>で算出します。
              <code>全工程率 = 1 − Π(1 − 工程別率)</code>、工程別率＝その工程の不良（または廃棄）本数 ÷ 実績本数。
              実績が0の工程は計算から除外します。
            </dd>
            <dt>品質ロス率（不良＋廃棄）</dt>
            <dd>不良＋廃棄の合計本数を使い、同じ連乗方式で算出した総合損失率。不良率と廃棄率の単純合計より正確です。</dd>
            <dt>不良本数・廃棄本数</dt>
            <dd>全工程の不良・廃棄本数の合計。「手動修正」で報告用の値に上書きでき、グラフ・KPI・印刷へ即時反映されます（計算値も保持されます）。</dd>
            <dt>目安 2%</dt>
            <dd>廃棄率の管理目安ライン。超過した月は自動分析・ハイライトで注意喚起されます。</dd>
          </dl>
        </section>

        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-violet">棚卸差異</h3>
          <dl>
            <dt>理論在庫</dt>
            <dd>生産集計（実績・繰越・推移）から計算上あるべき在庫数。月末時点・製品×工程単位で集計します。</dd>
            <dt>棚卸在庫</dt>
            <dd>実地棚卸（棚卸記録）で実際に数えた在庫数。</dd>
            <dt>棚卸差異</dt>
            <dd>
              <code>差異 = 棚卸在庫 − 理論在庫</code>。プラスは帳簿より実物が多い、マイナスは実物が少ないことを意味します。
            </dd>
            <dt>差異率</dt>
            <dd><code>差異率 = 差異 ÷ 理論在庫 × 100</code>。理論在庫が0の場合は表示しません（—）。</dd>
            <dt>一致率</dt>
            <dd>製品×工程の明細のうち、理論と棚卸が一致した件数の割合。95%以上を目安に、下回る場合は原因調査を推奨します。</dd>
            <dt>差異絶対値合計</dt>
            <dd>各月の差異合計の絶対値を対象期間で合算した値。プラスマイナスの相殺を避け、差異の規模を把握するための指標です。</dd>
          </dl>
        </section>

        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-rose">その他</h3>
          <dl>
            <dt>大量廃棄・保留品</dt>
            <dd>「大量廃棄・保留品管理」に登録された、選択期間内に発生した記録の集計。未処理件数が残っている場合は対応を促します。</dd>
            <dt>下書き保存／確定保存</dt>
            <dd>集計スナップショット・手動修正・報告メモをまとめて保存します。確定保存は報告版として記録する場合に使用します。</dd>
            <dt>自動分析を挿入</dt>
            <dd>在庫トレンド・品質・棚卸差異・大量廃棄の集計値から、報告メモ（サマリ・改善アクション）の下書きを自動生成します。</dd>
            <dt>印刷</dt>
            <dd>画面そのものではなく、生成レポートと同じ内容をA4の報告書レイアウト（表・グラフ入り）に整形して印刷します。</dd>
          </dl>
        </section>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  Box,
  CaretBottom,
  CaretTop,
  CircleCheck,
  DataAnalysis,
  DataBoard,
  Delete,
  Document,
  EditPen,
  FolderOpened,
  Goods,
  Histogram,
  InfoFilled,
  List,
  MagicStick,
  Minus,
  Printer,
  QuestionFilled,
  RefreshLeft,
  ScaleToOriginal,
  TrendCharts,
  WarningFilled,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  inventoryReportApi,
  type MonthlyReportKpi,
  type QuarterlyReportPayload,
  type ReportHighlight,
  type ScrapOverrides,
  type SavedReportSummary,
} from '@/api/inventoryReport'

const loading = ref(false)
const fiscalYear = ref(new Date().getFullYear())
const reportType = ref<'quarter' | 'half' | 'annual'>('quarter')
const quarter = ref(1)
const periodOptions = computed(() => {
  if (reportType.value === 'half') {
    return [
      { value: 5, label: '上期 4–9' },
      { value: 6, label: '下期 10–3' },
    ]
  }
  if (reportType.value === 'annual') return [{ value: 7, label: '年間 4–3' }]
  return [
    { value: 1, label: 'Q1 4–6' },
    { value: 2, label: 'Q2 7–9' },
    { value: 3, label: 'Q3 10–12' },
    { value: 4, label: 'Q4 1–3' },
  ]
})
const reportTypeLabel = computed(() =>
  reportType.value === 'quarter' ? '四半期' : reportType.value === 'half' ? '半期' : '年間'
)
const selectedPeriodLabel = computed(
  () => periodOptions.value.find((opt) => opt.value === quarter.value)?.label || '年間 4–3'
)
const fiscalYearOptions = computed(() => {
  const y = new Date().getFullYear()
  return [y - 2, y - 1, y, y + 1]
})

const payload = ref<QuarterlyReportPayload | null>(null)
const previousPeriod = computed(
  () => payload.value?.previous_period ?? payload.value?.previous_quarter ?? null
)
const savedId = ref<number | null>(null)
const savedList = ref<SavedReportSummary[]>([])
const scrapOverrides = ref<ScrapOverrides>({})
const scrapEditDialogVisible = ref(false)
const scrapOverrideCount = computed(() => Object.keys(scrapOverrides.value).length)
const helpVisible = ref(false)
const executiveSummary = ref('')
const actionItems = ref('')
const notes = ref('')

type ScrapEditRow = {
  month: string
  month_label: string
  calc_rate: number | null
  calc_defect: number
  calc_scrap: number
  edit_rate: number | null
  edit_defect: number
  edit_scrap: number
  note: string
}
const scrapEditRows = ref<ScrapEditRow[]>([])

const invChartRef = ref<HTMLDivElement | null>(null)
const scrapRateChartRef = ref<HTMLDivElement | null>(null)
const scrapQtyChartRef = ref<HTMLDivElement | null>(null)
const diffChartRef = ref<HTMLDivElement | null>(null)
let invChart: ECharts | null = null
let scrapRateChart: ECharts | null = null
let scrapQtyChart: ECharts | null = null
let diffChart: ECharts | null = null

const monthlyKpiRows = computed<MonthlyReportKpi[]>(() => {
  const report = payload.value
  if (!report) return []
  const apiRows = report.monthly_kpis || []

  return report.inventory_series.map((inv) => {
    const base = apiRows.find((r) => r.month === inv.month)
    const edit = scrapEditRows.value.find((r) => r.month === inv.month)
    const qualitySeries = report.scrap_series.find((r) => r.month === inv.month)
    const legacyMonth = report.months.find((m) => String(m.month || '') === inv.month) as
      | { stocktake_diff?: { kpi?: { match_rate?: number; diff_qty_total?: number } } }
      | undefined
    const legacyBulkItems = (report.bulk_disposal?.items || []).filter((item) =>
      String(item.occurred_date || '').startsWith(inv.month)
    )
    const legacyBulk = report.bulk_disposal?.by_month?.find((r) => r.month === inv.month)

    return {
      month: inv.month,
      month_label: inv.month_label,
      closing_wip_qty: base?.closing_wip_qty ?? inv.wip_qty,
      closing_product_qty: base?.closing_product_qty ?? inv.product_qty,
      closing_total_qty: base?.closing_total_qty ?? inv.total_qty,
      scrap_rate_percent: edit?.edit_rate ?? base?.scrap_rate_percent ?? null,
      defect_rate_percent:
        base?.defect_rate_percent ?? qualitySeries?.defect_rate_percent ?? null,
      defect_qty: edit?.edit_defect ?? base?.defect_qty ?? 0,
      scrap_qty: edit?.edit_scrap ?? base?.scrap_qty ?? 0,
      match_rate:
        base?.match_rate ?? Number(legacyMonth?.stocktake_diff?.kpi?.match_rate || 0),
      diff_abs:
        base?.diff_abs ??
        Math.abs(Number(legacyMonth?.stocktake_diff?.kpi?.diff_qty_total || 0)),
      bulk_disposal_count:
        base?.bulk_disposal_count ?? legacyBulk?.count ?? legacyBulkItems.length,
      bulk_disposal_quantity:
        base?.bulk_disposal_quantity ??
        legacyBulk?.quantity ??
        legacyBulkItems.reduce((sum, item) => sum + Number(item.quantity || 0), 0),
      bulk_disposal_pending:
        base?.bulk_disposal_pending ??
        legacyBulk?.pending_count ??
        legacyBulkItems.filter((item) => item.handling_status === '未処理').length,
    }
  })
})

function fmtInt(v: number | null | undefined) {
  if (v == null || Number.isNaN(Number(v))) return '0'
  return Number(v).toLocaleString()
}

function fmtPct(v: number | null | undefined) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return `${Number(v).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`
}

function fmtSigned(v: number | null | undefined) {
  const n = Number(v) || 0
  if (n > 0) return `+${n.toLocaleString()}`
  return n.toLocaleString()
}

function reportTypeForCode(code: number): 'quarter' | 'half' | 'annual' {
  if (code <= 4) return 'quarter'
  if (code <= 6) return 'half'
  return 'annual'
}

function deltaClass(v: number | null | undefined) {
  const n = Number(v) || 0
  if (n > 0) return 'num-up'
  if (n < 0) return 'num-down'
  return ''
}

function deltaDir(v: number | null | undefined) {
  const n = Number(v) || 0
  if (n > 0) return 'up'
  if (n < 0) return 'down'
  return 'flat'
}

function deltaArrow(v: number | null | undefined) {
  const n = Number(v) || 0
  if (n > 0) return CaretTop
  if (n < 0) return CaretBottom
  return Minus
}

/** 差異テーブル：月ラベル → 月インデックス（0〜2、色分け用） */
const diffMonthIndexMap = computed(() => {
  const map: Record<string, number> = {}
  let i = 0
  for (const r of payload.value?.diff_by_month_process || []) {
    const key = String(r.month_label || '')
    if (!(key in map)) map[key] = i++
  }
  return map
})

function diffMonthIdx(monthLabel: string | null | undefined) {
  return (diffMonthIndexMap.value[String(monthLabel || '')] ?? 0) % 3
}

function diffRowClass({ row, rowIndex }: { row: { month_label?: string }; rowIndex: number }) {
  const rows = payload.value?.diff_by_month_process || []
  const prev = rowIndex > 0 ? rows[rowIndex - 1] : null
  const firstOfMonth = !prev || prev.month_label !== row.month_label
  return `diff-month-${diffMonthIdx(row.month_label)}${firstOfMonth ? ' diff-month-first' : ''}`
}

function matchRateClass(v: number | null | undefined) {
  const n = Number(v) || 0
  if (n >= 95) return 'diff-match--good'
  if (n >= 85) return 'diff-match--warn'
  return 'diff-match--bad'
}

function bulkCategoryClass(category: string | null | undefined) {
  const s = String(category || '')
  if (s.includes('廃棄')) return 'bulk-chip--rose'
  if (s.includes('保留')) return 'bulk-chip--amber'
  return 'bulk-chip--slate'
}

function bulkStatusClass(status: string | null | undefined) {
  const s = String(status || '')
  if (s.includes('未')) return 'bulk-chip--bad'
  if (s) return 'bulk-chip--good'
  return 'bulk-chip--slate'
}

/** ハイライト種別 → テーマ色クラス（tone は強調度の補助のみ） */
function hlThemeClass(h: ReportHighlight) {
  const typeTheme: Record<string, string> = {
    inventory_trend: 'hl-blue',
    defect_peak: 'hl-amber',
    scrap_peak: 'hl-rose',
    stocktake_match: 'hl-green',
    bulk_disposal: 'hl-violet',
    qoq: 'hl-teal',
  }
  const cls = typeTheme[h.type] || 'hl-slate'
  return [cls, h.tone === 'bad' || h.tone === 'warn' ? 'is-attention' : '']
}

function hlIcon(type: string) {
  const icons: Record<string, unknown> = {
    inventory_trend: TrendCharts,
    defect_peak: WarningFilled,
    scrap_peak: Delete,
    stocktake_match: CircleCheck,
    bulk_disposal: Bell,
    qoq: DataAnalysis,
  }
  return icons[type] || DataBoard
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/** 数値（±・カンマ・小数・%・本・件）だけ着色するリッチテキスト */
function hlRichText(text: string) {
  const escaped = escapeHtml(String(text || ''))
  return escaped.replace(
    /([+\-−]?\d[\d,]*(?:\.\d+)?)(\s*(?:%|％|本|件|月)?)/g,
    (_all, num: string, unit: string) => {
      const isNegative = /^[-−]/.test(num)
      const isPositive = /^\+/.test(num)
      const cls = isNegative ? 'hl-num hl-num--down' : isPositive ? 'hl-num hl-num--up' : 'hl-num'
      return `<em class="${cls}">${num}</em><i class="hl-unit">${unit}</i>`
    }
  )
}

function syncScrapEditRows() {
  const series = payload.value?.scrap_series || []
  scrapEditRows.value = series.map((s) => {
    const ov = scrapOverrides.value[s.month]
    // 旧保存レポートは sum_defect 未保持のため、不良＋廃棄から復元する。
    const calcDefect =
      s.sum_defect ?? Math.max(0, Number(s.sum_defect_and_scrap || 0) - Number(s.sum_scrap || 0))
    return {
      month: s.month,
      month_label: s.month_label,
      calc_rate: s.rate_percent,
      calc_defect: calcDefect,
      calc_scrap: s.sum_scrap,
      edit_rate: ov?.rate_percent != null ? ov.rate_percent : s.rate_percent,
      edit_defect: ov?.sum_defect != null ? Number(ov.sum_defect) : calcDefect,
      edit_scrap: ov?.sum_scrap != null ? Number(ov.sum_scrap) : s.sum_scrap,
      note: ov?.note || '',
    }
  })
}

function onScrapEdit() {
  const next: ScrapOverrides = {}
  for (const r of scrapEditRows.value) {
    const base = payload.value?.scrap_series.find((s) => s.month === r.month)
    const rateChanged = r.edit_rate !== base?.rate_percent
    const defectChanged = r.edit_defect !== base?.sum_defect
    const scrapChanged = r.edit_scrap !== base?.sum_scrap
    if (rateChanged || defectChanged || scrapChanged || r.note) {
      next[r.month] = {
        rate_percent: r.edit_rate,
        sum_defect: r.edit_defect,
        sum_scrap: r.edit_scrap,
        note: r.note || undefined,
      }
    }
  }
  scrapOverrides.value = next
  renderCharts()
}

function resetScrapOverrides() {
  scrapOverrides.value = {}
  syncScrapEditRows()
  renderCharts()
}

function disposeCharts() {
  invChart?.dispose()
  scrapRateChart?.dispose()
  scrapQtyChart?.dispose()
  diffChart?.dispose()
  invChart = scrapRateChart = scrapQtyChart = diffChart = null
}

function renderCharts() {
  if (!payload.value) return
  const labels = payload.value.inventory_series.map((x) => x.month_label)
  const wip = payload.value.inventory_series.map((x) => x.wip_qty)
  const prod = payload.value.inventory_series.map((x) => x.product_qty)

  if (invChartRef.value) {
    if (!invChart) invChart = echarts.init(invChartRef.value)
    const totals = payload.value.inventory_series.map((x) => x.total_qty)
    invChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(59, 130, 246, 0.06)' } },
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: 'rgba(147, 197, 253, 0.6)',
        borderWidth: 1,
        padding: [8, 12],
        textStyle: { color: '#0f172a', fontSize: 12 },
        extraCssText: 'box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14); border-radius: 10px;',
        valueFormatter: (v: unknown) => `${Number(v ?? 0).toLocaleString()} 本`,
      },
      legend: {
        data: ['仕掛品', '製品'],
        top: 0,
        itemWidth: 14,
        itemHeight: 9,
        icon: 'roundRect',
        textStyle: { color: '#475569', fontWeight: 600 },
      },
      grid: { left: 56, right: 20, top: 48, bottom: 30 },
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        axisLabel: { color: '#475569', fontWeight: 700, fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        name: '本',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: {
          color: '#94a3b8',
          formatter: (v: number) => (v >= 10000 ? `${(v / 10000).toLocaleString()}万` : v.toLocaleString()),
        },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.25)' } },
      },
      animationDuration: 900,
      animationEasing: 'elasticOut',
      series: [
        {
          name: '仕掛品',
          type: 'bar',
          stack: 'inv',
          barMaxWidth: 64,
          data: wip,
          itemStyle: {
            borderRadius: [0, 0, 4, 4],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#60a5fa' },
              { offset: 1, color: '#2563eb' },
            ]),
            shadowColor: 'rgba(37, 99, 235, 0.28)',
            shadowBlur: 8,
            shadowOffsetY: 3,
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 14, shadowColor: 'rgba(37, 99, 235, 0.45)' },
          },
          label: {
            show: true,
            position: 'inside',
            color: '#fff',
            fontSize: 11,
            fontWeight: 700,
            textShadowColor: 'rgba(15, 23, 42, 0.35)',
            textShadowBlur: 4,
            formatter: ({ value }: { value: number }) =>
              Number(value) > 0 ? Number(value).toLocaleString() : '',
          },
          animationDelay: (idx: number) => idx * 120,
        },
        {
          name: '製品',
          type: 'bar',
          stack: 'inv',
          barMaxWidth: 64,
          data: prod,
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#5eead4' },
              { offset: 1, color: '#0d9488' },
            ]),
            shadowColor: 'rgba(13, 148, 136, 0.28)',
            shadowBlur: 8,
            shadowOffsetY: 3,
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 14, shadowColor: 'rgba(13, 148, 136, 0.45)' },
          },
          label: {
            show: true,
            position: 'inside',
            color: '#fff',
            fontSize: 11,
            fontWeight: 700,
            textShadowColor: 'rgba(15, 23, 42, 0.35)',
            textShadowBlur: 4,
            formatter: ({ value }: { value: number }) =>
              Number(value) > 0 ? Number(value).toLocaleString() : '',
          },
          animationDelay: (idx: number) => idx * 120 + 60,
        },
        {
          // 合計ラベル用の透明系列（積み上げ最上部に合計値を表示）
          name: '合計',
          type: 'bar',
          stack: 'inv',
          barMaxWidth: 64,
          data: totals.map(() => 0),
          itemStyle: { color: 'transparent' },
          tooltip: { show: false },
          silent: true,
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: '#1e3a8a',
            fontSize: 12,
            fontWeight: 800,
            formatter: ({ dataIndex }: { dataIndex: number }) =>
              `計 ${Number(totals[dataIndex] ?? 0).toLocaleString()}`,
          },
        },
      ],
    })
  }

  const scrapLabels = scrapEditRows.value.map((r) => r.month_label)
  const scrapRates = scrapEditRows.value.map((r) => r.edit_rate)
  const defectQtys = scrapEditRows.value.map((r) => r.edit_defect)
  const scrapQtys = scrapEditRows.value.map((r) => r.edit_scrap)
  const defectRates = scrapEditRows.value.map((r) => {
    const hit = payload.value?.scrap_series.find((s) => s.month === r.month)
    return hit?.defect_rate_percent ?? null
  })
  const qualityLossRates = scrapEditRows.value.map((r) => {
    const hit = payload.value?.scrap_series.find((s) => s.month === r.month)
    return hit?.quality_loss_rate_percent ?? null
  })

  if (scrapRateChartRef.value) {
    if (!scrapRateChart) scrapRateChart = echarts.init(scrapRateChartRef.value)
    const pctLabel = {
      show: true,
      fontSize: 11,
      fontWeight: 700,
      formatter: ({ value }: { value: number | null }) =>
        value == null ? '' : `${Number(value).toFixed(2)}%`,
    }
    scrapRateChart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: 'rgba(251, 191, 36, 0.5)',
        borderWidth: 1,
        padding: [8, 12],
        textStyle: { color: '#0f172a', fontSize: 12 },
        extraCssText: 'box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14); border-radius: 10px;',
        valueFormatter: (v: unknown) => (v == null ? '-' : `${Number(v).toFixed(2)}%`),
      },
      legend: {
        data: ['ロス率（不良＋廃棄）', '不良率', '廃棄率'],
        top: 0,
        itemWidth: 18,
        itemHeight: 4,
        textStyle: { color: '#475569', fontWeight: 600 },
      },
      grid: { left: 48, right: 20, top: 44, bottom: 28 },
      xAxis: {
        type: 'category',
        data: scrapLabels,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        axisLabel: { color: '#475569', fontWeight: 700, fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        name: '%',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.25)' } },
      },
      animationDuration: 900,
      animationEasing: 'cubicOut',
      series: [
        {
          name: 'ロス率（不良＋廃棄）',
          type: 'line',
          smooth: true,
          data: qualityLossRates,
          symbol: 'diamond',
          symbolSize: 11,
          lineStyle: {
            width: 3,
            type: 'dashed',
            color: '#8b5cf6',
            shadowColor: 'rgba(139, 92, 246, 0.3)',
            shadowBlur: 8,
            shadowOffsetY: 4,
          },
          itemStyle: { color: '#8b5cf6', borderColor: '#fff', borderWidth: 2 },
          label: { ...pctLabel, position: 'top', distance: 10, color: '#6d28d9' },
          labelLayout: { hideOverlap: true },
          emphasis: { focus: 'series', scale: 1.4 },
        },
        {
          name: '不良率',
          type: 'line',
          smooth: true,
          data: defectRates,
          symbol: 'circle',
          symbolSize: 9,
          lineStyle: {
            width: 3,
            color: '#f59e0b',
            shadowColor: 'rgba(245, 158, 11, 0.35)',
            shadowBlur: 8,
            shadowOffsetY: 4,
          },
          itemStyle: { color: '#f59e0b', borderColor: '#fff', borderWidth: 2 },
          label: { ...pctLabel, position: 'top', distance: 8, color: '#b45309' },
          labelLayout: { hideOverlap: true },
          emphasis: { focus: 'series', scale: 1.4 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(245,158,11,0.18)' },
              { offset: 1, color: 'rgba(245,158,11,0.02)' },
            ]),
          },
        },
        {
          name: '廃棄率',
          type: 'line',
          smooth: true,
          data: scrapRates,
          symbol: 'circle',
          symbolSize: 9,
          lineStyle: {
            width: 3,
            color: '#e11d48',
            shadowColor: 'rgba(225, 29, 72, 0.35)',
            shadowBlur: 8,
            shadowOffsetY: 4,
          },
          itemStyle: { color: '#e11d48', borderColor: '#fff', borderWidth: 2 },
          label: { ...pctLabel, position: 'bottom', distance: 8, color: '#be123c' },
          emphasis: { focus: 'series', scale: 1.4 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(225,29,72,0.2)' },
              { offset: 1, color: 'rgba(225,29,72,0.02)' },
            ]),
          },
          markLine: {
            silent: true,
            data: [{ yAxis: 2, name: '目安2%' }],
            lineStyle: { type: 'dashed', color: '#f59e0b' },
            label: { formatter: '目安 2%', color: '#b45309', fontWeight: 700 },
          },
        },
      ],
    })
  }

  if (scrapQtyChartRef.value) {
    if (!scrapQtyChart) scrapQtyChart = echarts.init(scrapQtyChartRef.value)
    const lossTotals = scrapEditRows.value.map(
      (r) => Number(r.edit_defect || 0) + Number(r.edit_scrap || 0),
    )
    scrapQtyChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(249, 115, 22, 0.06)' } },
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: 'rgba(253, 186, 116, 0.6)',
        borderWidth: 1,
        padding: [8, 12],
        textStyle: { color: '#0f172a', fontSize: 12 },
        extraCssText: 'box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14); border-radius: 10px;',
        valueFormatter: (v: unknown) => `${Number(v ?? 0).toLocaleString()} 本`,
      },
      legend: {
        data: ['不良本数', '廃棄本数'],
        top: 0,
        itemWidth: 14,
        itemHeight: 9,
        icon: 'roundRect',
        textStyle: { color: '#475569', fontWeight: 600 },
      },
      grid: { left: 56, right: 20, top: 48, bottom: 30 },
      xAxis: {
        type: 'category',
        data: scrapLabels,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        axisLabel: { color: '#475569', fontWeight: 700, fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        name: '本',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: {
          color: '#94a3b8',
          formatter: (v: number) => (v >= 10000 ? `${(v / 10000).toLocaleString()}万` : v.toLocaleString()),
        },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.25)' } },
      },
      animationDuration: 900,
      animationEasing: 'elasticOut',
      series: [
        {
          name: '不良本数',
          type: 'bar',
          stack: 'quality-loss',
          barMaxWidth: 64,
          data: defectQtys,
          itemStyle: {
            borderRadius: [0, 0, 4, 4],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#fbbf24' },
              { offset: 1, color: '#d97706' },
            ]),
            shadowColor: 'rgba(217, 119, 6, 0.28)',
            shadowBlur: 8,
            shadowOffsetY: 3,
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 14, shadowColor: 'rgba(217, 119, 6, 0.45)' },
          },
          label: {
            show: true,
            position: 'inside',
            color: '#fff',
            fontSize: 11,
            fontWeight: 700,
            textShadowColor: 'rgba(15, 23, 42, 0.35)',
            textShadowBlur: 4,
            formatter: ({ value }: { value: number }) =>
              Number(value) > 0 ? Number(value).toLocaleString() : '',
          },
          animationDelay: (idx: number) => idx * 120,
        },
        {
          name: '廃棄本数',
          type: 'bar',
          stack: 'quality-loss',
          barMaxWidth: 64,
          data: scrapQtys,
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#fb7185' },
              { offset: 1, color: '#e11d48' },
            ]),
            shadowColor: 'rgba(225, 29, 72, 0.28)',
            shadowBlur: 8,
            shadowOffsetY: 3,
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 14, shadowColor: 'rgba(225, 29, 72, 0.45)' },
          },
          label: {
            show: true,
            position: 'inside',
            color: '#fff',
            fontSize: 11,
            fontWeight: 700,
            textShadowColor: 'rgba(15, 23, 42, 0.35)',
            textShadowBlur: 4,
            formatter: ({ value }: { value: number }) =>
              Number(value) > 0 ? Number(value).toLocaleString() : '',
          },
          animationDelay: (idx: number) => idx * 120 + 60,
        },
        {
          // 合計ラベル用の透明系列（積み上げ最上部に合計値を表示）
          name: '合計',
          type: 'bar',
          stack: 'quality-loss',
          barMaxWidth: 64,
          data: lossTotals.map(() => 0),
          itemStyle: { color: 'transparent' },
          tooltip: { show: false },
          silent: true,
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: '#9f1239',
            fontSize: 12,
            fontWeight: 800,
            formatter: ({ dataIndex }: { dataIndex: number }) =>
              `計 ${Number(lossTotals[dataIndex] ?? 0).toLocaleString()}`,
          },
        },
      ],
    })
  }

  // 差異：工程を系列、月をカテゴリ
  const diffRows = payload.value.diff_by_month_process || []
  const monthLabels = [...new Set(diffRows.map((r) => r.month_label))]
  const processes = [...new Set(diffRows.map((r) => r.process_name || r.process_cd))]
  // 工程別カラーパレット（上：明るい色 → 下：濃い色、ラベルは濃色）
  const diffPalette = [
    { top: '#60a5fa', bottom: '#2563eb', label: '#1d4ed8' },
    { top: '#a78bfa', bottom: '#7c3aed', label: '#6d28d9' },
    { top: '#fbbf24', bottom: '#d97706', label: '#b45309' },
    { top: '#2dd4bf', bottom: '#0d9488', label: '#0f766e' },
    { top: '#818cf8', bottom: '#4f46e5', label: '#4338ca' },
    { top: '#f472b6', bottom: '#db2777', label: '#be185d' },
    { top: '#94a3b8', bottom: '#475569', label: '#334155' },
  ]
  const diffSeries = processes.slice(0, 10).map((pname, si) => {
    const c = diffPalette[si % diffPalette.length]
    return {
      name: pname,
      type: 'bar' as const,
      barMaxWidth: 36,
      barGap: '18%',
      data: monthLabels.map((ml) => {
        const hit = diffRows.find(
          (r) => r.month_label === ml && (r.process_name || r.process_cd) === pname,
        )
        const v = hit ? Number(hit.diff_qty || 0) : 0
        return {
          value: v,
          // マイナス差異はラベルを下側に出す
          label: { position: v < 0 ? ('bottom' as const) : ('top' as const) },
          itemStyle: {
            borderRadius: v < 0 ? [0, 0, 6, 6] : [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, v < 0 ? 1 : 0, 0, v < 0 ? 0 : 1, [
              { offset: 0, color: c.top },
              { offset: 1, color: c.bottom },
            ]),
          },
        }
      }),
      itemStyle: {
        shadowColor: 'rgba(15, 23, 42, 0.2)',
        shadowBlur: 6,
        shadowOffsetY: 2,
      },
      emphasis: {
        focus: 'series' as const,
        itemStyle: { shadowBlur: 12, shadowColor: 'rgba(15, 23, 42, 0.35)' },
      },
      label: {
        show: true,
        fontSize: 10,
        fontWeight: 700,
        distance: 4,
        color: c.label,
        formatter: ({ value }: { value: number }) =>
          Number(value) === 0 ? '' : Number(value).toLocaleString(),
      },
      labelLayout: { hideOverlap: true },
      animationDelay: (idx: number) => idx * 100 + si * 60,
    }
  })

  if (diffChartRef.value) {
    if (!diffChart) diffChart = echarts.init(diffChartRef.value)
    diffChart.setOption({
      color: diffPalette.map((c) => c.bottom),
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.06)' } },
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: 'rgba(165, 180, 252, 0.6)',
        borderWidth: 1,
        padding: [8, 12],
        textStyle: { color: '#0f172a', fontSize: 12 },
        extraCssText: 'box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14); border-radius: 10px;',
        valueFormatter: (v: unknown) => `${Number(v ?? 0).toLocaleString()} 本`,
      },
      legend: {
        type: 'scroll',
        top: 0,
        itemWidth: 14,
        itemHeight: 9,
        icon: 'roundRect',
        textStyle: { color: '#475569', fontWeight: 600 },
      },
      grid: { left: 56, right: 20, top: 48, bottom: 30 },
      xAxis: {
        type: 'category',
        data: monthLabels,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        axisLabel: { color: '#475569', fontWeight: 700, fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        name: '差異本数',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8', formatter: (v: number) => v.toLocaleString() },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.25)' } },
      },
      animationDuration: 900,
      animationEasing: 'elasticOut',
      series: diffSeries,
    })
  }
}

async function onGenerate() {
  loading.value = true
  try {
    const data = await inventoryReportApi.generate(fiscalYear.value, quarter.value)
    payload.value = data
    savedId.value = null
    scrapOverrides.value = {}
    executiveSummary.value = ''
    actionItems.value = ''
    notes.value = ''
    syncScrapEditRows()
    await nextTick()
    renderCharts()
    ElMessage.success(`${data.label} を生成しました`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '生成に失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function onSave(status: 'draft' | 'final') {
  if (!payload.value) return
  if (status === 'final') {
    try {
      await ElMessageBox.confirm('確定保存しますか？（報告用として固定されます）', '確定保存', {
        type: 'warning',
        confirmButtonText: '確定',
        cancelButtonText: 'キャンセル',
      })
    } catch {
      return
    }
  }
  loading.value = true
  try {
    const saved = await inventoryReportApi.save({
      fiscal_year: fiscalYear.value,
      quarter: quarter.value,
      status,
      payload: payload.value,
      scrap_overrides: scrapOverrides.value,
      executive_summary: executiveSummary.value || undefined,
      action_items: actionItems.value || undefined,
      notes: notes.value || undefined,
    })
    savedId.value = saved.id
    ElMessage.success(status === 'final' ? '確定保存しました' : '下書き保存しました')
    await loadSavedList()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存に失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function onLoadSaved(id: number) {
  loading.value = true
  try {
    const detail = await inventoryReportApi.getSaved(id)
    fiscalYear.value = detail.fiscal_year
    reportType.value = reportTypeForCode(detail.quarter)
    quarter.value = detail.quarter
    payload.value = detail.payload
    scrapOverrides.value = detail.scrap_overrides || {}
    executiveSummary.value = detail.executive_summary || ''
    actionItems.value = detail.action_items || ''
    notes.value = detail.notes || ''
    savedId.value = detail.id
    syncScrapEditRows()
    await nextTick()
    renderCharts()
    ElMessage.success('保存済みレポートを読み込みました')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '読込に失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function loadSavedList() {
  try {
    const res = await inventoryReportApi.listSaved(fiscalYear.value)
    savedList.value = res.list || []
  } catch {
    savedList.value = []
  }
}

/** 集計データから報告メモ（サマリ・改善アクション）を自動生成する */
function buildAutoAnalysis(): { summary: string; actions: string } | null {
  const p = payload.value
  if (!p) return null

  const summaryLines: string[] = []

  // 在庫トレンド
  const inv = p.inventory_series || []
  const firstInv = inv[0]
  const lastInv = inv[inv.length - 1]
  if (lastInv) {
    let s =
      `期末在庫は${lastInv.month_label}時点で合計 ${fmtInt(lastInv.total_qty)} 本` +
      `（仕掛品 ${fmtInt(lastInv.wip_qty)} 本・製品 ${fmtInt(lastInv.product_qty)} 本）。`
    if (firstInv && firstInv !== lastInv) {
      const d = Number(lastInv.total_qty) - Number(firstInv.total_qty)
      s += `対象期間内では${firstInv.month_label}比 ${fmtSigned(d)} 本${d > 0 ? '増加' : d < 0 ? '減少' : 'で横ばい'}。`
    }
    const prev = p.previous_period ?? p.previous_quarter
    if (prev) {
      s += `前期間（${prev.label}）比では ${fmtSigned(prev.delta_total_qty)} 本。`
    }
    summaryLines.push(s)
  }

  // 品質（不良・廃棄）
  const rows = scrapEditRows.value
  if (rows.length) {
    const scrapVals = rows.filter((r) => r.edit_rate != null)
    const scrapPeak = scrapVals.length
      ? scrapVals.reduce((a, b) => (Number(b.edit_rate) > Number(a.edit_rate) ? b : a))
      : null
    const totalDefect = rows.reduce((sum, r) => sum + Number(r.edit_defect || 0), 0)
    const totalScrap = rows.reduce((sum, r) => sum + Number(r.edit_scrap || 0), 0)
    const defectSeries = (p.scrap_series || []).filter((s) => s.defect_rate_percent != null)
    const defectPeak = defectSeries.length
      ? defectSeries.reduce((a, b) =>
          Number(b.defect_rate_percent) > Number(a.defect_rate_percent) ? b : a
        )
      : null
    let s = `品質面では不良本数 ${fmtInt(totalDefect)} 本・廃棄本数 ${fmtInt(totalScrap)} 本。`
    if (defectPeak) {
      s += `不良率のピークは${defectPeak.month_label}の ${fmtPct(defectPeak.defect_rate_percent)}。`
    }
    if (scrapPeak) {
      s += `廃棄率のピークは${scrapPeak.month_label}の ${fmtPct(scrapPeak.edit_rate)}${
        Number(scrapPeak.edit_rate) >= 2 ? '（目安2%超過）' : ''
      }。`
    }
    summaryLines.push(s)
  }

  // 棚卸差異
  const diffRows = p.diff_by_month_process || []
  if (diffRows.length || p.kpi) {
    let s = `棚卸は平均一致率 ${fmtPct(p.kpi.avg_match_rate)}・差異絶対値合計 ${fmtInt(p.kpi.total_diff_abs)} 本。`
    if (diffRows.length) {
      const byProc = new Map<string, number>()
      for (const r of diffRows) {
        const key = String(r.process_name || r.process_cd || '')
        byProc.set(key, (byProc.get(key) || 0) + Math.abs(Number(r.diff_qty) || 0))
      }
      const worst = [...byProc.entries()].sort((a, b) => b[1] - a[1])[0]
      if (worst && worst[1] > 0) {
        s += `差異が最も大きいのは${worst[0]}工程（絶対値合計 ${fmtInt(worst[1])} 本）。`
      }
    }
    summaryLines.push(s)
  }

  // 大量廃棄・保留品
  const bulk = p.bulk_disposal
  if (bulk?.count) {
    summaryLines.push(
      `大量廃棄・保留品は ${fmtInt(bulk.count)} 件・合計 ${fmtInt(bulk.total_quantity)} 本` +
        `（未処理 ${fmtInt(bulk.pending_count)} 件）。`
    )
  }

  // 改善アクション（データ条件に応じて提案）
  const actions: string[] = []
  const scrapOver2 = rows.filter((r) => Number(r.edit_rate || 0) >= 2).map((r) => r.month_label)
  if (scrapOver2.length) {
    actions.push(`廃棄率が目安2%を超過（${scrapOver2.join('・')}）→ 工程別の廃棄要因を分析し削減策を立案`)
  }
  if (Number(p.kpi.avg_match_rate) < 95) {
    actions.push('棚卸一致率が95%未満 → 差異上位品目を対象に棚卸精度・記帳タイミングを調査')
  }
  if (bulk?.pending_count) {
    actions.push(`大量廃棄・保留品の未処理 ${fmtInt(bulk.pending_count)} 件 → 処理期限と担当を設定し完了させる`)
  }
  const prev = p.previous_period ?? p.previous_quarter
  if (prev && Number(prev.delta_total_qty) > 0) {
    actions.push(
      `期末在庫が前期間比 ${fmtSigned(prev.delta_total_qty)} 本増加 → 滞留在庫の確認と生産計画の調整を検討`
    )
  }
  if (!actions.length) {
    actions.push('主要指標は目安範囲内 → 現行の管理水準を維持し継続モニタリング')
  }

  return {
    summary: summaryLines.map((s, i) => `${i + 1}. ${s}`).join('\n'),
    actions: actions.map((s, i) => `${i + 1}. ${s}`).join('\n'),
  }
}

async function onAutoAnalysis() {
  const result = buildAutoAnalysis()
  if (!result) return
  if (executiveSummary.value.trim() || actionItems.value.trim()) {
    try {
      await ElMessageBox.confirm(
        '既存の報告メモ（サマリ・改善アクション）を自動分析の内容で上書きします。よろしいですか？',
        '自動分析を挿入',
        { confirmButtonText: '上書きする', cancelButtonText: 'キャンセル', type: 'warning' }
      )
    } catch {
      return
    }
  }
  executiveSummary.value = result.summary
  actionItems.value = result.actions
  ElMessage.success('自動分析を報告メモに挿入しました。内容を確認・編集してください')
}

/** 生成レポートと同じ内容を、報告書レイアウトの専用ドキュメントとして印刷する */
function onPrint() {
  const p = payload.value
  if (!p) return

  const esc = (v: unknown) =>
    String(v ?? '').replace(
      /[&<>"']/g,
      (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string
    )
  const chartImg = (chart: ECharts | null, title: string) =>
    chart
      ? `<figure class="chart"><figcaption>${esc(title)}</figcaption><img src="${chart.getDataURL(
          { type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' }
        )}" /></figure>`
      : ''

  const kpiRows = monthlyKpiRows.value
    .map(
      (m) => `<tr>
        <td class="c">${esc(m.month_label)}</td>
        <td class="r">${fmtInt(m.closing_wip_qty)}</td>
        <td class="r">${fmtInt(m.closing_product_qty)}</td>
        <td class="r">${fmtInt(m.closing_total_qty)}</td>
        <td class="r">${fmtPct(m.defect_rate_percent)}</td>
        <td class="r">${fmtPct(m.scrap_rate_percent)}</td>
        <td class="r">${fmtInt(m.defect_qty)}</td>
        <td class="r">${fmtInt(m.scrap_qty)}</td>
        <td class="r">${fmtPct(m.match_rate)}</td>
        <td class="r">${fmtInt(m.diff_abs)}</td>
      </tr>`
    )
    .join('')

  const highlightItems = (p.highlights || [])
    .map((h) => `<li><strong>${esc(h.title)}：</strong>${esc(h.text)}</li>`)
    .join('')

  const scrapRows = scrapEditRows.value
    .map(
      (r) => `<tr>
        <td class="c">${esc(r.month_label)}</td>
        <td class="r">${fmtPct(r.calc_rate)}</td>
        <td class="r">${fmtPct(r.edit_rate)}</td>
        <td class="r">${fmtInt(r.calc_defect)}</td>
        <td class="r">${fmtInt(r.edit_defect)}</td>
        <td class="r">${fmtInt(r.calc_scrap)}</td>
        <td class="r">${fmtInt(r.edit_scrap)}</td>
        <td>${esc(r.note)}</td>
      </tr>`
    )
    .join('')

  const diffRows = (p.diff_by_month_process || [])
    .map(
      (r) => `<tr>
        <td class="c">${esc(r.month_label)}</td>
        <td>${esc(r.process_name)}</td>
        <td class="r">${fmtInt(r.theoretical_qty)}</td>
        <td class="r">${fmtInt(r.stocktake_qty)}</td>
        <td class="r ${Number(r.diff_qty) > 0 ? 'up' : Number(r.diff_qty) < 0 ? 'down' : ''}">${fmtSigned(r.diff_qty)}</td>
        <td class="r">${r.diff_rate == null ? '—' : fmtPct(r.diff_rate)}</td>
        <td class="r">${fmtPct(r.match_rate)}</td>
      </tr>`
    )
    .join('')

  const topRows = (p.top_mismatch || [])
    .map(
      (r, i) => `<tr>
        <td class="c">${i + 1}</td>
        <td class="c">${esc(r.month_label)}</td>
        <td>${esc(r.product_cd)}</td>
        <td>${esc(r.product_name)}</td>
        <td>${esc(r.process_name)}</td>
        <td class="r">${fmtInt(Number(r.theoretical_qty))}</td>
        <td class="r">${fmtInt(Number(r.stocktake_qty))}</td>
        <td class="r ${Number(r.diff_qty) > 0 ? 'up' : Number(r.diff_qty) < 0 ? 'down' : ''}">${fmtSigned(Number(r.diff_qty))}</td>
      </tr>`
    )
    .join('')

  const bulkItems = p.bulk_disposal?.items || []
  const bulkRows = bulkItems
    .map(
      (r) => `<tr>
        <td class="c">${esc(r.occurred_date || '—')}</td>
        <td class="c">${esc(r.report_category || '—')}</td>
        <td>${esc(r.process_name)}</td>
        <td>${esc(r.product_name)}</td>
        <td class="r">${fmtInt(Number(r.quantity))}</td>
        <td class="c">${esc(r.handling_status || '—')}</td>
      </tr>`
    )
    .join('')

  const prev = p.previous_period ?? p.previous_quarter
  const prevBlock = prev
    ? `<section>
        <h2>前期間比（期末在庫）</h2>
        <p class="lead">${esc(prev.label)} 比 ${fmtSigned(prev.delta_total_qty)} 本
        （仕掛 ${fmtSigned(prev.delta_wip_qty)} / 製品 ${fmtSigned(prev.delta_product_qty)}）</p>
      </section>`
    : ''

  const notesBlock =
    executiveSummary.value || actionItems.value || notes.value
      ? `<section>
          <h2>報告メモ</h2>
          ${executiveSummary.value ? `<h3>エグゼクティブサマリ</h3><p class="memo">${esc(executiveSummary.value)}</p>` : ''}
          ${actionItems.value ? `<h3>改善アクション</h3><p class="memo">${esc(actionItems.value)}</p>` : ''}
          ${notes.value ? `<h3>備考</h3><p class="memo">${esc(notes.value)}</p>` : ''}
        </section>`
      : ''

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<title>${esc(p.label)} 在庫報告書</title>
<style>
  @page { size: A4 portrait; margin: 14mm 12mm; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Yu Gothic', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
    font-size: 11px;
    color: #1e293b;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  header.doc {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 3px solid #1d4ed8;
    padding-bottom: 8px;
    margin-bottom: 14px;
  }
  header.doc h1 { margin: 0; font-size: 20px; letter-spacing: 0.04em; }
  header.doc .sub { color: #64748b; font-size: 10.5px; text-align: right; line-height: 1.7; }
  section { margin-bottom: 16px; break-inside: avoid; }
  h2 {
    margin: 0 0 6px;
    padding: 3px 8px;
    font-size: 12.5px;
    color: #1e3a8a;
    background: #eff6ff;
    border-left: 4px solid #2563eb;
  }
  h3 { margin: 8px 0 3px; font-size: 11px; color: #334155; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #cbd5e1; padding: 3px 6px; }
  th { background: #f1f5f9; font-weight: 700; color: #334155; }
  td.r { text-align: right; font-variant-numeric: tabular-nums; }
  td.c { text-align: center; }
  td.up { color: #b91c1c; font-weight: 700; }
  td.down { color: #1d4ed8; font-weight: 700; }
  ul.hl { margin: 0; padding-left: 18px; }
  ul.hl li { margin: 2px 0; }
  .lead { margin: 2px 0; }
  .memo { margin: 2px 0 6px; white-space: pre-wrap; }
  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  figure.chart { margin: 0; border: 1px solid #e2e8f0; padding: 4px; break-inside: avoid; }
  figure.chart figcaption { font-size: 10.5px; font-weight: 700; color: #334155; padding: 2px 2px 4px; }
  figure.chart img { width: 100%; height: auto; display: block; }
  footer.doc {
    margin-top: 18px;
    padding-top: 6px;
    border-top: 1px solid #cbd5e1;
    color: #94a3b8;
    font-size: 9.5px;
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>
  <header class="doc">
    <h1>${esc(p.label)}　在庫報告書</h1>
    <div class="sub">
      集計日時：${esc(p.generated_at || '—')}<br />
      印刷日時：${esc(new Date().toLocaleString('ja-JP'))}
    </div>
  </header>

  <section>
    <h2>月別サマリ（KPI）</h2>
    <table>
      <thead><tr>
        <th>月</th><th>期末仕掛品</th><th>期末製品</th><th>期末合計</th>
        <th>不良率</th><th>廃棄率</th><th>不良本数</th><th>廃棄本数</th>
        <th>棚卸一致率</th><th>差異絶対値</th>
      </tr></thead>
      <tbody>${kpiRows}</tbody>
    </table>
  </section>

  ${highlightItems ? `<section><h2>ハイライト</h2><ul class="hl">${highlightItems}</ul></section>` : ''}
  ${prevBlock}

  <section>
    <h2>グラフ</h2>
    <div class="charts">
      ${chartImg(invChart, '月末在庫（仕掛品・製品）')}
      ${chartImg(scrapRateChart, '不良率・廃棄率推移')}
      ${chartImg(scrapQtyChart, '不良・廃棄本数（月別）')}
      ${chartImg(diffChart, '棚卸差異（月別×工程）')}
    </div>
  </section>

  <section>
    <h2>廃棄率・不良本数・廃棄本数（報告用）</h2>
    <table>
      <thead><tr>
        <th rowspan="2">月</th>
        <th colspan="2">廃棄率(%)</th><th colspan="2">不良本数</th><th colspan="2">廃棄本数</th>
        <th rowspan="2">コメント</th>
      </tr><tr>
        <th>計算値</th><th>報告用</th><th>計算値</th><th>報告用</th><th>計算値</th><th>報告用</th>
      </tr></thead>
      <tbody>${scrapRows}</tbody>
    </table>
  </section>

  <section>
    <h2>理論在庫 vs 棚卸差異（月別・工程別）</h2>
    <table>
      <thead><tr>
        <th>月</th><th>工程</th><th>理論在庫</th><th>棚卸在庫</th><th>差異</th><th>差異率%</th><th>一致率%</th>
      </tr></thead>
      <tbody>${diffRows}</tbody>
    </table>
  </section>

  ${topRows ? `<section>
    <h2>差異が大きい品目（上位）</h2>
    <table>
      <thead><tr>
        <th>#</th><th>月</th><th>製品CD</th><th>製品名</th><th>工程</th><th>理論</th><th>棚卸</th><th>差異</th>
      </tr></thead>
      <tbody>${topRows}</tbody>
    </table>
  </section>` : ''}

  ${bulkRows ? `<section>
    <h2>大量廃棄・保留品（対象期間）</h2>
    <table>
      <thead><tr>
        <th>発生日</th><th>区分</th><th>工程</th><th>製品</th><th>本数</th><th>状態</th>
      </tr></thead>
      <tbody>${bulkRows}</tbody>
    </table>
  </section>` : ''}

  ${notesBlock}

  <footer class="doc">
    <span>Smart-EMAPs 在庫報告管理</span>
    <span>${esc(p.label)} 在庫報告書</span>
  </footer>
</body>
</html>`

  const iframe = document.createElement('iframe')
  iframe.style.position = 'fixed'
  iframe.style.right = '0'
  iframe.style.bottom = '0'
  iframe.style.width = '0'
  iframe.style.height = '0'
  iframe.style.border = '0'
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  if (!doc) {
    document.body.removeChild(iframe)
    return
  }
  doc.open()
  doc.write(html)
  doc.close()
  const win = iframe.contentWindow
  // 画像（グラフPNG）の読み込みを待ってから印刷する
  const imgs = Array.from(doc.images)
  void Promise.all(
    imgs.map(
      (img) =>
        new Promise<void>((resolve) => {
          if (img.complete) return resolve()
          img.onload = () => resolve()
          img.onerror = () => resolve()
        })
    )
  ).then(() => {
    setTimeout(() => {
      win?.focus()
      win?.print()
      setTimeout(() => {
        if (iframe.parentNode) iframe.parentNode.removeChild(iframe)
      }, 1000)
    }, 100)
  })
}

function onResize() {
  invChart?.resize()
  scrapRateChart?.resize()
  scrapQtyChart?.resize()
  diffChart?.resize()
}

watch(reportType, (type) => {
  const valid =
    (type === 'quarter' && quarter.value >= 1 && quarter.value <= 4) ||
    (type === 'half' && quarter.value >= 5 && quarter.value <= 6) ||
    (type === 'annual' && quarter.value === 7)
  if (!valid) {
    quarter.value = type === 'quarter' ? 1 : type === 'half' ? 5 : 7
  }
})

watch([fiscalYear, quarter], () => {
  loadSavedList()
})

onMounted(async () => {
  try {
    const opts = await inventoryReportApi.getQuarterOptions()
    fiscalYear.value = opts.current_fiscal_year
    quarter.value = opts.current_quarter
  } catch {
    const m = new Date().getMonth() + 1
    fiscalYear.value = m >= 4 ? new Date().getFullYear() : new Date().getFullYear() - 1
    quarter.value = m <= 3 ? 4 : m <= 6 ? 1 : m <= 9 ? 2 : 3
  }
  await loadSavedList()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})
</script>

<style scoped lang="scss">
.rpt-page {
  --rpt-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset, 0 10px 28px rgba(15, 23, 42, 0.08),
    0 2px 8px rgba(15, 23, 42, 0.04);
  --rpt-shadow-hover: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 16px 36px rgba(15, 23, 42, 0.12),
    0 4px 12px rgba(15, 23, 42, 0.06);
  position: relative;
  min-height: 100%;
  padding: 12px 14px 24px;
  box-sizing: border-box;
  overflow: hidden;
}

.rpt-ambient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(165deg, #eef4ff 0%, #f8fafc 42%, #fff7ed 100%);
}

.rpt-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(88px);
  opacity: 0.42;
  animation: rpt-orb-float 18s ease-in-out infinite;
}
.rpt-orb--a {
  width: 420px;
  height: 420px;
  top: -140px;
  right: 4%;
  background: radial-gradient(circle, #93c5fd 0%, transparent 70%);
}
.rpt-orb--b {
  width: 340px;
  height: 340px;
  bottom: 4%;
  left: -90px;
  background: radial-gradient(circle, #fdba74 0%, transparent 70%);
  animation-delay: -6s;
}
.rpt-orb--c {
  width: 280px;
  height: 280px;
  top: 42%;
  right: 22%;
  background: radial-gradient(circle, #99f6e4 0%, transparent 70%);
  animation-delay: -12s;
}

@keyframes rpt-orb-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(12px, -14px) scale(1.04);
  }
}

.rpt-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.animate-in {
  animation: rpt-fade-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes rpt-fade-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.rpt-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.92) 100%);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: var(--rpt-shadow);
}

.rpt-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 200px;
}
.rpt-brand__icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #0d9488 0%, #2563eb 100%);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.35) inset, 0 6px 16px rgba(37, 99, 235, 0.35);
}
.rpt-brand__title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
  line-height: 1.2;
}
.rpt-brand__meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
}

.rpt-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.rpt-fy {
  width: 120px;
}
.rpt-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-left: auto;
}

/* ── アクションボタン（色別・立体） ── */
:deep(.rpt-btn) {
  --btn-c1: #64748b;
  --btn-c2: #475569;
  position: relative;
  border: none !important;
  border-radius: 9px !important;
  padding: 7px 13px !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em;
  color: #fff !important;
  background: linear-gradient(145deg, var(--btn-c1), var(--btn-c2)) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 -1px 0 rgba(0, 0, 0, 0.12) inset,
    0 5px 12px color-mix(in srgb, var(--btn-c2) 42%, transparent),
    0 2px 4px rgba(15, 23, 42, 0.08);
  transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;
}
:deep(.rpt-btn .el-icon) {
  margin-right: 4px;
  font-size: 14px;
}
:deep(.rpt-btn:hover:not(.is-disabled)) {
  transform: translateY(-2px);
  filter: brightness(1.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.4) inset,
    0 -1px 0 rgba(0, 0, 0, 0.12) inset,
    0 9px 20px color-mix(in srgb, var(--btn-c2) 52%, transparent),
    0 3px 6px rgba(15, 23, 42, 0.1);
}
:deep(.rpt-btn:active:not(.is-disabled)) {
  transform: translateY(0);
  filter: brightness(0.97);
  box-shadow:
    0 2px 6px color-mix(in srgb, var(--btn-c2) 35%, transparent),
    0 1px 2px rgba(15, 23, 42, 0.1);
}
:deep(.rpt-btn.is-disabled) {
  opacity: 0.45;
  filter: saturate(0.4);
  box-shadow: none;
}
:deep(.rpt-btn--slate) {
  --btn-c1: #94a3b8;
  --btn-c2: #64748b;
}
:deep(.rpt-btn--emerald) {
  --btn-c1: #10b981;
  --btn-c2: #047857;
}
:deep(.rpt-btn--amber) {
  --btn-c1: #f59e0b;
  --btn-c2: #d97706;
}
:deep(.rpt-btn--blue) {
  --btn-c1: #3b82f6;
  --btn-c2: #1d4ed8;
}
:deep(.rpt-btn--violet) {
  --btn-c1: #a78bfa;
  --btn-c2: #7c3aed;
}
:deep(.rpt-btn--edit) {
  --btn-c1: #fb7185;
  --btn-c2: #e11d48;
}

/* ── 手動修正：起動カード ── */
.rpt-edit-launcher {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 14px;
  background: linear-gradient(120deg, #fff1f2, #fff 45%, #fff7ed);
  border: 1px solid rgba(225, 29, 72, 0.16);
  box-shadow: 0 4px 14px rgba(225, 29, 72, 0.07), 0 1px 3px rgba(15, 23, 42, 0.05);
}
.rpt-edit-launcher__info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.rpt-edit-launcher__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: 11px;
  color: #fff;
  font-size: 18px;
  background: linear-gradient(145deg, #fb7185, #e11d48);
  box-shadow: 0 5px 12px rgba(225, 29, 72, 0.35), 0 1px 0 rgba(255, 255, 255, 0.35) inset;
}
.rpt-edit-launcher__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.rpt-edit-launcher__text strong {
  font-size: 13.5px;
  font-weight: 800;
  color: #0f172a;
}
.rpt-edit-launcher__text small {
  font-size: 11.5px;
  color: #94a3b8;
}
.rpt-edit-launcher__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: none;
}

/* ── 手動修正：ダイアログ ── */
:deep(.rpt-edit-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
}
:deep(.rpt-edit-dialog .el-dialog__header) {
  margin: 0;
  padding: 14px 20px;
  background: linear-gradient(120deg, #fff1f2, #ffe4e6 55%, #fff7ed);
  border-bottom: 1px solid rgba(225, 29, 72, 0.14);
}
:deep(.rpt-edit-dialog .el-dialog__headerbtn) {
  top: 16px;
}
:deep(.rpt-edit-dialog .el-dialog__body) {
  padding: 16px 20px 4px;
}
:deep(.rpt-edit-dialog .el-dialog__footer) {
  padding: 10px 20px 16px;
}
.rpt-edit-dialog__head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.rpt-edit-dialog__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: none;
  border-radius: 10px;
  color: #fff;
  font-size: 17px;
  background: linear-gradient(145deg, #fb7185, #e11d48);
  box-shadow: 0 5px 12px rgba(225, 29, 72, 0.35), 0 1px 0 rgba(255, 255, 255, 0.35) inset;
}
.rpt-edit-dialog__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.rpt-edit-dialog__titles strong {
  font-size: 14px;
  font-weight: 800;
  color: #881337;
}
.rpt-edit-dialog__titles small {
  font-size: 11.5px;
  color: #b45309;
  opacity: 0.85;
}
.rpt-edit-dialog__hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0 6px;
  padding: 8px 12px;
  border-radius: 9px;
  font-size: 11.5px;
  color: #92400e;
  background: rgba(251, 191, 36, 0.12);
  border: 1px dashed rgba(217, 119, 6, 0.35);
}
.rpt-edit-dialog__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ── 手動修正：テーブル ── */
:deep(.rpt-edit-table .el-table__header th) {
  font-weight: 800;
  color: #475569;
  background: #f8fafc;
}
:deep(.rpt-edit-table th.col-edit),
:deep(.rpt-edit-table td.col-edit) {
  background: rgba(255, 241, 242, 0.55);
}
:deep(.rpt-edit-table th.col-calc),
:deep(.rpt-edit-table td.col-calc) {
  color: #94a3b8;
  background: rgba(248, 250, 252, 0.7);
}
.rpt-edit-table__month {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 12px;
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.12);
}
:deep(.rpt-edit-table .rpt-num.is-modified .el-input__wrapper) {
  background: #fef3c7;
  box-shadow: 0 0 0 1px #f59e0b inset;
}

/* ── 四半期スイッチ・年度セレクト ── */
:deep(.rpt-quarter .el-radio-button__inner) {
  font-weight: 700;
  border-color: rgba(148, 163, 184, 0.35);
  background: linear-gradient(180deg, #ffffff, #f1f5f9);
  color: #475569;
  transition: all 0.16s ease;
}
:deep(.rpt-quarter .el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 9px 0 0 9px;
}
:deep(.rpt-quarter .el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 9px 9px 0;
}
:deep(.rpt-quarter .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(145deg, #3b82f6, #1d4ed8);
  border-color: transparent;
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 4px 12px rgba(37, 99, 235, 0.4);
}
:deep(.rpt-fy .el-select__wrapper) {
  border-radius: 9px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow:
    0 0 0 1px rgba(148, 163, 184, 0.35) inset,
    0 2px 6px rgba(15, 23, 42, 0.05);
  font-weight: 600;
}

.rpt-saved-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}
.rpt-saved-bar__label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}
.rpt-saved-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.rpt-saved-chip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.rpt-saved-chip.is-final {
  color: #047857;
  background: linear-gradient(180deg, #ecfdf5, #d1fae5);
  border-color: rgba(16, 185, 129, 0.25);
}
.rpt-saved-chip.is-final .rpt-saved-chip__dot {
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}
.rpt-saved-chip.is-draft {
  color: #334155;
  background: linear-gradient(180deg, #f8fafc, #e2e8f0);
  border-color: rgba(100, 116, 139, 0.2);
}
.rpt-saved-chip.is-draft .rpt-saved-chip__dot {
  background: #94a3b8;
}
.rpt-saved-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.1);
}

.rpt-empty {
  margin-top: 48px;
  padding: 28px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.75);
  box-shadow: var(--rpt-shadow);
}

.rpt-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rpt-kpi {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 6px;
}
.rpt-kpi.is-half,
.rpt-kpi.is-annual {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.rpt-kpi.is-annual .rpt-kpi__months {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 10px;
}
.rpt-kpi.is-annual .rpt-kpi__month:nth-child(2) {
  border-top: 0;
  padding-top: 0;
}
@media (max-width: 1400px) {
  .rpt-kpi {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
@media (max-width: 1000px) {
  .rpt-kpi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.rpt-kpi__card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  padding: 12px 12px 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.96) 100%);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: var(--rpt-shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.rpt-kpi__card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--kpi-accent, #94a3b8);
  border-radius: 14px 0 0 14px;
}
.rpt-kpi__card::after {
  content: '';
  position: absolute;
  top: -28px;
  right: -24px;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--kpi-glow, rgba(148, 163, 184, 0.22)) 0%, transparent 70%);
  pointer-events: none;
}
.rpt-kpi__card:hover {
  transform: translateY(-2px);
  box-shadow: var(--rpt-shadow-hover);
}
.rpt-kpi__card.is-warn {
  outline: 1px solid rgba(245, 158, 11, 0.45);
}

.theme-wip {
  --kpi-accent: #3b82f6;
  --kpi-glow: rgba(59, 130, 246, 0.28);
  --kpi-strong: #1d4ed8;
}
.theme-product {
  --kpi-accent: #14b8a6;
  --kpi-glow: rgba(20, 184, 166, 0.28);
  --kpi-strong: #0f766e;
}
.theme-defect {
  --kpi-accent: #f59e0b;
  --kpi-glow: rgba(245, 158, 11, 0.28);
  --kpi-strong: #b45309;
}
.theme-scrap {
  --kpi-accent: #e11d48;
  --kpi-glow: rgba(225, 29, 72, 0.24);
  --kpi-strong: #be123c;
}
.theme-qty {
  --kpi-accent: #f97316;
  --kpi-glow: rgba(249, 115, 22, 0.26);
  --kpi-strong: #c2410c;
}
.theme-match {
  --kpi-accent: #10b981;
  --kpi-glow: rgba(16, 185, 129, 0.26);
  --kpi-strong: #047857;
}
.theme-bulk {
  --kpi-accent: #8b5cf6;
  --kpi-glow: rgba(139, 92, 246, 0.26);
  --kpi-strong: #6d28d9;
}

.rpt-kpi__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.rpt-kpi__ico {
  width: 28px;
  height: 28px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, var(--kpi-accent), color-mix(in srgb, var(--kpi-accent) 70%, #0f172a));
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.3) inset, 0 4px 10px color-mix(in srgb, var(--kpi-accent) 45%, transparent);
  font-size: 14px;
}
.rpt-kpi__label {
  font-size: 12px;
  color: #334155;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.rpt-kpi__months {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.rpt-kpi__month {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: baseline;
  gap: 2px 5px;
  padding: 5px 0;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  font-variant-numeric: tabular-nums;
}
.rpt-kpi__month:first-child {
  border-top: 0;
  padding-top: 0;
}
.rpt-kpi__month > span {
  grid-row: 1 / span 2;
  align-self: center;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}
.rpt-kpi__month > strong {
  min-width: 0;
  font-size: 15px;
  font-weight: 800;
  color: var(--kpi-strong, #0f172a);
  text-align: right;
  white-space: nowrap;
}
.rpt-kpi__month > small {
  font-size: 9px;
  line-height: 1.1;
  color: #94a3b8;
  text-align: right;
  white-space: nowrap;
}

.rpt-highlights {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.rpt-hl {
  --hl-accent: #64748b;
  --hl-soft: rgba(100, 116, 139, 0.1);
  --hl-strong: #334155;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background:
    linear-gradient(135deg, var(--hl-soft) 0%, rgba(255, 255, 255, 0) 46%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  border-radius: 13px;
  padding: 11px 13px;
  font-size: 12px;
  border: 1px solid color-mix(in srgb, var(--hl-accent) 22%, #ffffff);
  box-shadow: var(--rpt-shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.rpt-hl:hover {
  transform: translateY(-1px);
  box-shadow: var(--rpt-shadow-hover);
}
.rpt-hl::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--hl-accent) 70%, #ffffff),
    var(--hl-accent)
  );
}
.rpt-hl::after {
  content: '';
  position: absolute;
  top: -30px;
  right: -26px;
  width: 92px;
  height: 92px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    color-mix(in srgb, var(--hl-accent) 24%, transparent) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.hl-blue {
  --hl-accent: #2563eb;
  --hl-soft: rgba(59, 130, 246, 0.12);
  --hl-strong: #1d4ed8;
}
.hl-amber {
  --hl-accent: #d97706;
  --hl-soft: rgba(245, 158, 11, 0.14);
  --hl-strong: #b45309;
}
.hl-rose {
  --hl-accent: #e11d48;
  --hl-soft: rgba(225, 29, 72, 0.11);
  --hl-strong: #be123c;
}
.hl-green {
  --hl-accent: #059669;
  --hl-soft: rgba(16, 185, 129, 0.12);
  --hl-strong: #047857;
}
.hl-violet {
  --hl-accent: #7c3aed;
  --hl-soft: rgba(139, 92, 246, 0.12);
  --hl-strong: #6d28d9;
}
.hl-teal {
  --hl-accent: #0d9488;
  --hl-soft: rgba(20, 184, 166, 0.12);
  --hl-strong: #0f766e;
}
.hl-slate {
  --hl-accent: #64748b;
  --hl-soft: rgba(100, 116, 139, 0.1);
  --hl-strong: #334155;
}
.rpt-hl.is-attention {
  border-color: color-mix(in srgb, var(--hl-accent) 45%, #ffffff);
}
.rpt-hl.is-attention .rpt-hl__ico {
  animation: hl-pulse 2.4s ease-in-out infinite;
}

@keyframes hl-pulse {
  0%,
  100% {
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.3) inset,
      0 4px 10px color-mix(in srgb, var(--hl-accent) 45%, transparent);
  }
  50% {
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.3) inset,
      0 4px 16px color-mix(in srgb, var(--hl-accent) 70%, transparent);
  }
}

.rpt-hl__ico {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  margin-top: 1px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 15px;
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--hl-accent) 82%, #ffffff),
    var(--hl-accent)
  );
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 4px 10px color-mix(in srgb, var(--hl-accent) 45%, transparent);
}
.rpt-hl__body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.rpt-hl__title {
  color: var(--hl-strong);
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.01em;
}
.rpt-hl__text {
  color: #475569;
  line-height: 1.55;
  font-variant-numeric: tabular-nums;
}
.rpt-hl__text :deep(.hl-num) {
  font-style: normal;
  font-weight: 800;
  font-size: 13px;
  color: var(--hl-strong);
  padding: 0 1px;
}
.rpt-hl__text :deep(.hl-num--up) {
  color: #dc2626;
}
.rpt-hl__text :deep(.hl-num--down) {
  color: #2563eb;
}
.rpt-hl__text :deep(.hl-unit) {
  font-style: normal;
  font-size: 11px;
  color: #64748b;
  margin-right: 1px;
}

.rpt-qoq {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 20px;
  font-size: 13px;
  color: #334155;
  border-radius: 14px;
  padding: 12px 16px;
  background:
    linear-gradient(120deg, rgba(59, 130, 246, 0.1) 0%, rgba(255, 255, 255, 0) 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  border: 1px solid rgba(147, 197, 253, 0.5);
  box-shadow: var(--rpt-shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.rpt-qoq:hover {
  transform: translateY(-1px);
  box-shadow: var(--rpt-shadow-hover);
}
.rpt-qoq::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}
.rpt-qoq::after {
  content: '';
  position: absolute;
  top: -34px;
  right: -28px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.22) 0%, transparent 70%);
  pointer-events: none;
}
.rpt-qoq__lead {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.rpt-qoq__badge {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 16px;
  background: linear-gradient(145deg, #60a5fa, #2563eb);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.35) inset, 0 5px 14px rgba(37, 99, 235, 0.4);
  flex-shrink: 0;
}
.rpt-qoq__caption {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.rpt-qoq__caption strong {
  font-size: 13px;
  font-weight: 800;
  color: #1e3a8a;
  letter-spacing: 0.01em;
}
.rpt-qoq__caption small {
  font-size: 11px;
  color: #64748b;
}
.rpt-qoq__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}
.rpt-qoq__stat {
  --qoq-c: #64748b;
  --qoq-bg1: #f8fafc;
  --qoq-bg2: #eef2f7;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--qoq-bg1), var(--qoq-bg2));
  border: 1px solid color-mix(in srgb, var(--qoq-c) 28%, #ffffff);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset, 0 2px 6px rgba(15, 23, 42, 0.06);
}
.rpt-qoq__stat[data-dir='up'] {
  --qoq-c: #dc2626;
  --qoq-bg1: #fef2f2;
  --qoq-bg2: #fee2e2;
}
.rpt-qoq__stat[data-dir='down'] {
  --qoq-c: #2563eb;
  --qoq-bg1: #eff6ff;
  --qoq-bg2: #dbeafe;
}
.rpt-qoq__stat--total {
  padding: 7px 14px;
}
.rpt-qoq__stat--total .rpt-qoq__stat-value {
  font-size: 16px;
}
.rpt-qoq__stat-label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.02em;
}
.rpt-qoq__stat-value {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  font-size: 14px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--qoq-c);
  white-space: nowrap;
}
.rpt-qoq__stat-value i {
  font-style: normal;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  margin-left: 1px;
}
.rpt-qoq__arrow {
  align-self: center;
  font-size: 13px;
  color: var(--qoq-c);
}

.rpt-charts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
@media (max-width: 960px) {
  .rpt-charts,
  .rpt-highlights,
  .rpt-two-col {
    grid-template-columns: 1fr;
  }
}

.rpt-chart-card,
.rpt-block {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  border-radius: 14px;
  padding: 12px 12px 8px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: var(--rpt-shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.rpt-chart-card:hover,
.rpt-block:hover {
  transform: translateY(-1px);
  box-shadow: var(--rpt-shadow-hover);
}
.rpt-chart-card::before,
.rpt-block::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--panel-accent, #94a3b8);
}
.accent-blue {
  --panel-accent: linear-gradient(90deg, #60a5fa, #2563eb);
}
.accent-rose {
  --panel-accent: linear-gradient(90deg, #fb7185, #e11d48);
}
.accent-amber {
  --panel-accent: linear-gradient(90deg, #fbbf24, #f97316);
}
.accent-violet {
  --panel-accent: linear-gradient(90deg, #a78bfa, #7c3aed);
}
.accent-teal {
  --panel-accent: linear-gradient(90deg, #5eead4, #0d9488);
}
.accent-slate {
  --panel-accent: linear-gradient(90deg, #cbd5e1, #64748b);
}

.rpt-chart-card__title,
.rpt-block__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}
.rpt-chart-card__title {
  margin-bottom: 4px;
}
.rpt-chart-host {
  height: 260px;
  width: 100%;
}

.rpt-block {
  padding: 12px;
  margin-bottom: 0;
}
.rpt-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.rpt-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.rpt-num {
  width: 120px;
}
.num-up {
  color: #dc2626;
  font-weight: 700;
}
.num-down {
  color: #2563eb;
  font-weight: 700;
}

.rpt-notes__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.rpt-notes__full {
  grid-column: 1 / -1;
}
.rpt-notes__field {
  padding: 10px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.9);
}
.rpt-notes label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.rpt-ideas ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #475569;
  line-height: 1.75;
}
.rpt-ideas li + li {
  margin-top: 2px;
}

:deep(.rpt-table) {
  --el-table-border-color: rgba(226, 232, 240, 0.9);
  --el-table-header-bg-color: #f1f5f9;
  border-radius: 10px;
  overflow: hidden;
}
:deep(.rpt-table th.el-table__cell) {
  font-weight: 700;
  color: #334155;
}
:deep(.rpt-quarter .el-radio-button__inner) {
  font-weight: 600;
}

/* ── 理論在庫 vs 棚卸差異：月別色分けテーブル ── */
:deep(.rpt-diff-table .diff-month-0 > td.el-table__cell) {
  background: rgba(59, 130, 246, 0.06);
}
:deep(.rpt-diff-table .diff-month-1 > td.el-table__cell) {
  background: rgba(139, 92, 246, 0.06);
}
:deep(.rpt-diff-table .diff-month-2 > td.el-table__cell) {
  background: rgba(20, 184, 166, 0.06);
}
:deep(.rpt-diff-table .diff-month-first > td.el-table__cell) {
  border-top: 2px solid rgba(100, 116, 139, 0.25);
}
:deep(.rpt-diff-table .diff-month-first.diff-month-0 > td.el-table__cell) {
  border-top-color: rgba(37, 99, 235, 0.4);
}
:deep(.rpt-diff-table .diff-month-first.diff-month-1 > td.el-table__cell) {
  border-top-color: rgba(124, 58, 237, 0.4);
}
:deep(.rpt-diff-table .diff-month-first.diff-month-2 > td.el-table__cell) {
  border-top-color: rgba(13, 148, 136, 0.4);
}
.diff-month-badge {
  --dm-c1: #94a3b8;
  --dm-c2: #64748b;
  display: inline-block;
  min-width: 46px;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 12px;
  color: #fff;
  letter-spacing: 0.03em;
  background: linear-gradient(145deg, var(--dm-c1), var(--dm-c2));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 2px 6px color-mix(in srgb, var(--dm-c2) 40%, transparent);
}
.diff-month-badge--0 {
  --dm-c1: #60a5fa;
  --dm-c2: #2563eb;
}
.diff-month-badge--1 {
  --dm-c1: #a78bfa;
  --dm-c2: #7c3aed;
}
.diff-month-badge--2 {
  --dm-c1: #2dd4bf;
  --dm-c2: #0d9488;
}
.diff-proc {
  font-weight: 700;
  color: #334155;
}
.diff-proc-cd {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  background: rgba(100, 116, 139, 0.1);
  border-radius: 6px;
  padding: 1px 7px;
}
.diff-strong {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.diff-match {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.diff-match--good {
  color: #047857;
}
.diff-match--warn {
  color: #b45309;
}
.diff-match--bad {
  color: #be123c;
}
.diff-num {
  font-variant-numeric: tabular-nums;
  color: #475569;
}

/* ── 差異が大きい品目（上位）── */
:deep(.rpt-top-table .el-table__row:nth-child(-n + 3) > td.el-table__cell) {
  background: rgba(59, 130, 246, 0.045);
}
.top-rank {
  --rk-c1: #cbd5e1;
  --rk-c2: #94a3b8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, var(--rk-c1), var(--rk-c2));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 2px 6px color-mix(in srgb, var(--rk-c2) 45%, transparent);
}
.top-rank--1 {
  --rk-c1: #f87171;
  --rk-c2: #dc2626;
}
.top-rank--2 {
  --rk-c1: #fb923c;
  --rk-c2: #ea580c;
}
.top-rank--3 {
  --rk-c1: #fbbf24;
  --rk-c2: #d97706;
}

/* ── 大量廃棄・保留品（対象期間）── */
.bulk-date {
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #64748b;
}
.bulk-qty {
  color: #9f1239;
}
.bulk-chip {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 700;
  line-height: 1.6;
  white-space: nowrap;
}
.bulk-chip--rose {
  color: #be123c;
  background: rgba(225, 29, 72, 0.1);
  border: 1px solid rgba(225, 29, 72, 0.25);
}
.bulk-chip--amber {
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(217, 119, 6, 0.28);
}
.bulk-chip--slate {
  color: #475569;
  background: rgba(100, 116, 139, 0.1);
  border: 1px solid rgba(100, 116, 139, 0.22);
}
.bulk-chip--bad {
  color: #fff;
  background: linear-gradient(145deg, #fb7185, #e11d48);
  box-shadow: 0 2px 6px rgba(225, 29, 72, 0.35);
}
.bulk-chip--good {
  color: #047857;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(5, 150, 105, 0.28);
}

/* ── ヘルプ（用語説明）── */
.rpt-help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-left: 6px;
  padding: 0;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  vertical-align: middle;
  color: #fff;
  font-size: 15px;
  background: linear-gradient(145deg, #94a3b8, #64748b);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 2px 6px rgba(100, 116, 139, 0.35);
  transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;
}
.rpt-help-btn:hover {
  transform: translateY(-1px) scale(1.06);
  filter: brightness(1.08);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.4) inset,
    0 4px 10px rgba(100, 116, 139, 0.45);
}
:deep(.rpt-help-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
}
:deep(.rpt-help-dialog .el-dialog__header) {
  margin: 0;
  padding: 14px 20px;
  background: linear-gradient(120deg, #eff6ff, #e0f2fe 55%, #f0fdfa);
  border-bottom: 1px solid rgba(37, 99, 235, 0.14);
}
:deep(.rpt-help-dialog .el-dialog__headerbtn) {
  top: 16px;
}
:deep(.rpt-help-dialog .el-dialog__body) {
  padding: 16px 20px 20px;
  max-height: 72vh;
  overflow-y: auto;
}
.rpt-help-dialog__head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.rpt-help-dialog__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: none;
  border-radius: 10px;
  color: #fff;
  font-size: 18px;
  background: linear-gradient(145deg, #60a5fa, #2563eb);
  box-shadow: 0 5px 12px rgba(37, 99, 235, 0.35), 0 1px 0 rgba(255, 255, 255, 0.35) inset;
}
.rpt-help-dialog__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.rpt-help-dialog__titles strong {
  font-size: 14px;
  font-weight: 800;
  color: #1e3a8a;
}
.rpt-help-dialog__titles small {
  font-size: 11.5px;
  color: #64748b;
}
.rpt-help {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.rpt-help__group {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  padding: 12px 14px;
  background: linear-gradient(180deg, #fff, #fafcff);
}
.rpt-help__group-title {
  margin: 0 0 8px;
  padding-left: 9px;
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  border-left: 4px solid var(--hg-c, #64748b);
}
.hg-blue {
  --hg-c: #2563eb;
}
.hg-teal {
  --hg-c: #0d9488;
}
.hg-amber {
  --hg-c: #d97706;
}
.hg-violet {
  --hg-c: #7c3aed;
}
.hg-rose {
  --hg-c: #e11d48;
}
.rpt-help dl {
  margin: 0;
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 6px 14px;
}
.rpt-help dt {
  font-size: 12px;
  font-weight: 800;
  color: #334155;
  padding-top: 1px;
}
.rpt-help dd {
  margin: 0;
  font-size: 12px;
  line-height: 1.75;
  color: #475569;
}
.rpt-help dd b {
  color: #0f172a;
}
.rpt-help dd code {
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 700;
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
}
@media (max-width: 720px) {
  .rpt-help dl {
    grid-template-columns: 1fr;
  }
}

@media print {
  .rpt-toolbar .rpt-actions,
  .rpt-saved-bar,
  .rpt-ideas,
  .rpt-ambient {
    display: none !important;
  }
  .rpt-page {
    background: #fff;
    padding: 0;
  }
  .rpt-chart-card,
  .rpt-block,
  .rpt-kpi__card {
    box-shadow: none !important;
    break-inside: avoid;
  }
}
</style>
