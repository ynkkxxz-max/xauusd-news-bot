import os
import json
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from main import XAUUSDNewsAssistantBot

logger = logging.getLogger("RenderServer")
_bot_instance = None
_start_time = time.time()

class HealthHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", "2")
        self.end_headers()

    def do_GET(self):
        global _bot_instance, _start_time
        path = self.path.split("?")[0].rstrip("/")

        if path in ("/status", "/healthz", "/debug"):
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()

            ai_names = []
            last_breaking = 0.0
            if _bot_instance and hasattr(_bot_instance, "analyzer"):
                ai_names = [getattr(a, "name", a.__class__.__name__)
                            for a in _bot_instance.analyzer.analyzers if a.is_available()]
                last_breaking = getattr(_bot_instance, "_last_breaking_sent_ts", 0.0)

            data = {
                "status": "online",
                "service": "XAUUSD News Bot & Telegram Mini App Assistant",
                "uptime_seconds": int(time.time() - _start_time),
                "ai_engines_active": ai_names,
                "last_breaking_sent_ts": last_breaking,
                "bot_running": _bot_instance is not None
            }
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
            return

        # Default 200 OK for root and /health (UptimeRobot, Render pings)
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-length", "2")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass # Suppress HTTP access log noise


def run_http_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

def run_self_pinger():
    """
    Pings the public Render URL every 8 minutes so Render Free Tier never spins down due to inactivity.
    Render's router counts this as inbound HTTP activity, keeping the instance 100% active 24/7.
    """
    url = os.getenv("RENDER_EXTERNAL_URL", "https://xauusd-news-bot-kh.onrender.com")
    time.sleep(30) # Initial delay after startup
    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Render-Internal-KeepAlive/1.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                pass
        except Exception:
            pass
        time.sleep(480) # 8 minutes

if __name__ == "__main__":
    import urllib.request

    # 1. Start HTTP health check in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True, name="HTTP-Health")
    http_thread.start()

    # 2. Start Self-Pinger keep-alive in background thread
    pinger_thread = threading.Thread(target=run_self_pinger, daemon=True, name="Keep-Alive-Pinger")
    pinger_thread.start()

    # 3. Start Autonomous Telegram Bot with self-healing 24/7 supervisor loop
    while True:
        try:
            print("[SUPERVISOR] Starting XAUUSDNewsAssistantBot...")
            _bot_instance = XAUUSDNewsAssistantBot()
            _bot_instance.start_loop()
        except KeyboardInterrupt:
            print("[SUPERVISOR] Bot stopped by user.")
            break
        except Exception as e:
            import traceback
            print(f"[FATAL ENGINE CRASH] {e}\n{traceback.format_exc()}")
            print("[SUPERVISOR] Restarting bot engine in 10 seconds...")
            time.sleep(10.0)
