import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from main import XAUUSDNewsAssistantBot

# Simple HTTP health check server so free cloud platforms (Render, Railway) know the app is alive
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("🥇 XAUUSD News Assistant is running 24/7!".encode("utf-8"))

    def log_message(self, format, *args):
        pass # Suppress HTTP access log noise

def run_http_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    # 1. Start HTTP health check in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # 2. Start Autonomous Telegram Bot
    bot = XAUUSDNewsAssistantBot()
    bot.start_loop()
