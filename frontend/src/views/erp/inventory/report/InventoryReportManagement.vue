<template>
  <div class="rpt-page ir-modern pb-std">
    <div class="page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="pb-bubbles" aria-hidden="true" />
      <div class="toolbar-left">
        <div class="toolbar-brand">
          <div class="toolbar-icon-wrap">
            <el-icon class="toolbar-icon"><DataBoard /></el-icon>
          </div>
          <div class="toolbar-text">
            <h1 class="toolbar-title pb-hero-title">
              在庫報告管理
              <button type="button" class="rpt-help-btn" title="操作説明を開く" @click="goManual">
                <el-icon><Document /></el-icon>
              </button>
              <button type="button" class="rpt-help-btn" title="用語・算出方法の説明" @click="helpVisible = true">
                <el-icon><QuestionFilled /></el-icon>
              </button>
            </h1>
            <p class="toolbar-desc pb-hero-desc">{{ reportTypeLabel }}報告 · {{ selectedPeriodLabel }}</p>
          </div>
        </div>
      </div>
      <div class="toolbar-right toolbar-actions">
        <el-button class="tb-btn tb-btn-slate" :loading="loading" @click="loadSavedList">
          <el-icon><FolderOpened /></el-icon>
          <span class="tb-label">保存一覧</span>
        </el-button>
        <el-button class="tb-btn tb-btn-green" :loading="loading" @click="onGenerate">
          <el-icon><MagicStick /></el-icon>
          <span class="tb-label">レポート生成</span>
        </el-button>
        <el-button class="tb-btn tb-btn-amber" :disabled="!payload" @click="onSave('draft')">
          <el-icon><EditPen /></el-icon>
          <span class="tb-label">下書き保存</span>
        </el-button>
        <el-button class="tb-btn tb-btn-blue" :disabled="!payload" @click="onSave('final')">
          <el-icon><CircleCheck /></el-icon>
          <span class="tb-label">確定保存</span>
        </el-button>
        <el-button class="tb-btn tb-btn-indigo" :disabled="!payload" :loading="printing" @click="onPrint">
          <el-icon><Printer /></el-icon>
          <span class="tb-label">印刷</span>
        </el-button>
        <el-button class="tb-btn tb-btn-teal" :disabled="!payload" :loading="exportingExcel" @click="onExportExcel">
          <el-icon><Download /></el-icon>
          <span class="tb-label">Excel出力</span>
        </el-button>
        <el-button class="tb-btn tb-btn-rose" :disabled="!payload" :loading="exportingPdf" @click="onExportPdf">
          <el-icon><Document /></el-icon>
          <span class="tb-label">PDF出力</span>
        </el-button>
        <el-button class="tb-btn tb-btn-violet" :disabled="!payload" :loading="exportingPpt" @click="onExportPpt">
          <el-icon><DataAnalysis /></el-icon>
          <span class="tb-label">PPT出力</span>
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-inline">
        <div class="fi-group">
          <el-icon class="fi-icon"><DataBoard /></el-icon>
          <el-select v-model="fiscalYear" size="default" class="fi-select fi-year" filterable>
            <el-option v-for="y in fiscalYearOptions" :key="y" :label="`${y}年度`" :value="y" />
          </el-select>
        </div>
        <div class="fi-sep" />
        <div class="fi-group">
          <el-radio-group v-model="reportType" size="small" class="rpt-period-type">
            <el-radio-button value="quarter">四半期</el-radio-button>
            <el-radio-button value="half">半期</el-radio-button>
            <el-radio-button value="annual">年間</el-radio-button>
          </el-radio-group>
        </div>
        <div v-if="reportType !== 'annual'" class="fi-group">
          <el-radio-group v-model="quarter" size="small" class="rpt-quarter">
            <el-radio-button v-for="opt in periodOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </div>

    <div v-if="savedList.length" class="rpt-saved-bar animate-in" style="--delay: 40ms">
      <span class="rpt-saved-bar__label">
        <el-icon :size="14"><FolderOpened /></el-icon>
        保存済み
        <em>{{ savedList.length }}</em>
      </span>
      <TransitionGroup name="rpt-chip" tag="div" class="rpt-saved-bar__chips">
        <div
          v-for="s in savedList"
          :key="s.id"
          class="rpt-saved-chip"
          :class="[
            s.status === 'final' ? 'is-final' : 'is-draft',
            { 'is-active': savedId === s.id },
          ]"
        >
          <button type="button" class="rpt-saved-chip__main" @click="onLoadSaved(s.id)">
            <i class="rpt-saved-chip__dot" />
            <span class="rpt-saved-chip__text">
              {{ s.label }}
              <small>{{ s.status === 'final' ? '確定' : '下書き' }}</small>
            </span>
          </button>
          <button
            type="button"
            class="rpt-saved-chip__del"
            title="この保存レポートを削除"
            :disabled="loading || deletingId === s.id"
            @click.stop="onDeleteSaved(s)"
          >
            <el-icon :size="12"><Close /></el-icon>
          </button>
        </div>
      </TransitionGroup>
    </div>

    <el-empty v-if="!payload && !loading" class="rpt-empty" description="年度・報告期間を選び「レポート生成」を実行してください" />

    <div v-else v-loading="loading" class="rpt-body">
      <section v-if="payload" class="rpt-kpi animate-in" :class="`is-${reportType}`" style="--delay: 80ms">
        <div class="rpt-kpi__card theme-inv rpt-kpi__card--wide">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><DataAnalysis /></el-icon></span>
            <div class="rpt-kpi__label">
              月末在庫（仕掛品・製品）
              <small class="rpt-kpi__unit">単位：千本</small>
            </div>
          </div>
          <div class="rpt-kpi__body">
            <div class="rpt-kpi__months">
              <div v-for="m in monthlyKpiRows" :key="`inv-${m.month}`" class="rpt-kpi__month">
                <span>{{ m.month_label }}</span>
                <strong :class="negClass(m.closing_total_qty)">計 {{ fmtSen(m.closing_total_qty) }}</strong>
                <small
                  >仕掛
                  <span :class="negClass(m.closing_wip_qty)">{{ fmtSen(m.closing_wip_qty) }}</span>
                  / 製品
                  <span :class="negClass(m.closing_product_qty)">{{ fmtSen(m.closing_product_qty) }}</span></small
                >
              </div>
            </div>
            <div ref="invChartRef" class="rpt-kpi__chart rpt-kpi__chart--tall" />
          </div>
        </div>
        <div class="rpt-kpi__card theme-wip">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Box /></el-icon></span>
            <div class="rpt-kpi__label">
              期末仕掛品
              <small class="rpt-kpi__unit">単位：千本</small>
            </div>
          </div>
          <div class="rpt-kpi__body">
            <div class="rpt-kpi__months">
              <div v-for="m in monthlyKpiRows" :key="`wip-${m.month}`" class="rpt-kpi__month">
                <span>{{ m.month_label }}</span>
                <strong :class="negClass(m.closing_wip_qty)">{{ fmtSen(m.closing_wip_qty) }}</strong>
              </div>
            </div>
            <div ref="wipChartRef" class="rpt-kpi__chart" />
          </div>
        </div>
        <div class="rpt-kpi__card theme-product">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Goods /></el-icon></span>
            <div class="rpt-kpi__label">
              期末製品
              <small class="rpt-kpi__unit">単位：千本</small>
              <small class="rpt-kpi__target">目安 {{ rptTargetClosingProductSen }}</small>
            </div>
          </div>
          <div class="rpt-kpi__body">
            <div class="rpt-kpi__months">
              <div v-for="m in monthlyKpiRows" :key="`prod-${m.month}`" class="rpt-kpi__month">
                <span>{{ m.month_label }}</span>
                <strong :class="negClass(m.closing_product_qty)">{{ fmtSen(m.closing_product_qty) }}</strong>
              </div>
            </div>
            <div ref="productChartRef" class="rpt-kpi__chart" />
          </div>
        </div>
        <div class="rpt-kpi__card theme-defect">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><WarningFilled /></el-icon></span>
            <div class="rpt-kpi__label">
              廃棄率
              <small class="rpt-kpi__unit">単位：%</small>
              <small class="rpt-kpi__target">目安 {{ rptTargetScrapRatePercent }}</small>
            </div>
          </div>
          <div class="rpt-kpi__body">
            <div class="rpt-kpi__months">
              <div v-for="m in monthlyKpiRows" :key="`rate-${m.month}`" class="rpt-kpi__month">
                <span>{{ m.month_label }}</span>
                <strong :class="negClass(m.quality_loss_rate_percent)">{{
                  fmtPctNum(m.quality_loss_rate_percent)
                }}</strong>
                <small>連乗損失率</small>
              </div>
            </div>
            <div ref="scrapRateChartRef" class="rpt-kpi__chart" />
          </div>
        </div>
        <div class="rpt-kpi__card theme-qty">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><Histogram /></el-icon></span>
            <div class="rpt-kpi__label">
              廃棄本数
              <small class="rpt-kpi__unit">単位：千本（不良+廃棄）</small>
            </div>
          </div>
          <div class="rpt-kpi__body">
            <div class="rpt-kpi__months">
              <div v-for="m in monthlyKpiRows" :key="`loss-${m.month}`" class="rpt-kpi__month">
                <span>{{ m.month_label }}</span>
                <strong :class="negClass(m.loss_qty)">{{ fmtSen(m.loss_qty) }}</strong>
              </div>
            </div>
            <div ref="scrapQtyChartRef" class="rpt-kpi__chart" />
          </div>
        </div>
        <div class="rpt-kpi__card theme-match">
          <div class="rpt-kpi__head">
            <span class="rpt-kpi__ico"><el-icon><CircleCheck /></el-icon></span>
            <div class="rpt-kpi__label">
              棚卸一致率
              <small class="rpt-kpi__unit">単位：%</small>
            </div>
          </div>
          <div class="rpt-kpi__body">
            <div class="rpt-kpi__months">
              <div v-for="m in monthlyKpiRows" :key="`match-${m.month}`" class="rpt-kpi__month">
                <span>{{ m.month_label }}</span>
                <strong :class="negClass(m.match_rate)">{{ fmtPctNum(m.match_rate) }}</strong>
                <small>差異 |Σ| {{ fmtInt(m.diff_abs) }}</small>
              </div>
            </div>
            <div ref="matchChartRef" class="rpt-kpi__chart" />
          </div>
        </div>
      </section>

      <section class="rpt-block accent-violet animate-in" style="--delay: 200ms">
        <div class="rpt-block__head">
          <span class="rpt-block__title"><el-icon><ScaleToOriginal /></el-icon>理論在庫 vs 棚卸差異（工程別）</span>
          <small class="rpt-block__hint"
            >対象期間の月平均・単位：千本（検査は倉庫へ合算／切断・面取は差異なし）</small
          >
        </div>
        <div ref="diffChartRef" class="rpt-embed-chart" />
        <el-table
          :data="diffByProcessAvg"
          size="small"
          border
          max-height="360"
          class="rpt-table rpt-diff-table"
        >
          <el-table-column prop="process_name" label="工程" width="140">
            <template #default="{ row }">
              <span class="diff-proc">{{ row.process_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="process_cd" label="工程CD" width="100">
            <template #default="{ row }">
              <span class="diff-proc-cd">{{ row.process_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="month_count" label="対象月数" width="88" align="center">
            <template #default="{ row }">{{ row.month_count }}</template>
          </el-table-column>
          <el-table-column prop="theoretical_qty" label="理論在庫(平均・千本)" width="148" align="right">
            <template #default="{ row }">
              <span :class="negClass(row.theoretical_qty)">{{ fmtSen(row.theoretical_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="stocktake_qty" label="棚卸在庫(平均・千本)" width="148" align="right">
            <template #default="{ row }">
              <span :class="negClass(row.stocktake_qty)">{{ fmtSen(row.stocktake_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="diff_qty" label="差異(平均・千本)" width="128" align="right">
            <template #default="{ row }">
              <span class="diff-strong" :class="negClass(row.diff_qty)">{{ fmtSignedSen(row.diff_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="diff_rate" label="差異率(平均・%)" width="120" align="right">
            <template #default="{ row }">
              <span :class="negClass(row.diff_rate)">{{
                row.diff_rate == null ? '—' : fmtPctNum(row.diff_rate)
              }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="rpt-block accent-amber animate-in" style="--delay: 220ms">
        <div class="rpt-block__head">
          <span class="rpt-block__title"><el-icon><Bell /></el-icon>大量廃棄・保留品・大量不良（対象期間）</span>
        </div>
        <div ref="bulkDetailChartRef" class="rpt-embed-chart" />
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
          <el-table-column prop="quantity" label="本数（本）" width="100" align="right">
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

      <section class="rpt-block accent-slate rpt-ideas animate-in" style="--delay: 240ms">
        <div class="rpt-block__head">
          <span class="rpt-block__title"><el-icon><MagicStick /></el-icon>報告向け・追加で使える観点</span>
        </div>
        <ul>
          <li>前期間比・前年同期比（在庫・廃棄率・一致率）</li>
          <li>仕掛品／製品構成比の変化と滞留リスク</li>
          <li>大量廃棄・保留品の未処理件数と期限超過アラート</li>
          <li>工程別廃棄率ヒートマップと目標ライン（例: 1.5%）の並記</li>
          <li>在庫金額（棚卸金額管理と連携）での金額ベース報告</li>
        </ul>
      </section>
    </div>

    <el-dialog
      v-model="helpVisible"
      class="rpt-help-dialog pb-std"
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
              <b>製品</b>＝検査・倉庫・外注倉庫の在庫合計。画面表示は<b>千本</b>単位です。
            </dd>
            <dt>前期間比</dt>
            <dd>選択期間末月の月末在庫と、同じ報告単位の前期間末月との差分。四半期は前Q、半期は前半期、年間は前年度と比較します。</dd>
          </dl>
        </section>

        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-amber">品質指標</h3>
          <dl>
            <dt>廃棄率</dt>
            <dd>
              廃棄率分析と同じく、<b>主ライン（切断・面取・成型・メッキ・溶接・検査）</b>の不良＋廃棄本数を使い、連乗方式で算出します。
              <code>廃棄率＝ 1 − Π(1 − 工程別率)</code>、工程別率＝その工程の（不良＋廃棄）本数 ÷ 実績本数。
              実績が0の工程は計算から除外します。倉庫・外注工程は含めません。
            </dd>
            <dt>廃棄本数</dt>
            <dd>全工程の不良＋廃棄本数の合計。画面表示は<b>千本</b>単位です。</dd>
            <dt>目安 1.5%</dt>
            <dd>廃棄率の管理目安ライン（グラフの破線）。超過した月は自動分析・ハイライトで注意喚起されます。</dd>
            <dt>期末製品 目安 375千本</dt>
            <dd>期末製品在庫の管理目安（千本）。グラフに破線で表示します。</dd>
          </dl>
        </section>

        <section class="rpt-help__group">
          <h3 class="rpt-help__group-title hg-violet">棚卸差異</h3>
          <dl>
            <dt>理論在庫</dt>
            <dd>生産集計（実績・繰越・推移）から計算上あるべき在庫数。月末時点・製品×工程単位で集計します。</dd>
            <dt>棚卸在庫</dt>
            <dd>実地棚卸（棚卸記録）で実際に数えた在庫数。</dd>
            <dt>棚卸差異（工程別）</dt>
            <dd>
              <code>差異 = 棚卸在庫 − 理論在庫</code>。画面では月別に分けず、<b>対象期間の月平均値</b>を工程別に表示します。
              プラスは帳簿より実物が多い、マイナスは実物が少ないことを意味します。
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
            <dt>大量廃棄・保留品・大量不良</dt>
            <dd>
              「大量廃棄・保留品管理」の登録記録に加え、生産実績で工程別不良本数が 200 本を超える「大量不良」を自動併記します。
              KPI・グラフは区分（大量廃棄／保留品／大量不良など）ごとに色分けして表示します。未処理件数は手動登録の未処理のみを対象とします。
            </dd>
            <dt>下書き保存／確定保存</dt>
            <dd>
              集計スナップショットをまとめて保存します。確定保存は報告版として記録する場合に使用します。
              上部の「保存済み」チップから読込でき、× で不要な保存を削除できます。
            </dd>
            <dt>印刷</dt>
            <dd>
              生成レポートをA4縦の報告書レイアウト（表紙・KPI・月別表・グラフ・差異・大量廃棄明細）に整形して印刷します。
            </dd>
            <dt>Excel出力</dt>
            <dd>
              画面と同じ内容を複数シートで出力します（月末在庫・月別KPI・大量廃棄区分・棚卸差異・大量廃棄明細）。在庫・廃棄本数は千本単位です。
            </dd>
            <dt>PDF出力</dt>
            <dd>
              画面に表示しているKPIカード・グラフ・差異表・大量廃棄明細と同じ構成をPDFファイルとして保存します。
            </dd>
            <dt>PPT出力</dt>
            <dd>
              生産管理部・在庫報告の表紙付きで、KPIカードを1枚ずつスライド化したPowerPointをダウンロードします（画面グラフを埋め込み）。
            </dd>
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
  CircleCheck,
  Close,
  DataAnalysis,
  DataBoard,
  Document,
  Download,
  EditPen,
  FolderOpened,
  Goods,
  Histogram,
  MagicStick,
  Printer,
  QuestionFilled,
  ScaleToOriginal,
  WarningFilled,
} from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'

/** echarts/core の init 戻り値（'echarts' の ECharts 型と冲突しないよう揃える） */
type ECharts = ReturnType<typeof echarts.init>
import {
  inventoryReportApi,
  type MonthlyReportKpi,
  type QuarterlyReportPayload,
  type SavedReportSummary,
} from '@/api/inventoryReport'
import {
  exportInventoryReportExcel,
  exportInventoryReportPdf,
  printInventoryReport,
  type InventoryReportChartImages,
  type InventoryReportExportInput,
} from './inventoryReportExport'
import {
  RPT_TARGET_CLOSING_PRODUCT_SEN,
  RPT_TARGET_SCRAP_RATE_PERCENT,
} from './inventoryReportTargets'

const rptTargetScrapRatePercent = RPT_TARGET_SCRAP_RATE_PERCENT
const rptTargetClosingProductSen = RPT_TARGET_CLOSING_PRODUCT_SEN

const loading = ref(false)
const printing = ref(false)
const exportingExcel = ref(false)
const exportingPdf = ref(false)
const exportingPpt = ref(false)
const deletingId = ref<number | null>(null)
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
const savedId = ref<number | null>(null)
const savedList = ref<SavedReportSummary[]>([])
const helpVisible = ref(false)
function goManual() {
  window.open('/manuals/inventory-report', '_blank', 'noopener,noreferrer')
}

const invChartRef = ref<HTMLDivElement | null>(null)
const wipChartRef = ref<HTMLDivElement | null>(null)
const productChartRef = ref<HTMLDivElement | null>(null)
const scrapRateChartRef = ref<HTMLDivElement | null>(null)
const scrapQtyChartRef = ref<HTMLDivElement | null>(null)
const matchChartRef = ref<HTMLDivElement | null>(null)
const diffChartRef = ref<HTMLDivElement | null>(null)
const bulkDetailChartRef = ref<HTMLDivElement | null>(null)
let invChart: ECharts | null = null
let wipChart: ECharts | null = null
let productChart: ECharts | null = null
let scrapRateChart: ECharts | null = null
let scrapQtyChart: ECharts | null = null
let matchChart: ECharts | null = null
let diffChart: ECharts | null = null
let bulkDetailChart: ECharts | null = null

const monthlyKpiRows = computed<MonthlyReportKpi[]>(() => {
  const report = payload.value
  if (!report) return []
  const apiRows = report.monthly_kpis || []

  return report.inventory_series.map((inv) => {
    const base = apiRows.find((r) => r.month === inv.month)
    const qualitySeries = report.scrap_series.find((r) => r.month === inv.month)
    const legacyMonth = report.months.find((m) => String(m.month || '') === inv.month) as
      | { stocktake_diff?: { kpi?: { match_rate?: number; diff_qty_total?: number } } }
      | undefined
    const legacyBulkItems = (report.bulk_disposal?.items || []).filter((item) =>
      String(item.occurred_date || '').startsWith(inv.month)
    )
    const legacyBulk = report.bulk_disposal?.by_month?.find((r) => r.month === inv.month)
    const lossQty =
      base?.loss_qty ??
      qualitySeries?.sum_defect_and_scrap ??
      Number(base?.defect_qty || 0) + Number(base?.scrap_qty || 0)
    const cuttingActual =
      base?.sum_cutting_actual ??
      qualitySeries?.sum_cutting_actual ??
      qualitySeries?.processes?.find((p) => p.key === 'cutting')?.sum_actual ??
      0

    return {
      month: inv.month,
      month_label: inv.month_label,
      closing_wip_qty: base?.closing_wip_qty ?? inv.wip_qty,
      closing_product_qty: base?.closing_product_qty ?? inv.product_qty,
      closing_total_qty: base?.closing_total_qty ?? inv.total_qty,
      scrap_rate_percent: base?.scrap_rate_percent ?? null,
      all_process_loss_rate_percent:
        base?.all_process_loss_rate_percent ?? qualitySeries?.all_process_loss_rate_percent ?? null,
      quality_loss_rate_percent:
        base?.quality_loss_rate_percent ?? qualitySeries?.quality_loss_rate_percent ?? null,
      sum_cutting_actual: cuttingActual,
      defect_rate_percent:
        base?.defect_rate_percent ?? qualitySeries?.defect_rate_percent ?? null,
      defect_qty: lossQty,
      scrap_qty: 0,
      loss_qty: lossQty,
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

type DiffProcessAvgRow = {
  process_cd: string
  process_name: string
  month_count: number
  theoretical_qty: number
  stocktake_qty: number
  diff_qty: number
  diff_rate: number | null
  match_rate: number
}

/** 工程表示順：切断→面取→成型→メッキ→溶接→倉庫（検査は倉庫へ合算済み） */
const DIFF_PROCESS_ORDER = ['KT01', 'KT02', 'KT04', 'KT05', 'KT07', 'KT13']

/** 切断・面取は差異なし表示（理論＝棚卸） */
function isZeroDiffProcess(processCd: string, processName?: string) {
  const cd = String(processCd || '').trim()
  const name = String(processName || '').trim().replace(/工程$/, '')
  return cd === 'KT01' || cd === 'KT02' || name === '切断' || name === '面取' || name === '面取り'
}

function avgRounded(sum: number, count: number) {
  if (count <= 0) return 0
  return Math.round(sum / count)
}

function processOrderIndex(processCd: string) {
  const idx = DIFF_PROCESS_ORDER.indexOf(processCd)
  return idx >= 0 ? idx : DIFF_PROCESS_ORDER.length + 1
}

/** 棚卸差異表示用：検査工程は倉庫へ合算する */
function normalizeDiffProcess(processCd: string, processName: string) {
  const cd = String(processCd || '').trim()
  let name = String(processName || '').trim().replace(/工程$/, '')
  if (name === '面取り') name = '面取'
  if (cd === 'KT01' || name === '切断') {
    return { process_cd: 'KT01', process_name: '切断', key: 'KT01' }
  }
  if (cd === 'KT02' || name === '面取') {
    return { process_cd: 'KT02', process_name: '面取', key: 'KT02' }
  }
  if (cd === 'KT09' || name === '検査') {
    return { process_cd: 'KT13', process_name: '倉庫', key: 'KT13' }
  }
  if (cd === 'KT13' || name === '倉庫') {
    return { process_cd: 'KT13', process_name: '倉庫', key: 'KT13' }
  }
  return {
    process_cd: cd,
    process_name: name || cd,
    key: cd || name,
  }
}

const diffByProcessAvg = computed<DiffProcessAvgRow[]>(() => {
  // ① 月×工程で合算（検査→倉庫）
  const monthBuckets = new Map<
    string,
    {
      process_cd: string
      process_name: string
      month: string
      theoretical_qty: number
      stocktake_qty: number
      diff_qty: number
      match_weight: number
      match_rate_sum: number
    }
  >()
  for (const r of payload.value?.diff_by_month_process || []) {
    const norm = normalizeDiffProcess(String(r.process_cd || ''), String(r.process_name || ''))
    if (!norm.key) continue
    const month = String(r.month || r.month_label || '')
    const bucketKey = `${norm.key}__${month}`
    const theo = Number(r.theoretical_qty || 0)
    const g = monthBuckets.get(bucketKey) || {
      process_cd: norm.process_cd,
      process_name: norm.process_name,
      month,
      theoretical_qty: 0,
      stocktake_qty: 0,
      diff_qty: 0,
      match_weight: 0,
      match_rate_sum: 0,
    }
    g.theoretical_qty += theo
    g.stocktake_qty += Number(r.stocktake_qty || 0)
    g.diff_qty += Number(r.diff_qty || 0)
    const w = Math.abs(theo) || 1
    g.match_weight += w
    g.match_rate_sum += Number(r.match_rate || 0) * w
    monthBuckets.set(bucketKey, g)
  }

  // ② 工程別に月平均
  const groups = new Map<
    string,
    {
      process_cd: string
      process_name: string
      month_count: number
      theoretical_qty: number
      stocktake_qty: number
      diff_qty: number
      match_rate: number
    }
  >()
  for (const m of monthBuckets.values()) {
    const g = groups.get(m.process_cd || m.process_name) || {
      process_cd: m.process_cd,
      process_name: m.process_name,
      month_count: 0,
      theoretical_qty: 0,
      stocktake_qty: 0,
      diff_qty: 0,
      match_rate: 0,
    }
    g.month_count += 1
    g.theoretical_qty += m.theoretical_qty
    g.stocktake_qty += m.stocktake_qty
    g.diff_qty += m.diff_qty
    g.match_rate += m.match_weight > 0 ? m.match_rate_sum / m.match_weight : 0
    groups.set(m.process_cd || m.process_name, g)
  }

  return [...groups.values()]
    .map((g) => {
      let theoretical_qty = avgRounded(g.theoretical_qty, g.month_count)
      let stocktake_qty = avgRounded(g.stocktake_qty, g.month_count)
      let diff_qty = avgRounded(g.diff_qty, g.month_count)
      let match_rate =
        g.month_count > 0 ? Math.round((g.match_rate / g.month_count) * 100) / 100 : 0
      let diff_rate: number | null =
        theoretical_qty !== 0
          ? Math.round((diff_qty / theoretical_qty) * 10000) / 100
          : null
      // 切断・面取：理論＝棚卸、差異なし（一致率100%）
      if (isZeroDiffProcess(g.process_cd, g.process_name)) {
        const qty = theoretical_qty || stocktake_qty
        theoretical_qty = qty
        stocktake_qty = qty
        diff_qty = 0
        diff_rate = 0
        match_rate = 100
      }
      return {
        process_cd: g.process_cd,
        process_name: g.process_name,
        month_count: g.month_count,
        theoretical_qty,
        stocktake_qty,
        diff_qty,
        diff_rate,
        match_rate,
      }
    })
    .sort((a, b) => {
      const oi = processOrderIndex(a.process_cd) - processOrderIndex(b.process_cd)
      if (oi !== 0) return oi
      return String(a.process_name).localeCompare(String(b.process_name), 'ja')
    })
})

type BulkCategoryColor = { top: string; bottom: string; label: string }

function bulkCategoryColor(name: string): BulkCategoryColor {
  if (name.includes('不良')) return { top: '#c4b5fd', bottom: '#7c3aed', label: '#6d28d9' }
  if (name.includes('廃棄')) return { top: '#fb7185', bottom: '#e11d48', label: '#be123c' }
  if (name.includes('保留')) return { top: '#fbbf24', bottom: '#d97706', label: '#b45309' }
  if (name.includes('消滅')) return { top: '#67e8f9', bottom: '#0891b2', label: '#0e7490' }
  return { top: '#94a3b8', bottom: '#64748b', label: '#475569' }
}

const bulkCategoryRows = computed(() => {
  const bulk = payload.value?.bulk_disposal
  const fromApi = (bulk?.by_category || []).map((c) => ({
    name: String(c.category || 'その他'),
    quantity: Number(c.quantity || 0),
    count: Number(c.count || 0),
  }))
  const rows =
    fromApi.length > 0
      ? fromApi
      : Object.values(
          (bulk?.items || []).reduce<Record<string, { name: string; quantity: number; count: number }>>(
            (acc, item) => {
              const name = String(item.report_category || 'その他')
              const bucket = acc[name] || { name, quantity: 0, count: 0 }
              bucket.quantity += Number(item.quantity || 0)
              bucket.count += 1
              acc[name] = bucket
              return acc
            },
            {},
          ),
        )
  return rows
    .map((r) => ({ ...r, color: bulkCategoryColor(r.name) }))
    .sort((a, b) => b.quantity - a.quantity || b.count - a.count)
})

function fmtInt(v: number | null | undefined) {
  if (v == null || Number.isNaN(Number(v))) return '0'
  return Number(v).toLocaleString()
}

/** 本数を千本単位へ換算（小数1桁） */
function toSen(v: number | null | undefined) {
  if (v == null || Number.isNaN(Number(v))) return 0
  return Math.round((Number(v) / 1000) * 10) / 10
}

function fmtSen(v: number | null | undefined) {
  return toSen(v).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })
}

function fmtSignedSen(v: number | null | undefined) {
  const n = toSen(v)
  const s = Math.abs(n).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })
  if (n > 0) return `+${s}`
  if (n < 0) return `-${s}`
  return s
}

/** 百分率の数値のみ（単位 % は見出し側で表示） */
function fmtPctNum(v: number | null | undefined) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function fmtPct(v: number | null | undefined) {
  const n = fmtPctNum(v)
  return n === '—' ? n : `${n}%`
}

function reportTypeForCode(code: number): 'quarter' | 'half' | 'annual' {
  if (code <= 4) return 'quarter'
  if (code <= 6) return 'half'
  return 'annual'
}

const CHART_NEG_COLOR = '#dc2626'

/** 負数は赤表示 */
function negClass(v: number | null | undefined) {
  const n = Number(v)
  if (Number.isNaN(n) || n >= 0) return ''
  return 'num-neg'
}

function deltaClass(v: number | null | undefined) {
  return negClass(v)
}

function isChartNeg(v: unknown) {
  const n = Number(v)
  return !Number.isNaN(n) && n < 0
}

/** グラフラベル色（負数は赤） */
function chartLabelColor(v: unknown, posColor: string) {
  return isChartNeg(v) ? CHART_NEG_COLOR : posColor
}

/** tooltip 用：負数を赤文字で返す */
function chartTipValue(text: string, v: unknown) {
  if (!isChartNeg(v)) return text
  return `<span style="color:${CHART_NEG_COLOR};font-weight:800">${text}</span>`
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
  if (s.includes('不良')) return 'bulk-chip--violet'
  if (s.includes('保留')) return 'bulk-chip--amber'
  if (s.includes('消滅')) return 'bulk-chip--cyan'
  return 'bulk-chip--slate'
}

function bulkStatusClass(status: string | null | undefined) {
  const s = String(status || '')
  if (s.includes('未')) return 'bulk-chip--bad'
  if (s) return 'bulk-chip--good'
  return 'bulk-chip--slate'
}

function disposeCharts() {
  invChart?.dispose()
  wipChart?.dispose()
  productChart?.dispose()
  scrapRateChart?.dispose()
  scrapQtyChart?.dispose()
  matchChart?.dispose()
  diffChart?.dispose()
  bulkDetailChart?.dispose()
  invChart =
    wipChart =
    productChart =
    scrapRateChart =
    scrapQtyChart =
    matchChart =
    diffChart =
    bulkDetailChart =
      null
}

function bindChart(current: ECharts | null, el: HTMLDivElement | null): ECharts | null {
  if (!el) return current
  if (current && !current.isDisposed()) return current
  return echarts.init(el)
}

type TargetTone = 'amber' | 'teal' | 'emerald'

function targetToneStyle(tone: TargetTone) {
  if (tone === 'teal') {
    return {
      line: '#14b8a6',
      badgeFill: '#f0fdfa',
      badgeStroke: '#5eead4',
      text: '#0f766e',
    }
  }
  if (tone === 'emerald') {
    return {
      line: '#10b981',
      badgeFill: '#ecfdf5',
      badgeStroke: '#6ee7b7',
      text: '#047857',
    }
  }
  return {
    line: '#f59e0b',
    badgeFill: '#fffbeb',
    badgeStroke: '#fcd34d',
    text: '#92400e',
  }
}

/** 目安ラベルをプロット内右上に固定（markLine ラベルのはみ出しを防ぐ） */
function buildTargetBadgeGraphic(label: string, tone: TargetTone) {
  const text = label.trim()
  if (!text) return undefined
  const toneStyle = targetToneStyle(tone)
  const height = 20
  const width = Math.min(112, Math.max(58, text.length * 7.2 + 14))
  return [
    {
      type: 'group',
      right: 8,
      top: 6,
      width,
      height,
      z: 100,
      children: [
        {
          type: 'rect',
          left: 0,
          top: 0,
          shape: { width, height, r: height / 2 },
          style: {
            fill: toneStyle.badgeFill,
            stroke: toneStyle.badgeStroke,
            lineWidth: 1,
          },
        },
        {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text,
            fill: toneStyle.text,
            fontSize: 9,
            fontWeight: 700,
            textAlign: 'center',
            textVerticalAlign: 'middle',
          },
        },
      ],
    },
  ]
}

function renderMiniLine(
  chart: ECharts,
  name: string,
  labels: string[],
  values: Array<number | null>,
  colors: { line: string; areaTop: string; areaBottom: string; label: string },
  format: (value: number) => string,
  opts?: { markLineY?: number; markLineLabel?: string; targetTone?: TargetTone },
) {
  const nums = values.filter((v): v is number => v != null && !Number.isNaN(Number(v))).map(Number)
  const targetY = opts?.markLineY
  const hasTarget = targetY != null && !Number.isNaN(Number(targetY))
  if (hasTarget) nums.push(Number(targetY))
  const maxVal = nums.length ? Math.max(...nums) : 0
  const minVal = nums.length ? Math.min(...nums) : 0
  const pad = Math.max((maxVal - minVal) * 0.28, Math.abs(maxVal) * 0.14, Math.abs(minVal) * 0.14, 0.5)
  let yMin = minVal < 0 ? minVal - pad * 0.35 : Math.max(0, minVal - pad * 0.35)
  let yMax = maxVal + pad
  if (hasTarget) {
    const t = Number(targetY)
    if (t >= yMax - pad * 0.15) yMax = t + pad * 0.45
    if (t <= yMin + pad * 0.1) yMin = t < 0 ? t - pad * 0.45 : Math.max(0, t - pad * 0.45)
  }
  const targetTone = opts?.targetTone ?? 'amber'
  const targetStyle = targetToneStyle(targetTone)

  chart.setOption(
    {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'line',
          lineStyle: { color: colors.line, width: 1.5, type: 'dashed', opacity: 0.45 },
        },
        backgroundColor: 'rgba(255, 255, 255, 0.97)',
        borderColor: colors.line,
        borderWidth: 1,
        padding: [8, 12],
        textStyle: { color: '#0f172a', fontSize: 12, fontWeight: 600 },
        extraCssText: 'box-shadow: 0 8px 22px rgba(15, 23, 42, 0.12); border-radius: 10px;',
        formatter: (params: unknown) => {
          const rows = (Array.isArray(params) ? params : [params]) as Array<{
            axisValueLabel?: string
            marker?: string
            seriesName?: string
            value?: number | null
          }>
          if (!rows.length) return ''
          const head = `<div style="font-weight:800;margin-bottom:4px">${rows[0]?.axisValueLabel || ''}</div>`
          const body = rows
            .map((r) => {
              const raw = r.value
              const text =
                raw == null || Number.isNaN(Number(raw)) ? '—' : format(Number(raw))
              return `<div style="display:flex;justify-content:space-between;gap:12px"><span>${r.marker || ''} ${r.seriesName || ''}</span><b>${chartTipValue(text, raw)}</b></div>`
            })
            .join('')
          return head + body
        },
      },
      grid: {
        left: 36,
        right: 12,
        top: hasTarget ? 32 : 44,
        bottom: 12,
        containLabel: true,
      },
      graphic: hasTarget ? buildTargetBadgeGraphic(opts?.markLineLabel || `目安 ${targetY}`, targetTone) : undefined,
      xAxis: {
        type: 'category',
        // 両端に余白を確保し、端点ラベルの見切れを防ぐ
        boundaryGap: true,
        data: labels,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b', fontWeight: 700, fontSize: 11, margin: 10 },
      },
      yAxis: {
        type: 'value',
        min: yMin,
        max: yMax,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.22)' } },
      },
      animationDuration: 850,
      animationEasing: 'cubicOut',
      series: [
        {
          name,
          type: 'line',
          smooth: 0.35,
          symbol: 'circle',
          symbolSize: 9,
          showSymbol: true,
          clip: true,
          data: values.map((v) => {
            if (v == null || Number.isNaN(Number(v))) return null
            const n = Number(v)
            const neg = n < 0
            return {
              value: n,
              label: {
                position: 'top' as const,
                color: chartLabelColor(n, colors.label),
              },
              itemStyle: neg
                ? {
                    color: CHART_NEG_COLOR,
                    borderColor: '#fff',
                    borderWidth: 2,
                    shadowColor: `${CHART_NEG_COLOR}66`,
                    shadowBlur: 6,
                  }
                : undefined,
            }
          }),
          connectNulls: false,
          lineStyle: {
            width: 3,
            color: colors.line,
            shadowColor: `${colors.line}55`,
            shadowBlur: 8,
            shadowOffsetY: 3,
          },
          itemStyle: {
            color: colors.line,
            borderColor: '#fff',
            borderWidth: 2,
            shadowColor: `${colors.line}66`,
            shadowBlur: 6,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: colors.areaTop },
              { offset: 1, color: colors.areaBottom },
            ]),
          },
          emphasis: {
            focus: 'series',
            scale: 1.35,
            itemStyle: { borderWidth: 3, shadowBlur: 10 },
          },
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: colors.label,
            fontSize: 10,
            fontWeight: 800,
            formatter: ({ value }: { value: number | null }) =>
              value == null || Number.isNaN(Number(value)) ? '' : format(Number(value)),
          },
          labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
          ...(hasTarget
            ? {
                markLine: {
                  silent: true,
                  symbol: 'none',
                  animation: false,
                  data: [{ yAxis: Number(targetY) }],
                  lineStyle: {
                    type: 'dashed',
                    color: targetStyle.line,
                    width: 1.5,
                    opacity: 0.85,
                  },
                  label: { show: false },
                },
              }
            : {}),
        },
      ],
    },
    { notMerge: true },
  )
}

function renderCharts() {
  if (!payload.value) return
  const labels = monthlyKpiRows.value.map((x) => x.month_label)
  const wip = monthlyKpiRows.value.map((x) => toSen(x.closing_wip_qty))
  const prod = monthlyKpiRows.value.map((x) => toSen(x.closing_product_qty))
  const totals = monthlyKpiRows.value.map((x) => toSen(x.closing_total_qty))

  invChart = bindChart(invChart, invChartRef.value)
  if (invChart) {
    invChart.setOption(
      {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            crossStyle: { color: '#94a3b8' },
            lineStyle: { color: '#94a3b8', type: 'dashed' },
          },
          backgroundColor: 'rgba(255, 255, 255, 0.97)',
          borderColor: 'rgba(59, 130, 246, 0.45)',
          borderWidth: 1,
          padding: [10, 14],
          textStyle: { color: '#0f172a', fontSize: 12 },
          extraCssText: 'box-shadow: 0 10px 28px rgba(15, 23, 42, 0.14); border-radius: 12px;',
          formatter: (params: unknown) => {
            const rows = (Array.isArray(params) ? params : [params]) as Array<{
              axisValueLabel?: string
              marker?: string
              seriesName?: string
              value?: number
              dataIndex?: number
            }>
            if (!rows.length) return ''
            const idx = rows[0]?.dataIndex ?? 0
            const head = `<div style="font-weight:800;margin-bottom:6px;color:#1e293b">${rows[0]?.axisValueLabel || ''}</div>`
            const body = rows
              .map((r) => {
                const n = Number(r.value ?? 0)
                const text = `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })} 千本`
                return (
                  `<div style="display:flex;justify-content:space-between;gap:16px;margin:3px 0">` +
                  `<span>${r.marker || ''} ${r.seriesName || ''}</span>` +
                  `<b style="font-variant-numeric:tabular-nums">${chartTipValue(text, n)}</b></div>`
                )
              })
              .join('')
            const totalN = Number(totals[idx] ?? 0)
            const totalText = `${totalN.toLocaleString(undefined, { maximumFractionDigits: 1 })} 千本`
            const total =
              `<div style="margin-top:6px;padding-top:6px;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;gap:16px">` +
              `<span style="color:#64748b">合計</span>` +
              `<b>${chartTipValue(totalText, totalN)}</b></div>`
            return head + body + total
          },
        },
        legend: {
          data: ['仕掛品', '製品', '合計'],
          top: 0,
          itemWidth: 16,
          itemHeight: 8,
          icon: 'roundRect',
          textStyle: { color: '#475569', fontWeight: 700, fontSize: 12 },
        },
        grid: { left: 40, right: 44, top: 56, bottom: 16, containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: true,
          data: labels,
          axisLine: { lineStyle: { color: '#e2e8f0' } },
          axisTick: { show: false },
          axisLabel: { color: '#64748b', fontWeight: 700, fontSize: 12, margin: 10 },
        },
        yAxis: {
          type: 'value',
          min: 200,
          max: 1200,
          interval: 200,
          name: '千本',
          nameTextStyle: { color: '#94a3b8', fontWeight: 600 },
          axisLabel: {
            color: (v: number) => chartLabelColor(v, '#94a3b8'),
            formatter: (v: number) =>
              Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 }),
          },
          splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.22)' } },
        },
        animationDuration: 900,
        animationEasing: 'cubicOut',
        series: [
          {
            name: '仕掛品',
            type: 'line',
            smooth: 0.35,
            symbol: 'circle',
            symbolSize: 9,
            clip: false,
            data: wip.map((v) => {
              const n = Number(v)
              const neg = n < 0
              return {
                value: n,
                label: {
                  position: 'top' as const,
                  color: chartLabelColor(n, '#1d4ed8'),
                },
                itemStyle: neg ? { color: CHART_NEG_COLOR, borderColor: '#fff', borderWidth: 2 } : undefined,
              }
            }),
            lineStyle: {
              width: 3,
              color: '#2563eb',
              shadowColor: 'rgba(37, 99, 235, 0.35)',
              shadowBlur: 8,
              shadowOffsetY: 3,
            },
            itemStyle: { color: '#2563eb', borderColor: '#fff', borderWidth: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59, 130, 246, 0.22)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.02)' },
              ]),
            },
            label: {
              show: true,
              position: 'top',
              distance: 6,
              color: '#1d4ed8',
              fontSize: 11,
              fontWeight: 800,
              formatter: ({ value }: { value: number }) =>
                Number(value) !== 0 && !Number.isNaN(Number(value))
                  ? Number(value).toLocaleString()
                  : '',
            },
            labelLayout: { hideOverlap: true },
            emphasis: { focus: 'series', scale: 1.3 },
          },
          {
            name: '製品',
            type: 'line',
            smooth: 0.35,
            symbol: 'diamond',
            symbolSize: 10,
            clip: false,
            data: prod.map((v) => {
              const n = Number(v)
              const neg = n < 0
              return {
                value: n,
                label: {
                  position: 'bottom' as const,
                  color: chartLabelColor(n, '#0f766e'),
                },
                itemStyle: neg ? { color: CHART_NEG_COLOR, borderColor: '#fff', borderWidth: 2 } : undefined,
              }
            }),
            lineStyle: {
              width: 3,
              color: '#0d9488',
              shadowColor: 'rgba(13, 148, 136, 0.35)',
              shadowBlur: 8,
              shadowOffsetY: 3,
            },
            itemStyle: { color: '#0d9488', borderColor: '#fff', borderWidth: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(20, 184, 166, 0.2)' },
                { offset: 1, color: 'rgba(20, 184, 166, 0.02)' },
              ]),
            },
            label: {
              show: true,
              position: 'bottom',
              distance: 6,
              color: '#0f766e',
              fontSize: 11,
              fontWeight: 800,
              formatter: ({ value }: { value: number }) =>
                Number(value) !== 0 && !Number.isNaN(Number(value))
                  ? Number(value).toLocaleString()
                  : '',
            },
            labelLayout: { hideOverlap: true },
            emphasis: { focus: 'series', scale: 1.3 },
          },
          {
            name: '合計',
            type: 'line',
            smooth: 0.35,
            symbol: 'emptyCircle',
            symbolSize: 8,
            clip: false,
            data: totals.map((v) => {
              const n = Number(v)
              const neg = n < 0
              return {
                value: n,
                label: {
                  position: 'top' as const,
                  color: chartLabelColor(n, '#4338ca'),
                },
                itemStyle: neg ? { color: CHART_NEG_COLOR, borderColor: '#fff', borderWidth: 2 } : undefined,
              }
            }),
            lineStyle: {
              width: 2.5,
              type: 'dashed',
              color: '#6366f1',
            },
            itemStyle: { color: '#6366f1', borderColor: '#fff', borderWidth: 2 },
            label: {
              show: true,
              position: 'top',
              distance: 14,
              color: '#4338ca',
              fontSize: 11,
              fontWeight: 800,
              formatter: ({ value }: { value: number }) =>
                Number(value) !== 0 && !Number.isNaN(Number(value))
                  ? `計 ${Number(value).toLocaleString()}`
                  : '',
            },
            labelLayout: { hideOverlap: true },
            emphasis: { focus: 'series', scale: 1.25 },
          },
        ],
      },
      { notMerge: true },
    )
  }

  const kpiLabels = monthlyKpiRows.value.map((m) => m.month_label)
  const fmtLineSen = (v: number) =>
    Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 })
  const fmtLinePct = (v: number) => `${v.toFixed(2)}%`

  wipChart = bindChart(wipChart, wipChartRef.value)
  if (wipChart) {
    renderMiniLine(
      wipChart,
      '期末仕掛品',
      kpiLabels,
      monthlyKpiRows.value.map((m) => toSen(m.closing_wip_qty)),
      {
        line: '#2563eb',
        areaTop: 'rgba(59, 130, 246, 0.28)',
        areaBottom: 'rgba(59, 130, 246, 0.02)',
        label: '#1d4ed8',
      },
      fmtLineSen,
    )
  }
  productChart = bindChart(productChart, productChartRef.value)
  if (productChart) {
    renderMiniLine(
      productChart,
      '期末製品',
      kpiLabels,
      monthlyKpiRows.value.map((m) => toSen(m.closing_product_qty)),
      {
        line: '#0d9488',
        areaTop: 'rgba(20, 184, 166, 0.26)',
        areaBottom: 'rgba(20, 184, 166, 0.02)',
        label: '#0f766e',
      },
      fmtLineSen,
      {
        markLineY: RPT_TARGET_CLOSING_PRODUCT_SEN,
        markLineLabel: `目安 ${RPT_TARGET_CLOSING_PRODUCT_SEN}`,
        targetTone: 'teal',
      },
    )
  }
  scrapRateChart = bindChart(scrapRateChart, scrapRateChartRef.value)
  if (scrapRateChart) {
    renderMiniLine(
      scrapRateChart,
      '廃棄率',
      kpiLabels,
      monthlyKpiRows.value.map((m) => m.quality_loss_rate_percent ?? null),
      {
        line: '#d97706',
        areaTop: 'rgba(251, 191, 36, 0.3)',
        areaBottom: 'rgba(251, 191, 36, 0.02)',
        label: '#b45309',
      },
      fmtLinePct,
      {
        markLineY: RPT_TARGET_SCRAP_RATE_PERCENT,
        markLineLabel: `目安 ${RPT_TARGET_SCRAP_RATE_PERCENT}%`,
        targetTone: 'amber',
      },
    )
  }
  scrapQtyChart = bindChart(scrapQtyChart, scrapQtyChartRef.value)
  if (scrapQtyChart) {
    renderMiniLine(
      scrapQtyChart,
      '廃棄本数',
      kpiLabels,
      monthlyKpiRows.value.map((m) => toSen(m.loss_qty ?? 0)),
      {
        line: '#ea580c',
        areaTop: 'rgba(249, 115, 22, 0.28)',
        areaBottom: 'rgba(249, 115, 22, 0.02)',
        label: '#c2410c',
      },
      fmtLineSen,
    )
  }
  matchChart = bindChart(matchChart, matchChartRef.value)
  if (matchChart) {
    renderMiniLine(
      matchChart,
      '棚卸一致率',
      kpiLabels,
      monthlyKpiRows.value.map((m) => m.match_rate),
      {
        line: '#059669',
        areaTop: 'rgba(16, 185, 129, 0.28)',
        areaBottom: 'rgba(16, 185, 129, 0.02)',
        label: '#047857',
      },
      fmtLinePct,
      { markLineY: 95, markLineLabel: '目安 95%', targetTone: 'emerald' },
    )
  }

  const bulkCats = bulkCategoryRows.value
  const renderBulkCategoryChart = (chart: ECharts) => {
    chart.setOption(
      {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          borderColor: 'rgba(148, 163, 184, 0.45)',
          textStyle: { color: '#0f172a', fontSize: 12 },
          formatter: (params: unknown) => {
            const row = (Array.isArray(params) ? params[0] : params) as { dataIndex?: number }
            const hit = bulkCats[row?.dataIndex ?? -1]
            if (!hit) return ''
            return `${hit.name}<br/>本数 ${hit.quantity.toLocaleString()}<br/>件数 ${hit.count.toLocaleString()}`
          },
        },
        grid: {
          left: 8,
          right: 12,
          top: 28,
          bottom: 8,
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: bulkCats.map((c) => c.name),
          axisTick: { show: false },
          axisLine: { lineStyle: { color: '#cbd5e1' } },
          axisLabel: { color: '#475569', fontWeight: 700, fontSize: 11 },
        },
        yAxis: {
          type: 'value',
          name: '本',
          nameTextStyle: { color: '#94a3b8' },
          axisLabel: { color: '#94a3b8' },
          splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.28)' } },
        },
        series: [
          {
            name: '本数',
            type: 'bar',
            barMaxWidth: 52,
            data: bulkCats.map((c) => ({
              value: c.quantity,
              itemStyle: {
                borderRadius: [6, 6, 2, 2],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: c.color.top },
                  { offset: 1, color: c.color.bottom },
                ]),
              },
              label: { color: c.color.label },
            })),
            label: {
              show: true,
              position: 'top',
              fontSize: 11,
              fontWeight: 800,
              formatter: ({ dataIndex }: { dataIndex: number }) => {
                const hit = bulkCats[dataIndex]
                if (!hit || hit.quantity <= 0) return ''
                return `${hit.quantity.toLocaleString()}本 / ${hit.count}件`
              },
            },
          },
        ],
      },
      { notMerge: true },
    )
  }

  // 差異：工程別（期間平均・千本）＋差異率（右軸）
  const processRows = diffByProcessAvg.value
  const processLabels = processRows.map((r) => r.process_name || r.process_cd)
  const theoVals = processRows.map((r) => toSen(r.theoretical_qty))
  const stockVals = processRows.map((r) => toSen(r.stocktake_qty))
  const diffVals = processRows.map((r) => toSen(r.diff_qty))
  const diffRateVals = processRows.map((r) =>
    r.diff_rate == null || Number.isNaN(Number(r.diff_rate)) ? null : Number(r.diff_rate),
  )

  diffChart = bindChart(diffChart, diffChartRef.value)
  if (diffChart) {
    diffChart.setOption(
      {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.06)' } },
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          borderColor: 'rgba(165, 180, 252, 0.6)',
          borderWidth: 1,
          padding: [8, 12],
          textStyle: { color: '#0f172a', fontSize: 12 },
          extraCssText: 'box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14); border-radius: 10px;',
          formatter: (params: unknown) => {
            const rows = (Array.isArray(params) ? params : [params]) as Array<{
              axisValueLabel?: string
              marker?: string
              seriesName?: string
              value?: number
              seriesType?: string
            }>
            if (!rows.length) return ''
            const head = `<div style="font-weight:800;margin-bottom:6px">${rows[0]?.axisValueLabel || ''}</div>`
            const body = rows
              .map((r) => {
                const isRate = String(r.seriesName || '').includes('差異率')
                const raw = r.value
                const val =
                  raw == null
                    ? '—'
                    : isRate
                      ? `${Number(raw).toFixed(2)}%`
                      : `${Number(raw).toLocaleString(undefined, { maximumFractionDigits: 1 })} 千本`
                return `<div style="display:flex;justify-content:space-between;gap:14px;margin:2px 0"><span>${r.marker || ''} ${r.seriesName || ''}</span><b>${chartTipValue(val, raw)}</b></div>`
              })
              .join('')
            return head + body
          },
        },
        legend: {
          data: ['理論在庫(平均)', '棚卸在庫(平均)', '差異(平均)', '差異率'],
          top: 0,
          itemWidth: 14,
          itemHeight: 9,
          icon: 'roundRect',
          textStyle: { color: '#475569', fontWeight: 600 },
        },
        grid: { left: 56, right: 52, top: 56, bottom: 30 },
        xAxis: {
          type: 'category',
          data: processLabels,
          axisLine: { lineStyle: { color: '#cbd5e1' } },
          axisTick: { show: false },
          axisLabel: { color: '#475569', fontWeight: 700, fontSize: 12 },
        },
        yAxis: [
          {
            type: 'value',
            name: '千本（月平均）',
            min: -100,
            max: 600,
            interval: 100,
            nameTextStyle: { color: '#94a3b8' },
            axisLabel: {
              color: (v: number) => chartLabelColor(v, '#94a3b8'),
              formatter: (v: number) =>
                Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 }),
            },
            splitLine: { lineStyle: { type: 'dashed', color: 'rgba(148, 163, 184, 0.25)' } },
          },
          {
            type: 'value',
            name: '差異率%',
            min: -180,
            max: 30,
            interval: 30,
            nameTextStyle: { color: '#7c3aed', fontWeight: 700 },
            axisLabel: {
              color: (v: number) => chartLabelColor(v, '#7c3aed'),
              fontWeight: 700,
              formatter: (v: number) => `${v}`,
            },
            splitLine: { show: false },
          },
        ],
        animationDuration: 900,
        animationEasing: 'elasticOut',
        series: [
          {
            name: '理論在庫(平均)',
            type: 'bar',
            barMaxWidth: 28,
            data: theoVals.map((v) => ({
              value: v,
              label: { color: chartLabelColor(v, '#1d4ed8') },
            })),
            itemStyle: {
              borderRadius: [4, 4, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#93c5fd' },
                { offset: 1, color: '#2563eb' },
              ]),
            },
            label: {
              show: true,
              position: 'top',
              fontSize: 10,
              fontWeight: 700,
              color: '#1d4ed8',
              formatter: ({ value }: { value: number }) =>
                Number(value) ? Number(value).toLocaleString() : '',
            },
          },
          {
            name: '棚卸在庫(平均)',
            type: 'bar',
            barMaxWidth: 28,
            data: stockVals.map((v) => ({
              value: v,
              label: { color: chartLabelColor(v, '#0f766e') },
            })),
            itemStyle: {
              borderRadius: [4, 4, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#5eead4' },
                { offset: 1, color: '#0d9488' },
              ]),
            },
            label: {
              show: true,
              position: 'top',
              fontSize: 10,
              fontWeight: 700,
              color: '#0f766e',
              formatter: ({ value }: { value: number }) =>
                Number(value) ? Number(value).toLocaleString() : '',
            },
          },
          {
            name: '差異(平均)',
            type: 'bar',
            barMaxWidth: 28,
            data: diffVals.map((v) => ({
              value: v,
              label: {
                position: v < 0 ? ('bottom' as const) : ('top' as const),
                color: chartLabelColor(v, '#6d28d9'),
              },
              itemStyle: {
                borderRadius: v < 0 ? [0, 0, 4, 4] : [4, 4, 0, 0],
                color: new echarts.graphic.LinearGradient(0, v < 0 ? 1 : 0, 0, v < 0 ? 0 : 1, [
                  { offset: 0, color: v < 0 ? '#fca5a5' : '#c4b5fd' },
                  { offset: 1, color: v < 0 ? '#dc2626' : '#7c3aed' },
                ]),
              },
            })),
            label: {
              show: true,
              fontSize: 10,
              fontWeight: 800,
              color: '#6d28d9',
              formatter: ({ value }: { value: number }) =>
                Number(value) === 0 ? '' : Number(value).toLocaleString(),
            },
          },
          {
            name: '差異率',
            type: 'line',
            yAxisIndex: 1,
            smooth: 0.2,
            symbol: 'circle',
            symbolSize: 9,
            z: 10,
            data: diffRateVals.map((v) => {
              if (v == null || Number.isNaN(Number(v))) return null
              const n = Number(v)
              const neg = n < 0
              return {
                value: n,
                label: {
                  position: 'top' as const,
                  color: chartLabelColor(n, '#6d28d9'),
                },
                itemStyle: neg
                  ? { color: CHART_NEG_COLOR, borderColor: '#fff', borderWidth: 2 }
                  : undefined,
              }
            }),
            lineStyle: { width: 2.5, color: '#7c3aed' },
            itemStyle: { color: '#7c3aed', borderColor: '#fff', borderWidth: 2 },
            label: {
              show: true,
              position: 'top',
              distance: 8,
              fontSize: 12,
              fontWeight: 800,
              color: '#6d28d9',
              formatter: ({ value }: { value: number | null }) =>
                value == null || Number.isNaN(Number(value))
                  ? ''
                  : `${Number(value).toFixed(1)}%`,
            },
          },
        ],
      },
      { notMerge: true },
    )
  }

  bulkDetailChart = bindChart(bulkDetailChart, bulkDetailChartRef.value)
  if (bulkDetailChart) renderBulkCategoryChart(bulkDetailChart)
  requestAnimationFrame(() => onResize())
}

