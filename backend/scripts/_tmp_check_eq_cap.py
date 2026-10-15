import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, or_, select, text

from app.core.database import AsyncSessionLocal
from app.modules.erp.production_equipment_capacity_api import classify_equipment
from app.modules.master.models import EquipmentEfficiency, Machine


async def main() -> None:
    async with AsyncSessionLocal() as db:
        menus = (
            await db.execute(
                text(
                    "SELECT code, name FROM menus "
                    "WHERE code LIKE 'ERP_PRODUCTION_EQ%' "
                    "OR code = 'ERP_PRODUCTION_EQUIPMENT_CAPACITY'"
                )
            )
        ).all()
        out = Path(__file__).with_name("_tmp_check_eq_cap_out.txt")
        lines = ["MENUS"]
        for code, name in menus:
            lines.append(f"  {code} {name}")
        out.write_text("\n".join(lines), encoding="utf-8")
        machines = (
            await db.execute(
                select(Machine.machine_cd, Machine.machine_name, Machine.machine_type, Machine.is_active)
            )
        ).all()
        counts: dict[str, int] = {}
        samples: dict[str, list[str]] = {}
        for cd, name, typ, active in machines:
            if active is False:
                continue
            code = classify_equipment(cd or "", name or "", typ or "")
            if not code:
                continue
            counts[code] = counts.get(code, 0) + 1
            samples.setdefault(code, []).append(f"{cd} / {name} / {typ}")
        lines.append("MACHINES " + str(counts))
        for key, rows in samples.items():
            lines.append(key)
            lines.extend(f"  {row}" for row in rows[:3])
        out.write_text("\n".join(lines), encoding="utf-8")
        print("MACHINES", counts)
        for key, rows in samples.items():
            print(key)
            for row in rows[:6]:
                print(" ", row)
        grouped = (
            await db.execute(
                select(
                    EquipmentEfficiency.machine_cd,
                    EquipmentEfficiency.machines_name,
                    func.count(EquipmentEfficiency.id),
                )
                .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status != 0))
                .group_by(EquipmentEfficiency.machine_cd, EquipmentEfficiency.machines_name)
            )
        ).all()
        eff: dict[str, int] = {}
        for cd, name, count in grouped:
            code = classify_equipment(cd or "", name or "")
            if code:
                eff[code] = eff.get(code, 0) + 1
        print("EFFICIENCY_EQUIPMENT", eff)


if __name__ == "__main__":
    asyncio.run(main())
