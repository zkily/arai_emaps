"""操作権限 FastAPI Depends（モジュール別 CRUD チェック）"""
from typing import Literal

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.models import User
from app.core.operation_modules import (
    OPERATION_MODULE_APS,
    OPERATION_MODULE_COST,
    OPERATION_MODULE_INVENTORY,
    OPERATION_MODULE_MASTER,
    OPERATION_MODULE_MES,
    OPERATION_MODULE_PURCHASE,
    OPERATION_MODULE_QUALITY,
    OPERATION_MODULE_SALES,
)

OperationAction = Literal["create", "edit", "delete", "export", "approve"]

_FIELD_MAP: dict[OperationAction, str] = {
    "create": "can_create",
    "edit": "can_edit",
    "delete": "can_delete",
    "export": "can_export",
    "approve": "can_approve",
}


async def assert_operation_permission(
    db: AsyncSession,
    user: User,
    module: str,
    action: OperationAction,
) -> None:
    # auth.api → system → settings → data_management_io → master → operation_deps の循環を避ける
    from app.modules.auth.api import get_user_operation_permissions

    role = user.role if user.role else "user"
    if role == "admin":
        return

    perms_list = await get_user_operation_permissions(db, user)
    mod_perm = next((p for p in perms_list if p["module"] == module), None)
    field = _FIELD_MAP[action]
    if not mod_perm or not mod_perm.get(field):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="操作権限がありません",
        )


def require_operation(module: str, action: OperationAction):
    from app.modules.auth.api import verify_token_and_get_user

    async def dependency(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ) -> User:
        await assert_operation_permission(db, current_user, module, action)
        return current_user

    return dependency


def require_master_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_MASTER, action)


def require_mes_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_MES, action)


def require_aps_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_APS, action)


def require_sales_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_SALES, action)


def require_purchase_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_PURCHASE, action)


def require_inventory_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_INVENTORY, action)


def require_cost_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_COST, action)


def require_quality_operation(action: OperationAction):
    return require_operation(OPERATION_MODULE_QUALITY, action)