async function onGenerate() {
  loading.value = true
  try {
    const data = await inventoryReportApi.generate(fiscalYear.value, quarter.value)
    payload.value = data
    savedId.value = null
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
    savedId.value = detail.id
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

async function onDeleteSaved(item: SavedReportSummary) {
  if (!item?.id) return
  try {
    await ElMessageBox.confirm(
      `「${item.label}」（${item.status === 'final' ? '確定' : '下書き'}）を削除しますか？\nこの操作は取り消せません。`,
      '保存レポート削除',
      {
        type: 'warning',
        confirmButtonText: '削除する',
        cancelButtonText: 'キャンセル',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }
  deletingId.value = item.id
  try {
    await inventoryReportApi.remove(item.id)
    if (savedId.value === item.id) {
      savedId.value = null
      payload.value = null
    }
    await loadSavedList()
    ElMessage.success('保存レポートを削除しました')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '削除に失敗しました'
    ElMessage.error(msg)
  } finally {
    deletingId.value = null
  }
}

function chartDataUrl(chart: ECharts | null, pixelRatio = 2): string | undefined {
  if (!chart) return undefined
  try {
    return chart.getDataURL({ type: 'png', pixelRatio, backgroundColor: '#ffffff' })
  } catch {
    return undefined
  }
}

/** PPT 用：option 内の fontSize を大きくする（画面表示は後で renderCharts で戻す） */
function boostOptionFontsForPpt(value: unknown, add = 8): unknown {
  if (Array.isArray(value)) return value.map((v) => boostOptionFontsForPpt(v, add))
  if (!value || typeof value !== 'object') return value
  const src = value as Record<string, unknown>
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(src)) {
    if (k === 'fontSize' && typeof v === 'number') {
      out[k] = Math.max(12, Math.round(v + add))
    } else if (
      (k === 'itemWidth' || k === 'itemHeight' || k === 'symbolSize') &&
      typeof v === 'number'
    ) {
      out[k] = Math.round(v * 1.35)
    } else if (k === 'barMaxWidth' && typeof v === 'number') {
      // 差異など棒グラフ：PPT では柱幅を約 +96%（1.4×1.4）
      out[k] = Math.round(v * 1.96)
    } else {
      out[k] = boostOptionFontsForPpt(v, add)
    }
  }
  // 目安バッジなど graphic group / rect も拡大
  if (src.type === 'group' && typeof src.width === 'number' && typeof src.height === 'number') {
    out.width = Math.round(Number(src.width) * 1.5)
    out.height = Math.round(Number(src.height) * 1.4)
  }
  if (src.type === 'rect' && src.shape && typeof src.shape === 'object') {
    const sh = src.shape as Record<string, unknown>
    out.shape = {
      ...sh,
      width: typeof sh.width === 'number' ? Math.round(Number(sh.width) * 1.5) : sh.width,
      height: typeof sh.height === 'number' ? Math.round(Number(sh.height) * 1.4) : sh.height,
      r: typeof sh.r === 'number' ? Math.round(Number(sh.r) * 1.4) : sh.r,
    }
  }
  return out
}

function applyPptChartFontBoost(chart: ECharts) {
  const boosted = boostOptionFontsForPpt(chart.getOption(), 8) as Record<string, unknown>
  chart.setOption(boosted, { notMerge: true })
  // getOption に fontSize が無い箇所（凡例・軸）も明示的に大きくする
  // 左右グリッドを詰めてプロット領域を広げ、PPT 上の上下余白を減らす
  // フォントは PPT 本文と同じ游ゴシック系
  const pptFont = '"游ゴシック", "Yu Gothic", "YuGothic", sans-serif'
  chart.setOption(
    {
      animation: false,
      textStyle: { fontSize: 16, fontFamily: pptFont },
      legend: {
        textStyle: { fontSize: 18, fontWeight: 700, fontFamily: pptFont },
        top: 0,
        itemGap: 10,
      },
      grid: {
        left: 18,
        right: 22,
        top: 36,
        bottom: 12,
        containLabel: true,
      },
      xAxis: {
        axisLabel: { fontSize: 16, fontWeight: 700, fontFamily: pptFont },
        nameTextStyle: { fontSize: 14, fontFamily: pptFont },
      },
      yAxis: {
        axisLabel: { fontSize: 15, fontFamily: pptFont },
        nameTextStyle: { fontSize: 14, fontFamily: pptFont },
      },
    },
    { notMerge: false },
  )
  // 全 series のラベルを拡大（merge で各 series に適用）
  const seriesCount = Array.isArray((boosted as { series?: unknown[] }).series)
    ? ((boosted as { series: unknown[] }).series.length)
    : 1
  chart.setOption(
    {
      series: Array.from({ length: seriesCount }, () => ({
        label: { fontSize: 15, fontWeight: 800, fontFamily: pptFont },
      })),
    },
    { notMerge: false },
  )
}

function collectChartImages(opts?: { forPpt?: boolean }): InventoryReportChartImages {
  const forPpt = Boolean(opts?.forPpt)
  const charts = [
    invChart,
    wipChart,
    productChart,
    scrapRateChart,
    scrapQtyChart,
    matchChart,
    bulkDetailChart,
    diffChart,
  ]
  if (forPpt) {
    for (const c of charts) {
      if (c && !c.isDisposed()) applyPptChartFontBoost(c)
    }
  }
  try {
    const pr = forPpt ? 3 : 2
    return {
      inventory: chartDataUrl(invChart, pr),
      wip: chartDataUrl(wipChart, pr),
      product: chartDataUrl(productChart, pr),
      scrapRate: chartDataUrl(scrapRateChart, pr),
      scrapQty: chartDataUrl(scrapQtyChart, pr),
      match: chartDataUrl(matchChart, pr),
      bulkDetail: chartDataUrl(bulkDetailChart, pr),
      diff: chartDataUrl(diffChart, pr),
    }
  } finally {
    if (forPpt) renderCharts()
  }
}

function buildExportInput(opts?: { forPpt?: boolean }): InventoryReportExportInput | null {
  if (!payload.value) return null
  return {
    payload: payload.value,
    monthlyKpis: monthlyKpiRows.value,
    diffByProcessAvg: diffByProcessAvg.value,
    bulkCategories: bulkCategoryRows.value.map((r) => ({
      name: r.name,
      count: r.count,
      quantity: r.quantity,
    })),
    chartImages: collectChartImages(opts),
  }
}

async function onExportExcel() {
  const input = buildExportInput()
  if (!input) {
    ElMessage.warning('先にレポートを生成してください')
    return
  }
  exportingExcel.value = true
  try {
    await exportInventoryReportExcel(input)
    ElMessage.success('Excelを出力しました')
  } catch (error) {
    console.error('Excel出力に失敗:', error)
    ElMessage.error('Excel出力に失敗しました')
  } finally {
    exportingExcel.value = false
  }
}

async function onExportPdf() {
  const input = buildExportInput()
  if (!input) {
    ElMessage.warning('先にレポートを生成してください')
    return
  }
  exportingPdf.value = true
  try {
    await exportInventoryReportPdf(input)
    ElMessage.success('PDFを出力しました')
  } catch (error) {
    console.error('PDF出力に失敗:', error)
    const msg = error instanceof Error ? error.message : 'PDF出力に失敗しました'
    ElMessage.error(msg)
  } finally {
    exportingPdf.value = false
  }
}

async function onPrint() {
  const input = buildExportInput()
  if (!input) {
    ElMessage.warning('先にレポートを生成してください')
    return
  }
  printing.value = true
  try {
    await printInventoryReport(input)
  } catch (error) {
    console.error('印刷に失敗:', error)
    const msg = error instanceof Error ? error.message : '印刷に失敗しました'
    ElMessage.error(msg)
  } finally {
    printing.value = false
  }
}

async function onExportPpt() {
  if (!payload.value) {
    ElMessage.warning('先にレポートを生成してください')
    return
  }
  exportingPpt.value = true
  try {
    await nextTick()
    const input = buildExportInput({ forPpt: true })
    if (!input) {
      ElMessage.warning('先にレポートを生成してください')
      return
    }
    await inventoryReportApi.downloadPptx({
      payload: input.payload,
      monthly_kpis: input.monthlyKpis,
      diff_by_process_avg: input.diffByProcessAvg as unknown as Array<Record<string, unknown>>,
      bulk_categories: input.bulkCategories,
      charts: input.chartImages as Partial<Record<string, string | undefined>> | undefined,
    })
    ElMessage.success('PPTを出力しました')
  } catch (error) {
    console.error('PPT出力に失敗:', error)
    const msg = error instanceof Error ? error.message : 'PPT出力に失敗しました'
    ElMessage.error(msg)
  } finally {
    exportingPpt.value = false
  }
}

function onResize() {
  invChart?.resize()
  wipChart?.resize()
  productChart?.resize()
  scrapRateChart?.resize()
  scrapQtyChart?.resize()
  matchChart?.resize()
  diffChart?.resize()
  bulkDetailChart?.resize()
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
  --rpt-shadow: 0 1px 0 rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.18);
  --rpt-shadow-hover: 0 1px 0 rgba(15, 23, 42, 0.05), 0 12px 24px -12px rgba(15, 23, 42, 0.22);
  position: relative;
  min-height: 100%;
  padding: 12px;
  box-sizing: border-box;
  color: #0f172a;
  font-family: 'Yu Gothic UI', 'Yu Gothic', 'Hiragino Sans', 'Noto Sans JP', Meiryo, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  background: linear-gradient(165deg, #eef2ff 0%, #f8fafc 42%, #ecfeff 100%);
}

/* ぼかし・文字影は使わない（視認性優先） */
.rpt-page,
.rpt-page :deep(*),
.rpt-page::before,
.rpt-page::after {
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
  text-shadow: none !important;
}

.animate-in {
  animation: rpt-fade-up 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0ms);
}

@keyframes rpt-fade-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rpt-card-in {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ── Hero toolbar（月受注管理と同系） ── */
.page-toolbar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  background: linear-gradient(125deg, #4f46e5 0%, #6d28d9 38%, #9333ea 72%, #a855f7 100%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  padding: 14px 18px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow:
    0 18px 36px -18px rgba(76, 29, 149, 0.6),
    0 4px 12px -6px rgba(79, 70, 229, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.page-toolbar-glow {
  position: absolute;
  inset: 0 auto auto 0;
  width: 42%;
  height: 100%;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.16), transparent 100%);
  pointer-events: none;
}
.toolbar-left {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  min-width: 0;
}
.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.toolbar-icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.38);
  box-shadow:
    0 6px 14px -6px rgba(15, 23, 42, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -2px 0 rgba(15, 23, 42, 0.12);
}
.toolbar-icon {
  font-size: 20px;
  color: #fff;
}
.toolbar-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.toolbar-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #ffffff;
}
.toolbar-desc {
  margin: 2px 0 0;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #e0e7ff;
}
.toolbar-right {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.rpt-help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  cursor: pointer;
  transition: background 0.16s ease, transform 0.16s ease;
}
.rpt-help-btn:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: scale(1.06);
}

