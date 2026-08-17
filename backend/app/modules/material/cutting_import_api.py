"""
材料切断ログ CSV インポート API（material_cutting_logs）
POST  /api/material/cutting/import-csv   共有フォルダの CSV を読み込んで DB へ一括書き込み
GET   /api/material/cutting/csv-status   取込元 CSV の存在・更新検知用（mtime/size）
GET   /api/material/cutting/logs         取込済みログ一覧
"""
import csv
import io
import os
import asyncio
import logging
import re
import traceback
from pathlib import Path
from datetime import date, time, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_quality_operation
from app.modules.auth.models import User
from app.modules.material.models import MaterialCuttingLog

logger = logging.getLogger(__name__)

router = APIRouter()


def _material_cutting_csv_path() -> str:
    return settings.get_material_cutting_csv_path()


EXPECTED_COLUMNS = ["項目", "日付", "時間", "HDNo", "担当者", "材料コード", "管理コード"]

# 設備CSVのヘッダゆれ（空白・別名）
_COLUMN_ALIASES = {
    "項目": ("項目", "item"),
    "日付": ("日付", "切断開始日", "切断日", "date", "log_date"),
    "時間": ("時間", "切断開始時刻", "切断開始時間", "時刻", "time", "log_time"),
    "HDNo": ("hdno", "hd_no", "hd no", "ｈｄｎｏ"),
    "担当者": ("担当者", "operator", "operator_name"),
    "材料コード": ("材料コード", "材料cd", "material_cd", "material code"),
    "管理コード": ("管理コード", "管理cd", "management_code", "management code"),
}

# 既定は削除しない（追記＋重複スキップ）。互換のため旧パラメータは残す。
RETENTION_DAYS = 0
# Windows では zoneinfo が tzdata 未導入だと失敗するため、固定 UTC+9（日本は夏時間なし）
JST = timezone(timedelta(hours=9))

# source_file がこのプレフィックスの行は full_replace 時も削除しない（手動連携など）
CUTTING_LOG_MANUAL_SOURCE_PREFIX = "manual:"

# 重複判定キー: 日付・時刻・HDNo・材料コード・管理コード
DedupeKey = tuple[str, str, str, str, str]


def cutting_log_dedupe_key(rec: dict[str, Any]) -> DedupeKey:
    """業務上の同一ログ判定キー。"""
    ld = rec.get("log_date")
    lt = rec.get("log_time")
    if isinstance(ld, date):
        ld_s = ld.isoformat()
    elif ld is None:
        ld_s = ""
    else:
        ld_s = str(ld)[:10]
    if isinstance(lt, time):
        lt_s = lt.strftime("%H:%M:%S")
    elif lt is None:
        lt_s = ""
    else:
        lt_s = str(lt).strip()
        if len(lt_s) >= 8:
            lt_s = lt_s[:8]
    return (
        ld_s,
        lt_s,
        (str(rec.get("hd_no") or "")).strip(),
        (str(rec.get("material_cd") or "")).strip(),
        (str(rec.get("management_code") or "")).strip(),
    )


