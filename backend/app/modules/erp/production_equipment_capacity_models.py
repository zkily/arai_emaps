"""生産設備能力（工程別・設備別の生産能力調査）"""

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class ProductionEquipmentCapacity(Base):
    """設備の稼働条件（定時間・直・残業・稼働日数）"""

    __tablename__ = "production_equipment_capacity"
    __table_args__ = (UniqueConstraint("process_cd", "machine_cd", name="uk_pec_process_machine"),)

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    process_cd = Column(
        String(32), nullable=False, comment="工程 cutting/chamfering/forming/welding"
    )
    machine_cd = Column(String(50), nullable=False, comment="設備コード")
    machine_name = Column(String(100), nullable=False, comment="設備名")
    partner_name = Column(String(100), nullable=True, comment="パートナー名")
    vehicle_model = Column(String(100), nullable=True, comment="対象車種など")
    regular_hours = Column(Numeric(6, 2), nullable=False, default=7.6, comment="定時間 h/直")
    shift_count = Column(Numeric(4, 1), nullable=False, default=2, comment="直数")
    overtime_hours = Column(Numeric(6, 2), nullable=False, default=0, comment="残業 h/直")
    working_days = Column(Numeric(5, 1), nullable=False, default=22, comment="月間稼働日数")
    note = Column(Text, nullable=True, comment="備考")
    sort_order = Column(Integer, nullable=False, default=0, comment="表示順")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )


class ProductionEquipmentCapacityItem(Base):
    """設備に載せる品目と能力調査の入力値"""

    __tablename__ = "production_equipment_capacity_item"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    capacity_id = Column(Integer, nullable=False, index=True, comment="設備能力ID")
    line_no = Column(Integer, nullable=False, default=0, comment="行番")
    part_no = Column(String(50), nullable=True, comment="部品番号")
    part_name = Column(String(100), nullable=True, comment="部品名")
    customer_name = Column(String(100), nullable=True, comment="取引先名")
    survey_target = Column(String(100), nullable=True, comment="調査対象")
    monthly_qty = Column(Numeric(14, 2), nullable=False, default=0, comment="設定数 個/月")
    qty_days = Column(Numeric(6, 2), nullable=False, default=0, comment="設定数に対する稼働日数")
    ct_sec = Column(Numeric(10, 3), nullable=False, default=0, comment="CT 秒/個")
    availability_rate = Column(Numeric(6, 4), nullable=False, default=0.9, comment="可動率 0-1")
    first_pass_rate = Column(Numeric(6, 4), nullable=False, default=0.99, comment="直行率 0-1")
    cavity_count = Column(Numeric(8, 2), nullable=False, default=1, comment="取り数")
    setup_hours = Column(Numeric(8, 3), nullable=False, default=0, comment="段取り h/回")
    actual_days = Column(Numeric(6, 2), nullable=False, default=0, comment="実生産日数")
    reference_rate = Column(Numeric(10, 2), nullable=True, comment="参照能率 本/H")
    current_rate = Column(Numeric(10, 2), nullable=True, comment="現在能率 本/H")
    takt1_date = Column(Date, nullable=True, comment="タクト1 日付")
    takt1_ct = Column(Numeric(10, 3), nullable=True, comment="タクト1 実測CT秒")
    takt1_inspect = Column(String(8), nullable=True, comment="タクト1 検査")
    takt1_prep = Column(String(8), nullable=True, comment="タクト1 準備")
    takt1_overall = Column(String(8), nullable=True, comment="タクト1 総合")
    takt2_date = Column(Date, nullable=True, comment="タクト2 日付")
    takt2_ct = Column(Numeric(10, 3), nullable=True, comment="タクト2 実測CT秒")
    takt2_inspect = Column(String(8), nullable=True, comment="タクト2 検査")
    takt2_prep = Column(String(8), nullable=True, comment="タクト2 準備")
    takt2_overall = Column(String(8), nullable=True, comment="タクト2 総合")
    remarks = Column(String(255), nullable=True, comment="備考")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )
