/** 検査員候補：仕上課所属のみ（検査実績収集・登録等で共用） */
import { getOrganizations, getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'

export const INSPECTION_SHIAGE_SECTION_NAME = '仕上課'

export interface InspectionInspectorOption {
  id: number
  username: string
  full_name?: string
  section?: string | null
}

export function isInspectionShiageSectionUser(u: { section?: string | null }): boolean {
  return (u.section || '').trim() === INSPECTION_SHIAGE_SECTION_NAME
}

export async function resolveInspectionShiageSectionId(): Promise<number | undefined> {
  try {
    const orgs = await getOrganizations()
    const section = (orgs ?? []).find(
      (o) => o.type === 'section' && o.name === INSPECTION_SHIAGE_SECTION_NAME,
    )
    return section?.id
  } catch {
    return undefined
  }
}

/** 仕上課所属の有効ユーザーを取得 */
export async function fetchInspectionShiageSectionInspectors(): Promise<InspectionInspectorOption[]> {
  const sectionId = await resolveInspectionShiageSectionId()
  const res = (await getUsers({
    page: 1,
    page_size: 500,
    status: 'active',
    section_id: sectionId,
  })) as unknown as PaginatedUserResponse
  return (res?.items ?? [])
    .filter((u): u is UserListItem & { id: number } => u.id != null && isInspectionShiageSectionUser(u))
    .map((u) => ({
      id: Number(u.id),
      username: u.username ?? '',
      full_name: u.full_name,
      section: u.section,
    }))
    .sort((a, b) =>
      (a.full_name || a.username).localeCompare(b.full_name || b.username, 'ja', {
        sensitivity: 'base',
      }),
    )
}
