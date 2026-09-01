"""
材料使用済 API
  /api/material/usage/preview  → 使用数プレビュー（書き込みなし）
  /api/material/usage/commit   → 使用数反映（3ステップ処理）
  /api/material/usage/reflected → 指定日の反映済状態確認
  /api/material/usage/records  → 過去の使用済レコード一覧

【commit 3ステップ仕様】
  Step 1: cutting_management（指定日）の各行を material_usage_record に1行1件で書き込み
          - usage_date = production_day, usage_count = 行の usage_count（按分時は <1）
          - サブ在庫行（use_material_stock_sub=1）は対象外
          - 反映済（reflected=1）または別日に既に記録済みの管理コードは更新しない
          - 同一日・未反映レコードは usage_count / material_cd を最新値で更新（再実行時の按分修正を反映）
          - material_cd は products または material_name → materials で解決
  Step 2: material_usage_record（reflected=0）を (usage_date, material_cd) で SUM(usage_count)
          → material_stock.planned_usage を更新（四捨五入して整数束）
  Step 3: Step 2 で material_stock 更新に成功した材料のレコードのみ reflected = 1
          cutting_management は当該管理コード行のみ「反映済」にする
"""
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam
from typing import Optional, List
from datetime import date as date_type
import logging

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_purchase_operation
from app.modules.auth.models import User
from app.modules.material.schemas import (
    MaterialUsagePreviewItem,
    MaterialUsageCommitRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)

SOURCE_CUTTING = "cutting_management"


def _normalize_mgmt_code(value) -> str:
    return str(value or "").strip()


async def collect_reflected_management_codes(
    db: AsyncSession,
    source: str = SOURCE_CUTTING,
    *,
    other_than_day: Optional[date_type] = None,
) -> set[str]:
    """
    既に使用数反映済みの management_code 集合（日付を問わない）。
    - material_usage_record.reflected=1
    - cutting_management.material_usage_reflected='反映済'
      other_than_day 指定時は「その日以外」の切断行だけを見る（当日の再実行は妨げない）
    """
    codes: set[str] = set()
    try:
        mur_sql = """
                SELECT management_code, management_codes
                FROM material_usage_record
                WHERE source = :source
                  AND reflected = 1
        """
        mur_params: dict = {"source": source}
        if other_than_day is not None:
            mur_sql += " AND (usage_date IS NULL OR usage_date <> :other_than_day)"
            mur_params["other_than_day"] = other_than_day
        mur = await db.execute(text(mur_sql), mur_params)
        for row in mur.fetchall():
            mc = _normalize_mgmt_code(row[0])
            if mc:
                codes.add(mc)
            extras = str(row[1] or "")
            for part in extras.replace("，", ",").split(","):
                p = part.strip()
                if p:
                    codes.add(p)
    except Exception as e:
        logger.warning("collect reflected codes from material_usage_record failed: %s", e)

    try:
        if other_than_day is not None:
            cm = await db.execute(
                text("""
                    SELECT DISTINCT management_code
                    FROM cutting_management
                    WHERE material_usage_reflected = '反映済'
                      AND management_code IS NOT NULL
                      AND LENGTH(TRIM(management_code)) > 0
                      AND production_day <> :other_than_day
                """),
                {"other_than_day": other_than_day},
            )
        else:
            cm = await db.execute(
                text("""
                    SELECT DISTINCT management_code
                    FROM cutting_management
                    WHERE material_usage_reflected = '反映済'
                      AND management_code IS NOT NULL
                      AND LENGTH(TRIM(management_code)) > 0
                """)
            )
        for row in cm.fetchall():
            mc = _normalize_mgmt_code(row[0])
            if mc:
                codes.add(mc)
    except Exception as e:
        logger.warning("collect reflected codes from cutting_management failed: %s", e)
    return codes


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


def _is_sub_stock(row: dict) -> bool:
    """use_material_stock_sub=1 は使用数反映対象外（サブ在庫は手動）。"""
    v = _row_val(row, "use_material_stock_sub")
    if v is True:
        return True
    if v is False or v is None:
        return False
    try:
        return int(v) == 1
    except (TypeError, ValueError):
        return str(v).strip().lower() in ("1", "true")


def _parse_usage_count(raw) -> Optional[float]:
    """行の usage_count。未設定は 1。0 以下は対象外のため None。"""
    if raw is None:
        return 1.0
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 1.0
    if value <= 0:
        return None
    return value


