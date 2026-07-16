<template>
  <div class="budget-page">
    <div class="dynamic-background" aria-hidden="true">
      <div class="gradient-orb orb-1" />
      <div class="gradient-orb orb-2" />
      <div class="gradient-orb orb-3" />
    </div>

    <header class="page-head page-head--glass">
      <div class="page-head-icon">
        <el-icon :size="26"><Coin /></el-icon>
      </div>
      <div class="page-head-text">
        <h1 class="page-head-title">予算管理</h1>
        <p class="page-head-sub">
          見直し予算CSVを取込み、品番→製品マスタ（製品CD末尾1）を紐付けて工程・設備・原価を分析
        </p>
      </div>
      <div class="page-head-filters">
        <el-select
          v-model="filterYearMonth"
          placeholder="対象年月"
          clearable
          size="small"
          class="ym-select"
          @change="onYearMonthChange"
        >
          <el-option
            v-for="m in monthOptions"
            :key="`${m.year}-${m.month}`"
            :label="`${m.year}年${m.month}月`"
            :value="`${m.year}-${m.month}`"
          />
        </el-select>
        <el-button size="small" :icon="Refresh" @click="reloadAll">更新</el-button>
      </div>
    </header>

    <!-- KPI -->
    <section class="kpi-row" v-loading="summaryLoading">
      <div class="kpi-card kpi-card--blue">
        <div class="kpi-card__label">予算総数量</div>
        <div class="kpi-card__value">{{ formatInt(summary.total_budget_qty) }}</div>
        <div class="kpi-card__hint">選択年月の合計</div>
      </div>
      <div class="kpi-card kpi-card--violet">
        <div class="kpi-card__label">品番数</div>
        <div class="kpi-card__value">{{ formatInt(summary.product_count) }}</div>
        <div class="kpi-card__hint">取込済みレコード</div>
      </div>
      <div class="kpi-card kpi-card--green">
        <div class="kpi-card__label">紐付成功</div>
        <div class="kpi-card__value">{{ formatInt(summary.matched_count) }}</div>
        <div class="kpi-card__hint">製品CD末尾1で一致</div>
      </div>
      <div class="kpi-card kpi-card--amber">
        <div class="kpi-card__label">未紐付</div>
        <div class="kpi-card__value">{{ formatInt(summary.unmatched_count) }}</div>
        <div class="kpi-card__hint">マスタ要確認</div>
      </div>
      <div class="kpi-card kpi-card--slate">
        <div class="kpi-card__label">対象月数</div>
        <div class="kpi-card__value">{{ formatInt(summary.month_count) }}</div>
        <div class="kpi-card__hint">フィルタ適用後</div>
      </div>
    </section>

    <el-tabs v-model="activeTab" class="budget-tabs" @tab-change="onTabChange">
      <!-- 取込 -->
      <el-tab-pane label="CSV取込" name="upload">
        <div class="tab-grid">
          <div class="panel upload-panel">
            <div class="panel__title">
              <el-icon><UploadFilled /></el-icon>
              ファイルアップロード
            </div>
            <p class="panel__desc">
              配信用CSV（開発コード / 品番 / 年月数量）。エンコードは Shift_JIS・UTF-8 両対応。
              <strong>同一品番は合算</strong>後に製品紐付し、<strong>同月・同品番は上書き更新</strong>します。
            </p>
            <el-upload
              drag
              accept=".csv"
              :auto-upload="false"
              :show-file-list="false"
              :disabled="uploading"
              class="budget-uploader"
              @change="onFileChange"
            >
              <div class="upload-inner">
                <el-icon class="upload-icon" :size="40"><UploadFilled /></el-icon>
                <div class="upload-text">CSVをドラッグ＆ドロップ、またはクリックして選択</div>
                <div class="upload-hint">例: 2026年度 見直し予算【ステー】 配信用.csv</div>
              </div>
            </el-upload>
            <div v-if="selectedFile" class="selected-file">
              <el-icon><Document /></el-icon>
              <span class="selected-file__name">{{ selectedFile.name }}</span>
              <span class="selected-file__size">{{ formatFileSize(selectedFile.size) }}</span>
              <el-button
                type="primary"
                size="small"
                :loading="uploading"
                :disabled="!canCreate"
                @click="doUpload"
              >
                取込実行
              </el-button>
              <el-button size="small" plain :disabled="uploading" @click="selectedFile = null">取消</el-button>
            </div>

            <div v-if="lastUpload" class="upload-result">
              <div class="upload-result__title">直近の取込結果</div>
              <div class="upload-result__grid">
                <div><span>ファイル</span><b>{{ lastUpload.file_name }}</b></div>
                <div><span>品番行</span><b>{{ lastUpload.total_rows }}</b></div>
                <div><span>紐付成功</span><b class="ok">{{ lastUpload.matched_rows }}</b></div>
                <div><span>未紐付</span><b class="warn">{{ lastUpload.unmatched_rows }}</b></div>
                <div><span>新規</span><b>{{ lastUpload.inserted_rows }}</b></div>
                <div><span>更新</span><b>{{ lastUpload.updated_rows }}</b></div>
              </div>
              <el-alert
                v-if="lastUpload.unmatched_samples?.length"
                type="warning"
                :closable="false"
                show-icon
                class="mt-8"
                title="未紐付サンプル（品番が製品マスタに無い、または製品CD末尾1が無い）"
              />
              <el-table
                v-if="lastUpload.unmatched_samples?.length"
                :data="lastUpload.unmatched_samples"
                size="small"
                max-height="180"
                class="mt-8"
              >
                <el-table-column prop="line_no" label="行" width="60" />
                <el-table-column prop="development_code" label="開発コード" min-width="120" />
                <el-table-column prop="part_number" label="品番" min-width="140" />
              </el-table>
            </div>
          </div>

          <div class="panel">
            <div class="panel__title">
              <el-icon><Clock /></el-icon>
              取込履歴
            </div>
            <el-table :data="imports" size="small" v-loading="importsLoading" max-height="420" stripe>
              <el-table-column prop="created_at" label="日時" width="160">
                <template #default="{ row }">{{ formatDt(row.created_at) }}</template>
              </el-table-column>
              <el-table-column prop="file_name" label="ファイル" min-width="160" show-overflow-tooltip />
              <el-table-column prop="total_rows" label="品番" width="64" align="right" />
              <el-table-column prop="matched_rows" label="紐付" width="64" align="right" />
              <el-table-column prop="updated_rows" label="更新" width="64" align="right" />
              <el-table-column prop="uploaded_by" label="実行者" width="90" show-overflow-tooltip />
            </el-table>
          </div>
        </div>

        <div class="panel guide-panel">
          <div class="panel__title">
            <el-icon><InfoFilled /></el-icon>
            取込ルール・分析の前提
          </div>
          <ul class="guide-list">
            <li>CSV列: <code>開発コード</code> / <code>品番</code> / <code>YYYY年M月</code>（複数月可）</li>
            <li><strong>同一品番は年月ごとに数量を合算</strong>してから製品マスタへ紐付</li>
            <li>合算後の品番で <code>products.part_number</code> を検索し、<strong>製品CDが「1」で終わる</strong>行のみ採用</li>
            <li>同一 <code>年+月+品番</code> が既にある場合は数量・製品情報を上書き</li>
            <li>工程負荷: 製品工程ルートの標準サイクルタイム × 予算数量（外注検査前・外注支給前・外注倉庫・溶接前検査・外注切断・倉庫は除外）</li>
            <li>設備負荷: 設備能率マスタの step_time / 能率 × 予算数量（無い場合は工程設備時間）</li>
            <li>原価: 標準原価（有効バージョン）× 数量、売上概算は製品単価 × 数量</li>
          </ul>
        </div>
      </el-tab-pane>

      <!-- 一覧 -->
      <el-tab-pane label="予算一覧" name="list">
        <div class="toolbar">
          <el-input
            v-model="listKeyword"
            size="small"
            clearable
            placeholder="品番・製品CD・製品名・開発コード"
            class="toolbar__search"
            @keyup.enter="loadList"
          />
          <el-select v-model="listMatchStatus" size="small" clearable placeholder="紐付状態" class="w-140" @change="loadList">
            <el-option label="紐付成功" value="matched" />
            <el-option label="複数候補" value="multi_match" />
            <el-option label="未紐付" value="unmatched" />
          </el-select>
          <el-button size="small" type="primary" :icon="Search" @click="loadList">検索</el-button>
          <el-button
            size="small"
            type="danger"
            plain
            :disabled="!canDelete || !selectedYear || !selectedMonth"
            @click="confirmDeleteMonth"
          >
            選択月を削除
          </el-button>
        </div>
        <el-table :data="listItems" size="small" v-loading="listLoading" stripe border class="data-table">
          <el-table-column label="年月" width="90" fixed>
            <template #default="{ row }">{{ row.year }}/{{ String(row.month).padStart(2, '0') }}</template>
          </el-table-column>
          <el-table-column prop="development_code" label="開発コード" min-width="120" show-overflow-tooltip />
          <el-table-column prop="part_number" label="品番" min-width="120" show-overflow-tooltip />
          <el-table-column prop="product_cd" label="製品CD" width="110" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="budget_qty" label="予算数量" width="100" align="right">
            <template #default="{ row }">{{ formatInt(row.budget_qty) }}</template>
          </el-table-column>
          <el-table-column prop="match_status" label="紐付" width="96" align="center">
            <template #default="{ row }">
              <el-tag
                size="small"
                :type="row.match_status === 'matched' ? 'success' : row.match_status === 'multi_match' ? 'warning' : 'danger'"
              >
                {{ matchLabel(row.match_status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager">
          <el-pagination
            v-model:current-page="listPage"
            v-model:page-size="listPageSize"
            :total="listTotal"
            :page-sizes="[20, 50, 100, 200]"
            layout="total, sizes, prev, pager, next"
            small
            @current-change="loadList"
            @size-change="onListPageSizeChange"
          />
        </div>
      </el-tab-pane>

      <!-- 推移 -->
      <el-tab-pane label="月次推移" name="trend">
        <div class="panel trend-panel">
          <div class="panel__title trend-panel__head">
            <div class="trend-panel__title-left">
              <el-icon><TrendCharts /></el-icon>
              予算数量の月次推移
            </div>
            <div class="trend-panel__meta">
              <template v-if="trendRows.length">
                <span>{{ trendRows.length }}か月</span>
                <span class="dot">·</span>
                <span>合計 {{ formatInt(trendTotalQty) }}</span>
                <span class="dot">·</span>
              </template>
              <el-button size="small" type="primary" plain :icon="Calendar" @click="openWorkingDaysDialog">
                月次稼働日の設定
              </el-button>
            </div>
          </div>
          <div ref="trendChartRef" class="chart-box chart-box--trend" v-loading="trendLoading" />
          <el-empty v-if="!trendLoading && !trendRows.length" description="推移データがありません" :image-size="72" />
        </div>

        <div class="panel trend-panel process-trend-panel" v-loading="processTrendLoading">
          <div class="panel__title trend-panel__head">
            <div class="trend-panel__title-left">
              <el-icon><Operation /></el-icon>
              工程別 予算数量の月次推移
            </div>
            <div v-if="processTrendList.length" class="trend-panel__meta">
              <span>{{ processTrendList.length }}工程</span>
              <span class="dot">·</span>
              <span>{{ processTrendMonths.length }}か月</span>
            </div>
          </div>
          <p class="panel__desc process-trend-desc">
            製品工程ルートに含まれる工程ごとに、紐付済み製品の予算数量を月次集計します（同一製品×工程は1回計上）。
            外注検査前・外注支給前・外注倉庫・溶接前検査・外注切断・倉庫は除外します。
            表示順: 切断 → 面取 → SW → 成型 → メッキ → 溶接 → 検査 → 外注メッキ → 外注溶接 → 外注検査。
          </p>

          <div v-if="processTrendList.length" class="process-trend-grid">
            <div
              v-for="(proc, idx) in processTrendList"
              :key="proc.process_cd"
              class="process-trend-card"
            >
              <div class="process-trend-card__head">
                <div class="process-trend-card__title">
                  <span class="process-trend-card__rank">{{ idx + 1 }}</span>
                  <span class="process-trend-card__name">{{ proc.process_name }}</span>
                  <el-tag size="small" :type="proc.is_outsource ? 'warning' : 'info'" effect="plain">
                    {{ proc.is_outsource ? '外注' : '社内' }}
                  </el-tag>
                </div>
                <div class="process-trend-card__total">
                  合計 <b>{{ formatInt(proc.total_qty) }}</b>
                </div>
              </div>
              <div
                class="chart-box chart-box--process-mini"
                :ref="(el) => setProcessMiniRef(proc.process_cd, el)"
              />
            </div>
          </div>

          <el-empty
            v-if="!processTrendLoading && !processTrendList.length"
            description="工程別推移データがありません（製品紐付・工程ルート要確認）"
            :image-size="72"
          />
        </div>
      </el-tab-pane>

      <!-- 工程 -->
      <el-tab-pane label="工程負荷" name="process">
        <div class="analysis-layout">
          <div class="panel">
            <div class="panel__title">
              <el-icon><Operation /></el-icon>
              工程別負荷（時間）
            </div>
            <div ref="processChartRef" class="chart-box chart-box--tall" v-loading="processLoading" />
          </div>
          <div class="panel">
            <el-table :data="processRows" size="small" v-loading="processLoading" stripe max-height="420">
              <el-table-column prop="process_cd" label="工程CD" width="90" />
              <el-table-column prop="process_name" label="工程名" min-width="120" show-overflow-tooltip />
              <el-table-column prop="product_count" label="品目数" width="72" align="right" />
              <el-table-column prop="total_budget_qty" label="予算数量" width="96" align="right">
                <template #default="{ row }">{{ formatInt(row.total_budget_qty) }}</template>
              </el-table-column>
              <el-table-column prop="total_hours" label="負荷(h)" width="90" align="right">
                <template #default="{ row }">{{ formatNum(row.total_hours) }}</template>
              </el-table-column>
              <el-table-column label="区分" width="72" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.is_outsource ? 'warning' : 'info'">
                    {{ row.is_outsource ? '外注' : '社内' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 設備 -->
      <el-tab-pane label="設備負荷" name="equipment">
        <div class="analysis-layout">
          <div class="panel">
            <div class="panel__title">
              <el-icon><Monitor /></el-icon>
              設備別負荷（時間）
            </div>
            <div ref="equipChartRef" class="chart-box chart-box--tall" v-loading="equipLoading" />
          </div>
          <div class="panel">
            <el-table :data="equipRows" size="small" v-loading="equipLoading" stripe max-height="420">
              <el-table-column prop="machine_cd" label="設備CD" width="100" />
              <el-table-column prop="machine_name" label="設備名" min-width="120" show-overflow-tooltip />
              <el-table-column prop="product_count" label="品目数" width="72" align="right" />
              <el-table-column prop="total_budget_qty" label="予算数量" width="96" align="right">
                <template #default="{ row }">{{ formatInt(row.total_budget_qty) }}</template>
              </el-table-column>
              <el-table-column prop="total_hours" label="負荷(h)" width="90" align="right">
                <template #default="{ row }">{{ formatNum(row.total_hours) }}</template>
              </el-table-column>
              <el-table-column prop="avg_efficiency_rate" label="平均能率%" width="96" align="right">
                <template #default="{ row }">
                  {{ row.avg_efficiency_rate != null ? formatNum(row.avg_efficiency_rate) : '—' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <!-- 原価 -->
      <el-tab-pane label="原価分析" name="cost">
        <section class="kpi-row kpi-row--compact">
          <div class="kpi-card kpi-card--blue">
            <div class="kpi-card__label">売上概算</div>
            <div class="kpi-card__value kpi-card__value--sm">{{ formatYen(costTotals.sales_amount) }}</div>
          </div>
          <div class="kpi-card kpi-card--amber">
            <div class="kpi-card__label">標準原価計</div>
            <div class="kpi-card__value kpi-card__value--sm">{{ formatYen(costTotals.cost_amount) }}</div>
          </div>
          <div class="kpi-card kpi-card--green">
            <div class="kpi-card__label">粗利概算</div>
            <div class="kpi-card__value kpi-card__value--sm">{{ formatYen(costTotals.margin_amount) }}</div>
          </div>
          <div class="kpi-card kpi-card--violet">
            <div class="kpi-card__label">予算数量</div>
            <div class="kpi-card__value kpi-card__value--sm">{{ formatInt(costTotals.budget_qty) }}</div>
          </div>
        </section>
        <div class="panel">
          <div class="panel__title">
            <el-icon><Money /></el-icon>
            製品別 原価・売上概算
          </div>
          <el-table :data="costRows" size="small" v-loading="costLoading" stripe border max-height="480">
            <el-table-column prop="development_code" label="開発コード" min-width="110" show-overflow-tooltip />
            <el-table-column prop="part_number" label="品番" min-width="110" show-overflow-tooltip />
            <el-table-column prop="product_cd" label="製品CD" width="100" />
            <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip />
            <el-table-column prop="budget_qty" label="数量" width="88" align="right">
              <template #default="{ row }">{{ formatInt(row.budget_qty) }}</template>
            </el-table-column>
            <el-table-column prop="unit_price" label="売単価" width="96" align="right">
              <template #default="{ row }">{{ row.unit_price != null ? formatNum(row.unit_price) : '—' }}</template>
            </el-table-column>
            <el-table-column prop="unit_cost_std" label="標準原価" width="96" align="right">
              <template #default="{ row }">{{ row.unit_cost_std != null ? formatNum(row.unit_cost_std) : '—' }}</template>
            </el-table-column>
            <el-table-column prop="sales_amount" label="売上概算" width="110" align="right">
              <template #default="{ row }">{{ formatYen(row.sales_amount) }}</template>
            </el-table-column>
            <el-table-column prop="cost_amount" label="原価計" width="110" align="right">
              <template #default="{ row }">{{ formatYen(row.cost_amount) }}</template>
            </el-table-column>
            <el-table-column prop="margin_amount" label="粗利" width="110" align="right">
              <template #default="{ row }">
                <span :class="{ 'neg': row.margin_amount < 0 }">{{ formatYen(row.margin_amount) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="workingDaysDialogVisible"
      title="月次稼働日の設定"
      width="720px"
      destroy-on-close
      class="working-days-dialog"
      @opened="onWorkingDaysDialogOpened"
    >
      <p class="wd-dialog-desc">
        共通稼働日をデフォルトとし、工程ごとに上書きできます。未指定の工程・月は共通値を使います。
        <br />
        <strong>日平均生産数量 = 予算数量 ÷ 稼働日数</strong>
      </p>
      <el-tabs v-model="workingDaysTab" class="wd-tabs">
        <el-tab-pane label="共通デフォルト" name="default">
          <el-table
            :data="workingDaysRows"
            size="small"
            v-loading="workingDaysLoading"
            stripe
            border
            max-height="380"
            class="wd-table"
          >
            <el-table-column prop="label" label="年月" width="100" />
            <el-table-column label="稼働日数" width="140" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.working_days"
                  :min="0"
                  :max="31"
                  :step="1"
                  size="small"
                  controls-position="right"
                  class="wd-input"
                />
              </template>
            </el-table-column>
            <el-table-column prop="total_budget_qty" label="予算数量" min-width="110" align="right">
              <template #default="{ row }">{{ formatInt(row.total_budget_qty) }}</template>
            </el-table-column>
            <el-table-column label="日平均生産数量" min-width="130" align="right">
              <template #default="{ row }">
                <span class="avg-cell" :class="{ 'avg-cell--empty': !row.working_days }">
                  {{ formatAvgDaily(row.total_budget_qty, row.working_days) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="!workingDaysLoading && !workingDaysRows.length"
            description="先に予算CSVを取込んでください"
            :image-size="64"
          />
        </el-tab-pane>
        <el-tab-pane label="工程別指定" name="process">
          <div class="wd-process-toolbar">
            <span class="wd-process-label">工程</span>
            <el-select
              v-model="selectedProcessCd"
              filterable
              placeholder="工程を選択"
              size="small"
              style="width: 260px"
              @change="rebuildProcessWorkingDaysRows"
            >
              <el-option
                v-for="opt in processWorkingDayOptions"
                :key="opt.process_cd"
                :label="opt.process_name"
                :value="opt.process_cd"
              />
            </el-select>
            <span class="wd-process-hint">空欄 = 共通デフォルトを使用</span>
          </div>
          <el-table
            :data="processWorkingDaysRows"
            size="small"
            v-loading="workingDaysLoading"
            stripe
            border
            max-height="340"
            class="wd-table"
          >
            <el-table-column prop="label" label="年月" width="100" />
            <el-table-column label="共通" width="80" align="center">
              <template #default="{ row }">
                <span class="wd-default-days">{{ row.default_days || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="工程稼働日" width="180" align="center">
              <template #default="{ row }">
                <div class="wd-override-cell">
                  <el-input-number
                    v-model="row.override_days"
                    :min="0"
                    :max="31"
                    :step="1"
                    size="small"
                    controls-position="right"
                    class="wd-input"
                    :value-on-clear="null"
                    :placeholder="row.default_days ? String(row.default_days) : ''"
                  />
                  <el-button
                    v-if="row.override_days != null"
                    link
                    type="primary"
                    size="small"
                    @click="row.override_days = null"
                  >
                    クリア
                  </el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="適用" width="80" align="center">
              <template #default="{ row }">
                <span
                  class="wd-effective"
                  :class="{ 'wd-effective--override': row.override_days != null }"
                >
                  {{ effectiveProcessDays(row) || '—' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="total_budget_qty" label="予算数量(総)" min-width="110" align="right">
              <template #default="{ row }">{{ formatInt(row.total_budget_qty) }}</template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="!workingDaysLoading && !processWorkingDayOptions.length"
            description="工程候補がありません（先に予算を取込んでください）"
            :image-size="64"
          />
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button size="small" @click="workingDaysDialogVisible = false">取消</el-button>
        <el-button size="small" :icon="Refresh" :loading="workingDaysLoading" @click="loadWorkingDays">
          再読込
        </el-button>
        <el-button
          size="small"
          type="primary"
          :loading="workingDaysSaving"
          :disabled="!canEdit"
          @click="saveWorkingDaysForm"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import {
  Clock,
  Coin,
  Calendar,
  Document,
  InfoFilled,
  Money,
  Monitor,
  Operation,
  Refresh,
  Search,
  TrendCharts,
  UploadFilled,
} from '@element-plus/icons-vue'
import {
  deleteBudgetMonth,
  fetchBudgetImports,
  fetchBudgetList,
  fetchBudgetMonths,
  fetchBudgetSummary,
  fetchBudgetTrend,
  fetchCostAnalysis,
  fetchEquipmentLoad,
  fetchProcessLoad,
  fetchProcessTrend,
  fetchWorkingDays,
  saveProcessWorkingDays,
  saveWorkingDays,
  uploadBudgetCsv,
  type BudgetImportBatch,
  type BudgetMonthlyItem,
  type BudgetSummary,
  type BudgetUploadResult,
  type CostAnalysisItem,
  type EquipmentLoadItem,
  type ProcessLoadItem,
  type ProcessTrendMonth,
  type ProcessTrendSeries,
  type ProcessWorkingDaysOption,
  type ProcessWorkingDaysOverride,
  type TrendItem,
  type WorkingDaysItem,
} from '@/api/erp/budget'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'

const { canCreate, canDelete, canEdit } = useSalesOperationPermission()

const activeTab = ref('upload')
const monthOptions = ref<{ year: number; month: number }[]>([])
const filterYearMonth = ref<string>('')
const selectedYear = computed(() => {
  if (!filterYearMonth.value) return undefined
  return Number(filterYearMonth.value.split('-')[0])
})
const selectedMonth = computed(() => {
  if (!filterYearMonth.value) return undefined
  return Number(filterYearMonth.value.split('-')[1])
})

const summaryLoading = ref(false)
const summary = reactive<BudgetSummary>({
  product_count: 0,
  matched_count: 0,
  unmatched_count: 0,
  total_budget_qty: 0,
  month_count: 0,
})

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const lastUpload = ref<BudgetUploadResult | null>(null)
const imports = ref<BudgetImportBatch[]>([])
const importsLoading = ref(false)

const listItems = ref<BudgetMonthlyItem[]>([])
const listLoading = ref(false)
const listKeyword = ref('')
const listMatchStatus = ref<string | undefined>()
const listPage = ref(1)
const listPageSize = ref(50)
const listTotal = ref(0)

const trendLoading = ref(false)
const trendRows = ref<TrendItem[]>([])
const trendChartRef = ref<HTMLDivElement | null>(null)
let trendChart: echarts.ECharts | null = null
const trendTotalQty = computed(() =>
  trendRows.value.reduce((sum, r) => sum + (r.total_budget_qty || 0), 0),
)

const processTrendLoading = ref(false)
const processTrendMonths = ref<ProcessTrendMonth[]>([])
const processTrendList = ref<ProcessTrendSeries[]>([])
const processMiniEls = new Map<string, HTMLDivElement>()
const processMiniCharts = new Map<string, echarts.ECharts>()

const PROCESS_TREND_COLORS = [
  '#2563eb',
  '#0d9488',
  '#7c3aed',
  '#d97706',
  '#db2777',
  '#0891b2',
  '#65a30d',
  '#ea580c',
  '#4f46e5',
  '#059669',
]

function setProcessMiniRef(processCd: string, el: unknown) {
  if (el instanceof HTMLDivElement) {
    processMiniEls.set(processCd, el)
  } else {
    processMiniEls.delete(processCd)
  }
}

const processLoading = ref(false)
const processRows = ref<ProcessLoadItem[]>([])
const processChartRef = ref<HTMLDivElement | null>(null)
let processChart: echarts.ECharts | null = null

const equipLoading = ref(false)
const equipRows = ref<EquipmentLoadItem[]>([])
const equipChartRef = ref<HTMLDivElement | null>(null)
let equipChart: echarts.ECharts | null = null

const costLoading = ref(false)
const costRows = ref<CostAnalysisItem[]>([])
const costTotals = reactive({
  budget_qty: 0,
  sales_amount: 0,
  cost_amount: 0,
  margin_amount: 0,
})

function formatInt(n?: number | null) {
  return (n ?? 0).toLocaleString()
}

function formatAvgDaily(qty: number, workingDays?: number | null) {
  if (!workingDays || workingDays <= 0) return '—'
  return Math.round(qty / workingDays).toLocaleString()
}

const workingDaysLoading = ref(false)
const workingDaysSaving = ref(false)
const workingDaysDialogVisible = ref(false)
const workingDaysTab = ref<'default' | 'process'>('default')
const workingDaysRows = ref<WorkingDaysItem[]>([])
const processWorkingDayOptions = ref<ProcessWorkingDaysOption[]>([])
const processWorkingDayOverrides = ref<ProcessWorkingDaysOverride[]>([])
const selectedProcessCd = ref('')
type ProcessWdRow = {
  year: number
  month: number
  label: string
  default_days: number
  override_days: number | null
  total_budget_qty: number
}
const processWorkingDaysRows = ref<ProcessWdRow[]>([])

function applyWorkingDaysBundle(bundle: {
  defaults?: WorkingDaysItem[]
  process_options?: ProcessWorkingDaysOption[]
  process_overrides?: ProcessWorkingDaysOverride[]
}) {
  workingDaysRows.value = (bundle.defaults || []).map((r) => ({ ...r }))
  processWorkingDayOptions.value = bundle.process_options || []
  processWorkingDayOverrides.value = bundle.process_overrides || []
  if (
    selectedProcessCd.value &&
    !processWorkingDayOptions.value.some((o) => o.process_cd === selectedProcessCd.value)
  ) {
    selectedProcessCd.value = ''
  }
  if (!selectedProcessCd.value && processWorkingDayOptions.value.length) {
    selectedProcessCd.value = processWorkingDayOptions.value[0].process_cd
  }
  rebuildProcessWorkingDaysRows()
}

function rebuildProcessWorkingDaysRows() {
  const pc = selectedProcessCd.value
  const overrideMap = new Map<string, number>()
  for (const o of processWorkingDayOverrides.value) {
    if (o.process_cd !== pc) continue
    overrideMap.set(`${o.year}-${o.month}`, o.working_days)
  }
  processWorkingDaysRows.value = workingDaysRows.value.map((r) => ({
    year: r.year,
    month: r.month,
    label: r.label,
    default_days: r.working_days || 0,
    override_days: overrideMap.has(`${r.year}-${r.month}`)
      ? overrideMap.get(`${r.year}-${r.month}`)!
      : null,
    total_budget_qty: r.total_budget_qty || 0,
  }))
}

function effectiveProcessDays(row: ProcessWdRow) {
  if (row.override_days != null && !Number.isNaN(Number(row.override_days))) {
    return Number(row.override_days)
  }
  return row.default_days || 0
}

async function loadWorkingDays() {
  workingDaysLoading.value = true
  try {
    applyWorkingDaysBundle(await fetchWorkingDays())
  } finally {
    workingDaysLoading.value = false
  }
}

async function openWorkingDaysDialog() {
  workingDaysDialogVisible.value = true
}

async function onWorkingDaysDialogOpened() {
  await loadWorkingDays()
}

async function saveWorkingDaysForm() {
  if (!canEdit.value) {
    ElMessage.warning('編集権限がありません')
    return
  }
  workingDaysSaving.value = true
  try {
    if (workingDaysTab.value === 'default') {
      const res = await saveWorkingDays(
        workingDaysRows.value.map((r) => ({
          year: r.year,
          month: r.month,
          working_days: Number(r.working_days) || 0,
        })),
      )
      // 共通保存後は defaults を更新しつつ工程設定は再読込
      workingDaysRows.value = (res.data || []).map((r) => ({ ...r }))
      rebuildProcessWorkingDaysRows()
      ElMessage.success(res.message || '共通稼働日を保存しました')
    } else {
      if (!selectedProcessCd.value) {
        ElMessage.warning('工程を選択してください')
        return
      }
      const opt = processWorkingDayOptions.value.find(
        (o) => o.process_cd === selectedProcessCd.value,
      )
      const res = await saveProcessWorkingDays(
        processWorkingDaysRows.value.map((r) => ({
          year: r.year,
          month: r.month,
          process_cd: selectedProcessCd.value,
          process_name: opt?.process_name,
          working_days:
            r.override_days == null || Number.isNaN(Number(r.override_days))
              ? null
              : Number(r.override_days),
        })),
      )
      if (res.data) applyWorkingDaysBundle(res.data)
      ElMessage.success(res.message || '工程別稼働日を保存しました')
    }
    workingDaysDialogVisible.value = false
    await loadTrend()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存に失敗しました')
  } finally {
    workingDaysSaving.value = false
  }
}
function formatNum(n?: number | null) {
  if (n == null || Number.isNaN(n)) return '—'
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })
}
function formatYen(n?: number | null) {
  return `¥${formatNum(n)}`
}
function formatDt(v?: string | null) {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '—'
}
function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
function matchLabel(s: string) {
  if (s === 'matched') return '成功'
  if (s === 'multi_match') return '複数'
  return '未紐付'
}

async function loadMonths() {
  monthOptions.value = await fetchBudgetMonths()
  if (!filterYearMonth.value && monthOptions.value.length) {
    const m = monthOptions.value[0]
    filterYearMonth.value = `${m.year}-${m.month}`
  }
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    const data = await fetchBudgetSummary({
      year: selectedYear.value,
      month: selectedMonth.value,
    })
    Object.assign(summary, data)
  } finally {
    summaryLoading.value = false
  }
}

async function loadImports() {
  importsLoading.value = true
  try {
    imports.value = await fetchBudgetImports(30)
  } finally {
    importsLoading.value = false
  }
}

async function loadList() {
  listLoading.value = true
  try {
    const res = await fetchBudgetList({
      year: selectedYear.value,
      month: selectedMonth.value,
      keyword: listKeyword.value || undefined,
      match_status: listMatchStatus.value,
      page: listPage.value,
      page_size: listPageSize.value,
    })
    listItems.value = res.items
    listTotal.value = res.total
  } finally {
    listLoading.value = false
  }
}

function ensureYm(): { year: number; month: number } | null {
  if (!selectedYear.value || !selectedMonth.value) {
    ElMessage.warning('対象年月を選択してください（先にCSVを取込んでください）')
    return null
  }
  return { year: selectedYear.value, month: selectedMonth.value }
}

async function loadTrend() {
  trendLoading.value = true
  processTrendLoading.value = true
  try {
    const [trend, processTrend] = await Promise.all([
      fetchBudgetTrend(),
      fetchProcessTrend(),
      loadWorkingDays(),
    ])
    trendRows.value = trend
    processTrendMonths.value = processTrend.months || []
    processTrendList.value = processTrend.processes || []
    await nextTick()
    renderTrendChart()
    await nextTick()
    renderProcessTrendMinis()
  } finally {
    trendLoading.value = false
    processTrendLoading.value = false
  }
}

async function loadProcess() {
  const ym = ensureYm()
  if (!ym) return
  processLoading.value = true
  try {
    processRows.value = await fetchProcessLoad(ym.year, ym.month)
    await nextTick()
    renderProcessChart()
  } finally {
    processLoading.value = false
  }
}

async function loadEquipment() {
  const ym = ensureYm()
  if (!ym) return
  equipLoading.value = true
  try {
    equipRows.value = await fetchEquipmentLoad(ym.year, ym.month)
    await nextTick()
    renderEquipChart()
  } finally {
    equipLoading.value = false
  }
}

async function loadCost() {
  const ym = ensureYm()
  if (!ym) return
  costLoading.value = true
  try {
    const res = await fetchCostAnalysis(ym.year, ym.month)
    costRows.value = res.items
    Object.assign(costTotals, res.totals)
  } finally {
    costLoading.value = false
  }
}

function renderTrendChart() {
  if (!trendChartRef.value) return
  if (!trendRows.value.length) {
    trendChart?.clear()
    return
  }
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value, null, { renderer: 'canvas' })
  }
  const labels = trendRows.value.map((r) => r.label)
  const qtys = trendRows.value.map((r) => r.total_budget_qty)
  const avgDaily = trendRows.value.map((r) =>
    r.avg_daily_qty != null ? Math.round(r.avg_daily_qty) : null,
  )
  const maxQty = Math.max(...qtys, 0)
  const qtyPad = maxQty > 0 ? maxQty * 0.22 : 10

  trendChart.setOption(
    {
      backgroundColor: 'transparent',
      animationDuration: 780,
      animationEasing: 'cubicOut',
      textStyle: {
        fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans JP", sans-serif',
      },
      color: ['#3b82f6', '#ea580c'],
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          crossStyle: { color: '#94a3b8' },
          lineStyle: { type: 'dashed', color: '#94a3b8' },
        },
        backgroundColor: 'rgba(255,255,255,0.97)',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        padding: [12, 14],
        extraCssText: 'box-shadow:0 12px 36px rgba(15,23,42,0.12);border-radius:12px;',
        textStyle: { color: '#334155', fontSize: 12 },
        formatter: (params: unknown) => {
          const list = Array.isArray(params) ? params : [params]
          const idx = (list[0] as { dataIndex?: number })?.dataIndex ?? 0
          const row = trendRows.value[idx]
          if (!row) return ''
          const avgText =
            row.avg_daily_qty != null ? formatInt(Math.round(row.avg_daily_qty)) : '—（稼働日未設定）'
          return `
            <div style="font-weight:700;margin-bottom:8px;font-size:13px">${row.year}年${row.month}月</div>
            <div style="display:flex;justify-content:space-between;gap:20px;margin:4px 0">
              <span style="color:#64748b">予算数量</span>
              <b style="font-variant-numeric:tabular-nums;color:#2563eb">${formatInt(row.total_budget_qty)}</b>
            </div>
            <div style="display:flex;justify-content:space-between;gap:20px;margin:4px 0">
              <span style="color:#64748b">稼働日数</span>
              <b style="font-variant-numeric:tabular-nums">${row.working_days || 0}</b>
            </div>
            <div style="display:flex;justify-content:space-between;gap:20px;margin:4px 0">
              <span style="color:#64748b">日平均生産数量</span>
              <b style="font-variant-numeric:tabular-nums;color:#c2410c">${avgText}</b>
            </div>
            <div style="display:flex;justify-content:space-between;gap:20px;margin:4px 0">
              <span style="color:#64748b">品番数</span>
              <b style="font-variant-numeric:tabular-nums">${formatInt(row.product_count)}</b>
            </div>
          `
        },
      },
      legend: {
        data: [
          { name: '予算数量', icon: 'roundRect' },
          { name: '日平均生産数量', icon: 'circle' },
        ],
        top: 4,
        right: 8,
        itemGap: 18,
        itemWidth: 12,
        itemHeight: 10,
        textStyle: { fontSize: 12, color: '#64748b', fontWeight: 600 },
      },
      grid: { left: 56, right: 62, top: 52, bottom: 48, containLabel: false },
      xAxis: {
        type: 'category',
        data: labels,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
        axisLabel: {
          fontSize: 12,
          fontWeight: 600,
          color: '#475569',
          margin: 14,
          formatter: (val: string) => {
            const parts = String(val).split('/')
            if (parts.length === 2) return `{y|${parts[0]}/}{m|${parts[1]}}`
            return val
          },
          rich: {
            y: { color: '#94a3b8', fontSize: 11, fontWeight: 500 },
            m: { color: '#1e293b', fontSize: 12, fontWeight: 700 },
          },
        },
      },
      yAxis: [
        {
          type: 'value',
          min: 0,
          max: maxQty + qtyPad,
          axisLabel: {
            fontSize: 11,
            color: '#94a3b8',
            formatter: (v: number) => (v >= 10000 ? `${(v / 1000).toFixed(0)}k` : String(v)),
          },
          splitLine: { lineStyle: { type: 'dashed', color: '#eef2f7', width: 1 } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        {
          type: 'value',
          min: 38000,
          max: 60000,
          axisLabel: {
            fontSize: 11,
            color: '#94a3b8',
            formatter: (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)),
          },
          splitLine: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
        },
      ],
      series: [
        {
          name: '予算数量',
          type: 'bar',
          barMaxWidth: 48,
          data: qtys.map((v) => {
            const isPeak = v === maxQty && maxQty > 0
            return {
              value: v,
              itemStyle: {
                borderRadius: [8, 8, 4, 4],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: isPeak ? '#93c5fd' : '#60a5fa' },
                  { offset: 0.45, color: '#3b82f6' },
                  { offset: 1, color: isPeak ? '#1e40af' : '#1d4ed8' },
                ]),
                shadowBlur: isPeak ? 16 : 10,
                shadowColor: isPeak ? 'rgba(37, 99, 235, 0.35)' : 'rgba(37, 99, 235, 0.22)',
                shadowOffsetY: isPeak ? 5 : 4,
                borderColor: isPeak ? 'rgba(255,255,255,0.55)' : 'transparent',
                borderWidth: isPeak ? 1 : 0,
              },
            }
          }),
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: '#1e3a8a',
            fontSize: 11,
            fontWeight: 700,
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            formatter: (p: { value?: number | string; dataIndex?: number }) => {
              const n = Number(p.value ?? 0)
              const qtyText = n ? n.toLocaleString() : '0'
              const days = trendRows.value[p.dataIndex ?? 0]?.working_days || 0
              const dayText = days > 0 ? `${days}日` : '—'
              return `{q|${qtyText}}\n{d|${dayText}}`
            },
            rich: {
              q: {
                color: '#1e3a8a',
                fontSize: 11,
                fontWeight: 700,
                lineHeight: 16,
                align: 'center',
              },
              d: {
                color: '#0369a1',
                fontSize: 10,
                fontWeight: 700,
                lineHeight: 14,
                align: 'center',
                padding: [2, 0, 0, 0],
              },
            },
          },
          emphasis: {
            focus: 'series',
            itemStyle: {
              shadowBlur: 18,
              shadowColor: 'rgba(37, 99, 235, 0.4)',
            },
          },
        },
        {
          name: '日平均生産数量',
          type: 'line',
          yAxisIndex: 1,
          data: avgDaily,
          connectNulls: false,
          smooth: 0.35,
          symbol: 'circle',
          symbolSize: 10,
          showSymbol: true,
          lineStyle: {
            width: 3,
            color: '#ea580c',
            shadowBlur: 6,
            shadowColor: 'rgba(234, 88, 12, 0.35)',
          },
          itemStyle: {
            color: '#ea580c',
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            position: 'top',
            distance: 6,
            color: '#c2410c',
            fontSize: 10,
            fontWeight: 700,
            backgroundColor: 'rgba(255, 247, 237, 0.95)',
            borderColor: 'rgba(251, 146, 60, 0.45)',
            borderWidth: 1,
            borderRadius: 4,
            padding: [2, 5],
            formatter: (p: { value?: number | string | null }) => {
              if (p.value == null || p.value === '') return ''
              return Number(p.value).toLocaleString(undefined, { maximumFractionDigits: 1 })
            },
          },
          z: 3,
        },
      ],
    },
    { notMerge: true },
  )
}

function disposeProcessTrendCharts() {
  processMiniCharts.forEach((c) => c.dispose())
  processMiniCharts.clear()
}

function renderProcessTrendMinis() {
  // dispose removed charts
  for (const [cd, chart] of [...processMiniCharts.entries()]) {
    if (!processMiniEls.has(cd)) {
      chart.dispose()
      processMiniCharts.delete(cd)
    }
  }

  const labels = processTrendMonths.value.map((m) => m.label)
  processTrendList.value.forEach((proc, idx) => {
    const el = processMiniEls.get(proc.process_cd)
    if (!el) return
    let chart = processMiniCharts.get(proc.process_cd)
    if (!chart) {
      chart = echarts.init(el, null, { renderer: 'canvas' })
      processMiniCharts.set(proc.process_cd, chart)
    }
    const color = PROCESS_TREND_COLORS[idx % PROCESS_TREND_COLORS.length]
    const maxV = Math.max(...proc.series, 0)
    // 日平均：后端値を優先、無ければ工程実効稼働日で自動算出（整数）
    const avgSeries = proc.series.map((qty, i) => {
      const fromApi = proc.avg_daily_series?.[i]
      if (fromApi != null && !Number.isNaN(Number(fromApi))) return Math.round(Number(fromApi))
      const days =
        proc.working_days_series?.[i] ?? processTrendMonths.value[i]?.working_days ?? 0
      if (!days || days <= 0) return null
      return Math.round(qty / days)
    })
    const avgVals = avgSeries.filter((v): v is number => v != null && !Number.isNaN(v))
    const maxAvg = avgVals.length ? Math.max(...avgVals) : 0
    const minAvg = avgVals.length ? Math.min(...avgVals) : 0
    // 折線が柱の中帯に来るよう右軸を調整
    const avgMid = avgVals.length ? (minAvg + maxAvg) / 2 : 0
    const avgSpan = Math.max(maxAvg - minAvg, maxAvg * 0.25, 1)
    const avgAxisMin = Math.max(0, avgMid - avgSpan * 1.35)
    const avgAxisMax = avgMid + avgSpan * 1.35 || 10

    chart.setOption(
      {
        backgroundColor: 'transparent',
        animationDuration: 560,
        legend: {
          data: [
            { name: '予算数量', icon: 'roundRect' },
            { name: '日平均', icon: 'circle' },
          ],
          top: 0,
          right: 4,
          itemWidth: 10,
          itemHeight: 8,
          itemGap: 10,
          textStyle: { fontSize: 10, color: '#64748b', fontWeight: 600 },
        },
        grid: { left: 40, right: 48, top: 32, bottom: 36 },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15,23,42,0.88)',
          borderWidth: 0,
          textStyle: { color: '#f8fafc', fontSize: 11 },
          formatter: (params: unknown) => {
            const list = Array.isArray(params) ? params : [params]
            const idx0 = (list[0] as { dataIndex?: number; axisValue?: string })?.dataIndex ?? 0
            const axis = (list[0] as { axisValue?: string })?.axisValue || ''
            const days =
              proc.working_days_series?.[idx0] ??
              processTrendMonths.value[idx0]?.working_days ??
              0
            const qty = proc.series[idx0] ?? 0
            const avg = avgSeries[idx0]
            const avgText = avg != null ? formatInt(Math.round(avg)) : '—'
            const override = proc.working_days_override_series?.[idx0]
            const dayNote = override ? '（工程指定）' : ''
            return `${axis}<br/>予算数量: <b>${formatInt(qty)}</b><br/>稼働日: ${days}${dayNote}<br/>日平均: <b>${avgText}</b>`
          },
        },
        xAxis: {
          type: 'category',
          data: labels,
          axisTick: { show: false },
          axisLine: { lineStyle: { color: '#e2e8f0' } },
          axisLabel: {
            fontSize: 10,
            color: '#64748b',
            margin: 12,
            rotate: labels.length > 6 ? 30 : 0,
          },
        },
        yAxis: [
          {
            type: 'value',
            min: 0,
            max: maxV > 0 ? maxV * 1.28 : 10,
            axisLabel: {
              fontSize: 9,
              color: '#94a3b8',
              formatter: (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)),
            },
            splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
          },
          {
            type: 'value',
            min: avgAxisMin,
            max: avgAxisMax,
            axisLabel: {
              fontSize: 9,
              color: '#94a3b8',
              formatter: (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)),
            },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            name: '予算数量',
            type: 'bar',
            data: proc.series,
            barMaxWidth: 28,
            itemStyle: {
              borderRadius: [5, 5, 2, 2],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color },
                { offset: 1, color: color + '99' },
              ]),
            },
            label: {
              show: true,
              position: 'top',
              distance: 4,
              color: '#334155',
              fontSize: 9,
              fontWeight: 700,
              formatter: (p: { value?: number | string; dataIndex?: number }) => {
                const n = Number(p.value ?? 0)
                const qtyText = n ? n.toLocaleString() : '0'
                const days =
                  proc.working_days_series?.[p.dataIndex ?? 0] ??
                  processTrendMonths.value[p.dataIndex ?? 0]?.working_days ??
                  0
                const dayText = days > 0 ? `${days}日` : '—'
                return `{q|${qtyText}}\n{d|${dayText}}`
              },
              rich: {
                q: {
                  color: '#334155',
                  fontSize: 9,
                  fontWeight: 700,
                  lineHeight: 13,
                  align: 'center',
                },
                d: {
                  color: '#0369a1',
                  fontSize: 9,
                  fontWeight: 700,
                  lineHeight: 12,
                  align: 'center',
                  padding: [1, 0, 0, 0],
                },
              },
            },
          },
          {
            name: '日平均',
            type: 'line',
            yAxisIndex: 1,
            data: avgSeries,
            connectNulls: false,
            smooth: 0.3,
            symbol: 'circle',
            symbolSize: 8,
            showSymbol: true,
            lineStyle: {
              width: 2.5,
              color: '#ea580c',
              shadowBlur: 4,
              shadowColor: 'rgba(234, 88, 12, 0.3)',
            },
            itemStyle: {
              color: '#ea580c',
              borderColor: '#fff',
              borderWidth: 1.5,
            },
            label: {
              show: true,
              position: 'bottom',
              distance: 6,
              color: '#c2410c',
              fontSize: 9,
              fontWeight: 700,
              backgroundColor: 'rgba(255, 247, 237, 0.95)',
              borderColor: 'rgba(251, 146, 60, 0.4)',
              borderWidth: 1,
              borderRadius: 3,
              padding: [2, 4],
              formatter: (p: {
                value?: number | string | null
                dataIndex?: number
              }) => {
                if (p.value == null || p.value === '') return ''
                return Number(p.value).toLocaleString(undefined, { maximumFractionDigits: 1 })
              },
            },
            labelLayout: {
              hideOverlap: true,
            },
            z: 3,
          },
        ],
      },
      { notMerge: true },
    )
  })
}

