"""
システム管理 API エンドポイント
ユーザー管理、組織管理、権限・ロール管理
"""
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_password_hash
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.permission_service import (
    assert_super_admin,
    user_is_super_admin,
)
from app.modules.auth.data_scope_service import (
    apply_scope_to_users_query,
    resolve_user_data_scope,
)
from app.modules.auth.role_codes import (
    LEGACY_ROLE_NAME_TO_CODE,
    legacy_role_code_from_name,
    user_role_code_for_role,
)
from app.modules.system.models import (
    Organization, Role, Menu, RoleMenuPermission, 
    RoleOperationPermission, UserRole
)
from app.modules.system.schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, OrganizationTreeNode,
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse, OperationPermission,
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserSearchParams, 
    PaginatedUserResponse, UserStatus,
    MenuResponse, MenuTreeNode, MenuCreate, MenuUpdate, MenuSyncRequest,
    PasswordResetRequest,
    UserPasswordSet,
)

logger = logging.getLogger(__name__)

router = APIRouter()

ROLE_CODE_TO_NAME = {code: name for name, code in LEGACY_ROLE_NAME_TO_CODE.items()}
_ROLE_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,49}$")


def _normalize_role_code(code: str | None) -> str | None:
    if code is None:
        return None
    c = code.strip().lower()
    return c or None


async def _ensure_role_code_unique(
    db: AsyncSession, code: str, exclude_role_id: int | None = None
) -> None:
    q = select(Role.id).where(Role.code == code)
    if exclude_role_id is not None:
        q = q.where(Role.id != exclude_role_id)
    if (await db.execute(q)).scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="このロールコードは既に使用されています")


async def _sync_users_role_for_role(db: AsyncSession, role_id: int, role_code: str) -> None:
    subq = select(UserRole.user_id).where(UserRole.role_id == role_id)
    await db.execute(update(User).where(User.id.in_(subq)).values(role=role_code[:20]))


async def _fetch_user_role_map(db: AsyncSession, user_ids: List[int]) -> dict:
    """user_id -> (role_id, role_name) from user_roles + roles."""
    if not user_ids:
        return {}
    result = await db.execute(
        select(UserRole.user_id, UserRole.role_id, Role.name)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id.in_(user_ids))
    )
    return {user_id: (role_id, role_name) for user_id, role_id, role_name in result.all()}


# ========== ユーザー管理 API ==========

@router.get("/users", response_model=PaginatedUserResponse, summary="ユーザー一覧取得")
async def get_users(
    keyword: Optional[str] = Query(None, description="キーワード（ユーザー名・氏名・メールアドレスで曖昧検索）"),
    department_id: Optional[int] = Query(None, description="部門IDで絞り込み"),
    section_id: Optional[int] = Query(None, description="課IDで絞り込み"),
    status: Optional[str] = Query(None, description="ステータスで絞り込み"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=500, description="1ページあたりの件数（最大500・MESドロップダウン等）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ユーザー一覧を取得（roles.data_scope に基づくデータ範囲）"""
    query = select(User)

    scope = await resolve_user_data_scope(db, current_user)
    query = apply_scope_to_users_query(query, scope, User)
    
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                User.username.ilike(kw),
                User.full_name.ilike(kw),
                User.email.ilike(kw),
            )
        )
    if department_id is not None:
        query = query.where(User.department_id == department_id)
    if section_id is not None:
        query = query.where(User.section_id == section_id)
    if status:
        query = query.where(User.is_active == (status == "active"))
    
    # 総件数取得
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # ページネーション
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.id)
    
    result = await db.execute(query)
    users = result.scalars().all()
    user_role_map = await _fetch_user_role_map(db, [u.id for u in users])

    # 部門・課名取得
    org_ids = set()
    for u in users:
        if getattr(u, "department_id", None):
            org_ids.add(u.department_id)
        if getattr(u, "section_id", None):
            org_ids.add(u.section_id)
    org_map = {}
    if org_ids:
        org_result = await db.execute(select(Organization).where(Organization.id.in_(org_ids)))
        for org in org_result.scalars().all():
            org_map[org.id] = org.name
    
    items = []
    for user in users:
        user_status = "locked" if not user.is_active else "active"
        dept_id = getattr(user, "department_id", None)
        sect_id = getattr(user, "section_id", None)
        two_fa = getattr(user, "two_factor_enabled", False)
        last_ln = getattr(user, "last_login_at", None)
        role_code = user.role or "user"
        role_id, role_name = user_role_map.get(user.id, (None, None))
        if role_name is None:
            role_name = ROLE_CODE_TO_NAME.get(role_code)
        items.append(UserListResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            department=org_map.get(dept_id) if dept_id else None,
            section=org_map.get(sect_id) if sect_id else None,
            role=role_code,
            role_id=role_id,
            role_name=role_name,
            status=UserStatus(user_status),
            two_factor=two_fa,
            last_login=last_ln.strftime("%Y-%m-%d %H:%M:%S") if last_ln else None,
        ))
    
    pages = (total + page_size - 1) // page_size
    
    return PaginatedUserResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/stats/online", summary="現在の利用者数（ログイン中）")
