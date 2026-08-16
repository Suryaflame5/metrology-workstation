"""
Standalone Desktop Application Launcher for Metrology Workstation (v1.0.0).
"""

import sys
import os
import time
import socket
import threading
import webbrowser
import uvicorn

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


def open_browser_after_delay(url: str, delay: float = 1.0):
    """Open user's default browser after server is ready."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


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
    # Handle CLI modes if invoked with arguments
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h", "demo", "selftest", "audit-verify", "backup", "list", "verify", "replay", "export"):
        from metrology_app.cli import main as cli_main
        cli_main()
        return

    # 1. Initialize environment & app data directories
    ensure_app_directories()
    init_db(DB_PATH)
    logger = get_logger()
    logger.info("Metrology Workstation initializing...")

    # 2. Allocate port and prepare URL
    host = "127.0.0.1"
    port = find_available_port(8000)
    server_url = f"http://{host}:{port}"
    logger.info(f"Metrology Workstation starting on {server_url}")

    # 3. Schedule browser opening
    if "--no-browser" not in sys.argv:
        t = threading.Thread(target=open_browser_after_delay, args=(server_url, 1.2), daemon=True)
        t.start()

    # 4. Run uvicorn on main thread
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
