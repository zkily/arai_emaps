"""
部品在庫 API
  part_stock → /api/part/stock
"""
import logging
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct, update, text
from collections import defaultdict
from typing import Optional, Any
from datetime import date, timedelta

from app.core.database import get_db

logger = logging.getLogger(__name__)


def _safe_float(v: Any) -> Optional[float]:
    """Decimal/int/float/None を float に安全変換"""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_date_iso(v: Any) -> Optional[str]:
    """date/datetime を ISO 文字列に。None は None"""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import PartMaster, Supplier
from app.modules.part.models import PartStock
from app.modules.part.schemas import (
    PartStockCreate,
    PartStockUpdate,
    PartStockResponse,
    PartStockCalculateRequest,
)
from app.modules.part.part_planned_usage_from_production import (
    calendar_date_only,
    fetch_part_daily_usage_from_stock_transaction_logs,
    fetch_part_daily_usage_plan_from_welding_actual_plan,
    normalize_part_stock_cd,
)

router = APIRouter()


def _is_missing_part_stock_table_error(exc: BaseException) -> bool:
    """
    MySQL 1146: Table '...part_stock' doesn't exist
    （マイグレーション `224_part_purchase_tables.sql` 未実行時）
    """
    depth = 0
    cur: BaseException | None = exc
    while cur is not None and depth < 10:
        depth += 1
        args = getattr(cur, "args", ())
        if args and args[0] == 1146:
            msg = str(args[1]) if len(args) > 1 else ""
            return "part_stock" in msg
        text = f"{cur!s} {args!r}".lower()
        if "part_stock" in text and ("1146" in text or "doesn't exist" in text):
            return True
        cur = cur.__cause__ or cur.__context__
    return False


# ─────────────────────────────────────────────
# part_stock  メイン在庫
# ─────────────────────────────────────────────

def _stock_to_dict(r: PartStock) -> dict:
    return {
        "id": getattr(r, "id", None),
        "part_cd": getattr(r, "part_cd", None) or "",
        "part_name": getattr(r, "part_name", None) or "",
        "date": _safe_date_iso(getattr(r, "date", None)),
        "initial_stock": getattr(r, "initial_stock", None),
        "current_stock": getattr(r, "current_stock", None),
        "planned_usage": getattr(r, "planned_usage", None),
        "usage_plan_qty": getattr(r, "usage_plan_qty", None),
        "stock_trend": getattr(r, "stock_trend", None),
        "adjustment_quantity": getattr(r, "adjustment_quantity", None),
        "standard_spec": getattr(r, "standard_spec", None) or "",
        "unit": getattr(r, "unit", None),
        "unit_price": _safe_float(getattr(r, "unit_price", None)),
        "pieces_per_bundle": getattr(r, "pieces_per_bundle", None),
        "supplier_cd": getattr(r, "supplier_cd", None),
        "supplier_name": getattr(r, "supplier_name", None),
        "lead_time": getattr(r, "lead_time", None),
        "order_quantity": getattr(r, "order_quantity", None),
        "order_bundle_quantity": getattr(r, "order_bundle_quantity", None),
        "order_amount": _safe_float(getattr(r, "order_amount", None)),
        "remarks": getattr(r, "remarks", None) or "",
        "last_updated": _safe_date_iso(getattr(r, "last_updated", None)),
        "created_at": _safe_date_iso(getattr(r, "created_at", None)),
    }


def _stock_to_dict_with_parts_status(r: PartStock, parts_status: Optional[int] = None) -> dict:
    """一覧用: parts.status を付与（フロントで status=0 を弾くため）"""
    d = _stock_to_dict(r)
    if parts_status is not None:
        d["part_master_status"] = int(parts_status)
    return d


