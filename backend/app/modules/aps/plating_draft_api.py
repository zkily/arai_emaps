from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.aps.models import (
    ApsPlatingPlanBoardCard,
    ApsPlatingPlanBoardDateMemo,
    ApsPlatingPlanDraft,
    ApsPlatingPlanDraftItem,
    ApsPlatingPlanDraftLayout,
    ApsPlatingJigAvailability,
)

router = APIRouter()


class PlatingDraftItemBody(BaseModel):
    sort_order: int = 0
    work_date: Optional[date] = None
    product_cd: str
    product_name: str
    plating_machine: str
    kake: float = 0
    qty: int = 0
    slots: int = 0
    source_type: str
    source_row_key: Optional[str] = None


class PlatingBoardCardBody(BaseModel):
    """第④看板 1 枠；draft_version_no 由服务端写入"""

    lap_work_date: date
    lap_start_time: Optional[str] = None
    lap_end_time: Optional[str] = None
    lap_no: int = 0
    turn_seq: int = 0
    product_cd: str = ""
    product_name: str = ""
    plating_machine: str = ""
    kake: float = 0
    qty: int = 0
    slots: int = 0
    board_mark: str = "standard"
    stable_key: Optional[str] = None


class PlatingBoardDateMemoBody(BaseModel):
    """ボード日付行メモ（lap_work_date ごと）"""

    lap_work_date: date
    memo: str = ""


class PlatingDraftLayoutBody(BaseModel):
    """追加レイアウト 1 ブロック（カード未配置でも骨格を永続化）"""

    block_seq: int = 0
    plan_date: date
    start_time: str = "08:00"
    minutes_per_lap: int = 100
    jigs_per_lap: int = 100
    lap_count: int = 1
    base_lap_no: int = 1


class PlatingDraftBody(BaseModel):
    plan_date: date
    daily_minutes: int = 600
    jigs_per_lap: int = 100
    max_laps: int = 1
    minutes_per_lap: int = 100
    board_start_time: Optional[str] = Field(None, description="ボード第1段開始 HH:mm")
    total_slots: int = 0
    used_slots: int = 0
    remain_slots: int = 0
    items: List[PlatingDraftItemBody] = Field(default_factory=list)
    board_cards: Optional[List[PlatingBoardCardBody]] = Field(
        default=None,
        description="None 时不改看板子表；传列表则替换该 draft 下全部看板行（客户端需合并多作業日）",
    )
    layout_blocks: Optional[List[PlatingDraftLayoutBody]] = Field(
        default=None,
        description=(
            "None 时不改 layouts 子表；传列表则替换该 draft 下全部 layouts 行（"
            "未配置でも骨格を保持する）。"
        ),
    )
    board_date_memos: Optional[List[PlatingBoardDateMemoBody]] = Field(
        default=None,
        description="None 时不改日付行メモ；传列表则替换该 draft 下全部メモ（空文字は削除）",
    )


class PlatingDraftItemOut(PlatingDraftItemBody):
    id: int
    draft_id: int

    class Config:
        from_attributes = True


class PlatingBoardCardOut(PlatingBoardCardBody):
    id: int
    draft_id: int
    draft_version_no: int = 1

    class Config:
        from_attributes = True


class PlatingDraftLayoutOut(PlatingDraftLayoutBody):
    id: int
    draft_id: int

    class Config:
        from_attributes = True


class PlatingBoardDateMemoOut(PlatingBoardDateMemoBody):
    id: int
    draft_id: int

    class Config:
        from_attributes = True


