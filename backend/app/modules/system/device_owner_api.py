"""
Android Device Owner QR 配布用 API。

- APK アップロード / 状態取得（要ログイン）
- タブレット QR 開通用の無認証ダウンロード
- Provisioning JSON 生成用ペイロード
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.permission_service import assert_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/device-owner", tags=["Device Owner QR"])

DPC_COMPONENT = (
    "com.example.smart_emap/com.example.smart_emap.admin.SmartEmapDeviceAdminReceiver"
)
APK_FILENAME = "smart-emap.apk"
DOWNLOAD_PATH = "/api/system/device-owner/apk/download"

_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "device_owner"
_APK_PATH = _DATA_DIR / APK_FILENAME
_META_PATH = _DATA_DIR / "meta.json"


class DeviceOwnerSettingsUpdate(BaseModel):
    """公開ダウンロード基址と任意の署名 checksum。"""

    public_base_url: str = Field(
        "",
        description="https://xxxx.trycloudflare.com または …/smart-emap.apk のフル URL",
    )
    signature_checksum: str = Field("", description="URL-safe Base64 の署名証明書 SHA-256")


class DeviceOwnerStatusResponse(BaseModel):
    has_apk: bool
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    package_checksum: Optional[str] = None
    signature_checksum: Optional[str] = None
    public_base_url: str = ""
    uploaded_at: Optional[str] = None
    download_path: str = DOWNLOAD_PATH
    dpc_component: str = DPC_COMPONENT


class ProvisioningPayloadResponse(BaseModel):
    has_apk: bool
    download_url: Optional[str] = None
    package_checksum: Optional[str] = None
    signature_checksum: Optional[str] = None
    dpc_component: str = DPC_COMPONENT
    qr_json: Optional[dict[str, Any]] = None
    qr_text: Optional[str] = None
    warning: Optional[str] = None


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _urlsafe_b64_sha256(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _load_meta() -> dict[str, Any]:
    if not _META_PATH.is_file():
        return {}
    try:
        return json.loads(_META_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("device_owner meta.json read failed")
        return {}


def _save_meta(meta: dict[str, Any]) -> None:
    _ensure_dir()
    _META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_base_url(raw: str) -> str:
    return (raw or "").strip().rstrip("/")


def _looks_like_direct_apk_url(url: str) -> bool:
    """フル APK URL（…/xxx.apk または API download パス）ならそのまま使う。"""
    lower = url.lower()
    if lower.endswith(".apk"):
        return True
    if "/api/system/device-owner/apk/download" in lower:
        return True
    return False


def _build_download_url(public_base_url: str) -> Optional[str]:
    """
    受け入れ例:
    - https://xxxx.trycloudflare.com
      → https://xxxx.trycloudflare.com/api/system/device-owner/apk/download
    - https://xxxx.trycloudflare.com/smart-emap.apk
      → そのまま（静的トンネル配布）
    """
    base = _normalize_base_url(public_base_url)
    if not base:
        return None
    if _looks_like_direct_apk_url(base):
        return base
    return f"{base}{DOWNLOAD_PATH}"


def _build_qr_json(
    download_url: str,
    package_checksum: str,
    signature_checksum: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": DPC_COMPONENT,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": download_url,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": package_checksum,
        "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": True,
        "android.app.extra.PROVISIONING_SKIP_ENCRYPTION": True,
    }
    sig = (signature_checksum or "").strip()
    if sig:
        payload["android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM"] = sig
    return payload


@router.get("/status", response_model=DeviceOwnerStatusResponse, summary="Device Owner APK 状態")
async def get_device_owner_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await assert_super_admin(db, current_user)
    meta = _load_meta()
    has_apk = _APK_PATH.is_file()
    return DeviceOwnerStatusResponse(
        has_apk=has_apk,
        filename=APK_FILENAME if has_apk else None,
        size_bytes=_APK_PATH.stat().st_size if has_apk else None,
        package_checksum=meta.get("package_checksum") if has_apk else None,
        signature_checksum=meta.get("signature_checksum") or "",
        public_base_url=meta.get("public_base_url") or "",
        uploaded_at=meta.get("uploaded_at") if has_apk else None,
    )


@router.put("/settings", response_model=DeviceOwnerStatusResponse, summary="公開 URL / 署名 checksum 保存")
async def update_device_owner_settings(
    body: DeviceOwnerSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await assert_super_admin(db, current_user)
    meta = _load_meta()
    meta["public_base_url"] = _normalize_base_url(body.public_base_url)
    meta["signature_checksum"] = (body.signature_checksum or "").strip()
    _save_meta(meta)
    return await get_device_owner_status(db=db, current_user=current_user)


@router.post("/apk", response_model=DeviceOwnerStatusResponse, summary="APK アップロード")
async def upload_device_owner_apk(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await assert_super_admin(db, current_user)
    name = (file.filename or "").lower()
    if not name.endswith(".apk"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="APK ファイルのみアップロードできます")

    _ensure_dir()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="空のファイルです")
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="APK が大きすぎます（上限 200MB）")

    _APK_PATH.write_bytes(content)
    package_checksum = _urlsafe_b64_sha256(content)
    meta = _load_meta()
    meta.update(
        {
            "filename": APK_FILENAME,
            "package_checksum": package_checksum,
            "size_bytes": len(content),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save_meta(meta)
    logger.info("Device Owner APK uploaded by user_id=%s size=%s", getattr(current_user, "id", None), len(content))
    return await get_device_owner_status(db=db, current_user=current_user)


@router.get("/provisioning-payload", response_model=ProvisioningPayloadResponse, summary="QR 用 Provisioning JSON")
async def get_provisioning_payload(
    public_base_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    ページ表示時に呼ぶ。APK があれば QR 用 JSON を返す。
    public_base_url 未指定時は保存済み設定を使用。
    """
    await assert_super_admin(db, current_user)
    meta = _load_meta()
    if not _APK_PATH.is_file():
        return ProvisioningPayloadResponse(has_apk=False, warning="APK が未アップロードです")

    package_checksum = meta.get("package_checksum")
    if not package_checksum:
        package_checksum = _urlsafe_b64_sha256(_APK_PATH.read_bytes())
        meta["package_checksum"] = package_checksum
        _save_meta(meta)

    base = _normalize_base_url(public_base_url or "") or _normalize_base_url(meta.get("public_base_url") or "")
    download_url = _build_download_url(base)
    warning = None
    if not download_url:
        warning = "公開 URL が未設定です。Tunnel の https://….trycloudflare.com か、…/smart-emap.apk のフル URL を入力してください"
        return ProvisioningPayloadResponse(
            has_apk=True,
            package_checksum=package_checksum,
            signature_checksum=meta.get("signature_checksum") or "",
            warning=warning,
        )

    if not re.match(r"^https://", download_url, re.I):
        warning = "公開 URL は https:// である必要があります（QR 開通の要件）"

    sig = meta.get("signature_checksum") or ""
    qr_json = _build_qr_json(download_url, package_checksum, sig)
    qr_text = json.dumps(qr_json, ensure_ascii=False, separators=(",", ":"))
    return ProvisioningPayloadResponse(
        has_apk=True,
        download_url=download_url,
        package_checksum=package_checksum,
        signature_checksum=sig,
        qr_json=qr_json,
        qr_text=qr_text,
        warning=warning,
    )


@router.get("/apk/download", summary="APK ダウンロード（QR 開通用・認証不要）", include_in_schema=True)
async def download_device_owner_apk():
    """タブレット Provisioning が認証なしで取得する。"""
    if not _APK_PATH.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="APK not found")
    return FileResponse(
        path=_APK_PATH,
        media_type="application/vnd.android.package-archive",
        filename=APK_FILENAME,
        content_disposition_type="attachment",
    )