@router.get("")
async def list_part_stocks(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=10000),
    keyword: Optional[str] = Query(None),
    part_cd: Optional[str] = Query(None),
    supplier_cd: Optional[str] = Query(None),
    suppliers: Optional[str] = Query(None, description="仕入先名称のカンマ区切り。指定時は supplier_name で IN 検索"),
    target_date: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="期間開始（YYYY-MM-DD、以上）"),
    end_date: Optional[str] = Query(None, description="期間終了（YYYY-MM-DD、以下）"),
    order_only: bool = Query(False, description="true のとき注文数>0の行のみ（部品注文履歴用）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """部品在庫一覧（parts.status=0 の部品は除外）"""
    try:
        # part_stock と parts の照合用 COLLATE
        join_cond = PartStock.part_cd.collate("utf8mb4_unicode_ci") == PartMaster.part_cd.collate("utf8mb4_unicode_ci")
        q = (
            select(PartStock, PartMaster.status)
            .join(PartMaster, join_cond)
            .where(PartMaster.status != 0)
        )
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            q = q.where(
                or_(
                    PartStock.part_cd.ilike(kw),
                    PartStock.part_name.ilike(kw),
                    PartStock.supplier_name.ilike(kw),
                )
            )
        if part_cd:
            q = q.where(PartStock.part_cd == part_cd)
        if supplier_cd:
            q = q.where(PartStock.supplier_cd == supplier_cd)
        if suppliers and suppliers.strip():
            supplier_list = [s.strip() for s in suppliers.split(",") if s.strip()]
            if supplier_list:
                q = q.where(PartStock.supplier_name.in_(supplier_list))
        has_range = bool(start_date and start_date.strip()) or bool(end_date and end_date.strip())
        if has_range:
            if start_date and start_date.strip():
                try:
                    sd = date.fromisoformat(start_date.strip())
                    q = q.where(PartStock.date >= sd)
                except ValueError as e:
                    logger.warning("list_part_stocks invalid start_date=%s: %s", start_date, e)
                    raise HTTPException(status_code=400, detail=f"無効な開始日: {start_date}") from e
            if end_date and end_date.strip():
                try:
                    ed = date.fromisoformat(end_date.strip())
                    q = q.where(PartStock.date <= ed)
                except ValueError as e:
                    logger.warning("list_part_stocks invalid end_date=%s: %s", end_date, e)
                    raise HTTPException(status_code=400, detail=f"無効な終了日: {end_date}") from e
        elif target_date and target_date.strip():
            try:
                filter_date = date.fromisoformat(target_date.strip())
                q = q.where(PartStock.date == filter_date)
            except ValueError as e:
                logger.warning("list_part_stocks invalid target_date=%s: %s", target_date, e)
                raise HTTPException(status_code=400, detail=f"無効な日付: {target_date}") from e

        if order_only:
            q = q.where(PartStock.order_quantity > 0)

        total_q = select(func.count()).select_from(q.subquery())
        total = (await db.execute(total_q)).scalar() or 0

        if order_only:
            q = q.order_by(PartStock.date.asc(), PartStock.part_cd)
        else:
            q = q.order_by(PartStock.part_cd, PartStock.date.asc())
        q = q.offset((page - 1) * pageSize).limit(pageSize)
        raw_rows = (await db.execute(q)).all()
        list_out = [_stock_to_dict_with_parts_status(row[0], row[1]) for row in raw_rows]

        return {"success": True, "data": {"list": list_out, "total": total}}
    except HTTPException:
        raise
    except Exception as e:
        if _is_missing_part_stock_table_error(e):
            logger.warning(
                "part_stock テーブルがありません。database/migrations/224_part_purchase_tables.sql を実行してください。"
            )
            return {"success": True, "data": {"list": [], "total": 0}}
        logger.exception("list_part_stocks failed: %s", e)
        raise HTTPException(status_code=500, detail=f"部品在庫一覧の取得に失敗しました: {str(e)}") from e


@router.get("/latest")
async def get_latest_part_stocks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """各部品の最新在庫（part_cd ごとに最新日付。parts.status=0 は除外）"""
    try:
        join_cond = PartStock.part_cd.collate("utf8mb4_unicode_ci") == PartMaster.part_cd.collate("utf8mb4_unicode_ci")
        subq = (
            select(PartStock.part_cd, func.max(PartStock.date).label("max_date"))
            .group_by(PartStock.part_cd)
            .subquery()
        )
        q = (
            select(PartStock, PartMaster.status)
            .join(PartMaster, join_cond)
            .where(PartMaster.status != 0)
            .join(
                subq,
                (PartStock.part_cd == subq.c.part_cd) & (PartStock.date == subq.c.max_date),
            )
        )
        raw_rows = (await db.execute(q)).all()
        return {
            "success": True,
            "data": [_stock_to_dict_with_parts_status(row[0], row[1]) for row in raw_rows],
        }
    except Exception as e:
        if _is_missing_part_stock_table_error(e):
            logger.warning(
                "part_stock テーブルがありません。database/migrations/224_part_purchase_tables.sql を実行してください。"
            )
            return {"success": True, "data": []}
        raise


@router.post("/calculate")
async def calculate_part_stock(
    body: PartStockCalculateRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    在庫計算:
      1) initial_stock > 0 の行が 1 件も無い場合は何もしない（従来どおり）。
      2) planned_usage は常に次の区間で集計・反映:
         initial_stock>0 の行のうち最遅の date ～ part_stock の日付最大（画面の日付指定は使わない）。
      3) usage_plan_qty は ComponentRequirements「日別・部品別需要」と同じ算出式で、
         planned_usage>0 の最終日 ～ part_stock の日付最大 の区間で集計・反映する。
      4) 再計算前に上記四列を一括 0 にクリアする日付範囲の開始は、
         part_stock 全体で initial_stock>0 の行のうち date が最も遅い日（ローリング開始日）。
         終了は part_stock の日付最大。
      5) stock_transaction_logs（KT07・実績+不良を日×製品で合算）× BOM（consume_process_cd=KT07 の部品行）→ planned_usage（合算値をそのまま部品×日に反映）
      6) production_summarys.molding_actual_plan × BOM → usage_plan_qty
      7) current_stock は -planned_usage、stock_trend は
         「planned_usage の最終 >0 日までは -planned_usage、翌日以降は -usage_plan_qty」
         で部品ごとに日付順再計算する。
    """
    _ = body  # 互換のため受け取るが日付は使わない（集計は錨点日～最大日で固定）
    q = select(PartStock).order_by(PartStock.part_cd, PartStock.date.asc())
    try:
        rows = (await db.execute(q)).scalars().all()
    except Exception as e:
        if _is_missing_part_stock_table_error(e):
            logger.warning(
                "part_stock テーブルがありません。database/migrations/224_part_purchase_tables.sql を実行してください。"
            )
            return {
                "success": True,
                "data": {
                    "calculated_count": 0,
                    "updated_count": 0,
                    "usage_synced": 0,
                    "usage_plan_synced": 0,
                    "usage_period": None,
                },
            }
        raise
    if not rows:
        return {
            "success": True,
            "data": {
                "calculated_count": 0,
                "updated_count": 0,
                "usage_synced": 0,
                "usage_plan_synced": 0,
                "usage_period": None,
            },
        }

    rows_with_initial = [r for r in rows if (r.initial_stock or 0) > 0]
    if not rows_with_initial:
        return {
            "success": True,
            "data": {
                "calculated_count": 0,
                "updated_count": 0,
                "usage_synced": 0,
                "usage_plan_synced": 0,
                "usage_period": None,
            },
        }

    data_max_date = max(r.date for r in rows)
    global_start_date = max(r.date for r in rows_with_initial)

    # 使用数・使用計画の集計・行への反映は常に「initial 錨点日～表内最大日」（リクエストの日付は無視）
    d_start, d_end = global_start_date, data_max_date

    if d_start > d_end:
        raise HTTPException(status_code=400, detail="同期の開始日は終了日以前である必要があります")

    usage_synced = 0
    usage_plan_synced = 0
    usage_plan_start_date = d_start
    usage_plan_end_date = d_end
    try:
        usage_map = await fetch_part_daily_usage_from_stock_transaction_logs(db, d_start, d_end)
    except Exception as e:
        msg = str(e).lower()
        if "stock_transaction_logs" in msg and (
            "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
        ):
            raise HTTPException(
                status_code=503,
                detail="stock_transaction_logs テーブルが存在しません。",
            ) from e
        if "product_bom_headers" in msg or "product_bom_lines" in msg:
            raise HTTPException(
                status_code=503,
                detail="product_bom_headers / product_bom_lines が存在しないため使用数を同期できません。",
            ) from e
        logger.exception("fetch_part_daily_usage_from_stock_transaction_logs failed: %s", e)
        raise HTTPException(status_code=500, detail=f"使用数の集計に失敗しました: {str(e)}") from e

    usage_plan_map = {}

    # 再計算前に四列を「initial_stock>0 の行のうち最遅の date」～最大日で一括クリア（実テーブル UPDATE + ORM 同期）
    clear_res = await db.execute(
        text(
            """
            UPDATE part_stock
            SET current_stock = 0,
                planned_usage = 0,
                usage_plan_qty = 0,
                stock_trend = 0
            WHERE `date` >= :gstart AND `date` <= :dmax
            """
        ),
        {"gstart": global_start_date, "dmax": data_max_date},
    )
    await db.flush()
    try:
        rc = clear_res.rowcount
    except (AttributeError, NotImplementedError):
        rc = None
    if rc is not None and rc >= 0:
        logger.info(
            "part_stock calculate: cleared %s rows (date %s .. %s, rolling from initial>0 anchor)",
            rc,
            global_start_date,
            data_max_date,
        )

    for r in rows:
        rd0 = calendar_date_only(r.date)
        if rd0 is None or rd0 < global_start_date or rd0 > data_max_date:
            continue
        r.current_stock = 0
        r.planned_usage = 0
        r.usage_plan_qty = 0
        r.stock_trend = 0

    sync_window_row_count = 0
    for r in rows:
        rd = calendar_date_only(r.date)
        if rd is None or rd < d_start or rd > d_end:
            continue
        sync_window_row_count += 1
        key = (normalize_part_stock_cd(r.part_cd), rd)
        new_u = int(usage_map.get(key, 0))
        if int(r.planned_usage or 0) != new_u:
            r.planned_usage = new_u
            usage_synced += 1
    await db.flush()

    # usage_plan_qty の集計期間は「planned_usage が最後に > 0 となる日」～表内最大日
    planned_usage_positive_dates = []
    for r in rows:
        rd = calendar_date_only(r.date)
        if rd is None or rd < global_start_date or rd > data_max_date:
            continue
        if int(r.planned_usage or 0) > 0:
            planned_usage_positive_dates.append(rd)
    if planned_usage_positive_dates:
        usage_plan_start_date = max(planned_usage_positive_dates)
    else:
        usage_plan_start_date = global_start_date
    usage_plan_end_date = data_max_date

    try:
        usage_plan_map = await fetch_part_daily_usage_plan_from_welding_actual_plan(
            db, usage_plan_start_date, usage_plan_end_date
        )
    except Exception as e:
        msg = str(e).lower()
        if "production_summarys" in msg and (
            "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
        ):
            raise HTTPException(
                status_code=503,
                detail="production_summarys テーブルが存在しません。",
            ) from e
        if "product_bom_headers" in msg or "product_bom_lines" in msg:
            raise HTTPException(
                status_code=503,
                detail="product_bom_headers / product_bom_lines が存在しないため使用計画を同期できません。",
            ) from e
        logger.exception("fetch_part_daily_usage_plan_from_welding_actual_plan failed: %s", e)
        raise HTTPException(status_code=500, detail=f"使用計画の集計に失敗しました: {str(e)}") from e

    usage_plan_sync_window_row_count = 0
    for r in rows:
        rd = calendar_date_only(r.date)
        if rd is None or rd < usage_plan_start_date or rd > usage_plan_end_date:
            continue
        usage_plan_sync_window_row_count += 1
        key = (normalize_part_stock_cd(r.part_cd), rd)
        new_p = int(usage_plan_map.get(key, 0))
        if int(r.usage_plan_qty or 0) != new_p:
            r.usage_plan_qty = new_p
            usage_plan_synced += 1
    await db.flush()

    # stock_trend の使用数切替日:
    # planned_usage が最後に >0 となる日の「翌日」から usage_plan_qty を使う
    trend_switch_date: date | None = None
    if planned_usage_positive_dates:
        trend_switch_date = max(planned_usage_positive_dates) + timedelta(days=1)

    usage_lookup_key_count = len(usage_map)
    usage_map_nonzero = sum(1 for v in usage_map.values() if int(v or 0) != 0)
    if usage_lookup_key_count == 0 and sync_window_row_count > 0:
        logger.warning(
            "part_stock calculate: usage_map is empty for window %s..%s (sync_window_rows=%s). "
            "Check stock_transaction_logs (KT07,実績/不良) and BOM lines with consume_process_cd=KT07.",
            d_start,
            d_end,
            sync_window_row_count,
        )

    # part_cd ごとにグループ化
    by_part: dict[str, list[PartStock]] = defaultdict(list)
    for r in rows:
        by_part[r.part_cd].append(r)

    updates_current: dict[int, int] = {}
    updates_trend: dict[int, int] = {}
    calculated_count = 0
    for _part_cd, list_rows in by_part.items():
        to_calc_candidates: list[PartStock] = []
        for r in list_rows:
            rd = calendar_date_only(r.date)
            if rd is not None and rd >= global_start_date:
                to_calc_candidates.append(r)
        to_calc = sorted(to_calc_candidates, key=lambda x: x.date)
        prev_current = 0
        prev_trend = 0
        for r in to_calc:
            init = int(r.initial_stock or 0)
            order_qty = int(r.order_quantity or 0)
            adj = int(r.adjustment_quantity or 0)
            usage = int(r.planned_usage or 0)
            plan_qty = int(r.usage_plan_qty or 0)
            new_current = init + adj + order_qty - usage + prev_current
            trend_usage = usage
            if trend_switch_date is not None:
                rd = calendar_date_only(r.date)
                if rd is not None and rd >= trend_switch_date:
                    trend_usage = plan_qty
            new_trend = init + adj + order_qty - trend_usage + prev_trend
            updates_current[r.id] = new_current
            updates_trend[r.id] = new_trend
            prev_current = new_current
            prev_trend = new_trend
        if to_calc:
            calculated_count += 1

    updated_count = 0
    for row in rows:
        ch = False
        if row.id in updates_current and row.current_stock != updates_current[row.id]:
            row.current_stock = updates_current[row.id]
            ch = True
        if row.id in updates_trend and row.stock_trend != updates_trend[row.id]:
            row.stock_trend = updates_trend[row.id]
            ch = True
        if ch:
            updated_count += 1
    # コミットは get_db の yield 後に任せる（ルート内で commit すると二重コミットでセッションと DB がずれることがある）
    await db.flush()
    return {
        "success": True,
        "data": {
            "calculated_count": calculated_count,
            "updated_count": updated_count,
            "usage_synced": usage_synced,
            "usage_plan_synced": usage_plan_synced,
            "usage_lookup_key_count": usage_lookup_key_count,
            "usage_map_nonzero": usage_map_nonzero,
            "sync_window_row_count": sync_window_row_count,
            "usage_plan_sync_window_row_count": usage_plan_sync_window_row_count,
            "usage_period": {
                # 画面表示用「同期期間」: ローリング・四列クリアの実効範囲（initial>0 の最遅日 ～ 表内最大日）
                "start_date": global_start_date.isoformat(),
                "end_date": data_max_date.isoformat(),
                "calculation_start_date": global_start_date.isoformat(),
                "usage_sync_from_request": False,
                "usage_map_query_start": d_start.isoformat(),
                "usage_map_query_end": d_end.isoformat(),
                "usage_plan_query_start": usage_plan_start_date.isoformat(),
                "usage_plan_query_end": usage_plan_end_date.isoformat(),
            },
        },
    }


@router.get("/summary")
async def get_part_stock_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫サマリー（総部品数・在庫マイナス行数・合計在庫金額）"""
    try:
        total_parts = (await db.execute(select(func.count(distinct(PartStock.part_cd))))).scalar() or 0
        below_zero = (
            await db.execute(select(func.count()).where(PartStock.current_stock < 0))
        ).scalar() or 0
        total_value_result = await db.execute(
            select(func.sum(PartStock.current_stock * PartStock.unit_price))
        )
        total_value = float(total_value_result.scalar() or 0)
    except Exception as e:
        if _is_missing_part_stock_table_error(e):
            logger.warning(
                "part_stock テーブルがありません。database/migrations/224_part_purchase_tables.sql を実行してください。"
            )
            total_parts = below_zero = 0
            total_value = 0.0
        else:
            raise
    return {
        "success": True,
        "data": {
            "total_parts": total_parts,
            "total_materials": total_parts,
            "below_zero": below_zero,
            "below_safety": below_zero,
            "total_value": total_value,
        },
    }


@router.get("/supplier-names")
async def list_distinct_part_stock_supplier_names(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先名一覧：part_stock.supplier_name を重複除去（NULL・空文字除く、名称昇順）"""
    q = (
        select(distinct(PartStock.supplier_name))
        .where(PartStock.supplier_name.isnot(None))
        .where(PartStock.supplier_name != "")
        .order_by(PartStock.supplier_name)
    )
    try:
        result = await db.execute(q)
    except Exception as e:
        if _is_missing_part_stock_table_error(e):
            logger.warning(
                "part_stock テーブルがありません。database/migrations/224_part_purchase_tables.sql を実行してください。"
            )
            return {"success": True, "data": []}
        raise
    raw = [row[0] for row in result.all() if row[0] is not None]
    names = sorted({str(n).strip() for n in raw if str(n).strip()})
    return {"success": True, "data": names}


@router.post("/sync-part-master")
async def sync_part_master_to_stock(
    body: dict | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    部品マスタ同期:
      part_stock.part_cd と parts.part_cd を結合し、
      part_stock の以下の項目を部品マスタから更新する:
        - part_name, unit(uom), standard_spec(category), unit_price
        - supplier_cd, supplier_name（suppliers 参照）
        - pieces_per_bundle=1
    期間指定:
      body.start_date, body.end_date が指定された場合、その期間内 (date BETWEEN start_date AND end_date)
      の part_stock のみを更新対象とする。
      未指定の場合は全期間を更新対象とする。
    """
    try:
        start_date: Optional[date] = None
        end_date: Optional[date] = None
        if body:
            s = body.get("start_date")
            e = body.get("end_date")
            if isinstance(s, str) and s.strip():
                start_date = date.fromisoformat(s.strip()[:10])
            if isinstance(e, str) and e.strip():
                end_date = date.fromisoformat(e.strip()[:10])

        # 有効な部品マスタを取得（status=1）
        mat_stmt = (
            select(
                PartMaster.part_cd,
                PartMaster.part_name,
                PartMaster.category,
                PartMaster.uom,
                PartMaster.unit_price,
                PartMaster.supplier_cd,
            )
            .where(PartMaster.status == 1)
        )
        mat_rows = (await db.execute(mat_stmt)).all()
        if not mat_rows:
            return {
                "success": True,
                "data": {
                    "updated_count": 0,
                },
            }

        # part_cd -> マスタ情報 のマップ
        master_map: dict[str, tuple] = {
            row[0]: row for row in mat_rows
        }

        # supplier_cd -> 仕入先名（part_stock.supplier_name は最大50文字）
        # mat_rows 列順: 0 part_cd, 1 part_name, 2 category, 3 uom, 4 unit_price, 5 supplier_cd
        supplier_cds = {str(row[5]).strip() for row in mat_rows if row[5] is not None and str(row[5]).strip()}
        supplier_name_map: dict[str, str] = {}
        if supplier_cds:
            sup_stmt = select(Supplier.supplier_cd, Supplier.supplier_name).where(
                Supplier.supplier_cd.in_(supplier_cds)
            )
            for scd, sname in (await db.execute(sup_stmt)).all():
                name = (sname or "").strip()
                supplier_name_map[str(scd).strip()] = name[:50] if len(name) > 50 else name

        # 対象となる part_stock 行を取得（parts.status=1 の part_cd のみ、必要なら期間で絞り込み）
        stock_stmt = select(PartStock).where(PartStock.part_cd.in_(master_map.keys()))
        if start_date:
            stock_stmt = stock_stmt.where(PartStock.date >= start_date)
        if end_date:
            stock_stmt = stock_stmt.where(PartStock.date <= end_date)
        stock_rows = (await db.execute(stock_stmt)).scalars().all()

        updated_count = 0
        for stock in stock_rows:
            m = master_map.get(stock.part_cd)
            if not m:
                continue
            _, part_name, category, uom, unit_price, supplier_cd = m

            stock.part_name = part_name or ""
            stock.supplier_cd = supplier_cd
            scd_key = (str(supplier_cd).strip() if supplier_cd is not None else "")
            stock.supplier_name = supplier_name_map.get(scd_key, "") if scd_key else ""
            stock.standard_spec = ((category or "") or "").strip() or ""
            stock.unit = (uom or "").strip() or None
            try:
                stock.unit_price = float(unit_price or 0)
            except (TypeError, ValueError):
                stock.unit_price = 0.0
            stock.pieces_per_bundle = 1

            updated_count += 1

        await db.commit()

        return {
            "success": True,
            "data": {
                "updated_count": updated_count,
            },
        }
    except Exception as e:
        logger.exception("sync_part_master_to_stock failed: %s", e)
        raise HTTPException(status_code=500, detail=f"部品マスタ同期に失敗しました: {str(e)}") from e


@router.post("")
async def create_part_stock(
    body: PartStockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """部品在庫登録"""
    row = PartStock(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _stock_to_dict(row)}


@router.put("/{item_id}")
async def update_part_stock(
    item_id: int,
    body: PartStockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """部品在庫更新"""
    result = await db.execute(select(PartStock).where(PartStock.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _stock_to_dict(row)}


@router.delete("/{item_id}")
async def delete_part_stock(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """部品在庫削除"""
    result = await db.execute(select(PartStock).where(PartStock.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


# 丸一注文書PDF（フロントで画像化したPDF）保存先 — 環境変数 MARUICHI_ORDER_PDF_DIR で上書き可
_MARUICHI_ORDER_PDF_DIR = Path(
    os.environ.get(
        "MARUICHI_ORDER_PDF_DIR",
        r"\\192.168.1.200\99_電子取引データ\4生産管理部\1.丸一注文書",
    )
)
_MARUICHI_ORDER_PDF_NAME_RE = re.compile(r"^\d{8}注文書_丸一鋼管\.pdf$")


def _validate_maruichi_order_pdf_filename(name: str) -> str:
    if not name or not isinstance(name, str):
        raise HTTPException(status_code=400, detail="ファイル名が不正です")
    base = name.strip()
    if "/" in base or "\\" in base or ".." in base:
        raise HTTPException(status_code=400, detail="ファイル名が不正です")
    if not _MARUICHI_ORDER_PDF_NAME_RE.match(base):
        raise HTTPException(
            status_code=400,
            detail="ファイル名は YYYYMMDD注文書_丸一鋼管.pdf 形式である必要があります",
        )
    return base


@router.post("/maruichi-order-pdf")
async def save_maruichi_part_order_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(verify_token_and_get_user),
):
    """丸一注文書PDFを共有フォルダへ保存する。同名ファイルは上書き。"""
    _ = current_user
    safe_name = _validate_maruichi_order_pdf_filename(file.filename or "")
    try:
        _MARUICHI_ORDER_PDF_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.exception("丸一注文書PDF: フォルダ作成・参照に失敗: %s", e)
        raise HTTPException(status_code=500, detail=f"保存フォルダにアクセスできません: {e}") from e
    dest = _MARUICHI_ORDER_PDF_DIR / safe_name
    try:
        content = await file.read()
        if len(content) < 8 or not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="PDFファイルではありません")
        dest.write_bytes(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("丸一注文書PDF保存失敗: %s", e)
        raise HTTPException(status_code=500, detail=f"保存に失敗しました: {e}") from e
    return {"success": True, "message": "保存しました", "path": str(dest)}
