#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smart-EMAP 起動スクリプト
バックエンド + 本番 dist（HTTP :3005 / HTTPS :5005）を起動します。
開発用 Vite は startsub.py を使用してください。
"""
import os
import sys
import subprocess
import signal
import time
import socket
import json
from pathlib import Path
from typing import Any, List, Optional
import threading
import http.server
import socketserver
import ssl

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
CERTS_DIR = BACKEND_DIR / "certs"
DEFAULT_SSL_CERT = CERTS_DIR / "dev-lan.crt"
DEFAULT_SSL_KEY = CERTS_DIR / "dev-lan.key"
DEFAULT_SSL_META = CERTS_DIR / "dev-lan.meta.json"

processes: List[subprocess.Popen] = []
should_exit = False
file_watcher_process_index: Optional[int] = None
PROCESS_NAMES = (
    "バックエンド",
    "ファイル監視",
)
production_httpds: List[Any] = []  # 本番 dist サーバー（複数ポート時は複数。signal で shutdown）
production_httpds_lock = threading.Lock()
_prod_static_ssl_ctx: Optional[Any] = None  # main で設定。dist HTTPS 用 SSLContext

# 設定
CONFIG = {
    "backend_port": 8005,
    "frontend_prod_https_port": 5005,
    # HTTPS 有効時: 5005=TLS、3005=プレーン HTTP（同一 TCP ポートに HTTP/HTTPS 併用不可）
    "frontend_prod_http_port": 3005,
    "backend_host": "0.0.0.0",
    # 起動時に自動検出したローカルIPを設定
    "production_ip": "127.0.0.1",
    # HTTPS_ENABLED + 証明書が有効なとき https
    "backend_scheme": "http",
    "backend_use_https": False,
    # dist が HTTPS で待ち受け（証明書あり。バックエンド TLS とは独立し得る）
    "frontend_prod_https": False,
    "dist_placeholder": False,
}

class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


def _configure_console_encoding() -> None:
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def print_color(message: str, color: str = Colors.RESET):
    """カラー出力"""
    print(f"{color}{message}{Colors.RESET}")


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _resolve_ssl_path(rel_or_abs: str) -> Path:
    """SSL パス: 絶対パス、または backend/・プロジェクトルートからの相対"""
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


def generate_self_signed_lan_cert(cert_path: Path, key_path: Path, hostnames: List[str]) -> None:
    """LAN / localhost 向け自己署名証明書（cryptography）"""
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

    san: List[x509.GeneralName] = []
    seen: set[str] = set()
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
    """
    HTTPS_ENABLED 時、SSL_* 未設定またはファイル欠落なら backend/certs/dev-lan.* を自動生成。
    戻り値: 証明書が利用可能なら True
    """
    if not _env_truthy("HTTPS_ENABLED"):
        return False

    cert_env = os.environ.get("SSL_CERTFILE", "").strip()
    key_env = os.environ.get("SSL_KEYFILE", "").strip()
    if cert_env and key_env:
        cpath = _resolve_ssl_path(cert_env)
        kpath = _resolve_ssl_path(key_env)
        if cpath.is_file() and kpath.is_file():
            return True

    san_hosts = ssl_san_hosts(network_ip)

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
            print_color(f"证书生成失败: {e}（pip install cryptography）", Colors.RED)
            return False

    os.environ["SSL_CERTFILE"] = str(DEFAULT_SSL_CERT.relative_to(BACKEND_DIR)).replace("\\", "/")
    os.environ["SSL_KEYFILE"] = str(DEFAULT_SSL_KEY.relative_to(BACKEND_DIR)).replace("\\", "/")
    return True


def ensure_prod_dist_available(network_ip: str) -> bool:
    """
    frontend/dist が無い場合、HTTPS:5005 を起動できるよう最小 index を配置。
    本番ビルド済みの dist がある場合はそのまま利用。
    """
    index = DIST_DIR / "index.html"
    if index.is_file():
        return True

    dev_port = CONFIG["frontend_prod_https_port"]
    http_port = CONFIG["frontend_prod_http_port"]
    try:
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        lan = (network_ip or "127.0.0.1").strip()
        https_url = f"https://{lan}:{dev_port}/"
        http_url = f"http://{lan}:{http_port}/"
        html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Smart-EMAP — dist 未ビルド</title></head>
<body style="font-family:sans-serif;padding:2rem;max-width:40rem">
<h1>Smart-EMAP</h1>
<p>frontend/dist が未ビルドです。以下を実行してからページを再読み込みしてください。</p>
<pre style="background:#f4f4f4;padding:1rem">cd frontend\nnpm run build</pre>
<p>ビルド後の URL:</p>
<ul>
<li><a href="{https_url}">{https_url}</a></li>
<li><a href="{http_url}">{http_url}</a></li>
</ul>
</body></html>"""
        index.write_text(html, encoding="utf-8")
        CONFIG["dist_placeholder"] = True
        return True
    except Exception as e:
        print_color(f"dist 占位页创建失败: {e}", Colors.RED)
        return False


