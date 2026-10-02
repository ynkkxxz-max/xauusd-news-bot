import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from main import XAUUSDNewsAssistantBot

# Simple HTTP health check server so free cloud platforms (Render, Railway) know the app is alive
# and can be pinged by cron-job.org every 5-10 minutes.
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        status_json = (
            '{"status":"online","service":"XAUUSD News Assistant","mode":"autonomous_24_7"}'
        )
        self.wfile.write(status_json.encode("utf-8"))

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
    import time
    import urllib.request
    url = os.getenv("RENDER_EXTERNAL_URL", "https://xauusd-news-bot-dl60.onrender.com")
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
    # 1. Start HTTP health check in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True, name="HTTP-Health")
    http_thread.start()

    # 2. Start Self-Pinger keep-alive in background thread
    pinger_thread = threading.Thread(target=run_self_pinger, daemon=True, name="Keep-Alive-Pinger")
    pinger_thread.start()

    # 3. Start Autonomous Telegram Bot
    bot = XAUUSDNewsAssistantBot()
    bot.start_loop()
