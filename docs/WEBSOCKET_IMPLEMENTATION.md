# WebSocket 实时推送功能实现说明

## 功能概述

实现了基于 WebSocket 的实时推送功能，用于单设备登录检测。当用户在另一台设备登录时，当前设备会立即收到通知并被强制退出。

## 架构设计

### 后端实现

1. **WebSocket 端点** (`backend/app/api/websocket.py`)
   - 路径: `/ws`
   - 功能: 管理 WebSocket 连接，处理实时消息推送
   - 连接管理: 使用字典 `active_connections` 存储每个用户的活跃连接

2. **登录时通知** (`backend/app/api/auth.py`)
   - 当用户登录时，检查是否有旧的 token
   - 如果有旧 token（表示之前有设备登录），通过 WebSocket 通知所有旧连接
   - 通知消息类型: `force_logout`

### 前端实现

1. **WebSocket 工具类** (`frontend/src/utils/websocket.ts`)
   - 自动连接/重连机制
   - 消息处理（强制退出通知）
   - 连接状态管理

2. **集成点**
   - `App.vue`: 应用启动时建立 WebSocket 连接
   - `Login.vue`: 登录成功后建立 WebSocket 连接
   - `stores/user.ts`: 登出时断开 WebSocket 连接

## 工作流程

1. **用户登录**
   ```
   用户A在设备1登录
   → 生成新 token
   → 保存到数据库 (last_login_token)
   → 建立 WebSocket 连接
   ```

2. **另一设备登录**
   ```
   用户A在设备2登录
   → 生成新 token
   → 更新数据库 (last_login_token)
   → 检测到旧 token 存在
   → 通过 WebSocket 通知设备1
   → 设备1收到 force_logout 消息
   → 设备1显示提示并退出登录
   ```

3. **实时检测**
   - WebSocket 连接保持活跃
   - 服务器主动推送消息
   - 无需轮询，零延迟

## 性能优势

### 相比轮询方式

| 特性 | 轮询方式 | WebSocket 方式 |
|------|---------|---------------|
| 延迟 | 10-60秒 | 实时（<1秒） |
| 服务器负载 | 每30秒1次请求 | 仅在有事件时推送 |
| 网络流量 | 持续请求 | 仅推送消息时 |
| 用户体验 | 延迟检测 | 即时响应 |

### 资源消耗

- **WebSocket 连接**: 每个连接约 2-4KB 内存
- **消息推送**: 仅在有事件时发送（约 100-200 字节）
- **网络流量**: 几乎为零（仅心跳包）

## 配置说明

### 后端配置

无需额外配置，WebSocket 端点自动启用。

### 前端配置

Vite 配置已添加 WebSocket 代理 (`frontend/vite.config.ts`):

```typescript
proxy: {
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true,
    changeOrigin: true,
  },
}
```

## 消息格式

### 连接成功消息
```json
{
  "type": "connected",
  "message": "WebSocket接続が確立されました"
}
```

### 强制退出消息
```json
{
  "type": "force_logout",
  "message": "このアカウントは他のデバイスでログインされています。再度ログインしてください。",
  "reason": "other_device_login"
}
```

### 心跳消息
```json
{
  "type": "pong",
  "message": "接続中"
}
```

## 自动重连机制

- **最大重连次数**: 5次
- **重连延迟**: 3秒
- **触发条件**: 连接意外断开且用户仍处于登录状态

## 故障处理

### WebSocket 连接失败

如果 WebSocket 连接失败，系统会自动降级到轮询模式：
- 每 60 秒检查一次 token 有效性
- 确保功能仍然可用

### 页面可见性优化

- 页面隐藏时：停止所有检查（包括轮询）
- 页面显示时：立即检查 + 重新建立 WebSocket 连接

## 测试方法

1. **单设备登录测试**
   - 在设备1登录
   - 检查浏览器控制台，应看到 `[WebSocket] Connected`

2. **多设备登录测试**
   - 在设备1登录
   - 在设备2使用相同账号登录
   - 设备1应立即收到通知并退出

3. **网络断开测试**
   - 登录后断开网络
   - 重新连接网络
   - WebSocket 应自动重连

## 日志输出

### 后端日志
```
[WebSocket] User zkily connected. Total connections: 1
[WebSocket] Sent force_logout message to zkily
[WebSocket] User zkily disconnected. Remaining connections: 0
```

### 前端日志
```
[WebSocket] Connecting to: ws://localhost:5000/ws?token=***
[WebSocket] Connected
[WebSocket] Received message: {type: "force_logout", ...}
[WebSocket] Force logout: このアカウントは他のデバイスでログインされています...
```

## 注意事项

1. **防火墙**: 确保 WebSocket 端口（与 HTTP 相同）未被阻止
2. **代理服务器**: 如果使用反向代理，需要支持 WebSocket 升级
3. **浏览器兼容性**: 现代浏览器均支持 WebSocket
4. **连接数限制**: 每个用户可以有多个连接（多标签页），系统会自动管理

## 未来扩展

可以基于此 WebSocket 基础设施实现：
- 实时通知系统
- 在线状态显示
- 实时数据更新（生产进度、库存变化等）
- 聊天/消息功能

