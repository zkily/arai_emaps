# システム・ユーザー関連画面 詳細仕様書

`frontend/src/views/system/user` フォルダ内の各 Vue コンポーネントと、対応するバックエンド API・データベースの関連をまとめた説明書です。

---

## 1. フォルダ構成

| ファイル | 概要 |
|----------|------|
| **UserList.vue** | ユーザー一覧・新規/編集・ロック/パスワード再設定 |
| **OrganizationList.vue** | 組織・部門のツリー表示と CRUD、組織詳細・所属ユーザー表示 |
| **RolePermission.vue** | ロール一覧・権限設定（メニュー/操作/データ範囲） |

---

## 2. UserList.vue（ユーザー管理）

### 2.1 画面概要

- **タイトル**: ユーザー管理（アカウント管理・権限設定・セキュリティ）
- **機能**: ユーザーの一覧表示、検索・フィルタ、新規登録、編集、ロック/ロック解除、パスワード再設定、印刷

### 2.2 フロントエンド

- **検索条件**: キーワード（ユーザー名・氏名・メール）、部門（`department_id`）、ステータス（有効/ロック中）
- **テーブル列**: ID、ユーザー名、氏名、メール、部門、ロール、ステータス、2FA、最終ログイン、操作
- **操作ボタン**: 編集、ロック/ロック解除、パスワード再設定
- **ダイアログ**: ユーザー新規/編集フォーム（ユーザー名、氏名、メール、部門、ロール、二要素認証、パスワード）、パスワード再設定ダイアログ
- **使用 API**（`@/api/system`）:
  - `getUsers(params)` — 一覧・検索・ページネーション
  - `getRoles()` — ロール選択肢
  - `getOrganizations()` — 部門選択肢（type が company/site/department の組織）
  - `createUser(data)` — 新規登録
  - `updateUser(userId, data)` — 更新
  - `lockUser(userId)` / `unlockUser(userId)` — ロック/解除
  - `resetUserPassword(userId, { new_password })` — パスワード再設定
- **ストア**: `useUserStore()`（現在ユーザー情報、自分自身のロック防止など）

### 2.3 バックエンド API（`/api/system`）

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/users` | ユーザー一覧。クエリ: `keyword`, `department_id`, `status`, `page`, `page_size`。管理者は全件、それ以外は自部門または自分のみ。 |
| POST | `/users` | ユーザー新規登録（管理者のみ） |
| PUT | `/users/{user_id}` | ユーザー更新 |
| POST | `/users/{user_id}/lock` | ロック（自分自身は不可） |
| POST | `/users/{user_id}/unlock` | ロック解除 |
| POST | `/users/{user_id}/reset-password` | パスワード直接設定（Body: `UserPasswordSet`） |
| GET | `/stats/online` | 現在の利用者数（`last_login_token` が NULL でない件数） |

### 2.4 関連データベース

- **users**（実体は `backend/app/modules/auth/models.py` の `User`）
  - `id`, `username`, `email`, `hashed_password`, `full_name`, `role`, `is_active`, `last_login_token`, `last_login_at`, `department_id`（FK → organizations.id）, `two_factor_enabled`, `created_at`, `updated_at`
- **user_roles**（多対多: ユーザー ⇔ ロール）
  - `user_id` → users.id, `role_id` → roles.id
- **organizations**
  - 部門名表示・フィルタ・フォームの部門選択に使用

---

## 3. OrganizationList.vue（組織・部門管理）

### 3.1 画面概要

- **タイトル**: 組織・部門管理（会社・拠点・部門・課・ライン階層構造）
- **レイアウト**: 左に組織ツリー、右に選択組織の詳細と「所属ユーザー」エリア
- **機能**: ツリーのクリックで詳細表示、ダブルクリックで編集、追加/編集/削除

### 3.2 フロントエンド

- **組織ツリー**: `el-tree`、node-key=`id`、種類（company/site/department/section/line）ごとにアイコン・色分け
- **詳細パネル**: 組織コード、種類、親組織、責任者、所在地、電話、メール、説明
- **所属ユーザー**: 選択組織に紐づくユーザー一覧を表示する想定だが、**現状は API で取得しておらず** `orgUsers` は常に空。メッセージ「所属ユーザーはユーザー管理で部門を指定して確認できます」を表示
- **使用 API**:
  - `getOrganizationTree(params?)` — ツリー取得（`_t` でキャッシュ回避）
  - `getOrganization(orgId)` — 組織詳細
  - `createOrganization(data)` — 組織作成
  - `updateOrganization(orgId, data)` — 組織更新
  - `deleteOrganization(orgId)` — 組織削除（物理削除）
- **フォーム**: 組織コード、組織名、種類、親組織（ツリー選択）、責任者、所在地、電話、メール、説明

### 3.3 バックエンド API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/organizations` | 組織一覧（is_active のみ、sort_order, id 順） |
| GET | `/organizations/tree` | 組織ツリー構造（親子の階層） |
| GET | `/organizations/{org_id}` | 組織詳細（is_active のみ） |
| POST | `/organizations` | 組織作成（管理者のみ、code 重複チェック） |
| PUT | `/organizations/{org_id}` | 組織更新 |
| DELETE | `/organizations/{org_id}` | 組織削除（物理削除） |

