"""
材料使用済 API
  /api/material/usage/preview  → 使用数プレビュー（書き込みなし）
  /api/material/usage/commit   → 使用数反映（3ステップ処理）
  /api/material/usage/reflected → 指定日の反映済状態確認
  /api/material/usage/records  → 過去の使用済レコード一覧

【commit 3ステップ仕様】
  Step 1: cutting_management（指定日）の各行を material_usage_record に1行1件で書き込み
          - usage_date = production_day, usage_count = 1, source = 'cutting_management'
          - management_code で重複排除（INSERT IGNORE）
          - material_cd は material_name → materials テーブルで解決
          - 完了後 cutting_management.material_usage_reflected = '反映済' に更新
  Step 2: material_usage_record（reflected=0）を (usage_date, material_cd) で集計
          → material_stock.planned_usage を更新
  Step 3: Step 2 対象レコードの reflected = 1 に更新
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import date as date_type

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.schemas import (
    MaterialUsagePreviewItem,
    MaterialUsageCommitRequest,
)

router = APIRouter()

SOURCE_CUTTING = "cutting_management"


# ─────────────────────────────────────────────
# ヘルパー：日付パース
# ─────────────────────────────────────────────

def _parse_date(day_str: Optional[str]) -> Optional[date_type]:
    """YYYY-MM-DD 文字列を date に変換。不正な場合は None を返す。"""
    if not day_str or not isinstance(day_str, str):
        return None
    s = day_str.strip()
    if len(s) >= 10:
        s = s[:10]
    try:
        parts = s.split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return date_type(y, m, d)
    except (ValueError, IndexError):
        pass
    try:
        return date_type.fromisoformat(s)
    except ValueError:
        return None


# ─────────────────────────────────────────────
# ヘルパー：cutting_management 行取得
# ─────────────────────────────────────────────

def _row_val(row: dict, *keys: str):
    """行からキーで値を取得（複数キー可）。"""
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return None


def _compute_management_code(row: dict, fallback_date: Optional[date_type] = None) -> str:
    """
    DBトリガー（migration 071）と同じロジックで management_code を計算する。
    管理コード = 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位2桁 + - + 生産ロット数2桁 + - + ロットNo2桁
    NULLの管理コードを持つ行（トリガー適用前に挿入されたレコード）に対して使用する。
    """
    prod_month = _row_val(row, "production_month")
    if prod_month is None:
        prod_month = fallback_date or date_type.today()
    if isinstance(prod_month, str):
        try:
            prod_month = date_type.fromisoformat(str(prod_month)[:10])
        except (ValueError, TypeError):
            prod_month = date_type.today()
    if not hasattr(prod_month, 'year'):
        prod_month = date_type.today()

    year_2 = str(prod_month.year)[-2:]
    month_2 = str(prod_month.month).zfill(2)
    product_cd = str(_row_val(row, "product_cd") or "")
    production_line = str(_row_val(row, "production_line") or "")
    # RIGHT(production_line, 2) — 末尾2文字
    line_2 = production_line[-2:] if len(production_line) >= 2 else production_line.ljust(0, " ")
    priority = int(_row_val(row, "priority_order") or 0)
    lot_size = int(_row_val(row, "production_lot_size") or 0)
    lot_no = str(_row_val(row, "lot_number") or "")

    return (
        f"{year_2}{month_2}{product_cd}{line_2}"
        f"{str(priority).zfill(2)}-{str(lot_size).zfill(2)}-{lot_no.zfill(2)}"
    )


async def _fetch_cutting_rows(db: AsyncSession, day_str: Optional[str]) -> list:
    """
    指定日の cutting_management 行を全件取得。
    - management_code が NULL の行はトリガーと同じ計算式で自動補完する
    - 管理コードのフィルタはしない（トリガー適用前のデータも処理対象とする）
    """
    if not day_str:
        return []
    d = _parse_date(day_str)
    if d is None:
        return []
    # management_code フィルタを外し、全列を取得（Python 側で補完するため）
    # JOIN 時に collation が混在する場合があるため、明示的に utf8mb4_unicode_ci で比較
    sql = text("""
        SELECT
            cm.id,
            cm.production_day,
            cm.production_month,
            cm.management_code,
            cm.product_cd,
            cm.production_line,
            cm.priority_order,
            cm.production_lot_size,
            cm.lot_number,
            cm.material_name,
            p.material_cd
        FROM cutting_management cm
        LEFT JOIN products p
          ON cm.product_cd COLLATE utf8mb4_unicode_ci = p.product_cd COLLATE utf8mb4_unicode_ci
        WHERE cm.production_day = :production_day
    """)
    try:
        result = await db.execute(sql, {"production_day": d})
        rows = [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        raise RuntimeError(f"cutting_management 取得エラー: {e}") from e

    resolved = []
    for row in rows:
        mgmt = str(_row_val(row, "management_code") or "").strip()
        if not mgmt:
            # トリガーと同じ計算式で management_code を補完
            mgmt = _compute_management_code(row, fallback_date=d)
            row["management_code"] = mgmt
            row["_mgmt_computed"] = True  # 計算で補完したフラグ
        resolved.append(row)

    return resolved


# ─────────────────────────────────────────────
# ヘルパー：material_cd 解決
# ─────────────────────────────────────────────

async def _resolve_material_by_product_cd(
    db: AsyncSession, product_cd: str
) -> Optional[tuple[str, str]]:
    sql = text("""
        SELECT m.material_cd, m.material_name
        FROM products p
        JOIN materials m ON p.material_cd COLLATE utf8mb4_unicode_ci = m.material_cd COLLATE utf8mb4_unicode_ci
        WHERE p.product_cd = :product_cd
        LIMIT 1
    """)
    try:
        result = await db.execute(sql, {"product_cd": product_cd})
        row = result.fetchone()
        if row:
            return (row[0] or "", row[1] or "")
    except Exception:
        pass
    return None


async def _resolve_material_cd_by_name(db: AsyncSession, material_name: str) -> Optional[str]:
    sql = text("""
        SELECT material_cd FROM materials WHERE material_name = :name LIMIT 1
    """)
    try:
        result = await db.execute(sql, {"name": material_name})
        row = result.fetchone()
        if row:
            return row[0]
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
# ヘルパー：既存レコード確認
# ─────────────────────────────────────────────

async def _check_existing_records(
    db: AsyncSession, usage_date: str, source: str
) -> set[str]:
    """指定日・ソースで既に material_usage_record に記録がある material_cd セットを返す"""
    try:
        d = date_type.fromisoformat(usage_date)
    except ValueError:
        return set()
    sql = text("""
        SELECT material_cd FROM material_usage_record
        WHERE usage_date = :d AND source = :source
    """)
    try:
        result = await db.execute(sql, {"d": d, "source": source})
        return {row[0] for row in result.fetchall()}
    except Exception:
        return set()


# ─────────────────────────────────────────────
# ヘルパー：集計（プレビュー用）
# ─────────────────────────────────────────────

async def _aggregate_usage(
    db: AsyncSession,
    today_str: str,
    tomorrow_str: Optional[str],
) -> List[dict]:
    """今日・翌日の cutting_management から材料別使用数を集計（プレビュー用）。"""
    today_rows = await _fetch_cutting_rows(db, today_str)
    tomorrow_rows = await _fetch_cutting_rows(db, tomorrow_str) if tomorrow_str else []

    today_mgmt_codes: set = {r["management_code"] for r in today_rows if r["management_code"]}
    tomorrow_rows_filtered = [
        r for r in tomorrow_rows
        if r["management_code"] and r["management_code"] not in today_mgmt_codes
    ]

    async def resolve_material_cd(rows: list) -> list:
        result = []
        for r in rows:
            mat_cd = r.get("material_cd") or ""
            mat_name = r.get("material_name") or ""
            if not mat_cd and r.get("product_cd"):
                resolved = await _resolve_material_by_product_cd(db, r["product_cd"])
                if resolved:
                    mat_cd, mat_name_from_db = resolved
                    mat_name = mat_name_from_db or mat_name
            if not mat_cd and mat_name:
                resolved2 = await _resolve_material_cd_by_name(db, mat_name)
                if resolved2:
                    mat_cd = resolved2
            r["_resolved_material_cd"] = mat_cd
            r["_resolved_material_name"] = mat_name
            result.append(r)
        return result

    today_rows = await resolve_material_cd(today_rows)
    tomorrow_rows_filtered = await resolve_material_cd(tomorrow_rows_filtered)

    today_map: dict[tuple, set] = {}
    for r in today_rows:
        mat_cd = r["_resolved_material_cd"]
        mat_name = r["_resolved_material_name"]
        mgmt = r.get("management_code")
        if not mgmt:
            continue
        key = (mat_cd or "__unknown__", mat_name or mat_cd or "不明")
        today_map.setdefault(key, set()).add(mgmt)

    tomorrow_map: dict[tuple, set] = {}
    for r in tomorrow_rows_filtered:
        mat_cd = r["_resolved_material_cd"]
        mat_name = r["_resolved_material_name"]
        mgmt = r.get("management_code")
        if not mgmt:
            continue
        key = (mat_cd or "__unknown__", mat_name or mat_cd or "不明")
        tomorrow_map.setdefault(key, set()).add(mgmt)

    results: list[dict] = []
    for (mat_cd, mat_name), codes in today_map.items():
        results.append({
            "usage_date": today_str,
            "material_cd": mat_cd,
            "material_name": mat_name,
            "usage_count": len(codes),
            "management_codes": ",".join(sorted(codes)) if codes else None,
        })
    for (mat_cd, mat_name), codes in tomorrow_map.items():
        results.append({
            "usage_date": tomorrow_str,
            "material_cd": mat_cd,
            "material_name": mat_name,
            "usage_count": len(codes),
            "management_codes": ",".join(sorted(codes)) if codes else None,
        })

    return results


# ─────────────────────────────────────────────
# GET /preview  使用数プレビュー（書き込みなし）
# ─────────────────────────────────────────────

@router.get("/preview")
async def preview_material_usage(
    today_date: str = Query(..., description="今日の生産日 YYYY-MM-DD"),
    tomorrow_date: Optional[str] = Query(None, description="翌日の生産日 YYYY-MM-DD"),
    source: str = Query("cutting_management", description="来源区分"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """使用数プレビュー API（書き込みなし）。今日・翌日の切断指示から材料別使用数を集計して返す。"""
    try:
        aggregated = await _aggregate_usage(db, today_date, tomorrow_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"集計に失敗しました: {e}") from e

    dates_to_check = {item["usage_date"] for item in aggregated}
    existing_by_date: dict[str, set[str]] = {}
    for d in dates_to_check:
        existing_by_date[d] = await _check_existing_records(db, d, source)

    preview_items = []
    for item in aggregated:
        already = item["material_cd"] in existing_by_date.get(item["usage_date"], set())
        preview_items.append(MaterialUsagePreviewItem(
            usage_date=date_type.fromisoformat(item["usage_date"]),
            material_cd=item["material_cd"],
            material_name=item["material_name"],
            usage_count=item["usage_count"],
            already_recorded=already,
        ))

    has_existing = any(p.already_recorded for p in preview_items)
    data_list = [p.model_dump() for p in preview_items]

    msg = None
    if has_existing and data_list:
        msg = "既存の反映記録があります。確認後に上書き保存されます。"
    elif not data_list:
        msg = (
            "指定日の切断指示に材料データがありません。"
            "生産日を確認するか、管理コードが入力された切断指示を登録してください。"
        )

    payload = {
        "success": True,
        "data": data_list,
        "has_existing_records": has_existing,
        "message": msg,
    }
    if not data_list:
        payload["received_dates"] = {"today_date": today_date, "tomorrow_date": tomorrow_date}
    return payload


# ─────────────────────────────────────────────
# POST /commit  使用数反映（3ステップ）
# ─────────────────────────────────────────────

@router.post("/commit")
async def commit_material_usage(
    body: MaterialUsageCommitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    使用数反映 API（3ステップ処理）。

    Step 1: cutting_management（指定日）の各行を material_usage_record に1行1件で書き込み。
            - management_code で重複排除（INSERT IGNORE）
            - material_cd は material_name → materials テーブルで解決
            - 完了後 cutting_management.material_usage_reflected = '反映済'

    Step 2: material_usage_record（reflected=0）を (usage_date, material_cd) で集計
            → material_stock.planned_usage を更新

    Step 3: Step 2 で対象とした material_usage_record.reflected = 1 に更新
    """
    today_d = _parse_date(body.today_date)
    if today_d is None:
        raise HTTPException(status_code=400, detail=f"today_date が不正です: {body.today_date}")

    source = body.source  # 'cutting_management'

    # ──────── Step 1: cutting_management → material_usage_record ────────
    try:
        rows = await _fetch_cutting_rows(db, body.today_date)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        return {
            "success": True,
            "message": (
                f"指定日（{body.today_date}）に切断指示がありません。"
                "日付を確認するか、切断指示を登録してください。"
            ),
            "inserted": 0,
            "stock_updated": 0,
        }

    inserted = 0
    try:
        for row in rows:
            mgmt_code = str(_row_val(row, "management_code") or "").strip()
            if not mgmt_code:
                continue

            mat_name = str(_row_val(row, "material_name") or "").strip()
            production_day = _row_val(row, "production_day") or today_d

            # material_cd を material_name から解決（products 経由でも試みる）
            mat_cd = str(_row_val(row, "material_cd") or "").strip()
            if not mat_cd and mat_name:
                mat_cd = await _resolve_material_cd_by_name(db, mat_name) or ""
            if not mat_cd and _row_val(row, "product_cd"):
                resolved = await _resolve_material_by_product_cd(db, str(_row_val(row, "product_cd")))
                if resolved:
                    mat_cd = resolved[0] or ""
                    if not mat_name:
                        mat_name = resolved[1] or ""

            if not mat_cd:
                mat_cd = "__unknown__"

            # INSERT IGNORE: management_code + source が一致する行は重複挿入しない
            insert_sql = text("""
                INSERT IGNORE INTO material_usage_record
                    (usage_date, material_cd, material_name, usage_count,
                     source, management_codes, management_code, reflected)
                VALUES
                    (:usage_date, :material_cd, :material_name, 1,
                     :source, :management_code, :management_code, 0)
            """)
            result = await db.execute(insert_sql, {
                "usage_date": production_day,
                "material_cd": mat_cd,
                "material_name": mat_name or "不明",
                "source": source,
                "management_code": mgmt_code,
            })
            inserted += result.rowcount

        # cutting_management を「反映済」に更新
        update_cm_sql = text("""
            UPDATE cutting_management
            SET material_usage_reflected = '反映済'
            WHERE production_day = :prod_day
        """)
        await db.execute(update_cm_sql, {"prod_day": today_d})

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Step 1 書き込みに失敗しました: {e}") from e

    # ──────── Step 2: material_usage_record 集計 → material_stock 更新 ────────
    agg_sql = text("""
        SELECT usage_date, material_cd, SUM(usage_count) AS total_count
        FROM material_usage_record
        WHERE usage_date = :usage_date
          AND source = :source
          AND reflected = 0
        GROUP BY usage_date, material_cd
    """)
    try:
        agg_result = await db.execute(agg_sql, {"usage_date": today_d, "source": source})
        agg_rows = agg_result.fetchall()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Step 2 集計に失敗しました: {e}") from e

    stock_updated = 0
    for agg_row in agg_rows:
        agg_date = agg_row[0]
        agg_mat_cd = agg_row[1]
        agg_count = int(agg_row[2] or 0)

        if not agg_mat_cd or agg_mat_cd == "__unknown__":
            continue

        try:
            update_stock_sql = text("""
                UPDATE material_stock
                SET planned_usage = :usage_count,
                    last_updated  = CURRENT_TIMESTAMP
                WHERE material_cd = :material_cd
                  AND date = :usage_date
            """)
            result = await db.execute(update_stock_sql, {
                "usage_count": agg_count,
                "material_cd": agg_mat_cd,
                "usage_date": agg_date,
            })
            stock_updated += result.rowcount
        except Exception:
            pass

    # ──────── Step 3: material_usage_record.reflected = 1 に更新 ────────
    try:
        mark_sql = text("""
            UPDATE material_usage_record
            SET reflected = 1
            WHERE usage_date = :usage_date
              AND source = :source
              AND reflected = 0
        """)
        await db.execute(mark_sql, {"usage_date": today_d, "source": source})
    except Exception:
        pass

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"コミットに失敗しました: {e}") from e

    return {
        "success": True,
        "message": (
            f"使用数を反映しました（{inserted} 件挿入、"
            f"material_stock {stock_updated} 件更新）"
        ),
        "inserted": inserted,
        "stock_updated": stock_updated,
    }


