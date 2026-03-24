"""编排层：遍历节点树生成 style，最小化节点，CLI 入口。"""
import json
import sys

from style.nodes import _TYPE_STYLE
from style.image import _is_image_node, _style_image
from style.layout import _style_common
from style.transform import _get_node_transform


_MINIMAL_KEYS_BASE = ("id", "type", "name", "visible", "style")
_MINIMAL_KEYS_TEXT = _MINIMAL_KEYS_BASE + ("characters", "textSegments", "hasListStyle", "listType")
_MINIMAL_KEYS_IMAGE = _MINIMAL_KEYS_BASE + ("isImage", "src", "locked")


def add_style(node, parent_container_transform=None, parent_type=None, parent_layout_mode=None, is_root=False, parent_node=None):
    """遍历节点树，为每个节点生成 style 并挂载到 node.style，递归处理 children。返回 node。"""
    if not isinstance(node, dict):
        return node
    if _is_image_node(node):
        node["style"] = _style_image(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
        return node
    handler = _TYPE_STYLE.get(node.get("type"))
    if handler:
        node["style"] = handler(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
    else:
        node["style"] = _style_common(node, parent_container_transform, parent_type, is_root, parent_layout_mode, parent_node)
        if node.get("type"):
            print(f"warning: no style handler for type {node.get('type')!r}, using common only", file=sys.stderr)
    node_type = node.get("type")
    if node_type == "FRAME":
        layout_mode = node.get("layoutMode")  # FRAME 用自身的 layoutMode
    elif node_type == "GROUP":
        layout_mode = None  # GROUP 无布局系统，子节点始终绝对定位
    else:
        layout_mode = parent_layout_mode
    # GROUP 子节点的 relativeTransform 是相对 container parent 的，
    # 需要用 GROUP 自身的 transform 做 rebasing，即使 GROUP 是根节点也必须传递。
    next_parent_transform = _get_node_transform(node)
    next_parent_type = node.get("type")
    for c in node.get("children") or []:
        add_style(c, next_parent_transform, next_parent_type, layout_mode, is_root=False, parent_node=node)
    return node


def minimize_node(node):
    """递归保留 id/type/name/visible/style/children 及 type 相关内容字段，其余删除。返回新 dict。"""
    if not isinstance(node, dict):
        return node
    if _is_image_node(node):
        keys = _MINIMAL_KEYS_IMAGE
    elif node.get("type") == "TEXT":
        keys = _MINIMAL_KEYS_TEXT
    else:
        keys = _MINIMAL_KEYS_BASE
    out = {k: node[k] for k in keys if k in node}
    if "children" in node and node["children"]:
        out["children"] = [minimize_node(c) for c in node["children"]]
    return out


def main():
    import argparse
    p = argparse.ArgumentParser(description="加 style 并默认最小化；--keep-all 保留全部属性")
    p.add_argument("input", help="input.json")
    p.add_argument("output", help="output.json")
    p.add_argument("--keep-all", action="store_true", help="保留全部 Figma 属性，不最小化")
    args = p.parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    add_style(data, None, None, None, is_root=True)
    if not args.keep_all:
        data = minimize_node(data)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
