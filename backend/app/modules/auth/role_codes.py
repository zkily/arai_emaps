"""ロールコード定数・users.role 同期ヘルパ（system パッケージへの依存なし）。"""

# roles.code 未設定時：表示名 → users.role フォールバック
LEGACY_ROLE_NAME_TO_CODE: dict[str, str] = {
    "管理者": "admin",
    "一般ユーザー": "user",
    "マネージャー": "manager",
    "作業者": "worker",
    "ゲスト": "guest",
    "閲覧者": "viewer",
}


def legacy_role_code_from_name(name: str | None) -> str | None:
    if not name:
        return None
    return LEGACY_ROLE_NAME_TO_CODE.get(name.strip())


def user_role_code_for_role(role: object) -> str:
    """Role → users.role に書き込むコード（列幅 20 文字まで）。"""
    code = (getattr(role, "code", None) or "").strip()
    if code:
        return code[:20]
    legacy = legacy_role_code_from_name(getattr(role, "name", None))
    return legacy or "user"


def coarse_permissions_for_role_code(role_code: str) -> list[str]:
    """フロント互換の粗粒度 permissions（is_super_admin でない場合）。"""
    code = (role_code or "user").strip()
    if code == "admin":
        return ["all"]
    if code in ("guest", "viewer"):
        return ["read"]
    return ["read", "write"]
