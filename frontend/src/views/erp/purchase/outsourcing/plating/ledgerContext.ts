import { inject, type InjectionKey } from 'vue'
import {
  calculatePlatingLedger,
  calculateWeldingLedger,
  generatePlatingLedger,
  generateWeldingLedger,
  getPlatingLedger,
  getPlatingLedgerHistory,
  getPlatingLedgerOptions,
  getPlatingLedgerOrderSheet,
  getPlatingLedgerStock,
  getPlatingLedgerStockTrend,
  getWeldingLedger,
  getWeldingLedgerHistory,
  getWeldingLedgerOptions,
  getWeldingLedgerOrderSheet,
  getWeldingLedgerStock,
  getWeldingLedgerStockTrend,
  markPlatingOrderSheetIssued,
  markWeldingOrderSheetIssued,
  refreshPlatingLedgerMaster,
  refreshWeldingLedgerMaster,
  updatePlatingLedger,
  updateWeldingLedger,
} from '@/api/outsourcing'

export interface LedgerContext {
  process: 'plating' | 'welding'
  title: string
  /** データ生成の説明に使う製品の呼び方 */
  productKind: string
  sheetReportType: string
  sheetReportTitle: string
  /** 注文書の発行者（初期値） */
  sheetDefaultIssuer: string
  /** 注文書の外注先（初期値）。空なら絞り込みの外注先を使う */
  sheetDefaultSupplierCd: string
  /** 現在庫分析の見出し注記。空なら表示しない */
  stockScopeNote: string
  getOptions: typeof getPlatingLedgerOptions
  getList: typeof getPlatingLedger
  generate: typeof generatePlatingLedger
  calculate: typeof calculatePlatingLedger
  refreshMaster: typeof refreshPlatingLedgerMaster
  markIssued: typeof markPlatingOrderSheetIssued
  update: typeof updatePlatingLedger
  getHistory: typeof getPlatingLedgerHistory
  getStock: typeof getPlatingLedgerStock
  getStockTrend: typeof getPlatingLedgerStockTrend
  getOrderSheet: typeof getPlatingLedgerOrderSheet
}

export const platingLedgerContext: LedgerContext = {
  process: 'plating',
  title: '外注メッキ',
  productKind: '外注メッキ製品',
  sheetReportType: 'plating_order',
  sheetReportTitle: '外注メッキ注文書',
  sheetDefaultIssuer: '竹村',
  sheetDefaultSupplierCd: '',
  stockScopeNote: '北九州ケミカルを除く',
  getOptions: getPlatingLedgerOptions,
  getList: getPlatingLedger,
  generate: generatePlatingLedger,
  calculate: calculatePlatingLedger,
  refreshMaster: refreshPlatingLedgerMaster,
  markIssued: markPlatingOrderSheetIssued,
  update: updatePlatingLedger,
  getHistory: getPlatingLedgerHistory,
  getStock: getPlatingLedgerStock,
  getStockTrend: getPlatingLedgerStockTrend,
  getOrderSheet: getPlatingLedgerOrderSheet,
}

export const weldingLedgerContext: LedgerContext = {
  process: 'welding',
  title: '外注溶接',
  productKind: '外注溶接製品',
  sheetReportType: 'welding_order',
  sheetReportTitle: '外注溶接注文書',
  sheetDefaultIssuer: '東條',
  // 共栄工業(株)
  sheetDefaultSupplierCd: 'OS-005',
  stockScopeNote: '',
  getOptions: getWeldingLedgerOptions,
  getList: getWeldingLedger,
  generate: generateWeldingLedger,
  calculate: calculateWeldingLedger,
  refreshMaster: refreshWeldingLedgerMaster,
  markIssued: markWeldingOrderSheetIssued,
  update: updateWeldingLedger,
  getHistory: getWeldingLedgerHistory,
  getStock: getWeldingLedgerStock,
  getStockTrend: getWeldingLedgerStockTrend,
  getOrderSheet: getWeldingLedgerOrderSheet,
}

export const LEDGER_KEY: InjectionKey<LedgerContext> = Symbol('outsourcingLedger')

export function useLedger(): LedgerContext {
  const ctx = inject(LEDGER_KEY)
  if (!ctx) throw new Error('台帳コンテキストがありません')
  return ctx
}
