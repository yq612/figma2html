"""定位与 Flex 布局：_style_common、_apply_flex_child 及相关常量。"""

from style.utils import _set, _normalize_num
from style.transform import (
    _get_local_transform,
    _linear_is_identity,
    _full_transform_to_css,
    _transform_to_css,
)

# layoutMode 常量
LAYOUT_NONE = "NONE"
LAYOUT_HORIZONTAL = "HORIZONTAL"
LAYOUT_VERTICAL = "VERTICAL"

_JUSTIFY_MAP = {"MIN": "flex-start", "CENTER": "center", "MAX": "flex-end", "SPACE_BETWEEN": "space-between"}
_ALIGN_MAP = {"MIN": "flex-start", "CENTER": "center", "MAX": "flex-end", "BASELINE": "baseline"}
_FLEX_DIRECTION_MAP = {"HORIZONTAL": "row", "VERTICAL": "column"}


def _visible_rect_in_parent(parent_abs, child_abs):
    """
    父开启 clipsContent 时，子节点在父坐标系下的可见矩形（交集）。
    返回 (rel_x, rel_y, rel_w, rel_h) 或 None（无交集）。
    """
    if not isinstance(parent_abs, dict) or not isinstance(child_abs, dict):
        return None
    px = parent_abs.get("x")
    py = parent_abs.get("y")
    pw = parent_abs.get("width")
    ph = parent_abs.get("height")
    cx = child_abs.get("x")
    cy = child_abs.get("y")
    cw = child_abs.get("width")
    ch = child_abs.get("height")
    if None in (px, py, pw, ph, cx, cy, cw, ch):
        return None
    ix = max(cx, px)
    iy = max(cy, py)
    ir = min(cx + cw, px + pw)
    ib = min(cy + ch, py + ph)
    if ix >= ir or iy >= ib:
        return None
    return (ix - px, iy - py, ir - ix, ib - iy)


def _is_flex_parent(parent_layout_mode):
    return parent_layout_mode in (LAYOUT_HORIZONTAL, LAYOUT_VERTICAL)


def _escapes_flex(node):
    """
    检测节点是否应脱离父级 flex 流，走绝对定位。
    依据：relativeTransform 平移分量存在负值，说明节点被设计为溢出父级边界
    （对应 Figma auto-layout 中的 "absolute position" 功能）。
    """
    rt = node.get("relativeTransform") or []
    if len(rt) >= 2 and len(rt[0]) >= 3 and len(rt[1]) >= 3:
        return rt[0][2] < 0 or rt[1][2] < 0
    return False


def _effective_size(node, local_transform):
    """
    取节点用于 style 的宽高。优先用 absoluteBoundingBox（与 Figma 画布上实际渲染/Resizing 一致），
    有旋转/倾斜时用 node.width/height（为变换前本地尺寸，由 transform 负责旋转）。
    """
    if not _linear_is_identity(local_transform):
        w, h = node.get("width"), node.get("height")
        if w is not None and h is not None:
            return w, h
    child_abs = node.get("absoluteBoundingBox")
    if isinstance(child_abs, dict):
        aw = child_abs.get("width")
        ah = child_abs.get("height")
        if aw is not None and ah is not None:
            return aw, ah
    return node.get("width"), node.get("height")


def _padding_css(pt, pr, pb, pl):
    if pt == pr == pb == pl:
        return f"{pt}px" if pt != 0 else None
    if pt == pb and pr == pl:
        return f"{pt}px {pr}px" if (pt or pr) else None
    return f"{pt}px {pr}px {pb}px {pl}px"


def _actually_stretches(node, parent_layout_mode):
    """
    检查子节点在交叉轴上是否真正拉伸到与父级一致。
    Figma JSON 中 layoutAlign="STRETCH" 有时并不反映实际渲染：
    子节点可能保留固有尺寸并居中对齐。
    判断依据：relativeTransform 的交叉轴偏移量。若子节点在交叉轴上有显著偏移
    （> paddingTop/paddingLeft），说明它被居中/对齐而非拉伸。
    """
    parent_info = node.get("parent") or {}
    rt = node.get("relativeTransform") or []
    if len(rt) < 2 or len(rt[0]) < 3 or len(rt[1]) < 3:
        return True  # 无法判断，默认信任
    if parent_layout_mode == LAYOUT_HORIZONTAL:
        # 交叉轴 = y 方向
        cross_offset = rt[1][2]
        parent_padding = parent_info.get("paddingTop", 0) or 0
        # 若 y 偏移显著大于 paddingTop，说明未拉伸
        if cross_offset > parent_padding + 2:
            return False
    elif parent_layout_mode == LAYOUT_VERTICAL:
        # 交叉轴 = x 方向
        cross_offset = rt[0][2]
        parent_padding = parent_info.get("paddingLeft", 0) or 0
        if cross_offset > parent_padding + 2:
            return False
    return True


