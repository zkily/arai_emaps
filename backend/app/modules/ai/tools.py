"""
AI 助手：只读数据库查询工具（白名单）
"""
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.query_executor import (
    describe_table,
    execute_read_sql,
    list_database_tables,
    query_table,
)
from app.modules.aps.models import ProductionSchedule
from app.modules.master.models import Customer, PartMaster, Supplier
from app.modules.material.models import MaterialStock

MAX_LIMIT = 50

_GENERIC_DB_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_database_tables",
            "description": "列出 eams_db 中所有业务表名（可先调用以确定要查哪张表）",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "按表名或注释模糊筛选"},
                    "limit": {"type": "integer", "description": "返回条数，默认 200，最大 200"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "查看指定表的字段名、类型与注释",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "表名，如 customers、orders"},
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_table",
            "description": "只读查询指定表的数据（支持关键词模糊匹配文本列、等值 filters、排序）",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "表名"},
                    "keyword": {"type": "string", "description": "在文本列中模糊搜索"},
                    "filters": {
                        "type": "object",
                        "description": "等值条件，如 {\"status\": 1, \"customer_cd\": \"C001\"}",
                        "additionalProperties": True,
                    },
                    "order_by": {"type": "string", "description": "排序列名，可加 ASC/DESC"},
                    "limit": {"type": "integer", "description": "返回条数，默认 50，最大 100"},
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_read_sql",
            "description": "执行只读 SELECT（可 JOIN 多表）。必须包含 LIMIT，禁止写操作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "单条 SELECT 语句，例如 SELECT ... FROM a JOIN b ... LIMIT 50"},
                },
                "required": ["sql"],
            },
        },
    },
]

_TOOL_DEFINITIONS_LEGACY: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_customers",
            "description": "按关键词搜索客户主数据（客户代码或名称模糊匹配）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词，空字符串则返回前几条"},
                    "limit": {"type": "integer", "description": "返回条数上限，默认 10，最大 50"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_parts",
            "description": "按关键词搜索部品主数据（部品代码或名称模糊匹配）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回条数上限，默认 10，最大 50"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_suppliers",
            "description": "按关键词搜索供应商主数据（供应商代码或名称模糊匹配）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回条数上限，默认 10，最大 50"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_production_schedule_summary",
            "description": "查询指定日期范围内的生产计划摘要（按 start_date 筛选）",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "date_to": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                    "limit": {"type": "integer", "description": "返回条数上限，默认 20，最大 50"},
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_material_stock_summary",
            "description": "查询指定材料代码的最近库存记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "材料代码 material_cd"},
                    "limit": {"type": "integer", "description": "返回最近记录条数，默认 5，最大 20"},
                },
                "required": ["material_code"],
            },
        },
    },
]

TOOL_DEFINITIONS: List[Dict[str, Any]] = _GENERIC_DB_TOOLS + _TOOL_DEFINITIONS_LEGACY


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _clamp_limit(limit: Optional[int], default: int, max_val: int = MAX_LIMIT) -> int:
    if limit is None:
        return default
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, max_val))


def _parse_date(value: str) -> date:
    s = (value or "").strip()[:10]
    return date.fromisoformat(s)


async def search_customers(db: AsyncSession, keyword: str = "", limit: int = 10) -> Dict[str, Any]:
    lim = _clamp_limit(limit, 10)
    kw = (keyword or "").strip()
    stmt = select(Customer)
    if kw:
        pattern = f"%{kw}%"
        stmt = stmt.where(
            or_(Customer.customer_cd.like(pattern), Customer.customer_name.like(pattern))
        )
    stmt = stmt.order_by(Customer.customer_cd).limit(lim)
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "customer_cd": r.customer_cd,
            "customer_name": r.customer_name,
            "customer_type": r.customer_type,
            "status": r.status,
            "phone": r.phone,
        }
        for r in rows
    ]
    return {"count": len(items), "items": items}


async def search_parts(db: AsyncSession, keyword: str = "", limit: int = 10) -> Dict[str, Any]:
    lim = _clamp_limit(limit, 10)
    kw = (keyword or "").strip()
    stmt = select(PartMaster)
    if kw:
        pattern = f"%{kw}%"
        stmt = stmt.where(or_(PartMaster.part_cd.like(pattern), PartMaster.part_name.like(pattern)))
    stmt = stmt.order_by(PartMaster.part_cd).limit(lim)
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "part_cd": r.part_cd,
            "part_name": r.part_name,
            "category": r.category,
            "supplier_cd": r.supplier_cd,
            "status": r.status,
            "unit_price": _json_safe(r.unit_price),
        }
        for r in rows
    ]
    return {"count": len(items), "items": items}