/* ── 白地ピルボタン（月受注と同系） ── */
.tb-btn {
  --tb-h: 32px;
  --k-rgb: 79 70 229;
  --k-fg: #4338ca;
  --k-fg-h: #3730a3;
  --k-bd: #c7d2fe;
  --k-bd-h: #a5b4fc;
  --k-tint: #e0e7ff;
  --k-tint-h: #c7d2fe;
  --k-ico: #6366f1;
  --el-button-text-color: var(--k-fg);
  --el-button-hover-text-color: var(--k-fg-h);
  --el-button-active-text-color: var(--k-fg-h);
  --el-button-border-color: var(--k-bd);
  --el-button-hover-border-color: var(--k-bd-h);
  --el-button-active-border-color: var(--k-bd-h);
  height: var(--tb-h);
  min-height: var(--tb-h);
  padding: 0 14px 0 11px;
  border-radius: 999px;
  border: 1px solid var(--k-bd);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--k-fg);
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}
.tb-btn :deep(.el-icon) {
  margin-right: 5px;
  font-size: 15px;
  color: var(--k-ico);
}
.tb-btn:hover,
.tb-btn:focus {
  border-color: var(--k-bd-h);
  color: var(--k-fg-h);
  background: linear-gradient(135deg, #ffffff 0%, var(--k-tint) 45%, var(--k-tint-h) 100%);
}
.tb-btn:disabled,
.tb-btn.is-disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.tb-btn-blue {
  --k-rgb: 37 99 235;
  --k-fg: #1d4ed8;
  --k-fg-h: #1e40af;
  --k-bd: #93c5fd;
  --k-bd-h: #60a5fa;
  --k-tint: #dbeafe;
  --k-tint-h: #bfdbfe;
  --k-ico: #3b82f6;
}
.tb-btn-teal {
  --k-rgb: 13 148 136;
  --k-fg: #0f766e;
  --k-fg-h: #115e59;
  --k-bd: #5eead4;
  --k-bd-h: #2dd4bf;
  --k-tint: #ccfbf1;
  --k-tint-h: #99f6e4;
  --k-ico: #14b8a6;
}
.tb-btn-amber {
  --k-rgb: 217 119 6;
  --k-fg: #b45309;
  --k-fg-h: #92400e;
  --k-bd: #fcd34d;
  --k-bd-h: #fbbf24;
  --k-tint: #fef3c7;
  --k-tint-h: #fde68a;
  --k-ico: #f59e0b;
}
.tb-btn-indigo {
  --k-rgb: 79 70 229;
  --k-fg: #4338ca;
  --k-fg-h: #3730a3;
  --k-bd: #a5b4fc;
  --k-bd-h: #818cf8;
  --k-tint: #e0e7ff;
  --k-tint-h: #c7d2fe;
  --k-ico: #6366f1;
}
.tb-btn-green {
  --k-rgb: 5 150 105;
  --k-fg: #047857;
  --k-fg-h: #065f46;
  --k-bd: #6ee7b7;
  --k-bd-h: #34d399;
  --k-tint: #d1fae5;
  --k-tint-h: #a7f3d0;
  --k-ico: #10b981;
}
.tb-btn-slate {
  --k-rgb: 100 116 139;
  --k-fg: #475569;
  --k-fg-h: #334155;
  --k-bd: #cbd5e1;
  --k-bd-h: #94a3b8;
  --k-tint: #f1f5f9;
  --k-tint-h: #e2e8f0;
  --k-ico: #64748b;
}
.tb-btn-rose {
  --k-rgb: 225 29 72;
  --k-fg: #be123c;
  --k-fg-h: #9f1239;
  --k-bd: #fda4af;
  --k-bd-h: #fb7185;
  --k-tint: #ffe4e6;
  --k-tint-h: #fecdd3;
  --k-ico: #f43f5e;
}
.tb-btn-violet {
  --k-rgb: 124 58 237;
  --k-fg: #6d28d9;
  --k-fg-h: #5b21b6;
  --k-bd: #c4b5fd;
  --k-bd-h: #a78bfa;
  --k-tint: #ede9fe;
  --k-tint-h: #ddd6fe;
  --k-ico: #8b5cf6;
}

.rpt-page.ir-modern.pb-std.pb-std .toolbar-actions .tb-btn.tb-btn.el-button.el-button:not(.is-link):not(.is-text):not(.is-disabled) {
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(15, 23, 42, 0.35) !important;
}
.rpt-page.ir-modern.pb-std.pb-std .toolbar-actions .tb-btn.tb-btn.el-button.el-button:not(.is-link):not(.is-text):not(.is-disabled):hover {
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.16),
    0 4px 8px -2px rgba(15, 23, 42, 0.3),
    0 10px 22px -8px rgb(var(--k-rgb) / 0.75) !important;
}