### 3.4 関連データベース

- **organizations**
  - `id`, `code`（ユニーク）, `name`, `type`（company/site/department/section/line）, `parent_id`（FK → organizations.id）, `manager_name`, `location`, `phone`, `email`, `description`, `sort_order`, `is_active`, `created_at`, `updated_at`
- **users.department_id** → organizations.id（所属部門）。組織に紐づくユーザーはユーザー一覧の `department_id` フィルタで参照可能。

---

## 4. RolePermission.vue（権限・ロール管理）

### 4.1 画面概要

- **タイトル**: 権限・ロール管理（RBAC・メニュー権限・操作権限・データ範囲）
- **レイアウト**: 左にロール一覧テーブル、右に選択ロールの権限設定（タブ: メニュー権限 / 操作権限 / データ範囲）
- **機能**: ロールの追加・編集・削除、メニュー権限（ツリー checkbox）、操作権限（モジュール別 新規・編集・削除・出力・承認）、データ範囲（self/department/department_below/all/custom）、カスタム部門は `custom` 時のみ

### 4.2 フロントエンド

- **ロール一覧**: ロール名、ユーザー数、編集/削除（システムロールは削除不可）
- **メニュー権限**: `getMenuTree()` で取得したツリーを `el-tree` で show-checkbox、チェック済み・半選を保存時に送信
- **操作権限**: 固定モジュール一覧（販売管理、購買管理、在庫管理、原価・会計、生産計画、製造実行、品質管理、システム管理）ごとに can_create / can_edit / can_delete / can_export / can_approve をテーブルで編集
- **データ範囲**: ラジオ的に self / department / department_below / all / custom を選択。custom 時は部門の複数選択
- **使用 API**:
  - `getRoles()` — ロール一覧
  - `getRole(roleId)` — ロール詳細（menu_permissions, operation_permissions, data_scope, custom_departments）
  - `getMenuTree()` — メニューツリー
  - `getOrganizations()` — 部門リスト（データ範囲カスタム・部門選択肢）
  - `createRole(data)` — ロール作成
  - `updateRole(roleId, data)` — ロール更新（基本情報＋menu_permissions, operation_permissions, data_scope, custom_departments）
  - `deleteRole(roleId)` — ロール削除（システムロールは 400）

### 4.3 バックエンド API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/roles` | ロール一覧（user_count 付き） |
| GET | `/roles/{role_id}` | ロール詳細（メニュー権限 ID リスト、操作権限リスト、data_scope, custom_departments） |
| POST | `/roles` | ロール作成（menu_permissions, operation_permissions も登録） |
| PUT | `/roles/{role_id}` | ロール更新（メニュー・操作権限の差し替え対応） |
| DELETE | `/roles/{role_id}` | ロール削除（is_system の場合は 400） |

メニュー関連（権限設定で参照）:

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/menus` | メニュー一覧 |
| GET | `/menus/tree` | メニューツリー（権限ツリー用） |

### 4.4 関連データベース

- **roles**
  - `id`, `name`（ユニーク）, `description`, `is_system`, `data_scope`, `custom_departments`（JSON）, `is_active`, `created_at`, `updated_at`
- **role_menu_permissions**
  - `role_id` → roles.id, `menu_id` → menus.id（CASCADE 削除）
- **role_operation_permissions**
  - `role_id`, `module`, `can_create`, `can_edit`, `can_delete`, `can_export`, `can_approve`, `created_at`, `updated_at`
- **user_roles**
  - `user_id` → users.id, `role_id` → roles.id（ロールに紐づくユーザー数の集計に使用）
- **menus**
  - `id`, `code`, `name`, `parent_id`, `path`, `icon`, `sort_order`, `is_active`, `created_at`

---

## 5. データベース関連図（関連テーブル）

```
users (auth.models.User)
  ├── department_id → organizations.id (SET NULL)
  └── user_roles (多対多) → roles

organizations
  └── parent_id → organizations.id (自己参照)

