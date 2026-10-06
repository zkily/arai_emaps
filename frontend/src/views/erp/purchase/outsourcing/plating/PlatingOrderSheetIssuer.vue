<template>
  <div class="sheet-issuer">
    <span class="issuer-label"><el-icon><Printer /></el-icon>注文書</span>
    <el-date-picker
      v-model="orderRange"
      type="daterange"
      value-format="YYYY-MM-DD"
      format="YYYY/MM/DD"
      range-separator="〜"
      start-placeholder="注文日(開始)"
      end-placeholder="注文日(終了)"
      :clearable="false"
      size="small"
      class="issuer-date"
    />
    <el-button-group class="issuer-quick">
      <el-button size="small" title="前日（期間ごと1日前へ）" @click="shiftRange(-1)">
        <el-icon><ArrowLeft /></el-icon>前日
      </el-button>
      <el-button size="small" title="今日" @click="setToday">今日</el-button>
      <el-button size="small" title="翌日（期間ごと1日後へ）" @click="shiftRange(1)">
        翌日<el-icon class="el-icon--right"><ArrowRight /></el-icon>
      </el-button>
    </el-button-group>
    <el-select
      v-model="supplierCd"
      placeholder="外注先"
      filterable
      size="small"
      class="issuer-supplier"
    >
      <el-option v-for="s in supplierOptions" :key="s.value" :label="s.label" :value="s.value" />
    </el-select>
    <el-button type="primary" size="small" class="issuer-btn" :loading="fetching" @click="openIssue">
      <el-icon><Printer /></el-icon>発行
    </el-button>

    <el-dialog
      v-model="dialogVisible"
      width="620px"
      :close-on-click-modal="false"
      :show-close="false"
      append-to-body
      class="sheet-issue-dialog pb-std"
    >
      <template #header>
        <div class="sid-header pb-hero">
          <div class="sid-fx pb-bubbles" aria-hidden="true" />
          <span class="sid-icon"><el-icon><Printer /></el-icon></span>
          <div class="sid-copy">
            <span class="sid-title">注文書印刷確認</span>
            <p class="sid-desc">
              {{ sheetSupplierName }}・{{ sheetPeriodLabel }} の注文書を印刷（1日1ページ・{{ sheetPages.length }} ページ）
            </p>
          </div>
          <el-button size="small" class="sid-print-btn" @click="confirmPrint">
            <el-icon><Printer /></el-icon>印刷実行
          </el-button>
          <el-icon class="sid-close" @click="dialogVisible = false"><Close /></el-icon>
        </div>
      </template>

      <div class="sid-summary">
        <div class="sid-summary-item">
          <span class="sid-summary-label">注文日</span>
          <span class="sid-summary-value" :title="sheetPeriodLabel">{{ sheetPeriodShort }}</span>
        </div>
        <div class="sid-summary-item">
          <span class="sid-summary-label">外注先</span>
          <span class="sid-summary-value">{{ sheetSupplierName }}</span>
        </div>
        <div class="sid-summary-item">
          <span class="sid-summary-label">件数</span>
          <span class="sid-summary-value">{{ sheetItems.length }} 件・{{ sheetPages.length }} 頁</span>
        </div>
        <div class="sid-summary-item">
          <span class="sid-summary-label">総注文数</span>
          <span class="sid-summary-value">{{ totalQty.toLocaleString('ja-JP') }} 本</span>
        </div>
      </div>

      <div v-if="issuedItems.length" class="sid-reissue">
        <el-icon><WarningFilled /></el-icon>
        <span>
          {{ issuedItems.length }} 件は発行済みです（最終 {{ lastIssuedLabel }}）。印刷すると再発行になります。
        </span>
      </div>

      <div class="sid-section">
        <div class="sid-section-title"><el-icon><User /></el-icon>受注先情報</div>
        <div class="sid-row">
          <label class="sid-label">受注先会社名</label>
          <el-input v-model="printForm.recipientCompany" placeholder="外注先会社名 御中" size="small" />
        </div>
      </div>

      <div class="sid-section">
        <div class="sid-section-title"><el-icon><EditPen /></el-icon>承認・発行情報</div>
        <div class="sid-row">
          <label class="sid-label">承認者</label>
          <el-select v-model="printForm.approver" placeholder="承認者を選択" size="small" clearable filterable>
            <el-option v-for="p in PERSON_OPTIONS" :key="p" :label="p" :value="p" />
          </el-select>
        </div>
        <div class="sid-row">
          <label class="sid-label">発行者</label>
          <el-select v-model="printForm.issuer" placeholder="発行者を選択" size="small" clearable filterable>
            <el-option v-for="p in PERSON_OPTIONS" :key="p" :label="p" :value="p" />
          </el-select>
        </div>
      </div>

      <div class="sid-section">
        <div class="sid-section-title"><el-icon><Box /></el-icon>備考・注意事項</div>
        <div class="sid-row">
          <label class="sid-label">備考1</label>
          <el-input v-model="printForm.note1" type="textarea" :rows="2" size="small" />
        </div>
        <div class="sid-row">
          <label class="sid-label">備考2</label>
          <el-input v-model="printForm.note2" type="textarea" :rows="2" size="small" />
        </div>
        <div class="sid-row">
          <label class="sid-label">備考3</label>
          <el-input v-model="printForm.note3" type="textarea" :rows="2" size="small" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  ArrowLeft,
  ArrowRight,
  Box,
  Close,
  EditPen,
  Printer,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { type PlatingLedgerRow, type PlatingOrderSheetItem } from '@/api/outsourcing'
