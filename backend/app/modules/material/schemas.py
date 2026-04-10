"""
材料管理 Pydantic スキーマ
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal


# ─────────────────────────────────────────────
# 検品基準マスタ (material_inspection_master)
# ─────────────────────────────────────────────
class InspectionMasterBase(BaseModel):
    inspection_cd: str
    inspection_standard: str


class InspectionMasterCreate(InspectionMasterBase):
    pass


class InspectionMasterUpdate(BaseModel):
    inspection_cd: Optional[str] = None
    inspection_standard: Optional[str] = None


class InspectionMasterResponse(InspectionMasterBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 受入ログ (material_logs)
# ─────────────────────────────────────────────
class MaterialLogBase(BaseModel):
    item: str
    material_cd: str
    material_name: Optional[str] = None
    process_cd: str
    log_date: date
    log_time: time
    hd_no: Optional[str] = None
    pieces_per_bundle: Optional[int] = None
    quantity: Optional[int] = None
    bundle_quantity: Optional[int] = None
    manufacture_no: Optional[str] = None
    manufacture_date: Optional[date] = None
    length: Optional[int] = None
    outer_diameter1: Optional[Decimal] = None
    outer_diameter2: Optional[Decimal] = None
    magnetic: Optional[str] = None
    appearance: Optional[str] = None
    supplier: Optional[str] = None
    material_quality: Optional[str] = None
    remarks: Optional[str] = None
    note: Optional[str] = None


class MaterialLogCreate(MaterialLogBase):
    pass


class MaterialLogUpdate(BaseModel):
    item: Optional[str] = None
    material_cd: Optional[str] = None
    material_name: Optional[str] = None
    process_cd: Optional[str] = None
    log_date: Optional[date] = None
    log_time: Optional[time] = None
    hd_no: Optional[str] = None
    pieces_per_bundle: Optional[int] = None
    quantity: Optional[int] = None
    bundle_quantity: Optional[int] = None
    manufacture_no: Optional[str] = None
    manufacture_date: Optional[date] = None
    length: Optional[int] = None
    outer_diameter1: Optional[Decimal] = None
    outer_diameter2: Optional[Decimal] = None
    magnetic: Optional[str] = None
    appearance: Optional[str] = None
    supplier: Optional[str] = None
    material_quality: Optional[str] = None
    remarks: Optional[str] = None
    note: Optional[str] = None
    cutting_used_manual: Optional[bool] = None
    cutting_used_manual_note: Optional[str] = None
    #: cutting_used_manual=True 時のみ有効。値があると material_cutting_logs に手動行を1件追加
    manual_cutting_management_code: Optional[str] = None


class MaterialLogResponse(MaterialLogBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cutting_used_manual: bool = False
    cutting_used_manual_at: Optional[datetime] = None
    cutting_used_manual_by: Optional[str] = None
    cutting_used_manual_note: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 材料在庫メイン (material_stock)
# ─────────────────────────────────────────────
class MaterialStockBase(BaseModel):
    material_cd: str
    material_name: str
    date: date
    initial_stock: Optional[int] = 0
    current_stock: Optional[int] = 0
    safety_stock: Optional[int] = 0
    planned_usage: Optional[int] = 0
    adjustment_quantity: Optional[int] = 0
    max_stock: Optional[int] = 0
    standard_spec: Optional[str] = ""
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    pieces_per_bundle: Optional[int] = 0
    long_weight: Optional[Decimal] = None
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    lead_time: Optional[int] = 0
    bundle_quantity: Optional[int] = 0
    bundle_weight: Optional[Decimal] = None
    order_quantity: Optional[int] = 0
    order_bundle_quantity: Optional[int] = 0
    order_amount: Optional[Decimal] = None
    remarks: Optional[str] = ""


class MaterialStockCreate(MaterialStockBase):
    pass


class MaterialStockUpdate(BaseModel):
    material_cd: Optional[str] = None
    material_name: Optional[str] = None
    date: Optional[date] = None
    initial_stock: Optional[int] = None
    current_stock: Optional[int] = None
    safety_stock: Optional[int] = None
    planned_usage: Optional[int] = None
    adjustment_quantity: Optional[int] = None
    max_stock: Optional[int] = None
    standard_spec: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    pieces_per_bundle: Optional[int] = None
    long_weight: Optional[Decimal] = None
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    lead_time: Optional[int] = None
    bundle_quantity: Optional[int] = None
    bundle_weight: Optional[Decimal] = None
    order_quantity: Optional[int] = None
    order_bundle_quantity: Optional[int] = None
    order_amount: Optional[Decimal] = None
    remarks: Optional[str] = None


class MaterialStockResponse(MaterialStockBase):
    id: int
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransferToSubBody(BaseModel):
    """主表在庫を半端（sub）へ転送するリクエスト"""
    stock_id: int
    quantity: int = 1


# ─────────────────────────────────────────────
# 材料在庫サブ (material_stock_sub)
# ─────────────────────────────────────────────
class MaterialStockSubBase(BaseModel):
    material_cd: str
    material_name: str
    date: date
    current_stock: Optional[Decimal] = None
    safety_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    lead_time: Optional[int] = 0
    planned_usage: Optional[Decimal] = None
    order_quantity: Optional[Decimal] = None
    order_bundle_quantity: Optional[Decimal] = None
    bundle_weight: Optional[Decimal] = None
    order_amount: Optional[Decimal] = None
    standard_spec: Optional[str] = None
    pieces_per_bundle: Optional[int] = 0
    long_weight: Optional[Decimal] = None
    remarks: Optional[str] = None
    label_color: Optional[str] = None


class MaterialStockSubCreate(MaterialStockSubBase):
    pass


class MaterialStockSubUpdate(BaseModel):
    material_cd: Optional[str] = None
    material_name: Optional[str] = None
    date: Optional[date] = None
    current_stock: Optional[Decimal] = None
    safety_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    lead_time: Optional[int] = None
    planned_usage: Optional[Decimal] = None
    order_quantity: Optional[Decimal] = None
    order_bundle_quantity: Optional[Decimal] = None
    bundle_weight: Optional[Decimal] = None
    order_amount: Optional[Decimal] = None
    standard_spec: Optional[str] = None
    pieces_per_bundle: Optional[int] = None
    long_weight: Optional[Decimal] = None
    remarks: Optional[str] = None
    label_color: Optional[str] = None


class MaterialStockSubResponse(MaterialStockSubBase):
    id: int
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 在庫材料管理 (stock_materials)
# ─────────────────────────────────────────────
class StockMaterialBase(BaseModel):
    material_name: str
    manufacture_no: str
    quantity: int = 0
    log_date: date
    supplier: Optional[str] = None
    material_quality: Optional[str] = None
    is_used: bool = False
    note: Optional[str] = None


class StockMaterialCreate(StockMaterialBase):
    pass


class StockMaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    manufacture_no: Optional[str] = None
    quantity: Optional[int] = None
    log_date: Optional[date] = None
    supplier: Optional[str] = None
    material_quality: Optional[str] = None
    is_used: Optional[bool] = None
    note: Optional[str] = None


class StockMaterialResponse(StockMaterialBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 材料使用済テーブル (material_usage_record)
# ─────────────────────────────────────────────

class MaterialUsageRecordBase(BaseModel):
    usage_date: date
    material_cd: str
    material_name: str
    usage_count: int = 0
    source: str = "cutting_management"
    management_codes: Optional[str] = None
    management_code: Optional[str] = None
    reflected: bool = False


class MaterialUsageRecordCreate(MaterialUsageRecordBase):
    pass


class MaterialUsageRecordResponse(MaterialUsageRecordBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialUsagePreviewItem(BaseModel):
    """使用数プレビュー（確認ダイアログ表示用）"""
    usage_date: date
    material_cd: str
    material_name: str
    usage_count: int
    already_recorded: bool = False


class MaterialUsageCommitRequest(BaseModel):
    """使用数反映確定リクエスト"""
    today_date: str
    tomorrow_date: Optional[str] = None
    source: str = "cutting_management"


class MaterialUsagePreviewRequest(BaseModel):
    """使用数プレビューリクエスト"""
    today_date: str
    tomorrow_date: Optional[str] = None
    source: str = "cutting_management"


# ─────────────────────────────────────────────
# 材料切断ログ (material_cutting_logs)
# ─────────────────────────────────────────────
class MaterialCuttingLogResponse(BaseModel):
    id: int
    item: Optional[str] = None
    log_date: Optional[date] = None
    log_time: Optional[time] = None
    hd_no: Optional[str] = None
    operator_name: Optional[str] = None
    material_cd: Optional[str] = None
    manufacture_no: Optional[str] = None
    management_code: Optional[str] = None
    raw_line: Optional[str] = None
    source_file: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialCuttingImportResult(BaseModel):
    success: bool
    imported: int = 0
    skipped: int = 0
    errors: List[str] = []
