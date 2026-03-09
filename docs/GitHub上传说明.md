# 项目代码上传到 GitHub 操作说明

本文档说明如何将 Smart-EMAPs 项目代码上传或推送到 GitHub。

---

## 一、前置准备

### 1. 安装 Git

- **Windows**：从 [https://git-scm.com/download/win](https://git-scm.com/download/win) 下载并安装。
- 安装时建议勾选「Add Git to PATH」。

### 2. 注册 GitHub 账号

- 打开 [https://github.com](https://github.com)，注册账号（若尚未注册）。

### 3. 配置 Git 用户信息（首次使用需配置一次）

在命令行中执行：

```bash
git config --global user.name "zkily"
git config --global user.email "chogai136228508@gmail.com"
```

---

## 二、本仓库已关联的远程地址

当前项目已配置的远程仓库：

- **远程名称**：`origin`
- **地址**：`https://github.com/zkily/arai_emaps.git`

查看远程：

```bash
git remote -v
```

---

## 三、日常上传流程（推荐）

在项目根目录（如 `C:\Users\你的用户名\Desktop\Smart-EMAPs`）打开终端（PowerShell 或 CMD），按顺序执行：

### 步骤 1：进入项目目录

```bash
cd C:\Users\你的用户名\Desktop\Smart-EMAPs
```

（请将路径改为你电脑上的实际路径。）

### 步骤 2：查看修改状态

```bash
git status
```

- 会列出「已修改」「未跟踪」的文件，便于确认要提交的内容。

### 步骤 3：添加要提交的文件

**方式 A：添加所有变更（常用）**

```bash
git add .
```

**方式 B：只添加指定文件或目录**

```bash
git add frontend/src/views/erp/purchase/material/
git add backend/app/modules/material/
```

### 步骤 4：提交到本地仓库

```bash
git commit -m "简短描述本次修改内容"
```

示例：

```bash
git commit -m "feat: 材料管理模块 - 前端页面与后端API"
```

### 步骤 5：推送到 GitHub

**若当前分支已与远程关联（如 `origin/2026-02-24-15ur-cb36a`）：**

```bash
git push origin 当前分支名
```

例如：

```bash
git push origin 2026-02-24-15ur-cb36a
```

**若当前是主分支且远程分支名为 `main`：**

```bash
git push -u origin main
```

**若当前是主分支且远程分支名为 `master`：**

```bash
git push -u origin master
```

首次推送可加 `-u`，之后同一分支可直接执行 `git push`。

---

## 四、首次从本机「已有文件夹」推到新仓库

若 GitHub 上已建好空仓库（如 `zkily/arai_emaps`），本机是已有项目目录：

```bash
cd 项目根目录路径
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/zkily/arai_emaps.git
git push -u origin main
```

若仓库已存在且本地已有 `git init` 和提交记录，只需确认 `remote` 并推送：

```bash
git remote add origin https://github.com/zkily/arai_emaps.git
git push -u origin main
```

（若已存在 `origin`，可先 `git remote remove origin` 再 `add`，或直接修改地址。）

---

## 五、认证方式（推送时需登录 GitHub）

### 方式 1：HTTPS + 个人访问令牌（推荐）

1. GitHub 网页：**Settings → Developer settings → Personal access tokens**，生成 Token。
2. 勾选权限：至少包含 `repo`。
3. 推送时，密码处**输入 Token**，不要用账号密码。

### 方式 2：SSH

1. 生成密钥：`ssh-keygen -t ed25519 -C "你的邮箱"`
2. 将 `id_ed25519.pub` 内容添加到 GitHub：**Settings → SSH and GPG keys**。
3. 将远程改为 SSH 地址再推送：

   ```bash
   git remote set-url origin git@github.com:zkily/arai_emaps.git
   git push origin 分支名
   ```

---

## 六、常用命令速查

| 操作           | 命令 |
|----------------|------|
| 查看状态       | `git status` |
| 添加所有变更   | `git add .` |
| 提交           | `git commit -m "说明"` |
| 推送到远程     | `git push origin 分支名` |
| 拉取远程更新   | `git pull origin 分支名` |
| 查看当前分支   | `git branch` |
| 查看远程地址   | `git remote -v` |

---

## 七、注意事项

1. **提交前**：确认不要提交敏感信息（如 `.env`、密钥），本项目 `.gitignore` 已忽略常见敏感与临时文件。
2. **推送失败**：若提示权限或认证错误，请检查 Token/SSH 配置；若提示「远程有新提交」，先执行 `git pull origin 分支名` 再 `git push`。
3. **分支名**：推送时 `分支名` 需与本地当前分支一致（如 `git branch` 显示的 `* 当前分支`）。

按上述步骤即可将项目代码上传或更新到 GitHub。若仓库地址或分支名不同，将文档中的 `zkily/arai_emaps` 和分支名替换为你的实际信息即可。


echo "# arai_emaps" >> README.md
git add .
git commit -m "first commit"
git push -u origin main