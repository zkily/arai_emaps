# 构建和部署指南

## 前端构建和启动

### 1. 生成生产构建文件（dist）

在项目根目录或 `frontend` 目录下执行：

```bash
cd frontend
npm run build
```

或者从项目根目录：

```bash
npm run build --prefix frontend
```

构建完成后，会在 `frontend/dist/` 目录下生成生产环境的文件。

### 2. 预览构建后的文件

#### 方法 1: 使用 Vite 预览（推荐用于测试）

```bash
cd frontend
npm run preview
```

或者指定端口和主机：

```bash
npm run serve
```

这将启动一个本地服务器，默认访问地址：
- 本地: `http://localhost:5000`
- 网络: `http://<你的IP>:5000`

#### 方法 2: 使用 Python HTTP 服务器

```bash
cd frontend/dist
python -m http.server 5000
```

或者 Python 3:

```bash
python3 -m http.server 5000
```

#### 方法 3: 使用 Node.js http-server

首先安装 http-server（如果还没有安装）：

```bash
npm install -g http-server
```

然后启动：

```bash
cd frontend/dist
http-server -p 5000 -a 0.0.0.0
```

### 3. 生产环境部署

#### 使用 Nginx（推荐）

1. **安装 Nginx**

   Windows: 下载并安装 [Nginx for Windows](http://nginx.org/en/download.html)

   Linux:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **配置 Nginx**

   编辑 Nginx 配置文件（通常在 `/etc/nginx/sites-available/default` 或 `C:\nginx\conf\nginx.conf`）：

   ```nginx
   server {
       listen 80;
       server_name localhost;  # 或您的域名
       
       # 前端静态文件
       location / {
           root /path/to/Smart-EMAPs/frontend/dist;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
       
       # 后端 API 代理
       location /api {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
       
       # WebSocket 代理
       location /ws {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

3. **启动 Nginx**

   Windows:
   ```bash
   cd C:\nginx
   start nginx
   ```

   Linux:
   ```bash
   sudo systemctl start nginx
   sudo systemctl enable nginx  # 开机自启
   ```

#### 使用 Apache

1. **安装 Apache**

2. **配置 Apache**

   编辑 Apache 配置文件，添加：

   ```apache
   <VirtualHost *:80>
       ServerName localhost
       DocumentRoot /path/to/Smart-EMAPs/frontend/dist
       
       <Directory /path/to/Smart-EMAPs/frontend/dist>
           Options Indexes FollowSymLinks
           AllowOverride All
           Require all granted
       </Directory>
       
       # API 代理
       ProxyPass /api http://localhost:8000/api
       ProxyPassReverse /api http://localhost:8000/api
       
       # WebSocket 代理
       ProxyPass /ws ws://localhost:8000/ws
       ProxyPassReverse /ws ws://localhost:8000/ws
   </VirtualHost>
   ```

## 构建配置说明

### 环境变量

生产环境构建前，可以创建 `frontend/.env.production` 文件：

```env
VITE_API_BASE_URL=/api
```

### 构建优化

Vite 会自动进行以下优化：
- 代码压缩和混淆
- Tree-shaking（移除未使用的代码）
- 资源优化（图片、CSS等）
- 代码分割（按路由分割）

### 构建输出

构建后的 `dist` 目录结构：

```
dist/
├── index.html          # 入口 HTML 文件
├── assets/            # 静态资源
│   ├── index-xxx.js   # JavaScript 文件
│   ├── index-xxx.css  # CSS 文件
│   └── ...            # 其他资源（图片、字体等）
└── ...
```

## 常见问题

### 1. 构建后页面空白

**原因**: 路由配置问题或 API 路径问题

**解决**:
- 确保 `vite.config.ts` 中的 `base` 配置正确
- 检查 API 请求路径是否正确
- 查看浏览器控制台的错误信息

### 2. 构建后 API 请求失败

**原因**: 生产环境 API 地址配置不正确

**解决**:
- 检查 `frontend/.env.production` 文件
- 确保后端服务器正在运行
- 检查 CORS 配置

### 3. WebSocket 连接失败

**原因**: 生产环境 WebSocket 路径配置问题

**解决**:
- 确保反向代理（Nginx/Apache）正确配置了 WebSocket 代理
- 检查 WebSocket URL 构建逻辑

## 快速启动脚本

可以创建一个简单的启动脚本 `start-prod.bat` (Windows) 或 `start-prod.sh` (Linux/Mac):

**Windows (start-prod.bat)**:
```batch
@echo off
echo 构建前端...
cd frontend
call npm run build
echo 启动预览服务器...
call npm run serve
pause
```

**Linux/Mac (start-prod.sh)**:
```bash
#!/bin/bash
echo "构建前端..."
cd frontend
npm run build
echo "启动预览服务器..."
npm run serve
```

## 注意事项

1. **构建前确保依赖已安装**:
   ```bash
   cd frontend
   npm install
   ```

2. **构建后检查文件大小**:
   - 如果 dist 目录过大，可能需要优化代码或资源

3. **生产环境变量**:
   - 不要在生产环境使用开发环境的配置
   - 确保敏感信息不会暴露在前端代码中

4. **HTTPS 配置**:
   - 生产环境建议使用 HTTPS
   - 需要配置 SSL 证书