function renderBar(chart: echarts.ECharts | null, el: HTMLDivElement | null, rows: { name: string; value: number }[], color: string) {
  if (!el) return chart
  if (!chart) chart = echarts.init(el)
  const top = rows.slice(0, 15).reverse()
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 24, top: 16, bottom: 24 },
    xAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
    yAxis: { type: 'category', data: top.map((r) => r.name), axisLabel: { fontSize: 11, width: 90, overflow: 'truncate' } },
    series: [
      {
        type: 'bar',
        data: top.map((r) => r.value),
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color },
            { offset: 1, color: color + '99' },
          ]),
        },
        label: { show: true, position: 'right', fontSize: 10 },
      },
    ],
  })
  return chart
}

function renderProcessChart() {
  processChart = renderBar(
    processChart,
    processChartRef.value,
    processRows.value.map((r) => ({ name: r.process_name || r.process_cd, value: r.total_hours })),
    '#7c3aed',
  )
}

function renderEquipChart() {
  equipChart = renderBar(
    equipChart,
    equipChartRef.value,
    equipRows.value.map((r) => ({ name: r.machine_name || r.machine_cd, value: r.total_hours })),
    '#0891b2',
  )
}

function onFileChange(file: UploadFile) {
  selectedFile.value = (file.raw as File) || null
}