# ─────────────────────────────────────────────
# GET /debug  診断エンドポイント（開発・調査用）
# ─────────────────────────────────────────────

@router.get("/debug")
async def debug_cutting_rows(
    date: str = Query(..., description="対象日 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定日の cutting_management 生データを返す診断用エンドポイント。
    management_code が NULL の行には _mgmt_computed フラグが付く。
    """
    d = _parse_date(date)
    if d is None:
        return {"success": False, "message": f"日付の形式が不正です: {date}"}

    # 生データ確認用（全件、フィルタなし）
    raw_sql = text("""
        SELECT id, production_day, management_code, product_cd,
               production_line, priority_order, production_lot_size, lot_number,
               material_name, production_month
        FROM cutting_management
        WHERE production_day = :production_day
        LIMIT 50
    """)
    try:
        result = await db.execute(raw_sql, {"production_day": d})
        raw_rows = [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        return {"success": False, "message": f"クエリエラー: {e}"}

    null_count = sum(1 for r in raw_rows if not str(r.get("management_code") or "").strip())
    has_count = len(raw_rows) - null_count

    # Python 計算後の管理コード（NULL 行に対して）
    preview_rows = []
    for r in raw_rows:
        mc = str(r.get("management_code") or "").strip()
        computed = None
        if not mc:
            computed = _compute_management_code(r, fallback_date=d)
        preview_rows.append({
            "id": r.get("id"),
            "production_day": str(r.get("production_day") or ""),
            "management_code_db": mc or None,
            "management_code_computed": computed,
            "product_cd": r.get("product_cd"),
            "material_name": r.get("material_name"),
        })

    return {
        "success": True,
        "date": date,
        "total": len(raw_rows),
        "with_management_code_in_db": has_count,
        "management_code_null_in_db": null_count,
        "sample_rows": preview_rows[:10],
    }


# ─────────────────────────────────────────────
# GET /reflected  反映済状態確認
# ─────────────────────────────────────────────

@router.get("/reflected")
async def get_reflected_status(
    date: str = Query(..., description="対象日 YYYY-MM-DD"),
    source: str = Query("cutting_management", description="来源区分"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定日の material_usage_record に reflected=1 のレコードが存在するか確認。
    存在すれば reflected=True を返す。
    """
    d = _parse_date(date)
    if d is None:
        return {"success": True, "date": date, "reflected": False}

    sql = text("""
        SELECT COUNT(*) FROM material_usage_record
        WHERE usage_date = :d
          AND source = :source
          AND reflected = 1
    """)
    try:
        count = (await db.execute(sql, {"d": d, "source": source})).scalar() or 0
        reflected = count > 0
    except Exception:
        reflected = False

    return {"success": True, "date": date, "source": source, "reflected": reflected}


# ─────────────────────────────────────────────
# GET /reflected-management-codes  反映済管理コード一覧（任意日で1回でも反映されていれば含む）
# ─────────────────────────────────────────────

@router.get("/reflected-management-codes")
async def get_reflected_management_codes(
    source: str = Query("cutting_management", description="来源区分"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    material_usage_record で reflected=1 のレコードに含まれる management_code の一覧を返す。
    同一管理コードが別日に反映されていても、一覧に含まれていれば「反映済」と表示するために使用。
    """
    sql = text("""
        SELECT DISTINCT management_code
        FROM material_usage_record
        WHERE source = :source
          AND reflected = 1
          AND management_code IS NOT NULL
          AND LENGTH(TRIM(COALESCE(management_code, ''))) > 0
    """)
    try:
        result = await db.execute(sql, {"source": source})
        codes = [row[0] for row in result.fetchall() if row[0]]
        return {"success": True, "management_codes": codes}
    except Exception as e:
        return {"success": False, "management_codes": [], "message": str(e)}


# ─────────────────────────────────────────────
# GET /records  過去の使用済レコード一覧
# ─────────────────────────────────────────────

@router.get("/records")
async def list_usage_records(
    usage_date: Optional[str] = Query(None, description="使用日 YYYY-MM-DD"),
    material_cd: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料使用済レコード一覧"""
    conditions = ["1=1"]
    params: dict = {}
    if usage_date:
        conditions.append("usage_date = :usage_date")
        params["usage_date"] = date_type.fromisoformat(usage_date)
    if material_cd:
        conditions.append("material_cd = :material_cd")
        params["material_cd"] = material_cd
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where = " AND ".join(conditions)
    count_sql = text(f"SELECT COUNT(*) FROM material_usage_record WHERE {where}")
    total = (await db.execute(count_sql, params)).scalar() or 0

    params["offset"] = (page - 1) * page_size
    params["limit"] = page_size
    list_sql = text(f"""
        SELECT id, usage_date, material_cd, material_name, usage_count, source,
               management_codes, management_code, reflected, created_at, updated_at
        FROM material_usage_record
        WHERE {where}
        ORDER BY usage_date DESC, material_cd ASC
        LIMIT :limit OFFSET :offset
    """)
    try:
        result = await db.execute(list_sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "material_usage_record" in msg and ("doesn't exist" in msg or "not exist" in msg):
            raise HTTPException(
                status_code=503,
                detail="material_usage_record テーブルが存在しません。Migration 075 を実行してください。",
            ) from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    def _row_to_dict(r: dict) -> dict:
        return {
            "id": r["id"],
            "usage_date": r["usage_date"].isoformat() if r["usage_date"] else None,
            "material_cd": r["material_cd"],
            "material_name": r["material_name"],
            "usage_count": r["usage_count"],
            "source": r["source"],
            "management_codes": r.get("management_codes"),
            "management_code": r.get("management_code"),
            "reflected": bool(r.get("reflected", 0)),
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
        }

    return {
        "success": True,
        "data": {"list": [_row_to_dict(dict(r)) for r in rows], "total": total},
    }