async def get_online_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """users テーブルで last_login_token が NULL でない件数（未ログアウトのユーザー数）を返す"""
    try:
        stmt = select(func.count(User.id)).where(User.last_login_token.isnot(None))
        result = await db.execute(stmt)
        count = result.scalar() or 0
        return {"online_count": count}
    except Exception as e:
        logger.debug("online count error: %s", e)
        return {"online_count": 0}


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="ユーザー新規登録")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規ユーザーを登録"""
    await assert_super_admin(db, current_user)
    
    # 重複チェック
    existing = await db.execute(
        select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ユーザー名またはメールアドレスが既に使用されています")
    
    role_result = await db.execute(select(Role).where(Role.id == user_data.role_id))
    role_obj = role_result.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="指定されたロールが見つかりません")
    if not role_obj.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なロールは割り当てできません")
    role_code = user_role_code_for_role(role_obj)

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=role_code,
        is_active=True,
        department_id=user_data.department_id,
        section_id=user_data.section_id,
        two_factor_enabled=user_data.two_factor_enabled or False,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    db.add(UserRole(user_id=new_user.id, role_id=user_data.role_id))
    await db.commit()
    
    logger.info(f"User created: {new_user.username} by {current_user.username}")
    
    dept_name = None
    sect_name = None
    org_ids = [oid for oid in (new_user.department_id, new_user.section_id) if oid]
    if org_ids:
        o = await db.execute(select(Organization).where(Organization.id.in_(org_ids)))
        for ob in o.scalars().all():
            if ob.id == new_user.department_id:
                dept_name = ob.name
            if ob.id == new_user.section_id:
                sect_name = ob.name
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        department_id=getattr(new_user, "department_id", None),
        section_id=getattr(new_user, "section_id", None),
        role_id=user_data.role_id,
        two_factor_enabled=getattr(new_user, "two_factor_enabled", False),
        status=UserStatus.active,
        last_login=None,
        department_name=dept_name,
        section_name=sect_name,
        role_name=role_obj.name,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )


@router.put("/users/{user_id}", response_model=UserResponse, summary="ユーザー更新")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ユーザー情報を更新"""
    if not await user_is_super_admin(db, current_user) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="権限がありません")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")
    
    update_data = user_data.model_dump(exclude_unset=True)
    if "status" in update_data:
        user.is_active = update_data["status"] == "active"
        del update_data["status"]

    assigned_role_id: Optional[int] = None
    assigned_role_name: Optional[str] = None
    if "role_id" in update_data:
        rid_raw = update_data.pop("role_id")
        rid = int(rid_raw) if rid_raw is not None and rid_raw != "" else None
        if not rid or rid <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ロールの指定が必須です。管理者にロールを割り当ててください。",
            )
        role_result = await db.execute(select(Role).where(Role.id == rid))
        role_obj = role_result.scalar_one_or_none()
        if not role_obj:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="指定されたロールが見つかりません")
        if not role_obj.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なロールは割り当てできません")
        await db.execute(delete(UserRole).where(UserRole.user_id == user.id))
        user.role = user_role_code_for_role(role_obj)
        db.add(UserRole(user_id=user.id, role_id=rid))
        assigned_role_id = rid
        assigned_role_name = role_obj.name
    
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User updated: {user.username} by {current_user.username}")
    
    dept_name = None
    sect_name = None
    org_ids = [oid for oid in (getattr(user, "department_id", None), getattr(user, "section_id", None)) if oid]
    if org_ids:
        o = await db.execute(select(Organization).where(Organization.id.in_(org_ids)))
        for ob in o.scalars().all():
            if ob.id == getattr(user, "department_id", None):
                dept_name = ob.name
            if ob.id == getattr(user, "section_id", None):
                sect_name = ob.name
    
    if assigned_role_id is None:
        role_map = await _fetch_user_role_map(db, [user.id])
        assigned_role_id, assigned_role_name = role_map.get(user.id, (None, None))
        if assigned_role_name is None:
            assigned_role_name = ROLE_CODE_TO_NAME.get(user.role or "user")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department_id=getattr(user, "department_id", None),
        section_id=getattr(user, "section_id", None),
        role_id=assigned_role_id,
        two_factor_enabled=getattr(user, "two_factor_enabled", False),
        status=UserStatus.active if user.is_active else UserStatus.locked,
        last_login=user.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(user, "last_login_at", None) else None,
        department_name=dept_name,
        section_name=sect_name,
        role_name=assigned_role_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/users/{user_id}/lock", summary="ユーザーロック")
