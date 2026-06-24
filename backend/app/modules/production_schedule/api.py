"""
生産状況・スケジュール API
- GET /processing-status: production_plan_schedules を file_name でフィルタして返す
- GET /schedule: 設備運行時間スロット（現状スタブ、必要に応じて production_plan_schedules 等から導出可能）
- GET /plan/batch/schedule-months: 生産月一覧
- GET /plan/batch/material-requirements-summary: instruction_plans を期間（start_date 優先）で集計し材料所要本数を返す
- POST /plan/batch/generate-from-schedule: 生産月で production_plan_schedules から切断指示計画(instruction_plans)を生成
"""
import json
import logging
import re
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any

from sqlalchemy import select
from app.core.inspection_inspector_work_schedule import (
    DEFAULT_INSPECTION_STANDARD_HOURS,
    DEFAULT_INSPECTION_STANDARD_SEC,
    InspectorWorkScheduleIndex,
    load_inspector_work_schedule_index,
)
from app.services.inspection_management_import import INSPECTOR_METRICS_DEFECT_HEADERS
from app.core.company_work_calendar import (
    count_scheduled_workdays,
    is_scheduled_workday,
    iter_dates_inclusive,
    load_company_calendar_sets,
    parse_date_csv,
)
from app.core.database import get_db
from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_aps_operation, require_mes_operation, require_menu_code
from app.modules.auth.models import User
from app.modules.master.models import ProcessDefectItem
from app.services.inspection_management_import import DATA_SOURCE_MES, resolve_data_source

router = APIRouter()
logger = logging.getLogger(__name__)

# MES 実績列の参照可否（03〜07 系）を DB から見て SQL 断片を組み立て
_CUTTING_MGMT_MES_COLUMNS = (
    "mes_production_started_at",
    "mes_production_ended_at",
    "mes_net_production_sec",
    "mes_paused_accum_sec",
    "mes_production_is_paused",
    "mes_setup_time_min",
    "mes_saw_blade_exchange_min",
    "mes_repair_min",
    "mes_operator_user_id",
    "mes_scanned_code",
)
_COMPONENT_REQUIREMENTS_PLAN_COLUMNS = frozenset({"molding_actual_plan", "molding_plan"})
_TOKYO_TZINFO_CACHE: Any = None


def _tokyo_tzinfo():
    """Asia/Tokyo（Windows で tzdata が無い場合は固定 UTC+9 オフセットを使う。DST は考慮しない）"""
    global _TOKYO_TZINFO_CACHE
    if _TOKYO_TZINFO_CACHE is not None:
        return _TOKYO_TZINFO_CACHE
    try:
        from zoneinfo import ZoneInfo

        _TOKYO_TZINFO_CACHE = ZoneInfo("Asia/Tokyo")
    except Exception:
        _TOKYO_TZINFO_CACHE = timezone(timedelta(hours=9))
    return _TOKYO_TZINFO_CACHE


async def _get_cutting_mgmt_columns(db: AsyncSession) -> set[str]:
    """cutting_management の既存列名を information_schema から取得（MES 列の有無判定用）"""
    try:
        result = await db.execute(
            text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'cutting_management'
            """)
        )
        return {str(r[0]) for r in result.fetchall()}
    except Exception as e:
        logger.warning("cutting_management column introspection failed: %s", e)
        return set()


def _cutting_mgmt_mes_select_fragment(existing: set[str]) -> str:
    parts = [f"`cutting_management`.`{c}`" for c in _CUTTING_MGMT_MES_COLUMNS if c in existing]
    return (",\n               ".join(parts) + ",") if parts else ""


def _mes_column_migration_hint(column: str) -> str:
    hints = {
        "mes_production_started_at": "03_cutting_management_mes_actual_fields.sql",
        "mes_production_ended_at": "03_cutting_management_mes_actual_fields.sql",
        "mes_setup_time_min": "03_cutting_management_mes_actual_fields.sql",
        "mes_saw_blade_exchange_min": "11_cutting_management_mes_blade_repair_min.sql",
        "mes_repair_min": "11_cutting_management_mes_blade_repair_min.sql",
        "mes_operator_user_id": "03_cutting_management_mes_actual_fields.sql",
        "mes_net_production_sec": "04_cutting_management_mes_net_production_sec.sql",
        "mes_paused_accum_sec": "05_cutting_management_mes_paused_accum_sec.sql",
        "mes_production_is_paused": "07_cutting_management_mes_production_is_paused.sql",
        "mes_scanned_code": "06_cutting_management_mes_scanned_code.sql",
    }
    mig = hints.get(column, "03〜07_cutting_management_mes_*.sql")
    return f"列 `{column}` が未作成です。backend/database/migrations/{mig} を実行してください。"


async def _reject_concurrent_mes_production_on_machine(
    db: AsyncSession,
    cutting_id: int,
    cm_cols: set[str],
) -> None:
    """同一切断機で他行の MES 生産が未完了なら 409 を返す"""
    if "mes_production_started_at" not in cm_cols or "mes_production_ended_at" not in cm_cols:
        return
    scope = await db.execute(
        text("""
            SELECT cutting_machine, production_day
            FROM cutting_management
            WHERE id = :cid
            LIMIT 1
        """),
        {"cid": cutting_id},
    )
    scope_row = scope.fetchone()
    if not scope_row or not scope_row[0] or scope_row[1] is None:
        return
    machine = str(scope_row[0]).strip()
    prod_day = scope_row[1]
    conflict = await db.execute(
        text("""
            SELECT id, production_sequence, product_name, product_cd
            FROM cutting_management
            WHERE cutting_machine = :machine
              AND production_day = :pday
              AND id <> :cid
              AND mes_production_started_at IS NOT NULL
              AND mes_production_ended_at IS NULL
            LIMIT 1
        """),
        {"cid": cutting_id, "machine": machine, "pday": prod_day},
    )
    other = conflict.fetchone()
    if not other:
        return
    oid, pseq, pname, pcd = other[0], other[1], other[2], other[3]
    label_parts: list[str] = []
    if pseq is not None:
        label_parts.append(f"?{pseq}")
    name = (pname or pcd or "").strip() if (pname or pcd) else ""
    if name:
        label_parts.append(str(name)[:80])
    label = " ".join(label_parts) if label_parts else f"ID {oid}"
    raise HTTPException(
        status_code=409,
        detail=f"同じ切断機で他の生産が進行中です（{label}）。完了するまで開始できません",
    )


_CHAMFERING_MGMT_MES_COLUMNS = _CUTTING_MGMT_MES_COLUMNS

_INSPECTION_MGMT_MES_COLUMNS = (
    "mes_production_started_at",
    "mes_production_ended_at",
    "mes_net_production_sec",
    "mes_paused_accum_sec",
    "mes_shift_sec",
    "mes_break_sec",
    "mes_stop_sec",
    "mes_production_is_paused",
    "mes_inspector_user_id",
    "mes_client_instance_id",
    "mes_client_lock_activity_at",
    "mes_defect_by_item",
)

# 検査系 checkpoint / ロック用の列存在チェック
INSPECTION_MES_CLIENT_LOCK_TTL_HOURS = 4

_INSPECTION_MGMT_META_COLUMNS = (
    "data_source",
    "external_sync_key",
    "manual_registration_note",
)

_WELDING_MGMT_MES_COLUMNS = (
    "mes_production_started_at",
    "mes_production_ended_at",
    "mes_net_production_sec",
    "mes_paused_accum_sec",
    "mes_shift_sec",
    "mes_break_sec",
    "mes_stop_sec",
    "mes_production_is_paused",
    "mes_operator_user_id",
    "mes_client_instance_id",
    "mes_defect_by_item",
)

_WELDING_MGMT_META_COLUMNS = (
    "data_source",
    "external_sync_key",
    "manual_registration_note",
)


async def _get_chamfering_mgmt_columns(db: AsyncSession) -> set[str]:
    """chamfering_management の既存列名を information_schema から取得"""
    try:
        result = await db.execute(
            text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'chamfering_management'
            """)
        )
        return {str(r[0]) for r in result.fetchall()}
    except Exception as e:
        logger.warning("chamfering_management column introspection failed: %s", e)
        return set()


def _chamfering_mgmt_mes_select_fragment(existing: set[str]) -> str:
    parts = [f"`chamfering_management`.`{c}`" for c in _CHAMFERING_MGMT_MES_COLUMNS if c in existing]
    return (",\n               ".join(parts) + ",") if parts else ""


def _chamfering_mes_column_migration_hint(column: str) -> str:
    return (
        f"列 `{column}` が未作成です。"
        "backend/database/migrations/08_chamfering_management_mes_fields.sql を実行してください。"
    )


async def _reject_concurrent_mes_production_on_chamfering_machine(
    db: AsyncSession,
    chamfering_id: int,
    cm_cols: set[str],
) -> None:
    """同一切断機で他行の MES 生産が未完了なら 409 を返す"""
    if "mes_production_started_at" not in cm_cols or "mes_production_ended_at" not in cm_cols:
        return
    scope = await db.execute(
        text("""
            SELECT chamfering_machine, production_day
            FROM chamfering_management
            WHERE id = :cid
            LIMIT 1
        """),
        {"cid": chamfering_id},
    )
    scope_row = scope.fetchone()
    if not scope_row or not scope_row[0] or scope_row[1] is None:
        return
    machine = str(scope_row[0]).strip()
    prod_day = scope_row[1]
    conflict = await db.execute(
        text("""
            SELECT id, production_sequence, product_name, product_cd
            FROM chamfering_management
            WHERE chamfering_machine = :machine
              AND production_day = :pday
              AND id <> :cid
              AND mes_production_started_at IS NOT NULL
              AND mes_production_ended_at IS NULL
            LIMIT 1
        """),
        {"cid": chamfering_id, "machine": machine, "pday": prod_day},
    )
    other = conflict.fetchone()
    if not other:
        return
    oid, pseq, pname, pcd = other[0], other[1], other[2], other[3]
    label_parts: list[str] = []
    if pseq is not None:
        label_parts.append(f"?{pseq}")
    name = (pname or pcd or "").strip() if (pname or pcd) else ""
    if name:
        label_parts.append(str(name)[:80])
    label = " ".join(label_parts) if label_parts else f"ID {oid}"
    raise HTTPException(
        status_code=409,
        detail=f"同じ切断機で他の生産が進行中です（{label}）。完了するまで開始できません",
    )


async def _reject_concurrent_mes_production_on_welding_machine(
    db: AsyncSession,
    welding_id: int,
    wm_cols: set[str],
    *,
    machine_hint: Optional[str] = None,
) -> None:
    """同一溶接設備で別行が MES 生産中なら 409"""
    if "welding_machine" not in wm_cols:
        return
    if "mes_production_started_at" not in wm_cols or "mes_production_ended_at" not in wm_cols:
        return
    scope = await db.execute(
        text("""
            SELECT welding_machine, production_day
            FROM welding_management
            WHERE id = :wid
            LIMIT 1
        """),
        {"wid": welding_id},
    )
    scope_row = scope.fetchone()
    if not scope_row or scope_row[1] is None:
        return
    machine = str(scope_row[0] or "").strip()
    if not machine and machine_hint:
        machine = str(machine_hint).strip()
    if not machine:
        return
    prod_day = scope_row[1]
    conflict = await db.execute(
        text("""
            SELECT id, production_sequence, product_name, product_cd
            FROM welding_management
            WHERE welding_machine = :machine
              AND production_day = :pday
              AND id <> :wid
              AND mes_production_started_at IS NOT NULL
              AND mes_production_ended_at IS NULL
            LIMIT 1
        """),
        {"wid": welding_id, "machine": machine, "pday": prod_day},
    )
    other = conflict.fetchone()
    if not other:
        return
    label = _welding_mes_conflict_label(other[0], other[1], other[2], other[3])
    raise HTTPException(
        status_code=409,
        detail=f"同じ倒角機で他の生産が進行中です（{label}）。完了するまで開始できません",
    )


async def _get_inspection_mgmt_columns(db: AsyncSession) -> set[str]:
    try:
        result = await db.execute(
            text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'inspection_management'
            """)
        )
        return {str(r[0]) for r in result.fetchall()}
    except Exception as e:
        logger.warning("inspection_management column introspection failed: %s", e)
        return set()


def _inspection_mgmt_mes_select_fragment(existing: set[str]) -> str:
    parts = [f"`inspection_management`.`{c}`" for c in _INSPECTION_MGMT_MES_COLUMNS if c in existing]
    return (",\n               ".join(parts) + ",") if parts else ""


def _inspection_mgmt_meta_select_fragment(existing: set[str]) -> str:
    parts = [f"inspection_management.{c}" for c in _INSPECTION_MGMT_META_COLUMNS if c in existing]
    return (",\n               ".join(parts) + ",") if parts else ""


def _normalize_inspection_mgmt_row(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    raw_def = out.get("mes_defect_by_item")
    if raw_def is not None and not isinstance(raw_def, dict):
        try:
            raw_def = json.loads(raw_def) if str(raw_def).strip() else None
        except json.JSONDecodeError:
            raw_def = None
    if isinstance(raw_def, dict):
        cleaned: dict[str, int] = {}
        for k, v in raw_def.items():
            if k is None:
                continue
            key = str(k).strip()
            if not key:
                continue
            qty: int | None = None
            if isinstance(v, dict):
                for qk in ("qty", "quantity", "count"):
                    qv = v.get(qk)
                    if qv is None:
                        continue
                    try:
                        qty = max(0, int(qv))
                        break
                    except (TypeError, ValueError):
                        continue
            elif v is not None:
                try:
                    qty = max(0, int(v))
                except (TypeError, ValueError):
                    qty = None
            if qty is not None and qty > 0:
                cleaned[key] = qty
        out["mes_defect_by_item"] = cleaned or None
    else:
        out["mes_defect_by_item"] = None
    for k in ("mes_production_started_at", "mes_production_ended_at", "created_at", "updated_at"):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    for k in ("production_month", "production_day"):
        v = out.get(k)
        if isinstance(v, date):
            out[k] = v.isoformat()
    out["data_source"] = resolve_data_source(
        out.get("data_source"),
        out.get("remarks"),
        out.get("external_sync_key"),
    )
    return out


def _normalize_welding_mgmt_row(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    raw_def = out.get("mes_defect_by_item")
    if raw_def is not None and not isinstance(raw_def, dict):
        try:
            out["mes_defect_by_item"] = json.loads(raw_def) if str(raw_def).strip() else None
        except json.JSONDecodeError:
            out["mes_defect_by_item"] = None
    for k in ("mes_production_started_at", "mes_production_ended_at", "created_at", "updated_at"):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    for k in ("production_month", "production_day"):
        v = out.get(k)
        if isinstance(v, date):
            out[k] = v.isoformat()
    out["data_source"] = resolve_data_source(
        out.get("data_source"),
        out.get("remarks"),
        out.get("external_sync_key"),
    )
    return out


def _build_inspection_productivity_session_row(
    item: dict[str, Any],
    *,
    net_sec: int,
    paused_sec: int,
    actual_qty: int,
    defect_qty: int,
    is_completed: bool,
) -> dict[str, Any]:
    """検査 API 向け: 不良項目 `**item` 列をパースして JSON / フラット形式に正規化"""
    inspector_id = item.get("mes_inspector_user_id")
    inspector_name = (item.get("mes_inspector_name") or item.get("mes_inspector_username") or "").strip()
    day_key = str(item.get("production_day") or "")[:10]
    row_id = item.get("id")
    return {
        "id": int(row_id) if row_id is not None else None,
        "production_day": day_key or None,
        "product_cd": (item.get("product_cd") or "").strip() or None,
        "product_name": (item.get("product_name") or "").strip() or None,
        "actual_production_quantity": actual_qty,
        "defect_qty": defect_qty,
        "mes_inspector_user_id": int(inspector_id) if inspector_id is not None else None,
        "mes_inspector_name": inspector_name or None,
        "mes_inspector_username": (item.get("mes_inspector_username") or "").strip() or None,
        "inspector_display_name": inspector_name or (f"ID:{inspector_id}" if inspector_id else "—"),
        "net_production_sec": int(net_sec),
        "paused_sec": int(paused_sec),
        "net_production_min": int(round(net_sec / 60)) if net_sec > 0 else 0,
        "paused_min": int(round(paused_sec / 60)) if paused_sec > 0 else 0,
        "efficiency_per_hour": _inspection_efficiency_per_hour(actual_qty, net_sec),
        "defect_rate_percent": _inspection_defect_rate_percent(actual_qty, defect_qty),
        "is_completed": is_completed,
    }


def _inspection_mes_column_migration_hint(column: str) -> str:
    if column == "mes_client_instance_id":
        return (
            f"列 `{column}` が未作成です。"
            "backend/database/migrations/12_inspection_management_mes_client_instance.sql を実行してください。"
        )
    if column == "mes_client_lock_activity_at":
        return (
            f"列 `{column}` が未作成です。"
            "backend/database/migrations/52_inspection_mes_client_lock_activity.sql を実行してください。"
        )
    return (
        f"列 `{column}` が未作成です。"
        "backend/database/migrations/09_inspection_management.sql を実行してください。"
    )


def _inspection_mgmt_inspector_select_fragment(join_inspector: bool, *, trailing_comma: bool = True) -> str:
    suffix = "," if trailing_comma else ""
    if join_inspector:
        return (
            "users.full_name AS mes_inspector_name,\n"
            f"               users.username AS mes_inspector_username{suffix}"
        )
    return (
        "NULL AS mes_inspector_name,\n"
        f"               NULL AS mes_inspector_username{suffix}"
    )


def _is_unknown_mysql_column_error(msg: str, column: str) -> bool:
    low = msg.lower()
    col = column.lower()
    if col not in low:
        return False
    return "unknown column" in low or "1054" in low


def _raise_inspection_mgmt_query_error(exc: Exception) -> None:
    msg = str(exc).lower()
    if "inspection_management" in msg and (
        "doesn't exist" in msg or "does not exist" in msg or "not exist" in msg or "unknown table" in msg
    ):
        raise HTTPException(
            status_code=503,
            detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
        ) from exc
    raw = str(exc)
    for col in _INSPECTION_MGMT_MES_COLUMNS:
        if _is_unknown_mysql_column_error(raw, col):
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint(col)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _parse_inspection_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _inspection_row_net_production_sec(item: dict[str, Any]) -> int:
    net = item.get("mes_net_production_sec")
    if isinstance(net, (int, float)) and net >= 0:
        return int(net)
    started = _parse_inspection_datetime(item.get("mes_production_started_at"))
    ended = _parse_inspection_datetime(item.get("mes_production_ended_at"))
    if started and ended:
        return max(0, int((ended - started).total_seconds()))
    return 0


def _welding_row_net_production_sec(item: dict[str, Any]) -> int:
    """溶接能率：actual_production_quantity / mes_net_production_sec（秒列のみ）"""
    net = item.get("mes_net_production_sec")
    if isinstance(net, (int, float)) and net > 0:
        return int(net)
    return 0


def _inspection_efficiency_per_hour(actual_qty: Any, net_sec: int) -> Optional[int]:
    actual = int(actual_qty or 0)
    if actual <= 0 or net_sec <= 0:
        return None
    hours = net_sec / 3600.0
    if hours <= 0:
        return None
    return round(actual / hours)


def _inspection_defect_rate_percent(actual_qty: Any, defect_qty: Any) -> Optional[float]:
    actual = int(actual_qty or 0)
    if actual <= 0:
        return None
    defect = int(defect_qty or 0)
    return round(defect / actual * 1000) / 10.0


def _merge_inspection_productivity_bucket(
    bucket: dict[str, Any],
    *,
    actual_qty: int,
    defect_qty: int,
    net_sec: int,
    session_count: int = 1,
    completed_count: int = 0,
) -> None:
    bucket["session_count"] = int(bucket.get("session_count") or 0) + session_count
    bucket["completed_session_count"] = int(bucket.get("completed_session_count") or 0) + completed_count
    bucket["sum_actual_qty"] = int(bucket.get("sum_actual_qty") or 0) + actual_qty
    bucket["sum_defect_qty"] = int(bucket.get("sum_defect_qty") or 0) + defect_qty
    bucket["sum_net_production_sec"] = int(bucket.get("sum_net_production_sec") or 0) + net_sec


def _finalize_inspection_productivity_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    actual = int(bucket.get("sum_actual_qty") or 0)
    defect = int(bucket.get("sum_defect_qty") or 0)
    net_sec = int(bucket.get("sum_net_production_sec") or 0)
    bucket["defect_rate_percent"] = _inspection_defect_rate_percent(actual, defect)
    bucket["efficiency_per_hour"] = _inspection_efficiency_per_hour(actual, net_sec)
    return bucket


INSPECTION_STANDARD_WORKDAY_HOURS = DEFAULT_INSPECTION_STANDARD_HOURS
INSPECTION_STANDARD_WORKDAY_SEC = DEFAULT_INSPECTION_STANDARD_SEC
INSPECTION_DEFECT_DETECTION_PROCESS_CD = "KT09"
WELDING_DEFECT_DETECTION_PROCESS_CD = "KT07"


def _norm_inspection_defect_name(value: Any) -> str:
    return str(value or "").strip().replace("\u3000", " ").replace(" ", "").lower()


def _build_inspector_metrics_defect_header_index() -> dict[str, str]:
    return {_norm_inspection_defect_name(header): header for header in INSPECTOR_METRICS_DEFECT_HEADERS}


async def _load_inspection_defect_cd_name_map(db: AsyncSession) -> dict[str, str]:
    try:
        result = await db.execute(
            text(
                """
                SELECT defect_cd, defect_name
                FROM process_defect_items
                WHERE detection_process_cd = :process_cd AND status = 'active'
                """
            ),
            {"process_cd": INSPECTION_DEFECT_DETECTION_PROCESS_CD},
        )
        return {str(row[0]).strip(): str(row[1] or "").strip() for row in result.fetchall()}
    except Exception:
        return {}


def _resolve_inspector_metrics_defect_header(
    defect_cd: str,
    *,
    cd_name_map: dict[str, str],
    header_index: dict[str, str],
) -> Optional[str]:
    cd = str(defect_cd or "").strip()
    if not cd:
        return None
    if cd.startswith("csv:"):
        raw = cd[4:].strip()
        nk = _norm_inspection_defect_name(raw)
        if nk in header_index:
            return header_index[nk]
        for nk_h, header in header_index.items():
            if nk_h in nk or nk in nk_h:
                return header
        return None
    name = cd_name_map.get(cd, cd)
    nk = _norm_inspection_defect_name(name)
    if nk in header_index:
        return header_index[nk]
    for nk_h, header in header_index.items():
        if nk_h in nk or nk in nk_h:
            return header
    return None


def _resolve_inspection_row_csv_time_secs(item: dict[str, Any], im_cols: set[str]) -> tuple[int, int, int, int]:
    work_sec = _inspection_row_net_production_sec(item)
    if "mes_shift_sec" in im_cols and item.get("mes_shift_sec") is not None:
        return (
            int(item.get("mes_shift_sec") or 0),
            int(item.get("mes_break_sec") or 0),
            int(item.get("mes_stop_sec") or 0),
            work_sec,
        )
    pause_sec = int(item.get("mes_paused_accum_sec") or 0)
    started = _parse_inspection_datetime(item.get("mes_production_started_at"))
    ended = _parse_inspection_datetime(item.get("mes_production_ended_at"))
    if started and ended:
        shift_sec = max(0, int((ended - started).total_seconds()))
    else:
        shift_sec = work_sec + pause_sec
    return shift_sec, 0, pause_sec, work_sec


def _format_inspector_display_name(full_name: str, username: str) -> str:
    return (full_name or "").strip()


def _new_inspector_metrics_bucket(
    *,
    inspector_user_id: Optional[int],
    inspector_name: str,
) -> dict[str, Any]:
    return {
        "inspector_user_id": inspector_user_id,
        "inspector_name": inspector_name,
        "defects": {header: 0 for header in INSPECTOR_METRICS_DEFECT_HEADERS},
        "sum_shift_sec": 0,
        "sum_break_sec": 0,
        "sum_stop_sec": 0,
        "sum_work_sec": 0,
        "sum_inspection_qty": 0,
    }


def _round_hours_from_sec(sec: int) -> float:
    return round(int(sec or 0) / 3600.0, 2)


def _round_efficiency_decimal(qty: int, work_sec: int) -> Optional[float]:
    work_h = int(work_sec or 0) / 3600.0
    if qty <= 0 or work_h <= 0:
        return None
    return round(qty / work_h * 10) / 10


def _finalize_inspector_metrics_row(row: dict[str, Any]) -> dict[str, Any]:
    shift_sec = int(row.get("sum_shift_sec") or 0)
    break_sec = int(row.get("sum_break_sec") or 0)
    stop_sec = int(row.get("sum_stop_sec") or 0)
    work_sec = int(row.get("sum_work_sec") or 0)
    qty = int(row.get("sum_inspection_qty") or 0)
    shift_h = shift_sec / 3600.0
    break_h = break_sec / 3600.0
    stop_h = stop_sec / 3600.0
    work_h = work_sec / 3600.0
    target_h = shift_h - break_h
    row["shift_hours"] = _round_hours_from_sec(shift_sec)
    row["break_hours"] = _round_hours_from_sec(break_sec)
    row["stop_hours"] = _round_hours_from_sec(stop_sec)
    row["target_work_hours"] = round(target_h, 2) if target_h > 0 else 0.0
    row["work_hours"] = _round_hours_from_sec(work_sec)
    row["work_rate_percent"] = round(work_h / target_h * 1000) / 10 if target_h > 0 else None
    row["sum_inspection_qty"] = qty
    row["efficiency_per_hour"] = _round_efficiency_decimal(qty, work_sec)
    row["operating_rate_percent"] = round(work_h / shift_h * 1000) / 10 if shift_h > 0 else None
    return row


def _build_inspector_metrics_total_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total: dict[str, Any] = {
        "inspector_name": "合計",
        "defects": {header: 0 for header in INSPECTOR_METRICS_DEFECT_HEADERS},
        "sum_shift_sec": 0,
        "sum_break_sec": 0,
        "sum_stop_sec": 0,
        "sum_work_sec": 0,
        "sum_inspection_qty": 0,
    }
    for row in rows:
        for header in INSPECTOR_METRICS_DEFECT_HEADERS:
            total["defects"][header] += int(row.get("defects", {}).get(header) or 0)
        total["sum_shift_sec"] += int(row.get("sum_shift_sec") or 0)
        total["sum_break_sec"] += int(row.get("sum_break_sec") or 0)
        total["sum_stop_sec"] += int(row.get("sum_stop_sec") or 0)
        total["sum_work_sec"] += int(row.get("sum_work_sec") or 0)
        total["sum_inspection_qty"] += int(row.get("sum_inspection_qty") or 0)
    finalized = _finalize_inspector_metrics_row(total)
    finalized["inspector_name"] = "合計"
    return finalized


def _apply_inspector_standard_to_daily_row(
    row: dict[str, Any],
    *,
    schedule_index: InspectorWorkScheduleIndex,
) -> None:
    day_key = str(row.get("day") or "")[:10]
    if not day_key:
        row["scheduled_hours"] = 0.0
        row["standard_sec"] = 0
        return
    day_d = date.fromisoformat(day_key)
    inspector_id = row.get("inspector_user_id")
    uid = int(inspector_id) if inspector_id is not None else None
    hours = schedule_index.resolve_hours(uid, day_d)
    is_scheduled = bool(row.get("is_scheduled_workday"))
    net = int(row.get("sum_net_production_sec") or 0)
    if is_scheduled or net > 0:
        row["scheduled_hours"] = hours
        row["standard_sec"] = int(round(hours * 3600))
    else:
        row["scheduled_hours"] = 0.0
        row["standard_sec"] = 0


def _split_utilization_sec(net_sec: int, standard_sec: int) -> tuple[int, int]:
    net = max(0, int(net_sec or 0))
    std = max(0, int(standard_sec or 0))
    if std <= 0:
        return net, 0
    regular = min(net, std)
    overtime = max(0, net - std)
    return regular, overtime


def _utilization_percent(regular_sec: int, standard_sec: int) -> Optional[float]:
    std = int(standard_sec or 0)
    if std <= 0:
        return None
    return round(int(regular_sec or 0) / std * 1000) / 10.0


def _finalize_inspection_utilization_daily_row(row: dict[str, Any]) -> dict[str, Any]:
    net = int(row.get("sum_net_production_sec") or 0)
    standard_sec = int(row.get("standard_sec") or 0)
    regular, overtime = _split_utilization_sec(net, standard_sec)
    row["sum_regular_sec"] = regular
    row["sum_overtime_sec"] = overtime
    row["sum_net_production_min"] = round(net / 60) if net > 0 else 0
    row["regular_min"] = round(regular / 60) if regular > 0 else 0
    row["overtime_min"] = round(overtime / 60) if overtime > 0 else 0
    row["utilization_percent"] = _utilization_percent(regular, standard_sec)
    row["load_percent"] = _utilization_percent(net, standard_sec)
    return row


def _finalize_inspection_utilization_inspector_row(
    row: dict[str, Any],
    *,
    schedule_index: InspectorWorkScheduleIndex,
    start_d: date,
    end_d: date,
    company_scheduled: set[str],
    company_off: set[str],
    extra_workdays: set[str],
    extra_holidays: set[str],
    daily_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    net = int(row.get("sum_net_production_sec") or 0)
    regular = int(row.get("sum_regular_sec") or 0)
    overtime = int(row.get("sum_overtime_sec") or 0)
    row["sum_net_production_min"] = round(net / 60) if net > 0 else 0
    row["regular_min"] = round(regular / 60) if regular > 0 else 0
    row["overtime_min"] = round(overtime / 60) if overtime > 0 else 0
    uid = row.get("inspector_user_id")
    uid_int = int(uid) if uid is not None else None
    std_worked = sum(
        int(r.get("standard_sec") or 0) for r in daily_rows if r.get("is_scheduled_workday")
    )
    std_calendar = 0
    for d in iter_dates_inclusive(start_d, end_d):
        if is_scheduled_workday(
            d,
            company_scheduled=company_scheduled,
            company_off=company_off,
            extra_workdays=extra_workdays,
            extra_holidays=extra_holidays,
        ):
            std_calendar += schedule_index.resolve_sec(uid_int, d)
    row["standard_sec_on_worked_days"] = std_worked
    row["standard_sec_calendar"] = std_calendar
    row["utilization_percent"] = _utilization_percent(regular, std_worked)
    row["calendar_utilization_percent"] = _utilization_percent(regular, std_calendar)
    ot_ratio = round(overtime / net * 1000) / 10.0 if net > 0 and overtime > 0 else None
    row["overtime_ratio_percent"] = ot_ratio
    return row


def _apply_operator_standard_to_daily_row(
    row: dict[str, Any],
    *,
    schedule_index: InspectorWorkScheduleIndex,
) -> None:
    day_key = str(row.get("day") or "")[:10]
    if not day_key:
        row["scheduled_hours"] = 0.0
        row["standard_sec"] = 0
        return
    day_d = date.fromisoformat(day_key)
    operator_id = row.get("operator_user_id")
    uid = int(operator_id) if operator_id is not None else None
    hours = schedule_index.resolve_hours(uid, day_d)
    is_scheduled = bool(row.get("is_scheduled_workday"))
    net = int(row.get("sum_net_production_sec") or 0)
    if is_scheduled or net > 0:
        row["scheduled_hours"] = hours
        row["standard_sec"] = int(round(hours * 3600))
    else:
        row["scheduled_hours"] = 0.0
        row["standard_sec"] = 0


def _finalize_welding_utilization_operator_row(
    row: dict[str, Any],
    *,
    schedule_index: InspectorWorkScheduleIndex,
    start_d: date,
    end_d: date,
    company_scheduled: set[str],
    company_off: set[str],
    extra_workdays: set[str],
    extra_holidays: set[str],
    daily_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    net = int(row.get("sum_net_production_sec") or 0)
    regular = int(row.get("sum_regular_sec") or 0)
    overtime = int(row.get("sum_overtime_sec") or 0)
    row["sum_net_production_min"] = round(net / 60) if net > 0 else 0
    row["regular_min"] = round(regular / 60) if regular > 0 else 0
    row["overtime_min"] = round(overtime / 60) if overtime > 0 else 0
    uid = row.get("operator_user_id")
    uid_int = int(uid) if uid is not None else None
    std_worked = sum(
        int(r.get("standard_sec") or 0) for r in daily_rows if r.get("is_scheduled_workday")
    )
    std_calendar = 0
    for d in iter_dates_inclusive(start_d, end_d):
        if is_scheduled_workday(
            d,
            company_scheduled=company_scheduled,
            company_off=company_off,
            extra_workdays=extra_workdays,
            extra_holidays=extra_holidays,
        ):
            std_calendar += schedule_index.resolve_sec(uid_int, d)
    row["standard_sec_on_worked_days"] = std_worked
    row["standard_sec_calendar"] = std_calendar
    row["utilization_percent"] = _utilization_percent(regular, std_worked)
    row["calendar_utilization_percent"] = _utilization_percent(regular, std_calendar)
    ot_ratio = round(overtime / net * 1000) / 10.0 if net > 0 and overtime > 0 else None
    row["overtime_ratio_percent"] = ot_ratio
    return row


def _merge_inspection_quality_bucket(
    bucket: dict[str, Any],
    *,
    actual_qty: int,
    defect_qty: int,
    session_count: int = 1,
    completed_count: int = 0,
    has_defect: bool = False,
) -> None:
    bucket["session_count"] = int(bucket.get("session_count") or 0) + session_count
    bucket["completed_session_count"] = int(bucket.get("completed_session_count") or 0) + completed_count
    bucket["sum_actual_qty"] = int(bucket.get("sum_actual_qty") or 0) + actual_qty
    bucket["sum_defect_qty"] = int(bucket.get("sum_defect_qty") or 0) + defect_qty
    if has_defect:
        bucket["sessions_with_defect_count"] = int(bucket.get("sessions_with_defect_count") or 0) + 1


def _finalize_inspection_quality_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    actual = int(bucket.get("sum_actual_qty") or 0)
    defect = int(bucket.get("sum_defect_qty") or 0)
    bucket["defect_rate_percent"] = _inspection_defect_rate_percent(actual, defect)
    return bucket


async def _load_process_defect_name_map(
    db: AsyncSession,
    detection_process_cd: str,
) -> dict[str, str]:
    """process_defect_items から defect_cd と defect_name を取得"""
    cd_norm = (detection_process_cd or "").strip()
    if not cd_norm:
        return {}
    try:
        result = await db.execute(
            select(ProcessDefectItem.defect_cd, ProcessDefectItem.defect_name).where(
                ProcessDefectItem.detection_process_cd == cd_norm,
                ProcessDefectItem.status == "active",
            )
        )
        out: dict[str, str] = {}
        for cd, name in result.all():
            key = str(cd or "").strip()
            if not key:
                continue
            label = str(name or "").strip()
            out[key] = label or key
        return out
    except Exception as e:
        logger.warning("process_defect_items load failed (%s): %s", cd_norm, e)
        return {}


def _defect_name_for_cd(defect_name_map: dict[str, str], defect_cd: str) -> str:
    cd = str(defect_cd or "").strip()
    if not cd:
        return "不明"
    return defect_name_map.get(cd) or cd


def _build_defect_breakdown_rows(
    defect_by_item: Optional[dict[str, Any]],
    defect_name_map: dict[str, str],
) -> list[dict[str, Any]]:
    if not defect_by_item:
        return []
    rows: list[dict[str, Any]] = []
    for defect_cd, qty_raw in defect_by_item.items():
        cd = str(defect_cd or "").strip()
        if not cd:
            continue
        qty = _mes_defect_item_qty(qty_raw)
        if qty <= 0:
            continue
        rows.append(
            {
                "defect_cd": cd,
                "defect_name": _defect_name_for_cd(defect_name_map, cd),
                "qty": qty,
            }
        )
    rows.sort(key=lambda x: (-int(x.get("qty") or 0), str(x.get("defect_cd") or "")))
    return rows


def _finalize_inspection_quality_defect_rows(
    defect_item_map: dict[str, int],
    *,
    total_actual: int,
    defect_name_map: dict[str, str],
) -> list[dict[str, Any]]:
    total_defect = sum(defect_item_map.values())
    rows = [{"defect_cd": cd, "qty": qty} for cd, qty in defect_item_map.items()]
    for row in rows:
        cd = str(row.get("defect_cd") or "").strip()
        qty = int(row["qty"] or 0)
        row["defect_name"] = _defect_name_for_cd(defect_name_map, cd)
        row["share_percent"] = round(qty / total_defect * 1000) / 10.0 if total_defect > 0 else None
        row["rate_per_actual_percent"] = (
            round(qty / total_actual * 1000) / 10.0 if total_actual > 0 else None
        )
    rows.sort(key=lambda x: (-int(x.get("qty") or 0), str(x.get("defect_cd") or "")))
    return rows


def _normalize_mes_client_instance_id(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    return s[:64]


def _inspection_mes_lock_activity_column(im_cols: set[str]) -> Optional[str]:
    if "mes_client_lock_activity_at" in im_cols:
        return "mes_client_lock_activity_at"
    return None


def _append_inspection_client_lock_activity_touch(
    updates: list[str],
    params: dict[str, Any],
    im_cols: set[str],
    *,
    at: Optional[datetime] = None,
) -> None:
    col = _inspection_mes_lock_activity_column(im_cols)
    if not col:
        return
    ts = at if at is not None else now_jst().replace(tzinfo=None)
    updates.append(f"{col} = :mes_client_lock_activity_at")
    params["mes_client_lock_activity_at"] = ts


async def _expire_stale_inspection_client_locks(
    db: AsyncSession,
    im_cols: set[str],
    *,
    production_day: Optional[Any] = None,
    inspection_id: Optional[int] = None,
) -> int:
    """checkpoint 更新時に mes_client_instance_id を必須化"""
    if "mes_client_instance_id" not in im_cols:
        return 0
    activity_col = _inspection_mes_lock_activity_column(im_cols) or "mes_production_started_at"
    threshold = now_jst().replace(tzinfo=None) - timedelta(hours=INSPECTION_MES_CLIENT_LOCK_TTL_HOURS)
    where_parts = [
        "mes_production_started_at IS NOT NULL",
        "(mes_production_ended_at IS NULL OR TRIM(COALESCE(CAST(mes_production_ended_at AS CHAR), '')) = '')",
        "mes_client_instance_id IS NOT NULL",
        "TRIM(mes_client_instance_id) <> ''",
        f"({activity_col} IS NULL OR {activity_col} < :lock_ttl_threshold)",
    ]
    params: dict[str, Any] = {"lock_ttl_threshold": threshold}
    if production_day is not None:
        where_parts.append("production_day = :production_day")
        params["production_day"] = production_day
    if inspection_id is not None:
        where_parts.append("id = :inspection_id")
        params["inspection_id"] = inspection_id
    clear_activity = ""
    if _inspection_mes_lock_activity_column(im_cols):
        clear_activity = ", mes_client_lock_activity_at = NULL"
    sql = (
        "UPDATE inspection_management "
        f"SET mes_client_instance_id = NULL{clear_activity} "
        f"WHERE {' AND '.join(where_parts)}"
    )
    try:
        result = await db.execute(text(sql), params)
        await db.commit()
        return int(result.rowcount or 0)
    except Exception:
        await db.rollback()
        return 0


def _inspection_row_mes_in_progress(started: Any, ended: Any) -> bool:
    if started is None or not str(started).strip():
        return False
    if ended is None or not str(ended).strip():
        return True
    return False


def _inspection_row_mes_completed(started: Any, ended: Any) -> bool:
    if started is None or not str(started).strip():
        return False
    if ended is None or not str(ended).strip():
        return False
    return True


async def _fetch_inspection_row_mes_state(
    db: AsyncSession,
    inspection_id: int,
    im_cols: set[str],
) -> dict[str, Any]:
    select_cols = ["mes_production_started_at", "mes_production_ended_at"]
    if "mes_client_instance_id" in im_cols:
        select_cols.append("mes_client_instance_id")
    sql = (
        f"SELECT {', '.join(select_cols)} FROM inspection_management WHERE id = :iid LIMIT 1"
    )
    result = await db.execute(text(sql), {"iid": inspection_id})
    row = result.mappings().first()
    return dict(row) if row else {}


def _reject_inspection_mes_client_lock_conflict(
    existing_lock: Optional[str],
    client_id: Optional[str],
    *,
    force_release: bool,
) -> None:
    if not existing_lock or not client_id or existing_lock == client_id or force_release:
        return
    raise HTTPException(
        status_code=409,
        detail="待発行または発行済のカンバンのみ再発行できます（完了済は再発行不可）",
    )


def _inspection_mes_inspector_user_id_from_user(current_user: User) -> int:
    uid = getattr(current_user, "id", None)
    if uid is None:
        raise HTTPException(status_code=400, detail="生産日の形式が不正です")
    return int(uid)


def _reject_inspection_mes_inspector_not_current_user(
    current_user: User,
    inspector_user_id: Optional[int],
) -> None:
    if inspector_user_id is None:
        return
    try:
        iid = int(inspector_user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="mes_inspector_user_id が未設定です")
    if iid <= 0:
        return
    if iid != _inspection_mes_inspector_user_id_from_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="待発行または発行済のカンバンのみ再発行できます（完了済は再発行不可）",
        )


async def _fetch_inspection_row_mes_inspector(
    db: AsyncSession,
    inspection_id: int,
    im_cols: set[str],
) -> Optional[int]:
    if "mes_inspector_user_id" not in im_cols:
        return None
    result = await db.execute(
        text("SELECT mes_inspector_user_id FROM inspection_management WHERE id = :iid LIMIT 1"),
        {"iid": inspection_id},
    )
    val = result.scalar()
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _inspection_mes_row_mutation_requested(body: "UpdateInspectionManagementBody") -> bool:
    return (
        body.mes_production_started_at is not None
        or body.mes_production_ended_at is not None
        or body.mes_net_production_sec is not None
        or body.mes_paused_accum_sec is not None
        or body.mes_break_sec is not None
        or body.mes_stop_sec is not None
        or body.mes_production_is_paused is not None
        or body.mes_defect_by_item is not None
        or body.mes_inspector_user_id is not None
        or body.mes_claim_client_lock
        or body.production_completed_check is not None
        or body.actual_production_quantity is not None
        or body.defect_qty is not None
    )


def _inspection_mes_conflict_label(
    oid: int,
    pseq: Any,
    pname: Any,
    pcd: Any,
) -> str:
    label_parts: list[str] = []
    if pseq is not None:
        label_parts.append(f"?{pseq}")
    name = (pname or pcd or "").strip() if (pname or pcd) else ""
    if name:
        label_parts.append(str(name)[:80])
    return " ".join(label_parts) if label_parts else f"ID {oid}"


async def _reject_concurrent_mes_production_on_inspection_start(
    db: AsyncSession,
    inspection_id: int,
    im_cols: set[str],
    *,
    inspector_user_id: Optional[int] = None,
) -> None:
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    if "mes_production_started_at" not in im_cols or "mes_production_ended_at" not in im_cols:
        return
    need_inspector_col = inspector_user_id is not None and inspector_user_id > 0
    if need_inspector_col and "mes_inspector_user_id" not in im_cols:
        need_inspector_col = False

    scope = await db.execute(
        text("""
            SELECT production_day, product_cd, mes_inspector_user_id
            FROM inspection_management
            WHERE id = :iid
            LIMIT 1
        """),
        {"iid": inspection_id},
    )
    scope_row = scope.fetchone()
    if not scope_row or scope_row[0] is None:
        return
    prod_day = scope_row[0]
    row_inspector = scope_row[2]
    effective_inspector = inspector_user_id if inspector_user_id and inspector_user_id > 0 else row_inspector

    if need_inspector_col and effective_inspector:
        inspector_conflict = await db.execute(
            text("""
                SELECT id, production_sequence, product_name, product_cd
                FROM inspection_management
                WHERE production_day = :pday
                  AND mes_inspector_user_id = :inspector
                  AND id <> :iid
                  AND mes_production_started_at IS NOT NULL
                  AND mes_production_ended_at IS NULL
                LIMIT 1
            """),
            {
                "iid": inspection_id,
                "pday": prod_day,
                "inspector": int(effective_inspector),
            },
        )
        other = inspector_conflict.fetchone()
        if other:
            label = _inspection_mes_conflict_label(other[0], other[1], other[2], other[3])
            raise HTTPException(
                status_code=409,
                detail=f"同じ検査ラインで他の作業が進行中です（{label}）。完了するまで開始できません",
            )


async def _get_welding_mgmt_columns(db: AsyncSession) -> set[str]:
    try:
        result = await db.execute(
            text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'welding_management'
            """)
        )
        return {str(r[0]) for r in result.fetchall()}
    except Exception as e:
        logger.warning("welding_management column introspection failed: %s", e)
        return set()


def _welding_mgmt_mes_select_fragment(existing: set[str]) -> str:
    parts = [f"`welding_management`.`{c}`" for c in _WELDING_MGMT_MES_COLUMNS if c in existing]
    return (",\n               ".join(parts) + ",") if parts else ""


def _welding_mgmt_meta_select_fragment(existing: set[str]) -> str:
    parts = [f"welding_management.{c}" for c in _WELDING_MGMT_META_COLUMNS if c in existing]
    return (",\n               ".join(parts) + ",") if parts else ""


def _welding_mes_row_mutation_requested(body: "UpdateWeldingManagementBody") -> bool:
    return (
        body.mes_production_started_at is not None
        or body.mes_production_ended_at is not None
        or body.mes_net_production_sec is not None
        or body.mes_paused_accum_sec is not None
        or body.mes_break_sec is not None
        or body.mes_stop_sec is not None
        or body.mes_production_is_paused is not None
        or body.mes_defect_by_item is not None
        or body.mes_operator_user_id is not None
        or body.mes_claim_client_lock
        or body.production_completed_check is not None
        or body.actual_production_quantity is not None
        or body.defect_qty is not None
    )


def _welding_mgmt_operator_select_fragment(join_operator: bool, *, trailing_comma: bool = True) -> str:
    suffix = "," if trailing_comma else ""
    if join_operator:
        return (
            "users.full_name AS mes_operator_name,\n"
            f"               users.username AS mes_operator_username{suffix}"
        )
    return (
        "NULL AS mes_operator_name,\n"
        f"               NULL AS mes_operator_username{suffix}"
    )


def _raise_welding_mgmt_query_error(exc: Exception) -> None:
    msg = str(exc).lower()
    if "welding_management" in msg and (
        "doesn't exist" in msg or "does not exist" in msg or "not exist" in msg or "unknown table" in msg
    ):
        raise HTTPException(
            status_code=503,
            detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
        ) from exc
    raw = str(exc)
    for col in _WELDING_MGMT_MES_COLUMNS:
        if _is_unknown_mysql_column_error(raw, col):
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint(col)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _welding_mes_column_migration_hint(column: str) -> str:
    return (
        f"列 `{column}` が未作成です。"
        "backend/database/migrations/13_welding_management.sql を実行してください。"
    )


def _normalize_mes_client_instance_id(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    return s[:64]


def _welding_row_mes_in_progress(started: Any, ended: Any) -> bool:
    if started is None or not str(started).strip():
        return False
    if ended is None or not str(ended).strip():
        return True
    return False


async def _fetch_welding_row_mes_state(
    db: AsyncSession,
    welding_id: int,
    im_cols: set[str],
) -> dict[str, Any]:
    select_cols = ["mes_production_started_at", "mes_production_ended_at"]
    if "mes_client_instance_id" in im_cols:
        select_cols.append("mes_client_instance_id")
    sql = (
        f"SELECT {', '.join(select_cols)} FROM welding_management WHERE id = :wid LIMIT 1"
    )
    result = await db.execute(text(sql), {"wid": welding_id})
    row = result.mappings().first()
    return dict(row) if row else {}


def _reject_welding_mes_client_lock_conflict(
    existing_lock: Optional[str],
    client_id: Optional[str],
    *,
    force_release: bool,
) -> None:
    if not existing_lock or not client_id or existing_lock == client_id or force_release:
        return
    raise HTTPException(
        status_code=409,
        detail="待発行または発行済のカンバンのみ再発行できます（完了済は再発行不可）",
    )


def _welding_mes_conflict_label(
    oid: int,
    pseq: Any,
    pname: Any,
    pcd: Any,
) -> str:
    label_parts: list[str] = []
    if pseq is not None:
        label_parts.append(f"?{pseq}")
    name = (pname or pcd or "").strip() if (pname or pcd) else ""
    if name:
        label_parts.append(str(name)[:80])
    return " ".join(label_parts) if label_parts else f"ID {oid}"


async def _reject_concurrent_mes_production_on_welding_start(
    db: AsyncSession,
    welding_id: int,
    im_cols: set[str],
    *,
    operator_user_id: Optional[int] = None,
) -> None:
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    if "mes_production_started_at" not in im_cols or "mes_production_ended_at" not in im_cols:
        return
    need_operator_col = operator_user_id is not None and operator_user_id > 0
    if need_operator_col and "mes_operator_user_id" not in im_cols:
        need_operator_col = False

    scope = await db.execute(
        text("""
            SELECT production_day, product_cd, mes_operator_user_id
            FROM welding_management
            WHERE id = :wid
            LIMIT 1
        """),
        {"wid": welding_id},
    )
    scope_row = scope.fetchone()
    if not scope_row or scope_row[0] is None:
        return
    prod_day = scope_row[0]
    row_operator = scope_row[2]
    effective_operator = operator_user_id if operator_user_id and operator_user_id > 0 else row_operator

    if need_operator_col and effective_operator:
        operator_conflict = await db.execute(
            text("""
                SELECT id, production_sequence, product_name, product_cd
                FROM welding_management
                WHERE production_day = :pday
                  AND mes_operator_user_id = :operator
                  AND id <> :wid
                  AND mes_production_started_at IS NOT NULL
                  AND mes_production_ended_at IS NULL
                LIMIT 1
            """),
            {
                "wid": welding_id,
                "pday": prod_day,
                "operator": int(effective_operator),
            },
        )
        other = operator_conflict.fetchone()
        if other:
            label = _welding_mes_conflict_label(other[0], other[1], other[2], other[3])
            raise HTTPException(
                status_code=409,
                detail=f"同じ溶接機で他の生産が進行中です（{label}）。完了するまで開始できません",
            )


def _parse_mes_defect_entry(val: Any) -> tuple[int, Optional[str]]:
    """切断指示1件を生産ロットへ戻すリクエスト"""
    if isinstance(val, dict):
        qty_raw = val.get("qty", val.get("quantity", val.get("count", 0)))
        try:
            qty = max(0, int(qty_raw))
        except (TypeError, ValueError):
            qty = 0
        at_raw = val.get("at") or val.get("occurred_at") or val.get("occurredAt")
        at = str(at_raw).strip() if at_raw is not None and str(at_raw).strip() else None
        return qty, at
    try:
        return max(0, int(val)), None
    except (TypeError, ValueError):
        return 0, None


def _mes_defect_item_qty(val: Any) -> int:
    """mes_defect_by_item の各項目値（数値または {qty, at}）から数量を取得"""
    qty, _ = _parse_mes_defect_entry(val)
    return qty


def _parse_mes_defect_by_item_for_db(val: Any) -> Optional[str]:
    """dict / JSON 文字列を MySQL JSON カラム用に正規化"""
    if val is None:
        return None
    if isinstance(val, dict):
        cleaned: dict[str, Any] = {}
        for k, v in val.items():
            if not k:
                continue
            qty, at = _parse_mes_defect_entry(v)
            if qty <= 0:
                continue
            cleaned[str(k)] = {"qty": qty, "at": at} if at else qty
        return json.dumps(cleaned, ensure_ascii=False) if cleaned else None
    if isinstance(val, str):
        raw = val.strip()
        if not raw:
            return None
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("mes_defect_by_item must be a JSON object")
        return _parse_mes_defect_by_item_for_db(parsed)
    raise ValueError("mes_defect_by_item must be object or JSON string")


def _sum_defect_qty_from_item_json(raw: Any) -> int:
    if raw is None:
        return 0
    try:
        if isinstance(raw, str):
            data = json.loads(raw) if raw.strip() else {}
        elif isinstance(raw, dict):
            data = raw
        else:
            return 0
        if not isinstance(data, dict):
            return 0
        total = 0
        for v in data.values():
            qty, _ = _parse_mes_defect_entry(v)
            total += qty
        return total
    except (TypeError, ValueError, json.JSONDecodeError):
        return 0


def _parse_mes_datetime_to_naive_tokyo(val: Optional[str]) -> Optional[datetime]:
    """ISO 8601 文字列を Asia/Tokyo として解釈し、naive な MySQL DATETIME 文字列へ変換"""
    if val is None:
        return None
    s = (val or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(_tokyo_tzinfo()).replace(tzinfo=None)
    return dt


_WELDING_USE_DRIVER_SQL = "(COALESCE(ps.welding_actual, 0) + COALESCE(ps.welding_defect, 0))"


def _plan_column_sql_expr(plan_column: str) -> tuple[str, str]:
    col = (plan_column or "molding_actual_plan").strip()
    if col not in _COMPONENT_REQUIREMENTS_PLAN_COLUMNS:
        allowed = ", ".join(sorted(_COMPONENT_REQUIREMENTS_PLAN_COLUMNS))
        raise HTTPException(status_code=400, detail=f"plan_column は次のいずれかです: {allowed}")
    expr = f"COALESCE(ps.{col}, 0)"
    labels = {
        "molding_actual_plan": "molding_actual_plan（成型実績計画）",
        "molding_plan": "molding_plan（成型計画）",
    }
    return expr, labels[col]


def _mysql_lpad(value: Any, length: int, pad: str = "0") -> str:
    """MySQL LPAD と同等（長い場合は左から切り詰める）。"""
    s = "" if value is None else str(value)
    if length <= 0:
        return ""
    if len(s) >= length:
        return s[:length]
    return (pad * (length - len(s))) + s


def _build_management_code(
    production_month: Optional[date],
    product_cd: str,
    production_line: str,
    priority_order: Optional[int],
    production_lot_size: Optional[int],
    lot_number: Optional[str],
) -> str:
    """management_code のサーバ側兜底計算（DB trigger 未適用環境向け）。"""
    pm = production_month or date.today()
    yy = f"{pm.year % 100:02d}"
    mm = f"{pm.month:02d}"
    cd = (product_cd or "").strip()
    line_suffix = (production_line or "")[-2:]
    po2 = _mysql_lpad(int(priority_order or 0), 2, "0")
    pls2 = _mysql_lpad(int(production_lot_size or 0), 2, "0")
    ln2 = _mysql_lpad((lot_number or "").strip(), 2, "0")
    return f"{yy}{mm}{cd}{line_suffix}{po2}-{pls2}-{ln2}"


def _instruction_production_month_first_day(value: Any, body_month: str) -> date:
    """instruction_plans.production_month は月初日。DB 値・YYYY-MM 文字列から正規化する。"""
    if value is not None:
        if isinstance(value, datetime):
            d = value.date()
            return date(d.year, d.month, 1)
        if isinstance(value, date):
            return date(value.year, value.month, 1)
        s = str(value).strip()[:10]
        if len(s) >= 10:
            try:
                d = date.fromisoformat(s)
                return date(d.year, d.month, 1)
            except ValueError:
                pass
    bm = (body_month or "").strip()
    parts = bm.split("-")
    if len(parts) >= 2:
        try:
            y, mo = int(parts[0]), int(parts[1])
            if 1 <= mo <= 12:
                return date(y, mo, 1)
        except ValueError:
            pass
    return date.today()


async def _aggregate_component_requirements_from_production_summarys(
    db: AsyncSession,
    d_start: date,
    d_end: date,
    driver_sql_expr: str,
    effective_date_note: str,
    production_month_filter: Optional[str],
) -> dict[str, Any]:
    """
    production_summarys × 明細 BOM で部品所要を集計。driver_sql_expr はサーバ側定数のみ（ユーザー入力不可）。
    """
    conditions = [
        "ps.date >= :d_start",
        "ps.date <= :d_end",
    ]
    params: dict = {"d_start": d_start, "d_end": d_end}

    sql = text(f"""
        SELECT
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)') AS component_cd,
            COALESCE(NULLIF(TRIM(p.part_name), ''), '') AS component_name,
            COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個')) AS component_uom,
            COUNT(DISTINCT ps.id) AS source_lot_count,
            SUM(
                ({driver_sql_expr})
                * COALESCE(l.qty_per, 0)
                / NULLIF(COALESCE(h.base_quantity, 1), 0)
                * (1 + COALESCE(l.scrap_rate, 0) / 100)
            ) AS required_qty
        FROM production_summarys ps
        JOIN product_bom_headers h
          ON h.id = (
              SELECT h2.id
              FROM product_bom_headers h2
              WHERE h2.parent_product_cd = ps.product_cd
                AND h2.status = 'active'
                AND (h2.effective_from IS NULL OR h2.effective_from <= ps.date)
                AND (h2.effective_to IS NULL OR h2.effective_to >= ps.date)
              ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
              LIMIT 1
          )
        JOIN product_bom_lines l
          ON l.header_id = h.id
         AND l.component_product_cd IS NOT NULL
         AND TRIM(l.component_product_cd) <> ''
         AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
        LEFT JOIN parts p
          ON p.part_cd = l.component_product_cd
        WHERE {" AND ".join(conditions)}
        GROUP BY
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)'),
            COALESCE(NULLIF(TRIM(p.part_name), ''), ''),
            COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個'))
        ORDER BY component_cd ASC
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "production_summarys" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="production_summarys テーブルが存在しません。",
            ) from e
        if "product_bom_headers" in msg or "product_bom_lines" in msg:
            raise HTTPException(
                status_code=503,
                detail="product_bom_headers / product_bom_lines テーブルが存在しないため集計できません。",
            ) from e
        logger.exception("component-requirements aggregate failed")
        raise HTTPException(status_code=500, detail="部品需要量の集計に失敗しました。") from e

    def _fnum(v) -> float:
        if v is None:
            return 0.0
        if isinstance(v, Decimal):
            return float(v)
        return float(v)

    def _inum(v) -> int:
        if v is None:
            return 0
        if isinstance(v, Decimal):
            return int(v)
        return int(v)

    items = []
    total_required_qty = 0.0
    for r in rows:
        rd = dict(r)
        rq = _fnum(rd.get("required_qty"))
        total_required_qty += rq
        items.append(
            {
                "component_cd": rd.get("component_cd"),
                "component_name": rd.get("component_name"),
                "component_uom": rd.get("component_uom"),
                "source_lot_count": _inum(rd.get("source_lot_count")),
                "required_qty": round(rq, 6),
            }
        )

    _DAY_MATRIX_MAX_DAYS = 186
    span_days = (d_end - d_start).days + 1
    daily_matrix: Optional[dict] = None
    daily_matrix_omitted = span_days > _DAY_MATRIX_MAX_DAYS

    if not daily_matrix_omitted:
        dsql = text(f"""
            SELECT
                ps.date AS eff_date,
                COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)') AS component_cd,
                COALESCE(NULLIF(TRIM(p.part_name), ''), '') AS component_name,
                COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個')) AS component_uom,
                SUM(
                    ({driver_sql_expr})
                    * COALESCE(l.qty_per, 0)
                    / NULLIF(COALESCE(h.base_quantity, 1), 0)
                    * (1 + COALESCE(l.scrap_rate, 0) / 100)
                ) AS required_qty
            FROM production_summarys ps
            JOIN product_bom_headers h
              ON h.id = (
                  SELECT h2.id
                  FROM product_bom_headers h2
                  WHERE h2.parent_product_cd = ps.product_cd
                    AND h2.status = 'active'
                    AND (h2.effective_from IS NULL OR h2.effective_from <= ps.date)
                    AND (h2.effective_to IS NULL OR h2.effective_to >= ps.date)
                  ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
                  LIMIT 1
              )
            JOIN product_bom_lines l
              ON l.header_id = h.id
             AND l.component_product_cd IS NOT NULL
             AND TRIM(l.component_product_cd) <> ''
             AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
            LEFT JOIN parts p
              ON p.part_cd = l.component_product_cd
            WHERE {" AND ".join(conditions)}
            GROUP BY
                ps.date,
                COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)'),
                COALESCE(NULLIF(TRIM(p.part_name), ''), ''),
                COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個'))
            ORDER BY
                ps.date ASC,
                component_cd ASC
        """)
        dresult = await db.execute(dsql, params)
        drows = dresult.mappings().fetchall()

        date_list = [(d_start + timedelta(days=i)).isoformat() for i in range(span_days)]
        pivot: dict[tuple, dict[str, float]] = {}
        for r in drows:
            rd = dict(r)
            ed = rd.get("eff_date")
            if ed is None:
                continue
            if hasattr(ed, "isoformat"):
                ds = ed.isoformat()[:10]
            else:
                ds = str(ed)[:10]
            key = (
                rd.get("component_cd"),
                rd.get("component_name"),
                rd.get("component_uom"),
            )
            if key not in pivot:
                pivot[key] = {d: 0.0 for d in date_list}
            qv = _fnum(rd.get("required_qty"))
            if ds in pivot[key]:
                pivot[key][ds] += qv

        for it in items:
            k = (it.get("component_cd"), it.get("component_name"), it.get("component_uom"))
            if k not in pivot:
                pivot[k] = {d: 0.0 for d in date_list}

        matrix_rows = []
        for key in sorted(pivot.keys(), key=lambda k: (k[0] or "", k[1] or "", k[2] or "")):
            cc, cn, cu = key
            by_date = pivot[key]
            row_total = sum(by_date.values())
            matrix_rows.append(
                {
                    "component_cd": cc,
                    "component_name": cn,
                    "component_uom": cu,
                    "by_date": {d: round(by_date[d], 6) for d in date_list},
                    "row_total": round(row_total, 6),
                }
            )

        daily_matrix = {
            "dates": date_list,
            "rows": matrix_rows,
        }

    return {
        "items": items,
        "daily_matrix": daily_matrix,
        "summary": {
            "date_start": d_start.isoformat(),
            "date_end": d_end.isoformat(),
            "production_month_filter": production_month_filter.strip() if production_month_filter and production_month_filter.strip() else None,
            "total_component_kinds": len(items),
            "total_required_qty": round(total_required_qty, 6),
            "effective_date_note": effective_date_note,
            "daily_matrix_omitted": daily_matrix_omitted,
            "daily_matrix_max_days": _DAY_MATRIX_MAX_DAYS,
        },
    }


async def _table_has_column(db: AsyncSession, table_name: str, column_name: str) -> bool:
    """現在の DB でテーブルが指定列を持つか（MySQL information_schema）。照会不可時は False（安全側の SQL にフォールバック）。"""
    try:
        r = await db.execute(
            text(
                """
                SELECT 1 FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table_name
                  AND COLUMN_NAME = :column_name
                LIMIT 1
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        )
        return r.first() is not None
    except Exception as e:
        logger.warning(
            "information_schema 照会失敗 (%s.%s): %s",
            table_name,
            column_name,
            e,
        )
        return False


class GenerateFromScheduleBody(BaseModel):
    month: str  # YYYY-MM e.g. "2025-01"


def _schedule_row_to_dict(row) -> dict:
    """production_plan_schedules 1行を辞書に（frontend の machine_name, product_name, production_order, planned_quantity 等）"""
    def _v(key, default=None):
        val = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val) if val is not None else default
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10] if val else default
        return val

    return {
        "id": _v("id"),
        "file_name": _v("file_name"),
        "machine_name": _v("machine_name"),
        "product_name": _v("product_name"),
        "production_order": _v("production_order"),
        "planned_quantity": _v("planned_quantity"),
        "production_start_date": _v("production_start_date"),
        "production_end_date": _v("production_end_date"),
        "actual_production": _v("actual_production"),
        "variance": _v("variance"),
        "achievement_rate": _v("achievement_rate"),
        "total_production_time": _v("total_production_time"),
        "operation_variance": _v("operation_variance"),
        "material_lot_count": _v("material_lot_count"),
        "material_name": _v("material_name"),
    }


@router.get("/processing-status")
async def get_processing_status(
    fileName: Optional[str] = Query(None, description="file_name に含まれる文字（例: 1月 → 加工計画(1月).xlsm）"),
    limit: int = Query(100000, ge=1, le=100000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_plan_schedules を取得。段取予定発行で利用。
    fileName で file_name を LIKE 検索（例: "1月" で 1月 を含むファイルのレコードのみ）。
    """
    if not fileName or not fileName.strip():
        return {"success": True, "data": [], "message": "OK"}

    sql = text("""
        SELECT id, file_name, processed_at, machine_name, product_name, production_order,
               planned_quantity, production_start_date, production_end_date,
               actual_production, variance, achievement_rate, total_production_time,
               operation_variance, material_lot_count, material_name
        FROM production_plan_schedules
        WHERE file_name LIKE :pattern
        ORDER BY machine_name, product_name, production_order
        LIMIT :limit
    """)
    pattern = f"%{fileName.strip()}%"
    result = await db.execute(sql, {"pattern": pattern, "limit": limit})
    rows = result.mappings().fetchall()
    data = [_schedule_row_to_dict(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/operation-rate")
async def get_operation_rate(
    fileName: Optional[str] = Query(None, description="file_name に含まれる文字（例: 1月）。操業度は machine_name で紐づく"),
    limit: int = Query(10000, ge=1, le=100000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_plan_rate を取得。段取予定発行の操業度列用。
    fileName で file_name を LIKE 検索。同一 machine_name が複数ある場合は先頭を採用（必要なら集約可）。
    """
    if not fileName or not fileName.strip():
        return {"success": True, "data": [], "message": "OK"}

    sql = text("""
        SELECT id, file_name, machine_cd, machine_name, operation_variance
        FROM production_plan_rate
        WHERE file_name LIKE :pattern
        ORDER BY machine_name
        LIMIT :limit
    """)
    pattern = f"%{fileName.strip()}%"
    result = await db.execute(sql, {"pattern": pattern, "limit": limit})
    rows = result.mappings().fetchall()

    def _row_to_dict(r):
        row = dict(r)
        def _v(k, default=None):
            val = row.get(k)
            if val is None:
                return default
            if isinstance(val, Decimal):
                return float(val)
            if hasattr(val, "isoformat"):
                return val.isoformat()[:10] if val else default
            return val
        return {
            "machine_cd": _v("machine_cd"),
            "machine_name": _v("machine_name"),
            "operation_variance": _v("operation_variance"),
        }

    data = [_row_to_dict(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/schedule")
async def get_schedule(
    machine_cd: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    設備運行時間スロット取得。frontend は start_time / end_time を期待。
    production_plan_schedules には開始/終了時刻がないため、現状は空リストを返す。
    必要に応じて他テーブルや計算で導出可能。
    """
    # スタブ: 空リストで 404 を避ける
    return {"success": True, "data": {"list": []}, "message": "OK"}


def _mes_schedule_plan_row_to_record(row: Any) -> dict:
    """schedule_details × production_schedules × machines → excel-monitor plan-data 互換1件"""
    def _val(key: str, default=None):
        v = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
        if v is None:
            return default
        if isinstance(v, Decimal):
            return float(v) if v is not None else default
        return v

    plan_date = _val("plan_date")
    if hasattr(plan_date, "isoformat"):
        plan_date = plan_date.isoformat()[:10] if plan_date else None
    op = _val("operator")
    if op is not None and not isinstance(op, str):
        op = str(op)
    eff = _val("efficiency_rate")
    st = _val("setup_time")
    if st is not None:
        try:
            st = int(st)
        except (TypeError, ValueError):
            st = None
    qty = _val("quantity", 0)
    try:
        qty = int(qty) if qty is not None else 0
    except (TypeError, ValueError):
        qty = 0
    return {
        "id": _val("id"),
        "schedule_id": _val("schedule_id"),
        "file_name": _val("file_name"),
        "plan_date": plan_date,
        "quantity": qty,
        "planned_quantity": qty,
        "planned_output_qty": _val("planned_output_qty", qty),
        "machine_name": _val("machine_name"),
        "machine_cd": _val("machine_cd"),
        "process_name": _val("process_name") or "成型",
        "operator": op,
        "production_order": op,
        "product_name": _val("product_name") or "",
        "product_cd": _val("product_cd"),
        "efficiency_rate": eff,
        "setup_time": st,
        "actual_production": _val("actual_production", 0),
        "actual_qty": _val("actual_production", 0),
        "defect_qty": _val("defect_qty", 0),
        "upstream_defect_qty_total": _val("upstream_defect_qty_total", 0),
        "remarks": _val("remarks") or "",
    }


@router.get("/mes/forming-plan-data")
async def get_mes_forming_plan_data_from_schedule(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    processName: Optional[str] = Query(None),
    machineName: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    productNameExact: Optional[str] = Query(
        None,
        description="品名または product_cd と完全一致",
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    MES 成型指示用: production_schedules と schedule_details を結合し、
    /api/excel-monitor/plan-data と同形の records を返す（設備は machine_type=成型）。
    能率(efficiency_rate)は equipment_efficiency（machine_cd + product_cd）を優先。
    """
    if not startDate or not endDate:
        return {
            "success": True,
            "data": {"records": [], "total": 0},
            "message": "OK",
        }
    pn = (processName or "").strip()
    process_label = pn if pn in ("成型", "溶接") else "成型"
    kw = keyword.strip() if keyword else ""
    pne = (productNameExact or "").strip() or None
    offset = (page - 1) * limit
    params = {
        "start_date": startDate,
        "end_date": endDate,
        "machine_name": (machineName or "").strip() or None,
        "process_label": process_label,
        "pne": pne,
        "keyword": kw or None,
        "kw_like": f"%{kw}%" if kw else "%",
        "limit": limit,
        "offset": offset,
    }
    base_where = """
        sd.schedule_date BETWEEN :start_date AND :end_date
        AND m.machine_type = :process_label
        AND (:machine_name IS NULL OR m.machine_name = :machine_name)
        AND (
            :pne IS NULL
            OR ps.item_name = :pne
            OR ps.product_cd = :pne
        )
        AND (
            :keyword IS NULL OR :keyword = ''
            OR ps.item_name LIKE :kw_like
            OR ps.product_cd LIKE :kw_like
            OR m.machine_name LIKE :kw_like
        )
    """
    count_sql = text(f"SELECT COUNT(*) AS cnt FROM schedule_details sd INNER JOIN production_schedules ps ON ps.id = sd.schedule_id INNER JOIN machines m ON m.id = ps.line_id WHERE {base_where}")
    count_keys = (
        "start_date",
        "end_date",
        "machine_name",
        "process_label",
        "pne",
        "keyword",
        "kw_like",
    )
    count_result = await db.execute(count_sql, {k: v for k, v in params.items() if k in count_keys})
    total = count_result.scalar() or 0
    if hasattr(total, "__int__"):
        total = int(total)
    sql = text(f"""
        SELECT
            sd.id AS id,
            ps.id AS schedule_id,
            'APS' AS file_name,
            sd.schedule_date AS plan_date,
            sd.planned_qty AS quantity,
            ps.planned_output_qty AS planned_output_qty,
            m.machine_name AS machine_name,
            m.machine_cd AS machine_cd,
            :process_label AS process_name,
            ps.order_no AS operator,
            ps.item_name AS product_name,
            ps.product_cd AS product_cd,
            ee.efficiency_rate AS efficiency_rate,
            ps.setup_time AS setup_time,
            sd.actual_qty AS actual_production,
            sd.defect_qty AS defect_qty,
            COALESCE(ub.upstream_defect_qty_total, 0) AS upstream_defect_qty_total
        FROM schedule_details sd
        INNER JOIN production_schedules ps ON ps.id = sd.schedule_id
        INNER JOIN machines m ON m.id = ps.line_id
        LEFT JOIN equipment_efficiency ee
          ON m.machine_cd = ee.machine_cd AND ps.product_cd = ee.product_cd
        LEFT JOIN (
          SELECT
            aps_schedule_id,
            COALESCE(SUM(COALESCE(upstream_defect_qty, 0)), 0) AS upstream_defect_qty_total
          FROM aps_batch_plans
          GROUP BY aps_schedule_id
        ) ub ON ub.aps_schedule_id = ps.id
        WHERE {base_where}
        ORDER BY sd.schedule_date, m.machine_name, ps.order_no, ps.item_name
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(sql, params)
    rows = result.mappings().fetchall()
    records = [_mes_schedule_plan_row_to_record(dict(r)) for r in rows]
    return {
        "success": True,
        "data": {"records": records, "total": total},
        "message": "OK",
    }


def _parse_month(month: str) -> tuple[date, str]:
    """Parse 'YYYY-MM' -> (production_month date, file_name month label e.g. '1月')."""
    parts = month.strip().split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="month は YYYY-MM 形式で指定してください")
    try:
        y, m = int(parts[0]), int(parts[1])
        if not (1 <= m <= 12):
            raise ValueError("month must be 1-12")
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"無効な月: {month}") from e
    production_month = date(y, m, 1)
    month_label = f"{m}月"
    return production_month, month_label


def _to_int(x) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    try:
        return int(float(str(x).strip()))
    except (ValueError, TypeError):
        return None


def _to_decimal_val(x):
    if x is None:
        return None
    if hasattr(x, "isoformat"):
        return x
    if isinstance(x, (int, float)):
        return x
    try:
        return float(str(x).strip())
    except (ValueError, TypeError):
        return None


@router.get("/plan/batch/schedule-months")
async def get_schedule_months(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    生産月一覧: production_plan_schedules の file_name から月を抽出して返す。
    例: "加工計画(1月).xlsm" → 当年の 1月。該当なしの場合は当年 1月～12月を返す。
    """
    sql = text("""
        SELECT DISTINCT file_name FROM production_plan_schedules
        WHERE file_name IS NOT NULL AND file_name != ''
        ORDER BY file_name
        LIMIT 500
    """)
    result = await db.execute(sql)
    rows = result.mappings().fetchall()
    seen = set()
    out = []
    current_year = date.today().year
    for r in rows:
        fn = dict(r).get("file_name") if hasattr(r, "keys") else None
        if not fn:
            continue
        # "1月" or "01月" or "（1月）" 等を抽出
        m = re.search(r"(\d{1,2})月", str(fn))
        if m:
            month_num = int(m.group(1))
            if 1 <= month_num <= 12 and month_num not in seen:
                seen.add(month_num)
                value = f"{current_year}-{month_num:02d}"
                out.append({"value": value, "label": f"{month_num}月"})
    if not out:
        out = [{"value": f"{current_year}-{m:02d}", "label": f"{m}月"} for m in range(1, 13)]
    return {"success": True, "data": out, "message": "OK"}


@router.get("/plan/batch/list")
async def get_instruction_plans_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    product_name: Optional[str] = Query(None, description="製品名（部分一致）"),
    equipment: Optional[str] = Query(None, description="設備/ライン（production_line 部分一致）"),
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    生産ロット一覧: instruction_plans を取得する。
    既定ソート: start_date 昇順（未設定は末尾）、同一日内は production_line・順位・ロットNo。
    """
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if product_name and product_name.strip():
        conditions.append("product_name LIKE :product_name")
        params["product_name"] = f"%{product_name.strip()}%"
    if equipment and equipment.strip():
        conditions.append("production_line LIKE :equipment")
        params["equipment"] = f"%{equipment.strip()}%"

    sql = text(f"""
        SELECT id, production_month, production_line, priority_order, product_cd, product_name,
               planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed,
               has_sw_process, is_sw_instructed, management_code, actual_production_quantity,
               take_count, cutting_length, chamfering_length, developed_length, scrap_length,
               material_name, material_manufacturer, standard_specification,
               use_material_stock_sub, usage_count,
               created_at, updated_at
        FROM instruction_plans
        WHERE {" AND ".join(conditions)}
        ORDER BY (start_date IS NULL) ASC, start_date ASC, production_line, priority_order,
                 CAST(COALESCE(lot_number, '0') AS UNSIGNED),
                 lot_number
        LIMIT :limit
    """)
    result = await db.execute(sql, params)
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _row_to_dict(r):
        row = dict(r)
        return {
            "id": row.get("id"),
            "production_month": _v(row, "production_month"),
            "production_line": _v(row, "production_line"),
            "priority_order": row.get("priority_order"),
            "product_cd": _v(row, "product_cd"),
            "product_name": _v(row, "product_name"),
            "planned_quantity": row.get("planned_quantity"),
            "start_date": _v(row, "start_date"),
            "end_date": _v(row, "end_date"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": _v(row, "lot_number"),
            "is_cutting_instructed": row.get("is_cutting_instructed"),
            "has_chamfering_process": row.get("has_chamfering_process"),
            "is_chamfering_instructed": row.get("is_chamfering_instructed"),
            "has_sw_process": row.get("has_sw_process"),
            "is_sw_instructed": row.get("is_sw_instructed"),
            "management_code": _v(row, "management_code"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "take_count": row.get("take_count"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "scrap_length": _v(row, "scrap_length"),
            "material_name": _v(row, "material_name"),
            "material_manufacturer": _v(row, "material_manufacturer"),
            "standard_specification": _v(row, "standard_specification"),
            "use_material_stock_sub": row.get("use_material_stock_sub"),
            "usage_count": _v(row, "usage_count", 1),
            "created_at": _v(row, "created_at"),
            "updated_at": _v(row, "updated_at"),
        }

    data = [_row_to_dict(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/plan/batch/material-requirements-summary")
async def get_material_requirements_summary_from_instruction_plans(
    date_start: Optional[str] = Query(None, description="集計開始日 YYYY-MM-DD（DATE(start_date) で判定、start_date 未設定行は対象外）"),
    date_end: Optional[str] = Query(None, description="集計終了日 YYYY-MM-DD（含む）"),
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM（date_start/date_end 未指定時にその月の全日を期間として使用）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    instruction_plans を期間で絞り、材料ごとに件数（行数）を集計する。
    - start_date が NULL の行は集計対象外
    - 期間キー: DATE(start_date)
    - 指標: COUNT(*)（planned_quantity / actual_production_quantity / usage_count は使わない）
    """
    d_start = _parse_date_ymd(date_start) if date_start else None
    d_end = _parse_date_ymd(date_end) if date_end else None

    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    if d_start is None:
                        d_start = date(y, m, 1)
                    if d_end is None:
                        if m == 12:
                            d_end = date(y, 12, 31)
                        else:
                            d_end = date(y, m + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            pass

    if d_start is None or d_end is None:
        raise HTTPException(
            status_code=400,
            detail="date_start と date_end を指定するか、production_month（YYYY-MM）を指定してください。",
        )
    if d_start > d_end:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    conditions = [
        "start_date IS NOT NULL",
        "DATE(start_date) >= :d_start",
        "DATE(start_date) <= :d_end",
    ]
    params = {"d_start": d_start, "d_end": d_end}

    sql = text(f"""
        SELECT
            COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)') AS material_name,
            COALESCE(NULLIF(TRIM(material_manufacturer), ''), '') AS material_manufacturer,
            COALESCE(NULLIF(TRIM(standard_specification), ''), '') AS standard_specification,
            COUNT(*) AS piece_count
        FROM instruction_plans
        WHERE {" AND ".join(conditions)}
        GROUP BY
            COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)'),
            COALESCE(NULLIF(TRIM(material_manufacturer), ''), ''),
            COALESCE(NULLIF(TRIM(standard_specification), ''), '')
        ORDER BY material_manufacturer ASC, material_name ASC, standard_specification ASC
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="instruction_plans テーブルが存在しません。",
            ) from e
        logger.exception("material-requirements-summary 集計失敗")
        raise HTTPException(status_code=500, detail="部品需要量の集計に失敗しました。") from e

    def _icount(v) -> int:
        if v is None:
            return 0
        if isinstance(v, Decimal):
            return int(v)
        return int(v)

    items = []
    total_pieces = 0
    for r in rows:
        rd = dict(r)
        c = _icount(rd.get("piece_count"))
        total_pieces += c
        items.append(
            {
                "material_name": rd.get("material_name"),
                "material_manufacturer": rd.get("material_manufacturer"),
                "standard_specification": rd.get("standard_specification"),
                "piece_count": c,
            }
        )

    # 翌日日付
    _DAY_MATRIX_MAX_DAYS = 186
    span_days = (d_end - d_start).days + 1
    daily_matrix: Optional[dict] = None
    daily_matrix_omitted = span_days > _DAY_MATRIX_MAX_DAYS

    if not daily_matrix_omitted:
        daily_sql = text(f"""
            SELECT
                DATE(start_date) AS eff_date,
                COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)') AS material_name,
                COALESCE(NULLIF(TRIM(material_manufacturer), ''), '') AS material_manufacturer,
                COALESCE(NULLIF(TRIM(standard_specification), ''), '') AS standard_specification,
                COUNT(*) AS cnt
            FROM instruction_plans
            WHERE {" AND ".join(conditions)}
            GROUP BY
                DATE(start_date),
                COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)'),
                COALESCE(NULLIF(TRIM(material_manufacturer), ''), ''),
                COALESCE(NULLIF(TRIM(standard_specification), ''), '')
            ORDER BY eff_date, material_manufacturer ASC, material_name ASC, standard_specification ASC
        """)
        try:
            dr = await db.execute(daily_sql, params)
            drows = dr.mappings().fetchall()
        except Exception as e:
            msg = str(e).lower()
            if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
                raise HTTPException(
                    status_code=503,
                    detail="instruction_plans テーブルが存在しません。",
                ) from e
            logger.exception("material-requirements daily 集計失敗")
            raise HTTPException(status_code=500, detail="日別材料需要量の集計に失敗しました。") from e

        date_list: list[str] = []
        cur = d_start
        while cur <= d_end:
            date_list.append(cur.isoformat())
            cur = cur + timedelta(days=1)

        pivot: dict[tuple, dict[str, int]] = {}
        for r in drows:
            rd = dict(r)
            ed = rd.get("eff_date")
            if ed is None:
                continue
            if hasattr(ed, "isoformat"):
                ds = ed.isoformat()[:10]
            else:
                ds = str(ed)[:10]
            key = (
                rd.get("material_name"),
                rd.get("material_manufacturer"),
                rd.get("standard_specification"),
            )
            if key not in pivot:
                pivot[key] = {d: 0 for d in date_list}
            qv = _icount(rd.get("cnt"))
            if ds in pivot[key]:
                pivot[key][ds] += qv

        # 合計表にのみ存在する材料も日別表に行として出す（該当日が無ければ 0）
        for it in items:
            k = (it.get("material_name"), it.get("material_manufacturer"), it.get("standard_specification"))
            if k not in pivot:
                pivot[k] = {d: 0 for d in date_list}

        matrix_rows = []
        # pivot key (material_name, material_manufacturer, standard_specification) → 表示順: メーカー・材料名・規格 昇順
        for key in sorted(pivot.keys(), key=lambda k: (k[1] or "", k[0] or "", k[2] or "")):
            mn, mf, sp = key
            by_date = pivot[key]
            row_total = sum(by_date.values())
            matrix_rows.append(
                {
                    "material_name": mn,
                    "material_manufacturer": mf,
                    "standard_specification": sp,
                    "by_date": {d: by_date[d] for d in date_list},
                    "row_total": row_total,
                }
            )

        daily_matrix = {
            "dates": date_list,
            "rows": matrix_rows,
        }

    return {
        "success": True,
        "message": "OK",
        "data": {
            "items": items,
            "daily_matrix": daily_matrix,
            "summary": {
                "date_start": d_start.isoformat(),
                "date_end": d_end.isoformat(),
                "production_month_filter": production_month.strip() if production_month and production_month.strip() else None,
                "total_material_kinds": len(items),
                "total_piece_count": total_pieces,
                "effective_date_note": "start_date が設定されている行のみ対象。日別は DATE(start_date) ごとの材料別ロット件数（COUNT(*)）です。",
                "daily_matrix_omitted": daily_matrix_omitted,
                "daily_matrix_max_days": _DAY_MATRIX_MAX_DAYS,
            },
        },
    }


def _component_requirements_date_range(
    date_start: Optional[str],
    date_end: Optional[str],
    production_month: Optional[str],
) -> tuple[date, date]:
    d_start = _parse_date_ymd(date_start) if date_start else None
    d_end = _parse_date_ymd(date_end) if date_end else None

    if production_month and production_month.strip():
        try:
            pm_parts = production_month.strip().split("-")
            if len(pm_parts) == 2:
                y, m = int(pm_parts[0]), int(pm_parts[1])
                if 1 <= m <= 12:
                    if d_start is None:
                        d_start = date(y, m, 1)
                    if d_end is None:
                        if m == 12:
                            d_end = date(y, 12, 31)
                        else:
                            d_end = date(y, m + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            pass

    if d_start is None or d_end is None:
        today = datetime.utcnow().date()
        d_start = d_start or today.replace(day=1)
        d_end = d_end or today

    if d_start > d_end:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")
    return d_start, d_end


@router.get("/plan/batch/component-requirements-summary")
async def get_component_requirements_summary_from_production_summarys(
    date_start: Optional[str] = Query(None, description="集計開始日 YYYY-MM-DD（production_summarys.date で判定）"),
    date_end: Optional[str] = Query(None, description="集計終了日 YYYY-MM-DD（含む）"),
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM（date_start/date_end 未指定時にその月の全日を期間として使用）"),
    plan_column: str = Query(
        "molding_actual_plan",
        description="需求量の駆動列: molding_actual_plan | molding_plan",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_summarys の指定列 × 明細 BOM から部品所要を集計。
    既定は molding_actual_plan（成型実績計画）。molding_plan で成型計画に切替可能。
    """
    d_start, d_end = _component_requirements_date_range(date_start, date_end, production_month)
    driver_expr, label = _plan_column_sql_expr(plan_column)
    note = (
        f"production_summarys を日付・製品で対象に、{label} × BOM構成比（qty_per/base_quantity）"
        "× 歩留補正（1+scrap_rate）で集計しています。source_lot_count は当該部品に寄与したサマリー行（id）の件数です。"
    )
    pmf = production_month.strip() if production_month and production_month.strip() else None
    inner = await _aggregate_component_requirements_from_production_summarys(
        db, d_start, d_end, driver_expr, note, pmf
    )
    inner["summary"]["plan_column"] = plan_column.strip()
    return {"success": True, "message": "OK", "data": inner}


@router.get("/plan/batch/component-requirements-use-summary")
async def get_component_requirements_use_summary_from_production_summarys(
    date_start: Optional[str] = Query(None, description="集計開始日 YYYY-MM-DD（production_summarys.date）"),
    date_end: Optional[str] = Query(None, description="集計終了日 YYYY-MM-DD（含む）"),
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    (welding_actual + welding_defect) × 明細 BOM で部品の日別使用量を集計。
    """
    d_start, d_end = _component_requirements_date_range(date_start, date_end, production_month)
    note = (
        "production_summarys を日付・製品で対象に、(welding_actual + welding_defect) × BOM構成比"
        "（qty_per/base_quantity）× 歩留補正（1+scrap_rate）で集計しています。"
    )
    pmf = production_month.strip() if production_month and production_month.strip() else None
    inner = await _aggregate_component_requirements_from_production_summarys(
        db, d_start, d_end, _WELDING_USE_DRIVER_SQL, note, pmf
    )
    return {"success": True, "message": "OK", "data": inner}


@router.get("/plan/batch/component-requirements-bundle")
async def get_component_requirements_bundle(
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    production_month: Optional[str] = Query(None),
    plan_column: str = Query("molding_actual_plan", description="需求量の駆動列"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """需求量サマリーと溶接ベース使用量サマリーを1回で返す。"""
    d_start, d_end = _component_requirements_date_range(date_start, date_end, production_month)
    pmf = production_month.strip() if production_month and production_month.strip() else None
    driver_expr, label = _plan_column_sql_expr(plan_column)
    note_d = (
        f"production_summarys を日付・製品で対象に、{label} × BOM構成比（qty_per/base_quantity）"
        "× 歩留補正（1+scrap_rate）で集計しています。source_lot_count は当該部品に寄与したサマリー行（id）の件数です。"
    )
    note_u = (
        "production_summarys を日付・製品で対象に、(welding_actual + welding_defect) × BOM構成比"
        "（qty_per/base_quantity）× 歩留補正（1+scrap_rate）で集計しています。"
    )
    demand = await _aggregate_component_requirements_from_production_summarys(
        db, d_start, d_end, driver_expr, note_d, pmf
    )
    demand["summary"]["plan_column"] = plan_column.strip()
    use = await _aggregate_component_requirements_from_production_summarys(
        db, d_start, d_end, _WELDING_USE_DRIVER_SQL, note_u, pmf
    )
    return {
        "success": True,
        "message": "OK",
        "data": {
            "date_start": d_start.isoformat(),
            "date_end": d_end.isoformat(),
            "production_month_filter": pmf,
            "demand": demand,
            "use": use,
        },
    }


class UpdatePlanBody(BaseModel):
    """指定月の instruction_plans を1件ずつ切断指示へ展開"""""
    production_month: Optional[str] = None  # YYYY-MM-DD
    production_line: Optional[str] = None
    priority_order: Optional[int] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    planned_quantity: Optional[int] = None
    actual_production_quantity: Optional[int] = None
    lot_number: Optional[str] = None
    production_lot_size: Optional[int] = None
    material_name: Optional[str] = None
    material_manufacturer: Optional[str] = None
    standard_specification: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    is_cutting_instructed: Optional[int] = None  # 0/1
    has_chamfering_process: Optional[int] = None
    is_chamfering_instructed: Optional[int] = None
    has_sw_process: Optional[int] = None
    is_sw_instructed: Optional[int] = None
    management_code: Optional[str] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    scrap_length: Optional[float] = None
    use_material_stock_sub: Optional[int] = None  # 0/1
    usage_count: Optional[float] = None  # 1=1本, <1=按分


class CreatePlanBody(BaseModel):
    """新規ロット追加（instruction_plans 1件 INSERT）"""
    production_month: Optional[str] = None  # YYYY-MM
    production_line: Optional[str] = None
    priority_order: Optional[int] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    material_name: Optional[str] = None
    material_manufacturer: Optional[str] = None
    standard_specification: Optional[str] = None
    planned_quantity: Optional[int] = None
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    scrap_length: Optional[float] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    has_chamfering_process: Optional[int] = None  # 0/1
    has_sw_process: Optional[int] = None  # 0/1
    use_material_stock_sub: Optional[int] = None  # 0/1
    usage_count: Optional[float] = None  # 1=1本, <1=按分


def _parse_date_ymd(s: Optional[str]):
    """Parse YYYY-MM-DD or YYYY-MM to date."""
    if s is None or len(str(s).strip()) < 7:
        return None
    try:
        parts = str(s).strip()[:10].replace("-", " ").split()
        if len(parts) >= 2:
            y, m = int(parts[0]), int(parts[1])
            d = int(parts[2]) if len(parts) >= 3 else 1
            if 1 <= m <= 12:
                return date(y, m, d)
    except (ValueError, IndexError):
        pass
    return None


def _parse_datetime_plan(s: Optional[str]):
    """Parse YYYY-MM-DD to datetime."""
    if s is None or len(str(s).strip()) < 10:
        return None
    try:
        parts = str(s).strip()[:10].split("-")
        if len(parts) == 3:
            return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


@router.post("/plan/batch/create")
async def create_instruction_plan(
    body: CreatePlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """instruction_plans に1件新規追加。management_code はトリガーで自動設定。"""
    production_month = _parse_date_ymd(body.production_month)
    if not production_month:
        raise HTTPException(status_code=400, detail="production_month (YYYY-MM) を指定してください")
    product_cd = (body.product_cd or "").strip() or None
    product_name = (body.product_name or "").strip() or None
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="product_cd と product_name は必須です")
    production_line = (body.production_line or "").strip() or ""
    priority_order = body.priority_order if body.priority_order is not None else 0
    planned_quantity = body.planned_quantity if body.planned_quantity is not None else 0
    production_lot_size = body.production_lot_size if body.production_lot_size is not None else None
    lot_number = (body.lot_number or "").strip() or None
    actual_production_quantity = body.actual_production_quantity if body.actual_production_quantity is not None else 0
    take_count = body.take_count if body.take_count is not None else None
    cutting_length = body.cutting_length
    chamfering_length = body.chamfering_length
    developed_length = body.developed_length
    scrap_length = body.scrap_length
    material_name = (body.material_name or "").strip() or None
    material_manufacturer = (body.material_manufacturer or "").strip() or None
    standard_specification = (body.standard_specification or "").strip() or None
    start_date = _parse_datetime_plan(body.start_date)
    end_date = _parse_datetime_plan(body.end_date)
    has_chamfering_process = 1 if (body.has_chamfering_process == 1) else 0
    has_sw_process = 1 if (body.has_sw_process == 1) else 0

    use_material_stock_sub = 1 if getattr(body, "use_material_stock_sub", 0) == 1 else 0
    usage_count_val = getattr(body, "usage_count", None)
    if usage_count_val is None:
        usage_count_val = 1.0
    try:
        usage_count_val = float(usage_count_val)
    except (TypeError, ValueError):
        usage_count_val = 1.0
    if usage_count_val <= 0:
        usage_count_val = 1.0

    sql = text("""
        INSERT INTO instruction_plans (
            production_month, production_line, priority_order, product_cd, product_name,
            planned_quantity, start_date, end_date, production_lot_size, lot_number,
            is_cutting_instructed, has_chamfering_process, is_chamfering_instructed,
            has_sw_process, is_sw_instructed, actual_production_quantity,
            take_count, cutting_length, chamfering_length, developed_length, scrap_length,
            material_name, material_manufacturer, standard_specification,
            use_material_stock_sub, usage_count
        ) VALUES (
            :production_month, :production_line, :priority_order, :product_cd, :product_name,
            :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
            0, :has_chamfering_process, 0, :has_sw_process, 0, :actual_production_quantity,
            :take_count, :cutting_length, :chamfering_length, :developed_length, :scrap_length,
            :material_name, :material_manufacturer, :standard_specification,
            :use_material_stock_sub, :usage_count
        )
    """)
    params = {
        "production_month": production_month,
        "production_line": production_line,
        "priority_order": priority_order,
        "product_cd": product_cd,
        "product_name": product_name,
        "planned_quantity": planned_quantity,
        "start_date": start_date,
        "end_date": end_date,
        "production_lot_size": production_lot_size,
        "lot_number": lot_number,
        "actual_production_quantity": actual_production_quantity,
        "take_count": take_count,
        "cutting_length": cutting_length,
        "chamfering_length": chamfering_length,
        "developed_length": developed_length,
        "scrap_length": scrap_length,
        "material_name": material_name,
        "material_manufacturer": material_manufacturer,
        "standard_specification": standard_specification,
        "has_chamfering_process": has_chamfering_process,
        "has_sw_process": has_sw_process,
        "use_material_stock_sub": use_material_stock_sub,
        "usage_count": usage_count_val,
    }
    await db.execute(sql, params)
    await db.commit()
    return {"success": True, "message": "レコードを追加しました"}


@router.patch("/plan/batch/{plan_id}")
async def update_instruction_plan(
    plan_id: int,
    body: UpdatePlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産ロット1件を更新。management_code は未送信時のみ再計算。"""
    updates = []
    params = {"plan_id": plan_id}

    def _parse_date(s: Optional[str]):
        if s is None or len(str(s).strip()) < 10:
            return None
        try:
            parts = str(s).strip()[:10].split("-")
            if len(parts) == 3:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None

    def _parse_datetime(s: Optional[str]):
        if s is None or len(str(s).strip()) < 10:
            return None
        try:
            parts = str(s).strip()[:10].split("-")
            if len(parts) == 3:
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None

    if body.production_month is not None:
        v = _parse_date(body.production_month)
        if v is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = v
    if body.production_line is not None:
        updates.append("production_line = :production_line")
        params["production_line"] = body.production_line.strip() if body.production_line else ""
    if body.priority_order is not None:
        updates.append("priority_order = :priority_order")
        params["priority_order"] = body.priority_order
    if body.product_cd is not None:
        updates.append("product_cd = :product_cd")
        params["product_cd"] = body.product_cd.strip() if body.product_cd else ""
    if body.product_name is not None:
        updates.append("product_name = :product_name")
        params["product_name"] = body.product_name.strip() if body.product_name else ""
    if body.planned_quantity is not None:
        updates.append("planned_quantity = :planned_quantity")
        params["planned_quantity"] = body.planned_quantity
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.lot_number is not None:
        updates.append("lot_number = :lot_number")
        params["lot_number"] = str(body.lot_number).strip() if body.lot_number else ""
    if body.production_lot_size is not None:
        updates.append("production_lot_size = :production_lot_size")
        params["production_lot_size"] = body.production_lot_size
    if body.material_name is not None:
        updates.append("material_name = :material_name")
        params["material_name"] = body.material_name.strip() if body.material_name else None
    if body.material_manufacturer is not None:
        updates.append("material_manufacturer = :material_manufacturer")
        params["material_manufacturer"] = body.material_manufacturer.strip() if body.material_manufacturer else None
    if body.standard_specification is not None:
        updates.append("standard_specification = :standard_specification")
        params["standard_specification"] = body.standard_specification.strip() if body.standard_specification else None
    if body.start_date is not None:
        v = _parse_datetime(body.start_date)
        if v is not None:
            updates.append("start_date = :start_date")
            params["start_date"] = v
    if body.end_date is not None:
        v = _parse_datetime(body.end_date)
        if v is not None:
            updates.append("end_date = :end_date")
            params["end_date"] = v
    if body.is_cutting_instructed is not None:
        updates.append("is_cutting_instructed = :is_cutting_instructed")
        params["is_cutting_instructed"] = 1 if body.is_cutting_instructed else 0
    if body.has_chamfering_process is not None:
        updates.append("has_chamfering_process = :has_chamfering_process")
        params["has_chamfering_process"] = 1 if body.has_chamfering_process else 0
    if body.is_chamfering_instructed is not None:
        updates.append("is_chamfering_instructed = :is_chamfering_instructed")
        params["is_chamfering_instructed"] = 1 if body.is_chamfering_instructed else 0
    if body.has_sw_process is not None:
        updates.append("has_sw_process = :has_sw_process")
        params["has_sw_process"] = 1 if body.has_sw_process else 0
    if body.is_sw_instructed is not None:
        updates.append("is_sw_instructed = :is_sw_instructed")
        params["is_sw_instructed"] = 1 if body.is_sw_instructed else 0
    if body.management_code is not None:
        updates.append("management_code = :management_code")
        params["management_code"] = body.management_code.strip() if body.management_code else None
    if body.take_count is not None:
        updates.append("take_count = :take_count")
        params["take_count"] = body.take_count
    if body.cutting_length is not None:
        updates.append("cutting_length = :cutting_length")
        params["cutting_length"] = body.cutting_length
    if body.chamfering_length is not None:
        updates.append("chamfering_length = :chamfering_length")
        params["chamfering_length"] = body.chamfering_length
    if body.developed_length is not None:
        updates.append("developed_length = :developed_length")
        params["developed_length"] = body.developed_length
    if body.scrap_length is not None:
        updates.append("scrap_length = :scrap_length")
        params["scrap_length"] = body.scrap_length
    if body.use_material_stock_sub is not None:
        updates.append("use_material_stock_sub = :use_material_stock_sub")
        params["use_material_stock_sub"] = 1 if body.use_material_stock_sub == 1 else 0
    if body.usage_count is not None:
        try:
            uc = float(body.usage_count)
            if uc > 0:
                updates.append("usage_count = :usage_count")
                params["usage_count"] = uc
        except (TypeError, ValueError):
            pass

    if not updates:
        return {"success": True, "message": "変更なし"}

    set_clause = ", ".join(updates)
    await db.execute(text(f"UPDATE instruction_plans SET {set_clause} WHERE id = :plan_id"), params)
    # management_code を送っていない場合のみ再計算
    if body.management_code is None:
        await db.execute(
            text("""
                UPDATE instruction_plans SET management_code = CONCAT(
                    RIGHT(YEAR(production_month), 2), LPAD(MONTH(production_month), 2, '0'),
                    COALESCE(product_cd, ''), RIGHT(COALESCE(production_line, ''), 2),
                    LPAD(COALESCE(priority_order, 0), 2, '0'), '-',
                    LPAD(COALESCE(production_lot_size, 0), 2, '0'), '-',
                    LPAD(COALESCE(lot_number, ''), 2, '0')
                ) WHERE id = :plan_id
            """),
            {"plan_id": plan_id},
        )
    await db.commit()
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/batch/{plan_id}")
async def delete_instruction_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産ロット1件を削除（instruction_plans のみ。切断指示へ移行済みの場合は一覧に無いため対象外）。"""
    result = await db.execute(text("DELETE FROM instruction_plans WHERE id = :plan_id"), {"plan_id": plan_id})
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="該当するロットがありません")
    return {"success": True, "message": "更新しました"}


@router.get("/plan/cutting-management/list")
async def get_cutting_management_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    production_line: Optional[str] = Query(None, description="ライン（部分一致）"),
    cutting_machine: Optional[str] = Query(None, description="切断機（完全一致でフィルタ）"),
    limit: int = Query(2000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    切断指示一覧: cutting_management を取得。
    並び: 生産日 → 切断機 → 生産順（同一天同一设备内で 1,2,3... の順）。
    """
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if production_day and production_day.strip():
        try:
            parts = production_day.strip().split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                params["production_day"] = date(y, m, d)
                conditions.append("production_day = :production_day")
        except (ValueError, IndexError):
            pass
    if production_line and production_line.strip():
        conditions.append("production_line LIKE :production_line")
        params["production_line"] = f"%{production_line.strip()}%"
    if cutting_machine is not None and cutting_machine.strip():
        conditions.append("cutting_machine = :cutting_machine")
        params["cutting_machine"] = cutting_machine.strip()

    # WHERE は修飾なし（cutting_management のみ該当列を持つため曖昧でない）。:param の誤置換を防ぐ
    where_clause = " AND ".join(conditions)
    cm_cols = await _get_cutting_mgmt_columns(db)
    mes_select = _cutting_mgmt_mes_select_fragment(cm_cols)
    # 生産時間を実時計算: product_cd + 切断機(cutting_machine)=machines_name で equipment_efficiency を結合し efficiency_rate を取得、生産数/能率
    sql = text(f"""
        SELECT `cutting_management`.id, `cutting_management`.production_month, `cutting_management`.production_day,
               `cutting_management`.production_line, `cutting_management`.cutting_machine, `cutting_management`.production_sequence,
               `cutting_management`.priority_order, `cutting_management`.product_cd, `cutting_management`.product_name,
               `cutting_management`.planned_quantity, `cutting_management`.start_date, `cutting_management`.end_date,
               `cutting_management`.production_lot_size, `cutting_management`.lot_number,
               `cutting_management`.is_cutting_instructed, `cutting_management`.has_chamfering_process,
               `cutting_management`.is_chamfering_instructed, `cutting_management`.has_sw_process, `cutting_management`.is_sw_instructed,
               `cutting_management`.management_code, `cutting_management`.actual_production_quantity, `cutting_management`.defect_qty, `cutting_management`.take_count,
               `cutting_management`.cutting_length, `cutting_management`.chamfering_length, `cutting_management`.developed_length,
               `cutting_management`.scrap_length, `cutting_management`.material_name, `cutting_management`.material_manufacturer,
               `cutting_management`.standard_specification, `cutting_management`.production_completed_check, `cutting_management`.material_usage_reflected,
               `cutting_management`.use_material_stock_sub, `cutting_management`.usage_count,
               {mes_select}
               `cutting_management`.cd,
               `cutting_management`.created_at, `cutting_management`.updated_at, `cutting_management`.remarks,
               `equipment_efficiency`.efficiency_rate AS efficiency_rate
        FROM `cutting_management`
        LEFT JOIN `equipment_efficiency`
          ON `cutting_management`.product_cd = `equipment_efficiency`.product_cd
         AND `cutting_management`.cutting_machine = `equipment_efficiency`.machines_name
        WHERE {where_clause}
        ORDER BY `cutting_management`.production_day ASC, `cutting_management`.cutting_machine ASC, `cutting_management`.production_sequence ASC
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "cutting_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="cutting_management テーブルが存在しません。マイグレーション 053_cutting_management.sql を実行してください。",
            ) from e
        if "unknown column" in msg:
            for col in _CUTTING_MGMT_MES_COLUMNS:
                if col in msg:
                    raise HTTPException(status_code=503, detail=_mes_column_migration_hint(col)) from e
            raise HTTPException(
                status_code=503,
                detail="cutting_management テーブルが存在しません。backend/database/migrations/03〜06_cutting_management_mes_*.sql を実行してください",
            ) from e
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e), "message": "切断指示一覧の取得に失敗しました"},
        )

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _v_date(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10] if val else default
        return str(val)[:10] if val else default

    def _cm_row(r):
        row = dict(r)
        # 生産時間 = 生産数 / efficiency_rate（equipment_efficiency を product_cd・切断機=machines_name で結合）
        qty = row.get("actual_production_quantity")
        rate = row.get("efficiency_rate")
        if qty is not None and rate is not None:
            try:
                q = float(qty) if not isinstance(qty, (int, float)) else qty
                r = float(rate) if not isinstance(rate, (int, float)) else rate
                production_time = round(q / r, 1) if r > 0 else None
            except (TypeError, ValueError):
                production_time = None
        else:
            production_time = None
        return {
            "id": row.get("id"),
            "production_month": _v_date(row, "production_month"),
            "production_day": _v_date(row, "production_day"),
            "production_line": row.get("production_line"),
            "cutting_machine": row.get("cutting_machine"),
            "production_sequence": row.get("production_sequence"),
            "priority_order": row.get("priority_order"),
            "product_cd": row.get("product_cd"),
            "product_name": row.get("product_name"),
            "planned_quantity": row.get("planned_quantity"),
            "start_date": _v(row, "start_date"),
            "end_date": _v(row, "end_date"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": row.get("lot_number"),
            "is_cutting_instructed": row.get("is_cutting_instructed"),
            "has_chamfering_process": row.get("has_chamfering_process"),
            "is_chamfering_instructed": row.get("is_chamfering_instructed"),
            "has_sw_process": row.get("has_sw_process"),
            "is_sw_instructed": row.get("is_sw_instructed"),
            "management_code": row.get("management_code"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "defect_qty": row.get("defect_qty"),
            "take_count": row.get("take_count"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "scrap_length": _v(row, "scrap_length"),
            "material_name": row.get("material_name"),
            "material_manufacturer": row.get("material_manufacturer"),
            "standard_specification": row.get("standard_specification"),
            "production_completed_check": row.get("production_completed_check"),
            "material_usage_reflected": row.get("material_usage_reflected") or "未反映",
            "use_material_stock_sub": row.get("use_material_stock_sub"),
            "usage_count": _v(row, "usage_count", 1),
            "mes_production_started_at": _v(row, "mes_production_started_at"),
            "mes_production_ended_at": _v(row, "mes_production_ended_at"),
            "mes_net_production_sec": row.get("mes_net_production_sec"),
            "mes_paused_accum_sec": row.get("mes_paused_accum_sec"),
            "mes_production_is_paused": row.get("mes_production_is_paused"),
            "mes_setup_time_min": row.get("mes_setup_time_min"),
            "mes_saw_blade_exchange_min": row.get("mes_saw_blade_exchange_min"),
            "mes_repair_min": row.get("mes_repair_min"),
            "mes_operator_user_id": row.get("mes_operator_user_id"),
            "mes_scanned_code": row.get("mes_scanned_code"),
            "cd": row.get("cd"),
            "created_at": _v(row, "created_at"),
            "updated_at": _v(row, "updated_at"),
            "remarks": row.get("remarks"),
            "production_time": production_time,
        }

    try:
        data = [_cm_row(dict(r)) for r in rows]
        return {"success": True, "data": data, "message": "OK"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e), "message": "切断指示一覧の取得に失敗しました"},
        )


@router.post("/plan/cutting-management/confirm-actual")
async def confirm_cutting_actual(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    cutting_machine: Optional[str] = Query(None, description="切断機（完全一致でフィルタ）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """
    切断指示-今日の「実績確定」: production_completed_check=1 の cutting_management を
    stock_transaction_logs へ切断実績を登録（同日・同ロットは一旦削除してから再登録）
    既存 cutting_management 実績を先に削除してから挿入する（先删除再插入）。
    """
    try:
        parts = production_day.strip().split("-")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="production_day は YYYY-MM-DD で指定してください")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        prod_day = date(y, m, d)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="production_day の形式が不正です") from e

    # 去重复：同一範囲の既存実績を削除（source_file=cutting_management & 同日 & 同一切断機なら削除）
    del_params: dict = {"production_day": prod_day}
    del_conditions = [
        "source_file = 'cutting_management'",
        "DATE(transaction_time) = :production_day",
    ]
    if cutting_machine and cutting_machine.strip():
        del_conditions.append("machine_cd = :cutting_machine")
        del_params["cutting_machine"] = cutting_machine.strip()
    del_sql = text("DELETE FROM stock_transaction_logs WHERE " + " AND ".join(del_conditions))
    await db.execute(del_sql, del_params)

    conditions = ["production_day = :production_day", "production_completed_check = 1"]
    params: dict = {"production_day": prod_day}
    if cutting_machine and cutting_machine.strip():
        conditions.append("cutting_machine = :cutting_machine")
        params["cutting_machine"] = cutting_machine.strip()
    sel = text("""
        SELECT id, product_cd, management_code, cutting_machine, actual_production_quantity, defect_qty, production_day
        FROM cutting_management
        WHERE """ + " AND ".join(conditions))
    res = await db.execute(sel, params)
    rows = res.mappings().fetchall()
    if not rows:
        await db.commit()
        return {"success": True, "message": "対象データがありません（既存分は削除済み）", "inserted": 0, "total_quantity": 0, "deleted": True}
    # transaction_time: date → datetime (00:00:00)
    ins = text("""
        INSERT INTO stock_transaction_logs (
            stock_type, transaction_type, target_cd, location_cd, lot_no, process_cd, machine_cd,
            quantity, unit, transaction_time, source_file
        ) VALUES (
            '仕掛品', :transaction_type, :target_cd, '工程中間在庫', :lot_no, 'KT01', :machine_cd,
            :quantity, '本', :transaction_time, 'cutting_management'
        )
    """)
    inserted = 0
    total_quantity = 0
    for row in rows:
        r = dict(row)
        product_cd = (r.get("product_cd") or "").strip()
        if not product_cd:
            continue
        prod_day_val = r.get("production_day")
        if hasattr(prod_day_val, "isoformat"):
            tx_time = datetime.combine(prod_day_val, datetime.min.time()) if prod_day_val else datetime.now()
        else:
            tx_time = datetime.now()
        qty = r.get("actual_production_quantity")
        if qty is None:
            qty = 0
        # 良品：transaction_type='実績'
        await db.execute(ins, {
            "target_cd": product_cd,
            "lot_no": r.get("management_code"),
            "machine_cd": r.get("cutting_machine"),
            "quantity": qty,
            "transaction_time": tx_time,
            "transaction_type": "実績",
        })
        inserted += 1
        total_quantity += int(qty)
        # 不良：transaction_type='不良'
        defect_qty = r.get("defect_qty")
        if defect_qty is not None and int(defect_qty) > 0:
            await db.execute(ins, {
                "target_cd": product_cd,
                "lot_no": r.get("management_code"),
                "machine_cd": r.get("cutting_machine"),
                "quantity": int(defect_qty),
                "transaction_time": tx_time,
                "transaction_type": "不良",
            })
            inserted += 1
    await db.commit()
    return {
        "success": True,
        "message": f"実績 {inserted} 件を登録しました",
        "inserted": inserted,
        "total_quantity": total_quantity,
        "production_day": prod_day.isoformat(),
    }


@router.get("/plan/cutting-management/confirm-actual/email-preview")
async def preview_cutting_confirm_actual_email(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    from app.services.confirm_actual_email import get_confirm_actual_email_preview

    return await get_confirm_actual_email_preview(
        db, process_type="cutting", production_day=production_day
    )


@router.post("/plan/cutting-management/confirm-actual/send-email")
async def send_cutting_confirm_actual_email(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    from app.services.confirm_actual_email import send_confirm_actual_email

    return await send_confirm_actual_email(
        db, process_type="cutting", production_day=production_day, current_user=current_user
    )


@router.get("/plan/cutting-management/trial-completed/email-preview")
async def preview_cutting_trial_completed_email(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """面取指示の生産順を変更するリクエスト（同一面取機・同一生産日内）"""
    from app.services.cutting_trial_notification import get_cutting_trial_notification_preview

    return await get_cutting_trial_notification_preview(db, production_day=production_day)


@router.post("/plan/cutting-management/trial-completed/send-email")
async def send_cutting_trial_completed_email(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """生産数未完了分を翌日へ順延する時のリクエスト"""
    from app.services.cutting_trial_notification import send_cutting_trial_notification

    return await send_cutting_trial_notification(
        db, production_day=production_day, current_user=current_user
    )


class MoveBatchToCuttingBody(BaseModel):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    plan_id: int
    production_month: str  # YYYY-MM
    production_line: str
    product_cd: str
    product_name: str
    actual_production_quantity: Optional[int] = 0
    material_name: Optional[str] = None
    management_code: Optional[str] = None
    production_day: Optional[str] = None  # 生成日（手動指定）YYYY-MM-DD、未指定時は今日
    start_date: Optional[str] = None  # 旧パラメータ・production_day の別名
    priority_order: Optional[int] = None  # → production_order（ロット側順位）
    cutting_machine: str = ""  # 切断機（手動指定）
    has_chamfering_process: Optional[bool] = False  # 面取工程ありなら面取指示へ自動登録


@router.post("/plan/cutting-management/move-from-batch")
async def move_batch_to_cutting_management(
    body: MoveBatchToCuttingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """
    生産ロット（instruction_plans）1件を切断指示（cutting_management）へ移行する。
    - cutting_management に INSERT
    - has_chamfering_process が True なら chamfering_plans（面取ロット一覧）に自動 INSERT
    - 第一工程のため kanban_issuance に status=pending で1件 INSERT（後で手動発行）
    - instruction_plans から該当 id を DELETE
    """
    try:
        parts = body.production_month.strip().split("-")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="production_month は YYYY-MM 形式で指定してください")
        y, m = int(parts[0]), int(parts[1])
        if not (1 <= m <= 12):
            raise ValueError("month")
        production_month_date = date(y, m, 1)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="production_month の形式が不正です") from e

    # 生成日（手動指定）: production_day または start_date、未指定時は今日
    day_str = (body.production_day or body.start_date or "").strip()[:10]
    if day_str and len(day_str) == 10:
        try:
            parts = day_str.split("-")
            if len(parts) == 3:
                production_day_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                production_day_date = date.today()
        except (ValueError, IndexError):
            production_day_date = date.today()
    else:
        production_day_date = date.today()

    cutting_machine = (body.cutting_machine or "").strip()
    if not cutting_machine:
        raise HTTPException(status_code=400, detail="切断機を指定してください")

    has_chamfering = bool(body.has_chamfering_process)

    # ロット（instruction_plans）1件を取得し、cutting_management に全項目コピー
    plan_res = await db.execute(
        text("""
            SELECT production_month, production_line, priority_order, product_cd, product_name,
                   planned_quantity, start_date, end_date, production_lot_size, lot_number,
                   is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                   management_code, aps_batch_plan_id, actual_production_quantity, take_count, cutting_length, chamfering_length,
                   developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                   use_material_stock_sub, usage_count
            FROM instruction_plans WHERE id = :plan_id
        """),
        {"plan_id": body.plan_id},
    )
    plan_row = plan_res.mappings().fetchone()
    if not plan_row:
        raise HTTPException(status_code=404, detail="指定のロットが見つかりません")

    plan = dict(plan_row)
    production_line = (plan.get("production_line") or body.production_line or "").strip() or ""
    product_cd = (plan.get("product_cd") or body.product_cd or "").strip() or ""
    product_name = (plan.get("product_name") or body.product_name or "").strip() or ""
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="product_cd と product_name は必須です")
    if not production_line:
        raise HTTPException(status_code=400, detail="production_line は必須です")

    # 同一切断機内の次 生産順（自動採番）
    order_res = await db.execute(
        text("SELECT COALESCE(MAX(production_sequence), 0) + 1 AS next_order FROM cutting_management WHERE cutting_machine = :cm"),
        {"cm": cutting_machine},
    )
    order_row = order_res.mappings().fetchone()
    production_sequence = int(order_row["next_order"]) if order_row and order_row.get("next_order") is not None else 1

    insert_cutting_sql = text("""
        INSERT INTO cutting_management (
            production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
            product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
            is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
            management_code, aps_batch_plan_id, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length, developed_length, scrap_length,
            material_name, material_manufacturer, standard_specification, production_completed_check,
            use_material_stock_sub, usage_count
        ) VALUES (
            :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
            :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
            :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
            :management_code, :aps_batch_plan_id, :actual_production_quantity, 0, :take_count, :cutting_length, :chamfering_length, :developed_length, :scrap_length,
            :material_name, :material_manufacturer, :standard_specification, 0,
            :use_material_stock_sub, :usage_count
        )
    """)
    def _to_date(v):
        if v is None:
            return None
        try:
            s = str(v).strip()[:10]
            if len(s) == 10:
                return datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
        except (ValueError, IndexError):
            pass
        return None

    cutting_params = {
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": production_line,
        "cutting_machine": cutting_machine,
        "production_sequence": production_sequence,
        "priority_order": plan.get("priority_order"),
        "product_cd": product_cd,
        "product_name": product_name,
        "planned_quantity": plan.get("planned_quantity"),
        "start_date": _to_date(plan.get("start_date")),
        "end_date": _to_date(plan.get("end_date")),
        "production_lot_size": plan.get("production_lot_size"),
        "lot_number": (plan.get("lot_number") or "").strip() or None,
        "is_cutting_instructed": 1 if plan.get("is_cutting_instructed") else 0,
        "has_chamfering_process": 1 if plan.get("has_chamfering_process") else 0,
        "is_chamfering_instructed": 1 if plan.get("is_chamfering_instructed") else 0,
        "has_sw_process": 1 if plan.get("has_sw_process") else 0,
        "is_sw_instructed": 1 if plan.get("is_sw_instructed") else 0,
        "management_code": (plan.get("management_code") or "").strip() or None,
        "aps_batch_plan_id": plan.get("aps_batch_plan_id") if plan.get("aps_batch_plan_id") is not None else None,
        "actual_production_quantity": plan.get("actual_production_quantity") if plan.get("actual_production_quantity") is not None else 0,
        "take_count": plan.get("take_count"),
        "cutting_length": float(plan["cutting_length"]) if plan.get("cutting_length") is not None else None,
        "chamfering_length": float(plan["chamfering_length"]) if plan.get("chamfering_length") is not None else None,
        "developed_length": float(plan["developed_length"]) if plan.get("developed_length") is not None else None,
        "scrap_length": float(plan["scrap_length"]) if plan.get("scrap_length") is not None else None,
        "material_name": (plan.get("material_name") or "").strip() or None,
        "material_manufacturer": (plan.get("material_manufacturer") or "").strip() or None,
        "standard_specification": (plan.get("standard_specification") or "").strip() or None,
        "use_material_stock_sub": 1 if plan.get("use_material_stock_sub") == 1 else 0,
        "usage_count": float(plan["usage_count"]) if plan.get("usage_count") is not None else 1.0,
    }
    if not (cutting_params.get("management_code") or "").strip():
        cutting_params["management_code"] = _build_management_code(
            production_month=production_month_date,
            product_cd=product_cd,
            production_line=production_line,
            priority_order=cutting_params.get("priority_order"),
            production_lot_size=cutting_params.get("production_lot_size"),
            lot_number=cutting_params.get("lot_number"),
        )

    try:
        await db.execute(insert_cutting_sql, cutting_params)
        # 新規 cutting_management.id 取得
        rid = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
        row = rid.mappings().fetchone()
        cutting_id = row.get("id") if row else None
        if not cutting_id:
            await db.rollback()
            raise HTTPException(status_code=500, detail="切断指示の登録に失敗しました")
        cutting_id = int(cutting_id)

        if has_chamfering:
            ins_cham = text("""
                INSERT INTO chamfering_plans (
                    cutting_management_id, production_month, production_day, production_line, production_order,
                    product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                    cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
                ) VALUES (
                    :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
                    :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
                    :cutting_length, :chamfering_length, :developed_length, :material_name, :management_code, :has_sw_process
                )
            """)
            await db.execute(ins_cham, {
                "cutting_management_id": cutting_id,
                "production_month": production_month_date,
                "production_day": production_day_date,
                "production_line": production_line,
                "production_order": cutting_params["priority_order"],
                "product_cd": product_cd,
                "product_name": product_name,
                "actual_production_quantity": cutting_params["actual_production_quantity"],
                "production_lot_size": cutting_params.get("production_lot_size"),
                "lot_number": cutting_params.get("lot_number"),
                "cutting_length": cutting_params.get("cutting_length"),
                "chamfering_length": cutting_params.get("chamfering_length"),
                "developed_length": cutting_params.get("developed_length"),
                "material_name": cutting_params["material_name"],
                "management_code": cutting_params["management_code"],
                "has_sw_process": 1 if cutting_params.get("has_sw_process") else 0,
            })

        # 同一製品・同一設備・同一日の既存行があれば 1 件に集約（数量加算・順序は最小）
        ins_kanban = text("""
            INSERT INTO kanban_issuance (
                process_type, source_id, kanban_no, issue_date, status,
                product_cd, product_name, production_line, cutting_machine,
                material_name, standard_specification, management_code,
                start_date, end_date, planned_quantity, production_lot_size,
                actual_production_quantity, take_count,
                cutting_length, chamfering_length, developed_length,
                has_chamfering_process, lot_number, production_day
            ) VALUES (
                'cutting', :source_id, NULL, NULL, 'pending',
                :product_cd, :product_name, :production_line, :cutting_machine,
                :material_name, :standard_specification, :management_code,
                :start_date, :end_date, :planned_quantity, :production_lot_size,
                :actual_production_quantity, :take_count,
                :cutting_length, :chamfering_length, :developed_length,
                :has_chamfering_process, :lot_number, :production_day
            )
        """)
        await db.execute(ins_kanban, {
            "source_id": cutting_id,
            "product_cd": cutting_params["product_cd"],
            "product_name": cutting_params["product_name"],
            "production_line": cutting_params["production_line"],
            "cutting_machine": cutting_params["cutting_machine"],
            "material_name": cutting_params["material_name"],
            "standard_specification": cutting_params["standard_specification"],
            "management_code": cutting_params["management_code"],
            "start_date": cutting_params["start_date"].date() if isinstance(cutting_params.get("start_date"), datetime) else cutting_params.get("start_date"),
            "end_date": cutting_params["end_date"].date() if isinstance(cutting_params.get("end_date"), datetime) else cutting_params.get("end_date"),
            "planned_quantity": cutting_params["planned_quantity"],
            "production_lot_size": cutting_params["production_lot_size"],
            "actual_production_quantity": cutting_params["actual_production_quantity"],
            "take_count": cutting_params["take_count"],
            "cutting_length": cutting_params["cutting_length"],
            "chamfering_length": cutting_params["chamfering_length"],
            "developed_length": cutting_params["developed_length"],
            "has_chamfering_process": 1 if cutting_params.get("has_chamfering_process") else 0,
            "lot_number": cutting_params["lot_number"],
            "production_day": production_day_date.date() if isinstance(production_day_date, datetime) else production_day_date,
        })

        await db.execute(text("DELETE FROM instruction_plans WHERE id = :plan_id"), {"plan_id": body.plan_id})
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        msg = str(e).lower()
        if "cutting_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="cutting_management テーブルが存在しません。マイグレーション 053_cutting_management.sql を実行してください。",
            ) from e
        if "chamfering_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="chamfering_management テーブルが存在しません。") from e
        if "chamfering_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="chamfering_plans テーブルが存在しません。マイグレーション 063_chamfering_batch.sql を実行してください。") from e
        if "kanban_issuance" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="kanban_issuance テーブルが存在しません。") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"success": True, "message": "切断指示に登録し、ロットから削除しました"}


class MoveCuttingToBatchBody(BaseModel):
    """切断指示1件を生産ロットへ戻すリクエスト"""
    cutting_id: int
    production_month: str  # YYYY-MM
    production_line: str
    product_cd: str
    product_name: str
    actual_production_quantity: Optional[int] = 0
    material_name: Optional[str] = None
    management_code: Optional[str] = None
    production_day: Optional[str] = None  # YYYY-MM-DD（未指定時は start_date/end_date から導出）
    production_order: Optional[int] = None  # ← priority_order


@router.post("/plan/batch/move-from-cutting")
async def move_cutting_to_batch(
    body: MoveCuttingToBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """
    切断指示1件を生産ロットへ戻す。
    処理順: ①切断指示を読取 ②面取指示ID取得 ③カンバン削除 ④chamfering_plans 削除 ⑤chamfering_management 削除
    ⑥cutting_management 削除 ⑦instruction_plans に INSERT。
    """
    # ① 切断指示1件を取得（削除前に全項目コピー用。cutting_machine/production_day は削除後の生産順リナンバ用）
    cut_sel = text("""
        SELECT production_month, production_line, priority_order, product_cd, product_name,
               planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
               management_code, aps_batch_plan_id, actual_production_quantity, take_count, cutting_length, chamfering_length,
               developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
               use_material_stock_sub, usage_count,
               cutting_machine, production_day
        FROM cutting_management WHERE id = :cid
    """)
    cut_res = await db.execute(cut_sel, {"cid": body.cutting_id})
    cut_row = cut_res.mappings().fetchone()
    if not cut_row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    cut = dict(cut_row)

    product_cd = (cut.get("product_cd") or body.product_cd or "").strip()
    product_name = (cut.get("product_name") or body.product_name or "").strip()
    production_line = (cut.get("production_line") or body.production_line or "").strip()
    if not product_cd or not product_name or not production_line:
        raise HTTPException(
            status_code=400,
            detail="切断指示に品番・品名・ラインが不足しています。画面データを更新してから再度お試しください。",
        )

    def _to_dt(v):
        if v is None:
            return None
        try:
            s = str(v).strip()[:19]
            if len(s) >= 10:
                parts = s[:10].split("-")
                if len(parts) == 3:
                    return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None

    def _to_float(v):
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    insert_sql = text("""
        INSERT INTO instruction_plans (
            production_month, production_line, priority_order, product_cd, product_name,
            planned_quantity, start_date, end_date, production_lot_size, lot_number,
            is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
            management_code, aps_batch_plan_id, actual_production_quantity, take_count, cutting_length, chamfering_length, developed_length, scrap_length,
            material_name, material_manufacturer, standard_specification,
            use_material_stock_sub, usage_count
        ) VALUES (
            :production_month, :production_line, :priority_order, :product_cd, :product_name,
            :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
            :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
            :management_code, :aps_batch_plan_id, :actual_production_quantity, :take_count, :cutting_length, :chamfering_length, :developed_length, :scrap_length,
            :material_name, :material_manufacturer, :standard_specification,
            :use_material_stock_sub, :usage_count
        )
        ON DUPLICATE KEY UPDATE
            id = LAST_INSERT_ID(id),
            production_month = VALUES(production_month),
            production_line = VALUES(production_line),
            priority_order = VALUES(priority_order),
            product_cd = VALUES(product_cd),
            product_name = VALUES(product_name),
            planned_quantity = VALUES(planned_quantity),
            start_date = VALUES(start_date),
            end_date = VALUES(end_date),
            production_lot_size = VALUES(production_lot_size),
            lot_number = VALUES(lot_number),
            is_cutting_instructed = VALUES(is_cutting_instructed),
            has_chamfering_process = VALUES(has_chamfering_process),
            is_chamfering_instructed = VALUES(is_chamfering_instructed),
            has_sw_process = VALUES(has_sw_process),
            is_sw_instructed = VALUES(is_sw_instructed),
            management_code = VALUES(management_code),
            aps_batch_plan_id = VALUES(aps_batch_plan_id),
            actual_production_quantity = VALUES(actual_production_quantity),
            take_count = VALUES(take_count),
            cutting_length = VALUES(cutting_length),
            chamfering_length = VALUES(chamfering_length),
            developed_length = VALUES(developed_length),
            scrap_length = VALUES(scrap_length),
            material_name = VALUES(material_name),
            material_manufacturer = VALUES(material_manufacturer),
            standard_specification = VALUES(standard_specification),
            use_material_stock_sub = VALUES(use_material_stock_sub),
            usage_count = VALUES(usage_count)
    """)
    production_month_date = _instruction_production_month_first_day(
        cut.get("production_month"), body.production_month
    )
    priority_order = cut.get("priority_order")
    if priority_order is None:
        priority_order = body.production_order

    insert_params = {
        "production_month": production_month_date,
        "production_line": production_line,
        "priority_order": priority_order,
        "product_cd": product_cd,
        "product_name": product_name,
        "planned_quantity": cut.get("planned_quantity"),
        "start_date": _to_dt(cut.get("start_date")),
        "end_date": _to_dt(cut.get("end_date")),
        "production_lot_size": cut.get("production_lot_size"),
        "lot_number": (cut.get("lot_number") or "").strip() or None,
        "is_cutting_instructed": 1 if cut.get("is_cutting_instructed") else 0,
        "has_chamfering_process": 1 if cut.get("has_chamfering_process") else 0,
        "is_chamfering_instructed": 1 if cut.get("is_chamfering_instructed") else 0,
        "has_sw_process": 1 if cut.get("has_sw_process") else 0,
        "is_sw_instructed": 1 if cut.get("is_sw_instructed") else 0,
        "management_code": (cut.get("management_code") or "").strip() or None,
        "aps_batch_plan_id": cut.get("aps_batch_plan_id") if cut.get("aps_batch_plan_id") is not None else None,
        "actual_production_quantity": cut.get("actual_production_quantity") if cut.get("actual_production_quantity") is not None else 0,
        "take_count": cut.get("take_count"),
        "cutting_length": _to_float(cut.get("cutting_length")),
        "chamfering_length": _to_float(cut.get("chamfering_length")),
        "developed_length": _to_float(cut.get("developed_length")),
        "scrap_length": _to_float(cut.get("scrap_length")),
        "material_name": (cut.get("material_name") or "").strip() or None,
        "material_manufacturer": (cut.get("material_manufacturer") or "").strip() or None,
        "standard_specification": (cut.get("standard_specification") or "").strip() or None,
        "use_material_stock_sub": 1 if cut.get("use_material_stock_sub") == 1 else 0,
        "usage_count": _to_float(cut.get("usage_count")) if cut.get("usage_count") is not None else 1.0,
    }
    # INSERT 時 BEFORE INSERT トリガーが management_code を上書きするため、重複判定はトリガー結果と同じ式で行う
    expected_management_code = _build_management_code(
        production_month=production_month_date,
        product_cd=product_cd,
        production_line=production_line,
        priority_order=insert_params.get("priority_order"),
        production_lot_size=insert_params.get("production_lot_size"),
        lot_number=insert_params.get("lot_number"),
    )
    if not (insert_params.get("management_code") or "").strip():
        insert_params["management_code"] = expected_management_code

    update_existing_ip_sql = text("""
        UPDATE instruction_plans SET
            production_month=:production_month,
            production_line=:production_line,
            priority_order=:priority_order,
            product_cd=:product_cd,
            product_name=:product_name,
            planned_quantity=:planned_quantity,
            start_date=:start_date,
            end_date=:end_date,
            production_lot_size=:production_lot_size,
            lot_number=:lot_number,
            is_cutting_instructed=:is_cutting_instructed,
            has_chamfering_process=:has_chamfering_process,
            is_chamfering_instructed=:is_chamfering_instructed,
            has_sw_process=:has_sw_process,
            is_sw_instructed=:is_sw_instructed,
            aps_batch_plan_id=:aps_batch_plan_id,
            actual_production_quantity=:actual_production_quantity,
            take_count=:take_count,
            cutting_length=:cutting_length,
            chamfering_length=:chamfering_length,
            developed_length=:developed_length,
            scrap_length=:scrap_length,
            material_name=:material_name,
            material_manufacturer=:material_manufacturer,
            standard_specification=:standard_specification,
            use_material_stock_sub=:use_material_stock_sub,
            usage_count=:usage_count
        WHERE id = :ins_id
    """)

    try:
        # ② この切断に紐づく面取指示IDを取得（カンバン削除用）
        chamfering_res = await db.execute(
            text("SELECT id FROM chamfering_management WHERE cutting_management_id = :cid"),
            {"cid": body.cutting_id},
        )
        chamfering_ids = [r[0] for r in chamfering_res.fetchall() if r[0] is not None]

        # ③ カンバン発行を削除（切断由来 + 面取由来）
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'cutting' AND source_id = :cid"),
            {"cid": body.cutting_id},
        )
        for chamfering_id in chamfering_ids:
            await db.execute(
                text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
                {"sid": chamfering_id},
            )

        # ④ 面取ロット一覧を先に削除（FK 構成差で面取指示より先に消す必要がある環境向け）
        await db.execute(
            text("DELETE FROM chamfering_plans WHERE cutting_management_id = :cid"),
            {"cid": body.cutting_id},
        )

        # ⑤ 面取指示を削除
        await db.execute(
            text("DELETE FROM chamfering_management WHERE cutting_management_id = :cid"),
            {"cid": body.cutting_id},
        )

        # ⑤ 面取指示を削除
        await db.execute(text("DELETE FROM cutting_management WHERE id = :cid"), {"cid": body.cutting_id})

        # ⑥' 同一切断機・同一生産日の残り行の生産順を 1,2,3... にリナンバ
        cm = (cut.get("cutting_machine") or "").strip()
        pd = cut.get("production_day")
        if cm and pd is not None:
            pd_str = str(pd)[:10] if pd else None
            if pd_str:
                remain = await db.execute(
                    text("""
                        SELECT id FROM cutting_management
                        WHERE cutting_machine = :cm AND production_day = :pd
                        ORDER BY production_sequence ASC, id ASC
                    """),
                    {"cm": cm, "pd": pd_str},
                )
                remain_ids = [r[0] for r in remain.fetchall() if r[0] is not None]
                for seq, rid in enumerate(remain_ids, start=1):
                    await db.execute(
                        text("UPDATE cutting_management SET production_sequence = :seq WHERE id = :id"),
                        {"seq": seq, "id": rid},
                    )

        # ⑦ 生産ロットへ反映（新規 INSERT または既存行 UPDATE）
        # 合算・APS 同期の重複で同一 management_code の行が残っていると UNIQUE で INSERT が 409 になるため、
        # トリガーと同じ management_code で既存を検出したら UPDATE のみ行う。
        bid0 = insert_params.get("aps_batch_plan_id")
        if bid0 is not None:
            chk_bp = await db.execute(
                text("SELECT 1 FROM aps_batch_plans WHERE id = :id LIMIT 1"),
                {"id": int(bid0)},
            )
            if chk_bp.scalar_one_or_none() is None:
                insert_params["aps_batch_plan_id"] = None

        existing_ip_id: Optional[int] = None
        # 最優先: aps_batch_plan_id（唯一キー）で既存行を特定する
        # management_code 先行だと「別行に紐づく aps_batch_plan_id」を上書きして 409 を再発し得る。
        if insert_params.get("aps_batch_plan_id") is not None:
            ex_bid = await db.execute(
                text(
                    "SELECT id FROM instruction_plans WHERE aps_batch_plan_id = :bid ORDER BY id ASC LIMIT 1"
                ),
                {"bid": int(insert_params["aps_batch_plan_id"])},
            )
            row_b = ex_bid.mappings().fetchone()
            if row_b and row_b.get("id") is not None:
                existing_ip_id = int(row_b["id"])
        if existing_ip_id is None:
            ex_mc = await db.execute(
                text(
                    "SELECT id FROM instruction_plans "
                    "WHERE TRIM(COALESCE(management_code, '')) = TRIM(:mc) ORDER BY id ASC LIMIT 1"
                ),
                {"mc": expected_management_code},
            )
            row_mc = ex_mc.mappings().fetchone()
            if row_mc and row_mc.get("id") is not None:
                existing_ip_id = int(row_mc["id"])

        if existing_ip_id is not None:
            up = {**insert_params, "ins_id": existing_ip_id}
            await db.execute(update_existing_ip_sql, up)
            await db.flush()
            ins_id = existing_ip_id
        else:
            await db.execute(insert_sql, insert_params)
            await db.flush()
            ins_id_res = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
            ins_id_row = ins_id_res.mappings().fetchone()
            ins_id = int(ins_id_row["id"]) if ins_id_row and ins_id_row.get("id") is not None else None
            if ins_id is None:
                raise HTTPException(
                    status_code=500,
                    detail="instruction_plans の登録に失敗しました（INSERT 後の ID が取得できません）",
                )

        # ⑦' 追加情報を補完
        # - APS ロットとの紐付けを復元（aps_batch_plan_id）
        # - キャンセル済み行は release_cancelled_* フラグで除外
        if ins_id is not None:
            lot_no = (insert_params.get("lot_number") or "").strip() if insert_params.get("lot_number") else ""
            pcd = (insert_params.get("product_cd") or "").strip()
            pline = (insert_params.get("production_line") or "").strip()

            aps_batch_plan_id = None
            if lot_no and pcd:
                aps_q = await db.execute(
                    text(
                        "SELECT id FROM aps_batch_plans "
                        "WHERE lot_number = :lot_no AND product_cd = :pcd "
                        "AND (:pline = '' OR production_line = :pline) "
                        "ORDER BY id DESC LIMIT 1"
                    ),
                    {"lot_no": lot_no, "pcd": pcd, "pline": pline},
                )
                aps_batch_plan_id = aps_q.scalar()

            if aps_batch_plan_id is not None:
                await db.execute(
                    text("UPDATE instruction_plans SET aps_batch_plan_id = :bid WHERE id = :iid"),
                    {"bid": int(aps_batch_plan_id), "iid": ins_id},
                )

            rollback_by = (
                (getattr(current_user, "user_cd", None) or "")
                or (getattr(current_user, "username", None) or "")
                or (getattr(current_user, "name", None) or "")
                or "system"
            )
            try:
                await db.execute(
                    text(
                        "UPDATE instruction_plans SET "
                        "release_cancelled_at = :ts, "
                        "release_cancel_reason = :reason, "
                        "release_cancel_by = :rb "
                        "WHERE id = :iid"
                    ),
                    {
                        "ts": datetime.now(),
                        "reason": "cutting_management から instruction_plans へ戻し",
                        "rb": str(rollback_by)[:64],
                        "iid": ins_id,
                    },
                )
            except Exception:
                # 旧スキーマ（103 未適用）では列が存在しないためスキップ
                pass

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        orig = getattr(e, "orig", None)
        detail = str(orig) if orig is not None else str(e)
        raise HTTPException(
            status_code=409,
            detail=f"instruction_plans への登録で整合性エラーが発生しました: {detail}",
        ) from e
    except Exception as e:
        await db.rollback()
        msg = str(e).lower()
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="instruction_plans テーブルが存在しません。") from e
        if "cutting_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
        logger.exception("move_cutting_to_batch failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"success": True, "message": "生産ロットに戻しました（切断・面取・カンバンを削除済み）"}


class ReorderCuttingBody(BaseModel):
    """需求量サマリーと溶接ベース使用量サマリーを1回で返す。"""
    cutting_machine: str
    ordered_ids: list[int]  # この順に production_sequence を 1,2,3,... で更新（最小1）


@router.post("/plan/cutting-management/reorder")
async def reorder_cutting_management(
    body: ReorderCuttingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """
    切断指示の生産順（production_sequence）を、同一切断機内で指定した ID 順に更新する。
    """
    cutting_machine = (body.cutting_machine or "").strip()
    if not cutting_machine:
        raise HTTPException(status_code=400, detail="切断機を指定してください")
    if not body.ordered_ids:
        return {"success": True, "message": "変更なし"}

    try:
        for idx, row_id in enumerate(body.ordered_ids):
            await db.execute(
                text("""
                    UPDATE cutting_management
                    SET production_sequence = :production_sequence
                    WHERE id = :id AND cutting_machine = :cutting_machine
                """),
                {"production_sequence": idx + 1, "id": row_id, "cutting_machine": cutting_machine},
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "生成順を更新しました"}


class UpdateCuttingManagementBody(BaseModel):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    production_day: Optional[str] = None  # YYYY-MM-DD
    cutting_machine: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    production_sequence: Optional[int] = None
    production_completed_check: Optional[bool] = None
    remarks: Optional[str] = None
    defect_qty: Optional[int] = None
    use_material_stock_sub: Optional[int] = None  # 0/1
    usage_count: Optional[float] = None  # 1=1本, <1=按分
    start_date: Optional[str] = None  # YYYY-MM-DD（空文字でクリア）
    end_date: Optional[str] = None  # YYYY-MM-DD（空文字でクリア）
    mes_production_started_at: Optional[str] = None  # ISO8601（生産開始）
    mes_production_ended_at: Optional[str] = None  # ISO8601（生産終了）
    mes_net_production_sec: Optional[int] = None  # 正味生産時間（秒）
    mes_paused_accum_sec: Optional[int] = None  # 中断累計（秒）
    mes_production_is_paused: Optional[int] = None  # 0=稼働中, 1=中断中（未設定は NULL）
    mes_setup_time_min: Optional[int] = None  # 段取（分）
    mes_saw_blade_exchange_min: Optional[int] = None  # のこ刃交換（分）
    mes_repair_min: Optional[int] = None  # 修理（分）
    mes_operator_user_id: Optional[int] = None  # users.id（0 は未設定扱い）
    mes_scanned_code: Optional[str] = None  # バーコード/QR 読取値（任意）


@router.patch("/plan/cutting-management/{cutting_id}")
async def update_cutting_management(
    cutting_id: int,
    body: UpdateCuttingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """切断指示の生成順を変更するリクエスト（同一切断機内）"""
    cm_cols = await _get_cutting_mgmt_columns(db)
    updates: list[str] = []
    params: dict = {"cid": cutting_id}
    if body.production_day is not None:
        _pd = body.production_day.strip()[:10] if body.production_day and len(body.production_day.strip()) >= 10 else None
        if _pd:
            try:
                parts = _pd.split("-")
                if len(parts) == 3:
                    params["production_day"] = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    updates.append("production_day = :production_day")
            except (ValueError, IndexError):
                pass
    if body.cutting_machine is not None:
        new_cm = (body.cutting_machine or "").strip()
        if not new_cm:
            raise HTTPException(status_code=500, detail="切断指示の登録に失敗しました")
        cur = await db.execute(
            text("""
                SELECT cutting_machine, production_completed_check,
                       mes_production_started_at, mes_production_ended_at
                FROM cutting_management
                WHERE id = :cid
                LIMIT 1
            """),
            {"cid": cutting_id},
        )
        cur_row = cur.fetchone()
        if not cur_row:
            raise HTTPException(status_code=404, detail="切断指示が見つかりません")
        old_cm = (str(cur_row[0]).strip() if cur_row[0] else "")
        if old_cm != new_cm:
            if int(cur_row[1] or 0) == 1:
                raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
            if "mes_production_ended_at" in cm_cols:
                ended_at = cur_row[3]
                if ended_at is not None and str(ended_at).strip():
                    raise HTTPException(status_code=400, detail="生産日が不正です")
            if "mes_production_started_at" in cm_cols and "mes_production_ended_at" in cm_cols:
                started_at = cur_row[2]
                ended_at = cur_row[3]
                if started_at is not None and str(started_at).strip():
                    if ended_at is None or not str(ended_at).strip():
                        raise HTTPException(status_code=400, detail="生産日が不正です")
        updates.append("cutting_machine = :cutting_machine")
        params["cutting_machine"] = new_cm
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.production_sequence is not None:
        updates.append("production_sequence = :production_sequence")
        params["production_sequence"] = body.production_sequence
    if body.production_completed_check is not None:
        updates.append("production_completed_check = :production_completed_check")
        params["production_completed_check"] = 1 if body.production_completed_check else 0
    if body.remarks is not None:
        updates.append("remarks = :remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if body.defect_qty is not None:
        updates.append("defect_qty = :defect_qty")
        params["defect_qty"] = max(0, body.defect_qty)
    if body.use_material_stock_sub is not None:
        updates.append("use_material_stock_sub = :use_material_stock_sub")
        params["use_material_stock_sub"] = 1 if body.use_material_stock_sub == 1 else 0
    if body.usage_count is not None:
        try:
            uc = float(body.usage_count)
            if uc > 0:
                updates.append("usage_count = :usage_count")
                params["usage_count"] = uc
        except (TypeError, ValueError):
            pass
    if body.start_date is not None:
        sd = body.start_date.strip()[:10] if body.start_date and len(body.start_date.strip()) >= 10 else None
        if sd:
            try:
                parts = sd.split("-")
                if len(parts) == 3:
                    params["start_date"] = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    updates.append("start_date = :start_date")
            except (ValueError, IndexError):
                pass
        else:
            updates.append("start_date = NULL")
    if body.end_date is not None:
        ed = body.end_date.strip()[:10] if body.end_date and len(body.end_date.strip()) >= 10 else None
        if ed:
            try:
                parts = ed.split("-")
                if len(parts) == 3:
                    params["end_date"] = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    updates.append("end_date = :end_date")
            except (ValueError, IndexError):
                pass
        else:
            updates.append("end_date = NULL")
    if body.mes_production_started_at is not None:
        if "mes_production_started_at" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_production_started_at"))
        raw = body.mes_production_started_at.strip() if isinstance(body.mes_production_started_at, str) else ""
        if raw == "":
            updates.append("mes_production_started_at = NULL")
        else:
            sdt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_started_at)
            if sdt:
                await _reject_concurrent_mes_production_on_machine(db, cutting_id, cm_cols)
                params["mes_production_started_at"] = sdt
                updates.append("mes_production_started_at = :mes_production_started_at")
    if body.mes_production_ended_at is not None:
        if "mes_production_ended_at" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_production_ended_at"))
        raw = body.mes_production_ended_at.strip() if isinstance(body.mes_production_ended_at, str) else ""
        if raw == "":
            updates.append("mes_production_ended_at = NULL")
        else:
            edt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_ended_at)
            if edt:
                params["mes_production_ended_at"] = edt
                updates.append("mes_production_ended_at = :mes_production_ended_at")
    if body.mes_net_production_sec is not None:
        if "mes_net_production_sec" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_net_production_sec"))
        net_sec = int(body.mes_net_production_sec)
        if net_sec < 0:
            updates.append("mes_net_production_sec = NULL")
        else:
            updates.append("mes_net_production_sec = :mes_net_production_sec")
            params["mes_net_production_sec"] = max(0, net_sec)
    if body.mes_paused_accum_sec is not None:
        if "mes_paused_accum_sec" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_paused_accum_sec"))
        pause_sec = int(body.mes_paused_accum_sec)
        if pause_sec < 0:
            updates.append("mes_paused_accum_sec = NULL")
        else:
            updates.append("mes_paused_accum_sec = :mes_paused_accum_sec")
            params["mes_paused_accum_sec"] = max(0, pause_sec)
    if body.mes_production_is_paused is not None:
        if "mes_production_is_paused" not in cm_cols:
            raise HTTPException(
                status_code=503, detail=_mes_column_migration_hint("mes_production_is_paused")
            )
        flag = int(body.mes_production_is_paused)
        if flag < 0:
            updates.append("mes_production_is_paused = NULL")
        else:
            params["mes_production_is_paused"] = 1 if flag else 0
            updates.append("mes_production_is_paused = :mes_production_is_paused")
    if body.mes_setup_time_min is not None:
        if "mes_setup_time_min" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_setup_time_min"))
        setup_min = int(body.mes_setup_time_min)
        if setup_min < 0:
            updates.append("mes_setup_time_min = NULL")
        else:
            updates.append("mes_setup_time_min = :mes_setup_time_min")
            params["mes_setup_time_min"] = max(0, setup_min)
    if body.mes_saw_blade_exchange_min is not None:
        if "mes_saw_blade_exchange_min" not in cm_cols:
            raise HTTPException(
                status_code=503, detail=_mes_column_migration_hint("mes_saw_blade_exchange_min")
            )
        blade_min = int(body.mes_saw_blade_exchange_min)
        if blade_min < 0:
            updates.append("mes_saw_blade_exchange_min = NULL")
        else:
            updates.append("mes_saw_blade_exchange_min = :mes_saw_blade_exchange_min")
            params["mes_saw_blade_exchange_min"] = max(0, blade_min)
    if body.mes_repair_min is not None:
        if "mes_repair_min" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_repair_min"))
        repair_min = int(body.mes_repair_min)
        if repair_min < 0:
            updates.append("mes_repair_min = NULL")
        else:
            updates.append("mes_repair_min = :mes_repair_min")
            params["mes_repair_min"] = max(0, repair_min)
    if body.mes_operator_user_id is not None:
        if "mes_operator_user_id" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_operator_user_id"))
        oid = int(body.mes_operator_user_id)
        if oid <= 0:
            updates.append("mes_operator_user_id = NULL")
        else:
            params["mes_operator_user_id"] = oid
            updates.append("mes_operator_user_id = :mes_operator_user_id")
    if body.mes_scanned_code is not None:
        if "mes_scanned_code" not in cm_cols:
            raise HTTPException(status_code=503, detail=_mes_column_migration_hint("mes_scanned_code"))
        raw_mc = body.mes_scanned_code.strip() if isinstance(body.mes_scanned_code, str) else ""
        if raw_mc == "":
            updates.append("mes_scanned_code = NULL")
        else:
            params["mes_scanned_code"] = raw_mc[:512]
            updates.append("mes_scanned_code = :mes_scanned_code")
    if not updates:
        return {"success": True, "message": "変更なし"}
    try:
        await db.execute(
            text(f"""
                UPDATE cutting_management
                SET {", ".join(updates)}
                WHERE id = :cid
            """),
            params,
        )
        # 面取ロット一覧（chamfering_plans）の同期: production_day / actual_production_quantity を更新
        chamfering_updates: list[str] = []
        chamfering_params: dict = {"cid": cutting_id}
        if "production_day" in params:
            chamfering_updates.append("production_day = :production_day")
            chamfering_params["production_day"] = params["production_day"]
        if "actual_production_quantity" in params:
            chamfering_updates.append("actual_production_quantity = :actual_production_quantity")
            chamfering_params["actual_production_quantity"] = params["actual_production_quantity"]
        if chamfering_updates:
            await db.execute(
                text(f"""
                    UPDATE chamfering_plans
                    SET {", ".join(chamfering_updates)}
                    WHERE cutting_management_id = :cid
                """),
                chamfering_params,
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class SplitToNextDayBody(BaseModel):
    """生産数未完了分を翌日へ順延する時のリクエスト"""
    today_quantity: int  # 当日完成数
    next_day: Optional[str] = None  # 翌日とする日付 YYYY-MM-DD（省略時は production_day + 1 日）


@router.post("/plan/cutting-management/{cutting_id}/split-to-next-day")
async def split_cutting_to_next_day(
    cutting_id: int,
    body: SplitToNextDayBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """
    指定日の切断実績を一括確定し在庫へ反映
    - 当日行: actual_production_quantity = today_quantity に更新
    - 翌日行: 新規INSERT（同一製品・同一切断機、production_day=翌日、actual_production_quantity=残り）
    """
    if body.today_quantity < 0:
        raise HTTPException(status_code=400, detail="当日完成数は0以上を指定してください")
    sel = text("""
        SELECT production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
               product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
               management_code, aps_batch_plan_id, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
               developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
               production_completed_check, remarks, use_material_stock_sub, usage_count
        FROM cutting_management WHERE id = :cid
    """)
    res = await db.execute(sel, {"cid": cutting_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    r = dict(row)
    total = int(r.get("actual_production_quantity") or 0)
    if body.today_quantity >= total:
        raise HTTPException(
            status_code=400,
            detail=f"当日完成数は、現在の生産数（{total}）より少ない値を指定してください（未完了分が翌日へコピーされます）",
        )
    remainder = total - body.today_quantity

    # 翌日日付
    try:
        pd = r.get("production_day")
        if hasattr(pd, "isoformat"):
            pd_str = pd.isoformat()[:10]
        else:
            pd_str = str(pd)[:10] if pd else ""
        if body.next_day and len((body.next_day or "").strip()) >= 10:
            next_day_str = body.next_day.strip()[:10]
        else:
            if pd:
                if hasattr(pd, "year"):
                    next_d = pd + timedelta(days=1)
                else:
                    parts = pd_str.split("-")
                    if len(parts) == 3:
                        next_d = date(int(parts[0]), int(parts[1]), int(parts[2])) + timedelta(days=1)
                    else:
                        raise HTTPException(status_code=400, detail="生産日が不正です")
                next_day_str = next_d.isoformat()[:10]
            else:
                raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        parts = next_day_str.split("-")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="翌日日付の形式は YYYY-MM-DD です")
        next_day_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"日付が不正です: {e}") from e

    # 翌日の production_month（その月の1日）
    next_month_date = date(next_day_date.year, next_day_date.month, 1)
    cm = (r.get("cutting_machine") or "").strip()
    if not cm:
        raise HTTPException(status_code=400, detail="切断機が空のため順延できません")

    try:
        # 5) 同一生産月の既存データを削除
        await db.execute(
            text("""
                UPDATE cutting_management
                SET actual_production_quantity = :qty
                WHERE id = :cid
            """),
            {"cid": cutting_id, "qty": body.today_quantity},
        )
        # 1') 面取ロット一覧（chamfering_plans）の生産数も同期
        await db.execute(
            text("UPDATE chamfering_plans SET actual_production_quantity = :qty WHERE cutting_management_id = :cid"),
            {"cid": cutting_id, "qty": body.today_quantity},
        )
        # 2) 翌日・同一切断機の既存行の production_sequence を +1 して、順延行を先頭（1）に挿入
        await db.execute(
            text("""
                UPDATE cutting_management
                SET production_sequence = production_sequence + 1
                WHERE cutting_machine = :cm AND production_day = :nd
            """),
            {"cm": cm, "nd": next_day_date},
        )
        next_seq = 1  # 順延データを翌日の先頭に
        # 3) 翌日行を INSERT（残り数量、生産順=1）
        params = {k: r.get(k) for k in (
            "production_line", "cutting_machine", "priority_order",
            "product_cd", "product_name", "planned_quantity", "start_date", "end_date", "production_lot_size", "lot_number",
            "is_cutting_instructed", "has_chamfering_process", "is_chamfering_instructed", "has_sw_process", "is_sw_instructed",
            "management_code", "aps_batch_plan_id", "take_count", "cutting_length", "chamfering_length",
            "developed_length", "scrap_length", "material_name", "material_manufacturer", "standard_specification", "remarks",
            "use_material_stock_sub", "usage_count"
        )}
        params["production_month"] = next_month_date
        params["production_day"] = next_day_date
        params["production_sequence"] = next_seq
        params["actual_production_quantity"] = remainder
        params["defect_qty"] = r.get("defect_qty") or 0
        if params.get("use_material_stock_sub") is None:
            params["use_material_stock_sub"] = 0
        if params.get("usage_count") is None:
            params["usage_count"] = 1.0
        ins = text("""
            INSERT INTO cutting_management (
                production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
                product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
                is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                management_code, aps_batch_plan_id, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
                developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                production_completed_check, remarks, use_material_stock_sub, usage_count
            ) VALUES (
                :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
                :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
                :management_code, :aps_batch_plan_id, :actual_production_quantity, :defect_qty, :take_count, :cutting_length, :chamfering_length,
                :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification,
                0, :remarks, :use_material_stock_sub, :usage_count
            )
        """)
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "生産ロットに戻しました（切断・面取・カンバンを削除済み）"}


@router.post("/plan/cutting-management/{cutting_id}/duplicate")
async def duplicate_cutting_management(
    cutting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    sel = text("""
        SELECT production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
               product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
               management_code, aps_batch_plan_id, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
               developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
               production_completed_check, remarks, use_material_stock_sub, usage_count
        FROM cutting_management WHERE id = :cid
    """)
    res = await db.execute(sel, {"cid": cutting_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    r = dict(row)
    cm = (r.get("cutting_machine") or "").strip()
    if not cm:
        raise HTTPException(status_code=400, detail="切断機が空のため順延できません")
    current_seq = int(r.get("production_sequence") or 0)

    try:
        await db.execute(
            text("""
                UPDATE cutting_management SET production_sequence = production_sequence + 1
                WHERE cutting_machine = :cm AND production_sequence > :seq
            """),
            {"cm": cm, "seq": current_seq},
        )
        ins = text("""
            INSERT INTO cutting_management (
                production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
                product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
                is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                management_code, aps_batch_plan_id, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
                developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                production_completed_check, remarks, use_material_stock_sub, usage_count
            ) VALUES (
                :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
                :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
                :management_code, :aps_batch_plan_id, :actual_production_quantity, :defect_qty, :take_count, :cutting_length, :chamfering_length,
                :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification,
                0, :remarks, :use_material_stock_sub, :usage_count
            )
        """)
        params = {k: r.get(k) for k in (
            "production_month", "production_day", "production_line", "cutting_machine", "priority_order",
            "product_cd", "product_name", "planned_quantity", "start_date", "end_date", "production_lot_size", "lot_number",
            "is_cutting_instructed", "has_chamfering_process", "is_chamfering_instructed", "has_sw_process", "is_sw_instructed",
            "management_code", "aps_batch_plan_id", "actual_production_quantity", "defect_qty", "take_count", "cutting_length", "chamfering_length",
            "developed_length", "scrap_length", "material_name", "material_manufacturer", "standard_specification", "remarks",
            "use_material_stock_sub", "usage_count"
        )}
        params["production_sequence"] = current_seq + 1
        if params.get("use_material_stock_sub") is None:
            params["use_material_stock_sub"] = 0
        if params.get("usage_count") is None:
            params["usage_count"] = 1.0
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/cutting-management/{cutting_id}")
async def delete_cutting_management(
    cutting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    try:
        chamfering_res = await db.execute(
            text("SELECT id FROM chamfering_management WHERE cutting_management_id = :cid"),
            {"cid": cutting_id},
        )
        chamfering_ids = [r[0] for r in chamfering_res.fetchall() if r[0] is not None]
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'cutting' AND source_id = :cid"),
            {"cid": cutting_id},
        )
        for sid in chamfering_ids:
            await db.execute(
                text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
                {"sid": sid},
            )
        await db.execute(text("DELETE FROM chamfering_management WHERE cutting_management_id = :cid"), {"cid": cutting_id})
        await db.execute(text("DELETE FROM chamfering_plans WHERE cutting_management_id = :cid"), {"cid": cutting_id})
        await db.execute(text("DELETE FROM cutting_management WHERE id = :cid"), {"cid": cutting_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


# ---------- 面取ロット一覧（chamfering_plans）----------
@router.get("/plan/chamfering-plans/list")
async def get_chamfering_plans_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    production_line: Optional[str] = Query(None, description="ライン（部分一致）"),
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット一覧: chamfering_plans を取得（切断指示登録時・面取工程ありで自動登録された待機データ）。"""
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if production_day and production_day.strip():
        try:
            parts = production_day.strip().split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                params["production_day"] = date(y, m, d)
                conditions.append("production_day = :production_day")
        except (ValueError, IndexError):
            pass
    if production_line and production_line.strip():
        conditions.append("production_line LIKE :production_line")
        params["production_line"] = f"%{production_line.strip()}%"

    sql = text(f"""
        SELECT id, cutting_management_id, production_month, production_day, production_line, production_order,
               product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
               cutting_length, chamfering_length, developed_length, material_name, management_code, cd, has_sw_process, created_at
        FROM chamfering_plans
        WHERE {" AND ".join(conditions)}
        ORDER BY production_month DESC, production_day DESC, production_line, production_order
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
    except Exception as e:
        msg = str(e).lower()
        if "chamfering_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="chamfering_plans テーブルが存在しません。マイグレーション 063_chamfering_batch.sql を実行してください。",
            ) from e
        raise
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _row(r):
        row = dict(r)
        pm = _v(row, "production_month")
        pd = _v(row, "production_day")
        return {
            "id": row.get("id"),
            "cutting_management_id": row.get("cutting_management_id"),
            "production_month": (str(pm)[:10] if pm else None),
            "production_day": (str(pd)[:10] if pd else None),
            "production_line": row.get("production_line"),
            "production_order": row.get("production_order"),
            "product_cd": row.get("product_cd"),
            "product_name": row.get("product_name"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": row.get("lot_number"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "material_name": row.get("material_name"),
            "management_code": row.get("management_code"),
            "cd": row.get("cd") or (str(row.get("management_code") or "")[-5:] or None),
            "has_sw_process": 1 if row.get("has_sw_process") else 0,
            "created_at": _v(row, "created_at"),
        }
    data = [_row(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


class CreateChamferingPlanBody(BaseModel):
    """面取ロット一覧：新規追加（chamfering_plans に1件INSERT、cutting_management_id は NULL）"""
    production_month: str  # YYYY-MM
    production_day: str  # YYYY-MM-DD
    production_line: str  # ライン（面取機）
    production_order: Optional[int] = None
    product_cd: str
    product_name: str
    actual_production_quantity: Optional[int] = 0
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    material_name: Optional[str] = None
    has_sw_process: Optional[int] = 0


@router.post("/plan/chamfering-plans")
async def create_chamfering_plan(
    body: CreateChamferingPlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """面取ロット一覧に新規1件追加（cutting_management_id は NULL）。management_code / cd はトリガーで自動設定。"""
    production_month_date = _parse_date_ymd(body.production_month)
    production_day_date = _parse_date_ymd(body.production_day)
    if production_month_date is None:
        raise HTTPException(status_code=400, detail="生産月（production_month）を YYYY-MM 形式で指定してください")
    if production_day_date is None:
        raise HTTPException(status_code=400, detail="生産日（production_day）を YYYY-MM-DD 形式で指定してください")
    line = (body.production_line or "").strip()
    if not line:
        raise HTTPException(status_code=400, detail="切断機を指定してください")
    product_cd = (body.product_cd or "").strip()
    product_name = (body.product_name or "").strip()
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="製品CD・製品名を指定してください")

    ins = text("""
        INSERT INTO chamfering_plans (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, material_name, has_sw_process
        ) VALUES (
            NULL, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :material_name, :has_sw_process
        )
    """)
    params = {
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": line,
        "production_order": body.production_order,
        "product_cd": product_cd,
        "product_name": product_name,
        "actual_production_quantity": body.actual_production_quantity if body.actual_production_quantity is not None else 0,
        "production_lot_size": body.production_lot_size,
        "lot_number": (body.lot_number or "").strip() or None,
        "cutting_length": body.cutting_length,
        "chamfering_length": body.chamfering_length,
        "developed_length": body.developed_length,
        "material_name": (body.material_name or "").strip() or None,
        "has_sw_process": 1 if body.has_sw_process else 0,
    }
    try:
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class MoveChamferingPlanToChamferingBody(BaseModel):
    """面取ロット1件を面取指示へ移行（オプションで生産日・ライン指定。SW時は production_line_2 で2件登録）"""
    chamfering_plan_id: int
    production_day: Optional[str] = None  # YYYY-MM-DD、指定時はこれを使用
    production_line: Optional[str] = None  # ライン/面取機、指定時はこれを使用
    production_line_2: Optional[str] = None  # SW時用の2台目面取機、指定時は2件INSERT


@router.post("/plan/chamfering-plans/move-to-chamfering")
async def move_chamfering_plan_to_chamfering(
    body: MoveChamferingPlanToChamferingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """面取ロット1件を面取指示（chamfering_management）へ移行し、chamfering_plans から削除。production_line_2 指定時は2件登録。"""
    res = await db.execute(
        text("""
            SELECT id, cutting_management_id, production_month, production_day, production_line, production_order,
                   product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                   cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process, no_count
            FROM chamfering_plans WHERE id = :bid
        """),
        {"bid": body.chamfering_plan_id},
    )
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    row = dict(row)

    def _to_date(v):
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        s = str(v).strip()[:10]
        if len(s) == 10:
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
            except (ValueError, IndexError):
                pass
        return date.today()

    if body.production_day and str(body.production_day).strip()[:10]:
        production_day_date = _to_date(str(body.production_day).strip()[:10]) or date.today()
    else:
        production_day_val = row.get("production_day")
        production_day_date = _to_date(production_day_val) or date.today()

    production_month_val = row.get("production_month")
    production_month_date = _to_date(production_month_val) or date.today()

    production_line_val = (body.production_line and str(body.production_line).strip()) or (row.get("production_line") or "").strip() or ""
    production_line_2_val = (body.production_line_2 and str(body.production_line_2).strip()) or None

    def _params(pl: str, chamfering_machine_val: str, production_sequence_val: int):
        return {
            "cutting_management_id": row.get("cutting_management_id"),
            "production_month": production_month_date,
            "production_day": production_day_date,
            "production_line": (row.get("production_line") or "").strip() or "",  # ライン：面取ロットのラインをそのまま使用（面取機ではない）
            "chamfering_machine": chamfering_machine_val or pl,
            "production_order": row.get("production_order"),
            "production_sequence": production_sequence_val,
            "product_cd": (row.get("product_cd") or "").strip() or "",
            "product_name": (row.get("product_name") or "").strip() or "",
            "actual_production_quantity": row.get("actual_production_quantity") or 0,
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": (row.get("lot_number") or "").strip() or None,
            "cutting_length": float(row["cutting_length"]) if row.get("cutting_length") is not None else None,
            "chamfering_length": float(row["chamfering_length"]) if row.get("chamfering_length") is not None else None,
            "developed_length": float(row["developed_length"]) if row.get("developed_length") is not None else None,
            "production_time": None,
            "material_name": (row.get("material_name") or "").strip() or None,
            "management_code": (row.get("management_code") or "").strip() or None,
            "has_sw_process": 1 if row.get("has_sw_process") else 0,
            "remarks": None,
            "no_count": 1 if row.get("no_count") else 0,
        }

    ins = text("""
        INSERT INTO chamfering_management (
            cutting_management_id, production_month, production_day, production_line, chamfering_machine, production_order, production_sequence,
            product_cd, product_name, actual_production_quantity, defect_qty, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, production_time, material_name, management_code, has_sw_process, production_completed_check, no_count, remarks
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :chamfering_machine, :production_order, :production_sequence,
            :product_cd, :product_name, :actual_production_quantity, 0, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :production_time, :material_name, :management_code, :has_sw_process, 0, :no_count, :remarks
        )
    """)
    try:
        order_res = await db.execute(
            text("""
                SELECT COALESCE(MAX(production_sequence), 0) + 1 AS next_seq
                FROM chamfering_management
                WHERE chamfering_machine = :cm AND production_day = :pd
            """),
            {"cm": production_line_val, "pd": production_day_date},
        )
        next_seq_1 = int(order_res.scalar() or 1)
        await db.execute(ins, _params(production_line_val, production_line_val, next_seq_1))
        if production_line_2_val:
            order_res2 = await db.execute(
                text("""
                    SELECT COALESCE(MAX(production_sequence), 0) + 1 AS next_seq
                    FROM chamfering_management
                    WHERE chamfering_machine = :cm AND production_day = :pd
                """),
                {"cm": production_line_2_val, "pd": production_day_date},
            )
            next_seq_2 = int(order_res2.scalar() or 1)
            await db.execute(ins, _params(production_line_2_val, production_line_2_val, next_seq_2))
        await db.execute(text("DELETE FROM chamfering_plans WHERE id = :bid"), {"bid": body.chamfering_plan_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "レコードを追加しました"}


class UpdateChamferingPlanSwBody(BaseModel):
    """面取ロットのSW工程フラグ更新"""
    has_sw_process: bool


class UpdateChamferingPlanContentBody(BaseModel):
    """面取ロット内容編集（ロット内容編集窗体と同様の項目のうち chamfering_plans に存在するもの）"""
    production_month: Optional[str] = None
    production_day: Optional[str] = None
    production_line: Optional[str] = None
    production_order: Optional[int] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    material_name: Optional[str] = None
    has_sw_process: Optional[bool] = None


@router.patch("/plan/chamfering-plans/{plan_id}")
async def update_chamfering_plan_sw(
    plan_id: int,
    body: UpdateChamferingPlanSwBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """面取ロット1件のhas_sw_processを更新。"""
    try:
        await db.execute(
            text("UPDATE chamfering_plans SET has_sw_process = :v WHERE id = :pid"),
            {"v": 1 if body.has_sw_process else 0, "pid": plan_id},
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/chamfering-plans/{plan_id}")
async def delete_chamfering_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    """面取ロット1件を削除。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_plans WHERE id = :pid"),
        {"pid": plan_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    try:
        await db.execute(text("DELETE FROM chamfering_plans WHERE id = :pid"), {"pid": plan_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.put("/plan/chamfering-plans/{plan_id}/content")
async def update_chamfering_plan_content(
    plan_id: int,
    body: UpdateChamferingPlanContentBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """面取ロット1件の内容を更新（ロット内容編集と同様の項目）。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_plans WHERE id = :pid"),
        {"pid": plan_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    updates = []
    params = {"pid": plan_id}
    if body.production_month is not None:
        d = _parse_date_ymd(body.production_month)
        if d is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = d
    if body.production_day is not None:
        d = _parse_date_ymd(body.production_day)
        if d is not None:
            updates.append("production_day = :production_day")
            params["production_day"] = d
    if body.production_line is not None:
        updates.append("production_line = :production_line")
        params["production_line"] = body.production_line.strip() or None
    if body.production_order is not None:
        updates.append("production_order = :production_order")
        params["production_order"] = body.production_order
    if body.product_cd is not None:
        updates.append("product_cd = :product_cd")
        params["product_cd"] = body.product_cd.strip() or None
    if body.product_name is not None:
        updates.append("product_name = :product_name")
        params["product_name"] = body.product_name.strip() or None
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.production_lot_size is not None:
        updates.append("production_lot_size = :production_lot_size")
        params["production_lot_size"] = body.production_lot_size
    if body.lot_number is not None:
        updates.append("lot_number = :lot_number")
        params["lot_number"] = body.lot_number.strip() or None
    if body.cutting_length is not None:
        updates.append("cutting_length = :cutting_length")
        params["cutting_length"] = body.cutting_length
    if body.chamfering_length is not None:
        updates.append("chamfering_length = :chamfering_length")
        params["chamfering_length"] = body.chamfering_length
    if body.developed_length is not None:
        updates.append("developed_length = :developed_length")
        params["developed_length"] = body.developed_length
    if body.material_name is not None:
        updates.append("material_name = :material_name")
        params["material_name"] = body.material_name.strip() or None
    if body.has_sw_process is not None:
        updates.append("has_sw_process = :has_sw_process")
        params["has_sw_process"] = 1 if body.has_sw_process else 0
    if not updates:
        return {"success": True, "message": "変更なし"}
    set_clause = ", ".join(updates)
    try:
        await db.execute(
            text(f"UPDATE chamfering_plans SET {set_clause} WHERE id = :pid"),
            params,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.post("/plan/chamfering-plans/{plan_id}/copy")
async def copy_chamfering_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    res = await db.execute(
        text("""
            SELECT cutting_management_id, production_month, production_day, production_line, production_order,
                   product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                   cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
            FROM chamfering_plans WHERE id = :pid
        """),
        {"pid": plan_id},
    )
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    row = dict(row)

    def _to_date(v):
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        s = str(v).strip()[:10]
        if len(s) == 10:
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
            except (ValueError, IndexError):
                pass
        return date.today()

    production_month_date = _to_date(row.get("production_month")) or date.today()
    production_day_date = _to_date(row.get("production_day")) or date.today()

    ins = text("""
        INSERT INTO chamfering_plans (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :material_name, :management_code, :has_sw_process
        )
    """)
    params = {
        "cutting_management_id": row.get("cutting_management_id"),
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": (row.get("production_line") or "").strip() or "",
        "production_order": row.get("production_order"),
        "product_cd": (row.get("product_cd") or "").strip() or "",
        "product_name": (row.get("product_name") or "").strip() or "",
        "actual_production_quantity": row.get("actual_production_quantity") or 0,
        "production_lot_size": row.get("production_lot_size"),
        "lot_number": (row.get("lot_number") or "").strip() or None,
        "cutting_length": float(row["cutting_length"]) if row.get("cutting_length") is not None else None,
        "chamfering_length": float(row["chamfering_length"]) if row.get("chamfering_length") is not None else None,
        "developed_length": float(row["developed_length"]) if row.get("developed_length") is not None else None,
        "material_name": (row.get("material_name") or "").strip() or None,
        "management_code": (row.get("management_code") or "").strip() or None,
        "has_sw_process": 1 if row.get("has_sw_process") else 0,
    }
    try:
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class MoveChamferingManagementToBatchBody(BaseModel):
    """面取指示1件を面取ロット一覧へ戻す"""
    chamfering_management_id: int


@router.post("/plan/chamfering-plans/move-from-chamfering")
async def move_chamfering_management_to_batch(
    body: MoveChamferingManagementToBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """面取指示1件を面取ロット一覧（chamfering_plans）へ戻し、chamfering_management から削除。"""
    res = await db.execute(
        text("""
            SELECT id, cutting_management_id, production_month, production_day, production_line, production_order,
                   product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                   cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
            FROM chamfering_management WHERE id = :mid
        """),
        {"mid": body.chamfering_management_id},
    )
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    row = dict(row)

    def _to_date(v):
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        s = str(v).strip()[:10]
        if len(s) == 10:
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
            except (ValueError, IndexError):
                pass
        return date.today()

    production_month_date = _to_date(row.get("production_month")) or date.today()
    production_day_date = _to_date(row.get("production_day")) or date.today()

    ins = text("""
        INSERT INTO chamfering_plans (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :material_name, :management_code, :has_sw_process
        )
    """)
    params = {
        "cutting_management_id": row.get("cutting_management_id"),
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": (row.get("production_line") or "").strip() or "",
        "production_order": row.get("production_order"),
        "product_cd": (row.get("product_cd") or "").strip() or "",
        "product_name": (row.get("product_name") or "").strip() or "",
        "actual_production_quantity": row.get("actual_production_quantity") or 0,
        "production_lot_size": row.get("production_lot_size"),
        "lot_number": (row.get("lot_number") or "").strip() or None,
        "cutting_length": float(row["cutting_length"]) if row.get("cutting_length") is not None else None,
        "chamfering_length": float(row["chamfering_length"]) if row.get("chamfering_length") is not None else None,
        "developed_length": float(row["developed_length"]) if row.get("developed_length") is not None else None,
        "material_name": (row.get("material_name") or "").strip() or None,
        "management_code": (row.get("management_code") or "").strip() or None,
        "has_sw_process": 1 if row.get("has_sw_process") else 0,
    }
    try:
        await db.execute(ins, params)
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
            {"sid": body.chamfering_management_id},
        )
        await db.execute(text("DELETE FROM chamfering_management WHERE id = :mid"), {"mid": body.chamfering_management_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "面取ロット一覧に戻しました"}


# ---------- 面取指示（chamfering_management）----------
@router.get("/plan/chamfering-management/list")
async def get_chamfering_management_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    production_line: Optional[str] = Query(None, description="ライン（部分一致）"),
    chamfering_machine: Optional[str] = Query(None, description="面取機（省略時は全機）"),
    limit: int = Query(2000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示一覧: chamfering_management を取得する。
    生産時間は切断指示一覧と同様、product_cd + 面取機=equipment_efficiency.machines_name で能率を結合し 生産数/能率 で算出する。
    """
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if production_day and production_day.strip():
        try:
            parts = production_day.strip().split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                params["production_day"] = date(y, m, d)
                conditions.append("production_day = :production_day")
        except (ValueError, IndexError):
            pass
    if production_line and production_line.strip():
        conditions.append("production_line LIKE :production_line")
        params["production_line"] = f"%{production_line.strip()}%"
    if chamfering_machine is not None and chamfering_machine.strip():
        conditions.append("chamfering_machine = :chamfering_machine")
        params["chamfering_machine"] = chamfering_machine.strip()

    where_clause = " AND ".join(conditions)
    cm_cols = await _get_chamfering_mgmt_columns(db)
    mes_select = _chamfering_mgmt_mes_select_fragment(cm_cols)
    sql = text(f"""
        SELECT `chamfering_management`.id, `chamfering_management`.cutting_management_id, `chamfering_management`.production_month,
               `chamfering_management`.production_day, `chamfering_management`.production_line, `chamfering_management`.chamfering_machine,
               `chamfering_management`.production_order, `chamfering_management`.production_sequence, `chamfering_management`.product_cd,
               `chamfering_management`.product_name, `chamfering_management`.actual_production_quantity, `chamfering_management`.defect_qty,
               `chamfering_management`.production_lot_size, `chamfering_management`.lot_number,
               `chamfering_management`.cutting_length, `chamfering_management`.chamfering_length, `chamfering_management`.developed_length,
               `chamfering_management`.material_name, `chamfering_management`.management_code, `chamfering_management`.has_sw_process,
               `chamfering_management`.production_completed_check, `chamfering_management`.no_count, `chamfering_management`.remarks, `chamfering_management`.cd,
               {mes_select}
               `chamfering_management`.created_at,
               `equipment_efficiency`.efficiency_rate AS efficiency_rate
        FROM `chamfering_management`
        LEFT JOIN `equipment_efficiency`
          ON `chamfering_management`.product_cd = `equipment_efficiency`.product_cd
         AND `chamfering_management`.chamfering_machine = `equipment_efficiency`.machines_name
        WHERE {where_clause}
        ORDER BY `chamfering_management`.production_day ASC, `chamfering_management`.chamfering_machine ASC,
                 `chamfering_management`.production_sequence ASC
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
    except Exception as e:
        msg = str(e).lower()
        if "chamfering_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="chamfering_management テーブルが存在しません。マイグレーション 054_chamfering_management.sql を実行してください。",
            ) from e
        if "unknown column" in msg:
            for col in _CHAMFERING_MGMT_MES_COLUMNS:
                if col in msg:
                    raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint(col)) from e
            raise HTTPException(
                status_code=503,
                detail="chamfering_management テーブルが存在しません。backend/database/migrations/08_chamfering_management_mes_fields.sql を実行してください",
            ) from e
        raise
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _cham_row(r):
        row = dict(r)
        pm = _v(row, "production_month")
        pd = _v(row, "production_day")
        # 生産時間 = 生産数 / efficiency_rate（切断指示一覧の cutting_management と同じ）
        qty = row.get("actual_production_quantity")
        rate = row.get("efficiency_rate")
        if qty is not None and rate is not None:
            try:
                q = float(qty) if not isinstance(qty, (int, float)) else qty
                rr = float(rate) if not isinstance(rate, (int, float)) else rate
                production_time = round(q / rr, 1) if rr > 0 else None
            except (TypeError, ValueError):
                production_time = None
        else:
            production_time = None
        return {
            "id": row.get("id"),
            "cutting_management_id": row.get("cutting_management_id"),
            "production_month": (str(pm)[:10] if pm else None),
            "production_day": (str(pd)[:10] if pd else None),
            "production_line": row.get("production_line"),
            "chamfering_machine": row.get("chamfering_machine"),
            "production_order": row.get("production_order"),
            "production_sequence": row.get("production_sequence"),
            "product_cd": row.get("product_cd"),
            "product_name": row.get("product_name"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "defect_qty": row.get("defect_qty"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": row.get("lot_number"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "production_time": production_time,
            "material_name": row.get("material_name"),
            "management_code": row.get("management_code"),
            "has_sw_process": 1 if row.get("has_sw_process") else 0,
            "production_completed_check": row.get("production_completed_check"),
            "no_count": 1 if row.get("no_count") else 0,
            "remarks": row.get("remarks"),
            "cd": row.get("cd"),
            "mes_production_started_at": _v(row, "mes_production_started_at"),
            "mes_production_ended_at": _v(row, "mes_production_ended_at"),
            "mes_net_production_sec": row.get("mes_net_production_sec"),
            "mes_paused_accum_sec": row.get("mes_paused_accum_sec"),
            "mes_production_is_paused": row.get("mes_production_is_paused"),
            "mes_setup_time_min": row.get("mes_setup_time_min"),
            "mes_operator_user_id": row.get("mes_operator_user_id"),
            "mes_scanned_code": row.get("mes_scanned_code"),
            "created_at": _v(row, "created_at"),
        }
    data = [_cham_row(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.post("/plan/chamfering-management/confirm-actual")
async def confirm_chamfering_actual(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    chamfering_machine: Optional[str] = Query(None, description="面取機（省略時は全機）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """
    面取指示-今日の「実績確定」: production_completed_check=1 かつ no_count=0 の chamfering_management を
    stock_transaction_logs に保存する。去重复：同一範囲の既存 chamfering_management 実績を先に削除してから挿入。
    """
    try:
        parts = production_day.strip().split("-")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="production_day は YYYY-MM-DD で指定してください")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        prod_day = date(y, m, d)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="production_day の形式が不正です") from e

    # 翌日日付
    del_params: dict = {"production_day": prod_day}
    del_conditions = [
        "source_file = 'chamfering_management'",
        "DATE(transaction_time) = :production_day",
    ]
    if chamfering_machine and chamfering_machine.strip():
        del_conditions.append("machine_cd = :chamfering_machine")
        del_params["chamfering_machine"] = chamfering_machine.strip()
    del_sql = text("DELETE FROM stock_transaction_logs WHERE " + " AND ".join(del_conditions))
    await db.execute(del_sql, del_params)

    conditions = [
        "production_day = :production_day",
        "production_completed_check = 1",
        "(no_count IS NULL OR no_count = 0)",
    ]
    params = {"production_day": prod_day}
    if chamfering_machine and chamfering_machine.strip():
        conditions.append("chamfering_machine = :chamfering_machine")
        params["chamfering_machine"] = chamfering_machine.strip()
    sel = text("""
        SELECT id, product_cd, management_code, chamfering_machine, actual_production_quantity, defect_qty, production_day
        FROM chamfering_management
        WHERE """ + " AND ".join(conditions))
    res = await db.execute(sel, params)
    rows = res.mappings().fetchall()
    if not rows:
        await db.commit()
        return {"success": True, "message": "対象データがありません（既存分は削除済み）", "inserted": 0, "total_quantity": 0, "deleted": True}
    ins = text("""
        INSERT INTO stock_transaction_logs (
            stock_type, transaction_type, target_cd, location_cd, lot_no, process_cd, machine_cd,
            quantity, unit, transaction_time, source_file
        ) VALUES (
            '仕掛品', :transaction_type, :target_cd, '工程中間在庫', :lot_no, 'KT02', :machine_cd,
            :quantity, '本', :transaction_time, 'chamfering_management'
        )
    """)
    inserted = 0
    total_quantity = 0
    for row in rows:
        r = dict(row)
        product_cd = (r.get("product_cd") or "").strip()
        if not product_cd:
            continue
        prod_day_val = r.get("production_day")
        if hasattr(prod_day_val, "isoformat"):
            tx_time = datetime.combine(prod_day_val, datetime.min.time()) if prod_day_val else datetime.now()
        else:
            tx_time = datetime.now()
        qty = r.get("actual_production_quantity")
        if qty is None:
            qty = 0
        # 良品：transaction_type='実績'
        await db.execute(ins, {
            "target_cd": product_cd,
            "lot_no": r.get("management_code"),
            "machine_cd": r.get("chamfering_machine"),
            "quantity": qty,
            "transaction_time": tx_time,
            "transaction_type": "実績",
        })
        inserted += 1
        total_quantity += int(qty)
        # 不良：transaction_type='不良'
        defect_qty = r.get("defect_qty")
        if defect_qty is not None and int(defect_qty) > 0:
            await db.execute(ins, {
                "target_cd": product_cd,
                "lot_no": r.get("management_code"),
                "machine_cd": r.get("chamfering_machine"),
                "quantity": int(defect_qty),
                "transaction_time": tx_time,
                "transaction_type": "不良",
            })
            inserted += 1
    await db.commit()
    return {
        "success": True,
        "message": f"実績 {inserted} 件を登録しました",
        "inserted": inserted,
        "total_quantity": total_quantity,
        "production_day": prod_day.isoformat(),
    }


@router.get("/plan/chamfering-management/confirm-actual/email-preview")
async def preview_chamfering_confirm_actual_email(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    from app.services.confirm_actual_email import get_confirm_actual_email_preview

    return await get_confirm_actual_email_preview(
        db, process_type="chamfering", production_day=production_day
    )


@router.post("/plan/chamfering-management/confirm-actual/send-email")
async def send_chamfering_confirm_actual_email(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    from app.services.confirm_actual_email import send_confirm_actual_email

    return await send_confirm_actual_email(
        db, process_type="chamfering", production_day=production_day, current_user=current_user
    )


@router.delete("/plan/chamfering-management/{chamfering_id}")
async def delete_chamfering_management(
    chamfering_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_management WHERE id = :mid"),
        {"mid": chamfering_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    try:
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
            {"sid": chamfering_id},
        )
        await db.execute(text("DELETE FROM chamfering_management WHERE id = :mid"), {"mid": chamfering_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class CreateChamferingManagementBody(BaseModel):
    """面取指示の新規追加（chamfering_management 1件挿入）"""
    production_day: str  # YYYY-MM-DD
    production_line: str = ""
    chamfering_machine: str = ""
    product_cd: str = ""
    product_name: str = ""
    actual_production_quantity: Optional[int] = 0
    production_sequence: Optional[int] = None  # 省略時は同一面取機・同一生産日の最大+1
    material_name: Optional[str] = None
    management_code: Optional[str] = None
    remarks: Optional[str] = None


@router.post("/plan/chamfering-management")
async def create_chamfering_management(
    body: CreateChamferingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """面取指示を1件新規追加。production_month は production_day の年月の初日に設定。"""
    production_day_s = (body.production_day or "").strip()[:10]
    if len(production_day_s) != 10:
        raise HTTPException(status_code=400, detail="生産日は YYYY-MM-DD で指定してください")
    try:
        y, m, d = int(production_day_s[:4]), int(production_day_s[5:7]), int(production_day_s[8:10])
        prod_day = date(y, m, d)
        production_month = date(y, m, 1)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="生産日の形式が不正です") from e
    chamfering_machine = (body.chamfering_machine or "").strip() or None
    if not chamfering_machine:
        raise HTTPException(status_code=400, detail="切断機を指定してください")
    product_cd = (body.product_cd or "").strip() or ""
    product_name = (body.product_name or "").strip() or ""
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="製品CD・製品名は必須です")
    production_line = (body.production_line or "").strip() or ""
    production_sequence = body.production_sequence
    if production_sequence is None:
        next_seq = await db.execute(
            text(
                "SELECT COALESCE(MAX(production_sequence), 0) + 1 AS n FROM chamfering_management "
                "WHERE chamfering_machine = :cm AND production_day = :pd"
            ),
            {"cm": chamfering_machine, "pd": prod_day},
        )
        production_sequence = next_seq.scalar() or 1
    # 管理コード未指定時は自動生成（YYMM + product_cd + ライン下2桁 + 生産順2桁、不足は0埋め）
    management_code_val = (body.management_code or "").strip() or None
    if not management_code_val:
        yy = str(prod_day.year)[-2:]
        mm = str(prod_day.month).zfill(2)
        line_suffix = (production_line or "").strip()[-2:] if (production_line or "").strip() else "00"
        if len(line_suffix) < 2:
            line_suffix = line_suffix.ljust(2, "0")
        seq_s = str(production_sequence).zfill(2)
        management_code_val = f"{yy}{mm}{product_cd}{line_suffix}{seq_s}"
    try:
        ins = text("""
            INSERT INTO chamfering_management (
                cutting_management_id, production_month, production_day, production_line, chamfering_machine,
                production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
                production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
                has_sw_process, production_completed_check, no_count, remarks
            ) VALUES (
                NULL, :production_month, :production_day, :production_line, :chamfering_machine,
                NULL, :production_sequence, :product_cd, :product_name, :actual_production_quantity, 0,
                NULL, NULL, NULL, NULL, NULL, NULL, :material_name, :management_code,
                0, 0, 0, :remarks
            )
        """)
        params = {
            "production_month": production_month,
            "production_day": prod_day,
            "production_line": production_line,
            "chamfering_machine": chamfering_machine,
            "production_sequence": production_sequence,
            "product_cd": product_cd,
            "product_name": product_name,
            "actual_production_quantity": body.actual_production_quantity or 0,
            "material_name": (body.material_name or "").strip() or None,
            "management_code": management_code_val,
            "remarks": (body.remarks or "").strip() or None,
        }
        await db.execute(ins, params)
        await db.commit()
        res = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
        new_id = res.scalar()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "登録しました", "id": new_id}


class UpdateChamferingManagementBody(BaseModel):
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    production_completed_check: Optional[bool] = None
    no_count: Optional[bool] = None
    chamfering_machine: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    defect_qty: Optional[int] = None
    production_sequence: Optional[int] = None
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    remarks: Optional[str] = None
    production_day: Optional[str] = None  # YYYY-MM-DD
    mes_production_started_at: Optional[str] = None  # ISO8601（生産開始）
    mes_production_ended_at: Optional[str] = None  # ISO8601（生産終了）
    mes_net_production_sec: Optional[int] = None
    mes_paused_accum_sec: Optional[int] = None
    mes_production_is_paused: Optional[int] = None  # 0=稼働中, 1=中断中
    mes_setup_time_min: Optional[int] = None
    mes_operator_user_id: Optional[int] = None
    mes_scanned_code: Optional[str] = None


@router.patch("/plan/chamfering-management/{chamfering_id}")
async def update_chamfering_management(
    chamfering_id: int,
    body: UpdateChamferingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    cm_cols = await _get_chamfering_mgmt_columns(db)
    updates: list[str] = []
    params: dict = {"mid": chamfering_id}
    if body.production_day is not None:
        d = _parse_date_ymd(body.production_day)
        if d is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = d.replace(day=1)
            updates.append("production_day = :production_day")
            params["production_day"] = d
    if body.chamfering_machine is not None:
        new_cm = (body.chamfering_machine or "").strip()
        cur = await db.execute(
            text("""
                SELECT chamfering_machine, production_completed_check,
                       mes_production_started_at, mes_production_ended_at
                FROM chamfering_management
                WHERE id = :mid
                LIMIT 1
            """),
            {"mid": chamfering_id},
        )
        cur_row = cur.fetchone()
        if not cur_row:
            raise HTTPException(status_code=404, detail="切断指示が見つかりません")
        old_cm = (str(cur_row[0]).strip() if cur_row[0] else "")
        if not new_cm:
            if old_cm:
                raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        elif old_cm != new_cm:
            if int(cur_row[1] or 0) == 1:
                raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
            if "mes_production_ended_at" in cm_cols:
                ended_at = cur_row[3]
                if ended_at is not None and str(ended_at).strip():
                    raise HTTPException(status_code=400, detail="生産日が不正です")
            if "mes_production_started_at" in cm_cols and "mes_production_ended_at" in cm_cols:
                started_at = cur_row[2]
                ended_at = cur_row[3]
                if started_at is not None and str(started_at).strip():
                    if ended_at is None or not str(ended_at).strip():
                        raise HTTPException(status_code=400, detail="生産日が不正です")
            updates.append("chamfering_machine = :chamfering_machine")
            params["chamfering_machine"] = new_cm
    if body.production_completed_check is not None:
        updates.append("production_completed_check = :production_completed_check")
        params["production_completed_check"] = 1 if body.production_completed_check else 0
    if body.no_count is not None:
        updates.append("no_count = :no_count")
        params["no_count"] = 1 if body.no_count else 0
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.production_sequence is not None:
        updates.append("production_sequence = :production_sequence")
        params["production_sequence"] = body.production_sequence
    if body.production_lot_size is not None:
        updates.append("production_lot_size = :production_lot_size")
        params["production_lot_size"] = body.production_lot_size
    if body.lot_number is not None:
        updates.append("lot_number = :lot_number")
        params["lot_number"] = (body.lot_number or "").strip() or None
    if body.remarks is not None:
        updates.append("remarks = :remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if body.defect_qty is not None:
        updates.append("defect_qty = :defect_qty")
        params["defect_qty"] = max(0, body.defect_qty)
    if body.mes_production_started_at is not None:
        if "mes_production_started_at" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_production_started_at"))
        raw = body.mes_production_started_at.strip() if isinstance(body.mes_production_started_at, str) else ""
        if raw == "":
            updates.append("mes_production_started_at = NULL")
        else:
            sdt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_started_at)
            if sdt:
                await _reject_concurrent_mes_production_on_chamfering_machine(db, chamfering_id, cm_cols)
                params["mes_production_started_at"] = sdt
                updates.append("mes_production_started_at = :mes_production_started_at")
    if body.mes_production_ended_at is not None:
        if "mes_production_ended_at" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_production_ended_at"))
        raw = body.mes_production_ended_at.strip() if isinstance(body.mes_production_ended_at, str) else ""
        if raw == "":
            updates.append("mes_production_ended_at = NULL")
        else:
            edt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_ended_at)
            if edt:
                params["mes_production_ended_at"] = edt
                updates.append("mes_production_ended_at = :mes_production_ended_at")
    if body.mes_net_production_sec is not None:
        if "mes_net_production_sec" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_net_production_sec"))
        net_sec = int(body.mes_net_production_sec)
        if net_sec < 0:
            updates.append("mes_net_production_sec = NULL")
        else:
            updates.append("mes_net_production_sec = :mes_net_production_sec")
            params["mes_net_production_sec"] = max(0, net_sec)
    if body.mes_paused_accum_sec is not None:
        if "mes_paused_accum_sec" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_paused_accum_sec"))
        pause_sec = int(body.mes_paused_accum_sec)
        if pause_sec < 0:
            updates.append("mes_paused_accum_sec = NULL")
        else:
            updates.append("mes_paused_accum_sec = :mes_paused_accum_sec")
            params["mes_paused_accum_sec"] = max(0, pause_sec)
    if body.mes_production_is_paused is not None:
        if "mes_production_is_paused" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_production_is_paused"))
        flag = int(body.mes_production_is_paused)
        if flag < 0:
            updates.append("mes_production_is_paused = NULL")
        else:
            params["mes_production_is_paused"] = 1 if flag else 0
            updates.append("mes_production_is_paused = :mes_production_is_paused")
    if body.mes_setup_time_min is not None:
        if "mes_setup_time_min" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_setup_time_min"))
        setup_min = int(body.mes_setup_time_min)
        if setup_min < 0:
            updates.append("mes_setup_time_min = NULL")
        else:
            updates.append("mes_setup_time_min = :mes_setup_time_min")
            params["mes_setup_time_min"] = max(0, setup_min)
    if body.mes_operator_user_id is not None:
        if "mes_operator_user_id" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_operator_user_id"))
        oid = int(body.mes_operator_user_id)
        if oid <= 0:
            updates.append("mes_operator_user_id = NULL")
        else:
            params["mes_operator_user_id"] = oid
            updates.append("mes_operator_user_id = :mes_operator_user_id")
    if body.mes_scanned_code is not None:
        if "mes_scanned_code" not in cm_cols:
            raise HTTPException(status_code=503, detail=_chamfering_mes_column_migration_hint("mes_scanned_code"))
        raw_mc = body.mes_scanned_code.strip() if isinstance(body.mes_scanned_code, str) else ""
        if raw_mc == "":
            updates.append("mes_scanned_code = NULL")
        else:
            params["mes_scanned_code"] = raw_mc[:512]
            updates.append("mes_scanned_code = :mes_scanned_code")
    if not updates:
        return {"success": True, "message": "変更なし"}
    try:
        await db.execute(
            text(f"UPDATE chamfering_management SET {', '.join(updates)} WHERE id = :mid"),
            params,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class SplitToNextDayChamferingBody(BaseModel):
    """生産数未完了分を翌日へ順延する時のリクエスト"""
    today_quantity: int  # 当日完成数
    next_day: Optional[str] = None  # 翌日 YYYY-MM-DD（省略時は production_day + 1 日）


@router.post("/plan/chamfering-management/{chamfering_id}/split-to-next-day")
async def split_chamfering_to_next_day(
    chamfering_id: int,
    body: SplitToNextDayChamferingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    if body.today_quantity < 0:
        raise HTTPException(status_code=400, detail="当日完成数は0以上を指定してください")
    sel = text("""
        SELECT id, cutting_management_id, production_month, production_day, production_line, chamfering_machine,
               production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
               production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
               has_sw_process, production_completed_check, no_count, remarks
        FROM chamfering_management WHERE id = :mid
    """)
    res = await db.execute(sel, {"mid": chamfering_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    r = dict(row)
    total = int(r.get("actual_production_quantity") or 0)
    if body.today_quantity >= total:
        raise HTTPException(
            status_code=400,
            detail=f"当日完成数は、現在の生産数（{total}）より少ない値を指定してください",
        )
    remainder = total - body.today_quantity

    pd = r.get("production_day")
    if hasattr(pd, "isoformat"):
        pd_str = pd.isoformat()[:10]
    else:
        pd_str = str(pd)[:10] if pd else ""
    if body.next_day and len((body.next_day or "").strip()) >= 10:
        next_day_str = body.next_day.strip()[:10]
    else:
        if pd:
            if hasattr(pd, "year"):
                next_d = pd + timedelta(days=1)
                next_day_str = next_d.isoformat()[:10]
            else:
                parts = pd_str.split("-")
                if len(parts) == 3:
                    next_d = date(int(parts[0]), int(parts[1]), int(parts[2])) + timedelta(days=1)
                    next_day_str = next_d.isoformat()[:10]
                else:
                    raise HTTPException(status_code=400, detail="生産日が不正です")
        else:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
    parts = next_day_str.split("-")
    if len(parts) != 3:
        raise HTTPException(status_code=400, detail="翌日の形式は YYYY-MM-DD です")
    next_day_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    next_month_date = date(next_day_date.year, next_day_date.month, 1)
    cm = (r.get("chamfering_machine") or "").strip()
    if not cm:
        raise HTTPException(status_code=400, detail="切断機が空のため順延できません")

    try:
        await db.execute(
            text("""
                UPDATE chamfering_management
                SET actual_production_quantity = :qty, production_completed_check = 1
                WHERE id = :mid
            """),
            {"mid": chamfering_id, "qty": body.today_quantity},
        )
        # 翌日行は順位1で挿入し、既存の翌日行の production_sequence を +1 して自動ソート
        params = {
            "cutting_management_id": r.get("cutting_management_id"),
            "production_month": next_month_date,
            "production_day": next_day_date,
            "production_line": r.get("production_line") or "",
            "chamfering_machine": cm,
            "production_order": r.get("production_order"),
            "production_sequence": 1,
            "product_cd": r.get("product_cd") or "",
            "product_name": r.get("product_name") or "",
            "actual_production_quantity": remainder,
            "defect_qty": r.get("defect_qty") or 0,
            "production_lot_size": r.get("production_lot_size"),
            "lot_number": r.get("lot_number"),
            "cutting_length": r.get("cutting_length"),
            "chamfering_length": r.get("chamfering_length"),
            "developed_length": r.get("developed_length"),
            "production_time": r.get("production_time"),
            "material_name": r.get("material_name"),
            "management_code": r.get("management_code"),
            "has_sw_process": 1 if r.get("has_sw_process") else 0,
            "no_count": 1 if r.get("no_count") else 0,
            "remarks": r.get("remarks"),
        }
        ins = text("""
            INSERT INTO chamfering_management (
                cutting_management_id, production_month, production_day, production_line, chamfering_machine,
                production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
                production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
                has_sw_process, production_completed_check, no_count, remarks
            ) VALUES (
                :cutting_management_id, :production_month, :production_day, :production_line, :chamfering_machine,
                :production_order, :production_sequence, :product_cd, :product_name, :actual_production_quantity, :defect_qty,
                :production_lot_size, :lot_number, :cutting_length, :chamfering_length, :developed_length, :production_time, :material_name, :management_code,
                :has_sw_process, 0, :no_count, :remarks
            )
        """)
        await db.execute(ins, params)
        lid_res = await db.execute(text("SELECT LAST_INSERT_ID() AS new_id"))
        lid_row = lid_res.mappings().fetchone()
        new_id = int(lid_row["new_id"]) if lid_row and lid_row.get("new_id") is not None else None
        if new_id is not None:
            await db.execute(
                text("""
                    UPDATE chamfering_management
                    SET production_sequence = production_sequence + 1
                    WHERE chamfering_machine = :cm AND production_day = :nd AND id != :new_id
                """),
                {"cm": cm, "nd": next_day_date, "new_id": new_id},
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "生産ロットに戻しました（切断・面取・カンバンを削除済み）"}


@router.post("/plan/chamfering-management/{chamfering_id}/duplicate")
async def duplicate_chamfering_management(
    chamfering_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """需求量サマリーと溶接ベース使用量サマリーを1回で返す。"""
    sel = text("""
        SELECT id, cutting_management_id, production_month, production_day, production_line, chamfering_machine,
               production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
               production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
               has_sw_process, production_completed_check, no_count, remarks
        FROM chamfering_management WHERE id = :mid
    """)
    res = await db.execute(sel, {"mid": chamfering_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    r = dict(row)
    cm = (r.get("chamfering_machine") or "").strip()
    pd = r.get("production_day")
    if not cm:
        raise HTTPException(status_code=400, detail="切断機が空のため順延できません")
    if hasattr(pd, "isoformat"):
        pd_date = pd
    else:
        s = str(pd)[:10] if pd else ""
        if len(s) != 10:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        pd_date = date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    current_seq = int(r.get("production_sequence") or 0)

    try:
        await db.execute(
            text("""
                UPDATE chamfering_management SET production_sequence = production_sequence + 1
                WHERE chamfering_machine = :cm AND production_day = :pd AND production_sequence > :seq
            """),
            {"cm": cm, "pd": pd_date, "seq": current_seq},
        )
        params = {
            "cutting_management_id": r.get("cutting_management_id"),
            "production_month": r.get("production_month"),
            "production_day": pd_date,
            "production_line": r.get("production_line") or "",
            "chamfering_machine": cm,
            "production_order": r.get("production_order"),
            "production_sequence": current_seq + 1,
            "product_cd": r.get("product_cd") or "",
            "product_name": r.get("product_name") or "",
            "actual_production_quantity": r.get("actual_production_quantity") or 0,
            "defect_qty": r.get("defect_qty") or 0,
            "production_lot_size": r.get("production_lot_size"),
            "lot_number": r.get("lot_number"),
            "cutting_length": r.get("cutting_length"),
            "chamfering_length": r.get("chamfering_length"),
            "developed_length": r.get("developed_length"),
            "production_time": r.get("production_time"),
            "material_name": r.get("material_name"),
            "management_code": r.get("management_code"),
            "has_sw_process": 1 if r.get("has_sw_process") else 0,
            "no_count": 1 if r.get("no_count") else 0,
            "remarks": r.get("remarks"),
        }
        ins = text("""
            INSERT INTO chamfering_management (
                cutting_management_id, production_month, production_day, production_line, chamfering_machine,
                production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
                production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
                has_sw_process, production_completed_check, no_count, remarks
            ) VALUES (
                :cutting_management_id, :production_month, :production_day, :production_line, :chamfering_machine,
                :production_order, :production_sequence, :product_cd, :product_name, :actual_production_quantity, :defect_qty,
                :production_lot_size, :lot_number, :cutting_length, :chamfering_length, :developed_length, :production_time, :material_name, :management_code,
                :has_sw_process, 0, :no_count, :remarks
            )
        """)
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class ReorderChamferingBody(BaseModel):
    """面取指示の生産順を変更するリクエスト（同一面取機・同一生産日内）"""
    chamfering_machine: str
    production_day: str  # YYYY-MM-DD
    ordered_ids: list[int]


@router.post("/plan/chamfering-management/reorder")
async def reorder_chamfering_management(
    body: ReorderChamferingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """面取指示の生産順（production_sequence）を、同一面取機・同一生産日内で指定した ID 順に更新する。"""
    chamfering_machine = (body.chamfering_machine or "").strip()
    if not chamfering_machine:
        raise HTTPException(status_code=400, detail="切断機を指定してください")
    production_day_s = (body.production_day or "").strip()[:10]
    if len(production_day_s) != 10:
        raise HTTPException(status_code=400, detail="生産日を指定してください（YYYY-MM-DD）")
    try:
        production_day_date = date(
            int(production_day_s[:4]), int(production_day_s[5:7]), int(production_day_s[8:10])
        )
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="生産日の形式が不正です")
    if not body.ordered_ids:
        return {"success": True, "message": "変更なし"}

    try:
        for idx, row_id in enumerate(body.ordered_ids):
            await db.execute(
                text("""
                    UPDATE chamfering_management
                    SET production_sequence = :production_sequence
                    WHERE id = :id AND chamfering_machine = :chamfering_machine AND production_day = :production_day
                """),
                {
                    "production_sequence": idx + 1,
                    "id": row_id,
                    "chamfering_machine": chamfering_machine,
                    "production_day": production_day_date,
                },
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "生成順を更新しました"}


class GenerateChamferingFromCuttingBody(BaseModel):
    """切断指示から面取指示を1件生成"""
    cutting_management_id: int


@router.post("/plan/chamfering-management/generate-from-cutting")
async def generate_chamfering_from_cutting(
    body: GenerateChamferingFromCuttingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """切断指示1件から面取指示を1件生成する。cutting_management を読んで chamfering_management に挿入。"""
    sel = text("""
        SELECT id, production_month, production_day, production_line, priority_order,
               product_cd, product_name, actual_production_quantity, material_name, management_code
        FROM cutting_management
        WHERE id = :cid
    """)
    res = await db.execute(sel, {"cid": body.cutting_management_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    row = dict(row)
    production_month_val = row.get("production_month")
    production_day_val = row.get("production_day")
    if production_month_val is not None and hasattr(production_month_val, "isoformat"):
        production_month_date = production_month_val.date() if hasattr(production_month_val, "date") else production_month_val
    else:
        s = str(production_month_val or "")[:10]
        production_month_date = date.fromisoformat(s) if len(s) == 10 else date.today()
    if production_day_val is not None and hasattr(production_day_val, "isoformat"):
        production_day_date = production_day_val.date() if hasattr(production_day_val, "date") else production_day_val
    else:
        s = str(production_day_val or "")[:10]
        production_day_date = date.fromisoformat(s) if len(s) == 10 else date.today()
    ins = text("""
        INSERT INTO chamfering_management (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, material_name, management_code, production_completed_check
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :material_name, :management_code, 0
        )
    """)
    params = {
        "cutting_management_id": body.cutting_management_id,
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": row.get("production_line") or "",
        "production_order": row.get("priority_order"),
        "product_cd": row.get("product_cd") or "",
        "product_name": row.get("product_name") or "",
        "actual_production_quantity": row.get("actual_production_quantity") or 0,
        "material_name": row.get("material_name"),
        "management_code": row.get("management_code"),
    }
    try:
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "レコードを追加しました"}


# ---------- カンバン発行（kanban_issuance）----------
@router.get("/plan/kanban-issuance/list")
async def get_kanban_issuance_list(
    process_type: Optional[str] = Query(None, description="工程 cutting / chamfering"),
    issue_date: Optional[str] = Query(None, description="発行日 YYYY-MM-DD"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="状態 pending / issued / completed"),
    product_name: Optional[str] = Query(None, description="製品名（部分一致）"),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """カンバン発行一覧（instruction_plans と同様の項目を cutting/chamfering から結合）"""
    conditions = ["1=1"]
    params = {"limit": limit}
    if process_type and process_type.strip():
        params["process_type"] = process_type.strip()
        conditions.append("k.process_type = :process_type")
    if issue_date and len(issue_date.strip()) >= 10:
        try:
            params["issue_date"] = date.fromisoformat(issue_date.strip()[:10])
            conditions.append("k.issue_date = :issue_date")
        except ValueError:
            pass
    if production_day and len(production_day.strip()) >= 10:
        try:
            params["production_day"] = date.fromisoformat(production_day.strip()[:10])
            conditions.append("k.production_day = :production_day")
        except ValueError:
            pass
    if status and status.strip():
        params["status"] = status.strip().lower()
        conditions.append("k.status = :status")
    if product_name and product_name.strip():
        params["product_name"] = f"%{product_name.strip()}%"
        conditions.append("k.product_name LIKE :product_name")
    sql = text(f"""
        SELECT
            k.id, k.process_type, k.source_id, k.kanban_no, k.issue_date, k.status, k.created_at,
            k.product_cd, k.product_name, k.production_line, k.cutting_machine,
            k.material_name, k.standard_specification, k.management_code,
            k.start_date, k.end_date, k.planned_quantity, k.production_lot_size,
            k.actual_production_quantity, k.take_count,
            k.cutting_length, k.chamfering_length, k.developed_length,
            k.has_chamfering_process, k.lot_number, k.production_day
        FROM kanban_issuance k
        WHERE {" AND ".join(conditions)}
        ORDER BY
            k.production_day ASC,
            k.cutting_machine ASC,
            k.source_id ASC,
            k.id ASC
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
    except Exception as e:
        msg = str(e).lower()
        if "kanban_issuance" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="kanban_issuance テーブルが存在しません。マイグレーション 055_kanban_issuance.sql を実行してください。",
            ) from e
        raise
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10] if val else default
        return val

    data = [
        {
            "id": r.get("id"),
            "process_type": r.get("process_type"),
            "source_id": r.get("source_id"),
            "kanban_no": r.get("kanban_no"),
            "issue_date": _v(r, "issue_date"),
            "status": r.get("status"),
            "created_at": _v(dict(r), "created_at"),
            "product_cd": r.get("product_cd"),
            "product_name": r.get("product_name"),
            "production_line": r.get("production_line"),
            "cutting_machine": r.get("cutting_machine"),
            "material_name": r.get("material_name"),
            "standard_specification": r.get("standard_specification"),
            "management_code": r.get("management_code"),
            "start_date": _v(r, "start_date"),
            "end_date": _v(r, "end_date"),
            "planned_quantity": r.get("planned_quantity"),
            "production_lot_size": r.get("production_lot_size"),
            "actual_production_quantity": r.get("actual_production_quantity"),
            "take_count": r.get("take_count"),
            "cutting_length": float(r["cutting_length"]) if r.get("cutting_length") is not None else None,
            "chamfering_length": float(r["chamfering_length"]) if r.get("chamfering_length") is not None else None,
            "developed_length": float(r["developed_length"]) if r.get("developed_length") is not None else None,
            "has_chamfering_process": bool(r.get("has_chamfering_process")),
            "lot_number": r.get("lot_number"),
            "production_day": _v(r, "production_day"),
        }
        for r in rows
    ]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/plan/kanban-issuance/product-names")
async def get_kanban_issuance_product_names(
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示の生産順を変更するリクエスト（同一面取機・同一生産日内）"""
    sql = text("""
        SELECT DISTINCT product_name
        FROM kanban_issuance
        WHERE product_name IS NOT NULL AND TRIM(product_name) != ''
        ORDER BY product_name
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, {"limit": limit})
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "kanban_issuance" in msg:
            return {"success": True, "data": []}
        raise
    data = [r.get("product_name") for r in rows if r.get("product_name")]
    return {"success": True, "data": data}


class IssueKanbanBody(BaseModel):
    process_type: str  # cutting / chamfering
    source_id: int


class BatchIssueKanbanBody(BaseModel):
    kanban_ids: list[int]


class UpdateKanbanIssuanceBody(BaseModel):
    """カンバン発行1件のデータを更新する。"""
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    production_line: Optional[str] = None
    cutting_machine: Optional[str] = None
    material_name: Optional[str] = None
    standard_specification: Optional[str] = None
    management_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    planned_quantity: Optional[int] = None
    production_lot_size: Optional[int] = None
    actual_production_quantity: Optional[int] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    has_chamfering_process: Optional[bool] = None
    lot_number: Optional[str] = None
    production_day: Optional[str] = None


@router.patch("/plan/kanban-issuance/{kanban_id:int}")
async def update_kanban_issuance(
    kanban_id: int,
    body: UpdateKanbanIssuanceBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """カンバン発行1件のデータを更新する。"""
    res = await db.execute(text("SELECT id FROM kanban_issuance WHERE id = :kid"), {"kid": kanban_id})
    if not res.mappings().fetchone():
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    body_dict = body.model_dump(exclude_unset=True)
    if not body_dict:
        return {"success": True, "message": "変更なし"}
    set_parts = []
    params = {"kid": kanban_id}
    date_fields = ("start_date", "end_date", "production_day")
    for k, v in body_dict.items():
        if k in date_fields and v is not None:
            try:
                params[k] = date.fromisoformat(str(v).strip()[:10])
            except ValueError:
                continue
        else:
            params[k] = v
        set_parts.append(f"`{k}` = :{k}")
    if not set_parts:
        return {"success": True, "message": "変更なし"}
    if "has_chamfering_process" in params and isinstance(params["has_chamfering_process"], bool):
        params["has_chamfering_process"] = 1 if params["has_chamfering_process"] else 0
    sql = text(f"UPDATE kanban_issuance SET {', '.join(set_parts)} WHERE id = :kid")
    await db.execute(sql, params)
    await db.commit()
    return {"success": True, "message": "更新しました"}


@router.post("/plan/kanban-issuance/issue")
async def issue_kanban(
    body: IssueKanbanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("export")),
):
    """カンバン発行を1件登録。kanban_no は自動採番（process_type + source_id + 日時等）でよいが、ここでは簡易で source_id ベース。"""
    pt = (body.process_type or "").strip()
    if pt not in ("cutting", "chamfering"):
        raise HTTPException(status_code=400, detail="process_type は cutting または chamfering を指定してください")
    today = date.today()
    kanban_no = f"{pt.upper()}-{body.source_id}-{today.isoformat().replace('-', '')}"
    ins = text("""
        INSERT INTO kanban_issuance (process_type, source_id, kanban_no, issue_date, status)
        VALUES (:process_type, :source_id, :kanban_no, :issue_date, 'issued')
    """)
    try:
        await db.execute(ins, {
            "process_type": pt,
            "source_id": body.source_id,
            "kanban_no": kanban_no,
            "issue_date": today,
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        msg = str(e).lower()
        if "kanban_issuance" in msg:
            raise HTTPException(status_code=503, detail="kanban_issuance テーブルが存在しません。") from e
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "カンバンを発行しました", "kanban_no": kanban_no}


@router.post("/plan/kanban-issuance/{kanban_id:int}/issue")
async def issue_pending_kanban(
    kanban_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("export")),
):
    """待発行（pending）のカンバンを発行する。kanban_no と issue_date を設定し status を issued に更新。"""
    sel = text("SELECT id, process_type, source_id, status FROM kanban_issuance WHERE id = :kid")
    res = await db.execute(sel, {"kid": kanban_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    row = dict(row)
    if (row.get("status") or "").strip().lower() != "pending":
        raise HTTPException(status_code=400, detail="待発行のカンバンのみ発行できます")
    today = date.today()
    pt = (row.get("process_type") or "cutting").strip()
    src_id = row.get("source_id") or 0
    kanban_no = f"{pt.upper()}-{src_id}-{today.isoformat().replace('-', '')}"
    upd = text("""
        UPDATE kanban_issuance SET kanban_no = :kanban_no, issue_date = :issue_date, status = 'issued'
        WHERE id = :kid
    """)
    await db.execute(upd, {"kanban_no": kanban_no, "issue_date": today, "kid": kanban_id})
    await db.commit()
    return {"success": True, "message": "カンバンを発行しました", "kanban_no": kanban_no}


@router.post("/plan/kanban-issuance/{kanban_id:int}/reissue")
async def reissue_kanban(
    kanban_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("export")),
):
    """発行済のカンバンを再発行する（現場で紛失した場合など）。新しい kanban_no と issue_date で更新。"""
    sel = text("SELECT id, process_type, source_id, status FROM kanban_issuance WHERE id = :kid")
    res = await db.execute(sel, {"kid": kanban_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    row = dict(row)
    status = (row.get("status") or "").strip().lower()
    if status not in ("pending", "issued"):
        raise HTTPException(
            status_code=400,
            detail="待発行または発行済のカンバンのみ再発行できます（完了済は再発行不可）",
        )
    today = date.today()
    pt = (row.get("process_type") or "cutting").strip()
    src_id = row.get("source_id") or 0
    kanban_no = f"{pt.upper()}-{src_id}-{today.isoformat().replace('-', '')}"
    upd = text("""
        UPDATE kanban_issuance SET kanban_no = :kanban_no, issue_date = :issue_date, status = 'issued'
        WHERE id = :kid
    """)
    await db.execute(upd, {"kanban_no": kanban_no, "issue_date": today, "kid": kanban_id})
    await db.commit()
    return {"success": True, "message": "カンバンを再発行しました", "kanban_no": kanban_no}


@router.post("/plan/kanban-issuance/sync-production-day")
async def sync_kanban_production_day(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """kanban_issuance の production_day を source_id で cutting_management / chamfering_management から取得して更新する。"""
    # process_type='cutting' の source_id = cutting_management.id
    upd_cutting = text("""
        UPDATE kanban_issuance k
        INNER JOIN cutting_management c ON k.source_id = c.id AND k.process_type = 'cutting'
        SET k.production_day = c.production_day
    """)
    # process_type='chamfering' → source_id = chamfering_management.id, production_day は chamfering_management から
    upd_chamfering = text("""
        UPDATE kanban_issuance k
        INNER JOIN chamfering_management ch ON k.source_id = ch.id AND k.process_type = 'chamfering'
        SET k.production_day = ch.production_day
    """)
    try:
        r1 = await db.execute(upd_cutting)
        r2 = await db.execute(upd_chamfering)
        await db.commit()
        # rowcount は DB によっては UPDATE 件数が返らない場合がある
        updated = getattr(r1, "rowcount", None) or 0
        updated += getattr(r2, "rowcount", None) or 0
        return {"success": True, "message": "生産日を更新しました", "updated": updated}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/plan/kanban-issuance/batch-issue")
async def batch_issue_pending_kanban(
    body: BatchIssueKanbanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("export")),
):
    """待発行（pending）・発行済（issued）のカンバンを一括発行する。発行済は再発行扱いで新 kanban_no を付与。"""
    if not body.kanban_ids:
        return {"success": True, "message": "発行対象がありません", "issued": 0, "skipped": 0, "errors": [], "issued_items": []}
    today = date.today()
    sel = text("SELECT id, process_type, source_id, status FROM kanban_issuance WHERE id = :kid")
    upd = text("""
        UPDATE kanban_issuance SET kanban_no = :kanban_no, issue_date = :issue_date, status = 'issued'
        WHERE id = :kid
    """)
    issued = 0
    skipped = 0
    errors = []
    issued_items: list[dict] = []
    for kid in body.kanban_ids:
        res = await db.execute(sel, {"kid": kid})
        row = res.mappings().fetchone()
        if not row:
            errors.append(f"id={kid}: カンバンが見つかりません")
            continue
        row = dict(row)
        status = (row.get("status") or "").strip().lower()
        if status not in ("pending", "issued"):
            skipped += 1
            continue
        pt = (row.get("process_type") or "cutting").strip()
        src_id = row.get("source_id") or 0
        kanban_no = f"{pt.upper()}-{src_id}-{today.isoformat().replace('-', '')}"
        try:
            await db.execute(upd, {"kanban_no": kanban_no, "issue_date": today, "kid": kid})
            issued += 1
            issued_items.append({"id": kid, "kanban_no": kanban_no})
        except Exception as e:
            errors.append(f"id={kid}: {e}")
    await db.commit()
    return {
        "success": True,
        "message": f"一括発行完了（発行: {issued} 件、スキップ: {skipped} 件）",
        "issued": issued,
        "skipped": skipped,
        "errors": errors,
        "issued_items": issued_items,
    }


@router.post("/plan/batch/sync-lengths-from-products")
async def sync_batch_lengths_from_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    products の cut_length / chamfer_length / developed_length を、同一 product_cd の
    instruction_plans・cutting_management・chamfering_plans・chamfering_management・
    kanban_issuance（product_cd がある行）へ反映する。
    instruction_plans については製品の工程ルート（product_route_steps × processes）から
    has_chamfering_process / has_sw_process も更新する（batch-detail / APS 同期と同じ判定）。
    chamfering_plans / chamfering_management に cutting_length・developed_length が無い環境
    （マイグレーション 208 未実行）では、chamfering_length のみ同期する。
    """
    cp_has_cut = await _table_has_column(db, "chamfering_plans", "cutting_length")
    cm_has_cut = await _table_has_column(db, "chamfering_management", "cutting_length")
    kanban_has_lengths = await _table_has_column(db, "kanban_issuance", "cutting_length")

    # products 列が utf8mb4_0900_ai_ci、他テーブルが utf8mb4_unicode_ci の環境で JOIN 時に 1267 を避ける
    _pc = "p.product_cd COLLATE utf8mb4_unicode_ci = {alias}.product_cd COLLATE utf8mb4_unicode_ci"

    stmts: list[tuple[str, object]] = [
        (
            "instruction_plans",
            text(f"""
                UPDATE instruction_plans ip
                INNER JOIN products p ON {_pc.format(alias="ip")}
                LEFT JOIN (
                    SELECT
                        prs.product_cd AS prs_product_cd,
                        prs.route_cd AS prs_route_cd,
                        MAX(CASE WHEN pr.process_name LIKE '%面取%' THEN 1 ELSE 0 END) AS has_ch,
                        MAX(CASE
                            WHEN pr.process_name LIKE '%SW%'
                                 OR LOWER(pr.process_name) LIKE '%swaging%' THEN 1 ELSE 0
                            END) AS has_sw
                    FROM product_route_steps prs
                    INNER JOIN processes pr
                        ON pr.process_cd COLLATE utf8mb4_unicode_ci
                         = prs.process_cd COLLATE utf8mb4_unicode_ci
                    GROUP BY prs.product_cd, prs.route_cd
                ) rf ON rf.prs_product_cd COLLATE utf8mb4_unicode_ci
                        = p.product_cd COLLATE utf8mb4_unicode_ci
                    AND p.route_cd IS NOT NULL
                    AND TRIM(p.route_cd) <> ''
                    AND TRIM(rf.prs_route_cd) = TRIM(p.route_cd)
                SET ip.cutting_length = p.cut_length,
                    ip.chamfering_length = p.chamfer_length,
                    ip.developed_length = p.developed_length,
                    ip.has_chamfering_process = COALESCE(rf.has_ch, 0),
                    ip.has_sw_process = COALESCE(rf.has_sw, 0)
            """),
        ),
        (
            "cutting_management",
            text(f"""
                UPDATE cutting_management cm
                INNER JOIN products p ON {_pc.format(alias="cm")}
                SET cm.cutting_length = p.cut_length,
                    cm.chamfering_length = p.chamfer_length,
                    cm.developed_length = p.developed_length
            """),
        ),
    ]
    if cp_has_cut:
        stmts.append(
            (
                "chamfering_plans",
                text(f"""
                    UPDATE chamfering_plans cp
                    INNER JOIN products p ON {_pc.format(alias="cp")}
                    SET cp.cutting_length = p.cut_length,
                        cp.chamfering_length = p.chamfer_length,
                        cp.developed_length = p.developed_length
                """),
            )
        )
    else:
        stmts.append(
            (
                "chamfering_plans",
                text(f"""
                    UPDATE chamfering_plans cp
                    INNER JOIN products p ON {_pc.format(alias="cp")}
                    SET cp.chamfering_length = p.chamfer_length
                """),
            )
        )
    if cm_has_cut:
        stmts.append(
            (
                "chamfering_management",
                text(f"""
                    UPDATE chamfering_management ch
                    INNER JOIN products p ON {_pc.format(alias="ch")}
                    SET ch.cutting_length = p.cut_length,
                        ch.chamfering_length = p.chamfer_length,
                        ch.developed_length = p.developed_length
                """),
            )
        )
    else:
        stmts.append(
            (
                "chamfering_management",
                text(f"""
                    UPDATE chamfering_management ch
                    INNER JOIN products p ON {_pc.format(alias="ch")}
                    SET ch.chamfering_length = p.chamfer_length
                """),
            )
        )
    if kanban_has_lengths:
        stmts.append(
            (
                "kanban_issuance",
                text(f"""
                    UPDATE kanban_issuance k
                    INNER JOIN products p ON {_pc.format(alias="k")}
                    SET k.cutting_length = p.cut_length,
                        k.chamfering_length = p.chamfer_length,
                        k.developed_length = p.developed_length
                    WHERE k.product_cd IS NOT NULL AND TRIM(k.product_cd) != ''
                """),
            )
        )

    counts: dict[str, int] = {}
    notes: list[str] = []
    if not cp_has_cut or not cm_has_cut:
        notes.append(
            "chamfering_plans / chamfering_management はマイグレーション 208 未適用のため、"
            "面取長（chamfering_length）のみ同期しました。切断長・展開長も反映する場合は 208_chamfering_plans_management_length_fields.sql を実行してください。"
        )
    if not kanban_has_lengths:
        notes.append(
            "kanban_issuance に寸法列が無いためスキップしました（マイグレーション 067 等を確認してください）。"
        )

    try:
        for name, sql in stmts:
            res = await db.execute(sql)
            counts[name] = int(res.rowcount or 0)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("sync-lengths-from-products failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"同期に失敗しました: {e!s}",
        ) from e
    total = sum(counts.values())
    msg = f"製品マスタの寸法を反映しました（更新行数合計: {total}）"
    if notes:
        msg += " " + " ".join(notes)
    return {
        "success": True,
        "message": msg,
        "data": {"counts": counts, "notes": notes},
    }


@router.post("/plan/batch/generate-from-schedule")
async def generate_cutting_plans_from_schedule(
    body: GenerateFromScheduleBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定月でロット生成: production_plan_schedules の file_name に生産月を含み、
    '溶接' を含まない行を取得し、material_lot_count 回分ループして
    instruction_plans に挿入する。
    products / materials を product_name / material_name で結合して
    product_cd, lot_size, cut_length 等を取得する。
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        production_month, month_label = _parse_month(body.month)
        pattern = f"%{month_label}%"

        # 1) production_plan_schedules から取得（file_name に生産月を含む、'溶接' を除く）
        sql_schedules = text("""
            SELECT machine_name, product_name, production_order, planned_quantity,
                   production_start_date, production_end_date, material_lot_count, material_name
            FROM production_plan_schedules
            WHERE file_name LIKE :pattern
              AND file_name NOT LIKE '%溶接%'
            ORDER BY machine_name, product_name, production_order
        """)
        result = await db.execute(sql_schedules, {"pattern": pattern})
        rows = result.mappings().fetchall()

        if not rows:
            return {
                "success": True,
                "data": {"inserted": 0},
                "message": f"該当する計画データがありません（file_name に「{month_label}」を含み「溶接」を含まないもの）",
            }

        # 2) products を product_name で取得（同一製品名で複数ある場合は product_cd 末尾が '1' のものを優先）
        product_names = list({str(r.get("product_name") or "").strip() for r in rows if r.get("product_name")})
        product_map = {}
        if product_names:
            placeholders = ", ".join([f":p{i}" for i in range(len(product_names))])
            sql_products = text(f"""
                SELECT product_cd, product_name, lot_size, cut_length, chamfer_length,
                       developed_length, scrap_length, take_count
                FROM products
                WHERE product_name IN ({placeholders})
            """)
            params_products = {f"p{i}": name for i, name in enumerate(product_names)}
            res_p = await db.execute(sql_products, params_products)
            for r in res_p.mappings().fetchall():
                pname = (r.get("product_name") or "").strip()
                if pname not in product_map:
                    product_map[pname] = dict(r)
                else:
                    cd = (r.get("product_cd") or "").strip()
                    if cd and str(cd)[-1:] == "1":
                        product_map[pname] = dict(r)

        # 3) product_route_steps で KT01/KT02/KT03 を取得（has_cutting / has_chamfering / has_sw）
        product_cds = list({(v.get("product_cd") or "").strip() for v in product_map.values() if (v.get("product_cd") or "").strip()})
        route_step_map = {}
        if product_cds:
            placeholders = ", ".join([f":c{i}" for i in range(len(product_cds))])
            sql_steps = text(f"""
                SELECT product_cd, process_cd FROM product_route_steps
                WHERE product_cd IN ({placeholders}) AND process_cd IN ('KT01', 'KT02', 'KT03')
            """)
            params_steps = {f"c{i}": cd for i, cd in enumerate(product_cds)}
            res_s = await db.execute(sql_steps, params_steps)
            for r in res_s.mappings().fetchall():
                cd = (r.get("product_cd") or "").strip()
                proc = (r.get("process_cd") or "").strip()
                if cd not in route_step_map:
                    route_step_map[cd] = set()
                route_step_map[cd].add(proc)

        # 4) materials を material_name で取得（standard_spec -> standard_specification, supplier_cd -> material_manufacturer）
        material_names = list({str(r.get("material_name") or "").strip() for r in rows if r.get("material_name")})
        material_map = {}
        if material_names:
            placeholders = ", ".join([f":m{i}" for i in range(len(material_names))])
            sql_materials = text(f"""
                SELECT material_name, standard_spec, supplier_cd
                FROM materials
                WHERE material_name IN ({placeholders})
            """)
            params_materials = {f"m{i}": name for i, name in enumerate(material_names)}
            res_m = await db.execute(sql_materials, params_materials)
            for r in res_m.mappings().fetchall():
                material_map[(r.get("material_name") or "").strip()] = dict(r)

        # 5) 同一生産月の既存データを削除
        await db.execute(
            text("DELETE FROM instruction_plans WHERE production_month = :pm"),
            {"pm": production_month},
        )

        # 6) 行ごとに material_lot_count 回ループして挿入（lot_number は 1, 2, ... material_lot_count）
        inserted = 0
        for r in rows:
            row_dict = dict(r) if hasattr(r, "keys") else r
            machine_name = (row_dict.get("machine_name") or "").strip() or ""
            product_name = (row_dict.get("product_name") or "").strip() or ""
            production_order = _to_int(row_dict.get("production_order"))
            planned_quantity = _to_int(row_dict.get("planned_quantity")) or 0
            start_d = row_dict.get("production_start_date")
            end_d = row_dict.get("production_end_date")
            lot_count = _to_int(row_dict.get("material_lot_count")) or 1
            if lot_count < 1:
                lot_count = 1
            material_name = (row_dict.get("material_name") or "").strip() or ""

            prod = product_map.get(product_name) or {}
            product_cd = (prod.get("product_cd") or "").strip() or ""
            actual_qty = _to_int(prod.get("lot_size")) or 0
            cut_len = _to_decimal_val(prod.get("cut_length"))
            chamfer_len = _to_decimal_val(prod.get("chamfer_length"))
            developed_len = _to_decimal_val(prod.get("developed_length"))
            scrap_len = _to_decimal_val(prod.get("scrap_length"))
            take_count = _to_int(prod.get("take_count"))

            steps = route_step_map.get(product_cd) or set()
            has_cutting = 1 if "KT01" in steps else 0
            has_chamfering = 1 if "KT02" in steps else 0
            has_sw = 1 if "KT03" in steps else 0

            mat = material_map.get(material_name) or {}
            standard_spec = (mat.get("standard_spec") or "").strip() or None
            supplier_cd = (mat.get("supplier_cd") or "").strip() or None

            start_ts = None
            if start_d:
                if hasattr(start_d, "year"):
                    start_ts = datetime(start_d.year, start_d.month, start_d.day)
                else:
                    start_ts = start_d
            end_ts = None
            if end_d:
                if hasattr(end_d, "year"):
                    end_ts = datetime(end_d.year, end_d.month, end_d.day)
                else:
                    end_ts = end_d

            for lot_idx in range(1, lot_count + 1):
                lot_number = str(lot_idx)
                await db.execute(
                    text("""
                        INSERT INTO instruction_plans (
                            production_month, production_line, priority_order, product_cd, product_name,
                            planned_quantity, start_date, end_date, production_lot_size, lot_number,
                            is_cutting_instructed, has_chamfering_process, has_sw_process,
                            actual_production_quantity, take_count, cutting_length, chamfering_length,
                            developed_length, scrap_length, material_name, material_manufacturer, standard_specification
                        ) VALUES (
                            :production_month, :production_line, :priority_order, :product_cd, :product_name,
                            :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                            :is_cutting_instructed, :has_chamfering_process, :has_sw_process,
                            :actual_production_quantity, :take_count, :cutting_length, :chamfering_length,
                            :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification
                        )
                    """),
                    {
                        "production_month": production_month,
                        "production_line": machine_name,
                        "priority_order": production_order,
                        "product_cd": product_cd,
                        "product_name": product_name,
                        "planned_quantity": planned_quantity,
                        "start_date": start_ts,
                        "end_date": end_ts,
                        "production_lot_size": lot_count,
                        "lot_number": lot_number,
                        "is_cutting_instructed": has_cutting,
                        "has_chamfering_process": has_chamfering,
                        "has_sw_process": has_sw,
                        "actual_production_quantity": actual_qty,
                        "take_count": take_count,
                        "cutting_length": cut_len,
                        "chamfering_length": chamfer_len,
                        "developed_length": developed_len,
                        "scrap_length": scrap_len,
                        "material_name": material_name or None,
                        "material_manufacturer": supplier_cd,
                        "standard_specification": standard_spec,
                    },
                )
                inserted += 1

        return {
            "success": True,
            "data": {"inserted": inserted},
            "message": f"切断指示計画を {inserted} 件生成しました（生産月: {body.month}）",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("generate-from-schedule failed")
        msg = str(e)
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "Unknown table" in msg):
            msg = "instruction_plans テーブルが存在しません。マイグレーション 052_cutting_instruction_plans.sql を実行してください。"
        raise HTTPException(status_code=500, detail=msg)


# ============================
# メモ（TODO）: instruction notes（cutting_instruction_notes.scope）
#   cutting:
#     GET/POST/PATCH/DELETE /api/plan/cutting-instruction-notes
#   forming:
#     GET/POST/PATCH/DELETE /api/plan/forming-instruction-notes
#   forming planning (APS 成型計画作成):
#     GET/POST/PATCH/DELETE /api/plan/forming-planning-notes
#   welding planning (APS 溶接計画作成):
#     GET/POST/PATCH/DELETE /api/plan/welding-planning-notes
#   welding:
#     GET/POST/PATCH/DELETE /api/plan/welding-instruction-notes
# ============================

INSTRUCTION_NOTE_SCOPE_CUTTING = "cutting_instruction"
INSTRUCTION_NOTE_SCOPE_FORMING = "forming_instruction"
INSTRUCTION_NOTE_SCOPE_FORMING_PLANNING = "forming_planning"
INSTRUCTION_NOTE_SCOPE_WELDING_PLANNING = "welding_planning"
INSTRUCTION_NOTE_SCOPE_WELDING = "welding_instruction"


class CuttingInstructionNoteCreateBody(BaseModel):
    content: str


class CuttingInstructionNoteUpdateBody(BaseModel):
    content: Optional[str] = None
    is_done: Optional[int] = None


def _instruction_note_datetime_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()[:19]
    return str(v)


def _reraise_instruction_notes_db_error(e: Exception) -> None:
    msg = str(e).lower()
    if "cutting_instruction_notes" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
        raise HTTPException(
            status_code=503,
            detail="cutting_instruction_notes テーブルが存在しません。マイグレーション 237_cutting_instruction_notes.sql を確認してください。",
        ) from e


async def _list_instruction_notes(db: AsyncSession, scope: str, limit: int) -> dict[str, Any]:
    try:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT id, content, is_done, created_by, created_at, updated_at
                    FROM cutting_instruction_notes
                    WHERE scope = :scope
                    ORDER BY is_done ASC, id DESC
                    LIMIT :limit
                    """
                ),
                {"scope": scope, "limit": limit},
            )
        ).mappings().fetchall()
    except Exception as e:
        _reraise_instruction_notes_db_error(e)
        raise

    notes = [
        {
            "id": int(r.get("id")),
            "content": r.get("content"),
            "is_done": int(r.get("is_done") or 0),
            "created_by": r.get("created_by"),
            "created_at": _instruction_note_datetime_str(r.get("created_at")),
            "updated_at": _instruction_note_datetime_str(r.get("updated_at")),
        }
        for r in rows
    ]
    return {"success": True, "data": {"list": notes}, "message": "OK"}


async def _create_instruction_note(
    db: AsyncSession,
    scope: str,
    content: str,
    created_by: Optional[str],
) -> dict[str, Any]:
    try:
        await db.execute(
            text(
                """
                INSERT INTO cutting_instruction_notes (scope, content, is_done, created_by)
                VALUES (:scope, :content, 0, :created_by)
                """
            ),
            {"scope": scope, "content": content, "created_by": created_by},
        )
        note_id = (await db.execute(text("SELECT LAST_INSERT_ID() AS id"))).scalar()
        await db.commit()
    except Exception as e:
        _reraise_instruction_notes_db_error(e)
        raise

    if not note_id:
        return {"success": True, "data": {}, "message": "OK"}

    row = (
        await db.execute(
            text(
                """
                SELECT id, content, is_done, created_by, created_at, updated_at
                FROM cutting_instruction_notes
                WHERE id = :id
                """
            ),
            {"id": int(note_id)},
        )
    ).mappings().fetchone()

    created = {
        "id": int(row.get("id")) if row else int(note_id),
        "content": row.get("content") if row else content,
        "is_done": int(row.get("is_done") or 0) if row else 0,
        "created_by": row.get("created_by") if row else created_by,
        "created_at": _instruction_note_datetime_str(row.get("created_at")) if row else None,
        "updated_at": _instruction_note_datetime_str(row.get("updated_at")) if row else None,
    }
    return {"success": True, "data": {"note": created}, "message": "OK"}


async def _update_instruction_note(
    db: AsyncSession,
    scope: str,
    note_id: int,
    body: CuttingInstructionNoteUpdateBody,
    current_user: User,
) -> dict[str, Any]:
    updates: list[str] = []
    params: dict[str, Any] = {"id": note_id, "scope": scope}

    if body.content is not None:
        content = body.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="content が空です")
        if len(content) > 200:
            raise HTTPException(status_code=400, detail="content は200文字以内で指定してください")
        updates.append("content = :content")
        params["content"] = content

    if body.is_done is not None:
        updates.append("is_done = :is_done")
        params["is_done"] = 1 if int(body.is_done) == 1 else 0

    if not updates:
        return {"success": True, "data": {}, "message": "OK（更新なし）"}

    try:
        set_clause = ", ".join(updates)
        await db.execute(
            text(
                f"UPDATE cutting_instruction_notes SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND scope = :scope"
            ),
            params,
        )
        await db.commit()
    except Exception as e:
        _reraise_instruction_notes_db_error(e)
        raise

    row = (
        await db.execute(
            text(
                """
                SELECT id, content, is_done, created_by, created_at, updated_at
                FROM cutting_instruction_notes
                WHERE id = :id AND scope = :scope
                """
            ),
            {"id": int(note_id), "scope": scope},
        )
    ).mappings().fetchone()

    updated = (
        {
            "id": int(row.get("id")) if row else note_id,
            "content": row.get("content") if row else None,
            "is_done": int(row.get("is_done") or 0) if row else 0,
            "created_by": row.get("created_by") if row else getattr(current_user, "username", None),
            "created_at": _instruction_note_datetime_str(row.get("created_at")) if row else None,
            "updated_at": _instruction_note_datetime_str(row.get("updated_at")) if row else None,
        }
        if row
        else {"id": note_id}
    )
    return {"success": True, "data": {"note": updated}, "message": "OK"}


async def _delete_instruction_note(db: AsyncSession, scope: str, note_id: int) -> dict[str, Any]:
    try:
        await db.execute(
            text("DELETE FROM cutting_instruction_notes WHERE id = :id AND scope = :scope"),
            {"id": int(note_id), "scope": scope},
        )
        await db.commit()
    except Exception as e:
        _reraise_instruction_notes_db_error(e)
        raise
    return {"success": True, "message": "更新しました"}


@router.get("/plan/cutting-instruction-notes")
async def list_cutting_instruction_notes(
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await _list_instruction_notes(db, INSTRUCTION_NOTE_SCOPE_CUTTING, limit)


@router.post("/plan/cutting-instruction-notes")
async def create_cutting_instruction_note(
    body: CuttingInstructionNoteCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content を指定してください")
    if len(content) > 200:
        raise HTTPException(status_code=400, detail="content は200文字以内で指定してください")
    return await _create_instruction_note(
        db,
        INSTRUCTION_NOTE_SCOPE_CUTTING,
        content,
        getattr(current_user, "username", None),
    )


@router.patch("/plan/cutting-instruction-notes/{note_id}")
async def update_cutting_instruction_note(
    note_id: int,
    body: CuttingInstructionNoteUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    return await _update_instruction_note(db, INSTRUCTION_NOTE_SCOPE_CUTTING, note_id, body, current_user)


@router.delete("/plan/cutting-instruction-notes/{note_id}")
async def delete_cutting_instruction_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    return await _delete_instruction_note(db, INSTRUCTION_NOTE_SCOPE_CUTTING, note_id)


@router.get("/plan/forming-instruction-notes")
async def list_forming_instruction_notes(
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await _list_instruction_notes(db, INSTRUCTION_NOTE_SCOPE_FORMING, limit)


@router.post("/plan/forming-instruction-notes")
async def create_forming_instruction_note(
    body: CuttingInstructionNoteCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content を指定してください")
    if len(content) > 200:
        raise HTTPException(status_code=400, detail="content は200文字以内で指定してください")
    return await _create_instruction_note(
        db,
        INSTRUCTION_NOTE_SCOPE_FORMING,
        content,
        getattr(current_user, "username", None),
    )


@router.patch("/plan/forming-instruction-notes/{note_id}")
async def update_forming_instruction_note(
    note_id: int,
    body: CuttingInstructionNoteUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    return await _update_instruction_note(db, INSTRUCTION_NOTE_SCOPE_FORMING, note_id, body, current_user)


@router.delete("/plan/forming-instruction-notes/{note_id}")
async def delete_forming_instruction_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    return await _delete_instruction_note(db, INSTRUCTION_NOTE_SCOPE_FORMING, note_id)


@router.get("/plan/forming-planning-notes")
async def list_forming_planning_notes(
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await _list_instruction_notes(db, INSTRUCTION_NOTE_SCOPE_FORMING_PLANNING, limit)


@router.post("/plan/forming-planning-notes")
async def create_forming_planning_note(
    body: CuttingInstructionNoteCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("create")),
):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content を指定してください")
    if len(content) > 200:
        raise HTTPException(status_code=400, detail="content は200文字以内で指定してください")
    return await _create_instruction_note(
        db,
        INSTRUCTION_NOTE_SCOPE_FORMING_PLANNING,
        content,
        getattr(current_user, "username", None),
    )


@router.patch("/plan/forming-planning-notes/{note_id}")
async def update_forming_planning_note(
    note_id: int,
    body: CuttingInstructionNoteUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    return await _update_instruction_note(
        db, INSTRUCTION_NOTE_SCOPE_FORMING_PLANNING, note_id, body, current_user
    )


@router.delete("/plan/forming-planning-notes/{note_id}")
async def delete_forming_planning_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("delete")),
):
    return await _delete_instruction_note(db, INSTRUCTION_NOTE_SCOPE_FORMING_PLANNING, note_id)


@router.get("/plan/welding-planning-notes")
async def list_welding_planning_notes(
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await _list_instruction_notes(db, INSTRUCTION_NOTE_SCOPE_WELDING_PLANNING, limit)


@router.post("/plan/welding-planning-notes")
async def create_welding_planning_note(
    body: CuttingInstructionNoteCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("create")),
):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content を指定してください")
    if len(content) > 200:
        raise HTTPException(status_code=400, detail="content は200文字以内で指定してください")
    return await _create_instruction_note(
        db,
        INSTRUCTION_NOTE_SCOPE_WELDING_PLANNING,
        content,
        getattr(current_user, "username", None),
    )


@router.patch("/plan/welding-planning-notes/{note_id}")
async def update_welding_planning_note(
    note_id: int,
    body: CuttingInstructionNoteUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    return await _update_instruction_note(
        db, INSTRUCTION_NOTE_SCOPE_WELDING_PLANNING, note_id, body, current_user
    )


@router.delete("/plan/welding-planning-notes/{note_id}")
async def delete_welding_planning_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("delete")),
):
    return await _delete_instruction_note(db, INSTRUCTION_NOTE_SCOPE_WELDING_PLANNING, note_id)


@router.get("/plan/welding-instruction-notes")
async def list_welding_instruction_notes(
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return await _list_instruction_notes(db, INSTRUCTION_NOTE_SCOPE_WELDING, limit)


@router.post("/plan/welding-instruction-notes")
async def create_welding_instruction_note(
    body: CuttingInstructionNoteCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content を指定してください")
    if len(content) > 200:
        raise HTTPException(status_code=400, detail="content は200文字以内で指定してください")
    return await _create_instruction_note(
        db,
        INSTRUCTION_NOTE_SCOPE_WELDING,
        content,
        getattr(current_user, "username", None),
    )


@router.patch("/plan/welding-instruction-notes/{note_id}")
async def update_welding_instruction_note(
    note_id: int,
    body: CuttingInstructionNoteUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    return await _update_instruction_note(db, INSTRUCTION_NOTE_SCOPE_WELDING, note_id, body, current_user)


@router.delete("/plan/welding-instruction-notes/{note_id}")
async def delete_welding_instruction_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    return await _delete_instruction_note(db, INSTRUCTION_NOTE_SCOPE_WELDING, note_id)


# ---------- 検査（inspection_management）MES 実績 API ----------


async def _query_inspection_management_list(
    db: AsyncSession,
    *,
    production_day: Optional[str],
    hide_completed: bool,
    data_source: Optional[str],
    limit: int,
    join_inspector_names: bool = False,
) -> list[dict[str, Any]]:
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(
            status_code=503,
            detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
        )
    expire_day = None
    if production_day:
        expire_day = _parse_date_ymd(production_day)
    await _expire_stale_inspection_client_locks(db, im_cols, production_day=expire_day)
    mes_frag = _inspection_mgmt_mes_select_fragment(im_cols)
    meta_frag = _inspection_mgmt_meta_select_fragment(im_cols)
    join_inspector = join_inspector_names and "mes_inspector_user_id" in im_cols
    inspector_select = _inspection_mgmt_inspector_select_fragment(join_inspector)
    inspector_join = (
        "LEFT JOIN users ON users.id = inspection_management.mes_inspector_user_id"
        if join_inspector
        else ""
    )
    where_parts: list[str] = ["1=1"]
    params: dict[str, Any] = {"lim": limit}
    if production_day:
        d = _parse_date_ymd(production_day)
        if d is None:
            raise HTTPException(status_code=400, detail="production_line は必須です")
        where_parts.append("inspection_management.production_day = :production_day")
        params["production_day"] = d
    if hide_completed:
        where_parts.append("inspection_management.production_completed_check = 0")
    ds_norm = (data_source or "").strip().lower()
    if ds_norm:
        if ds_norm not in ("mes", "excel", "csv"):
            raise HTTPException(status_code=400, detail="data_source は mes / excel / csv のいずれかです")
        if "data_source" not in im_cols:
            raise HTTPException(
                status_code=503,
                detail="data_source 列が未作成です。backend/database/migrations/43_inspection_management_data_source.sql を実行してください",
            )
        where_parts.append("inspection_management.data_source = :data_source")
        params["data_source"] = ds_norm
    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT inspection_management.id,
               inspection_management.production_month,
               inspection_management.production_day,
               inspection_management.production_sequence,
               inspection_management.product_cd,
               inspection_management.product_name,
               inspection_management.actual_production_quantity,
               inspection_management.defect_qty,
               inspection_management.mes_defect_by_item,
               inspection_management.production_completed_check,
               {mes_frag}
               {inspector_select}
               {meta_frag}
               inspection_management.remarks,
               inspection_management.created_at,
               inspection_management.updated_at
        FROM inspection_management
        {inspector_join}
        WHERE {where_sql}
        ORDER BY inspection_management.production_day ASC,
                 inspection_management.production_sequence ASC,
                 inspection_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        _raise_inspection_mgmt_query_error(e)

    return [_normalize_inspection_mgmt_row(dict(row)) for row in rows]


@router.get("/plan/inspection-management/list")
async def get_inspection_management_list(
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    hide_completed: bool = Query(False, description="完了分を非表示"),
    data_source: Optional[str] = Query(
        None, description="データソース: mes / excel / csv"
    ),
    limit: int = Query(2000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件を面取ロット一覧へ戻す"""
    out = await _query_inspection_management_list(
        db,
        production_day=production_day,
        hide_completed=hide_completed,
        data_source=data_source,
        limit=limit,
    )
    return {"success": True, "data": out}


@router.get("/plan/inspection-management/monitor-summary")
async def get_inspection_monitor_summary(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    limit: int = Query(2000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_code("MES_MONITOR_INSPECTION")),
):
    """生産数未完了分を翌日へ順延する時のリクエスト"""
    if _parse_date_ymd(production_day) is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    out = await _query_inspection_management_list(
        db,
        production_day=production_day,
        hide_completed=False,
        data_source="mes",
        limit=limit,
        join_inspector_names=True,
    )
    return {
        "success": True,
        "data": out,
        "fetched_at": now_jst().isoformat(),
    }


@router.get("/plan/inspection-management/inspectors")
async def get_inspection_management_inspectors(
    start_date: Optional[str] = Query(None, description="集計開始日 YYYY-MM-DD（以上）"),
    end_date: Optional[str] = Query(None, description="集計終了日 YYYY-MM-DD（含む）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """inspection_management 一覧（検査員 users を JOIN）"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(
            status_code=503,
            detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
        )
    if "mes_inspector_user_id" not in im_cols:
        return {"success": True, "data": []}

    where_parts = [
        "inspection_management.mes_inspector_user_id IS NOT NULL",
        "inspection_management.mes_inspector_user_id > 0",
    ]
    params: dict[str, Any] = {}
    if start_date or end_date:
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")
        start_d = _parse_date_ymd(start_date)
        end_d = _parse_date_ymd(end_date)
        if start_d is None or end_d is None:
            raise HTTPException(status_code=400, detail="start_date / end_date が不正です")
        if start_d > end_d:
            raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")
        where_parts.append("inspection_management.production_day >= :start_date")
        where_parts.append("inspection_management.production_day <= :end_date")
        params["start_date"] = start_d
        params["end_date"] = end_d

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT DISTINCT
               inspection_management.mes_inspector_user_id AS id,
               users.full_name AS full_name,
               users.username AS username
        FROM inspection_management
        INNER JOIN users ON users.id = inspection_management.mes_inspector_user_id
        WHERE {where_sql}
        ORDER BY users.full_name ASC, users.username ASC, inspection_management.mes_inspector_user_id ASC
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        msg = str(e).lower()
        if "inspection_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
            ) from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    out: list[dict[str, Any]] = []
    for row in rows:
        uid = row.get("id")
        if uid is None:
            continue
        out.append(
            {
                "id": int(uid),
                "full_name": row.get("full_name"),
                "username": row.get("username"),
            }
        )
    return {"success": True, "data": out}


_INSPECTION_MES_PRODUCT_NAME_EXCLUDES = ("試作", "サンプル")
_INSPECTION_SHIAGE_SECTION_NAME = "仕上"


def _normalize_inspection_next_assignment_row(row: dict[str, Any]) -> dict[str, Any]:
    pd = row.get("production_day")
    aa = row.get("assigned_at")
    return {
        "id": row.get("id"),
        "production_day": pd.isoformat() if hasattr(pd, "isoformat") else (str(pd)[:10] if pd else None),
        "inspector_user_id": row.get("inspector_user_id"),
        "next_product_cd": row.get("next_product_cd"),
        "next_product_name": row.get("next_product_name"),
        "assigned_by_user_id": row.get("assigned_by_user_id"),
        "assigned_at": aa.isoformat() if hasattr(aa, "isoformat") else aa,
        "note": row.get("note"),
        "inspector_name": row.get("inspector_name"),
        "inspector_username": row.get("inspector_username"),
        "assigned_by_name": row.get("assigned_by_name"),
    }


def _validate_inspection_mes_product_cd_name(product_cd: str, product_name: str | None) -> tuple[str, str]:
    cd = (product_cd or "").strip()
    if not cd:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    if not cd.endswith("1"):
        raise HTTPException(status_code=400, detail="製品CD・製品名を指定してください")
    name = (product_name or "").strip() or cd
    if any(kw in name for kw in _INSPECTION_MES_PRODUCT_NAME_EXCLUDES):
        raise HTTPException(status_code=400, detail="生産日の形式が不正です")
    return cd, name


async def _inspection_next_assignment_table_ready(db: AsyncSession) -> bool:
    return await _table_has_column(db, "inspection_inspector_next_assignment", "id")


async def _assert_inspection_next_assignment_table(db: AsyncSession) -> None:
    if not await _inspection_next_assignment_table_ready(db):
        raise HTTPException(
            status_code=503,
            detail="inspection_inspector_next_assignment テーブルが存在しません。backend/database/migrations/48_inspection_inspector_next_assignment.sql を実行してください",
        )


async def _assert_active_inspection_inspector_user(db: AsyncSession, inspector_user_id: int) -> None:
    if inspector_user_id <= 0:
        raise HTTPException(status_code=400, detail="content を指定してください")
    sql = """
        SELECT u.id, o.name AS section_name
        FROM users u
        LEFT JOIN organizations o ON o.id = u.section_id
        WHERE u.id = :uid AND u.status = 'active'
        LIMIT 1
    """
    try:
        r = await db.execute(text(sql), {"uid": inspector_user_id})
        row = r.mappings().first()
        if not row:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        section = (row.get("section_name") or "").strip()
        if section and section != _INSPECTION_SHIAGE_SECTION_NAME:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _resolve_inspection_product_name(
    db: AsyncSession, product_cd: str, product_name: str | None
) -> tuple[str, str]:
    cd, name = _validate_inspection_mes_product_cd_name(product_cd, product_name)
    if (product_name or "").strip():
        return cd, name
    try:
        r = await db.execute(
            text(
                "SELECT product_name FROM products WHERE product_cd = :cd AND status = 'active' LIMIT 1"
            ),
            {"cd": cd},
        )
        row = r.first()
        if row and row[0]:
            resolved = str(row[0]).strip()
            return _validate_inspection_mes_product_cd_name(cd, resolved)
    except Exception:
        pass
    return cd, name


async def _query_inspection_next_assignments(
    db: AsyncSession, production_day: date
) -> list[dict[str, Any]]:
    await _assert_inspection_next_assignment_table(db)
    sql = """
        SELECT a.id,
               a.production_day,
               a.inspector_user_id,
               a.next_product_cd,
               a.next_product_name,
               a.assigned_by_user_id,
               a.assigned_at,
               a.note,
               insp.full_name AS inspector_name,
               insp.username AS inspector_username,
               assigner.full_name AS assigned_by_name
        FROM inspection_inspector_next_assignment a
        LEFT JOIN users insp ON insp.id = a.inspector_user_id
        LEFT JOIN users assigner ON assigner.id = a.assigned_by_user_id
        WHERE a.production_day = :production_day
        ORDER BY a.assigned_at DESC, a.id ASC
    """
    result = await db.execute(text(sql), {"production_day": production_day})
    return [_normalize_inspection_next_assignment_row(dict(row)) for row in result.mappings().all()]


class UpsertInspectionNextAssignmentBody(BaseModel):
    production_day: str
    inspector_user_id: int
    product_cd: str
    product_name: Optional[str] = None
    note: Optional[str] = None


class DeleteInspectionNextAssignmentBody(BaseModel):
    production_day: str
    inspector_user_id: int


@router.get("/plan/inspection-management/next-assignments")
async def get_inspection_next_assignments(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_menu_code("MES_MONITOR_INSPECTION", "MES_ACTUAL_INSPECTION")
    ),
):
    """面取指示1件を面取ロット一覧へ戻す"""
    d = _parse_date_ymd(production_day)
    if d is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    if not await _inspection_next_assignment_table_ready(db):
        return {"success": True, "data": []}
    data = await _query_inspection_next_assignments(db, d)
    return {"success": True, "data": data}


@router.get("/plan/inspection-management/next-assignment/me")
async def get_my_inspection_next_assignment(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_code("MES_ACTUAL_INSPECTION")),
):
    """需求量サマリーと溶接ベース使用量サマリーを1回で返す。"""
    d = _parse_date_ymd(production_day)
    if d is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    uid = _inspection_mes_inspector_user_id_from_user(current_user)
    if uid is None or uid <= 0:
        return {"success": True, "data": None}
    if not await _inspection_next_assignment_table_ready(db):
        return {"success": True, "data": None}
    sql = """
        SELECT a.id,
               a.production_day,
               a.inspector_user_id,
               a.next_product_cd,
               a.next_product_name,
               a.assigned_by_user_id,
               a.assigned_at,
               a.note,
               insp.full_name AS inspector_name,
               insp.username AS inspector_username,
               assigner.full_name AS assigned_by_name
        FROM inspection_inspector_next_assignment a
        LEFT JOIN users insp ON insp.id = a.inspector_user_id
        LEFT JOIN users assigner ON assigner.id = a.assigned_by_user_id
        WHERE a.production_day = :production_day
          AND a.inspector_user_id = :inspector_user_id
        LIMIT 1
    """
    result = await db.execute(
        text(sql),
        {"production_day": d, "inspector_user_id": uid},
    )
    row = result.mappings().first()
    if not row:
        return {"success": True, "data": None}
    return {"success": True, "data": _normalize_inspection_next_assignment_row(dict(row))}


@router.put("/plan/inspection-management/next-assignment")
async def upsert_inspection_next_assignment(
    body: UpsertInspectionNextAssignmentBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
    _menu: User = Depends(require_menu_code("MES_MONITOR_INSPECTION")),
):
    """切断指示1件を生産ロットへ戻すリクエスト"""
    d = _parse_date_ymd(body.production_day)
    if d is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    try:
        inspector_id = int(body.inspector_user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="content を指定してください")
    await _assert_inspection_next_assignment_table(db)
    await _assert_active_inspection_inspector_user(db, inspector_id)
    product_cd, product_name = await _resolve_inspection_product_name(
        db, body.product_cd, body.product_name
    )
    note = (body.note or "").strip() or None
    if note and len(note) > 500:
        raise HTTPException(status_code=400, detail="content を指定してください")
    assigner_id = _inspection_mes_inspector_user_id_from_user(current_user)
    sql = """
        INSERT INTO inspection_inspector_next_assignment (
            production_day,
            inspector_user_id,
            next_product_cd,
            next_product_name,
            assigned_by_user_id,
            assigned_at,
            note
        ) VALUES (
            :production_day,
            :inspector_user_id,
            :next_product_cd,
            :next_product_name,
            :assigned_by_user_id,
            :assigned_at,
            :note
        )
        ON DUPLICATE KEY UPDATE
            next_product_cd = VALUES(next_product_cd),
            next_product_name = VALUES(next_product_name),
            assigned_by_user_id = VALUES(assigned_by_user_id),
            assigned_at = VALUES(assigned_at),
            note = VALUES(note)
    """
    now = now_jst().replace(tzinfo=None)
    await db.execute(
        text(sql),
        {
            "production_day": d,
            "inspector_user_id": inspector_id,
            "next_product_cd": product_cd,
            "next_product_name": product_name,
            "assigned_by_user_id": assigner_id if assigner_id and assigner_id > 0 else None,
            "assigned_at": now,
            "note": note,
        },
    )
    await db.commit()
    rows = await _query_inspection_next_assignments(db, d)
    saved = next((r for r in rows if r.get("inspector_user_id") == inspector_id), None)
    return {"success": True, "message": "生成順を更新しました"}


@router.delete("/plan/inspection-management/next-assignment")
async def delete_inspection_next_assignment(
    body: DeleteInspectionNextAssignmentBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
    _menu: User = Depends(require_menu_code("MES_MONITOR_INSPECTION")),
):
    """面取ロットのSW工程フラグ更新"""
    d = _parse_date_ymd(body.production_day)
    if d is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    try:
        inspector_id = int(body.inspector_user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="content を指定してください")
    await _assert_inspection_next_assignment_table(db)
    await db.execute(
        text(
            "DELETE FROM inspection_inspector_next_assignment "
            "WHERE production_day = :production_day AND inspector_user_id = :inspector_user_id"
        ),
        {"production_day": d, "inspector_user_id": inspector_id},
    )
    await db.commit()
    return {"success": True, "message": "面取ロット一覧に戻しました"}


@router.get("/plan/inspection-management/productivity-analysis")
async def get_inspection_productivity_analysis(
    start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
    mes_inspector_user_id: Optional[int] = Query(None, description="検査員 users.id"),
    product_cd: Optional[str] = Query(None, description="製品CD"),
    include_incomplete: bool = Query(False, description="未完了セッションを含む"),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検査能率分析（inspection_management 集計）"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(
            status_code=503,
            detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
        )
    start_d = _parse_date_ymd(start_date)
    end_d = _parse_date_ymd(end_date)
    if start_d is None or end_d is None:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    mes_frag = _inspection_mgmt_mes_select_fragment(im_cols)
    meta_frag = _inspection_mgmt_meta_select_fragment(im_cols)
    join_inspector = "mes_inspector_user_id" in im_cols
    inspector_select = _inspection_mgmt_inspector_select_fragment(join_inspector)
    inspector_join = "LEFT JOIN users ON users.id = inspection_management.mes_inspector_user_id" if join_inspector else ""

    where_parts: list[str] = [
        "inspection_management.production_day >= :start_date",
        "inspection_management.production_day <= :end_date",
    ]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
    if mes_inspector_user_id is not None and join_inspector:
        where_parts.append("inspection_management.mes_inspector_user_id = :mes_inspector_user_id")
        params["mes_inspector_user_id"] = int(mes_inspector_user_id)
    product_cd_norm = (product_cd or "").strip()
    if product_cd_norm:
        where_parts.append("inspection_management.product_cd = :product_cd")
        params["product_cd"] = product_cd_norm
    if not include_incomplete:
        where_parts.append("inspection_management.production_completed_check = 1")

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT inspection_management.id,
               inspection_management.production_month,
               inspection_management.production_day,
               inspection_management.production_sequence,
               inspection_management.product_cd,
               inspection_management.product_name,
               inspection_management.actual_production_quantity,
               inspection_management.defect_qty,
               inspection_management.mes_defect_by_item,
               inspection_management.production_completed_check,
               {mes_frag}
               {inspector_select}
               {meta_frag}
               inspection_management.remarks,
               inspection_management.created_at,
               inspection_management.updated_at
        FROM inspection_management
        {inspector_join}
        WHERE {where_sql}
        ORDER BY inspection_management.production_day ASC,
                 inspection_management.production_sequence ASC,
                 inspection_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        _raise_inspection_mgmt_query_error(e)

    sessions: list[dict[str, Any]] = []
    summary_bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sum_net_production_sec": 0,
        "sum_paused_sec": 0,
    }
    daily_map: dict[str, dict[str, Any]] = {}
    inspector_map: dict[str, dict[str, Any]] = {}
    product_map: dict[str, dict[str, Any]] = {}
    product_inspector_map: dict[str, dict[str, Any]] = {}
    defect_item_map: dict[str, int] = {}
    inspector_metrics_map: dict[str, dict[str, Any]] = {}
    defect_cd_name_map = await _load_inspection_defect_cd_name_map(db)
    metrics_defect_header_index = _build_inspector_metrics_defect_header_index()
    im_col_set = set(im_cols)

    for row in rows:
        item = _normalize_inspection_mgmt_row(dict(row))
        defect_by_item = item.get("mes_defect_by_item") if isinstance(item.get("mes_defect_by_item"), dict) else None

        actual_qty = int(item.get("actual_production_quantity") or 0)
        defect_qty = int(item.get("defect_qty") or 0)
        net_sec = _inspection_row_net_production_sec(item)
        paused_sec = int(item.get("mes_paused_accum_sec") or 0)
        is_completed = int(item.get("production_completed_check") or 0) == 1
        day_key = str(item.get("production_day") or "")[:10]
        inspector_id = item.get("mes_inspector_user_id")
        inspector_key = str(inspector_id) if inspector_id is not None else "none"
        inspector_name = (item.get("mes_inspector_name") or item.get("mes_inspector_username") or "").strip()
        product_key = (item.get("product_cd") or "").strip() or "unknown"
        product_name = (item.get("product_name") or "").strip()

        session_row = _build_inspection_productivity_session_row(
            item,
            net_sec=net_sec,
            paused_sec=paused_sec,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            is_completed=is_completed,
        )
        sessions.append(session_row)

        completed_inc = 1 if is_completed else 0
        _merge_inspection_productivity_bucket(
            summary_bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )
        summary_bucket["sum_paused_sec"] = int(summary_bucket.get("sum_paused_sec") or 0) + paused_sec

        if day_key:
            if day_key not in daily_map:
                daily_map[day_key] = {
                    "day": day_key,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sum_net_production_sec": 0,
                }
            _merge_inspection_productivity_bucket(
                daily_map[day_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                net_sec=net_sec,
                completed_count=completed_inc,
            )

        if inspector_key not in inspector_map:
            inspector_map[inspector_key] = {
                "inspector_user_id": int(inspector_id) if inspector_id is not None else None,
                "inspector_name": inspector_name or (f"ID:{inspector_id}" if inspector_id else "—"),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sum_net_production_sec": 0,
            }
        _merge_inspection_productivity_bucket(
            inspector_map[inspector_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )

        if product_key not in product_map:
            product_map[product_key] = {
                "product_cd": product_key,
                "product_name": product_name or product_key,
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sum_net_production_sec": 0,
            }
        _merge_inspection_productivity_bucket(
            product_map[product_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )

        if product_key not in product_inspector_map:
            product_inspector_map[product_key] = {
                "product_cd": product_key,
                "product_name": product_name or product_key,
                "inspectors": {},
            }
        pi_bucket = product_inspector_map[product_key]["inspectors"]
        if inspector_key not in pi_bucket:
            pi_bucket[inspector_key] = {
                "inspector_user_id": int(inspector_id) if inspector_id is not None else None,
                "inspector_name": inspector_name or (f"ID:{inspector_id}" if inspector_id else "—"),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sum_net_production_sec": 0,
            }
        _merge_inspection_productivity_bucket(
            pi_bucket[inspector_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )

        if defect_by_item:
            for defect_cd, qty_raw in defect_by_item.items():
                cd = str(defect_cd or "").strip()
                if not cd:
                    continue
                qty = _mes_defect_item_qty(qty_raw)
                if qty <= 0:
                    continue
                defect_item_map[cd] = int(defect_item_map.get(cd) or 0) + qty

        if inspector_id is not None:
            metrics_inspector_key = str(inspector_id)
            inspector_username = (item.get("mes_inspector_username") or "").strip()
            display_name = _format_inspector_display_name(inspector_name, inspector_username)
            if metrics_inspector_key not in inspector_metrics_map:
                inspector_metrics_map[metrics_inspector_key] = _new_inspector_metrics_bucket(
                    inspector_user_id=int(inspector_id),
                    inspector_name=display_name,
                )
            metrics_bucket = inspector_metrics_map[metrics_inspector_key]
            shift_sec, break_sec, stop_sec, work_sec = _resolve_inspection_row_csv_time_secs(item, im_col_set)
            metrics_bucket["sum_shift_sec"] += shift_sec
            metrics_bucket["sum_break_sec"] += break_sec
            metrics_bucket["sum_stop_sec"] += stop_sec
            metrics_bucket["sum_work_sec"] += work_sec
            metrics_bucket["sum_inspection_qty"] += actual_qty
            if defect_by_item:
                for defect_cd, qty_raw in defect_by_item.items():
                    header = _resolve_inspector_metrics_defect_header(
                        str(defect_cd or ""),
                        cd_name_map=defect_cd_name_map,
                        header_index=metrics_defect_header_index,
                    )
                    if not header:
                        continue
                    qty = _mes_defect_item_qty(qty_raw)
                    if qty <= 0:
                        continue
                    metrics_bucket["defects"][header] = int(metrics_bucket["defects"].get(header) or 0) + qty

    summary = _finalize_inspection_productivity_bucket(summary_bucket)
    summary["sum_paused_sec"] = int(summary_bucket.get("sum_paused_sec") or 0)
    summary["sum_paused_min"] = round(summary["sum_paused_sec"] / 60) if summary["sum_paused_sec"] > 0 else 0
    summary["sum_net_production_min"] = (
        round(summary["sum_net_production_sec"] / 60) if summary["sum_net_production_sec"] > 0 else 0
    )

    daily = [_finalize_inspection_productivity_bucket(v) for v in sorted(daily_map.values(), key=lambda x: x["day"])]
    by_inspector = sorted(
        [_finalize_inspection_productivity_bucket(v) for v in inspector_map.values()],
        key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("inspector_name") or "")),
    )
    by_product = sorted(
        [_finalize_inspection_productivity_bucket(v) for v in product_map.values()],
        key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("product_cd") or "")),
    )
    defect_by_item = sorted(
        [{"defect_cd": cd, "qty": qty} for cd, qty in defect_item_map.items()],
        key=lambda x: (-x["qty"], x["defect_cd"]),
    )

    by_product_inspector_ranking: list[dict[str, Any]] = []
    for prod_key, prod_entry in product_inspector_map.items():
        inspectors_raw = list(prod_entry.get("inspectors", {}).values())
        inspectors_final: list[dict[str, Any]] = []
        for inv in inspectors_raw:
            fin = _finalize_inspection_productivity_bucket(dict(inv))
            if fin.get("efficiency_per_hour") is not None:
                inspectors_final.append(fin)
        inspectors_final.sort(
            key=lambda x: (
                -(x.get("efficiency_per_hour") or 0),
                -(x.get("sum_actual_qty") or 0),
                str(x.get("inspector_name") or ""),
            )
        )
        for rank_idx, inv in enumerate(inspectors_final, start=1):
            inv["rank"] = rank_idx
        prod_summary = product_map.get(prod_key) or {}
        by_product_inspector_ranking.append(
            {
                "product_cd": prod_entry.get("product_cd") or prod_key,
                "product_name": prod_entry.get("product_name") or prod_key,
                "sum_actual_qty": int(prod_summary.get("sum_actual_qty") or 0),
                "session_count": int(prod_summary.get("session_count") or 0),
                "inspector_count": len(inspectors_raw),
                "ranked_inspector_count": len(inspectors_final),
                "inspectors": inspectors_final,
                "top_inspector_name": inspectors_final[0]["inspector_name"] if inspectors_final else None,
                "top_efficiency_per_hour": inspectors_final[0]["efficiency_per_hour"] if inspectors_final else None,
            }
        )
    by_product_inspector_ranking.sort(
        key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("product_cd") or ""))
    )

    inspector_metrics_rows = sorted(
        [_finalize_inspector_metrics_row(dict(v)) for v in inspector_metrics_map.values()],
        key=lambda x: str(x.get("inspector_name") or ""),
    )
    support_row = _finalize_inspector_metrics_row(
        _new_inspector_metrics_bucket(inspector_user_id=None, inspector_name="応援")
    )
    total_metrics_row = _build_inspector_metrics_total_row(inspector_metrics_rows)

    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "include_incomplete": include_incomplete,
            "summary": summary,
            "daily": daily,
            "by_inspector": by_inspector,
            "by_product": by_product,
            "by_product_inspector_ranking": by_product_inspector_ranking,
            "defect_by_item": defect_by_item,
            "by_inspector_metrics": {
                "rows": inspector_metrics_rows,
                "support_row": support_row,
                "total_row": total_metrics_row,
                "defect_headers": list(INSPECTOR_METRICS_DEFECT_HEADERS),
            },
            "sessions": sessions,
        },
    }


@router.get("/plan/inspection-management/utilization-analysis")
async def get_inspection_utilization_analysis(
    start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
    mes_inspector_user_id: Optional[int] = Query(None, description="検査員 users.id"),
    include_incomplete: bool = Query(False, description="未完了セッションを含む"),
    issue_date: Optional[str] = Query(None, description="発行日 YYYY-MM-DD"),
    use_company_calendar: bool = Query(True, description="会社カレンダーで稼働日換算"),
    extra_workdays: Optional[str] = Query(None, description="追加稼働日（カンマ区切り YYYY-MM-DD）"),
    extra_holidays: Optional[str] = Query(None, description="追加休日（カンマ区切り YYYY-MM-DD）"),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検査生産性（inspection_management × 標準7.6h/日 × カレンダー）"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(
            status_code=503,
            detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
        )
    start_d = _parse_date_ymd(start_date)
    end_d = _parse_date_ymd(end_date)
    if start_d is None or end_d is None:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    extra_workday_set = parse_date_csv(extra_workdays)
    extra_holiday_set = parse_date_csv(extra_holidays)
    company_scheduled: set[str] = set()
    company_off: set[str] = set()
    company_calendar_applied = False
    if use_company_calendar:
        try:
            company_scheduled, company_off = await load_company_calendar_sets(db, start_d, end_d)
            company_calendar_applied = True
        except Exception as e:
            logger.warning("company_work_calendar load failed: %s", e)

    company_calendar_extra_workdays = sorted(
        iso
        for iso in company_scheduled
        if date.fromisoformat(iso).weekday() >= 5
    )
    company_calendar_holidays = sorted(company_off)

    calendar_workdays = count_scheduled_workdays(
        start_d,
        end_d,
        company_scheduled=company_scheduled,
        company_off=company_off,
        extra_workdays=extra_workday_set,
        extra_holidays=extra_holiday_set,
    )

    mes_frag = _inspection_mgmt_mes_select_fragment(im_cols)
    join_inspector = "mes_inspector_user_id" in im_cols
    inspector_select = _inspection_mgmt_inspector_select_fragment(join_inspector, trailing_comma=False)
    inspector_join = "LEFT JOIN users ON users.id = inspection_management.mes_inspector_user_id" if join_inspector else ""

    where_parts: list[str] = [
        "inspection_management.production_day >= :start_date",
        "inspection_management.production_day <= :end_date",
    ]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
    if mes_inspector_user_id is not None and join_inspector:
        where_parts.append("inspection_management.mes_inspector_user_id = :mes_inspector_user_id")
        params["mes_inspector_user_id"] = int(mes_inspector_user_id)
    if not include_incomplete:
        where_parts.append("inspection_management.production_completed_check = 1")

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT inspection_management.id,
               inspection_management.production_day,
               inspection_management.production_completed_check,
               inspection_management.product_cd,
               inspection_management.product_name,
               {mes_frag}
               {inspector_select}
        FROM inspection_management
        {inspector_join}
        WHERE {where_sql}
        ORDER BY inspection_management.production_day ASC,
                 inspection_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        _raise_inspection_mgmt_query_error(e)

    daily_inspector_map: dict[tuple[str, str], dict[str, Any]] = {}
    daily_inspector_set: dict[str, set[str]] = {}
    unassigned_session_count = 0
    sessions_without_time_count = 0
    sessions_without_time: list[dict[str, Any]] = []
    total_session_count = 0
    completed_session_count = 0

    for row in rows:
        item = dict(row)
        for k in ("mes_production_started_at", "mes_production_ended_at"):
            v = item.get(k)
            if isinstance(v, datetime):
                item[k] = v.isoformat()
        vday = item.get("production_day")
        if isinstance(vday, date):
            item["production_day"] = vday.isoformat()

        total_session_count += 1
        is_completed = int(item.get("production_completed_check") or 0) == 1
        if is_completed:
            completed_session_count += 1

        day_key = str(item.get("production_day") or "")[:10]
        if not day_key:
            continue

        inspector_id = item.get("mes_inspector_user_id")
        if inspector_id is None:
            unassigned_session_count += 1
            inspector_key = "none"
            inspector_name = "未割当"
        else:
            inspector_key = str(inspector_id)
            inspector_name = (
                (item.get("mes_inspector_name") or item.get("mes_inspector_username") or "").strip()
                or f"ID:{inspector_id}"
            )

        net_sec = _inspection_row_net_production_sec(item)
        if net_sec <= 0:
            sessions_without_time_count += 1
            sessions_without_time.append(
                {
                    "id": item.get("id"),
                    "production_day": day_key,
                    "inspector_user_id": int(inspector_id) if inspector_id is not None else None,
                    "inspector_name": inspector_name if inspector_id is not None else None,
                    "product_cd": (item.get("product_cd") or "").strip() or None,
                    "product_name": (item.get("product_name") or "").strip() or None,
                    "production_completed_check": is_completed,
                    "mes_production_started_at": item.get("mes_production_started_at"),
                    "mes_production_ended_at": item.get("mes_production_ended_at"),
                }
            )

        map_key = (day_key, inspector_key)
        if map_key not in daily_inspector_map:
            day_d = date.fromisoformat(day_key)
            scheduled = is_scheduled_workday(
                day_d,
                company_scheduled=company_scheduled,
                company_off=company_off,
                extra_workdays=extra_workday_set,
                extra_holidays=extra_holiday_set,
            )
            is_weekend = day_d.weekday() >= 5
            daily_inspector_map[map_key] = {
                "day": day_key,
                "inspector_user_id": int(inspector_id) if inspector_id is not None else None,
                "inspector_name": inspector_name,
                "is_scheduled_workday": scheduled,
                "is_weekend": is_weekend,
                "is_extra_workday": scheduled and (is_weekend or day_key in extra_workday_set),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_net_production_sec": 0,
            }
        bucket = daily_inspector_map[map_key]
        bucket["session_count"] = int(bucket.get("session_count") or 0) + 1
        bucket["completed_session_count"] = int(bucket.get("completed_session_count") or 0) + (
            1 if is_completed else 0
        )
        bucket["sum_net_production_sec"] = int(bucket.get("sum_net_production_sec") or 0) + net_sec
        daily_inspector_set.setdefault(day_key, set()).add(inspector_key)

    inspector_user_ids: set[int] = set()
    for raw in rows:
        iid = dict(raw).get("mes_inspector_user_id")
        if iid is not None:
            inspector_user_ids.add(int(iid))

    schedule_index = await load_inspector_work_schedule_index(
        db,
        start_d=start_d,
        end_d=end_d,
        inspector_user_ids=inspector_user_ids,
    )

    raw_daily_values = sorted(
        daily_inspector_map.values(),
        key=lambda x: (str(x.get("day") or ""), str(x.get("inspector_name") or "")),
    )
    for bucket in raw_daily_values:
        _apply_inspector_standard_to_daily_row(bucket, schedule_index=schedule_index)

    daily_by_inspector = [
        _finalize_inspection_utilization_daily_row(dict(v)) for v in raw_daily_values
    ]

    daily_rows_by_inspector: dict[str, list[dict[str, Any]]] = {}
    for row in daily_by_inspector:
        insp_key = (
            str(row.get("inspector_user_id"))
            if row.get("inspector_user_id") is not None
            else "none"
        )
        daily_rows_by_inspector.setdefault(insp_key, []).append(row)

    inspector_map: dict[str, dict[str, Any]] = {}
    for row in daily_by_inspector:
        insp_key = (
            str(row.get("inspector_user_id"))
            if row.get("inspector_user_id") is not None
            else "none"
        )
        if insp_key not in inspector_map:
            inspector_map[insp_key] = {
                "inspector_user_id": row.get("inspector_user_id"),
                "inspector_name": row.get("inspector_name") or "—",
                "session_count": 0,
                "work_day_count": 0,
                "scheduled_work_day_count": 0,
                "sum_net_production_sec": 0,
                "sum_regular_sec": 0,
                "sum_overtime_sec": 0,
            }
        inv = inspector_map[insp_key]
        inv["session_count"] = int(inv.get("session_count") or 0) + int(row.get("session_count") or 0)
        inv["work_day_count"] = int(inv.get("work_day_count") or 0) + 1
        if row.get("is_scheduled_workday"):
            inv["scheduled_work_day_count"] = int(inv.get("scheduled_work_day_count") or 0) + 1
        inv["sum_net_production_sec"] = int(inv.get("sum_net_production_sec") or 0) + int(
            row.get("sum_net_production_sec") or 0
        )
        inv["sum_regular_sec"] = int(inv.get("sum_regular_sec") or 0) + int(row.get("sum_regular_sec") or 0)
        inv["sum_overtime_sec"] = int(inv.get("sum_overtime_sec") or 0) + int(row.get("sum_overtime_sec") or 0)

    by_inspector = sorted(
        [
            _finalize_inspection_utilization_inspector_row(
                v,
                schedule_index=schedule_index,
                start_d=start_d,
                end_d=end_d,
                company_scheduled=company_scheduled,
                company_off=company_off,
                extra_workdays=extra_workday_set,
                extra_holidays=extra_holiday_set,
                daily_rows=daily_rows_by_inspector.get(
                    str(v.get("inspector_user_id"))
                    if v.get("inspector_user_id") is not None
                    else "none",
                    [],
                ),
            )
            for v in inspector_map.values()
        ],
        key=lambda x: (-int(x.get("sum_net_production_sec") or 0), str(x.get("inspector_name") or "")),
    )

    daily_map: dict[str, dict[str, Any]] = {}
    for row in daily_by_inspector:
        day_key = str(row.get("day") or "")
        if day_key not in daily_map:
            day_d = date.fromisoformat(day_key)
            daily_map[day_key] = {
                "day": day_key,
                "is_scheduled_workday": row.get("is_scheduled_workday"),
                "session_count": 0,
                "inspector_count": len(daily_inspector_set.get(day_key, set())),
                "sum_net_production_sec": 0,
                "sum_regular_sec": 0,
                "sum_overtime_sec": 0,
                "sum_standard_sec": 0,
            }
        day_row = daily_map[day_key]
        day_row["session_count"] = int(day_row.get("session_count") or 0) + int(row.get("session_count") or 0)
        day_row["sum_net_production_sec"] = int(day_row.get("sum_net_production_sec") or 0) + int(
            row.get("sum_net_production_sec") or 0
        )
        day_row["sum_regular_sec"] = int(day_row.get("sum_regular_sec") or 0) + int(row.get("sum_regular_sec") or 0)
        day_row["sum_overtime_sec"] = int(day_row.get("sum_overtime_sec") or 0) + int(row.get("sum_overtime_sec") or 0)
        day_row["sum_standard_sec"] = int(day_row.get("sum_standard_sec") or 0) + int(row.get("standard_sec") or 0)

    daily: list[dict[str, Any]] = []
    for day_key in sorted(daily_map.keys()):
        row = daily_map[day_key]
        net = int(row.get("sum_net_production_sec") or 0)
        regular = int(row.get("sum_regular_sec") or 0)
        overtime = int(row.get("sum_overtime_sec") or 0)
        std_total = int(row.get("sum_standard_sec") or 0)
        row["sum_net_production_min"] = round(net / 60) if net > 0 else 0
        row["utilization_percent"] = _utilization_percent(regular, std_total)
        daily.append(row)

    sum_net = sum(int(v.get("sum_net_production_sec") or 0) for v in by_inspector)
    sum_regular = sum(int(v.get("sum_regular_sec") or 0) for v in by_inspector)
    sum_overtime = sum(int(v.get("sum_overtime_sec") or 0) for v in by_inspector)
    std_worked_total = sum(int(v.get("standard_sec_on_worked_days") or 0) for v in by_inspector)
    std_calendar_total = sum(int(v.get("standard_sec_calendar") or 0) for v in by_inspector)

    summary = {
        "inspector_count": len(by_inspector),
        "session_count": total_session_count,
        "completed_session_count": completed_session_count,
        "calendar_workdays_in_range": calendar_workdays,
        "sum_net_production_sec": sum_net,
        "sum_regular_sec": sum_regular,
        "sum_overtime_sec": sum_overtime,
        "sum_net_production_min": round(sum_net / 60) if sum_net > 0 else 0,
        "regular_min": round(sum_regular / 60) if sum_regular > 0 else 0,
        "overtime_min": round(sum_overtime / 60) if sum_overtime > 0 else 0,
        "utilization_percent": _utilization_percent(sum_regular, std_worked_total),
        "calendar_utilization_percent": _utilization_percent(sum_regular, std_calendar_total),
        "unassigned_session_count": unassigned_session_count,
        "sessions_without_time_count": sessions_without_time_count,
    }

    data_gaps: list[str] = []
    if unassigned_session_count > 0:
        data_gaps.append(f"検査員未割当セッションが {unassigned_session_count} 件あります")
    if sessions_without_time_count > 0:
        data_gaps.append(f"作業時間未入力のセッションが {sessions_without_time_count} 件あります")
    if not company_calendar_applied and use_company_calendar:
        data_gaps.append("検査員勤務マスタまたは会社カレンダーが未設定のため、一部指標は参考値です")

    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "include_incomplete": include_incomplete,
            "standard_workday_hours": INSPECTION_STANDARD_WORKDAY_HOURS,
            "standard_workday_sec": INSPECTION_STANDARD_WORKDAY_SEC,
            "inspector_schedule_applied": True,
            "default_standard_workday_hours": DEFAULT_INSPECTION_STANDARD_HOURS,
            "extra_workdays": sorted(extra_workday_set),
            "extra_holidays": sorted(extra_holiday_set),
            "company_calendar_applied": company_calendar_applied,
            "company_calendar_extra_workdays": company_calendar_extra_workdays,
            "company_calendar_holidays": company_calendar_holidays,
            "calendar_workdays_in_range": calendar_workdays,
            "summary": summary,
            "by_inspector": by_inspector,
            "daily_by_inspector": daily_by_inspector,
            "daily": daily,
            "data_gaps": data_gaps,
            "sessions_without_time": sessions_without_time[:100],
        },
    }


@router.get("/plan/inspection-management/quality-analysis")
async def get_inspection_quality_analysis(
    start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
    mes_inspector_user_id: Optional[int] = Query(None, description="検査員 users.id"),
    product_cd: Optional[str] = Query(None, description="製品CD"),
    include_incomplete: bool = Query(False, description="未完了セッションを含む"),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検査不良分析（inspection_management × 工程 × 不良 × 検査員）"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(
            status_code=503,
            detail="inspection_management テーブルが存在しません。backend/database/migrations/09_inspection_management.sql を実行してください",
        )
    start_d = _parse_date_ymd(start_date)
    end_d = _parse_date_ymd(end_date)
    if start_d is None or end_d is None:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    mes_frag = _inspection_mgmt_mes_select_fragment(im_cols)
    meta_frag = _inspection_mgmt_meta_select_fragment(im_cols)
    join_inspector = "mes_inspector_user_id" in im_cols
    inspector_select = _inspection_mgmt_inspector_select_fragment(join_inspector)
    inspector_join = "LEFT JOIN users ON users.id = inspection_management.mes_inspector_user_id" if join_inspector else ""

    where_parts: list[str] = [
        "inspection_management.production_day >= :start_date",
        "inspection_management.production_day <= :end_date",
    ]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
    if mes_inspector_user_id is not None and join_inspector:
        where_parts.append("inspection_management.mes_inspector_user_id = :mes_inspector_user_id")
        params["mes_inspector_user_id"] = int(mes_inspector_user_id)
    product_cd_norm = (product_cd or "").strip()
    if product_cd_norm:
        where_parts.append("inspection_management.product_cd = :product_cd")
        params["product_cd"] = product_cd_norm
    if not include_incomplete:
        where_parts.append("inspection_management.production_completed_check = 1")

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT inspection_management.id,
               inspection_management.production_month,
               inspection_management.production_day,
               inspection_management.production_sequence,
               inspection_management.product_cd,
               inspection_management.product_name,
               inspection_management.actual_production_quantity,
               inspection_management.defect_qty,
               inspection_management.mes_defect_by_item,
               inspection_management.production_completed_check,
               {mes_frag}
               {inspector_select}
               {meta_frag}
               inspection_management.remarks,
               inspection_management.created_at,
               inspection_management.updated_at
        FROM inspection_management
        {inspector_join}
        WHERE {where_sql}
        ORDER BY inspection_management.production_day ASC,
                 inspection_management.production_sequence ASC,
                 inspection_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        _raise_inspection_mgmt_query_error(e)

    summary_bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sessions_with_defect_count": 0,
    }
    daily_map: dict[str, dict[str, Any]] = {}
    inspector_map: dict[str, dict[str, Any]] = {}
    product_map: dict[str, dict[str, Any]] = {}
    product_defect_map: dict[tuple[str, str], dict[str, Any]] = {}
    defect_item_map: dict[str, int] = {}
    defect_item_kinds: set[str] = set()
    sessions: list[dict[str, Any]] = []

    for row in rows:
        item = _normalize_inspection_mgmt_row(dict(row))
        defect_by_item = item.get("mes_defect_by_item") if isinstance(item.get("mes_defect_by_item"), dict) else None

        actual_qty = int(item.get("actual_production_quantity") or 0)
        defect_qty = int(item.get("defect_qty") or 0)
        item_defect_qty = 0
        if defect_by_item:
            for qty_raw in defect_by_item.values():
                item_defect_qty += _mes_defect_item_qty(qty_raw)
        if item_defect_qty > defect_qty:
            defect_qty = item_defect_qty
        is_completed = int(item.get("production_completed_check") or 0) == 1
        has_defect = defect_qty > 0 or bool(defect_by_item)
        day_key = str(item.get("production_day") or "")[:10]
        inspector_id = item.get("mes_inspector_user_id")
        inspector_key = str(inspector_id) if inspector_id is not None else "none"
        inspector_name = (item.get("mes_inspector_name") or item.get("mes_inspector_username") or "").strip()
        product_key = (item.get("product_cd") or "").strip() or "unknown"
        product_name = (item.get("product_name") or "").strip()

        session_row = {
            **item,
            "defect_qty": defect_qty,
            "defect_rate_percent": _inspection_defect_rate_percent(actual_qty, defect_qty),
            "is_completed": is_completed,
            "has_defect": has_defect,
            "inspector_display_name": inspector_name or (f"ID:{inspector_id}" if inspector_id else "—"),
        }
        sessions.append(session_row)

        completed_inc = 1 if is_completed else 0
        _merge_inspection_quality_bucket(
            summary_bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            completed_count=completed_inc,
            has_defect=has_defect,
        )

        if day_key:
            if day_key not in daily_map:
                daily_map[day_key] = {
                    "day": day_key,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sessions_with_defect_count": 0,
                }
            _merge_inspection_quality_bucket(
                daily_map[day_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                completed_count=completed_inc,
                has_defect=has_defect,
            )

        if inspector_key not in inspector_map:
            inspector_map[inspector_key] = {
                "inspector_user_id": int(inspector_id) if inspector_id is not None else None,
                "inspector_name": inspector_name or (f"ID:{inspector_id}" if inspector_id else "—"),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sessions_with_defect_count": 0,
            }
        _merge_inspection_quality_bucket(
            inspector_map[inspector_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            completed_count=completed_inc,
            has_defect=has_defect,
        )

        prod_bucket = product_map.get(product_key)
        if prod_bucket is None:
            prod_bucket = {
                "product_cd": product_key,
                "product_name": product_name or product_key,
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sessions_with_defect_count": 0,
                "defect_items": {},
            }
            product_map[product_key] = prod_bucket
        _merge_inspection_quality_bucket(
            prod_bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            completed_count=completed_inc,
            has_defect=has_defect,
        )

        if defect_by_item:
            for defect_cd, qty_raw in defect_by_item.items():
                cd = str(defect_cd or "").strip()
                if not cd:
                    continue
                qty = _mes_defect_item_qty(qty_raw)
                if qty <= 0:
                    continue
                defect_item_kinds.add(cd)
                defect_item_map[cd] = int(defect_item_map.get(cd) or 0) + qty
                prod_items: dict[str, int] = prod_bucket["defect_items"]
                prod_items[cd] = int(prod_items.get(cd) or 0) + qty
                pd_key = (product_key, cd)
                if pd_key not in product_defect_map:
                    product_defect_map[pd_key] = {
                        "product_cd": product_key,
                        "product_name": product_name or product_key,
                        "defect_cd": cd,
                        "qty": 0,
                    }
                product_defect_map[pd_key]["qty"] = int(product_defect_map[pd_key]["qty"] or 0) + qty

    summary = _finalize_inspection_quality_bucket(summary_bucket)
    summary["defect_item_kinds_count"] = len(defect_item_kinds)

    daily = [_finalize_inspection_quality_bucket(v) for v in sorted(daily_map.values(), key=lambda x: x["day"])]
    by_inspector = sorted(
        [_finalize_inspection_quality_bucket(v) for v in inspector_map.values()],
        key=lambda x: (-float(x.get("defect_rate_percent") or 0), -(x.get("sum_defect_qty") or 0)),
    )

    by_product: list[dict[str, Any]] = []
    for prod in product_map.values():
        fin = _finalize_inspection_quality_bucket(dict(prod))
        items: dict[str, int] = prod.get("defect_items") or {}
        if items:
            top_cd = max(items.keys(), key=lambda k: items[k])
            fin["top_defect_cd"] = top_cd
            fin["top_defect_qty"] = items[top_cd]
        fin.pop("defect_items", None)
        by_product.append(fin)
    by_product.sort(key=lambda x: (-float(x.get("defect_rate_percent") or 0), -(x.get("sum_defect_qty") or 0)))

    defect_name_map = await _load_process_defect_name_map(db, INSPECTION_DEFECT_DETECTION_PROCESS_CD)
    total_actual = int(summary.get("sum_actual_qty") or 0)
    defect_by_item = _finalize_inspection_quality_defect_rows(
        defect_item_map,
        total_actual=total_actual,
        defect_name_map=defect_name_map,
    )
    by_product_defect = sorted(
        product_defect_map.values(),
        key=lambda x: (
            str(x.get("product_cd") or ""),
            -int(x.get("qty") or 0),
            str(x.get("defect_cd") or ""),
        ),
    )
    for row in by_product_defect:
        row["defect_name"] = _defect_name_for_cd(defect_name_map, str(row.get("defect_cd") or ""))
    for fin in by_product:
        top_cd = fin.get("top_defect_cd")
        if top_cd:
            fin["top_defect_name"] = _defect_name_for_cd(defect_name_map, str(top_cd))
    for session in sessions:
        session["defect_breakdown"] = _build_defect_breakdown_rows(
            session.get("mes_defect_by_item"),
            defect_name_map,
        )

    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "include_incomplete": include_incomplete,
            "summary": summary,
            "daily": daily,
            "by_inspector": by_inspector,
            "by_product": by_product,
            "defect_by_item": defect_by_item,
            "by_product_defect": by_product_defect,
            "sessions": sessions,
        },
    }


@router.get("/plan/welding-management/quality-analysis")
async def get_welding_quality_analysis(
    start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
    mes_operator_user_id: Optional[int] = Query(None, description="作業者 users.id"),
    product_cd: Optional[str] = Query(None, description="製品CD"),
    include_incomplete: bool = Query(False, description="未完了セッションを含む"),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """Welding quality analysis (welding_management, defects, defect rate)."""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(
            status_code=503,
            detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
        )
    start_d = _parse_date_ymd(start_date)
    end_d = _parse_date_ymd(end_date)
    if start_d is None or end_d is None:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)
    wm_machine_col = (
        "welding_management.welding_machine,\n               "
        if "welding_machine" in wm_cols
        else ""
    )
    join_operator = "mes_operator_user_id" in wm_cols
    operator_select = _welding_mgmt_operator_select_fragment(join_operator)
    operator_join = "LEFT JOIN users ON users.id = welding_management.mes_operator_user_id" if join_operator else ""

    where_parts: list[str] = [
        "welding_management.production_day >= :start_date",
        "welding_management.production_day <= :end_date",
    ]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
    if mes_operator_user_id is not None and join_operator:
        where_parts.append("welding_management.mes_operator_user_id = :mes_operator_user_id")
        params["mes_operator_user_id"] = int(mes_operator_user_id)
    product_cd_norm = (product_cd or "").strip()
    if product_cd_norm:
        where_parts.append("welding_management.product_cd = :product_cd")
        params["product_cd"] = product_cd_norm
    if not include_incomplete:
        where_parts.append("welding_management.production_completed_check = 1")

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT welding_management.id,
               welding_management.production_month,
               welding_management.production_day,
               welding_management.production_sequence,
               welding_management.product_cd,
               welding_management.product_name,
               {wm_machine_col}welding_management.actual_production_quantity,
               welding_management.defect_qty,
               welding_management.mes_defect_by_item,
               welding_management.production_completed_check,
               {mes_frag}
               {operator_select}
               welding_management.remarks,
               welding_management.created_at,
               welding_management.updated_at
        FROM welding_management
        {operator_join}
        WHERE {where_sql}
        ORDER BY welding_management.production_day ASC,
                 welding_management.production_sequence ASC,
                 welding_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        _raise_welding_mgmt_query_error(e)

    summary_bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sessions_with_defect_count": 0,
    }
    daily_map: dict[str, dict[str, Any]] = {}
    operator_map: dict[str, dict[str, Any]] = {}
    product_map: dict[str, dict[str, Any]] = {}
    product_defect_map: dict[tuple[str, str], dict[str, Any]] = {}
    defect_item_map: dict[str, int] = {}
    defect_item_kinds: set[str] = set()
    sessions: list[dict[str, Any]] = []

    for row in rows:
        item = _normalize_welding_mgmt_row(dict(row))
        defect_by_item = item.get("mes_defect_by_item") if isinstance(item.get("mes_defect_by_item"), dict) else None

        actual_qty = int(item.get("actual_production_quantity") or 0)
        defect_qty = int(item.get("defect_qty") or 0)
        item_defect_qty = 0
        if defect_by_item:
            for qty_raw in defect_by_item.values():
                item_defect_qty += _mes_defect_item_qty(qty_raw)
        if item_defect_qty > defect_qty:
            defect_qty = item_defect_qty
        is_completed = int(item.get("production_completed_check") or 0) == 1
        has_defect = defect_qty > 0 or bool(defect_by_item)
        day_key = str(item.get("production_day") or "")[:10]
        operator_id = item.get("mes_operator_user_id")
        operator_key = str(operator_id) if operator_id is not None else "none"
        operator_name = (item.get("mes_operator_name") or item.get("mes_operator_username") or "").strip()
        product_key = (item.get("product_cd") or "").strip() or "unknown"
        product_name = (item.get("product_name") or "").strip()

        session_row = {
            **item,
            "defect_qty": defect_qty,
            "defect_rate_percent": _inspection_defect_rate_percent(actual_qty, defect_qty),
            "is_completed": is_completed,
            "has_defect": has_defect,
            "operator_display_name": operator_name or (f"ID:{operator_id}" if operator_id else "—"),
        }
        sessions.append(session_row)

        completed_inc = 1 if is_completed else 0
        _merge_inspection_quality_bucket(
            summary_bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            completed_count=completed_inc,
            has_defect=has_defect,
        )

        if day_key:
            if day_key not in daily_map:
                daily_map[day_key] = {
                    "day": day_key,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sessions_with_defect_count": 0,
                }
            _merge_inspection_quality_bucket(
                daily_map[day_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                completed_count=completed_inc,
                has_defect=has_defect,
            )

        if operator_key not in operator_map:
            operator_map[operator_key] = {
                "operator_user_id": int(operator_id) if operator_id is not None else None,
                "operator_name": operator_name or (f"ID:{operator_id}" if operator_id else "—"),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sessions_with_defect_count": 0,
            }
        _merge_inspection_quality_bucket(
            operator_map[operator_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            completed_count=completed_inc,
            has_defect=has_defect,
        )

        prod_bucket = product_map.get(product_key)
        if prod_bucket is None:
            prod_bucket = {
                "product_cd": product_key,
                "product_name": product_name or product_key,
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sessions_with_defect_count": 0,
                "defect_items": {},
            }
            product_map[product_key] = prod_bucket
        _merge_inspection_quality_bucket(
            prod_bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            completed_count=completed_inc,
            has_defect=has_defect,
        )

        if defect_by_item:
            for defect_cd, qty_raw in defect_by_item.items():
                cd = str(defect_cd or "").strip()
                if not cd:
                    continue
                qty = _mes_defect_item_qty(qty_raw)
                if qty <= 0:
                    continue
                defect_item_kinds.add(cd)
                defect_item_map[cd] = int(defect_item_map.get(cd) or 0) + qty
                prod_items: dict[str, int] = prod_bucket["defect_items"]
                prod_items[cd] = int(prod_items.get(cd) or 0) + qty
                pd_key = (product_key, cd)
                if pd_key not in product_defect_map:
                    product_defect_map[pd_key] = {
                        "product_cd": product_key,
                        "product_name": product_name or product_key,
                        "defect_cd": cd,
                        "qty": 0,
                    }
                product_defect_map[pd_key]["qty"] = int(product_defect_map[pd_key]["qty"] or 0) + qty

    summary = _finalize_inspection_quality_bucket(summary_bucket)
    summary["defect_item_kinds_count"] = len(defect_item_kinds)

    daily = [_finalize_inspection_quality_bucket(v) for v in sorted(daily_map.values(), key=lambda x: x["day"])]
    by_operator = sorted(
        [_finalize_inspection_quality_bucket(v) for v in operator_map.values()],
        key=lambda x: (-float(x.get("defect_rate_percent") or 0), -(x.get("sum_defect_qty") or 0)),
    )

    by_product: list[dict[str, Any]] = []
    for prod in product_map.values():
        fin = _finalize_inspection_quality_bucket(dict(prod))
        items: dict[str, int] = prod.get("defect_items") or {}
        if items:
            top_cd = max(items.keys(), key=lambda k: items[k])
            fin["top_defect_cd"] = top_cd
            fin["top_defect_qty"] = items[top_cd]
        fin.pop("defect_items", None)
        by_product.append(fin)
    by_product.sort(key=lambda x: (-float(x.get("defect_rate_percent") or 0), -(x.get("sum_defect_qty") or 0)))

    defect_name_map = await _load_process_defect_name_map(db, WELDING_DEFECT_DETECTION_PROCESS_CD)
    total_actual = int(summary.get("sum_actual_qty") or 0)
    defect_by_item = _finalize_inspection_quality_defect_rows(
        defect_item_map,
        total_actual=total_actual,
        defect_name_map=defect_name_map,
    )
    by_product_defect = sorted(
        product_defect_map.values(),
        key=lambda x: (
            str(x.get("product_cd") or ""),
            -int(x.get("qty") or 0),
            str(x.get("defect_cd") or ""),
        ),
    )
    for row in by_product_defect:
        row["defect_name"] = _defect_name_for_cd(defect_name_map, str(row.get("defect_cd") or ""))
    for fin in by_product:
        top_cd = fin.get("top_defect_cd")
        if top_cd:
            fin["top_defect_name"] = _defect_name_for_cd(defect_name_map, str(top_cd))
    for session in sessions:
        session["defect_breakdown"] = _build_defect_breakdown_rows(
            session.get("mes_defect_by_item"),
            defect_name_map,
        )

    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "include_incomplete": include_incomplete,
            "summary": summary,
            "daily": daily,
            "by_operator": by_operator,
            "by_product": by_product,
            "defect_by_item": defect_by_item,
            "by_product_defect": by_product_defect,
            "sessions": sessions,
        },
    }


class CreateInspectionManagementBody(BaseModel):
    production_day: str
    product_cd: str
    product_name: str
    mes_inspector_user_id: Optional[int] = None
    remarks: Optional[str] = None
    manual_registration_note: Optional[str] = None
    manual_registration: bool = False


@router.post("/plan/inspection-management")
async def create_inspection_management(
    body: CreateInspectionManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
    d = _parse_date_ymd(body.production_day)
    if d is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    product_cd = (body.product_cd or "").strip()
    product_name = (body.product_name or "").strip()
    if not product_cd:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    if not product_name:
        product_name = product_cd
    prod_month = d.replace(day=1)
    seq_row = await db.execute(
        text(
            "SELECT COALESCE(MAX(production_sequence), 0) + 1 AS n FROM inspection_management "
            "WHERE production_day = :pday"
        ),
        {"pday": d},
    )
    seq = int(seq_row.scalar() or 1)
    login_uid = _inspection_mes_inspector_user_id_from_user(current_user)
    inspector_id = body.mes_inspector_user_id
    if inspector_id is not None and int(inspector_id) > 0:
        if not body.manual_registration:
            _reject_inspection_mes_inspector_not_current_user(current_user, inspector_id)
    else:
        inspector_id = login_uid
    params: dict[str, Any] = {
        "production_month": prod_month,
        "production_day": d,
        "production_sequence": seq,
        "product_cd": product_cd,
        "product_name": product_name,
    }
    cols = [
        "production_month",
        "production_day",
        "production_sequence",
        "product_cd",
        "product_name",
    ]
    vals = [
        ":production_month",
        ":production_day",
        ":production_sequence",
        ":product_cd",
        ":product_name",
    ]
    if body.manual_registration:
        if "manual_registration_note" in im_cols:
            cols.append("manual_registration_note")
            vals.append(":manual_registration_note")
            params["manual_registration_note"] = (body.manual_registration_note or "").strip() or None
    else:
        cols.append("remarks")
        vals.append(":remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if inspector_id is not None and int(inspector_id) > 0 and "mes_inspector_user_id" in im_cols:
        cols.append("mes_inspector_user_id")
        vals.append(":mes_inspector_user_id")
        params["mes_inspector_user_id"] = int(inspector_id)
    if "data_source" in im_cols:
        cols.append("data_source")
        vals.append(":data_source")
        params["data_source"] = DATA_SOURCE_MES
    try:
        res = await db.execute(
            text(
                f"INSERT INTO inspection_management ({', '.join(cols)}) "
                f"VALUES ({', '.join(vals)})"
            ),
            params,
        )
        await db.commit()
        new_id = res.lastrowid
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "data": {"id": new_id}, "message": "登録しました"}


class UpdateInspectionManagementBody(BaseModel):
    production_day: Optional[str] = None
    production_sequence: Optional[int] = None
    actual_production_quantity: Optional[int] = None
    defect_qty: Optional[int] = None
    production_completed_check: Optional[bool] = None
    remarks: Optional[str] = None
    manual_registration_note: Optional[str] = None
    mes_production_started_at: Optional[str] = None
    mes_production_ended_at: Optional[str] = None
    mes_net_production_sec: Optional[int] = None
    mes_paused_accum_sec: Optional[int] = None
    mes_break_sec: Optional[int] = None
    mes_stop_sec: Optional[int] = None
    mes_shift_sec: Optional[int] = None
    mes_production_is_paused: Optional[int] = None
    mes_inspector_user_id: Optional[int] = None
    mes_defect_by_item: Optional[Any] = None
    mes_client_instance_id: Optional[str] = None
    mes_claim_client_lock: Optional[bool] = None
    mes_force_release: Optional[bool] = None
    mes_release_client_lock: Optional[bool] = None
    manual_registration: bool = False


@router.patch("/plan/inspection-management/{inspection_id}")
async def update_inspection_management(
    inspection_id: int,
    body: UpdateInspectionManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
    await _expire_stale_inspection_client_locks(db, im_cols, inspection_id=inspection_id)
    if _inspection_mes_row_mutation_requested(body) and not body.manual_registration:
        row_insp = await _fetch_inspection_row_mes_inspector(db, inspection_id, im_cols)
        if body.mes_inspector_user_id is not None:
            _reject_inspection_mes_inspector_not_current_user(current_user, body.mes_inspector_user_id)
            try:
                clear_insp = int(body.mes_inspector_user_id)
            except (TypeError, ValueError):
                clear_insp = -1
            if clear_insp <= 0 and row_insp is not None:
                _reject_inspection_mes_inspector_not_current_user(current_user, row_insp)
        elif row_insp is not None:
            _reject_inspection_mes_inspector_not_current_user(current_user, row_insp)
    row_mes = await _fetch_inspection_row_mes_state(db, inspection_id, im_cols)
    row_started = row_mes.get("mes_production_started_at")
    row_ended = row_mes.get("mes_production_ended_at")
    in_progress = _inspection_row_mes_in_progress(row_started, row_ended)
    row_already_completed = _inspection_row_mes_completed(row_started, row_ended)
    client_id = _normalize_mes_client_instance_id(body.mes_client_instance_id)
    force_release = bool(body.mes_force_release)
    existing_lock = _normalize_mes_client_instance_id(row_mes.get("mes_client_instance_id"))
    has_client_col = "mes_client_instance_id" in im_cols

    updates: list[str] = []
    params: dict[str, Any] = {"iid": inspection_id}
    mes_state_broadcast = False

    if body.mes_release_client_lock:
        if not has_client_col:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_client_instance_id"))
        if not force_release:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        if not in_progress:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        updates.append("mes_client_instance_id = NULL")
        if _inspection_mes_lock_activity_column(im_cols):
            updates.append("mes_client_lock_activity_at = NULL")
        mes_state_broadcast = True

    if body.mes_claim_client_lock:
        if not has_client_col:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_client_instance_id"))
        if not client_id:
            raise HTTPException(status_code=400, detail="content が空です")
        if not in_progress:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        allow_inspector_reclaim = False
        if body.mes_inspector_user_id is not None and "mes_inspector_user_id" in im_cols:
            try:
                claim_inspector = int(body.mes_inspector_user_id)
            except (TypeError, ValueError):
                claim_inspector = 0
            if claim_inspector > 0:
                insp_row = await db.execute(
                    text(
                        "SELECT mes_inspector_user_id FROM inspection_management WHERE id = :iid LIMIT 1"
                    ),
                    {"iid": inspection_id},
                )
                row_insp = insp_row.scalar()
                if row_insp is not None and int(row_insp) == claim_inspector:
                    allow_inspector_reclaim = True
        if not allow_inspector_reclaim:
            _reject_inspection_mes_client_lock_conflict(existing_lock, client_id, force_release=force_release)
        params["mes_client_instance_id"] = client_id
        updates.append("mes_client_instance_id = :mes_client_instance_id")
        _append_inspection_client_lock_activity_touch(updates, params, im_cols)
        mes_state_broadcast = True
    if body.production_day is not None:
        d = _parse_date_ymd(body.production_day)
        if d is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = d.replace(day=1)
            updates.append("production_day = :production_day")
            params["production_day"] = d
    if body.production_completed_check is not None:
        updates.append("production_completed_check = :production_completed_check")
        params["production_completed_check"] = 1 if body.production_completed_check else 0
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = max(0, int(body.actual_production_quantity))
    if body.production_sequence is not None:
        updates.append("production_sequence = :production_sequence")
        params["production_sequence"] = int(body.production_sequence)
    if body.remarks is not None and not body.manual_registration:
        updates.append("remarks = :remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if body.manual_registration_note is not None:
        if "manual_registration_note" not in im_cols:
            raise HTTPException(
                status_code=503,
                detail="manual_registration_note 列が未作成です。backend/database/migrations/47_inspection_management_manual_registration_note.sql を実行してください",
            )
        updates.append("manual_registration_note = :manual_registration_note")
        params["manual_registration_note"] = (body.manual_registration_note or "").strip() or None
    if body.defect_qty is not None:
        updates.append("defect_qty = :defect_qty")
        params["defect_qty"] = max(0, int(body.defect_qty))
    if body.mes_production_started_at is not None:
        if "mes_production_started_at" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_production_started_at"))
        raw = body.mes_production_started_at.strip() if isinstance(body.mes_production_started_at, str) else ""
        if raw == "":
            updates.append("mes_production_started_at = NULL")
        else:
            sdt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_started_at)
            if sdt:
                if not row_already_completed and not body.manual_registration:
                    start_inspector: Optional[int] = None
                    if body.mes_inspector_user_id is not None:
                        try:
                            parsed_inspector = int(body.mes_inspector_user_id)
                            if parsed_inspector > 0:
                                start_inspector = parsed_inspector
                        except (TypeError, ValueError):
                            start_inspector = None
                    await _reject_concurrent_mes_production_on_inspection_start(
                        db,
                        inspection_id,
                        im_cols,
                        inspector_user_id=start_inspector,
                    )
                    if has_client_col:
                        if not client_id:
                            raise HTTPException(status_code=400, detail="mes_client_instance_id が未設定です")
                        _reject_inspection_mes_client_lock_conflict(
                            existing_lock,
                            client_id,
                            force_release=force_release,
                        )
                        params["mes_client_instance_id"] = client_id
                        updates.append("mes_client_instance_id = :mes_client_instance_id")
                        _append_inspection_client_lock_activity_touch(updates, params, im_cols)
                params["mes_production_started_at"] = sdt
                updates.append("mes_production_started_at = :mes_production_started_at")
                mes_state_broadcast = True
    if body.mes_production_ended_at is not None:
        if "mes_production_ended_at" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_production_ended_at"))
        raw = body.mes_production_ended_at.strip() if isinstance(body.mes_production_ended_at, str) else ""
        if raw == "":
            updates.append("mes_production_ended_at = NULL")
        else:
            edt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_ended_at)
            if edt:
                if in_progress and not body.manual_registration:
                    _reject_inspection_mes_client_lock_conflict(
                        existing_lock,
                        client_id,
                        force_release=force_release,
                    )
                params["mes_production_ended_at"] = edt
                updates.append("mes_production_ended_at = :mes_production_ended_at")
                if has_client_col and not body.manual_registration:
                    updates.append("mes_client_instance_id = NULL")
                    if _inspection_mes_lock_activity_column(im_cols):
                        updates.append("mes_client_lock_activity_at = NULL")
                mes_state_broadcast = True
    if body.mes_net_production_sec is not None:
        if "mes_net_production_sec" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_net_production_sec"))
        net_sec = int(body.mes_net_production_sec)
        if net_sec < 0:
            updates.append("mes_net_production_sec = NULL")
        else:
            updates.append("mes_net_production_sec = :mes_net_production_sec")
            params["mes_net_production_sec"] = max(0, net_sec)
    if body.mes_paused_accum_sec is not None:
        if "mes_paused_accum_sec" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_paused_accum_sec"))
        pause_sec = int(body.mes_paused_accum_sec)
        if pause_sec < 0:
            updates.append("mes_paused_accum_sec = NULL")
        else:
            updates.append("mes_paused_accum_sec = :mes_paused_accum_sec")
            params["mes_paused_accum_sec"] = max(0, pause_sec)
    if body.mes_break_sec is not None:
        if "mes_break_sec" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_break_sec"))
        break_sec = int(body.mes_break_sec)
        if break_sec < 0:
            updates.append("mes_break_sec = NULL")
        else:
            updates.append("mes_break_sec = :mes_break_sec")
            params["mes_break_sec"] = max(0, break_sec)
    if body.mes_stop_sec is not None:
        if "mes_stop_sec" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_stop_sec"))
        stop_sec = int(body.mes_stop_sec)
        if stop_sec < 0:
            updates.append("mes_stop_sec = NULL")
        else:
            updates.append("mes_stop_sec = :mes_stop_sec")
            params["mes_stop_sec"] = max(0, stop_sec)
    if body.mes_shift_sec is not None:
        if "mes_shift_sec" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_shift_sec"))
        shift_sec = int(body.mes_shift_sec)
        if shift_sec < 0:
            updates.append("mes_shift_sec = NULL")
        else:
            updates.append("mes_shift_sec = :mes_shift_sec")
            params["mes_shift_sec"] = max(0, shift_sec)
    if body.mes_production_is_paused is not None:
        if "mes_production_is_paused" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_production_is_paused"))
        flag = int(body.mes_production_is_paused)
        if flag < 0:
            updates.append("mes_production_is_paused = NULL")
        else:
            params["mes_production_is_paused"] = max(0, min(2, flag))
            updates.append("mes_production_is_paused = :mes_production_is_paused")
    if body.mes_inspector_user_id is not None:
        if "mes_inspector_user_id" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_inspector_user_id"))
        iid = int(body.mes_inspector_user_id)
        if iid <= 0:
            updates.append("mes_inspector_user_id = NULL")
        else:
            params["mes_inspector_user_id"] = iid
            updates.append("mes_inspector_user_id = :mes_inspector_user_id")
    if body.mes_defect_by_item is not None:
        if "mes_defect_by_item" not in im_cols:
            raise HTTPException(status_code=503, detail=_inspection_mes_column_migration_hint("mes_defect_by_item"))
        try:
            if body.mes_defect_by_item == "" or body.mes_defect_by_item == {}:
                updates.append("mes_defect_by_item = NULL")
                updates.append("defect_qty = 0")
            else:
                json_str = _parse_mes_defect_by_item_for_db(body.mes_defect_by_item)
                if json_str is None:
                    updates.append("mes_defect_by_item = NULL")
                    updates.append("defect_qty = 0")
                else:
                    params["mes_defect_by_item"] = json_str
                    updates.append("mes_defect_by_item = CAST(:mes_defect_by_item AS JSON)")
                    params["defect_qty"] = _sum_defect_qty_from_item_json(json_str)
                    updates.append("defect_qty = :defect_qty")
        except (ValueError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=400, detail=f"日付が不正です: {e}") from e

    mes_control_touched = (
        body.mes_net_production_sec is not None
        or body.mes_paused_accum_sec is not None
        or body.mes_break_sec is not None
        or body.mes_stop_sec is not None
        or body.mes_production_is_paused is not None
        or body.mes_defect_by_item is not None
        or (body.mes_inspector_user_id is not None and in_progress)
    )
    if mes_control_touched and in_progress and has_client_col and not body.mes_claim_client_lock and not body.manual_registration:
        _reject_inspection_mes_client_lock_conflict(
            existing_lock,
            client_id,
            force_release=force_release,
        )
        if not existing_lock and client_id:
            params["mes_client_instance_id"] = client_id
            if "mes_client_instance_id = :mes_client_instance_id" not in updates:
                updates.append("mes_client_instance_id = :mes_client_instance_id")
        _append_inspection_client_lock_activity_touch(updates, params, im_cols)
        mes_state_broadcast = True

    if not updates:
        return {"success": True, "message": "変更なし"}
    try:
        await db.execute(
            text(f"UPDATE inspection_management SET {', '.join(updates)} WHERE id = :iid"),
            params,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    if mes_state_broadcast or mes_control_touched or body.mes_production_started_at is not None:
        try:
            pd_row = await db.execute(
                text("SELECT production_day FROM inspection_management WHERE id = :iid LIMIT 1"),
                {"iid": inspection_id},
            )
            pd_val = pd_row.scalar()
            if pd_val is not None:
                from app.modules.websocket.api import notify_mes_inspection_state_change

                await notify_mes_inspection_state_change(str(pd_val), inspection_id)
        except Exception as ws_exc:
            logger.warning("[WebSocket] mes_inspection_state broadcast failed: %s", ws_exc)
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/inspection-management/{inspection_id}")
async def delete_inspection_management(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    """面取指示1件を面取ロット一覧へ戻す"""
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
    result = await db.execute(
        text("SELECT id FROM inspection_management WHERE id = :iid LIMIT 1"),
        {"iid": inspection_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    try:
        await db.execute(
            text("DELETE FROM inspection_management WHERE id = :iid"),
            {"iid": inspection_id},
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


# ---------- 溶接（welding_management）MES 実績 API ----------


@router.get("/plan/welding-management/monitor-summary")
async def get_welding_monitor_summary(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    limit: int = Query(2000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_code("MES_MONITOR_WELDING")),
):
    """生産数未完了分を翌日へ順延する時のリクエスト"""
    if _parse_date_ymd(production_day) is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(
            status_code=503,
            detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
        )
    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)
    where_parts: list[str] = ["1=1"]
    params: dict[str, Any] = {"lim": limit}
    d = _parse_date_ymd(production_day)
    where_parts.append("welding_management.production_day = :production_day")
    params["production_day"] = d
    if "data_source" in wm_cols:
        where_parts.append("welding_management.data_source = :data_source")
        params["data_source"] = "mes"
    where_sql = " AND ".join(where_parts)
    wm_machine_col = (
        "welding_management.welding_machine,\n               "
        if "welding_machine" in wm_cols
        else ""
    )
    sql = f"""
        SELECT welding_management.id,
               welding_management.production_month,
               welding_management.production_day,
               welding_management.production_sequence,
               welding_management.product_cd,
               welding_management.product_name,
               {wm_machine_col}welding_management.actual_production_quantity,
               welding_management.defect_qty,
               welding_management.mes_defect_by_item,
               welding_management.production_completed_check,
               {mes_frag}
               welding_management.remarks,
               welding_management.created_at,
               welding_management.updated_at
        FROM welding_management
        WHERE {where_sql}
        ORDER BY welding_management.production_day ASC,
                 welding_management.production_sequence ASC,
                 welding_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        msg = str(e).lower()
        if "welding_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
            ) from e
        for col in _WELDING_MGMT_MES_COLUMNS:
            if col in msg:
                raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint(col)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    out: list[dict] = []
    for row in rows:
        item = dict(row)
        raw_def = item.get("mes_defect_by_item")
        if raw_def is not None and not isinstance(raw_def, dict):
            try:
                item["mes_defect_by_item"] = json.loads(raw_def) if str(raw_def).strip() else None
            except json.JSONDecodeError:
                item["mes_defect_by_item"] = None
        for k in ("mes_production_started_at", "mes_production_ended_at", "created_at", "updated_at"):
            v = item.get(k)
            if isinstance(v, datetime):
                item[k] = v.isoformat()
        for k in ("production_month", "production_day"):
            v = item.get(k)
            if isinstance(v, date):
                item[k] = v.isoformat()
        out.append(item)
    return {
        "success": True,
        "data": out,
        "fetched_at": now_jst().isoformat(),
    }


@router.get("/plan/welding-management/list")
async def get_welding_management_list(
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    welding_machine: Optional[str] = Query(None, description="溶接機（完全一致でフィルタ）"),
    hide_completed: bool = Query(False, description="完了分を非表示"),
    limit: int = Query(2000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件を面取ロット一覧へ戻す"""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(
            status_code=503,
            detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
        )
    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)
    meta_frag = _welding_mgmt_meta_select_fragment(wm_cols)
    where_parts: list[str] = ["1=1"]
    params: dict[str, Any] = {"lim": limit}
    if production_day:
        d = _parse_date_ymd(production_day)
        if d is None:
            raise HTTPException(status_code=400, detail="production_line は必須です")
        where_parts.append("welding_management.production_day = :production_day")
        params["production_day"] = d
    if hide_completed:
        where_parts.append("welding_management.production_completed_check = 0")
    if welding_machine is not None and welding_machine.strip():
        if "welding_machine" not in wm_cols:
            raise HTTPException(
                status_code=503,
                detail="列 `welding_machine` が未作成です。backend/database/migrations/14_welding_management_welding_machine.sql を実行してください",
            )
        where_parts.append("welding_management.welding_machine = :welding_machine")
        params["welding_machine"] = welding_machine.strip()
    where_sql = " AND ".join(where_parts)
    wm_machine_col = (
        "welding_management.welding_machine,\n               "
        if "welding_machine" in wm_cols
        else ""
    )
    sql = f"""
        SELECT welding_management.id,
               welding_management.production_month,
               welding_management.production_day,
               welding_management.production_sequence,
               welding_management.product_cd,
               welding_management.product_name,
               {wm_machine_col}welding_management.actual_production_quantity,
               welding_management.defect_qty,
               welding_management.mes_defect_by_item,
               welding_management.production_completed_check,
               {mes_frag}
               {meta_frag}
               welding_management.remarks,
               welding_management.created_at,
               welding_management.updated_at
        FROM welding_management
        WHERE {where_sql}
        ORDER BY welding_management.production_day ASC,
                 welding_management.production_sequence ASC,
                 welding_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        msg = str(e).lower()
        if "welding_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
            ) from e
        for col in _WELDING_MGMT_MES_COLUMNS:
            if col in msg:
                raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint(col)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"success": True, "data": [_normalize_welding_mgmt_row(dict(row)) for row in rows]}


class CreateWeldingManagementBody(BaseModel):
    production_day: str
    product_cd: str
    product_name: str
    welding_machine: Optional[str] = None
    mes_operator_user_id: Optional[int] = None
    remarks: Optional[str] = None
    manual_registration_note: Optional[str] = None
    manual_registration: bool = False


@router.post("/plan/welding-management")
async def create_welding_management(
    body: CreateWeldingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
    d = _parse_date_ymd(body.production_day)
    if d is None:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    product_cd = (body.product_cd or "").strip()
    product_name = (body.product_name or "").strip()
    if not product_cd:
        raise HTTPException(status_code=400, detail="production_line は必須です")
    if not product_name:
        product_name = product_cd
    prod_month = d.replace(day=1)
    seq_row = await db.execute(
        text(
            "SELECT COALESCE(MAX(production_sequence), 0) + 1 AS n FROM welding_management "
            "WHERE production_day = :pday"
        ),
        {"pday": d},
    )
    seq = int(seq_row.scalar() or 1)
    inspector_id = body.mes_operator_user_id
    params: dict[str, Any] = {
        "production_month": prod_month,
        "production_day": d,
        "production_sequence": seq,
        "product_cd": product_cd,
        "product_name": product_name,
    }
    cols = [
        "production_month",
        "production_day",
        "production_sequence",
        "product_cd",
        "product_name",
    ]
    vals = [
        ":production_month",
        ":production_day",
        ":production_sequence",
        ":product_cd",
        ":product_name",
    ]
    if body.manual_registration:
        if "manual_registration_note" in wm_cols:
            cols.append("manual_registration_note")
            vals.append(":manual_registration_note")
            params["manual_registration_note"] = (body.manual_registration_note or "").strip() or None
    else:
        cols.append("remarks")
        vals.append(":remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if inspector_id is not None and int(inspector_id) > 0 and "mes_operator_user_id" in wm_cols:
        cols.append("mes_operator_user_id")
        vals.append(":mes_operator_user_id")
        params["mes_operator_user_id"] = int(inspector_id)
    wm_name = (body.welding_machine or "").strip()
    if wm_name and "welding_machine" in wm_cols:
        cols.append("welding_machine")
        vals.append(":welding_machine")
        params["welding_machine"] = wm_name
    if "data_source" in wm_cols:
        cols.append("data_source")
        vals.append(":data_source")
        params["data_source"] = DATA_SOURCE_MES
    try:
        res = await db.execute(
            text(
                f"INSERT INTO welding_management ({', '.join(cols)}) "
                f"VALUES ({', '.join(vals)})"
            ),
            params,
        )
        await db.commit()
        new_id = res.lastrowid
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "data": {"id": new_id}, "message": "登録しました"}


class UpdateWeldingManagementBody(BaseModel):
    production_day: Optional[str] = None
    welding_machine: Optional[str] = None
    production_sequence: Optional[int] = None
    actual_production_quantity: Optional[int] = None
    defect_qty: Optional[int] = None
    production_completed_check: Optional[bool] = None
    remarks: Optional[str] = None
    mes_production_started_at: Optional[str] = None
    mes_production_ended_at: Optional[str] = None
    mes_net_production_sec: Optional[int] = None
    mes_paused_accum_sec: Optional[int] = None
    mes_shift_sec: Optional[int] = None
    mes_break_sec: Optional[int] = None
    mes_stop_sec: Optional[int] = None
    mes_production_is_paused: Optional[int] = None
    mes_operator_user_id: Optional[int] = None
    mes_defect_by_item: Optional[Any] = None
    mes_client_instance_id: Optional[str] = None
    mes_claim_client_lock: Optional[bool] = None
    mes_release_client_lock: Optional[bool] = None
    mes_force_release: Optional[bool] = None
    manual_registration_note: Optional[str] = None
    manual_registration: bool = False


@router.patch("/plan/welding-management/{welding_id}")
async def update_welding_management(
    welding_id: int,
    body: UpdateWeldingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
    row_mes = await _fetch_welding_row_mes_state(db, welding_id, wm_cols)
    in_progress = _welding_row_mes_in_progress(
        row_mes.get("mes_production_started_at"),
        row_mes.get("mes_production_ended_at"),
    )
    client_id = _normalize_mes_client_instance_id(body.mes_client_instance_id)
    force_release = bool(body.mes_force_release)
    existing_lock = _normalize_mes_client_instance_id(row_mes.get("mes_client_instance_id"))
    has_client_col = "mes_client_instance_id" in wm_cols

    updates: list[str] = []
    params: dict[str, Any] = {"wid": welding_id}

    if body.mes_release_client_lock:
        if not has_client_col:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_client_instance_id"))
        if not force_release:
            raise HTTPException(status_code=400, detail="mes_force_release required")
        if not in_progress:
            raise HTTPException(status_code=409, detail="not in progress")
        updates.append("mes_client_instance_id = NULL")

    if body.mes_claim_client_lock:
        if not has_client_col:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_client_instance_id"))
        if not client_id:
            raise HTTPException(status_code=400, detail="content が空です")
        if not in_progress:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        allow_inspector_reclaim = False
        if body.mes_operator_user_id is not None and "mes_operator_user_id" in wm_cols:
            try:
                claim_inspector = int(body.mes_operator_user_id)
            except (TypeError, ValueError):
                claim_inspector = 0
            if claim_inspector > 0:
                insp_row = await db.execute(
                    text(
                        "SELECT mes_operator_user_id FROM welding_management WHERE id = :wid LIMIT 1"
                    ),
                    {"wid": welding_id},
                )
                row_insp = insp_row.scalar()
                if row_insp is None or int(row_insp) == claim_inspector:
                    allow_inspector_reclaim = True
        if not allow_inspector_reclaim:
            _reject_welding_mes_client_lock_conflict(existing_lock, client_id, force_release=force_release)
        params["mes_client_instance_id"] = client_id
        updates.append("mes_client_instance_id = :mes_client_instance_id")
    if body.production_day is not None:
        d = _parse_date_ymd(body.production_day)
        if d is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = d.replace(day=1)
            updates.append("production_day = :production_day")
            params["production_day"] = d
    if body.production_completed_check is not None:
        updates.append("production_completed_check = :production_completed_check")
        params["production_completed_check"] = 1 if body.production_completed_check else 0
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = max(0, int(body.actual_production_quantity))
    if body.production_sequence is not None:
        updates.append("production_sequence = :production_sequence")
        params["production_sequence"] = int(body.production_sequence)
    if body.remarks is not None and not body.manual_registration:
        updates.append("remarks = :remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if body.manual_registration_note is not None:
        if "manual_registration_note" not in wm_cols:
            raise HTTPException(
                status_code=503,
                detail="manual_registration_note 列が未作成です。backend/database/migrations/57_welding_management_manual_registration_note.sql を実行してください",
            )
        updates.append("manual_registration_note = :manual_registration_note")
        params["manual_registration_note"] = (body.manual_registration_note or "").strip() or None
    if body.welding_machine is not None and "welding_machine" in wm_cols:
        wm_val = (body.welding_machine or "").strip()
        if wm_val:
            updates.append("welding_machine = :welding_machine")
            params["welding_machine"] = wm_val
        else:
            updates.append("welding_machine = NULL")
    if body.defect_qty is not None:
        updates.append("defect_qty = :defect_qty")
        params["defect_qty"] = max(0, int(body.defect_qty))
    if body.mes_production_started_at is not None:
        if "mes_production_started_at" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_production_started_at"))
        raw = body.mes_production_started_at.strip() if isinstance(body.mes_production_started_at, str) else ""
        if raw == "":
            updates.append("mes_production_started_at = NULL")
        else:
            sdt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_started_at)
            if sdt:
                if not body.manual_registration and not in_progress:
                    start_inspector: Optional[int] = None
                    if body.mes_operator_user_id is not None:
                        try:
                            parsed_inspector = int(body.mes_operator_user_id)
                            if parsed_inspector > 0:
                                start_inspector = parsed_inspector
                        except (TypeError, ValueError):
                            start_inspector = None
                    if "welding_machine" in wm_cols:
                        wm_hint = (body.welding_machine or "").strip() or None
                        await _reject_concurrent_mes_production_on_welding_machine(
                            db, welding_id, wm_cols, machine_hint=wm_hint
                        )
                        await _reject_concurrent_mes_production_on_welding_start(
                            db,
                            welding_id,
                            wm_cols,
                            operator_user_id=start_inspector,
                        )
                    else:
                        await _reject_concurrent_mes_production_on_welding_start(
                            db,
                            welding_id,
                            wm_cols,
                            operator_user_id=start_inspector,
                        )
                    if has_client_col:
                        if not client_id:
                            raise HTTPException(status_code=400, detail="mes_client_instance_id が未設定です")
                        _reject_welding_mes_client_lock_conflict(
                            existing_lock,
                            client_id,
                            force_release=force_release,
                        )
                        params["mes_client_instance_id"] = client_id
                        updates.append("mes_client_instance_id = :mes_client_instance_id")
                elif (
                    not body.manual_registration
                    and in_progress
                    and has_client_col
                    and client_id
                    and not body.mes_claim_client_lock
                ):
                    _reject_welding_mes_client_lock_conflict(
                        existing_lock,
                        client_id,
                        force_release=force_release,
                    )
                params["mes_production_started_at"] = sdt
                updates.append("mes_production_started_at = :mes_production_started_at")
    if body.mes_production_ended_at is not None:
        if "mes_production_ended_at" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_production_ended_at"))
        raw = body.mes_production_ended_at.strip() if isinstance(body.mes_production_ended_at, str) else ""
        if raw == "":
            updates.append("mes_production_ended_at = NULL")
        else:
            edt = _parse_mes_datetime_to_naive_tokyo(body.mes_production_ended_at)
            if edt:
                if in_progress and not body.manual_registration:
                    _reject_welding_mes_client_lock_conflict(
                        existing_lock,
                        client_id,
                        force_release=force_release,
                    )
                params["mes_production_ended_at"] = edt
                updates.append("mes_production_ended_at = :mes_production_ended_at")
                if has_client_col and not body.manual_registration:
                    updates.append("mes_client_instance_id = NULL")
    if body.mes_net_production_sec is not None:
        if "mes_net_production_sec" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_net_production_sec"))
        net_sec = int(body.mes_net_production_sec)
        if net_sec < 0:
            updates.append("mes_net_production_sec = NULL")
        else:
            updates.append("mes_net_production_sec = :mes_net_production_sec")
            params["mes_net_production_sec"] = max(0, net_sec)
    if body.mes_paused_accum_sec is not None:
        if "mes_paused_accum_sec" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_paused_accum_sec"))
        pause_sec = int(body.mes_paused_accum_sec)
        if pause_sec < 0:
            updates.append("mes_paused_accum_sec = NULL")
        else:
            updates.append("mes_paused_accum_sec = :mes_paused_accum_sec")
            params["mes_paused_accum_sec"] = max(0, pause_sec)
    if body.mes_shift_sec is not None:
        if "mes_shift_sec" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_shift_sec"))
        shift_sec = int(body.mes_shift_sec)
        if shift_sec < 0:
            updates.append("mes_shift_sec = NULL")
        else:
            updates.append("mes_shift_sec = :mes_shift_sec")
            params["mes_shift_sec"] = max(0, shift_sec)
    if body.mes_break_sec is not None:
        if "mes_break_sec" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_break_sec"))
        break_sec = int(body.mes_break_sec)
        if break_sec < 0:
            updates.append("mes_break_sec = NULL")
        else:
            updates.append("mes_break_sec = :mes_break_sec")
            params["mes_break_sec"] = max(0, break_sec)
    if body.mes_stop_sec is not None:
        if "mes_stop_sec" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_stop_sec"))
        stop_sec = int(body.mes_stop_sec)
        if stop_sec < 0:
            updates.append("mes_stop_sec = NULL")
        else:
            updates.append("mes_stop_sec = :mes_stop_sec")
            params["mes_stop_sec"] = max(0, stop_sec)
    if body.mes_production_is_paused is not None:
        if "mes_production_is_paused" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_production_is_paused"))
        flag = int(body.mes_production_is_paused)
        if flag < 0:
            updates.append("mes_production_is_paused = NULL")
        else:
            params["mes_production_is_paused"] = max(0, min(2, flag))
            updates.append("mes_production_is_paused = :mes_production_is_paused")
    if body.mes_operator_user_id is not None:
        if "mes_operator_user_id" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_operator_user_id"))
        iid = int(body.mes_operator_user_id)
        if iid <= 0:
            updates.append("mes_operator_user_id = NULL")
        else:
            params["mes_operator_user_id"] = iid
            updates.append("mes_operator_user_id = :mes_operator_user_id")
    if body.mes_defect_by_item is not None:
        if "mes_defect_by_item" not in wm_cols:
            raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint("mes_defect_by_item"))
        try:
            if body.mes_defect_by_item == "" or body.mes_defect_by_item == {}:
                updates.append("mes_defect_by_item = NULL")
                updates.append("defect_qty = 0")
            else:
                json_str = _parse_mes_defect_by_item_for_db(body.mes_defect_by_item)
                if json_str is None:
                    updates.append("mes_defect_by_item = NULL")
                    updates.append("defect_qty = 0")
                else:
                    params["mes_defect_by_item"] = json_str
                    updates.append("mes_defect_by_item = CAST(:mes_defect_by_item AS JSON)")
                    params["defect_qty"] = _sum_defect_qty_from_item_json(json_str)
                    updates.append("defect_qty = :defect_qty")
        except (ValueError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=400, detail=f"日付が不正です: {e}") from e

    mes_control_touched = (
        body.mes_net_production_sec is not None
        or body.mes_paused_accum_sec is not None
        or body.mes_shift_sec is not None
        or body.mes_break_sec is not None
        or body.mes_stop_sec is not None
        or body.mes_production_is_paused is not None
        or body.mes_defect_by_item is not None
        or (body.mes_operator_user_id is not None and in_progress)
    )
    if mes_control_touched and in_progress and has_client_col and not body.mes_claim_client_lock and not body.manual_registration:
        _reject_welding_mes_client_lock_conflict(
            existing_lock,
            client_id,
            force_release=force_release,
        )
        if not existing_lock and client_id:
            params["mes_client_instance_id"] = client_id
            if "mes_client_instance_id = :mes_client_instance_id" not in updates:
                updates.append("mes_client_instance_id = :mes_client_instance_id")

    if not updates:
        return {"success": True, "message": "変更なし"}
    try:
        await db.execute(
            text(f"UPDATE welding_management SET {', '.join(updates)} WHERE id = :wid"),
            params,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/welding-management/{welding_id}")
async def delete_welding_management(
    welding_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    """面取指示1件を面取ロット一覧へ戻す"""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
    result = await db.execute(
        text("SELECT id FROM welding_management WHERE id = :wid LIMIT 1"),
        {"wid": welding_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    try:
        await db.execute(
            text("DELETE FROM welding_management WHERE id = :wid"),
            {"wid": welding_id},
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.get("/plan/welding-management/productivity-analysis")
async def get_welding_productivity_analysis(
    start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
    mes_operator_user_id: Optional[int] = Query(None, description="作業者 users.id"),
    product_cd: Optional[str] = Query(None, description="製品CD"),
    include_incomplete: bool = Query(False, description="未完了セッションを含む"),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """溶接能率分析（welding_management 集計）"""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(
            status_code=503,
            detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
        )
    start_d = _parse_date_ymd(start_date)
    end_d = _parse_date_ymd(end_date)
    if start_d is None or end_d is None:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)
    wm_machine_col = (
        "welding_management.welding_machine,\n               "
        if "welding_machine" in wm_cols
        else ""
    )
    join_operator = "mes_operator_user_id" in wm_cols
    operator_select = (
        "users.full_name AS mes_operator_name,\n               users.username AS mes_operator_username,"
        if join_operator
        else "NULL AS mes_operator_name,\n               NULL AS mes_operator_username,"
    )
    operator_join = "LEFT JOIN users ON users.id = welding_management.mes_operator_user_id" if join_operator else ""

    where_parts: list[str] = [
        "welding_management.production_day >= :start_date",
        "welding_management.production_day <= :end_date",
    ]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
    if mes_operator_user_id is not None and join_operator:
        where_parts.append("welding_management.mes_operator_user_id = :mes_operator_user_id")
        params["mes_operator_user_id"] = int(mes_operator_user_id)
    product_cd_norm = (product_cd or "").strip()
    if product_cd_norm:
        where_parts.append("welding_management.product_cd = :product_cd")
        params["product_cd"] = product_cd_norm
    if not include_incomplete:
        where_parts.append("welding_management.production_completed_check = 1")

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT welding_management.id,
               welding_management.production_month,
               welding_management.production_day,
               welding_management.production_sequence,
               welding_management.product_cd,
               welding_management.product_name,
               {wm_machine_col}welding_management.actual_production_quantity,
               welding_management.defect_qty,
               welding_management.mes_defect_by_item,
               welding_management.production_completed_check,
               {mes_frag}
               {operator_select}
               welding_management.remarks,
               welding_management.created_at,
               welding_management.updated_at
        FROM welding_management
        {operator_join}
        WHERE {where_sql}
        ORDER BY welding_management.production_day ASC,
                 welding_management.production_sequence ASC,
                 welding_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        msg = str(e).lower()
        if "welding_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
            ) from e
        for col in _WELDING_MGMT_MES_COLUMNS:
            if col in msg:
                raise HTTPException(status_code=503, detail=_welding_mes_column_migration_hint(col)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    sessions: list[dict[str, Any]] = []
    summary_bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sum_net_production_sec": 0,
        "sum_paused_sec": 0,
    }
    daily_map: dict[str, dict[str, Any]] = {}
    operator_map: dict[str, dict[str, Any]] = {}
    product_map: dict[str, dict[str, Any]] = {}
    product_operator_map: dict[str, dict[str, Any]] = {}
    defect_item_map: dict[str, int] = {}

    for row in rows:
        item = dict(row)
        raw_def = item.get("mes_defect_by_item")
        defect_by_item: Optional[dict[str, int]] = None
        if raw_def is not None and not isinstance(raw_def, dict):
            try:
                defect_by_item = json.loads(raw_def) if str(raw_def).strip() else None
            except json.JSONDecodeError:
                defect_by_item = None
        elif isinstance(raw_def, dict):
            defect_by_item = raw_def
        item["mes_defect_by_item"] = defect_by_item

        for k in ("mes_production_started_at", "mes_production_ended_at", "created_at", "updated_at"):
            v = item.get(k)
            if isinstance(v, datetime):
                item[k] = v.isoformat()
        for k in ("production_month", "production_day"):
            v = item.get(k)
            if isinstance(v, date):
                item[k] = v.isoformat()

        actual_qty = int(item.get("actual_production_quantity") or 0)
        defect_qty = int(item.get("defect_qty") or 0)
        net_sec = _welding_row_net_production_sec(item)
        paused_sec = int(item.get("mes_paused_accum_sec") or 0)
        is_completed = int(item.get("production_completed_check") or 0) == 1
        day_key = str(item.get("production_day") or "")[:10]
        operator_id = item.get("mes_operator_user_id")
        operator_key = str(operator_id) if operator_id is not None else "none"
        operator_name = (item.get("mes_operator_name") or item.get("mes_operator_username") or "").strip()
        product_key = (item.get("product_cd") or "").strip() or "unknown"
        product_name = (item.get("product_name") or "").strip()

        session_row = {
            "id": int(item["id"]) if item.get("id") is not None else None,
            "production_day": day_key or None,
            "product_cd": (item.get("product_cd") or "").strip() or None,
            "product_name": (item.get("product_name") or "").strip() or None,
            "actual_production_quantity": actual_qty,
            "defect_qty": defect_qty,
            "mes_operator_user_id": int(operator_id) if operator_id is not None else None,
            "mes_operator_name": operator_name or None,
            "mes_operator_username": (item.get("mes_operator_username") or "").strip() or None,
            "operator_display_name": operator_name or (f"ID:{operator_id}" if operator_id else "—"),
            "net_production_sec": int(net_sec),
            "paused_sec": int(paused_sec),
            "net_production_min": int(round(net_sec / 60)) if net_sec > 0 else 0,
            "paused_min": int(round(paused_sec / 60)) if paused_sec > 0 else 0,
            "efficiency_per_hour": _inspection_efficiency_per_hour(actual_qty, net_sec),
            "defect_rate_percent": _inspection_defect_rate_percent(actual_qty, defect_qty),
            "is_completed": is_completed,
        }
        sessions.append(session_row)

        completed_inc = 1 if is_completed else 0
        _merge_inspection_productivity_bucket(
            summary_bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )
        summary_bucket["sum_paused_sec"] = int(summary_bucket.get("sum_paused_sec") or 0) + paused_sec

        if day_key:
            if day_key not in daily_map:
                daily_map[day_key] = {
                    "day": day_key,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sum_net_production_sec": 0,
                }
            _merge_inspection_productivity_bucket(
                daily_map[day_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                net_sec=net_sec,
                completed_count=completed_inc,
            )

        if operator_key not in operator_map:
            operator_map[operator_key] = {
                "operator_user_id": int(operator_id) if operator_id is not None else None,
                "operator_name": operator_name or (f"ID:{operator_id}" if operator_id else "—"),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sum_net_production_sec": 0,
            }
        _merge_inspection_productivity_bucket(
            operator_map[operator_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )

        if product_key not in product_map:
            product_map[product_key] = {
                "product_cd": product_key,
                "product_name": product_name or product_key,
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sum_net_production_sec": 0,
            }
        _merge_inspection_productivity_bucket(
            product_map[product_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )

        if product_key not in product_operator_map:
            product_operator_map[product_key] = {
                "product_cd": product_key,
                "product_name": product_name or product_key,
                "operators": {},
            }
        pi_bucket = product_operator_map[product_key]["operators"]
        if operator_key not in pi_bucket:
            pi_bucket[operator_key] = {
                "operator_user_id": int(operator_id) if operator_id is not None else None,
                "operator_name": operator_name or (f"ID:{operator_id}" if operator_id else "—"),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_actual_qty": 0,
                "sum_defect_qty": 0,
                "sum_net_production_sec": 0,
            }
        _merge_inspection_productivity_bucket(
            pi_bucket[operator_key],
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=completed_inc,
        )

        if defect_by_item:
            for defect_cd, qty_raw in defect_by_item.items():
                cd = str(defect_cd or "").strip()
                if not cd:
                    continue
                qty = _mes_defect_item_qty(qty_raw)
                if qty <= 0:
                    continue
                defect_item_map[cd] = int(defect_item_map.get(cd) or 0) + qty

    summary = _finalize_inspection_productivity_bucket(summary_bucket)
    summary["sum_paused_sec"] = int(summary_bucket.get("sum_paused_sec") or 0)
    summary["sum_paused_min"] = round(summary["sum_paused_sec"] / 60) if summary["sum_paused_sec"] > 0 else 0
    summary["sum_net_production_min"] = (
        round(summary["sum_net_production_sec"] / 60) if summary["sum_net_production_sec"] > 0 else 0
    )

    daily = [_finalize_inspection_productivity_bucket(v) for v in sorted(daily_map.values(), key=lambda x: x["day"])]
    by_operator = sorted(
        [_finalize_inspection_productivity_bucket(v) for v in operator_map.values()],
        key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("operator_name") or "")),
    )
    by_product = sorted(
        [_finalize_inspection_productivity_bucket(v) for v in product_map.values()],
        key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("product_cd") or "")),
    )
    defect_by_item = sorted(
        [{"defect_cd": cd, "qty": qty} for cd, qty in defect_item_map.items()],
        key=lambda x: (-x["qty"], x["defect_cd"]),
    )

    by_product_operator_ranking: list[dict[str, Any]] = []
    for prod_key, prod_entry in product_operator_map.items():
        operators_raw = list(prod_entry.get("operators", {}).values())
        operators_final: list[dict[str, Any]] = []
        for inv in operators_raw:
            fin = _finalize_inspection_productivity_bucket(dict(inv))
            if fin.get("efficiency_per_hour") is not None:
                operators_final.append(fin)
        operators_final.sort(
            key=lambda x: (
                -(x.get("efficiency_per_hour") or 0),
                -(x.get("sum_actual_qty") or 0),
                str(x.get("operator_name") or ""),
            )
        )
        for rank_idx, inv in enumerate(operators_final, start=1):
            inv["rank"] = rank_idx
        prod_summary = product_map.get(prod_key) or {}
        by_product_operator_ranking.append(
            {
                "product_cd": prod_entry.get("product_cd") or prod_key,
                "product_name": prod_entry.get("product_name") or prod_key,
                "sum_actual_qty": int(prod_summary.get("sum_actual_qty") or 0),
                "session_count": int(prod_summary.get("session_count") or 0),
                "operator_count": len(operators_raw),
                "ranked_operator_count": len(operators_final),
                "operators": operators_final,
                "top_operator_name": operators_final[0]["operator_name"] if operators_final else None,
                "top_efficiency_per_hour": operators_final[0]["efficiency_per_hour"] if operators_final else None,
            }
        )
    by_product_operator_ranking.sort(
        key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("product_cd") or ""))
    )

    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "include_incomplete": include_incomplete,
            "summary": summary,
            "daily": daily,
            "by_operator": by_operator,
            "by_product": by_product,
            "by_product_operator_ranking": by_product_operator_ranking,
            "defect_by_item": defect_by_item,
            "sessions": sessions,
        },
    }

@router.get("/plan/welding-management/utilization-analysis")
async def get_welding_utilization_analysis(
    start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
    end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
    mes_operator_user_id: Optional[int] = Query(None, description="作業者 users.id"),
    include_incomplete: bool = Query(False, description="未完了セッションを含む"),
    issue_date: Optional[str] = Query(None, description="発行日 YYYY-MM-DD"),
    use_company_calendar: bool = Query(True, description="会社カレンダーで稼働日換算"),
    extra_workdays: Optional[str] = Query(None, description="追加稼働日（カンマ区切り YYYY-MM-DD）"),
    extra_holidays: Optional[str] = Query(None, description="追加休日（カンマ区切り YYYY-MM-DD）"),
    limit: int = Query(5000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """Welding utilization analysis (welding_management, 7.6h/day standard)."""
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        raise HTTPException(
            status_code=503,
            detail="welding_management テーブルが存在しません。backend/database/migrations/13_welding_management.sql を実行してください",
        )
    start_d = _parse_date_ymd(start_date)
    end_d = _parse_date_ymd(end_date)
    if start_d is None or end_d is None:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    extra_workday_set = parse_date_csv(extra_workdays)
    extra_holiday_set = parse_date_csv(extra_holidays)
    company_scheduled: set[str] = set()
    company_off: set[str] = set()
    company_calendar_applied = False
    if use_company_calendar:
        try:
            company_scheduled, company_off = await load_company_calendar_sets(db, start_d, end_d)
            company_calendar_applied = True
        except Exception as e:
            logger.warning("company_work_calendar load failed: %s", e)

    company_calendar_extra_workdays = sorted(
        iso for iso in company_scheduled if date.fromisoformat(iso).weekday() >= 5
    )
    company_calendar_holidays = sorted(company_off)

    calendar_workdays = count_scheduled_workdays(
        start_d,
        end_d,
        company_scheduled=company_scheduled,
        company_off=company_off,
        extra_workdays=extra_workday_set,
        extra_holidays=extra_holiday_set,
    )

    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)
    join_operator = "mes_operator_user_id" in wm_cols
    operator_select = _welding_mgmt_operator_select_fragment(join_operator, trailing_comma=False)
    operator_join = "LEFT JOIN users ON users.id = welding_management.mes_operator_user_id" if join_operator else ""

    where_parts: list[str] = [
        "welding_management.production_day >= :start_date",
        "welding_management.production_day <= :end_date",
    ]
    params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
    if mes_operator_user_id is not None and join_operator:
        where_parts.append("welding_management.mes_operator_user_id = :mes_operator_user_id")
        params["mes_operator_user_id"] = int(mes_operator_user_id)
    if not include_incomplete:
        where_parts.append("welding_management.production_completed_check = 1")

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT welding_management.id,
               welding_management.production_day,
               welding_management.production_completed_check,
               welding_management.product_cd,
               welding_management.product_name,
               {mes_frag}
               {operator_select}
        FROM welding_management
        {operator_join}
        WHERE {where_sql}
        ORDER BY welding_management.production_day ASC,
                 welding_management.id ASC
        LIMIT :lim
    """
    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
    except Exception as e:
        _raise_welding_mgmt_query_error(e)

    daily_operator_map: dict[tuple[str, str], dict[str, Any]] = {}
    daily_operator_set: dict[str, set[str]] = {}
    unassigned_session_count = 0
    sessions_without_time_count = 0
    sessions_without_time: list[dict[str, Any]] = []
    total_session_count = 0
    completed_session_count = 0

    for row in rows:
        item = dict(row)
        for k in ("mes_production_started_at", "mes_production_ended_at"):
            v = item.get(k)
            if isinstance(v, datetime):
                item[k] = v.isoformat()
        vday = item.get("production_day")
        if isinstance(vday, date):
            item["production_day"] = vday.isoformat()

        total_session_count += 1
        is_completed = int(item.get("production_completed_check") or 0) == 1
        if is_completed:
            completed_session_count += 1

        day_key = str(item.get("production_day") or "")[:10]
        if not day_key:
            continue

        operator_id = item.get("mes_operator_user_id")
        if operator_id is None:
            unassigned_session_count += 1
            operator_key = "none"
            operator_name = "未割当"
        else:
            operator_key = str(operator_id)
            operator_name = (
                (item.get("mes_operator_name") or item.get("mes_operator_username") or "").strip()
                or f"ID:{operator_id}"
            )

        net_sec = _welding_row_net_production_sec(item)
        if net_sec <= 0:
            sessions_without_time_count += 1
            sessions_without_time.append(
                {
                    "id": item.get("id"),
                    "production_day": day_key,
                    "operator_user_id": int(operator_id) if operator_id is not None else None,
                    "operator_name": operator_name if operator_id is not None else None,
                    "product_cd": (item.get("product_cd") or "").strip() or None,
                    "product_name": (item.get("product_name") or "").strip() or None,
                    "production_completed_check": is_completed,
                    "mes_production_started_at": item.get("mes_production_started_at"),
                    "mes_production_ended_at": item.get("mes_production_ended_at"),
                }
            )

        map_key = (day_key, operator_key)
        if map_key not in daily_operator_map:
            day_d = date.fromisoformat(day_key)
            scheduled = is_scheduled_workday(
                day_d,
                company_scheduled=company_scheduled,
                company_off=company_off,
                extra_workdays=extra_workday_set,
                extra_holidays=extra_holiday_set,
            )
            is_weekend = day_d.weekday() >= 5
            daily_operator_map[map_key] = {
                "day": day_key,
                "operator_user_id": int(operator_id) if operator_id is not None else None,
                "operator_name": operator_name,
                "is_scheduled_workday": scheduled,
                "is_weekend": is_weekend,
                "is_extra_workday": scheduled and (is_weekend or day_key in extra_workday_set),
                "session_count": 0,
                "completed_session_count": 0,
                "sum_net_production_sec": 0,
            }
        bucket = daily_operator_map[map_key]
        bucket["session_count"] = int(bucket.get("session_count") or 0) + 1
        bucket["completed_session_count"] = int(bucket.get("completed_session_count") or 0) + (
            1 if is_completed else 0
        )
        bucket["sum_net_production_sec"] = int(bucket.get("sum_net_production_sec") or 0) + net_sec
        daily_operator_set.setdefault(day_key, set()).add(operator_key)

    schedule_index = InspectorWorkScheduleIndex()

    raw_daily_values = sorted(
        daily_operator_map.values(),
        key=lambda x: (str(x.get("day") or ""), str(x.get("operator_name") or "")),
    )
    for bucket in raw_daily_values:
        _apply_operator_standard_to_daily_row(bucket, schedule_index=schedule_index)

    daily_by_operator = [
        _finalize_inspection_utilization_daily_row(dict(v)) for v in raw_daily_values
    ]

    daily_rows_by_operator: dict[str, list[dict[str, Any]]] = {}
    for row in daily_by_operator:
        op_key = (
            str(row.get("operator_user_id")) if row.get("operator_user_id") is not None else "none"
        )
        daily_rows_by_operator.setdefault(op_key, []).append(row)

    operator_map: dict[str, dict[str, Any]] = {}
    for row in daily_by_operator:
        op_key = (
            str(row.get("operator_user_id")) if row.get("operator_user_id") is not None else "none"
        )
        if op_key not in operator_map:
            operator_map[op_key] = {
                "operator_user_id": row.get("operator_user_id"),
                "operator_name": row.get("operator_name") or "—",
                "session_count": 0,
                "work_day_count": 0,
                "scheduled_work_day_count": 0,
                "sum_net_production_sec": 0,
                "sum_regular_sec": 0,
                "sum_overtime_sec": 0,
            }
        inv = operator_map[op_key]
        inv["session_count"] = int(inv.get("session_count") or 0) + int(row.get("session_count") or 0)
        inv["work_day_count"] = int(inv.get("work_day_count") or 0) + 1
        if row.get("is_scheduled_workday"):
            inv["scheduled_work_day_count"] = int(inv.get("scheduled_work_day_count") or 0) + 1
        inv["sum_net_production_sec"] = int(inv.get("sum_net_production_sec") or 0) + int(
            row.get("sum_net_production_sec") or 0
        )
        inv["sum_regular_sec"] = int(inv.get("sum_regular_sec") or 0) + int(row.get("sum_regular_sec") or 0)
        inv["sum_overtime_sec"] = int(inv.get("sum_overtime_sec") or 0) + int(row.get("sum_overtime_sec") or 0)

    by_operator = sorted(
        [
            _finalize_welding_utilization_operator_row(
                v,
                schedule_index=schedule_index,
                start_d=start_d,
                end_d=end_d,
                company_scheduled=company_scheduled,
                company_off=company_off,
                extra_workdays=extra_workday_set,
                extra_holidays=extra_holiday_set,
                daily_rows=daily_rows_by_operator.get(
                    str(v.get("operator_user_id"))
                    if v.get("operator_user_id") is not None
                    else "none",
                    [],
                ),
            )
            for v in operator_map.values()
        ],
        key=lambda x: (-int(x.get("sum_net_production_sec") or 0), str(x.get("operator_name") or "")),
    )

    daily_map: dict[str, dict[str, Any]] = {}
    for row in daily_by_operator:
        day_key = str(row.get("day") or "")
        if day_key not in daily_map:
            daily_map[day_key] = {
                "day": day_key,
                "is_scheduled_workday": row.get("is_scheduled_workday"),
                "session_count": 0,
                "operator_count": len(daily_operator_set.get(day_key, set())),
                "sum_net_production_sec": 0,
                "sum_regular_sec": 0,
                "sum_overtime_sec": 0,
                "sum_standard_sec": 0,
            }
        day_row = daily_map[day_key]
        day_row["session_count"] = int(day_row.get("session_count") or 0) + int(row.get("session_count") or 0)
        day_row["sum_net_production_sec"] = int(day_row.get("sum_net_production_sec") or 0) + int(
            row.get("sum_net_production_sec") or 0
        )
        day_row["sum_regular_sec"] = int(day_row.get("sum_regular_sec") or 0) + int(row.get("sum_regular_sec") or 0)
        day_row["sum_overtime_sec"] = int(day_row.get("sum_overtime_sec") or 0) + int(row.get("sum_overtime_sec") or 0)
        day_row["sum_standard_sec"] = int(day_row.get("sum_standard_sec") or 0) + int(row.get("standard_sec") or 0)

    daily: list[dict[str, Any]] = []
    for day_key in sorted(daily_map.keys()):
        row = daily_map[day_key]
        net = int(row.get("sum_net_production_sec") or 0)
        regular = int(row.get("sum_regular_sec") or 0)
        overtime = int(row.get("sum_overtime_sec") or 0)
        std_total = int(row.get("sum_standard_sec") or 0)
        row["sum_net_production_min"] = round(net / 60) if net > 0 else 0
        row["utilization_percent"] = _utilization_percent(regular, std_total)
        daily.append(row)

    sum_net = sum(int(v.get("sum_net_production_sec") or 0) for v in by_operator)
    sum_regular = sum(int(v.get("sum_regular_sec") or 0) for v in by_operator)
    sum_overtime = sum(int(v.get("sum_overtime_sec") or 0) for v in by_operator)
    std_worked_total = sum(int(v.get("standard_sec_on_worked_days") or 0) for v in by_operator)
    std_calendar_total = sum(int(v.get("standard_sec_calendar") or 0) for v in by_operator)

    summary = {
        "operator_count": len(by_operator),
        "session_count": total_session_count,
        "completed_session_count": completed_session_count,
        "calendar_workdays_in_range": calendar_workdays,
        "sum_net_production_sec": sum_net,
        "sum_regular_sec": sum_regular,
        "sum_overtime_sec": sum_overtime,
        "sum_net_production_min": round(sum_net / 60) if sum_net > 0 else 0,
        "regular_min": round(sum_regular / 60) if sum_regular > 0 else 0,
        "overtime_min": round(sum_overtime / 60) if sum_overtime > 0 else 0,
        "utilization_percent": _utilization_percent(sum_regular, std_worked_total),
        "calendar_utilization_percent": _utilization_percent(sum_regular, std_calendar_total),
        "unassigned_session_count": unassigned_session_count,
        "sessions_without_time_count": sessions_without_time_count,
    }

    data_gaps: list[str] = []
    if unassigned_session_count > 0:
        data_gaps.append(f"作業者未割当セッションが {unassigned_session_count} 件あります")
    if sessions_without_time_count > 0:
        data_gaps.append(f"作業時間未入力のセッションが {sessions_without_time_count} 件あります")
    if not company_calendar_applied and use_company_calendar:
        data_gaps.append("検査員勤務マスタまたは会社カレンダーが未設定のため、一部指標は参考値です")

    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "include_incomplete": include_incomplete,
            "standard_workday_hours": INSPECTION_STANDARD_WORKDAY_HOURS,
            "standard_workday_sec": INSPECTION_STANDARD_WORKDAY_SEC,
            "operator_schedule_applied": False,
            "default_standard_workday_hours": DEFAULT_INSPECTION_STANDARD_HOURS,
            "extra_workdays": sorted(extra_workday_set),
            "extra_holidays": sorted(extra_holiday_set),
            "company_calendar_applied": company_calendar_applied,
            "company_calendar_extra_workdays": company_calendar_extra_workdays,
            "company_calendar_holidays": company_calendar_holidays,
            "calendar_workdays_in_range": calendar_workdays,
            "summary": summary,
            "by_operator": by_operator,
            "daily_by_operator": daily_by_operator,
            "daily": daily,
            "data_gaps": data_gaps,
            "sessions_without_time": sessions_without_time[:100],
        },
    }