class PlatingDraftOut(BaseModel):
    id: int
    plan_date: date
    version_no: int
    status: str
    daily_minutes: int
    jigs_per_lap: int
    max_laps: int
    minutes_per_lap: int
    board_start_time: Optional[str] = None
    total_slots: int
    used_slots: int
    remain_slots: int
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    items: List[PlatingDraftItemOut] = Field(default_factory=list)
    board_cards: List[PlatingBoardCardOut] = Field(default_factory=list)
    layout_blocks: List[PlatingDraftLayoutOut] = Field(default_factory=list)
    board_date_memos: List[PlatingBoardDateMemoOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PlatingJigAvailabilityItem(BaseModel):
    plating_machine: str
    available_qty: int = 0


class PlatingJigAvailabilityBatchBody(BaseModel):
    work_date: date
    items: List[PlatingJigAvailabilityItem] = Field(default_factory=list)


class PlatingJigAvailabilityOut(PlatingJigAvailabilityItem):
    id: int
    work_date: date
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


def _items_filter_for_work_date(work_date_filter: date, plan_d: date):
    """明細 work_date 筛选：当日匹配，或旧数据 work_date IS NULL 且作業日等于 plan_date。"""
    return or_(
        ApsPlatingPlanDraftItem.work_date == work_date_filter,
        and_(ApsPlatingPlanDraftItem.work_date.is_(None), work_date_filter == plan_d),
    )


async def _load_draft_items(
    db: AsyncSession,
    draft_id: int,
    plan_d: date,
    work_date_filter: Optional[date],
) -> List[ApsPlatingPlanDraftItem]:
    q = select(ApsPlatingPlanDraftItem).where(ApsPlatingPlanDraftItem.draft_id == draft_id)
    if work_date_filter is not None:
        q = q.where(_items_filter_for_work_date(work_date_filter, plan_d))
    q = q.order_by(ApsPlatingPlanDraftItem.sort_order.asc(), ApsPlatingPlanDraftItem.id.asc())
    return list((await db.execute(q)).scalars().all())


def _board_card_effective_date_col():
    """表示期間の基準日：lap_work_date のみを使用"""
    return ApsPlatingPlanBoardCard.lap_work_date


async def _load_board_cards(
    db: AsyncSession,
    draft_id: int,
    board_from: Optional[date] = None,
    board_to: Optional[date] = None,
) -> List[ApsPlatingPlanBoardCard]:
    q = select(ApsPlatingPlanBoardCard).where(ApsPlatingPlanBoardCard.draft_id == draft_id)
    eff = _board_card_effective_date_col()
    if board_from is not None and board_to is not None:
        lo, hi = (board_from, board_to) if board_from <= board_to else (board_to, board_from)
        q = q.where(eff >= lo, eff <= hi)
    q = q.order_by(
        ApsPlatingPlanBoardCard.lap_work_date.asc(),
        ApsPlatingPlanBoardCard.lap_no.asc(),
        ApsPlatingPlanBoardCard.turn_seq.asc(),
        ApsPlatingPlanBoardCard.id.asc(),
    )
    return list((await db.execute(q)).scalars().all())


async def _load_board_date_memos(
    db: AsyncSession,
    draft_id: int,
    board_from: Optional[date] = None,
    board_to: Optional[date] = None,
) -> List[ApsPlatingPlanBoardDateMemo]:
    q = select(ApsPlatingPlanBoardDateMemo).where(ApsPlatingPlanBoardDateMemo.draft_id == draft_id)
    if board_from is not None and board_to is not None:
        lo, hi = (board_from, board_to) if board_from <= board_to else (board_to, board_from)
        q = q.where(
            ApsPlatingPlanBoardDateMemo.lap_work_date >= lo,
            ApsPlatingPlanBoardDateMemo.lap_work_date <= hi,
        )
    q = q.order_by(ApsPlatingPlanBoardDateMemo.lap_work_date.asc(), ApsPlatingPlanBoardDateMemo.id.asc())
    return list((await db.execute(q)).scalars().all())


def _board_date_memos_to_out(rows: List[ApsPlatingPlanBoardDateMemo]) -> List[PlatingBoardDateMemoOut]:
    return [
        PlatingBoardDateMemoOut(
            id=int(r.id),
            draft_id=int(r.draft_id),
            lap_work_date=r.lap_work_date,
            memo=r.memo if r.memo is not None else "",
        )
        for r in sorted(rows, key=lambda x: (x.lap_work_date, int(x.id or 0)))
    ]


async def _replace_board_date_memos(
    db: AsyncSession,
    draft_id: int,
    memos: List[PlatingBoardDateMemoBody],
) -> None:
    await db.execute(
        delete(ApsPlatingPlanBoardDateMemo).where(ApsPlatingPlanBoardDateMemo.draft_id == draft_id)
    )
    await db.flush()
    for m in memos:
        db.add(
            ApsPlatingPlanBoardDateMemo(
                draft_id=draft_id,
                lap_work_date=m.lap_work_date,
                memo=(m.memo or "").strip(),
            )
        )
    await db.flush()


def _board_cards_to_out(cards: List[ApsPlatingPlanBoardCard]) -> List[PlatingBoardCardOut]:
    out: List[PlatingBoardCardOut] = []
    for c in sorted(
        cards,
        key=lambda x: (
            x.lap_work_date,
            int(x.lap_no or 0),
            int(x.turn_seq or 0),
            int(x.id or 0),
        ),
    ):
        out.append(
            PlatingBoardCardOut(
                id=int(c.id),
                draft_id=int(c.draft_id),
                draft_version_no=int(c.draft_version_no or 1),
                lap_work_date=c.lap_work_date,
                lap_start_time=(c.lap_start_time or "").strip() or None,
                lap_end_time=(c.lap_end_time or "").strip() or None,
                lap_no=int(c.lap_no or 0),
                turn_seq=int(c.turn_seq or 0),
                product_cd=c.product_cd or "",
                product_name=c.product_name or "",
                plating_machine=c.plating_machine or "",
                kake=float(c.kake or 0),
                qty=int(c.qty or 0),
                slots=int(c.slots or 0),
                board_mark=(c.board_mark or "standard").strip() or "standard",
                stable_key=c.stable_key,
            )
        )
    return out


async def _load_layouts(
    db: AsyncSession,
    draft_id: int,
) -> List[ApsPlatingPlanDraftLayout]:
    q = (
        select(ApsPlatingPlanDraftLayout)
        .where(ApsPlatingPlanDraftLayout.draft_id == draft_id)
        .order_by(
            ApsPlatingPlanDraftLayout.block_seq.asc(),
            ApsPlatingPlanDraftLayout.base_lap_no.asc(),
            ApsPlatingPlanDraftLayout.id.asc(),
        )
    )
    return list((await db.execute(q)).scalars().all())


def _layouts_to_out(layouts: List[ApsPlatingPlanDraftLayout]) -> List[PlatingDraftLayoutOut]:
    out: List[PlatingDraftLayoutOut] = []
    for lb in sorted(
        layouts,
        key=lambda x: (int(x.block_seq or 0), int(x.base_lap_no or 0), int(x.id or 0)),
    ):
        out.append(
            PlatingDraftLayoutOut(
                id=int(lb.id),
                draft_id=int(lb.draft_id),
                block_seq=int(lb.block_seq or 0),
                plan_date=lb.plan_date,
                start_time=(lb.start_time or "08:00").strip() or "08:00",
                minutes_per_lap=int(lb.minutes_per_lap or 0),
                jigs_per_lap=int(lb.jigs_per_lap or 0),
                lap_count=max(1, int(lb.lap_count or 1)),
                base_lap_no=max(1, int(lb.base_lap_no or 1)),
            )
        )
    return out


async def _replace_layouts(
    db: AsyncSession,
    draft_id: int,
    blocks: List[PlatingDraftLayoutBody],
) -> None:
    await db.execute(
        delete(ApsPlatingPlanDraftLayout).where(ApsPlatingPlanDraftLayout.draft_id == draft_id)
    )
    await db.flush()
    for idx, lb in enumerate(blocks):
        db.add(
            ApsPlatingPlanDraftLayout(
                draft_id=draft_id,
                block_seq=int(lb.block_seq if lb.block_seq is not None else idx),
                plan_date=lb.plan_date,
                start_time=(lb.start_time or "08:00").strip() or "08:00",
                minutes_per_lap=max(1, int(lb.minutes_per_lap or 1)),
                jigs_per_lap=max(1, int(lb.jigs_per_lap or 1)),
                lap_count=max(1, int(lb.lap_count or 1)),
                base_lap_no=max(1, int(lb.base_lap_no or 1)),
            )
        )
    await db.flush()


def _to_out(
    row: ApsPlatingPlanDraft,
    board_cards_override: Optional[List[ApsPlatingPlanBoardCard]] = None,
    layouts_override: Optional[List[ApsPlatingPlanDraftLayout]] = None,
    board_date_memos_override: Optional[List[ApsPlatingPlanBoardDateMemo]] = None,
) -> PlatingDraftOut:
    items = sorted(list(row.items or []), key=lambda x: (int(x.sort_order or 0), int(x.id or 0)))
    board_list = list(board_cards_override if board_cards_override is not None else (row.board_cards or []))
    layout_list = list(layouts_override if layouts_override is not None else (row.layouts or []))
    memo_list = list(
        board_date_memos_override
        if board_date_memos_override is not None
        else (row.board_date_memos or [])
    )
    return PlatingDraftOut(
        id=int(row.id),
        plan_date=row.plan_date,
        version_no=int(row.version_no or 1),
        status=row.status or "draft",
        daily_minutes=int(row.daily_minutes or 0),
        jigs_per_lap=int(row.jigs_per_lap or 0),
        max_laps=int(row.max_laps or 1),
        minutes_per_lap=int(row.minutes_per_lap or 0),
        board_start_time=(row.board_start_time or "").strip() or None,
        total_slots=int(row.total_slots or 0),
        used_slots=int(row.used_slots or 0),
        remain_slots=int(row.remain_slots or 0),
        created_by=row.created_by,
        updated_by=row.updated_by,
        items=[
            PlatingDraftItemOut(
                id=int(it.id),
                draft_id=int(it.draft_id),
                sort_order=int(it.sort_order or 0),
                work_date=it.work_date,
                product_cd=it.product_cd or "",
                product_name=it.product_name or "",
                plating_machine=it.plating_machine or "",
                kake=float(it.kake or 0),
                qty=int(it.qty or 0),
                slots=int(it.slots or 0),
                source_type=it.source_type or "",
                source_row_key=it.source_row_key,
            )
            for it in items
        ],
        board_cards=_board_cards_to_out(board_list),
        layout_blocks=_layouts_to_out(layout_list),
        board_date_memos=_board_date_memos_to_out(memo_list),
    )


async def _replace_board_cards(
    db: AsyncSession,
    draft_id: int,
    draft_version_no: int,
    cards: List[PlatingBoardCardBody],
) -> None:
    await db.execute(delete(ApsPlatingPlanBoardCard).where(ApsPlatingPlanBoardCard.draft_id == draft_id))
    await db.flush()
    for bc in cards:
        sk = (bc.stable_key or "").strip() or None
        db.add(
            ApsPlatingPlanBoardCard(
                draft_id=draft_id,
                draft_version_no=int(draft_version_no or 1),
                lap_work_date=bc.lap_work_date,
                lap_start_time=(bc.lap_start_time or "").strip() or None,
                lap_end_time=(bc.lap_end_time or "").strip() or None,
                lap_no=int(bc.lap_no or 0),
                turn_seq=int(bc.turn_seq or 0),
                product_cd=(bc.product_cd or "").strip() or "",
                product_name=(bc.product_name or "").strip() or "",
                plating_machine=(bc.plating_machine or "").strip() or "",
                kake=float(bc.kake or 0),
                qty=int(bc.qty or 0),
                slots=int(bc.slots or 0),
                board_mark=(bc.board_mark or "standard").strip() or "standard",
                stable_key=sk,
            )
        )
    await db.flush()


@router.post("/plating/drafts", response_model=PlatingDraftOut)
async def create_plating_draft(
    body: PlatingDraftBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    max_ver_res = await db.execute(
        select(func.max(ApsPlatingPlanDraft.version_no)).where(ApsPlatingPlanDraft.plan_date == body.plan_date)
    )
    max_ver = max_ver_res.scalar_one_or_none() or 0
    row = ApsPlatingPlanDraft(
        plan_date=body.plan_date,
        version_no=int(max_ver) + 1,
        status="draft",
        daily_minutes=body.daily_minutes,
        jigs_per_lap=body.jigs_per_lap,
        max_laps=max(1, int(body.max_laps or 1)),
        minutes_per_lap=body.minutes_per_lap,
        board_start_time=(body.board_start_time or "").strip() or None,
        total_slots=body.total_slots,
        used_slots=body.used_slots,
        remain_slots=body.remain_slots,
        created_by=(current_user.username or "").strip() or None,
        updated_by=(current_user.username or "").strip() or None,
    )
    db.add(row)
    await db.flush()
    for it in body.items:
        db.add(
            ApsPlatingPlanDraftItem(
                draft_id=row.id,
                sort_order=it.sort_order,
                work_date=it.work_date,
                product_cd=it.product_cd,
                product_name=it.product_name,
                plating_machine=it.plating_machine,
                kake=it.kake,
                qty=it.qty,
                slots=it.slots,
                source_type=it.source_type,
                source_row_key=it.source_row_key,
            )
        )
    await db.flush()
    ver = int(row.version_no or 1)
    if body.board_cards is not None:
        await _replace_board_cards(db, int(row.id), ver, body.board_cards)
    if body.layout_blocks is not None:
        await _replace_layouts(db, int(row.id), body.layout_blocks)
    if body.board_date_memos is not None:
        await _replace_board_date_memos(db, int(row.id), body.board_date_memos)
    q = (
        select(ApsPlatingPlanDraft)
        .options(
            selectinload(ApsPlatingPlanDraft.items),
            selectinload(ApsPlatingPlanDraft.board_cards),
            selectinload(ApsPlatingPlanDraft.layouts),
            selectinload(ApsPlatingPlanDraft.board_date_memos),
        )
        .where(ApsPlatingPlanDraft.id == row.id)
    )
    saved = (await db.execute(q)).scalar_one()
    return _to_out(saved)


@router.put("/plating/drafts/{draft_id}", response_model=PlatingDraftOut)
async def update_plating_draft(
    draft_id: int,
    body: PlatingDraftBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ApsPlatingPlanDraft, draft_id)
    if row is None:
        raise HTTPException(404, "草稿不存在")
    # 草稿ヘッダ plan_date は (plan_date, version_no) UK のため更新しない。ボード日付は lap_work_date のみ。
    plan_d = row.plan_date
    row.daily_minutes = body.daily_minutes
    row.jigs_per_lap = body.jigs_per_lap
    row.max_laps = max(1, int(body.max_laps or 1))
    row.minutes_per_lap = body.minutes_per_lap
    row.board_start_time = (body.board_start_time or "").strip() or None
    row.total_slots = body.total_slots
    row.used_slots = body.used_slots
    row.remain_slots = body.remain_slots
    row.updated_by = (current_user.username or "").strip() or None
    await db.execute(delete(ApsPlatingPlanDraftItem).where(ApsPlatingPlanDraftItem.draft_id == draft_id))
    await db.flush()
    for it in body.items:
        db.add(
            ApsPlatingPlanDraftItem(
                draft_id=draft_id,
                sort_order=it.sort_order,
                work_date=it.work_date,
                product_cd=it.product_cd,
                product_name=it.product_name,
                plating_machine=it.plating_machine,
                kake=it.kake,
                qty=it.qty,
                slots=it.slots,
                source_type=it.source_type,
                source_row_key=it.source_row_key,
            )
        )
    await db.flush()
    ver = int(row.version_no or 1)
    if body.board_cards is not None:
        await _replace_board_cards(db, draft_id, ver, body.board_cards)
    if body.layout_blocks is not None:
        await _replace_layouts(db, draft_id, body.layout_blocks)
    if body.board_date_memos is not None:
        await _replace_board_date_memos(db, draft_id, body.board_date_memos)
    q = (
        select(ApsPlatingPlanDraft)
        .options(
            selectinload(ApsPlatingPlanDraft.items),
            selectinload(ApsPlatingPlanDraft.board_cards),
            selectinload(ApsPlatingPlanDraft.layouts),
            selectinload(ApsPlatingPlanDraft.board_date_memos),
        )
        .where(ApsPlatingPlanDraft.id == draft_id)
    )
    saved = (await db.execute(q)).scalar_one()
    return _to_out(saved)


def _parse_optional_ymd(value: Optional[str], field_name: str) -> Optional[date]:
    if not value or not str(value).strip():
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        raise HTTPException(400, f"{field_name} 格式错误，应为 YYYY-MM-DD")


@router.get("/plating/drafts/latest", response_model=Optional[PlatingDraftOut])
async def get_latest_plating_draft(
    planDate: str = Query(..., description="YYYY-MM-DD"),
    workDate: Optional[str] = Query(None, description="YYYY-MM-DD；指定时仅返回该作業日的明細"),
    boardFrom: Optional[str] = Query(None, description="YYYY-MM-DD；board_cards 表示期間（開始）"),
    boardTo: Optional[str] = Query(None, description="YYYY-MM-DD；board_cards 表示期間（終了）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        d = date.fromisoformat(planDate[:10])
    except ValueError:
        raise HTTPException(400, "planDate 格式错误，应为 YYYY-MM-DD")
    wd_filter = _parse_optional_ymd(workDate, "workDate")
    bf = _parse_optional_ymd(boardFrom, "boardFrom")
    bt = _parse_optional_ymd(boardTo, "boardTo")
    q = (
        select(ApsPlatingPlanDraft)
        .options(noload(ApsPlatingPlanDraft.items))
        .where(ApsPlatingPlanDraft.plan_date == d)
        .order_by(ApsPlatingPlanDraft.version_no.desc(), ApsPlatingPlanDraft.id.desc())
        .limit(1)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if row is None:
        return None
    row.items = await _load_draft_items(db, int(row.id), row.plan_date, wd_filter)
    bc = await _load_board_cards(db, int(row.id), bf, bt)
    lb = await _load_layouts(db, int(row.id))
    bdm = await _load_board_date_memos(db, int(row.id), bf, bt)
    return _to_out(row, board_cards_override=bc, layouts_override=lb, board_date_memos_override=bdm)


@router.get("/plating/drafts/{draft_id}", response_model=PlatingDraftOut)
async def get_plating_draft_by_id(
    draft_id: int,
    workDate: Optional[str] = Query(None, description="YYYY-MM-DD；指定时仅返回该作業日的明細"),
    boardFrom: Optional[str] = Query(None, description="YYYY-MM-DD；board_cards 表示期間（開始）"),
    boardTo: Optional[str] = Query(None, description="YYYY-MM-DD；board_cards 表示期間（終了）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    wd_filter = _parse_optional_ymd(workDate, "workDate")
    bf = _parse_optional_ymd(boardFrom, "boardFrom")
    bt = _parse_optional_ymd(boardTo, "boardTo")
    q = (
        select(ApsPlatingPlanDraft)
        .options(noload(ApsPlatingPlanDraft.items))
        .where(ApsPlatingPlanDraft.id == draft_id)
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "草稿不存在")
    row.items = await _load_draft_items(db, draft_id, row.plan_date, wd_filter)
    bc = await _load_board_cards(db, draft_id, bf, bt)
    lb = await _load_layouts(db, draft_id)
    bdm = await _load_board_date_memos(db, draft_id, bf, bt)
    return _to_out(row, board_cards_override=bc, layouts_override=lb, board_date_memos_override=bdm)


@router.delete("/plating/drafts/{draft_id}")
async def delete_plating_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ApsPlatingPlanDraft, draft_id)
    if row is None:
        raise HTTPException(404, "草稿不存在")
    await db.delete(row)
    await db.flush()
    return {"success": True}


@router.get("/plating/jig-availability", response_model=List[PlatingJigAvailabilityOut])
async def get_plating_jig_availability(
    workDate: str = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        d = date.fromisoformat(workDate[:10])
    except ValueError:
        raise HTTPException(400, "workDate 格式错误，应为 YYYY-MM-DD")
    q = (
        select(ApsPlatingJigAvailability)
        .where(ApsPlatingJigAvailability.work_date == d)
        .order_by(ApsPlatingJigAvailability.plating_machine.asc())
    )
    rows = (await db.execute(q)).scalars().all()
    return [
        PlatingJigAvailabilityOut(
            id=int(r.id),
            work_date=r.work_date,
            plating_machine=r.plating_machine or "",
            available_qty=int(r.available_qty or 0),
            updated_by=r.updated_by,
        )
        for r in rows
    ]


@router.put("/plating/jig-availability")
async def put_plating_jig_availability(
    body: PlatingJigAvailabilityBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await db.execute(delete(ApsPlatingJigAvailability).where(ApsPlatingJigAvailability.work_date == body.work_date))
    await db.flush()
    for it in body.items:
        mc = (it.plating_machine or "").strip()
        if not mc:
            continue
        db.add(
            ApsPlatingJigAvailability(
                work_date=body.work_date,
                plating_machine=mc,
                available_qty=max(0, int(it.available_qty or 0)),
                updated_by=(current_user.username or "").strip() or None,
            )
        )
    await db.flush()
    return {"success": True}
