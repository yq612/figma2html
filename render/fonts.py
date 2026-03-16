"""字体收集与 Google Fonts 链接生成。"""


def collect_fonts(node, fonts=None):
    """收集整棵节点树中 style 里用到的 font-family。返回 set。"""
    if fonts is None:
        fonts = set()
    if not isinstance(node, dict):
        return fonts
    style = node.get("style")
    if isinstance(style, dict) and style.get("font-family"):
        fonts.add(style["font-family"].strip())
    for c in node.get("children") or []:
        collect_fonts(c, fonts)
    return fonts


def _google_fonts_link(font_names):
    """根据字体名生成 Google Fonts css2 的 link href。"""
    if not font_names:
        return ""
    # 每个 family 用常见字重，避免 URL 过长；若需可改为从 JSON 收集字重
    families = []
    for name in sorted(font_names):
        safe = name.replace(" ", "+")
        families.append(f"family={safe}:wght@100;200;300;400;500;600;700;800;900")
    query = "&".join(families)
    return f"https://fonts.googleapis.com/css2?{query}&display=swap"
