"""
APS Pydantic スキーマ（リクエスト / レスポンス）
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, time, datetime


# ──────────────────── Production Lines ────────────────────

class ProductionLineOut(BaseModel):
    id: int
    line_code: str
    line_name: str = Field(default="", description="設備名（machines.machine_name）")
    default_work_hours: float
    is_active: bool

    class Config:
        from_attributes = True


class LineReplanAnchorOut(BaseModel):
    """設備別に保存した再計算アンカー日（未設定時 anchor_date は null）"""
    line_id: int
    line_code: str
    line_name: str = ""
    anchor_date: Optional[str] = None


class LineReplanAnchorItemBody(BaseModel):
    line_id: int
    anchor_date: Optional[str] = None


class LineReplanAnchorsBatchBody(BaseModel):
    items: List[LineReplanAnchorItemBody]


class EquipmentEfficiencyProductOut(BaseModel):
    """equipment_efficiency 1 行（APS 品名プルダウン用）"""
    id: int
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    efficiency_rate: float = 0.0
    step_time: Optional[int] = None
    lot_size: Optional[int] = Field(
        default=None,
        description="製品マスタ products.lot_size（product_cd 一致時）",
    )


# ──────────────────── Line Capacities ────────────────────

class LineCapacityItem(BaseModel):
    line_id: int
    work_date: date
    available_hours: float
    note: Optional[str] = None


class LineCapacityBatchBody(BaseModel):
    items: List[LineCapacityItem]


class LineCapacityOut(BaseModel):
    id: int
    line_id: int
    work_date: date
    available_hours: float
    note: Optional[str] = None

    class Config:
        from_attributes = True


# ──────────────────── Line Capacity Time Slots ────────────────────

class TimeSlotItem(BaseModel):
    start_time: time
    end_time: time
    sort_order: int = 0
    is_rest: bool = False


class DaySlotsBody(BaseModel):
    line_id: int
    work_date: date
    slots: List[TimeSlotItem]


class TimeSlotOut(BaseModel):
    id: int
    start_time: time
    end_time: time
    sort_order: int
    is_rest: bool = False

    class Config:
        from_attributes = True


class DaySlotsOut(BaseModel):
    work_date: date
    available_hours: float
    slots: List[TimeSlotOut]


class DaySlotsBatchBody(BaseModel):
    line_id: int
    days: List[DaySlotsBody]


# ──────────────────── Line Product Standard ────────────────────

class LineProductStandardBody(BaseModel):
    line_id: int
    product_cd: str
    std_qty_per_hour: float
    setup_time_min: int = 0
    efficiency_pct: float = 100.0


class LineProductStandardOut(BaseModel):
    id: int
    line_id: int
    product_cd: str
    std_qty_per_hour: float
    setup_time_min: int
    efficiency_pct: float

    class Config:
        from_attributes = True


# ──────────────────── Production Schedules ────────────────────

class ScheduleCreateBody(BaseModel):
    line_id: int
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: str
    product_cd: Optional[str] = None
    material_shortage: bool = False
    lot_qty: int = 0
    planned_batch_count: Optional[int] = None
    lot_size_snapshot: Optional[int] = None
    planned_process_qty: Optional[int] = None
    prev_month_carryover: int = 0
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    forced_start_date: Optional[date] = None
    setup_time: int = 0
    efficiency: float = 100.0
    daily_capacity: int
    start_date: Optional[date] = None
    run_immediately: bool = True


class ScheduleUpdateBody(BaseModel):
    line_id: Optional[int] = None
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: Optional[str] = None
    product_cd: Optional[str] = None
    material_shortage: Optional[bool] = None
    lot_qty: Optional[int] = None
    planned_batch_count: Optional[int] = None
    lot_size_snapshot: Optional[int] = None
    planned_process_qty: Optional[int] = None
    prev_month_carryover: Optional[int] = None
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    forced_start_date: Optional[date] = None
    setup_time: Optional[int] = None
    efficiency: Optional[float] = None
    daily_capacity: Optional[int] = None
    start_date: Optional[date] = None
    # 部分更新時は既定でエンジンを走らせない（ライン串接は replan-sequence で行う）
    run_immediately: bool = False


class ScheduleDailyPlanUpdateBody(BaseModel):
    schedule_date: date
    planned_qty: int = Field(ge=0, description="日別計画数（0 以上の整数）")


class ScheduleAppendPlannedBody(BaseModel):
    additional_qty: int = Field(gt=0, description="既存計画の末尾に追記する本数")


class ScheduleOut(BaseModel):
    id: int
    line_id: int
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: str
    product_cd: Optional[str] = None
    material_shortage: bool
    lot_qty: int
    planned_batch_count: int = 0
    lot_size_snapshot: int = 0
    planned_process_qty: int
    prev_month_carryover: int
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    forced_start_date: Optional[date] = None
    setup_time: int
    efficiency: float
    daily_capacity: int
    planned_output_qty: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    completion_rate: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


class ScheduleWithLineOut(ScheduleOut):
    """GET /schedules：設備コード・名称を付与した工単行"""
    line_code: str = ""
    line_name: str = ""


# ──────────────────── Scheduling Grid ────────────────────


class DailyUpstreamTintSeg(BaseModel):
    """APS ロット上流状態別の按分本数（マトリクス日セル背景用）。合計は当日 daily と一致させる。"""

    in_cutting: int = Field(0, description="cutting_management 登録済ロット由来")
    in_instruction: int = Field(0, description="instruction_plans のみ（切断未移行）")
    only_planned: int = Field(0, description="上流未同期・計画のみ")


class DailyManagementCodeAlloc(BaseModel):
    """日セル内の APS ロット按分に対応する管理コード。"""

    management_code: str
    aps_batch_plan_id: Optional[int] = None
    allocated_qty: int = Field(0, description="当日セル按分本数")


class ScheduleGridRow(BaseModel):
    """一行 = 一個工単 + 展平された日別 planned_qty"""
    id: int
    order_no: Optional[int] = None
    item_name: str
    material_shortage: bool
    lot_qty: int
    planned_batch_count: int = 0
    lot_size_snapshot: int = 0
    planned_process_qty: int
    prev_month_carryover: int
    due_date: Optional[str] = None
    material_date: Optional[str] = None
    setup_time: int
    efficiency: float
    efficiency_rate: Optional[float] = None
    daily_capacity: int
    planned_output_qty: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    completion_rate: Optional[float] = None
    status: str
    daily: Dict[str, int] = Field(default_factory=dict)
    actual_daily: Dict[str, int] = Field(default_factory=dict)
    defect_daily: Dict[str, int] = Field(default_factory=dict)
    upstream_defect_daily: Dict[str, int] = Field(default_factory=dict)
    remaining_daily: Dict[str, int] = Field(default_factory=dict)
    defect_qty_sum: int = Field(
        0,
        description="検索期間内 schedule_details.defect_qty の合計（defect_daily の総和と一致）",
    )
    upstream_defect_qty_total: int = Field(
        0,
        description="当製造指示の aps_batch_plans.upstream_defect_qty 合計（切断+面取・FormingPlanning と同趣旨）",
    )
    has_aps_batch_plans: bool = Field(
        False,
        description="当製造指示に aps_batch_plans が1件以上あるか（マトリクス上流状態色分け用）",
    )
    daily_upstream_tint: Dict[str, DailyUpstreamTintSeg] = Field(
        default_factory=dict,
        description="日付(YYYY-MM-DD)ごとの上流状態別按分（スライス×ロット窓の比率で daily を分割）",
    )
    daily_management_codes: Dict[str, List[DailyManagementCodeAlloc]] = Field(
        default_factory=dict,
        description="日付ごとの管理コード按分（ホバーで内示帰属照会用）",
    )


class LineGridBlock(BaseModel):
    line_id: int
    line_code: str
    default_work_hours: float
    calendar: Dict[str, float] = Field(default_factory=dict)
    rows: List[ScheduleGridRow] = Field(default_factory=list)
    daily_totals: Dict[str, int] = Field(default_factory=dict)
    sum_planned_process_qty: int = 0
    sum_planned_output_qty: int = 0
    completion_rate: Optional[float] = None


class SchedulingGridResponse(BaseModel):
    dates: List[str]
    blocks: List[LineGridBlock]


# ──────────────────── Hourly slice grid（時間別ガント）────────────────────

class HourlyGridColumnOut(BaseModel):
    key: str
    work_date: str
    period_start: str
    period_end: str


class HourlyGridRowOut(BaseModel):
    schedule_id: int
    order_no: Optional[int] = None
    planned_batch_count: int = 0
    lot_size_snapshot: int = 0
    planned_process_qty: int = 0
    efficiency_rate: Optional[float] = None
    item_name: str
    slice_qty: Dict[str, int] = Field(default_factory=dict)


class SchedulingHourlyGridResponse(BaseModel):
    columns: List[HourlyGridColumnOut]
    rows: List[HourlyGridRowOut]


# ──────────────────── APS Batch Plans ────────────────────
class ApsBatchPlanOut(BaseModel):
    id: int
    aps_schedule_id: int
    production_month: date
    production_line: str
    priority_order: Optional[int] = None
    product_cd: str
    product_name: str
    planned_quantity: int
    upstream_defect_qty: int = 0
    original_planned_quantity: Optional[int] = None
    production_lot_size: int
    lot_number: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


# ──────────────────── Production Progress（生産進捗） ────────────────────

class ProgressLotItem(BaseModel):
    """ロット単位の生産進捗（instruction_plans / cutting_management を照合）"""
    batch_plan_id: int
    aps_schedule_id: int
    product_cd: str
    product_name: str
    lot_number: str
    planned_quantity: int = Field(..., description="計画一覧由来のロット本数（original_planned_quantity、成型実績で変わらない）")
    order_no: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    predicted_completion: Optional[str] = Field(None, description="予測完了日時 = end_date")
    progress_status: str = Field("PLANNED", description="PLANNED / RELEASED / IN_PROGRESS / COMPLETED")
    management_code: Optional[str] = None
    production_lot_size_forming: Optional[int] = Field(
        None, description="aps_batch_plans.production_lot_size（スライス残口径・照会码用）",
    )
    production_lot_size_instruction: Optional[int] = Field(
        None, description="計画一覧合計から算出するロット数（instruction_plans 同期码用）",
    )
    management_code_instruction: Optional[str] = Field(
        None, description="指示同期用 management_code（ロット数が異なると照会码と不一致になり得る）",
    )
    lot_size_code_dual_source: bool = Field(
        False,
        description="成型ロット数と指示ロット数が異なる、または照会码と指示码不一致",
    )
    schedule_slice_total: Optional[int] = Field(
        None, description="工単スライス残合計（成型ロット数の算出元）",
    )
    schedule_full_plan_total: Optional[int] = Field(
        None, description="工単計画一覧合計（指示ロット数の算出元）",
    )
    in_instruction_plans_by_instruction_code: bool = Field(
        False,
        description="instruction_plans に指示用コードで行がある（照会码とは別）",
    )
    production_line: str = ""
    cutting_planned_qty: Optional[int] = Field(
        None, description="切断指示 cutting_management.planned_quantity（生産中ロットのみ）"
    )
    cutting_actual_qty: Optional[int] = Field(
        None, description="切断実績 cutting_management.actual_production_quantity"
    )
    cutting_completed: Optional[bool] = Field(
        None, description="切断 production_completed_check（実績確定イメージ）"
    )
    upstream_defect_qty: int = Field(
        0,
        description="前工程不良合計（切断+面取、management_code／aps ロットと照合）",
    )
    forming_effective_planned_qty: int = Field(
        0,
        description="成型有効計画本数（計画表示−前工程不良、下限0）",
    )
    status_determined_by: Optional[str] = Field(
        None,
        description="進捗ステータス判定元: CUTTING_BY_MC / CUTTING_BY_BATCH_ID / INSTRUCTION / PLANNED",
    )
    edit_location_hint: Optional[str] = Field(
        None,
        description="ステータス・切断本数の修正先（画面・テーブル）",
    )
    position_summary: Optional[str] = Field(
        None,
        description="ライン内位置（順位・工単・ロット）の要約",
    )
    in_cutting_management: bool = Field(
        False,
        description="cutting_management に行があり、照会 management_code と DB management_code が一致",
    )
    in_cutting_by_management_code: bool = Field(
        False,
        description="cutting_management.management_code が照会表示コードと一致（in_cutting_management と同義）",
    )
    in_cutting_by_batch_plan_id: bool = Field(
        False,
        description="廃止: バッチIDのみ一致は進捗・所在の紐付けに含めない（常に false）",
    )
    cutting_management_code_in_db: Optional[str] = Field(
        None,
        description="紐付け成立時の cutting_management.management_code",
    )
    cutting_management_row_id: Optional[int] = Field(
        None,
        description="紐付け成立時の cutting_management.id",
    )
    cutting_batch_link_mismatch_id: Optional[int] = Field(
        None,
        description="aps_batch_plan_id のみ一致し code 不一致の切断行 id（参考・進捗には未使用）",
    )
    cutting_batch_link_mismatch_db_code: Optional[str] = Field(
        None,
        description="上記不一致行の DB management_code",
    )
    in_instruction_plans: bool = Field(
        False,
        description="instruction_plans に行があり、照会 management_code と DB が一致",
    )
    in_instruction_by_management_code: bool = Field(
        False,
        description="instruction_plans.management_code が照会表示コードと一致",
    )
    in_instruction_by_batch_plan_id: bool = Field(
        False,
        description="廃止: バッチIDのみ一致は紐付けに含めない（常に false）",
    )
    instruction_management_code_in_db: Optional[str] = Field(
        None,
        description="instruction_plans に登録されている management_code",
    )
    cutting_match_field: Optional[str] = Field(
        None,
        description="進捗判定の切断照合キー: management_code | aps_batch_plan_id",
    )
    instruction_match_field: Optional[str] = Field(
        None,
        description="製造指示照合キー: management_code | aps_batch_plan_id",
    )
    upstream_data_table: Optional[str] = Field(
        None,
        description="進捗ステータス判定に効く主テーブル: cutting_management | instruction_plans | 未登録",
    )


class UpstreamApsBatchPlanLinkItem(BaseModel):
    """管理コード所在照会からの upstream 紐付け更新対象"""
    batch_plan_id: int = Field(..., description="aps_batch_plans.id（照会行のロット）")
    cutting_management_id: Optional[int] = Field(
        None,
        description="cutting_management.id。省略時は batch_plan_id で該当切断行を更新",
    )


class UpstreamApsBatchPlanLinksBody(BaseModel):
    items: List[UpstreamApsBatchPlanLinkItem] = Field(..., min_length=1)
    new_aps_batch_plan_id: Optional[int] = Field(
        None,
        description="設定する aps_batch_plans.id。null で cutting_management / instruction_plans の紐付けをクリア",
    )
    update_instruction_plans: bool = Field(
        True,
        description="true のとき instruction_plans.aps_batch_plan_id も同様に更新",
    )


class UpstreamApsBatchPlanLinksResult(BaseModel):
    cutting_updated: int = 0
    instruction_updated: int = 0


class ReassignCuttingManagementLotBody(BaseModel):
    """cutting_management を正しい APS ロットへ移管（管理コード再生成 + aps_batch_plan_id 設定）"""
    cutting_management_id: int = Field(..., description="cutting_management.id")
    target_batch_plan_id: int = Field(..., description="移管先 aps_batch_plans.id")
    update_instruction_plans: bool = Field(
        True,
        description="true のとき移管先ロットの management_code に一致する instruction_plans の aps_batch_plan_id も更新",
    )


class ReassignCuttingManagementLotResult(BaseModel):
    cutting_management_id: int
    previous_batch_plan_id: Optional[int] = None
    target_batch_plan_id: int
    previous_management_code: Optional[str] = None
    new_management_code: str
    instruction_updated: int = 0


class ProductionProgressResponse(BaseModel):
    lots: List[ProgressLotItem] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list, description="日別タイムライン用日付列")
    lot_daily: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="lot_key -> 日別数量。成型ガント連動（schedule_details の planned/actual）。切断本数は ProgressLotItem の cutting_* を参照",
    )
    lot_daily_source: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="同一キーで ACTUAL / PLANNED / WAIT_UPSTREAM（セル配色用）",
    )
