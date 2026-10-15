<template>
  <div class="eqc-page pb-std" :class="`eqc-page--${processCd}`">
    <header class="eqc-hero page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="pb-bubbles" aria-hidden="true" />
      <div class="eqc-hero__main">
        <span class="eqc-mark">{{ mark }}</span>
        <div>
          <h1 class="pb-hero-title">{{ processLabel }}設備能力</h1>
          <p>定時間・直・残業・能率/H・可動率・合格率から、設備の月間負荷を見ます。</p>
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
          <el-button type="warning" size="small" @click="openAdd">
            <el-icon><Plus /></el-icon>
            設備を追加
          </el-button>
          <el-button class="eqc-btn-teal" size="small" @click="openImport">
            <el-icon><Download /></el-icon>
            マスタから取込
            <span v-if="suggestions.length" class="eqc-count">{{ suggestions.length }}</span>
          </el-button>
        </div>
      </div>
    </header>

    <section class="eqc-kpis" aria-label="能力サマリ">
      <p class="eqc-kpis__scope">{{ kpiTitle }}</p>
      <div class="eqc-kpis__grid">
        <article class="eqc-kpi eqc-kpi--blue">
          <span class="eqc-kpi__icon"><el-icon><Timer /></el-icon></span>
          <div>
            <p>月間総時間</p>
            <strong>{{ fmtNum(kpi.total_hours, 1) }}<small> H</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--purple">
          <span class="eqc-kpi__icon"><el-icon><Histogram /></el-icon></span>
          <div>
            <p>占有時間</p>
            <strong>{{ fmtNum(kpi.occupied_hours, 1) }}<small> H</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--amber">
          <span class="eqc-kpi__icon"><el-icon><PieChart /></el-icon></span>
          <div>
            <p>設備占有率</p>
            <strong>{{ fmtNum(kpi.occupancy_pct, 1) }}<small> %</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--green">
          <span class="eqc-kpi__icon"><el-icon><CircleCheck /></el-icon></span>
          <div>
            <p>月当判定</p>
            <strong :class="judgeClass(kpi.month_judgment)">{{ judgmentLabel(kpi.month_judgment) }}</strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--teal">
          <span class="eqc-kpi__icon"><el-icon><Clock /></el-icon></span>
          <div>
            <p>残時間</p>
            <strong :class="{ 'is-neg': kpi.remain_hours < -0.05 }">{{ fmtNum(kpi.remain_hours, 1) }}<small> H</small></strong>
          </div>
        </article>
        <article class="eqc-kpi eqc-kpi--pink">
          <span class="eqc-kpi__icon"><el-icon><Odometer /></el-icon></span>
          <div>
            <p>最大能率</p>
            <strong>{{ fmtNum(kpi.peak_hourly, 1) }}<small> 本/H</small></strong>
          </div>
        </article>
      </div>
    </section>

    <div class="eqc-body">
      <aside class="eqc-list" v-loading="listLoading">
        <div class="eqc-list__head">
          <el-input v-model="keyword" size="small" clearable placeholder="設備名・コード" />
          <span class="eqc-list__meta">
            {{ equipments.length }}台
            <b :class="judgeClass(aggregate.month_judgment)">{{ judgmentLabel(aggregate.month_judgment) }}</b>
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
          <span class="eqc-card__name">{{ eq.machine_name }}</span>
          <span class="eqc-card__cd">{{ eq.machine_cd }}</span>
          <span class="eqc-card__line">
            {{ fmtNum(eq.shift_count, 0) }}直 · 定時 {{ fmtNum(eq.regular_hours, 1) }}h · {{ fmtNum(eq.working_days, 0) }}日
          </span>
          <span class="eqc-card__stats">
            <em>{{ fmtNum(cardSummary(eq).occupancy_pct, 1) }}%</em>
            <em>{{ fmtNum(cardSummary(eq).peak_hourly, 1) }} 能率</em>
            <b :class="judgeClass(cardSummary(eq).month_judgment)">{{ judgmentLabel(cardSummary(eq).month_judgment) }}</b>
          </span>
        </button>
        <p v-if="!listLoading && !visibleEquipments.length" class="eqc-muted">
          この工程の設備はまだありません。追加するか、マスタから取り込んでください。
        </p>
      </aside>

      <section v-if="draft" v-loading="detailLoading" class="eqc-detail">
        <div class="eqc-cond">
          <label class="eqc-field">
            <span>設備名</span>
            <el-input v-model="draft.machine_name" size="small" maxlength="100" @input="touch" />
          </label>
          <label class="eqc-field">
            <span>設備コード</span>
            <el-input v-model="draft.machine_cd" size="small" maxlength="50" @input="touch" />
          </label>
          <label class="eqc-field">
            <span>定時間 (h/直)</span>
            <el-input-number v-model="draft.regular_hours" size="small" :min="0" :max="24" :step="0.1" :precision="1" :controls="false" @change="touch" />
          </label>
          <label class="eqc-field">
            <span>直</span>
            <el-input-number v-model="draft.shift_count" size="small" :min="1" :max="3" :step="1" :precision="0" :controls="false" @change="touch" />
          </label>
          <label class="eqc-field">
            <span>残業 (h/直)</span>
            <el-input-number v-model="draft.overtime_hours" size="small" :min="0" :max="12" :step="0.5" :precision="1" :controls="false" @change="touch" />
          </label>
          <label class="eqc-field">
            <span>稼働日数 (日/月)</span>
            <el-input-number v-model="draft.working_days" size="small" :min="0" :max="31" :step="1" :precision="0" :controls="false" @change="touch" />
          </label>
          <label class="eqc-field eqc-field--ro">
            <span>1日の稼働可能</span>
            <b>{{ fmtNum(headerCalc.daily_available, 2) }} H</b>
          </label>
          <label class="eqc-field eqc-field--ro">
            <span>月間総時間</span>
            <b>{{ fmtNum(headerCalc.total_hours, 2) }} H</b>
          </label>
          <label class="eqc-field eqc-field--wide">
            <span>備考</span>
            <el-input v-model="draft.note" size="small" maxlength="500" @input="touch" />
          </label>
        </div>

        <div class="eqc-actions">
          <label class="eqc-month">
            <span>対象月</span>
            <el-date-picker
              v-model="targetMonth"
              type="month"
              value-format="YYYY-MM"
              size="small"
              :clearable="false"
              placeholder="年月"
            />
          </label>
          <el-button class="eqc-btn-amber" size="small" :loading="loadingForecast" :disabled="!targetMonth" @click="applyForecast">
            内示を設定数へ
          </el-button>
          <el-button type="primary" size="small" @click="addRow">
            <el-icon><Plus /></el-icon>
            行を追加
          </el-button>
          <el-button class="eqc-btn-teal" size="small" @click="applyDays">稼働日数を明細へ</el-button>
          <el-button class="eqc-btn-indigo" size="small" :loading="importingRates" @click="importRates">
            設備能率から品目
          </el-button>
          <el-button class="eqc-btn-teal" size="small" :loading="refreshingMetrics" @click="refreshMetrics">
            指標を更新
          </el-button>
          <el-button type="danger" size="small" plain @click="removeEquipment">設備を削除</el-button>
          <el-button type="success" size="small" :loading="saving" :disabled="!dirty" @click="save">
            保存
          </el-button>
          <span class="eqc-actions__judge">
            日当 {{ judgmentLabel(totals.daily_judgment) }}
            · 月当 <b :class="judgeClass(totals.month_judgment)">{{ judgmentLabel(totals.month_judgment) }}</b>
            · 占有 {{ fmtNum(totals.occupancy_pct, 1) }}%
          </span>
        </div>

        <el-collapse class="eqc-help">
          <el-collapse-item title="計算式（生産能力調査と同じ）" name="formula">
            <ul>
              <li>総時間 =（定時間 + 残業）× 直 × 稼働日数</li>
              <li>日当数 = 設定数 ÷ 稼働日数</li>
              <li>生産時間 = 日当数 ÷ (能率/H × 可動率 × 合格率)</li>
              <li>稼働時間 = 生産時間 + 段取り（生産が無い行は 0）</li>
              <li>加重平均 = 設定稼働日数 ÷ 実生産日数 × 生産時間 + 段取り</li>
              <li>占有時間 = 加重平均 × 実生産日数。占有率 = 占有時間合計 ÷ 総時間</li>
              <li>日当判定は稼働時間の合計が 1 日の稼働可能を超えると ×。月当判定は占有時間が総時間を超えると ×</li>
              <li>能率/H は設備能率、可動率は設備マスタ、合格率は廃棄率分析と同口径の直近3ヶ月実績から取得します</li>
              <li>「内示を設定数へ」は月受注の内示本数を、製品CD末尾を 1 にそろえて合算し、設定数/月へ反映します</li>
            </ul>
          </el-collapse-item>
        </el-collapse>

        <el-table :data="draft.items" size="small" border stripe class="eqc-table" :max-height="tableMax">
          <el-table-column label="#" width="46" fixed="left" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column label="部品番号" width="120" fixed="left">
            <template #default="{ row }">
              <el-input v-model="row.part_no" size="small" maxlength="50" @input="touch" />
            </template>
          </el-table-column>
          <el-table-column label="部品名" width="160" fixed="left">
            <template #default="{ row }">
              <el-input v-model="row.part_name" size="small" maxlength="100" @input="touch" />
            </template>
          </el-table-column>
          <el-table-column label="設定数/月" width="110" align="right">
            <template #default="{ row }">
              <el-input-number v-model="row.monthly_qty" size="small" :min="0" :step="100" :precision="0" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="日数" width="78" align="right">
            <template #header><span title="設定数に対する稼働日数">日数</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.qty_days" size="small" :min="0" :max="31" :precision="1" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="日当" width="78" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).daily_qty, 0) }}</span></template>
          </el-table-column>
          <el-table-column label="能率/H" width="90" align="right">
            <template #header><span title="設備能率テーブルの本/H">能率/H</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.rate_per_hour" size="small" :min="0" :precision="1" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="可動率%" width="84" align="right">
            <template #header><span title="設備マスタの可動率">可動率%</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.availability_pct" size="small" :min="0" :max="100" :precision="1" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="合格率%" width="84" align="right">
            <template #header><span title="廃棄率分析と同口径・直近3ヶ月実績の加重平均">合格率%</span></template>
            <template #default="{ row }">
              <el-input-number v-model="row.pass_rate_pct" size="small" :min="0" :max="100" :precision="2" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="生産H" width="76" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).production_hours, 2) }}</span></template>
          </el-table-column>
          <el-table-column label="段取H" width="80" align="right">
            <template #default="{ row }">
              <el-input-number v-model="row.setup_hours" size="small" :min="0" :precision="2" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="稼働H" width="76" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).operating_hours, 2) }}</span></template>
          </el-table-column>
          <el-table-column label="実日数" width="78" align="right">
            <template #default="{ row }">
              <el-input-number v-model="row.actual_days" size="small" :min="0" :max="31" :precision="1" :controls="false" class="eqc-num" @change="touch" />
            </template>
          </el-table-column>
          <el-table-column label="加重H" width="76" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).weighted_hours, 2) }}</span></template>
          </el-table-column>
          <el-table-column label="占有H" width="76" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).occupied_hours, 2) }}</span></template>
          </el-table-column>
          <el-table-column label="占有%" width="70" align="right">
            <template #default="{ row }"><span class="eqc-ro">{{ fmtNum(lineCalc(row).occupancy_pct, 1) }}</span></template>
          </el-table-column>
          <el-table-column label="判定" width="58" align="center">
            <template #default="{ row }">
              <b :class="judgeClass(lineCalc(row).daily_judgment)">{{ judgmentLabel(lineCalc(row).daily_judgment) }}</b>
            </template>
          </el-table-column>
          <el-table-column label="" width="108" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" @click="openTakt(row.key)">タクト</el-button>
              <el-button link type="danger" @click="removeRow(row.key)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section v-else class="eqc-placeholder">
        <el-empty description="設備を選ぶと、品目ごとの能力と負荷を編集できます">
          <el-button type="warning" size="small" @click="openAdd">設備を追加</el-button>
          <el-button class="eqc-btn-teal" size="small" @click="openImport">マスタから取込</el-button>
        </el-empty>
      </section>
    </div>

    <el-dialog v-model="addOpen" title="設備を追加" width="520px" class="eqc-dialog" append-to-body>
      <div class="eqc-form">
        <label><span>設備コード</span><el-input v-model="addForm.machine_cd" maxlength="50" /></label>
        <label><span>設備名</span><el-input v-model="addForm.machine_name" maxlength="100" /></label>
        <label><span>定時間 h/直</span><el-input-number v-model="addForm.regular_hours" :min="0" :max="24" :precision="1" :controls="false" /></label>
        <label><span>直</span><el-input-number v-model="addForm.shift_count" :min="1" :max="3" :precision="0" :controls="false" /></label>
        <label><span>残業 h/直</span><el-input-number v-model="addForm.overtime_hours" :min="0" :max="12" :precision="1" :controls="false" /></label>
        <label><span>稼働日数</span><el-input-number v-model="addForm.working_days" :min="0" :max="31" :precision="0" :controls="false" /></label>
      </div>
      <template #footer>
        <el-button @click="addOpen = false">キャンセル</el-button>
        <el-button type="success" :loading="saving" @click="createEquipment">追加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importOpen" title="未登録の設備を取り込む" width="680px" class="eqc-dialog" append-to-body>
      <p class="eqc-dialog__lead">設備マスタと設備能率から、この工程の未登録設備を追加します。品目も取り込むと、能率/H・可動率・合格率を反映します。</p>
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
        <el-button type="primary" :loading="importing" :disabled="!importPick.length" @click="runImport">
          {{ importPick.length }} 台を追加
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="taktOpen" title="タクトトライ" width="720px" class="eqc-dialog" append-to-body>
      <template v-if="taktRow">
        <p class="eqc-dialog__lead">{{ taktRow.part_no || '（品番未入力）' }} {{ taktRow.part_name }}</p>
        <div class="eqc-takt">
          <section>
            <h3>1回目</h3>
            <label><span>日付</span><el-date-picker v-model="taktRow.takt1_date" type="date" value-format="YYYY-MM-DD" size="small" @change="touch" /></label>
            <label><span>実測CT（秒）</span><el-input-number v-model="taktRow.takt1_ct" :min="0" :precision="3" :controls="false" size="small" @change="touch" /></label>
            <label><span>検査</span><el-select v-model="taktRow.takt1_inspect" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`a-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
            <label><span>準備状況</span><el-select v-model="taktRow.takt1_prep" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`b-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
            <label><span>総合</span><el-select v-model="taktRow.takt1_overall" size="small" @change="touch"><el-option v-for="m in MARKS" :key="`c-${m}`" :label="m || '未入力'" :value="m" /></el-select></label>
          </section>
          <section>
            <h3>2回目</h3>
            <label><span>日付</span><el-date-picker v-model="taktRow.takt2_date" type="date" value-format="YYYY-MM-DD" size="small" @change="touch" /></label>
            <label><span>実測CT（秒）</span><el-input-number v-model="taktRow.takt2_ct" :min="0" :precision="3" :controls="false" size="small" @change="touch" /></label>
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
        <el-button type="primary" @click="taktOpen = false">閉じる</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createEquipmentCapacity,
  deleteEquipmentCapacity,
  fetchEquipmentCapacity,
  fetchEquipmentCapacityDetail,
  fetchEquipmentCapacityForecastMonthly,
  importEquipmentCapacityMaster,
  importEquipmentCapacityRates,
  refreshEquipmentCapacityMetrics,
  saveEquipmentCapacity,
  type CapacityItem,
  type CapacitySummary,
  type EquipmentListItem,
  type EquipmentSuggestion,
} from '@/api/erp/productionEquipmentCapacity'
import {
  calcHeader,
  calcLine,
  calcTotals,
  fmtNum,
  judgmentLabel,
  type Judgment,
  type TotalCalc,
} from './capacityCalc'

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

