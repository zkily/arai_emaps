"""
出荷管理表 API
- GET /welding/products: 対象製品一覧（product_name に 'SD' を含み、status=active、product_type=量産品）
- POST /welding/data: 出荷データ（shipping_items から取得、日付・納入先・製品別に明細保持）
- POST /welding/export: 印刷用レポート HTML（出荷管理表）
"""
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_sales_operation
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Destination, Product

router = APIRouter()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    if not DATE_RE.match(s.strip()):
        return False
    try:
        datetime.strptime(s.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


class WeldingDataRequest(BaseModel):
    start_date: str
    end_date: str
    products: Optional[List[str]] = None
    destination_cds: Optional[List[str]] = None


@router.get("/products")
async def get_welding_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> List[dict]:
    """対象製品一覧。products テーブルから product_name に 'SD' を含む、status=active、product_type=量産品 を取得。"""
    q = select(Product).where(
        Product.product_name.like("%SD%"),
        Product.status == "active",
        Product.product_type == "量産品",
    ).order_by(Product.product_cd)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"value": row.product_cd, "label": f"{row.product_cd} - {row.product_name}"}
        for row in rows
    ]


@router.post("/data")
async def get_welding_shipping_data(
    body: WeldingDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("edit")),
) -> dict:
    """
    出荷データ。
    - 検証: start_date, end_date（YYYY-MM-DD）, products または destination_cds のいずれか一方（同時指定不可）
    - shipping_items から shipping_date BETWEEN start_date AND end_date, status != 'キャンセル'
    - products で product_name を取得して表示用マッピング
    - メモリ上で data[date][destination][productCd] = その組み合わせの複数件 { boxes }（集計せず明細のまま）
    - 返却: { dates, destinations, products: [{ cd, name }], data }
    """
    # 1. パラメータ検証
    if not _validate_date(body.start_date):
        raise HTTPException(status_code=400, detail="start_date は YYYY-MM-DD 形式で指定してください")
    if not _validate_date(body.end_date):
        raise HTTPException(status_code=400, detail="end_date は YYYY-MM-DD 形式で指定してください")
    start_date = body.start_date.strip()
    end_date = body.end_date.strip()
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date は end_date 以前を指定してください")

    product_cds = [
        str(p).strip() for p in (body.products or []) if p is not None and str(p).strip()
    ]
    dest_cds = [
        str(d).strip() for d in (body.destination_cds or []) if d is not None and str(d).strip()
    ]
    if product_cds and dest_cds:
        raise HTTPException(
            status_code=400,
            detail="products と destination_cds は同時に指定できません",
        )
    if not product_cds and not dest_cds:
        raise HTTPException(
            status_code=400,
            detail="products または destination_cds を選択してください",
        )

    # 納入先のみ指定時は shipping_items を直接参照（製品マスタの SD 条件で絞らない）
    destination_only = bool(dest_cds) and not product_cds
    dest_names: List[str] = []
    if dest_cds:
        q_dest = select(Destination.destination_name).where(Destination.destination_cd.in_(dest_cds))
        result_dest = await db.execute(q_dest)
        dest_names = [
            str(r.destination_name).strip()
            for r in result_dest.all()
            if r.destination_name and str(r.destination_name).strip()
        ]

    if destination_only:
        params_si = {
            "start_date": start_date,
            "end_date": end_date,
        }
        dest_cd_ph = ", ".join([f":dc_{i}" for i in range(len(dest_cds))])
        params_si.update({f"dc_{i}": dest_cds[i] for i in range(len(dest_cds))})
        dest_filter_parts = [f"destination_cd IN ({dest_cd_ph})"]
        if dest_names:
            dest_name_ph = ", ".join([f":dn_{i}" for i in range(len(dest_names))])
            params_si.update({f"dn_{i}": dest_names[i] for i in range(len(dest_names))})
            dest_filter_parts.append(f"destination_name IN ({dest_name_ph})")
        destination_filter_sql = f" AND ({' OR '.join(dest_filter_parts)})"

        q_si = text(f"""
            SELECT shipping_date, destination_cd, destination_name, product_cd, product_name, confirmed_boxes
            FROM shipping_items
            WHERE shipping_date BETWEEN :start_date AND :end_date
              AND (status IS NULL OR status != 'キャンセル'){destination_filter_sql}
            ORDER BY shipping_date, destination_cd, product_cd
        """)
    else:
        if not product_cds:
            q_welding = select(Product.product_cd).where(
                Product.product_name.like("%SD%"),
                Product.status == "active",
                Product.product_type == "量産品",
            ).order_by(Product.product_cd)
            result_welding = await db.execute(q_welding)
            product_cds = [row.product_cd for row in result_welding.all()]
            if not product_cds:
                return {"dates": [], "destinations": [], "products": [], "data": {}}

        placeholders = ", ".join([f":pc_{i}" for i in range(len(product_cds))])
        params_si = {
            "start_date": start_date,
            "end_date": end_date,
            **{f"pc_{i}": product_cds[i] for i in range(len(product_cds))},
        }
        destination_filter_sql = ""
        if dest_cds:
            dest_cd_ph = ", ".join([f":dc_{i}" for i in range(len(dest_cds))])
            params_si.update({f"dc_{i}": dest_cds[i] for i in range(len(dest_cds))})
            dest_filter_parts = [f"destination_cd IN ({dest_cd_ph})"]
            if dest_names:
                dest_name_ph = ", ".join([f":dn_{i}" for i in range(len(dest_names))])
                params_si.update({f"dn_{i}": dest_names[i] for i in range(len(dest_names))})
                dest_filter_parts.append(f"destination_name IN ({dest_name_ph})")
            destination_filter_sql = f" AND ({' OR '.join(dest_filter_parts)})"

        q_si = text(f"""
            SELECT shipping_date, destination_cd, destination_name, product_cd, product_name, confirmed_boxes
            FROM shipping_items
            WHERE shipping_date BETWEEN :start_date AND :end_date
              AND product_cd IN ({placeholders})
              AND (status IS NULL OR status != 'キャンセル'){destination_filter_sql}
            ORDER BY shipping_date, destination_cd, product_cd
        """)
    result_si = await db.execute(q_si, params_si)
    rows_si = result_si.mappings().all()

    # 3. products 表示名を組み立て
    display_product_cds = (
        sorted({r["product_cd"] for r in rows_si if r.get("product_cd")})
        if destination_only
        else product_cds
    )
    if not display_product_cds:
        return {"dates": [], "destinations": [], "products": [], "data": {}}

    # shipping_items.product_name を優先、無ければ products マスタ
    name_from_rows: dict = {}
    for r in rows_si:
        pc = r.get("product_cd")
        if not pc or pc in name_from_rows:
            continue
        row_name = (r.get("product_name") or "").strip()
        if row_name:
            name_from_rows[pc] = row_name

    q_prod = select(Product.product_cd, Product.product_name).where(
        Product.product_cd.in_(display_product_cds)
    ).order_by(Product.product_cd)
    result_prod = await db.execute(q_prod)
    rows_prod = result_prod.all()
    product_name_by_cd = {row.product_cd: (row.product_name or row.product_cd) for row in rows_prod}

    products_out = [
        {
            "cd": cd,
            "name": name_from_rows.get(cd) or product_name_by_cd.get(cd, cd),
        }
        for cd in display_product_cds
    ]

    # 4. メモリ上で data[date][destination][productCd] = [{ boxes }, ...]
    dates_set = set()
    destinations_set = set()
    data_nested = {}

    for r in rows_si:
        ship_date = r["shipping_date"]
        date_str = ship_date.isoformat() if hasattr(ship_date, "isoformat") else str(ship_date)
        dest = r["destination_name"] or r["destination_cd"] or ""
        pc = r["product_cd"] or ""
        boxes = int(r.get("confirmed_boxes") or 0)

        dates_set.add(date_str)
        destinations_set.add(dest)

        if date_str not in data_nested:
            data_nested[date_str] = {}
        if dest not in data_nested[date_str]:
            data_nested[date_str][dest] = {}
        if pc not in data_nested[date_str][dest]:
            data_nested[date_str][dest][pc] = []
        data_nested[date_str][dest][pc].append({"boxes": boxes})

    dates_out = sorted(dates_set)
    destinations_out = sorted(destinations_set)

    return {
        "dates": dates_out,
        "destinations": destinations_out,
        "products": products_out,
        "data": data_nested,
    }


