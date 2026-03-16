"""节点 HTML 渲染：标签选择与递归输出。"""
import html

from render.css_utils import build_inline_style
from render.text import render_text_content, render_text_content_as_list


def _is_image_node(node):
    """视为图片节点：isImage 为 True 或 locked 为 True（locked 节点按 image 导出处理）。"""
    return node.get("isImage") is True or node.get("locked") is True


def _tag_for_node(node):
    """根据 type、isImage、locked、列表属性返回标签名。"""
    node_type = node.get("type") or ""
    is_image = _is_image_node(node)
    if is_image:
        return "img"
    if node_type == "TEXT" and node.get("hasListStyle") and node.get("listType") in ("ORDERED", "UNORDERED"):
        return "ol" if node.get("listType") == "ORDERED" else "ul"
    if node_type == "TEXT":
        return "div"
    return "div"


def render_node(node, is_root=False, indent=0):
    """
    递归渲染节点为 HTML 字符串。
    - visible=false 时加 display:none
    - isImage 时只输出 <img>，不渲染 children
    - 根节点 position 改为 relative
    - 每个标签带 data-id
    """
    if not isinstance(node, dict):
        return ""

    indent_str = "  " * indent
    visible = node.get("visible", True)
    is_image = _is_image_node(node)
    node_id = node.get("id", "")
    name = node.get("name", "")
    style_obj = node.get("style") or {}

    style_str = build_inline_style(
        style_obj,
        is_image=is_image,
        is_root=is_root,
        visible=visible,
    )

    data_attrs = f' data-id="{html.escape(str(node_id))}"'

    if is_image:
        src = node.get("src") or ""
        if style_str:
            return f'{indent_str}<img{data_attrs} style="{style_str}" src="{html.escape(src)}">\n'
        return f'{indent_str}<img{data_attrs} src="{html.escape(src)}">\n'

    tag = _tag_for_node(node)
    node_type = node.get("type") or ""

    if node_type == "TEXT":
        if tag in ("ul", "ol"):
            inner = render_text_content_as_list(node)
        else:
            inner = render_text_content(node)
        if style_str:
            return f'{indent_str}<{tag}{data_attrs} style="{style_str}">{inner}</{tag}>\n'
        return f'{indent_str}<{tag}{data_attrs}>{inner}</{tag}>\n'

    children = node.get("children") or []
    child_html = "".join(render_node(c, is_root=False, indent=indent + 1) for c in children)

    if style_str:
        return f'{indent_str}<{tag}{data_attrs} style="{style_str}">\n{child_html}{indent_str}</{tag}>\n'
    return f'{indent_str}<{tag}{data_attrs}>\n{child_html}{indent_str}</{tag}>\n'
