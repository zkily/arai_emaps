import request from '@/utils/request'
import type { InventoryShortagePrintRow } from '@/api/database'

/** 倉庫日次 shipping_warehouse_daily_stock ベースの不足数印刷用（在庫不足画面と同一行形式） */
export function getWarehouseDailyShortagePrint(params: {
  startDate: string
  endDate: string
  productCd?: string
}) {
  return request.get<{ success?: boolean; data: InventoryShortagePrintRow[] }>(
    '/api/shipping/warehouse-daily/shortage-print',
    { params },
  )
}
