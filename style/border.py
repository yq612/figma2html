"""背景色、边框、圆角与阴影效果。"""

import math

from style.effects import _effects_to_css
from style.layout import LAYOUT_VERTICAL


def _n(v):
    """统一数值规范化：整数不带小数点，其余保留 2 位小数。"""
    r = round(v, 2)
    return int(r) if r == int(r) else r


def _gradient_to_css(fill):
    """
    将 GRADIENT_LINEAR fill 转为 CSS linear-gradient()。
    gradientHandlePositions: [{x,y}, ...] — 归一化坐标（相对于节点宽高 0-1）
      [0] = 渐变起点, [1] = 渐变终点
    gradientStops: [{color:{r,g,b,a}, position:0-1}, ...]
    返回 None 表示数据不足，无法生成。
    """
    stops = fill.get("gradientStops") or []
    handles = fill.get("gradientHandlePositions") or []
    if not stops or len(handles) < 2:
        return None

    start, end = handles[0], handles[1]
    dx = end["x"] - start["x"]
    dy = end["y"] - start["y"]
    # CSS angle: 0deg = to top, 90deg = to right（顺时针）
    angle_deg = round(math.degrees(math.atan2(dx, -dy)))

    stop_parts = []
    for stop in stops:
        c = stop.get("color") or {}
        r = round(c.get("r", 0) * 255)
        g = round(c.get("g", 0) * 255)
        b = round(c.get("b", 0) * 255)
        a = _n(c.get("a", 1))
        pos = _n(stop.get("position", 0) * 100)
        stop_parts.append(f"rgba({r},{g},{b},{a}) {pos}%")

    return f"linear-gradient({angle_deg}deg, {', '.join(stop_parts)})"


def _style_background_border(node, s, parent_node=None):
    fills = node.get("fills")
    if fills and len(fills) > 0:
        fill = fills[0]
        ftype = fill.get("type", "")
        if ftype == "SOLID" and fill.get("rgba"):
            s["background"] = fill["rgba"]
        elif "GRADIENT" in ftype:
            css = _gradient_to_css(fill)
            if css:
                s["background"] = css
    cr = node.get("cornerRadius")
    if cr is not None:
        if isinstance(cr, dict):
            # 各角独立值：CSS 顺序 top-left / top-right / bottom-right / bottom-left
            tl = _n(cr.get("topLeft") or 0)
            tr = _n(cr.get("topRight") or 0)
            br = _n(cr.get("bottomRight") or 0)
            bl = _n(cr.get("bottomLeft") or 0)
            if tl or tr or br or bl:
                s["border-radius"] = f"{tl}px {tr}px {br}px {bl}px"
        elif cr != 0:
            # 单值：交给 build_inline_style 的 _normalize_css_value 统一处理
            s["border-radius"] = f"{cr}px"
    strokes = node.get("strokes")
    if strokes and len(strokes) > 0:
        stroke = strokes[0]
        sw = round(node.get("strokeWeight", 1) or 1, 2)
        stype = stroke.get("type", "")
        if stroke.get("rgba"):
            rgba = stroke["rgba"]
            children = (parent_node or {}).get("children") or []
            if (
                parent_node is not None
                and parent_node.get("layoutMode") == LAYOUT_VERTICAL
                and len(children) >= 2
            ):
                s["border-bottom"] = f"{sw}px solid {rgba}"
            else:
                s["border"] = f"{sw}px solid {rgba}"
        elif "GRADIENT" in stype:
            grad_css = _gradient_to_css(stroke)
            if grad_css:
                has_radius = s.get("border-radius")
                if has_radius:
                    # border-image 不支持 border-radius，用 background-clip 技巧实现
                    s["border"] = f"{sw}px solid transparent"
                    existing_bg = s.get("background")
                    inner = existing_bg if existing_bg else "#fff"
                    s["background"] = f"linear-gradient({inner},{inner}) padding-box, {grad_css} border-box"
                    s["background-origin"] = "border-box"
                else:
                    s["border"] = f"{sw}px solid"
                    s["border-image"] = f"{grad_css} 1"
    effects = node.get("effects")
    if effects:
        box_str, backdrop, layer_blur = _effects_to_css(effects)
        if box_str:
            s["box-shadow"] = box_str
        if backdrop:
            s["backdrop-filter"] = backdrop
            s["-webkit-backdrop-filter"] = backdrop
        if layer_blur:
            s["filter"] = layer_blur
