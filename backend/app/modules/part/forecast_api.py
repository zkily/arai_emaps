"""部品月次内示 API

GET  /api/part/forecast                 部品×年の 12 ヶ月
GET  /api/part/forecast/batch           複数部品×指定年月
PUT  /api/part/forecast                 手入力保存
POST /api/part/forecast/from-products   BOM × 月受注内示から算出（apply=true で保存）
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_purchase_operation
from app.modules.master.models import PartMaster
from app.modules.part.models import PartMonthlyForecast

router = APIRouter()


class MonthQty(BaseModel):
    month: int = Field(..., ge=1, le=12)
    forecast_qty: int = Field(0, ge=0, le=99_999_999)


class ForecastSaveBody(BaseModel):
    part_cd: str
    year: int = Field(..., ge=2000, le=2100)
    source: Literal["manual", "from_product"] = "manual"
    months: list[MonthQty]


class ForecastFromProductsBody(BaseModel):
    part_cd: str
    year: int = Field(..., ge=2000, le=2100)
    apply: bool = False


def _operator(user: User) -> Optional[str]:
    name = (user.full_name or user.username or "")[:100]
    return name or None


async def _part_name(db: AsyncSession, part_cd: str) -> str:
    row = (
        await db.execute(select(PartMaster.part_name).where(PartMaster.part_cd == part_cd))
    ).scalar_one_or_none()
    return row or ""


async def _load_saved(db: AsyncSession, part_cd: str, year: int) -> list[dict]:
    rows = (
        (
            await db.execute(
                select(PartMonthlyForecast)
                .where(PartMonthlyForecast.part_cd == part_cd, PartMonthlyForecast.year == year)
                .order_by(PartMonthlyForecast.month)
            )
        )
        .scalars()
        .all()
    )
    by_month = {r.month: r for r in rows}
    out = []
    for m in range(1, 13):
        row = by_month.get(m)
        out.append(
            {
                "month": m,
                "forecast_qty": int(row.forecast_qty or 0) if row else 0,
                "source": row.source if row else None,
            }
        )
    return out


async def _upsert(
    db: AsyncSession,
    part_cd: str,
    year: int,
    months: list[MonthQty],
    source: str,
    operator: Optional[str],
) -> list[dict]:
    existing = (
        (
            await db.execute(
                select(PartMonthlyForecast).where(
                    PartMonthlyForecast.part_cd == part_cd,
                    PartMonthlyForecast.year == year,
                )
            )
        )
        .scalars()
        .all()
    )
    by_month = {r.month: r for r in existing}
    seen: set[int] = set()
    for item in months:
        if item.month in seen:
            continue
        seen.add(item.month)
        row = by_month.get(item.month)
        if row is None:
            row = PartMonthlyForecast(
                part_cd=part_cd,
                year=year,
                month=item.month,
                forecast_qty=item.forecast_qty,
                source=source,
                updated_by=operator,
            )
            db.add(row)
        else:
            row.forecast_qty = item.forecast_qty
            row.source = source
            row.updated_by = operator
    await db.commit()
    return await _load_saved(db, part_cd, year)


_FROM_PRODUCT_SQL = text(
    """
    SELECT
        om.month AS month,
        ROUND(SUM(
            COALESCE(om.forecast_units, 0)
            * COALESCE(l.qty_per, 0)
            / NULLIF(COALESCE(h.base_quantity, 1), 0)
        )) AS forecast_qty,
        COUNT(DISTINCT om.product_cd) AS product_count
    FROM order_monthly om
    INNER JOIN product_bom_headers h
      ON h.id = (
          SELECT h2.id
          FROM product_bom_headers h2
          WHERE h2.parent_product_cd = om.product_cd
            AND h2.status = 'active'
            AND COALESCE(h2.bom_type, 'production') = 'production'
            AND (
              h2.effective_from IS NULL
              OR h2.effective_from <= STR_TO_DATE(
                   CONCAT(om.year, '-', LPAD(om.month, 2, '0'), '-01'), '%Y-%m-%d'
                 )
            )
            AND (
              h2.effective_to IS NULL
              OR h2.effective_to >= STR_TO_DATE(
                   CONCAT(om.year, '-', LPAD(om.month, 2, '0'), '-01'), '%Y-%m-%d'
                 )
            )
          ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
          LIMIT 1
      )
    INNER JOIN product_bom_lines l
      ON l.header_id = h.id
     AND l.component_product_cd IS NOT NULL
     AND TRIM(l.component_product_cd) <> ''
     AND TRIM(l.component_product_cd) = :part_cd
    WHERE om.year = :year
    GROUP BY om.month
    """
)


async def _from_products(db: AsyncSession, part_cd: str, year: int) -> tuple[list[dict], int]:
    rows = (await db.execute(_FROM_PRODUCT_SQL, {"part_cd": part_cd, "year": year})).mappings().all()
    by_month = {int(r["month"]): r for r in rows}
    product_count = max((int(r["product_count"] or 0) for r in rows), default=0)
    months = []
    for m in range(1, 13):
        hit = by_month.get(m)
        qty = int(hit["forecast_qty"] or 0) if hit else 0
        if qty < 0:
            qty = 0
        months.append({"month": m, "forecast_qty": qty, "source": "from_product" if hit else None})
    return months, product_count


@router.get("/batch")
async def get_part_forecast_batch(
    part_cds: str = Query(..., description="部品CDのカンマ区切り"),
    months: str = Query(..., description="YYYY-MM のカンマ区切り"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """複数部品×指定年月の内示数を一括取得。戻り: { part_cd: { 'YYYY-MM': qty } }"""
    cds = sorted({c.strip() for c in part_cds.split(",") if c.strip()})
    ym_list: list[tuple[int, int, str]] = []
    for raw in months.split(","):
        token = raw.strip()
        if not token:
            continue
        parts = token.split("-")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail=f"年月形式が不正です: {token}")
        try:
            y, m = int(parts[0]), int(parts[1])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"年月形式が不正です: {token}") from e
        if y < 2000 or y > 2100 or m < 1 or m > 12:
            raise HTTPException(status_code=400, detail=f"年月が範囲外です: {token}")
        ym_list.append((y, m, f"{y:04d}-{m:02d}"))
    if not cds:
        raise HTTPException(status_code=400, detail="部品を指定してください")
    if not ym_list:
        raise HTTPException(status_code=400, detail="年月を指定してください")
    if len(cds) > 500:
        raise HTTPException(status_code=400, detail="部品は500件以内にしてください")

    years = {y for y, _, _ in ym_list}
    month_nums = {m for _, m, _ in ym_list}
    rows = (
        (
            await db.execute(
                select(PartMonthlyForecast).where(
                    PartMonthlyForecast.part_cd.in_(cds),
                    PartMonthlyForecast.year.in_(years),
                    PartMonthlyForecast.month.in_(month_nums),
                )
            )
        )
        .scalars()
        .all()
    )
    wanted = {(y, m) for y, m, _ in ym_list}
    data: dict[str, dict[str, int]] = {cd: {ym: 0 for _, _, ym in ym_list} for cd in cds}
    for r in rows:
        if (r.year, r.month) not in wanted:
            continue
        key = f"{r.year:04d}-{r.month:02d}"
        data.setdefault(r.part_cd, {})[key] = int(r.forecast_qty or 0)
    return {"success": True, "data": data}


@router.get("")
async def get_part_forecast(
    part_cd: str = Query(...),
    year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    cd = part_cd.strip()
    if not cd:
        raise HTTPException(status_code=400, detail="部品を指定してください")
    months = await _load_saved(db, cd, year)
    return {
        "success": True,
        "data": {
            "part_cd": cd,
            "part_name": await _part_name(db, cd),
            "year": year,
            "months": months,
        },
    }


@router.put("")
async def save_part_forecast(
    body: ForecastSaveBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    cd = body.part_cd.strip()
    if not cd:
        raise HTTPException(status_code=400, detail="部品を指定してください")
    if not body.months:
        raise HTTPException(status_code=400, detail="月次内示がありません")
    months = await _upsert(db, cd, body.year, body.months, body.source, _operator(current_user))
    return {
        "success": True,
        "data": {
            "part_cd": cd,
            "part_name": await _part_name(db, cd),
            "year": body.year,
            "months": months,
        },
    }


@router.post("/from-products")
async def forecast_from_products(
    body: ForecastFromProductsBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    cd = body.part_cd.strip()
    if not cd:
        raise HTTPException(status_code=400, detail="部品を指定してください")
    months, product_count = await _from_products(db, cd, body.year)
    applied = False
    if body.apply:
        from app.modules.auth.operation_deps import assert_operation_permission
        from app.core.operation_modules import OPERATION_MODULE_PURCHASE

        await assert_operation_permission(db, current_user, OPERATION_MODULE_PURCHASE, "edit")
        saved = await _upsert(
            db,
            cd,
            body.year,
            [MonthQty(month=m["month"], forecast_qty=m["forecast_qty"]) for m in months],
            "from_product",
            _operator(current_user),
        )
        months = saved
        applied = True
    return {
        "success": True,
        "data": {
            "part_cd": cd,
            "part_name": await _part_name(db, cd),
            "year": body.year,
            "months": months,
            "product_count": product_count,
            "applied": applied,
        },
    }