/* ── Filter bar ── */
.filter-bar {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  border-radius: 12px;
  border: 1px solid #c7d2fe;
  padding: 10px 12px 10px 16px;
  margin-bottom: 10px;
  box-shadow: var(--rpt-shadow);
  animation: rpt-fade-up 0.35s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.filter-bar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #4f46e5;
}
.filter-inline {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.fi-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.fi-icon {
  width: 26px;
  height: 26px;
  padding: 5px;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(67, 56, 202, 0.3),
    0 4px 10px -4px rgba(99, 102, 241, 0.55);
}
.fi-year {
  width: 120px;
}
.fi-sep {
  width: 1px;
  height: 22px;
  background: #e0e7ff;
}
.filter-bar :deep(.el-select__wrapper) {
  border-radius: 9px;
  background-color: #f8fafc;
  box-shadow:
    0 0 0 1px #dfe3f0 inset,
    0 1px 2px rgba(15, 23, 42, 0.05);
}
.filter-bar :deep(.el-select__wrapper:hover) {
  background-color: #fff;
  box-shadow:
    0 0 0 1px #a5b4fc inset,
    0 4px 10px -4px rgba(99, 102, 241, 0.3);
}
.filter-bar :deep(.el-select__wrapper.is-focused) {
  background-color: #fff;
  box-shadow:
    0 0 0 1px #6366f1 inset,
    0 0 0 3px rgba(99, 102, 241, 0.16);
}

:deep(.rpt-period-type .el-radio-button__inner),
:deep(.rpt-quarter .el-radio-button__inner) {
  font-weight: 700;
  border-color: #c7d2fe;
  background: linear-gradient(180deg, #ffffff, #f5f3ff);
  color: #475569;
  transition: all 0.16s ease;
}
:deep(.rpt-period-type .el-radio-button:first-child .el-radio-button__inner),
:deep(.rpt-quarter .el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 9px 0 0 9px;
}
:deep(.rpt-period-type .el-radio-button:last-child .el-radio-button__inner),
:deep(.rpt-quarter .el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 9px 9px 0;
}
:deep(.rpt-period-type .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(145deg, #818cf8, #6366f1);
  border-color: transparent;
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 4px 12px rgba(99, 102, 241, 0.4);
}
:deep(.rpt-quarter .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(145deg, #a78bfa, #7c3aed);
  border-color: transparent;
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 4px 12px rgba(124, 58, 237, 0.4);
}

.rpt-saved-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 10px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e0e7ff;
  box-shadow: var(--rpt-shadow);
}
.rpt-saved-bar__label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}
.rpt-saved-bar__label em {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  font-style: normal;
  font-size: 11px;
  font-weight: 800;
  color: #4338ca;
  background: #e0e7ff;
  border: 1px solid #c7d2fe;
}
.rpt-saved-bar__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.rpt-saved-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 2px 4px 2px 4px;
  font-size: 12px;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}
.rpt-saved-chip__main {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 3px 6px 3px 8px;
  font: inherit;
  color: inherit;
  cursor: pointer;
  border-radius: 999px;
}
.rpt-saved-chip__text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}
.rpt-saved-chip__text small {
  font-size: 10.5px;
  font-weight: 700;
  opacity: 0.78;
  letter-spacing: 0.02em;
}
.rpt-saved-chip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.rpt-saved-chip__del {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-right: 2px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition:
    background 0.16s ease,
    color 0.16s ease,
    transform 0.16s ease;
}
.rpt-saved-chip__del:hover:not(:disabled) {
  background: #fee2e2;
  color: #dc2626;
  transform: scale(1.06);
}
.rpt-saved-chip__del:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.rpt-saved-chip.is-final {
  color: #047857;
  background: linear-gradient(180deg, #ecfdf5, #d1fae5);
  border-color: rgba(16, 185, 129, 0.28);
}
.rpt-saved-chip.is-final .rpt-saved-chip__dot {
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}
.rpt-saved-chip.is-draft {
  color: #334155;
  background: linear-gradient(180deg, #f8fafc, #e2e8f0);
  border-color: rgba(100, 116, 139, 0.22);
}
.rpt-saved-chip.is-draft .rpt-saved-chip__dot {
  background: #94a3b8;
}
.rpt-saved-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.1);
}
.rpt-saved-chip.is-active.is-final {
  border-color: #10b981;
  box-shadow:
    0 0 0 2px rgba(16, 185, 129, 0.18),
    0 6px 16px rgba(16, 185, 129, 0.18);
}
.rpt-saved-chip.is-active.is-draft {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff, #e0e7ff);
  color: #1d4ed8;
  box-shadow:
    0 0 0 2px rgba(59, 130, 246, 0.16),
    0 6px 16px rgba(59, 130, 246, 0.16);
}
.rpt-saved-chip.is-active.is-draft .rpt-saved-chip__dot {
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}

