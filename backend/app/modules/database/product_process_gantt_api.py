"""
製品工程ガント API（ProductProcessGantt ビュー向け）

production_summarys の工程別 *_plan / *_actual / *_trend / *_actual_plan_trend 列と
product_route_steps（製品別工程ルート）を組み合わせ、
「製品 × 工程 × 日」のガント／推移用データを 1 リクエストで返す。

- GET /product-process-gantt
  - days: 計画/実績（または倉庫在庫）ガント用
  - trends: 各工程 *_trend
  - actual_plan_trends: 各工程 *_actual_plan_trend（倉庫系は無し）
"""
import logging
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["product-process-gantt"])

MAX_PERIOD_DAYS = 93
MAX_PAGE_SIZE = 100
MAX_PRODUCT_FILTER = 50

# mode=plan_actual_merge: 当日以前は実績、当日は実績優先・無ければ計画、翌日以降は計画
# mode=plan: 計画のみ（検査＝画面表示「内示」）
# mode=inventory_trend: *_inventory を在庫推移として表示（倉庫 / 外注倉庫）
GANTT_PROCESS_DEFS: list[dict[str, Any]] = [
    {
        "key": "cutting",
        "process_cds": ["KT01"],
        "label": "切断",
        "mode": "plan_actual_merge",
        "plan_col": "cutting_plan",
        "actual_col": "cutting_actual",
        "trend_col": "cutting_trend",
        "apt_col": "cutting_actual_plan_trend",
    },
    {
        "key": "chamfering",
        "process_cds": ["KT02"],
        "label": "面取",
        "mode": "plan_actual_merge",
        "plan_col": "chamfering_plan",
        "actual_col": "chamfering_actual",
        "trend_col": "chamfering_trend",
        "apt_col": "chamfering_actual_plan_trend",
    },
    {
        "key": "molding",
        "process_cds": ["KT04"],
        "label": "成型",
        "mode": "plan_actual_merge",
        "plan_col": "molding_plan",
        "actual_col": "molding_actual",
        "trend_col": "molding_trend",
        "apt_col": "molding_actual_plan_trend",
    },
    {
        "key": "plating",
        "process_cds": ["KT05"],
        "label": "メッキ",
        "mode": "plan_actual_merge",
        "plan_col": "plating_plan",
        "actual_col": "plating_actual",
        "trend_col": "plating_trend",
        "apt_col": "plating_actual_plan_trend",
    },
    {
        "key": "outsourced_plating",
        "process_cds": ["KT06"],
        "label": "外注メッキ",
        "mode": "plan_actual_merge",
        "plan_col": "outsourced_plating_plan",
        "actual_col": "outsourced_plating_actual",
        "trend_col": "outsourced_plating_trend",
        "apt_col": "outsourced_plating_actual_plan_trend",
    },
    {
        "key": "welding",
        "process_cds": ["KT07"],
        "label": "溶接",
        "mode": "plan_actual_merge",
        "plan_col": "welding_plan",
        "actual_col": "welding_actual",
        "trend_col": "welding_trend",
        "apt_col": "welding_actual_plan_trend",
    },
    {
        "key": "outsourced_welding",
        "process_cds": ["KT08"],
        "label": "外注溶接",
        "mode": "plan_actual_merge",
        "plan_col": "outsourced_welding_plan",
        "actual_col": "outsourced_welding_actual",
        "trend_col": "outsourced_welding_trend",
        "apt_col": "outsourced_welding_actual_plan_trend",
    },
    {
        "key": "inspection",
        "process_cds": ["KT09"],
        "label": "内示",
        "mode": "plan",
        "plan_col": "inspection_plan",
        "actual_col": "inspection_actual",
        "trend_col": "inspection_trend",
        "apt_col": "inspection_actual_plan_trend",
    },
    {
        "key": "warehouse",
        "process_cds": ["KT13"],
        "label": "倉庫",
        "mode": "inventory_trend",
        "inventory_col": "warehouse_inventory",
        "trend_col": "warehouse_trend",
    },
    {
        "key": "outsourced_warehouse",
        "process_cds": ["KT10", "KT15"],
        "label": "外注検査/倉庫",
        "mode": "inventory_trend",
        "inventory_col": "outsourced_warehouse_inventory",
        "trend_col": "outsourced_warehouse_trend",
    },
]

