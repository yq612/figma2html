"""2x3 仿射矩阵工具：生成、组合、求逆、转 CSS。"""
import math

from style.utils import _normalize_num


def _identity_transform():
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


def _matrix_from_rotation_translation(rotation, x, y):
    """relativeTransform 缺失时，用 rotation + x/y 生成回退矩阵。"""
    rad = (rotation or 0) * math.pi / 180
    c, s = math.cos(rad), math.sin(rad)
    return [[c, s, x], [-s, c, y]]


def _get_node_transform(node):
    """
    返回节点相对其 container parent 的 2x3 affine matrix。
    优先使用 relativeTransform；缺失时回退到 rotation + x/y。
    """
    rt = node.get("relativeTransform")
    if (
        isinstance(rt, list)
        and len(rt) == 2
        and all(isinstance(row, list) and len(row) == 3 for row in rt)
    ):
        return [
            [float(rt[0][0]), float(rt[0][1]), float(rt[0][2])],
            [float(rt[1][0]), float(rt[1][1]), float(rt[1][2])],
        ]
    return _matrix_from_rotation_translation(
        node.get("rotation") or 0,
        node.get("x", 0) or 0,
        node.get("y", 0) or 0,
    )


def _matrix_multiply(m1, m2):
    a1, c1, e1 = m1[0]
    b1, d1, f1 = m1[1]
    a2, c2, e2 = m2[0]
    b2, d2, f2 = m2[1]
    return [
        [a1 * a2 + c1 * b2, a1 * c2 + c1 * d2, a1 * e2 + c1 * f2 + e1],
        [b1 * a2 + d1 * b2, b1 * c2 + d1 * d2, b1 * e2 + d1 * f2 + f1],
    ]


def _matrix_inverse(m):
    a, c, e = m[0]
    b, d, f = m[1]
    det = a * d - b * c
    if abs(det) < 1e-9:
        return _identity_transform()
    return [
        [d / det, -c / det, (c * f - d * e) / det],
        [-b / det, a / det, (b * e - a * f) / det],
    ]


def _get_local_transform(node, parent_container_transform, parent_type, is_root=False):
    """
    计算节点相对于 DOM 直接父节点的局部变换。
    Figma 文档说明 relativeTransform 是相对 container parent 的；
    对 GROUP 子节点需要 rebasing 到 GROUP 本地坐标系。
    """
    if is_root:
        return _identity_transform()
    node_transform = _get_node_transform(node)
    if parent_type == "GROUP" and parent_container_transform is not None:
        return _matrix_multiply(_matrix_inverse(parent_container_transform), node_transform)
    return node_transform


def _linear_is_identity(m):
    a, c, _ = m[0]
    b, d, _ = m[1]
    return abs(a - 1) < 1e-9 and abs(b) < 1e-9 and abs(c) < 1e-9 and abs(d - 1) < 1e-9


def _transform_to_css(m):
    a, c, _ = m[0]
    b, d, _ = m[1]
    return (
        f"matrix({_normalize_num(a)}, {_normalize_num(b)}, "
        f"{_normalize_num(c)}, {_normalize_num(d)}, 0, 0)"
    )


def _full_transform_to_css(m):
    a, c, e = m[0]
    b, d, f = m[1]
    return (
        f"matrix({_normalize_num(a)}, {_normalize_num(b)}, {_normalize_num(c)}, "
        f"{_normalize_num(d)}, {_normalize_num(e)}, {_normalize_num(f)})"
    )


def _apply_point(m, x, y):
    a, c, e = m[0]
    b, d, f = m[1]
    return a * x + c * y + e, b * x + d * y + f


def _bounding_box_from_transform(m, w, h):
    points = [
        _apply_point(m, 0, 0),
        _apply_point(m, w, 0),
        _apply_point(m, 0, h),
        _apply_point(m, w, h),
    ]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    left = min(xs)
    top = min(ys)
    return left, top, max(xs) - left, max(ys) - top
