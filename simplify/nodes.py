"""各节点类型的字段白名单、精简处理器，以及 simplify_node 递归编排。"""
import sys

from simplify.utils import _pick, _simplify_fills, _simplify_strokes, _drop_stroke_if_no_strokes, _drop_nulls

# 各 type 保留字段；locked 节点按 image 导出处理，故保留 locked
_IMAGE_KEYS = (
    "id", "type", "name", "visible", "locked", "isImage", "src",
    "width", "height", "x", "y", "opacity", "rotation", "relativeTransform",
    "absoluteBoundingBox",
    "layoutGrow", "layoutAlign",
)
_FRAME_KEYS = (
    "id", "type", "name", "visible",
    "width", "height", "x", "y", "opacity", "rotation", "relativeTransform",
    "fills", "strokes", "strokeWeight", "strokeAlign", "cornerRadius", "effects",
    "layoutMode", "primaryAxisAlignItems", "counterAxisAlignItems",
    "paddingLeft", "paddingRight", "paddingTop", "paddingBottom",
    "itemSpacing", "layoutWrap",
    "clipsContent", "absoluteBoundingBox",
    "layoutGrow", "layoutAlign",
    "children",
)
_GROUP_KEYS = (
    "id", "type", "name", "visible",
    "width", "height", "x", "y", "opacity", "rotation", "relativeTransform",
    "absoluteBoundingBox",
    "layoutGrow", "layoutAlign",
    "children",
)
_TEXT_KEYS = (
    "id", "type", "name", "visible",
    "width", "height", "x", "y", "opacity", "rotation", "relativeTransform",
    "absoluteBoundingBox",
    "fills", "strokes", "strokeWeight", "strokeAlign",
    "fontSize", "fontName",
    "textAlignHorizontal", "textAlignVertical",
    "letterSpacing", "lineHeight", "textDecoration", "textCase",
    "textAutoResize",
    "characters",
    "textSegments", "hasListStyle", "listType",
    "layoutGrow", "layoutAlign",
)
_RECTANGLE_KEYS = (
    "id", "type", "name", "visible",
    "width", "height", "x", "y", "opacity", "rotation", "relativeTransform",
    "absoluteBoundingBox",
    "fills", "strokes", "strokeWeight", "strokeAlign", "cornerRadius", "effects",
    "layoutGrow", "layoutAlign",
)
_LINE_KEYS = (
    "id", "type", "name", "visible",
    "width", "height", "x", "y", "opacity", "rotation", "relativeTransform",
    "absoluteBoundingBox",
    "strokes", "strokeWeight", "strokeAlign",
    "layoutGrow", "layoutAlign",
)
_BASE_KEYS = ("id", "type", "name", "visible", "width", "height", "x", "y")


def _simplify_image(node):
    return _pick(node, _IMAGE_KEYS)


def _simplify_frame(node):
    out = _pick(node, _FRAME_KEYS)
    if "children" in out:
        out["children"] = [simplify_node(c) for c in out["children"]]
    return out


def _simplify_group(node):
    out = _pick(node, _GROUP_KEYS)
    if "children" in out:
        out["children"] = [simplify_node(c) for c in out["children"]]
    return out


def _simplify_text(node):
    out = _pick(node, _TEXT_KEYS)
    segs = out.get("textSegments")
    if segs is not None and len(segs) <= 1:
        out.pop("textSegments", None)
    return out


def _simplify_rectangle(node):
    return _pick(node, _RECTANGLE_KEYS)


def _simplify_line(node):
    return _pick(node, _LINE_KEYS)


def _simplify_instance(node):
    print("warning: INSTANCE without isImage, keeping base fields only", file=sys.stderr)
    return _pick(node, _BASE_KEYS)


def _simplify_vector(node):
    print("warning: VECTOR without isImage, keeping base fields only", file=sys.stderr)
    return _pick(node, _BASE_KEYS)


def _simplify_unknown(node):
    print(f"warning: unknown type {node.get('type')!r}, keeping base fields only", file=sys.stderr)
    return _pick(node, _BASE_KEYS)


_TYPE_HANDLERS = {
    "FRAME":     _simplify_frame,
    "GROUP":     _simplify_group,
    "TEXT":      _simplify_text,
    "RECTANGLE": _simplify_rectangle,
    "LINE":      _simplify_line,
    "INSTANCE":  _simplify_instance,
    "VECTOR":    _simplify_vector,
}


def simplify_node(node):
    """递归精简节点树。isImage 或 locked 时按 image 处理，再按 type 分发。"""
    if not isinstance(node, dict):
        return node
    is_image = node.get("isImage") is True or node.get("locked") is True
    if is_image:
        out = _simplify_image(node)
        # locked 但上游未带 export 时，确保有 isImage 与 src 占位，便于 style/render 按 img 渲染
        if node.get("locked") is True:
            out["isImage"] = True
            if not out.get("src"):
                out["src"] = ""
    else:
        handler = _TYPE_HANDLERS.get(node.get("type"), _simplify_unknown)
        out = handler(node)
    if out.get("fills"):
        out["fills"] = _simplify_fills(out["fills"])
        if not out["fills"]:
            out.pop("fills", None)
    if out.get("strokes"):
        out["strokes"] = _simplify_strokes(out["strokes"])
        if not out["strokes"]:
            out.pop("strokes", None)
    _drop_stroke_if_no_strokes(out)
    return _drop_nulls(out)
