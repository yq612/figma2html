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
        # Figma fills 从下到上渲染（最后一项在最上层）；CSS background 从上到下渲染（第一项在最上层）
        bg_parts = []  # [(kind, css_value), ...] 按视觉从上到下排列
        for fill in reversed(fills):
            if fill.get("visible") is False:
                continue
            ftype = fill.get("type", "")
            if ftype == "SOLID" and fill.get("rgba"):
                bg_parts.append(("solid", fill["rgba"]))
            elif "GRADIENT" in ftype:
                css = _gradient_to_css(fill)
                if css:
                    bg_parts.append(("gradient", css))
        if len(bg_parts) == 1:
            s["background"] = bg_parts[0][1]
        elif len(bg_parts) > 1:
            layers = []
            for i, (kind, value) in enumerate(bg_parts):
                if kind == "gradient":
                    layers.append(value)
                elif i < len(bg_parts) - 1:
                    # 非底层纯色需要转为 gradient 才能参与多层叠加
                    layers.append(f"linear-gradient({value},{value})")
                else:
                    # 最底层纯色可直接作为 background-color（CSS shorthand 末尾层）
                    layers.append(value)
            s["background"] = ", ".join(layers)
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
        stroke_align = node.get("strokeAlign", "INSIDE")
        if stroke.get("rgba"):
            rgba = stroke["rgba"]
            if stroke_align == "OUTSIDE":
                # OUTSIDE 描边不占用布局空间，用 outline 模拟（不影响盒模型尺寸）
                s["outline"] = f"{sw}px solid {rgba}"
            else:
                children = (parent_node or {}).get("children") or []
                if (
                    parent_node is not None
                    and parent_node.get("layoutMode") == LAYOUT_VERTICAL
                    and len(children) >= 2
                ):
                    s["border-bottom"] = f"{sw}px solid {rgba}"
                else:
                    s["border"] = f"{sw}px solid {rgba}"
                if stroke_align == "INSIDE":
                    s["box-sizing"] = "border-box"
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
