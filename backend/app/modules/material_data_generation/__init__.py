from fastapi import APIRouter
from .api import router as material_data_generation_router

router = APIRouter()
router.include_router(material_data_generation_router, prefix="", tags=["材料在庫データ生成"])

__all__ = ["router"]

