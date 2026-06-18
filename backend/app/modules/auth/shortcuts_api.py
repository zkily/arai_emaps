"""
サイドバー常用ページ API
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.shortcuts_service import get_shortcuts, record_visit, replace_pins

router = APIRouter()


class ShortcutItem(BaseModel):
    path: str
    menu_code: str | None = None
    visit_count: int | None = None
    last_visited_at: str | None = None


class ShortcutsResponse(BaseModel):
    pinned: list[ShortcutItem]
    frequent: list[ShortcutItem]


class PinsUpdateRequest(BaseModel):
    paths: list[str] = Field(default_factory=list)


class VisitRequest(BaseModel):
    path: str


@router.get("", response_model=ShortcutsResponse, summary="常用ページ一覧取得")
async def list_shortcuts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    data = await get_shortcuts(db, current_user)
    return data


@router.put("/pins", response_model=ShortcutsResponse, summary="ピン留め一覧更新")
async def update_pins(
    body: PinsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await replace_pins(db, current_user, body.paths)


@router.post("/visit", summary="ページ訪問記録")
async def post_visit(
    body: VisitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await record_visit(db, current_user, body.path)
    return {"ok": True}
