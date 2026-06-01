"""
工程別設備別計画 API（ProcessMachinePlanView 向け）

production_summarys を期間で集計し、工程（切断・面取・SW・成型・溶接）
× 設備（*_machine 列）ごとに「計画 / 実績」を対比できるデータを返す。

- GET /production-summarys/process-machine-plan
    - summary: 工程 × 設備の集計（計画・実績・実計・差異・達成率・不良・廃棄・不良率・日別内訳）
    - processTotals: 工程ごとの合計
    - grandTotal: 全体合計
    - dates: 期間内の日付一覧（日別明細マトリクス用）
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/production-summarys", tags=["process-machine-plan"])

# 工程定義：(key, ラベル, 設備列, 計画列, 実績列, 実計列, 不良列, 廃棄列)
# ※ 列はすべてホワイトリスト（SQL へは固定識別子のみ展開）
PROCESS_DEFS: list[dict[str, str]] = [
    {
        "key": "cutting",
        "label": "切断",
        "machine": "cutting_machine",
        "plan": "cutting_plan",
        "actual": "cutting_actual",
        "actual_plan": "cutting_actual_plan",
        "defect": "cutting_defect",
        "scrap": "cutting_scrap",
    },
    {
        "key": "chamfering",
        "label": "面取",
        "machine": "chamfering_machine",
        "plan": "chamfering_plan",
        "actual": "chamfering_actual",
        "actual_plan": "chamfering_actual_plan",
        "defect": "chamfering_defect",
        "scrap": "chamfering_scrap",
    },
    {
        "key": "sw",
        "label": "SW",
        "machine": "sw_machine",
        "plan": "sw_plan",
        "actual": None,
        "actual_plan": None,
        "defect": None,
        "scrap": None,
    },
    {
        "key": "molding",
        "label": "成型",
        "machine": "molding_machine",
        "plan": "molding_plan",
        "actual": "molding_actual",
        "actual_plan": "molding_actual_plan",
        "defect": "molding_defect",
        "scrap": "molding_scrap",
    },
    {
        "key": "welding",
        "label": "溶接",
        "machine": "welding_machine",
        "plan": "welding_plan",
        "actual": "welding_actual",
        "actual_plan": "welding_actual_plan",
        "defect": "welding_defect",
        "scrap": "welding_scrap",
    },
]

PROCESS_DEF_BY_KEY = {d["key"]: d for d in PROCESS_DEFS}
DEFAULT_PROCESS_KEYS = [d["key"] for d in PROCESS_DEFS]

UNSET_MACHINE_LABEL = "(設備未設定)"


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


def _achievement_rate(plan: int, actual: int) -> Optional[float]:
    """達成率(%) = 実績 / 計画 * 100。計画 0 のときは None（実績ありは画面側で「-」表示）。"""
    if plan <= 0:
        return None
    return _round1(actual / plan * 100.0)


def _defect_rate(actual: int, defect: int, scrap: int) -> Optional[float]:
    """不良率(%) = (不良 + 廃棄) / (実績 + 不良 + 廃棄) * 100。"""
    base = actual + defect + scrap
    if base <= 0:
        return None
    return _round1((defect + scrap) / base * 100.0)


def _sum_expr(col: Optional[str]) -> str:
    """集計対象列。None のときは 0（SW など実績列未整備の工程）。"""
    if col:
        return f"SUM(COALESCE(`{col}`, 0))"
    return "0"


def _empty_acc() -> dict:
    return {"plan": 0, "actual": 0, "actual_plan": 0, "defect": 0, "scrap": 0}


def _build_metrics(acc: dict, days: int) -> dict:
    plan = acc["plan"]
    actual = acc["actual"]
    defect = acc["defect"]
    scrap = acc["scrap"]
    return {
        "plan": plan,
        "actual": actual,
        "actual_plan": acc["actual_plan"],
        "defect": defect,
        "scrap": scrap,
        "diff": actual - plan,
        "achievement_rate": _achievement_rate(plan, actual),
        "defect_rate": _defect_rate(actual, defect, scrap),
        "days": days,
    }


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
    """
    production_summarys を期間集計し、工程 × 設備の計画/実績対比を返す。
    """
    ps = _parse_iso_date("startDate", startDate)
    pe = _parse_iso_date("endDate", endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")

    # 対象工程の確定（ホワイトリスト）
    if processes and processes.strip():
        keys = [k.strip() for k in processes.split(",") if k.strip()]
        target_defs = [PROCESS_DEF_BY_KEY[k] for k in keys if k in PROCESS_DEF_BY_KEY]
        if not target_defs:
            raise HTTPException(
                status_code=400,
                detail=f"processes は次のいずれかです: {DEFAULT_PROCESS_KEYS}",
            )
    else:
        target_defs = list(PROCESS_DEFS)

    params: dict[str, object] = {"start": ps, "end": pe}
    product_clause = ""
    if productCd and productCd.strip():
        product_clause = " AND product_cd = :product_cd"
        params["product_cd"] = productCd.strip()

    # 工程ごとに (設備, 日付) で集計し UNION ALL（列名は固定ホワイトリストのみ）
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

    # 期間内の日付一覧（実データに存在する日のみ。空でも startDate/endDate は返す）
    date_set: set[str] = set()

    # process_key → machine → 集計 + 日別
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

        # 計画も実績も不良も廃棄もすべて 0 の (設備, 日) はスキップ（ノイズ除去）
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
        # 設備名でソート（未設定は末尾）
        machine_names = sorted(
            m_map.keys(),
            key=lambda x: (x == UNSET_MACHINE_LABEL, x),
        )
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
        "data": {
            "startDate": ps.isoformat(),
            "endDate": pe.isoformat(),
            "dates": dates,
            "processes": [{"key": d["key"], "label": d["label"]} for d in target_defs],
            "summary": summary,
            "processTotals": process_totals,
            "grandTotal": grand_total,
        }
    }


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
