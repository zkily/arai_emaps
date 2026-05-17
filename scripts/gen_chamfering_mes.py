#!/usr/bin/env python3
"""Generate chamfering MES frontend files from cutting counterparts."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUT = ROOT / "frontend/src/views/mes/actualDataCollection/cutting"
CHAM = ROOT / "frontend/src/views/mes/actualDataCollection/chamfering"
API_CUT = ROOT / "frontend/src/api/cuttingManagement.ts"
API_CHAM = ROOT / "frontend/src/api/chamferingManagement.ts"
LOCALES = ["zh.ts", "ja.ts", "en.ts", "vi.ts"]

REPLACEMENTS = [
    ("CuttingActualDataCollection", "ChamferingActualDataCollection"),
    ("cuttingManagement", "chamferingManagement"),
    ("CuttingManagement", "ChamferingManagement"),
    ("CuttingMgmt", "ChamferingMgmt"),
    ("cutting_machine", "chamfering_machine"),
    ("cuttingMachine", "chamferingMachine"),
    ("fetchCuttingManagementList", "fetchChamferingManagementList"),
    ("patchCuttingManagement", "patchChamferingManagement"),
    ("reorderCuttingManagement", "reorderChamferingManagement"),
    ("splitCuttingManagementToNextDay", "splitChamferingManagementToNextDay"),
    ("cuttingActualPersist", "chamferingActualPersist"),
    ("cuttingActualOfflineSync", "chamferingActualOfflineSync"),
    ("loadCuttingActualPersist", "loadChamferingActualPersist"),
    ("saveCuttingActualPersist", "saveChamferingActualPersist"),
    ("CuttingActualPersist", "ChamferingActualPersist"),
    ("CUTTING_ACTUAL", "CHAMFERING_ACTUAL"),
    ("smart_emap_mes_cutting", "smart_emap_mes_chamfering"),
    ("[cuttingActual]", "[chamferingActual]"),
    ("mesCuttingActual", "mesChamferingActual"),
    ("cutting-management", "chamfering-management"),
    ("CuttingPlanningMachine", "ChamferingMesMachine"),
    ("fetchCuttingPlanningMachines", "fetchChamferingMesMachines"),
    ("isCuttingRowConfirmed", "isChamferingRowConfirmed"),
    ("cuttingMachineHasGaichu", "chamferingMachineHasGaichu"),
    ("PatchCuttingManagementBody", "PatchChamferingManagementBody"),
    ("ReorderCuttingManagementBody", "ReorderChamferingManagementBody"),
    ("切断", "面取"),
    ("cutting_management", "chamfering_management"),
    ("切断指示", "面取指示"),
    ("切断実績", "面取実績"),
    ("切断機", "面取機"),
    ("切断设备", "面取设备"),
]

LOCALE_TEXT = [
    ("切断", "面取"),
    ("cutting_management", "chamfering_management"),
    ("切断指示", "面取指示"),
    ("切断实绩", "面取实绩"),
    ("切断设备", "面取设备"),
    ("切断机", "面取机"),
    ("Cutting", "Chamfering"),
    ("cutting", "chamfering"),
]


def apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def fix_reorder_calls(text: str) -> str:
    """Add production_day to reorderChamferingManagement calls."""

    def repl(m: re.Match[str]) -> str:
        block = m.group(0)
        if "production_day:" in block:
            return block
        insert = "production_day: (productionDay.value ?? '').trim().slice(0, 10), "
        return block.replace("{ ", "{ " + insert, 1)

    return re.sub(
        r"reorderChamferingManagement\(\s*\{[^}]+\}\s*\)",
        repl,
        text,
        flags=re.DOTALL,
    )


def gen_api():
    text = API_CUT.read_text(encoding="utf-8")
    text = apply_replacements(text)
    text = text.replace(
        "/**\n * 面取指示 cutting_management（/api/plan/chamfering-management/*）\n */",
        "/**\n * 面取指示 chamfering_management（/api/plan/chamfering-management/*）\n */",
    )
    text = re.sub(
        r"export interface ReorderChamferingManagementBody \{[^}]+\}",
        """export interface ReorderChamferingManagementBody {
  chamfering_machine: string
  production_day: string
  ordered_ids: number[]
}""",
        text,
        count=1,
    )
    machine_fetch = """

import { getMachineList } from '@/api/master/machineMaster'
import type { MachineItem } from '@/types/master'

export interface ChamferingMesMachine {
  id: number
  machine_cd: string
  machine_name: string
}

/** 面取機一覧（設備マスタ・名称に「面取」を含む） */
export async function fetchChamferingMesMachines(): Promise<ChamferingMesMachine[]> {
  const result = await getMachineList({ keyword: '面取', pageSize: 500 })
  const list: MachineItem[] = result.data?.list ?? result.list ?? []
  return list
    .filter((r) => r.machine_name && String(r.machine_name).includes('面取'))
    .map((r) => ({
      id: Number(r.id),
      machine_cd: String(r.machine_cd ?? ''),
      machine_name: String(r.machine_name ?? ''),
    }))
    .filter((m) => Number.isFinite(m.id) && m.id > 0)
}
"""
    if "fetchChamferingMesMachines" not in text:
        text = text.rstrip() + machine_fetch
    API_CHAM.write_text(text, encoding="utf-8")


def copy_ts(name: str):
    src = CUT / name
    dst = CHAM / name.replace("cutting", "chamfering")
    text = apply_replacements(src.read_text(encoding="utf-8"))
    if name.endswith("OfflineSync.ts"):
        text = text.replace("PatchChamferingManagementBody", "PatchChamferingManagementBody")
    dst.write_text(text, encoding="utf-8")


def gen_vue():
    src = CUT / "CuttingActualDataCollection.vue"
    dst = CHAM / "ChamferingActualDataCollection.vue"
    text = apply_replacements(src.read_text(encoding="utf-8"))
    text = text.replace("@/api/cuttingPlanning", "@/api/chamferingManagement")
    text = fix_reorder_calls(text)
    dst.write_text(text, encoding="utf-8")


def copy_vue_components():
    for name in ["MesBarcodeScanDialog.vue", "ScanRegisteredHint.vue"]:
        src = CUT / name
        if src.exists():
            shutil.copy2(src, CHAM / name)


def gen_locales():
    for loc in LOCALES:
        path = ROOT / "frontend/src/locales" / loc
        content = path.read_text(encoding="utf-8")
        if "mesChamferingActual:" in content:
            continue
        m = re.search(
            r"(\s+mesCuttingActual:\s*\{[\s\S]*?\n\s+\},)\n",
            content,
        )
        if not m:
            print(f"skip locale {loc}: mesCuttingActual block not found")
            continue
        block = m.group(1).replace("mesCuttingActual", "mesChamferingActual")
        for old, new in LOCALE_TEXT:
            block = block.replace(old, new)
        content = content[: m.end()] + "\n" + block + content[m.end() :]
        path.write_text(content, encoding="utf-8")


def main():
    CHAM.mkdir(parents=True, exist_ok=True)
    gen_api()
    copy_ts("cuttingActualPersist.ts")
    copy_ts("cuttingActualOfflineSync.ts")
    copy_vue_components()
    gen_vue()
    gen_locales()
    print("done:", CHAM)


if __name__ == "__main__":
    main()