async function doUpload() {
  if (!selectedFile.value) return
  if (!canCreate.value) {
    ElMessage.warning('取込権限がありません')
    return
  }
  uploading.value = true
  try {
    lastUpload.value = await uploadBudgetCsv(selectedFile.value)
    ElMessage.success(lastUpload.value.message || '取込完了')
    selectedFile.value = null
    await loadMonths()
    if (lastUpload.value.months?.length) {
      const m = lastUpload.value.months[0]
      filterYearMonth.value = `${m.year}-${m.month}`
    }
    await Promise.all([loadSummary(), loadImports(), loadList()])
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '取込に失敗しました')
  } finally {
    uploading.value = false
  }
}

async function confirmDeleteMonth() {
  const ym = ensureYm()
  if (!ym) return
  try {
    await ElMessageBox.confirm(
      `${ym.year}年${ym.month}月の予算データをすべて削除します。よろしいですか？`,
      '削除確認',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: '取消' },
    )
    const res = await deleteBudgetMonth(ym.year, ym.month)
    ElMessage.success(res.message || '削除しました')
    filterYearMonth.value = ''
    await reloadAll()
  } catch {
    /* cancel */
  }
}

async function onYearMonthChange() {
  await loadSummary()
  if (activeTab.value === 'list') await loadList()
  if (activeTab.value === 'process') await loadProcess()
  if (activeTab.value === 'equipment') await loadEquipment()
  if (activeTab.value === 'cost') await loadCost()
}

