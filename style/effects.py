"""阴影与滤镜效果：box-shadow、backdrop-filter、filter。"""
import sys


def _effects_to_css(effects):
    """effects 数组 → box_shadows (str), backdrop_filter (str), filter (str)。"""
    if not effects:
        return None, None, None
    box_shadows = []
    backdrop = None
    layer_blur = None
    for e in effects:
        if not isinstance(e, dict) or not e.get("visible", True):
            continue
        t = e.get("type")
        if t in ("DROP_SHADOW", "INNER_SHADOW"):
            # Support both flat keys (offsetX/offsetY/rgba) and nested Figma format (offset.x/offset.y/color)
            rgba = e.get("rgba")
            if not rgba:
                c = e.get("color", {})
                cr, cg, cb, ca = c.get("r", 0), c.get("g", 0), c.get("b", 0), c.get("a", 1)
                rgba = f"rgba({round(cr*255)}, {round(cg*255)}, {round(cb*255)}, {ca})"
            offset = e.get("offset")
            if offset and isinstance(offset, dict):
                ox, oy = offset.get("x", 0), offset.get("y", 0)
            else:
                ox, oy = e.get("offsetX", 0), e.get("offsetY", 0)
            r, sp = e.get("radius", 0), e.get("spread", 0)
            prefix = "inset " if t == "INNER_SHADOW" else ""
            box_shadows.append(f"{prefix}{ox}px {oy}px {r}px {sp}px {rgba}")
        elif t == "BACKGROUND_BLUR":
            r = e.get("radius", 0)
            backdrop = f"blur({r}px)"
        elif t == "LAYER_BLUR":
            r = e.get("radius", 0)
            layer_blur = f"blur({r}px)"
        else:
            print(f"warning: unknown effect type {t!r}", file=sys.stderr)
    box_str = ", ".join(box_shadows) if box_shadows else None
    return box_str, backdrop, layer_blur