const route = useRoute()
const router = useRouter()
const processCd = computed(() => String(route.meta.process || 'cutting'))
const processLabel = computed(() => PROCESSES.find((item) => item.cd === processCd.value)?.label || '切断')
const mark = computed(() => ({ cutting: '切', chamfering: '面', forming: '成', welding: '溶' }[processCd.value] || '設'))

const listLoading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const importing = ref(false)
const importingRates = ref(false)
const refreshingMetrics = ref(false)
const loadingForecast = ref(false)
const hydrating = ref(false)
const dirty = ref(false)
const keyword = ref('')
const targetMonth = ref(currentMonthValue())
const equipments = ref<EquipmentListItem[]>([])
const suggestions = ref<EquipmentSuggestion[]>([])
const selectedId = ref<number | null>(null)
const draft = ref<Draft | null>(null)
const tableMax = ref(480)

const addOpen = ref(false)
const addForm = reactive({
  machine_cd: '',
  machine_name: '',
  regular_hours: 7.6,
  shift_count: 2,
  overtime_hours: 0,
  working_days: 22,
})

function currentMonthValue() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function normalizeProductCd(cd: string) {
  const text = (cd || '').trim()
  if (!text) return ''
  return `${text.slice(0, -1)}1`
}
const importOpen = ref(false)
const importPick = ref<EquipmentSuggestion[]>([])
const withProducts = ref(true)
const taktOpen = ref(false)
const taktKey = ref('')

