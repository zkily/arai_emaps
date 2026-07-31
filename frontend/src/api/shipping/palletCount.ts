import request from '@/utils/request'

export interface PalletCountDestination {
  cd: string
  name: string
}

/** 1グループ分：日付×納入先 */
export interface PalletCountGroupCard {
  group_name: string
  destinations: PalletCountDestination[]
  dates: string[]
  matrix: Record<string, Record<string, number>>
  row_totals: Record<string, number>
  col_totals: Record<string, number>
  grand_total: number
  enable_advance_tohoku?: boolean
  tohoku_destination_cd?: string | null
  advance_qty?: Record<string, number>
  advance_total?: number
  tohoku_deduct_by_date?: Record<string, number>
  enable_bin2?: boolean
  bin2_qty?: Record<string, number>
  bin2_total?: number
  /** 手動修正 date -> dest_cd -> qty */
  cell_overrides?: Record<string, Record<string, number>>
}

export interface PalletCountMatrixData {
  dates: string[]
  groups: PalletCountGroupCard[]
  grand_total: number
}

/** グループ別・日付×納入先の出荷パレット数集計（同一出荷番号=1パレット） */
export function getPalletCountMatrix(params: {
  start_date?: string
  end_date?: string
  page_key?: string
  group_names?: string
}) {
  return request.get('/api/shipping/pallet-count', { params })
}

/** オワリ便「先出(東北)」保存 */
export function saveAdvanceTohoku(payload: { advance_date: string; qty: number }) {
  return request.put('/api/shipping/pallet-count/advance-tohoku', payload)
}

/** オワリ便「2便」保存 */
export function saveBin2(payload: { shipping_date: string; qty: number }) {
  return request.put('/api/shipping/pallet-count/bin2', payload)
}

/** セル手動修正（ダブルクリック編集）保存／削除 */
export function saveCellOverride(payload: {
  shipping_date: string
  destination_cd: string
  qty?: number | null
  clear?: boolean
}) {
  return request.put('/api/shipping/pallet-count/cell-override', payload)
}

export interface AdvancePrintSheet {
  advance_date: string
  shipping_date: string
  delivery_date: string
  destination_cd: string
  destination_name: string
  advance_label: string
  shipping_portion_label: string
  shipping_date_label: string
  delivery_date_label: string
  qty: number
  copy_index: number
}

/** 先出(東北) A5 印刷データ（数量分のシート） */
export function getAdvancePrintSheets(params: { start_date?: string; end_date?: string }) {
  return request.get('/api/shipping/pallet-count/advance-print', { params })
}

/** グループ表をメール送信 */
export function sendPalletCountMail(payload: {
  start_date: string
  end_date: string
  group_name: string
  to_emails: string[]
  subject?: string
  page_key?: string
}) {
  return request.post('/api/shipping/pallet-count/send-mail', payload)
}
