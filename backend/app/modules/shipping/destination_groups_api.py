"""
納入先分组 API (destination_groups)
- GET /destination-groups/destination_groups_list: 出荷リスト用分组一覧 (page_key=destination_groups_list)
- GET /destination-groups/{page_key}: 指定 page_key の分组一覧
- POST /destination-groups: 新規分组作成
- PUT /destination-groups/{id}: 分组更新
- DELETE /destination-groups/{id}: 分组削除
- PUT /destination-groups/page/{page_key}: 一括保存
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Any, Optional
import json

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


# ---------- Schemas ----------
class DestinationItem(BaseModel):
    value: str
    label: Optional[str] = None


class GroupCreate(BaseModel):
    pageKey: str
    groupName: str
    destinations: List[Any] = []


class GroupUpdate(BaseModel):
    groupName: str
    destinations: List[Any] = []


class GroupSaveItem(BaseModel):
    id: Optional[int] = None
    groupName: str
    destinations: List[Any] = []


class PageGroupsSave(BaseModel):
    groups: List[GroupSaveItem]


def _serialize_destinations(destinations: Any) -> str:
    if isinstance(destinations, str):
        return destinations
    return json.dumps(destinations or [], ensure_ascii=False)


def _parse_destinations(raw: Any) -> list:
    if raw is None:
        return []
    if isinstance(raw, (list, dict)):
        return raw if isinstance(raw, list) else [raw]
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


# ---------- GET /destination-groups/destination_groups_list ----------
@router.get("/destination_groups_list")
async def list_destination_groups_for_shipping_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """出荷構成表ページ用の納入先分组一覧（page_key='destination_groups_list'）"""
    return await _list_by_page_key(db, "destination_groups_list")


# ---------- GET /destination-groups/{page_key} ----------
@router.get("/{page_key}")
async def list_destination_groups(
    page_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定 page_key の納入先分组一覧"""
    return await _list_by_page_key(db, page_key)


async def _list_by_page_key(db: AsyncSession, page_key: str) -> List[dict]:
    q = text(
        "SELECT id, page_key, group_name, destinations, updated_at, created_at "
        "FROM destination_groups WHERE page_key = :page_key ORDER BY id"
    )
    result = await db.execute(q, {"page_key": page_key})
    rows = result.mappings().all()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "group_name": r["group_name"],
            "destinations": _parse_destinations(r["destinations"]),
        })
    return out


# ---------- POST /destination-groups ----------
@router.post("")
async def create_destination_group(
    body: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先分组を新規作成"""
    dest_json = _serialize_destinations(body.destinations)
    q = text(
        "INSERT INTO destination_groups (page_key, group_name, destinations) "
        "VALUES (:page_key, :group_name, :destinations)"
    )
    await db.execute(q, {
        "page_key": body.pageKey,
        "group_name": body.groupName,
        "destinations": dest_json,
    })
    await db.commit()
    # get last insert id (MySQL)
    r = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
    row = r.mappings().first()
    new_id = int(row["id"]) if row else None
    return {"id": new_id, "success": True}


# ---------- PUT /destination-groups/page/{page_key} （先に定義し /{group_id} より優先） ----------
@router.put("/page/{page_key}")
async def save_page_groups(
    page_key: str,
    body: PageGroupsSave,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定 page_key の分组を一括更新"""
    for g in body.groups:
        if g.id is not None:
            dest_json = _serialize_destinations(g.destinations)
            q = text(
                "UPDATE destination_groups SET group_name = :group_name, destinations = :destinations "
                "WHERE id = :id"
            )
            await db.execute(q, {
                "id": g.id,
                "group_name": g.groupName,
                "destinations": dest_json,
            })
    await db.commit()
    return {"success": True}


# ---------- PUT /destination-groups/{id} ----------
@router.put("/{group_id}")
async def update_destination_group(
    group_id: int,
    body: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先分组を更新"""
    dest_json = _serialize_destinations(body.destinations)
    q = text(
        "UPDATE destination_groups SET group_name = :group_name, destinations = :destinations "
        "WHERE id = :id"
    )
    result = await db.execute(q, {
        "id": group_id,
        "group_name": body.groupName,
        "destinations": dest_json,
    })
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="グループが見つかりません")
    return {"success": True}


# ---------- DELETE /destination-groups/{id} ----------
@router.delete("/{group_id}")
async def delete_destination_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先分组を削除"""
    q = text("DELETE FROM destination_groups WHERE id = :id")
    result = await db.execute(q, {"id": group_id})
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="グループが見つかりません")
    return {"success": True}