let seq = 0
function uid() {
  seq += 1
  return `n-${Date.now()}-${seq}`
}

function touch() {
  if (!hydrating.value) dirty.value = true
}

function blankItem(days: number): DraftItem {
  return {
    key: uid(),
    part_no: '',
    part_name: '',
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

function lineCalc(item: DraftItem) {
  return calcLine(item, headerCalc.value)
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
  peak_hourly: 0,
})

function cardSummary(eq: EquipmentListItem): CapacitySummary {
  if (draft.value && draft.value.id === eq.id) {
    return { ...emptySummary(), ...totals.value }
  }
  return eq.summary
}

const aggregate = computed<TotalCalc>(() => {
  let total = 0
  let daily = 0
  let production = 0
  let operating = 0
  let occupied = 0
  let peak = 0
  let active = 0
  let items = 0
  let dailyNg = false
  let monthNg = false
  for (const eq of equipments.value) {
    const summary = cardSummary(eq)
    total += Number(summary.total_hours) || 0
    daily += Number(summary.daily_available) || 0
    production += Number(summary.production_hours) || 0
    operating += Number(summary.operating_hours) || 0
    occupied += Number(summary.occupied_hours) || 0
    peak = Math.max(peak, Number(summary.peak_hourly) || 0)
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
    occupancy_pct: total > 0 ? (occupied / total) * 100 : null,
    remain_hours: total - occupied,
    daily_judgment: active <= 0 ? null : dailyNg ? 'ng' : 'ok',
    month_judgment: active <= 0 ? null : monthNg ? 'ng' : 'ok',
    peak_hourly: peak,
  }
})

const kpi = computed(() => (draft.value ? totals.value : aggregate.value))
const kpiTitle = computed(() => (draft.value ? draft.value.machine_name : `${processLabel.value} 合計`))
const taktRow = computed(() => draft.value?.items.find((item) => item.key === taktKey.value) ?? null)

const visibleEquipments = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return equipments.value
  return equipments.value.filter((eq) => `${eq.machine_cd} ${eq.machine_name}`.toLowerCase().includes(q))
})

