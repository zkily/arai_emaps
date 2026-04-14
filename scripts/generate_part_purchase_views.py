# -*- coding: utf-8 -*-
"""Copy material purchase Vue views to part/ with API & field renames.

部品在庫は半端サブ（part_stock_sub）を廃止済み。本スクリプトで MaterialOrderPage
から PartOrderPage を上書きすると半端タブ・転送UIが再混入するため、再生成後は手で削除し、
手入力登録は createPartStock に合わせること。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / "frontend/src/views/erp/purchase/material"
PART = ROOT / "frontend/src/views/erp/purchase/part"
PART.mkdir(parents=True, exist_ok=True)


def xform_order(text: str) -> str:
    reps = [
        ("material-order-container", "part-order-container"),
        ("@/api/material'", "@/api/part'"),
        ("@/api/materialStockCalculation", "@/api/partStockCalculation"),
        ("@/api/materialDataGeneration", "@/api/partDataGeneration"),
        ("@/api/materialStockUpdate", "@/api/partStockUpdate"),
        ("import type { MaterialQuantityUpdate } from '@/api/materialStockUpdate'", "import type { PartQuantityUpdate } from '@/api/partStockUpdate'"),
        ("MaterialQuantityUpdate", "PartQuantityUpdate"),
        ("syncMaterialStockFromMaster", "syncPartStockFromMaster"),
        ("getMaterialStockSupplierNames", "getPartStockSupplierNames"),
        ("getMaterialStockList", "getPartStockList"),
        ("updateMaterialStock", "updatePartStock"),
        ("getMaterialStockSubList", "getPartStockList"),
        ("updateMaterialStockSub", "updatePartStock"),
        ("createMaterialStockSub", "createPartStock"),
        ("deleteMaterialStockSub", "deletePartStockSub"),
        ("transferMaterialStockToSub", "transferPartStockToSub"),
        ("calculateMaterialStock", "calculatePartStock"),
        ("generateMaterialStockData", "generatePartStockData"),
        ("updateMaterialQuantities", "updatePartQuantities"),
        ("updateMaterialRemarks", "updatePartRemarks"),
        ("/api/material-order/create", "/api/part-order/create"),
        ("/api/master/materials", "/api/master/parts"),
        ("saveMaruichiOrderPdf", "saveMaruichiPartOrderPdf"),
        ("interface Material ", "interface PartMasterOption "),
        ("Material[]", "PartMasterOption[]"),
        ("Material | null", "PartMasterOption | null"),
        ("MaterialOrderItem", "PartOrderItem"),
        ("materialOptions", "partOptions"),
        ("selectedMaterial", "selectedPart"),
        ("selectedMaterialDetail", "selectedPartDetail"),
        ("loadMaterials", "loadParts"),
        ("handleMaterialChange", "handlePartChange"),
        ("materialSearchLoading", "partSearchLoading"),
        ("materialMasterSyncLoading", "partMasterSyncLoading"),
        ("mapMaterialStockRow", "mapPartStockRow"),
        ("resolveReceivingRowMaterialCd", "resolveReceivingRowPartCd"),
        ("fillMaterialData", "fillPartData"),
        ("handleOpenManualMaterialOrder", "handleOpenManualPartOrder"),
        ("material_cd: string", "part_cd: string"),
        ("material_name: string", "part_name: string"),
        ("stats.totalMaterials", "stats.totalParts"),
        ("totalMaterials", "totalParts"),
        ("'material_cd'", "'part_cd'"),
        ("prop: 'material_cd'", "prop: 'part_cd'"),
        ("prop: 'material_name'", "prop: 'part_name'"),
        ("default-sort=\"{ prop: 'material_name'", "default-sort=\"{ prop: 'part_name'"),
        ("row.material_cd", "row.part_cd"),
        ("row.material_name", "row.part_name"),
        ("transferRow.material_name", "transferRow.part_name"),
        ("transferRow.material_cd", "transferRow.part_cd"),
        ("m.material_cd", "m.part_cd"),
        ("m.material_name", "m.part_name"),
        ("material.material_cd", "material.part_cd"),
        ("material.material_name", "material.part_name"),
        ("const material = partOptions.value.find", "const part = partOptions.value.find"),
        ("selectedPart.value = { ...material }", "selectedPart.value = { ...part }"),
        ("manualOrderForm.part_name = material.part_name", "manualOrderForm.part_name = part.part_name"),
        ("fillPartData(material)", "fillPartData(part)"),
        ("manualOrderForm.material_cd", "manualOrderForm.part_cd"),
        ("v-model=\"manualOrderForm.material_cd\"", "v-model=\"manualOrderForm.part_cd\""),
        ("prop=\"material_cd\"", "prop=\"part_cd\""),
        ("selectedMaterialDetail?.material_cd", "selectedPartDetail?.part_cd"),
        ("selectedMaterialDetail.material_cd", "selectedPartDetail.part_cd"),
        ("selectedMaterialDetail?.material_name", "selectedPartDetail?.part_name"),
        ("material_cd:", "part_cd:"),
        ("material_name:", "part_name:"),
    ]
    for a, b in reps:
        text = text.replace(a, b)
    for a, b in [
        ("材料在庫管理(発注・使用)", "部品在庫管理(発注・使用)"),
        ("材料マスタ更新", "部品マスタ更新"),
        ("総材料種類数", "総部品種類数"),
        ("平均kg単価", "平均単価"),
        ("材料CD", "部品CD"),
        ("材料名", "部品名"),
        ("半端材料", "半端部品"),
        ("材料注文", "部品注文"),
        ("材料日別在庫", "部品日別在庫"),
        ("材料使用管理", "部品使用管理"),
        ("材料未使用", "部品未使用"),
        ("材料種類", "部品種類"),
        ("手入力材料注文", "手入力部品注文"),
        ("材料詳細", "部品詳細"),
        ("材料を選択", "部品を選択"),
        ("label=\"材料\"", "label=\"部品\""),
        ("材料詳細情報", "部品詳細情報"),
        ("material-detail-dialog", "part-detail-dialog"),
        ("handleOpenManualPartOrder", "handleOpenManualPartOrder"),
    ]:
        text = text.replace(a, b)
    text = text.replace(
        "const fillPartData = (part: PartMasterOption) => {\n  console.log('填充材料数据:', part)",
        "const fillPartData = (part: PartMasterOption) => {\n  console.log('填充部品データ:', part)",
    )
    text = text.replace(
        "manualOrderForm.standard_spec = part.standard_spec || ''",
        "manualOrderForm.standard_spec = (part as any).category || part.standard_spec || ''",
    )
    text = text.replace(
        "manualOrderForm.unit = part.unit || ''",
        "manualOrderForm.unit = (part as any).uom || part.unit || ''",
    )
    text = text.replace(
        "manualOrderForm.pieces_per_bundle = part.pieces_per_bundle || 0",
        "manualOrderForm.pieces_per_bundle = (part as any).pieces_per_bundle ?? 1",
    )
    text = text.replace(
        "manualOrderForm.long_weight = part.long_weight || 0",
        "manualOrderForm.long_weight = (part as any).long_weight ?? 0",
    )
    text = text.replace(
        "manualOrderForm.safety_stock = part.safety_stock || 0",
        "manualOrderForm.safety_stock = (part as any).safety_stock ?? 0",
    )
    text = text.replace(
        "manualOrderForm.max_stock = part.max_stock || 0",
        "manualOrderForm.max_stock = (part as any).max_stock ?? 0",
    )
    text = text.replace(
        "manualOrderForm.lead_time = part.lead_time || 0",
        "manualOrderForm.lead_time = (part as any).lead_time ?? 0",
    )
    return text


def xform_simple(text: str) -> str:
    text = text.replace("@/api/material'", "@/api/part'")
    text = text.replace("/api/master/materials", "/api/master/parts")
    text = text.replace("material_cd", "part_cd")
    text = text.replace("material_name", "part_name")
    text = text.replace("material_type", "category")
    text = text.replace("材料受入履歴", "部品受入履歴")
    text = text.replace("材料の受入", "部品の受入")
    text = text.replace("材料管理", "部品管理")
    text = text.replace("材料検品", "部品検品")
    text = text.replace("材料名", "部品名")
    text = text.replace("材料CD", "部品CD")
    text = text.replace("material-", "part-")
    text = text.replace("MaterialReceiving", "PartReceiving")
    return text


def main():
    order_src = MAT / "materialOrder/MaterialOrderPage.vue"
    order_dst = PART / "partOrder/PartOrderPage.vue"
    order_dst.parent.mkdir(parents=True, exist_ok=True)
    order_dst.write_text(xform_order(order_src.read_text(encoding="utf-8")), encoding="utf-8")
    print("Wrote", order_dst)

    jobs = [
        (MAT / "MaterialLayoutWrapper.vue", PART / "PartLayoutWrapper.vue", lambda t: t.replace("material-layout", "part-layout")),
        (
            MAT / "MaterialHome.vue",
            PART / "PartHome.vue",
            lambda t: t.replace("材料管理", "部品管理")
            .replace("Material Management", "Parts Management")
            .replace("/erp/purchase/material", "/erp/purchase/part")
            .replace("material-home", "part-home")
            .replace("master/material-inspection", "master/parts"),
        ),
    ]
    for src, dst, fn in jobs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(fn(src.read_text(encoding="utf-8")), encoding="utf-8")
        print("Wrote", dst)


if __name__ == "__main__":
    main()
