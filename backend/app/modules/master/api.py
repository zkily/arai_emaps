"""
製品マスタ API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from decimal import Decimal, InvalidOperation
import io
import csv
import os

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Product, Material, Supplier, ProductRouteStep, Process
from app.modules.master.schemas import ProductCreate, ProductUpdate

router = APIRouter()
_DEFAULT_PRODUCT_CSV_DIR = "//192.168.1.200/社内共有/02_生産管理部/Data/BT-data/送信"
PRODUCT_CSV_OUTPUT_DIR = os.environ.get("PRODUCT_CSV_OUTPUT_DIR", _DEFAULT_PRODUCT_CSV_DIR)
PRODUCT_CSV_FILENAME = "ProductMaster.csv"


def _row_to_dict(row: Product) -> dict:
    return {
        "id": row.id,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "product_type": row.product_type,
        "location_cd": row.location_cd,
        "start_use_date": row.start_use_date.isoformat() if row.start_use_date else None,
        "category": row.category,
        "department_id": row.department_id,
        "destination_cd": row.destination_cd,
        "process_count": row.process_count,
        "lead_time": row.lead_time,
        "lot_size": row.lot_size,
        "is_multistage": bool(row.is_multistage),
        "priority": row.priority,
        "status": row.status,
        "part_number": row.part_number,
        "vehicle_model": row.vehicle_model,
        "box_type": row.box_type,
        "unit_per_box": row.unit_per_box,
        "dimensions": row.dimensions,
        "weight": float(row.weight) if row.weight is not None else None,
        "material_cd": row.material_cd,
        "cut_length": float(row.cut_length) if row.cut_length is not None else None,
        "chamfer_length": float(row.chamfer_length) if row.chamfer_length is not None else None,
        "developed_length": float(row.developed_length) if row.developed_length is not None else None,
        "take_count": row.take_count,
        "scrap_length": float(row.scrap_length) if row.scrap_length is not None else None,
        "bom_id": row.bom_id,
        "route_cd": row.route_cd,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "safety_days": row.safety_days,
        "unit_price": float(row.unit_price) if row.unit_price is not None else None,
        "product_alias": row.product_alias,
    }


@router.get("")
async def get_product_list(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    material_cd: Optional[str] = Query(None),
    route_cd: Optional[str] = Query(None),
    location_cd: Optional[str] = Query(None),
    destination_cd: Optional[str] = Query(None, description="納入先CD（該当納入先の製品のみ）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品一覧取得（検索・ページネーション）"""
    query = select(Product)
    if keyword:
        query = query.where(
            or_(
                Product.product_name.like(f"%{keyword}%"),
                Product.product_alias.like(f"%{keyword}%"),
                Product.part_number.like(f"%{keyword}%"),
                Product.product_cd.like(f"%{keyword}%"),
            )
        )
    if category:
        query = query.where(Product.category == category)
    if product_type:
        query = query.where(Product.product_type == product_type)
    if status:
        query = query.where(Product.status == status)
    if product_cd:
        query = query.where(Product.product_cd == product_cd)
    if material_cd:
        query = query.where(Product.material_cd == material_cd)
    if route_cd:
        query = query.where(Product.route_cd == route_cd)
    if location_cd:
        query = query.where(Product.location_cd == location_cd)
    if destination_cd:
        query = query.where(Product.destination_cd == destination_cd)

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    # 材料名を付与：material_cd 一覧で materials を取得
    material_cds = [r.material_cd for r in rows if getattr(r, "material_cd", None)]
    material_names = {}
    if material_cds:
        mat_result = await db.execute(
            select(Material.material_cd, Material.material_name).where(Material.material_cd.in_(material_cds))
        )
        for mat_row in mat_result.all():
            material_names[mat_row.material_cd] = mat_row.material_name

    def _item_with_material(p: Product) -> dict:
        d = _row_to_dict(p)
        if p.material_cd and p.material_cd in material_names:
            d["material_name"] = material_names[p.material_cd]
        else:
            d["material_name"] = None
        return d

    return {
        "success": True,
        "data": {
            "list": [_item_with_material(r) for r in rows],
            "total": total,
        },
    }


def _material_stock_length_from_name(material_name: Optional[str]) -> Optional[Decimal]:
    """材料名の末尾4文字を材料長（数値）として解釈する。"""
    if not material_name or not isinstance(material_name, str):
        return None
    s = material_name.strip()
    if len(s) < 4:
        return None
    tail = s[-4:].strip()
    try:
        return Decimal(tail)
    except InvalidOperation:
        return None


