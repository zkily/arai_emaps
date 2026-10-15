/**
 * 設備能力画面の印刷 HTML 生成（単一設備 / 全設備）
 */
import {
  buildPrintHtmlDocument,
  escapeHtml,
  openPrintWindow,
  PRINT_POPUP_BLOCKED_MSG,
} from '@/utils/printWindow'
import {
  calcHeader,
  calcLine,
  calcTotals,
  fmtNum,
  judgmentLabel,
  type HeaderInput,
  type Judgment,
  type LineInput,
  type TotalCalc,
} from './capacityCalc'

export { PRINT_POPUP_BLOCKED_MSG }

export interface PrintItemInput extends LineInput {
  part_no?: string
  part_name?: string
  material?: string
}

export interface PrintEquipmentInput extends HeaderInput {
  machine_cd: string
  machine_name: string
  items: PrintItemInput[]
}

export interface BuildCapacityPrintOptions {
  processLabel: string
  targetMonth?: string
  printedAt?: string
  mode: 'single' | 'all'
  equipments: PrintEquipmentInput[]
}

function loadTone(pct: number | null | undefined): string {
  if (pct == null || !Number.isFinite(pct)) return ''
  if (pct < 85) return 'ok'
  if (pct <= 100) return 'warn'
  return 'ng'
}

function judgeClass(v: Judgment): string {
  if (v === 'ok') return 'ok'
  if (v === 'ng') return 'ng'
  return ''
}

