#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仅开发模式：启动后端 (uvicorn --reload) + 前端 Vite 开发服务器。
不与 start.py 的端口冲突（start.py: 后端 8005、开发前端 5000/5001、本番 3005/3004）。
本脚本默认: 后端 8010、前端 HTTPS :5010 + HTTP :3010（本机/局域网）。
可通过环境变量覆盖: DEV_ONLY_BACKEND_PORT, DEV_ONLY_FRONTEND_PORT, DEV_ONLY_FRONTEND_HTTP_PORT

HTTPS 开发（默认，可用 backend/.env 关闭）:
  HTTPS_ENABLED=true（默认；设 START_DISABLE_AUTO_HTTPS=1 则尊重 .env）
  未配置 SSL_CERTFILE/SSL_KEYFILE 时自动生成 backend/certs/dev-lan.*
  局域网手机访问: https://<本机IP>:5010/ ；信任证书见 scripts/trust-dev-lan-cert.ps1

HTTP 局域网开发（无需证书）:
  python startsub.py --http
  或 DEV_ONLY_HTTP_MODE=1 python startsub.py
  前端默认 :5001，局域网访问 http://<本机IP>:5001/

  python startsub.py --http6000
  或 DEV_ONLY_HTTP_MODE=6000 python startsub.py
  前端默认 :6000、后端默认 :8020（避免与默认模式 8010 冲突），局域网 http://<本机IP>:6000/
