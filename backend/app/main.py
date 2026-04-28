"""
Smart-EMAP (ERP+APS+MES) 統合管理システム
メインアプリケーションエントリーポイント
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.datetime_utils import JST
from app.core.database import AsyncSessionLocal
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.modules import (
    auth,
    erp,
    aps,
    cutting_planning,
    mes,
    websocket,
    system,
    master,
    order,
    database,
    shipping,
    excel_monitor,
    machine_work_time_config,
    production_schedule,
    plan_baseline,
    outsourcing,
    material,
    material_data_generation,
    part,
    part_data_generation,
    part_order,
)


# Loguru による統一ログ初期化（標準 logging もブリッジ）
setup_logging(
    level=getattr(settings, "LOG_LEVEL", "INFO"),
    log_file=getattr(settings, "LOG_FILE", "logs/app.log"),
)

# APIログ自動削除（JST 毎日 02:00、2か月より古いデータ）
async def _delete_old_api_logs_once() -> int:
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # 「2か月」を SQL の INTERVAL 2 MONTH で統一
        q = text("DELETE FROM api_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL 2 MONTH)")
        result = await db.execute(q)
        await db.commit()
        return int(result.rowcount or 0)


def _seconds_until_next_jst_2am(now: datetime) -> float:
    target = now.replace(hour=2, minute=0, second=0, microsecond=0)
    if now >= target:
        target = target + timedelta(days=1)
    return max((target - now).total_seconds(), 1.0)


async def _api_logs_cleanup_loop():
    logger.info("🧹 APIログ自動削除タスク開始（毎日 02:00 JST、保持期間 2か月）")
    while True:
        try:
            now = datetime.now(JST)
            wait_seconds = _seconds_until_next_jst_2am(now)
            await asyncio.sleep(wait_seconds)
            run_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
            deleted = await _delete_old_api_logs_once()
            logger.info("🧹 api_logs 自動削除完了: 実行時刻={} / 削除件数={} 件（2か月より古いデータ）", run_at, deleted)
        except asyncio.CancelledError:
            logger.info("🛑 APIログ自動削除タスク停止")
            raise
        except Exception as e:
            logger.warning("APIログ自動削除でエラー: {}", e)
            # 異常時は 5 分後に再試行
            await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger.info("🚀 Smart-EMAP システム起動中...")
    logger.info(
        "⏰ 現在時刻 (JST): {}",
        datetime.now(JST).strftime("%Y年%m月%d日 %H:%M:%S"),
    )
    if getattr(settings, "FILE_WATCH_START_WITH_API", False):
        from app.services.file_watcher.run import start_file_watcher_background

        start_file_watcher_background()
        logger.info(
            "📂 ファイル監視: API プロセス内バックグラウンドを有効化"
            "（FILE_WATCH_START_WITH_API）"
        )
    cleanup_task = asyncio.create_task(_api_logs_cleanup_loop())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("🛑 Smart-EMAP システム停止中...")


# FastAPIアプリケーションの初期化
app = FastAPI(
    title=settings.SERVER_NAME,
    description="製造業のデジタルトランスフォーメーションを実現する統合管理システム",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
# 開発環境でネットワークアクセスを許可する場合の設定
# 開発環境では、すべてのHTTPオリジンを許可（ネットワークアクセス対応）
if settings.CORS_ALLOW_ALL or settings.APP_ENV == "development":
    # 開発環境: 正規表現ですべての HTTP / HTTPS オリジンを許可
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 本番環境: 指定されたオリジンのみ許可
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API連携ログ記録（/api/* のみ、api_logs テーブルに記録）
from app.core.middleware.api_log_middleware import ApiLogMiddleware  # noqa: E402

app.add_middleware(ApiLogMiddleware)

# グローバル例外ハンドラ（統一エラーレスポンス形式）
register_exception_handlers(app)


# ルーターの登録
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Smart-EMAP API",
        "version": "1.0.0",
        "timestamp": datetime.now(JST).isoformat(),
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(JST).isoformat(),
    }


# APIルーターの登録
app.include_router(auth.router, prefix="/api/auth", tags=["認証"])
app.include_router(erp.router, prefix="/api/erp", tags=["ERP"])
app.include_router(aps.router, prefix="/api/aps", tags=["APS"])
app.include_router(cutting_planning.router, prefix="/api/cutting-planning", tags=["切断計画作成"])
app.include_router(mes.router, prefix="/api/mes", tags=["MES"])
app.include_router(master.router, prefix="/api/master", tags=["マスタ管理"])
app.include_router(system.router, prefix="/api/system", tags=["システム管理"])
app.include_router(order.router, prefix="/api/order", tags=["受注ロット"])
app.include_router(database.router, prefix="/api/database", tags=["データベース"])
app.include_router(outsourcing.router, prefix="/api/outsourcing", tags=["外注管理"])
app.include_router(material.router, prefix="/api/material", tags=["材料管理"])
app.include_router(
    material_data_generation.router,
    prefix="/api/material-data-generation",
    tags=["材料在庫データ生成"],
)
app.include_router(part.router, prefix="/api/part", tags=["部品購買・在庫"])
app.include_router(
    part_data_generation.router,
    prefix="/api/part-data-generation",
    tags=["部品在庫データ生成"],
)
app.include_router(part_order.router, prefix="/api/part-order", tags=["部品注文"])
app.include_router(shipping.router, prefix="/api/shipping", tags=["出荷管理"])
app.include_router(excel_monitor.router, prefix="/api/excel-monitor", tags=["Excel監視・計画データ"])
app.include_router(machine_work_time_config.router, prefix="/api/machine-work-time-config", tags=["設備運行時間設定"])
app.include_router(production_schedule.router, prefix="/api", tags=["生産状況・スケジュール"])
app.include_router(plan_baseline.router, prefix="/api/plan-baseline", tags=["生産計画ベースライン"])

# WebSocketエンドポイント
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket接続ルート"""
    from app.modules.websocket.api import websocket_endpoint
    from app.core.database import get_db
    
    # データベースセッションを取得してWebSocket接続を処理
    async for db in get_db():
        try:
            await websocket_endpoint(websocket, db)
        finally:
            # セッションは get_db() のコンテキストマネージャーで自動的に閉じられる
            pass
        break


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
    )

