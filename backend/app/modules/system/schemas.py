"""
システム管理 Pydantic スキーマ
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== Enums ==========
class UserStatus(str, Enum):
    active = "active"
    locked = "locked"
    inactive = "inactive"


class OrganizationType(str, Enum):
    company = "company"
    site = "site"
    department = "department"
    section = "section"  # 課
    line = "line"


class DataScope(str, Enum):
    self = "self"
    department = "department"
    department_below = "department_below"
    all = "all"
    custom = "custom"


# ========== Organization Schemas ==========
class OrganizationBase(BaseModel):
    code: str = Field(..., max_length=50, description="組織コード")
    name: str = Field(..., max_length=200, description="組織名")
    type: OrganizationType = Field(..., description="種類")
    parent_id: Optional[int] = Field(None, description="親組織ID")
    manager_name: Optional[str] = Field(None, max_length=100, description="責任者名")
    location: Optional[str] = Field(None, max_length=200, description="所在地")
    phone: Optional[str] = Field(None, max_length=50, description="電話番号")
    email: Optional[EmailStr] = Field(None, description="メールアドレス")
    description: Optional[str] = Field(None, description="説明")
    sort_order: int = Field(0, description="表示順序")


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    type: Optional[OrganizationType] = None
    parent_id: Optional[int] = None
    manager_name: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationTreeNode(BaseModel):
    id: int
    code: str
    name: str
    type: str
    parent_id: Optional[int]
    children: List["OrganizationTreeNode"] = []
    
    class Config:
        from_attributes = True


# ========== Role Schemas ==========
class OperationPermission(BaseModel):
    module: str = Field(..., description="モジュール名")
    can_create: bool = Field(False, description="新規作成権限")
    can_edit: bool = Field(False, description="編集権限")
    can_delete: bool = Field(False, description="削除権限")
    can_export: bool = Field(False, description="出力権限")
    can_approve: bool = Field(False, description="承認権限")


class RoleBase(BaseModel):
    name: str = Field(..., max_length=100, description="ロール名")
    description: Optional[str] = Field(None, description="説明")
    data_scope: DataScope = Field(DataScope.department, description="データ参照範囲")
    custom_departments: Optional[List[str]] = Field(None, description="カスタム部門リスト")


class RoleCreate(RoleBase):
    menu_permissions: List[int] = Field(default=[], description="メニュー権限IDリスト")
    operation_permissions: List[OperationPermission] = Field(default=[], description="操作権限リスト")


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    data_scope: Optional[DataScope] = None
    custom_departments: Optional[List[str]] = None
    menu_permissions: Optional[List[int]] = None
    operation_permissions: Optional[List[OperationPermission]] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    id: int
    is_system: bool
    is_active: bool
    user_count: int = 0
    menu_permissions: List[int] = []
    operation_permissions: List[OperationPermission] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    id: int
    name: str
    is_system: bool
    user_count: int = 0
    
    class Config:
        from_attributes = True


# ========== User Schemas (Extended) ==========
class UserBase(BaseModel):
    username: str = Field(..., max_length=50, description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    full_name: Optional[str] = Field(None, max_length=100, description="氏名")
    department_id: Optional[int] = Field(None, description="所属部門ID")
    role_id: Optional[int] = Field(None, description="ロールID")
    two_factor_enabled: bool = Field(False, description="二要素認証有効")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="パスワード")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    two_factor_enabled: Optional[bool] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    id: int
    status: UserStatus = UserStatus.active
    last_login: Optional[datetime] = None
    department_name: Optional[str] = None
    role_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: str
    department: Optional[str]
    role: str
    status: UserStatus
    two_factor: bool
    last_login: Optional[str]
    
    class Config:
        from_attributes = True


class UserSearchParams(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    status: Optional[UserStatus] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class PaginatedUserResponse(BaseModel):
    items: List[UserListResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ========== Menu Schemas ==========
class MenuBase(BaseModel):
    code: str = Field(..., max_length=50, description="メニューコード")
    name: str = Field(..., max_length=100, description="メニュー名")
    parent_id: Optional[int] = Field(None, description="親メニューID")
    path: Optional[str] = Field(None, max_length=200, description="ルートパス")
    icon: Optional[str] = Field(None, max_length=50, description="アイコン名")
    sort_order: int = Field(0, description="表示順序")


class MenuResponse(MenuBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class MenuTreeNode(BaseModel):
    id: int
    code: str
    label: str
    children: List["MenuTreeNode"] = []
    
    class Config:
        from_attributes = True


class MenuCreate(BaseModel):
    code: str = Field(..., max_length=50, description="メニューコード（一意）")
    name: str = Field(..., max_length=100, description="メニュー名")
    parent_id: Optional[int] = Field(None, description="親メニューID")
    path: Optional[str] = Field(None, max_length=200, description="ルートパス")
    icon: Optional[str] = Field(None, max_length=50, description="アイコン名")
    sort_order: int = Field(0, description="表示順序")
    is_active: bool = Field(True, description="有効フラグ")


class MenuUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[int] = None
    path: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MenuSyncItem(BaseModel):
    """ルート定義から同期する1件のメニュー"""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    path: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)
    parent_code: Optional[str] = Field(None, max_length=50, description="親メニューのcode")
    sort_order: int = 0


class MenuSyncRequest(BaseModel):
    """ルート定義一括同期リクエスト"""
    items: List[MenuSyncItem] = Field(..., description="メニュー定義リスト")


# ========== Password Reset ==========
class PasswordResetRequest(BaseModel):
    user_id: int


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserPasswordSet(BaseModel):
    """管理者によるユーザーパスワード直接設定"""
    new_password: str = Field(..., min_length=8, description="新しいパスワード")
