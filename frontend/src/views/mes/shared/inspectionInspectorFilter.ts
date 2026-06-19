/** 検査員候補：製造部・仕上課所属のみ（検査実績収集・登録等で共用） */
import { getOrganizations, getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'

export const INSPECTION_DEPARTMENT_NAME = '製造部'
export const INSPECTION_SHIAGE_SECTION_NAME = '仕上課'

export interface InspectionInspectorOption {
  id: number
  username: string
  full_name?: string
  department?: string | null
  section?: string | null
}

export function isInspectionShiageSectionUser(u: {
  department?: string | null
  section?: string | null
}): boolean {
  return (
    (u.department || '').trim() === INSPECTION_DEPARTMENT_NAME &&
    (u.section || '').trim() === INSPECTION_SHIAGE_SECTION_NAME
  )
}

export async function resolveInspectionShiageSectionOrgIds(): Promise<{
  departmentId?: number
  sectionId?: number
}> {
  try {
    const orgs = await getOrganizations()
    const department = (orgs ?? []).find(
      (o) => o.type === 'department' && o.name === INSPECTION_DEPARTMENT_NAME,
    )
    const section = (orgs ?? []).find(
      (o) => o.type === 'section' && o.name === INSPECTION_SHIAGE_SECTION_NAME,
    )
    return { departmentId: department?.id, sectionId: section?.id }
  } catch {
    return {}
  }
}

/** @deprecated use resolveInspectionShiageSectionOrgIds */
export async function resolveInspectionShiageSectionId(): Promise<number | undefined> {
  const { sectionId } = await resolveInspectionShiageSectionOrgIds()
  return sectionId
}

/** 製造部・仕上課所属の有効ユーザーを取得 */
export async function fetchInspectionShiageSectionInspectors(): Promise<InspectionInspectorOption[]> {
  const { departmentId, sectionId } = await resolveInspectionShiageSectionOrgIds()
  const res = (await getUsers({
    page: 1,
    page_size: 500,
    status: 'active',
    department_id: departmentId,
    section_id: sectionId,
  })) as unknown as PaginatedUserResponse
  return (res?.items ?? [])
    .filter((u): u is UserListItem & { id: number } => u.id != null && isInspectionShiageSectionUser(u))
    .map((u) => ({
      id: Number(u.id),
      username: u.username ?? '',
      full_name: u.full_name,
      department: u.department,
      section: u.section,
    }))
    .sort((a, b) =>
      (a.full_name || a.username).localeCompare(b.full_name || b.username, 'ja', {
        sensitivity: 'base',
      }),
    )
}
