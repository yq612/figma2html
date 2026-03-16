"""
Pipeline 主入口：simplify → style → render

用法：
    python3 main.py <input.json>

产物输出到 __result__/<timestamp>_simplified.json
                  __result__/<timestamp>_styled.json
                  __result__/<timestamp>.html

时间戳格式与 JS new Date().getTime() 一致（毫秒级 Unix 时间戳）。
"""
import json
import os
import sys
import time

# 保证从任意工作目录调用时，包路径均能正确解析
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simplify.nodes import simplify_node
from style.main import add_style, minimize_node
from render.builder import build_html

RESULT_DIR = os.path.join(PROJECT_ROOT, "__result__")


def run_pipeline(input_path: str) -> str:
    """执行完整 pipeline，返回最终 HTML 路径。"""
    ts = int(time.time() * 1000)  # 毫秒时间戳，与 JS new Date().getTime() 一致
    os.makedirs(RESULT_DIR, exist_ok=True)

    # ── 1. 读取原始 JSON ──────────────────────────────────────────────────────
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── 2. Simplify：精简 Figma JSON，去除渲染无关字段 ───────────────────────
    simplified = simplify_node(data)
    simplified_path = os.path.join(RESULT_DIR, f"{ts}_simplified.json")
    with open(simplified_path, "w", encoding="utf-8") as f:
        json.dump(simplified, f, ensure_ascii=False, indent=2)
    print(f"[1/3] simplify  →  {simplified_path}", file=sys.stderr)

    # ── 3. Style：为每个节点生成 CSS style 并最小化树 ────────────────────────
    add_style(simplified, None, None, None, is_root=True)
    styled = minimize_node(simplified)
    styled_path = os.path.join(RESULT_DIR, f"{ts}_styled.json")
    with open(styled_path, "w", encoding="utf-8") as f:
        json.dump(styled, f, ensure_ascii=False, indent=2)
    print(f"[2/3] style     →  {styled_path}", file=sys.stderr)

    # ── 4. Render：将 styled JSON 渲染为单文件 HTML ──────────────────────────
    html_content = build_html(styled)
    html_path = os.path.join(RESULT_DIR, f"{ts}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[3/3] render    →  {html_path}", file=sys.stderr)

    return html_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <input.json>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path!r}", file=sys.stderr)
        sys.exit(1)

    html_path = run_pipeline(input_path)
    print(f"\nDone  →  {html_path}")


if __name__ == "__main__":
    main()
