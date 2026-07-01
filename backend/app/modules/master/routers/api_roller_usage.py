"""
ローラー使用管理 API（roller_usage_status / roller_usage_log）

エンドポイント一覧:
  GET    /roller-usage-status               主表一覧（ページング・フィルタ）
  PUT    /roller-usage-status/{id}          主表手動修正
  POST   /roller-usage/sync-from-master     roller_master → 主表へ差分同期
  POST   /roller-usage/recalculate          次回実施日・交換残数の再計算
  GET    /roller-usage-log                  登録履歴一覧
  POST   /roller-usage-log                  使用ログ新規登録
  DELETE /roller-usage-log/{id}             ログ削除
  GET    /roller-usage-plan                 予定スケジュール一覧
  POST   /roller-usage-plan                 予定1件登録
  POST   /roller-usage-plan/batch-sync      対象月の予定を一括同期
  PUT    /roller-usage-plan/{id}            予定更新
  DELETE /roller-usage-plan/{id}            予定削除
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_quality_operation
from app.modules.auth.models import User
from app.modules.database.models import ProductionSummary
from app.modules.master.models import (
    Machine,
    RollerBom,
    RollerMaster,
    RollerUsageLog,
    RollerUsagePlan,
    RollerUsageStatus,
)

# ---------------------------------------------------------------------------
# Router はモジュール分割のため 2 本定義し、__init__.py で個別 include する
# ---------------------------------------------------------------------------
status_router = APIRouter()   # prefix=/roller-usage-status
log_router    = APIRouter()   # prefix=/roller-usage-log
plan_router   = APIRouter()   # prefix=/roller-usage-plan
action_router = APIRouter()   # prefix=/roller-usage  (sync / recalculate)

# 一覧の並び替え対象（ホワイトリスト）
ROLLER_USAGE_SORT_COLUMNS = {
    "category": RollerMaster.category,
    "roller_type": RollerUsageStatus.roller_type,
    "exchange_freq_month": RollerUsageStatus.exchange_freq_month,
    "cleaning_freq_month": RollerUsageStatus.cleaning_freq_month,
    "next_exec_date": RollerUsageStatus.next_exec_date,
    "exchange_remaining_qty": RollerUsageStatus.exchange_remaining_qty,
}


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _status_to_dict(r: RollerUsageStatus) -> dict:
    return {
        "id": r.id,
        "roller_cd": r.roller_cd,
        "roller_type": r.roller_type,
        "machine_cd": r.machine_cd,
        "machine_name": r.machine_name,
        "exchange_freq_qty": r.exchange_freq_qty,
        "exchange_freq_month": r.exchange_freq_month,
        "cleaning_freq_month": r.cleaning_freq_month,
        "exec_type": r.exec_type,
        "last_exec_date": r.last_exec_date.isoformat() if r.last_exec_date else None,
        "next_exec_date": r.next_exec_date.isoformat() if r.next_exec_date else None,
        "prod_cumulative_qty": r.prod_cumulative_qty,
        "prod_cumulative_qty_prev_month_end": r.prod_cumulative_qty_prev_month_end,
        "prod_manual_addon_qty": r.prod_manual_addon_qty,
        "planned_product_cd": r.planned_product_cd,
        "exchange_remaining_qty": r.exchange_remaining_qty,
        "source_roller_master_updated_at": (
            r.source_roller_master_updated_at.isoformat()
            if r.source_roller_master_updated_at else None
        ),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _log_to_dict(r: RollerUsageLog) -> dict:
    return {
        "id": r.id,
        "roller_cd": r.roller_cd,
        "exec_type": r.exec_type,
        "exec_date": r.exec_date.isoformat() if r.exec_date else None,
        "management_cd": r.management_cd,
        "note": r.note,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _to_opt_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        s = str(v).strip()
        return int(float(s)) if s else None
    except (TypeError, ValueError):
        return None


def _skip_prod_cumulative_for_exchange_freq(exchange_freq_qty: Optional[int]) -> bool:
    """交換頻度本数が未設定または 0 のときは生産数累計（BOM×実績サマリー集計）を行わない"""
    if exchange_freq_qty is None:
        return True
    return exchange_freq_qty == 0


def _current_month_end(d: Optional[date] = None) -> date:
    """基準日が属する暦月の末日（累計集計の終了日に使用）"""
    base = d or date.today()
    first_next = base.replace(day=1) + relativedelta(months=1)
    return first_next - timedelta(days=1)


def _previous_month_end(d: Optional[date] = None) -> date:
    """基準日の直前の暦月の末日（前月末までの累計集計の終了日）"""
    base = d or date.today()
    first_this = base.replace(day=1)
    return first_this - timedelta(days=1)


def _parse_date(v: Any) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _plan_month_from_date(d: date) -> str:
    return d.strftime("%Y-%m")


def _is_manual_schedule_mode(mode: Optional[str]) -> bool:
    return str(mode or "auto").strip().lower() == "manual"


async def _load_manual_roller_cd_set(db: AsyncSession) -> set[str]:
    rows = (
        await db.execute(
            select(RollerMaster.roller_cd).where(RollerMaster.schedule_mode == "manual")
        )
    ).all()
    return {str(r[0]).strip() for r in rows if r[0]}


async def _sync_status_next_from_plans(
    db: AsyncSession,
    status_row: RollerUsageStatus,
) -> None:
    """manual ローラー: 未実施の最も近い予定日を next_exec_date に反映"""
    roller_cd = (status_row.roller_cd or "").strip()
    if not roller_cd:
        return
    today = date.today()
    plans = (
        await db.execute(
            select(RollerUsagePlan)
            .where(RollerUsagePlan.roller_cd == roller_cd)
            .where(RollerUsagePlan.status == "planned")
            .where(RollerUsagePlan.planned_exec_date >= today)
            .order_by(
                RollerUsagePlan.planned_exec_date.asc(),
                RollerUsagePlan.sort_order.asc(),
                RollerUsagePlan.id.asc(),
            )
        )
    ).scalars().all()
    if not plans:
        status_row.next_exec_date = None
        return
    nearest = plans[0]
    status_row.next_exec_date = nearest.planned_exec_date
    if nearest.planned_product_cd:
        status_row.planned_product_cd = nearest.planned_product_cd
    if nearest.exec_type:
        status_row.exec_type = nearest.exec_type


async def _mark_plan_done_for_log(
    db: AsyncSession,
    roller_cd: str,
    exec_date: date,
) -> int:
    """実施登録日と一致する予定を done にする"""
    plans = (
        await db.execute(
            select(RollerUsagePlan)
            .where(RollerUsagePlan.roller_cd == roller_cd)
            .where(RollerUsagePlan.planned_exec_date == exec_date)
            .where(RollerUsagePlan.status == "planned")
        )
    ).scalars().all()
    for p in plans:
        p.status = "done"
    return len(plans)


def _plan_to_dict(r: RollerUsagePlan) -> dict:
    return {
        "id": r.id,
        "roller_cd": r.roller_cd,
        "plan_month": r.plan_month,
        "planned_exec_date": r.planned_exec_date.isoformat() if r.planned_exec_date else None,
        "planned_product_cd": r.planned_product_cd,
        "exec_type": r.exec_type,
        "status": r.status,
        "sort_order": r.sort_order,
        "note": r.note,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


# ---------------------------------------------------------------------------
# 予測計算ロジック（ハイブリッド: 数量ルール + 月ルール → 早い方）
# ---------------------------------------------------------------------------


def _calc_next_exec_date(
    last_exec_date: Optional[date],
    exchange_freq_month: Optional[int],
    cleaning_freq_month: Optional[int],
    exchange_freq_qty: Optional[int],
    prod_cumulative_qty: Optional[int],
    exec_type: Optional[str],
) -> Optional[date]:
    """次回実施日を計算する（数量ルールと月ルールの早い方）"""
    candidates: List[date] = []

    # --- 月ルール ---
    if last_exec_date:
        months = None
        # 要件:
        # - 交換頻度本数（exchange_freq_qty）が 0 の場合は、次回日付の基準を「交換月」を優先する
        # - 交換月が未設定（または 0）なら「清掃月」にフォールバックする
        if exchange_freq_qty == 0:
            months = exchange_freq_month or None
            if not months:
                months = cleaning_freq_month or None
        else:
            t = (exec_type or "").strip()
            if "清掃" in t and cleaning_freq_month:
                months = cleaning_freq_month
            elif exchange_freq_month:
                months = exchange_freq_month
        if months:
            candidates.append(last_exec_date + relativedelta(months=months))

    # --- 数量ルール（簡易: 累計が頻度本数を超えた時点を起点として次周期を想定）---
    # 厳密な将来日付予測には計画データが必要。ここでは本数超過を警告するだけで
    # 日付は月ルールに委ねる。交換残数は別途算出する。

    return min(candidates) if candidates else None


def _calc_exchange_remaining(
    exchange_freq_qty: Optional[int],
    prod_cumulative_qty: Optional[int],
    prod_manual_addon_qty: Optional[int] = None,
) -> Optional[int]:
    if exchange_freq_qty is None:
        return None
    cum = (prod_cumulative_qty or 0) + (prod_manual_addon_qty or 0)
    return exchange_freq_qty - cum


def _planned_product_label_trunc(product_name: Optional[str], product_cd: Optional[str], max_len: int = 50) -> str:
    """予定段取品列は VARCHAR 長さ制限があるため短縮。製品名優先。"""
    name = (product_name or "").strip()
    cd = (product_cd or "").strip()
    raw = name if name else cd
    if not raw:
        return ""
    return raw[:max_len]


def _apply_prediction(row: RollerUsageStatus) -> None:
    """row のフィールドを元に next_exec_date / exchange_remaining_qty を更新"""
    row.next_exec_date = _calc_next_exec_date(
        row.last_exec_date,
        row.exchange_freq_month,
        row.cleaning_freq_month,
        row.exchange_freq_qty,
        row.prod_cumulative_qty,
        row.exec_type,
    )
    row.exchange_remaining_qty = _calc_exchange_remaining(
        row.exchange_freq_qty,
        row.prod_cumulative_qty,
        row.prod_manual_addon_qty,
    )


# ---------------------------------------------------------------------------
# roller_usage_status — 一覧 / 手動修正
# ---------------------------------------------------------------------------


@status_router.get("")
async def list_roller_usage_status(
    keyword: Optional[str] = Query(None),
    machine_cd: Optional[str] = Query(None),
    exec_type: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, alias="sortBy"),
    sort_order: Optional[str] = Query(None, alias="sortOrder"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=5000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ローラー使用状況一覧（ページング・フィルタ）"""
    clauses = []
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        clauses.append(or_(
            RollerUsageStatus.roller_cd.like(k),
            RollerUsageStatus.roller_type.like(k),
            RollerUsageStatus.machine_cd.like(k),
            RollerUsageStatus.machine_name.like(k),
        ))
    if machine_cd and machine_cd.strip():
        clauses.append(RollerUsageStatus.machine_cd == machine_cd.strip())
    if exec_type and exec_type.strip():
        clauses.append(RollerUsageStatus.exec_type == exec_type.strip())

    where = and_(*clauses) if clauses else None

    from sqlalchemy import func as sqlfunc
    count_q = select(sqlfunc.count()).select_from(RollerUsageStatus)
    if where is not None:
        count_q = count_q.where(where)
    total = (await db.execute(count_q)).scalar() or 0

    list_q = select(RollerUsageStatus)
    if where is not None:
        list_q = list_q.where(where)

    sort_col = ROLLER_USAGE_SORT_COLUMNS.get((sort_by or "").strip())
    order_norm = (sort_order or "").strip().lower()
    if sort_col is not None and order_norm in ("asc", "desc"):
        if (sort_by or "").strip() == "category":
            list_q = list_q.outerjoin(
                RollerMaster,
                RollerMaster.roller_cd == RollerUsageStatus.roller_cd,
            )
        primary = sort_col.desc() if order_norm == "desc" else sort_col.asc()
        list_q = list_q.order_by(primary, RollerUsageStatus.machine_cd, RollerUsageStatus.roller_cd)
    else:
        list_q = list_q.order_by(RollerUsageStatus.machine_cd, RollerUsageStatus.roller_cd)

    list_q = list_q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(list_q)).scalars().all()

    return {
        "success": True,
        "data": {"list": [_status_to_dict(r) for r in rows], "total": total},
        "list": [_status_to_dict(r) for r in rows],
        "total": total,
    }