.rpt-chip-enter-active,
.rpt-chip-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}
.rpt-chip-enter-from,
.rpt-chip-leave-to {
  opacity: 0;
  transform: scale(0.94);
}

.rpt-empty {
  margin-top: 28px;
  padding: 36px 28px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e0e7ff;
  box-shadow: var(--rpt-shadow);
  animation: rpt-fade-up 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: 60ms;
}
.rpt-empty :deep(.el-empty__description p) {
  color: #64748b;
  font-weight: 600;
}

.rpt-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rpt-kpi {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 6px;
}
.rpt-kpi.is-half,
.rpt-kpi.is-annual {
  grid-template-columns: 1fr;
}
.rpt-kpi__card--wide {
  grid-column: 1 / -1;
}
.rpt-kpi__body {
  display: grid;
  grid-template-columns: minmax(168px, 32%) minmax(0, 1fr);
  gap: 8px;
  align-items: stretch;
  min-width: 0;
}
.rpt-kpi__chart {
  height: 200px;
  min-width: 0;
  padding: 4px 4px 2px;
  box-sizing: border-box;
  overflow: hidden;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid color-mix(in srgb, var(--kpi-border) 80%, #ffffff);
}
.rpt-kpi__chart--tall {
  height: 252px;
}
@media (max-width: 1100px) {
  .rpt-kpi,
  .rpt-kpi.is-half,
  .rpt-kpi.is-annual {
    grid-template-columns: 1fr;
  }
  .rpt-kpi__body {
    grid-template-columns: minmax(140px, 38%) minmax(0, 1fr);
  }
}
@media (max-width: 720px) {
  .rpt-kpi__body {
    grid-template-columns: 1fr;
  }
}

.rpt-kpi__card {
  --kpi-accent: #6366f1;
  --kpi-tint: #f8fafc;
  --kpi-border: #cbd5e1;
  --kpi-strong: #0f172a;
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  padding: 12px 12px 10px 14px;
  background: linear-gradient(180deg, #ffffff 0%, var(--kpi-tint) 100%);
  border: 1px solid var(--kpi-border);
  border-left: 4px solid var(--kpi-accent);
  box-shadow: var(--rpt-shadow);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease,
    border-color 0.22s ease;
  animation: rpt-card-in 0.42s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.rpt-kpi__card:nth-child(1) {
  animation-delay: 70ms;
}
.rpt-kpi__card:nth-child(2) {
  animation-delay: 110ms;
}
.rpt-kpi__card:nth-child(3) {
  animation-delay: 150ms;
}
.rpt-kpi__card:nth-child(4) {
  animation-delay: 190ms;
}
.rpt-kpi__card:nth-child(5) {
  animation-delay: 230ms;
}
.rpt-kpi__card:nth-child(6) {
  animation-delay: 270ms;
}
.rpt-kpi__card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: var(--kpi-accent);
  border-radius: 14px 14px 0 0;
}
.rpt-kpi__card:hover {
  transform: translateY(-3px);
  border-color: var(--kpi-accent);
  box-shadow: var(--rpt-shadow-hover);
}
.rpt-kpi__card.is-warn {
  outline: 2px solid #f59e0b;
  outline-offset: 0;
}

.theme-inv {
  --kpi-accent: #4f46e5;
  --kpi-tint: #eef2ff;
  --kpi-border: #c7d2fe;
  --kpi-strong: #312e81;
}
.theme-wip {
  --kpi-accent: #2563eb;
  --kpi-tint: #eff6ff;
  --kpi-border: #bfdbfe;
  --kpi-strong: #1e3a8a;
}
.theme-product {
  --kpi-accent: #0d9488;
  --kpi-tint: #f0fdfa;
  --kpi-border: #99f6e4;
  --kpi-strong: #115e59;
}
.theme-defect {
  --kpi-accent: #d97706;
  --kpi-tint: #fffbeb;
  --kpi-border: #fde68a;
  --kpi-strong: #92400e;
}
.theme-qty {
  --kpi-accent: #e11d48;
  --kpi-tint: #fff1f2;
  --kpi-border: #fecdd3;
  --kpi-strong: #9f1239;
}
.theme-match {
  --kpi-accent: #059669;
  --kpi-tint: #ecfdf5;
  --kpi-border: #a7f3d0;
  --kpi-strong: #065f46;
}
.rpt-kpi__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.rpt-kpi__ico {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--kpi-accent);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.28);
  font-size: 15px;
}
.rpt-kpi__label {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
  font-size: 13px;
  color: var(--kpi-strong);
  font-weight: 800;
  letter-spacing: 0.02em;
}
.rpt-kpi__target {
  font-size: 11px;
  font-weight: 700;
  color: var(--kpi-strong);
  padding: 2px 8px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid var(--kpi-border);
}
.rpt-kpi__unit {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.01em;
}
.rpt-kpi__months {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 252px;
  overflow: auto;
  padding-right: 4px;
}
.rpt-kpi__months--cats .rpt-kpi__month {
  grid-template-columns: minmax(88px, 48%) minmax(0, 1fr);
}
.bulk-cat-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: 0;
  box-shadow: 0 0 0 2px #ffffff;
}
.rpt-kpi__month {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  align-items: baseline;
  gap: 2px 6px;
  padding: 6px 6px;
  margin: 0 -4px;
  border-radius: 8px;
  border-top: 1px solid color-mix(in srgb, var(--kpi-border) 70%, transparent);
  font-variant-numeric: tabular-nums;
  transition: background 0.16s ease;
}
.rpt-kpi__month:first-child {
  border-top: 0;
  padding-top: 4px;
}
.rpt-kpi__month:hover {
  background: color-mix(in srgb, var(--kpi-tint) 65%, #ffffff);
}
.rpt-kpi__month > span {
  grid-row: 1 / span 2;
  align-self: center;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}
.rpt-kpi__month > strong {
  min-width: 0;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--kpi-strong);
  text-align: right;
  white-space: nowrap;
  line-height: 1.15;
}
.rpt-kpi__month > small {
  font-size: 11px;
  line-height: 1.2;
  font-weight: 600;
  color: #64748b;
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
  color: #0f172a;
}
.rpt-hl__text :deep(.hl-num--down) {
  color: #dc2626;
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
  background: #2563eb;
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
  --qoq-c: #0f172a;
  --qoq-bg1: #f8fafc;
  --qoq-bg2: #e2e8f0;
}
.rpt-qoq__stat[data-dir='down'] {
  --qoq-c: #dc2626;
  --qoq-bg1: #fef2f2;
  --qoq-bg2: #fee2e2;
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
  .rpt-highlights {
    grid-template-columns: 1fr;
  }
}