import { recordPrintHistory } from '@/api/shipping/printHistory'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'
import { useLedger } from './ledgerContext'
import { notifyLedgerError } from './ledgerError'

const ledger = useLedger()

const props = defineProps<{
  /** 台帳の表示期間と双方向で連動（v-model:range） */
  range?: [string, string]
  defaultSupplierCd?: string
}>()

const emit = defineEmits<{
  issued: [rows: PlatingLedgerRow[]]
  'update:range': [range: [string, string]]
}>()

const PERSON_OPTIONS = ['篠田', '小森', '趙', '青山', '孫', '竹村', '東條']

const { canExport } = usePurchaseOperationPermission()

const localRange = ref<string[]>([])
const orderRange = computed<string[]>({
  get: () => (props.range?.length === 2 ? props.range : localRange.value),
  set: (v) => {
    localRange.value = v || []
    if (v?.length === 2 && v[0] && v[1]) emit('update:range', [v[0], v[1]])
  },
})
const supplierCd = ref(props.defaultSupplierCd || '')
const supplierOptions = ref<{ value: string; label: string }[]>([])
const fetching = ref(false)
const dialogVisible = ref(false)
const sheetItems = ref<PlatingOrderSheetItem[]>([])
const sheetSupplierName = ref('')
const sheetStart = ref('')
const sheetEnd = ref('')

const printForm = reactive({
  recipientCompany: '',
  approver: '小森',
  issuer: ledger.sheetDefaultIssuer,
  note1: '1.納品書と請求書には必ずこの注文番号をご記入下さい。',
  note2: '2.支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。',
  note3:
    '3.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年7月1日の「支払方法等について」によります。',
})

const totalQty = computed(() => sheetItems.value.reduce((sum, r) => sum + (r.order_qty || 0), 0))

const issuedItems = computed(() => sheetItems.value.filter((r) => r.order_sheet_issued_at))

const lastIssuedLabel = computed(() => {
  const last = issuedItems.value.reduce<PlatingOrderSheetItem | null>(
    (acc, r) => (!acc || (r.order_sheet_issued_at || '') > (acc.order_sheet_issued_at || '') ? r : acc),
    null,
  )
  if (!last) return ''
  return [last.order_sheet_issued_at, last.order_sheet_issued_by].filter(Boolean).join(' ')
})

function formatJpDate(ymd: string): string {
  if (!ymd) return ''
  const [y, m, d] = ymd.split('-').map(Number)
  return `${y}年${m}月${d}日`
}

function formatSlashDate(ymd: string, withYear = true): string {
  if (!ymd) return ''
  const [y, m, d] = ymd.split('-')
  return withYear ? `${y}/${m}/${d}` : `${m}/${d}`
}

const sheetPeriodLabel = computed(() =>
  sheetStart.value === sheetEnd.value
    ? formatJpDate(sheetStart.value)
    : `${formatJpDate(sheetStart.value)}〜${formatJpDate(sheetEnd.value)}`,
)

const sheetPeriodShort = computed(() => {
  if (sheetStart.value === sheetEnd.value) return formatSlashDate(sheetStart.value)
  const sameYear = sheetStart.value.slice(0, 4) === sheetEnd.value.slice(0, 4)
  return `${formatSlashDate(sheetStart.value)}〜${formatSlashDate(sheetEnd.value, !sameYear)}`
})

