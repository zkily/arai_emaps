"""操作権限モジュール名（RolePermission.vue / login payload と同期）

system パッケージ __init__ を経由しないよう core に配置（循環 import 回避）。
"""

OPERATION_MODULE_SALES = "販売管理"
OPERATION_MODULE_PURCHASE = "購買管理"
OPERATION_MODULE_INVENTORY = "在庫管理"
OPERATION_MODULE_COST = "原価・会計"
OPERATION_MODULE_QUALITY = "品質管理"
OPERATION_MODULE_MASTER = "マスタ管理"
OPERATION_MODULE_MES = "製造実行"
OPERATION_MODULE_APS = "生産計画"

OPERATION_MODULES: tuple[str, ...] = (
    "販売管理",
    "購買管理",
    "在庫管理",
    "原価・会計",
    "経理・原価・人事",
    "生産計画",
    "製造実行",
    "品質管理",
    "マスタ管理",
    "システム管理",
)
