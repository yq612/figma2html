"""图片节点识别与样式生成。"""

from style.utils import _normalize_num, _set
from style.transform import _get_local_transform, _bounding_box_from_transform, _linear_is_identity, _full_transform_to_css
from style.layout import _is_flex_parent, _apply_flex_child, _visible_rect_in_parent, _escapes_flex


def _is_image_node(node):
    """视为图片节点：isImage 为 True 或 locked 为 True（locked 节点按 image 导出处理）。"""
    return node.get("isImage") is True or node.get("locked") is True


def _style_image(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node=None):
    s = {}
    parent_abs = parent_node.get("absoluteBoundingBox") if parent_node else None
    child_abs = node.get("absoluteBoundingBox")
    if (
        parent_node
        and not _is_flex_parent(parent_layout_mode)
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
            _apply_flex_child(node, s, parent_layout_mode)
            return s
    # 父为 flex 时，区分三种情况：
    # 1. horizontal:MAX → 右侧绝对定位
    # 2. 坐标溢出父级（负值）→ 脱离 flex 流，走绝对定位
    # 3. 其余 → 正常 flex 子节点
    if _is_flex_parent(parent_layout_mode):
        constraints = node.get("constraints") or {}
        h_constraint = constraints.get("horizontal")
        if (
            h_constraint == "MAX"
            and isinstance(parent_abs, dict)
            and isinstance(child_abs, dict)
        ):
            px, pw = parent_abs.get("x"), parent_abs.get("width")
            cx, cy, cw, ch = child_abs.get("x"), child_abs.get("y"), child_abs.get("width"), child_abs.get("height")
            py = parent_abs.get("y")
            if None not in (px, pw, py, cx, cy, cw, ch):
                right_px = (px + pw) - (cx + cw)
                top_px = cy - py
                s["position"] = "absolute"
                s["right"] = f"{_normalize_num(right_px)}px"
                s["top"] = f"{_normalize_num(top_px)}px"
                s["width"] = f"{_normalize_num(cw)}px"
                s["height"] = f"{_normalize_num(ch)}px"
                _apply_flex_child(node, s, parent_layout_mode)
                return s
        if _escapes_flex(node):
            # 负坐标节点脱离 flex 流，按绝对定位还原 Figma 坐标
            local_transform = _get_local_transform(node, parent_container_transform, parent_type, is_root)
            w, h = node.get("width"), node.get("height")
            if w is not None and h is not None:
                if _linear_is_identity(local_transform):
                    left, top, box_w, box_h = _bounding_box_from_transform(local_transform, w, h)
                    s["left"] = f"{_normalize_num(left)}px"
                    s["top"] = f"{_normalize_num(top)}px"
                    _set(s, "width", f"{_normalize_num(box_w)}px")
                    _set(s, "height", f"{_normalize_num(box_h)}px")
                else:
                    _set(s, "left", "0px")
                    _set(s, "top", "0px")
                    s["transform"] = _full_transform_to_css(local_transform)
                    s["transform-origin"] = "0 0"
                    _set(s, "width", f"{_normalize_num(w)}px")
                    _set(s, "height", f"{_normalize_num(h)}px")
                s["position"] = "absolute"
            return s
        w, h = node.get("width"), node.get("height")
        if w is not None and h is not None:
            s["width"] = f"{_normalize_num(w)}px"
            s["height"] = f"{_normalize_num(h)}px"
        s["position"] = "relative"
        s["flex-shrink"] = "0"
        _apply_flex_child(node, s, parent_layout_mode)
        return s
    # 非 flex 父：图片用绝对定位还原 Figma 坐标（如右侧滚动条等）。
    local_transform = _get_local_transform(node, parent_container_transform, parent_type, is_root)
    w, h = node.get("width"), node.get("height")
    if w is not None and h is not None:
        if _linear_is_identity(local_transform):
            left, top, box_w, box_h = _bounding_box_from_transform(local_transform, w, h)
            s["left"] = f"{_normalize_num(left)}px"
            s["top"] = f"{_normalize_num(top)}px"
            _set(s, "width", f"{_normalize_num(box_w)}px")
            _set(s, "height", f"{_normalize_num(box_h)}px")
        else:
            # 有旋转/倾斜时，用原始尺寸 + CSS transform 还原旋转，避免拉伸
            _set(s, "left", "0px")
            _set(s, "top", "0px")
            s["transform"] = _full_transform_to_css(local_transform)
            s["transform-origin"] = "0 0"
            _set(s, "width", f"{_normalize_num(w)}px")
            _set(s, "height", f"{_normalize_num(h)}px")
        s["position"] = "absolute"
    _apply_flex_child(node, s, parent_layout_mode)
    return s