async function onTabChange(name: string | number) {
  const tab = String(name)
  if (tab === 'list') await loadList()
  if (tab === 'trend') await loadTrend()
  if (tab === 'process') await loadProcess()
  if (tab === 'equipment') await loadEquipment()
  if (tab === 'cost') await loadCost()
  if (tab === 'upload') await loadImports()
}

async function reloadAll() {
  await loadMonths()
  await loadSummary()
  await onTabChange(activeTab.value)
}

function onResize() {
  trendChart?.resize()
  processMiniCharts.forEach((c) => c.resize())
  processChart?.resize()
  equipChart?.resize()
}

onMounted(async () => {
  await reloadAll()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  trendChart?.dispose()
  disposeProcessTrendCharts()
  processChart?.dispose()
  equipChart?.dispose()
})

function onListPageSizeChange() {
  listPage.value = 1
  loadList()
}
</script>

<style scoped lang="scss">
.budget-page {
  --budget-blue: #2563eb;
  --budget-violet: #7c3aed;
  --budget-teal: #0d9488;
  --budget-amber: #d97706;
  position: relative;
  min-height: 100%;
  padding: 12px 14px 20px;
  overflow: hidden;
}

.dynamic-background {
  pointer-events: none;
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.35;
}
.orb-1 {
  width: 320px;
  height: 320px;
  top: -80px;
  right: -40px;
  background: radial-gradient(circle, #93c5fd 0%, transparent 70%);
}
.orb-2 {
  width: 280px;
  height: 280px;
  bottom: 10%;
  left: -60px;
  background: radial-gradient(circle, #c4b5fd 0%, transparent 70%);
}
.orb-3 {
  width: 220px;
  height: 220px;
  top: 40%;
  right: 20%;
  background: radial-gradient(circle, #99f6e4 0%, transparent 70%);
}

.page-head,
.kpi-row,
.budget-tabs,
.panel,
.guide-panel {
  position: relative;
  z-index: 1;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
}
.page-head-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #2563eb 0%, #60a5fa 100%);
  flex-shrink: 0;
}
.page-head-text {
  flex: 1;
  min-width: 0;
}
.page-head-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.page-head-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}
.page-head-filters {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}
.ym-select {
  width: 150px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.kpi-row--compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 8px;
}
.kpi-card {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
}
.kpi-card__label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}
.kpi-card__value {
  margin-top: 2px;
  font-size: 22px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  line-height: 1.2;
}
.kpi-card__value--sm {
  font-size: 18px;
}
.kpi-card__hint {
  margin-top: 2px;
  font-size: 10px;
  color: #94a3b8;
}
.kpi-card--blue {
  border-top: 3px solid #2563eb;
}
.kpi-card--violet {
  border-top: 3px solid #7c3aed;
}
.kpi-card--green {
  border-top: 3px solid #059669;
}
.kpi-card--amber {
  border-top: 3px solid #d97706;
}
.kpi-card--slate {
  border-top: 3px solid #64748b;
}

