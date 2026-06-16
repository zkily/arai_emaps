# Smart-EMAP LINE 通知 完整操作说明

本文说明如何从 **LINE 官方账号创建** 开始，完成 Smart-EMAP 的 LINE 推送通知与 Webhook User ID 收集，并在 **切断実績確定** 等业务场景中发送通知。

**适用版本**：含迁移 `49_notification_recipients_email.sql`、`50_line_notification_push.sql` 及通知センター功能的 Smart-EMAPs 代码库。

---

## 目录

1. [整体架构](#1-整体架构)
2. [前置条件](#2-前置条件)
3. [LINE 官方账号与频道创建](#3-line-官方账号与频道创建)
4. [获取 Channel Token / Channel Secret](#4-获取-channel-token--channel-secret)
5. [Smart-EMAP 数据库迁移](#5-smart-emap-数据库迁移)
6. [通知センター：LINE 外部连携配置](#6-通知センターline-外部连携配置)
7. [本地开发：ngrok 暴露 Webhook](#7-本地开发ngrok-暴露-webhook)
8. [LINE Developers：Webhook 设置与验证](#8-line-developerswebhook-设置与验证)
9. [收集 LINE User ID（受信者登记）](#9-收集-line-user-id受信者登记)
10. [通知イベント与受信者配置](#10-通知イベント与受信者配置)
11. [测试 LINE 推送](#11-测试-line-推送)
12. [业务联动：切断実績確定发送通知](#12-业务联动切断実績確定发送通知)
13. [生产环境部署要点](#13-生产环境部署要点)
14. [常见问题排查](#14-常见问题排查)
15. [附录：关键 URL 与数据表](#15-附录关键-url-与数据表)

---

## 1. 整体架构

```
┌─────────────┐     Webhook POST      ┌──────────────┐     HTTPS/HTTP     ┌─────────────────┐
│ LINE 平台   │ ────────────────────► │ ngrok（开发） │ ─────────────────► │ Smart-EMAP 后端 │
│ 用户发消息   │                       │ 或公网域名    │                    │ /api/line/webhook│
└─────────────┘                       └──────────────┘                    └────────┬────────┘
                                                                                  │
                                                                                  ▼
                                                                        notification_recipients
                                                                        （自动写入 LINE User ID）

┌─────────────┐     Push API          ┌─────────────────┐
│ 用户手机 LINE│ ◄──────────────────── │ Smart-EMAP 后端 │
│ 收到通知     │   Channel Token       │ 实绩确定 / 测试  │
└─────────────┘                       └─────────────────┘
```

| 组件 | 作用 |
|------|------|
| **Messaging API 频道** | 官方账号推送消息、接收 Webhook |
| **Channel Token** | 调用 LINE Push API 发消息 |
| **Channel Secret** | 校验 Webhook 签名（`X-Line-Signature`） |
| **LINE User ID** | 推送目标（`U` + 32 位十六进制，共 33 字符） |
| **通知センター** | 保存 Token/Secret、管理受信者与事件开关 |
| **Webhook** | 用户加好友/发消息时收集 User ID |

> **注意**：须使用 **Messaging API** 频道，不是 LINE Login 频道。

---

## 2. 前置条件

- Smart-EMAP 后端、前端可正常启动
- MySQL 数据库可连接
- 拥有 Smart-EMAP **管理员**权限（通知センター部分功能需管理员）
- LINE 账号（个人或企业均可，用于登录 [LINE Developers](https://developers.line.biz/console/)）
- 本地调试 Webhook 时需安装 [ngrok](https://ngrok.com/download)（或使用其他 HTTPS 公网隧道）

### 开发环境默认端口（`py startsub.py`）

| 服务 | 地址 |
|------|------|
| 前端 HTTPS | `https://localhost:5010/` |
| 前端 HTTP | `http://localhost:3010/` |
| 后端 API | `https://localhost:8010/docs` |

> `startsub.py` 默认后端为 **HTTPS 8010**。`py start.py` 生产/本番模式后端为 **HTTPS 8005**。

---

## 3. LINE 官方账号与频道创建

### 3.1 登录 LINE Developers

1. 打开 [https://developers.line.biz/console/](https://developers.line.biz/console/)
2. 使用 LINE 账号登录
3. 若无 Provider，先 **Create a new provider**（提供商名称可填公司名）

### 3.2 创建 Messaging API 频道

1. 在 Provider 下点击 **Create a new channel**
2. 选择 **Messaging API**（不要选 LINE Login）
3. 填写频道信息：
   - **频道名称**：如 `Smart-EMAP 通知`
   - **频道描述**：任意
   - **类别**：按实际选择
   - **子类别**：按实际选择
4. 同意条款并创建

### 3.3 关联 LINE 官方账号（重要）

创建后进入频道：

1. 打开 **Messaging API** 标签页
2. 找到 **LINE Official Account** 区域
3. 若提示创建官方账号，按向导完成 **LINE 官方账号** 的创建与关联
4. 记下官方账号名称与 **Basic ID**（后续用户需加该账号为好友）

### 3.4 开启 Messaging API

在 **Messaging API** 标签页确认：

- **Channel access token**：稍后生成（见下一节）
- **Webhook settings**：稍后配置（见第 8 节）
- 建议关闭 **Auto-reply messages** 的自动回复（可选，避免与业务混淆）
- 建议关闭 **Greeting messages**（可选）

---

## 4. 获取 Channel Token / Channel Secret

### 4.1 Channel Secret

1. 进入频道 → **Basic settings** 标签页
2. 找到 **Channel secret**
3. 点击 **Issue** 或复制现有 Secret
4. **妥善保管**，后续填入 Smart-EMAP 通知センター

### 4.2 Channel Access Token（Channel Token）

1. 进入频道 → **Messaging API** 标签页
2. 滚动到 **Channel access token**
3. 点击 **Issue** 生成 **长期 Token**（Long-lived）
4. 复制 Token（只显示一次时请立即保存）

### 4.3 安全提醒

- Token 与 Secret **不要**提交到 Git、不要发到聊天工具
- 若泄露，请在 LINE Developers 中 **重新发行（Reissue）**
- Smart-EMAP 将凭证保存在数据库表 `integration_configs`（`service_type=line`），**不**写入 `.env`

---

## 5. Smart-EMAP 数据库迁移

在 MySQL 中依次执行（若尚未执行）：

```bash
# 示例：使用 mysql 客户端
mysql -u root -p eams_db < backend/database/migrations/49_notification_recipients_email.sql
mysql -u root -p eams_db < backend/database/migrations/50_line_notification_push.sql
```

### 迁移内容摘要

| 迁移文件 | 内容 |
|----------|------|
| `49_...` | `notification_recipients`、`email_send_logs`、切断/面取实绩确定事件与邮件模板 |
| `50_...` | `line_user_id` 字段、`line_send_logs`、默认开启切断/面取事件的 LINE 开关 |

执行后可在库中确认：

```sql
SELECT event_code, event_name, email_enabled, line_enabled, is_active
FROM notification_settings
WHERE event_code IN ('CUTTING_ACTUAL_CONFIRMED', 'CHAMFERING_ACTUAL_CONFIRMED');
```

---

## 6. 通知センター：LINE 外部连携配置

### 6.1 打开页面

1. 登录 Smart-EMAP
2. 菜单：**システム管理** → **通知センター**
3. 路径：`/system/notification`
4. 切换到 **外部連携** 标签页

### 6.2 填写 LINE 配置

| 字段 | 说明 |
|------|------|
| **Channel Token** | 第 4.2 节获取的 Channel access token |
| **Channel Secret** | 第 4.1 节获取的 Channel secret |
| **テスト送信先 User ID** | 测试用 User ID（第 9 节获取后可填） |
| **有効** 开关 | 正式推送时建议打开 |

操作步骤：

1. 填入 **Channel Token**、**Channel Secret**
2. 点击 **保存**（必须保存，Webhook 签名校验从数据库读取 Secret）
3. 页面会显示 **Webhook URL（User ID 収集）**，格式为：
   ```
   https://<你的访问域名>/api/line/webhook
   ```
   本地开发时此域名需通过 ngrok 获得（见第 7 节）

> 保存后 Token/Secret 会以掩码显示，但已持久化到数据库，无需每次重填。

---

## 7. 本地开发：ngrok 暴露 Webhook

LINE Webhook 要求 **HTTPS 公网 URL**。本机 `localhost` 无法被 LINE 直接访问，开发时需用 ngrok。

### 7.1 安装与登录 ngrok（一次性）

1. 从 [https://ngrok.com/download](https://ngrok.com/download) 下载 Windows 版并解压  
   例：`C:\Users\zkily\Desktop\ngrok-v3-stable-windows-amd64\`
2. 注册 ngrok 账号，在 Dashboard 复制 **Authtoken**
3. 配置 token：

```powershell
C:\Users\zkily\Desktop\ngrok-v3-stable-windows-amd64\ngrok.exe config add-authtoken <你的_AUTHTOKEN>
```

### 7.2 启动 Smart-EMAP 后端

**终端 1**：

```powershell
cd C:\Users\zkily\Desktop\Smart-EMAPs
py startsub.py
```

确认输出含：`API  https://localhost:8010/docs`

### 7.3 启动 ngrok（注意 HTTPS）

**终端 2**（`startsub.py` 默认后端为 **HTTPS 8010**，须用下列命令）：

```powershell
C:\Users\zkily\Desktop\ngrok-v3-stable-windows-amd64\ngrok.exe http https://localhost:8010
```

> ❌ 错误：`ngrok http 8010`（会转发到 HTTP，导致 503）  
> ✅ 正确：`ngrok http https://localhost:8010`

若使用 HTTP 模式启动后端：

```powershell
py startsub.py --http
ngrok http 8010
```

若使用 `py start.py`（后端 **8005 HTTPS**）：

```powershell
ngrok http https://localhost:8005
```

### 7.4 记录公网地址

ngrok 启动后示例：

```
Forwarding   https://substance-ream-these.ngrok-free.dev -> https://localhost:8010
```

则 Webhook 完整 URL 为：

```
https://substance-ream-these.ngrok-free.dev/api/line/webhook
```

### 7.5 ngrok 调试面板

浏览器打开 **http://127.0.0.1:4040** 可查看每次 Webhook 请求的状态码与 Body（开发时比终端日志更直观）。

---

## 8. LINE Developers：Webhook 设置与验证

1. 进入 LINE Developers → 你的 **Messaging API** 频道
2. 打开 **Messaging API** 标签页 → **Webhook settings**
3. **Webhook URL** 填入：
   ```
   https://<ngrok子域名>.ngrok-free.dev/api/line/webhook
   ```
   或生产环境：`https://<你的正式域名>/api/line/webhook`
4. 打开 **Use webhook**
5. 点击 **Verify**

### 验证成功条件

| 检查项 | 说明 |
|--------|------|
| 后端正在运行 | `startsub.py` 或 `start.py` 未停止 |
| ngrok 正在运行 | 开发环境隧道窗口保持打开 |
| Channel Secret 已保存 | 通知センター → LINE → **保存** |
| URL 路径正确 | 必须含 `/api/line/webhook` |
| ngrok 协议正确 | HTTPS 后端须用 `ngrok http https://localhost:8010` |

验证成功时 LINE 控制台显示成功；ngrok 面板中 `POST /api/line/webhook` 状态码为 **200**。

> **不要用浏览器直接 GET 打开 Webhook URL** 来测试。Webhook 仅接受 LINE 的 **POST** 请求。

---

## 9. 收集 LINE User ID（受信者登记）

### 9.1 User ID 是什么

- 格式：`U` + 32 位十六进制（**共 33 字符**）
- 示例：`Uaed4244a1aef5283f020ae35021087e9`
- **不是**手机号、LINE 显示名、Basic ID
- 用户须 **先加官方账号为好友**，才能推送消息

### 9.2 自动收集流程（推荐）

1. 在通知センター **通知イベント** 中，为目标事件打开 **LINE** 开关（如 **切断実績確定**）
2. 手机 LINE 搜索并 **添加** 你的官方账号为好友
3. 向官方账号 **发送任意文字消息**（如 `test`）
4. LINE 平台 POST 到 Webhook，后端自动：
   - 解析 `events[].source.userId`
   - 写入 `notification_recipients`（`recipient_type=line`）

### 9.3 如何确认已收到 User ID

| 方式 | 操作 |
|------|------|
| **通知センター** | **メール受信者** 标签页查看是否出现 LINE 受信者 |
| **ngrok 面板** | `http://127.0.0.1:4040` → 最近 POST → Request Body 中 `source.userId` |
| **后端日志文件** | `backend/logs/app.log`（`LOG_LEVEL=INFO` 时） |

> **说明**：`py startsub.py` 终端默认**只显示**含 `ERROR` / `WARNING` 的日志，成功的 `userId=...` **不会**出现在 startsub 终端，属正常现象。

### 9.4 手动添加受信者

若未自动登记，可手动添加：

1. 通知センター → **メール受信者** → **追加**
2. **種別** 选择 **LINE**
3. **LINE User ID** 填入 Webhook 中获得的 `U...`
4. **イベント** 选择 **切断実績確定** 等
5. **有効** 打开 → **保存**

### 9.5 区分两种 ID（易混淆）

Webhook JSON 中：

| 字段 | 含义 |
|------|------|
| `destination` | **Bot（官方账号）** 的 User ID |
| `events[].source.userId` | **发消息的用户** ID ← **登记与推送用这个** |

---

## 10. 通知イベント与受信者配置

### 10.1 通知イベント

路径：通知センター → **イベント通知**

| 事件代码 | 名称 | 说明 |
|----------|------|------|
| `CUTTING_ACTUAL_CONFIRMED` | 切断実績確定 | 切断指示页面实绩确定后 |
| `CHAMFERING_ACTUAL_CONFIRMED` | 面取実績確定 | 面取指示页面实绩确定后 |

每个事件可独立开关：

- **メール**：邮件通知
- **LINE**：LINE 推送
- **有効（ON/OFF）**：事件总开关

### 10.2 メール受信者

路径：通知センター → **メール受信者**

受信者 **種別** 支持：

| 種別 | 用途 |
|------|------|
| ユーザー | 系统用户（邮件走用户邮箱） |
| ロール | 按角色解析收件人 |
| メール | 直接指定邮箱 |
| **LINE** | LINE User ID 推送 |

LINE 受信者须满足：

- `line_user_id` 为合法 `U...` 格式
- 对应 `event_code` 与事件 **LINE** 开关已开启
- **有効** 为 ON

---

## 11. 测试 LINE 推送

### 11.1 通知センター测试发送

1. 外部連携 → LINE
2. 确认 Token、Secret 已 **保存**
3. **テスト送信先 User ID** 填入你的 `U...`（须已加好友）
4. 点击 **テスト送信**
5. 手机 LINE 应收到测试消息

### 11.2 常见测试失败原因

| 现象 | 原因 | 处理 |
|------|------|------|
| 400 `to` invalid | User ID 格式错误 | 使用 `U` 开头 33 位 ID |
| 403 / 不能发送 | 用户未加好友 | 先加官方账号好友 |
| 401 | Token 无效或过期 | 在 LINE Developers 重新 Issue Token 并保存 |
| 按钮无反应 | 未点保存 | 先 **保存** 再测试 |

---

## 12. 业务联动：切断実績確定发送通知

### 12.1 操作路径

1. 打开 **切断・面取指示管理** 画面
2. 在 **切断指示－今日** 区域完成实绩登记
3. 点击 **実績確定**
4. 在结果对话框中查看：
   - 邮件收件人预览
   - LINE 收件人预览
5. 点击 **メール・LINE送信**

### 12.2 发送逻辑

- 仅向已在 **メール受信者** 登记、且事件 **LINE/メール** 开关已开启的收件人发送
- 发送记录写入 `line_send_logs` / `email_send_logs`
- 面取实绩确定（`CHAMFERING_ACTUAL_CONFIRMED`）流程相同

### 12.3 前置检查清单

- [ ] 迁移 49、50 已执行
- [ ] LINE Token、Secret 已保存且 **有効**
- [ ] 目标事件 **LINE** 开关 ON
- [ ] 至少一名 LINE 受信者（自动或手动）
- [ ] 受信者用户已加官方账号好友

---

## 13. 生产环境部署要点

### 13.1 公网 HTTPS 域名

生产环境不使用 ngrok，须：

1. 将 Smart-EMAP API 部署在 **HTTPS 公网域名** 下（如 `https://emap.company.com`）
2. LINE Webhook URL 设为：
   ```
   https://emap.company.com/api/line/webhook
   ```
3. 确保防火墙 / 反向代理将 `/api/line/webhook` 转发到 FastAPI 后端

### 13.2 与开发环境差异

| 项目 | 开发 | 生产 |
|------|------|------|
| 公网入口 | ngrok | 正式域名 + SSL 证书 |
| 后端端口 | 8010（startsub）或 8005（start） | 按部署配置 |
| ngrok | 需保持运行 | 不需要 |

### 13.3 凭证轮换

定期或在泄露后：

1. LINE Developers 重新 Issue Token / Secret
2. 通知センター更新并 **保存**
3. 重新 **Verify** Webhook

---

## 14. 常见问题排查

### 14.1 Webhook Verify 返回 503 Service Unavailable

| 原因 | 处理 |
|------|------|
| 后端未启动 | 运行 `py startsub.py` |
| ngrok 未启动 | 启动 ngrok 隧道 |
| 端口不一致 | ngrok 端口与后端一致（8010 或 8005） |
| HTTPS/HTTP 不匹配 | HTTPS 后端用 `ngrok http https://localhost:8010` |

### 14.2 Webhook Verify 返回 400

| 原因 | 处理 |
|------|------|
| Channel Secret 未保存 | 通知センター → LINE → 保存 |
| Secret 与 LINE 控制台不一致 | 重新复制 Secret 并保存 |
| 签名验证失败 | 查看后端日志 `[LINE Webhook] 署名検証失敗` |

### 14.3 发消息后没有 User ID / 受信者未自动登记

| 原因 | 处理 |
|------|------|
| 事件 LINE 开关未开 | 通知イベント → 打开 LINE |
| Webhook 未启用 | LINE Developers → Use webhook ON |
| 看错终端 | 用 ngrok 4040 面板或通知センター确认 |
| 自动登记仅针对 `line_enabled=true` 的事件 | 先开 LINE 开关再发消息 |

### 14.4 LINE 推送失败

| 原因 | 处理 |
|------|------|
| 未加好友 | 用户须加官方账号 |
| User ID 错误 | 使用 Webhook 获得的 `source.userId` |
| Token 无效 | 重新 Issue 并保存 |
| LINE 未启用 | 外部連携 LINE **有効** 开关 |

### 14.5 ngrok 免费版域名变化

每次重启 ngrok，子域名可能改变 → 须在 LINE Developers **重新填写 Webhook URL** 并 Verify。

### 14.6 `ngrok` 命令找不到

使用完整路径：

```powershell
C:\Users\zkily\Desktop\ngrok-v3-stable-windows-amd64\ngrok.exe http https://localhost:8010
```

或将 ngrok 目录加入系统 `Path` 环境变量。

---

## 15. 附录：关键 URL 与数据表

### 15.1 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/line/webhook` | POST | LINE Webhook（User ID 收集） |
| `/api/system/settings/integrations/line` | GET/PUT | LINE 连携配置 |
| `/api/system/settings/integrations/line/test` | POST | LINE 测试发送 |
| `/api/system/settings/notification-recipients` | CRUD | 受信者管理 |
| `/api/mes/.../confirm-actual/send-email` | POST | 实绩确定后发送邮件+LINE |

### 15.2 数据表

| 表名 | 说明 |
|------|------|
| `integration_configs` | LINE Token/Secret（`service_type=line`） |
| `notification_settings` | 事件与渠道开关 |
| `notification_recipients` | 受信者（含 `line_user_id`） |
| `line_send_logs` | LINE 发送日志 |
| `email_send_logs` | 邮件发送日志 |
| `email_templates` | 邮件模板 |

### 15.3 开发环境快速命令备忘

```powershell
# 终端 1：启动开发环境
cd C:\Users\zkily\Desktop\Smart-EMAPs
py startsub.py

# 终端 2：启动 ngrok（HTTPS 后端）
C:\Users\zkily\Desktop\ngrok-v3-stable-windows-amd64\ngrok.exe http https://localhost:8010

# LINE Webhook URL（示例）
# https://<ngrok子域名>.ngrok-free.dev/api/line/webhook
```

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-16 | 初版：LINE 账号设定 → Webhook → User ID → 实绩通知完整流程 |
