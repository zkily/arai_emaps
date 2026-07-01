"""
工程別設備別計画 API（ProcessMachinePlanView 向け）

production_summarys を期間で集計し、工程（切断・面取・SW・成型・溶接）
× 設備（*_machine 列）ごとに「計画 / 実績」を対比できるデータを返す。

- GET /production-summarys/process-machine-plan
- POST /production-summarys/process-machine-plan/simulate
- GET/POST/PUT/DELETE .../process-machine-plan/scenarios
"""
import json
import logging
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_aps_operation
from app.modules.database.process_machine_plan_adjust import (
    apply_adjust_rules,
    build_diff_plan_data,
)
from app.modules.database.process_machine_plan_common import (
    DEFAULT_PROCESS_KEYS,
    PROCESS_DEFS,
    PROCESS_DEF_BY_KEY,
    UNSET_MACHINE_LABEL,
    build_metrics as _build_metrics,
    achievement_rate as _achievement_rate,
    defect_rate as _defect_rate,
    empty_acc as _empty_acc,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/production-summarys", tags=["process-machine-plan"])


def _parse_iso_date(label: str, value: str) -> date:
    s = (value or "").strip()[:10]
    if len(s) != 10 or s[4] != "-" or s[7] != "-":
        raise HTTPException(status_code=400, detail=f"{label} は YYYY-MM-DD 形式で指定してください")
    try:
        y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
        return date(y, m, d)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{label} が不正な日付です")


def _to_int(v) -> int:
    try:
        if v is None:
            return 0
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return 0


def _round1(v: float) -> float:
    return round(v, 1)


def _sum_expr(col: Optional[str]) -> str:
    """集計対象列。None のときは 0（SW など実績列未整備の工程）。"""
    if col:
        return f"SUM(COALESCE(`{col}`, 0))"
    return "0"


def _resolve_target_defs(processes: Optional[str]) -> list[dict]:
    if processes and processes.strip():
        keys = [k.strip() for k in processes.split(",") if k.strip()]
        target_defs = [PROCESS_DEF_BY_KEY[k] for k in keys if k in PROCESS_DEF_BY_KEY]
        if not target_defs:
            raise HTTPException(
                status_code=400,
                detail=f"processes は次のいずれかです: {DEFAULT_PROCESS_KEYS}",
            )
        return target_defs
    return list(PROCESS_DEFS)


async def _fetch_process_machine_plan_data(
    db: AsyncSession,
    ps: date,
    pe: date,
    target_defs: list[dict],
    product_cd: Optional[str] = None,
) -> dict:
    params: dict[str, object] = {"start": ps, "end": pe}
    product_clause = ""
    if product_cd and product_cd.strip():
        product_clause = " AND product_cd = :product_cd"
        params["product_cd"] = product_cd.strip()

    union_parts: list[str] = []
    for d in target_defs:
        union_parts.append(
            f"""
            SELECT
                '{d['key']}' AS process_key,
                COALESCE(NULLIF(TRIM(`{d['machine']}`), ''), '__UNSET__') AS machine,
                `date` AS d,
                {_sum_expr(d['plan'])} AS plan_qty,
                {_sum_expr(d['actual'])} AS actual_qty,
                {_sum_expr(d['actual_plan'])} AS actual_plan_qty,
                {_sum_expr(d['defect'])} AS defect_qty,
                {_sum_expr(d['scrap'])} AS scrap_qty
            FROM production_summarys
            WHERE `date` >= :start AND `date` <= :end{product_clause}
            GROUP BY machine, `date`
            """
        )
    sql = text(" UNION ALL ".join(union_parts))
    result = await db.execute(sql, params)
    rows = result.mappings().all()

    date_set: set[str] = set()
    bucket: dict[str, dict[str, dict]] = {d["key"]: {} for d in target_defs}

    for r in rows:
        pk = str(r["process_key"])
        raw_machine = str(r["machine"])
        machine = UNSET_MACHINE_LABEL if raw_machine == "__UNSET__" else raw_machine
        d_val = r["d"]
        d_str = d_val.isoformat()[:10] if hasattr(d_val, "isoformat") else str(d_val)[:10]
        date_set.add(d_str)

        plan = _to_int(r["plan_qty"])
        actual = _to_int(r["actual_qty"])
        actual_plan = _to_int(r["actual_plan_qty"])
        defect = _to_int(r["defect_qty"])
        scrap = _to_int(r["scrap_qty"])

        if plan == 0 and actual == 0 and actual_plan == 0 and defect == 0 and scrap == 0:
            continue

        m_map = bucket[pk]
        if machine not in m_map:
            m_map[machine] = {"acc": _empty_acc(), "daily": {}, "days": set()}
        node = m_map[machine]
        acc = node["acc"]
        acc["plan"] += plan
        acc["actual"] += actual
        acc["actual_plan"] += actual_plan
        acc["defect"] += defect
        acc["scrap"] += scrap
        node["days"].add(d_str)
        node["daily"][d_str] = {"plan": plan, "actual": actual, "diff": actual - plan}

    dates = sorted(date_set)
    summary: list[dict] = []
    process_totals: dict[str, dict] = {}
    grand_acc = _empty_acc()
    grand_days: set[str] = set()

    for d in target_defs:
        pk = d["key"]
        m_map = bucket.get(pk, {})
        proc_acc = _empty_acc()
        proc_days: set[str] = set()
        machine_names = sorted(m_map.keys(), key=lambda x: (x == UNSET_MACHINE_LABEL, x))
        for machine in machine_names:
            node = m_map[machine]
            acc = node["acc"]
            summary.append(
                {
                    "process_key": pk,
                    "process_label": d["label"],
                    "machine": machine,
                    **_build_metrics(acc, len(node["days"])),
                    "daily": node["daily"],
                }
            )
            for k in proc_acc:
                proc_acc[k] += acc[k]
            proc_days |= node["days"]

        process_totals[pk] = {
            "process_key": pk,
            "process_label": d["label"],
            **_build_metrics(proc_acc, len(proc_days)),
        }
        for k in grand_acc:
            grand_acc[k] += proc_acc[k]
        grand_days |= proc_days

    grand_total = _build_metrics(grand_acc, len(grand_days))
    return {
        "startDate": ps.isoformat(),
        "endDate": pe.isoformat(),
        "dates": dates,
        "processes": [{"key": d["key"], "label": d["label"]} for d in target_defs],
        "summary": summary,
        "processTotals": process_totals,
        "grandTotal": grand_total,
    }


class AdjustRuleTargetBody(BaseModel):
    machine: str
    weight: float = 1.0


class AdjustRuleBody(BaseModel):
    id: str
    type: str = Field(..., description="adjust | allocate_unset")
    process_key: str
    enabled: bool = True
    machine: Optional[str] = None
    mode: Optional[str] = Field(None, description="percent | delta（adjust 時）")
    value: Optional[float] = None
    targets: Optional[list[AdjustRuleTargetBody]] = None


class SimulatePlanBody(BaseModel):
    startDate: str
    endDate: str
    processes: Optional[str] = None
    productCd: Optional[str] = None
    rules: list[AdjustRuleBody] = Field(default_factory=list)


class ScenarioSaveBody(BaseModel):
    name: str
    startDate: str
    endDate: str
    processes: Optional[str] = None
    rules: list[AdjustRuleBody] = Field(default_factory=list)


class ScenarioUpdateBody(BaseModel):
    name: Optional[str] = None
    rules: Optional[list[AdjustRuleBody]] = None


def _rules_to_dict(rules: list[AdjustRuleBody]) -> list[dict[str, Any]]:
    return [r.model_dump() for r in rules]


@router.get("/process-machine-plan")
async def get_process_machine_plan(
    startDate: str = Query(..., description="開始日 YYYY-MM-DD"),
    endDate: str = Query(..., description="終了日 YYYY-MM-DD"),
    processes: Optional[str] = Query(
        None, description="対象工程キー（カンマ区切り）。未指定なら全工程"
    ),
    productCd: Optional[str] = Query(None, description="製品CDで絞り込み（任意）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """production_summarys を期間集計し、工程 × 設備の計画/実績対比を返す。"""
    ps = _parse_iso_date("startDate", startDate)
    pe = _parse_iso_date("endDate", endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")
    target_defs = _resolve_target_defs(processes)
    data = await _fetch_process_machine_plan_data(db, ps, pe, target_defs, productCd)
    return {"data": data}


@router.post("/process-machine-plan/simulate")
async def simulate_process_machine_plan(
    body: SimulatePlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """調整ルールを適用した計画シミュレーション（DB へは書き込まない）。"""
    ps = _parse_iso_date("startDate", body.startDate)
    pe = _parse_iso_date("endDate", body.endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")
    target_defs = _resolve_target_defs(body.processes)
    base = await _fetch_process_machine_plan_data(db, ps, pe, target_defs, body.productCd)
    rules = _rules_to_dict(body.rules)
    adjusted = apply_adjust_rules(base, rules)
    diff = build_diff_plan_data(base, adjusted)
    return {
        "data": {
            "base": base,
            "adjusted": adjusted,
            "diff": diff,
            "rules": rules,
        }
    }


@router.get("/process-machine-plan/scenarios")
async def list_process_machine_plan_scenarios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    res = await db.execute(
        text(
            """
            SELECT id, name, period_start, period_end, status, created_by, created_at, updated_at
            FROM process_machine_plan_scenarios
            WHERE status <> 'archived'
            ORDER BY updated_at DESC
            LIMIT 100
            """
        )
    )
    items = []
    for row in res.mappings().all():
        items.append(
            {
                "id": row["id"],
                "name": row["name"],
                "startDate": row["period_start"].isoformat() if row["period_start"] else None,
                "endDate": row["period_end"].isoformat() if row["period_end"] else None,
                "status": row["status"],
                "createdBy": row["created_by"],
                "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
        )
    return {"code": 200, "data": {"items": items}}


@router.post("/process-machine-plan/scenarios")
async def create_process_machine_plan_scenario(
    body: ScenarioSaveBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    ps = _parse_iso_date("startDate", body.startDate)
    pe = _parse_iso_date("endDate", body.endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")

    target_defs = _resolve_target_defs(body.processes)
    base = await _fetch_process_machine_plan_data(db, ps, pe, target_defs)
    rules = _rules_to_dict(body.rules)
    adjusted = apply_adjust_rules(base, rules)
    payload = {
        "processes": body.processes,
        "rules": rules,
        "last_simulation": {
            "base": base,
            "adjusted": adjusted,
            "diff": build_diff_plan_data(base, adjusted),
        },
    }

    ins = text(
        """
        INSERT INTO process_machine_plan_scenarios (name, period_start, period_end, status, created_by)
        VALUES (:name, :ps, :pe, 'draft', :by)
        """
    )
    res = await db.execute(
        ins,
        {
            "name": body.name.strip(),
            "ps": ps,
            "pe": pe,
            "by": getattr(current_user, "username", None) or str(current_user.id),
        },
    )
    scenario_id = res.lastrowid
    await db.execute(
        text(
            "INSERT INTO process_machine_plan_scenario_payload (scenario_id, payload) VALUES (:id, :payload)"
        ),
        {"id": scenario_id, "payload": json.dumps(payload, ensure_ascii=False, default=str)},
    )
    await db.commit()
    return {"code": 200, "data": {"id": scenario_id, "simulation": payload["last_simulation"]}}


@router.get("/process-machine-plan/scenarios/{scenario_id}")
async def get_process_machine_plan_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    meta = (
        await db.execute(
            text("SELECT * FROM process_machine_plan_scenarios WHERE id = :id"),
            {"id": scenario_id},
        )
    ).mappings().first()
    if not meta:
        raise HTTPException(status_code=404, detail="方案が見つかりません")
    payload_row = (
        await db.execute(
            text("SELECT payload FROM process_machine_plan_scenario_payload WHERE scenario_id = :id"),
            {"id": scenario_id},
        )
    ).mappings().first()
    payload = payload_row["payload"] if payload_row else {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return {
        "code": 200,
        "data": {
            "id": meta["id"],
            "name": meta["name"],
            "startDate": meta["period_start"].isoformat(),
            "endDate": meta["period_end"].isoformat(),
            "status": meta["status"],
            "processes": (payload or {}).get("processes"),
            "rules": (payload or {}).get("rules") or [],
            "lastSimulation": (payload or {}).get("last_simulation"),
        },
    }


@router.put("/process-machine-plan/scenarios/{scenario_id}")
async def update_process_machine_plan_scenario(
    scenario_id: int,
    body: ScenarioUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    meta = (
        await db.execute(
            text("SELECT * FROM process_machine_plan_scenarios WHERE id = :id"),
            {"id": scenario_id},
        )
    ).mappings().first()
    if not meta:
        raise HTTPException(status_code=404, detail="方案が見つかりません")

    payload_row = (
        await db.execute(
            text("SELECT payload FROM process_machine_plan_scenario_payload WHERE scenario_id = :id"),
            {"id": scenario_id},
        )
    ).mappings().first()
    payload = payload_row["payload"] if payload_row else {}
    if isinstance(payload, str):
        payload = json.loads(payload)

    if body.name and body.name.strip():
        await db.execute(
            text("UPDATE process_machine_plan_scenarios SET name = :name WHERE id = :id"),
            {"name": body.name.strip(), "id": scenario_id},
        )

    if body.rules is not None:
        ps = meta["period_start"]
        pe = meta["period_end"]
        processes = (payload or {}).get("processes")
        target_defs = _resolve_target_defs(processes)
        base = await _fetch_process_machine_plan_data(db, ps, pe, target_defs)
        rules = _rules_to_dict(body.rules)
        adjusted = apply_adjust_rules(base, rules)
        payload = {
            "processes": processes,
            "rules": rules,
            "last_simulation": {
                "base": base,
                "adjusted": adjusted,
                "diff": build_diff_plan_data(base, adjusted),
            },
        }
        await db.execute(
            text("UPDATE process_machine_plan_scenario_payload SET payload = :payload WHERE scenario_id = :id"),
            {"id": scenario_id, "payload": json.dumps(payload, ensure_ascii=False, default=str)},
        )

    await db.commit()
    return {"code": 200, "data": {"id": scenario_id}}


@router.delete("/process-machine-plan/scenarios/{scenario_id}")
async def delete_process_machine_plan_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    res = await db.execute(
        text("DELETE FROM process_machine_plan_scenarios WHERE id = :id"),
        {"id": scenario_id},
    )
    await db.commit()
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="方案が見つかりません")
    return {"code": 200, "message": "削除しました"}


@router.get("/process-machine-plan/products")
async def get_process_machine_plan_products(
    startDate: str = Query(..., description="開始日 YYYY-MM-DD"),
    endDate: str = Query(..., description="終了日 YYYY-MM-DD"),
    process: str = Query(..., description="工程キー（単一）"),
    machine: str = Query(..., description="設備名（未設定は『(設備未設定)』）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定工程 × 指定設備の製品別 計画/実績明細（ドリルダウン）。
    """
    ps = _parse_iso_date("startDate", startDate)
    pe = _parse_iso_date("endDate", endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")

    d = PROCESS_DEF_BY_KEY.get(process.strip())
    if not d:
        raise HTTPException(
            status_code=400, detail=f"process は次のいずれかです: {DEFAULT_PROCESS_KEYS}"
        )

    params: dict[str, object] = {"start": ps, "end": pe}
    machine_in = (machine or "").strip()
    if machine_in == UNSET_MACHINE_LABEL or machine_in == "":
        machine_clause = f"(`{d['machine']}` IS NULL OR TRIM(`{d['machine']}`) = '')"
    else:
        machine_clause = f"TRIM(`{d['machine']}`) = :machine"
        params["machine"] = machine_in

    sql = text(
        f"""
        SELECT
            product_cd,
            MAX(product_name) AS product_name,
            {_sum_expr(d['plan'])} AS plan_qty,
            {_sum_expr(d['actual'])} AS actual_qty,
            {_sum_expr(d['actual_plan'])} AS actual_plan_qty,
            {_sum_expr(d['defect'])} AS defect_qty,
            {_sum_expr(d['scrap'])} AS scrap_qty
        FROM production_summarys
        WHERE `date` >= :start AND `date` <= :end AND {machine_clause}
        GROUP BY product_cd
        """
    )
    result = await db.execute(sql, params)

    products: list[dict] = []
    total_acc = _empty_acc()
    for r in result.mappings().all():
        plan = _to_int(r["plan_qty"])
        actual = _to_int(r["actual_qty"])
        actual_plan = _to_int(r["actual_plan_qty"])
        defect = _to_int(r["defect_qty"])
        scrap = _to_int(r["scrap_qty"])
        if plan == 0 and actual == 0 and actual_plan == 0 and defect == 0 and scrap == 0:
            continue
        acc = {
            "plan": plan,
            "actual": actual,
            "actual_plan": actual_plan,
            "defect": defect,
            "scrap": scrap,
        }
        products.append(
            {
                "product_cd": r["product_cd"],
                "product_name": r["product_name"],
                **_build_metrics(acc, 0),
            }
        )
        for k in total_acc:
            total_acc[k] += acc[k]

    # 実績の多い順 → 計画の多い順
    products.sort(key=lambda x: (-x["actual"], -x["plan"], str(x["product_cd"])))

    return {
        "data": {
            "startDate": ps.isoformat(),
            "endDate": pe.isoformat(),
            "process_key": d["key"],
            "process_label": d["label"],
            "machine": machine_in or UNSET_MACHINE_LABEL,
            "products": products,
            "total": _build_metrics(total_acc, 0),
        }
    }
