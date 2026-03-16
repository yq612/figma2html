"""
本地预览服务：GET / 返回预览页，POST /render 接收 JSON 请求体，
执行 style.main + render.builder 后返回 HTML。仅用标准库。

启动方式：python -m preview.server
"""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# style/ 和 render/ 包在项目根目录，需将根目录加入 sys.path
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from style.main import add_style, minimize_node
from render.builder import build_html

from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8765
PREVIEW_HTML_PATH = os.path.join(SCRIPT_DIR, "preview.html")


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_preview_page()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/render":
            self._handle_render()
        else:
            self.send_error(404, "Not Found")

    def _serve_preview_page(self):
        try:
            with open(PREVIEW_HTML_PATH, "r", encoding="utf-8") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(500, "preview.html not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body.encode("utf-8")))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _handle_render(self):
        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._send_error_response(400, "Missing Content-Length")
            return
        try:
            length = int(content_length)
        except ValueError:
            self._send_error_response(400, "Invalid Content-Length")
            return
        if length <= 0 or length > 50 * 1024 * 1024:  # 50MB 上限
            self._send_error_response(400, "Body size out of range")
            return
        raw = self.rfile.read(length)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            self._send_error_response(400, "Request body must be UTF-8")
            return
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            self._send_error_response(400, f"Invalid JSON: {e}")
            return
        if not isinstance(data, dict):
            self._send_error_response(400, "JSON root must be an object")
            return
        try:
            add_style(data, None, None, None, is_root=True)
            data = minimize_node(data)
            html_content = build_html(data)
        except Exception as e:
            self._send_error_response(500, str(e))
            return
        body = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_response(self, code, message):
        body = f"Error: {message}".encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def main():
    server = HTTPServer(("", PORT), PreviewHandler)
    print(f"Preview server: http://localhost:{PORT}", file=sys.stderr)
    print("Open in browser, paste JSON and click 渲染.", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
