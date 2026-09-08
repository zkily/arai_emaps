/**
 * CP-SAT ジョブショップ展開 / 求解 API
 */
import request from '@/shared/api/request'

const BASE = '/api/cpsat'
const SOLVE_TIMEOUT_MS = 180_000

export type QtySource = 'confirmed' | 'forecast' | 'confirmed_or_forecast'
export type ObjectiveType = 'tardiness' | 'makespan' | 'weighted'

export interface ExpandRunIn {
  due_from: string
  due_to: string
  product_cds?: string[] | null
  qty_source?: QtySource
  name?: string | null
  max_jobs?: number | null
}

export interface SolveRunIn {
  max_solve_seconds?: number | null
  objective_type?: ObjectiveType | null
}

export interface ExpandWarningOut {
  skipped_no_qty: number
  skipped_no_due: number
  skipped_no_route: number
  skipped_no_ops: number
  incomplete_no_machine: number
  incomplete_zero_ptime: number
  skipped_product_cds: string[]
}

export interface CpsatCandidate {
  id: number
  machine_cd: string
  machine_name?: string | null
  process_time_sec: number
  setup_time_sec: number
  processing_sec: number
  is_assigned: boolean
}

export interface CpsatOperation {
  id: number
  op_index: number
  step_no: number
  process_cd: string
  process_name?: string | null
  yield_percent: number
  wait_sec_after: number
  q_input: number
  q_output: number
  start_sec?: number | null
  end_sec?: number | null
  start_at?: string | null
  end_at?: string | null
  assigned_machine_cd?: string | null
  assigned_machine_name?: string | null
  processing_sec?: number | null
  setup_sec?: number | null
  candidate_count: number
  candidates?: CpsatCandidate[] | null
}

export interface CpsatJob {
  id: number
  job_index: number
  source_type: string
  source_id?: number | null
  order_no?: string | null
  product_cd: string
  product_name?: string | null
  q_target: number
  q_start: number
  lot_size?: number | null
  lot_index?: number | null
  lot_count?: number | null
  due_at?: string | null
  due_sec?: number | null
  last_op_end_sec?: number | null
  tardiness_sec?: number | null
  operation_count: number
  incomplete: boolean
  operations?: CpsatOperation[] | null
}

export interface CpsatRun {
  id: number
  run_code?: string | null
  name?: string | null
  horizon_start: string
  horizon_end: string
  time_unit_sec: number
  objective_type: string
  status: string
  solver_status?: string | null
  wall_time_sec?: number | null
  makespan_sec?: number | null
  total_tardiness_sec?: number | null
  objective_value?: number | null
  job_count: number
  operation_count: number
  error_message?: string | null
  created_by?: string | null
  created_at?: string | null
  warnings?: ExpandWarningOut | null
  jobs?: CpsatJob[] | null
}

export function expandCpsatRun(body: ExpandRunIn): Promise<CpsatRun> {
  return request.post(`${BASE}/runs/expand`, body, { timeout: SOLVE_TIMEOUT_MS }) as Promise<CpsatRun>
}

export function solveCpsatRun(runId: number, body: SolveRunIn = {}): Promise<CpsatRun> {
  return request.post(`${BASE}/runs/${runId}/solve`, body, {
    timeout: SOLVE_TIMEOUT_MS,
  }) as Promise<CpsatRun>
}

export function listCpsatRuns(limit = 50): Promise<CpsatRun[]> {
  return request.get(`${BASE}/runs`, { params: { limit } }) as Promise<CpsatRun[]>
}

export function deleteCpsatRun(runId: number): Promise<{ ok: boolean; id: number }> {
  return request.delete(`${BASE}/runs/${runId}`) as Promise<{ ok: boolean; id: number }>
}

export function getCpsatRun(runId: number, sampleJobs = 0): Promise<CpsatRun> {
  return request.get(`${BASE}/runs/${runId}`, { params: { sample_jobs: sampleJobs } }) as Promise<CpsatRun>
}

export function listCpsatJobs(runId: number, params: { skip?: number; limit?: number } = {}): Promise<CpsatJob[]> {
  return request.get(`${BASE}/runs/${runId}/jobs`, {
    params: { skip: params.skip ?? 0, limit: params.limit ?? 500 },
  }) as Promise<CpsatJob[]>
}

export function getCpsatJob(runId: number, jobId: number): Promise<CpsatJob> {
  return request.get(`${BASE}/runs/${runId}/jobs/${jobId}`) as Promise<CpsatJob>
}
