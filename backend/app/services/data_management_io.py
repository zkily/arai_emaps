"""
データ管理：マスター CSV のエクスポート / インポート（settings API 用）。
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import date
from decimal import Decimal
from typing import Any, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.master.models import Customer, Product, Supplier
from app.modules.erp.inventory_models import Warehouse

logger = logging.getLogger(__name__)

# テンプレート列（download_import_template と一致）
HEADERS: dict[str, list[str]] = {
    "items": ["品目コード", "品目名", "カテゴリ", "単位", "単価", "在庫数"],
    "customers": ["取引先コード", "取引先名", "住所", "電話番号", "担当者名"],
    "suppliers": ["仕入先コード", "仕入先名", "住所", "電話番号", "担当者名"],
    "warehouses": ["倉庫コード", "倉庫名", "住所", "管理者"],
    "users": ["ユーザー名", "氏名", "メールアドレス", "部門", "ロール"],
}


def _dec(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return format(v, "f").rstrip("0").rstrip(".") or "0"
    return str(v)


async def build_master_export_csv(
    db: AsyncSession,
    master_type: str,
    encoding_key: str,
) -> Tuple[bytes, int]:
    """マスターを CSV バイト列に変換。戻り値: (body, row_count)"""
    if master_type not in HEADERS:
        raise ValueError(f"無効なマスター種類: {master_type}")

    headers = HEADERS[master_type]
    rows: List[List[str]] = []

    if master_type == "items":
        res = await db.execute(select(Product).order_by(Product.product_cd))
        for p in res.scalars().all():
            rows.append(
                [
                    p.product_cd or "",
                    p.product_name or "",
                    p.category or "",
                    "",
                    _dec(p.unit_price),
                    "0",
                ]
            )
    elif master_type == "customers":
        res = await db.execute(select(Customer).order_by(Customer.customer_cd))
        for c in res.scalars().all():
            rows.append([c.customer_cd or "", c.customer_name or "", c.address or "", c.phone or "", ""])
    elif master_type == "suppliers":
        res = await db.execute(select(Supplier).order_by(Supplier.supplier_cd))
        for s in res.scalars().all():
            rows.append(
                [
                    s.supplier_cd or "",
                    s.supplier_name or "",
                    (s.address1 or "") + (s.address2 or ""),
                    s.phone or "",
                    s.contact_person or "",
                ]
            )
    elif master_type == "warehouses":
        res = await db.execute(select(Warehouse).order_by(Warehouse.warehouse_code))
        for w in res.scalars().all():
            rows.append([w.warehouse_code or "", w.warehouse_name or "", w.address or "", w.manager or ""])
    elif master_type == "users":
        res = await db.execute(select(User).order_by(User.username))
        for u in res.scalars().all():
            rows.append(
                [
                    u.username or "",
                    u.full_name or "",
                    u.email or "",
                    str(u.department_id) if u.department_id is not None else "",
                    u.role or "",
                ]
            )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    text = buf.getvalue()
    enc = (encoding_key or "utf8").lower()
    if enc in ("sjis", "shift_jis", "shift-jis"):
        body = text.encode("cp932", errors="replace")
    else:
        body = text.encode("utf-8-sig")
    return body, len(rows)


async def build_master_export_xlsx(
    db: AsyncSession,
    master_type: str,
) -> Tuple[bytes, int]:
    from openpyxl import Workbook

    body_csv, _n = await build_master_export_csv(db, master_type, "utf8")
    text = body_csv.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    lines = list(reader)
    wb = Workbook()
    ws = wb.active
    ws.title = master_type[:31]
    for line in lines:
        ws.append(line)
    out = io.BytesIO()
    wb.save(out)
    row_count = max(0, len(lines) - 1)
    return out.getvalue(), row_count


def _decode_upload(content: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


async def import_master_csv(
    db: AsyncSession,
    master_type: str,
    content: bytes,
    update_existing: bool,
    skip_errors: bool,
) -> Tuple[int, int, List[str]]:
    """
    CSV を取り込み。戻り値: (成功件数, 失敗件数, エラーメッセージ一覧・最大20件)
    """
    if master_type == "users":
        raise ValueError("ユーザーマスターの CSV インポートは未対応です（セキュリティのため）")

    if master_type not in HEADERS:
        raise ValueError(f"無効なマスター種類: {master_type}")

    text = _decode_upload(content)
    reader = csv.DictReader(io.StringIO(text))
    expected = HEADERS[master_type]
    if reader.fieldnames is None:
        raise ValueError("CSV にヘッダー行がありません")
    raw_fields = [((h or "").strip()) for h in reader.fieldnames]
    if expected[0] not in raw_fields:
        raise ValueError(f"CSV の列がテンプレートと一致しません。先頭列に「{expected[0]}」が必要です。")
    success = 0
    errors = 0
    err_msgs: List[str] = []

    for i, row in enumerate(reader, start=2):
        try:
            if not any((str(v).strip() if v is not None else "") for v in (row or {}).values()):
                continue

            def g(name: str) -> str:
                v = row.get(name)
                if v is None:
                    for k in row:
                        if k and k.strip() == name:
                            return (row.get(k) or "").strip()
                return (v or "").strip()

            if master_type == "customers":
                cd = g("取引先コード")
                if not cd:
                    raise ValueError("取引先コードが空です")
                res = await db.execute(select(Customer).where(Customer.customer_cd == cd))
                ex = res.scalar_one_or_none()
                if ex:
                    if not update_existing:
                        raise ValueError(f"既に存在: {cd}")
                    ex.customer_name = g("取引先名") or ex.customer_name
                    ex.address = g("住所") or ex.address
                    ex.phone = g("電話番号") or ex.phone
                else:
                    db.add(
                        Customer(
                            customer_cd=cd,
                            customer_name=g("取引先名") or cd,
                            address=g("住所") or None,
                            phone=g("電話番号") or None,
                        )
                    )
            elif master_type == "suppliers":
                cd = g("仕入先コード")
                if not cd:
                    raise ValueError("仕入先コードが空です")
                res = await db.execute(select(Supplier).where(Supplier.supplier_cd == cd))
                ex = res.scalar_one_or_none()
                if ex:
                    if not update_existing:
                        raise ValueError(f"既に存在: {cd}")
                    ex.supplier_name = g("仕入先名") or ex.supplier_name
                    ex.address1 = g("住所") or ex.address1
                    ex.phone = g("電話番号") or ex.phone
                    ex.contact_person = g("担当者名") or ex.contact_person
                else:
                    db.add(
                        Supplier(
                            supplier_cd=cd,
                            supplier_name=g("仕入先名") or cd,
                            address1=g("住所") or None,
                            phone=g("電話番号") or None,
                            contact_person=g("担当者名") or None,
                        )
                    )
            elif master_type == "warehouses":
                cd = g("倉庫コード")
                if not cd:
                    raise ValueError("倉庫コードが空です")
                res = await db.execute(select(Warehouse).where(Warehouse.warehouse_code == cd))
                ex = res.scalar_one_or_none()
                if ex:
                    if not update_existing:
                        raise ValueError(f"既に存在: {cd}")
                    ex.warehouse_name = g("倉庫名") or ex.warehouse_name
                    ex.address = g("住所") or ex.address
                    ex.manager = g("管理者") or ex.manager
                else:
                    db.add(
                        Warehouse(
                            warehouse_code=cd,
                            warehouse_name=g("倉庫名") or cd,
                            address=g("住所") or None,
                            manager=g("管理者") or None,
                        )
                    )
            elif master_type == "items":
                cd = g("品目コード")
                if not cd:
                    raise ValueError("品目コードが空です")
                res = await db.execute(select(Product).where(Product.product_cd == cd))
                ex = res.scalar_one_or_none()
                price_raw = g("単価")
                unit_price: Optional[Decimal] = None
                if price_raw:
                    try:
                        unit_price = Decimal(price_raw.replace(",", ""))
                    except Exception:
                        unit_price = None
                if ex:
                    if not update_existing:
                        raise ValueError(f"既に存在: {cd}")
                    ex.product_name = g("品目名") or ex.product_name
                    ex.category = g("カテゴリ") or ex.category
                    if unit_price is not None:
                        ex.unit_price = unit_price
                else:
                    db.add(
                        Product(
                            product_cd=cd,
                            product_name=g("品目名") or cd,
                            category=g("カテゴリ") or None,
                            unit_price=unit_price,
                            status="active",
                        )
                    )
            success += 1
            await db.flush()
        except Exception as e:
            errors += 1
            msg = f"{i}行目: {e}"
            if len(err_msgs) < 20:
                err_msgs.append(msg)
            logger.warning("import row %s: %s", i, e)
            if not skip_errors:
                raise ValueError(msg) from e

    return success, errors, err_msgs