.rpt-chart-card,
.rpt-block {
  --panel-solid: #6366f1;
  --panel-tint: #eef2ff;
  --panel-border: #c7d2fe;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff 0%, var(--panel-tint) 100%);
  border-radius: 14px;
  padding: 12px 14px 10px;
  border: 1px solid var(--panel-border);
  border-left: 4px solid var(--panel-solid);
  box-shadow: var(--rpt-shadow);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease,
    border-color 0.22s ease;
}
.rpt-chart-card:hover,
.rpt-block:hover {
  transform: translateY(-2px);
  border-color: var(--panel-solid);
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
  background: var(--panel-solid);
}
.accent-blue {
  --panel-solid: #2563eb;
  --panel-tint: #eff6ff;
  --panel-border: #bfdbfe;
}
.accent-rose {
  --panel-solid: #e11d48;
  --panel-tint: #fff1f2;
  --panel-border: #fecdd3;
}
.accent-amber {
  --panel-solid: #d97706;
  --panel-tint: #fffbeb;
  --panel-border: #fde68a;
}
.accent-violet {
  --panel-solid: #7c3aed;
  --panel-tint: #f5f3ff;
  --panel-border: #ddd6fe;
}
.accent-teal {
  --panel-solid: #0d9488;
  --panel-tint: #f0fdfa;
  --panel-border: #99f6e4;
}
.accent-slate {
  --panel-solid: #475569;
  --panel-tint: #f8fafc;
  --panel-border: #cbd5e1;
}

