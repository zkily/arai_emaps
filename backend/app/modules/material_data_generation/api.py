"""
材料在庫データ生成 API
  POST /api/material-data-generation/generate

materials（status=1 の材料）と suppliers を基に、
指定期間（start_date～end_date）の material_stock 日別在庫データを一括生成する。
"""
from datetime import date as date_type, datetime, timedelta
from typing import Optional, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import Material, Supplier
from app.modules.material.models import MaterialStock

router = APIRouter()


class MaterialDataGenerationRequest(BaseModel):
  start_date: str
  end_date: str
  overwrite_existing: bool = False


def _parse_date_str(value: str) -> date_type:
  """YYYY-MM-DD 形式の文字列を date に変換する。"""
  if not value:
    raise ValueError("empty date")
  s = value.strip()
  # 先頭10文字だけを見る (2026-03-10T00:00:00 なども許容)
  if len(s) >= 10:
    s = s[:10]
  try:
    return date_type.fromisoformat(s)
  except ValueError as e:
    raise ValueError(f"無効な日付形式: {value}") from e


@router.post("/generate")
async def generate_material_stock_data(
  body: MaterialDataGenerationRequest,
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(verify_token_and_get_user),
):
  """
  材料在庫データ生成:
    - 対象: materials.status = 1 の材料
    - 期間: start_date ～ end_date（両端含む）
    - 各 (material_cd, date) について material_stock を作成/更新/スキップ
      * 既存行があり overwrite_existing=False → スキップ
      * 既存行があり overwrite_existing=True  → 主にマスタ系項目を更新
      * 行が無い場合                            → 新規作成
  """
  # 1) 日付パラメータの検証
  try:
    start = _parse_date_str(body.start_date)
    end = _parse_date_str(body.end_date)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))

  if start > end:
    raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")

  # 2) 有効な材料マスタ + 仕入先名 取得（materials.status = 1）
  mat_stmt = (
    select(
      Material.material_cd,
      Material.material_name,
      Material.material_type,
      Material.unit,
      Material.supplier_cd,
      Supplier.supplier_name,
      Material.unit_price,
      Material.lead_time,
      Material.safety_stock,
      Material.long_weight,
      Material.pieces_per_bundle,
      Material.standard_spec,
    )
    .select_from(Material)
    .outerjoin(Supplier, Material.supplier_cd == Supplier.supplier_cd)
    .where(Material.status == 1)
    .order_by(Material.material_cd)
  )
  mat_rows = (await db.execute(mat_stmt)).all()

  if not mat_rows:
    # 対象材料なし
    return {
      "success": True,
      "data": {
        "generated_count": 0,
        "updated_count": 0,
        "skipped_count": 0,
        "duplicate_count": 0,
      },
    }

  # material_cd 一覧
  material_cds = [row[0] for row in mat_rows]

  # 3) 期間内既存 material_stock を一括取得してマップ化
  existing_stmt = (
    select(MaterialStock)
    .where(
      MaterialStock.material_cd.in_(material_cds),
      MaterialStock.date >= start,
      MaterialStock.date <= end,
    )
  )
  existing_rows = (await db.execute(existing_stmt)).scalars().all()
  existing_map: dict[Tuple[str, date_type], MaterialStock] = {
    (r.material_cd, r.date): r for r in existing_rows
  }

  # 4) 期間の date リストを生成（両端含む）
  dates: List[date_type] = []
  cur = start
  one_day = timedelta(days=1)
  while cur <= end:
    dates.append(cur)
    cur += one_day

  generated_count = 0
  updated_count = 0
  skipped_count = 0
  duplicate_count = 0

  # 5) 日付 × 材料の二重ループで生成/更新/スキップ判定
  for d in dates:
    for (
      material_cd,
      material_name,
      material_type,
      unit,
      supplier_cd,
      supplier_name,
      unit_price,
      lead_time,
      safety_stock,
      long_weight,
      pieces_per_bundle,
      standard_spec,
    ) in mat_rows:
      key = (material_cd, d)
      existing = existing_map.get(key)

      if existing:
        # 既に行がある
        if body.overwrite_existing:
          # マスタ系項目を更新（数量などは保持）
          existing.material_name = material_name
          existing.unit = unit
          existing.supplier_cd = supplier_cd
          existing.supplier_name = supplier_name
          existing.unit_price = unit_price or 0
          existing.lead_time = int(lead_time or 0)
          existing.safety_stock = int(safety_stock or 0)
          existing.long_weight = long_weight or 0
          existing.pieces_per_bundle = int(pieces_per_bundle or 0)
          existing.standard_spec = standard_spec
          # 金額は計算し直す前提で 0 にリセット
          existing.order_amount = 0

          updated_count += 1
        else:
          # 既存行をそのまま使用 → スキップ & 重複扱い
          skipped_count += 1
          duplicate_count += 1
        continue

      # 存在しない場合は新規作成
      row = MaterialStock(
        material_cd=material_cd,
        material_name=material_name,
        date=d,
        current_stock=0,
        safety_stock=int(safety_stock or 0),
        max_stock=0,
        unit=unit,
        unit_price=unit_price or 0,
        supplier_cd=supplier_cd,
        supplier_name=supplier_name,
        lead_time=int(lead_time or 0),
        long_weight=long_weight or 0,
        pieces_per_bundle=int(pieces_per_bundle or 0),
        standard_spec=standard_spec,
        remarks="",
        order_amount=0,
      )
      db.add(row)
      generated_count += 1

  # 6) コミットして結果を返却
  await db.commit()

  return {
    "success": True,
    "data": {
      "generated_count": generated_count,
      "updated_count": updated_count,
      "skipped_count": skipped_count,
      "duplicate_count": duplicate_count,
    },
  }