.budget-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 10px;
  }
  :deep(.el-tabs__item) {
    font-weight: 600;
    font-size: 13px;
  }
  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
  }
}

.tab-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 10px;
}
.analysis-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.panel {
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.22);
  margin-bottom: 10px;
}
.panel__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}
.panel__desc {
  margin: 0 0 10px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  strong {
    color: #b45309;
  }
}

.budget-uploader {
  width: 100%;
  :deep(.el-upload-dragger) {
    width: 100%;
    padding: 28px 16px;
    border-radius: 10px;
    border: 1.5px dashed #93c5fd;
    background: linear-gradient(180deg, #eff6ff 0%, #f8fafc 100%);
    transition: border-color 0.2s, transform 0.15s;
    &:hover {
      border-color: #2563eb;
      transform: translateY(-1px);
    }
  }
}
.upload-inner {
  text-align: center;
}
.upload-icon {
  color: #2563eb;
  margin-bottom: 6px;
}
.upload-text {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.upload-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f1f5f9;
  font-size: 12px;
}
.selected-file__name {
  font-weight: 600;
  color: #0f172a;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.selected-file__size {
  color: #64748b;
}

.upload-result {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
}
.upload-result__title {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #334155;
}
.upload-result__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  font-size: 12px;
  div {
    display: flex;
    justify-content: space-between;
    padding: 6px 8px;
    border-radius: 6px;
    background: #f8fafc;
    span {
      color: #64748b;
    }
    b {
      font-variant-numeric: tabular-nums;
    }
    b.ok {
      color: #059669;
    }
    b.warn {
      color: #d97706;
    }
  }
}