async def lock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ユーザーをロック（自分自身はロック不可）"""
    await assert_super_admin(db, current_user)
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身をロックすることはできません。他の管理者にロック解除を依頼してください。",
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")
    
    user.is_active = False
    await db.commit()
    
    logger.info(f"User locked: {user.username} by {current_user.username}")
    return {"message": f"ユーザー「{user.username}」をロックしました"}


@router.post("/users/{user_id}/unlock", summary="ユーザーロック解除")
async def unlock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ユーザーロックを解除"""
    await assert_super_admin(db, current_user)
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")
    
    user.is_active = True
    await db.commit()
    
    logger.info(f"User unlocked: {user.username} by {current_user.username}")
    return {"message": f"ユーザー「{user.username}」のロックを解除しました"}


@router.post("/users/{user_id}/reset-password", summary="パスワード再設定")
async def reset_user_password(
    user_id: int,
    body: UserPasswordSet,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """管理者が指定した新しいパスワードでユーザーのパスワードを直接更新"""
    await assert_super_admin(db, current_user)
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")
    
    user.hashed_password = get_password_hash(body.new_password)
    await db.commit()
    
    logger.info(f"Password updated for user: {user.username} by {current_user.username}")
    return {"message": "パスワードを更新しました"}


# ========== 組織管理 API ==========

@router.get("/organizations", response_model=List[OrganizationResponse], summary="組織一覧取得")
async def get_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """組織一覧を取得"""
    result = await db.execute(
        select(Organization).where(Organization.is_active == True).order_by(Organization.sort_order, Organization.id)
    )
    return result.scalars().all()


@router.get("/organizations/tree", response_model=List[OrganizationTreeNode], summary="組織ツリー取得")
async def get_organization_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """組織ツリー構造を取得"""
    result = await db.execute(
        select(Organization).where(Organization.is_active == True).order_by(Organization.sort_order, Organization.id)
    )
    organizations = result.scalars().all()
    
    # ツリー構造に変換
    org_dict = {org.id: {
        "id": org.id,
        "code": org.code,
        "name": org.name,
        "type": org.type,
        "parent_id": org.parent_id,
        "children": []
    } for org in organizations}
    
    tree = []
    for org in organizations:
        node = org_dict[org.id]
        if org.parent_id and org.parent_id in org_dict:
            org_dict[org.parent_id]["children"].append(node)
        else:
            tree.append(node)
    
    return tree


@router.get("/organizations/{org_id}", response_model=OrganizationResponse, summary="組織詳細取得")
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """組織詳細を取得（一覧・ツリーと同様に is_active のみ）"""
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_active == True,
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="組織が見つかりません")
    
    return org