@router.post("/recalculate-scrap-length")
async def recalculate_all_scrap_length(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    全製品の端材長（scrap_length）を一括再計算して DB に保存する。
    材料長 = materials.material_name の末尾4文字を数値化、
    scrap_length = 材料長 - (cut_length + 2.5) * take_count。
    material_cd・材料マスタ・cut_length・take_count が揃わない行はスキップ。
    """
    result = await db.execute(select(Product))
    products = result.scalars().all()
    mat_cds = {p.material_cd for p in products if getattr(p, "material_cd", None)}
    material_names: dict[str, Optional[str]] = {}
    if mat_cds:
        mat_result = await db.execute(
            select(Material.material_cd, Material.material_name).where(Material.material_cd.in_(mat_cds))
        )
        for row in mat_result.all():
            material_names[row.material_cd] = row.material_name

    updated = 0
    skipped = 0
    margin = Decimal("2.5")

    for p in products:
        if not p.material_cd or p.material_cd not in material_names:
            skipped += 1
            continue
        stock_len = _material_stock_length_from_name(material_names.get(p.material_cd))
        if stock_len is None:
            skipped += 1
            continue
        if p.cut_length is None or p.take_count is None:
            skipped += 1
            continue
        try:
            cut = Decimal(str(p.cut_length))
            take = int(p.take_count)
        except (InvalidOperation, ValueError, TypeError):
            skipped += 1
            continue
        scrap = stock_len - (cut + margin) * take
        scrap_q = scrap.quantize(Decimal("0.01"))
        p.scrap_length = scrap_q
        updated += 1

    await db.commit()
    return {
        "success": True,
        "updated": updated,
        "skipped": skipped,
        "total": len(products),
    }


@router.get("/by-destination/{destination_cd}")
async def get_products_by_destination_for_batch(
    destination_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月注文一括登録用：指定納入先の製品のみ。条件は destination_cd=納入先、status=active、product_type=量産品"""
    query = (
        select(Product)
        .where(Product.destination_cd == destination_cd)
        .where(Product.status == "active")
        .where(Product.product_type == "量産品")
        .order_by(Product.product_cd)
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_row_to_dict(r) for r in rows], "total": len(rows)},
        "list": [_row_to_dict(r) for r in rows],
    }


@router.get("/batch-detail/{product_cd}")
async def get_product_batch_detail(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規ロット追加用：製品の製品CD・製品名・原材料・規格・材料メーカー・取数・切断長・面取長・展開長・端材長・面取工程・SW工程を返す。"""
    q = select(Product).where(Product.product_cd == product_cd)
    res = await db.execute(q)
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="製品が見つかりません")
    material_name = None
    standard_specification = None
    material_manufacturer = None
    if product.material_cd:
        mat_res = await db.execute(select(Material).where(Material.material_cd == product.material_cd))
        mat = mat_res.scalar_one_or_none()
        if mat:
            material_name = mat.material_name
            standard_specification = getattr(mat, "standard_spec", None) or None
            if getattr(mat, "supplier_cd", None):
                sup_res = await db.execute(select(Supplier).where(Supplier.supplier_cd == mat.supplier_cd))
                sup = sup_res.scalar_one_or_none()
                if sup:
                    material_manufacturer = sup.supplier_name
    has_chamfering_process = False
    has_sw_process = False
    if product.route_cd:
        steps_res = await db.execute(
            select(ProductRouteStep.process_cd)
            .where(ProductRouteStep.product_cd == product_cd)
            .where(ProductRouteStep.route_cd == product.route_cd)
        )
        process_cds = [r[0] for r in steps_res.all() if r[0]]
        if process_cds:
            proc_res = await db.execute(select(Process.process_cd, Process.process_name).where(Process.process_cd.in_(process_cds)))
            for row in proc_res.all():
                name = (row.process_name or "").strip()
                if "面取" in name:
                    has_chamfering_process = True
                if "SW" in name or "swaging" in name.lower():
                    has_sw_process = True
    return {
        "success": True,
        "data": {
            "product_cd": product.product_cd,
            "product_name": product.product_name or product.product_cd,
            "material_name": material_name,
            "standard_specification": standard_specification,
            "material_manufacturer": material_manufacturer,
            "take_count": product.take_count,
            "cutting_length": float(product.cut_length) if product.cut_length is not None else None,
            "chamfering_length": float(product.chamfer_length) if product.chamfer_length is not None else None,
            "developed_length": float(product.developed_length) if product.developed_length is not None else None,
            "scrap_length": float(product.scrap_length) if product.scrap_length is not None else None,
            "has_chamfering_process": has_chamfering_process,
            "has_sw_process": has_sw_process,
        },
    }


@router.get("/max-cd")
async def get_max_product_cd(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """最大製品CD取得（新規登録時の初期値用）"""
    q = select(Product.product_cd)
    res = await db.execute(q)
    codes = [r for r in res.scalars().all() if r and str(r).isdigit()]
    if not codes:
        return 90000
    return max(int(c) for c in codes)


@router.post("")
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品新規登録"""
    q = select(Product).where(Product.product_cd == body.product_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="製品CDは既に存在します")
    row = Product(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品更新"""
    q = select(Product).where(Product.id == product_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品が見つかりません")
    for k, v in body.model_dump().items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品削除"""
    q = select(Product).where(Product.id == product_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="製品が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


class ExportCsvItem(BaseModel):
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    unit_per_box: Optional[int] = None


@router.post("/export-csv")
async def export_products_csv(
    body: list[ExportCsvItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """CSV出力（body: [{ product_cd, product_name, unit_per_box }]）"""
    output = io.StringIO()
    output.write("\uFEFF")  # UTF-8 BOM（Excel で日本語文字化け防止）
    writer = csv.writer(output)
    writer.writerow(["product_cd", "product_name", "unit_per_box"])
    for item in body:
        writer.writerow([
            item.product_cd or "",
            item.product_name or "",
            item.unit_per_box if item.unit_per_box is not None else "",
        ])
    csv_content = output.getvalue()

    if not PRODUCT_CSV_OUTPUT_DIR:
        raise HTTPException(status_code=500, detail="CSV出力先が未設定です")

    try:
        os.makedirs(PRODUCT_CSV_OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(PRODUCT_CSV_OUTPUT_DIR, PRODUCT_CSV_FILENAME)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            f.write(csv_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV保存失敗: {str(e)}")

    return {
        "success": True,
        "message": "ProductMaster.csv を共有フォルダに保存しました",
        "fileName": PRODUCT_CSV_FILENAME,
        "csvFilePath": output_path,
        "rowCount": len(body),
    }