.guide-panel {
  margin-top: 0;
}
.guide-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #475569;
  line-height: 1.7;
  code {
    padding: 1px 5px;
    border-radius: 4px;
    background: #f1f5f9;
    font-size: 11px;
    color: #1d4ed8;
  }
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.toolbar__search {
  width: 260px;
  min-width: 160px;
}
.w-140 {
  width: 140px;
}
.data-table {
  width: 100%;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.chart-box {
  width: 100%;
  height: 280px;
}
.chart-box--tall {
  height: 400px;
}
.chart-box--trend {
  height: 400px;
  min-height: 340px;
}
.chart-box--process-mini {
  height: 280px;
}

.process-trend-panel {
  margin-top: 10px;
}
.process-trend-desc {
  margin-top: -2px;
  margin-bottom: 10px;
}
.process-trend-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.process-trend-card {
  padding: 10px 10px 6px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.22);
}
.process-trend-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 2px;
}
.process-trend-card__title {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.process-trend-card__rank {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, #2563eb, #60a5fa);
}
.process-trend-card__name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.process-trend-card__total {
  flex-shrink: 0;
  font-size: 11px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
  b {
    color: #1e40af;
    font-size: 13px;
  }
}

@media (max-width: 1100px) {
  .process-trend-grid {
    grid-template-columns: 1fr;
  }
}

.trend-panel {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.88) 100%);
}
.wd-dialog-desc {
  margin: 0 0 10px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  strong {
    color: #b45309;
  }
}
.wd-tabs {
  margin-top: 4px;
}
.wd-process-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.wd-process-label {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}
.wd-process-hint {
  font-size: 11px;
  color: #94a3b8;
}
.wd-default-days {
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.wd-effective {
  font-weight: 700;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.wd-effective--override {
  color: #0369a1;
}
.wd-table {
  width: 100%;
}
.wd-input {
  width: 110px;
}
.wd-override-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.avg-cell {
  font-weight: 700;
  color: #c2410c;
  font-variant-numeric: tabular-nums;
}
.avg-cell--empty {
  color: #94a3b8;
  font-weight: 500;
}
.trend-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.trend-panel__title-left {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.trend-panel__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 0;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.trend-panel__meta .dot {
  margin: 0 4px;
  opacity: 0.5;
}

.mt-8 {
  margin-top: 8px;
}
.neg {
  color: #dc2626;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .tab-grid,
  .analysis-layout {
    grid-template-columns: 1fr;
  }
  .page-head {
    flex-wrap: wrap;
  }
}
</style>
