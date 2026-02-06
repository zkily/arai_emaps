"""
システム管理モデル
組織、ロール、権限、メニュー
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Organization(Base):
    """組織テーブルモデル（会社、拠点、部門、ライン）"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True, comment="組織ID（主キー）")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="組織コード（一意）")
    name = Column(String(200), nullable=False, comment="組織名")
    type = Column(String(20), nullable=False, comment="種類（company:会社, site:拠点, department:部門, section:課, line:ライン）")
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, comment="親組織ID")
    manager_name = Column(String(100), nullable=True, comment="責任者名")
    location = Column(String(200), nullable=True, comment="所在地")
    phone = Column(String(50), nullable=True, comment="電話番号")
    email = Column(String(100), nullable=True, comment="メールアドレス")
    description = Column(Text, nullable=True, comment="説明")
    sort_order = Column(Integer, default=0, comment="表示順序")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    # リレーション
    parent = relationship("Organization", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, code='{self.code}', name='{self.name}', type='{self.type}')>"


class Role(Base):
    """ロールテーブルモデル"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, comment="ロールID（主キー）")
    name = Column(String(100), unique=True, nullable=False, comment="ロール名")
    description = Column(Text, nullable=True, comment="説明")
    is_system = Column(Boolean, default=False, nullable=False, comment="システムロールフラグ（TRUE:削除不可）")
    data_scope = Column(String(20), default="department", comment="データ参照範囲（self/department/department_below/all/custom）")
    custom_departments = Column(JSON, nullable=True, comment="カスタム部門リスト（data_scope=customの場合）")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    # リレーション
    menu_permissions = relationship("RoleMenuPermission", back_populates="role", cascade="all, delete-orphan")
    operation_permissions = relationship("RoleOperationPermission", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', is_system={self.is_system})>"


class Menu(Base):
    """メニューテーブルモデル"""
    __tablename__ = "menus"
    
    id = Column(Integer, primary_key=True, index=True, comment="メニューID（主キー）")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="メニューコード")
    name = Column(String(100), nullable=False, comment="メニュー名")
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True, comment="親メニューID")
    path = Column(String(200), nullable=True, comment="ルートパス")
    icon = Column(String(50), nullable=True, comment="アイコン名")
    sort_order = Column(Integer, default=0, comment="表示順序")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    # リレーション
    parent = relationship("Menu", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<Menu(id={self.id}, code='{self.code}', name='{self.name}')>"


class RoleMenuPermission(Base):
    """ロール・メニュー権限関連テーブル"""
    __tablename__ = "role_menu_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="ロールID")
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, comment="メニューID")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    # リレーション
    role = relationship("Role", back_populates="menu_permissions")
    menu = relationship("Menu")


class RoleOperationPermission(Base):
    """ロール・操作権限テーブル"""
    __tablename__ = "role_operation_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="ロールID")
    module = Column(String(100), nullable=False, comment="モジュール名")
    can_create = Column(Boolean, default=False, comment="新規作成権限")
    can_edit = Column(Boolean, default=False, comment="編集権限")
    can_delete = Column(Boolean, default=False, comment="削除権限")
    can_export = Column(Boolean, default=False, comment="出力権限")
    can_approve = Column(Boolean, default=False, comment="承認権限")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    # リレーション
    role = relationship("Role", back_populates="operation_permissions")


class UserRole(Base):
    """ユーザー・ロール関連テーブル"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="ユーザーID")
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="ロールID")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