def _qty_to_stock_int(value) -> int:
    """
    material_stock.planned_usage は整数束。
    Python の round() は banker rounding（0.5→0, 1.5→2）のため使わず、四捨五入する。
    """
    try:
        qty = Decimal(str(value if value is not None else 0))
    except Exception:
        return 0
    return int(qty.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


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
            cm.use_material_stock_sub,
            cm.usage_count,
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

    def accumulate(rows: list) -> tuple[dict[tuple, float], dict[tuple, set]]:
        """管理コード単位で1回だけ数え、材料別に usage_count を合計する。"""
        by_code: dict[str, tuple[tuple, float]] = {}
        for r in rows:
            if _is_sub_stock(r):
                continue
            mgmt = str(r.get("management_code") or "").strip()
            if not mgmt:
                continue
            usage = _parse_usage_count(r.get("usage_count"))
            if usage is None:
                continue
            mat_cd = r.get("_resolved_material_cd") or ""
            mat_name = r.get("_resolved_material_name") or ""
            key = (mat_cd or "__unknown__", mat_name or mat_cd or "不明")
            by_code[mgmt] = (key, usage)
        qty_map: dict[tuple, float] = {}
        code_map: dict[tuple, set] = {}
        for mgmt, (key, usage) in by_code.items():
            qty_map[key] = qty_map.get(key, 0.0) + usage
            code_map.setdefault(key, set()).add(mgmt)
        return qty_map, code_map

    today_qty, today_codes = accumulate(today_rows)
    tomorrow_qty, tomorrow_codes = accumulate(tomorrow_rows_filtered)

    results: list[dict] = []
    for key, qty in today_qty.items():
        mat_cd, mat_name = key
        codes = today_codes.get(key, set())
        results.append({
            "usage_date": today_str,
            "material_cd": mat_cd,
            "material_name": mat_name,
            "usage_count": _qty_to_stock_int(qty),
            "management_codes": ",".join(sorted(codes)) if codes else None,
        })
    for key, qty in tomorrow_qty.items():
        mat_cd, mat_name = key
        codes = tomorrow_codes.get(key, set())
        results.append({
            "usage_date": tomorrow_str,
            "material_cd": mat_cd,
            "material_name": mat_name,
            "usage_count": _qty_to_stock_int(qty),
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
    current_user: User = Depends(require_purchase_operation("edit")),
):
    """
    使用数反映 API（3ステップ処理）。

    Step 1: cutting_management（指定日）の各行を material_usage_record に1行1件で書き込み。
            - サブ在庫行は対象外。usage_count は行の値（按分可）
            - 反映済または別日記録済みの管理コードは更新しない
            - 同一日・未反映は usage_count を最新値で更新
    Step 2: material_usage_record（reflected=0）を (usage_date, material_cd) で集計
            → material_stock.planned_usage を更新（四捨五入）
    Step 3: stock 更新成功分のみ reflected / 切断「反映済」（当該管理コード行のみ）

    最後に更新した材料の current_stock を再計算する。
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
    updated_existing = 0
    already_reflected_codes = await collect_reflected_management_codes(
        db, source, other_than_day=today_d
    )
    try:
        for row in rows:
            if _is_sub_stock(row):
                continue

            mgmt_code = str(_row_val(row, "management_code") or "").strip()
            if not mgmt_code:
                continue
            # 別日で既に反映済の同一管理コードは再書き込みしない（順延コピー行）
            if mgmt_code in already_reflected_codes:
                continue

            usage_count_val = _parse_usage_count(_row_val(row, "usage_count"))
            if usage_count_val is None:
                continue

            mat_name = str(_row_val(row, "material_name") or "").strip()
            production_day = _row_val(row, "production_day") or today_d

            mat_cd = str(_row_val(row, "material_cd") or "").strip()
            if not mat_cd and mat_name:
                mat_cd = await _resolve_material_cd_by_name(db, mat_name) or ""
            if not mat_cd and _row_val(row, "product_cd"):
                resolved = await _resolve_material_by_product_cd(db, str(_row_val(row, "product_cd")))
                if resolved:
                    mat_cd = resolved[0] or ""
                    if not mat_name:
                        mat_name = resolved[1] or ""

            if not mat_cd or mat_cd == "__unknown__":
                logger.warning(
                    "usage commit: material_cd 未解決のためスキップ management_code=%s",
                    mgmt_code,
                )
                continue

            if row.get("_mgmt_computed") and row.get("id") is not None:
                await db.execute(
                    text("""
                        UPDATE cutting_management
                        SET management_code = :mgmt
                        WHERE id = :id
                          AND (management_code IS NULL OR TRIM(management_code) = '')
                    """),
                    {"mgmt": mgmt_code, "id": row["id"]},
                )

            # 反映済 / 別日記録済みは据え置き。同一日・未反映のみ usage_count を更新
            upsert_sql = text("""
                INSERT INTO material_usage_record
                    (usage_date, material_cd, material_name, usage_count,
                     source, management_codes, management_code, reflected)
                VALUES
                    (:usage_date, :material_cd, :material_name, :usage_count,
                     :source, :management_code, :management_code, 0) AS new
                ON DUPLICATE KEY UPDATE
                    usage_count = IF(
                        material_usage_record.reflected = 1
                        OR material_usage_record.usage_date <> new.usage_date,
                        material_usage_record.usage_count,
                        new.usage_count
                    ),
                    material_cd = IF(
                        material_usage_record.reflected = 1
                        OR material_usage_record.usage_date <> new.usage_date,
                        material_usage_record.material_cd,
                        new.material_cd
                    ),
                    material_name = IF(
                        material_usage_record.reflected = 1
                        OR material_usage_record.usage_date <> new.usage_date,
                        material_usage_record.material_name,
                        new.material_name
                    ),
                    management_codes = IF(
                        material_usage_record.reflected = 1
                        OR material_usage_record.usage_date <> new.usage_date,
                        material_usage_record.management_codes,
                        new.management_codes
                    ),
                    reflected = material_usage_record.reflected
            """)
            result = await db.execute(upsert_sql, {
                "usage_date": production_day,
                "material_cd": mat_cd,
                "material_name": mat_name or "不明",
                "usage_count": usage_count_val,
                "source": source,
                "management_code": mgmt_code,
            })
            rc = int(result.rowcount or 0)
            if rc == 1:
                inserted += 1
            elif rc >= 2:
                updated_existing += 1

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
    updated_material_cds: list[str] = []
    for agg_row in agg_rows:
        agg_date = agg_row[0]
        agg_mat_cd = agg_row[1]
        agg_count = _qty_to_stock_int(agg_row[2] or 0)

        if not agg_mat_cd or agg_mat_cd == "__unknown__":
            continue

        try:
            # 再実行時に未反映分だけで上書きしないよう、当日・当該材料の全レコード合計を書く
            total_sql = text("""
                SELECT COALESCE(SUM(usage_count), 0)
                FROM material_usage_record
                WHERE usage_date = :usage_date
                  AND source = :source
                  AND material_cd = :material_cd
            """)
            total_result = await db.execute(total_sql, {
                "usage_date": agg_date,
                "source": source,
                "material_cd": agg_mat_cd,
            })
            total_count = _qty_to_stock_int(total_result.scalar() or agg_count or 0)

            update_stock_sql = text("""
                UPDATE material_stock
                SET planned_usage = :usage_count,
                    last_updated  = CURRENT_TIMESTAMP
                WHERE material_cd = :material_cd
                  AND date = :usage_date
            """)
            result = await db.execute(update_stock_sql, {
                "usage_count": total_count,
                "material_cd": agg_mat_cd,
                "usage_date": agg_date,
            })
            rowcount = int(result.rowcount or 0)
            if rowcount > 0:
                stock_updated += rowcount
                updated_material_cds.append(agg_mat_cd)
            else:
                logger.warning(
                    "usage commit: material_stock 更新0件 material_cd=%s date=%s（レコード未作成の可能性）",
                    agg_mat_cd,
                    agg_date,
                )
        except Exception as e:
            logger.warning(
                "usage commit: material_stock 更新失敗 material_cd=%s date=%s: %s",
                agg_mat_cd,
                agg_date,
                e,
            )

    # ──────── Step 3: stock 更新成功分のみ reflected = 1、切断側は当該管理コードのみ ────────
    unique_updated_cds = list(dict.fromkeys(updated_material_cds))
    if unique_updated_cds:
        try:
            mark_sql = text("""
                UPDATE material_usage_record
                SET reflected = 1
                WHERE usage_date = :usage_date
                  AND source = :source
                  AND reflected = 0
                  AND material_cd IN :material_cds
            """).bindparams(bindparam("material_cds", expanding=True))
            await db.execute(
                mark_sql,
                {
                    "usage_date": today_d,
                    "source": source,
                    "material_cds": unique_updated_cds,
                },
            )
        except Exception as e:
            logger.warning("usage commit: reflected 更新失敗: %s", e)
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Step 3 reflected 更新に失敗しました: {e}",
            ) from e

    # 反映済フラグは未反映へ戻さない。指定日の切断行で既に reflected=1 の管理コードは列も反映済にする
    try:
        sync_cm_sql = text("""
            UPDATE cutting_management cm
            INNER JOIN material_usage_record mur
              ON mur.source = :source
             AND mur.reflected = 1
             AND TRIM(cm.management_code) COLLATE utf8mb4_unicode_ci
                 = TRIM(mur.management_code) COLLATE utf8mb4_unicode_ci
            SET cm.material_usage_reflected = '反映済'
            WHERE cm.production_day = :prod_day
              AND COALESCE(cm.use_material_stock_sub, 0) = 0
              AND cm.management_code IS NOT NULL
              AND LENGTH(TRIM(cm.management_code)) > 0
              AND COALESCE(cm.material_usage_reflected, '') <> '反映済'
        """)
        await db.execute(sync_cm_sql, {"prod_day": today_d, "source": source})
        # 順延コピー：別日で既に反映済の同一管理コードも当日行へ写す
        await db.execute(
            text("""
                UPDATE cutting_management cm
                INNER JOIN cutting_management cm_src
                  ON TRIM(cm.management_code) COLLATE utf8mb4_unicode_ci
                     = TRIM(cm_src.management_code) COLLATE utf8mb4_unicode_ci
                 AND cm_src.material_usage_reflected = '反映済'
                 AND cm_src.production_day <> cm.production_day
                SET cm.material_usage_reflected = '反映済'
                WHERE cm.production_day = :prod_day
                  AND COALESCE(cm.use_material_stock_sub, 0) = 0
                  AND cm.management_code IS NOT NULL
                  AND LENGTH(TRIM(cm.management_code)) > 0
                  AND COALESCE(cm.material_usage_reflected, '') <> '反映済'
            """),
            {"prod_day": today_d},
        )
    except Exception as e:
        logger.warning("usage commit: cutting_management 反映済同期失敗: %s", e)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Step 3 reflected 更新に失敗しました: {e}",
        ) from e

    # planned_usage 反映後、当該材料の current_stock を再計算する
    if unique_updated_cds:
        try:
            from app.modules.material.stock_api import recalculate_material_current_stock

            await db.flush()
            await recalculate_material_current_stock(db, unique_updated_cds)
        except Exception as e:
            logger.warning("usage commit: current_stock 再計算失敗: %s", e)
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"現在在庫の再計算に失敗しました: {e}",
            ) from e

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"コミットに失敗しました: {e}") from e

    skipped_cds = {
        str(r[1])
        for r in agg_rows
        if r[1] and r[1] != "__unknown__" and str(r[1]) not in set(updated_material_cds)
    }
    message = (
        f"使用数を反映しました（{inserted} 件挿入"
        + (f"、{updated_existing} 件更新" if updated_existing else "")
        + f"、material_stock {stock_updated} 件更新）"
    )
    if skipped_cds:
        message += f"（未更新 {len(skipped_cds)} 材料分は reflected 未設定のため再実行可能）"

    return {
        "success": True,
        "message": message,
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
    current_user: User = Depends(require_purchase_operation("edit")),
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
    current_user: User = Depends(require_purchase_operation("edit")),
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
    exclude_date: Optional[str] = Query(None, description="この日以外で既に反映済のコード（使用数一覧から除外するため）"),
    date: Optional[str] = Query(None, description="exclude_date の別名"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    既に使用数反映済みの management_code 一覧。
    exclude_date / date を指定すると、その日以外で反映済のコードだけを返す
    （順延コピー行を使用材料数一覧から除外するため）。
    """
    try:
        other_day = _parse_date(exclude_date or date)
        codes = sorted(await collect_reflected_management_codes(db, source, other_than_day=other_day))
        return {"success": True, "management_codes": codes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ─────────────────────────────────────────────
# GET /records  過去の使用済レコード一覧（WHERE 共有）
# ─────────────────────────────────────────────

def _usage_record_filter_conditions(
    usage_date: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    material_cd: Optional[str],
    material_keyword: Optional[str],
    source: Optional[str],
    reflected: Optional[bool],
) -> tuple[str, dict]:
    conditions = ["1=1"]
    params: dict = {}
    if date_from and date_to:
        conditions.append("usage_date BETWEEN :date_from AND :date_to")
        params["date_from"] = date_type.fromisoformat(date_from[:10])
        params["date_to"] = date_type.fromisoformat(date_to[:10])
    elif date_from:
        conditions.append("usage_date >= :date_from")
        params["date_from"] = date_type.fromisoformat(date_from[:10])
    elif date_to:
        conditions.append("usage_date <= :date_to")
        params["date_to"] = date_type.fromisoformat(date_to[:10])
    elif usage_date:
        conditions.append("usage_date = :usage_date")
        params["usage_date"] = date_type.fromisoformat(usage_date[:10])
    if material_cd:
        conditions.append("material_cd = :material_cd")
        params["material_cd"] = material_cd.strip()
    if material_keyword and material_keyword.strip():
        conditions.append(
            "(material_cd LIKE :material_keyword OR material_name LIKE :material_keyword)"
        )
        params["material_keyword"] = f"%{material_keyword.strip()}%"
    if source:
        conditions.append("source = :source")
        params["source"] = source
    if reflected is not None:
        conditions.append("reflected = :reflected")
        params["reflected"] = 1 if reflected else 0
    return " AND ".join(conditions), params


@router.get("/records/chart-summary")
async def usage_records_chart_summary(
    usage_date: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="使用日 開始 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="使用日 終了 YYYY-MM-DD"),
    material_cd: Optional[str] = Query(None),
    material_keyword: Optional[str] = Query(None, description="材料CD・材料名 あいまい検索"),
    source: Optional[str] = Query(None),
    reflected: Optional[bool] = Query(None),
    material_top_n: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    """一覧と同一条件で、日別・材料別の使用数合計（チャート用）"""
    where, params = _usage_record_filter_conditions(
        usage_date, date_from, date_to, material_cd, material_keyword, source, reflected
    )
    try:
        by_date_sql = text(f"""
            SELECT usage_date, SUM(usage_count) AS total
            FROM material_usage_record
            WHERE {where}
            GROUP BY usage_date
            ORDER BY usage_date ASC
        """)
        by_mat_sql = text(f"""
            SELECT material_cd, material_name, SUM(usage_count) AS total
            FROM material_usage_record
            WHERE {where}
            GROUP BY material_cd, material_name
            ORDER BY total DESC
            LIMIT :material_top_n
        """)
        p2 = {**params, "material_top_n": material_top_n}
        dr = await db.execute(by_date_sql, params)
        mr = await db.execute(by_mat_sql, p2)
        by_date = []
        for row in dr.mappings().fetchall():
            d = row["usage_date"]
            t = row["total"]
            by_date.append(
                {
                    "usage_date": d.isoformat() if d else None,
                    "total": float(t) if t is not None else 0.0,
                }
            )
        by_material = []
        for row in mr.mappings().fetchall():
            t = row["total"]
            by_material.append(
                {
                    "material_cd": row["material_cd"],
                    "material_name": row["material_name"],
                    "total": float(t) if t is not None else 0.0,
                }
            )
        return {"success": True, "data": {"by_date": by_date, "by_material": by_material}}
    except Exception as e:
        msg = str(e).lower()
        if "material_usage_record" in msg and ("doesn't exist" in msg or "not exist" in msg):
            raise HTTPException(
                status_code=503,
                detail="material_usage_record テーブルが存在しません。Migration 075 を実行してください。",
            ) from e
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/records")
async def list_usage_records(
    usage_date: Optional[str] = Query(None, description="使用日 YYYY-MM-DD（単日。期間指定時は date_from/date_to を優先）"),
    date_from: Optional[str] = Query(None, description="使用日 開始 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="使用日 終了 YYYY-MM-DD"),
    material_cd: Optional[str] = Query(None),
    material_keyword: Optional[str] = Query(None, description="材料CD・材料名 あいまい検索"),
    source: Optional[str] = Query(None),
    reflected: Optional[bool] = Query(None, description="在庫反映済み true / 未反映 false"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    """材料使用済レコード一覧"""
    where, params = _usage_record_filter_conditions(
        usage_date, date_from, date_to, material_cd, material_keyword, source, reflected
    )
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