def build_uvicorn_ssl_args() -> List[str]:
    """HTTPS_ENABLED かつ証明書が揃うとき uvicorn 用 --ssl-* を返す"""
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


def build_prod_static_ssl_context():
    """dist 静的サーバー用 SSL。HTTPS_ENABLED かつ証明書が揃えばバックエンド TLS なしでも使用可。"""
    if not _env_truthy("HTTPS_ENABLED"):
        return None
    import ssl as _ssl

    cert = os.environ.get("SSL_CERTFILE", "").strip()
    key = os.environ.get("SSL_KEYFILE", "").strip()
    if not cert or not key:
        return None
    cpath = _resolve_ssl_path(cert)
    kpath = _resolve_ssl_path(key)
    if not cpath.is_file() or not kpath.is_file():
        return None
    ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_SERVER)
    try:
        ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
    except (AttributeError, ValueError):
        pass
    ctx.load_cert_chain(str(cpath.resolve()), str(kpath.resolve()))
    return ctx


def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """指定されたポートが使用中かチェック"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def get_local_ip() -> str:
    """ローカルネットワークのIPアドレスを取得"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def resolve_network_ip() -> str:
    """LAN 表示用 IP。DEV_LAN_IP 未設定時は本机 IP を自動検出。"""
    override = os.environ.get("DEV_LAN_IP", "").strip()
    if override:
        return override
    return get_local_ip()


def ssl_san_hosts(network_ip: str) -> List[str]:
    """証明書 SAN 用ホスト一覧（localhost / 127.0.0.1 / 設定・検出 LAN IP）"""
    hosts = ["localhost", "127.0.0.1"]
    for raw in (network_ip, get_local_ip()):
        ip = (raw or "").strip()
        if ip and ip not in hosts:
            hosts.append(ip)
    return hosts


def _win_encoding():
    """Windows コンソールのエンコーディング（taskkill 等の出力用）"""
    if sys.platform != "win32":
        return "utf-8"
    try:
        import locale
        return locale.getpreferredencoding() or "cp932"
    except Exception:
        return "cp932"


def kill_port_process(port: int) -> bool:
    """指定されたポートを使用しているプロセスを強制終了"""
    try:
        if sys.platform == "win32":
            enc = _win_encoding()
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                encoding=enc,
                errors='replace'
            )
            pids_to_kill = set()
            for line in result.stdout.split('\n'):
                line_stripped = line.strip()
                if f":{port}" in line_stripped and (
                    "LISTENING" in line_stripped.upper() or "ESTABLISHED" in line_stripped.upper()
                    or "リッスン" in line_stripped or "接続" in line_stripped
                ):
                    parts = line_stripped.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 0:
                            pids_to_kill.add(pid)
            if not pids_to_kill:
                return False
            killed_any = False
            for pid in pids_to_kill:
                r = subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", pid],
                    capture_output=True,
                    text=True,
                    encoding=enc,
                    errors='replace'
                )
                if r.returncode == 0:
                    killed_any = True
                else:
                    r2 = subprocess.run(
                        ["taskkill", "/F", "/PID", pid],
                        capture_output=True,
                        text=True,
                        encoding=enc,
                        errors='replace'
                    )
                    if r2.returncode == 0:
                        killed_any = True
                time.sleep(0.3)
            time.sleep(0.5)
            return killed_any
        else:
            # Linux/Mac: lsof で PID 取得して kill -9
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True
            )
            pids = result.stdout.strip().split('\n') if result.stdout else []
            killed_any = False
            for pid in pids:
                pid = pid.strip()
                if pid.isdigit():
                    subprocess.run(["kill", "-9", pid], capture_output=True)
                    killed_any = True
                    time.sleep(0.2)
            if killed_any:
                time.sleep(0.5)
            return killed_any
    except Exception:
        return False


