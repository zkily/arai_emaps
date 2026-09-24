"""オブジェクト状態の読み書き。PLC 接続時は同じ表を source=plc で更新する。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.factory_layout.models import FactoryLayoutObject, FactoryLayoutStatus
from app.modules.factory_layout.schemas import ObjectStatusOut

ALLOWED_STATUS: dict[str, set[str]] = {
    "machine": {"running", "idle", "alarm", "maintenance", "offline"},
    "aisle": {"open", "blocked"},
    "material_zone": {"stocked", "empty", "low"},
    "workshop": set(),
}

DEFAULT_STATUS: dict[str, str] = {
    "machine": "idle",
    "aisle": "open",
    "material_zone": "empty",
    "workshop": "idle",
}


class StatusRejected(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class MockStatusProvider:
    """factory_layout_status を読む。行がなければ種別ごとの初期状態を返す。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def statuses_for(self, objects: list[FactoryLayoutObject]) -> dict[str, ObjectStatusOut]:
        if not objects:
            return {}
        ids = [obj.id for obj in objects]
        result = await self.db.execute(
            select(FactoryLayoutStatus).where(FactoryLayoutStatus.object_id.in_(ids))
        )
        rows = {row.object_id: row for row in result.scalars().all()}
        out: dict[str, ObjectStatusOut] = {}
        for obj in objects:
            row = rows.get(obj.id)
            if row is None:
                out[str(obj.id)] = ObjectStatusOut(
                    status=DEFAULT_STATUS.get(obj.object_type, "idle"),
                    message="",
                    updated_at=None,
                    source="mock",
                    payload=None,
                )
                continue
            payload = row.payload if isinstance(row.payload, dict) else None
            out[str(obj.id)] = ObjectStatusOut(
                status=row.status,
                message=row.message or "",
                updated_at=row.updated_at,
                source=row.source or "mock",
                payload=payload,
            )
        return out

    async def set_mock_status(
        self, obj: FactoryLayoutObject, status: str, message: str
    ) -> FactoryLayoutStatus:
        allowed = ALLOWED_STATUS.get(obj.object_type)
        if allowed is None or (allowed and status not in allowed):
            raise StatusRejected(422, "このオブジェクト種別では使えないステータスです")
        result = await self.db.execute(
            select(FactoryLayoutStatus).where(FactoryLayoutStatus.object_id == obj.id)
        )
        row = result.scalar_one_or_none()
        if row is not None and (row.source or "mock") != "mock":
            raise StatusRejected(409, "模擬以外のステータスは更新できません")
        text = (message or "").strip()
        if row is None:
            row = FactoryLayoutStatus(
                object_id=obj.id,
                status=status,
                message=text,
                source="mock",
                payload=None,
            )
            self.db.add(row)
        else:
            row.status = status
            row.message = text
            row.source = "mock"
        await self.db.commit()
        await self.db.refresh(row)
        return row