function formatPrintedAt(d = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function computeEquipment(eq: PrintEquipmentInput) {
  const header = calcHeader(eq)
  const lines = eq.items.map((item) => calcLine(item, header))
  const totals = calcTotals(lines, header)
  return { header, lines, totals }
}

const PRINT_STYLES = `
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0;
  padding: 10px 12px 14px;
  color: #0f172a;
  font: 9px/1.35 "Yu Gothic UI", "Yu Gothic", Meiryo, sans-serif;
  background: #fff;
}
.doc-hd {
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid #dbe5f1;
  border-radius: 8px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
}
.doc-tt { font-size: 14px; font-weight: 800; color: #1e3a8a; }
.doc-meta { margin-top: 4px; color: #475569; font-size: 8.5px; line-height: 1.55; }
.doc-meta strong { color: #334155; font-weight: 700; }
.eq-sec {
  margin-bottom: 14px;
  page-break-before: always;
  break-before: page;
  page-break-inside: avoid;
  break-inside: avoid;
}
/* 単一設備印刷：タイトル直後は改ページしない（白紙ページ防止） */
.doc-hd + .eq-sec {
  page-break-before: auto;
  break-before: auto;
}
.eq-hd {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: baseline;
  margin: 0 0 6px;
  padding-bottom: 4px;
  border-bottom: 2px solid #64748b;
}
.eq-name { font-size: 12px; font-weight: 800; color: #0f172a; }
.eq-cd { font-size: 9px; color: #64748b; font-weight: 700; }
.cond-row, .sum-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  margin: 0 0 6px;
  font-size: 8.5px;
  color: #334155;
}
.cond-row span, .sum-row span { white-space: nowrap; }
.cond-row b, .sum-row b { font-weight: 800; color: #0f172a; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  font-weight: 700;
}
.chip b.ok, .tone-ok { color: #15803d; }
.chip b.ng, .tone-ng { color: #dc2626; }
.chip b.warn, .tone-warn { color: #ca8a04; }
table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 7.5px;
}
th, td {
  border: 1px solid #cbd5e1;
  padding: 6px 5px;
  min-height: 22px;
  line-height: 1.55;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  vertical-align: middle;
}
th {
  background: linear-gradient(180deg, #eaf3ff 0%, #dceafe 100%);
  font-weight: 800;
  color: #334155;
  font-size: 7.5px;
}
tbody tr:nth-child(odd) { background: #fcfdff; }
tbody tr:nth-child(even) { background: #f7fbff; }
.left { text-align: left; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.cen { text-align: center; }
.empty { color: #94a3b8; font-style: italic; padding: 8px; text-align: center; }
.overview {
  margin-bottom: 8px;
  page-break-after: avoid;
  break-after: avoid;
  page-break-inside: avoid;
  break-inside: avoid;
}
.overview .eq-hd { margin-bottom: 3px; padding-bottom: 2px; }
.overview .eq-name { font-size: 10px; }
.overview table { font-size: 7.5px; }
.overview th, .overview td {
  padding: 2px 3px;
  min-height: 0;
  line-height: 1.25;
  font-size: 7.5px;
}
.doc-hd + .overview {
  page-break-before: avoid;
  break-before: avoid;
}
@media print {
  @page { size: A4 landscape; margin: 8mm; }
  body { padding: 0; }
}
`

function buildCondRow(eq: PrintEquipmentInput, header: { daily_available: number; total_hours: number }): string {
  return `<div class="cond-row">
    <span>定時 <b>${escapeHtml(fmtNum(eq.regular_hours))}</b> h/直</span>
    <span>直 <b>${escapeHtml(fmtNum(eq.shift_count))}</b></span>
    <span>残業 <b>${escapeHtml(fmtNum(eq.overtime_hours))}</b> h/直</span>
    <span>稼働日 <b>${escapeHtml(fmtNum(eq.working_days, 0))}</b></span>
    <span>1日稼働 <b>${escapeHtml(fmtNum(header.daily_available))}</b> H</span>
    <span>月間総時間 <b>${escapeHtml(fmtNum(header.total_hours))}</b> H</span>
  </div>`
}

function buildSumRow(totals: TotalCalc): string {
  const loadCls = loadTone(totals.occupancy_pct)
  return `<div class="sum-row">
    <span class="chip">所要 <b>${escapeHtml(fmtNum(totals.occupied_hours))}</b> H</span>
    <span class="chip">残 <b>${escapeHtml(fmtNum(totals.remain_hours))}</b> H</span>
    <span class="chip">負荷 <b class="${loadCls}">${escapeHtml(fmtNum(totals.occupancy_pct))}%</b></span>
    <span class="chip">平均能率 <b>${escapeHtml(fmtNum(totals.avg_hourly))}</b> 本/H</span>
    <span class="chip">日当 <b class="${judgeClass(totals.daily_judgment)}">${escapeHtml(judgmentLabel(totals.daily_judgment))}</b></span>
    <span class="chip">月当 <b class="${judgeClass(totals.month_judgment)}">${escapeHtml(judgmentLabel(totals.month_judgment))}</b></span>
    <span class="chip">品目 <b>${escapeHtml(String(totals.item_count))}</b></span>
  </div>`
}

function buildItemsTable(eq: PrintEquipmentInput, lines: ReturnType<typeof calcLine>[]): string {
  if (!eq.items.length) {
    return `<p class="empty">品目がありません</p>`
  }
  const rows = eq.items
    .map((item, i) => {
      const line = lines[i]
      const loadCls = loadTone(line.occupancy_pct)
      return `<tr>
        <td class="cen">${i + 1}</td>
        <td class="left">${escapeHtml(item.part_no || '—')}</td>
        <td class="left">${escapeHtml(item.part_name || '—')}</td>
        <td class="left">${escapeHtml(item.material || '—')}</td>
        <td class="num">${escapeHtml(fmtNum(item.monthly_qty, 0))}</td>
        <td class="num">${escapeHtml(fmtNum(item.qty_days, 0))}</td>
        <td class="num">${escapeHtml(fmtNum(line.daily_qty, 0))}</td>
        <td class="num">${escapeHtml(fmtNum(item.rate_per_hour))}</td>
        <td class="num">${escapeHtml(fmtNum(item.availability_pct))}</td>
        <td class="num">${escapeHtml(fmtNum(item.pass_rate_pct))}</td>
        <td class="num">${escapeHtml(fmtNum(line.production_hours))}</td>
        <td class="num">${escapeHtml(fmtNum(item.setup_hours))}</td>
        <td class="num">${escapeHtml(fmtNum(line.operating_hours))}</td>
        <td class="num">${escapeHtml(fmtNum(item.actual_days, 0))}</td>
        <td class="num">${escapeHtml(fmtNum(line.weighted_hours))}</td>
        <td class="num">${escapeHtml(fmtNum(line.occupied_hours))}</td>
        <td class="num tone-${loadCls}">${escapeHtml(fmtNum(line.occupancy_pct))}</td>
        <td class="cen ${judgeClass(line.daily_judgment)}">${escapeHtml(judgmentLabel(line.daily_judgment))}</td>
      </tr>`
    })
    .join('')

  return `<table>
    <thead>
      <tr>
        <th style="width:3%">#</th>
        <th style="width:8%">製品CD</th>
        <th style="width:10%">製品名</th>
        <th style="width:9%">材料</th>
        <th style="width:6%">内示/月</th>
        <th style="width:4%">日数</th>
        <th style="width:4%">日当</th>
        <th style="width:5%">能率/H</th>
        <th style="width:5%">作業率%</th>
        <th style="width:5%">合格率%</th>
        <th style="width:5%">生産H</th>
        <th style="width:4%">段取H</th>
        <th style="width:5%">稼働H</th>
        <th style="width:4%">実日数</th>
        <th style="width:5%">加重H</th>
        <th style="width:5%">所要H</th>
        <th style="width:4%">負荷%</th>
        <th style="width:3%">判定</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`
}

function buildEquipmentSection(eq: PrintEquipmentInput): string {
  const { header, lines, totals } = computeEquipment(eq)
  return `<section class="eq-sec">
    <div class="eq-hd">
      <span class="eq-name">${escapeHtml(eq.machine_name || '—')}</span>
      <span class="eq-cd">${escapeHtml(eq.machine_cd || '')}</span>
    </div>
    ${buildCondRow(eq, header)}
    ${buildSumRow(totals)}
    ${buildItemsTable(eq, lines)}
  </section>`
}

function buildOverview(equipments: PrintEquipmentInput[]): string {
  if (equipments.length <= 1) return ''
  const rows = equipments
    .map((eq, i) => {
      const { header, totals } = computeEquipment(eq)
      const loadCls = loadTone(totals.occupancy_pct)
      return `<tr>
        <td class="cen">${i + 1}</td>
        <td class="left">${escapeHtml(eq.machine_name || '—')}</td>
        <td class="left">${escapeHtml(eq.machine_cd || '')}</td>
        <td class="num">${escapeHtml(fmtNum(header.total_hours))}</td>
        <td class="num">${escapeHtml(fmtNum(totals.occupied_hours))}</td>
        <td class="num tone-${loadCls}">${escapeHtml(fmtNum(totals.occupancy_pct))}%</td>
        <td class="cen ${judgeClass(totals.month_judgment)}">${escapeHtml(judgmentLabel(totals.month_judgment))}</td>
        <td class="num">${escapeHtml(fmtNum(totals.avg_hourly))}</td>
        <td class="num">${escapeHtml(String(totals.item_count))}</td>
      </tr>`
    })
    .join('')

  return `<section class="overview">
    <div class="eq-hd"><span class="eq-name">設備一覧サマリ</span></div>
    <table>
      <thead>
        <tr>
          <th style="width:4%">#</th>
          <th style="width:18%">設備名</th>
          <th style="width:12%">コード</th>
          <th style="width:10%">月間総時間</th>
          <th style="width:10%">所要時間</th>
          <th style="width:10%">負荷率</th>
          <th style="width:8%">月当</th>
          <th style="width:12%">平均能率</th>
          <th style="width:8%">品目数</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  </section>`
}

/** 印刷用 HTML を組み立てる */
export function buildCapacityPrintHtml(opts: BuildCapacityPrintOptions): string {
  const printedAt = opts.printedAt || formatPrintedAt()
  const month = (opts.targetMonth || '').trim()
  const title =
    opts.mode === 'all'
      ? `${opts.processLabel}設備能力（全設備）`
      : `${opts.processLabel}設備能力 — ${opts.equipments[0]?.machine_name || ''}`

  const metaBits = [
    `工程：<strong>${escapeHtml(opts.processLabel)}</strong>`,
    month ? `対象月：<strong>${escapeHtml(month)}</strong>` : '',
    `設備：<strong>${escapeHtml(String(opts.equipments.length))}</strong> 台`,
    `印刷日時：${escapeHtml(printedAt)}`,
  ].filter(Boolean)

  const body = `
    <div class="doc-hd">
      <div class="doc-tt">${escapeHtml(title)}</div>
      <div class="doc-meta">${metaBits.join('　')}</div>
    </div>
    ${opts.mode === 'all' ? buildOverview(opts.equipments) : ''}
    ${opts.equipments.map(buildEquipmentSection).join('\n')}
  `

  return buildPrintHtmlDocument(title, PRINT_STYLES, body)
}

/** 印刷ウィンドウを開く。失敗時は null */
export function printCapacityReport(opts: BuildCapacityPrintOptions): Window | null {
  const html = buildCapacityPrintHtml(opts)
  return openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 400 })
}