def dedupe_rows_keep_last(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """CSV 内重複を除去（同一キーは後勝ち）。戻り値: (ユニーク行, 除去件数)。"""
    by_key: dict[DedupeKey, dict[str, Any]] = {}
    for rec in rows:
        by_key[cutting_log_dedupe_key(rec)] = rec
    unique = list(by_key.values())
    return unique, max(0, len(rows) - len(unique))


def _cutting_delete_scope():
    """full_replace 時に消してよい行：手動行（manual:）以外"""
    return or_(
        MaterialCuttingLog.source_file.is_(None),
        ~MaterialCuttingLog.source_file.like(CUTTING_LOG_MANUAL_SOURCE_PREFIX + "%"),
    )


def _norm_header(name: str) -> str:
    s = str(name).replace("\ufeff", "").strip().lower()
    s = re.sub(r"[\s\u3000_\-　]+", "", s)
    return s


def _header_index_map(header: list[str]) -> dict[str, int]:
    by_norm = {_norm_header(h): i for i, h in enumerate(header) if str(h).strip()}
    out: dict[str, int] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            idx = by_norm.get(_norm_header(alias))
            if idx is not None:
                out[canonical] = idx
                break
        if canonical not in out:
            # 正規化後の canonical 自身（例: HDNo → hdno）
            idx = by_norm.get(_norm_header(canonical))
            if idx is not None:
                out[canonical] = idx
    # ヘッダ名が取れない場合、列数が一致すれば位置フォールバック
    if len(out) < 3 and len(header) >= len(EXPECTED_COLUMNS):
        for i, name in enumerate(EXPECTED_COLUMNS):
            out.setdefault(name, i)
    return out


def _csv_file_stat(path: str) -> dict:
    """共有 CSV の存在・最終更新・サイズ（フロントのポーリング用）。"""
    p = Path(path)
    if not p.exists():
        return {
            "exists": False,
            "path": path,
            "mtime_ms": None,
            "size": None,
            "signature": None,
        }
    st = p.stat()
    mtime_ms = int(st.st_mtime * 1000)
    size = int(st.st_size)
    return {
        "exists": True,
        "path": path,
        "mtime_ms": mtime_ms,
        "size": size,
        "signature": f"{mtime_ms}:{size}",
    }


def _read_csv_file(path: str) -> str:
    """複数エンコーディングで CSV を読む（日本語設備は cp932/shift_jis が多い）。"""
    if not path or not str(path).strip():
        raise FileNotFoundError("CSV パスが未設定です。.env の MATERIAL_CUTTING_CSV_PATH を確認してください。")
    # UNC は pathlib より os.path の方が安定
    if not os.path.isfile(path):
        raise FileNotFoundError(f"CSV ファイルが見つかりません: {path}")

    raw = None
    last_err: Optional[Exception] = None
    for enc in ("cp932", "shift_jis", "utf-8-sig", "utf-8", "euc-jp"):
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                raw = f.read()
            break
        except (UnicodeDecodeError, ValueError, OSError) as e:
            last_err = e
            continue
    if raw is None:
        try:
            with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
                raw = f.read()
        except OSError as e:
            raise FileNotFoundError(f"CSV を読めません: {path} ({e})") from e
    if not raw or not raw.strip():
        raise ValueError(f"CSV ファイルが空です: {path}")
    if last_err and not raw.strip():
        raise ValueError(f"ファイルのエンコーディングを判定できません: {path}")
    return raw


def _detect_delimiter(sample: str) -> str:
    """カンマ / タブ / セミコロンを簡易判定。"""
    lines = [ln for ln in sample.splitlines() if ln.strip()][:5]
    if not lines:
        return ","
    best, best_score = ",", -1
    for delim in (",", "\t", ";"):
        counts = [ln.count(delim) for ln in lines]
        if not counts:
            continue
        # 各行で区切りが同数かつ 1 以上なら有力
        if min(counts) >= 1 and max(counts) == min(counts) and min(counts) > best_score:
            best, best_score = delim, min(counts)
    return best


def _parse_date(val: str) -> Optional[date]:
    if not val or not str(val).strip():
        return None
    val = str(val).strip().strip("'\"")
    # 日時が付いている CSV（Excel / 設備出力）は日付部分だけ取る
    if "T" in val:
        val = val.split("T", 1)[0].strip()
    elif " " in val:
        val = val.split(" ", 1)[0].strip()
    val = val.replace(".", "/").replace("-", "/")
    # 年月日表記
    m = re.match(r"^(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", val)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    # YYYY/M/D or YYYYMMDD
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", val)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    if re.match(r"^\d{8}$", val):
        try:
            return datetime.strptime(val, "%Y%m%d").date()
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", val)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            return None
    return None


def _parse_time(val: str) -> Optional[time]:
    if not val or not str(val).strip():
        return None
    val = str(val).strip().strip("'\"")
    if "T" in val:
        val = val.split("T", 1)[-1].strip()
    elif " " in val and ":" in val.split(" ", 1)[-1]:
        val = val.split(" ", 1)[-1].strip()
    val = val.split(".")[0]
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(val, fmt).time()
        except ValueError:
            continue
    return None


def parse_material_cutting_csv_text(raw_text: str, source_path: str = "") -> dict[str, Any]:
    """
    CSV テキストをパースし、取込用レコードとメタ情報を返す。
    returns: {
      rows: list[dict],  # item/log_date/.../raw_line
      header: list[str],
      header_idx: dict,
      csv_dates: list[date],
      errors: list[str],
      delimiter: str,
    }
    """
    delimiter = _detect_delimiter(raw_text[:4096])
    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    header: Optional[list[str]] = None
    header_idx: dict[str, int] = {}
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    csv_dates: list[date] = []

    for row_idx, row in enumerate(reader, start=1):
        if not any(str(cell).strip() for cell in row):
            continue

        if header is None:
            header = [str(c).replace("\ufeff", "").strip() for c in row]
            header_idx = _header_index_map(header)
            # 必須列の最低限チェック（日付 or 管理コードのどちらかは欲しい）
            if "日付" not in header_idx and "管理コード" not in header_idx and "材料コード" not in header_idx:
                raise ValueError(
                    "CSV ヘッダを認識できません。"
                    f"検出ヘッダ={header!r} / 区切り={delimiter!r}。"
                    f"期待列の例: {EXPECTED_COLUMNS}"
                )
            continue

        raw_line = delimiter.join(row)

        try:

            def _col(name: str) -> str:
                idx = header_idx.get(name, -1)
                return str(row[idx]).strip() if 0 <= idx < len(row) else ""

            log_date = _parse_date(_col("日付"))
            log_time = _parse_time(_col("時間"))
            rec = {
                "item": _col("項目") or None,
                "log_date": log_date,
                "log_time": log_time,
                "hd_no": _col("HDNo") or None,
                "operator_name": _col("担当者") or None,
                "material_cd": _col("材料コード") or None,
                "management_code": _col("管理コード") or None,
                "raw_line": raw_line,
                "source_file": source_path or None,
            }
            # 全項目空ならスキップ
            if not any(
                [
                    rec["item"],
                    rec["log_date"],
                    rec["hd_no"],
                    rec["material_cd"],
                    rec["management_code"],
                ]
            ):
                continue
            rows.append(rec)
            if log_date is not None:
                csv_dates.append(log_date)
        except Exception as exc:
            msg = f"行 {row_idx}: {exc}"
            errors.append(msg)
            if len(errors) >= 50:
                errors.append("... エラーが多すぎるため省略")
                break

    if header is None:
        raise ValueError("CSV にヘッダ行がありません")

    return {
        "rows": rows,
        "header": header,
        "header_idx": header_idx,
        "csv_dates": csv_dates,
        "errors": errors,
        "delimiter": delimiter,
    }


def compute_import_window(
    csv_dates: list[date],
    retain_days: int = 0,
    today: Optional[date] = None,
) -> dict[str, Any]:
    """互換用。既定運用では削除しないため retain_days=0。"""
    today_jst = today or datetime.now(JST).date()
    cutoff: Optional[date] = None
    if retain_days > 0:
        cutoff = today_jst - timedelta(days=retain_days)
    d_min = min(csv_dates) if csv_dates else None
    d_max = max(csv_dates) if csv_dates else None
    return {
        "today": today_jst,
        "cutoff": cutoff,
        "csv_date_min": d_min,
        "csv_date_max": d_max,
        "window_start": None,
        "window_end": None,
    }


async def _load_existing_dedupe_keys(
    db: AsyncSession,
    d_min: Optional[date],
    d_max: Optional[date],
) -> set[DedupeKey]:
    """DB 既存行の重複キーを取得（CSV 日付帯があればその範囲のみ）。"""
    q = select(
        MaterialCuttingLog.log_date,
        MaterialCuttingLog.log_time,
        MaterialCuttingLog.hd_no,
        MaterialCuttingLog.material_cd,
        MaterialCuttingLog.management_code,
    )
    if d_min is not None and d_max is not None:
        q = q.where(
            or_(
                MaterialCuttingLog.log_date.is_(None),
                and_(MaterialCuttingLog.log_date >= d_min, MaterialCuttingLog.log_date <= d_max),
            )
        )
    result = await db.execute(q)
    keys: set[DedupeKey] = set()
    for row in result.all():
        keys.add(
            cutting_log_dedupe_key(
                {
                    "log_date": row[0],
                    "log_time": row[1],
                    "hd_no": row[2],
                    "material_cd": row[3],
                    "management_code": row[4],
                }
            )
        )
    return keys


@router.get("/csv-status")
async def cutting_csv_status(
    current_user: User = Depends(verify_token_and_get_user),
):
    """取込元 materialCutting.csv の stat。フロントが signature 変化で自動取込する。"""
    path = _material_cutting_csv_path()
    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, _csv_file_stat, path)
        return {"success": True, "data": data}
    except OSError as e:
        logger.warning("CSV stat OSError: %s", e)
        raise HTTPException(status_code=503, detail=f"CSV パスにアクセスできません: {e}")
    except Exception as e:
        logger.exception("CSV stat エラー")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-csv")
