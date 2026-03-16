"""
Vercel Python serverless function: POST /api/render
接收 Figma 精简 JSON，执行 style + render 管线，返回单文件 HTML。
"""
import json
import os
import sys

# 将项目根目录加入 sys.path，使 style/render 包可被正常导入
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from http.server import BaseHTTPRequestHandler  # noqa: E402

from style.main import add_style, minimize_node  # noqa: E402
from render.builder import build_html  # noqa: E402

MAX_BODY = 10 * 1024 * 1024  # 10 MB


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._error(400, "Missing Content-Length")
            return
        try:
            length = int(content_length)
        except ValueError:
            self._error(400, "Invalid Content-Length")
            return
        if length <= 0 or length > MAX_BODY:
            self._error(400, "Body size out of range (max 10 MB)")
            return

        raw = self.rfile.read(length)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            self._error(400, "Request body must be UTF-8")
            return

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            self._error(400, f"Invalid JSON: {exc}")
            return

        if not isinstance(data, dict):
            self._error(400, "JSON root must be an object")
            return

        try:
            add_style(data, None, None, None, is_root=True)
            data = minimize_node(data)
            html_content = build_html(data)
        except Exception as exc:
            self._error(500, str(exc))
            return

        body = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code: int, message: str) -> None:
        body = f"Error: {message}".encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):  # silence default access log in Vercel
        pass
