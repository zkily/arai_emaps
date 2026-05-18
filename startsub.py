#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仅开发模式：启动后端 (uvicorn --reload) + 前端 Vite 开发服务器。
不与 start.py 的端口冲突（start.py: 后端 8005、开发前端 5000、本番 3005/3004）。
本脚本默认: 后端 8010、前端 5010。可通过环境变量覆盖:
  DEV_ONLY_BACKEND_PORT, DEV_ONLY_FRONTEND_PORT

HTTPS 开发（与 start.py 一致，默认开启，可用 backend/.env 关闭）:
  HTTPS_ENABLED=true（默认；设 START_DISABLE_AUTO_HTTPS=1 则尊重 .env）
  未配置 SSL_CERTFILE/SSL_KEYFILE 时自动生成 backend/certs/dev-lan.*
  局域网手机访问: https://<本机IP>:5010/ ；信任证书见 scripts/trust-dev-lan-cert.ps1
"""
import os
import sys
import subprocess
import signal
import time
import json
import socket
from pathlib import Path
from typing import List, Optional
import threading

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CERTS_DIR = BACKEND_DIR / "certs"
DEFAULT_SSL_CERT = CERTS_DIR / "dev-lan.crt"
DEFAULT_SSL_KEY = CERTS_DIR / "dev-lan.key"
DEFAULT_SSL_META = CERTS_DIR / "dev-lan.meta.json"

processes: List[subprocess.Popen] = []
should_exit = False

# 与 start.py CONFIG 错开，避免同时运行两套脚本时抢端口
CONFIG = {
    "backend_port": int(os.environ.get("DEV_ONLY_BACKEND_PORT", "8010")),
    "frontend_dev_port": int(os.environ.get("DEV_ONLY_FRONTEND_PORT", "5010")),
    "backend_host": "0.0.0.0",
    "backend_scheme": "http",
    "backend_use_https": False,
    "frontend_dev_https": False,
    "network_ip": "127.0.0.1",
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


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_self_signed_lan_cert(cert_path: Path, key_path: Path, hostnames: List[str]) -> None:
    import datetime
    import ipaddress

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    primary = next((h for h in hostnames if h and h != "127.0.0.1"), "localhost")
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, primary)])

    san: List = []
    seen: set = set()
    for raw in hostnames:
        h = (raw or "").strip()
        if not h or h in seen:
            continue
        seen.add(h)
        try:
            san.append(x509.IPAddress(ipaddress.ip_address(h)))
        except ValueError:
            san.append(x509.DNSName(h))

    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=825))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def ensure_ssl_certificate_files(network_ip: str) -> bool:
    """HTTPS_ENABLED 时自动生成或复用 backend/certs/dev-lan.*"""
    if not _env_truthy("HTTPS_ENABLED"):
        return False

    cert_env = os.environ.get("SSL_CERTFILE", "").strip()
    key_env = os.environ.get("SSL_KEYFILE", "").strip()
    if cert_env and key_env:
        cpath = _resolve_ssl_path(cert_env)
        kpath = _resolve_ssl_path(key_env)
        if cpath.is_file() and kpath.is_file():
            return True
        print(
            f"⚠️  配置的证书不存在: cert={cpath} key={kpath}，将尝试自动生成",
            file=sys.stderr,
        )

    san_hosts = ["localhost", "127.0.0.1"]
    nip = (network_ip or "").strip()
    if nip and nip not in san_hosts:
        san_hosts.append(nip)

    need_gen = True
    if DEFAULT_SSL_CERT.is_file() and DEFAULT_SSL_KEY.is_file() and DEFAULT_SSL_META.is_file():
        try:
            meta = json.loads(DEFAULT_SSL_META.read_text(encoding="utf-8"))
            if meta.get("san") == san_hosts:
                need_gen = False
        except Exception:
            need_gen = True

    if need_gen:
        try:
            generate_self_signed_lan_cert(DEFAULT_SSL_CERT, DEFAULT_SSL_KEY, san_hosts)
            DEFAULT_SSL_META.write_text(
                json.dumps({"san": san_hosts, "generated_at": time.time()}, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"🔐 已生成 LAN 开发证书: {DEFAULT_SSL_CERT}")
            print(f"   SAN: {', '.join(san_hosts)}（手机首次访问需在浏览器中信任证书）")
        except Exception as e:
            print(f"❌ 证书自动生成失败: {e}", file=sys.stderr)
            print("   请执行: pip install cryptography", file=sys.stderr)
            return False

    os.environ["SSL_CERTFILE"] = str(DEFAULT_SSL_CERT.relative_to(BACKEND_DIR)).replace("\\", "/")
    os.environ["SSL_KEYFILE"] = str(DEFAULT_SSL_KEY.relative_to(BACKEND_DIR)).replace("\\", "/")
    return True


def build_uvicorn_ssl_args() -> List[str]:
    if not _env_truthy("HTTPS_ENABLED"):
        return []
    cert = os.environ.get("SSL_CERTFILE", "").strip()
    key = os.environ.get("SSL_KEYFILE", "").strip()
    if not cert or not key:
        print("⚠️  HTTPS_ENABLED 已开启但 SSL_CERTFILE/SSL_KEYFILE 未配置，后端将使用 HTTP")
        return []
    cpath = _resolve_ssl_path(cert)
    kpath = _resolve_ssl_path(key)
    if not cpath.is_file() or not kpath.is_file():
        print(f"⚠️  找不到证书: cert={cpath} key={kpath}，后端将使用 HTTP")
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

    if CONFIG.get("backend_use_https") or CONFIG.get("frontend_dev_https"):
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

    CONFIG["network_ip"] = get_local_ip()

    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_DIR / ".env", encoding="utf-8")
    except Exception:
        pass

    if not _env_truthy("START_DISABLE_AUTO_HTTPS"):
        os.environ.setdefault("HTTPS_ENABLED", "true")

    if _env_truthy("HTTPS_ENABLED"):
        ensure_ssl_certificate_files(CONFIG["network_ip"])
        if not _env_truthy("CORS_ALLOW_ALL"):
            print(
                "💡 若局域网 https 访问 API 被拒，请在 backend/.env 设置 CORS_ALLOW_ALL=true"
            )

    uvicorn_ssl = build_uvicorn_ssl_args()
    CONFIG["backend_use_https"] = bool(uvicorn_ssl)
    CONFIG["frontend_dev_https"] = bool(uvicorn_ssl)
    CONFIG["backend_scheme"] = "https" if uvicorn_ssl else "http"

    bp = CONFIG["backend_port"]
    fp = CONFIG["frontend_dev_port"]

    if is_port_in_use(bp):
        print(f"错误: 端口 {bp} 已被占用（后端）。可设置环境变量 DEV_ONLY_BACKEND_PORT 改用其他端口。")
        sys.exit(1)
    if is_port_in_use(fp):
        print(f"错误: 端口 {fp} 已被占用（前端）。可设置环境变量 DEV_ONLY_FRONTEND_PORT 改用其他端口。")
        sys.exit(1)

    fe_scheme = "https" if CONFIG.get("frontend_dev_https") else "http"
    print("\n仅开发模式启动（无本番 dist、无 start.py 同端口）")
    print(f"  后端: {CONFIG['backend_scheme']}://0.0.0.0:{bp}")
    print(f"  前端: {fe_scheme}://0.0.0.0:{fp}（API 代理 → 本脚本后端 {bp}）")
    if CONFIG.get("frontend_dev_https"):
        nip = CONFIG["network_ip"]
        print(f"  局域网: {fe_scheme}://{nip}:{fp}/")
    print()

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

    fe_scheme = "https" if CONFIG.get("frontend_dev_https") else "http"
    nip = CONFIG["network_ip"]
    print("\n" + "=" * 60)
    print("开发环境已就绪（Ctrl+C 停止）")
    print(f"  前端: {fe_scheme}://localhost:{fp}/")
    if nip and nip != "127.0.0.1":
        print(f"  前端 (LAN): {fe_scheme}://{nip}:{fp}/")
    print(f"  API:  {CONFIG['backend_scheme']}://localhost:{bp}/docs")
    if CONFIG.get("frontend_dev_https"):
        print("  证书: backend/certs/dev-lan.crt（Windows 信任: scripts/trust-dev-lan-cert.ps1）")
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
