from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
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
for a, b in REPL:
    text = text.replace(a, b)
path.write_text(text, encoding="utf-8", newline="\n")
print("ok", path)