/** 注文日ごとに 1 ページ（注文のない日はページを作らない） */
const sheetPages = computed(() => {
  const byDate = new Map<string, PlatingOrderSheetItem[]>()
  for (const r of sheetItems.value) {
    const key = r.order_date || ''
    const list = byDate.get(key) ?? []
    list.push(r)
    byDate.set(key, list)
  }
  return [...byDate.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, items]) => ({
      date,
      items: [...items].sort((a, b) =>
        (a.product_name || '').localeCompare(b.product_name || '', 'ja-JP', {
          numeric: true,
          sensitivity: 'base',
        }),
      ),
    }))
})

function setToday() {
  const today = dayjs().format('YYYY-MM-DD')
  orderRange.value = [today, today]
}

/** 期間の長さを保ったまま前後へずらす（未指定なら今日基準の1日） */
function shiftRange(days: number) {
  const [start, end] = orderRange.value || []
  if (!start || !end) {
    const d = dayjs().add(days, 'day').format('YYYY-MM-DD')
    orderRange.value = [d, d]
    return
  }
  orderRange.value = [
    dayjs(start).add(days, 'day').format('YYYY-MM-DD'),
    dayjs(end).add(days, 'day').format('YYYY-MM-DD'),
  ]
}

watch(
  () => props.defaultSupplierCd,
  (v) => {
    if (v) supplierCd.value = v
  },
)

async function loadSuppliers() {
  try {
    const res = await ledger.getOptions()
    const map = new Map<string, string>()
    for (const o of res?.data || []) {
      if (!map.has(o.supplier_cd)) map.set(o.supplier_cd, o.supplier_name || o.supplier_cd)
    }
    supplierOptions.value = [...map.entries()]
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label, 'ja'))
  } catch {
    supplierOptions.value = []
  }
}

async function openIssue() {
  if (!guardPurchaseOperation(canExport)) return
  const [start, end] = orderRange.value || []
  if (!start || !end) {
    ElMessage.warning('注文日の期間を指定してください')
    return
  }
  if (!supplierCd.value) {
    ElMessage.warning('外注先を指定してください')
    return
  }
  fetching.value = true
  try {
    const res = await ledger.getOrderSheet(start, end, supplierCd.value)
    const items = res?.data?.items || []
    if (items.length === 0) {
      ElMessage.warning('指定した期間・外注先の注文データがありません')
      return
    }
    sheetItems.value = items
    sheetStart.value = start
    sheetEnd.value = end
    sheetSupplierName.value = res.data.supplier_name || supplierCd.value
    printForm.recipientCompany = `${sheetSupplierName.value} 御中`
    printForm.approver = '小森'
    printForm.issuer = ledger.sheetDefaultIssuer
    dialogVisible.value = true
  } catch (error: any) {
    notifyLedgerError(error, '注文データの取得に失敗しました')
  } finally {
    fetching.value = false
  }
}

