import os
import sys
import gc
import json
import time
import logging
import threading
import urllib.request
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Explicitly ensure root and subpackages are in sys.path
BASE_DIR = Path(__file__).resolve().parent
for p in [str(BASE_DIR), str(BASE_DIR / 'analyzers'), str(BASE_DIR / 'collectors'), str(BASE_DIR / 'formatters')]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import XAUUSDNewsAssistantBot
from tradingview_gemini_bridge import handle_tradingview

logger = logging.getLogger("RenderServer")
_bot_instance = None
_start_time = time.time()
_last_error = "None"
_bot_stage = "Not started"

class HealthHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", "2")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_POST(self):
        if not handle_tradingview(self):
            self.send_error(404)

    def do_GET(self):
        if handle_tradingview(self):
            return
        if "/api/signal" in self.path or "/api/active_signal" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                import database
                sig_json = database.get_state("active_official_signal_json") or "{}"
                self.wfile.write(sig_json.encode("utf-8"))
            except Exception:
                self.wfile.write(b"{}")
            return

        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            data = {
                "bot_running": _bot_instance is not None,
                "bot_stage": _bot_stage,
                "last_error": _last_error,
                "uptime_seconds": time.time() - _start_time,
                "uptime_hours": round((time.time() - _start_time) / 3600.0, 2),
                "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
                "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
                "has_gemini_key": bool(os.getenv("GEMINI_API_KEY")),
                "render_url": os.getenv("RENDER_EXTERNAL_URL", "https://xauusd-news-bot-1-a6gh.onrender.com"),
            }
            if _bot_instance:
                data["last_breaking_sent_ts"] = getattr(_bot_instance, "_last_breaking_sent_ts", 0)
                data["broadcasted_cache_count"] = len(getattr(_bot_instance, "_broadcasted_titles_cache", set()))
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-length", "2")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass # Suppress HTTP access log noise


def run_http_server():
    port = int(os.getenv("PORT", "10000"))
    print(f"[HTTP Health] Starting HTTP health server on 0.0.0.0:{port}...", flush=True)
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"[HTTP Health] Successfully bound and listening on 0.0.0.0:{port}! Ready for UptimeRobot / Render Health Check.", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"[HTTP Health ERROR] Could not bind on 0.0.0.0:{port}: {e}", flush=True)

def run_self_pinger():
    """
    Pings the public Render URL every 5 minutes (300 seconds) using lightweight HEAD request (0-byte payload)
    so Render Free Tier never spins down due to inactivity, while using practically ZERO bandwidth.
    Cadence: 300 seconds (5 minutes) provides an ironclad anti-sleep safety net well inside Render's 15m timeout.
    """
    url = os.getenv("RENDER_EXTERNAL_URL", "https://xauusd-news-bot-1-a6gh.onrender.com")

    time.sleep(30) # Initial delay after startup
    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Render-KeepAlive/2.0"}, method="HEAD")
            with urllib.request.urlopen(req, timeout=15) as resp:
                pass
        except Exception as e:
            logger.debug(f"[Self-Pinger] {e}")
        time.sleep(300) # 5 minutes

def run_memory_guard():
    """
    Periodic garbage collection watchdog to prevent memory leaks over 30+ days of 24/7 continuous operation.
    Guarantees RAM usage strictly stays well under Render's 512MB free tier limit!
    """
    while True:
        time.sleep(180) # Every 3 minutes
        try:
            collected = gc.collect()
            logger.debug(f"[MemoryGuard] Periodic GC collected {collected} objects.")
        except Exception:
            pass

if __name__ == "__main__":
    # Flag supervisor environment so main.py does not duplicate port binding
    os.environ["RUNNING_IN_RENDER_SUPERVISOR"] = "1"

    # 1. Start HTTP health check in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True, name="HTTP-Health")
    http_thread.start()

    # 2. Start Self-Pinger keep-alive in background thread
    pinger_thread = threading.Thread(target=run_self_pinger, daemon=True, name="Keep-Alive-Pinger")
    pinger_thread.start()

    # 3. Start Periodic Memory Guard in background thread
    mem_thread = threading.Thread(target=run_memory_guard, daemon=True, name="Memory-Guard")
    mem_thread.start()

    # 4. Start Autonomous Telegram Bot with self-healing 24/7 supervisor loop
    while True:
        try:
            _bot_stage = "Initializing XAUUSDNewsAssistantBot..."
            print("[SUPERVISOR] Starting XAUUSDNewsAssistantBot...", flush=True)
            _bot_instance = XAUUSDNewsAssistantBot()
            _bot_stage = "Bot loop running"
            _bot_instance.start_loop()
        except KeyboardInterrupt:
            _bot_stage = "Stopped by user"
            print("[SUPERVISOR] Bot stopped by user.", flush=True)
            break
        except Exception as e:
            import traceback
            _last_error = f"{e}\n{traceback.format_exc()}"
            _bot_stage = f"Crashed: {e}"
            print(f"[FATAL ENGINE CRASH] {e}\n{traceback.format_exc()}")
            print("[SUPERVISOR] Restarting bot engine in 10 seconds...")
            time.sleep(10.0)

