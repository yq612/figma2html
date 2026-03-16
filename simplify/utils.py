"""通用辅助：null 清理、字段裁剪、fills/strokes 精简。"""


def _drop_nulls(obj, _seen=None):
    """递归移除值为 None 的键；_seen 用于打破循环引用（如 parent）。"""
    if _seen is None:
        _seen = set()
    if isinstance(obj, dict):
        oid = id(obj)
        if oid in _seen:
            return {}
        _seen.add(oid)
        try:
            return {k: _drop_nulls(v, _seen) for k, v in obj.items() if v is not None}
        finally:
            _seen.discard(oid)
    if isinstance(obj, list):
        oid = id(obj)
        if oid in _seen:
            return []
        _seen.add(oid)
        try:
            return [_drop_nulls(x, _seen) for x in obj]
        finally:
            _seen.discard(oid)
    return obj


def _pick(node, keys):
    """从 node 中只取 keys 中的字段（存在则取，不存在则无该键）。"""
    return {k: node[k] for k in keys if k in node}


def _simplify_fills(fills):
    """精简 fills：SOLID 保留 type+rgba；GRADIENT_* 保留 type+gradientStops+gradientHandlePositions。"""
    if not fills:
        return fills
    result = []
    for f in fills:
        if not isinstance(f, dict):
            continue
        ftype = f.get("type", "")
        if ftype == "SOLID":
            if f.get("rgba"):
                result.append({"type": ftype, "rgba": f["rgba"]})
        elif "GRADIENT" in ftype:
            entry = {"type": ftype}
            if "gradientStops" in f:
                entry["gradientStops"] = f["gradientStops"]
            if "gradientHandlePositions" in f:
                entry["gradientHandlePositions"] = f["gradientHandlePositions"]
            # 即使缺少 stops 数据也保留，后续渲染层按需处理
            result.append(entry)
    return result or None


def _simplify_strokes(strokes):
    """与 fills SOLID 逻辑一致：每项只保留 type + rgba。"""
    if not strokes:
        return strokes
    return [{k: s[k] for k in ("type", "rgba") if k in s} for s in strokes if isinstance(s, dict) and s.get("rgba")]


def _drop_stroke_if_no_strokes(out):
    """strokes 为空或不存在时去掉 strokeWeight、strokeAlign。"""
    if not out.get("strokes"):
        out.pop("strokeWeight", None)
        out.pop("strokeAlign", None)
