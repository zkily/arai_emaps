import type { BulkDisposalRetentionOverdueSummary } from '@/api/erp/bulkDisposalRetention'

export interface RetentionDeadlineHeaderOverview {
  as_of: string
  count: number
  samples: Array<{
    id: number
    product_name: string
    product_cd?: string | null
    management_no?: string | null
    processing_deadline_date?: string | null
    occurred_date?: string | null
    quantity: number
  }>
}

export function parseRetentionDeadlineOverview(
  raw: unknown,
): RetentionDeadlineHeaderOverview | null {
  const payload = (raw as BulkDisposalRetentionOverdueSummary | undefined) ?? null
  if (!payload || !payload.count || payload.count <= 0) return null

  return {
    as_of: payload.as_of,
    count: payload.count,
    samples: (payload.list || []).slice(0, 6).map((row) => ({
      id: row.id,
      product_name: row.product_name,
      product_cd: row.product_cd,
      management_no: row.management_no,
      processing_deadline_date: row.processing_deadline_date,
      occurred_date: row.occurred_date,
      quantity: row.quantity,
    })),
  }
}
