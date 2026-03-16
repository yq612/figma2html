"""CSS 值规范化与 inline style 字符串构建。"""
import re


def _normalize_css_value(v):
    """浮点数清理：158.0px → 158px；1.4827...px → 1.48px（保留 2 位小数）。"""
    if not isinstance(v, str) or "px" not in v:
        return v
    num_part = v.replace("px", "").strip()
    try:
        f = float(num_part)
    except ValueError:
        return v
    if f == int(f):
        return f"{int(f)}px"
    return f"{round(f, 2)}px"


def _normalize_style_value_string(s):
    """对整段 style 字符串中的 blur(Npx) 做规范化：长小数保留 2 位。"""
    if not s:
        return s

    def _blur_repl(m):
        try:
            f = float(m.group(1))
            n = round(f, 2) if f != int(f) else int(f)
            return f"blur({n}px)"
        except ValueError:
            return m.group(0)

    return re.sub(r"blur\(([\d.]+)px\)", _blur_repl, s)


def build_inline_style(style, is_image=False, is_root=False, visible=True):
    """
    将 style 对象转为 inline style 字符串。
    - is_root 时 position: absolute → relative
    - isImage 且 style 有 left/top 但无 position 时补 position: absolute
    - visible=False 时加上 display:none
    - 数值清理：整数值去掉 .0，border 等保留 2 位小数
    """
    if not style or not isinstance(style, dict):
        style = {}
    s = dict(style)

    if not visible:
        s["display"] = "none"
    if is_root and s.get("position") == "absolute":
        s["position"] = "relative"
    if is_image and "position" not in s and ("left" in s or "top" in s):
        s["position"] = "absolute"

    parts = []
    for k, v in s.items():
        if v is None:
            continue
        if isinstance(v, (int, float)):
            # font-weight, line-height 等数字；浮点数保留 2 位小数
            if isinstance(v, float) and k not in ("z-index",):
                v = round(v, 2) if v != int(v) else int(v)
            parts.append(f"{k}: {v}")
            continue
        v = str(v).strip()
        if not v:
            continue
        # 带 px 的数值做规范化
        if v.endswith("px") and re.match(r"^-?\d+\.?\d*$", v.replace("px", "").strip()):
            v = _normalize_css_value(v)
        parts.append(f"{k}: {v}")
    result = "; ".join(parts)
    return _normalize_style_value_string(result)