@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, summary="組織作成")
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規組織を作成"""
    await assert_super_admin(db, current_user)
    
    # 重複チェック
    existing = await db.execute(select(Organization).where(Organization.code == org_data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="組織コードが既に使用されています")
    
    new_org = Organization(**org_data.model_dump())
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    logger.info(f"Organization created: {new_org.code} by {current_user.username}")
    return new_org


@router.put("/organizations/{org_id}", response_model=OrganizationResponse, summary="組織更新")
async def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """組織を更新"""
    await assert_super_admin(db, current_user)
    
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="組織が見つかりません")
    
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)
    
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Organization updated: {org.code} by {current_user.username}")
    return org


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT, summary="組織削除")
async def delete_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """組織を削除（物理削除：DBから行を削除）"""
    await assert_super_admin(db, current_user)
    
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="組織が見つかりません")
    
    code = org.code
    await db.delete(org)
    await db.commit()
    
    logger.info(f"Organization deleted: {code} by {current_user.username}")


# ========== ロール・権限管理 API ==========

@router.get("/roles", response_model=List[RoleListResponse], summary="ロール一覧取得")
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ロール一覧を取得"""
    result = await db.execute(
        select(Role).where(Role.is_active == True).order_by(Role.id)
    )
    roles = result.scalars().all()
    
    # ユーザー数をカウント
    role_list = []
    for role in roles:
        count_result = await db.execute(
            select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id)
        )
        user_count = count_result.scalar() or 0
        
        role_list.append(RoleListResponse(
            id=role.id,
            name=role.name,
            code=getattr(role, "code", None),
            is_system=role.is_system,
            is_super_admin=bool(getattr(role, "is_super_admin", False)),
            user_count=user_count,
        ))
    
    return role_list


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="ロール詳細取得")
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ロール詳細を取得"""
    result = await db.execute(
        select(Role)
        .options(
            selectinload(Role.menu_permissions),
            selectinload(Role.operation_permissions),
        )
        .where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません")
    
    # ユーザー数をカウント
    count_result = await db.execute(
        select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id)
    )
    user_count = count_result.scalar() or 0
    
    menu_permission_ids = [mp.menu_id for mp in role.menu_permissions]
    operation_perms = [
        OperationPermission(
            module=op.module,
            can_create=op.can_create,
            can_edit=op.can_edit,
            can_delete=op.can_delete,
            can_export=op.can_export,
            can_approve=op.can_approve,
        )
        for op in role.operation_permissions
    ]
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        code=getattr(role, "code", None),
        description=role.description,
        is_system=role.is_system,
        is_super_admin=bool(getattr(role, "is_super_admin", False)),
        data_scope=role.data_scope,
        custom_departments=role.custom_departments,
        is_active=role.is_active,
        user_count=user_count,
        menu_permissions=menu_permission_ids,
        operation_permissions=operation_perms,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


def _validate_role_code_format(code: str) -> None:
    if not _ROLE_CODE_RE.match(code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ロールコードは英小文字・数字・アンダースコア（先頭は英字）のみ使用できます",
        )


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="ロール作成")
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規ロールを作成"""
    await assert_super_admin(db, current_user)
    
    # 重複チェック
    existing = await db.execute(select(Role).where(Role.name == role_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ロール名が既に使用されています")

    code = _normalize_role_code(role_data.code)
    if code:
        _validate_role_code_format(code)
        await _ensure_role_code_unique(db, code)

    new_role = Role(
        name=role_data.name,
        code=code,
        description=role_data.description,
        data_scope=role_data.data_scope.value,
        custom_departments=role_data.custom_departments,
        is_system=False,
        is_super_admin=bool(role_data.is_super_admin),
    )
    db.add(new_role)
    await db.flush()
    if not new_role.code:
        new_role.code = f"role_{new_role.id}"
        await _ensure_role_code_unique(db, new_role.code)
    
    # メニュー権限を追加
    for menu_id in role_data.menu_permissions:
        db.add(RoleMenuPermission(role_id=new_role.id, menu_id=menu_id))
    
    # 操作権限を追加
    for op in role_data.operation_permissions:
        db.add(RoleOperationPermission(
            role_id=new_role.id,
            module=op.module,
            can_create=op.can_create,
            can_edit=op.can_edit,
            can_delete=op.can_delete,
            can_export=op.can_export,
            can_approve=op.can_approve,
        ))
    
    await db.commit()
    await db.refresh(new_role)
    
    logger.info(f"Role created: {new_role.name} by {current_user.username}")
    
    return RoleResponse(
        id=new_role.id,
        name=new_role.name,
        code=new_role.code,
        description=new_role.description,
        is_system=new_role.is_system,
        is_super_admin=bool(new_role.is_super_admin),
        data_scope=new_role.data_scope,
        custom_departments=new_role.custom_departments,
        is_active=new_role.is_active,
        user_count=0,
        menu_permissions=role_data.menu_permissions,
        operation_permissions=role_data.operation_permissions,
        created_at=new_role.created_at,
        updated_at=new_role.updated_at,
    )


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="ロール更新")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ロールを更新"""
    await assert_super_admin(db, current_user)
    
    result = await db.execute(
        select(Role)
        .options(
            selectinload(Role.menu_permissions),
            selectinload(Role.operation_permissions),
        )
        .where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません")
    
    # 基本情報更新
    update_data = role_data.model_dump(exclude_unset=True, exclude={"menu_permissions", "operation_permissions"})
    if "code" in update_data:
        code = _normalize_role_code(update_data.pop("code"))
        if code:
            _validate_role_code_format(code)
            await _ensure_role_code_unique(db, code, exclude_role_id=role_id)
            role.code = code
            await _sync_users_role_for_role(db, role_id, code)
    if "data_scope" in update_data and update_data["data_scope"]:
        update_data["data_scope"] = update_data["data_scope"].value

    for field, value in update_data.items():
        setattr(role, field, value)
    
    # メニュー権限更新（role_menu_permissions）
    if role_data.menu_permissions is not None:
        await db.execute(
            RoleMenuPermission.__table__.delete().where(RoleMenuPermission.role_id == role_id)
        )
        for menu_id in role_data.menu_permissions:
            db.add(RoleMenuPermission(role_id=role.id, menu_id=menu_id))
    
    # 操作権限更新（role_operation_permissions）
    if role_data.operation_permissions is not None:
        await db.execute(
            RoleOperationPermission.__table__.delete().where(RoleOperationPermission.role_id == role_id)
        )
        for op in role_data.operation_permissions:
            db.add(RoleOperationPermission(
                role_id=role.id,
                module=op.module,
                can_create=op.can_create,
                can_edit=op.can_edit,
                can_delete=op.can_delete,
                can_export=op.can_export,
                can_approve=op.can_approve,
            ))
    
    await db.commit()
    await db.refresh(role)
    
    count_result = await db.execute(
        select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id)
    )
    user_count = count_result.scalar() or 0
    
    menu_permission_ids = [mp.menu_id for mp in role.menu_permissions] if role_data.menu_permissions is None else role_data.menu_permissions
    
    if role_data.operation_permissions is not None:
        operation_perms = list(role_data.operation_permissions)
    else:
        await db.refresh(role, attribute_names=["operation_permissions"])
        operation_perms = [
            OperationPermission(
                module=op.module,
                can_create=op.can_create,
                can_edit=op.can_edit,
                can_delete=op.can_delete,
                can_export=op.can_export,
                can_approve=op.can_approve,
            )
            for op in role.operation_permissions
        ]
    
    logger.info(f"Role updated: {role.name} by {current_user.username}")
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        code=getattr(role, "code", None),
        description=role.description,
        is_system=role.is_system,
        is_super_admin=bool(getattr(role, "is_super_admin", False)),
        data_scope=role.data_scope,
        custom_departments=role.custom_departments,
        is_active=role.is_active,
        user_count=user_count,
        menu_permissions=menu_permission_ids,
        operation_permissions=operation_perms,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="ロール削除")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ロールを削除"""
    await assert_super_admin(db, current_user)
    
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません")
    
    if role.is_system:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="システムロールは削除できません")
    
    role.is_active = False
    await db.commit()
    
    logger.info(f"Role deleted: {role.name} by {current_user.username}")


