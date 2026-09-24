"""工場レイアウト API スキーマ"""

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

ObjectType = Literal["machine", "aisle", "material_zone", "workshop"]
LayoutKind = Literal["site", "workshop"]


class LayoutCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    canvas_width: int = Field(default=1600, ge=400, le=8000)
    canvas_height: int = Field(default=900, ge=300, le=8000)
    grid_size: int = Field(default=20, ge=8, le=80)
    kind: LayoutKind = "workshop"
    parent_id: Optional[int] = None


class LayoutUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    canvas_width: Optional[int] = Field(default=None, ge=400, le=8000)
    canvas_height: Optional[int] = Field(default=None, ge=300, le=8000)
    grid_size: Optional[int] = Field(default=None, ge=8, le=80)


class LayoutSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    canvas_width: int
    canvas_height: int
    grid_size: int
    kind: str = "workshop"
    parent_id: Optional[int] = None


class LayoutObjectIn(BaseModel):
    id: Optional[int] = None
    object_type: ObjectType
    x: int = Field(ge=0, le=20000)
    y: int = Field(ge=0, le=20000)
    width: int = Field(ge=40, le=4000)
    height: int = Field(ge=40, le=4000)
    label: str = Field(default="", max_length=100)
    ref_cd: Optional[str] = Field(default=None, max_length=100)
    z_index: int = Field(default=0, ge=0, le=9999)
    rotation: int = 0
    locked: bool = False
    group_key: Optional[str] = Field(default=None, max_length=36)
    fill_color: Optional[str] = Field(default=None, max_length=7)
    border_color: Optional[str] = Field(default=None, max_length=7)
    opacity: int = Field(default=100, ge=0, le=100)
    child_layout_id: Optional[int] = None

    @field_validator("rotation")
    @classmethod
    def _rotation(cls, value: int) -> int:
        if value not in (0, 90, 180, 270):
            raise ValueError("rotation must be 0, 90, 180 or 270")
        return value

    @field_validator("fill_color", "border_color")
    @classmethod
    def _hex_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        if not _HEX.fullmatch(text):
            raise ValueError("color must be #RRGGBB")
        return text.lower()


class LayoutObjectsReplace(BaseModel):
    objects: list[LayoutObjectIn]


class LayoutObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    layout_id: int
    object_type: str
    x: int
    y: int
    width: int
    height: int
    label: str
    ref_cd: Optional[str] = None
    z_index: int
    rotation: int = 0
    locked: bool = False
    group_key: Optional[str] = None
    fill_color: Optional[str] = None
    border_color: Optional[str] = None
    opacity: int = 100
    child_layout_id: Optional[int] = None


class LayoutDetail(LayoutSummary):
    objects: list[LayoutObjectOut]


class ObjectStatusOut(BaseModel):
    status: str
    message: str = ""
    updated_at: Optional[datetime] = None
    source: str = "mock"
    payload: Optional[dict] = None


class LayoutStatusResponse(BaseModel):
    statuses: dict[str, ObjectStatusOut]


class StatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)
    message: str = Field(default="", max_length=500)
