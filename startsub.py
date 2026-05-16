#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仅开发模式：启动后端 (uvicorn --reload) + 前端 Vite 开发服务器。
不与 start.py 的端口冲突（start.py: 后端 8005、开发前端 5000、本番 3005/3004）。
本脚本默认: 后端 8010、前端 5010。可通过环境变量覆盖:
  DEV_ONLY_BACKEND_PORT, DEV_ONLY_FRONTEND_PORT
"""
import os
import sys
import subprocess
import signal
import time
import socket
from pathlib import Path
from typing import List, Optional
import threading

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

processes: List[subprocess.Popen] = []
should_exit = False

# 与 start.py CONFIG 错开，避免同时运行两套脚本时抢端口
CONFIG = {
    "backend_port": int(os.environ.get("DEV_ONLY_BACKEND_PORT", "8010")),
    "frontend_dev_port": int(os.environ.get("DEV_ONLY_FRONTEND_PORT", "5010")),
    "backend_host": "0.0.0.0",
    "backend_scheme": "http",
    "backend_use_https": False,
}


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _resolve_ssl_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs.strip())
    if p.is_file():
        return p
    cand = BACKEND_DIR / p
    if cand.is_file():
        return cand
    cand = PROJECT_ROOT / p
    if cand.is_file():
        return cand
    return p


def build_uvicorn_ssl_args() -> List[str]:
    if not _env_truthy("HTTPS_ENABLED"):
        return []
    cert = os.environ.get("SSL_CERTFILE", "").strip()
    key = os.environ.get("SSL_KEYFILE", "").strip()
    if not cert or not key:
        return []
    cpath = _resolve_ssl_path(cert)
    kpath = _resolve_ssl_path(key)
    if not cpath.is_file() or not kpath.is_file():
        return []
    return ["--ssl-certfile", str(cpath.resolve()), "--ssl-keyfile", str(kpath.resolve())]


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def wait_for_port(port: int, timeout: int = 60) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def signal_handler(sig, frame):
    global should_exit
    should_exit = True
    print("\n正在停止开发服务器...")
    for p in processes:
        if p is None:
            continue
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                    capture_output=True,
                )
            else:
                p.terminate()
                p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("已停止。\n")
    sys.exit(0)


def start_backend(output_buffer: List[str], ssl_args: Optional[List[str]] = None) -> subprocess.Popen:
    if sys.platform == "win32":
        python_path = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    else:
        python_path = BACKEND_DIR / "venv" / "bin" / "python"
    if not python_path.exists():
        python_path = Path(sys.executable)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        str(python_path),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        CONFIG["backend_host"],
        "--port",
        str(CONFIG["backend_port"]),
        "--reload",
        "--no-access-log",
        "--log-level",
        "warning",
    ]
    if ssl_args:
        cmd.extend(ssl_args)

    process = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
        encoding="utf-8",
        errors="replace",
    )

    def read_output():
        try:
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    if not line:
                        break
                    line = line.rstrip()
                    output_buffer.append(line)
                    if line:
                        print(f"[backend] {line}")
        except Exception:
            pass

    threading.Thread(target=read_output, daemon=True).start()
    return process


def start_frontend_dev(output_buffer: List[str]) -> subprocess.Popen:
    be_port = CONFIG["backend_port"]
    fe_scheme = "https" if CONFIG.get("backend_use_https") else "http"
    api_target = f"{fe_scheme}://127.0.0.1:{be_port}"

    npm_cmd = [
        "npm",
        "run",
        "dev",
        "--",
        "--port",
        str(CONFIG["frontend_dev_port"]),
        "--host",
        "0.0.0.0",
    ]
    env = os.environ.copy()
    env["VITE_API_PROXY_TARGET"] = api_target
    env["VITE_WS_PROXY_TARGET"] = (
        "wss://" + api_target.removeprefix("https://")
        if api_target.startswith("https://")
        else "ws://" + api_target.removeprefix("http://")
    )

    if CONFIG.get("backend_use_https"):
        env["VITE_API_HTTPS"] = "true"
        env["VITE_DEV_HTTPS"] = "true"
        cert = os.environ.get("SSL_CERTFILE", "").strip()
        key = os.environ.get("SSL_KEYFILE", "").strip()
        if cert:
            cp = _resolve_ssl_path(cert)
            if cp.is_file():
                env["VITE_SSL_CERTFILE"] = str(cp.resolve())
        if key:
            kp = _resolve_ssl_path(key)
            if kp.is_file():
                env["VITE_SSL_KEYFILE"] = str(kp.resolve())

    if sys.platform == "win32":
        process = subprocess.Popen(
            ["cmd.exe", "/c"] + npm_cmd,
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            encoding="utf-8",
            errors="replace",
        )
    else:
        process = subprocess.Popen(
            npm_cmd,
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            encoding="utf-8",
            errors="replace",
        )

    def read_output():
        try:
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    if not line:
                        break
                    line = line.rstrip()
                    output_buffer.append(line)
                    if line:
                        print(f"[frontend] {line}")
        except Exception:
            pass

    threading.Thread(target=read_output, daemon=True).start()
    return process


def main():
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)

    bp = CONFIG["backend_port"]
    fp = CONFIG["frontend_dev_port"]

    if is_port_in_use(bp):
        print(f"错误: 端口 {bp} 已被占用（后端）。可设置环境变量 DEV_ONLY_BACKEND_PORT 改用其他端口。")
        sys.exit(1)
    if is_port_in_use(fp):
        print(f"错误: 端口 {fp} 已被占用（前端）。可设置环境变量 DEV_ONLY_FRONTEND_PORT 改用其他端口。")
        sys.exit(1)

    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_DIR / ".env", encoding="utf-8")
    except Exception:
        pass

    uvicorn_ssl = build_uvicorn_ssl_args()
    CONFIG["backend_use_https"] = bool(uvicorn_ssl)
    CONFIG["backend_scheme"] = "https" if uvicorn_ssl else "http"

    print("\n仅开发模式启动（无本番 dist、无 start.py 同端口）")
    print(f"  后端: {CONFIG['backend_scheme']}://0.0.0.0:{bp}")
    print(f"  前端: npm run dev → 端口 {fp}（API 代理 → 本脚本后端 {bp}）\n")

    backend_out: List[str] = []
    frontend_out: List[str] = []

    processes.append(start_backend(backend_out, uvicorn_ssl if uvicorn_ssl else None))
    time.sleep(0.5)
    processes.append(start_frontend_dev(frontend_out))

    print("等待服务就绪...")
    if not wait_for_port(bp, timeout=30):
        print("后端启动超时。最近输出:")
        for line in backend_out[-15:]:
            print(" ", line)
        signal_handler(None, None)
        sys.exit(1)
    if not wait_for_port(fp, timeout=90):
        print("前端启动超时。最近输出:")
        for line in frontend_out[-15:]:
            print(" ", line)
        signal_handler(None, None)
        sys.exit(1)

    fe_scheme = "https" if CONFIG.get("backend_use_https") else "http"
    print("\n" + "=" * 60)
    print("开发环境已就绪（Ctrl+C 停止）")
    print(f"  前端: {fe_scheme}://localhost:{fp}/")
    print(f"  API:  {CONFIG['backend_scheme']}://localhost:{bp}/docs")
    print("=" * 60 + "\n")

    while not should_exit:
        for i, p in enumerate(processes):
            if p is None:
                continue
            if p.poll() is not None:
                name = "后端" if i == 0 else "前端"
                print(f"\n{name}进程已退出 (code: {p.returncode})")
                signal_handler(None, None)
                sys.exit(1)
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(None, None)
