"""
WebSocket APIエンドポイント
リアルタイム通信（単一デバイスログイン通知など）
"""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.auth.api import get_user_by_username
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

# 接続中のWebSocketクライアントを管理
# キー: username, 値: Set[WebSocket]
active_connections: Dict[str, Set[WebSocket]] = {}


async def get_user_from_token(websocket: WebSocket, db: AsyncSession) -> User:
    """WebSocket接続からトークンを取得してユーザーを検証"""
    # WebSocketクエリパラメータからトークンを取得
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが必要です"
        )
    
    # トークンをデコード
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが無効です"
        )
    
    username: str = payload.get("sub")
    if not username:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが無効です"
        )
    
    # データベースからユーザーを取得
    user = await get_user_by_username(db, username)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # トークンの有効性を確認（単一デバイスログイン対応）
    if user.last_login_token and user.last_login_token != token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="このアカウントは他のデバイスでログインされています"
        )
    
    return user


async def register_connection(username: str, websocket: WebSocket):
    """WebSocket接続を登録"""
    if username not in active_connections:
        active_connections[username] = set()
    active_connections[username].add(websocket)
    logger.info(f"[WebSocket] User {username} connected. Total connections: {len(active_connections[username])}")


async def unregister_connection(username: str, websocket: WebSocket):
    """WebSocket接続を登録解除"""
    if username in active_connections:
        active_connections[username].discard(websocket)
        if not active_connections[username]:
            del active_connections[username]
        logger.info(f"[WebSocket] User {username} disconnected. Remaining connections: {len(active_connections.get(username, []))}")


async def notify_user_logged_in_elsewhere(username: str, new_token: str):
    """他のデバイスでログインされたことを通知"""
    if username in active_connections:
        message = {
            "type": "force_logout",
            "message": "このアカウントは他のデバイスでログインされています。再度ログインしてください。",
            "reason": "other_device_login"
        }
        
        # すべての接続に通知
        disconnected = []
        for websocket in list(active_connections[username]):
            try:
                await websocket.send_json(message)
                logger.info(f"[WebSocket] Sent force_logout message to {username}")
            except Exception as e:
                logger.error(f"[WebSocket] Error sending message to {username}: {e}")
                disconnected.append(websocket)
        
        # 切断された接続を削除
        for websocket in disconnected:
            await unregister_connection(username, websocket)


async def websocket_endpoint(websocket: WebSocket, db: AsyncSession):
    """WebSocket接続エンドポイント"""
    await websocket.accept()
    user = None
    
    try:
        # トークンからユーザーを取得
        user = await get_user_from_token(websocket, db)
        
        # 接続を登録
        await register_connection(user.username, websocket)
        
        # 接続確認メッセージを送信
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket接続が確立されました"
        })
        
        # メッセージを受信し続ける
        while True:
            try:
                data = await websocket.receive_text()
                # クライアントからのメッセージを処理（必要に応じて）
                # 現在は単に接続を維持するため
                await websocket.send_json({
                    "type": "pong",
                    "message": "接続中"
                })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"[WebSocket] Error receiving message: {e}")
                break
                
    except Exception as e:
        logger.error(f"[WebSocket] Connection error: {e}")
        try:
            await websocket.close()
        except:
            pass
    finally:
        # 接続を登録解除
        if user:
            await unregister_connection(user.username, websocket)

