"""build_html 主函数与 CLI 入口。"""
import html
import json
import sys

from render.fonts import collect_fonts, _google_fonts_link
from render.node import render_node


def build_html(data):
    """
    从带 style 的节点树 data 生成完整 HTML 字符串。
    供命令行写文件与预览服务复用。
    """
    fonts = collect_fonts(data)
    font_link = _google_fonts_link(fonts)
    font_tag = f'  <link href="{font_link}" rel="stylesheet">\n' if font_link else ""

    root_name = data.get("name") or "Figma Export"
    title = html.escape(root_name)
    body_content = render_node(data, is_root=True, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #f0f0f0; }}
    /* img {{ display: block; object-fit: cover; }} */
  </style>
  <!-- 字体：从 JSON 中收集的 font-family，从 Google Fonts 引入 -->
{font_tag}</head>
<body>
{body_content}</body>
</html>
"""


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m render.builder input.json output.html", file=sys.stderr)
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = build_html(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Wrote {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