PROCESS_CD_TO_KEY: dict[str, str] = {
    cd: d["key"] for d in GANTT_PROCESS_DEFS for cd in d["process_cds"]
}
PLAN_DEFS = [d for d in GANTT_PROCESS_DEFS if d["mode"] in ("plan", "plan_actual_merge")]
INV_DEFS = [d for d in GANTT_PROCESS_DEFS if d["mode"] == "inventory_trend"]
TREND_DEFS = [d for d in GANTT_PROCESS_DEFS if d.get("trend_col")]
APT_DEFS = [d for d in GANTT_PROCESS_DEFS if d.get("apt_col")]

_ANY_PLAN_SQL = " OR ".join(f"COALESCE(`{d['plan_col']}`, 0) > 0" for d in PLAN_DEFS)

_DAY_SELECT_PARTS: list[str] = [
    f"COALESCE(`{d['plan_col']}`, 0) AS `{d['key']}_p`, COALESCE(`{d['actual_col']}`, 0) AS `{d['key']}_a`"
    for d in PLAN_DEFS
]
_DAY_SELECT_PARTS.extend(
    f"COALESCE(`{d['inventory_col']}`, 0) AS `{d['key']}_i`" for d in INV_DEFS
)
_DAY_SELECT_PARTS.extend(f"COALESCE(`{d['trend_col']}`, 0) AS `{d['key']}_tr`" for d in TREND_DEFS)
_DAY_SELECT_PARTS.extend(f"COALESCE(`{d['apt_col']}`, 0) AS `{d['key']}_apt`" for d in APT_DEFS)
_DAY_SELECT_COLS = ", ".join(_DAY_SELECT_PARTS)


def _parse_iso_date(label: str, value: str) -> date:
    s = (value or "").strip()[:10]
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{label} は YYYY-MM-DD 形式で指定してください")


def _parse_product_cds(raw: Optional[str]) -> list[str]:
    """カンマ／セミコロン区切りの製品CDを重複なく返す。"""
    if not raw or not str(raw).strip():
        return []
    seen: list[str] = []
    for part in str(raw).replace(";", ",").split(","):
        cd = part.strip()
        if cd and cd not in seen:
            seen.append(cd)
    if len(seen) > MAX_PRODUCT_FILTER:
        raise HTTPException(
            status_code=422,
            detail=f"製品指定は最大 {MAX_PRODUCT_FILTER} 件までです",
        )
    return seen


async def _list_planned_products(
    db: AsyncSession,
    start_d: date,
    end_d: date,
    keyword: Optional[str],
    page: int,
    page_size: int,
) -> tuple[list[str], int]:
    """期間内にいずれかの工程計画がある製品CDをページングで返す。"""
    where = ["`date` >= :start_date", "`date` <= :end_date", f"({_ANY_PLAN_SQL})"]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d}
    if keyword and keyword.strip():
        where.append("(`product_cd` LIKE :kw OR `product_name` LIKE :kw)")
        params["kw"] = f"%{keyword.strip()}%"
    base = (
        "SELECT `product_cd` FROM production_summarys "
        f"WHERE {' AND '.join(where)} GROUP BY `product_cd`"
    )
    total = (
        await db.execute(text(f"SELECT COUNT(*) FROM ({base}) t"), params)
    ).scalar() or 0
    rows = (
        await db.execute(
            text(f"{base} ORDER BY `product_cd` LIMIT :limit OFFSET :offset"),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        )
    ).all()
    return [r[0] for r in rows], int(total)


