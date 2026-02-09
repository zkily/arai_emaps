"""
Smart-EMAP (ERP+APS+MES) 統合管理システム
メインアプリケーションエントリーポイント
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings
from app.core.datetime_utils import JST
from app.modules import auth, erp, aps, mes, websocket, system, master, order


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時の処理
    print(f"🚀 Smart-EMAP システム起動中...")
    print(f"⏰ 現在時刻 (JST): {datetime.now(JST).strftime('%Y年%m月%d日 %H:%M:%S')}")
    yield
    # シャットダウン時の処理
    print(f"🛑 Smart-EMAP システム停止中...")


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
    # 開発環境: 正規表現ですべてのHTTPオリジンを許可
    # これにより、localhost、127.0.0.1、または任意のIPアドレスからのアクセスを許可
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://.*",  # すべてのHTTPオリジンを許可
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
from app.core.middleware.api_log_middleware import ApiLogMiddleware
app.add_middleware(ApiLogMiddleware)


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
app.include_router(mes.router, prefix="/api/mes", tags=["MES"])
app.include_router(master.router, prefix="/api/master", tags=["マスタ管理"])
app.include_router(system.router, prefix="/api/system", tags=["システム管理"])
app.include_router(order.router, prefix="/api/order", tags=["受注バッチ"])

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
        port=8000,
        reload=True,
    )

