"""字体解析与文字节点样式生成。"""

from style.utils import _set
from style.layout import _style_common, _apply_flex_child, _is_flex_parent
from style.border import _gradient_to_css


def _font_weight(style_str):
    """fontName.style → font-weight 数值；含 Italic 时返回 (weight, font_style)。"""
    if not style_str:
        return 400, None
    s = (style_str or "").upper()
    weight = 400
    if "THIN" in s or "HAIRLINE" in s:
        weight = 100
    elif "EXTRA LIGHT" in s or "EXTRALIGHT" in s:
        weight = 200
    elif "LIGHT" in s:
        weight = 300
    elif "REGULAR" in s or "NORMAL" in s:
        weight = 400
    elif "MEDIUM" in s:
        weight = 500
    elif "SEMI BOLD" in s or "SEMIBOLD" in s:
        weight = 600
    elif "BOLD" in s and "EXTRA" not in s:
        weight = 700
    elif "EXTRA BOLD" in s or "EXTRABOLD" in s:
        weight = 800
    elif "BLACK" in s or "HEAVY" in s:
        weight = 900
    font_style = "italic" if "ITALIC" in s else None
    return weight, font_style


def _style_text(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
    s["position"] = "relative" if _is_flex_parent(parent_layout_mode) else "absolute"
    fills = node.get("fills")
    if fills and len(fills) > 0:
        fill = fills[0]
        ftype = fill.get("type", "")
        if ftype == "SOLID" and fill.get("rgba"):
            s["color"] = fill["rgba"]
        elif "GRADIENT" in ftype:
            grad_css = _gradient_to_css(fill)
            if grad_css:
                s["background"] = grad_css
                s["-webkit-background-clip"] = "text"
                s["background-clip"] = "text"
                s["-webkit-text-fill-color"] = "transparent"
    elif not fills:
        # node 无整体 fill 时，从第一个 textSegment 的 fill 取 color，
        # 使 list-style marker 等继承到正确颜色。
        for seg in (node.get("textSegments") or []):
            if not isinstance(seg, dict):
                continue
            for f in (seg.get("fills") or []):
                if isinstance(f, dict) and f.get("type") == "SOLID" and f.get("rgba"):
                    s["color"] = f["rgba"]
                    break
            break
    fs = node.get("fontSize")
    if fs is not None:
        s["font-size"] = f"{fs}px"
    fn = node.get("fontName")
    if isinstance(fn, dict):
        _set(s, "font-family", fn.get("family"))
        style_str = fn.get("style") or ""
        w, italic = _font_weight(style_str)
        s["font-weight"] = w
        if italic:
            s["font-style"] = italic
    elif fn is not None:
        s["font-family"] = str(fn)
    tah = node.get("textAlignHorizontal")
    if tah:
        s["text-align"] = {"LEFT": "left", "CENTER": "center", "RIGHT": "right"}.get(tah, "left")
    lh = node.get("lineHeight")
    if isinstance(lh, dict):
        unit = lh.get("unit")
        val = lh.get("value")
        if val is not None:
            if unit == "PERCENT":
                s["line-height"] = val / 100
            else:
                s["line-height"] = f"{val}px"
    ls = node.get("letterSpacing")
    if isinstance(ls, dict):
        unit = ls.get("unit")
        val = ls.get("value", 0) or 0
        if val != 0 and unit:
            if unit == "PERCENT":
                s["letter-spacing"] = f"{val / 100}em"
            else:
                s["letter-spacing"] = f"{val}px"
    td = node.get("textDecoration")
    if td and td != "NONE":
        s["text-decoration"] = {"UNDERLINE": "underline", "STRIKETHROUGH": "line-through"}.get(td, td.lower())
    tc = node.get("textCase")
    if tc:
        s["text-transform"] = {"UPPER": "uppercase", "LOWER": "lowercase", "TITLE": "capitalize"}.get(tc)
    # Figma 列表：TextListOptions 为 ORDERED | UNORDERED | NONE；节点上有 hasListStyle + listType 时输出列表样式
    if node.get("hasListStyle") and node.get("listType"):
        lt = node.get("listType")
        if lt == "UNORDERED":
            s["list-style-type"] = "disc"
        elif lt == "ORDERED":
            s["list-style-type"] = "decimal"
        if lt in ("UNORDERED", "ORDERED"):
            s["list-style-position"] = "outside"
            # 缩进：与 Figma 常见效果一致，避免序号/符号与文字重叠
            if "padding-left" not in s and "padding" not in s:
                s["padding-left"] = "1.5em"
    # textAutoResize 决定文本尺寸行为，避免浏览器字体渲染与 Figma 略有差异时文本换行
    auto_resize = node.get("textAutoResize") or "NONE"
    if auto_resize == "WIDTH_AND_HEIGHT":
        # 宽高均随内容自适应：不设固定尺寸，nowrap 防止字体差异导致折行
        s.pop("width", None)
        s.pop("height", None)
        s["white-space"] = "nowrap"
    elif auto_resize == "HEIGHT":
        # 固定宽、高随内容增长：保留 width，移除 height
        s.pop("height", None)
    elif auto_resize == "TRUNCATE":
        # 固定宽高 + 超出截断
        s["overflow"] = "hidden"
        s["text-overflow"] = "ellipsis"
        s["white-space"] = "nowrap"
    _apply_flex_child(node, s, parent_layout_mode)
    return s
