"""
材料管理 データベースモデル
対象テーブル:
  - material_inspection_master  (検品基準マスタ)
  - material_logs               (受入ログ)
  - material_stock              (材料在庫メイン)
  - material_stock_sub          (材料在庫サブ / 手動注文)
  - stock_materials             (在庫材料管理)
  - material_usage_record       (材料使用済テーブル)
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, Numeric, Time
from sqlalchemy.sql import func
from app.core.database import Base


class MaterialInspectionMaster(Base):
    """材料検品基準マスタ（material_inspection_master）"""
    __tablename__ = "material_inspection_master"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inspection_cd = Column(String(50), unique=True, nullable=False, index=True, comment="検験代码")
    inspection_standard = Column(Text, nullable=False, comment="検験基準")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新日時")


class MaterialLog(Base):
    """材料受入ログ（material_logs）"""
    __tablename__ = "material_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item = Column(String(100), nullable=False, comment="項目")
    material_cd = Column(String(50), nullable=False, index=True, comment="製品CD")
    material_name = Column(String(255), comment="製品名")
    process_cd = Column(String(50), nullable=False, index=True, comment="工程CD")
    log_date = Column(Date, nullable=False, index=True, comment="日付")
    log_time = Column(Time, nullable=False, comment="時間")
    hd_no = Column(String(50), comment="HD番号")
    pieces_per_bundle = Column(Integer, comment="1束あたりの本数")
    quantity = Column(Integer, comment="数量")
    bundle_quantity = Column(Integer, comment="束数量")
    manufacture_no = Column(String(100), index=True, comment="製造番号")
    manufacture_date = Column(Date, comment="製造日")
    length = Column(Integer, comment="長さ(mm)")
    outer_diameter1 = Column(Numeric(10, 4), comment="外径1(mm)")
    outer_diameter2 = Column(Numeric(10, 4), comment="外径2(mm)")
    magnetic = Column(String(1), comment="磁気")
    appearance = Column(String(1), comment="外観")
    supplier = Column(String(255), index=True, comment="仕入先")
    material_quality = Column(String(100), comment="材質")
    remarks = Column(Text, comment="備考")
    note = Column(String(255), comment="メモ")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新日時")


class MaterialStock(Base):
    """材料在庫メイン（material_stock）"""
    __tablename__ = "material_stock"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_cd = Column(String(50), nullable=False, index=True, comment="材料CD")
    material_name = Column(String(50), nullable=False, comment="材料名")
    date = Column(Date, nullable=False, default="2025-01-01", index=True, comment="日付")
    initial_stock = Column(Integer, default=0, comment="初期在庫")
    current_stock = Column(Integer, default=0, index=True, comment="現在在庫")
    safety_stock = Column(Integer, default=0, comment="安全在庫")
    planned_usage = Column(Integer, default=0, comment="使用数")
    adjustment_quantity = Column(Integer, default=0, comment="調整数")
    max_stock = Column(Integer, default=0, comment="最大在庫")
    standard_spec = Column(String(50), default="", comment="規格")
    unit = Column(String(20), comment="単位")
    unit_price = Column(Numeric(15, 2), default=0.00, comment="単価")
    pieces_per_bundle = Column(Integer, default=0, comment="束当たり本数")
    long_weight = Column(Numeric(15, 2), comment="一本重量")
    supplier_cd = Column(String(15), index=True, comment="仕入先CD")
    supplier_name = Column(String(50), comment="仕入先名")
    lead_time = Column(Integer, default=0, comment="リードタイム(日)")
    bundle_quantity = Column(Integer, default=0, comment="束本数")
    bundle_weight = Column(Numeric(15, 2), default=0.00, comment="束重量(kg)")
    order_quantity = Column(Integer, default=0, comment="注文数")
    order_bundle_quantity = Column(Integer, default=0, comment="注文本数")
    order_amount = Column(Numeric(15, 2), default=0.00, comment="注文金額")
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), comment="最終更新日時")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")
    remarks = Column(String(50), default="", comment="備考")


class MaterialStockSub(Base):
    """材料在庫サブ（手動注文データ）（material_stock_sub）"""
    __tablename__ = "material_stock_sub"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_cd = Column(String(50), nullable=False, index=True, comment="材料CD")
    material_name = Column(String(255), nullable=False, comment="材料名")
    date = Column(Date, nullable=False, index=True, comment="日期")
    current_stock = Column(Numeric(10, 2), default=0.00, comment="現在在庫")
    safety_stock = Column(Numeric(10, 2), default=0.00, comment="安全在庫")
    max_stock = Column(Numeric(10, 2), default=0.00, comment="最大在庫")
    unit = Column(String(20), comment="単位")
    unit_price = Column(Numeric(10, 2), default=0.00, comment="単価")
    supplier_cd = Column(String(50), index=True, comment="仕入先CD")
    supplier_name = Column(String(255), comment="仕入先名")
    lead_time = Column(Integer, default=0, comment="リードタイム")
    planned_usage = Column(Numeric(10, 2), default=0.00, comment="計画使用数")
    order_quantity = Column(Numeric(10, 2), default=0.00, comment="注文束数")
    order_bundle_quantity = Column(Numeric(10, 2), default=0.00, comment="注文本数")
    bundle_weight = Column(Numeric(10, 2), default=0.00, comment="捆重量")
    order_amount = Column(Numeric(15, 2), default=0.00, comment="注文金額")
    standard_spec = Column(String(255), comment="規格")
    pieces_per_bundle = Column(Integer, default=0, comment="每捆件数")
    long_weight = Column(Numeric(10, 2), default=0.00, comment="长重量")
    remarks = Column(Text, comment="備考")
    label_color = Column(String(20), comment="ラベル色（白/緑）")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="作成日時")
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="最終更新日時")


class StockMaterial(Base):
    """在庫材料管理（stock_materials）"""
    __tablename__ = "stock_materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_name = Column(String(255), nullable=False, index=True, comment="材料名称")
    manufacture_no = Column(String(100), nullable=False, index=True, comment="制造编号")
    quantity = Column(Integer, nullable=False, default=0, comment="库存数量")
    log_date = Column(Date, nullable=False, index=True, comment="日志日期")
    supplier = Column(String(255), index=True, comment="供应商")
    material_quality = Column(String(100), comment="材料质量")
    is_used = Column(Boolean, nullable=False, default=False, index=True, comment="是否已使用")
    note = Column(String(255), comment="备注")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class MaterialCuttingLog(Base):
    """材料切断ログ（material_cutting_logs）— materialCutting.csv インポート先"""
    __tablename__ = "material_cutting_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item = Column(String(100), comment="項目")
    log_date = Column(Date, index=True, comment="日付")
    log_time = Column(Time, comment="時間")
    hd_no = Column(String(255), index=True, comment="HDNo")
    operator_name = Column(String(100), comment="担当者")
    material_cd = Column(String(255), index=True, comment="材料コード")
    management_code = Column(String(255), index=True, comment="管理コード")
    raw_line = Column(Text, comment="CSV原始行")
    source_file = Column(String(500), comment="取込元ファイルパス")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")


class MaterialUsageRecord(Base):
    """材料使用済テーブル（material_usage_record）
    切断工程の日次材料使用数を記録し、material_stock.planned_usage の更新ソースとなる。
    """
    __tablename__ = "material_usage_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usage_date = Column(Date, nullable=False, index=True, comment="使用日（生産日）")
    material_cd = Column(String(50), nullable=False, index=True, comment="材料CD")
    material_name = Column(String(255), nullable=False, comment="材料名")
    usage_count = Column(Numeric(10, 4), nullable=False, default=1, comment="使用数（行のusage_count、按分時は<1）")
    source = Column(String(50), nullable=False, default="cutting", index=True, comment="来源区分")
    management_codes = Column(Text, nullable=True, comment="管理コード（複数はカンマ区切り）")
    reflected = Column(Boolean, nullable=False, default=False, index=True, comment="反映済")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新日時")
