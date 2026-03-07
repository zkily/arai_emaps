# Python 3.14 环境修复说明

## 检查结果摘要

- **Python 3.14 已安装**，位置：`C:\Program Files\Python314\`，运行 `"C:\Program Files\Python314\python.exe" --version` 可得到 `Python 3.14.0`。
- **存在的问题：**
  1. **注册表指向错误路径**：系统里仍把 Python 3.14 记在已不存在的 `C:\Python314\`，导致 `py -3.14` 报错：“Unable to create process using 'C:\Python314\python.exe'”。
  2. **系统 PATH 含无效项**：系统环境变量 Path 中仍有 `C:\Python314\Scripts\` 和 `C:\Python314\`，这两个目录已不存在。
  3. **`python` 命令被应用别名占用**：若未把 `C:\Program Files\Python314` 放在 PATH 前面，系统会优先用“应用执行别名”里的 python，从而打开 Microsoft Store。

## 你需要做的（修复注册表和系统 PATH）

修改注册表和系统 PATH 需要**管理员权限**，请任选一种方式执行一次即可。

### 方式一：用 PowerShell 脚本（推荐）

1. 右键 `fix_python314_env.ps1`
2. 选择 **“使用 PowerShell 运行”**
3. 若提示无法执行脚本，先在“以管理员身份运行”的 PowerShell 里执行：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
4. 再次右键 `fix_python314_env.ps1` → “使用 PowerShell 运行”，或在**以管理员身份打开**的 PowerShell 中执行：
   ```powershell
   cd "C:\Users\zkily\Desktop\Smart-EMAPs"
   .\fix_python314_env.ps1
   ```

### 方式二：用注册表文件

1. 右键 `fix_python314_registry.reg` → **“合并”**（若 UAC 提示，选“是”）。
2. 系统 PATH 仍需手动清理：  
   **设置 → 系统 → 关于 → 高级系统设置 → 环境变量**，在“系统变量”里选中 `Path` → “编辑”，删除：
   - `C:\Python314\Scripts\`
   - `C:\Python314\`
   并确认存在：
   - `C:\Program Files\Python314`
   - `C:\Program Files\Python314\Scripts`
   （没有则添加并确定保存。）

## 修复完成后

- **关闭并重新打开**所有终端（含 Cursor 内置终端）。
- 验证：
  ```powershell
  py -3.14 --version    # 应显示 Python 3.14.0
  python --version     # 应显示 Python 3.14.0
  pip --version        # 应能正常显示 pip 版本
  ```

## 当前已做的无需管理员的操作

- 已将 **用户** PATH 中 `C:\Program Files\Python314` 和 `C:\Program Files\Python314\Scripts` 调整到前面（若上一步的脚本成功执行过，用户 PATH 已包含这两项且靠前）。  
  这样在新开的终端里，`python` 会优先使用本机安装的 3.14，而不是 Store 别名。

完成上述任一种“需要管理员”的修复后，Python 3.14 的环境即可正常使用。