def ensure_port_free(port: int, name: str) -> bool:
    """端口占用则静默结束占用进程，失败才报错。"""
    if not is_port_in_use(port):
        return True
    print_color(f"端口 {port} 占用 ({name})，正在释放...", Colors.YELLOW)
    kill_port_process(port)
    for _ in range(6):
        time.sleep(0.3)
        if not is_port_in_use(port):
            return True
    print_color(
        f"端口 {port} 无法释放，请手动结束占用进程或管理员运行",
        Colors.RED,
    )
    return False


def signal_handler(sig, frame):
    """シグナルハンドラー（Ctrl+C）"""
    global should_exit, production_httpds
    should_exit = True

    print("\n正在停止...")
    with production_httpds_lock:
        to_shutdown = list(production_httpds)
    for h in to_shutdown:
        try:
            h.shutdown()
        except Exception:
            pass
    with production_httpds_lock:
        production_httpds.clear()

    for i, process in enumerate(processes):
        if process is None:
            continue
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True
                )
            else:
                process.terminate()
            
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception:
            pass

    print("已停止\n")
    sys.exit(0)


def start_backend(output_buffer: List[str], ssl_args: Optional[List[str]] = None) -> subprocess.Popen:
    """バックエンドサーバーを起動（ssl_args に --ssl-certfile / --ssl-keyfile を渡すと HTTPS）"""
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
        "-m", "uvicorn",
        "app.main:app",
        "--host", CONFIG["backend_host"],
        "--port", str(CONFIG["backend_port"]),
        "--reload",
        "--no-access-log",
        "--log-level", "warning",
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
        encoding='utf-8',
        errors='replace'
    )
    
    def read_output():
        try:
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    output_buffer.append(line)
                    if line and ("ERROR" in line or "WARNING" in line or "Traceback" in line):
                        print(f"[backend] {line}")
        except Exception:
            pass
    
    threading.Thread(target=read_output, daemon=True).start()
    return process


def start_file_watcher(output_buffer: List[str]) -> subprocess.Popen:
    """バックエンドのBT-data受信CSVファイル監視を起動"""
    if sys.platform == "win32":
        python_path = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    else:
        python_path = BACKEND_DIR / "venv" / "bin" / "python"
    if not python_path.exists():
        python_path = Path(sys.executable)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        [str(python_path), "run_file_watcher.py"],
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
                    s = line.rstrip()
                    output_buffer.append(s)
                    if s:
                        print(f"[file-watcher] {s}")
        except Exception:
            pass

    threading.Thread(target=read_output, daemon=True).start()
    return process


def _is_client_disconnect(exc: BaseException) -> bool:
    """ブラウザ側の接続切断（WinError 10053 等）。サーバー障害ではない。"""
    if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, ssl.SSLEOFError)):
        return True
    if isinstance(exc, OSError):
        if getattr(exc, "winerror", None) in (10053, 10054):
            return True
        if exc.errno in (32, 54, 104):
            return True
    cause = exc.__cause__
    if cause is not None and cause is not exc and _is_client_disconnect(cause):
        return True
    return False


