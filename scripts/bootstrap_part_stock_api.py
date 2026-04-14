# 注意: 現在の part/stock_api は半端サブを含まない。再実行で material から上書きしないこと。
"""One-off: generate backend/app/modules/part/stock_api.py from material/stock_api.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "backend/app/modules/material/stock_api.py"
dst = ROOT / "backend/app/modules/part/stock_api.py"
dst.parent.mkdir(parents=True, exist_ok=True)
t = src.read_text(encoding="utf-8")
pairs = [
    ("材料在庫 API", "部品在庫 API"),
    ("material_stock     → /api/material/stock", "part_stock     → /api/part/stock"),
    ("material_stock_sub → /api/material/stock/sub", "part_stock_sub → /api/part/stock/sub"),
    ("from app.modules.master.models import Material, Supplier", "from app.modules.master.models import PartMaster, Supplier"),
    ("from app.modules.material.models import MaterialStock, MaterialStockSub", "from app.modules.part.models import PartStock, PartStockSub"),
    ("from app.modules.material.schemas import (", "from app.modules.part.schemas import ("),
    ("MaterialStockCreate", "PartStockCreate"),
    ("MaterialStockUpdate", "PartStockUpdate"),
    ("MaterialStockResponse", "PartStockResponse"),
    ("MaterialStockSubCreate", "PartStockSubCreate"),
    ("MaterialStockSubUpdate", "PartStockSubUpdate"),
    ("MaterialStockSubResponse", "PartStockSubResponse"),
    ("MaterialStock", "PartStock"),
    ("MaterialStockSub", "PartStockSub"),
    ("from app.modules.master.models import PartMaster, Supplier", "from app.modules.master.models import PartMaster, Supplier"),
]
# Material -> PartMaster only after MaterialStock already renamed
t = t.replace("from app.modules.master.models import Material, Supplier", "from app.modules.master.models import PartMaster, Supplier")
t = t.replace("from app.modules.material.models import MaterialStock, MaterialStockSub", "from app.modules.part.models import PartStock, PartStockSub")
t = t.replace("from app.modules.material.schemas import (", "from app.modules.part.schemas import (")
for a, b in [
    ("MaterialStockCreate", "PartStockCreate"),
    ("MaterialStockUpdate", "PartStockUpdate"),
    ("MaterialStockResponse", "PartStockResponse"),
    ("MaterialStockSubCreate", "PartStockSubCreate"),
    ("MaterialStockSubUpdate", "PartStockSubUpdate"),
    ("MaterialStockSubResponse", "PartStockSubResponse"),
]:
    t = t.replace(a, b)
t = t.replace("MaterialStock", "PartStock")
t = t.replace("MaterialStockSub", "PartStockSub")
t = t.replace("Material", "PartMaster")
t = t.replace("list_material_stocks", "list_part_stocks")
t = t.replace("get_latest_stocks", "get_latest_part_stocks")
t = t.replace("calculate_material_stock", "calculate_part_stock")
t = t.replace("get_stock_summary", "get_part_stock_summary")
t = t.replace("list_distinct_material_stock_supplier_names", "list_distinct_part_stock_supplier_names")
t = t.replace("sync_material_master_to_stock", "sync_part_master_to_stock")
t = t.replace("create_material_stock", "create_part_stock")
t = t.replace("update_material_stock", "update_part_stock")
t = t.replace("delete_material_stock", "delete_part_stock")
t = t.replace("async def transfer_to_sub", "async def transfer_part_to_sub")
t = t.replace("list_stock_sub", "list_part_stock_sub")
t = t.replace("create_stock_sub", "create_part_stock_sub")
t = t.replace("update_stock_sub", "update_part_stock_sub")
t = t.replace("delete_stock_sub", "delete_part_stock_sub")
t = t.replace("save_maruichi_order_pdf", "save_maruichi_part_order_pdf")
t = t.replace("material_stock", "part_stock")
t = t.replace("材料在庫", "部品在庫")
t = t.replace("材料マスタ", "部品マスタ")
t = t.replace("materials.status", "parts.status")
t = t.replace("material_cd", "part_cd")
t = t.replace("material_name", "part_name")
t = t.replace("by_material", "by_part")
t = t.replace("material_cd ごと", "part_cd ごと")
t = t.replace("各材料", "各部品")
t = t.replace("半端（part_stock_sub）", "半端（part_stock_sub）")
# Fix accidental PartMasterStock -> PartStock (if any)
t = t.replace("PartMasterStock", "PartStock")
t = t.replace("PartMasterStockSub", "PartStockSub")
dst.write_text(t, encoding="utf-8")
print("OK", dst)
