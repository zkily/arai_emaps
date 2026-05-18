"""One-off: copy inspection MES module to welding with renames."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "views" / "mes" / "actualDataCollection"
INS = ROOT / "inspection"
WLD = ROOT / "welding"

PAIRS = [
    ("useInspectionMesCollection.ts", "useWeldingMesCollection.ts"),
    ("inspectionActualPersist.ts", "weldingActualPersist.ts"),
    ("inspectionActualOfflineSync.ts", "weldingActualOfflineSync.ts"),
    ("inspectionActualConfig.ts", "weldingActualConfig.ts"),
    ("mesClientInstance.ts", "mesClientInstance.ts"),
    ("InspectionActualDataCollection.vue", "WeldingActualDataCollection.vue"),
]

REPL = [
    ("InspectionMgmtRow", "WeldingMgmtRow"),
    ("useInspectionMesCollection", "useWeldingMesCollection"),
    ("InspectionActual", "WeldingActual"),
    ("inspectionActual", "weldingActual"),
    ("INSPECTION_ACTUAL", "WELDING_ACTUAL"),
    ("INSPECTION_DEFECT", "WELDING_DEFECT"),
    ("inspection_management", "welding_management"),
    ("inspection-management", "welding-management"),
    ("inspectionManagement", "weldingManagement"),
    ("InspectionManagement", "WeldingManagement"),
    ("@/api/inspectionManagement", "@/api/weldingManagement"),
    ("mesInspectionActual", "mesWeldingActual"),
    ("smart_emap_mes_inspection", "smart_emap_mes_welding"),
    ("mes-insp-", "mes-weld-"),
    ("INSPECTION_PRODUCT", "WELDING_PRODUCT"),
    ("inspectorUserId", "operatorUserId"),
    ("inspectors", "operators"),
    ("loadingInspectors", "loadingOperators"),
    ("inspectorNameById", "operatorNameById"),
    ("isInspectorOptionDisabled", "isOperatorOptionDisabled"),
    ("inspectorOptionLabel", "operatorOptionLabel"),
    ("inspectorLabel", "operatorLabel"),
    ("rowInspectorId", "rowOperatorId"),
    ("mes_inspector_user_id", "mes_operator_user_id"),
    ("findOpenRowForInspectorProduct", "findOpenRowForInspectorProduct_TEMP"),
    ("findInProgressRowForInspector", "findInProgressRowForOperator"),
    ("findOtherActiveRowForInspector", "findOtherActiveRowForOperator"),
    ("bindContextFromInspector", "bindContextFromOperator"),
    ("suppressInspectorUserWatch", "suppressOperatorUserWatch"),
    ("findOpenRowForInspectorProduct_TEMP", "findOpenRowForOperatorProduct"),
    ("compareInspectionMgmtRows", "compareWeldingMgmtRows"),
    ("copyInspectionRowFromServer", "copyWeldingRowFromServer"),
    ("createInspectionManagement", "createWeldingManagement"),
    ("fetchInspectionManagementList", "fetchWeldingManagementList"),
    ("patchInspectionManagement", "patchWeldingManagement"),
    ("PatchInspectionManagementBody", "PatchWeldingManagementBody"),
    ("loadInspectors", "loadOperators"),
    ("InspectionActualDataCollection", "WeldingActualDataCollection"),
    ("KT09", "KT07"),
    ("[inspectionActual]", "[weldingActual]"),
]

WLD.mkdir(parents=True, exist_ok=True)
for src_name, dst_name in PAIRS:
    text = (INS / src_name).read_text(encoding="utf-8")
    for a, b in REPL:
        text = text.replace(a, b)
    (WLD / dst_name).write_text(text, encoding="utf-8", newline="\n")
    print("wrote", dst_name)

# remove bad file from broken copy
bad = WLD / "useweldingMesCollection.ts"
if bad.exists():
    bad.unlink()
    print("removed", bad.name)