# ========== メニュー API ==========

@router.get("/menus", response_model=List[MenuResponse], summary="メニュー一覧取得")
async def get_menus(
    include_inactive: bool = Query(False, description="無効メニューも含む（管理用）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メニュー一覧を取得"""
    query = select(Menu).order_by(Menu.sort_order, Menu.id)
    if not include_inactive:
        query = query.where(Menu.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/menus", response_model=MenuResponse, status_code=status.HTTP_201_CREATED, summary="メニュー新規登録")
async def create_menu(
    data: MenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規メニューを登録（管理者のみ）"""
    await assert_super_admin(db, current_user)
    existing = await db.execute(select(Menu).where(Menu.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"メニューコード '{data.code}' は既に存在します")
    menu = Menu(**data.model_dump())
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return menu


@router.put("/menus/{menu_id}", response_model=MenuResponse, summary="メニュー更新")
async def update_menu(
    menu_id: int,
    data: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メニューを更新（管理者のみ）"""
    await assert_super_admin(db, current_user)
    result = await db.execute(select(Menu).where(Menu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="メニューが見つかりません")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(menu, k, v)
    await db.commit()
    await db.refresh(menu)
    return menu


@router.delete("/menus/{menu_id}", status_code=status.HTTP_204_NO_CONTENT, summary="メニュー削除")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メニューを削除（管理者のみ、子メニューは parent_id が NULL に）"""
    await assert_super_admin(db, current_user)
    result = await db.execute(select(Menu).where(Menu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="メニューが見つかりません")
    await db.delete(menu)
    await db.commit()
    return None


@router.post("/menus/sync", response_model=List[MenuResponse], summary="ルート定義からメニュー同期")
async def sync_menus(
    body: MenuSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ルート定義（code 一覧）を DB に同期。既存は更新、新規は追加。code が DB にないものは削除しない。"""
    await assert_super_admin(db, current_user)
    # 既存メニューを code で取得
    result = await db.execute(select(Menu))
    existing_by_code = {m.code: m for m in result.scalars().all()}
    # parent_code -> id マップ（同期後に確定する id を使うため、先に全件処理してから親子を設定）
    code_to_id_after_sync: dict = {}
    updated_menus: List[Menu] = []
    for item in body.items:
        parent_id = None
        if item.parent_code:
            # 既存の親があればその id、なければ今回の items 内の code から解決（同一ロット内の親）
            parent_id = existing_by_code.get(item.parent_code)
            if parent_id:
                parent_id = parent_id.id
            elif item.parent_code in code_to_id_after_sync:
                parent_id = code_to_id_after_sync[item.parent_code]
        if item.code in existing_by_code:
            menu = existing_by_code[item.code]
            menu.name = item.name
            menu.path = item.path
            menu.icon = item.icon
            menu.sort_order = item.sort_order
            menu.parent_id = parent_id
            updated_menus.append(menu)
        else:
            menu = Menu(
                code=item.code,
                name=item.name,
                path=item.path,
                icon=item.icon,
                sort_order=item.sort_order,
                parent_id=parent_id,
                is_active=True,
            )
            db.add(menu)
            updated_menus.append(menu)
    await db.flush()  # 新規の id を取得するため
    for m in updated_menus:
        code_to_id_after_sync[m.code] = m.id
    # 親コードが今回の items 内にある場合、親 id を再設定
    for item in body.items:
        if not item.parent_code:
            continue
        pid = code_to_id_after_sync.get(item.parent_code)
        if pid is None:
            continue
        m = existing_by_code.get(item.code) or next((x for x in updated_menus if x.code == item.code), None)
        if m:
            m.parent_id = pid
    await db.commit()
    for m in updated_menus:
        await db.refresh(m)
    return updated_menus


@router.get("/menus/tree", response_model=List[MenuTreeNode], summary="メニューツリー取得")
async def get_menu_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メニューツリー構造を取得"""
    result = await db.execute(
        select(Menu).where(Menu.is_active == True).order_by(Menu.sort_order, Menu.id)
    )
    menus = result.scalars().all()
    
    # ツリー構造に変換
    menu_dict = {menu.id: {
        "id": menu.id,
        "code": menu.code,
        "label": menu.name,
        "children": []
    } for menu in menus}
    
    tree = []
    for menu in menus:
        node = menu_dict[menu.id]
        if menu.parent_id and menu.parent_id in menu_dict:
            menu_dict[menu.parent_id]["children"].append(node)
        else:
            tree.append(node)
    
    return tree


_NAGOYA_LAT = 35.1815
_NAGOYA_LON = 136.9066


def _wmo_weather_code_to_emoji(code: int) -> str:
    if code == 0:
        return "☀️"
    if 1 <= code <= 3:
        return "⛅"
    if 4 <= code <= 48:
        return "🌫️"
    if 49 <= code <= 57:
        return "🌦️"
    if 58 <= code <= 67:
        return "🌧️"
    if 68 <= code <= 77:
        return "❄️"
    if 78 <= code <= 82:
        return "🌧️"
    if 83 <= code <= 86:
        return "❄️"
    if 87 <= code <= 99:
        return "⛈️"
    return "🌤️"


@router.get("/header-weather", summary="ヘッダー用天気（名古屋）")
async def get_header_weather():
    """
    タブレット等の社内 LAN から Open-Meteo へ直接到達できない場合のプロキシ。
    認証不要（公開気象データ）。
    """
    import httpx

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={_NAGOYA_LAT}&longitude={_NAGOYA_LON}"
        "&current=temperature_2m,weather_code&timezone=Asia%2FTokyo"
    )
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=6.0)) as client:
            res = await client.get(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Smart-EMAPs/1.0 (header-weather)",
                },
            )
            res.raise_for_status()
            data = res.json()
        current = data.get("current") or {}
        temp = current.get("temperature_2m")
        code = current.get("weather_code")
        if not isinstance(temp, (int, float)):
            raise ValueError("temperature missing")
        weather_code = int(code) if isinstance(code, (int, float)) else 0
        return {
            "success": True,
            "temperature": f"{round(temp)}°C",
            "emoji": _wmo_weather_code_to_emoji(weather_code),
            "location": "名古屋",
        }
    except Exception as e:
        logger.warning("header-weather fetch failed: %s", e)
        raise HTTPException(status_code=502, detail="天気情報の取得に失敗しました") from e