async def search_suppliers(db: AsyncSession, keyword: str = "", limit: int = 10) -> Dict[str, Any]:
    lim = _clamp_limit(limit, 10)
    kw = (keyword or "").strip()
    stmt = select(Supplier)
    if kw:
        pattern = f"%{kw}%"
        stmt = stmt.where(
            or_(Supplier.supplier_cd.like(pattern), Supplier.supplier_name.like(pattern))
        )
    stmt = stmt.order_by(Supplier.supplier_cd).limit(lim)
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "supplier_cd": r.supplier_cd,
            "supplier_name": r.supplier_name,
            "contact_person": r.contact_person,
            "phone": r.phone,
        }
        for r in rows
    ]
    return {"count": len(items), "items": items}


async def get_production_schedule_summary(
    db: AsyncSession,
    date_from: str,
    date_to: str,
    limit: int = 20,
) -> Dict[str, Any]:
    lim = _clamp_limit(limit, 20)
    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)
    if d_from > d_to:
        d_from, d_to = d_to, d_from

    stmt = (
        select(ProductionSchedule)
        .where(
            ProductionSchedule.start_date.isnot(None),
            ProductionSchedule.start_date >= d_from,
            ProductionSchedule.start_date <= d_to,
        )
        .order_by(ProductionSchedule.start_date, ProductionSchedule.id)
        .limit(lim)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "id": r.id,
            "item_name": r.item_name,
            "product_cd": r.product_cd,
            "line_id": r.line_id,
            "lot_qty": r.lot_qty,
            "planned_output_qty": r.planned_output_qty,
            "start_date": _json_safe(r.start_date),
            "end_date": _json_safe(r.end_date),
            "due_date": _json_safe(r.due_date),
            "status": r.status,
            "completion_rate": _json_safe(r.completion_rate),
        }
        for r in rows
    ]

    count_stmt = select(func.count()).select_from(ProductionSchedule).where(
        ProductionSchedule.start_date.isnot(None),
        ProductionSchedule.start_date >= d_from,
        ProductionSchedule.start_date <= d_to,
    )
    total = (await db.execute(count_stmt)).scalar() or 0
    return {
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "total_in_range": int(total),
        "returned": len(items),
        "items": items,
    }


async def get_material_stock_summary(
    db: AsyncSession,
    material_code: str,
    limit: int = 5,
) -> Dict[str, Any]:
    code = (material_code or "").strip()
    if not code:
        return {"error": "material_code is required", "items": []}
    lim = _clamp_limit(limit, 5, max_val=20)
    stmt = (
        select(MaterialStock)
        .where(MaterialStock.material_cd == code)
        .order_by(MaterialStock.date.desc())
        .limit(lim)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "material_cd": r.material_cd,
            "material_name": r.material_name,
            "date": _json_safe(r.date),
            "current_stock": r.current_stock,
            "safety_stock": r.safety_stock,
            "supplier_name": r.supplier_name,
            "unit": r.unit,
        }
        for r in rows
    ]
    return {"material_code": code, "count": len(items), "items": items}


_TOOL_HANDLERS = {
    "list_database_tables": list_database_tables,
    "describe_table": describe_table,
    "query_table": query_table,
    "execute_read_sql": execute_read_sql,
    "search_customers": search_customers,
    "search_parts": search_parts,
    "search_suppliers": search_suppliers,
    "get_production_schedule_summary": get_production_schedule_summary,
    "get_material_stock_summary": get_material_stock_summary,
}


def get_tool_definitions() -> List[Dict[str, Any]]:
    return TOOL_DEFINITIONS


def _parse_tool_arguments(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


async def execute_tool(db: AsyncSession, tool_name: str, arguments: Any) -> Dict[str, Any]:
    handler = _TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"unknown tool: {tool_name}"}
    args = _parse_tool_arguments(arguments)
    try:
        return await handler(db, **args)
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


async def execute_tool_call(db: AsyncSession, tool_call: Dict[str, Any]) -> Dict[str, Any]:
    fn = tool_call.get("function") or {}
    name = fn.get("name") or tool_call.get("name") or ""
    args = fn.get("arguments") or tool_call.get("arguments")
    return await execute_tool(db, name, args)