roles
  ├── role_menu_permissions → menus
  ├── role_operation_permissions
  └── user_roles → users

menus
  └── parent_id → menus.id (自己参照)
```

- **User**: `backend/app/modules/auth/models.py` で定義（`department_id`, `two_factor_enabled` 含む）。システム API では `from app.modules.auth.models import User` を使用。
- **Organization, Role, Menu, RoleMenuPermission, RoleOperationPermission, UserRole**: `backend/app/modules/system/models.py` で定義。

---

## 6. スキーマ（バックエンド Pydantic）

- **backend/app/modules/system/schemas.py**
  - ユーザー: `UserCreate`, `UserUpdate`, `UserResponse`, `UserListResponse`, `UserSearchParams`, `PaginatedUserResponse`, `UserStatus`, `UserPasswordSet`
  - 組織: `OrganizationCreate`, `OrganizationUpdate`, `OrganizationResponse`, `OrganizationTreeNode`, `OrganizationType`
  - ロール: `RoleCreate`, `RoleUpdate`, `RoleResponse`, `RoleListResponse`, `OperationPermission`, `DataScope`
  - メニュー: `MenuResponse`, `MenuTreeNode`, `MenuCreate`, `MenuUpdate`, `MenuSyncRequest` など

---

## 7. ルーティング・認証

- システム API は `verify_token_and_get_user` で認証。管理者専用操作（ユーザー/組織/ロールの作成・削除・ロック・パスワード再設定など）は `current_user.role == "admin"` をチェック。
- ユーザー一覧のデータ範囲: 管理者は全件、それ以外は `department_id` が自ユーザーと一致するユーザーのみ（未設定時は自分自身のみ）。

---

## 8. 補足

- **組織の所属ユーザー**: 組織詳細で「所属ユーザー」を表示する専用 API は現状ない。ユーザー一覧の `department_id` で該当組織を指定して一覧を取得する運用。
- **ロールと User.role**: ロールテーブル（roles）は「ロール名」と権限を保持し、`user_roles` でユーザーと多対多。一方、`users.role` には認証用のコード（admin/user/manager/worker/guest/viewer）が格納され、API では `ROLE_NAME_TO_CODE` でロール名とコードを対応付けている。
- **app.models.user と auth.models.User**: システム API が参照するのは **auth.models.User**（`department_id`, `two_factor_enabled` あり）。`app.models.user` は別定義の可能性があり、本機能では auth 側が正とする。

---

## 9. 多言語対応（i18n）

本フォルダ配下の **UserList.vue**・**OrganizationList.vue**・**RolePermission.vue** の 3 画面は、vue-i18n による多言語表示に対応しています。

### 9.1 対応言語

- **ja**（日本語）— デフォルト・フォールバック
- **zh**（简体中文）
- **en**（English）
- **vi**（Tiếng Việt）

言語の切り替えはヘッダーの言語選択で行い、選択値は `localStorage` の `app-locale` に保存されます。

### 9.2 翻訳キー構造

各画面の文言は `frontend/src/locales/{ja,zh,en,vi}.ts` の **systemUser** オブジェクトで定義されています。

| キー | 対象画面 | 内容 |
|------|----------|------|
| **systemUser.org** | OrganizationList.vue | 組織・部門管理のタイトル、ラベル、ボタン、メッセージ、バリデーション、組織タイプ（会社/拠点/部門/課/ライン）など |
| **systemUser.role** | RolePermission.vue | 権限・ロール管理のタイトル、ロール一覧、タブ（メニュー権限/操作権限/データ範囲）、データ範囲オプション、フォーム、メッセージなど |
| **systemUser.user** | UserList.vue | ユーザー管理のタイトル、検索・テーブル列、フォーム、ロール/ステータスラベル、バリデーション、成功/エラーメッセージ、印刷用ラベルなど |

### 9.3 コンポーネントでの利用

各 Vue コンポーネントでは `useI18n()` で `t` を取得し、テンプレートおよび script 内で `t('systemUser.org.xxx')` のようにキーを指定して表示しています。

- **テンプレート**: `{{ t('systemUser.org.title') }}` や `:label="t('systemUser.user.username')"`
- **script**: `ElMessage.success(t('systemUser.user.msgSaveSuccess'))`、`computed` 内のフォームルールメッセージなど

新規に文言を追加する場合は、上記 4 言語の locale ファイルの `systemUser.org` / `systemUser.role` / `systemUser.user` のいずれかに同じキーを追加してください。

以上が、`frontend/src/views/system/user` 配下のファイルとバックエンド・データベースの対応の詳細説明です。
