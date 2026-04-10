"""
材料切断ログ CSV インポート API（material_cutting_logs）
POST  /api/material/cutting/import-csv   共有フォルダの CSV を読み込んで DB へ一括書き込み
GET   /api/material/cutting/csv-status   取込元 CSV の存在・更新検知用（mtime/size）
GET   /api/material/cutting/logs         取込済みログ一覧
"""
import csv
import io
import asyncio
import logging
import traceback
from pathlib import Path
from datetime import date, time, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, text

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.models import MaterialCuttingLog

logger = logging.getLogger(__name__)

router = APIRouter()


def _material_cutting_csv_path() -> str:
    return settings.get_material_cutting_csv_path()

EXPECTED_COLUMNS = ["項目", "日付", "時間", "HDNo", "担当者", "材料コード", "管理コード"]

# 取込前に log_date がこれより古い行を削除（0 で無効）
RETENTION_DAYS = 5
# Windows では zoneinfo が tzdata 未導入だと失敗するため、固定 UTC+9（日本は夏時間なし）
JST = timezone(timedelta(hours=9))


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
    """Read CSV with encoding fallback: utf-8-sig -> cp932 -> shift_jis."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV ファイルが見つかりません: {path}")

    for enc in ("utf-8-sig", "cp932", "shift_jis"):
        try:
            return p.read_text(encoding=enc)
        except (UnicodeDecodeError, ValueError):
            continue
    raise ValueError(f"ファイルのエンコーディングを判定できません: {path}")


def _parse_date(val: str) -> Optional[date]:
    if not val or not val.strip():
        return None
    val = val.strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def _parse_time(val: str) -> Optional[time]:
    if not val or not val.strip():
        return None
    val = val.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(val, fmt).time()
        except ValueError:
            continue
    return None


@router.get("/csv-status")
async def cutting_csv_status(
    current_user: User = Depends(verify_token_and_get_user),
):
    """取込元 materialCutting.csv の stat。フロントが signature 変化で自動取込する。"""
    path = _material_cutting_csv_path()
    try:
        loop = asyncio.get_event_loop()
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
        description="true のとき TRUNCATE 後に全行を取込（最速だが CSV に無い履歴は消える）",
    ),
    retain_days: int = Query(
        RETENTION_DAYS,
        ge=0,
        le=3650,
        description="この日数より古い log_date を先に削除。0 でスキップ。full_replace 時は無視",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """共有フォルダから materialCutting.csv を読み込み material_cutting_logs へ書き込む。

    デフォルト（推奨・高速）:
    1) retain_days より古い行を DELETE（インデックス利用）
    2) 本 CSV に含まれる日付の最小～最大の範囲の行を DELETE（同一ファイル再取込で重複しない）
    3) CSV のうち、log_date が無い行はそのまま INSERT；ある行は cutoff 以降のみ INSERT

    full_replace=true のときは TRUNCATE のあと CSV 全行を INSERT（最速だが他用途の履歴も消える）。
    """
    path = _material_cutting_csv_path()
    try:
        loop = asyncio.get_event_loop()
        raw_text = await loop.run_in_executor(None, _read_csv_file, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("CSV 読み込み中にエラー発生")
        raise HTTPException(status_code=500, detail=f"CSV 読み込みエラー: {e}")

    try:
        reader = csv.reader(io.StringIO(raw_text))
        header = None
        errors: list[str] = []
        pending: list[MaterialCuttingLog] = []
        csv_dates: list[date] = []

        for row_idx, row in enumerate(reader, start=1):
            if not any(cell.strip() for cell in row):
                continue

            if header is None:
                header = [c.strip() for c in row]
                continue

            raw_line = ",".join(row)

            try:
                def _col(name: str) -> str:
                    idx = header.index(name) if name in header else -1
                    return row[idx].strip() if 0 <= idx < len(row) else ""

                log_date = _parse_date(_col("日付"))
                log_time = _parse_time(_col("時間"))

                record = MaterialCuttingLog(
                    item=_col("項目") or None,
                    log_date=log_date,
                    log_time=log_time,
                    hd_no=_col("HDNo") or None,
                    operator_name=_col("担当者") or None,
                    material_cd=_col("材料コード") or None,
                    management_code=_col("管理コード") or None,
                    raw_line=raw_line,
                    source_file=path,
                )
                pending.append(record)
                if log_date is not None:
                    csv_dates.append(log_date)
            except Exception as exc:
                msg = f"行 {row_idx}: {exc}"
                errors.append(msg)
                if len(errors) >= 50:
                    errors.append("... エラーが多すぎるため省略")
                    break

        deleted_prune = 0
        deleted_window = 0
        truncated = False
        cutoff: Optional[date] = None
        d_min: Optional[date] = None
        d_max: Optional[date] = None
        skipped_retention = 0

        if full_replace:
            await db.execute(text("TRUNCATE TABLE material_cutting_logs"))
            truncated = True
            imported = 0
            for rec in pending:
                db.add(rec)
                imported += 1
        else:
            today_jst = datetime.now(JST).date()
            if retain_days > 0:
                cutoff = today_jst - timedelta(days=retain_days)
                r_prune = await db.execute(
                    delete(MaterialCuttingLog).where(MaterialCuttingLog.log_date < cutoff)
                )
                deleted_prune = r_prune.rowcount or 0

            d_min = min(csv_dates) if csv_dates else None
            d_max = max(csv_dates) if csv_dates else None
            if d_min is not None and d_max is not None and d_min <= d_max:
                r_win = await db.execute(
                    delete(MaterialCuttingLog).where(
                        MaterialCuttingLog.log_date >= d_min,
                        MaterialCuttingLog.log_date <= d_max,
                    )
                )
                deleted_window = r_win.rowcount or 0

            imported = 0
            for rec in pending:
                if rec.log_date is not None and cutoff is not None and rec.log_date < cutoff:
                    skipped_retention += 1
                    continue
                db.add(rec)
                imported += 1

        await db.commit()

        body: dict = {
            "success": True,
            "imported": imported,
            "errors_count": len(errors),
            "errors": errors[:20],
            "full_replace": truncated,
        }
        if not full_replace:
            body["deleted_prune"] = deleted_prune
            body["deleted_window"] = deleted_window
            body["retain_days"] = retain_days
            body["csv_date_min"] = d_min.isoformat() if d_min else None
            body["csv_date_max"] = d_max.isoformat() if d_max else None
            body["skipped_before_retention"] = skipped_retention
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
    current_user: User = Depends(verify_token_and_get_user),
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