function judgeClass(value: Judgment) {
  return { 'is-ok': value === 'ok', 'is-ng': value === 'ng' }
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

function resizeTable() {
  tableMax.value = Math.max(280, window.innerHeight - 430)
}

async function loadList() {
  listLoading.value = true
  try {
    const res = await fetchEquipmentCapacity(processCd.value)
    equipments.value = res.data?.equipments || []
    suggestions.value = res.data?.suggestions || []
    if (selectedId.value != null && !equipments.value.some((eq) => eq.id === selectedId.value)) {
      selectedId.value = null
      draft.value = null
      dirty.value = false
    }
  } catch (error) {
    equipments.value = []
    suggestions.value = []
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
      regular_hours: Number(data.regular_hours) || 0,
      shift_count: Number(data.shift_count) || 1,
      overtime_hours: Number(data.overtime_hours) || 0,
      working_days: days,
      note: data.note || '',
      items: (data.items?.length ? data.items : [blankItem(days)]).map((item) => toDraftItem(item, days)),
    }
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
    items: current.items.map((item) => ({
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
    })),
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

function applyDays() {
  if (!draft.value) return
  const days = Number(draft.value.working_days) || 0
  for (const item of draft.value.items) {
    item.qty_days = days
    item.actual_days = days
  }
  touch()
  ElMessage.success('稼働日数を明細へ反映しました。保存はまだです。')
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
    const remaining = new Map(forecastItems.map((item) => [item.product_cd, item]))
    let updated = 0
    for (const row of draft.value.items) {
      const key = normalizeProductCd(row.part_no)
      const hit = remaining.get(key)
      if (!hit) continue
      row.monthly_qty = Number(hit.monthly_qty) || 0
      if (!row.part_name && hit.product_name) row.part_name = hit.product_name
      remaining.delete(key)
      updated += 1
    }
    let added = 0
    const days = Number(draft.value.working_days) || 0
    for (const hit of remaining.values()) {
      const qty = Number(hit.monthly_qty) || 0
      if (qty <= 0) continue
      const row = blankItem(days)
      row.part_no = hit.product_cd
      row.part_name = hit.product_name || ''
      row.monthly_qty = qty
      draft.value.items.push(row)
      added += 1
    }
    touch()
    ElMessage.success(
      `${targetMonth.value} の内示を反映しました（更新 ${updated} / 追加 ${added} / 合計 ${res.data.total_qty.toLocaleString('ja-JP')} 本）`,
    )
  } catch (error) {
    showServerError(error, '内示の取得に失敗しました')
  } finally {
    loadingForecast.value = false
  }
}

async function importRates() {
  if (!draft.value) return
  if (dirty.value) {
    try {
      await ElMessageBox.confirm('未保存の編集は、能率の取り込みで上書きされます。続けますか？', '確認', {
        type: 'warning',
      })
    } catch {
      return
    }
  }
  importingRates.value = true
  try {
    const res = await importEquipmentCapacityRates(processCd.value, draft.value.id)
    await loadList()
    await loadDetail(res.data.id)
    const meta = res.meta
    ElMessage.success(`品目を反映しました（追加 ${meta?.added ?? 0} / 更新 ${meta?.updated ?? 0}）`)
  } catch (error) {
    showServerError(error, '設備能率の取り込みに失敗しました')
  } finally {
    importingRates.value = false
  }
}

async function refreshMetrics() {
  if (!draft.value) return
  if (dirty.value) {
    try {
      await ElMessageBox.confirm('未保存の編集は、指標更新で上書きされます。続けますか？', '確認', {
        type: 'warning',
      })
    } catch {
      return
    }
  }
  refreshingMetrics.value = true
  try {
    const res = await refreshEquipmentCapacityMetrics(processCd.value, draft.value.id)
    await loadList()
    await loadDetail(res.data.id)
    ElMessage.success('能率・可動率・合格率を更新しました')
  } catch (error) {
    showServerError(error, '指標の更新に失敗しました')
  } finally {
    refreshingMetrics.value = false
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

onMounted(() => {
  resizeTable()
  window.addEventListener('resize', resizeTable)
})
onBeforeUnmount(() => window.removeEventListener('resize', resizeTable))
</script>

<style scoped>
.eqc-page {
  width: 100%;
  min-height: calc(100vh - 56px);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px 12px;
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
}
.eqc-page--chamfering {
  --eqc-hero: linear-gradient(125deg, #134e4a 0%, #0f766e 40%, #14b8a6 72%, #5eead4 100%);
  --eqc-shadow: rgba(15, 118, 110, 0.45);
  --eqc-bg1: rgba(13, 148, 136, 0.16);
  --eqc-bg2: rgba(45, 212, 191, 0.12);
  --eqc-accent: #0f766e;
}
.eqc-page--forming {
  --eqc-hero: linear-gradient(125deg, #365314 0%, #4d7c0f 40%, #84cc16 74%, #d9f99d 100%);
  --eqc-shadow: rgba(63, 98, 18, 0.4);
  --eqc-bg1: rgba(101, 163, 13, 0.16);
  --eqc-bg2: rgba(163, 230, 53, 0.14);
  --eqc-accent: #4d7c0f;
}
.eqc-page--welding {
  --eqc-hero: linear-gradient(125deg, #7c2d12 0%, #c2410c 42%, #f97316 74%, #fdba74 100%);
  --eqc-shadow: rgba(154, 52, 18, 0.42);
  --eqc-bg1: rgba(234, 88, 12, 0.16);
  --eqc-bg2: rgba(251, 146, 60, 0.12);
  --eqc-accent: #c2410c;
}
.eqc-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  color: #fff;
  background: var(--eqc-hero);
  box-shadow: 0 10px 24px -16px var(--eqc-shadow);
}
.page-toolbar-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(420px 140px at 12% 0%, rgba(255, 255, 255, 0.28), transparent 70%),
    radial-gradient(280px 120px at 90% 120%, rgba(255, 255, 255, 0.16), transparent 70%);
}
.eqc-hero__main,
.eqc-hero__side {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  align-items: center;
}
.eqc-hero__side {
  flex-direction: column;
  align-items: flex-end;
}
.eqc-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.18);
}
.eqc-hero h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #fff;
}
.eqc-hero p {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.86);
}
.eqc-switch,
.eqc-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.eqc-switch__btn {
  border: 0;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  cursor: pointer;
}
.eqc-switch__btn.is-on {
  background: #fff;
}
.eqc-switch__btn.is-cutting.is-on { color: #1d4ed8; }
.eqc-switch__btn.is-chamfering.is-on { color: #0f766e; }
.eqc-switch__btn.is-forming.is-on { color: #3f6212; }
.eqc-switch__btn.is-welding.is-on { color: #9a3412; }
.eqc-count {
  margin-left: 6px;
  min-width: 16px;
  padding: 0 5px;
  border-radius: 999px;
  background: #fff;
  color: #0f766e;
  font-size: 11px;
}
.eqc-kpis__scope {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 800;
  color: #334155;
}
.eqc-kpis__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 8px;
}
.eqc-kpi {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  background: #fff;
  border-radius: 12px;
  border-top: 3px solid var(--accent);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.eqc-kpi--blue { --accent: #3b82f6; }
.eqc-kpi--purple { --accent: #8b5cf6; }
.eqc-kpi--amber { --accent: #f59e0b; }
.eqc-kpi--green { --accent: #10b981; }
.eqc-kpi--teal { --accent: #14b8a6; }
.eqc-kpi--pink { --accent: #ec4899; }
.eqc-kpi__icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--accent);
}
.eqc-kpi p {
  margin: 0;
  font-size: 11px;
  color: #64748b;
}
.eqc-kpi strong {
  font-size: 17px;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
}
.eqc-kpi small {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}
.eqc-body {
  flex: 1;
  min-height: 420px;
  display: grid;
  grid-template-columns: 268px minmax(0, 1fr);
  gap: 8px;
}
.eqc-list,
.eqc-detail,
.eqc-placeholder {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  min-width: 0;
}
.eqc-list {
  padding: 8px;
  overflow: auto;
  max-height: calc(100vh - 250px);
}
.eqc-list__head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
.eqc-list__meta {
  font-size: 12px;
  color: #64748b;
}
.eqc-card {
  width: 100%;
  text-align: left;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 6px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.eqc-card.is-on {
  border-color: var(--eqc-accent);
  background: #f8fafc;
}
.eqc-card.is-ok { box-shadow: inset 3px 0 0 #10b981; }
.eqc-card.is-ng { box-shadow: inset 3px 0 0 #e11d48; }
.eqc-card__name { font-weight: 800; color: #0f172a; }
.eqc-card__cd, .eqc-card__line { font-size: 11px; color: #64748b; }
.eqc-card__stats {
  display: flex;
  gap: 8px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.eqc-card__stats em { font-style: normal; color: #334155; }
.eqc-detail { padding: 8px; display: flex; flex-direction: column; gap: 8px; }
.eqc-cond {
  display: grid;
  grid-template-columns: repeat(6, minmax(110px, 1fr));
  gap: 8px;
}
.eqc-field, .eqc-form label, .eqc-takt label, .eqc-takt-note {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 11px;
  color: #64748b;
}
.eqc-field--wide { grid-column: span 2; }
.eqc-field--ro b {
  height: 24px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  border-radius: 8px;
  background: #f8fafc;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.eqc-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.eqc-month {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}
.eqc-month :deep(.el-date-editor) {
  width: 128px;
}
.eqc-actions__judge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}
.eqc-help { border: 0; }
.eqc-help ul { margin: 0; padding-left: 18px; color: #334155; font-size: 12px; line-height: 1.6; }
.eqc-num { width: 100%; }
.eqc-num :deep(.el-input) { width: 100%; }
.eqc-field :deep(.el-input-number) { width: 100%; }
.eqc-ro { font-variant-numeric: tabular-nums; color: #0f172a; }
.eqc-placeholder { display: grid; place-items: center; }
.eqc-muted { color: #64748b; font-size: 12px; line-height: 1.5; }
.is-ok { color: #059669; }
.is-ng { color: #e11d48; }
.is-neg { color: #e11d48; }
.eqc-page.eqc-page .eqc-btn-teal.el-button {
  --k-rgb: 15 118 110;
  background: #0f766e;
  border-color: #0f766e;
  color: #fff;
}
.eqc-page.eqc-page .eqc-btn-indigo.el-button {
  --k-rgb: 79 70 229;
  background: #4f46e5;
  border-color: #4f46e5;
  color: #fff;
}
.eqc-page.eqc-page .eqc-btn-amber.el-button {
  --k-rgb: 217 119 6;
  background: #d97706;
  border-color: #d97706;
  color: #fff;
}
@media (max-width: 960px) {
  .eqc-body { grid-template-columns: 1fr; }
  .eqc-list { max-height: 240px; }
  .eqc-cond { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .eqc-hero__side { align-items: flex-start; }
  .eqc-actions__judge { margin-left: 0; }
}
@media (max-width: 480px) {
  .eqc-kpis__grid { grid-template-columns: 1fr 1fr; }
}
</style>

<style>
.eqc-dialog .eqc-form,
.eqc-dialog .eqc-takt {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.eqc-dialog .eqc-takt section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  background: #f8fafc;
}
.eqc-dialog .eqc-takt h3 { margin: 0; font-size: 13px; }
.eqc-dialog .eqc-dialog__lead { margin: 0 0 8px; color: #475569; font-size: 13px; }
.eqc-dialog .eqc-import-table { margin-top: 8px; }
.eqc-dialog .eqc-takt-note { display: flex; flex-direction: column; gap: 4px; margin-top: 10px; font-size: 12px; color: #64748b; }
@media (max-width: 640px) {
  .eqc-dialog .eqc-form,
  .eqc-dialog .eqc-takt { grid-template-columns: 1fr; }
}
</style>
