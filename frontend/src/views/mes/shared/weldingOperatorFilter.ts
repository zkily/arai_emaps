/** 溶接作業者候補：製造部・溶接課所属のみ（溶接実績・分析等で共用） */
import { getOrganizations, getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'

export const WELDING_DEPARTMENT_NAME = '製造部'
export const WELDING_SECTION_NAME = '溶接課'

export function isWeldingSectionOperatorUser(u: {
  department?: string | null
  section?: string | null
}): boolean {
  return (
    (u.department || '').trim() === WELDING_DEPARTMENT_NAME &&
    (u.section || '').trim() === WELDING_SECTION_NAME
  )
}

export async function resolveWeldingSectionOrgIds(): Promise<{
  departmentId?: number
  sectionId?: number
}> {
  try {
    const orgs = await getOrganizations()
    const department = (orgs ?? []).find(
      (o) => o.type === 'department' && o.name === WELDING_DEPARTMENT_NAME,
    )
    const section = (orgs ?? []).find(
      (o) => o.type === 'section' && o.name === WELDING_SECTION_NAME,
    )
    return { departmentId: department?.id, sectionId: section?.id }
  } catch {
    return {}
  }
}

/** 製造部・溶接課所属の有効ユーザーを取得 */
export async function fetchWeldingSectionOperators(): Promise<UserListItem[]> {
  const { departmentId, sectionId } = await resolveWeldingSectionOrgIds()
  const res = (await getUsers({
    page: 1,
    page_size: 500,
    status: 'active',
    department_id: departmentId,
    section_id: sectionId,
  })) as unknown as PaginatedUserResponse
  return (res?.items ?? [])
    .filter((u): u is UserListItem => u.id != null && isWeldingSectionOperatorUser(u))
    .sort((a, b) =>
      (a.full_name || a.username).localeCompare(b.full_name || b.username, 'ja', {
        sensitivity: 'base',
      }),
    )
}
