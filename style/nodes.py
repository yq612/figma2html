"""各节点类型的 style 生成器：FRAME、GROUP、RECTANGLE、LINE。"""

from style.layout import (
    _style_common,
    _apply_flex_child,
    _is_flex_parent,
    _escapes_flex,
    _padding_css,
    LAYOUT_NONE,
    _JUSTIFY_MAP,
    _ALIGN_MAP,
    _FLEX_DIRECTION_MAP,
)
from style.border import _style_background_border
from style.transform import _get_local_transform, _normalize_num
from style.typography import _style_text
from style.utils import _set


def _pos(parent_layout_mode, node):
    """计算节点的 CSS position 值：flex 子节点默认 relative，但脱离 flex 流时强制 absolute。"""
    if _is_flex_parent(parent_layout_mode) and not _escapes_flex(node):
        return "relative"
    return "absolute"


def _style_frame(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
    # 背景/边框/阴影对两种 layout 均适用，统一在分支前处理
    _style_background_border(node, s, parent_node)
    if node.get("clipsContent"):
        s["overflow"] = "hidden"
    escapes = _escapes_flex(node)
    layout = node.get("layoutMode") or LAYOUT_NONE
    if layout == LAYOUT_NONE:
        s["position"] = _pos(parent_layout_mode, node)
        if not escapes:
            _apply_flex_child(node, s, parent_layout_mode)
        return s
    # flex
    s["position"] = _pos(parent_layout_mode, node)
    s["display"] = "flex"
    _set(s, "flex-direction", _FLEX_DIRECTION_MAP.get(layout, "row"))
    pa = node.get("primaryAxisAlignItems")
    if pa and pa in _JUSTIFY_MAP:
        s["justify-content"] = _JUSTIFY_MAP[pa]
    else:
        _set(s, "justify-content", _JUSTIFY_MAP.get(pa, "flex-start"))
    ca = node.get("counterAxisAlignItems")
    if ca and ca in _ALIGN_MAP:
        s["align-items"] = _ALIGN_MAP[ca]
    else:
        _set(s, "align-items", _ALIGN_MAP.get(ca, "flex-start"))
    pt = node.get("paddingTop", 0) or 0
    pr = node.get("paddingRight", 0) or 0
    pb = node.get("paddingBottom", 0) or 0
    pl = node.get("paddingLeft", 0) or 0
    pad = _padding_css(pt, pr, pb, pl)
    if pad:
        s["padding"] = pad
    gap = node.get("itemSpacing")
    # Figma 的 SPACE_BETWEEN 对应的是"自动分配剩余空间"，应映射为
    # justify-content: space-between，而不是再额外叠加固定 gap。
    if pa != "SPACE_BETWEEN" and gap is not None and gap != 0:
        s["gap"] = f"{gap}px"
    if node.get("layoutWrap") == "WRAP":
        s["flex-wrap"] = "wrap"
    if not escapes:
        _apply_flex_child(node, s, parent_layout_mode)
    return s


def _style_group(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
    s["position"] = _pos(parent_layout_mode, node)
    if not _escapes_flex(node):
        _apply_flex_child(node, s, parent_layout_mode)
    return s


def _style_rectangle(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
    s["position"] = _pos(parent_layout_mode, node)
    _style_background_border(node, s, parent_node)
    if not _escapes_flex(node):
        _apply_flex_child(node, s, parent_layout_mode)
    return s


def _style_line(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
    local_transform = _get_local_transform(node, parent_container_transform, parent_type, is_root)
    escapes = _escapes_flex(node)
    s["position"] = _pos(parent_layout_mode, node)
    s["border"] = "none"
    strokes = node.get("strokes")
    stroke_css = None
    if strokes and len(strokes) > 0 and strokes[0].get("rgba"):
        sw = round(node.get("strokeWeight", 1) or 1, 2)
        stroke_css = f"{sw}px solid {strokes[0]['rgba']}"
    rot = node.get("rotation") or 0
    if stroke_css:
        if rot == 0:
            s["border-top"] = stroke_css
        elif rot in (-90, 90):
            s.pop("transform", None)
            s.pop("transform-origin", None)
            if not _is_flex_parent(parent_layout_mode) or escapes:
                s["left"] = f"{_normalize_num(local_transform[0][2])}px"
                s["top"] = f"{_normalize_num(local_transform[1][2])}px"
            s["border-left"] = stroke_css
        else:
            s["border-top"] = stroke_css
    if not escapes:
        _apply_flex_child(node, s, parent_layout_mode)
    return s


_TYPE_STYLE = {
    "FRAME": _style_frame,
    "GROUP": _style_group,
    "TEXT": _style_text,
    "RECTANGLE": _style_rectangle,
    "LINE": _style_line,
}
