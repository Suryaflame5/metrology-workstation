"""
Native Windows Desktop Application Launcher for Metrology Workstation (v7.0.0).
Creates a native desktop application window hosting the full workstation interface.
"""

import sys
import os
import time
import socket
import threading
import webbrowser
import uvicorn
import webview

from metrology_app.config import ensure_app_directories, DB_PATH
from metrology_app.db import init_db
from metrology_app.server import app
from metrology_app.services.log_service import get_logger


def find_available_port(start_port: int = 8000, max_attempts: int = 50) -> int:
    """Find an open TCP port on localhost."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return start_port


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Wait until the backend server is responding on localhost."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def init_dpi_awareness():
    """Enable Per-Monitor V2 DPI awareness on Windows."""
    if sys.platform == "win32":
        try:
            import ctypes
            # PROCESS_PER_MONITOR_DPI_AWARE_V2 = 2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def main():
    init_dpi_awareness()

    # 1. Handle CLI subcommands if invoked with arguments
    if len(sys.argv) > 1 and sys.argv[1] in (
        "--help", "-h", "demo", "selftest", "audit-verify",
        "backup", "list", "verify", "replay", "export", "version", "serve"
    ):
        if sys.argv[1] == "version":
            print("Metrology Workstation v7.0.0 (Native Desktop Application)")
            return
        from metrology_app.cli import main as cli_main
        cli_main()
        return

    # 2. Initialize environment & app data directories
    ensure_app_directories()
    init_db(DB_PATH)
    logger = get_logger()
    logger.info("Metrology Workstation Desktop v7.0.0 initializing...")

    # 3. Parse port / host
    host = "127.0.0.1"
    port = 8000
    if "--port" in sys.argv:
        try:
            idx = sys.argv.index("--port")
            port = int(sys.argv[idx + 1])
        except Exception:
            port = find_available_port(8000)
    else:
        port = find_available_port(8000)

    server_url = f"http://{host}:{port}"
    logger.info(f"Metrology Workstation Engine running on {server_url}")

    # 4. Start Uvicorn in background daemon thread
    def run_uvicorn():
        uvicorn.run(app, host=host, port=port, log_level="warning")

    server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    server_thread.start()

    # 5. Wait for backend to be ready
    wait_for_server(host, port)

    # 6. Check for headless / server-only mode
    if "--headless" in sys.argv or "--server-only" in sys.argv:
        logger.info("Running in headless / server-only mode. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return

    # 7. Check for explicit browser mode fallback
    if "--browser" in sys.argv:
        logger.info(f"Opening browser at {server_url}")
        webbrowser.open(server_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return

    # 8. Launch Native Desktop Window (Primary GUI)
    logger.info("Launching Native Windows Desktop Application Window...")
    try:
        window = webview.create_window(
            title="Metrology Workstation 7",
            url=server_url,
            width=1480,
            height=940,
            min_size=(1024, 700),
            background_color="#030712",
        )
        webview.start(private_mode=False)
    except Exception as e:
        logger.warning(f"Native desktop window initialization error: {e}. Falling back to browser.")
        webbrowser.open(server_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