function esc(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function buildSheetHtml(): string {
  return sheetPages.value.map((p) => buildPageHtml(p.date, p.items)).join('')
}

function buildPageHtml(orderDate: string, items: PlatingOrderSheetItem[]): string {
  const fmtNum = (v: number | null | undefined) => (v == null || isNaN(v) ? '0' : v.toLocaleString('ja-JP'))
  const fmtCurrency = (v: number | null | undefined) =>
    v == null || isNaN(v)
      ? '¥0.00'
      : `¥${v.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

  const pageQty = items.reduce((sum, r) => sum + (r.order_qty || 0), 0)
  const first = items[0]
  const rowsHtml = items
    .map(
      (r) => `
        <tr>
          <td class="text-center">${esc(r.order_no)}</td>
          <td class="text-center">${esc(r.product_name)}</td>
          <td class="text-center">${esc(r.content)}</td>
          <td class="text-right">${fmtCurrency(r.unit_price)}</td>
          <td class="text-center">${fmtNum(r.order_qty)}</td>
          <td class="text-center">本</td>
          <td class="text-center">${esc(r.category)}</td>
        </tr>`,
    )
    .join('')

  return `
    <div class="order-sheet">
      <div class="issued-info">注文日: ${esc(formatJpDate(orderDate))}</div>
      <div class="title">注 文 書</div>
      <div class="header">
        <div class="recipient-block"><div>${esc(printForm.recipientCompany || '外注先会社名 御中')}</div></div>
        <div class="sender-block">
          <div>日鉄物産荒井オートモーティブ(株)     </div>
          <div>〒496-0902 愛知県愛西市須依町2189  </div>
          <div>TEL&lt;0567&gt;28-4171</div>
          <div>FAX&lt;0567&gt;26-2281</div>
          <div class="approval-box">
            <table>
              <tr><td>承認</td><td>発行</td></tr>
              <tr><td>${esc(printForm.approver)}</td><td>${esc(printForm.issuer)}</td></tr>
            </table>
          </div>
        </div>
      </div>
      <div class="delivery-meta">
        <div class="delivery-meta-left">納入日: ${esc(first?.delivery_date || '未指定')}</div>
        <div class="delivery-meta-right">納品場所: ${esc(first?.delivery_location || '未指定')}</div>
      </div>
      <div class="order-note">＊下記のとおり注文いたします。</div>
      <table>
        <thead>
          <tr>
            <th width="25%">注文番号</th>
            <th width="15%">製品名</th>
            <th width="15%">内容</th>
            <th width="10%">単価(円)</th>
            <th width="10%">注文数</th>
            <th width="6%">単位</th>
            <th width="19%">区分</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
      <div class="summary-row">
        <div class="summary-item">総注文数  ${fmtNum(pageQty)} 本</div>
      </div>
      <div class="notes">
        <p>${esc(printForm.note1)}</p>
        <p>${esc(printForm.note2)}</p>
        <p>${esc(printForm.note3)}</p>
      </div>
    </div>`
}

const SHEET_STYLE = `
  body { font-family: 'Meiryo', 'Yu Gothic', sans-serif; margin: 1.0cm; font-size: 10pt; line-height: 1.4; background: #fff; color: #000; }
  .delivery-meta { display: flex; justify-content: space-between; margin: 6mm 0 4mm; font-size: 18pt; font-weight: 600; }
  .delivery-meta-left, .delivery-meta-right { background: #f8f9fa; padding: 4px 8px; border-radius: 4px; border: 1px solid #e5e7eb; }
  .order-note { margin: 3mm 0 2mm; font-size: 11pt; font-weight: 600; }
  .order-sheet { width: 100%; margin: 0 auto; position: relative; min-height: 281mm; height: 281mm; box-sizing: border-box; page-break-inside: avoid; }
  .order-sheet + .order-sheet { page-break-before: always; break-before: page; }
  .header { margin-bottom: 1mm; position: relative; display: flex; flex-direction: column; gap: 4mm; }
  .issued-info { text-align: left; font-size: 13pt; font-weight: 600; margin-bottom: 1mm; }
  .title { text-align: center; font-size: 30pt; font-weight: bold; margin: 1mm 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); letter-spacing: 2px; }
  .recipient-block { margin-top: 4mm; width: 100%; }
  .recipient-block div { font-size: 26pt; font-weight: bold; width: 100%; }
  .sender-block { text-align: right; margin-bottom: 1mm; }
  .sender-block div { margin-bottom: 2mm; font-size: 10pt; }
  .approval-box { border: 2px solid #34495e; width: 120px; margin-left: auto; text-align: center; margin-top: 1mm; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .approval-box table { width: 100%; border-collapse: collapse; margin: 0; box-shadow: none; }
  .approval-box td { border: 1px solid #34495e; padding: 1mm; text-align: center; font-size: 8pt; width: 50%; background: #f8f9fa; font-weight: 500; }
  table { width: 100%; border-collapse: collapse; margin: 2mm 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden; }
  th, td { border: 1px solid #dee2e6; padding: 2.4mm 3.6mm; text-align: left; font-size: 10.5pt; }
  th { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); text-align: center; font-weight: bold; border-bottom: 2px solid #dee2e6; }
  .text-center { text-align: center; }
  .text-right { text-align: right; }
  .summary-row { display: flex; justify-content: flex-end; margin-top: 4mm; margin-bottom: 12mm; gap: 8mm; border-top: 2px solid #dee2e6; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 6px; padding: 4mm 8mm; }
  .summary-item { font-weight: bold; font-size: 11pt; padding: 2mm 4mm; background: #fff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #dee2e6; }
  .notes { font-size: 9pt; line-height: 1.6; position: absolute; bottom: 1cm; left: 0.5cm; right: 0.5cm; background: #f8f9fa; padding: 4mm 6mm; border-radius: 6px; border-left: 4px solid #6c757d; box-shadow: 0 2px 4px rgba(0,0,0,0.1); page-break-inside: avoid; }
  .notes p { margin: 2mm 0; font-weight: 400; }
  .notes p:first-child { margin-top: 0; }
  .notes p:last-child { margin-bottom: 0; }
  @page { size: A4; margin: 0.8cm; }
  @media print { body { margin: 0; padding: 0; } }
`

async function confirmPrint() {
  if (!guardPurchaseOperation(canExport)) return
  if (sheetItems.value.length === 0) {
    ElMessage.warning('注文データがありません')
    return
  }
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('印刷ウィンドウを開けませんでした。ポップアップを許可してください')
    return
  }
  printWindow.document.write(`
    <html>
    <head><title>注文書</title><meta charset="UTF-8"><style>${SHEET_STYLE}</style></head>
    <body>${buildSheetHtml()}</body>
    </html>
  `)
  printWindow.document.close()
  printWindow.onload = () => {
    printWindow.print()
    setTimeout(() => printWindow.close(), 1000)
  }

  try {
    const res = await ledger.markIssued(sheetItems.value.map((r) => r.id))
    emit('issued', res?.data?.rows || [])
  } catch (error: any) {
    notifyLedgerError(error, '発行記録の保存に失敗しました')
  }

  try {
    await recordPrintHistory({
      report_type: ledger.sheetReportType,
      report_title: ledger.sheetReportTitle,
      filters: {
        startDate: sheetStart.value,
        endDate: sheetEnd.value,
        supplier: supplierCd.value,
        orderNos: sheetItems.value.map((r) => r.order_no).filter(Boolean),
      },
      record_count: sheetItems.value.length,
      status: '成功',
    })
  } catch (err) {
    console.error('印刷履歴の保存に失敗しました:', err)
  }
  dialogVisible.value = false
}

onMounted(loadSuppliers)
</script>

<style scoped>
.sheet-issuer {
  display: flex;
  align-items: center;
  gap: 6px;
}

.issuer-label {
  flex-shrink: 0;
  height: 22px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #115e59;
  background: #e6f7f5;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #99e0d8;
}

.issuer-date {
  width: 250px !important;
  flex: 0 0 250px;
}

.issuer-supplier {
  width: 170px;
}

.issuer-quick {
  flex-shrink: 0;
  display: inline-flex;
}

.issuer-quick .el-button {
  height: 24px;
  padding: 0 8px;
  font-weight: 700;
  color: #0f766e;
  border-color: #cfe6e3;
  background: #fff;
}

.issuer-quick .el-button:hover,
.issuer-quick .el-button:focus-visible {
  color: #115e59;
  border-color: #7dd3c8;
  background: #ecfdf9;
}

.issuer-quick .el-button:first-child {
  border-radius: 8px 0 0 8px;
}

.issuer-quick .el-button:last-child {
  border-radius: 0 8px 8px 0;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.sheet-issuer :deep(.el-input__wrapper),
.sheet-issuer :deep(.el-select__wrapper) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #cfe6e3 inset;
}

.sheet-issuer :deep(.el-input__wrapper:hover),
.sheet-issuer :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #7dd3c8 inset;
}

.sheet-issuer :deep(.el-input__wrapper.is-focus),
.sheet-issuer :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #0d9488 inset,
    0 0 0 3px rgba(13, 148, 136, 0.14);
}

.issuer-btn {
  --k-rgb: 13 148 136;
  height: 26px;
  padding: 0 12px;
  border-radius: 8px;
  font-weight: 700;
  color: #fff;
  border: 1px solid #0f766e;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #14b8a6, #0f766e);
}

.issuer-btn:hover,
.issuer-btn:focus-visible {
  color: #fff;
  border-color: #115e59;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #2dd4bf, #0d9488);
}

.issuer-btn .el-icon {
  margin-right: 4px;
}
</style>

<style>
/* append-to-body のため非 scoped（クラス名は本コンポーネント専用） */
.el-dialog.sheet-issue-dialog {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
}

.sheet-issue-dialog .el-dialog__header {
  margin: 0;
  padding: 0;
}

.sheet-issue-dialog .sid-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #0f766e 0%, #0d9488 34%, #0891b2 66%, #2563eb 100%);
}

.sheet-issue-dialog .sid-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font-size: 18px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(19, 78, 74, 0.3);
}

.sheet-issue-dialog .sid-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sheet-issue-dialog .sid-title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
}

.sheet-issue-dialog .sid-desc {
  margin: 0;
  overflow: hidden;
  font-size: 11px;
  line-height: 1.5;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.88);
}

/* ヒーロー上の白ピル */
.sheet-issue-dialog .sid-print-btn {
  --k-rgb: 13 148 136;
  flex-shrink: 0;
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 700;
  color: #0f766e;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #ecfdf9 100%);
}

.sheet-issue-dialog .sid-print-btn:hover,
.sheet-issue-dialog .sid-print-btn:focus-visible {
  color: #115e59;
  border-color: #fff;
  background: #fff;
}

.sheet-issue-dialog .sid-print-btn .el-icon {
  margin-right: 4px;
}

.sheet-issue-dialog .sid-close {
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
  transition:
    transform 0.2s ease,
    background 0.2s ease;
}

.sheet-issue-dialog .sid-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.sheet-issue-dialog .el-dialog__body {
  padding: 14px 18px 18px;
  background: #f8fafc;
}

/* 概要（色分け・動きなし） */
.sheet-issue-dialog .sid-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.sheet-issue-dialog .sid-summary-item {
  --accent: #0d9488;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px 8px 13px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--accent) 20%, #e2e8f0);
  background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 8%, #fff) 0%, #fff 75%);
}

.sheet-issue-dialog .sid-summary-item::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 45%, #fff), var(--accent));
}

.sheet-issue-dialog .sid-summary-item:nth-child(2) {
  --accent: #0891b2;
}

.sheet-issue-dialog .sid-summary-item:nth-child(3) {
  --accent: #4f46e5;
}

.sheet-issue-dialog .sid-summary-item:nth-child(4) {
  --accent: #d97706;
}

.sheet-issue-dialog .sid-summary-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.sheet-issue-dialog .sid-summary-value {
  overflow: hidden;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: color-mix(in srgb, var(--accent) 70%, #0f172a);
  font-variant-numeric: tabular-nums;
}

/* 再発行の注意 */
.sheet-issue-dialog .sid-reissue {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  color: #b45309;
  border: 1px solid #fde68a;
  background: #fffbeb;
}

.sheet-issue-dialog .sid-reissue .el-icon {
  flex-shrink: 0;
  font-size: 15px;
  color: #d97706;
}

/* 入力セクション：上端カラーバー付き白カード */
.sheet-issue-dialog .sid-section {
  position: relative;
  overflow: hidden;
  margin-bottom: 10px;
  padding: 12px 12px 10px;
  border-radius: 10px;
  border: 1px solid #ccebe8;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.sheet-issue-dialog .sid-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0d9488 0%, #0891b2 55%, #3b82f6 100%);
}

.sheet-issue-dialog .sid-section:last-child {
  margin-bottom: 0;
}

.sheet-issue-dialog .sid-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 800;
  color: #115e59;
}

.sheet-issue-dialog .sid-section-title .el-icon {
  width: 22px;
  height: 22px;
  padding: 4px;
  box-sizing: border-box;
  border-radius: 6px;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #2dd4bf, #0d9488);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(19, 78, 74, 0.3);
}

.sheet-issue-dialog .sid-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}

.sheet-issue-dialog .sid-row:last-child {
  margin-bottom: 0;
}

.sheet-issue-dialog .sid-label {
  flex-shrink: 0;
  width: 90px;
  font-size: 12px;
  font-weight: 700;
  line-height: 24px;
  color: #475569;
}

.sheet-issue-dialog .sid-row .el-input,
.sheet-issue-dialog .sid-row .el-select,
.sheet-issue-dialog .sid-row .el-textarea {
  flex: 1;
}

.sheet-issue-dialog .sid-row .el-input__wrapper,
.sheet-issue-dialog .sid-row .el-select__wrapper,
.sheet-issue-dialog .sid-row .el-textarea__inner {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #cfe6e3 inset;
}

.sheet-issue-dialog .sid-row .el-input__wrapper:hover,
.sheet-issue-dialog .sid-row .el-select__wrapper:hover,
.sheet-issue-dialog .sid-row .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #7dd3c8 inset;
}

.sheet-issue-dialog .sid-row .el-input__wrapper.is-focus,
.sheet-issue-dialog .sid-row .el-select__wrapper.is-focused,
.sheet-issue-dialog .sid-row .el-textarea__inner:focus {
  box-shadow:
    0 0 0 1px #0d9488 inset,
    0 0 0 3px rgba(13, 148, 136, 0.14);
}
</style>
