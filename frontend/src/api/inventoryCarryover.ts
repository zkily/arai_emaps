/**
 * 棚卸繰越 API（バックエンド未実装時はプレースホルダ）
 */

export async function getCarryoverData(_params: { month: string; process_cd: string }) {
  return []
}

export async function executeCarryover(_params: {
  month: string
  process_cd: string
  selectedData: unknown[]
}) {
  return { successCount: 0 }
}

export async function getCarryoverHistory(params: {
  page?: number
  pageSize?: number
  [key: string]: unknown
}) {
  return {
    list: [],
    total: 0,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 20,
  }
}

export async function deleteCarryoverRecord(_id: number) {
  return { ok: true }
}

export async function addCarryoverRecord(_data: unknown) {
  return { ok: true }
}

export async function updateCarryoverRecord(_id: number, _data: unknown) {
  return { ok: true }
}

export async function exportCarryoverHistory(_params: unknown) {
  return { data: '' }
}