class ProductionHandler(http.server.SimpleHTTPRequestHandler):
    """本番用静的ファイルサーバー（SPAルーティング + APIプロキシ対応）"""
    
    def handle(self):
        try:
            super().handle()
        except Exception as e:
            if _is_client_disconnect(e):
                return
            raise

    def _safe_write(self, data: bytes) -> bool:
        try:
            self.wfile.write(data)
            return True
        except Exception as e:
            if _is_client_disconnect(e):
                return False
            raise

    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory or str(DIST_DIR)
        # parse_request 失敗 → send_error → end_headers の時点では未設定になり得る（Py3.14 等）
        self.path = ""
        super().__init__(*args, directory=self.directory, **kwargs)

    def send_error(self, code, message=None, explain=None):
        if not hasattr(self, "path"):
            self.path = ""
        super().send_error(code, message=message, explain=explain)

    def _send_bad_gateway(self, exc: BaseException) -> None:
        """
        バックエンドへ繋がらない等のプロキシ失敗。
        send_error(502, str(e)) は Win 等の日本語メッセージで reason phrase が latin-1 に
        載らず UnicodeEncodeError になるため、ステータス行は ASCII のみ・本文は UTF-8 JSON とする。
        """
        detail = str(exc)
        try:
            print_color(f"[API proxy] {detail}", Colors.RED)
        except Exception:
            print(f"[API proxy] {detail}", file=sys.stderr)
        payload = json.dumps(
            {"error": "bad_gateway", "detail": detail},
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(502, "Bad Gateway")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self._safe_write(payload)
    
    def _proxy_to_backend(self):
        """APIリクエストをバックエンドにプロキシ（Content-Length で返すとブラウザが正しく JSON を解釈する）"""
        import urllib.request
        import urllib.error

        scheme = CONFIG.get("backend_scheme", "http")
        backend_url = f"{scheme}://127.0.0.1:{CONFIG['backend_port']}{self.path}"
        hop_by_hop = {'connection', 'keep-alive', 'proxy-authenticate',
                     'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade'}

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            req = urllib.request.Request(backend_url, data=body, method=self.command)
            for key, value in self.headers.items():
                if key.lower() not in hop_by_hop:
                    req.add_header(key, value)

            ssl_ctx = None
            if scheme == "https":
                import ssl as _ssl
                ssl_ctx = _ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = _ssl.CERT_NONE

            open_kw = {"timeout": 30}
            if ssl_ctx is not None:
                open_kw["context"] = ssl_ctx
            with urllib.request.urlopen(req, **open_kw) as response:
                response_body = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    k = key.lower()
                    if k not in hop_by_hop and k != 'content-length' and k != 'transfer-encoding':
                        self.send_header(key, value)
                self.send_header('Content-Length', len(response_body))
                self.end_headers()
                self._safe_write(response_body)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                if key.lower() not in hop_by_hop and key.lower() != 'content-length':
                    self.send_header(key, value)
            err_body = e.read()
            self.send_header('Content-Length', len(err_body))
            self.end_headers()
            self._safe_write(err_body)
        except Exception as e:
            if _is_client_disconnect(e):
                return
            self._send_bad_gateway(e)
    
    def do_GET(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
            return
        # 本番でAPIを直叩きするための設定（プロキシ経由より高速）
        if self.path.rstrip('/') == '/api-config.js':
            # ページが https で API が http だと混合コンテンツでブロックされるため、
            # dist のみ TLS・バックエンド HTTP のときは同一オリジン /api プロキシ（空 = 相対）
            if CONFIG.get("frontend_prod_https") and not CONFIG.get("backend_use_https"):
                api_base = ""
            else:
                sch = CONFIG.get("backend_scheme", "http")
                api_base = f"{sch}://{CONFIG['production_ip']}:{CONFIG['backend_port']}"
            body = f"window.__API_BASE__={repr(api_base)};\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self._safe_write(body)
            return

        path = self.translate_path(self.path)
        if os.path.exists(path) and os.path.isfile(path):
            try:
                super().do_GET()
            except Exception as e:
                if not _is_client_disconnect(e):
                    raise
            return
        else:
            self.path = '/index.html'
            path = self.translate_path(self.path)
            if not os.path.isfile(path):
                self.send_error(404)
                return
            # index.html に api-config.js を注入（先読み→本番でAPI直叩き）
            with open(path, 'rb') as f:
                html = f.read().decode('utf-8', errors='replace')
            inject = '<script src="/api-config.js"></script>'
            if inject not in html:
                if '<head>' in html:
                    html = html.replace('<head>', '<head>' + inject, 1)
                elif '<head ' in html:
                    idx = html.find('>', html.find('<head'))
                    if idx != -1:
                        html = html[: idx + 1] + inject + html[idx + 1 :]
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self._safe_write(body)
    
    def do_POST(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_PUT(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_DELETE(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_PATCH(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_OPTIONS(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
        else:
            self.send_response(200)
            self.send_header('Allow', 'GET, HEAD, OPTIONS')
            self.end_headers()
    
    def end_headers(self):
        try:
            p = getattr(self, "path", "") or ""
            if isinstance(p, str) and p.startswith("/assets/"):
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        except Exception:
            pass
        try:
            super().end_headers()
        except AttributeError:
            try:
                http.server.BaseHTTPRequestHandler.end_headers(self)
            except Exception:
                pass

    def log_message(self, format, *args):
        pass


def _run_prod_server(ssl_context: Optional[Any], port: int, label: str) -> None:
    """1 ポートで dist を serve_forever（本番用デーモンスレッドから呼ぶ）"""
    global should_exit

    class ProdServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

        def server_activate(self):
            self.socket.listen(128)

    handler = lambda *args, **kwargs: ProductionHandler(*args, directory=str(DIST_DIR), **kwargs)

    if ssl_context:

        class SSLProdServer(ProdServer):
            def get_request(self):
                sock, addr = super().get_request()
                return ssl_context.wrap_socket(sock, server_side=True), addr

        ServerClass = SSLProdServer
        scheme = "https"
    else:
        ServerClass = ProdServer
        scheme = "http"

    httpd = None
    try:
        httpd = ServerClass(("0.0.0.0", port), handler)
        with production_httpds_lock:
            production_httpds.append(httpd)
        httpd.serve_forever()
    except Exception as e:
        if not should_exit:
            print_color(f"❌ 本番サーバー [{label} :{port}] エラー: {e}", Colors.RED)
    finally:
        if httpd is not None:
            with production_httpds_lock:
                try:
                    production_httpds.remove(httpd)
                except ValueError:
                    pass
            try:
                httpd.server_close()
            except Exception:
                pass


def start_production_server():
    """本番 dist。証明書ありなら :5005=HTTPS・:3005=HTTP。無ければ HTTP のみ :3005。"""

    if not (DIST_DIR / "index.html").is_file():
        if not ensure_prod_dist_available(CONFIG.get("production_ip", "127.0.0.1")):
            return False

    prod_ssl = _prod_static_ssl_ctx
    if prod_ssl:
        fb = CONFIG["frontend_prod_http_port"]
        threading.Thread(
            target=_run_prod_server,
            args=(None, fb, "HTTP"),
            daemon=True,
        ).start()
        _run_prod_server(prod_ssl, CONFIG["frontend_prod_https_port"], "HTTPS")
    else:
        _run_prod_server(None, CONFIG["frontend_prod_http_port"], "HTTP")


def wait_for_ports(ports: List[int], timeout: float = 30) -> bool:
    """等待全部端口就绪。"""
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


def print_success_banner(network_ip: str):
    """启动完成 — 仅显示常用访问地址。"""
    nip = (network_ip or "127.0.0.1").strip()
    hp = CONFIG["frontend_prod_https_port"]
    http_p = CONFIG["frontend_prod_http_port"]
    bp = CONFIG["backend_port"]
    be_scheme = CONFIG.get("backend_scheme", "http")
    dist_built = not CONFIG.get("dist_placeholder", False)

    print()
    print("=" * 52)
    print("Smart-EMAP 已就绪  (Ctrl+C 停止)")
    if CONFIG.get("frontend_prod_https"):
        print(f"  https://{nip}:{hp}/")
    print(f"  http://{nip}:{http_p}/")
    print(f"  API  {be_scheme}://localhost:{bp}/docs")
    if not dist_built:
        print("  提示: cd frontend && npm run build")
    print("=" * 52)
    print()


def main():
    _configure_console_encoding()
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        try:
            from dotenv import load_dotenv
            load_dotenv(BACKEND_DIR / ".env", encoding="utf-8")
        except Exception:
            pass

        network_ip = resolve_network_ip()
        CONFIG["production_ip"] = network_ip

        if not _env_truthy("START_DISABLE_AUTO_HTTPS"):
            os.environ.setdefault("HTTPS_ENABLED", "true")

        if _env_truthy("HTTPS_ENABLED"):
            ensure_ssl_certificate_files(network_ip)

        uvicorn_ssl = build_uvicorn_ssl_args()
        CONFIG["backend_use_https"] = bool(uvicorn_ssl)
        CONFIG["backend_scheme"] = "https" if uvicorn_ssl else "http"

        global _prod_static_ssl_ctx
        _prod_static_ssl_ctx = build_prod_static_ssl_context()
        CONFIG["frontend_prod_https"] = bool(_prod_static_ssl_ctx)

        ports_to_check: List[tuple[int, str]] = [
            (CONFIG["backend_port"], "后端"),
        ]
        if CONFIG["frontend_prod_https"]:
            ports_to_check.append((CONFIG["frontend_prod_http_port"], "前端HTTP"))
            ports_to_check.append((CONFIG["frontend_prod_https_port"], "前端HTTPS"))
        else:
            ports_to_check.append((CONFIG["frontend_prod_http_port"], "前端HTTP"))

        for port, label in ports_to_check:
            if not ensure_port_free(port, label):
                sys.exit(1)

        backend_output: List[str] = []
        backend_proc = start_backend(backend_output, uvicorn_ssl if uvicorn_ssl else None)
        processes.append(backend_proc)

        watch_path = os.environ.get("FILE_WATCH_BASE_PATH", "").strip()
        file_watcher_output: List[str] = []
        global file_watcher_process_index
        if watch_path:
            file_watcher_proc = start_file_watcher(file_watcher_output)
            processes.append(file_watcher_proc)
            file_watcher_process_index = len(processes) - 1

        threading.Thread(target=start_production_server, daemon=True).start()

        wait_ports = [CONFIG["backend_port"]]
        if CONFIG["frontend_prod_https"]:
            wait_ports.extend([
                CONFIG["frontend_prod_http_port"],
                CONFIG["frontend_prod_https_port"],
            ])
        else:
            wait_ports.append(CONFIG["frontend_prod_http_port"])

        if not wait_for_ports(wait_ports, timeout=45):
            if not is_port_in_use(CONFIG["backend_port"]):
                print_color("后端启动失败", Colors.RED)
                for line in backend_output[-10:]:
                    print(f"  {line}")
                signal_handler(None, None)
                sys.exit(1)
            print_color("前端启动超时（请检查 frontend/dist）", Colors.YELLOW)

        print_success_banner(network_ip)
        
        # メインループ
        while not should_exit:
            for i, process in enumerate(processes):
                if process is None:
                    continue
                if process.poll() is not None:
                    name = PROCESS_NAMES[i] if i < len(PROCESS_NAMES) else f"プロセス{i}"
                    # ファイル監視が code 0 で終了＝監視パス未設定またはパスが存在しない（正常扱いでアプリは継続）
                    if (
                        file_watcher_process_index is not None
                        and i == file_watcher_process_index
                        and process.returncode == 0
                    ):
                        print_color("⚠️  ファイル監視が終了しました（監視パスが未設定か、指定パスが存在しません）", Colors.YELLOW)
                        processes[i] = None
                        continue
                    if (
                        file_watcher_process_index is not None
                        and i == file_watcher_process_index
                        and process.returncode != 0
                        and file_watcher_output
                    ):
                        print_color("   ファイル監視のエラー出力:", Colors.YELLOW)
                        for line in file_watcher_output[-25:]:
                            print(f"   {line}")
                    print_color(f"\n❌ {name}サーバーが終了しました (code: {process.returncode})", Colors.RED)
                    signal_handler(None, None)
                    sys.exit(1)
            time.sleep(2)
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print_color(f"\n❌ エラー: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        signal_handler(None, None)
        sys.exit(1)


if __name__ == "__main__":
    main()