@status_router.put("/{item_id:int}")
async def update_roller_usage_status(
    item_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """ローラー使用状況の手動修正"""
    row = (await db.execute(
        select(RollerUsageStatus).where(RollerUsageStatus.id == item_id)
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラー使用状況が見つかりません")

    updatable = [
        "exec_type", "last_exec_date", "prod_cumulative_qty",
        "prod_manual_addon_qty",
        "planned_product_cd",
        "exchange_freq_qty", "exchange_freq_month", "cleaning_freq_month",
        "machine_cd", "machine_name", "roller_type",
    ]
    for field in updatable:
        if field not in body:
            continue
        v = body[field]
        if field in ("last_exec_date",):
            setattr(row, field, _parse_date(v))
        elif field in ("prod_cumulative_qty", "prod_manual_addon_qty", "exchange_freq_qty",
                       "exchange_freq_month", "cleaning_freq_month"):
            setattr(row, field, _to_opt_int(v))
        else:
            setattr(row, field, str(v).strip() if v is not None and str(v).strip() else None)

    manual_cds = await _load_manual_roller_cd_set(db)
    if (row.roller_cd or "") in manual_cds:
        await _sync_status_next_from_plans(db, row)
    else:
        _apply_prediction(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _status_to_dict(row)}


# ---------------------------------------------------------------------------
# roller_usage_log — 一覧 / 新規 / 削除
# ---------------------------------------------------------------------------


@log_router.get("")
async def list_roller_usage_log(
    roller_cd: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=5000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ローラー使用ログ一覧"""
    from sqlalchemy import func as sqlfunc

    clauses = []
    if roller_cd and roller_cd.strip():
        clauses.append(RollerUsageLog.roller_cd == roller_cd.strip())
    where = and_(*clauses) if clauses else None

    count_q = select(sqlfunc.count()).select_from(RollerUsageLog)
    if where is not None:
        count_q = count_q.where(where)
    total = (await db.execute(count_q)).scalar() or 0

    list_q = (
        select(RollerUsageLog)
        .order_by(RollerUsageLog.exec_date.desc(), RollerUsageLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if where is not None:
        list_q = list_q.where(where)
    rows = (await db.execute(list_q)).scalars().all()

    return {
        "success": True,
        "data": {"list": [_log_to_dict(r) for r in rows], "total": total},
        "list": [_log_to_dict(r) for r in rows],
        "total": total,
    }


@log_router.post("")
async def create_roller_usage_log(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    """使用ログ新規登録（主表の last_exec_date / exec_type も更新）"""
    roller_cd = (body.get("roller_cd") or "").strip()
    if not roller_cd:
        raise HTTPException(status_code=400, detail="roller_cd は必須です")
    exec_type = (body.get("exec_type") or "").strip()
    if not exec_type:
        raise HTTPException(status_code=400, detail="exec_type は必須です")
    exec_date = _parse_date(body.get("exec_date"))
    if not exec_date:
        raise HTTPException(status_code=400, detail="exec_date は必須です（YYYY-MM-DD）")

    log_row = RollerUsageLog(
        roller_cd=roller_cd,
        exec_type=exec_type,
        exec_date=exec_date,
        management_cd=(body.get("management_cd") or None),
        note=body.get("note"),
        created_by=str(getattr(current_user, "username", "") or ""),
    )
    db.add(log_row)

    # 主表を更新（last_exec_date, exec_type を最新ログで上書き）
    status_row = (await db.execute(
        select(RollerUsageStatus).where(RollerUsageStatus.roller_cd == roller_cd)
    )).scalar_one_or_none()
    if status_row is not None:
        # 最新の実施日のみ上書き（過去日付が来ても上書きしない）
        if status_row.last_exec_date is None or exec_date >= status_row.last_exec_date:
            status_row.last_exec_date = exec_date
            status_row.exec_type = exec_type
        await _mark_plan_done_for_log(db, roller_cd, exec_date)
        manual_cds = await _load_manual_roller_cd_set(db)
        if roller_cd in manual_cds:
            await _sync_status_next_from_plans(db, status_row)
        else:
            _apply_prediction(status_row)

    await db.commit()
    await db.refresh(log_row)
    return {"success": True, "data": _log_to_dict(log_row)}


@log_router.delete("/{log_id:int}")
async def delete_roller_usage_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("delete")),
):
    """使用ログ削除"""
    row = (await db.execute(
        select(RollerUsageLog).where(RollerUsageLog.id == log_id)
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ログが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


# ---------------------------------------------------------------------------
# roller_usage_plan — 予定スケジュール（manual ローラー用）
# ---------------------------------------------------------------------------


@plan_router.get("")
async def list_roller_usage_plan(
    roller_cd: Optional[str] = Query(None),
    plan_month: Optional[str] = Query(None, alias="planMonth"),
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="fromDate"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=5000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """予定スケジュール一覧"""
    from sqlalchemy import func as sqlfunc

    clauses = []
    if roller_cd and roller_cd.strip():
        clauses.append(RollerUsagePlan.roller_cd == roller_cd.strip())
    if plan_month and plan_month.strip():
        clauses.append(RollerUsagePlan.plan_month == plan_month.strip()[:7])
    if status and status.strip():
        clauses.append(RollerUsagePlan.status == status.strip())
    if from_date and from_date.strip():
        d = _parse_date(from_date)
        if d:
            clauses.append(RollerUsagePlan.planned_exec_date >= d)
    where = and_(*clauses) if clauses else None

    count_q = select(sqlfunc.count()).select_from(RollerUsagePlan)
    if where is not None:
        count_q = count_q.where(where)
    total = (await db.execute(count_q)).scalar() or 0

    list_q = (
        select(RollerUsagePlan)
        .order_by(
            RollerUsagePlan.planned_exec_date.asc(),
            RollerUsagePlan.sort_order.asc(),
            RollerUsagePlan.id.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if where is not None:
        list_q = list_q.where(where)
    rows = (await db.execute(list_q)).scalars().all()

    return {
        "success": True,
        "data": {"list": [_plan_to_dict(r) for r in rows], "total": total},
        "list": [_plan_to_dict(r) for r in rows],
        "total": total,
    }


@plan_router.post("")
async def create_roller_usage_plan(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    """予定1件登録"""
    roller_cd = (body.get("roller_cd") or "").strip()
    if not roller_cd:
        raise HTTPException(status_code=400, detail="roller_cd は必須です")
    planned_exec_date = _parse_date(body.get("planned_exec_date"))
    if not planned_exec_date:
        raise HTTPException(status_code=400, detail="planned_exec_date は必須です（YYYY-MM-DD）")

    master = (
        await db.execute(select(RollerMaster).where(RollerMaster.roller_cd == roller_cd))
    ).scalar_one_or_none()
    if master is None:
        raise HTTPException(status_code=404, detail="ローラーマスタが見つかりません")
    if not _is_manual_schedule_mode(master.schedule_mode):
        raise HTTPException(status_code=400, detail="このローラーは手動予定モードではありません")

    plan_month = (body.get("plan_month") or "").strip() or _plan_month_from_date(planned_exec_date)
    exec_type = (body.get("exec_type") or "ローラー交換").strip() or "ローラー交換"
    sort_order = _to_opt_int(body.get("sort_order")) or 0

    row = RollerUsagePlan(
        roller_cd=roller_cd,
        plan_month=plan_month[:7],
        planned_exec_date=planned_exec_date,
        planned_product_cd=(body.get("planned_product_cd") or None)
        and str(body.get("planned_product_cd")).strip()
        or None,
        exec_type=exec_type,
        status="planned",
        sort_order=sort_order,
        note=body.get("note"),
        created_by=str(getattr(current_user, "username", "") or ""),
    )
    db.add(row)

    status_row = (
        await db.execute(select(RollerUsageStatus).where(RollerUsageStatus.roller_cd == roller_cd))
    ).scalar_one_or_none()
    if status_row is not None:
        await _sync_status_next_from_plans(db, status_row)

    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _plan_to_dict(row)}


@plan_router.post("/batch-sync")
async def batch_sync_roller_usage_plan(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """対象月の予定を一括同期（既存 planned を置換）"""
    roller_cd = (body.get("roller_cd") or "").strip()
    plan_month = (body.get("plan_month") or "").strip()
    if not roller_cd:
        raise HTTPException(status_code=400, detail="roller_cd は必須です")
    if not plan_month or len(plan_month) < 7:
        raise HTTPException(status_code=400, detail="plan_month は YYYY-MM 形式で指定してください")

    master = (
        await db.execute(select(RollerMaster).where(RollerMaster.roller_cd == roller_cd))
    ).scalar_one_or_none()
    if master is None:
        raise HTTPException(status_code=404, detail="ローラーマスタが見つかりません")
    if not _is_manual_schedule_mode(master.schedule_mode):
        raise HTTPException(status_code=400, detail="このローラーは手動予定モードではありません")

    items = body.get("items") or []
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items は配列で指定してください")

    month_key = plan_month[:7]
    existing = (
        await db.execute(
            select(RollerUsagePlan)
            .where(RollerUsagePlan.roller_cd == roller_cd)
            .where(RollerUsagePlan.plan_month == month_key)
            .where(RollerUsagePlan.status == "planned")
        )
    ).scalars().all()
    for old in existing:
        await db.delete(old)

    created = 0
    username = str(getattr(current_user, "username", "") or "")
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        planned_exec_date = _parse_date(item.get("planned_exec_date"))
        if not planned_exec_date:
            continue
        if _plan_month_from_date(planned_exec_date) != month_key:
            raise HTTPException(
                status_code=400,
                detail=f"予定日 {planned_exec_date.isoformat()} は対象月 {month_key} と一致しません",
            )
        exec_type = (item.get("exec_type") or "ローラー交換").strip() or "ローラー交換"
        sort_order = _to_opt_int(item.get("sort_order"))
        if sort_order is None:
            sort_order = idx
        db.add(
            RollerUsagePlan(
                roller_cd=roller_cd,
                plan_month=month_key,
                planned_exec_date=planned_exec_date,
                planned_product_cd=(item.get("planned_product_cd") or None)
                and str(item.get("planned_product_cd")).strip()
                or None,
                exec_type=exec_type,
                status="planned",
                sort_order=sort_order,
                note=item.get("note"),
                created_by=username,
            )
        )
        created += 1

    status_row = (
        await db.execute(select(RollerUsageStatus).where(RollerUsageStatus.roller_cd == roller_cd))
    ).scalar_one_or_none()
    if status_row is not None:
        await _sync_status_next_from_plans(db, status_row)

    await db.commit()
    return {
        "success": True,
        "created": created,
        "message": f"{month_key} の予定を {created} 件登録しました",
    }


@plan_router.put("/{item_id:int}")
async def update_roller_usage_plan(
    item_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """予定更新"""
    row = (
        await db.execute(select(RollerUsagePlan).where(RollerUsagePlan.id == item_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="予定が見つかりません")

    if "planned_exec_date" in body:
        d = _parse_date(body.get("planned_exec_date"))
        if not d:
            raise HTTPException(status_code=400, detail="planned_exec_date が不正です")
        row.planned_exec_date = d
        row.plan_month = _plan_month_from_date(d)
    if "planned_product_cd" in body:
        v = body.get("planned_product_cd")
        row.planned_product_cd = str(v).strip() if v is not None and str(v).strip() else None
    if "exec_type" in body:
        row.exec_type = (body.get("exec_type") or "ローラー交換").strip() or "ローラー交換"
    if "status" in body:
        st = (body.get("status") or "").strip()
        if st in ("planned", "done", "cancelled"):
            row.status = st
    if "sort_order" in body:
        row.sort_order = _to_opt_int(body.get("sort_order")) or 0
    if "note" in body:
        row.note = body.get("note")

    status_row = (
        await db.execute(
            select(RollerUsageStatus).where(RollerUsageStatus.roller_cd == row.roller_cd)
        )
    ).scalar_one_or_none()
    if status_row is not None:
        await _sync_status_next_from_plans(db, status_row)

    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _plan_to_dict(row)}


@plan_router.delete("/{item_id:int}")
async def delete_roller_usage_plan(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("delete")),
):
    """予定削除"""
    row = (
        await db.execute(select(RollerUsagePlan).where(RollerUsagePlan.id == item_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="予定が見つかりません")
    roller_cd = row.roller_cd
    await db.delete(row)

    status_row = (
        await db.execute(select(RollerUsageStatus).where(RollerUsageStatus.roller_cd == roller_cd))
    ).scalar_one_or_none()
    if status_row is not None:
        await _sync_status_next_from_plans(db, status_row)

    await db.commit()
    return {"success": True, "message": "削除しました"}


# ---------------------------------------------------------------------------
# アクション: 同期 / 再計算
# ---------------------------------------------------------------------------


@action_router.post("/sync-from-master")
async def sync_from_roller_master(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """roller_master から roller_usage_status へ差分同期
    - 新しい roller_cd は INSERT
    - 既存行はマスタフィールド（roller_type/machine_cd/頻度）のみ UPDATE
    - last_exec_date など手動管理フィールドは上書きしない
    """
    masters = (await db.execute(select(RollerMaster))).scalars().all()

    # 設備名マップ
    machine_rows = (await db.execute(select(Machine))).scalars().all()
    machine_name_map: Dict[str, str] = {m.machine_cd: m.machine_name for m in machine_rows}

    existing_map: Dict[str, RollerUsageStatus] = {
        r.roller_cd: r
        for r in (await db.execute(select(RollerUsageStatus))).scalars().all()
    }
    manual_cds = await _load_manual_roller_cd_set(db)

    inserted = 0
    updated = 0
    for m in masters:
        mname = machine_name_map.get(m.machine_cd or "", None)
        if m.roller_cd not in existing_map:
            new_row = RollerUsageStatus(
                roller_cd=m.roller_cd,
                roller_type=m.roller_name,
                machine_cd=m.machine_cd,
                machine_name=mname,
                exchange_freq_qty=m.exchange_freq_qty,
                exchange_freq_month=m.exchange_freq_month,
                cleaning_freq_month=m.cleaning_freq_month,
                source_roller_master_updated_at=m.updated_at,
            )
            if m.roller_cd in manual_cds:
                await _sync_status_next_from_plans(db, new_row)
            else:
                _apply_prediction(new_row)
            db.add(new_row)
            inserted += 1
        else:
            row = existing_map[m.roller_cd]
            row.roller_type = m.roller_name
            row.machine_cd = m.machine_cd
            row.machine_name = mname
            row.exchange_freq_qty = m.exchange_freq_qty
            row.exchange_freq_month = m.exchange_freq_month
            row.cleaning_freq_month = m.cleaning_freq_month
            row.source_roller_master_updated_at = m.updated_at
            if m.roller_cd in manual_cds:
                await _sync_status_next_from_plans(db, row)
            else:
                _apply_prediction(row)
            updated += 1

    await db.commit()
    return {
        "success": True,
        "inserted": inserted,
        "updated": updated,
        "message": f"同期完了: {inserted} 件追加 / {updated} 件更新",
    }


@action_router.post("/recalculate")
async def recalculate_predictions(
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """次回実施日・交換残数の全件（または指定 roller_cd）再計算"""
    roller_cds: Optional[List[str]] = body.get("roller_cds")  # type: ignore[assignment]

    q = select(RollerUsageStatus)
    if roller_cds:
        q = q.where(RollerUsageStatus.roller_cd.in_(roller_cds))
    rows = (await db.execute(q)).scalars().all()
    manual_cds = await _load_manual_roller_cd_set(db)

    # 先にログ表から roller_cd ごとの最新実施日を取得して主表へ反映
    target_cds = [r.roller_cd for r in rows if (r.roller_cd or "").strip()]
    latest_log_map: Dict[str, RollerUsageLog] = {}
    if target_cds:
        log_q = (
            select(RollerUsageLog)
            .where(RollerUsageLog.roller_cd.in_(target_cds))
            .order_by(
                RollerUsageLog.roller_cd.asc(),
                RollerUsageLog.exec_date.desc(),
                RollerUsageLog.id.desc(),
            )
        )
        log_rows = (await db.execute(log_q)).scalars().all()
        for log in log_rows:
            if log.roller_cd not in latest_log_map:
                latest_log_map[log.roller_cd] = log

    # roller_cd -> BOM製品CD一覧
    bom_product_map: Dict[str, List[str]] = {}
    if target_cds:
        bom_q = (
            select(RollerBom.roller_cd, RollerBom.product_cd)
            .where(RollerBom.roller_cd.in_(target_cds))
        )
        bom_rows = (await db.execute(bom_q)).all()
        for roller_cd, product_cd in bom_rows:
            rcd = (roller_cd or "").strip()
            pcd = (product_cd or "").strip()
            if not rcd or not pcd:
                continue
            if rcd not in bom_product_map:
                bom_product_map[rcd] = []
            if pcd not in bom_product_map[rcd]:
                bom_product_map[rcd].append(pcd)

    period_end = _current_month_end()
    prev_month_end = _previous_month_end()

    async def _sum_molding_actual_plan(
        product_cds: List[str], start_date: date, end_date: date, machine_cd: Optional[str]
    ) -> int:
        sum_q = (
            select(func.coalesce(func.sum(ProductionSummary.molding_actual_plan), 0))
            .where(ProductionSummary.product_cd.in_(product_cds))
            .where(ProductionSummary.date >= start_date)
            .where(ProductionSummary.date <= end_date)
        )
        machine_cd_norm = (machine_cd or "").strip()
        if machine_cd_norm:
            sum_q = sum_q.where(ProductionSummary.molding_machine == machine_cd_norm)
        val = (await db.execute(sum_q)).scalar()
        return int(val or 0)

    async def _daily_molding_plan_rows(
        product_cds: List[str], start_date: date, end_date: date, machine_cd: Optional[str]
    ) -> List[Tuple[date, int, Optional[str], Optional[str]]]:
        """日別の成型計画（molding_actual_plan）を返す。

        戻り値: [(date, day_total_qty, representative_product_name, representative_product_cd), ...]
        representative は当日 qty が最大の製品（同値時は取得順）。
        """
        if not product_cds:
            return []
        q = (
            select(
                ProductionSummary.date,
                ProductionSummary.product_name,
                ProductionSummary.product_cd,
                ProductionSummary.molding_actual_plan,
            )
            .where(ProductionSummary.product_cd.in_(product_cds))
            .where(ProductionSummary.date >= start_date)
            .where(ProductionSummary.date <= end_date)
            .where(ProductionSummary.molding_actual_plan > 0)
            .order_by(ProductionSummary.date.asc(), ProductionSummary.molding_actual_plan.desc())
        )
        machine_cd_norm = (machine_cd or "").strip()
        if machine_cd_norm:
            q = q.where(ProductionSummary.molding_machine == machine_cd_norm)
        rows = (await db.execute(q)).all()
        if not rows:
            return []

        grouped: Dict[date, Dict[str, Any]] = {}
        for d, pname, pcd, qty in rows:
            if not isinstance(d, date):
                continue
            day_qty = int(qty or 0)
            if d not in grouped:
                grouped[d] = {
                    "sum_qty": day_qty,
                    "rep_name": str(pname) if pname is not None else None,
                    "rep_cd": str(pcd) if pcd is not None else None,
                }
            else:
                grouped[d]["sum_qty"] += day_qty

        return [
            (
                d,
                int(v["sum_qty"]),
                v["rep_name"],
                v["rep_cd"],
            )
            for d, v in sorted(grouped.items(), key=lambda x: x[0])
        ]

    async def _pick_latest_molding_plan_row(
        product_cds: List[str], start_date: date, end_date: date, machine_cd: Optional[str]
    ) -> tuple[Optional[str], Optional[date]]:
        """交換残数マイナス時：BOM 製品のうち、期間内で molding_actual_plan が残っている最終日の行を採用"""
        if not product_cds:
            return None, None
        pick_q = (
            select(
                ProductionSummary.product_name,
                ProductionSummary.product_cd,
                ProductionSummary.date,
            )
            .where(ProductionSummary.product_cd.in_(product_cds))
            .where(ProductionSummary.date >= start_date)
            .where(ProductionSummary.date <= end_date)
            .where(ProductionSummary.molding_actual_plan > 0)
            .order_by(
                ProductionSummary.date.desc(),
                ProductionSummary.molding_actual_plan.desc(),
            )
            .limit(1)
        )
        machine_cd_norm = (machine_cd or "").strip()
        if machine_cd_norm:
            pick_q = pick_q.where(ProductionSummary.molding_machine == machine_cd_norm)
        one = (await db.execute(pick_q)).first()
        if not one:
            return None, None
        pname, pcd, od = one[0], one[1], one[2]
        label = _planned_product_label_trunc(
            str(pname) if pname is not None else None,
            str(pcd) if pcd is not None else None,
        )
        if not label:
            return None, od if isinstance(od, date) else None
        return label, od if isinstance(od, date) else None

    synced_from_log = 0
    updated_prod_cumulative_qty = 0
    updated_prod_cumulative_qty_prev_month = 0
    updated_planned_when_negative_remaining = 0
    reached_exchange_threshold_count = 0
    for row in rows:
        is_manual = (row.roller_cd or "") in manual_cds
        # 再計算前に生産数累計をクリアし、旧データの残留を除去する
        row.prod_cumulative_qty = 0
        row.prod_cumulative_qty_prev_month_end = 0

        latest_log = latest_log_map.get(row.roller_cd or "")
        if latest_log is not None:
            if row.last_exec_date != latest_log.exec_date or row.exec_type != latest_log.exec_type:
                synced_from_log += 1
            row.last_exec_date = latest_log.exec_date
            row.exec_type = latest_log.exec_type

        # 予測再計算時、BOM対象製品の molding_actual_plan を
        # last_exec_date ～ 当月月末まで合計し、主表の生産累計数へ反映
        # （交換頻度本数が空または 0 のローラーは 0 のまま／集計しない）
        product_cds = bom_product_map.get((row.roller_cd or "").strip(), [])
        sum_qty = 0
        sum_qty_prev = 0
        if not is_manual and not _skip_prod_cumulative_for_exchange_freq(row.exchange_freq_qty):
            if row.last_exec_date and product_cds:
                sum_qty = await _sum_molding_actual_plan(
                    product_cds, row.last_exec_date, period_end, row.machine_name
                )
                sum_qty_prev = await _sum_molding_actual_plan(
                    product_cds, row.last_exec_date, prev_month_end, row.machine_name
                )
                # 要件:
                # - 生産数累計 < 交換本数: 生産数累計をそのまま表示
                # - 生産数累計 >= 交換本数: （交換本数 - 生産数累計）を表示（0以下）
                if row.exchange_freq_qty is not None and sum_qty >= row.exchange_freq_qty:
                    row.prod_cumulative_qty = row.exchange_freq_qty - sum_qty
                else:
                    row.prod_cumulative_qty = sum_qty
                updated_prod_cumulative_qty += 1
                if row.exchange_freq_qty is not None and sum_qty_prev >= row.exchange_freq_qty:
                    row.prod_cumulative_qty_prev_month_end = row.exchange_freq_qty - sum_qty_prev
                else:
                    row.prod_cumulative_qty_prev_month_end = sum_qty_prev
                updated_prod_cumulative_qty_prev_month += 1
        if is_manual:
            await _sync_status_next_from_plans(db, row)
        else:
            _apply_prediction(row)

        # 生産数累計を日別に段階加算し、交換本数に到達した日を実施日へ設定。
        # 予定段取品はその到達日に対応する production_summarys の製品名を設定。
        if (
            not is_manual
            and not _skip_prod_cumulative_for_exchange_freq(row.exchange_freq_qty)
            and row.last_exec_date
            and product_cds
            and row.exchange_freq_qty is not None
            and row.exchange_freq_qty > 0
        ):
            daily_rows = await _daily_molding_plan_rows(
                product_cds, row.last_exec_date, period_end, row.machine_name
            )
            running = 0
            reached_date: Optional[date] = None
            reached_label: Optional[str] = None
            for d, day_qty, rep_name, rep_cd in daily_rows:
                running += day_qty
                if running >= row.exchange_freq_qty:
                    reached_date = d
                    reached_label = _planned_product_label_trunc(rep_name, rep_cd)
                    break

            if reached_date is not None:
                row.next_exec_date = reached_date
                if reached_label:
                    row.planned_product_cd = reached_label
                reached_exchange_threshold_count += 1
                updated_planned_when_negative_remaining += 1

        # 交換残数表示も要件に合わせる:
        # - 生産数累計 < 交換本数: 生産数累計（正数）
        # - 生産数累計 >= 交換本数: 交換本数 - 生産数累計（0以下）
        if not is_manual and row.exchange_freq_qty is not None and row.exchange_freq_qty > 0:
            if sum_qty >= row.exchange_freq_qty:
                row.exchange_remaining_qty = row.exchange_freq_qty - sum_qty
            else:
                row.exchange_remaining_qty = sum_qty

    await db.commit()
    return {
        "success": True,
        "recalculated": len(rows),
        "synced_from_log": synced_from_log,
        "updated_prod_cumulative_qty": updated_prod_cumulative_qty,
        "updated_prod_cumulative_qty_prev_month": updated_prod_cumulative_qty_prev_month,
        "updated_planned_when_negative_remaining": updated_planned_when_negative_remaining,
        "reached_exchange_threshold_count": reached_exchange_threshold_count,
        "prod_cumulative_period_end": period_end.isoformat(),
        "prod_cumulative_prev_month_end": prev_month_end.isoformat(),
        "message": (
            f"{len(rows)} 件の予測を更新しました"
            f"（ログ同期 {synced_from_log} 件 / 累計再計算 {updated_prod_cumulative_qty} 件"
            f"・前月末累計 {updated_prod_cumulative_qty_prev_month} 件"
            f"・超過時予定更新 {updated_planned_when_negative_remaining} 件"
            f"・交換到達日更新 {reached_exchange_threshold_count} 件"
            f"・累計締め {period_end.isoformat()}／前月末 {prev_month_end.isoformat()}）"
        ),
    }