async def _load_product_meta(db: AsyncSession, product_cds: list[str]) -> dict[str, dict[str, Any]]:
    """products マスタから製品名・route_cd を取得。"""
    if not product_cds:
        return {}
    q = text(
        "SELECT `product_cd`, `product_name`, `route_cd` FROM products WHERE `product_cd` IN :cds"
    ).bindparams(bindparam("cds", expanding=True))
    rows = (await db.execute(q, {"cds": product_cds})).mappings().all()
    return {
        r["product_cd"]: {
            "product_cd": r["product_cd"],
            "product_name": r["product_name"] or r["product_cd"],
            "route_cd": r["route_cd"] or "",
        }
        for r in rows
    }


async def _load_route_steps(
    db: AsyncSession,
    product_cds: list[str],
    meta: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """製品別工程ルートステップを取得。"""
    if not product_cds:
        return {}

    q = text(
        "SELECT prs.`product_cd`, prs.`route_cd`, prs.`step_no`, prs.`process_cd`, pr.`process_name` "
        "FROM product_route_steps prs "
        "LEFT JOIN processes pr ON pr.`process_cd` = prs.`process_cd` "
        "WHERE prs.`product_cd` IN :cds "
        "ORDER BY prs.`product_cd`, prs.`step_no`"
    ).bindparams(bindparam("cds", expanding=True))
    rows = (await db.execute(q, {"cds": product_cds})).mappings().all()

    by_product: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for r in rows:
        by_product.setdefault(r["product_cd"], {}).setdefault(r["route_cd"], []).append(
            {
                "step_no": int(r["step_no"]),
                "process_cd": r["process_cd"],
                "process_key": PROCESS_CD_TO_KEY.get(r["process_cd"]),
                "process_name": r["process_name"] or r["process_cd"],
            }
        )

    result: dict[str, list[dict[str, Any]]] = {}
    missing_route_cds: set[str] = set()
    for cd in product_cds:
        routes = by_product.get(cd)
        preferred = (meta.get(cd) or {}).get("route_cd") or ""
        if routes:
            steps = routes.get(preferred) or next(iter(routes.values()))
            result[cd] = steps
        elif preferred:
            missing_route_cds.add(preferred)

    if missing_route_cds:
        q2 = text(
            "SELECT rs.`route_cd`, rs.`step_no`, rs.`process_cd`, pr.`process_name` "
            "FROM process_route_steps rs "
            "LEFT JOIN processes pr ON pr.`process_cd` = rs.`process_cd` "
            "WHERE rs.`route_cd` IN :rcds "
            "ORDER BY rs.`route_cd`, rs.`step_no`"
        ).bindparams(bindparam("rcds", expanding=True))
        rows2 = (await db.execute(q2, {"rcds": list(missing_route_cds)})).mappings().all()
        tpl: dict[str, list[dict[str, Any]]] = {}
        for r in rows2:
            tpl.setdefault(r["route_cd"], []).append(
                {
                    "step_no": int(r["step_no"]),
                    "process_cd": r["process_cd"],
                    "process_key": PROCESS_CD_TO_KEY.get(r["process_cd"]),
                    "process_name": r["process_name"] or r["process_cd"],
                }
            )
        for cd in product_cds:
            if cd in result:
                continue
            preferred = (meta.get(cd) or {}).get("route_cd") or ""
            if preferred in tpl:
                result[cd] = tpl[preferred]

    return result


async def _load_daily_payload(
    db: AsyncSession,
    product_cds: list[str],
    start_d: date,
    end_d: date,
) -> dict[str, dict[str, dict[str, list[dict[str, Any]]]]]:
    """
    戻り値:
      days[product][process] = [{d,p,a} | {d,i,t}]
      trends[product][process] = [{d,v}]  （*_trend）
      actual_plan_trends[product][process] = [{d,v}]  （*_actual_plan_trend）
    """
    empty: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {
        "days": {},
        "trends": {},
        "actual_plan_trends": {},
    }
    if not product_cds:
        return empty

    q = text(
        f"SELECT `product_cd`, `date`, {_DAY_SELECT_COLS} "
        "FROM production_summarys "
        "WHERE `product_cd` IN :cds AND `date` >= :start_date AND `date` <= :end_date "
        "ORDER BY `product_cd`, `date`"
    ).bindparams(bindparam("cds", expanding=True))
    rows = (
        await db.execute(q, {"cds": product_cds, "start_date": start_d, "end_date": end_d})
    ).mappings().all()

    days: dict[str, dict[str, list[dict[str, Any]]]] = {}
    trends: dict[str, dict[str, list[dict[str, Any]]]] = {}
    apts: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for r in rows:
        ds = r["date"].isoformat() if r["date"] else None
        if not ds:
            continue
        pcd = r["product_cd"]

        for d in PLAN_DEFS:
            p = int(r[f"{d['key']}_p"] or 0)
            a = int(r[f"{d['key']}_a"] or 0)
            if d["mode"] == "plan":
                if p <= 0:
                    continue
            elif p <= 0 and a <= 0:
                continue
            days.setdefault(pcd, {}).setdefault(d["key"], []).append({"d": ds, "p": p, "a": a})

        for d in INV_DEFS:
            inv = int(r[f"{d['key']}_i"] or 0)
            tr = int(r[f"{d['key']}_tr"] or 0)
            days.setdefault(pcd, {}).setdefault(d["key"], []).append({"d": ds, "i": inv, "t": tr})

        for d in TREND_DEFS:
            v = int(r[f"{d['key']}_tr"] or 0)
            trends.setdefault(pcd, {}).setdefault(d["key"], []).append({"d": ds, "v": v})

        for d in APT_DEFS:
            v = int(r[f"{d['key']}_apt"] or 0)
            apts.setdefault(pcd, {}).setdefault(d["key"], []).append({"d": ds, "v": v})

    return {"days": days, "trends": trends, "actual_plan_trends": apts}


@router.get("/product-process-gantt")
async def get_product_process_gantt(
    start_date: str = Query(..., description="期間開始 YYYY-MM-DD"),
    end_date: str = Query(..., description="期間終了 YYYY-MM-DD"),
    product_cd: Optional[str] = Query(
        None, description="製品CD指定。カンマ区切りで複数可（指定時はページング無視）"
    ),
    keyword: Optional[str] = Query(None, description="製品CD・製品名キーワード"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品×工程×日のガント／推移チャート用データを返す。"""
    start_d = _parse_iso_date("start_date", start_date)
    end_d = _parse_iso_date("end_date", end_date)
    if end_d < start_d:
        raise HTTPException(status_code=422, detail="end_date は start_date 以降を指定してください")
    if (end_d - start_d).days + 1 > MAX_PERIOD_DAYS:
        raise HTTPException(status_code=422, detail=f"期間は最大 {MAX_PERIOD_DAYS} 日までです")

    selected_cds = _parse_product_cds(product_cd)
    if selected_cds:
        page_cds = selected_cds
        total = len(page_cds)
        page = 1
    else:
        page_cds, total = await _list_planned_products(
            db, start_d, end_d, keyword, page, page_size
        )

    meta = await _load_product_meta(db, page_cds)
    steps_map = await _load_route_steps(db, page_cds, meta)
    payload = await _load_daily_payload(db, page_cds, start_d, end_d)

    products_out: list[dict[str, Any]] = []
    for cd in page_cds:
        m = meta.get(cd) or {"product_cd": cd, "product_name": cd, "route_cd": ""}
        products_out.append(
            {
                **m,
                "steps": steps_map.get(cd, []),
                "days": payload["days"].get(cd, {}),
                "trends": payload["trends"].get(cd, {}),
                "actual_plan_trends": payload["actual_plan_trends"].get(cd, {}),
            }
        )

    return {
        "data": {
            "period": {"start": start_d.isoformat(), "end": end_d.isoformat()},
            "page": page,
            "page_size": page_size,
            "total": total,
            "processes": [
                {
                    "key": d["key"],
                    "label": d["label"],
                    "process_cds": d["process_cds"],
                    "mode": d["mode"],
                    "has_trend": bool(d.get("trend_col")),
                    "has_actual_plan_trend": bool(d.get("apt_col")),
                }
                for d in GANTT_PROCESS_DEFS
            ],
            "products": products_out,
        }
    }