"""
import argparse
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
    "frontend_dev_http_port": int(os.environ.get("DEV_ONLY_FRONTEND_HTTP_PORT", "3010")),
    "backend_host": "0.0.0.0",
    "backend_scheme": "http",
    "backend_use_https": False,
    "frontend_dev_https": False,
    "frontend_dev_dual": False,
    "http_lan_mode": False,
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


def resolve_network_ip() -> str:
    """LAN 显示用 IP。DEV_LAN_IP 未设置时自动检测本机 IP。"""
    override = os.environ.get("DEV_LAN_IP", "").strip()
    if override:
        return override
    return get_local_ip()


def _configure_console_encoding() -> None:
    """Windows 控制台默认 cp932，含 emoji/中文的 print 会 UnicodeEncodeError。"""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="仅开发模式：启动后端 + 前端 Vite 开发服务器",
    )
    http_group = parser.add_mutually_exclusive_group()
    http_group.add_argument(
        "--http",
        action="store_true",
        help="HTTP 局域网开发：前端 :5001，访问 http://<本机IP>:5001/（无需证书）",
    )
    http_group.add_argument(
        "--http6000",
        action="store_true",
        help="HTTP 局域网开发：前端 :6000，访问 http://<本机IP>:6000/（无需证书）",
    )
    return parser.parse_args()


def resolve_http_lan_port_from_env() -> Optional[int]:
    raw = os.environ.get("DEV_ONLY_HTTP_MODE", "").strip().lower()
    if raw in ("6000",):
        return 6000
    if raw in ("5001", "1", "true", "yes", "on"):
        return 5001
    return None


def apply_http_lan_mode(default_port: int = 5001) -> None:
    """HTTP 局域网开发：关闭 HTTPS，前端默认 default_port。"""
    CONFIG["http_lan_mode"] = True
    CONFIG["frontend_dev_port"] = int(
        os.environ.get("DEV_ONLY_FRONTEND_PORT", str(default_port))
    )
    # :6000 模式默认用 8020 后端，可与默认 HTTPS 模式（8010/5010）并存
    if default_port == 6000 and "DEV_ONLY_BACKEND_PORT" not in os.environ:
        CONFIG["backend_port"] = 8020
    os.environ["START_DISABLE_AUTO_HTTPS"] = "1"
    os.environ["HTTPS_ENABLED"] = "false"


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
        except Exception as e:
            print(f"证书生成失败: {e}（pip install cryptography）", file=sys.stderr)
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


def ensure_port_free(port: int, name: str) -> bool:
    if not is_port_in_use(port):
        return True
    print(f"端口 {port} 占用 ({name})，正在释放...", file=sys.stderr)
    _kill_port_process(port)
    for _ in range(6):
        time.sleep(0.3)
        if not is_port_in_use(port):
            return True
    print(f"错误: 端口 {port} 无法释放 ({name})", file=sys.stderr)
    return False


def _kill_port_process(port: int) -> bool:
    """结束占用端口的进程（静默）。"""
    try:
        if sys.platform == "win32":
            enc = "utf-8"
            try:
                import locale
                enc = locale.getpreferredencoding() or "cp932"
            except Exception:
                pass
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                encoding=enc,
                errors="replace",
            )
            pids = set()
            for line in result.stdout.split("\n"):
                s = line.strip()
                if f":{port}" in s and (
                    "LISTENING" in s.upper() or "リッスン" in s
                ):
                    parts = s.split()
                    if len(parts) >= 5 and parts[-1].isdigit():
                        pids.add(parts[-1])
            for pid in pids:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", pid],
                    capture_output=True,
                )
            time.sleep(0.5)
            return bool(pids)
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
        )
        pids = [p.strip() for p in (result.stdout or "").split("\n") if p.strip().isdigit()]
        for pid in pids:
            subprocess.run(["kill", "-9", pid], capture_output=True)
        if pids:
            time.sleep(0.5)
        return bool(pids)
    except Exception:
        return False


def wait_for_ports(ports: List[int], timeout: float = 90) -> bool:
    pending = {p for p in ports if p > 0}
    if not pending:
        return True
    deadline = time.time() + timeout
    while pending and time.time() < deadline:
        for p in list(pending):
            if is_port_in_use(p):
                pending.discard(p)
        if not pending:
            return True
        time.sleep(0.15)
    return False


def wait_for_port(port: int, timeout: int = 60) -> bool:
    return wait_for_ports([port], timeout=float(timeout))


def signal_handler(sig, frame):
    global should_exit
    should_exit = True
    print("\n正在停止...")
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
                    if line and (
                        "ERROR" in line or "WARNING" in line or "Traceback" in line
                    ):
                        print(f"[backend] {line}")
        except Exception:
            pass

    threading.Thread(target=read_output, daemon=True).start()
    return process


def start_frontend_dev(
    output_buffer: List[str],
    *,
    port: int,
    use_https: bool,
    tag: str = "frontend",
) -> subprocess.Popen:
    be_port = CONFIG["backend_port"]
    fe_scheme = "https" if CONFIG.get("backend_use_https") else "http"
    api_target = f"{fe_scheme}://127.0.0.1:{be_port}"

    npm_cmd = [
        "npm",
        "run",
        "dev",
        "--",
        "--port",
        str(port),
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

    if use_https:
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
    else:
        env["VITE_DEV_HTTPS"] = "false"
        env.pop("VITE_SSL_CERTFILE", None)
        env.pop("VITE_SSL_KEYFILE", None)
        if CONFIG.get("backend_use_https"):
            env["VITE_API_HTTPS"] = "true"
        else:
            env["VITE_API_HTTPS"] = "false"

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
                    if "ready in" in line.lower() or "error" in line.lower():
                        print(f"[{tag}] {line}")
        except Exception:
            pass

    threading.Thread(target=read_output, daemon=True).start()
    return process


def print_ready_banner() -> None:
    nip = (CONFIG.get("network_ip") or "127.0.0.1").strip()
    bp = CONFIG["backend_port"]
    be_scheme = CONFIG.get("backend_scheme", "http")
    fp = CONFIG["frontend_dev_port"]
    http_p = CONFIG.get("frontend_dev_http_port", 3010)

    print()
    print("=" * 52)
    print("开发环境已就绪  (Ctrl+C 停止)")
    if CONFIG.get("http_lan_mode"):
        print(f"  http://localhost:{fp}/")
        if nip:
            print(f"  http://{nip}:{fp}/")
    elif CONFIG.get("frontend_dev_dual"):
        print(f"  https://localhost:{fp}/")
        if nip:
            print(f"  https://{nip}:{fp}/")
        print(f"  http://localhost:{http_p}/")
        if nip:
            print(f"  http://{nip}:{http_p}/")
    elif CONFIG.get("frontend_dev_https"):
        print(f"  https://localhost:{fp}/")
        if nip:
            print(f"  https://{nip}:{fp}/")
    else:
        print(f"  http://localhost:{fp}/")
        if nip:
            print(f"  http://{nip}:{fp}/")
    print(f"  API  {be_scheme}://localhost:{bp}/docs")
    print("=" * 52)
    print()


def main():
    _configure_console_encoding()
    args = parse_args()
    http_port: Optional[int] = None
    if args.http6000:
        http_port = 6000
    elif args.http:
        http_port = 5001
    else:
        http_port = resolve_http_lan_port_from_env()
    if http_port is not None:
        apply_http_lan_mode(http_port)

    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)

    CONFIG["network_ip"] = resolve_network_ip()

    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_DIR / ".env", encoding="utf-8")
    except Exception:
        pass

    if CONFIG.get("http_lan_mode"):
        os.environ["START_DISABLE_AUTO_HTTPS"] = "1"
        os.environ["HTTPS_ENABLED"] = "false"

    if not _env_truthy("START_DISABLE_AUTO_HTTPS"):
        os.environ.setdefault("HTTPS_ENABLED", "true")

    if _env_truthy("HTTPS_ENABLED"):
        ensure_ssl_certificate_files(CONFIG["network_ip"])

    uvicorn_ssl = build_uvicorn_ssl_args()
    CONFIG["backend_use_https"] = bool(uvicorn_ssl)
    CONFIG["frontend_dev_https"] = bool(uvicorn_ssl)
    CONFIG["frontend_dev_dual"] = bool(uvicorn_ssl) and not CONFIG.get("http_lan_mode")
    CONFIG["backend_scheme"] = "https" if uvicorn_ssl else "http"

    bp = CONFIG["backend_port"]
    fp = CONFIG["frontend_dev_port"]
    http_fp = CONFIG["frontend_dev_http_port"]

    ports: List[tuple[int, str]] = [(bp, "后端")]
    if CONFIG.get("http_lan_mode"):
        ports.append((fp, "前端"))
    elif CONFIG.get("frontend_dev_dual"):
        ports.append((fp, "前端HTTPS"))
        ports.append((http_fp, "前端HTTP"))
    else:
        ports.append((fp, "前端"))

    for port, label in ports:
        if not ensure_port_free(port, label):
            if CONFIG.get("http_lan_mode") and CONFIG["frontend_dev_port"] == 6000:
                print(
                    "  提示: 若已有 py startsub.py 在运行，请先停止或设置 DEV_ONLY_BACKEND_PORT=8021",
                    file=sys.stderr,
                )
            sys.exit(1)

    backend_out: List[str] = []
    frontend_out: List[str] = []
    frontend_http_out: List[str] = []

    processes.append(start_backend(backend_out, uvicorn_ssl if uvicorn_ssl else None))

    if CONFIG.get("frontend_dev_dual"):
        processes.append(
            start_frontend_dev(
                frontend_out,
                port=fp,
                use_https=True,
                tag="frontend-https",
            )
        )
        processes.append(
            start_frontend_dev(
                frontend_http_out,
                port=http_fp,
                use_https=False,
                tag="frontend-http",
            )
        )
    else:
        processes.append(
            start_frontend_dev(
                frontend_out,
                port=fp,
                use_https=bool(CONFIG.get("frontend_dev_https")),
                tag="frontend",
            )
        )

    wait_ports = [bp, fp]
    if CONFIG.get("frontend_dev_dual"):
        wait_ports.append(http_fp)

    if not wait_for_ports(wait_ports, timeout=90):
        if not is_port_in_use(bp):
            print("后端启动超时:", file=sys.stderr)
            for line in backend_out[-10:]:
                print(" ", line)
            signal_handler(None, None)
            sys.exit(1)
        if not is_port_in_use(fp):
            print("前端启动超时:", file=sys.stderr)
            for buf in (frontend_out, frontend_http_out):
                for line in buf[-8:]:
                    print(" ", line)
            signal_handler(None, None)
            sys.exit(1)

    print_ready_banner()

    while not should_exit:
        proc_names = ("后端", "前端HTTPS", "前端HTTP", "前端")
        for i, p in enumerate(processes):
            if p is None:
                continue
            if p.poll() is not None:
                name = proc_names[i] if i < len(proc_names) else f"进程{i}"
                print(f"\n{name}已退出 (code: {p.returncode})")
                signal_handler(None, None)
                sys.exit(1)
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(None, None)
