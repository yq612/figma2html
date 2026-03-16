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
        if t == "DROP_SHADOW":
            rgba = e.get("rgba", "rgba(0,0,0,0)")
            ox, oy = e.get("offsetX", 0), e.get("offsetY", 0)
            r, sp = e.get("radius", 0), e.get("spread", 0)
            box_shadows.append(f"{ox}px {oy}px {r}px {sp}px {rgba}")
        elif t == "INNER_SHADOW":
            rgba = e.get("rgba", "rgba(0,0,0,0)")
            ox, oy = e.get("offsetX", 0), e.get("offsetY", 0)
            r, sp = e.get("radius", 0), e.get("spread", 0)
            box_shadows.append(f"inset {ox}px {oy}px {r}px {sp}px {rgba}")
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
