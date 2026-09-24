/**
 * 工場レイアウト API
 */
import request from '@/shared/api/request'

export type LayoutObjectType = 'machine' | 'aisle' | 'material_zone' | 'workshop'
export type LayoutKind = 'site' | 'workshop'

export interface FactoryLayoutSummary {
  id: number
  name: string
  canvas_width: number
  canvas_height: number
  grid_size: number
  kind: LayoutKind
  parent_id: number | null
}

export interface FactoryLayoutObject {
  id: number
  layout_id: number
  object_type: LayoutObjectType
  x: number
  y: number
  width: number
  height: number
  label: string
  ref_cd: string | null
  z_index: number
  rotation: number
  locked: boolean
  group_key: string | null
  fill_color: string | null
  border_color: string | null
  opacity: number
  child_layout_id: number | null
}

export interface FactoryLayoutDetail extends FactoryLayoutSummary {
  objects: FactoryLayoutObject[]
}

export interface ObjectStatus {
  status: string
  message: string
  updated_at: string | null
  source: string
  payload: Record<string, unknown> | null
}

export interface LayoutStatusResponse {
  statuses: Record<string, ObjectStatus>
}

export interface LayoutObjectInput {
  id?: number | null
  object_type: LayoutObjectType
  x: number
  y: number
  width: number
  height: number
  label: string
  ref_cd?: string | null
  z_index: number
  rotation?: number
  locked?: boolean
  group_key?: string | null
  fill_color?: string | null
  border_color?: string | null
  opacity?: number
  child_layout_id?: number | null
}

export function normalizeLayoutObject(raw: FactoryLayoutObject): FactoryLayoutObject {
  return {
    ...raw,
    rotation: raw.rotation ?? 0,
    locked: Boolean(raw.locked),
    group_key: raw.group_key || null,
    fill_color: raw.fill_color || null,
    border_color: raw.border_color || null,
    opacity: raw.opacity ?? 100,
    child_layout_id: raw.child_layout_id ?? null,
  }
}

export function listFactoryLayouts(): Promise<FactoryLayoutSummary[]> {
  return request.get('/api/factory-layout/layouts') as Promise<FactoryLayoutSummary[]>
}

export function getFactoryLayout(id: number): Promise<FactoryLayoutDetail> {
  return request.get(`/api/factory-layout/layouts/${id}`) as Promise<FactoryLayoutDetail>
}

export function createFactoryLayout(body: {
  name: string
  canvas_width?: number
  canvas_height?: number
  grid_size?: number
  kind?: LayoutKind
  parent_id?: number | null
}): Promise<FactoryLayoutDetail> {
  return request.post('/api/factory-layout/layouts', body) as Promise<FactoryLayoutDetail>
}

export function updateFactoryLayout(
  id: number,
  body: Partial<Pick<FactoryLayoutSummary, 'name' | 'canvas_width' | 'canvas_height' | 'grid_size'>>,
): Promise<FactoryLayoutSummary> {
  return request.put(`/api/factory-layout/layouts/${id}`, body) as Promise<FactoryLayoutSummary>
}

export function deleteFactoryLayout(id: number): Promise<{ message: string }> {
  return request.delete(`/api/factory-layout/layouts/${id}`) as Promise<{ message: string }>
}

export function saveFactoryLayoutObjects(
  layoutId: number,
  objects: LayoutObjectInput[],
): Promise<FactoryLayoutObject[]> {
  return request.put(`/api/factory-layout/layouts/${layoutId}/objects`, {
    objects,
  }) as Promise<FactoryLayoutObject[]>
}

export function getFactoryLayoutStatus(layoutId: number): Promise<LayoutStatusResponse> {
  return request.get(`/api/factory-layout/layouts/${layoutId}/status`) as Promise<LayoutStatusResponse>
}

export function updateFactoryObjectStatus(
  objectId: number,
  body: { status: string; message: string },
): Promise<ObjectStatus> {
  return request.put(`/api/factory-layout/objects/${objectId}/status`, body) as Promise<ObjectStatus>
}

export function listFactoryStorageLocations(): Promise<string[]> {
  return request.get('/api/factory-layout/storage-locations') as Promise<string[]>
}
