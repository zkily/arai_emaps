"""
eams_db 只读通用查询（表发现 / 结构 / 安全 SELECT）
"""
from __future__ import annotations

import re
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SENSITIVE_COLUMNS = frozenset(
    {
        "password",
        "password_hash",
        "hashed_password",
        "secret",
        "secret_key",
        "jwt_secret",
        "token",
        "access_token",
        "refresh_token",
    }
)
FORBIDDEN_SQL_RE = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|create|truncate|grant|revoke|"
    r"replace|merge|call|execute|prepare|handler|lock|unlock|"
    r"load\s+data|into\s+outfile|into\s+dumpfile|load_file"
    r")\b",
    re.IGNORECASE,
)
BLOCKED_SQL_FRAGMENTS = (
    "information_schema",
    "performance_schema",
    "mysql.",
    "sys.",
    "@@",
    "char(",
    "sleep(",
    "benchmark(",
)


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    return value


def row_to_dict(columns: List[str], row: Tuple[Any, ...]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for col, val in zip(columns, row):
        if col.lower() in SENSITIVE_COLUMNS:
            out[col] = "[REDACTED]"
        else:
            out[col] = json_safe(val)
    return out


def clamp_limit(limit: Optional[int], default: int = 50) -> int:
    max_val = max(int(getattr(settings, "AI_QUERY_MAX_LIMIT", 100) or 100), 1)
    if limit is None:
        return min(default, max_val)
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return min(default, max_val)
    return max(1, min(n, max_val))


def validate_identifier(name: str, label: str = "identifier") -> str:
    n = (name or "").strip()
    if not n or not IDENT_RE.match(n):
        raise ValueError(f"invalid {label}: {name!r}")
    return n


async def _schema_name(db: AsyncSession) -> str:
    name = (settings.DB_NAME or "eams_db").strip()
    result = await db.execute(text("SELECT DATABASE()"))
    current = result.scalar()
    return str(current or name)


async def list_database_tables(
    db: AsyncSession,
    search: str = "",
    limit: int = 200,
) -> Dict[str, Any]:
    lim = min(clamp_limit(limit, default=200), 200)
    schema = await _schema_name(db)
    kw = (search or "").strip()
    params: Dict[str, Any] = {"schema": schema, "lim": lim}
    sql = """
        SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = :schema AND TABLE_TYPE = 'BASE TABLE'
    """
    if kw:
        sql += " AND (TABLE_NAME LIKE :pat OR TABLE_COMMENT LIKE :pat)"
        params["pat"] = f"%{kw}%"
    sql += " ORDER BY TABLE_NAME LIMIT :lim"
    rows = (await db.execute(text(sql), params)).all()
    items = [
        {
            "table_name": r[0],
            "approx_rows": int(r[1] or 0),
            "comment": (r[2] or "").strip() or None,
        }
        for r in rows
    ]
    return {"database": schema, "count": len(items), "tables": items}


async def describe_table(db: AsyncSession, table_name: str) -> Dict[str, Any]:
    table = validate_identifier(table_name, "table_name")
    schema = await _schema_name(db)
    exists = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
            """
        ),
        {"schema": schema, "table": table},
    )
    if int(exists.scalar() or 0) == 0:
        return {"error": f"table not found: {table}", "database": schema}

    cols = await db.execute(
        text(
            """
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
            ORDER BY ORDINAL_POSITION
            """
        ),
        {"schema": schema, "table": table},
    )
    columns = [
        {
            "name": r[0],
            "data_type": r[1],
            "column_type": r[2],
            "nullable": r[3] == "YES",
            "key": r[4] or None,
            "comment": (r[5] or "").strip() or None,
            "sensitive": r[0].lower() in SENSITIVE_COLUMNS,
        }
        for r in cols.all()
    ]
    return {"database": schema, "table_name": table, "column_count": len(columns), "columns": columns}


async def _text_columns(db: AsyncSession, schema: str, table: str) -> List[str]:
    rows = await db.execute(
        text(
            """
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
              AND DATA_TYPE IN ('char','varchar','text','tinytext','mediumtext','longtext')
            ORDER BY ORDINAL_POSITION
            """
        ),
        {"schema": schema, "table": table},
    )
    return [r[0] for r in rows.all() if r[0].lower() not in SENSITIVE_COLUMNS]


async def query_table(
    db: AsyncSession,
    table_name: str,
    keyword: str = "",
    filters: Optional[Dict[str, Any]] = None,
    order_by: str = "",
    limit: int = 50,
) -> Dict[str, Any]:
    table = validate_identifier(table_name, "table_name")
    schema = await _schema_name(db)
    lim = clamp_limit(limit, default=50)

    exists = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
            """
        ),
        {"schema": schema, "table": table},
    )
    if int(exists.scalar() or 0) == 0:
        return {"error": f"table not found: {table}", "database": schema}

    col_rows = await db.execute(
        text(
            """
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
            ORDER BY ORDINAL_POSITION
            """
        ),
        {"schema": schema, "table": table},
    )
    all_columns = [r[0] for r in col_rows.all()]
    if not all_columns:
        return {"error": "table has no columns", "table_name": table}

    select_cols = [
        f"`{c}`" for c in all_columns if c.lower() not in SENSITIVE_COLUMNS
    ]
    if not select_cols:
        return {"error": "no readable columns", "table_name": table}

    where_parts: List[str] = []
    params: Dict[str, Any] = {"lim": lim}

    filt = filters or {}
    if isinstance(filt, str):
        try:
            import json

            filt = json.loads(filt)
        except Exception:
            filt = {}
    if not isinstance(filt, dict):
        filt = {}

    col_set = {c.lower(): c for c in all_columns}
    for raw_key, raw_val in filt.items():
        key = validate_identifier(str(raw_key), "filter column")
        if key.lower() not in col_set:
            raise ValueError(f"unknown column in filters: {key}")
        if key.lower() in SENSITIVE_COLUMNS:
            continue
        pname = f"f_{key}"
        where_parts.append(f"`{col_set[key.lower()]}` = :{pname}")
        params[pname] = raw_val

    kw = (keyword or "").strip()
    if kw:
        text_cols = await _text_columns(db, schema, table)
        if text_cols:
            ors = []
            for i, col in enumerate(text_cols[:12]):
                pname = f"kw{i}"
                ors.append(f"`{col}` LIKE :{pname}")
                params[pname] = f"%{kw}%"
            where_parts.append("(" + " OR ".join(ors) + ")")

    sql = f"SELECT {', '.join(select_cols)} FROM `{table}`"
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    order_sql = ""
    if order_by:
        order_by = order_by.strip()
        if order_by.upper().endswith(" DESC"):
            base = order_by[:-5].strip()
            direction = "DESC"
        elif order_by.upper().endswith(" ASC"):
            base = order_by[:-4].strip()
            direction = "ASC"
        else:
            base = order_by
            direction = "ASC"
        ob = validate_identifier(base, "order_by")
        if ob.lower() not in col_set:
            raise ValueError(f"unknown order_by column: {ob}")
        order_sql = f" ORDER BY `{col_set[ob.lower()]}` {direction}"
    sql += order_sql + " LIMIT :lim"

    result = await db.execute(text(sql), params)
    keys = list(result.keys())
    items = [row_to_dict(keys, tuple(row)) for row in result.fetchall()]
    return {
        "database": schema,
        "table_name": table,
        "returned": len(items),
        "limit": lim,
        "items": items,
    }


def validate_read_sql(sql: str) -> str:
    raw = (sql or "").strip()
    if not raw:
        raise ValueError("sql is empty")
    if ";" in raw.rstrip(";"):
        raise ValueError("only a single SQL statement is allowed")
    raw = raw.rstrip(";").strip()
    lowered = raw.lower()
    if FORBIDDEN_SQL_RE.search(lowered):
        raise ValueError("only SELECT queries are allowed")
    for frag in BLOCKED_SQL_FRAGMENTS:
        if frag in lowered:
            raise ValueError(f"forbidden SQL fragment: {frag}")
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("query must start with SELECT or WITH")
    if "limit" not in lowered:
        raw = f"{raw} LIMIT {clamp_limit(None, default=50)}"
    return raw


async def execute_read_sql(db: AsyncSession, sql: str) -> Dict[str, Any]:
    safe_sql = validate_read_sql(sql)
    schema = await _schema_name(db)
    result = await db.execute(text(safe_sql))
    keys = list(result.keys())
    rows = result.fetchall()
    items = [row_to_dict(keys, tuple(row)) for row in rows]
    return {
        "database": schema,
        "returned": len(items),
        "columns": keys,
        "items": items,
    }
