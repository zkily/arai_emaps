#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smart-EMAP 起動スクリプト
開発・本番の前後端を同時に起動します。
"""
import os
import sys
import subprocess
import signal
import time
import socket
from pathlib import Path
from typing import List
import threading
import http.server
import socketserver

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

processes: List[subprocess.Popen] = []
should_exit = False
PROCESS_NAMES = ("バックエンド", "フロントエンド（開発）", "ファイル監視")
production_httpd = None  # 本番サーバー（signal で shutdown 用）

# 設定
CONFIG = {
    "backend_port": 8005,
    "frontend_dev_port": 5000,
    "frontend_prod_port": 3005,
    "backend_host": "0.0.0.0",
    "production_ip": "192.168.1.59",
}

class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


def print_color(message: str, color: str = Colors.RESET):
    """カラー出力"""
    print(f"{color}{message}{Colors.RESET}")


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
                print_color(f"   🔪 PID {pid} を終了中...", Colors.YELLOW)
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
                    elif r2.stderr:
                        print_color(f"   ⚠️  PID {pid}: {r2.stderr.strip()}", Colors.YELLOW)
                time.sleep(0.5)
            time.sleep(2)  # ポート解放を待つ（プロセス未検出でも解放遅延あり得る）
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
                    print_color(f"   🔪 PID {pid} を終了中...", Colors.YELLOW)
                    subprocess.run(["kill", "-9", pid], capture_output=True)
                    killed_any = True
                    time.sleep(0.5)
            if killed_any:
                time.sleep(2)
            return killed_any
    except Exception as e:
        print_color(f"   ⚠️  プロセス終了エラー: {e}", Colors.YELLOW)
        return False


def check_port(port: int, name: str) -> bool:
    """ポートの使用状況をチェック（使用中なら強制終了）"""
    print(f"ポート {port} の使用状況を確認中...（{name}）")
    if is_port_in_use(port):
        print_color(f"⚠️  ポート {port} は既に使用されています ({name})", Colors.YELLOW)
        print_color(f"   既存のプロセスを終了します...", Colors.YELLOW)
        kill_port_process(port)
        # taskkill が「プロセスが見つからない」等で失敗しても、ポートは既に解放されている場合があるので必ず再確認
        for attempt in range(3):
            time.sleep(2 if attempt == 0 else 2)
            if not is_port_in_use(port):
                print_color(f"✅ ポート {port} を解放しました", Colors.GREEN)
                return True
        print_color(f"❌ ポート {port} の解放に失敗しました（管理者権限で実行するか、手動でプロセスを終了してください）", Colors.RED)
        return False
    print(f"ポート {port} は使用されていません")
    return True


def signal_handler(sig, frame):
    """シグナルハンドラー（Ctrl+C）"""
    global should_exit, production_httpd
    should_exit = True

    print("\n\n🛑 サーバーを停止中...")
    if production_httpd:
        try:
            production_httpd.shutdown()
        except Exception:
            pass
        production_httpd = None

    for i, process in enumerate(processes):
        if process is None:
            continue
        try:
            name = PROCESS_NAMES[i] if i < len(PROCESS_NAMES) else f"プロセス{i}"
            print(f"   {name}サーバーを停止中...")
            
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True
                )
            else:
                process.terminate()
            
            process.wait(timeout=5)
            print(f"   ✅ {name}サーバーを停止しました")
            
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception:
            pass
    
    print("\n✅ すべてのサーバーを停止しました")
    print("👋 ご利用ありがとうございました\n")
    sys.exit(0)


def start_backend(output_buffer: List[str]) -> subprocess.Popen:
    """バックエンドサーバーを起動"""
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
        [
            str(python_path),
            "-m", "uvicorn",
            "app.main:app",
            "--host", CONFIG["backend_host"],
            "--port", str(CONFIG["backend_port"]),
            "--reload"
        ],
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
        except Exception:
            pass
    
    threading.Thread(target=read_output, daemon=True).start()
    return process


def start_frontend_dev(output_buffer: List[str]) -> subprocess.Popen:
    """フロントエンド開発サーバーを起動"""
    npm_cmd = ["npm", "run", "dev"]
    
    if sys.platform == "win32":
        process = subprocess.Popen(
            ["cmd.exe", "/c"] + npm_cmd,
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            encoding='utf-8',
            errors='replace'
        )
    else:
        process = subprocess.Popen(
            npm_cmd,
            cwd=FRONTEND_DIR,
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


class ProductionHandler(http.server.SimpleHTTPRequestHandler):
    """本番用静的ファイルサーバー（SPAルーティング + APIプロキシ対応）"""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory or str(DIST_DIR)
        super().__init__(*args, directory=self.directory, **kwargs)
    
    def _proxy_to_backend(self):
        """APIリクエストをバックエンドにプロキシ（Content-Length で返すとブラウザが正しく JSON を解釈する）"""
        import urllib.request
        import urllib.error

        backend_url = f"http://127.0.0.1:{CONFIG['backend_port']}{self.path}"
        hop_by_hop = {'connection', 'keep-alive', 'proxy-authenticate',
                     'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade'}

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            req = urllib.request.Request(backend_url, data=body, method=self.command)
            for key, value in self.headers.items():
                if key.lower() not in hop_by_hop:
                    req.add_header(key, value)

            with urllib.request.urlopen(req, timeout=30) as response:
                response_body = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    k = key.lower()
                    if k not in hop_by_hop and k != 'content-length' and k != 'transfer-encoding':
                        self.send_header(key, value)
                self.send_header('Content-Length', len(response_body))
                self.end_headers()
                self.wfile.write(response_body)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                if key.lower() not in hop_by_hop and key.lower() != 'content-length':
                    self.send_header(key, value)
            err_body = e.read()
            self.send_header('Content-Length', len(err_body))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_error(502, f"Bad Gateway: {str(e)}")
    
    def do_GET(self):
        if self.path.startswith('/api'):
            self._proxy_to_backend()
            return
        # 本番でAPIを直叩きするための設定（プロキシ経由より高速）
        if self.path.rstrip('/') == '/api-config.js':
            api_base = f"http://{CONFIG['production_ip']}:{CONFIG['backend_port']}"
            body = f"window.__API_BASE__={repr(api_base)};\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        path = self.translate_path(self.path)
        if os.path.exists(path) and os.path.isfile(path):
            super().do_GET()
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
            self.wfile.write(body)
    
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
        # ハッシュ付き静的ファイル（/assets/）は長期キャッシュで再訪問を高速化
        if self.path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        super().end_headers()

    def log_message(self, format, *args):
        pass


def start_production_server():
    """本番用静的ファイルサーバー（マルチスレッド + serve_forever で並行受付）"""
    global should_exit, production_httpd

    if not DIST_DIR.exists():
        print_color(f"⚠️  distフォルダが見つかりません: {DIST_DIR}", Colors.YELLOW)
        print_color("   npm run build を実行してビルドしてください", Colors.YELLOW)
        return False

    port = CONFIG["frontend_prod_port"]

    class ProdServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

        def server_activate(self):
            self.socket.listen(128)  # 接続キューを拡大

    handler = lambda *args, **kwargs: ProductionHandler(*args, directory=str(DIST_DIR), **kwargs)

    try:
        production_httpd = ProdServer(("0.0.0.0", port), handler)
        print_color(f"✅ 本番サーバー起動: http://{CONFIG['production_ip']}:{port}/", Colors.GREEN)
        production_httpd.serve_forever()
    except Exception as e:
        if not should_exit:
            print_color(f"❌ 本番サーバーエラー: {e}", Colors.RED)
        return False
    finally:
        production_httpd = None
    return True


def wait_for_port(port: int, timeout: int = 60) -> bool:
    """ポートがリッスン開始するまで待機"""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def print_success_banner(network_ip: str):
    """起動成功バナーを表示"""
    backend_port = CONFIG["backend_port"]
    dev_port = CONFIG["frontend_dev_port"]
    prod_port = CONFIG["frontend_prod_port"]
    prod_ip = CONFIG["production_ip"]
    
    print()
    print("=" * 65)
    print("🚀 Smart-EMAP システムが起動しました")
    print("=" * 65)
    print()
    print(f"📱 フロントエンド【開発モード】:")
    print(f"   ➜  Local:   http://localhost:{dev_port}/")
    if network_ip != '127.0.0.1':
        print(f"   ➜  Network: http://{network_ip}:{dev_port}/")
    print()
    print(f"🌐 フロントエンド【本番モード】(dist):")
    print(f"   ➜  Local:   http://localhost:{prod_port}/")
    print(f"   ➜  Network: http://{prod_ip}:{prod_port}/")
    print()
    print(f"🔧 バックエンド API:")
    print(f"   ➜  Local:   http://localhost:{backend_port}")
    if network_ip != '127.0.0.1':
        print(f"   ➜  Network: http://{network_ip}:{backend_port}")
    print(f"   ➜  Docs:    http://localhost:{backend_port}/docs")
    print()
    print("=" * 65)
    print("   Ctrl+C で停止")
    print("=" * 65)
    print()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        print("\n🚀 Smart-EMAP 開発・本番サーバーを起動中...\n")
        
        # ポートチェック
        if not check_port(CONFIG["backend_port"], "バックエンド"):
            sys.exit(1)
        if not check_port(CONFIG["frontend_dev_port"], "フロントエンド開発"):
            sys.exit(1)
        if not check_port(CONFIG["frontend_prod_port"], "フロントエンド本番"):
            sys.exit(1)
        
        print("\nサービスを起動中...")
        print()
        
        # 出力バッファ
        backend_output = []
        frontend_output = []
        
        # バックエンド起動
        print("> dev:backend")
        backend_proc = start_backend(backend_output)
        processes.append(backend_proc)
        
        # フロントエンド開発サーバー起動
        print()
        print("> dev:frontend")
        frontend_proc = start_frontend_dev(frontend_output)
        processes.append(frontend_proc)
        
        # バックエンド ファイル監視（BT-data受信CSV）。.env の FILE_WATCH_BASE_PATH が空でない場合のみ起動
        try:
            from dotenv import load_dotenv
            load_dotenv(BACKEND_DIR / ".env", encoding="utf-8")
        except Exception:
            pass
        watch_path = os.environ.get("FILE_WATCH_BASE_PATH", "").strip()
        file_watcher_output = []
        if watch_path:
            print()
            print("> file-watcher")
            file_watcher_proc = start_file_watcher(file_watcher_output)
            processes.append(file_watcher_proc)
        
        # 本番フロント（dist）をスレッドで起動
        print()
        print("> prod:frontend (dist)")
        threading.Thread(target=start_production_server, daemon=True).start()
        
        # サーバー起動待機
        print()
        print("サーバー起動を待機中...")
        
        backend_ready = wait_for_port(CONFIG["backend_port"], timeout=30)
        dev_ready = wait_for_port(CONFIG["frontend_dev_port"], timeout=60)
        prod_ready = wait_for_port(CONFIG["frontend_prod_port"], timeout=10)
        
        if not backend_ready:
            print_color("❌ バックエンドサーバーの起動に失敗しました", Colors.RED)
            if backend_output:
                print("   最後の出力:")
                for line in backend_output[-10:]:
                    print(f"   {line}")
            signal_handler(None, None)
            sys.exit(1)
        
        if not dev_ready:
            print_color("❌ フロントエンド開発サーバーの起動に失敗しました", Colors.RED)
            if frontend_output:
                print("   最後の出力:")
                for line in frontend_output[-10:]:
                    print(f"   {line}")
            signal_handler(None, None)
            sys.exit(1)
        
        if not prod_ready:
            print_color("⚠️  本番サーバーの起動に失敗しました（distフォルダを確認してください）", Colors.YELLOW)
        
        # 起動成功
        network_ip = get_local_ip()
        print_success_banner(network_ip)
        
        # メインループ
        while not should_exit:
            for i, process in enumerate(processes):
                if process is None:
                    continue
                if process.poll() is not None:
                    name = PROCESS_NAMES[i] if i < len(PROCESS_NAMES) else f"プロセス{i}"
                    # ファイル監視が code 0 で終了＝監視パス未設定またはパスが存在しない（正常扱いでアプリは継続）
                    if i == 2 and process.returncode == 0:
                        print_color("⚠️  ファイル監視が終了しました（監視パスが未設定か、指定パスが存在しません）", Colors.YELLOW)
                        processes[i] = None
                        continue
                    if i == 2 and process.returncode != 0 and file_watcher_output:
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