.rpt-chart-card__title,
.rpt-block__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #0f172a;
}
.rpt-chart-card__title {
  margin-bottom: 4px;
}
.rpt-chart-host,
.rpt-embed-chart {
  height: 280px;
  width: 100%;
}
.rpt-embed-chart {
  margin: 4px 0 10px;
  padding: 8px 6px 4px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid var(--panel-border, #e2e8f0);
}

.rpt-block {
  padding: 12px 14px 10px;
  margin-bottom: 0;
}
.rpt-block__hint {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  padding: 3px 10px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid var(--panel-border, #e2e8f0);
}
.rpt-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.rpt-block__title .el-icon {
  color: var(--panel-solid, #6366f1);
}

.rpt-num {
  width: 120px;
}
.num-neg,
.num-down {
  color: #dc2626 !important;
  font-weight: 800;
}
.num-up {
  color: #0f172a;
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
  --el-table-border-color: var(--panel-border, #c7d2fe);
  --el-table-header-bg-color: var(--panel-tint, #eef2ff);
  --el-table-text-color: #0f172a;
  border-radius: 10px;
  overflow: hidden;
  font-variant-numeric: tabular-nums;
}
:deep(.rpt-table th.el-table__cell) {
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.02em;
  color: #0f172a;
  background: var(--panel-tint, #eef2ff) !important;
}
:deep(.rpt-table td.el-table__cell) {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
:deep(.rpt-period-type .el-radio-button__inner),
:deep(.rpt-quarter .el-radio-button__inner) {
  font-weight: 700;
  letter-spacing: 0.02em;
}
:deep(.rpt-period-type .el-radio-button__original-radio:checked + .el-radio-button__inner),
:deep(.rpt-quarter .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #ffffff;
  box-shadow: none;
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
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  color: #4338ca;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 999px;
  padding: 1px 8px;
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
.bulk-chip--violet {
  color: #6d28d9;
  background: rgba(124, 58, 237, 0.1);
  border: 1px solid rgba(109, 40, 217, 0.28);
}
.bulk-chip--cyan {
  color: #0e7490;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(8, 145, 178, 0.28);
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
  background: linear-gradient(145deg, #818cf8, #6366f1);
  box-shadow: 0 5px 12px rgba(99, 102, 241, 0.35), 0 1px 0 rgba(255, 255, 255, 0.35) inset;
}
.rpt-help-dialog__titles {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.rpt-help-dialog__titles strong {
  font-size: 14px;
  font-weight: 800;
  color: #3730a3;
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
  .page-toolbar,
  .filter-bar,
  .rpt-saved-bar,
  .rpt-ideas {
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