class WeldingExportRequest(BaseModel):
    start_date: str
    end_date: str
    products: List[str]
    table_data: Optional[dict] = None


def _format_date_ja(date_str: str) -> str:
    """YYYY-MM-DD -> 月/日(曜)"""
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        week = ["月", "火", "水", "木", "金", "土", "日"][d.weekday()]
        return f"{d.month}/{d.day}({week})"
    except Exception:
        return date_str


def _format_date_short(date_str: str) -> str:
    """YYYY-MM-DD -> 月/日（印刷用）"""
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return f"{d.month}/{d.day}"
    except Exception:
        return date_str


def _build_export_html(table_data: dict, start_date: str, end_date: str) -> str:
    """table_data から印刷用 HTML を生成（出荷管理表・A4横向）。"""
    dates = table_data.get("dates") or []
    destinations = table_data.get("destinations") or []
    products = table_data.get("products") or []
    data_map = table_data.get("data") or {}

    if not dates or not products:
        return "<html><body><p>データがありません。</p></body></html>"

    # 行リスト: (destination, product_cd, product_name) で hasData のものだけ
    rows = []
    for dest in destinations:
        for p in products:
            cd = p.get("cd") or p.get("product_cd") or ""
            name = p.get("name") or p.get("product_name") or cd
            has_data = False
            for dt in dates:
                arr = ((data_map.get(dt) or {}).get(dest) or {}).get(cd) or []
                if arr:
                    has_data = True
                    break
            if has_data:
                rows.append((dest, cd, name))

    # 納入先ごとの rowspan
    dest_spans = {}
    i = 0
    while i < len(rows):
        d = rows[i][0]
        j = i + 1
        while j < len(rows) and rows[j][0] == d:
            j += 1
        dest_spans[i] = j - i
        i = j

    # 表头：納入先 | 製品名 | 日期列
    date_headers = "".join(
        f'<th class="th-date">{_format_date_short(d)}</th>' for d in dates
    )

    # データセル：複数は「N箱」を改行で連結、無い場合は「-」
    def cell_content(arr: list) -> str:
        if not arr or not isinstance(arr, list):
            return "—"
        parts = []
        for x in arr:
            b = x.get("boxes")
            if b is not None:
                parts.append(f"{int(b)}箱")
        return "<br>".join(parts) if parts else "—"

    # 表本体：納入先第一列独占一行；製品名第二列独占一行，同行为日期数据
    n_dates = len(dates)
    tbody = []
    i = 0
    while i < len(rows):
        dest, _, _ = rows[i]
        span = dest_spans.get(i, 1)
        # 納入先行：第一列納入先，其余列合并为空
        tbody.append(
            f'<tr><td class="td-dest">{_escape(dest)}</td><td class="td-empty" colspan="{1 + n_dates}"></td></tr>'
        )
        # 製品名行：第一列空，第二列製品名，其后为日期数据
        for k in range(span):
            _, pcd, pname = rows[i + k]
            cells = [f'<td class="td-empty"></td>', f'<td class="td-product">{_escape(pname)}</td>']
            for dt in dates:
                arr = ((data_map.get(dt) or {}).get(dest) or {}).get(pcd) or []
                txt = cell_content(arr)
                cells.append(f'<td class="td-num">{txt}</td>')
            tbody.append(f"<tr>{''.join(cells)}</tr>")
        i += span

    period = f"{start_date} ~ {end_date}"
    product_labels = "、".join(_escape(p.get("name") or p.get("product_name") or p.get("cd") or "") for p in products)
    dest_labels = "、".join(_escape(d) for d in destinations) if destinations else "—"
    print_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>出荷管理表</title>
  <style>
    @page {{ size: A4 landscape; margin-left: 5mm; margin-right: 5mm; margin-top: 12mm; margin-bottom: 12mm; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Yu Gothic', 'Meiryo', 'Hiragino Sans', sans-serif; color: #000; background: #fff; margin: 0; padding-left: 5mm; padding-right: 5mm; padding-top: 12mm; padding-bottom: 12mm; font-size: 11px; }}
    .header {{ text-align: center; margin-bottom: 12px; }}
    .title {{ font-size: 18px; font-weight: bold; margin-bottom: 6px; }}
    .period {{ margin-bottom: 4px; }}
    .products {{ margin-bottom: 10px; }}
    table {{ border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 10px; }}
    th, td {{ border: 1px solid #000; padding: 4px 6px; vertical-align: middle; }}
    th {{ background: #fff; font-weight: 600; text-align: center; }}
    .th-date {{ min-width: 0; }}
    .th-dest {{ text-align: left; white-space: nowrap; border-right: none; }}
    .th-product {{ text-align: left; white-space: nowrap; width: 9%; border-left: none; }}
    .td-dest {{ text-align: left; white-space: nowrap; padding: 6px 8px; vertical-align: middle; border-right: none; }}
    .td-empty {{ border: 1px solid #000; }}
    .td-empty[colspan] {{ border-left: none; }}
    .td-empty:not([colspan]) {{ border-right: none; }}
    .td-product {{ font-weight: 600; text-align: left; white-space: nowrap; padding: 4px 8px; width: 11%; border-left: none; }}
    .td-num {{ text-align: center; white-space: normal; word-break: break-all; }}
    .footer {{ position: fixed; bottom: 12mm; right: 5mm; font-size: 10px; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">出荷管理表</div>
    <div class="period">期間: {_escape(period)}</div>
    <div class="products">対象製品: {product_labels}</div>
    <div class="destinations">対象納入先: {dest_labels}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th class="th-dest">納入先</th>
        <th class="th-product">製品名</th>
        {date_headers}
      </tr>
    </thead>
    <tbody>
      {''.join(tbody)}
    </tbody>
  </table>
  <div class="footer">出力日時: {print_time}</div>
</body>
</html>"""
    return html


def _escape(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


@router.post("/export")
async def export_welding_shipping_report(
    body: WeldingExportRequest,
    current_user: User = Depends(require_sales_operation("export")),
) -> dict:
    """印刷用レポート HTML。table_data から表を生成する。"""
    if not body.table_data or not isinstance(body.table_data, dict):
        return {"html": "<html><body><p>データがありません。</p></body></html>"}
    html = _build_export_html(body.table_data, body.start_date, body.end_date)
    return {"html": html}
