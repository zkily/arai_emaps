"""工場レイアウト（平面図オブジェクトと状態）"""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class FactoryLayout(Base):
    """工場レイアウト"""

    __tablename__ = "factory_layouts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    canvas_width = Column(Integer, nullable=False, default=1600)
    canvas_height = Column(Integer, nullable=False, default=900)
    grid_size = Column(Integer, nullable=False, default=20)
    kind = Column(String(20), nullable=False, default="workshop")
    parent_id = Column(
        Integer, ForeignKey("factory_layouts.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class FactoryLayoutObject(Base):
    """レイアウト上の設備・通路・材料置き場"""

    __tablename__ = "factory_layout_objects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    layout_id = Column(
        Integer, ForeignKey("factory_layouts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    object_type = Column(String(20), nullable=False)
    x = Column(Integer, nullable=False, default=0)
    y = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=80)
    height = Column(Integer, nullable=False, default=60)
    label = Column(String(100), nullable=False, default="")
    ref_cd = Column(String(100), nullable=True)
    z_index = Column(Integer, nullable=False, default=0)
    rotation = Column(Integer, nullable=False, default=0)
    locked = Column(Boolean, nullable=False, default=False)
    group_key = Column(String(36), nullable=True)
    fill_color = Column(String(7), nullable=True)
    border_color = Column(String(7), nullable=True)
    opacity = Column(Integer, nullable=False, default=100)
    child_layout_id = Column(
        Integer, ForeignKey("factory_layouts.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class FactoryLayoutStatus(Base):
    """オブジェクト状態。source=mock は画面から更新、plc は外部取込用。"""

    __tablename__ = "factory_layout_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    object_id = Column(
        Integer,
        ForeignKey("factory_layout_objects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status = Column(String(30), nullable=False)
    message = Column(String(500), nullable=True)
    payload = Column(JSON, nullable=True)
    source = Column(String(20), nullable=False, default="mock")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