async def import_cutting_csv(
    full_replace: bool = Query(
        False,
        description="true のとき手動行以外を消してから全行取込（通常は使わない）",
    ),
    retain_days: int = Query(
        RETENTION_DAYS,
        ge=0,
        le=3650,
        description="互換用。既定 0=削除しない。>0 のときだけ古い行を削除（非推奨）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("export")),
):
    """共有フォルダから materialCutting.csv を読み込み material_cutting_logs へ書き込む。

    デフォルト（推奨）:
    - 既存データは削除しない
    - CSV 内・DB 既存と同一キー（日付+時刻+HDNo+材料コード+管理コード）はスキップして追記
    """
    path = _material_cutting_csv_path()
    try:
        loop = asyncio.get_running_loop()
        raw_text = await loop.run_in_executor(None, _read_csv_file, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("CSV 読み込み中にエラー発生")
        raise HTTPException(status_code=500, detail=f"CSV 読み込みエラー: {e}")

    try:
        parsed = parse_material_cutting_csv_text(raw_text, source_path=path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pending_rows: list[dict[str, Any]] = parsed["rows"]
    errors: list[str] = list(parsed["errors"])
    csv_dates: list[date] = list(parsed["csv_dates"])

    if not pending_rows:
        raise HTTPException(
            status_code=400,
            detail=(
                "CSV から取込可能なデータ行がありません。"
                f"ヘッダ={parsed.get('header')!r} / 区切り={parsed.get('delimiter')!r} / "
                f"パス={path}"
            ),
        )

    try:
        unique_rows, skipped_csv_dup = dedupe_rows_keep_last(pending_rows)
        d_min = min(csv_dates) if csv_dates else None
        d_max = max(csv_dates) if csv_dates else None

        deleted_prune = 0
        truncated = False
        skipped_db_dup = 0
        imported = 0

        if full_replace:
            await db.execute(delete(MaterialCuttingLog).where(_cutting_delete_scope()))
            truncated = True
            for rec in unique_rows:
                db.add(MaterialCuttingLog(**rec))
                imported += 1
        else:
            # 非推奨: 明示指定時のみ古い行削除（デフォルトは削除しない）
            if retain_days > 0:
                cutoff = datetime.now(JST).date() - timedelta(days=retain_days)
                r_prune = await db.execute(
                    delete(MaterialCuttingLog).where(
                        MaterialCuttingLog.log_date < cutoff,
                        _cutting_delete_scope(),
                    )
                )
                deleted_prune = r_prune.rowcount or 0

            existing = await _load_existing_dedupe_keys(db, d_min, d_max)
            for rec in unique_rows:
                key = cutting_log_dedupe_key(rec)
                if key in existing:
                    skipped_db_dup += 1
                    continue
                db.add(MaterialCuttingLog(**rec))
                existing.add(key)
                imported += 1

        await db.commit()

        body: dict = {
            "success": True,
            "imported": imported,
            "parsed_rows": len(pending_rows),
            "unique_rows": len(unique_rows),
            "skipped_csv_dup": skipped_csv_dup,
            "skipped_db_dup": skipped_db_dup,
            "errors_count": len(errors),
            "errors": errors[:20],
            "full_replace": truncated,
            "csv_path": path,
            "delimiter": parsed.get("delimiter"),
            "header": parsed.get("header"),
            "csv_date_min": d_min.isoformat() if d_min else None,
            "csv_date_max": d_max.isoformat() if d_max else None,
            "deleted_prune": deleted_prune,
            "deleted_window": 0,
            "retain_days": retain_days,
            "skipped_before_retention": 0,
        }
        if imported == 0 and skipped_db_dup > 0:
            body["warning"] = (
                f"新規取込 0 件（DB 既存と重複 {skipped_db_dup} 件をスキップ）。"
                "すでに取り込み済みです。"
            )
        return body
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CSV インポート処理中にエラー発生")
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"インポート処理エラー: {e}\n{tb[-500:]}")


def _log_to_dict(r: MaterialCuttingLog) -> dict:
    return {
        "id": r.id,
        "item": r.item,
        "log_date": r.log_date.isoformat() if r.log_date else None,
        "log_time": str(r.log_time) if r.log_time else None,
        "hd_no": r.hd_no,
        "operator_name": r.operator_name,
        # JSON で数値化され指数表記になるのを防ぐ（常に文字列で返す）
        "material_cd": str(r.material_cd) if r.material_cd is not None else None,
        "manufacture_no": str(r.manufacture_no) if r.manufacture_no is not None else None,
        "management_code": str(r.management_code) if r.management_code is not None else None,
        "raw_line": r.raw_line,
        "source_file": r.source_file,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/logs")
async def list_cutting_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=20000),
    keyword: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("export")),
):
    """取込済み切断ログ一覧"""
    q = select(MaterialCuttingLog)

    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            or_(
                MaterialCuttingLog.material_cd.ilike(kw),
                MaterialCuttingLog.manufacture_no.ilike(kw),
                MaterialCuttingLog.management_code.ilike(kw),
                MaterialCuttingLog.hd_no.ilike(kw),
                MaterialCuttingLog.operator_name.ilike(kw),
            )
        )
    if startDate:
        q = q.where(MaterialCuttingLog.log_date >= date.fromisoformat(startDate))
    if endDate:
        q = q.where(MaterialCuttingLog.log_date <= date.fromisoformat(endDate))

    total_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    q = q.order_by(MaterialCuttingLog.log_date.desc(), MaterialCuttingLog.id.desc())
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": {"list": [_log_to_dict(r) for r in rows], "total": total},
    }