def _apply_flex_child(node, s, parent_layout_mode):
    if parent_layout_mode not in (LAYOUT_HORIZONTAL, LAYOUT_VERTICAL):
        return
    if node.get("layoutAlign") == "STRETCH":
        if _actually_stretches(node, parent_layout_mode):
            s["align-self"] = "stretch"
            # STRETCH 控制交叉轴：column 父 → cross=width → 100%；row 父 → cross=height → 100%
            if parent_layout_mode == LAYOUT_VERTICAL:
                s["width"] = "100%"
            elif parent_layout_mode == LAYOUT_HORIZONTAL:
                s["height"] = "100%"
        # 若实际未拉伸，不设置 align-self，让父级 align-items 生效
    if node.get("layoutGrow") == 1:
        s["flex"] = "1"
        # flex:1 接管主轴尺寸（flex-basis:0 覆盖固定值），移除主轴的固定 px 避免冲突
        # column 父 → 主轴=height；row 父 → 主轴=width
        if parent_layout_mode == LAYOUT_VERTICAL:
            s.pop("height", None)
            # 交叉轴填满并允许收缩，避免固定 width 超出父级导致答案被裁切或换行失效
            s["width"] = "100%"
            s["min-width"] = "0"
        elif parent_layout_mode == LAYOUT_HORIZONTAL:
            s.pop("width", None)
            s["min-width"] = "0"


def _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = {}
    # 仅当父开启 clipsContent 且父子均有 absoluteBoundingBox 时，用可见矩形（交集）作为位置与尺寸。
    # 父为 flex 布局时跳过此分支，让子节点按 flex 流式布局，避免固定 left/top/width 导致错位或答案不显示。
    parent_abs = parent_node.get("absoluteBoundingBox") if parent_node else None
    child_abs = node.get("absoluteBoundingBox")
    parent_is_flex = _is_flex_parent(parent_layout_mode)
    if (
        parent_node
        and not parent_is_flex
        and parent_node.get("clipsContent")
        and isinstance(parent_abs, dict)
        and isinstance(child_abs, dict)
    ):
        visible = _visible_rect_in_parent(parent_abs, child_abs)
        if visible:
            rel_x, rel_y, rel_w, rel_h = visible
            s["left"] = f"{_normalize_num(rel_x)}px"
            s["top"] = f"{_normalize_num(rel_y)}px"
            s["width"] = f"{_normalize_num(rel_w)}px"
            s["height"] = f"{_normalize_num(rel_h)}px"
            s["position"] = "relative" if _is_flex_parent(parent_layout_mode) else "absolute"
            _set(s, "opacity", node.get("opacity"), 1)
            if _is_flex_parent(parent_layout_mode):
                _apply_flex_child(node, s, parent_layout_mode)
            return s
    local_transform = _get_local_transform(node, parent_container_transform, parent_type, is_root)
    if not _is_flex_parent(parent_layout_mode) or _escapes_flex(node):
        if _linear_is_identity(local_transform):
            _set(s, "left", f"{_normalize_num(local_transform[0][2])}px")
            _set(s, "top", f"{_normalize_num(local_transform[1][2])}px")
        else:
            # Figma 文档中 relativeTransform 是完整的局部仿射矩阵。
            # 一旦存在旋转/倾斜，旋转支点已经被编码进矩阵平移分量中，
            # 不应再通过 width/height 推导额外的 transform-origin。
            _set(s, "left", "0px")
            _set(s, "top", "0px")
            s["transform"] = _full_transform_to_css(local_transform)
            s["transform-origin"] = "0 0"
    w, h = _effective_size(node, local_transform)
    _set(s, "width", f"{_normalize_num(w)}px" if w is not None else None)
    _set(s, "height", f"{_normalize_num(h)}px" if h is not None else None)
    _set(s, "opacity", node.get("opacity"), 1)
    if _is_flex_parent(parent_layout_mode) and not _linear_is_identity(local_transform):
        s["transform"] = _transform_to_css(local_transform)
    return s
