/**
 * 棚卸（実地棚卸ログ）フロント専用 API。
 * バックエンド未接続時は localStorage に永続化して画面を動作させる。
 */
const STORAGE_KEY = 'smart-emaps-stocktake-logs-v1'

export interface InventoryLog {
  id: number
  item: string
  product_cd: string
  product_name: string
  process_cd?: string
  process_name?: string
  log_date: string
  log_time: string
  hd_no?: string
  pack_qty?: number | null
  case_qty?: number | null
  quantity: number
  remarks?: string
  worker_name?: string
  updated_at?: string
}

export interface InventoryFilters {
  keyword?: string
  dateRange?: string[]
  monthPicker?: string
  item?: string
  stageType?: string
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: string
}

function loadAll(): InventoryLog[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as InventoryLog[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveAll(items: InventoryLog[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}

function nextId(items: InventoryLog[]): number {
  const max = items.reduce((m, r) => Math.max(m, Number(r.id) || 0), 0)
  return max + 1
}

function filterRows(items: InventoryLog[], f: InventoryFilters): InventoryLog[] {
  let out = [...items]
  if (f.keyword) {
    const k = f.keyword.trim().toLowerCase()
    out = out.filter(
      (r) =>
        r.product_name?.toLowerCase().includes(k) ||
        r.product_cd?.toLowerCase().includes(k),
    )
  }
  if (f.item) {
    out = out.filter((r) => r.item === f.item)
  }
  if (f.stageType) {
    out = out.filter((r) => r.process_cd === f.stageType)
  }
  if (f.dateRange && f.dateRange.length === 2) {
    const [a, b] = f.dateRange
    out = out.filter((r) => r.log_date >= a && r.log_date <= b)
  }
  if (f.monthPicker) {
    const m = String(f.monthPicker).slice(0, 7)
    out = out.filter((r) => r.log_date.startsWith(m))
  }
  return out
}

function sortRows(items: InventoryLog[], sortBy: string, sortOrder: string): InventoryLog[] {
  const mul = sortOrder === 'asc' ? 1 : -1
  const key = sortBy || 'log_date'
  return [...items].sort((a, b) => {
    switch (key) {
      case 'quantity':
        return (Number(a.quantity) - Number(b.quantity)) * mul
      case 'product_cd':
        return String(a.product_cd).localeCompare(String(b.product_cd), 'ja') * mul
      case 'product_name':
        return String(a.product_name).localeCompare(String(b.product_name), 'ja') * mul
      case 'updated_at':
        return (
          (new Date(a.updated_at || 0).getTime() - new Date(b.updated_at || 0).getTime()) * mul
        )
      case 'log_date':
      default: {
        const da = `${a.log_date}T${a.log_time || '00:00:00'}`
        const db = `${b.log_date}T${b.log_time || '00:00:00'}`
        return (new Date(da).getTime() - new Date(db).getTime()) * mul
      }
    }
  })
}

export async function getInventoryLogs(filters: InventoryFilters) {
  const page = filters.page ?? 1
  const pageSize = filters.pageSize ?? 20
  const sortBy = filters.sortBy ?? 'log_date'
  const sortOrder = filters.sortOrder ?? 'desc'

  const all = loadAll()
  const filtered = filterRows(all, filters)
  const totalQuantity = filtered.reduce((s, r) => s + Number(r.quantity ?? 0), 0)
  const sorted = sortRows(filtered, sortBy, sortOrder)
  const start = (page - 1) * pageSize
  const list = sorted.slice(start, start + pageSize)

  return {
    list,
    total: filtered.length,
    totalQuantity,
  }
}

export async function createInventoryEntry(data: Partial<InventoryLog>) {
  const all = loadAll()
  const rec: InventoryLog = {
    id: nextId(all),
    item: String(data.item ?? ''),
    product_cd: String(data.product_cd ?? ''),
    product_name: String(data.product_name ?? ''),
    process_cd: data.process_cd,
    process_name: data.process_name,
    log_date: String(data.log_date ?? ''),
    log_time: String(data.log_time ?? ''),
    hd_no: data.hd_no,
    pack_qty: data.pack_qty ?? undefined,
    case_qty: data.case_qty ?? undefined,
    quantity: Number(data.quantity ?? 0),
    remarks: data.remarks,
    worker_name: data.remarks ? String(data.remarks) : '',
    updated_at: new Date().toISOString(),
  }
  all.push(rec)
  saveAll(all)
  return { data: rec }
}

export async function getRecentEntries(limit = 50, hdNo?: string) {
  let items = loadAll()
  if (hdNo) items = items.filter((r) => r.hd_no === hdNo)
  items.sort(
    (a, b) =>
      new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime(),
  )
  return { data: items.slice(0, limit) }
}

export async function deleteInventoryLog(id: number) {
  const all = loadAll().filter((r) => r.id !== id)
  saveAll(all)
  return { ok: true }
}

export async function importInventoryCSV() {
  return {
    data: {
      summary: { totalProcessed: 0, newRecords: 0, duplicates: 0 },
      fileDetails: {
        inventoryLog: { processed: 0, newRecords: 0, duplicates: 0, exists: false },
        partsLog: { processed: 0, newRecords: 0, duplicates: 0, exists: false },
        materialLog: { processed: 0, newRecords: 0, duplicates: 0, exists: false },
      },
    },
    message: 'CSVサーバー取込は未接続です（ローカル棚卸のみ利用可能）',
  }
}
