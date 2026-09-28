import re
import time
import atexit
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from config import BASE_DIR, PORT

class CloudflareTunnelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CloudflareTunnelManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        self.is_running: bool = False
        self.last_error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.exe_path = BASE_DIR / "cloudflared.exe"
        atexit.register(self.stop_tunnel)

    def start_tunnel(self, timeout: int = 25) -> Dict[str, Any]:
        """Starts cloudflared tunnel pointing to localhost:PORT and extracts public URL."""
        with self._lock:
            if self.is_running and self.tunnel_url and self.process and self.process.poll() is None:
                return {
                    "success": True,
                    "url": self.tunnel_url,
                    "running": True,
                    "message": "Tunnel is already running."
                }

            if not self.exe_path.exists():
                return {
                    "success": False,
                    "url": None,
                    "running": False,
                    "message": f"cloudflared.exe not found at {self.exe_path}"
                }

            # Stop existing if any broken process
            self._cleanup_process()

            cmd = [
                str(self.exe_path.resolve()),
                "tunnel",
                "--url",
                f"http://127.0.0.1:{PORT}"
            ]

            try:
                # Windows-specific: hide console window if needed
                startupinfo = None
                creationflags = 0
                import os
                if os.name == "nt":
                    creationflags = subprocess.CREATE_NO_WINDOW

                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=creationflags
                )
                self.is_running = True
                self.started_at = time.time()
                self.tunnel_url = None
                self.last_error = None
            except Exception as e:
                self.is_running = False
                self.last_error = str(e)
                return {"success": False, "url": None, "running": False, "message": str(e)}

        # Wait for public URL to appear in stderr
        found_url = None
        start_wait = time.time()

        while time.time() - start_wait < timeout:
            if self.process.poll() is not None:
                self.is_running = False
                self.last_error = "Tunnel process exited unexpectedly."
                return {"success": False, "url": None, "running": False, "message": self.last_error}

            line = self.process.stderr.readline()
            if not line:
                time.sleep(0.1)
                continue

            m = re.search(r'https://(?!(?:api|www)\.)[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if m:
                found_url = m.group(0)
                break

        if found_url:
            with self._lock:
                self.tunnel_url = found_url
                self.is_running = True

            # Start background consumer thread to keep pipe from blocking
            def _drain_stderr(proc):
                try:
                    for _ in proc.stderr:
                        pass
                except Exception:
                    pass

            self.reader_thread = threading.Thread(target=_drain_stderr, args=(self.process,), daemon=True)
            self.reader_thread.start()

            return {
                "success": True,
                "url": found_url,
                "running": True,
                "message": "Cloudflare Tunnel active and reachable."
            }
        else:
            self.stop_tunnel()
            return {
                "success": False,
                "url": None,
                "running": False,
                "message": "Timed out waiting for Cloudflare Tunnel URL."
            }

    def stop_tunnel(self) -> Dict[str, Any]:
        """Stops the active tunnel."""
        with self._lock:
            self._cleanup_process()
            self.is_running = False
            self.tunnel_url = None
            return {
                "success": True,
                "running": False,
                "message": "Cloudflare Tunnel stopped."
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns the current state of the tunnel."""
        with self._lock:
            if self.process:
                poll_res = self.process.poll()
                if poll_res is not None:
                    self.is_running = False
                    self.tunnel_url = None

            return {
                "running": self.is_running,
                "url": self.tunnel_url,
                "uptime": int(time.time() - self.started_at) if (self.is_running and self.started_at) else 0,
                "last_error": self.last_error
            }

    def _cleanup_process(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

# Global singleton
tunnel_mgr = CloudflareTunnelManager()

